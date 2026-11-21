import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
from taverna.config import CELULA as C
from taverna.mesa.token import TokenItem
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
M=JanelaMestre(); M.resize(1400,860); M.show(); c=M.cena
c.criar_camadas_padrao(); c.nome_aventura="Névoa"; c.nome_aba="Masmorra"; M._recarregar_abas(); M.mostrar_mesa(); w(50)
# two rooms connected by a door; a corridor
c.material_chao="pedra"; c.material_parede="pedra"
c.criar_sala(QPointF(0,0),QPointF(6*C,5*C)); c.criar_sala(QPointF(6*C,0),QPointF(12*C,5*C))
c.material_chao="terra"; c.criar_sala(QPointF(0,5*C),QPointF(12*C,7*C))
c.tipo_porta="madeira"; porta=c.colocar_porta(QPointF(6*C,2.5*C))
c.tipo_porta="madeira"; porta2=c.colocar_porta(QPointF(3*C,5*C))
c.material_parede="vidro"; c.adicionar_parede(QPointF(9*C,5*C),QPointF(9*C,7*C))
heroi=c.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Bia"), QPointF(2*C,2.5*C))
heroi.definir_visao(12, 120, 0)
ogro=c.adicionar_token(dict(nome="Ogro",tipo="criatura",cor="#6e2a2f",tamanho=2,imagem=None), QPointF(9*C,2.5*C))
goblin=c.adicionar_token(dict(nome="Goblin",tipo="criatura",cor="#4a6e2f",tamanho=1,imagem=None), QPointF(4.5*C,2.5*C))
rato=c.adicionar_token(dict(nome="Rato",tipo="criatura",cor="#666",tamanho=1,imagem=None), QPointF(0.5*C,4.5*C))
M.a_nevoa.setChecked(True); M.a_cones.setChecked(True)
assert M.servidor.abrir(7787)
P=JanelaPlayer(); P.resize(1000,700); P.show(); P.nome,P.ip,P.porta="Bia","127.0.0.1",7787; P.cliente.conectar("127.0.0.1",7787,"Bia"); w(800)
def vejo(): return sorted(i.nome for i in P.cena.itens.values() if isinstance(i,TokenItem))
print("porta fechada, olhando p/ direita:", vejo())
porta.alternar(); w(400); print("porta aberta:", vejo())
heroi.definir_visao(direcao=180); w(400); print("olhando p/ esquerda:", vejo())
heroi.definir_visao(abertura=360); w(400); print("visão 360°:", vejo())
heroi.definir_visao(alcance=0, abertura=0); w(400); print("cegueira:", vejo())
heroi.definir_visao(12, 120, 0); w(400)
# player rotates with E
P.girar(90); w(400); print("player girou +90 -> mestre dir:", heroi.direcao, vejo())
heroi.definir_visao(pode_girar=False); w(300); P.girar(90); w(300); print("travado -> mestre dir:", heroi.direcao)
heroi.definir_visao(direcao=0, pode_girar=True); w(400)
print("explorado células:", len(P.cena.nevoa.explorado))
P.visao.zoom_100(); P.visao.centerOn(6*C,3.5*C); w(100); P.grab().save("e5_player.png")
M.visao.zoom_100(); M.visao.definir_zoom(0.9); M.visao.centerOn(6*C,3.5*C); w(100); M.grab().save("e5_mestre.png")
# fog off
M.a_nevoa.setChecked(False); w(400); print("névoa desligada:", vejo(), "fog visível:", P.cena.nevoa.isVisible())
# save/load keeps vision
M.caminho_cena=os.path.abspath("nevoa.taverna"); M.salvar(); M.abrir_cena(M.caminho_cena)
t=[x for x in M.cena.itens_do_usuario() if getattr(x,"nome","")=="Aelar"][0]; print("salvo:", t.visao_alcance, t.visao_abertura, t.direcao, t.pode_girar, M.cena.nevoa_ativa)
for x in M.cenas: x.marcar_modificada(False)
print("FIM")
