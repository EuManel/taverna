"""(v0.76) Otimização medida (câmera inclinada girando: 20 → 31 fps na placa do Manel). Confere as peças:
- os títulos dos painéis NÃO se redesenham em ciclo (o ícone era trocado dentro do desenho e pedia outro);
- qualidade adaptativa: logo depois de mexer a câmera `em_movimento()` vale, e some sozinho;
- piso com resolução POR PEDAÇO com a câmera inclinada (longe em baixa);
- a imagem de luz/sombra é feita em meia resolução (e mais leve com a câmera mexendo)."""
import os
import sys
import time

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
from taverna.mesa import camera3d
from taverna.ui import acabamento
from taverna.ui.janela_mestre import JanelaMestre

M = JanelaMestre(); M.resize(1400, 900); M.show(); M.mostrar_mesa(); QTest.qWait(300)
c, v = M.cena, M.visao

print("== títulos dos painéis: sem redesenho em ciclo")
contagem = [0]
orig = acabamento.TituloPainel.paintEvent


def contar(self, ev):
    contagem[0] += 1
    orig(self, ev)


acabamento.TituloPainel.paintEvent = contar
for w in M.findChildren(acabamento.TituloPainel):
    w.update()
QTest.qWait(150)
contagem[0] = 0
QTest.qWait(700)
print("   redesenhos em 0,7 s parado:", contagem[0])
assert contagem[0] <= 3, contagem[0]
acabamento.TituloPainel.paintEvent = orig

print("== qualidade adaptativa enquanto a câmera mexe")
c.criar_sala(QPointF(-40 * C, -40 * C), QPointF(40 * C, 40 * C))   # chão grande
c.colocar_luz(QPointF(0, 0))
c.definir_ambiente("penumbra")
v.definir_zoom(0.9)
v.definir_camera(10, 50, livre=True)
assert camera3d.em_movimento()
QTest.qWait(300)
assert not camera3d.em_movimento()

print("== piso inclinado: perto em resolução normal, longe em baixa")
ter = c.terreno
heroi = c.adicionar_token(dict(nome="Aelar", tipo="jogador", cor="#3f6b4a", tamanho=1, imagem=None, dono=""),
                          QPointF(0, 20 * C))
heroi.direcao = 270.0
v.ver_pelos_olhos(heroi)   # mostra até o horizonte
QTest.qWait(300)
ter._cache.clear()
v.viewport().update()
QTest.qWait(400)
niveis = {k[2] for k in ter._cache}
print("   níveis dos pedaços:", niveis)
assert 1 in niveis and 0 in niveis
v.sair_dos_olhos()
v.definir_camera(10, 50, livre=True)
QTest.qWait(400)
v.viewport().update()
QTest.qWait(200)

print("== luz em meia resolução")
luz = c.luz_overlay
g = getattr(luz, "_img_cache", None)
assert g is not None
img = g[2]
assert img.width() <= v.viewport().width() * 0.55, (img.width(), v.viewport().width())
v.camera_de_cima()
QTest.qWait(200)
print("   erros:", erros[:2])
assert not erros, erros
print("FIM")
sys.stdout.flush()
os._exit(0)
