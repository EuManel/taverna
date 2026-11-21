"""v0.47: removedor de fundo com IA — motor numpy (contas conferidas) e a janela recortando de verdade."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"; os.environ["TAVERNA_SEM_AUDIO"] = "1"
import numpy as np
from PyQt6.QtCore import QRectF, QPointF, Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QRadialGradient
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
app = QApplication(sys.argv); app.setStyle("Fusion")
from taverna.ia.motor import _conv, _maxpool, _resize
from taverna.ia import recorte

print("== CONVOLUÇÃO (com dilatação, passo e borda) bate com a conta na mão")
rng = np.random.default_rng(1)
for dil, passo, pad in ((1, 1, 1), (2, 1, 2), (1, 2, 1), (4, 1, 4)):
    x = rng.standard_normal((1, 3, 11, 9)).astype(np.float32)
    w = rng.standard_normal((4, 3, 3, 3)).astype(np.float32)
    b = rng.standard_normal(4).astype(np.float32)
    y = _conv(x, w, b, {"dilations": [dil, dil], "strides": [passo, passo], "pads": [pad] * 4})
    xp = np.pad(x, ((0, 0), (0, 0), (pad, pad), (pad, pad)))
    ho = (xp.shape[2] - (2 * dil + 1)) // passo + 1
    wo = (xp.shape[3] - (2 * dil + 1)) // passo + 1
    ref = np.zeros((1, 4, ho, wo), np.float32)
    for o in range(4):
        for i in range(ho):
            for j in range(wo):
                janela = xp[0, :, i * passo:i * passo + 2 * dil + 1:dil, j * passo:j * passo + 2 * dil + 1:dil]
                ref[0, o, i, j] = (janela * w[o]).sum() + b[o]
    assert y.shape == ref.shape and np.allclose(y, ref, atol=1e-4), (dil, passo, pad)
print("4 combinações conferidas")

print("== MAXPOOL com arredondamento pra cima e RESIZE bilinear")
x = np.arange(1 * 1 * 5 * 5, dtype=np.float32).reshape(1, 1, 5, 5)
m = _maxpool(x, {"kernel_shape": [2, 2], "strides": [2, 2], "ceil_mode": 1})
assert m.shape == (1, 1, 3, 3) and m[0, 0, 2, 2] == 24 and m[0, 0, 0, 0] == 6
r = _resize(np.array([[[[0, 10]]]], np.float32), None, np.array([1, 1, 1, 4]), {"mode": "linear"})
assert np.allclose(r[0, 0, 0], [0, 2.5, 7.5, 10]), r
print("ok")

print("== A JANELA DO REMOVEDOR: botão de baixar quando não tem modelo")
from taverna.ui.remover_fundo import DialogoRemoverFundo, _para_array
from taverna.mesa.props import CATALOGO
W = H = 400
img = QImage(W, H, QImage.Format.Format_RGBA8888)
img.fill(QColor(110, 150, 100))
p = QPainter(img)
import random
rr = random.Random(3)
for _ in range(60):   # fundo bagunçado: o 🪄 Automático não daria conta
    g = QRadialGradient(QPointF(rr.uniform(0, W), rr.uniform(0, H)), rr.uniform(15, 80))
    c = QColor(rr.randint(60, 220), rr.randint(80, 220), rr.randint(60, 200))
    g.setColorAt(0, c); c.setAlpha(0); g.setColorAt(1, c)
    p.setPen(Qt.PenStyle.NoPen); p.setBrush(g); p.drawRect(0, 0, W, H)
obj = QImage(W, H, QImage.Format.Format_RGBA8888); obj.fill(QColor(0, 0, 0, 0))
q = QPainter(obj); CATALOGO["barril"][4](q, QRectF(100, 80, 200, 240)); q.end()
p.drawImage(0, 0, obj); p.end()
from taverna.ui.remover_fundo import imagem_png
dados = imagem_png(img)
verdade = _para_array(obj)[:, :, 3] > 128

vazia = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida", "ia_vazia")
os.makedirs(vazia, exist_ok=True)
os.environ["TAVERNA_PASTA_IA"] = vazia
d = DialogoRemoverFundo(dados, "teste")
d.show(); QTest.qWait(50)
print("botão:", d.b_ia.text())
assert "Baixar" in d.b_ia.text()
d.reject()

# modelo de verdade: o que o usuário já baixou (Documentos/Taverna/IA)
os.environ.pop("TAVERNA_PASTA_IA")
if not recorte.modelo_instalado("rapido"):
    print("(modelo Rápido não baixado neste PC: pulei o recorte de verdade)")
    print("FIM")
    sys.exit(0)

print("== RECORTE DE VERDADE com o modelo Rápido (em segundo plano, a janela não trava)")
d = DialogoRemoverFundo(dados, "teste")
d.show(); QTest.qWait(50)
d.cb_modelo.setCurrentIndex(d.cb_modelo.findData("rapido"))
t0 = time.time()
d._clicou_ia()
assert d._trabalho is not None and d.b_ia.text() == "Cancelar"
while d._trabalho is not None and time.time() - t0 < 60:
    QTest.qWait(50)
alfa = d.arr[:, :, 3] > 128
iou = (alfa & verdade).sum() / max(1, (alfa | verdade).sum())
print(f"levou {time.time() - t0:.1f}s · acerto (IoU) {iou:.3f} · régua da borda visível: {not d.firmeza.isHidden()}")
assert iou > 0.9 and not d.firmeza.isHidden()
d.grab().save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida", "ia_janela.png"))
d.firmeza.setValue(0)    # borda suave: muda a imagem sem rodar a IA de novo
suave = d.arr[:, :, 3].copy()
d.firmeza.setValue(100)
assert (np.abs(suave.astype(int) - d.arr[:, :, 3]) > 0).any()
d._desfazer()
assert (d.arr[:, :, 3] == 255).all()   # volta pra antes da IA
from PyQt6.QtGui import QImage as _Q
saida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")
d._mascara_ia = None
d.firmeza.setValue(50)
d._clicou_ia()
while d._trabalho is not None:
    QTest.qWait(50)
_Q.fromData(d.resultado()).save(os.path.join(saida, "ia_recorte.png"))
print("FIM")
