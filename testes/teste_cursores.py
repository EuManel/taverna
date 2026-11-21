"""(v0.64.1) Cada tema tem o seu ponteiro do mouse (luvinha no medieval, seta holográfica no futurista, ponteiro de
latão no steampunk…), sempre na cor do jogador e com a ponta no lugar do clique. Trocar de tema troca o ponteiro."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QPainter
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)
from taverna.mesa import luva
from taverna.temas import TEMAS
from taverna.ui import tema as T

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")
cores = [QColor("#e8c25a"), QColor("#3f9bd8"), QColor("#8a3fbb")]
imgs = {}
for k in TEMAS:
    assert k in luva.DESENHOS, k
    for cor in cores:
        img = luva.pixmap_luva(cor, 32, k).toImage()
        imgs[(k, cor.name())] = img
        # a ponta (onde clica) tem desenho por perto
        perto = [img.pixelColor(x, y).alpha() for x in range(0, 7) for y in range(0, 7)]
        assert max(perto) > 120, (k, cor.name())
        assert sum(img.pixelColor(x, y).alpha() > 0 for x in range(32) for y in range(32)) > 60, k
# cada tema é um desenho diferente, e a cor do jogador aparece
for a in TEMAS:
    for b in TEMAS:
        if a < b:
            assert imgs[(a, "#e8c25a")] != imgs[(b, "#e8c25a")], (a, b)
    assert imgs[(a, "#3f9bd8")] != imgs[(a, "#8a3fbb")], a
print("desenhos ok:", len(TEMAS), "temas")

# trocar o tema troca o ponteiro (o cursor do programa e o da mesa)
T.gerar_qss("medieval")
c1 = luva.cursor_luva(QColor("#3f9bd8"))
T.gerar_qss("futurista")
assert luva.tema_atual() == "futurista"
c2 = luva.cursor_luva(QColor("#3f9bd8"))
assert c1.pixmap().toImage() != c2.pixmap().toImage()
assert luva.cursor_luva(QColor("#3f9bd8")) is c2          # guardado (não redesenha toda hora)

# prancha pra olhar (4x)
Z = 4
prancha = QImage(len(TEMAS) * 40 * Z // 1 + 20, len(cores) * 40 * Z + 50, QImage.Format.Format_ARGB32)
prancha.fill(QColor("#2a2420"))
p = QPainter(prancha)
p.setRenderHint(QPainter.RenderHint.Antialiasing)
f = QFont()
f.setPixelSize(18)
f.setBold(True)
p.setFont(f)
for i, k in enumerate(TEMAS):
    x = 10 + i * 40 * Z
    p.setPen(QColor("#e8c25a"))
    p.drawText(QRectF(x, 8, 40 * Z, 30), Qt.AlignmentFlag.AlignCenter, k)
    for j, cor in enumerate(cores):
        y = 45 + j * 40 * Z
        p.fillRect(QRectF(x + 8, y, 32 * Z, 32 * Z), QColor("#e8e0d0") if j == 2 else QColor("#4a5a3a"))
        p.save()
        p.translate(x + 8, y)
        p.scale(Z, Z)
        luva.desenhar_luva(p, cor, 1.0, k)
        p.restore()
        p.setPen(QColor(255, 0, 0))
        p.drawEllipse(QPointF(x + 8 + luva.PONTA[0] * Z, y + luva.PONTA[1] * Z), 3, 3)   # onde clica
p.end()
prancha.save(os.path.join(SAIDA, "cursores_temas.png"))
print("FIM")
sys.stdout.flush()
os._exit(0)
