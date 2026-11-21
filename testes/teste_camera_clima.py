"""(v0.72) 🎥 Câmera livre, etapa 3: EFEITOS e CLIMA com a câmera girada/inclinada.
O clima (chuva, neve, cinzas, folhas, raio) tinha a sua própria câmera "de cima": agora usa a mesma da mesa —
as partículas acompanham o mapa também no GIRO, nascem no chão que aparece (inclinada vai bem mais longe) e são
projetadas com a perspectiva; o respingo fica deitado no chão. Impactos e lançamentos já usavam a camera3d."""
import math
import os
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
from taverna.ui.janela_mestre import JanelaMestre

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")
M = JanelaMestre(); M.resize(1400, 900); M.show(); M.mostrar_mesa(); QTest.qWait(80)
c, v, cl = M.cena, M.visao, M.clima_overlay
c.criar_sala(QPointF(-7 * C, -5 * C), QPointF(7 * C, 5 * C))
c.clearSelection()
v.definir_zoom(0.8)
v.centerOn(QPointF(0, 0))
M._clima_mudou("chuva", 3)
QTest.qWait(400)
w, h = cl.width(), cl.height()

print("== de cima: a projeção é a de sempre (amplia a partir do centro)")
cl._acompanhar_mapa()
q, f = cl._proj(w / 2 + 100, h / 2 + 50, 0.3)
assert abs(f - 1 / 0.7) < 1e-6 and abs(q.x() - (w / 2 + 100 / 0.7)) < 1e-6

print("== girou a mesa: a gota que estava sobre um ponto do chão continua sobre ele")
de_cima, *_ = cl._camera()
alvo = QPointF(3 * C, 2 * C)
px = de_cima.map(alvo)
cl._p = [[px.x(), px.y(), 0.2, 1.0, 0.02, 0.5]]
v.definir_camera(40, 0, livre=True)
cl._acompanhar_mapa()
de_cima2, *_ = cl._camera()
volta = de_cima2.inverted()[0].map(QPointF(cl._p[0][0], cl._p[0][1]))
print("   desvio:", round((volta - alvo).manhattanLength(), 3))
assert (volta - alvo).manhattanLength() < 0.5

print("== inclinada: o chão visível vai mais longe (mais chuva) e a perspectiva vale")
area0 = cl._area_chao()
v.definir_camera(40, 50, livre=True)
cl._acompanhar_mapa()
area1 = cl._area_chao()
print("   chão na tela: de cima", int(area0.height()), "px · inclinada", int(area1.height()), "px")
assert area1.height() > area0.height() * 1.3
s, co, D = cl._incl
assert abs(s - math.sin(math.radians(50))) < 1e-6
g, _ = cl._proj(w / 2, h / 2, 0.3)
assert g.y() < h / 2   # o que está no alto "sobe" na tela (a câmera está atrás)

print("== deixa chover/nevar e explodir, inclinada, sem erro")
QTest.qWait(600)
v.grab().save(os.path.join(SAIDA, "camera_chuva.png"))
M._clima_mudou("neve", 2)
QTest.qWait(400)
M._clima_mudou("tempestade", 3)
cl._proximo_raio = 0
QTest.qWait(400)
M.servidor.impacto("explosao", 1 * C, -1 * C, 4.0)
M.servidor.lancar({"tipo": "projetil", "elemento": "fogo", "x0": -4 * C, "y0": 2 * C, "x1": 4 * C, "y1": -3 * C,
                   "tam": 3, "deixar": False}, "Manel")
QTest.qWait(500)
v.grab().save(os.path.join(SAIDA, "camera_efeitos.png"))
v.camera_de_cima()
QTest.qWait(200)
print("   erros:", erros[:2])
assert not erros, erros
print("FIM")
sys.stdout.flush()
os._exit(0)
