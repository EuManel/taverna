"""(v0.67) Mesa 3D detalhada (pedido do Manel): porta com TEXTURA (tábuas com ferragem, pedra entalhada, metal
rebitado…), MAÇANETA no lado livre e DOBRADIÇAS (só na face virada pra câmera), GRADE de barras de verdade
(vazada) e PALIÇADA de troncos redondos com ponta. Nenhuma porta pode dar erro ao desenhar."""
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
from taverna.mesa import texturas_porta
from taverna.mesa.portas import TIPOS_PORTA
from taverna.ui.janela_mestre import JanelaMestre

print("== texturas")
for tipo in texturas_porta.FEITOS:
    pm = texturas_porta.textura(tipo)
    assert pm is not None and not pm.isNull() and pm.width() == int(C * texturas_porta.ESCALA), tipo
assert texturas_porta.textura("grade") is None and not texturas_porta.casca().isNull()

M = JanelaMestre(); M.resize(1600, 1000); M.show(); M.mostrar_mesa(); QTest.qWait(50)
c = M.cena
c.criar_sala(QPointF(-10 * C, -3 * C), QPointF(10 * C, 3 * C))
portas = {}
for i, tipo in enumerate(TIPOS_PORTA):
    c.tipo_porta = tipo
    portas[tipo] = c.colocar_porta(QPointF(-9 * C + i * 2 * C + C, -3 * C))
c.paredes.adicionar(QPointF(-6 * C, 1 * C), QPointF(6 * C, 1 * C), "palicada")

print("== maçaneta e dobradiças: só na face que a câmera vê")
p = portas["madeira"]
for cam in (QPointF(0, 300), QPointF(0, -300)):
    vols = p._volumes_3d(cam)
    folha = [v for v in vols if len(v) > 4 and v[4] is not None]
    assert len(folha) == 1                                          # a folha com textura
    macaneta = [v for v in vols if v[1] > 0.9 * C and v[2] < 1.1 * C]
    assert len(macaneta) == 1, len(macaneta)
    lado = macaneta[0][0].boundingRect().center().y()
    assert (lado > 0) == (cam.y() > 0), (cam, lado)                  # do lado de quem olha
p.dupla = True
assert sum(1 for v in p._volumes_3d(QPointF(0, 300)) if v[1] > 0.9 * C and v[2] < 1.1 * C) == 2
p.dupla = False

print("== grade vazada (barras)")
g = portas["grade"]
barras = [v for v in g._volumes_3d(QPointF(0, 300)) if v[0].boundingRect().width() < 4]
print("   barras:", len(barras))
assert len(barras) >= 6
g.aberta = True
g.pular_animacao()
assert not [v for v in g._volumes_3d(QPointF(0, 300)) if v[0].boundingRect().width() < 4]   # subiu toda

print("== paliçada: troncos")
tr = c.paredes.troncos()
print("   troncos:", len(tr))
assert len(tr) >= 30 and all(t[2] > 1.8 * C and t[3] > 0.2 * C for t in tr)
assert c.paredes.troncos() == tr                                     # sempre iguais (não "piscam")

print("== desenha tudo sem erro")
c.clearSelection()
M.visao.definir_zoom(1.0)
M.visao.centerOn(QPointF(0, -1 * C))
QTest.qWait(200)
img = M.visao.grab()
img.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida", "portas3d.png"))
print("   erros:", erros[:2])
assert not [e for e in erros if "Porta" in e or "porta" in e], erros
print("FIM")
sys.stdout.flush()
os._exit(0)
