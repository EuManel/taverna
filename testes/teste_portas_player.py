import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.environ["QT_QPA_PLATFORM"]="offscreen"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
from taverna.config import CELULA
from taverna.mesa.portas import PortaItem
from taverna.mesa.linha_de_visao import obstaculos
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
M=JanelaMestre(); M.resize(1400,850); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
c=M.cena
c.criar_sala(QPointF(-4*CELULA,-3*CELULA), QPointF(4*CELULA,3*CELULA))
porta=c.colocar_porta(QPointF(4*CELULA, 0))
c.tipo_porta="janela"; jan=c.colocar_porta(QPointF(0, -3*CELULA))
c.tipo_porta="janela_persiana"; pers=c.colocar_porta(QPointF(0, 3*CELULA))
c.tipo_porta="secreta"; sec=c.colocar_porta(QPointF(-4*CELULA, 0))
print("tipos:", porta.tipo, jan.tipo, pers.tipo, sec.tipo, "| secreta jogadores abrem?", sec.jogadores_abrem)
print("obstáculos (janela de vidro não bloqueia):", len(obstaculos(c.paredes.segmentos, [porta, jan, pers, sec])), "de", len(obstaculos(c.paredes.segmentos, [])) + 3)
aelar=c.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Manel"), QPointF(2.5*CELULA,-0.5*CELULA))
assert M.servidor.abrir(7797)
P=JanelaPlayer(); P.resize(1100,750); P.show(); P.nome,P.ip,P.porta="Manel","127.0.0.1",7797
P._ja_entrou=False; P._primeiro_estado=True; P.cliente.conectar(P.ip,P.porta,P.nome); w(900)
avisos=[]; P.cliente.aviso_recebido.connect(avisos.append)
pp=P.cena.itens[porta.uid]
print("player sabe se está trancada?", "trancada" in str(M.servidor._estado_completo()[0]))
P.cena.porta_duplo_clique(pp); w(400); print("abrir perto:", porta.aberta)
P.cena.porta_duplo_clique(pp); w(400); print("fechar:", porta.aberta)
porta.trancada=True; P.cena.porta_duplo_clique(pp); w(400); print("trancada:", porta.aberta, avisos[-1])
porta.trancada=False; porta.jogadores_abrem=False; porta.mudou(); w(300)
P.cena.porta_duplo_clique(pp); w(300); print("mestre não deixa ->", porta.aberta, "| (player nem pede)", len(avisos))
porta.jogadores_abrem=True; porta.mudou(); w(300)
P.cena.porta_duplo_clique(P.cena.itens[jan.uid]); w(300); print("janela longe:", jan.aberta, avisos[-1])
aelar.setPos(-0.5*CELULA, -2.5*CELULA); w(400)
P.cena.porta_duplo_clique(P.cena.itens[jan.uid]); w(500); print("janela perto:", jan.aberta)
print("--- histórico:"); print("\n".join(l for l in M.painel_historico.texto.toPlainText().splitlines() if "🚪" in l or "⚠" in l))
pers.alternar(); w(600)
M.visao.centerOn(QPointF(0,0)); c.clearSelection(); w(200); M.visao.grab().save("janelas.png")
print("FIM")
