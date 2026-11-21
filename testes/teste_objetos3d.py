"""(v0.67.1) Objetos na Mesa 3D: MÓVEIS COM PERNAS (tampo + pés, não um bloco maciço) e FAIXAS de material nas
laterais (aros do barril, ferragem do baú, fiadas de pedra, prateleiras, luz das máquinas). Nada pode dar erro."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

app = QApplication(sys.argv)
from taverna import seguranca
erros = []
seguranca.registrar_erro = lambda t: erros.append(t)
from taverna.graficos import graficos
graficos().definir("alto")
from taverna.config import CELULA as C
from taverna.mesa import props as P
from taverna.ui.janela_mestre import JanelaMestre

print("== tabelas")
assert all(k in P.CATALOGO for k in P.PERNAS), [k for k in P.PERNAS if k not in P.CATALOGO]
assert all(k in P.CATALOGO for k in P.FAIXAS), [k for k in P.FAIXAS if k not in P.CATALOGO]
for tipo, faixas in P.FAIXAS.items():
    assert all(0 <= de < ate <= 1.0001 for de, ate, _ in faixas), tipo
assert len(P._pes(QRectF(0, 0, 128, 64), 0.08, "quatro")) == 4
assert len(P._pes(QRectF(0, 0, 96, 96), 0.14, "centro")) == 1
pes = P._pes(QRectF(0, 0, 128, 64), 0.08, "quatro")
assert all(QRectF(0, 0, 128, 64).contains(p.boundingRect()) for p in pes)   # dentro do tampo

print("== desenha na mesa sem erro")
M = JanelaMestre(); M.resize(1500, 1000); M.show(); M.mostrar_mesa(); QTest.qWait(50)
c = M.cena
c.criar_sala(QPointF(-9 * C, -6 * C), QPointF(9 * C, 6 * C))
tipos = list(P.PERNAS) + list(P.FAIXAS)
for i, t in enumerate(tipos):
    c.colocar_prop(t, QPointF(-8 * C + (i % 9) * 2 * C, -5 * C + (i // 9) * 2.4 * C))
c.clearSelection()
M.visao.definir_zoom(0.7)
M.visao.centerOn(QPointF(0, 0))
QTest.qWait(200)
M.visao.grab().save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida", "objetos3d.png"))
print("   objetos:", len(tipos), "· erros:", erros[:2])
assert not [e for e in erros if "Objeto 3D" in e], erros
mesa = next(i for i in c.itens_do_usuario() if getattr(i, "tipo", "") == "mesa")
assert P._cor_media(mesa._corpo_e_sombra(QRectF(0, 0, mesa.largura, mesa.altura), 2)[0]).isValid()
print("FIM")
sys.stdout.flush()
os._exit(0)
