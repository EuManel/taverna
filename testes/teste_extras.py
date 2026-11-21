import sys, os, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.environ["QT_QPA_PLATFORM"]="offscreen"
from PyQt6.QtCore import QPointF, Qt, QPoint
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
from taverna.config import CELULA
from taverna.mesa.token import TokenItem
from taverna.mesa.ping import PingItem
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
M=JanelaMestre(); M.resize(1400,850); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
c=M.cena
aelar=c.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Manel"), QPointF(0,0))
ogro=c.adicionar_token(dict(nome="Ogro",tipo="criatura",cor="#6e2a2f",tamanho=2,imagem=None), QPointF(5*CELULA,0))
assert M.servidor.abrir(7785)
P=JanelaPlayer(); P.resize(1100,750); P.show(); P.nome,P.ip,P.porta="Manel","127.0.0.1",7785
P._ja_entrou=False; P._primeiro_estado=True; P.cliente.conectar(P.ip,P.porta,P.nome); w(800)
def tok(nome): return next(i for i in P.cena.itens.values() if isinstance(i,TokenItem) and i.nome==nome)

print("== PING")
P.visao.ping_pedido.emit(QPointF(100,100)); w(300)
print("ping no mestre:", sum(isinstance(i,PingItem) for i in c.items()), "| no player:", sum(isinstance(i,PingItem) for i in P.cena.items()))
M._ping(QPointF(200,50)); w(300)
print("ping do mestre chegou no player:", sum(isinstance(i,PingItem) and i.nome=="Mestre" for i in P.cena.items()))
w(2800); print("pings somem:", sum(isinstance(i,PingItem) for i in c.items()+P.cena.items()))

print("== DURAÇÃO")
c.clearSelection(); ogro.setSelected(True); w(50)
campo = ogro.info["condicoes"]; campo["dur"]={"atordoado":1}; ogro.definir_info("condicoes",["atordoado","caido"], vis="todos")
M.painel_info.atualizar()
print("botão:", M.painel_info.botoes_cond["atordoado"].text())
M.painel_combate.iniciar("todos"); w(200)
for p in M.servidor.combate.participantes: p["ini"] = 20 if p["nome"]=="Ogro" else 5
M.servidor.atualizar_combate()
M.painel_combate.proximo(); w(200)   # começa: vez do ogro
print("vez:", M.servidor.combate.participante(M.servidor.combate.vez)["nome"], "| player vê dur:", tok("Ogro").info["condicoes"].get("dur"))
M.painel_combate.proximo(); w(300)   # fim do turno do ogro
print("após turno do ogro:", ogro.info["condicoes"]["v"], ogro.info["condicoes"].get("dur"), "| status:", M.statusBar().currentMessage())

print("== RASTRO DO TURNO")
print("vez:", M.servidor.combate.participante(M.servidor.combate.vez)["nome"], "origem:", aelar.origem_turno)
P.cliente.mover(aelar.uid, 3*CELULA, 4*CELULA); w(900)
print("player origem:", tok("Aelar").origem_turno, "| mestre centro:", aelar.centro_cena())
M.visao.centerOn(aelar); w(100); M.visao.grab().save("extras_rastro.png")
P.visao.centerOn(tok("Aelar")); w(100); P.visao.grab().save("extras_player.png")

print("== RÉGUA")
v=M.visao; vp=v.viewport()
QTest.keyPress(v, Qt.Key.Key_M); w(30)
p0=v.mapFromScene(QPointF(0,0)); p1=v.mapFromScene(QPointF(6*CELULA,8*CELULA))
QTest.mousePress(vp, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p0)
QTest.mouseMove(vp, p1); w(50)
print("régua:", v._regua is not None, "medida m:", round(((v._regua[1]-v._regua[0]).x()**2+(v._regua[1]-v._regua[0]).y()**2)**0.5/CELULA,2))
v.grab().save("extras_regua.png")
QTest.mouseRelease(vp, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p1)
QTest.keyRelease(v, Qt.Key.Key_M); w(30)
print("régua some:", v._regua is None, "| token não moveu:", aelar.scenePos())

print("== AUTO-SAVE")
pasta=tempfile.mkdtemp(); M.caminho_cena=os.path.join(pasta,"Teste.taverna")
M.salvar(); c.marcar_modificada(True)
aelar.definir_info("notas","depois do save")
M.salvar_automatico()
print("arquivos:", sorted(os.listdir(pasta)), "| título sem •:", "•" not in M.windowTitle())
M.caminho_cena=None; M.cena.nome_aventura="Aventura X"; c.marcar_modificada(True)
M.caminho_da_aventura = lambda nome: os.path.join(pasta, nome+".taverna")
M.salvar_automatico()
print("sem nome:", sorted(os.listdir(pasta)), "| continua marcado não salvo:", "•" in M.windowTitle(), "| continuar abre:", os.path.basename(M.config.value("ultima_cena")))
M.config.setValue("ultima_cena", "")
print("FIM")
