"""(v0.83) 🌫 Névoa DESENHADA na cidade/mundo do jogador: por cima da parte que não chegou (coberta) vai uma névoa no
estilo do tema, com borda; o revelado continua igual. Baixo = sem desenho (como antes), Médio = parada, Alto = anda.
Prancha dos 9 temas em testes/saida/nevoa_atlas_temas.png."""
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QRadialGradient, QTransform
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv[:1])
from taverna.temas import TEMAS
from taverna.ui import nevoa_atlas as N

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")
W, H = 800, 560

# o que o jogador recebe: o mapa só onde foi revelado (o resto transparente, borda suave)
tela = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
tela.fill(0)
mapa = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
mapa.fill(QColor("#6a7a50"))
pm = QPainter(mapa)
for i in range(0, W, 40):
    pm.fillRect(i, 0, 3, H, QColor("#58683f"))
pm.fillRect(300, 200, 120, 90, QColor("#8a5a3a"))
pm.end()
mascara = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
mascara.fill(0)
pk = QPainter(mascara)
for cx, cy, r in ((360, 250, 190), (560, 330, 120)):
    g = QRadialGradient(QPointF(cx, cy), r)
    g.setColorAt(0, QColor(0, 0, 0, 255)); g.setColorAt(0.8, QColor(0, 0, 0, 255)); g.setColorAt(1, QColor(0, 0, 0, 0))
    pk.setBrush(g); pk.setPen(Qt.PenStyle.NoPen); pk.drawEllipse(QPointF(cx, cy), r, r)
pk.end()
pt = QPainter(tela)
pt.drawImage(0, 0, mapa)
pt.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
pt.drawImage(0, 0, mascara)
pt.end()


def render(tema, nivel, t=0.0, chave="c"):
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(QColor("#0f0d0b"))   # o fundo da mesa (o "escuro liso" de antes)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    p.drawImage(0, 0, tela)
    N.desenhar(p, chave + tema, 1, tela, QTransform(), tema, nivel, t)
    p.end()
    return img


print("== Baixo: nada (o escuro liso de antes)")
assert N.imagem("x", 1, tela, "medieval", 0, 0.0)[0] is None
b = render("medieval", 0)
assert b.pixelColor(40, 40).name() == "#0f0d0b"

print("== cada tema: o coberto ganha a névoa do tema, o revelado fica igual")
quadros = []
for tema in TEMAS:
    img = render(tema, 1)
    quadros.append((tema, img))
    longe = img.pixelColor(40, 40)
    assert longe.alpha() == 255 and longe.name() != "#0f0d0b", (tema, longe.name())
    meio = img.pixelColor(360, 245)                     # dentro do revelado: o mapa
    assert abs(meio.red() - 0x8a) < 8 and abs(meio.green() - 0x5a) < 8, (tema, meio.name())
    # é DESENHADA (tem variação), não uma cor chapada
    vals = [img.pixelColor(x, y).lightness() for x in range(10, 200, 9) for y in range(10, 120, 9)]
    assert max(vals) - min(vals) > 12, (tema, max(vals) - min(vals))

print("== Médio parada, Alto anda")
a0 = render("moderno", 1, 0.0, "m"); a1 = render("moderno", 1, 3.0, "m")
assert a0 == a1
h0 = render("moderno", 2, 0.0, "a"); h1 = render("moderno", 2, 3.0, "a")
assert h0 != h1

print("== rapidez: refazer um quadro do Alto")
t0 = time.perf_counter()
for k in range(10):
    N.imagem("rap", 1, tela, "futurista", 2, k * 0.1)
ms = (time.perf_counter() - t0) * 100
print(f"   {ms:.1f} ms por quadro (grade {N._cache['rap']['camadas']['alfa'].shape})")
assert ms < 60, ms

print("== prancha")
col = 3
lin = math.ceil(len(quadros) / col)
esc = 0.42
prancha = QImage(int(W * esc) * col, int(H * esc + 22) * lin, QImage.Format.Format_RGB32)
prancha.fill(QColor("#111"))
pp = QPainter(prancha)
pp.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
f = QFont(); f.setPixelSize(14); f.setBold(True); pp.setFont(f)
for i, (tema, img) in enumerate(quadros):
    x, y = (i % col) * int(W * esc), (i // col) * int(H * esc + 22)
    pp.drawImage(x, y + 22, img.scaled(int(W * esc), int(H * esc), Qt.AspectRatioMode.IgnoreAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation))
    pp.setPen(QColor("#e8dcc4")); pp.drawText(x + 6, y + 16, TEMAS[tema]["nome"])
pp.end()
prancha.save(os.path.join(SAIDA, "nevoa_atlas_temas.png"))
print("FIM")
sys.stdout.flush()
os._exit(0)
