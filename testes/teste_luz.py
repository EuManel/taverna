import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PyQt6.QtCore import QPointF
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
c.criar_camadas_padrao(); c.nome_aventura="Luz"; c.nome_aba="Cripta"; M._recarregar_abas(); M.mostrar_mesa(); w(50)
print("camadas:", [x.nome for x in c.camadas])
c.material_chao="pedra"; c.material_parede="pedra"
c.criar_sala(QPointF(0,0),QPointF(7*C,6*C)); c.criar_sala(QPointF(7*C,0),QPointF(14*C,6*C))
c.tipo_porta="madeira"; porta=c.colocar_porta(QPointF(7*C,3*C))
c.tipo_luz="tocha"; tocha=c.colocar_luz(QPointF(2*C,1*C))
c.tipo_luz="cristal"; cristal=c.colocar_luz(QPointF(12*C,5*C))
heroi=c.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Bia"), QPointF(3.5*C,3.5*C))
heroi.definir_visao(20, 360, 0)
ogro=c.adicionar_token(dict(nome="Ogro",tipo="criatura",cor="#6e2a2f",tamanho=1,imagem=None), QPointF(10.5*C,2.5*C))
morcego=c.adicionar_token(dict(nome="Morcego",tipo="criatura",cor="#444",tamanho=1,imagem=None), QPointF(12*C,4.5*C))
rato=c.adicionar_token(dict(nome="Rato",tipo="criatura",cor="#666",tamanho=1,imagem=None), QPointF(5.5*C,5.5*C))
M.a_nevoa.setChecked(True); M._ambiente("escuro"); w(100)
assert M.servidor.abrir(7788)
P=JanelaPlayer(); P.resize(1100,700); P.show(); P.nome,P.ip,P.porta="Bia","127.0.0.1",7788; P.cliente.conectar("127.0.0.1",7788,"Bia"); w(800)
def vejo(): return sorted(i.nome for i in P.cena.itens.values() if isinstance(i,TokenItem))
print("escuro, porta fechada (tocha na sala A, cristal na sala B):", vejo())
porta.alternar(); w(400); print("porta aberta:", vejo())
tocha.alternar(); w(400); print("tocha apagada:", vejo())
heroi.definir_visao(escuro=4); w(400); print("visão no escuro 4m:", vejo())
heroi.definir_visao(escuro=0); tocha.alternar(); w(400)
M._ambiente("penumbra"); w(400); print("penumbra:", vejo())
M._ambiente("escuro"); w(400)
P.visao.zoom_100(); P.visao.definir_zoom(0.8); P.visao.centerOn(7*C,3*C); w(150); P.grab().save("luz_player.png")
M.visao.definir_zoom(0.8); M.visao.centerOn(7*C,3*C); c.clearSelection(); w(150); M.grab().save("luz_mestre.png")
# nevoa off, escuro: player sees darkness overlay
M.a_nevoa.setChecked(False); w(400); print("sem névoa:", vejo(), "overlay so_brilho:", P.cena.luz_overlay.so_brilho)
P.grab().save("luz_player_sem_nevoa.png")
M.caminho_cena=os.path.abspath("luz.taverna"); M.salvar(); M.abrir_cena(M.caminho_cena); w(100)
print("salvo/recarregado: ambiente", M.cena.luz_ambiente, "luzes", len(M.cena.itens_de_luz()))
for x in M.cenas: x.marcar_modificada(False)
print("FIM")
