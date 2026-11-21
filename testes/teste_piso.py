"""(v0.68) Piso detalhado: as texturas de chão do gerador saem no DOBRO da resolução (mesmo desenho, mais nítido)
e, com zoom perto, os azulejos do piso são feitos a 2 px por unidade — o detalhe aparece em vez de borrar.
Um quadrado da textura continua sendo um quadrado da mesa."""
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
from taverna.mesa import materiais, texturas
from taverna.ui.janela_mestre import JanelaMestre

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")

print("== texturas no dobro")
for chave, (f, tam) in texturas.CHAOS.items():
    pm = materiais.textura("chao", chave)
    assert pm.width() == tam * texturas.ESCALA_CHAO, (chave, pm.width())
    assert materiais.escala_chao(chave) == texturas.ESCALA_CHAO
    assert abs(materiais.pincel_chao(chave).transform().m11() - 1 / texturas.ESCALA_CHAO) < 1e-6
assert texturas.ESC == 1.0                     # o gerador volta pro normal (paredes não mudam)
fora = next(k for k in materiais.CHAO if k not in texturas.CHAOS)   # um chão "desenhado" (antigo) segue em 1×
assert materiais.escala_chao(fora) == 1.0 and materiais.pincel_chao(fora).transform().isIdentity()
print("   desenhado em 1x:", fora)

print("== mesmo desenho, mais pixels: a média de cor não muda")
texturas.ESCALA_CHAO = 1
um = texturas.gerar("chao", "pedra")
texturas.ESCALA_CHAO = 2
dois = texturas.gerar("chao", "pedra")


def media(img):
    s = img.scaled(8, 8)
    return sum(s.pixelColor(x, y).lightness() for x in range(8) for y in range(8)) / 64


print("   luz média 1x/2x:", round(media(um)), round(media(dois)))
assert abs(media(um) - media(dois)) < 12

print("== zoom perto usa o azulejo detalhado")
M = JanelaMestre(); M.resize(1400, 900); M.show(); M.mostrar_mesa(); QTest.qWait(50)
c = M.cena
c.material_chao = "pedra"
c.criar_sala(QPointF(-6 * C, -4 * C), QPointF(0, 4 * C))
c.material_chao = "madeira"
c.criar_sala(QPointF(0, -4 * C), QPointF(6 * C, 4 * C))
c.clearSelection()
ter = c.terreno
for zoom, nivel in ((0.25, 1), (1.0, 0), (2.5, 2)):
    ter._cache.clear()
    M.visao.definir_zoom(zoom)
    M.visao.centerOn(QPointF(0, 0))
    QTest.qWait(150)
    M.visao.grab().save(os.path.join(SAIDA, f"piso_zoom{zoom}.png"))
    niveis = {k[2] for k in ter._cache}
    print(f"   zoom {zoom}: níveis {niveis}")
    assert niveis == {nivel}, (zoom, niveis)
graficos().definir("baixo")
ter._cache.clear(); M.visao.viewport().update(); QTest.qWait(150)
assert {k[2] for k in ter._cache} == {0}       # no Baixo, nada de azulejo pesado
print("   erros:", erros[:2])
assert not erros, erros
print("FIM")
sys.stdout.flush()
os._exit(0)
