"""
Gás que respeita paredes (v0.44) — pedido do Manel: "gás tóxico… bloqueado por paredes, portas etc."

Áreas de GÁS (veneno, fumaça) não atravessam parede, porta fechada nem objeto que bloqueia: a nuvem se
espalha a partir do centro (ou da boca, no cone/linha) e CONTORNA cantos e pilares (espalha em duas
etapas: do centro, e de novo de pontos no meio do caminho). Abriu a porta, o gás passa por ela.

É a mesma conta da luz (linha_de_visao.poligono), feita só quando algo muda.
"""

import math

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainterPath

from ..config import CELULA

GASES = {"veneno", "fumaca"}


def espalhar(cx: float, cy: float, raio: float, obst: list) -> QPainterPath | None:
    """Até onde a nuvem chega (cena). None = nada no caminho (não precisa recortar)."""
    from .linha_de_visao import poligono
    perto = [s for s in obst
             if min(s[0], s[2]) <= cx + raio and max(s[0], s[2]) >= cx - raio
             and min(s[1], s[3]) <= cy + raio and max(s[1], s[3]) >= cy - raio]
    if not perto:
        return None
    from PyQt6.QtCore import Qt
    caminho = QPainterPath()
    caminho.setFillRule(Qt.FillRule.WindingFill)   # (as partes se SOMAM — com o padrão, a sobreposição virava buraco)
    p0 = poligono(cx, cy, 0, 360, raio / CELULA, perto)
    caminho.addPolygon(p0)
    caminho.closeSubpath()
    # segunda etapa: de pontos que a nuvem já alcançou, ela continua (contorna o canto/pilar)
    for anel in (0.4, 0.7):
        d = raio * anel
        for k in range(8):
            ang = k * math.pi / 4 + anel
            px, py = cx + math.cos(ang) * d, cy + math.sin(ang) * d
            if p0.containsPoint(QPointF(px, py), caminho.fillRule()):
                extra = poligono(px, py, 0, 360, (raio - d) / CELULA, perto)
                caminho.addPolygon(extra)
                caminho.closeSubpath()
    return caminho.simplified()


def origem_e_raio(area):
    """De onde o gás sai (centro do círculo/quadrado; boca do cone/linha) e até onde vai (cena)."""
    base = area.caminho_base()
    r = base.boundingRect()
    if area.forma in ("cone", "linha"):
        o = QPointF(0, 0)
    else:
        o = r.center()
    raio = max(math.hypot(c.x() - o.x(), c.y() - o.y())
               for c in (r.topLeft(), r.topRight(), r.bottomLeft(), r.bottomRight()))
    return area.mapToScene(o), raio
