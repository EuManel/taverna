"""
Materiais de chão e parede, desenhados pelo próprio programa.

Cada material vira uma textura pequena que se repete sem emenda (tile).
Elas são geradas uma vez e guardadas em cache.
"""

import math
import random
import zlib

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QBrush, QColor, QLinearGradient, QPainter, QPainterPath,
                         QPen, QPixmap, QPolygonF, QRadialGradient, QTransform)

TAM_CHAO = 64     # = 1 quadrado
TAM_PAREDE = 32


# ====================================================================== helpers
def _c(hex_, alfa=255):
    c = QColor(hex_)
    c.setAlpha(alfa)
    return c


def _repetir(tam, x, y, desenhar):
    """Desenha nas 9 posições pra textura emendar nas bordas."""
    for dx in (-tam, 0, tam):
        for dy in (-tam, 0, tam):
            desenhar(x + dx, y + dy)


def _pontos(p, rnd, tam, n, cores, rmin, rmax, alfa=(30, 90)):
    p.setPen(Qt.PenStyle.NoPen)
    for _ in range(n):
        x, y = rnd.uniform(0, tam), rnd.uniform(0, tam)
        r = rnd.uniform(rmin, rmax)
        p.setBrush(_c(rnd.choice(cores), rnd.randint(*alfa)))
        _repetir(tam, x, y, lambda a, b: p.drawEllipse(QPointF(a, b), r, r))


def _base(tam, cor):
    pm = QPixmap(tam, tam)
    pm.fill(QColor(cor))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    return pm, p


# ====================================================================== chãos
def _areia(p, rnd, t):
    _pontos(p, rnd, t, 260, ["#e9d6a3", "#a88d58", "#f4e6bd"], 0.5, 1.4)
    p.setBrush(Qt.BrushStyle.NoBrush)
    for k in range(3):
        y0 = 12 + k * 20 + rnd.uniform(-3, 3)
        cam = QPainterPath(QPointF(-2, y0))
        for x in range(0, t + 3, 2):
            cam.lineTo(x, y0 + 3 * math.sin(2 * math.pi * x / t + k))
        p.setPen(QPen(_c("#f2e2b5", 70), 1.4))
        p.drawPath(cam)


def _terra(p, rnd, t):
    _pontos(p, rnd, t, 22, ["#4a3522", "#7d5e41"], 3, 7, (40, 90))
    _pontos(p, rnd, t, 180, ["#3d2b1b", "#8a6a4b"], 0.6, 1.6)
    _pontos(p, rnd, t, 9, ["#8a8378", "#6f685f"], 1.2, 2.4, (150, 220))


def _grama(p, rnd, t):
    _pontos(p, rnd, t, 18, ["#3c6427", "#5f8f3f"], 5, 10, (50, 110))
    for _ in range(240):
        x, y = rnd.uniform(0, t), rnd.uniform(0, t)
        dx, dy = rnd.uniform(-2.5, 2.5), rnd.uniform(-6, -3)
        cor = _c(rnd.choice(["#7fb055", "#3a6a24", "#96c46a", "#2f5a1f"]), rnd.randint(120, 220))
        p.setPen(QPen(cor, 1.1))
        _repetir(t, x, y, lambda a, b: p.drawLine(QPointF(a, b), QPointF(a + dx, b + dy)))


