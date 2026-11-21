"""
Efeitos de atmosfera desenhados na mesa (Etapa 10).

- EfeitoItem: uma ÁREA com efeito (template de magia ou terreno afetado):
  círculo, quadrado, cone ou linha — em chamas, congelado, veneno, escuridão...
  Animado. O mestre coloca; o jogador também pode colocar o template da magia dele.
  Escuridão e fumaça bloqueiam a visão; fogo, luz e raio iluminam.
- desenhar_sobre(): o mesmo efeito por cima de um token ou objeto ("em chamas", "molhado"...).
- Um relógio só (ANIMACAO) redesenha tudo que está animado, ~15 vezes por segundo.
"""

import math
import random
import time
import uuid
import weakref

from PyQt6.QtCore import QObject, QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF,
                         QRadialGradient)
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsObject

from ..config import CELULA

# chave: (nome, cor, ilumina?, bloqueia a visão?)
EFEITOS = {
    "fogo": ("🔥 Fogo", "#ff6a1a", True, False),
    "lava": ("🌋 Lava", "#ff5a0a", True, False),
    "gelo": ("❄ Gelo", "#a8e4ff", True, False),
    "veneno": ("☠ Veneno", "#7bd14a", True, False),
    "acido": ("🧪 Ácido", "#c6f53a", True, False),
    "agua": ("💧 Água", "#3a8cff", False, False),
    "eletrico": ("⚡ Elétrico", "#ffe94a", True, False),
    "trevas": ("🌑 Escuridão mágica", "#08060c", False, True),
    "fumaca": ("💨 Fumaça / névoa", "#9a9a9a", False, True),
    "luz": ("✨ Luz mágica", "#fff6c8", True, False),
    "sagrado": ("☀ Radiante", "#ffd66a", True, False),
    "teia": ("🕸 Teia", "#e8e8e8", False, False),
    "planta": ("🌿 Vinhas / mato", "#4f9a32", False, False),
    "magia": ("🔮 Magia", "#b07aff", True, False),
}

# v0.36: áreas "mágicas" com cor livre (quem coloca escolhe). As outras têm a cor do elemento.
CORES_LIVRES = {"magia", "luz", "sagrado", "trevas"}
CORES_MAGIA = [("Roxo", "#b07aff"), ("Azul", "#4a8cff"), ("Ciano", "#38e1ff"), ("Verde", "#4ae070"),
               ("Dourado", "#ffc840"), ("Vermelho", "#ff4a4a"), ("Rosa", "#ff6ad0"), ("Branco", "#f0eeff")]


def cor_valida(c) -> str:
    """'#rrggbb' ou '' (protege contra lixo vindo da rede)."""
    c = str(c or "").strip()
    return c if len(c) == 7 and c[0] == "#" and all(x in "0123456789abcdefABCDEF" for x in c[1:]) else ""


# Luz que cada efeito solta: (cor, tremula?, alcance relativo ao tamanho da área).
# Revela no escuro igual uma tocha (decisão do Manel). Escuridão e fumaça não iluminam.
LUZ_EFEITO = {
    "fogo": ("#ff9a3a", True, 1.0), "lava": ("#ff6a10", True, 1.15), "eletrico": ("#b8d4ff", True, 0.9),
    "luz": ("#fff6c8", False, 1.0), "sagrado": ("#ffe39a", False, 1.1), "acido": ("#9be02e", False, 0.6),
    "veneno": ("#b4d84a", False, 0.45), "gelo": ("#9fd8ff", False, 0.45), "magia": ("#b07aff", False, 0.75),
}

# Efeito em cima de um token/objeto (rótulo de menu)
EFEITOS_OBJETO = {
    "fogo": "🔥 Em chamas",
    "agua": "💧 Molhado",
    "gelo": "❄ Congelado",
    "veneno": "☠ Envenenado",
    "acido": "🧪 Corroendo (ácido)",
    "eletrico": "⚡ Eletrizado",
    "luz": "✨ Brilhando",
    "teia": "🕸 Preso na teia",
    "planta": "🌿 Enroscado",
}

FORMAS = {
    "circulo": "⭕ Círculo (raio)",
    "quadrado": "⬛ Quadrado / cubo (lado)",
    "cone": "🔺 Cone (comprimento)",
    "linha": "➖ Linha (comprimento)",
}

TAMANHO_PADRAO = {"circulo": 6.0, "quadrado": 3.0, "cone": 4.5, "linha": 9.0}


# ====================================================================== relógio
class _Animacao(QObject):
    def __init__(self):
        super().__init__()
        self.itens = weakref.WeakSet()
        self.timer = QTimer(self)
        self.timer.setInterval(66)
        self.timer.timeout.connect(self._tique)

    def registrar(self, item):
        self.itens.add(item)
        if not self.timer.isActive():
            self.timer.start()

    def esquecer(self, item):
        self.itens.discard(item)

    def _tique(self):
        from ..graficos import nivel
        intervalo = (160, 66, 40)[nivel()]   # baixo anima devagar (leve), alto bem liso
        if self.timer.interval() != intervalo:
            self.timer.setInterval(intervalo)
        vivos = False
        for item in list(self.itens):
            try:
                if item.scene() is not None and item.isVisible() and item.animado():
                    item.update()
                    vivos = True
            except RuntimeError:
                self.itens.discard(item)
        if not vivos and not len(self.itens):
            self.timer.stop()


_ANIM = None


def animacao() -> _Animacao:
    global _ANIM
    if _ANIM is None:
        _ANIM = _Animacao()
    return _ANIM


def agora() -> float:
    return time.monotonic()


# ====================================================================== geometria
NOME_VAPOR = "Vapor"   # nuvem de vapor das reações (some sozinha e não bloqueia a visão/luz)
GASES_AREA = {"veneno", "fumaca"}   # gás: não atravessa parede nem porta fechada (mesa/gas.py)


def _caminho_poligonos(poligonos) -> QPainterPath:
    p = QPainterPath()
    for pol in poligonos or []:
        if len(pol) >= 3:
            p.addPolygon(QPolygonF([QPointF(float(x), float(y)) for x, y in pol]))
            p.closeSubpath()
    return p


def caminho_local(forma: str, tamanho_m: float, largura_m: float = 1.5, pontos=None, recortes=None) -> QPainterPath:
    """Forma do efeito com a ORIGEM em (0,0), apontando pra direita (ângulo 0).
    forma "livre" = os polígonos de 'pontos' (pedaço que sobrou/virou outra coisa numa reação).
    recortes = polígonos TIRADOS da forma (a água apagou só aquele pedaço do fogo)."""
    p = _forma_base(forma, tamanho_m, largura_m, pontos)
    if recortes:
        p = p.subtracted(_caminho_poligonos(recortes))
    return p


def _forma_base(forma, tamanho_m, largura_m, pontos) -> QPainterPath:
    if forma == "livre":
        return _caminho_poligonos(pontos)
    L = max(0.25, float(tamanho_m)) * CELULA
    p = QPainterPath()
    if forma == "circulo":
        p.addEllipse(QPointF(0, 0), L, L)
    elif forma == "quadrado":
        p.addRect(QRectF(-L / 2, -L / 2, L, L))
    elif forma == "cone":   # cone do D&D: no fim, a largura é igual ao comprimento
        p.addPolygon(QPolygonF([QPointF(0, 0), QPointF(L, -L / 2), QPointF(L, L / 2)]))
        p.closeSubpath()
    else:  # linha
        w = max(0.25, float(largura_m)) * CELULA
        p.addRect(QRectF(0, -w / 2, L, w))
    return p


