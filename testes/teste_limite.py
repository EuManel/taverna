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
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
M=JanelaMestre(); M.resize(1500,880); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
c=M.cena
aelar=c.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Manel"), QPointF(0,0))
ogro=c.adicionar_token(dict(nome="Ogro",tipo="criatura",cor="#6e2a2f",tamanho=2,imagem=None), QPointF(8*CELULA,0))
aelar.definir_info("desl", 6.0)
assert M.servidor.abrir(7787)
P=JanelaPlayer(); P.resize(1100,750); P.show(); P.nome,P.ip,P.porta="Manel","127.0.0.1",7787
P._ja_entrou=False; P._primeiro_estado=True; P.cliente.conectar(P.ip,P.porta,P.nome); w(800)
def tok(nome): return next(i for i in P.cena.itens.values() if isinstance(i,TokenItem) and i.nome==nome)
def dist(t, o): 
    c0=t.centro_cena(); return round(((c0.x()-o.x())**2+(c0.y()-o.y())**2)**0.5/CELULA,2)

P.visao.ping_pedido.emit(QPointF(50,50)); w(100)
P.painel_dados.expr.setText("1d20+4"); P.painel_dados._rolar_texto(); w(200)
M.painel_combate.iniciar("todos"); w(200)
for p in M.servidor.combate.participantes: p["ini"] = 20 if p["nome"]=="Aelar" else 3
M.servidor.atualizar_combate(); M.painel_combate.proximo(); w(400)
print("vez:", M.servidor.combate.participante(M.servidor.combate.vez)["nome"], "| limite mestre:", aelar.limite_turno, "| player:", tok("Aelar").limite_turno)
origem = aelar.origem_turno
# player tenta ir 10 m pra direita (servidor deve segurar em 6)
P.cliente.mover(aelar.uid, 10*CELULA, 0); w(1500)
print("servidor segurou em:", dist(aelar, origem), "m")
# arrasto de verdade no player: não sai do círculo
t=tok("Aelar"); P.visao.zoom_100(); P.visao.centerOn(t); w(100)
vp=P.visao.viewport(); p0=P.visao.mapFromScene(t.centro_cena())
QTest.mousePress(vp, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p0)
for k in range(1,8): QTest.mouseMove(vp, p0+QPoint(0, 60*k)); w(30)
print("player arrastando (local):", dist(t, origem), "m")
P.visao.grab().save("limite_player.png")
QTest.mouseRelease(vp, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p0+QPoint(0,420)); w(1500)
print("mestre depois do arrasto:", dist(aelar, origem), "m")
M.painel_combate.disparada(); w(300)
print("disparada -> limite:", aelar.limite_turno, "| player:", tok("Aelar").limite_turno)
# mestre muda o deslocamento pela tabela (ferido)
for r in range(M.painel_combate.tabela.rowCount()):
    if M.painel_combate.tabela.item(r,1).text().startswith("Aelar"):
        M.painel_combate.tabela.item(r,4).setText("4,5")
w(300); print("tabela 4,5 -> desl:", aelar.deslocamento, "limite c/ disparada:", aelar.limite_turno)
M.painel_combate.chk_limitar.setChecked(False); w(300)
print("sem limite:", aelar.limite_turno, tok("Aelar").limite_turno)
M.painel_combate.chk_limitar.setChecked(True); M.painel_combate.proximo(); w(300)
# fora da vez
P.cliente.mover(aelar.uid, 0, 0); w(1300)
M.dock_historico.show(); w(100)
print("--- HISTÓRICO ---"); print(M.painel_historico.texto.toPlainText())
M.visao.centerOn(aelar); w(100); M.grab().save("limite_mestre.png")
print("FIM")
