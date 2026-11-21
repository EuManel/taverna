"""
Linha de visão: o que um token consegue enxergar.

Como funciona (o jeito clássico dos jogos):
  1. Junta os "obstáculos": paredes opacas e portas fechadas, como segmentos de reta.
  2. Do olho do token, dispara vários raios dentro do cone de visão
     (e alguns raios mirando exatamente nas pontas das paredes, pra borda ficar certinha).
  3. Cada raio para na primeira parede que bater (ou no alcance máximo).
  4. Ligando as pontas dos raios, sai o polígono do que dá pra ver.

Funciona igual no mestre (pra filtrar o que vai pros players) e no player (pra desenhar a névoa).
"""

import math

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainterPath, QPolygonF

from ..config import CELULA
from .materiais import TRANSPARENTES

# Portas que deixam ver através mesmo fechadas
PORTAS_TRANSPARENTES = {"grade", "janela"}   # dá pra ver através mesmo fechada

PASSO_RAIO_GRAUS = 2.0

# Atalhos de visão que o mestre pode aplicar num token
PRESETS_VISAO = {
    # chave: (nome, alcance m, abertura °, visão no escuro m)
    # (v0.71, o Manel) padrão = cone de 60° pra frente, 24 m; 180° e 360° viraram opções
    "normal": ("Normal (cone de 60°, 24 m)", 24, 60, 0),
    "escuro": ("Visão no escuro (18 m)", 24, 60, 18),
    "amplo": ("Amplo (180°)", 24, 180, 0),
    "total": ("Visão total (360°)", 12, 360, 0),
    "escuridao": ("Escuridão (mal enxerga)", 3, 120, 0),
    "cegueira": ("Cegueira (não vê nada)", 0, 0, 0),
}


def obstaculos(segmentos_parede: dict | list, portas: list) -> list[tuple]:
    """
    segmentos_parede: dict {id: {"a":[x,y],"b":[x,y],"m":mat}} ou lista de dicts com "a","b","m"
    portas: lista de dicts (para_dict da porta) ou objetos PortaItem
    Retorna [(x1, y1, x2, y2), ...]
    """
    lista = []
    valores = segmentos_parede.values() if isinstance(segmentos_parede, dict) else segmentos_parede
    for seg in valores:
        if seg.get("m") in TRANSPARENTES:
            continue
        (x1, y1), (x2, y2) = seg["a"], seg["b"]
        lista.append((float(x1), float(y1), float(x2), float(y2)))
    for p in portas:
        if (isinstance(p, dict) and p.get("classe") == "efeito") or hasattr(p, "efeito_area"):
            from .efeitos import obstaculos_de_efeito
            lista.extend(obstaculos_de_efeito(p))
            continue
        if (isinstance(p, dict) and p.get("classe") == "prop") or hasattr(p, "luz_dict"):
            from .props import obstaculos_de_prop
            lista.extend(obstaculos_de_prop(p))
            continue
        if hasattr(p, "segmentos_bloqueio"):   # (v0.60) porta física: onde a folha está agora
            lista.extend(p.segmentos_bloqueio())
            continue
        d = p if isinstance(p, dict) else p.para_dict()
        if d.get("aberta") or d.get("tipo") in PORTAS_TRANSPARENTES or not d.get("visivel", True):
            continue
        meio = float(d.get("largura_m", 1.0)) * CELULA / 2
        ang = math.radians(float(d.get("angulo", 0)))
        cx, cy = float(d["x"]), float(d["y"])
        dx, dy = math.cos(ang) * meio, math.sin(ang) * meio
        lista.append((cx - dx, cy - dy, cx + dx, cy + dy))
    return lista


def _raio(ox, oy, ang, alcance, segs):
    dx, dy = math.cos(ang), math.sin(ang)
    melhor = alcance
    for x1, y1, x2, y2 in segs:
        ex, ey = x2 - x1, y2 - y1
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            continue
        fx, fy = x1 - ox, y1 - oy
        t = (fx * ey - fy * ex) / den        # distância ao longo do raio
        u = (fx * dy - fy * dx) / den        # posição ao longo da parede (0..1)
        if t > 0.01 and -1e-6 <= u <= 1 + 1e-6 and t < melhor:
            melhor = t
    return ox + dx * melhor, oy + dy * melhor


def _dentro_do_cone(ang, centro, meia):
    diff = (ang - centro + math.pi) % (2 * math.pi) - math.pi
    return abs(diff) <= meia + 1e-9


