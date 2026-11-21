import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PyQt6.QtCore import QLocale, QPointF, Qt, QPoint
QLocale.setDefault(QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil))
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
from taverna.config import CELULA
from taverna.mesa.token import TokenItem
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
M=JanelaMestre(); M.resize(1600,900); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
c=M.cena
M._carregar_imagem("mapa_teste.png", QPointF(0,0))
mapa=c.itens_do_usuario()[0]; mapa.definir_tamanho_metros(16,12); mapa.setPos(-8*CELULA,-6*CELULA)
aelar=c.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Manel"), QPointF(-3*CELULA,-2*CELULA))
lyra=c.adicionar_token(dict(nome="Lyra",tipo="jogador",cor="#5a3f6b",tamanho=1,imagem=None,dono="Bia"), QPointF(-1*CELULA,-2*CELULA))
ogro=c.adicionar_token(dict(nome="Ogro",tipo="criatura",cor="#6e2a2f",tamanho=2,imagem=None), QPointF(2*CELULA,0))
espiao=c.adicionar_token(dict(nome="Espião",tipo="npc",cor="#3b5470",tamanho=1,imagem=None), QPointF(4*CELULA,-3*CELULA))
c.definir_item_visivel(espiao, False)
assert M.servidor.abrir(7783)
def player(nome):
    P=JanelaPlayer(); P.resize(1300,800); P.show()
    P.nome, P.ip, P.porta = nome, "127.0.0.1", 7783
    P._ja_entrou=False; P._primeiro_estado=True
    P.cliente.conectar(P.ip, P.porta, P.nome); return P
P1=player("Manel"); P2=player("Bia"); w(800)
def tok(P, nome): return next(i for i in P.cena.itens.values() if isinstance(i,TokenItem) and i.nome==nome)

print("== INFORMAÇÕES")
aelar.definir_info("pv", [18, 24])                      # oculto: só mestre e dono
aelar.definir_info("condicoes", ["envenenado","sangrando"], vis="todos")
aelar.definir_info("raca", "Meio-Elfo", vis=["Bia"])
aelar.definir_info("notas", "anotação pro dono")         # oculto
aelar.definir_info("segredo", "É um doppelganger!", vis="mestre")
print("docks fechados no início:", not M.dock_combate.isVisible(), not M.dock_dados.isVisible(), not P1.docks[0].isVisible())
w(400)
a1, a2 = tok(P1,"Aelar"), tok(P2,"Aelar")
print("P1 (dono) vê:", {k:v["v"] for k,v in a1.info.items() if v["vis"]!="-"})
print("P2 vê     :", {k:v["v"] for k,v in a2.info.items() if v["vis"]!="-"})

print("segredo chegou no dono?", "doppelganger" in str(tok(P1,"Aelar").info))
print("== DADOS")
P1.painel_dados.expr.setText("1d20+3"); P1.painel_dados._rolar_texto(); w(300)
print("mestre recebeu:", M.painel_dados.historico.toPlainText().count("Manel"), "| P2 recebeu:", "Manel" in P2.painel_dados.historico.toPlainText())
M.painel_dados.privada.setChecked(True); M.painel_dados.expr.setText("8d6"); M.painel_dados._rolar_texto(); w(300)
print("privada no mestre:", "privada" in M.painel_dados.historico.toPlainText(), "| chegou no P1:", "8d6" in P1.painel_dados.historico.toPlainText())
P1.painel_dados.expr.setText("banana"); P1.painel_dados._rolar_texto(); w(300); print("erro P1:", P1.painel_dados.erro.text())

print("== FORA DE COMBATE: mestre trava movimento")
M.painel_combate.chk_movem.setChecked(False); w(300)
print("P1 token travado:", tok(P1,"Aelar").travado)
antes = aelar.scenePos(); P1.cliente.mover(aelar.uid, 0, 0); w(300)
print("servidor recusou mover:", aelar.scenePos()==antes)
M.painel_combate.chk_movem.setChecked(True); w(300)
print("liberado:", not tok(P1,"Aelar").travado)

print("== COMBATE")
M.painel_combate.iniciar("todos"); w(400)
print("participantes:", [p["nome"] for p in M.servidor.combate.participantes])
print("P1 pedido:", P1.painel_combate._pendente is not None, P1.painel_combate.pedido.text())
print("faixa mestre:", M.faixa_turnos.isVisible(), "| faixa P1 com botão rolar:", P1.faixa_turnos.isVisible(), P1.faixa_turnos.btn_rolar.isVisible())
P1.painel_combate.mod.setValue(2); P1.painel_combate._rolar(); w(300)
P2.painel_combate._rolar(); w(300)
M.painel_combate.rolar_criaturas(); w(300)
print("iniciativas:", [(p["nome"],p["ini"]) for p in M.servidor.combate.ordem()])
print("P1 lista:", [P1.painel_combate.lista.item(k).text() for k in range(P1.painel_combate.lista.count())])
M.painel_combate.proximo(); w(400)
vez = M.servidor.combate.vez; nome_vez = M.servidor.combate.participante(vez)["nome"]
print("vez de:", nome_vez, "| destaque no mestre:", [t.nome for t in (aelar,lyra,ogro) if t.da_vez])
for P,n in ((P1,"Aelar"),(P2,"Lyra")):
    print(f"  {n} pode mover?", not tok(P,n).travado, "| status:", P.painel_combate.status.text())
# quem não é da vez tenta mover
outro = lyra if nome_vez=="Aelar" else aelar
Pout = P2 if outro is lyra else P1
antes=outro.scenePos(); Pout.cliente.mover(outro.uid, 0, 0); w(300)
print("fora da vez recusado:", outro.scenePos()==antes)
for _ in range(3): M.painel_combate.proximo(); w(150)
print("após 3 próximos: rodada", M.servidor.combate.rodada, "vez", M.servidor.combate.participante(M.servidor.combate.vez)["nome"])
w(300)
c.clearSelection(); aelar.setSelected(True); w(100)
M.dock_info.raise_(); M.visao.centerOn(0,0); w(100)
M.grab().save("e6_mestre.png")
print("aviso de rolagem no mestre:", M.aviso_rolagem.isVisible(), "| no P1:", P1.aviso_rolagem.isVisible())
P1.visao.centerOn(tok(P1,"Aelar")); w(100); P1.grab().save("e6_player.png")
M.painel_combate.encerrar(); w(300)
print("encerrado:", not M.servidor.combate.ativo, P1.painel_combate.status.text(), "destaques:", [t.nome for t in (aelar,lyra,ogro) if t.da_vez])
print("FIM")
