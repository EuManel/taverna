"""(v0.70) 🎥 Câmera livre, etapa 1: GIRAR e INCLINAR a mesa (bússola no canto ou Alt+arrastar).
Travada = reto de cima, exatamente como antes. Inclinada: o chão em perspectiva, e paredes, portas, objetos e tokens
"em pé" (camera3d com a projeção de verdade). O horizonte nunca entra na tela; afastando muito volta a ficar de cima."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QPainter, QImage
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

app = QApplication(sys.argv[:1])
from taverna import seguranca
erros = []
seguranca.registrar_erro = lambda t: erros.append(t)
from taverna.graficos import graficos
graficos().definir("alto")
from taverna.config import CELULA as C
from taverna.mesa import camera3d
from taverna.ui.janela_mestre import JanelaMestre

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")

print("== contas da câmera: inclinação 0 = igual a antes")
img = QImage(1000, 800, QImage.Format.Format_ARGB32)
p = QPainter(img)
p.translate(500, 400)
p.scale(0.8, 0.8)
cam = camera3d.Camera(p)
assert not cam.inclinada
q = cam.projetar(QPointF(100, 50), 2 * C)
f = cam.H / (cam.H - 2 * C * 0.8)
esperado = QPointF(500 + 80 * f, 400 + 40 * f)
assert abs(q.x() - esperado.x()) < 1e-6 and abs(q.y() - esperado.y()) < 1e-6
t = cam.transformacao_topo(2 * C)
assert abs(t.map(QPointF(100, 50)).x() - q.x()) < 1e-6
p.end()
H = camera3d.homografia(500, 400, 1440, math.radians(40))
assert abs(H.map(QPointF(500, 400)).x() - 500) < 1e-6 and abs(H.map(QPointF(500, 400)).y() - 400) < 1e-6
assert H.map(QPointF(500, 100)).x() == 500 and H.map(QPointF(600, 100)).x() - 500 < 100   # o longe encolhe

M = JanelaMestre(); M.resize(1400, 900); M.show(); M.mostrar_mesa(); QTest.qWait(80)
c, v = M.cena, M.visao
c.criar_sala(QPointF(-6 * C, -4 * C), QPointF(6 * C, 4 * C))
c.tipo_porta = "madeira"
c.colocar_porta(QPointF(0, 4 * C))
c.adicionar_token(dict(nome="Aelar", tipo="jogador", cor="#3f6b4a", tamanho=1, imagem=None, dono="Manel"), QPointF(0, 0))
c.colocar_prop("mesa", QPointF(2 * C, -1 * C))
c.clearSelection()
v.definir_zoom(0.8)
v.centerOn(QPointF(0, 0))
QTest.qWait(100)
meio = v.viewport().rect().center()

print("== travada: reto de cima, a bússola solta")
assert not v.camera_livre and v.viewportTransform().isAffine()
v.definir_camera(30, 40)                 # travada: guarda, mas não aplica
assert v.viewportTransform().isAffine() and v.inclinacao_efetiva() == 0
v.bussola.mousePressEvent(type("E", (), {"position": lambda s: QPointF(10, 10), "accept": lambda s: None})())
assert v.camera_livre, "o cadeado da bússola solta a câmera"
QTest.qWait(50)
assert not v.viewportTransform().isAffine()

print("== inclinada: centro no lugar, limite do horizonte, clique cai no chão certo")
v.definir_camera(0, 999)
assert v._cam_incl == camera3d.INCLINACAO_MAX
ctr = v.mapToScene(meio)
assert abs(ctr.x()) < 3 and abs(ctr.y()) < 3, ctr
alvo = QPointF(3 * C, 2 * C)
tela = v.mapFromScene(alvo)
volta = v.mapToScene(tela)
assert (volta - alvo).manhattanLength() < 3, (volta, alvo)       # clique → ponto certo da mesa
cima = v.mapToScene(QPoint(meio.x(), 0))
baixo = v.mapToScene(QPoint(meio.x(), v.viewport().height() - 1))
assert (meio.y() - 0) < ((ctr.y() - cima.y()) * 0.8) * 3        # longe (em cima) mostra mais chão
assert ctr.y() - cima.y() > baixo.y() - ctr.y(), "em cima é o longe (mais chão por pixel)"
QTest.qWait(150)
v.grab().save(os.path.join(SAIDA, "camera_inclinada.png"))

print("== o que é grande (grid, paredes 3D) continua aparecendo inclinado")
pintou = {}
from taverna.mesa import altura3d, grid
orig_g, orig_a = grid.GridItem.paint, altura3d.ParedesAltas.paint


def _pg(s, *a):
    pintou["grid"] = 1
    orig_g(s, *a)


def _pa(s, *a):
    pintou["paredes"] = 1
    orig_a(s, *a)


grid.GridItem.paint, altura3d.ParedesAltas.paint = _pg, _pa
v.viewport().update()
QTest.qWait(150)
grid.GridItem.paint, altura3d.ParedesAltas.paint = orig_g, orig_a
print("   pintou:", pintou)
assert pintou.get("grid") and pintou.get("paredes")

print("== arrastar a visão inclinada: o ponto embaixo do mouse acompanha")
a = QPoint(meio.x() + 100, meio.y() + 60)
antes = v.mapToScene(a)
QTest.mousePress(v.viewport(), Qt.MouseButton.MiddleButton, Qt.KeyboardModifier.NoModifier, a)
QTest.mouseMove(v.viewport(), QPoint(a.x() + 80, a.y() - 50))
QTest.mouseRelease(v.viewport(), Qt.MouseButton.MiddleButton, Qt.KeyboardModifier.NoModifier, QPoint(a.x() + 80, a.y() - 50))
depois = v.mapToScene(QPoint(a.x() + 80, a.y() - 50))
print("   desvio:", round((depois - antes).manhattanLength(), 1))
assert (depois - antes).manhattanLength() < 0.12 * C

print("== Alt+arrastar gira e inclina")
v.definir_camera(0, 20)
QTest.mousePress(v.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.AltModifier, meio)
QTest.mouseMove(v.viewport(), QPoint(meio.x() + 100, meio.y() + 40))
QTest.mouseRelease(v.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.AltModifier, QPoint(meio.x() + 100, meio.y() + 40))
print("   giro", round(v._cam_giro), "incl", round(v._cam_incl))
assert 20 < v._cam_giro < 60 and v._cam_incl > 25

print("== afastando muito volta a ficar de cima (cidade/mundo)")
v.definir_zoom(0.25)
assert v.inclinacao_efetiva() == 0 and v.viewportTransform().isAffine() is False or v.inclinacao_efetiva() == 0
v.definir_zoom(0.8)
assert v.inclinacao_efetiva() > 0

print("== desenha tudo sem erro (girada + inclinada)")
v.definir_camera(35, 50)
QTest.qWait(200)
v.grab().save(os.path.join(SAIDA, "camera_livre.png"))
print("== volta pro reto de cima")
v.camera_de_cima()
assert v.viewportTransform().isAffine() and v._cam_giro == 0
assert camera3d._ESTADO.get("visivel") is None
print("   erros:", erros[:2])
assert not erros, erros
print("FIM")
sys.stdout.flush()
os._exit(0)
