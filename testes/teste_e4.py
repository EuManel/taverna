import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PyQt6.QtCore import QPointF, Qt, QPoint
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.config import CELULA
from taverna.mesa.token import TokenItem
from taverna.mesa.portas import PortaItem
app=QApplication(sys.argv); app.setStyle("Fusion")
w=QTest.qWait
M=JanelaMestre(); M.resize(1400,860); M.show()
c=M.cena; v=M.visao; vp=v.viewport()
c.criar_camadas_padrao(); c.nome_aventura="Viva"; M.caminho_cena=os.path.abspath("viva.taverna"); M.mostrar_mesa(); w(50)
# --- undo/redo
c.material_chao="grama"; c.pincel=2
c.comecar_pincelada(QPointF(0,0)); c.continuar_pincelada(QPointF(200,0)); c.terminar_pincelada()
c.adicionar_parede(QPointF(0,-64), QPointF(256,-64))
c.criar_sala(QPointF(0,128), QPointF(256,384))
porta=c.colocar_porta(QPointF(128,-64))
print("hist:", len(c._historico), "ops", len(c.terreno.ops), "seg", len(c.paredes.segmentos), "portas", len(c.camada_por_tipo("paredes").itens()))
M.desfazer(); print("undo1 portas:", len(c.camada_por_tipo("paredes").itens()), "seg", len(c.paredes.segmentos))
M.desfazer(); print("undo2 (sala) ops:", len(c.terreno.ops), "seg", len(c.paredes.segmentos))
M.refazer(); M.refazer(); print("redo2 portas:", len(c.camada_por_tipo("paredes").itens()), "seg", len(c.paredes.segmentos))
for _ in range(10): M.desfazer()
print("tudo desfeito:", len(c.terreno.ops), len(c.paredes.segmentos))
for _ in range(10): M.refazer()
print("tudo refeito:", len(c.terreno.ops), len(c.paredes.segmentos), len(c.camada_por_tipo("paredes").itens()))
# --- door animation
porta=c.camada_por_tipo("paredes").itens()[0]
porta.alternar(); w(100); meio=porta._prog; w(400)
print("anim: meio", round(meio,2), "fim", porta._prog)
# --- network smooth + cursors
c.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Manel"), QPointF(64,256))
assert M.servidor.abrir(7784)
def player(nome):
    P=JanelaPlayer(); P.resize(900,600); P.show(); P.nome,P.ip,P.porta=nome,"127.0.0.1",7784
    P.cliente.conectar(P.ip,P.porta,P.nome); return P
P1=player("Manel"); P2=player("Bia"); w(800)
tok=[t for t in c.itens_do_usuario() if isinstance(t,TokenItem)][0]
t2=P2.cena.itens[tok.uid]
# P1 moves token programmatically like a drag: send moves
P1.cliente.mover(tok.uid, 640, 256); w(30)
print("mestre logo após (deslizando):", tok.pos().x())
w(500); print("mestre final:", tok.pos().x(), "| P2 final:", t2.pos().x())
# porta animada no player
pp=P2.cena.itens[porta.uid]; porta.alternar(); w(150); print("porta P2 prog meio:", round(pp._prog,2)); w(400); print("porta P2 fim:", pp._prog, pp.aberta)
# cursors
P1._enviar_cursor(300.0, 200.0); w(300)
print("cursores mestre:", list(c.cursores.itens), "P2:", list(P2.cena.cursores.itens))
M.servidor.cursor_mestre(100.0, 100.0); w(300)
print("P1 vê:", list(P1.cena.cursores.itens), "P2 vê:", list(P2.cena.cursores.itens))
P1._enviar_cursor(None, None); w(300); print("P1 saiu do mapa -> P2 vê:", list(P2.cena.cursores.itens))
P1._enviar_cursor(400.0, 260.0); M.servidor.cursor_mestre(200.0, 300.0); w(300)
P2.visao.zoom_100(); P2.visao.centerOn(200,150); w(100); P2.grab().save("e4_player.png")
v.zoom_100(); v.centerOn(200,150); w(100); M.grab().save("e4_mestre.png")
P1.close(); w(400); print("após P1 sair, P2 vê:", list(P2.cena.cursores.itens), "mestre:", list(c.cursores.itens))
c.marcar_modificada(False); print("FIM")
