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

M=JanelaMestre(); M.resize(1400,860); M.show()
c=M.cena
M._carregar_imagem("mapa_teste.png", QPointF(0,0))
mapa=c.itens_do_usuario()[0]; mapa.definir_tamanho_metros(16,12); mapa.setPos(-8*CELULA,-6*CELULA)
aelar=c.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Manel"), QPointF(-3*CELULA,-2*CELULA))
bruna=c.adicionar_token(dict(nome="Lyra",tipo="jogador",cor="#5a3f6b",tamanho=1,imagem=None,dono="Bia"), QPointF(-1*CELULA,-2*CELULA))
ogro=c.adicionar_token(dict(nome="Ogro",tipo="criatura",cor="#6e2a2f",tamanho=2,imagem=None), QPointF(2.5*CELULA,1.5*CELULA))
espiao=c.adicionar_token(dict(nome="Espião",tipo="npc",cor="#3b5470",tamanho=1,imagem=open("mapa_teste.png","rb").read()), QPointF(4*CELULA,-3*CELULA))
c.definir_item_visivel(espiao, False)  # emboscada!
print("ips:", M.servidor.enderecos_locais())
assert M.servidor.abrir(7781); M._atualizar_jogadores()

def player(nome):
    P=JanelaPlayer(); P.resize(1100,750); P.show()
    P.nome, P.ip, P.porta = nome, "127.0.0.1", 7781
    P._ja_entrou=False; P._primeiro_estado=True
    P.cliente.conectar(P.ip, P.porta, P.nome)
    return P
P1=player("manel"); P2=player("Bia")
w(800)
print("jogadores:", M.servidor.nomes(), "|", M.lbl_taverna.text())
def nomes(P): return sorted((i.nome if isinstance(i,TokenItem) else "MAPA") for i in P.cena.itens.values())
print("P1 vê:", nomes(P1), "meus:", [t.nome for t in P1.cena.meus_tokens()])
print("P2 vê:", nomes(P2), "meus:", [t.nome for t in P2.cena.meus_tokens()])
print("P1 imagens recebidas:", len(P1.cliente.imagens))

# duplicate name
from taverna.rede.cliente import ClienteRede
C3=ClienteRede(); motivos=[]; C3.recusado.connect(motivos.append)
C3.conectar("127.0.0.1",7781,"BIA"); w(500)
print("dup recusado:", motivos)

# P1 drags own token
P1.visao.zoom_100(); P1.visao.centerOn(0,0); w(100)
t=[x for x in P1.cena.meus_tokens()][0]
p=P1.visao.mapFromScene(t.mapToScene(QPointF(32,32)))
vp=P1.visao.viewport()
QTest.mousePress(vp, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p)
for k in range(1,6): QTest.mouseMove(vp, p+QPoint(20*k, 10*k)); w(30)
QTest.mouseRelease(vp, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p+QPoint(100,50))
w(400)
print("P1 token:", t.scenePos(), "mestre Aelar:", aelar.scenePos())
t2=[x for x in P2.cena.itens.values() if isinstance(x,TokenItem) and x.nome=="Aelar"][0]
print("P2 vê Aelar em:", t2.scenePos())

# P1 tries to move Ogro (not his) — UI blocked; also forged msg
og1=[x for x in P1.cena.itens.values() if isinstance(x,TokenItem) and x.nome=="Ogro"][0]
print("ogro movable on P1:", bool(og1.flags() & og1.GraphicsItemFlag.ItemIsMovable))
P1.cliente.mover(ogro.uid, 0, 0); P1.cliente.mover(espiao.uid, 0,0); w(300)
print("ogro mestre (deve ficar igual):", ogro.scenePos(), "espiao:", espiao.scenePos())

# mestre reveals espiao and moves ogro
c.definir_item_visivel(espiao, True); ogro.setPos(5*CELULA, 5*CELULA); w(400)
print("P2 vê após revelar:", nomes(P2), "imgs P2:", len(P2.cliente.imagens))
og2=[x for x in P2.cena.itens.values() if isinstance(x,TokenItem) and x.nome=="Ogro"][0]
print("P2 ogro:", og2.scenePos())
# hide whole creature layer
c.definir_visivel(c.camada_por_tipo("criaturas"), False); w(300)
print("P2 com camada escondida:", nomes(P2))
c.definir_visivel(c.camada_por_tipo("criaturas"), True); w(300)
# snap on: P2 move
c.definir_snap(True); w(200)
P2.visao.zoom_100(); P2.visao.centerOn(0,0); w(100)
ly=P2.cena.meus_tokens()[0]
p=P2.visao.mapFromScene(ly.mapToScene(QPointF(32,32))); vp=P2.visao.viewport()
QTest.mousePress(vp, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p)
QTest.mouseMove(vp, p+QPoint(30,10)); w(30); QTest.mouseMove(vp, p+QPoint(75,45)); w(30)
QTest.mouseRelease(vp, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p+QPoint(75,45)); w(400)
print("Lyra mestre (snap):", bruna.scenePos())
# edit token rename + reassign
aelar.atualizar("Aelar, o Bravo","jogador","#3f6b4a",1,None,"Bia"); c.camadas_mudaram.emit(); w(400)
print("P1 meus após trocar dono:", [x.nome for x in P1.cena.meus_tokens()], "P2 meus:", sorted(x.nome for x in P2.cena.meus_tokens()))
print("lista jogadores:", [M.lista_jogadores.item(i).text() for i in range(M.lista_jogadores.count())])
M.grab().save("rede_mestre.png"); P2.visao.enquadrar_tudo(); w(100); P2.grab().save("rede_player.png")
# disconnect & reconnect
M.servidor.fechar(); w(400)
print("P1 faixa:", P1.faixa.isVisible(), P1.faixa.text(), "reconectando:", P1._reconectar.isActive())
M.servidor.abrir(7781); w(3800)
print("P1 voltou:", P1.cliente.dentro, "jogadores:", M.servidor.nomes())
print("FIM")
