"""(v0.80) Pendências pequenas da câmera livre: a INICIAL do token fica em pé na tela mesmo com a câmera girada, e
a bola de fogo da explosão não sobe demais no 3D (fica presa no chão)."""
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
from taverna.mesa import impactos
from taverna.mesa.token import TokenItem as Token
from taverna.ui.janela_mestre import JanelaMestre

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")
M = JanelaMestre(); M.resize(1400, 900); M.show(); M.mostrar_mesa(); QTest.qWait(80)
c, v = M.cena, M.visao
c.criar_sala(QPointF(-6 * C, -4 * C), QPointF(6 * C, 4 * C))
tok = c.adicionar_token(dict(nome="Bruxa", tipo="criatura", cor="#6a5a40", tamanho=1, imagem=None, dono=""),
                        QPointF(0, 0))
c.clearSelection()

print("== a letra fica em pé com a câmera girada (de cima e inclinada)")
angulos = []
orig = Token._pintar_letra


def medir(self, painter, cc, d):
    t = painter.worldTransform()
    a = t.map(cc.center())
    b = t.map(cc.center() + QPointF(10, 0))                # o "pra direita" da letra, na tela
    angulos.append(math.degrees(math.atan2(b.y() - a.y(), b.x() - a.x())))
    orig(self, painter, cc, d)


Token._pintar_letra = medir
v.definir_zoom(1.0)
v.centerOn(QPointF(0, 0))
for giro, incl in ((90, 0), (200, 0), (135, 40)):
    angulos.clear()
    v.definir_camera(giro, incl, livre=True)
    QTest.qWait(300)
    assert angulos, "a letra não foi desenhada"
    print(f"   giro {giro} incl {incl}: letra a {angulos[-1]:.1f}°")
    assert abs(angulos[-1]) < 12, angulos[-1]                 # (inclinada a perspectiva entorta um pouco)
Token._pintar_letra = orig
v.grab().save(os.path.join(SAIDA, "letra_em_pe.png"))

print("== explosão inclinada: a bola de fogo fica baixa")
alturas = []
classe = impactos.ImpactoItem
orig_alto = classe._alto


def alto(self, p, z):
    alturas.append(z / self.R)
    orig_alto(self, p, z)


classe._alto = alto
v.definir_camera(0, 45, livre=True)
QTest.qWait(200)
impactos.tocar(c, None, None, "explosao", 2 * C, 0, 3.0)
QTest.qWait(900)
classe._alto = orig_alto
assert alturas, "a explosão não desenhou nada no alto"
print(f"   mais alto: {max(alturas):.2f} R")
assert max(alturas) <= 1.2, max(alturas)                     # (antes chegava a ~2,7 R com a fumaça)
print("   erros:", erros[:2])
assert not erros, erros
print("FIM")
sys.stdout.flush()
os._exit(0)
