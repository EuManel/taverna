"""(v0.65.1) Falha crítica: fumaça com VOLUME (nada de bolota preta chapada), fendas com profundidade em volta do
dado, e a borda vermelha só nas beiradas — desenhado numa imagem comum (a tela preta era a placa de vídeo lendo
a textura errada; ver render_gl: glActiveTexture(GL_TEXTURE0) antes do QPainter)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QImage, QPainter
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)
from taverna.dados3d import efeitos_critico as fx

W, H = 600, 400
c, raio = QPointF(300, 220), 30.0
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")
prancha = QImage(W * 3, H, QImage.Format.Format_RGB32)
pp = QPainter(prancha)
for i, dt in enumerate((0.2, 0.9, 1.6)):
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    fx.desenhar_vinheta(p, W, H, max(0.0, 1 - dt / 1.1))
    fx.desenhar_rachaduras(p, c, raio, dt, 1.0, 7)
    fx.desenhar_fumaca(p, c, raio, dt, 1.0, 7)
    p.end()
    # o meio da tela continua transparente (nada de tela preta)
    assert img.pixelColor(80, 60).alpha() < 40 or dt < 1.1, dt
    assert img.pixelColor(W // 2, 30).alpha() < 255
    # fumaça: tem coisa acima do dado, e NÃO é preto chapado (tem luz: claro em cima)
    acima = [img.pixelColor(int(c.x()) + dx, int(c.y() - raio * 2.2) + dy) for dx in range(-20, 21, 5)
             for dy in range(-20, 21, 5)]
    com_fumaca = [q for q in acima if q.alpha() > 40]
    if dt >= 0.9:
        assert com_fumaca, dt
        assert max(q.lightness() for q in com_fumaca) > 60, "fumaça preta chapada"
    # fendas escuras em volta do dado (no chão), e o centro do dado livre
    perto = [img.pixelColor(int(c.x() + dx), int(c.y() + dy)) for dx in range(-90, 91, 3) for dy in range(-70, 71, 3)
             if (dx * dx + dy * dy) ** 0.5 > raio * 1.2]
    assert sum(1 for q in perto if q.alpha() > 150 and q.lightness() < 40) > 20, "sem rachado"
    fundo = QImage(W, H, QImage.Format.Format_RGB32)
    fundo.fill(QColor("#8a8070"))
    pf = QPainter(fundo)
    pf.drawImage(0, 0, img)
    pf.end()
    pp.drawImage(i * W, 0, fundo)
pp.end()
prancha.save(os.path.join(SAIDA, "falha_critica.png"))
print("FIM")
sys.stdout.flush()
os._exit(0)
