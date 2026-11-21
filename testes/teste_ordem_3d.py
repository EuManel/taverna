"""(v0.84) Mesa 3D com a câmera inclinada: OBJETOS entram na mesma fila de profundidade das fichas (do mais longe pro
mais perto) e são recortados pelas paredes da frente — antes ficavam sempre por baixo de fichas e paredes. E a
otimização da v0.84 (contorno da ficha guardado, paredes da frente calculadas uma vez por quadro) não muda o desenho."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

app = QApplication(sys.argv)
from taverna import seguranca
erros = []
seguranca.registrar_erro = lambda t: erros.append(t)
from taverna.graficos import graficos
graficos().definir("alto")
from taverna.config import CELULA as C
from taverna.mesa import altura3d, camera3d
from taverna.mesa import props as P
from taverna.mesa import token as T
from taverna.ui.janela_mestre import JanelaMestre

M = JanelaMestre(); M.resize(1300, 900); M.show(); M.mostrar_mesa(); QTest.qWait(50)
c, v = M.cena, M.visao
c.criar_sala(QPointF(-8 * C, -6 * C), QPointF(8 * C, 6 * C))
bau = c.colocar_prop("bau", QPointF(0, 0))
mesa = c.colocar_prop("mesa", QPointF(0, -3 * C))
longe = c.adicionar_token(dict(nome="Longe", tipo="criatura", cor="#3f6b4a", tamanho=1, imagem=None, dono=""),
                          QPointF(0.2 * C, -1.6 * C))
perto = c.adicionar_token(dict(nome="Perto", tipo="criatura", cor="#6b3f3f", tamanho=1, imagem=None, dono=""),
                          QPointF(0.2 * C, 2.5 * C))
c.clearSelection()
v.definir_zoom(0.9); v.centerOn(QPointF(0, 0))
v.definir_camera(0, 50, livre=True)
QTest.qWait(300)

ordem = []
corpo_prop, corpo_tok = P.PropItem.pintar_corpo_3d, T.TokenItem.pintar_corpo_3d
desenho_prop = P.PropItem._desenhar_3d
P.PropItem.pintar_corpo_3d = lambda s, p, n: (ordem.append(s), corpo_prop(s, p, n))[1]
T.TokenItem.pintar_corpo_3d = lambda s, p, n: (ordem.append(s), corpo_tok(s, p, n))[1]
corpos = []
def _d3(s, p, r, n, sombra=True, corpo=True):
    if corpo:
        corpos.append(s)
    return desenho_prop(s, p, r, n, sombra=sombra, corpo=corpo)
P.PropItem._desenhar_3d = _d3
v.viewport().repaint(); QTest.qWait(50)
v.viewport().repaint(); QTest.qWait(50)

print("== tudo na mesma fila, do mais longe pro mais perto")
quadro = ordem[-4:]
print("   ordem:", [getattr(x, "nome", "") or x.tipo for x in quadro])
assert set(quadro) == {bau, mesa, longe, perto}, quadro
assert quadro.index(mesa) < quadro.index(longe) < quadro.index(bau) < quadro.index(perto)
print("== o corpo do objeto é desenhado UMA vez por quadro (só pela camada alta)")
n_quadros = ordem.count(perto)
assert corpos.count(bau) == n_quadros, (corpos.count(bau), n_quadros)
assert bau in altura3d.OBJETOS

print("== mesa 2D (Baixo): o objeto se desenha sozinho de novo")
graficos().definir("baixo"); v.viewport().repaint(); QTest.qWait(50)
assert bau not in altura3d.OBJETOS
graficos().definir("alto")

print("== paredes da frente: o mesmo resultado calculado por quadro")
from PyQt6.QtGui import QImage, QPainter
img = QImage(1300, 900, QImage.Format.Format_ARGB32_Premultiplied)
p = QPainter(img)
p.setWorldTransform(v.viewportTransform())
cam = camera3d.Camera(p)
quadro = altura3d._ParedesDoQuadro(cam, c.paredes)
for tok in (longe, perto):
    a = [x.boundingRect() for x in quadro.na_frente(tok.centro_cena())]
    b = [x.boundingRect() for x in altura3d._na_frente(cam, c.paredes, tok.centro_cena())]
    assert a == b
p.end()
v.viewport().grab().save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida", "ordem_3d.png"))
assert not erros, erros[:3]
print("FIM")
sys.stdout.flush()
os._exit(0)