def poligono(ox: float, oy: float, direcao_graus: float, abertura_graus: float,
             alcance_m: float, segs: list[tuple]) -> QPolygonF:
    """Polígono (em coordenadas da mesa) do que o olho em (ox, oy) enxerga."""
    alcance = max(0.0, alcance_m) * CELULA
    if alcance <= 0 or abertura_graus <= 0:
        return QPolygonF()

    # Só as paredes perto interessam
    perto = [s for s in segs
             if min(s[0], s[2]) <= ox + alcance and max(s[0], s[2]) >= ox - alcance
             and min(s[1], s[3]) <= oy + alcance and max(s[1], s[3]) >= oy - alcance]

    chave = (round(ox, 2), round(oy, 2), round(direcao_graus, 2), round(abertura_graus, 2), alcance,
             hash(tuple(perto)))
    pronto = _CACHE.get(chave)
    if pronto is not None:
        return QPolygonF(pronto)

    cheio = abertura_graus >= 359.5
    centro = math.radians(direcao_graus)
    meia = math.radians(min(abertura_graus, 360) / 2)

    angulos = []
    passo = math.radians(PASSO_RAIO_GRAUS)
    if cheio:
        n = int(2 * math.pi / passo)
        angulos = [i * passo for i in range(n)]
    else:
        n = max(2, int(2 * meia / passo))
        angulos = [centro - meia + 2 * meia * i / n for i in range(n + 1)]
    # Raios mirando nas pontas das paredes (borda da sombra fica precisa)
    for x1, y1, x2, y2 in perto:
        for px, py in ((x1, y1), (x2, y2)):
            a = math.atan2(py - oy, px - ox)
            for eps in (-0.0004, 0.0004):
                if cheio or _dentro_do_cone(a + eps, centro, meia):
                    angulos.append(a + eps)

    if cheio:
        angulos.sort(key=lambda a: a % (2 * math.pi))
    else:
        angulos.sort(key=lambda a: (a - (centro - meia)) % (2 * math.pi))

    xs, ys = _raios(ox, oy, angulos, alcance, perto)
    pontos = [QPointF(x, y) for x, y in zip(xs.tolist(), ys.tolist())]
    if not cheio:
        pontos = [QPointF(ox, oy)] + pontos
    pol = QPolygonF(pontos)
    if len(_CACHE) > 600:
        _CACHE.clear()
    _CACHE[chave] = pol
    return QPolygonF(pol)


def _raios(ox, oy, angulos, alcance, perto):
    """(v0.47) Todos os raios contra todas as paredes de uma vez (numpy), em vez de raio por raio."""
    import numpy as np
    a = np.asarray(angulos, np.float64)
    dx, dy = np.cos(a), np.sin(a)
    if not perto:
        return ox + dx * alcance, oy + dy * alcance
    s = np.asarray(perto, np.float64)
    ex, ey = (s[:, 2] - s[:, 0])[None, :], (s[:, 3] - s[:, 1])[None, :]
    fx, fy = (s[:, 0] - ox)[None, :], (s[:, 1] - oy)[None, :]
    dxc, dyc = dx[:, None], dy[:, None]
    den = dxc * ey - dyc * ex
    ok = np.abs(den) >= 1e-9
    den = np.where(ok, den, 1.0)
    t = (fx * ey - fy * ex) / den
    u = (fx * dyc - fy * dxc) / den
    ok &= (t > 0.01) & (u >= -1e-6) & (u <= 1 + 1e-6)
    melhor = np.minimum(np.where(ok, t, alcance).min(axis=1), alcance)
    return ox + dx * melhor, oy + dy * melhor


_CACHE = {}   # (v0.47) luz parada + paredes iguais = mesmo polígono (não recalcula a cada passo de token)


def caminho_da_visao(poligonos: list[QPolygonF]) -> QPainterPath:
    """Une vários polígonos (vários tokens do mesmo jogador) num caminho só."""
    total = QPainterPath()
    total.setFillRule(total.fillRule().WindingFill)
    for pol in poligonos:
        if not pol.isEmpty():
            total.addPolygon(pol)
            total.closeSubpath()
    return total


def ponto_visivel(caminho: QPainterPath, x: float, y: float, raio: float = 0) -> bool:
    """O ponto (ou um pouquinho em volta dele) está na área vista?"""
    if caminho.isEmpty():
        return False
    if caminho.contains(QPointF(x, y)):
        return True
    if raio > 0:
        for ang in range(0, 360, 45):
            a = math.radians(ang)
            if caminho.contains(QPointF(x + math.cos(a) * raio, y + math.sin(a) * raio)):
                return True
    return False