def _pontos_dentro(caminho: QPainterPath, n: int, semente: int) -> list[tuple]:
    rnd = random.Random(semente)
    r = caminho.boundingRect()
    pts = []
    tentativas = 0
    while len(pts) < n and tentativas < n * 30:
        tentativas += 1
        x = r.left() + rnd.random() * r.width()
        y = r.top() + rnd.random() * r.height()
        if caminho.contains(QPointF(x, y)):
            pts.append((x, y, rnd.random(), rnd.random()))
    return pts


def _cor(hexa, alfa):
    c = QColor(hexa)
    c.setAlpha(max(0, min(255, int(alfa))))
    return c


# ====================================================================== desenho
def _lingua(x, y, larg, alt, balanco):
    """Uma labareda (gota apontando pra cima, com a ponta balançando)."""
    c = QPainterPath()
    c.moveTo(x - larg, y)
    c.cubicTo(x - larg, y - alt * 0.5, x + balanco * 0.5 - larg * 0.3, y - alt * 0.72, x + balanco, y - alt)
    c.cubicTo(x + balanco * 0.5 + larg * 0.3, y - alt * 0.72, x + larg, y - alt * 0.5, x + larg, y)
    c.closeSubpath()
    return c


def _placas(pts, rnd):
    """Polígonos irregulares (crosta de lava, lascas de gelo) — calculados uma vez."""
    placas = []
    for x, y, a, b in pts:
        raio = CELULA * (0.3 + a * 0.32)
        n = rnd.randint(6, 8)
        giro = b * 6.28
        placas.append((x, y, [(math.cos(giro + k * 6.28 / n) * raio * rnd.uniform(0.7, 1.1),
                               math.sin(giro + k * 6.28 / n) * raio * rnd.uniform(0.7, 1.1)) for k in range(n)]))
    return placas


def _rachaduras(pts, rnd, passo):
    linhas = []
    for x, y, a, b in pts:
        ang = b * 6.28
        linha = [QPointF(x, y)]
        for _ in range(rnd.randint(3, 6)):
            ang += rnd.uniform(-0.8, 0.8)
            x, y = x + math.cos(ang) * passo * rnd.uniform(0.5, 1.2), y + math.sin(ang) * passo * rnd.uniform(0.5, 1.2)
            linha.append(QPointF(x, y))
        linhas.append(QPolygonF(linha))
    return linhas


def _tons(cor: str):
    """(clara, escura, bem escura) a partir de uma cor — pros detalhes das áreas de cor livre."""
    c = QColor(cor)
    return c.lighter(165).name(), c.darker(260).name(), c.darker(520).name()


