"""(v0.60) Porta FÍSICA pra luz e pra visão (pedido do Manel): fechada, a luz não passa; abrindo, a luz vai
entrando junto com a folha; aberta, a luz passa pelo vão e a FOLHA faz sombra. Vale pros tipos que deslizam,
recolhem etc. Grade e janela de vidro continuam deixando a luz passar."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

app = QApplication(sys.argv)
from taverna.config import CELULA as C
from taverna.mesa.luzes import ponto_iluminado
from taverna.ui.janela_mestre import JanelaMestre
w = QTest.qWait

M = JanelaMestre(); M.resize(1000, 700); M.show(); M.mostrar_mesa(); w(50)
c = M.cena
c.criar_sala(QPointF(-4 * C, -3 * C), QPointF(4 * C, 3 * C))
porta = c.colocar_porta(QPointF(4 * C, 0))
c.tipo_luz = "tocha"
luz = c.colocar_luz(QPointF(1.5 * C, 0))
w(200)
fora = (5.5 * C, 0)
iluminado = lambda x, y: ponto_iluminado(c._polys_fixos, x, y)

print("== fechada: o vão inteiro bloqueia")
assert len(porta.segmentos_bloqueio()) == 1
assert not iluminado(*fora)

print("== no meio da animação a folha está na diagonal")
porta.aberta = True
porta._prog = 0.5
(x1, y1, x2, y2), = porta.segmentos_bloqueio()
ang = abs(math.degrees(math.atan2(y2 - y1, x2 - x1))) % 180
assert 30 < ang < 60 or 120 < ang < 150, ang
porta.aberta = False
porta.pular_animacao()

print("== aberta: a luz passa pelo vão, e a folha faz sombra")
porta.alternar()
for _ in range(60):
    w(20)
    if porta._prog >= 1:
        break
w(200)
assert porta._prog == 1.0
assert iluminado(*fora), "a luz devia passar pela porta aberta"
(x1, y1, x2, y2), = porta.segmentos_bloqueio()
assert abs(y2 - y1) < 2 and abs(abs(x2 - x1) - C) < 2      # parede em pé → folha aberta deitada (perpendicular)
ly = luz.scenePos().y()
yl = (y1 + y2) / 2
atras = (max(x1, x2) - 0.1 * C, yl + math.copysign(0.2 * C, yl - ly))   # do outro lado da folha, dentro da sala
print("sombra atrás da folha em", [round(v / C, 2) for v in atras], "->", iluminado(*atras))
assert not iluminado(*atras), "a folha aberta devia fazer sombra"

print("== fechando de novo: escuro lá fora")
porta.alternar()
for _ in range(60):
    w(20)
    if porta._prog <= 0:
        break
w(200)
assert not iluminado(*fora)

print("== outros tipos")
# (mecânica e secreta deixam a pontinha da folha no batente, igual ao desenho; cortina fica recolhida nos cantos)
for tipo, bloqueia_fechada, bloqueia_aberta in (("mecanica", True, True), ("cortina", True, True),
                                                 ("grade", False, False), ("janela", False, False),
                                                 ("magica", True, False), ("secreta", True, True)):
    porta.tipo = tipo
    porta.aberta = False
    porta.pular_animacao()
    f = bool(porta.segmentos_bloqueio())
    porta.aberta = True
    porta.pular_animacao()
    a = bool(porta.segmentos_bloqueio())
    print(f"  {tipo}: fechada bloqueia={f} · aberta sobra pedaço={a}")
    assert f == bloqueia_fechada and a == bloqueia_aberta, tipo
porta.tipo = "cortina"   # cortina aberta: só os pedaços recolhidos nos cantos — o meio do vão fica livre
w(200)
assert iluminado(*fora)
print("FIM")
sys.stdout.flush()
os._exit(0)
