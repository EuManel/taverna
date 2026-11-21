"""(v0.58) 📣 "Todos olhem pra cá": a câmera do jogador desliza até o ponto (no zoom do mestre), trava por uns
segundos se o mestre pediu, quem está em outro andar só recebe aviso, e vai pro histórico."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.config import CELULA
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS

app = QApplication(sys.argv)
app.setStyle("Fusion")
app.setStyleSheet(QSS)
w = QTest.qWait

M = JanelaMestre()
M.resize(1300, 800)
M.show()
M.cena.criar_camadas_padrao()
M.mostrar_mesa()
w(50)
c = M.cena
c.criar_sala(QPointF(-10 * CELULA, -6 * CELULA), QPointF(10 * CELULA, 6 * CELULA))
c.adicionar_token(dict(nome="Aelar", tipo="jogador", cor="#3f6b4a", tamanho=1, imagem=None, dono="Manel"),
                  QPointF(-8 * CELULA, -4 * CELULA))
# antes de abrir a taverna: não dá
pode, motivo = M._pode_chamar_atencao()
print("taverna fechada:", pode, "|", motivo)
assert not pode
assert M.servidor.abrir(7871)
P = JanelaPlayer()
P.resize(1100, 700)
P.show()
P.nome, P.ip, P.porta = "Manel", "127.0.0.1", 7871
P._ja_entrou = False
P._primeiro_estado = True
P.cliente.conectar(P.ip, P.porta, P.nome)
w(900)
assert P.cliente.dentro

alvo = QPointF(7 * CELULA, 4 * CELULA)
M.visao.definir_zoom(1.6)
P.visao.definir_zoom(0.7)
P.visao.centerOn(-8 * CELULA, -4 * CELULA)
w(100)
M.chamar_atencao(alvo, travar=3)
w(1300)
centro = P.visao.centro_da_visao()
dist = ((centro.x() - alvo.x()) ** 2 + (centro.y() - alvo.y()) ** 2) ** 0.5
print(f"câmera do jogador: centro=({centro.x():.0f},{centro.y():.0f}) alvo=({alvo.x():.0f},{alvo.y():.0f}) "
      f"dist={dist:.1f} | zoom jogador={P.visao.escala:.2f} mestre={M.visao.escala:.2f}")
assert dist < 6, dist
assert abs(P.visao.escala - M.visao.escala) < 0.05
assert P.visao.camera_travada(), "a câmera devia estar travada"
# travada: Home (ver tudo) e arrastar não mexem
antes = P.visao.centro_da_visao()
P.visao.enquadrar_tudo()
P.centralizar_meu_token()
w(50)
depois = P.visao.centro_da_visao()
print("travada — tentou mexer, a câmera ficou:", abs(antes.x() - depois.x()) < 1 and abs(antes.y() - depois.y()) < 1)
assert abs(antes.x() - depois.x()) < 1 and abs(antes.y() - depois.y()) < 1
w(3200)
assert not P.visao.camera_travada(), "devia ter destravado"
P.centralizar_meu_token()
print("destravou e voltou a mexer:", P.visao.centro_da_visao() != depois)

# sem trava: não trava
M.chamar_atencao(QPointF(0, 0), travar=0)
w(1200)
assert not P.visao.camera_travada()

# jogador em OUTRO andar/aba: só recebe o aviso
from taverna.mesa.cena import MesaCena
outra = MesaCena()
outra.nome_aba = "Esgoto"
avisos = []
P.cliente.aviso_recebido.connect(avisos.append)
n = M.servidor.olhar_aqui(outra, 10, 10, 1.0, 0)
w(400)
print("outro andar — levados:", n, "| aviso:", avisos[-1] if avisos else None)
assert n == 0 and avisos and "Esgoto" in avisos[-1]

hist = M.painel_historico.texto.toPlainText()
print("histórico:", [l for l in hist.splitlines() if "atenção" in l][-2:])
assert "chamou a atenção de todos pra cá (câmera travada 3 s)" in hist
print("FIM")   # (sem M.close(): a mesa mudou e ele abriria o "quer salvar?")
sys.stdout.flush()
os._exit(0)
