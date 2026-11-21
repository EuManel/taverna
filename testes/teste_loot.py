import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.environ["QT_QPA_PLATFORM"]="offscreen"
from PyQt6.QtCore import QPointF, Qt, QPoint
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
from taverna.config import CELULA
from taverna.mesa.token import TokenItem
from taverna.mesa.props import PropItem
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
M=JanelaMestre(); M.resize(1500,880); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
c=M.cena
aelar=c.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Manel"), QPointF(0,0))
lyra=c.adicionar_token(dict(nome="Lyra",tipo="jogador",cor="#5a3f6b",tamanho=1,imagem=None,dono="Bia"), QPointF(-3*CELULA,2*CELULA))
gob=c.adicionar_token(dict(nome="Goblin",tipo="criatura",cor="#6e2a2f",tamanho=1,imagem=None), QPointF(1*CELULA,0))
gob.definir_info("inventario",[{"id":"g1","nome":"Cimitarra","qtd":1,"desc":"Enferrujada.","img":None},
                               {"id":"g2","nome":"Moedas de prata","qtd":7,"desc":"","img":None}])
M._colocar_prop("cama_casal", QPointF(-2*CELULA, -1*CELULA)); cama=c.selectedItems()[0]
M._colocar_prop("estatua", QPointF(4*CELULA, 3*CELULA)); est=c.selectedItems()[0]
assert M.servidor.abrir(7791)
P=JanelaPlayer(); P.resize(1200,800); P.show(); P.nome,P.ip,P.porta="Manel","127.0.0.1",7791
P._ja_entrou=False; P._primeiro_estado=True; P.cliente.conectar(P.ip,P.porta,P.nome); w(900)
avisos=[]; P.cliente.aviso_recebido.connect(avisos.append)
def tok(n): return next(i for i in P.cena.itens.values() if isinstance(i,TokenItem) and i.nome==n)
def prop(n): return next(i for i in P.cena.itens.values() if isinstance(i,PropItem) and i.nome==n)

print("== ESTADO / MORTE")
c.clearSelection(); gob.setSelected(True); M.painel_info.atualizar()
M.painel_info.pv_max.setValue(7); M.painel_info.pv.setValue(7); w(50)
P.cena.token_duplo_clique(tok("Goblin")); w(300); print("vivo, revistar:", avisos[-1] if avisos else None)
M.painel_info.pv.setValue(0); w(400)
print("goblin PV 0 ->", gob.estado, "| player vê:", tok("Goblin").estado)
c.clearSelection(); aelar.setSelected(True); M.painel_info.atualizar()
M.painel_info.pv_max.setValue(20); M.painel_info.pv.setValue(-2); w(300)
print("Aelar PV<=0 ->", aelar.estado); M.painel_info.pv.setValue(5); w(300); print("curado ->", aelar.estado)

print("== SAQUEAR")
P.cena.token_duplo_clique(tok("Goblin")); w(400)
print("janela:", P.janela_conteudo.isVisible(), P.janela_conteudo.titulo.text(), "|", P.janela_conteudo.subtitulo.text())
P.janela_conteudo.grab().save("loot_janela.png")
P.janela_conteudo.pegar.emit(gob.uid, "g1"); w(400)
print("goblin ficou:", [i["nome"] for i in gob.info["inventario"]["v"]], "| Aelar:", [i["nome"] for i in aelar.info["inventario"]["v"]])
P.janela_conteudo.hide()

print("== COMBATE pula morto")
M.painel_combate.iniciar("todos"); w(200)
for p in M.servidor.combate.participantes: p["ini"]={"Aelar":15,"Goblin":10,"Lyra":5}[p["nome"]]
M.servidor.atualizar_combate(); M.painel_combate.proximo(); w(100)
M.painel_combate.proximo(); w(200)
print("depois do Aelar vem:", M.servidor.combate.participante(M.servidor.combate.vez)["nome"])
M.painel_combate.encerrar(); w(300)

print("== MOVER OBJETOS")
print("cama móvel no player:", bool(prop("Cama de casal").flags() & prop("Cama de casal").GraphicsItemFlag.ItemIsMovable),
      "| estátua:", bool(prop("Estátua").flags() & prop("Estátua").GraphicsItemFlag.ItemIsMovable))
antes = cama.centro_cena()
P.cliente.mover_prop(cama.uid, cama.scenePos().x()-1*CELULA, cama.scenePos().y()); w(400)
print("empurrou 1 m:", round((antes.x()-cama.centro_cena().x())/CELULA,2))
antes = cama.centro_cena()
P.cliente.mover_prop(cama.uid, cama.scenePos().x()-10*CELULA, cama.scenePos().y()); w(400)
print("tentou jogar 10 m, foi:", round((antes.x()-cama.centro_cena().x())/CELULA,2), "m (limitado ao alcance)")
P.cliente.mover_prop(est.uid, 0, 0); w(300); print("estátua:", avisos[-1])
aelar.setPos(10*CELULA, 10*CELULA); w(300)
P.cliente.mover_prop(cama.uid, 0, 0); w(300); print("longe:", avisos[-1])
print("--- HISTÓRICO ---"); print(M.painel_historico.texto.toPlainText())
aelar.setPos(0,0); w(400)
c.clearSelection(); gob.setSelected(True); M.dock_info.raise_(); M.painel_info.atualizar()
M.visao.centerOn(QPointF(0,0)); w(200); M.grab().save("loot_mestre.png")
P.visao.centerOn(QPointF(0,0)); w(300); P.visao.grab().save("loot_player.png")
print("FIM")