def desenhar_efeito(painter: QPainter, caminho: QPainterPath, efeito: str, t: float,
                    semente: int = 1, cache: dict | None = None, forte: float = 1.0, cor_livre: str = ""):
    """
    Desenha o efeito animado dentro do caminho (coordenadas locais).
    Gráficos: baixo = simples e quase parado · médio = animado · alto = todas as camadas.
    cor_livre: a cor escolhida (só vale pra magia, luz, radiante e escuridão).
    """
    from ..graficos import nivel
    n = nivel()
    nome, cor, _, _ = EFEITOS.get(efeito, EFEITOS["magia"])
    livre = cor_valida(cor_livre) if efeito in CORES_LIVRES else ""
    if livre:
        cor = livre
    clara, escura, bem_escura = _tons(cor)
    r = caminho.boundingRect()
    tam = max(r.width(), r.height(), 1.0)
    centro = r.center()
    if cache is None:
        cache = {}
    area = (r.width() * r.height()) / (CELULA * CELULA)
    qtd = int(max(5, min((12, 28, 48)[n], area * (1.0, 1.9, 2.6)[n])))
    chave = (round(r.width()), round(r.height()), qtd, semente, efeito)
    if cache.get("chave") != chave:
        cache.clear()
        cache["chave"] = chave
        cache["pts"] = sorted(_pontos_dentro(caminho, qtd, semente), key=lambda q: q[1])
    pts = cache["pts"]
    F = forte
    if n == 0:
        t = math.floor(t * 3) / 3   # no modo leve, anima "aos pulinhos" (bem mais barato)
    p = painter
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setClipPath(caminho, Qt.ClipOperation.IntersectClip)
    p.setPen(Qt.PenStyle.NoPen)

    if efeito == "fogo":
        p.setBrush(_cor("#260902", 165 * F))
        p.drawPath(caminho)
        for x, y, a, b in pts:   # brasa no chão
            raio = CELULA * (0.7 + 0.25 * math.sin(t * 2.2 + a * 9))
            g = QRadialGradient(QPointF(x, y), raio)
            g.setColorAt(0, _cor("#ff7a18", 120 * F))
            g.setColorAt(1, _cor("#ff3a00", 0))
            p.setBrush(QBrush(g))
            p.drawEllipse(QPointF(x, y), raio, raio)
        for x, y, a, b in pts:   # labaredas (de trás pra frente)
            larg = CELULA * (0.2 + 0.16 * a)
            alt = CELULA * (0.6 + 0.55 * b) * (0.72 + 0.28 * math.sin(t * (6 + 3 * a) + b * 9))
            bal = math.sin(t * 4.2 + a * 7) * larg * 0.9
            g = QLinearGradient(x, y, x, y - alt)
            g.setColorAt(0, _cor("#ff4a0a", 215 * F))
            g.setColorAt(0.45, _cor("#ff9a1e", 190 * F))
            g.setColorAt(1, _cor("#ffe27a", 0))
            p.setBrush(QBrush(g))
            p.drawPath(_lingua(x, y, larg, alt, bal))
            if n >= 1:   # miolo claro
                g2 = QLinearGradient(x, y, x, y - alt * 0.6)
                g2.setColorAt(0, _cor("#fff6c0", 220 * F))
                g2.setColorAt(1, _cor("#ffd060", 0))
                p.setBrush(QBrush(g2))
                p.drawPath(_lingua(x, y, larg * 0.45, alt * 0.6, bal * 0.5))
        if n >= 1:   # fagulhas
            p.setBrush(_cor("#ffe890", 235 * F))
            for x, y, a, b in pts[::2] if n == 1 else pts:
                ciclo = (t * (0.5 + a * 0.7) + b) % 1.0
                p.setOpacity(1 - ciclo)
                p.drawEllipse(QPointF(x + math.sin(t * 3 + a * 9) * 8, y - ciclo * CELULA * 1.9), 1.7, 1.7)
            p.setOpacity(1.0)
        if n == 2:   # fumaça fina
            for x, y, a, b in pts[::3]:
                ciclo = (t * (0.18 + a * 0.12) + b) % 1.0
                raio = CELULA * (0.3 + ciclo * 0.6)
                g = QRadialGradient(QPointF(x, y - CELULA * (0.7 + ciclo * 1.3)), raio)
                g.setColorAt(0, QColor(30, 26, 24, int(70 * (1 - ciclo) * F)))
                g.setColorAt(1, QColor(30, 26, 24, 0))
                p.setBrush(QBrush(g))
                p.drawEllipse(QPointF(x + math.sin(t + a * 5) * 10, y - CELULA * (0.7 + ciclo * 1.3)), raio, raio)

    elif efeito == "lava":
        pulso = 0.8 + 0.2 * math.sin(t * 1.6)
        g = QRadialGradient(centro, tam * 0.7)
        g.setColorAt(0, _cor("#ff8a1a", 245 * F))
        g.setColorAt(0.6, _cor("#e2410a", 240 * F))
        g.setColorAt(1, _cor("#8a1c04", 240 * F))
        p.setBrush(QBrush(g))
        p.drawPath(caminho)
        for x, y, a, b in pts:   # veios mais quentes correndo devagar
            dx, dy = math.sin(t * 0.3 + a * 9) * CELULA * 0.3, math.cos(t * 0.25 + b * 9) * CELULA * 0.3
            raio = CELULA * (0.5 + 0.2 * math.sin(t * 0.9 + b * 7))
            g = QRadialGradient(QPointF(x + dx, y + dy), raio)
            g.setColorAt(0, _cor("#fff0a0", 170 * pulso * F))
            g.setColorAt(0.5, _cor("#ffb020", 90 * F))
            g.setColorAt(1, _cor("#ff6a00", 0))
            p.setBrush(QBrush(g))
            p.drawEllipse(QPointF(x + dx, y + dy), raio, raio)
        if "placas" not in cache:
            cache["placas"] = _placas(pts[::2] if n else pts[::3], random.Random(semente))
        for k, (x, y, verts) in enumerate(cache["placas"]):   # crosta escura boiando
            dx, dy = math.sin(t * 0.35 + k) * 4, math.cos(t * 0.3 + k * 2) * 4
            pol = QPolygonF([QPointF(x + dx + vx, y + dy + vy) for vx, vy in verts])
            p.setPen(QPen(_cor("#ffd060", 200 * pulso * F), 2.4))
            p.setBrush(_cor("#2a140c", 240 * F))
            p.drawPolygon(pol)
            if n >= 1:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(_cor("#4a2a1c", 200 * F))
                p.drawPolygon(QPolygonF([QPointF(x + dx + vx * 0.6 - 2, y + dy + vy * 0.6 - 2) for vx, vy in verts]))
        p.setPen(Qt.PenStyle.NoPen)
        if n >= 1:   # bolhas estourando
            for x, y, a, b in pts[1::3]:
                ciclo = (t * (0.35 + a * 0.3) + b) % 1.0
                if ciclo < 0.8:
                    rr = CELULA * 0.16 * (ciclo / 0.8)
                    g = QRadialGradient(QPointF(x - rr * 0.3, y - rr * 0.3), rr * 1.2)
                    g.setColorAt(0, _cor("#fff6c0", 240 * F))
                    g.setColorAt(1, _cor("#ff7a10", 230 * F))
                    p.setBrush(QBrush(g))
                    p.drawEllipse(QPointF(x, y), rr, rr)
                else:
                    k2 = (ciclo - 0.8) / 0.2
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.setPen(QPen(_cor("#ffe080", 220 * (1 - k2) * F), 2))
                    p.drawEllipse(QPointF(x, y), CELULA * (0.16 + 0.2 * k2), CELULA * (0.16 + 0.2 * k2))
                    p.setPen(Qt.PenStyle.NoPen)
        if n == 2:
            p.setBrush(_cor("#ffd070", 230 * F))
            for x, y, a, b in pts[::2]:
                ciclo = (t * (0.3 + a * 0.4) + b) % 1.0
                p.setOpacity(1 - ciclo)
                p.drawEllipse(QPointF(x + math.sin(t * 2 + a * 9) * 6, y - ciclo * CELULA * 1.2), 1.5, 1.5)
            p.setOpacity(1.0)

    elif efeito == "gelo":
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, _cor("#e6f6ff", 150 * F))
        g.setColorAt(0.5, _cor("#a8dcf6", 130 * F))
        g.setColorAt(1, _cor("#74b8e0", 150 * F))
        p.setBrush(QBrush(g))
        p.drawPath(caminho)
        p.setBrush(Qt.BrushStyle.NoBrush)   # geada na borda
        for larg, alfa in ((CELULA * 0.5, 40), (CELULA * 0.22, 80)):
            p.setPen(QPen(_cor("#ffffff", alfa * F), larg))
            p.drawPath(caminho)
        if "rach" not in cache:
            cache["rach"] = _rachaduras(pts[::2], random.Random(semente), CELULA * 0.45)
        for linha in cache["rach"]:   # rachaduras com profundidade
            p.setPen(QPen(_cor("#2a6a9a", 110 * F), 2.2))
            p.drawPolyline(linha.translated(1.2, 1.4))
            p.setPen(QPen(_cor("#ffffff", 190 * F), 1.2))
            p.drawPolyline(linha)
        if n >= 1:   # cristais de neve
            p.setPen(QPen(_cor("#ffffff", 170 * F), 1.3))
            for x, y, a, b in pts[1::2]:
                s = CELULA * (0.12 + a * 0.16)
                for k in range(6):
                    ang = b * 3.14 + k * math.pi / 3
                    ex, ey = x + math.cos(ang) * s, y + math.sin(ang) * s
                    p.drawLine(QPointF(x, y), QPointF(ex, ey))
                    for lado in (-0.6, 0.6):
                        mx, my = x + math.cos(ang) * s * 0.6, y + math.sin(ang) * s * 0.6
                        p.drawLine(QPointF(mx, my), QPointF(mx + math.cos(ang + lado) * s * 0.3,
                                                            my + math.sin(ang + lado) * s * 0.3))
            p.setPen(Qt.PenStyle.NoPen)   # brilhos piscando
            p.setBrush(_cor("#ffffff", 240 * F))
            for x, y, a, b in pts[::3]:
                br = max(0.0, math.sin(t * (1.5 + a * 2) + b * 20))
                if br > 0.05:
                    s = 2 + 7 * br
                    p.drawPolygon(QPolygonF([QPointF(x, y - s), QPointF(x + s * 0.2, y - s * 0.2), QPointF(x + s, y),
                                             QPointF(x + s * 0.2, y + s * 0.2), QPointF(x, y + s),
                                             QPointF(x - s * 0.2, y + s * 0.2), QPointF(x - s, y),
                                             QPointF(x - s * 0.2, y - s * 0.2)]))
        if n == 2:   # reflexo passando
            faixa = (t * 0.22 % 1.5 - 0.25) * tam
            g = QLinearGradient(r.left() + faixa - 40, r.top(), r.left() + faixa + 40, r.top() + 50)
            g.setColorAt(0, _cor("#ffffff", 0))
            g.setColorAt(0.5, _cor("#ffffff", 85 * F))
            g.setColorAt(1, _cor("#ffffff", 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(g))
            p.drawPath(caminho)

    elif efeito == "agua":
        g = QRadialGradient(centro, tam * 0.7)
        g.setColorAt(0, _cor("#2f86d8", 150 * F))
        g.setColorAt(1, _cor("#123f8c", 185 * F))
        p.setBrush(QBrush(g))
        p.drawPath(caminho)
        if n >= 1:   # reflexos de luz ondulando
            p.setBrush(Qt.BrushStyle.NoBrush)
            linhas = 7 if n == 1 else 13
            passo_y = r.height() / linhas
            for k in range(linhas):
                onda = QPainterPath()
                x = r.left()
                y0 = r.top() + (k + 0.5) * passo_y
                onda.moveTo(x, y0)
                while x < r.right():
                    x += 14
                    onda.lineTo(x, y0 + math.sin(x * 0.03 + t * 1.3 + k * 1.7) * 7 + math.sin(x * 0.07 - t * 0.8 + k) * 3)
                p.setPen(QPen(_cor("#c8ecff", (46 + 26 * math.sin(t + k)) * F), 2.0))
                p.drawPath(onda)
        p.setBrush(Qt.BrushStyle.NoBrush)   # ondinhas
        for x, y, a, b in pts[::2] if n < 2 else pts:
            ciclo = (t * 0.4 + a) % 1.0
            p.setPen(QPen(_cor("#e4f4ff", 170 * (1 - ciclo) * F), 1.5))
            p.drawEllipse(QPointF(x, y), ciclo * CELULA * 0.85, ciclo * CELULA * 0.5)
        for larg, alfa in ((CELULA * 0.3, 34), (CELULA * 0.12, 70 + 30 * math.sin(t * 1.5))):   # espuma na margem
            p.setPen(QPen(_cor("#eaf7ff", alfa * F), larg))
            p.drawPath(caminho)
        if n == 2:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(_cor("#ffffff", 220 * F))
            for x, y, a, b in pts[::3]:
                br = max(0.0, math.sin(t * 2.2 + b * 30))
                p.drawEllipse(QPointF(x + 6, y - 4), 1.6 * br, 1.6 * br)

    elif efeito in ("veneno", "acido"):
        acido = efeito == "acido"
        clara = "#f2ffb0" if acido else "#d9ffb0"
        g = QRadialGradient(centro, tam * 0.7)
        g.setColorAt(0, _cor(cor, (120 if acido else 95) * F))
        g.setColorAt(1, _cor(QColor(cor).darker(220).name(), 150 * F))
        p.setBrush(QBrush(g))
        p.drawPath(caminho)
        for k, (x, y, a, b) in enumerate(pts):   # gás rodando devagar
            ang = t * (0.12 + a * 0.1) + b * 6.28
            ox, oy = math.cos(ang) * CELULA * 0.35, math.sin(ang) * CELULA * 0.35
            raio = CELULA * (0.75 + 0.2 * math.sin(t * 0.8 + a * 6))
            g = QRadialGradient(QPointF(x + ox, y + oy), raio)
            g.setColorAt(0, _cor(clara if k % 3 == 0 else cor, 78 * F))
            g.setColorAt(1, _cor(cor, 0))
            p.setBrush(QBrush(g))
            p.drawEllipse(QPointF(x + ox, y + oy), raio, raio)
        for x, y, a, b in pts[::2] if n == 0 else pts:   # bolhas que sobem e estouram
            ciclo = (t * (0.5 + a * 0.6) + b) % 1.0
            yy = y - ciclo * CELULA * 0.6
            if ciclo < 0.85:
                rr = 2 + ciclo * 5
                p.setPen(QPen(_cor(clara, 200 * F), 1.2))
                p.setBrush(_cor(clara, 40 * F))
                p.drawEllipse(QPointF(x, yy), rr, rr)
                if n >= 1:
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(_cor("#ffffff", 190 * F))
                    p.drawEllipse(QPointF(x - rr * 0.35, yy - rr * 0.35), rr * 0.22, rr * 0.22)
            elif n >= 1:
                k2 = (ciclo - 0.85) / 0.15
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(_cor(clara, 200 * (1 - k2) * F), 1.4))
                p.drawEllipse(QPointF(x, yy), 7 + 9 * k2, 7 + 9 * k2)
        p.setPen(Qt.PenStyle.NoPen)
        if acido and n >= 1:   # chiado: pontinhos faiscando
            rnd = random.Random(int(t * 12) * 131 + semente)
            p.setBrush(_cor("#ffffd0", 230 * F))
            for _ in range(qtd // 2):
                x, y = rnd.choice(pts)[:2]
                p.drawEllipse(QPointF(x + rnd.uniform(-22, 22), y + rnd.uniform(-22, 22)), 1.3, 1.3)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(_cor(clara, 60 * F), CELULA * 0.16))
        p.drawPath(caminho)

    elif efeito == "eletrico":
        p.setBrush(_cor("#141a44", 110 * F))
        p.drawPath(caminho)
        pulso = 0.5 + 0.5 * math.sin(t * 9)
        for x, y, a, b in pts[::4]:
            raio = CELULA * (0.9 + 0.3 * pulso)
            g = QRadialGradient(QPointF(x, y), raio)
            g.setColorAt(0, _cor("#9fc4ff", 110 * F * (0.5 + 0.5 * math.sin(t * 7 + a * 20))))
            g.setColorAt(1, _cor("#5a8cff", 0))
            p.setBrush(QBrush(g))
            p.drawEllipse(QPointF(x, y), raio, raio)
        rnd = random.Random(int(t * (4, 9, 12)[n]) * 7919 + semente)
        for _ in range((2, 4, 7)[n]):
            x, y = rnd.choice(pts)[:2] if pts else (0, 0)
            ang = rnd.random() * 6.28
            pontos = [QPointF(x, y)]
            ramos = []
            for _k in range(7):
                ang += rnd.uniform(-0.9, 0.9)
                passo = CELULA * rnd.uniform(0.2, 0.45)
                x, y = x + math.cos(ang) * passo, y + math.sin(ang) * passo
                pontos.append(QPointF(x, y))
                if n >= 1 and rnd.random() < 0.35:   # galho
                    a2 = ang + rnd.choice((-1, 1)) * rnd.uniform(0.5, 1.1)
                    ramos.append(QPolygonF([QPointF(x, y), QPointF(x + math.cos(a2) * passo, y + math.sin(a2) * passo),
                                            QPointF(x + math.cos(a2 + 0.4) * passo * 1.7, y + math.sin(a2 + 0.4) * passo * 1.7)]))
            for linha, grosso in [(QPolygonF(pontos), 1.0)] + [(rm, 0.6) for rm in ramos]:
                p.setPen(QPen(_cor("#5a9cff", 110 * F), 7 * grosso, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                              Qt.PenJoinStyle.RoundJoin))
                p.drawPolyline(linha)
                p.setPen(QPen(_cor("#f4fbff", 245 * F), 1.9 * grosso))
                p.drawPolyline(linha)
            if n >= 1:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(_cor("#ffffff", 240 * F))
                p.drawEllipse(pontos[-1], 3, 3)
        p.setPen(Qt.PenStyle.NoPen)

    elif efeito == "trevas":
        # (cor livre: os véus e as faíscas ganham a cor escolhida; o miolo continua quase preto)
        veu = QColor(livre).darker(220).name() if livre else "#3a1e5c"
        faisca = livre or "#8a5cd0"
        borda = bem_escura if livre else "#1a0a2c"
        p.setBrush(_cor("#040207", 240 * F))
        p.drawPath(caminho)
        if n >= 1:   # véus girando
            p.setBrush(Qt.BrushStyle.NoBrush)
            for k in range(4 if n == 1 else 8):
                raio = tam * (0.12 + 0.055 * k)
                inicio = int((t * (9 + k * 3) * (1 if k % 2 else -1) + k * 70) * 16)
                p.setPen(QPen(_cor(veu, 85 * F), CELULA * 0.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawArc(QRectF(centro.x() - raio, centro.y() - raio, raio * 2, raio * 2), inicio, 110 * 16)
            p.setPen(Qt.PenStyle.NoPen)
            for x, y, a, b in pts[::2]:
                br = max(0.0, math.sin(t * (0.7 + a) + b * 20))
                p.setBrush(_cor(faisca, 150 * br * F))
                p.drawEllipse(QPointF(x, y), 1.6, 1.6)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(_cor(borda, 200 * F), CELULA * 0.35))
        p.drawPath(caminho)

    elif efeito == "fumaca":
        p.setBrush(_cor("#5e5e60", 150 * F))
        p.drawPath(caminho)
        for k, (x, y, a, b) in enumerate(pts):
            raio = CELULA * (0.95 + 0.28 * math.sin(t * 0.5 + a * 6))
            dx = math.sin(t * 0.25 + b * 6) * CELULA * 0.55
            dy = math.cos(t * 0.2 + a * 6) * CELULA * 0.35
            clara = k % 3 != 0
            g = QRadialGradient(QPointF(x + dx - raio * 0.2, y + dy - raio * 0.2), raio)
            g.setColorAt(0, _cor("#e0e0e2" if clara else "#3c3c40", (120 if clara else 110) * F))
            g.setColorAt(1, _cor("#bdbdc0" if clara else "#3c3c40", 0))
            p.setBrush(QBrush(g))
            p.drawEllipse(QPointF(x + dx, y + dy), raio, raio)

    elif efeito in ("luz", "sagrado"):
        pulso = 0.78 + 0.22 * math.sin(t * 2.0)
        g = QRadialGradient(centro, tam * 0.6)
        g.setColorAt(0, _cor("#ffffff", 150 * pulso * F))
        g.setColorAt(0.35, _cor(cor, 120 * pulso * F))
        g.setColorAt(1, _cor(cor, 40 * F))
        p.setBrush(QBrush(g))
        p.drawPath(caminho)
        raios = (0, 8, 14)[n] if efeito == "luz" else (6, 12, 18)[n]
        for k in range(raios):   # feixes girando
            ang = t * (0.22 if efeito == "luz" else 0.35) + k * 6.283 / raios
            abre = 0.09 if k % 2 else 0.05
            feixe = QPolygonF([centro, centro + QPointF(math.cos(ang - abre), math.sin(ang - abre)) * tam,
                               centro + QPointF(math.cos(ang + abre), math.sin(ang + abre)) * tam])
            g = QRadialGradient(centro, tam * 0.6)
            g.setColorAt(0, _cor(clara if livre else "#fffbe0", 95 * F))
            g.setColorAt(1, _cor(cor, 0))
            p.setBrush(QBrush(g))
            p.drawPolygon(feixe)
        if efeito == "sagrado" and n >= 1:   # anéis de luz abrindo
            p.setBrush(Qt.BrushStyle.NoBrush)
            for k in range(2):
                ciclo = (t * 0.35 + k * 0.5) % 1.0
                p.setPen(QPen(_cor(clara if livre else "#fff2b8", 170 * (1 - ciclo) * F), 3))
                p.drawEllipse(centro, tam * 0.5 * ciclo, tam * 0.5 * ciclo)
            p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_cor("#ffffff", 230 * F))
        for x, y, a, b in pts[::2] if n < 2 else pts:   # poeira de luz subindo
            ciclo = (t * (0.15 + a * 0.2) + b) % 1.0
            s = 1.2 + 2.2 * max(0.0, math.sin(t * 3 + a * 12))
            p.setOpacity(math.sin(ciclo * math.pi))
            p.drawEllipse(QPointF(x, y - ciclo * CELULA * 0.8), s, s)
        p.setOpacity(1.0)

    elif efeito == "teia":
        p.setBrush(_cor("#ffffff", 26 * F))
        p.drawPath(caminho)
        p.setBrush(Qt.BrushStyle.NoBrush)
        centros = pts[:: max(1, len(pts) // (2, 3, 4)[n])][:(2, 3, 4)[n]]
        for x, y, a, b in centros:
            raio = CELULA * (0.9 + a * 0.9)
            fios = 9
            p.setPen(QPen(_cor("#f4f4f4", 165 * F), 1.1))
            for k in range(fios):
                ang = b + k * 6.283 / fios
                p.drawLine(QPointF(x, y), QPointF(x + math.cos(ang) * raio, y + math.sin(ang) * raio))
            p.setPen(QPen(_cor("#f4f4f4", 120 * F), 0.9))
            for anel in (0.22, 0.4, 0.58, 0.76, 0.94):   # fios em arco (cedendo pro centro)
                teia = QPainterPath()
                for k in range(fios + 1):
                    ang = b + k * 6.283 / fios
                    pt = QPointF(x + math.cos(ang) * raio * anel, y + math.sin(ang) * raio * anel)
                    if k == 0:
                        teia.moveTo(pt)
                    else:
                        meio = b + (k - 0.5) * 6.283 / fios
                        teia.quadTo(QPointF(x + math.cos(meio) * raio * anel * 0.86, y + math.sin(meio) * raio * anel * 0.86), pt)
                p.drawPath(teia)
            if n >= 1:   # gotinhas brilhando
                p.setPen(Qt.PenStyle.NoPen)
                for k in range(fios):
                    ang = b + k * 6.283 / fios
                    br = 0.4 + 0.6 * max(0.0, math.sin(t * 1.5 + k * 2 + a * 9))
                    p.setBrush(_cor("#ffffff", 230 * br * F))
                    p.drawEllipse(QPointF(x + math.cos(ang) * raio * 0.58, y + math.sin(ang) * raio * 0.58), 1.6, 1.6)
                p.setBrush(Qt.BrushStyle.NoBrush)

    elif efeito == "planta":
        g = QRadialGradient(centro, tam * 0.7)
        g.setColorAt(0, _cor("#2c6a1a", 135 * F))
        g.setColorAt(1, _cor("#143a0c", 150 * F))
        p.setBrush(QBrush(g))
        p.drawPath(caminho)
        if "vinhas" not in cache:
            rnd = random.Random(semente)
            cache["vinhas"] = [(x, y, rnd.uniform(0, 6.28), rnd.uniform(0.8, 1.6), rnd.uniform(-1.2, 1.2))
                               for x, y, a, b in pts[::2]]
        for k, (x, y, ang, comp, curva) in enumerate(cache["vinhas"]):   # vinhas com folhas
            L = CELULA * comp
            bal = math.sin(t * 0.9 + k) * 0.12
            fim = QPointF(x + math.cos(ang + bal) * L, y + math.sin(ang + bal) * L)
            ctrl = QPointF(x + math.cos(ang + curva) * L * 0.6, y + math.sin(ang + curva) * L * 0.6)
            vinha = QPainterPath(QPointF(x, y))
            vinha.quadTo(ctrl, fim)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(_cor("#1c4a10", 230 * F), 4.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawPath(vinha)
            p.setPen(QPen(_cor("#4f9a32", 230 * F), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawPath(vinha)
            p.setPen(Qt.PenStyle.NoPen)
            for f in ((0.35, 0.7, 1.0) if n else (0.6, 1.0)):
                pt = vinha.pointAtPercent(f)
                p.save()
                p.translate(pt)
                p.rotate(vinha.angleAtPercent(min(0.99, f)) * -1 + (40 if int(f * 10) % 2 else -40) + bal * 60)
                p.setBrush(_cor("#6cc040" if f < 1 else "#8ad85a", 235 * F))
                folha = QPainterPath()
                folha.moveTo(0, 0)
                folha.quadTo(7, -6, 15, 0)
                folha.quadTo(7, 6, 0, 0)
                p.drawPath(folha)
                p.restore()
        if n >= 1:   # capim balançando
            for x, y, a, b in pts[1::2]:
                bal = math.sin(t * 1.4 + a * 6) * 0.3
                for k in range(3):
                    ang = -math.pi / 2 + (k - 1) * 0.5 + bal
                    comp = CELULA * (0.18 + b * 0.2)
                    p.setPen(QPen(_cor("#7ccc48", 210 * F), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                    p.drawLine(QPointF(x, y), QPointF(x + math.cos(ang) * comp, y + math.sin(ang) * comp))
        p.setPen(Qt.PenStyle.NoPen)

    else:  # magia: círculo rúnico girando
        p.setBrush(_cor(cor, 55 * F))
        p.drawPath(caminho)
        R = min(r.width(), r.height()) * 0.46
        pulso = 0.7 + 0.3 * math.sin(t * 1.4)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for raio, vel, marcas in ((1.0, 0.25, 12), (0.72, -0.4, 8)) if n else ((1.0, 0.2, 8),):
            rr = R * raio
            p.setPen(QPen(_cor(clara if livre else "#d9c2ff", 150 * pulso * F), 1.6))
            p.drawEllipse(centro, rr, rr)
            p.drawEllipse(centro, rr * 0.92, rr * 0.92)
            p.save()
            p.translate(centro)
            p.rotate(math.degrees(t * vel))
            for _k in range(marcas):
                p.rotate(360 / marcas)
                p.drawLine(QPointF(0, -rr * 0.99), QPointF(0, -rr * 0.93))
                p.drawPolygon(QPolygonF([QPointF(0, -rr * 0.9), QPointF(4, -rr * 0.86), QPointF(0, -rr * 0.82),
                                         QPointF(-4, -rr * 0.86)]))
            p.restore()
        if n >= 1:
            p.save()
            p.translate(centro)
            p.rotate(math.degrees(-t * 0.18))
            p.setPen(QPen(_cor(clara if livre else "#efe0ff", 110 * pulso * F), 1.3))
            p.drawPolyline(QPolygonF([QPointF(math.cos(k * 4 * math.pi / 5) * R * 0.66, math.sin(k * 4 * math.pi / 5) * R * 0.66)
                                      for k in range(6)]))
            p.restore()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_cor(clara if livre else "#efe0ff", 220 * F))
        for x, y, a, b in pts[::2] if n < 2 else pts:
            s = 1.2 + 2.2 * max(0.0, math.sin(t * 2.5 + a * 12))
            p.drawEllipse(QPointF(x, y), s, s)

    p.restore()


def desenhar_sobre(painter: QPainter, area: QRectF, efeito: str, t: float, semente: int,
                   cache: dict, redondo: bool = True):
    """Efeito em cima de um token (redondo) ou objeto (retângulo)."""
    if not efeito or efeito not in EFEITOS:
        return
    caminho = QPainterPath()
    if redondo:
        caminho.addEllipse(area)
    else:
        caminho.addRect(area)
    if efeito == "fogo":
        # labaredas saindo pra cima, um pouco pra fora do contorno
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        rnd = random.Random(semente)
        for k in range(9):
            a, b = rnd.random(), rnd.random()
            x = area.left() + area.width() * (0.12 + 0.76 * a)
            base = area.top() + area.height() * (0.35 + 0.55 * b)
            alt = area.height() * (0.35 + 0.25 * math.sin(t * (5 + a * 3) + b * 6))
            larg = area.width() * 0.16
            chama = QPainterPath()
            chama.moveTo(x - larg, base)
            chama.quadTo(x - larg * 0.6, base - alt * 0.6, x + math.sin(t * 4 + a * 7) * larg * 0.5, base - alt)
            chama.quadTo(x + larg * 0.6, base - alt * 0.6, x + larg, base)
            chama.closeSubpath()
            g = QRadialGradient(QPointF(x, base), alt)
            g.setColorAt(0, QColor(255, 245, 170, 230))
            g.setColorAt(0.5, QColor(255, 150, 40, 200))
            g.setColorAt(1, QColor(220, 50, 10, 60))
            painter.setBrush(QBrush(g))
            painter.drawPath(chama)
        painter.restore()
        return
    forte = 0.85
    desenhar_efeito(painter, caminho, efeito, t, semente, cache, forte)
    # contorno pra ficar claro que está "afetado"
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(_cor(EFEITOS[efeito][1], 220), 2.5))
    painter.drawPath(caminho)
    painter.restore()


def luz_de_efeito(efeito: str, x: float, y: float, uid: str, raio_m: float | None = None,
                  cor_livre: str = "") -> dict | None:
    """Luz que o efeito solta, na cor dele (magia/luz/radiante: a cor escolhida)."""
    tipo = LUZ_EFEITO.get(efeito)
    if not tipo:
        return None
    cor, tremula, fator = tipo
    if efeito in CORES_LIVRES and cor_valida(cor_livre):
        cor = cor_valida(cor_livre)
    fraco = (raio_m if raio_m is not None else 4) * fator
    return {"classe": "luz", "id": uid + ":luz", "x": x, "y": y, "tipo": "efeito", "forte": fraco / 2,
            "fraco": fraco, "cor": cor, "tremula": tremula, "acesa": True, "visivel": True}


# ====================================================================== item
class EfeitoItem(QGraphicsObject):
    """Área de efeito na mesa. pos() = origem (centro do círculo/quadrado, ponta do cone/linha)."""

    def __init__(self, efeito: str = "fogo", forma: str = "circulo", tamanho: float | None = None,
                 largura: float = 1.5, angulo: float = 0.0, dono: str = ""):
        super().__init__()
        self.uid = uuid.uuid4().hex
        self.efeito = efeito if efeito in EFEITOS else "magia"
        self.forma = forma if forma in FORMAS or forma == "livre" else "circulo"
        self.tamanho = float(tamanho if tamanho else TAMANHO_PADRAO.get(self.forma, 3))
        self.largura = float(largura)
        self.angulo = float(angulo)
        self.pontos = []            # forma "livre": polígonos (coordenadas locais)
        self.recortes = []          # polígonos tirados da forma (reação só onde encostou)
        self._cam_cache = None
        self._gas_t = -1.0          # gás: recorte das paredes (ver _atualizar_gas)
        self._gas_chave = None
        self._gas_final = None
        self._gas_versao = 0
        self.dono = dono            # "" = do mestre; senão, o jogador que colocou o template
        self.nome = ""              # opcional ("Bola de fogo do Aelar")
        self.cor = ""               # cor livre (magia, luz, radiante, escuridão); "" = a padrão
        self.mostrar_rotulo = True
        self.travado = False
        self._cache = {}
        self._semente = random.randint(1, 10 ** 6)
        self._desde = agora()       # parada no lugar desde quando (a marca no chão vai "pegando")
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable
                      | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
                      | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setRotation(self.angulo)
        animacao().registrar(self)
        from .efeitos3d import AREAS
        AREAS.add(self)   # partículas 3D (desenhadas pela camada das coisas altas)

    efeito_area = True   # marca pra linha de visão

    # --- o que os outros módulos perguntam
    def animado(self) -> bool:
        return True

    @property
    def ilumina(self) -> bool:
        return EFEITOS[self.efeito][2]

    @property
    def bloqueia(self) -> bool:
        if self.nome == NOME_VAPOR:   # vapor de reação: passageiro, não faz sombra dura
            return False
        return EFEITOS[self.efeito][3]

    def chave_forma(self) -> tuple:
        """Identifica a forma (pra caches: máscara do shader, partículas, contorno)."""
        return (self.forma, round(self.tamanho, 3), round(self.largura, 3),
                hash(str(self.pontos)) if self.pontos else 0, hash(str(self.recortes)) if self.recortes else 0,
                self._gas_versao)

    def caminho_base(self) -> QPainterPath:
        """A forma sem o recorte das paredes (gás)."""
        chave = self.chave_forma()[:5]
        if self._cam_cache is None or self._cam_cache[0] != chave:
            self._cam_cache = (chave, caminho_local(self.forma, self.tamanho, self.largura, self.pontos, self.recortes))
        return QPainterPath(self._cam_cache[1])

    def caminho(self) -> QPainterPath:
        base = self.caminho_base()
        self._atualizar_recorte()
        if self._gas_final is None:
            return base
        return QPainterPath(self._gas_final)

    def _atualizar_recorte(self):
        """O que corta a área (refaz no máx. ~3×/s, e só se algo mudou):
        - gás (veneno, fumaça) não atravessa parede/porta fechada (mesa/gas.py);
        - NENHUMA área existe fora do cenário (chão pintado + mapas, mesa/chao.py) — v0.45."""
        cena = self.scene()
        if cena is None:
            return
        # v0.45.1: mudou de LUGAR/forma/giro → refaz NA HORA. (Antes, com o intervalo de 0,3 s, a área
        # criada no (0,0) e logo levada pro clique ficava com o recorte velho: a "sala fantasma".)
        # Só a conta das paredes do gás (a parte cara) espera o intervalo.
        p = self.scenePos()
        rapida = (round(p.x()), round(p.y()), round(self.rotation()), self.chave_forma()[:5])
        t = agora()
        if rapida == getattr(self, "_recorte_rapida", None) and t - self._gas_t < 0.3:
            return
        self._recorte_rapida = rapida
        self._gas_t = t
        try:
            chao = cena.chao_caminho() if hasattr(cena, "chao_caminho") else None
            gas = self.efeito in GASES_AREA and hasattr(cena, "obstaculos_gas")
            obst = cena.obstaculos_gas() if gas else []
        except RuntimeError:
            return
        o, raio = (None, 0)
        if gas:
            from .gas import origem_e_raio
            o, raio = origem_e_raio(self)
        chave = rapida + (hash(tuple(obst)) if gas else 0,
                          getattr(cena, "_chao_versao", 0) if chao is not None else -1)
        if chave == self._gas_chave:
            return
        self._gas_chave = chave
        final = None
        if gas:
            from .gas import espalhar
            nuvem = espalhar(o.x(), o.y(), raio, obst)
            if nuvem is not None:
                final = self.caminho_base().intersected(self.mapFromScene(nuvem))
        if chao is not None:   # no vazio não existe efeito
            base = final if final is not None else self.caminho_base()
            if not chao.contains(self.mapToScene(base.boundingRect()).boundingRect()):
                final = base.intersected(self.mapFromScene(chao))
        if (final is None) != (self._gas_final is None) or final is not None:
            self._gas_final = final
            self._gas_versao += 1   # (máscara do shader, partículas, marca: tudo segue a forma nova)
            self._cache.clear()
            self.update()

    def recortar(self, caminho_cena: QPainterPath) -> bool:
        """Tira esse pedaço (na cena) da área. Devolve False se não sobrou quase nada."""
        self.gravar_se_marcou()   # o que já marcou o chão fica
        self.prepareGeometryChange()
        local = self.mapFromScene(caminho_cena)
        for pol in local.toFillPolygons():
            pts = [[round(pol.at(i).x(), 1), round(pol.at(i).y(), 1)] for i in range(pol.count())]
            if len(pts) >= 3:
                self.recortes.append(pts)
        self._cache.clear()
        self.update()
        self._mudou()
        from .reacoes import _area_caminho
        return _area_caminho(self.caminho()) > (0.3 * CELULA) ** 2

    def caminho_cena(self) -> QPainterPath:
        return self.mapToScene(self.caminho())

    def contem(self, ponto: QPointF) -> bool:
        return self.caminho().contains(self.mapFromScene(ponto))

    def centro_cena(self) -> QPointF:
        return self.mapToScene(self.caminho().boundingRect().center())

    def luz_dict(self) -> dict | None:
        if not self.ilumina or not self.isVisible():
            return None
        c = self.centro_cena()
        r = self.caminho().boundingRect()
        raio = max(r.width(), r.height()) / CELULA / 2 + 3
        return luz_de_efeito(self.efeito, c.x(), c.y(), self.uid, raio, self.cor)

    @property
    def cor_efetiva(self) -> str:
        """A cor que vale: a escolhida (se o efeito aceita cor livre) ou a do elemento."""
        if self.efeito in CORES_LIVRES and cor_valida(self.cor):
            return self.cor
        return EFEITOS[self.efeito][1]

    def descricao(self) -> str:
        nome = EFEITOS[self.efeito][0]
        medida = f"{self.tamanho:g} m" + (f" × {self.largura:g} m" if self.forma == "linha" else "")
        if self.forma == "livre":
            return f"{nome} · forma livre"
        forma = {"circulo": "raio", "quadrado": "lado", "cone": "cone", "linha": "linha"}[self.forma]
        return f"{nome} · {forma} {medida}"

    # --- mudanças
    # --- marca no chão (mesa/marcas.py): parada no lugar, o chão vai pegando; apagou/moveu, fica
    def forca_marca(self) -> float:
        """0 → 1: o quanto o chão embaixo já 'pegou' o efeito."""
        from .marcas import ATRASO, MARCA_DO_EFEITO, TEMPO_QUEIMA
        if self.efeito not in MARCA_DO_EFEITO:
            return 0.0
        return max(0.0, min(1.0, (agora() - self._desde - ATRASO) / TEMPO_QUEIMA))

    def gravar_se_marcou(self):
        """Só no mestre (a cena dele sabe gravar): a marca vira parte do terreno."""
        cena = self.scene()
        if cena is not None and hasattr(cena, "gravar_marca") and self.isVisible() and self.forca_marca() >= 1.0:
            try:
                cena.gravar_marca(self)
            except Exception as erro:
                from ..seguranca import registrar_erro
                registrar_erro(f"Marca no chão não gravou: {erro!r}")
        self._desde = agora()

    def _pintar_marca(self, painter: QPainter):
        forca = self.forca_marca()
        if forca <= 0:
            return
        from ..graficos import nivel
        if nivel() < 1:
            return
        from PyQt6.QtGui import QPaintEngine
        from .marcas import desenhar, imagem, op_da_area
        op = op_da_area(self)
        if not op:
            return
        img_m, img_c, r = imagem(op["k"], op["p"], op["s"], op.get("c", ""))
        inv, ok = self.sceneTransform().inverted()
        if not ok:
            return
        motor = painter.paintEngine()
        multiplica = motor is None or motor.type() != QPaintEngine.Type.OpenGL2
        painter.save()
        painter.setWorldTransform(inv * painter.worldTransform())   # a marca é desenhada na cena
        painter.setOpacity(forca)
        desenhar(painter, img_m, img_c, r, multiplica)
        painter.restore()

    def aplicar(self, efeito=None, forma=None, tamanho=None, largura=None, angulo=None, nome=None, cor=None):
        self.gravar_se_marcou()   # mudou a área: o que já marcou fica, e recomeça
        self.prepareGeometryChange()
        if cor is not None:
            self.cor = cor_valida(cor)
        if efeito in EFEITOS:
            self.efeito = efeito
        antes = (self.forma, self.tamanho, self.largura)
        if forma in FORMAS or (forma == "livre" and self.pontos):
            self.forma = forma
        if tamanho is not None:
            self.tamanho = max(0.25, float(tamanho))
        if largura is not None:
            self.largura = max(0.25, float(largura))
        if antes != (self.forma, self.tamanho, self.largura):   # forma refeita: sem recortes
            self.recortes = []
            if self.forma != "livre":
                self.pontos = []
        if angulo is not None:
            self.angulo = float(angulo) % 360
            self.setRotation(self.angulo)
        if nome is not None:
            self.nome = nome
        self._cache.clear()
        self.update()
        self._mudou()

    def _mudou(self):
        cena = self.scene()
        if cena is not None and hasattr(cena, "marcar_modificada"):
            cena.marcar_modificada()
            if hasattr(cena, "mesa_mudou"):
                cena.mesa_mudou.emit()
        if cena is not None and hasattr(cena, "area_mudou"):
            cena.area_mudou(self)   # (só o mestre) — reações entre áreas

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene() is not None:
            if value != self.pos():
                self.gravar_se_marcou()   # vai sair do lugar: se o chão já pegou, a marca fica
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._mudou()
        return super().itemChange(change, value)

    def aplicar_trava(self, travado: bool):
        self.travado = travado
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not travado)

    def mouseDoubleClickEvent(self, event):
        cena = self.scene()
        if cena is not None and hasattr(cena, "editar_efeito_pedido"):
            cena.editar_efeito_pedido.emit(self)
        event.accept()

    # --- desenho
    def boundingRect(self) -> QRectF:
        folga = CELULA
        from . import camera3d
        if camera3d.ligada():   # partículas 3D sobem até ~3 m e se deslocam na perspectiva
            folga += camera3d.margem(3 * CELULA)
        return self.caminho_base().boundingRect().adjusted(-folga, -folga, folga, folga)

    def shape(self) -> QPainterPath:
        # a forma inteira (mesmo o pedaço no vazio): o mestre consegue clicar pra mover/apagar
        return self.caminho_base()

    def paint(self, painter: QPainter, option, widget=None):
        caminho = self.caminho()
        try:
            self._pintar_marca(painter)   # o chão embaixo pegando (queimando, congelando…)
        except Exception as erro:   # (erro dentro de paint() fecha o programa)
            from ..seguranca import registrar_erro
            registrar_erro(f"Marca da área não desenhou: {erro!r}")
            self._desde = float("inf")
        from . import efeitos_gl
        # Mesa 3D na placa de vídeo: a superfície da área é um shader animado; senão, o desenho 2D
        if not (efeitos_gl.ativo(painter) and efeitos_gl.desenhar(painter, self)):
            desenhar_efeito(painter, caminho, self.efeito, agora(), self._semente, self._cache, cor_livre=self.cor)
        cor = QColor(self.cor_efetiva)
        if self.efeito == "trevas":
            cor = QColor(self.cor_efetiva).lighter(260) if cor_valida(self.cor) else QColor("#6a4c90")
        cor.setAlpha(230 if self.isSelected() else 150)
        caneta = QPen(cor, 3 if self.isSelected() else 1.6,
                      Qt.PenStyle.SolidLine if self.isSelected() else Qt.PenStyle.DashLine)
        caneta.setCosmetic(True)
        painter.setPen(caneta)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if caminho.isEmpty() and self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable:
            # arrastada toda pro vazio: sem efeito, só o contorno apagadinho pro mestre achar e apagar
            caneta.setStyle(Qt.PenStyle.DotLine)
            painter.setPen(caneta)
            painter.setOpacity(0.5)
            painter.drawPath(self.caminho_base())
            painter.setOpacity(1.0)
        painter.drawPath(caminho)
        if self.mostrar_rotulo and (self.nome or self.dono):
            texto = self.nome or self.dono
            painter.save()
            c = caminho.boundingRect().center()
            painter.translate(c)
            painter.rotate(-self.rotation())
            fonte = QFont()
            fonte.setPixelSize(11)
            fonte.setBold(True)
            painter.setFont(fonte)
            larg = painter.fontMetrics().horizontalAdvance(texto) + 12
            placa = QRectF(-larg / 2, -10, larg, 20)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(18, 14, 11, 200))
            painter.drawRoundedRect(placa, 5, 5)
            painter.setPen(QColor(240, 228, 205))
            painter.drawText(placa, Qt.AlignmentFlag.AlignCenter, texto)
            painter.restore()

    # --- salvar / rede
    def para_dict(self) -> dict:
        p = self.pos()
        return {"classe": "efeito", "id": self.uid, "x": p.x(), "y": p.y(), "z": self.zValue(),
                "efeito": self.efeito, "forma": self.forma, "tamanho": self.tamanho,
                "largura": self.largura, "angulo": self.angulo, "dono": self.dono, "nome": self.nome,
                "visivel": self.isVisible(), "semente": self._semente, "cor": self.cor,
                "pontos": self.pontos, "recortes": self.recortes}

    @staticmethod
    def _poligonos(v) -> list:
        """Lista de polígonos vinda do arquivo/rede, conferida (nada de lixo derrubando o desenho)."""
        saida = []
        for pol in (v or [])[:64]:
            try:
                pts = [[float(x), float(y)] for x, y in pol][:400]
            except (TypeError, ValueError):
                continue
            if len(pts) >= 3:
                saida.append(pts)
        return saida

    def aplicar_dict(self, d: dict):
        antes = (self.efeito, self.chave_forma(), self.angulo)
        self.prepareGeometryChange()
        self.efeito = d.get("efeito", self.efeito) if d.get("efeito") in EFEITOS else self.efeito
        self.pontos = self._poligonos(d.get("pontos"))
        self.recortes = self._poligonos(d.get("recortes"))
        forma = d.get("forma", self.forma)
        self.forma = forma if forma in FORMAS or (forma == "livre" and self.pontos) else self.forma
        self.tamanho = float(d.get("tamanho", self.tamanho))
        self.largura = float(d.get("largura", self.largura))
        self.angulo = float(d.get("angulo", self.angulo))
        self.setRotation(self.angulo)
        self.dono = d.get("dono", "")
        self.nome = d.get("nome", "")
        self.cor = cor_valida(d.get("cor", ""))
        self._semente = int(d.get("semente", self._semente))
        if antes != (self.efeito, self.chave_forma(), self.angulo):
            self._desde = agora()   # (no jogador: mudou a área, a marca recomeça)
        self._cache.clear()
        self.update()

    @classmethod
    def de_dict(cls, d: dict) -> "EfeitoItem":
        item = cls()
        item.aplicar_dict(d)
        item.uid = d.get("id") or item.uid
        item.setPos(float(d.get("x", 0)), float(d.get("y", 0)))
        item.setZValue(d.get("z", 0))
        item.setVisible(d.get("visivel", True))
        return item


# ====================================================================== visão e luz (dicts da rede também)
def _caminho_de(d) -> QPainterPath:
    if isinstance(d, EfeitoItem):
        return d.caminho_cena()
    from PyQt6.QtGui import QTransform
    t = QTransform()
    t.translate(float(d["x"]), float(d["y"]))
    t.rotate(float(d.get("angulo", 0)))
    return t.map(caminho_local(d.get("forma", "circulo"), d.get("tamanho", 3), d.get("largura", 1.5),
                               d.get("pontos"), d.get("recortes")))


def obstaculos_de_efeito(d) -> list[tuple]:
    """Escuridão/fumaça: o contorno da área vira 'parede' pra visão."""
    if isinstance(d, EfeitoItem):
        if not d.bloqueia or not d.isVisible():
            return []
    elif (not EFEITOS.get(d.get("efeito"), EFEITOS["magia"])[3] or not d.get("visivel", True)
          or d.get("nome") == NOME_VAPOR):
        return []
    poligonos = _caminho_de(d).toSubpathPolygons()
    segs = []
    for pol in poligonos:
        pts = [pol[i] for i in range(pol.count())]
        if len(pts) > 40:   # círculo: simplifica
            passo = len(pts) / 40
            pts = [pts[int(k * passo)] for k in range(40)]
        for k in range(len(pts)):
            a, b = pts[k], pts[(k + 1) % len(pts)]
            if a != b:
                segs.append((a.x(), a.y(), b.x(), b.y()))
    return segs


def luz_de_dict(d: dict) -> dict | None:
    if not d.get("visivel", True) or not EFEITOS.get(d.get("efeito"), EFEITOS["magia"])[2]:
        return None
    r = _caminho_de(d).boundingRect()
    raio = max(r.width(), r.height()) / CELULA / 2 + 3
    return luz_de_efeito(d["efeito"], r.center().x(), r.center().y(), d.get("id", ""), raio, d.get("cor", ""))


def esta_dentro(d, ponto: QPointF) -> bool:
    return _caminho_de(d).contains(ponto)
