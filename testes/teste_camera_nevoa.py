"""(v0.71) 🎥 Câmera livre, etapa 2: NÉVOA e LUZ com a câmera inclinada (tela do JOGADOR).
A névoa de guerra é "tinta no chão": inclinada, o alto das paredes caía em cima do chão de trás e entregava
sala não explorada. Agora o 3D consulta a névoa: parede conhecida = chão de QUALQUER lado dela já visto, em
pedaços de ~1 m; topo de cada parede com a névoa dos lados dela; porta/objeto escondidos não aparecem.
Neblina e gás volumétricos: o raio de cada pixel sai do pé da câmera (inclinada fica atrás e mais baixa)."""
import os
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

app = QApplication(sys.argv[:1])
from taverna import seguranca
erros = []
seguranca.registrar_erro = lambda t: erros.append(t)
from taverna.graficos import graficos
graficos().definir("alto")
from taverna.config import CELULA as C
from taverna.mesa import camera3d, neblina
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")

print("== neblina/gás: a conta do raio não depende mais do centro da tela")
assert "min(0.95, z * escala / H)" in neblina.FRAG
from taverna.mesa import fluidos_desenho
assert "min(0.95, z * escala / H)" in fluidos_desenho.FRAG_GAS

s = socket.socket(); s.bind(("127.0.0.1", 0)); porta = s.getsockname()[1]; s.close()
M = JanelaMestre(); M.resize(900, 600); M.show(); M.mostrar_mesa(); QTest.qWait(80)
c = M.cena
c.criar_sala(QPointF(-7 * C, -5 * C), QPointF(0, 5 * C))
c.criar_sala(QPointF(0, -5 * C), QPointF(7 * C, 5 * C))
c.tipo_porta = "madeira"
c.colocar_porta(QPointF(0, 0))
c.colocar_prop("barril", QPointF(4 * C, 2 * C))
c.adicionar_token(dict(nome="Aelar", tipo="jogador", cor="#3f6b4a", tamanho=1, imagem=None, dono="Manel"),
                  QPointF(-3.5 * C, 1.5 * C))
c.colocar_luz(QPointF(-3 * C, -1 * C))
c.definir_ambiente("penumbra")
c.definir_nevoa(True)
c.clearSelection()
assert M.servidor.abrir(porta)
P = JanelaPlayer(); P.resize(1300, 800); P.show()
P.nome, P.ip, P.porta = "Manel", "127.0.0.1", porta
P._ja_entrou = False; P._primeiro_estado = True
P.cliente.conectar(P.ip, P.porta, P.nome)
for _ in range(80):
    QTest.qWait(100)
    if P.cena.nevoa.ativa and P.cena.paredes is not None and P.cena.paredes.segmentos:
        break
QTest.qWait(600)
v = P.visao
nv = camera3d.nevoa_da_cena(P.cena)
assert nv is not None, "a névoa do jogador tem que estar ligada"
assert camera3d.nevoa_da_cena(M.cena) is None          # o mestre não tem névoa no 3D
v.definir_zoom(0.8)
v.centerOn(QPointF(0, 0))
v.definir_camera(25, 50, livre=True)
QTest.qWait(300)
v.viewport().update()
QTest.qWait(300)

print("== parede conhecida x parede da sala não explorada")
from PyQt6.QtGui import QImage, QPainter
img = QImage(v.viewport().size(), QImage.Format.Format_ARGB32)
p = QPainter(img)
p.setWorldTransform(v.viewportTransform())
cam = camera3d.Camera(p)
p.end()
# a parede do meio, bem na frente do jogador (o cone padrão é de 60° pra frente — v0.71)
vista = camera3d.nevoa_da_parede(nv, cam, QPointF(0, 1.5 * C), QPointF(0, 2.5 * C), 1, 0)
# parede do fundo da sala ao lado (x = 7), que ele nunca viu
escondida = camera3d.nevoa_da_parede(nv, cam, QPointF(7 * C, -2 * C), QPointF(7 * C, 2 * C), 1, 0)
print(f"   vista {vista:.2f} · escondida {escondida:.2f}")
assert vista < 0.9 and escondida >= 0.97

print("== na tela: onde estaria o topo da parede escondida, só névoa")
v.grab().save(os.path.join(SAIDA, "camera_nevoa.png"))
foto = v.grab().toImage()
cor_nevoa = P.cena.nevoa.cor
for y in (-3, 0, 3):
    q = cam.projetar(QPointF(7 * C, y * C), camera3d.ALTURA_PAREDE)
    if 0 <= q.x() < foto.width() and 0 <= q.y() < foto.height():
        px = foto.pixelColor(int(q.x()), int(q.y()))
        dif = abs(px.red() - cor_nevoa.red()) + abs(px.green() - cor_nevoa.green()) + abs(px.blue() - cor_nevoa.blue())
        print("   topo escondido em", (int(q.x()), int(q.y())), "diferença da névoa:", dif)
        assert dif < 30, "o topo da parede da sala não explorada apareceu"

print("== de cima continua igual (sem névoa no corpo 3D vazando)")
v.camera_de_cima()
QTest.qWait(200)
print("   erros:", erros[:2])
assert not erros, erros
print("FIM")
sys.stdout.flush()
os._exit(0)