def _laje(p, rnd, t):
    """
    4 lajes de pedra de verdade (v0.34.2): cantos levemente tortos, superfície manchada e granulada,
    lascas nas bordas e rachaduras finas; argamassa com grão. Antes eram retângulos perfeitos com
    degradê liso — pareciam azulejo de plástico (o Manel reparou com a luz nova).
    """
    # argamassa (o fundo) com grão
    _pontos(p, rnd, t, 120 * (t // 64) ** 2, ["#2c2925", "#4a453f", "#3a3631"], 0.5, 1.4, (60, 140))
    # grade de cantos com tremidinha (lajes de 32 px = meio metro); o canto da borda é o mesmo do
    # começo, então a textura emenda certinho. Textura de 128 px = 16 lajes diferentes antes de repetir.
    n = max(1, t // 32)
    trem = {(i, j): QPointF(rnd.uniform(-2.2, 2.2), rnd.uniform(-2.2, 2.2)) for i in range(n) for j in range(n)}
    canto = lambda i, j: QPointF(i * 32, j * 32) + trem[(i % n, j % n)]
    for (i, j) in ((a_, b_) for a_ in range(n) for b_ in range(n)):
        a, b, c_, d = canto(i, j), canto(i + 1, j), canto(i + 1, j + 1), canto(i, j + 1)
        centro = (a + b + c_ + d) / 4
        # encolhe pro centro (a junta) e entorta os lados um pouquinho
        pts = []
        for p0, p1 in ((a, b), (b, c_), (c_, d), (d, a)):
            q0 = p0 + (centro - p0) * 0.06
            q1 = p1 + (centro - p1) * 0.06
            meio = (q0 + q1) / 2 + (centro - (q0 + q1) / 2) * rnd.uniform(-0.03, 0.04)
            pts += [q0, meio]
        laje = QPolygonF(pts)
        base = QColor(rnd.choice(["#7d7871", "#8a847b", "#6c6761", "#938c82", "#77716a", "#827a6e", "#6f6a66"]))
        caminho = QPainterPath()
        caminho.addPolygon(laje)
        caminho.closeSubpath()
        for dx in (-t, 0, t):            # desenha nas 9 posições (emenda nas bordas)
            for dy in (-t, 0, t):
                p.save()
                p.translate(dx, dy)
                p.setClipPath(caminho)
                p.fillPath(caminho, base)
                r2 = random.Random(hash((i, j)) & 0xFFFF)
                # manchas grandes e médias (pedra nunca é de uma cor só)
                for _ in range(9):
                    q = centro + QPointF(r2.uniform(-14, 14), r2.uniform(-14, 14))
                    raio = r2.uniform(4, 12)
                    g = QRadialGradient(q, raio)
                    tom = base.darker(r2.randint(115, 145)) if r2.random() < 0.6 else base.lighter(r2.randint(110, 125))
                    g.setColorAt(0, _c(tom.name(), 170))
                    g.setColorAt(1, _c(tom.name(), 0))
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QBrush(g))
                    p.drawEllipse(q, raio, raio)
                # grão fino
                for _ in range(90):
                    q = centro + QPointF(r2.uniform(-16, 16), r2.uniform(-16, 16))
                    p.setBrush(_c(r2.choice(["#b9b2a7", "#5a554e", "#9b958b", "#46423c"]), r2.randint(50, 130)))
                    rr = r2.uniform(0.35, 0.9)
                    p.drawEllipse(q, rr, rr)
                # rachadura fina (nem toda laje tem)
                if r2.random() < 0.55:
                    q = centro + QPointF(r2.uniform(-10, 10), r2.uniform(-10, 10))
                    cam = QPainterPath(q)
                    ang = r2.uniform(0, 6.28)
                    for _ in range(4):
                        ang += r2.uniform(-0.9, 0.9)
                        q = q + QPointF(math.cos(ang) * r2.uniform(2.5, 5), math.sin(ang) * r2.uniform(2.5, 5))
                        cam.lineTo(q)
                    p.setPen(QPen(_c("#2f2b27", 150), 0.7))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.drawPath(cam)
                # lascas na borda
                p.setPen(Qt.PenStyle.NoPen)
                for _ in range(3):
                    k = r2.randrange(len(pts))
                    q = pts[k] + (centro - pts[k]) * r2.uniform(0.02, 0.08)
                    p.setBrush(_c("#3a3631", 170))
                    p.drawEllipse(q, r2.uniform(0.8, 1.8), r2.uniform(0.8, 1.6))
                p.restore()


def _madeira(p, rnd, t):
    altura = t // 4
    for k in range(4):
        y = k * altura
        cor = QColor(rnd.choice(["#7a5232", "#6b4529", "#86603c", "#734b2d"]))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(cor)
        p.drawRect(QRectF(0, y, t, altura))
        for _ in range(4):
            yy = y + rnd.uniform(2, altura - 2)
            p.setPen(QPen(cor.darker(125), 0.8))
            cam = QPainterPath(QPointF(0, yy))
            fase = rnd.uniform(0, 6)
            for x in range(0, t + 2, 2):
                cam.lineTo(x, yy + 0.8 * math.sin(2 * math.pi * x / t * 2 + fase))
            p.drawPath(cam)
        p.setPen(QPen(_c("#2b1b10", 200), 1.2))
        p.drawLine(QPointF(0, y + 0.5), QPointF(t, y + 0.5))
        junta = rnd.uniform(8, t - 8)
        p.drawLine(QPointF(junta, y), QPointF(junta, y + altura))


def _agua(p, rnd, t):
    g = QLinearGradient(0, 0, t, t)
    g.setColorAt(0, QColor("#2f6a8c"))
    g.setColorAt(1, QColor("#244f6e"))
    p.fillRect(QRectF(0, 0, t, t), QBrush(g))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for _ in range(9):
        x, y = rnd.uniform(0, t), rnd.uniform(0, t)
        w = rnd.uniform(8, 16)
        p.setPen(QPen(_c("#9fd3ee", rnd.randint(60, 130)), 1.2))
        _repetir(t, x, y, lambda a, b: p.drawArc(QRectF(a, b, w, w * 0.45), 20 * 16, 140 * 16))


def _concreto(p, rnd, t):
    _pontos(p, rnd, t, 300, ["#a7a5a0", "#6f6d69", "#bdbab4"], 0.4, 1.2)
    p.setPen(QPen(_c("#5c5a56", 120), 0.9))
    x, y = rnd.uniform(10, 50), 0
    for _ in range(5):
        nx, ny = x + rnd.uniform(-6, 6), y + rnd.uniform(6, 14)
        p.drawLine(QPointF(x, y), QPointF(nx, ny))
        x, y = nx, ny


def _asfalto(p, rnd, t):
    _pontos(p, rnd, t, 380, ["#6a6a6e", "#1f1f22", "#8c8c90"], 0.4, 1.1, (60, 160))


def _ceramica(p, rnd, t):
    for (x, y) in ((0, 0), (32, 0), (0, 32), (32, 32)):
        cor = QColor(rnd.choice(["#d9d4c9", "#d2ccc0", "#ded9cf"]))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(cor)
        p.drawRect(QRectF(x + 1, y + 1, 30, 30))
        p.setBrush(_c("#ffffff", 40))
        p.drawRect(QRectF(x + 2, y + 2, 14, 6))


def _carpete(p, rnd, t):
    _pontos(p, rnd, t, 500, ["#7d3a40", "#4f2025", "#8f4a50"], 0.4, 0.9, (80, 180))


def _placa_metal(p, rnd, t):
    g = QLinearGradient(0, 0, t, t)
    g.setColorAt(0, QColor("#6e767f"))
    g.setColorAt(1, QColor("#4f565e"))
    p.fillRect(QRectF(0, 0, t, t), QBrush(g))
    p.setPen(QPen(_c("#8f98a2", 150), 1.4))
    for i in range(4):
        for j in range(4):
            cx, cy = i * 16 + 8, j * 16 + 8
            if (i + j) % 2:
                p.drawLine(QPointF(cx - 4, cy - 2), QPointF(cx + 4, cy + 2))
            else:
                p.drawLine(QPointF(cx - 4, cy + 2), QPointF(cx + 4, cy - 2))
    p.setPen(QPen(_c("#2c3137", 200), 1.5))
    p.drawRect(QRectF(0.75, 0.75, t - 1.5, t - 1.5))
    p.setBrush(_c("#a9b2bc"))
    p.setPen(Qt.PenStyle.NoPen)
    for (x, y) in ((4, 4), (t - 4, 4), (4, t - 4), (t - 4, t - 4)):
        p.drawEllipse(QPointF(x, y), 1.6, 1.6)


def _grade(p, rnd, t):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(_c("#3a424c"))
    for k in range(0, t, 8):
        p.drawRect(QRectF(k, 0, 3, t))
        p.drawRect(QRectF(0, k, t, 3))
    p.setBrush(_c("#6d7782", 120))
    for k in range(0, t, 8):
        p.drawRect(QRectF(k, 0, 1, t))


def _painel_neon(p, rnd, t):
    for (x, y) in ((0, 0), (32, 0), (0, 32), (32, 32)):
        r = QRectF(x + 2, y + 2, 28, 28)
        p.setPen(QPen(_c("#38e1ff", 60), 3))
        p.setBrush(_c("#141c2a"))
        p.drawRect(r)
        p.setPen(QPen(_c("#7ff0ff", 170), 1))
        p.drawRect(r)


def _vidro_piso(p, rnd, t):
    p.setPen(QPen(_c("#e8f7ff", 90), 2))
    p.drawLine(QPointF(6, 0), QPointF(0, 6))
    p.drawLine(QPointF(40, 0), QPointF(0, 40))
    p.drawLine(QPointF(64, 30), QPointF(30, 64))
    p.setPen(QPen(_c("#5f8797", 160), 1))
    p.drawRect(QRectF(0.5, 0.5, t - 1, t - 1))


def _cristal(p, rnd, t):
    pts = [QPointF(rnd.uniform(0, t), rnd.uniform(0, t)) for _ in range(10)]
    cantos = [QPointF(0, 0), QPointF(t, 0), QPointF(0, t), QPointF(t, t)]
    todos = pts + cantos
    p.setPen(QPen(_c("#c9b0ff", 90), 0.8))
    for a in todos:
        vizinhos = sorted(todos, key=lambda b: (a.x() - b.x()) ** 2 + (a.y() - b.y()) ** 2)[1:3]
        tri = QPolygonF([a] + vizinhos)
        p.setBrush(_c(rnd.choice(["#4b347a", "#5d3f99", "#3b2a62", "#6a52b0", "#3c5a8a"]), 190))
        p.drawPolygon(tri)
    _pontos(p, rnd, t, 14, ["#e9dcff", "#8ff3ff"], 0.6, 1.2, (150, 255))


def _marmore(p, rnd, t):
    p.setBrush(Qt.BrushStyle.NoBrush)
    for _ in range(4):
        y0 = rnd.uniform(0, t)
        fase, amp = rnd.uniform(0, 6), rnd.uniform(4, 9)
        cam = QPainterPath(QPointF(0, y0))
        for x in range(0, t + 2, 2):
            cam.lineTo(x, y0 + amp * math.sin(2 * math.pi * x / t + fase))
        p.setPen(QPen(_c("#b48cff", rnd.randint(70, 140)), rnd.uniform(0.8, 1.8)))
        p.drawPath(cam)
    _pontos(p, rnd, t, 120, ["#3c2f5c", "#18122a"], 0.5, 1.5)


def _runas(p, rnd, t):
    _laje(p, rnd, t)
    p.fillRect(QRectF(0, 0, t, t), _c("#2a1f40", 120))
    for (x, y) in ((16, 16), (48, 48)):
        p.setPen(QPen(_c("#b58cff", 70), 4))
        _runa(p, x, y)
        p.setPen(QPen(_c("#e2d0ff", 220), 1.2))
        _runa(p, x, y)


def _runa(p, x, y):
    p.drawLine(QPointF(x, y - 7), QPointF(x, y + 7))
    p.drawLine(QPointF(x, y - 7), QPointF(x + 5, y - 2))
    p.drawLine(QPointF(x, y), QPointF(x - 5, y + 4))


def _musgo(p, rnd, t):
    _pontos(p, rnd, t, 20, ["#1f3a24", "#2d4f2f"], 4, 9, (80, 160))
    _pontos(p, rnd, t, 18, ["#8fffb0"], 1.5, 3.5, (20, 50))
    _pontos(p, rnd, t, 18, ["#c8ffd8"], 0.5, 1.1, (160, 255))


# ---------------------------------------------------------------- chãos extras
def _lava(p, rnd, t):
    g = QRadialGradient(QPointF(t / 2, t / 2), t * 0.8)
    g.setColorAt(0, QColor("#ffb22e"))
    g.setColorAt(0.5, QColor("#ff5a12"))
    g.setColorAt(1, QColor("#b8200a"))
    p.fillRect(QRectF(0, 0, t, t), QBrush(g))
    # crosta escura rachada por cima
    for _ in range(7):
        x, y = rnd.uniform(0, t), rnd.uniform(0, t)
        larg, alt = rnd.uniform(10, 22), rnd.uniform(8, 16)
        cor = _c(rnd.choice(["#2a120c", "#3b1a10", "#1e0e0a"]), 235)
        def crosta(a, b, larg=larg, alt=alt, cor=cor):
            p.setPen(QPen(_c("#ffcf5a", 160), 1.2))
            p.setBrush(cor)
            p.drawRoundedRect(QRectF(a, b, larg, alt), 4, 4)
        _repetir(t, x, y, crosta)
    _pontos(p, rnd, t, 14, ["#fff3a0"], 0.6, 1.4, (160, 255))


def _gelo(p, rnd, t):
    g = QLinearGradient(0, 0, t, t)
    g.setColorAt(0, QColor("#cfeefa"))
    g.setColorAt(1, QColor("#9fd2ea"))
    p.fillRect(QRectF(0, 0, t, t), QBrush(g))
    p.setPen(QPen(_c("#ffffff", 170), 1))
    for _ in range(6):
        x, y = rnd.uniform(0, t), rnd.uniform(0, t)
        nx, ny = x + rnd.uniform(-16, 16), y + rnd.uniform(-16, 16)
        _repetir(t, x, y, lambda a, b, nx=nx - x, ny=ny - y:
                 p.drawLine(QPointF(a, b), QPointF(a + nx, b + ny)))
    _pontos(p, rnd, t, 30, ["#ffffff"], 0.5, 1.2, (80, 200))


def _neve(p, rnd, t):
    _pontos(p, rnd, t, 40, ["#dfe8f0", "#ffffff"], 3, 7, (60, 140))
    _pontos(p, rnd, t, 120, ["#b9c8d6", "#ffffff"], 0.5, 1.3, (60, 160))


def _lama(p, rnd, t):
    _pontos(p, rnd, t, 26, ["#3a2a1a", "#5a4228"], 4, 9, (70, 140))
    _pontos(p, rnd, t, 10, ["#8a7a5a"], 2, 4, (40, 90))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for _ in range(4):
        x, y = rnd.uniform(0, t), rnd.uniform(0, t)
        p.setPen(QPen(_c("#a89470", 70), 1))
        _repetir(t, x, y, lambda a, b: p.drawEllipse(QPointF(a, b), 5, 3))


def _cascalho(p, rnd, t):
    for _ in range(70):
        x, y = rnd.uniform(0, t), rnd.uniform(0, t)
        r = rnd.uniform(1.5, 4)
        cor = _c(rnd.choice(["#8c867c", "#a39d92", "#6e695f", "#b8b2a6"]))
        def pedra(a, b, r=r, cor=cor):
            p.setPen(QPen(_c("#2c2a26", 160), 0.6))
            p.setBrush(cor)
            p.drawEllipse(QPointF(a, b), r, r * 0.8)
        _repetir(t, x, y, pedra)


def _paralelepipedo(p, rnd, t):
    for linha in range(4):
        y = linha * 16
        desloc = 0 if linha % 2 == 0 else 8
        for x in range(-16, t + 16, 16):
            cor = QColor(rnd.choice(["#77716a", "#6a655e", "#837c73", "#5e5a54"]))
            r = QRectF(x + desloc + 1, y + 1, 14, 14)
            g = QRadialGradient(r.center() - QPointF(2, 2), 10)
            g.setColorAt(0, cor.lighter(125))
            g.setColorAt(1, cor.darker(120))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(g))
            p.drawRoundedRect(r, 4, 4)


def _tabuas_velhas(p, rnd, t):
    _madeira(p, rnd, t)
    p.fillRect(QRectF(0, 0, t, t), _c("#3b3022", 90))
    p.setPen(QPen(_c("#1a120b", 200), 1.6))
    for _ in range(3):
        x, y = rnd.uniform(4, t - 4), rnd.uniform(4, t - 4)
        p.drawLine(QPointF(x, y), QPointF(x + rnd.uniform(-8, 8), y + rnd.uniform(-2, 2)))
    _pontos(p, rnd, t, 6, ["#000000"], 1.5, 2.5, (120, 200))


def _tapete(p, rnd, t):
    p.fillRect(QRectF(0, 0, t, t), QColor("#6b1f24"))
    p.setPen(QPen(_c("#c9a24a", 200), 1.4))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRect(QRectF(4, 4, t - 8, t - 8))
    losango = QPolygonF([QPointF(t / 2, 12), QPointF(t - 12, t / 2),
                         QPointF(t / 2, t - 12), QPointF(12, t / 2)])
    p.setBrush(_c("#1f2f5a", 220))
    p.drawPolygon(losango)
    p.setBrush(_c("#c9a24a"))
    p.drawEllipse(QPointF(t / 2, t / 2), 4, 4)


def _pantano(p, rnd, t):
    p.fillRect(QRectF(0, 0, t, t), QColor("#2f3b22"))
    _pontos(p, rnd, t, 16, ["#3f5a3a", "#24301c"], 5, 10, (90, 170))
    _pontos(p, rnd, t, 8, ["#6f8f3a"], 2, 3.5, (120, 200))
    _pontos(p, rnd, t, 10, ["#a8c070"], 0.6, 1.2, (100, 200))


def _obsidiana(p, rnd, t):
    p.fillRect(QRectF(0, 0, t, t), QColor("#141218"))
    for _ in range(9):
        a = QPointF(rnd.uniform(0, t), rnd.uniform(0, t))
        b = a + QPointF(rnd.uniform(-20, 20), rnd.uniform(-20, 20))
        c = a + QPointF(rnd.uniform(-20, 20), rnd.uniform(-20, 20))
        p.setPen(QPen(_c("#6a5a8a", 90), 0.8))
        p.setBrush(_c(rnd.choice(["#1c1824", "#24202e", "#100e14"]), 230))
        p.drawPolygon(QPolygonF([a, b, c]))
    _pontos(p, rnd, t, 10, ["#b9a6ff"], 0.5, 1.0, (100, 200))


def _marmore_branco(p, rnd, t):
    p.fillRect(QRectF(0, 0, t, t), QColor("#e6e2da"))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for _ in range(3):
        y0 = rnd.uniform(0, t)
        fase, amp = rnd.uniform(0, 6), rnd.uniform(3, 8)
        cam = QPainterPath(QPointF(0, y0))
        for x in range(0, t + 2, 2):
            cam.lineTo(x, y0 + amp * math.sin(2 * math.pi * x / t + fase))
        p.setPen(QPen(_c("#9a948a", rnd.randint(60, 120)), rnd.uniform(0.6, 1.4)))
        p.drawPath(cam)


def _xadrez(p, rnd, t):
    for i in range(2):
        for j in range(2):
            p.fillRect(QRectF(i * 32, j * 32, 32, 32),
                       QColor("#e8e4dc") if (i + j) % 2 == 0 else QColor("#2a2a2e"))


def _metal_enferrujado(p, rnd, t):
    _placa_metal(p, rnd, t)
    _pontos(p, rnd, t, 24, ["#8a3f16", "#a5531f", "#5e2a10"], 2, 7, (80, 170))


def _hexagono(p, rnd, t):
    p.fillRect(QRectF(0, 0, t, t), QColor("#1a2230"))
    r = 9.2
    h = r * math.sqrt(3)
    p.setPen(QPen(_c("#38e1ff", 120), 1))
    for col in range(-1, 5):
        for lin in range(-1, 5):
            cx = col * 1.5 * r
            cy = lin * h + (h / 2 if col % 2 else 0)
            hexa = QPolygonF([QPointF(cx + r * math.cos(math.radians(a)),
                                      cy + r * math.sin(math.radians(a)))
                              for a in range(0, 360, 60)])
            p.setBrush(_c(rnd.choice(["#202a3a", "#1c2533", "#25314a"])))
            p.drawPolygon(hexa)


def _acido(p, rnd, t):
    g = QRadialGradient(QPointF(t / 2, t / 2), t * 0.75)
    g.setColorAt(0, QColor("#b8ff3a"))
    g.setColorAt(1, QColor("#4f9a14"))
    p.fillRect(QRectF(0, 0, t, t), QBrush(g))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for _ in range(8):
        x, y = rnd.uniform(0, t), rnd.uniform(0, t)
        r = rnd.uniform(2, 5)
        p.setPen(QPen(_c("#eaffb0", 170), 1))
        _repetir(t, x, y, lambda a, b, r=r: p.drawEllipse(QPointF(a, b), r, r))


def _ouro(p, rnd, t):
    _pontos(p, rnd, t, 60, ["#f5d36a", "#b88a1e", "#ffe9a0"], 3, 6, (120, 220))
    _pontos(p, rnd, t, 20, ["#fff6c8"], 0.5, 1.2, (160, 255))


def _sangue(p, rnd, t):
    _concreto(p, rnd, t)
    for _ in range(3):
        x, y = rnd.uniform(0, t), rnd.uniform(0, t)
        r = rnd.uniform(6, 12)
        def poca(a, b, r=r):
            g = QRadialGradient(QPointF(a, b), r)
            g.setColorAt(0, _c("#5a0a0e", 230))
            g.setColorAt(0.7, _c("#7a1016", 200))
            g.setColorAt(1, _c("#7a1016", 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(g))
            p.drawEllipse(QPointF(a, b), r, r * 0.8)
        _repetir(t, x, y, poca)


def _rocha_caverna(p, rnd, t):
    _pontos(p, rnd, t, 20, ["#4a4540", "#5c5650", "#38342f"], 6, 12, (120, 200))
    _pontos(p, rnd, t, 150, ["#7a746c", "#2a2723"], 0.5, 1.4)



CHAO = {
    # chave: (nome, cor base, desenhador)
    "pedra": ("Chão de pedra", "#3f3c38", _laje),
    "terra": ("Terra", "#5e4430", _terra),
    "grama": ("Grama", "#4b7431", _grama),
    "areia": ("Areia", "#c9b07a", _areia),
    "madeira": ("Madeira", "#6b4529", _madeira),
    "agua": ("Água", "#2a5d7c", _agua),
    "concreto": ("Concreto", "#8c8a85", _concreto),
    "asfalto": ("Asfalto", "#36363a", _asfalto),
    "ceramica": ("Cerâmica", "#9a958c", _ceramica),
    "carpete": ("Carpete", "#6a2e33", _carpete),
    "placa_metal": ("Placa de metal", "#5d646c", _placa_metal),
    "grade": ("Grade de metal", "#14181e", _grade),
    "painel_neon": ("Painel neon", "#0b111b", _painel_neon),
    "vidro_piso": ("Piso de vidro", "#7fa9ba", _vidro_piso),
    "cristal": ("Cristal", "#2e2250", _cristal),
    "marmore_arcano": ("Mármore arcano", "#2a2140", _marmore),
    "runas": ("Pedra rúnica", "#3a3640", _runas),
    "musgo_luminoso": ("Musgo luminoso", "#16281a", _musgo),
    "lava": ("Lava / magma", "#c8320c", _lava),
    "gelo": ("Gelo", "#b6e0f2", _gelo),
    "neve": ("Neve", "#eef3f7", _neve),
    "lama": ("Lama", "#4a3826", _lama),
    "cascalho": ("Cascalho", "#57534c", _cascalho),
    "paralelepipedo": ("Paralelepípedo", "#2c2a27", _paralelepipedo),
    "tabuas_velhas": ("Tábuas velhas", "#5a3e26", _tabuas_velhas),
    "tapete": ("Tapete ornamental", "#6b1f24", _tapete),
    "pantano": ("Pântano", "#2f3b22", _pantano),
    "rocha_caverna": ("Rocha de caverna", "#423e39", _rocha_caverna),
    "obsidiana": ("Obsidiana", "#141218", _obsidiana),
    "marmore_branco": ("Mármore branco", "#e6e2da", _marmore_branco),
    "xadrez": ("Piso xadrez", "#e8e4dc", _xadrez),
    "metal_enferrujado": ("Metal enferrujado", "#5d646c", _metal_enferrujado),
    "hexagono": ("Piso hexagonal", "#1a2230", _hexagono),
    "acido": ("Ácido / lodo tóxico", "#6fbf1e", _acido),
    "ouro": ("Pilha de ouro", "#c9a03a", _ouro),
    "sangue": ("Concreto com sangue", "#8c8a85", _sangue),
}


# ====================================================================== paredes
# Texturas de parede são uma faixa: comprimento 32 (ao longo da parede) × 12 (espessura).
# Paredes verticais usam a mesma textura girada.
LARG_PAREDE, ESP_PAREDE = 32, 12


def _p_pedra(p, rnd, t):
    x = 0
    for larg in (15, 17):
        cor = QColor(rnd.choice(["#8a857d", "#7b766f", "#958f86", "#837d74"]))
        r = QRectF(x + 0.8, 0.8, larg - 1.6, ESP_PAREDE - 1.6)
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0, cor.lighter(118))
        g.setColorAt(1, cor.darker(125))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawRoundedRect(r, 2, 2)
        x += larg
    _pontos_faixa(p, rnd, 30, ["#c2bcb2", "#4e4a45"])


def _p_tijolo(p, rnd, t):
    for linha, desloc in ((0, 0), (1, 6)):
        y = linha * 6
        for x in range(-12, LARG_PAREDE + 12, 12):
            cor = QColor(rnd.choice(["#9a4f38", "#8a4430", "#a65a40"]))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(cor)
            p.drawRect(QRectF(x + desloc + 0.7, y + 0.7, 10.6, 4.6))


def _p_madeira(p, rnd, t):
    for y in (0, 4, 8):
        cor = QColor(rnd.choice(["#7a5232", "#6b4529", "#86603c"]))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(cor)
        p.drawRect(QRectF(0, y, LARG_PAREDE, 4))
        p.setPen(QPen(cor.darker(130), 0.6))
        p.drawLine(QPointF(0, y + 2), QPointF(LARG_PAREDE, y + 2.4))
    p.setPen(QPen(_c("#2b1b10"), 0.8))
    p.drawLine(QPointF(LARG_PAREDE - 0.5, 0), QPointF(LARG_PAREDE - 0.5, ESP_PAREDE))


def _p_ferro(p, rnd, t):
    g = QLinearGradient(0, 0, 0, ESP_PAREDE)
    g.setColorAt(0, QColor("#5b6169"))
    g.setColorAt(0.45, QColor("#9aa3ad"))
    g.setColorAt(1, QColor("#454a51"))
    p.fillRect(QRectF(0, 0, LARG_PAREDE, ESP_PAREDE), QBrush(g))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(_c("#d0d6dd"))
    for x in (8, 24):
        p.drawEllipse(QPointF(x, ESP_PAREDE / 2), 1.3, 1.3)
    p.setPen(QPen(_c("#2c3137"), 0.8))
    p.drawLine(QPointF(LARG_PAREDE - 0.5, 0), QPointF(LARG_PAREDE - 0.5, ESP_PAREDE))


def _p_concreto(p, rnd, t):
    _pontos_faixa(p, rnd, 70, ["#b9b6b0", "#6f6d69"])


def _p_vidro(p, rnd, t):
    p.setPen(QPen(_c("#ffffff", 150), 1.2))
    p.drawLine(QPointF(0, 3), QPointF(LARG_PAREDE, 3))


def _p_gesso(p, rnd, t):
    _pontos_faixa(p, rnd, 30, ["#ffffff", "#b4ad9f"])


def _p_energia(p, rnd, t):
    g = QLinearGradient(0, 0, 0, ESP_PAREDE)
    g.setColorAt(0, _c("#38e1ff", 60))
    g.setColorAt(0.5, _c("#e6fcff", 240))
    g.setColorAt(1, _c("#38e1ff", 60))
    p.fillRect(QRectF(0, 0, LARG_PAREDE, ESP_PAREDE), QBrush(g))


def _p_cristal(p, rnd, t):
    for x in range(0, LARG_PAREDE, 8):
        cor = _c(rnd.choice(["#6a52b0", "#8a6be0", "#4b347a", "#5d7fd0"]), 230)
        p.setPen(QPen(_c("#e0d2ff", 140), 0.6))
        p.setBrush(cor)
        p.drawPolygon(QPolygonF([QPointF(x, ESP_PAREDE), QPointF(x + 4, 0),
                                 QPointF(x + 8, ESP_PAREDE)]))


def _p_runica(p, rnd, t):
    _p_pedra(p, rnd, t)
    p.fillRect(QRectF(0, 0, LARG_PAREDE, ESP_PAREDE), _c("#2a1f40", 110))
    p.setPen(QPen(_c("#d2b6ff", 220), 1))
    p.drawLine(QPointF(7, 2), QPointF(7, 10))
    p.drawLine(QPointF(7, 2), QPointF(11, 6))
    p.drawLine(QPointF(23, 2), QPointF(23, 10))
    p.drawLine(QPointF(20, 5), QPointF(26, 5))


def _pontos_faixa(p, rnd, n, cores):
    p.setPen(Qt.PenStyle.NoPen)
    for _ in range(n):
        p.setBrush(_c(rnd.choice(cores), rnd.randint(30, 90)))
        p.drawEllipse(QPointF(rnd.uniform(0, LARG_PAREDE), rnd.uniform(0, ESP_PAREDE)),
                      0.6, 0.6)


def _p_rocha(p, rnd, t):
    p.fillRect(QRectF(0, 0, LARG_PAREDE, ESP_PAREDE), QColor("#4f4a44"))
    for _ in range(6):
        cor = _c(rnd.choice(["#5f5952", "#3f3a35", "#6b655d"]))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(cor)
        p.drawEllipse(QPointF(rnd.uniform(0, LARG_PAREDE), rnd.uniform(0, ESP_PAREDE)),
                      rnd.uniform(3, 6), rnd.uniform(2, 4))


def _p_palicada(p, rnd, t):
    for x in range(0, LARG_PAREDE, 8):
        cor = QColor(rnd.choice(["#6b4a2b", "#5a3d22", "#7a5532"]))
        g = QLinearGradient(QPointF(x, 0), QPointF(x + 8, 0))
        g.setColorAt(0, cor.darker(140))
        g.setColorAt(0.5, cor.lighter(115))
        g.setColorAt(1, cor.darker(140))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(QRectF(x, 0, 8, ESP_PAREDE))


def _p_gelo(p, rnd, t):
    g = QLinearGradient(0, 0, 0, ESP_PAREDE)
    g.setColorAt(0, _c("#e8f8ff", 230))
    g.setColorAt(1, _c("#8cc8e6", 230))
    p.fillRect(QRectF(0, 0, LARG_PAREDE, ESP_PAREDE), QBrush(g))
    p.setPen(QPen(_c("#ffffff", 200), 0.8))
    p.drawLine(QPointF(3, 3), QPointF(14, 9))
    p.drawLine(QPointF(19, 2), QPointF(29, 7))


def _p_obsidiana(p, rnd, t):
    p.fillRect(QRectF(0, 0, LARG_PAREDE, ESP_PAREDE), QColor("#16131c"))
    p.setPen(QPen(_c("#7a68a8", 140), 0.8))
    p.drawLine(QPointF(0, 4), QPointF(LARG_PAREDE, 2))
    p.drawLine(QPointF(5, ESP_PAREDE), QPointF(20, 5))


def _p_enferrujado(p, rnd, t):
    _p_ferro(p, rnd, t)
    _pontos_faixa(p, rnd, 40, ["#8a3f16", "#a5531f", "#5e2a10"])


def _p_osso(p, rnd, t):
    p.fillRect(QRectF(0, 0, LARG_PAREDE, ESP_PAREDE), QColor("#2a2420"))
    for x in (4, 20):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#d9cdb4"))
        p.drawEllipse(QRectF(x, 1.5, 10, 9))
        p.setBrush(QColor("#2a2420"))
        p.drawEllipse(QRectF(x + 2, 4, 2.5, 2.5))
        p.drawEllipse(QRectF(x + 5.5, 4, 2.5, 2.5))


def _p_sebe(p, rnd, t):
    p.fillRect(QRectF(0, 0, LARG_PAREDE, ESP_PAREDE), QColor("#2e5a22"))
    _pontos_faixa(p, rnd, 60, ["#4f8a34", "#1e3f16", "#6aa846"])



PAREDES = {
    "pedra": ("Pedra", "#3a3632", _p_pedra),
    "tijolo": ("Tijolo", "#4a3a33", _p_tijolo),
    "madeira": ("Madeira", "#2b1b10", _p_madeira),
    "ferro": ("Ferro", "#4a4f56", _p_ferro),
    "metal": ("Metal", "#4a4f56", _p_ferro),
    "concreto": ("Concreto", "#8c8a85", _p_concreto),
    "vidro": ("Vidro", "#a8d8ea", _p_vidro),
    "gesso": ("Gesso", "#d8d2c4", _p_gesso),
    "energia": ("Campo de energia", "#38e1ff", _p_energia),
    "cristal": ("Cristal", "#3b2a62", _p_cristal),
    "pedra_runica": ("Pedra rúnica", "#3a3640", _p_runica),
    "rocha": ("Rocha (caverna)", "#2f2b27", _p_rocha),
    "palicada": ("Paliçada de troncos", "#3a2614", _p_palicada),
    "gelo": ("Gelo", "#8cc8e6", _p_gelo),
    "obsidiana": ("Obsidiana", "#0c0a10", _p_obsidiana),
    "enferrujado": ("Metal enferrujado", "#4a3020", _p_enferrujado),
    "osso": ("Ossos e crânios", "#1a1512", _p_osso),
    "sebe": ("Sebe / arbustos", "#1e3f16", _p_sebe),
}

# Paredes que deixam ver através (vão importar na etapa de visão)
TRANSPARENTES = {"vidro", "energia", "gelo"}

_cache: dict[tuple, QPixmap] = {}


VERSAO_TEXTURAS = "3"   # (v0.68: chão no dobro da resolução) suba quando o gerador mudar (as texturas guardadas no disco são refeitas)


def _pasta_cache():
    import os
    from PyQt6.QtCore import QStandardPaths
    docs = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    pasta = os.path.join(docs or os.path.expanduser("~"), "Taverna", "cache", f"texturas_v{VERSAO_TEXTURAS}")
    try:
        os.makedirs(pasta, exist_ok=True)
    except OSError:
        return None
    return pasta


def textura(tipo: str, chave: str) -> QPixmap:
    """
    tipo = 'chao', 'parede' (o topo, visto de cima) ou 'parede_face' (a lateral, vista de frente).

    v0.35: os materiais naturais vêm do gerador novo (texturas.py: ruído natural, pedras de formato
    orgânico, sem luz pintada); os "desenhados" (runas, neon, xadrez…) continuam com o desenho antigo,
    mas sem a luz pintada (só grão e sombra nos vãos). Tudo fica guardado no disco depois da 1ª vez.
    """
    import os
    k = (tipo, chave)
    if k in _cache:
        return _cache[k]
    pasta = _pasta_cache()
    arquivo = os.path.join(pasta, f"{tipo}_{chave}.png") if pasta else None
    pm = QPixmap()
    if arquivo and os.path.exists(arquivo) and pm.load(arquivo):
        _cache[k] = pm
        return pm
    from . import texturas
    img = None
    try:
        img = texturas.gerar(tipo, chave, 64, ESP_PAREDE)
    except Exception as erro:   # gerador novo falhou: volta pro desenho antigo, sem quebrar
        from ..seguranca import registrar_erro
        registrar_erro(f"Textura nova de {tipo}/{chave} falhou: {erro!r}")
    if img is None and tipo == "parede_face":
        pm = textura("parede", chave)   # sem face própria: usa o topo
        _cache[k] = pm
        return pm
    if img is None:   # desenho antigo + acabamento novo
        tabela = CHAO if tipo == "chao" else PAREDES
        larg, alt = (TAM_CHAO, TAM_CHAO) if tipo == "chao" else (LARG_PAREDE, ESP_PAREDE)
        nome, base, desenhar = tabela.get(chave) or next(iter(tabela.values()))
        pm = QPixmap(larg, alt)
        pm.fill(_c(base, 150) if (tipo == "parede" and chave == "vidro") else QColor(base))
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        desenhar(p, random.Random(zlib.crc32(chave.encode())), TAM_CHAO)
        p.end()
        if not (tipo == "parede" and chave in ("vidro", "energia")):
            img = texturas.acabamento(pm.toImage())
        else:
            img = pm.toImage()
    pm = QPixmap.fromImage(img)
    if arquivo:
        img.save(arquivo)
    _cache[k] = pm
    return pm


def escala_chao(chave: str) -> float:
    """(v0.68) Quantos pixels da textura de chão cabem em 1 unidade da cena (os do gerador saem no dobro)."""
    from . import texturas
    return float(texturas.ESCALA_CHAO) if chave in texturas.CHAOS else 1.0


def pincel_chao(chave: str) -> QBrush:
    """Pincel do chão já na medida certa: 1 quadrado da textura = 1 quadrado da mesa, seja qual for a resolução."""
    pincel = QBrush(textura("chao", chave))
    s = escala_chao(chave)
    if s != 1.0:
        pincel.setTransform(QTransform.fromScale(1 / s, 1 / s))
    return pincel


def amostra(tipo: str, chave: str, tam: int = 40) -> QPixmap:
    """Miniatura pra mostrar no painel."""
    pm = QPixmap(tam, tam)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    if tipo == "chao":
        p.setBrush(pincel_chao(chave))
    else:
        p.setBrush(QColor(28, 24, 20))
    p.setPen(QPen(QColor(0, 0, 0, 160), 1))
    p.drawRoundedRect(QRectF(0.5, 0.5, tam - 1, tam - 1), 5, 5)
    if tipo != "chao":
        # Um pedaço de parede em "L" pra mostrar o material
        faixa = textura(tipo, chave)
        p.drawTiledPixmap(QRectF(4, tam / 2 - ESP_PAREDE / 2, tam - 8, ESP_PAREDE), faixa)
    p.end()
    return pm


def nome(tipo: str, chave: str) -> str:
    tabela = CHAO if tipo == "chao" else PAREDES
    return tabela.get(chave, (chave,))[0]
