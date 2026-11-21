"""
Tela inicial do Taverna — um cenário animado pra cada tema (tudo desenhado pelo programa,
nenhuma imagem externa):

  medieval  muro de pedra, tochas tremulando e brasas subindo
  moderno   cidade à noite, janelas acesas e chuva
  futurista grade de neon correndo pro horizonte, sol de faixas e estrelas
  mágico    círculo arcano girando e faíscas flutuando
  terror    lua pálida, árvores mortas, névoa rasteira e a luz falhando
  claro     pergaminho com rosa dos ventos e poeira no sol
  escuro    ardósia discreta com luzes lentas

A parte parada fica guardada numa imagem (cache); só a animação é redesenhada.
Gráficos "baixo" = cenário parado · "médio" = animação leve · "alto" = tudo.
"""

import math
import random

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPainter,
                         QPainterPath, QPen, QPixmap, QPolygonF, QRadialGradient)
from PyQt6.QtWidgets import (QComboBox, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton,
                             QVBoxLayout, QWidget)

from ..config import APP_VERSAO
from ..graficos import NIVEIS, graficos, nivel
from ..temas import TEMAS, TEMA_PADRAO, tema as dados_tema

# Tons de pedra (cinzas puxando pro marrom)
PEDRAS = [(78, 72, 66), (88, 82, 74), (70, 66, 62), (96, 88, 78), (64, 60, 58),
          (84, 76, 66), (74, 70, 68), (92, 86, 80), (60, 56, 52), (80, 74, 70)]
ARGAMASSA = QColor(22, 19, 17)

def desenhar_muro(largura: int, altura: int, semente: int = 7) -> QPixmap:
    """Desenha um muro de tijolos de pedra (aparelho corrido, tijolos irregulares)."""
    rnd = random.Random(semente)
    pm = QPixmap(largura, altura)
    pm.fill(ARGAMASSA)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    alt_tijolo = 54
    larg_tijolo = 132
    junta = 6
    linhas = altura // alt_tijolo + 2

    for linha in range(linhas):
        y = linha * alt_tijolo - 10
        x = -rnd.randint(0, larg_tijolo) if linha % 2 else -larg_tijolo // 2
        while x < largura:
            larg = larg_tijolo + rnd.randint(-28, 28)
            r = QRectF(x + junta / 2, y + junta / 2, larg - junta, alt_tijolo - junta)
            _tijolo(p, r, rnd)
            x += larg

    # Escurece bem as bordas (vinheta)
    vinheta = QRadialGradient(QPointF(largura / 2, altura * 0.45), max(largura, altura) * 0.72)
    vinheta.setColorAt(0.0, QColor(0, 0, 0, 0))
    vinheta.setColorAt(0.55, QColor(0, 0, 0, 70))
    vinheta.setColorAt(1.0, QColor(0, 0, 0, 225))
    p.fillRect(pm.rect(), QBrush(vinheta))
    p.end()
    return pm


def _tijolo(p: QPainter, r: QRectF, rnd: random.Random):
    base = rnd.choice(PEDRAS)
    var = rnd.randint(-8, 8)
    cor = QColor(*(max(0, min(255, c + var)) for c in base))

    # Contorno irregular: cantos "lascados"
    j = lambda: rnd.uniform(-2.5, 2.5)
    lasca = lambda: rnd.uniform(2, 7)
    pontos = [
        QPointF(r.left() + lasca(), r.top() + j()),
        QPointF(r.center().x() + j() * 6, r.top() + j()),
        QPointF(r.right() - lasca(), r.top() + j()),
        QPointF(r.right() + j(), r.top() + lasca()),
        QPointF(r.right() + j(), r.bottom() - lasca()),
        QPointF(r.right() - lasca(), r.bottom() + j()),
        QPointF(r.center().x() + j() * 6, r.bottom() + j()),
        QPointF(r.left() + lasca(), r.bottom() + j()),
        QPointF(r.left() + j(), r.bottom() - lasca()),
        QPointF(r.left() + j(), r.top() + lasca()),
    ]
    forma = QPainterPath()
    forma.addPolygon(QPolygonF(pontos))
    forma.closeSubpath()

    # Volume: luz de cima, sombra embaixo
    grad = QLinearGradient(r.topLeft(), r.bottomLeft())
    grad.setColorAt(0, cor.lighter(118))
    grad.setColorAt(0.5, cor)
    grad.setColorAt(1, cor.darker(135))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(grad))
    p.drawPath(forma)

    p.save()
    p.setClipPath(forma)
    # Textura: pontinhos claros e escuros
    for _ in range(int(r.width() * r.height() / 90)):
        cx = rnd.uniform(r.left(), r.right())
        cy = rnd.uniform(r.top(), r.bottom())
        claro = rnd.random() < 0.45
        alfa = rnd.randint(18, 55)
        p.setBrush(QColor(255, 245, 230, alfa) if claro else QColor(0, 0, 0, alfa + 10))
        raio = rnd.uniform(0.6, 2.2)
        p.drawEllipse(QPointF(cx, cy), raio, raio)
    # Manchas (musgo/umidade) às vezes
    if rnd.random() < 0.18:
        mancha = QRadialGradient(QPointF(rnd.uniform(r.left(), r.right()), r.bottom()),
                                 rnd.uniform(18, 40))
        mancha.setColorAt(0, QColor(40, 52, 30, 90))
        mancha.setColorAt(1, QColor(40, 52, 30, 0))
        p.setBrush(QBrush(mancha))
        p.drawRect(r)
    # Rachadura às vezes
    if rnd.random() < 0.22:
        p.setPen(QPen(QColor(18, 15, 13, 170), 1.2))
        x, y = rnd.uniform(r.left(), r.right()), r.top()
        for _ in range(rnd.randint(3, 6)):
            nx = x + rnd.uniform(-10, 10)
            ny = y + rnd.uniform(5, 14)
            p.drawLine(QPointF(x, y), QPointF(nx, ny))
            x, y = nx, ny
    p.restore()

    # Quina iluminada no topo e sombra na base
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(QColor(255, 240, 220, 40), 1.4))
    p.drawLine(pontos[0], pontos[2])
    p.setPen(QPen(QColor(0, 0, 0, 110), 2))
    p.drawLine(pontos[5], pontos[7])



# ====================================================================== utilidades
def _vinheta(p, w, h, forca=225, centro=0.45):
    v = QRadialGradient(QPointF(w / 2, h * centro), max(w, h) * 0.72)
    v.setColorAt(0.0, QColor(0, 0, 0, 0))
    v.setColorAt(0.55, QColor(0, 0, 0, int(forca * 0.3)))
    v.setColorAt(1.0, QColor(0, 0, 0, forca))
    p.fillRect(QRectF(0, 0, w, h), QBrush(v))


def _degrade(p, w, h, *paradas):
    g = QLinearGradient(0, 0, 0, h)
    for pos, cor in paradas:
        g.setColorAt(pos, QColor(cor))
    p.fillRect(QRectF(0, 0, w, h), QBrush(g))


def _pontos(semente, n):
    rnd = random.Random(semente)
    return [(rnd.random(), rnd.random(), rnd.random(), rnd.random()) for _ in range(n)]


# ====================================================================== fundos parados
def _fundo_moderno(p, w, h):
    _degrade(p, w, h, (0, "#070b14"), (0.55, "#141c2c"), (0.8, "#27303f"), (1, "#0c0f14"))
    rnd = random.Random(11)
    # brilho da cidade no horizonte
    g = QRadialGradient(QPointF(w / 2, h * 0.86), w * 0.7)
    g.setColorAt(0, QColor(79, 179, 169, 60))
    g.setColorAt(1, QColor(0, 0, 0, 0))
    p.fillRect(QRectF(0, 0, w, h), QBrush(g))
    for camada, (cor, base, amin, amax, acesa) in enumerate((("#111925", 0.62, 0.10, 0.34, 0.10),
                                                             ("#0b111a", 0.72, 0.12, 0.42, 0.22),
                                                             ("#06090e", 0.84, 0.10, 0.36, 0.30))):
        x = -20.0
        while x < w:
            larg = rnd.uniform(46, 120) * (0.8 + camada * 0.25)
            alt = h * rnd.uniform(amin, amax)
            topo = h * base - alt + h * 0.16
            p.fillRect(QRectF(x, topo, larg, h - topo), QColor(cor))
            if rnd.random() < 0.3:   # antena
                p.setPen(QPen(QColor(cor), 2))
                p.drawLine(QPointF(x + larg / 2, topo), QPointF(x + larg / 2, topo - rnd.uniform(14, 40)))
            passo_x, passo_y = 11 + camada * 2, 15 + camada * 2
            yy = topo + 8
            while yy < h - 10:
                xx = x + 6
                while xx < x + larg - 8:
                    if rnd.random() < acesa:
                        quente = rnd.random() < 0.7
                        c = QColor(255, 214, 140, rnd.randint(110, 230)) if quente else QColor(150, 220, 235, rnd.randint(90, 200))
                        p.fillRect(QRectF(xx, yy, 5 + camada, 8 + camada), c)
                    xx += passo_x
                yy += passo_y
            x += larg + rnd.uniform(-6, 14)
    _vinheta(p, w, h, 200, 0.5)


def _fundo_futurista(p, w, h):
    _degrade(p, w, h, (0, "#03040c"), (0.45, "#0b1030"), (0.62, "#2a1050"), (0.625, "#05070f"), (1, "#020308"))
    rnd = random.Random(5)
    p.setPen(Qt.PenStyle.NoPen)
    for _ in range(int(w * h / 5200)):
        a = rnd.randint(60, 230)
        p.setBrush(QColor(200, 235, 255, a))
        r = rnd.uniform(0.4, 1.5)
        p.drawEllipse(QPointF(rnd.uniform(0, w), rnd.uniform(0, h * 0.6)), r, r)
    # sol de faixas
    cx, cy, raio = w / 2, h * 0.62, min(w, h) * 0.2
    sol = QPainterPath()
    sol.addEllipse(QPointF(cx, cy), raio, raio)
    p.save()
    p.setClipRect(QRectF(0, 0, w, cy))
    g = QLinearGradient(0, cy - raio, 0, cy)
    g.setColorAt(0, QColor("#ffd84a"))
    g.setColorAt(0.55, QColor("#ff5fa8"))
    g.setColorAt(1, QColor("#b030ff"))
    p.fillPath(sol, QBrush(g))
    p.setBrush(QColor("#0b1030"))
    for k in range(7):
        y = cy - raio * 0.62 + k * raio * 0.1
        p.fillRect(QRectF(cx - raio, y, raio * 2, 2 + k * 1.6), QColor(11, 12, 44))
    p.restore()
    halo = QRadialGradient(QPointF(cx, cy), raio * 2.2)
    halo.setColorAt(0, QColor(255, 80, 180, 70))
    halo.setColorAt(1, QColor(0, 0, 0, 0))
    p.fillRect(QRectF(0, 0, w, cy), QBrush(halo))


def _fundo_magico(p, w, h):
    _degrade(p, w, h, (0, "#0b0618"), (0.5, "#1a0f33"), (1, "#0a0614"))
    rnd = random.Random(21)
    p.setPen(Qt.PenStyle.NoPen)
    for cor in ((180, 140, 255), (95, 224, 208), (255, 120, 200), (120, 150, 255)):
        for _ in range(3):
            c = QPointF(rnd.uniform(0, w), rnd.uniform(0, h))
            r = rnd.uniform(0.18, 0.4) * max(w, h)
            g = QRadialGradient(c, r)
            g.setColorAt(0, QColor(*cor, 34))
            g.setColorAt(1, QColor(*cor, 0))
            p.fillRect(QRectF(0, 0, w, h), QBrush(g))
    for _ in range(int(w * h / 7000)):
        p.setBrush(QColor(236, 226, 255, rnd.randint(40, 190)))
        r = rnd.uniform(0.4, 1.4)
        p.drawEllipse(QPointF(rnd.uniform(0, w), rnd.uniform(0, h)), r, r)
    _vinheta(p, w, h, 190)


def _arvore(p, x, y, alt, rnd, ang=-math.pi / 2, nivel_=0):
    if alt < 9 or nivel_ > 6:
        return
    x2, y2 = x + math.cos(ang) * alt, y + math.sin(ang) * alt
    p.setPen(QPen(QColor(5, 4, 5), max(1.0, alt * 0.11), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(x, y), QPointF(x2, y2))
    for _ in range(rnd.choice((2, 2, 3))):
        _arvore(p, x2, y2, alt * rnd.uniform(0.55, 0.78), rnd, ang + rnd.uniform(-0.75, 0.75), nivel_ + 1)


def _fundo_terror(p, w, h):
    _degrade(p, w, h, (0, "#050506"), (0.55, "#141216"), (0.8, "#1c1417"), (1, "#030303"))
    rnd = random.Random(13)
    # lua pálida atrás de nuvens
    lua = QPointF(w * 0.86, h * 0.17)
    r = min(w, h) * 0.085
    halo = QRadialGradient(lua, r * 6)
    halo.setColorAt(0, QColor(200, 205, 190, 70))
    halo.setColorAt(0.3, QColor(140, 150, 140, 22))
    halo.setColorAt(1, QColor(0, 0, 0, 0))
    p.fillRect(QRectF(0, 0, w, h), QBrush(halo))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(206, 208, 190))
    p.drawEllipse(lua, r, r)
    p.setBrush(QColor(160, 162, 148, 120))
    for dx, dy, rr in ((-0.3, -0.2, 0.22), (0.25, 0.3, 0.16), (0.1, -0.4, 0.1), (-0.35, 0.35, 0.12)):
        p.drawEllipse(QPointF(lua.x() + dx * r, lua.y() + dy * r), rr * r, rr * r)
    for _ in range(7):   # nuvens escuras
        c = QPointF(rnd.uniform(0, w), rnd.uniform(h * 0.08, h * 0.42))
        g = QRadialGradient(c, rnd.uniform(0.12, 0.3) * w)
        g.setColorAt(0, QColor(8, 8, 10, 190))
        g.setColorAt(1, QColor(8, 8, 10, 0))
        p.setBrush(QBrush(g))
        p.drawEllipse(c, w * 0.32, h * 0.09)
    # colina, cerca torta e árvores mortas
    colina = QPainterPath()
    colina.moveTo(0, h)
    colina.lineTo(0, h * 0.8)
    colina.cubicTo(w * 0.25, h * 0.7, w * 0.5, h * 0.86, w * 0.72, h * 0.78)
    colina.cubicTo(w * 0.86, h * 0.73, w * 0.95, h * 0.8, w, h * 0.77)
    colina.lineTo(w, h)
    p.fillPath(colina, QColor(5, 4, 5))
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    for fx, alt in ((0.07, 0.34), (0.2, 0.2), (0.9, 0.38), (0.6, 0.16)):
        _arvore(p, w * fx, h * 0.82, h * alt * 0.36, rnd)
    p.setPen(QPen(QColor(5, 4, 5), 3))
    x = w * 0.28
    while x < w * 0.56:
        inc = rnd.uniform(-0.12, 0.12)
        p.drawLine(QPointF(x, h * 0.83), QPointF(x + inc * 30, h * 0.83 - rnd.uniform(26, 40)))
        x += 24
    p.drawLine(QPointF(w * 0.27, h * 0.8), QPointF(w * 0.57, h * 0.805))
    _vinheta(p, w, h, 240, 0.4)


def _fundo_claro(p, w, h):
    _degrade(p, w, h, (0, "#f2e8cf"), (0.5, "#ead9b4"), (1, "#d9c296"))
    rnd = random.Random(3)
    p.setPen(Qt.PenStyle.NoPen)
    for _ in range(26):   # manchas do papel
        c = QPointF(rnd.uniform(0, w), rnd.uniform(0, h))
        g = QRadialGradient(c, rnd.uniform(60, 240))
        tom = rnd.choice(((150, 110, 50, 26), (255, 250, 235, 60), (120, 90, 40, 18)))
        g.setColorAt(0, QColor(*tom))
        g.setColorAt(1, QColor(tom[0], tom[1], tom[2], 0))
        p.fillRect(QRectF(0, 0, w, h), QBrush(g))
    p.setPen(QPen(QColor(110, 80, 40, 26), 1))
    for _ in range(int(w * h / 2600)):   # fibras
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        a = rnd.uniform(0, math.pi)
        c = rnd.uniform(4, 16)
        p.drawLine(QPointF(x, y), QPointF(x + math.cos(a) * c, y + math.sin(a) * c))
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    tinta = QColor(92, 58, 22, 70)
    # linhas de mapa (rotas e costa)
    p.setPen(QPen(tinta, 1.4, Qt.PenStyle.DashLine))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for _ in range(4):
        rota = QPainterPath()
        rota.moveTo(rnd.uniform(0, w), rnd.uniform(0, h))
        rota.cubicTo(rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(0, w), rnd.uniform(0, h),
                     rnd.uniform(0, w), rnd.uniform(0, h))
        p.drawPath(rota)
    # rosa dos ventos
    c = QPointF(w * 0.84, h * 0.74)
    R = min(w, h) * 0.13
    p.setPen(QPen(tinta, 1.6))
    p.drawEllipse(c, R, R)
    p.drawEllipse(c, R * 0.78, R * 0.78)
    for k in range(16):
        a = k * math.pi / 8
        comp = R * (1.25 if k % 4 == 0 else 0.95 if k % 2 == 0 else 0.6)
        ponta = QPointF(c.x() + math.cos(a) * comp, c.y() + math.sin(a) * comp)
        l1 = QPointF(c.x() + math.cos(a + 0.22) * R * 0.2, c.y() + math.sin(a + 0.22) * R * 0.2)
        l2 = QPointF(c.x() + math.cos(a - 0.22) * R * 0.2, c.y() + math.sin(a - 0.22) * R * 0.2)
        p.setBrush(QColor(92, 58, 22, 60 if k % 2 == 0 else 24))
        p.drawPolygon(QPolygonF([ponta, l1, c, l2]))
    # moldura dupla
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(QColor(92, 58, 22, 90), 2))
    p.drawRect(QRectF(18, 18, w - 36, h - 36))
    p.setPen(QPen(QColor(92, 58, 22, 60), 1))
    p.drawRect(QRectF(26, 26, w - 52, h - 52))
    borda = QRadialGradient(QPointF(w / 2, h / 2), max(w, h) * 0.75)
    borda.setColorAt(0.6, QColor(120, 80, 30, 0))
    borda.setColorAt(1, QColor(100, 62, 20, 110))
    p.fillRect(QRectF(0, 0, w, h), QBrush(borda))


def _fundo_escuro(p, w, h):
    _degrade(p, w, h, (0, "#15171b"), (1, "#0b0c0e"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 255, 255, 13))
    passo = 28
    for y in range(0, h, passo):
        for x in range(0, w, passo):
            p.drawEllipse(QPointF(x + 14, y + 14), 1.1, 1.1)
    _vinheta(p, w, h, 170)


FUNDOS = {"moderno": _fundo_moderno, "futurista": _fundo_futurista, "magico": _fundo_magico,
          "terror": _fundo_terror, "claro": _fundo_claro, "escuro": _fundo_escuro}


def desenhar_fundo(chave: str, w: int, h: int) -> QPixmap:
    if chave not in FUNDOS:
        return desenhar_muro(w, h)
    pm = QPixmap(w, h)
    pm.fill(QColor("#000000"))
    p = QPainter(pm)
    FUNDOS[chave](p, w, h)
    p.end()
    return pm


# ====================================================================== animações
def _anim_medieval(p, w, h, t, n, rnd):
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
    for i, x in enumerate((w * 0.12, w * 0.88)):
        fase = i * 2.1
        forca = 0.86 + 0.07 * math.sin(t * 7.3 + fase) + 0.05 * math.sin(t * 13.1 + fase * 2) \
            + (rnd.uniform(-0.03, 0.03) if n else 0)
        raio = max(w, h) * 0.42 * (0.96 + 0.04 * forca)
        luz = QRadialGradient(QPointF(x, h * 0.36), raio)
        luz.setColorAt(0.0, QColor(255, 150, 60, int(95 * forca)))
        luz.setColorAt(0.25, QColor(230, 110, 40, int(45 * forca)))
        luz.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(QRectF(0, 0, w, h), QBrush(luz))
    if n >= 1:   # brasas subindo
        p.setPen(Qt.PenStyle.NoPen)
        for a, b, c, d in _pontos(31, 26 if n == 1 else 60):
            ciclo = (t * (0.035 + c * 0.05) + b) % 1.0
            lado = w * 0.12 if a < 0.5 else w * 0.88
            x = lado + (a - 0.5 if a < 0.5 else a - 1.0) * w * 0.3 + math.sin(t * 1.3 + d * 9) * 14 + w * 0.07
            y = h * 0.62 - ciclo * h * 0.6
            alfa = int(230 * (1 - ciclo) * min(1.0, ciclo * 8))
            p.setBrush(QColor(255, 170 + int(60 * d), 70, alfa))
            r = 1.0 + d * 1.8
            p.drawEllipse(QPointF(x, y), r, r)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)


def _anim_moderno(p, w, h, t, n, rnd):
    if n >= 1:
        p.setPen(QPen(QColor(170, 200, 225, 70), 1.1))
        for a, b, c, d in _pontos(41, 90 if n == 1 else 220):
            vel = 0.9 + c * 0.7
            y = ((t * vel + b) % 1.0) * (h + 60) - 30
            x = (a * (w + 200) - 100) - (y / h) * 70
            comp = 12 + d * 16
            p.drawLine(QPointF(x, y), QPointF(x + comp * 0.22, y - comp))
    # letreiro de neon piscando ao longe
    pisca = 0.55 + 0.45 * math.sin(t * 2.2) if int(t * 3.1) % 11 else 0.15
    g = QRadialGradient(QPointF(w * 0.2, h * 0.7), w * 0.16)
    g.setColorAt(0, QColor(79, 179, 169, int(70 * pisca)))
    g.setColorAt(1, QColor(0, 0, 0, 0))
    p.fillRect(QRectF(0, 0, w, h), QBrush(g))


def _anim_futurista(p, w, h, t, n, rnd):
    hz = h * 0.625
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    neon = QColor(56, 225, 255)
    # linhas que fogem pro horizonte
    for k in range(-14, 15):
        x_base = w / 2 + k * w * 0.11
        alfa = max(30, 150 - abs(k) * 9)
        p.setPen(QPen(QColor(neon.red(), neon.green(), neon.blue(), alfa), 1.3))
        p.drawLine(QPointF(w / 2 + k * w * 0.012, hz), QPointF(x_base + k * w * 0.16, h))
    # linhas horizontais correndo pra frente
    passo = (t * 0.35) % 1.0
    for k in range(13):
        f = ((k + passo) / 13) ** 2.4
        y = hz + f * (h - hz)
        p.setPen(QPen(QColor(255, 63, 164, int(40 + 170 * f)), 1 + f * 1.6))
        p.drawLine(QPointF(0, y), QPointF(w, y))
    brilho = QLinearGradient(0, hz - 30, 0, hz + 40)
    brilho.setColorAt(0, QColor(255, 63, 164, 0))
    brilho.setColorAt(0.45, QColor(255, 120, 200, 110))
    brilho.setColorAt(1, QColor(255, 63, 164, 0))
    p.fillRect(QRectF(0, hz - 30, w, 70), QBrush(brilho))
    if n >= 1:   # estrelas piscando
        p.setPen(Qt.PenStyle.NoPen)
        for a, b, c, d in _pontos(51, 30 if n == 1 else 70):
            br = max(0.0, math.sin(t * (0.8 + c * 2) + d * 9))
            p.setBrush(QColor(220, 245, 255, int(210 * br)))
            p.drawEllipse(QPointF(a * w, b * h * 0.5), 1 + br * 1.3, 1 + br * 1.3)
    if n >= 2:   # linhas de varredura
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 34))
        y = 0
        while y < h:
            p.drawRect(QRectF(0, y, w, 1))
            y += 3


def _anim_magico(p, w, h, t, n, rnd):
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    c = QPointF(w / 2, h * 0.5)
    R = min(w, h) * 0.44
    pulso = 0.75 + 0.25 * math.sin(t * 0.9)
    for raio, vel, cor, traco in ((1.0, 0.05, (180, 140, 255), 12), (0.86, -0.08, (95, 224, 208), 8),
                                  (0.6, 0.12, (255, 150, 220), 6)):
        r = R * raio
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(*cor, int(70 * pulso)), 1.6))
        p.drawEllipse(c, r, r)
        p.drawEllipse(c, r * 0.94, r * 0.94)
        p.save()
        p.translate(c)
        p.rotate(math.degrees(t * vel))
        for k in range(traco):   # runas (tracinhos e losangos) em volta
            p.rotate(360 / traco)
            p.setPen(QPen(QColor(*cor, int(120 * pulso)), 1.8))
            p.drawLine(QPointF(0, -r * 0.97), QPointF(0, -r * 0.9))
            p.drawPolygon(QPolygonF([QPointF(0, -r * 0.89), QPointF(5, -r * 0.865), QPointF(0, -r * 0.84),
                                     QPointF(-5, -r * 0.865)]))
        if raio == 0.6:   # estrela de sete pontas
            pts = [QPointF(math.cos(k * 2 * math.pi * 3 / 7) * r * 0.92, math.sin(k * 2 * math.pi * 3 / 7) * r * 0.92)
                   for k in range(8)]
            p.setPen(QPen(QColor(*cor, int(60 * pulso)), 1.2))
            p.drawPolyline(QPolygonF(pts))
        p.restore()
    if n >= 1:
        p.setPen(Qt.PenStyle.NoPen)
        for a, b, cc, d in _pontos(61, 40 if n == 1 else 110):
            ciclo = (t * (0.02 + cc * 0.04) + b) % 1.0
            x = a * w + math.sin(t * 0.6 + d * 12) * 26
            y = h - ciclo * h
            br = math.sin(ciclo * math.pi) * (0.5 + 0.5 * math.sin(t * 3 + d * 20))
            cor = (180, 140, 255) if d < 0.5 else (95, 224, 208)
            p.setBrush(QColor(*cor, int(200 * max(0.0, br))))
            r = 1 + d * 2.2
            p.drawEllipse(QPointF(x, y), r, r)


def _anim_terror(p, w, h, t, n, rnd):
    p.setPen(Qt.PenStyle.NoPen)
    faixas = 4 if n == 0 else (8 if n == 1 else 14)
    for k, (a, b, c, d) in enumerate(_pontos(71, faixas)):   # névoa rasteira
        x = ((a + t * (0.006 + c * 0.012)) % 1.4 - 0.2) * w
        y = h * (0.68 + b * 0.3)
        rx, ry = w * (0.25 + d * 0.25), h * (0.05 + c * 0.07)
        g = QRadialGradient(QPointF(x, y), rx)
        alfa = int(52 + 26 * math.sin(t * 0.3 + k))
        g.setColorAt(0, QColor(170, 175, 170, alfa))
        g.setColorAt(1, QColor(170, 175, 170, 0))
        p.setBrush(QBrush(g))
        p.save()
        p.translate(x, y)
        p.scale(1.0, ry / rx)
        p.drawEllipse(QPointF(0, 0), rx, rx)
        p.restore()
    if n >= 1:
        # olhos na escuridão, de vez em quando
        fase = (t * 0.12) % 1.0
        if 0.62 < fase < 0.8:
            ind = int(t * 0.12) % 4
            ox, oy = ((0.1, 0.72), (0.93, 0.7), (0.42, 0.78), (0.64, 0.74))[ind]
            abre = math.sin((fase - 0.62) / 0.18 * math.pi)
            p.setBrush(QColor(200, 30, 30, int(210 * abre)))
            for dx in (-7, 7):
                p.drawEllipse(QPointF(w * ox + dx, h * oy), 3.2, 1.2 + 1.6 * abre)
        # a luz falha
        falha = int(t * 9) % 53
        if falha in (0, 2, 3):
            p.fillRect(QRectF(0, 0, w, h), QColor(0, 0, 0, 120 if falha != 2 else 50))
    if n >= 2:
        respiro = 0.5 + 0.5 * math.sin(t * 0.7)
        g = QRadialGradient(QPointF(w / 2, h * 0.45), max(w, h) * 0.7)
        g.setColorAt(0.55, QColor(90, 0, 0, 0))
        g.setColorAt(1, QColor(90, 0, 0, int(60 * respiro)))
        p.fillRect(QRectF(0, 0, w, h), QBrush(g))


def _anim_claro(p, w, h, t, n, rnd):
    # raio de sol passeando devagar
    x = (0.25 + 0.2 * math.sin(t * 0.12)) * w
    feixe = QPainterPath()
    feixe.moveTo(x - w * 0.05, 0)
    feixe.lineTo(x + w * 0.16, 0)
    feixe.lineTo(x + w * 0.5, h)
    feixe.lineTo(x + w * 0.1, h)
    feixe.closeSubpath()
    g = QLinearGradient(x, 0, x + w * 0.3, h)
    g.setColorAt(0, QColor(255, 250, 225, 80))
    g.setColorAt(1, QColor(255, 250, 225, 0))
    p.fillPath(feixe, QBrush(g))
    if n >= 1:   # poeira dourada
        p.setPen(Qt.PenStyle.NoPen)
        for a, b, c, d in _pontos(81, 24 if n == 1 else 60):
            px = (a + math.sin(t * 0.15 + d * 9) * 0.03) * w
            py = ((b + t * (0.006 + c * 0.012)) % 1.0) * h
            br = 0.4 + 0.6 * max(0.0, math.sin(t * 1.3 + d * 30))
            p.setBrush(QColor(140, 96, 30, int(120 * br)))
            r = 0.8 + d * 1.6
            p.drawEllipse(QPointF(px, py), r, r)


def _anim_escuro(p, w, h, t, n, rnd):
    p.setPen(Qt.PenStyle.NoPen)
    for k, (a, b, c, d) in enumerate(_pontos(91, 2 if n == 0 else (4 if n == 1 else 7))):
        x = (a + 0.12 * math.sin(t * (0.05 + c * 0.06) + k)) * w
        y = (b + 0.12 * math.cos(t * (0.04 + d * 0.06) + k * 2)) * h
        r = (0.18 + d * 0.22) * max(w, h)
        cor = (124, 156, 255) if k % 2 == 0 else (87, 214, 164)
        g = QRadialGradient(QPointF(x, y), r)
        g.setColorAt(0, QColor(*cor, 30))
        g.setColorAt(1, QColor(*cor, 0))
        p.fillRect(QRectF(0, 0, w, h), QBrush(g))


# ====================================================================== (v0.59) STEAMPUNK e PÓS-APOCALÍPTICO
# Plano B 2D (sem placa de vídeo ou Gráficos Baixo): o cenário 3D de verdade fica no QML.
def _engrenagem(p, c, raio, dentes, ang, cor, furo=0.35):
    caminho = QPainterPath()
    pts = []
    for k in range(dentes * 2):
        a = ang + k * math.pi / dentes
        r = raio * (1.0 if k % 2 == 0 else 0.84)
        for da in (-0.32, 0.32):
            aa = a + da * math.pi / dentes
            pts.append(QPointF(c.x() + math.cos(aa) * r, c.y() + math.sin(aa) * r))
    caminho.addPolygon(QPolygonF(pts))
    caminho.closeSubpath()
    caminho.addEllipse(c, raio * furo, raio * furo)
    for k in range(5):                                   # raios vazados
        a = ang + k * 2 * math.pi / 5 + 0.6
        caminho.addEllipse(QPointF(c.x() + math.cos(a) * raio * 0.6, c.y() + math.sin(a) * raio * 0.6),
                           raio * 0.12, raio * 0.12)
    caminho.setFillRule(Qt.FillRule.OddEvenFill)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(cor)
    p.drawPath(caminho)


_ENGRENAGENS = ((0.08, 0.2, 0.2, 18), (0.24, 0.05, 0.12, 12), (0.92, 0.78, 0.22, 20), (0.78, 0.95, 0.12, 12),
                (0.95, 0.18, 0.1, 10), (0.04, 0.82, 0.13, 14))


def _fundo_steampunk(p, w, h):
    _degrade(p, w, h, (0, "#2a1c10"), (0.6, "#1c140e"), (1, "#0e0906"))
    p.setPen(QPen(QColor(150, 90, 50, 120), 10))          # canos de cobre
    for y in (0.62, 0.66):
        p.drawLine(QPointF(0, h * y), QPointF(w * 0.3, h * y))
        p.drawLine(QPointF(w * 0.3, h * y), QPointF(w * 0.3, h))
    p.drawLine(QPointF(w * 0.72, 0), QPointF(w * 0.72, h * 0.4))
    p.drawLine(QPointF(w * 0.72, h * 0.4), QPointF(w, h * 0.4))
    luz = QRadialGradient(QPointF(w * 0.5, h * 0.25), max(w, h) * 0.6)   # lampião a gás
    luz.setColorAt(0, QColor(255, 190, 110, 70))
    luz.setColorAt(1, QColor(255, 190, 110, 0))
    p.fillRect(QRectF(0, 0, w, h), QBrush(luz))
    _vinheta(p, w, h, 200)


def _anim_steampunk(p, w, h, t, n, rnd):
    for k, (x, y, r, d) in enumerate(_ENGRENAGENS):        # engrenagens girando (sentidos alternados)
        ang = (t * 0.25 * (1 if k % 2 == 0 else -1) * 18 / d) if n else k
        _engrenagem(p, QPointF(w * x, h * y), max(w, h) * r, d, ang, QColor(120, 84, 40, 150))
    if n >= 1:                                              # vapor escapando
        p.setPen(Qt.PenStyle.NoPen)
        for a, b, c, d in _pontos(61, 10 if n == 1 else 22):
            fase = (t * (0.08 + c * 0.06) + a) % 1.0
            x = w * (0.3 + (d - 0.5) * 0.05 + fase * 0.04)
            y = h * (0.62 - fase * 0.45)
            r = 8 + fase * 60
            g = QRadialGradient(QPointF(x, y), r)
            g.setColorAt(0, QColor(220, 215, 210, int(70 * (1 - fase))))
            g.setColorAt(1, QColor(220, 215, 210, 0))
            p.setBrush(QBrush(g))
            p.drawEllipse(QPointF(x, y), r, r)


def _fundo_posapoc(p, w, h):
    _degrade(p, w, h, (0, "#3a2a44"), (0.45, "#c8703a"), (0.62, "#e8a050"), (1, "#1a1a14"))   # entardecer
    sol = QRadialGradient(QPointF(w * 0.62, h * 0.56), h * 0.3)
    sol.setColorAt(0, QColor(255, 220, 150, 230))
    sol.setColorAt(0.25, QColor(255, 180, 90, 120))
    sol.setColorAt(1, QColor(255, 160, 80, 0))
    p.fillRect(QRectF(0, 0, w, h), QBrush(sol))
    rng = random.Random(59)
    x = -20.0
    while x < w:                                            # prédios em ruínas (silhueta)
        lw = rng.uniform(w * 0.05, w * 0.12)
        topo = h * rng.uniform(0.28, 0.6)
        pts = [QPointF(x, h), QPointF(x, topo)]
        for k in range(4):                                  # topo quebrado
            pts.append(QPointF(x + lw * (k + 1) / 5, topo + rng.uniform(-10, 40)))
        pts += [QPointF(x + lw, topo + rng.uniform(0, 30)), QPointF(x + lw, h)]
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(28, 26, 22))
        p.drawPolygon(QPolygonF(pts))
        p.setBrush(QColor(52, 74, 34, 200))                 # hera escorrendo
        for _ in range(int(lw / 12)):
            vx = x + rng.uniform(0, lw)
            p.drawRect(QRectF(vx, topo + 10, rng.uniform(3, 8), rng.uniform(20, h * 0.25)))
        x += lw + rng.uniform(4, 30)
    p.setBrush(QColor(20, 20, 16))
    p.drawRect(QRectF(0, h * 0.86, w, h * 0.14))
    _vinheta(p, w, h, 190)


def _anim_posapoc(p, w, h, t, n, rnd):
    if n >= 1:                                              # pólen/poeira na luz do sol
        p.setPen(Qt.PenStyle.NoPen)
        for a, b, c, d in _pontos(67, 30 if n == 1 else 80):
            px = ((a + t * (0.004 + c * 0.01)) % 1.0) * w
            py = (b + 0.03 * math.sin(t * 0.4 + d * 9)) * h
            br = 0.4 + 0.6 * max(0.0, math.sin(t * 1.1 + d * 30))
            p.setBrush(QColor(255, 230, 170, int(150 * br)))
            r = 0.8 + d * 1.8
            p.drawEllipse(QPointF(px, py), r, r)


FUNDOS.update({"steampunk": _fundo_steampunk, "posapoc": _fundo_posapoc})
ANIMACOES = {"medieval": _anim_medieval, "moderno": _anim_moderno, "futurista": _anim_futurista,
             "magico": _anim_magico, "terror": _anim_terror, "claro": _anim_claro, "escuro": _anim_escuro,
             "steampunk": _anim_steampunk, "posapoc": _anim_posapoc}

# título, subtítulo, fundo/texto/borda do botão, brilho do botão
CORES_TELA = {
    "medieval": ("#e2bd62", "#cbbd9f", "rgba(16, 12, 9, 215)", "#e8dcc4", "#8a6d32", "#f3d991", "rgba(58, 40, 18, 230)"),
    "moderno": ("#e9eef2", "#8fd3cb", "rgba(10, 14, 20, 210)", "#e4e7eb", "#3d6b67", "#7fe3d8", "rgba(22, 48, 46, 235)"),
    "futurista": ("#38e1ff", "#ff7ac4", "rgba(4, 8, 20, 205)", "#d8f3ff", "#38e1ff", "#ffffff", "rgba(40, 14, 60, 235)"),
    "magico": ("#d9c2ff", "#8fe9dc", "rgba(16, 10, 30, 205)", "#ece2ff", "#7d5bc4", "#ffffff", "rgba(52, 34, 88, 235)"),
    "terror": ("#b3202c", "#9a9088", "rgba(6, 5, 6, 225)", "#d9d2c9", "#5a1a20", "#ff4a55", "rgba(40, 8, 12, 240)"),
    "steampunk": ("#d8b060", "#c8865a", "rgba(28, 20, 14, 215)", "#ecdcb8", "#8a6a32", "#ffd88a", "rgba(70, 46, 20, 230)"),
    "posapoc": ("#d0702a", "#a8b060", "rgba(20, 20, 16, 220)", "#e0d8c0", "#6a4a28", "#ffa060", "rgba(60, 36, 16, 235)"),
    "claro": ("#1d1f24", "#5a616c", "rgba(255, 255, 255, 230)", "#1d1f24", "#cfd4db", "#3a6df0", "rgba(240, 243, 248, 240)"),
    "escuro": ("#e6e7ea", "#7c9cff", "rgba(18, 19, 22, 220)", "#e6e7ea", "#3a4054", "#a9bcff", "rgba(32, 40, 66, 240)"),
}


def _estilo_botao(chave: str) -> str:
    t = dados_tema(chave)
    _tit, _sub, fundo, texto, borda, brilho, fundo_hover = CORES_TELA.get(chave, CORES_TELA["medieval"])
    serifa = "sans" not in t["fonte_titulo"]
    tam_botao = {"medieval": 15, "terror": 17, "moderno": 17, "futurista": 11, "magico": 12}.get(chave, 15 if serifa else 13)
    return f"""
QPushButton {{
    background: {fundo}; color: {texto}; border: 1px solid {borda}; border-radius: {max(2, t['raio'])}px;
    padding: 14px 30px; font-family: {t['fonte_titulo']}; font-size: {tam_botao}pt;
    letter-spacing: {3 if serifa else 4}px; min-width: 300px;
}}
QPushButton:hover {{ background: {fundo_hover}; color: {brilho}; border-color: {brilho}; }}
QPushButton:pressed {{ background: {fundo_hover}; padding-top: 16px; padding-bottom: 12px; }}
QPushButton:disabled {{ color: {t['fraco']}; border-color: {t['borda']}; }}
"""


class TelaInicial(QWidget):
    """
    Tela de entrada. `botoes` é uma lista de (texto, chave). Ao clicar, emite
    `escolhido(chave)`. `tema_escolhido(chave)` quando a pessoa troca o tema aqui.
    """
    escolhido = pyqtSignal(str)
    tema_escolhido = pyqtSignal(str)

    def __init__(self, subtitulo: str, botoes: list[tuple[str, str]], parent=None, tema_inicial: str = TEMA_PADRAO):
        super().__init__(parent)
        self._fundo: QPixmap | None = None
        self._t = 0.0
        self._rnd = random.Random()
        self.tema = tema_inicial if tema_inicial in TEMAS else TEMA_PADRAO
        self.botoes: dict[str, QPushButton] = {}

        self.titulo = QLabel("TAVERNA")
        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sombra_titulo = QGraphicsDropShadowEffect(self.titulo)   # (o título é desenhado à mão no paintEvent)

        self.sub = QLabel(f"— {subtitulo} —")
        self.sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sombra2 = QGraphicsDropShadowEffect(self.sub)
        sombra2.setBlurRadius(16)
        sombra2.setOffset(0, 2)
        self._sombra_sub = sombra2
        self.sub.setGraphicsEffect(sombra2)

        self.info = QLabel("")
        self.info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        coluna = QVBoxLayout()
        coluna.setSpacing(14)
        coluna.addStretch(3)
        coluna.addWidget(self.titulo)
        coluna.addWidget(self.sub)
        coluna.addSpacing(64)
        for texto, chave in botoes:
            b = QPushButton(texto.upper())
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFixedWidth(380)
            b.clicked.connect(lambda _=False, k=chave: self.escolhido.emit(k))
            sombra_b = QGraphicsDropShadowEffect(b)
            sombra_b.setBlurRadius(24)
            sombra_b.setOffset(0, 6)
            sombra_b.setColor(QColor(0, 0, 0, 200))
            b.setGraphicsEffect(sombra_b)
            coluna.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
            self.botoes[chave] = b
        coluna.addSpacing(8)
        coluna.addWidget(self.info)
        coluna.addStretch(4)

        # rodapé: tema e gráficos (preferências deste PC) + versão
        self.cb_tema = QComboBox()
        for chave, t in TEMAS.items():
            self.cb_tema.addItem(f"🎨 {t['nome']}", chave)
        self.cb_tema.setToolTip("Tema da tela inicial. (Dentro da aventura vale o tema que o mestre escolheu pra ela.)")
        self.cb_tema.setCurrentIndex(self.cb_tema.findData(self.tema))
        self.cb_tema.currentIndexChanged.connect(lambda _i: self._trocar_tema())
        self.cb_graficos = QComboBox()
        for chave, nome in NIVEIS.items():
            self.cb_graficos.addItem(f"✨ Gráficos: {nome.split(' — ')[0]}", chave)
            self.cb_graficos.setItemData(self.cb_graficos.count() - 1, nome, Qt.ItemDataRole.ToolTipRole)
        self.cb_graficos.setToolTip("Qualidade dos efeitos e animações. Baixo = mais leve.")
        self.cb_graficos.setCurrentIndex(self.cb_graficos.findData(graficos().atual))
        self.cb_graficos.currentIndexChanged.connect(lambda _i: graficos().definir(self.cb_graficos.currentData()))
        graficos().mudou.connect(self._graficos_mudou)
        self.versao = QLabel(f"v{APP_VERSAO}")
        rodape = QHBoxLayout()
        rodape.addWidget(self.cb_tema)
        rodape.addWidget(self.cb_graficos)
        rodape.addStretch(1)
        rodape.addWidget(self.versao)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 12)
        layout.addLayout(coluna)
        layout.addLayout(rodape)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._passo)
        self._aplicar_estilo()

    # ------------------------------------------------------------ tema
    def definir_tema(self, chave: str):
        if chave not in TEMAS or chave == self.tema:
            return
        self.tema = chave
        self.cb_tema.blockSignals(True)
        self.cb_tema.setCurrentIndex(self.cb_tema.findData(chave))
        self.cb_tema.blockSignals(False)
        self._fundo = None
        self._aplicar_estilo()
        self.update()

    def _trocar_tema(self):
        chave = self.cb_tema.currentData()
        self.definir_tema(chave)
        self.tema_escolhido.emit(chave)

    def _aplicar_estilo(self):
        t = dados_tema(self.tema)
        tit, sub, fundo, texto, borda, brilho, _fh = CORES_TELA.get(self.tema, CORES_TELA["medieval"])
        from .tema import carregar_fontes
        carregar_fontes()
        serifa = "serif" in t["fonte_titulo"] and "sans" not in t["fonte_titulo"]
        # (tamanho, espaço entre letras, negrito) — cada fonte pede um ajuste
        tam, espaco, negrito = {"medieval": (112, 10, False), "moderno": (132, 20, False),
                                "futurista": (80, 22, True), "magico": (88, 10, True),
                                "terror": (132, 12, False), "claro": (96, 14, True),
                                "escuro": (84, 18, False)}.get(self.tema, (96, 14, True))
        peso = "bold" if negrito else "normal"
        self._fonte_titulo = (t["fonte_titulo"].split(",")[0].strip("'\" "), tam, espaco, peso == "bold")
        self.titulo.setStyleSheet(f"color: transparent; background: transparent; font-family: {t['fonte_titulo']}; "
                                  f"font-size: {tam}px; font-weight: {peso}; letter-spacing: {espaco}px;")
        claro = t["claro"]
        cor_sombra = {"futurista": QColor(56, 225, 255, 200), "magico": QColor(150, 100, 255, 220),
                      "terror": QColor(120, 0, 0, 255)}.get(self.tema, QColor(255, 250, 235, 230) if claro
                                                           else QColor(0, 0, 0, 255))
        self._cor_brilho_titulo = cor_sombra
        self.sub.setStyleSheet(f"color: {sub}; background: transparent; font-family: {t['fonte_titulo']}; "
                               f"font-size: 22px; font-style: {'italic' if serifa else 'normal'}; letter-spacing: 4px;")
        self._sombra_sub.setColor(QColor(255, 250, 235, 200) if claro else QColor(0, 0, 0, 255))
        self.info.setStyleSheet(f"color: {sub}; background: transparent; font-size: 10pt;")
        self.versao.setStyleSheet(f"color: {sub}; background: transparent;")
        estilo = _estilo_botao(self.tema)
        for b in self.botoes.values():
            b.setStyleSheet(estilo)
        combo = (f"QComboBox {{ background: {fundo}; color: {texto}; border: 1px solid {borda}; "
                 f"border-radius: {max(2, t['raio'])}px; padding: 5px 10px; min-width: 150px; }}"
                 f"QComboBox:hover {{ border-color: {brilho}; }}")
        self.cb_tema.setStyleSheet(combo)
        self.cb_graficos.setStyleSheet(combo)

    def _graficos_mudou(self, chave):
        self.cb_graficos.blockSignals(True)
        self.cb_graficos.setCurrentIndex(self.cb_graficos.findData(chave))
        self.cb_graficos.blockSignals(False)
        self._ligar_timer()
        self.update()

    # ------------------------------------------------------------ animação
    def _ligar_timer(self):
        n = nivel()
        if n == 0 or not self.isVisible():
            self._timer.stop()
        else:
            self._timer.start(70 if n == 1 else 33)

    def showEvent(self, event):
        self._ligar_timer()
        super().showEvent(event)

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def resizeEvent(self, event):
        self._fundo = None
        super().resizeEvent(event)

    def _passo(self):
        self._t += self._timer.interval() / 1000
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        w, h = max(1, self.width()), max(1, self.height())
        if self._fundo is None or self._fundo.size() != self.size():
            self._fundo = desenhar_fundo(self.tema, w, h)
        p.drawPixmap(0, 0, self._fundo)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        ANIMACOES.get(self.tema, _anim_medieval)(p, w, h, self._t if nivel() else 2.0, nivel(), self._rnd)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        # faixa atrás dos botões pra leitura
        claro = dados_tema(self.tema)["claro"]
        meio = QLinearGradient(QPointF(w * 0.28, 0), QPointF(w * 0.72, 0))
        cor = (255, 250, 235) if claro else (0, 0, 0)
        meio.setColorAt(0, QColor(*cor, 0))
        meio.setColorAt(0.5, QColor(*cor, 95 if self.tema != "medieval" else 70))
        meio.setColorAt(1, QColor(*cor, 0))
        p.fillRect(self.rect(), QBrush(meio))
        if self.tema == "medieval":
            self._tochas(p, w, h)
        self._placa(p)
        self._titulo_em_relevo(p)
        p.end()

    # ------------------------------------------------------------ peças com volume
    def _tochas(self, p, w, h):
        """Duas tochas de parede (suporte de ferro + chama viva) onde a luz nasce."""
        t = self._t if nivel() else 2.0
        for i, x in enumerate((w * 0.12, w * 0.88)):
            y = h * 0.36
            p.setPen(Qt.PenStyle.NoPen)
            # suporte: placa na parede, braço e copo de ferro
            ferro = QLinearGradient(x - 14, 0, x + 14, 0)
            ferro.setColorAt(0, QColor(70, 66, 62))
            ferro.setColorAt(0.5, QColor(34, 31, 29))
            ferro.setColorAt(1, QColor(14, 12, 11))
            p.setBrush(QBrush(ferro))
            p.drawRoundedRect(QRectF(x - 9, y + 52, 18, 64), 3, 3)
            p.drawPolygon(QPolygonF([QPointF(x - 5, y + 70), QPointF(x + 5, y + 70), QPointF(x + 4, y + 26), QPointF(x - 4, y + 26)]))
            p.drawPolygon(QPolygonF([QPointF(x - 17, y + 6), QPointF(x + 17, y + 6), QPointF(x + 10, y + 32), QPointF(x - 10, y + 32)]))
            p.setBrush(QColor(120, 112, 100))
            for ry in (58, 108):
                p.drawEllipse(QPointF(x, y + ry), 2.2, 2.2)
            # madeira e brasa
            p.setBrush(QColor(60, 36, 18))
            p.drawRect(QRectF(x - 6, y - 2, 12, 12))
            # chama em três camadas
            for larg, alt, cores, fase in ((17, 62, ((255, 80, 20, 210), (255, 150, 30, 150), (255, 220, 110, 0)), 0.0),
                                           (11, 44, ((255, 170, 40, 230), (255, 215, 90, 170), (255, 245, 180, 0)), 1.3),
                                           (5.5, 26, ((255, 250, 215, 245), (255, 235, 150, 190), (255, 255, 220, 0)), 2.1)):
                a = alt * (0.86 + 0.14 * math.sin(t * 9 + i * 2 + fase))
                bal = math.sin(t * 5.3 + i * 1.7 + fase) * larg * 0.55
                chama = QPainterPath()
                chama.moveTo(x - larg, y + 4)
                chama.cubicTo(x - larg, y - a * 0.45, x + bal * 0.5 - larg * 0.3, y - a * 0.7, x + bal, y - a)
                chama.cubicTo(x + bal * 0.5 + larg * 0.3, y - a * 0.7, x + larg, y - a * 0.45, x + larg, y + 4)
                g = QLinearGradient(x, y + 4, x, y - a)
                for pos, cor in zip((0, 0.5, 1), cores):
                    g.setColorAt(pos, QColor(*cor))
                p.fillPath(chama, QBrush(g))

    def _placa(self, p):
        """Moldura atrás dos botões, com cantoneiras — dá corpo ao menu."""
        if not self.botoes:
            return
        t = dados_tema(self.tema)
        _tit, sub, _f, _tx, borda, brilho, _fh = CORES_TELA.get(self.tema, CORES_TELA["medieval"])
        bs = list(self.botoes.values())
        topo = bs[0].geometry().top() - 26
        base = self.info.geometry().bottom() + 14
        cx = bs[0].geometry().center().x()
        r = QRectF(cx - 232, topo, 464, base - topo)
        raio = max(2, t["raio"] + 2)
        claro = t["claro"]
        fundo = QLinearGradient(r.topLeft(), r.bottomLeft())
        if claro:
            fundo.setColorAt(0, QColor(255, 250, 236, 150))
            fundo.setColorAt(1, QColor(226, 208, 164, 150))
        else:
            fundo.setColorAt(0, QColor(255, 255, 255, 16))
            fundo.setColorAt(0.08, QColor(0, 0, 0, 120))
            fundo.setColorAt(1, QColor(0, 0, 0, 165))
        p.setPen(Qt.PenStyle.NoPen)
        for k in (10, 6, 3):   # sombra da placa
            p.setBrush(QColor(0, 0, 0, 30 if not claro else 14))
            p.drawRoundedRect(r.adjusted(-k * 0.3, 0, k, k).translated(2, 5), raio, raio)
        p.setBrush(QBrush(fundo))
        p.drawRoundedRect(r, raio, raio)
        cb = QColor(borda)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(cb, 1.6))
        p.drawRoundedRect(r, raio, raio)
        p.setPen(QPen(QColor(cb.red(), cb.green(), cb.blue(), 110), 1))
        p.drawRoundedRect(r.adjusted(6, 6, -6, -6), max(1, raio - 2), max(1, raio - 2))
        # cantoneiras
        cbri = QColor(brilho)
        for ex, ey in ((r.left(), r.top()), (r.right(), r.top()), (r.left(), r.bottom()), (r.right(), r.bottom())):
            sx = 1 if ex == r.left() else -1
            sy = 1 if ey == r.top() else -1
            p.setPen(QPen(cbri, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap))
            p.drawLine(QPointF(ex, ey + sy * 26), QPointF(ex, ey))
            p.drawLine(QPointF(ex, ey), QPointF(ex + sx * 26, ey))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(cbri)
            c = QPointF(ex + sx * 13, ey + sy * 13)
            p.drawPolygon(QPolygonF([c + QPointF(0, -4.5), c + QPointF(4.5, 0), c + QPointF(0, 4.5), c + QPointF(-4.5, 0)]))
        # enfeite entre o subtítulo e o menu:  ——◆——
        y = topo - 16
        csub = QColor(sub)
        p.setPen(QPen(QColor(csub.red(), csub.green(), csub.blue(), 170), 1.3))
        p.drawLine(QPointF(cx - 150, y), QPointF(cx - 14, y))
        p.drawLine(QPointF(cx + 14, y), QPointF(cx + 150, y))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(csub)
        p.drawPolygon(QPolygonF([QPointF(cx, y - 6), QPointF(cx + 6, y), QPointF(cx, y + 6), QPointF(cx - 6, y)]))
        for dx in (-158, 158):
            p.drawEllipse(QPointF(cx + dx, y), 2.2, 2.2)

    def _titulo_em_relevo(self, p):
        """TAVERNA desenhado como letra de metal/neon: contorno, degradê, quina de luz e brilho."""
        familia, tam, espaco, negrito = self._fonte_titulo
        fonte = QFont(familia)
        fonte.setPixelSize(tam)
        fonte.setBold(negrito)
        fonte.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, espaco)
        letras = QPainterPath()
        letras.addText(0, 0, fonte, "TAVERNA")
        caixa = letras.boundingRect()
        g = self.titulo.geometry()
        letras.translate(g.center().x() - caixa.center().x() + espaco / 2, g.center().y() - caixa.center().y())
        caixa = letras.boundingRect()
        base = QColor(CORES_TELA.get(self.tema, CORES_TELA["medieval"])[0])
        brilho = self._cor_brilho_titulo
        claro = dados_tema(self.tema)["claro"]
        neon = self.tema in ("futurista", "magico", "terror")
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(Qt.BrushStyle.NoBrush)
        if neon:   # halo de luz em volta das letras
            pulso = 0.8 + 0.2 * math.sin(self._t * (2.2 if self.tema != "terror" else 0.9)) if nivel() else 1.0
            for larg, alfa in ((34, 16), (22, 26), (12, 44), (6, 70)):
                p.setPen(QPen(QColor(brilho.red(), brilho.green(), brilho.blue(), int(alfa * pulso)), larg,
                              Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                p.drawPath(letras)
        else:      # sombra projetada + "espessura" da letra
            p.setPen(Qt.PenStyle.NoPen)
            for k, alfa in ((14, 26), (9, 40), (5, 60)):
                p.setBrush(QColor(255, 250, 235, alfa) if claro else QColor(0, 0, 0, alfa + 30))
                p.drawPath(letras.translated(k * 0.35, k * 0.7))
            fundo = base.darker(300)
            for k in range(6, 0, -1):
                p.setBrush(fundo.lighter(100 + (6 - k) * 8))
                p.drawPath(letras.translated(k * 0.5, k))
        # contorno escuro e o preenchimento em degradê
        p.setPen(QPen(base.darker(380) if not claro else base.darker(170), 3.2, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(letras)
        grad = QLinearGradient(0, caixa.top(), 0, caixa.bottom())
        grad.setColorAt(0.0, base.lighter(165))
        grad.setColorAt(0.42, base.lighter(112))
        grad.setColorAt(0.5, base.darker(118))
        grad.setColorAt(1.0, base.darker(175 if not neon else 130))
        p.setPen(Qt.PenStyle.NoPen)
        p.fillPath(letras, QBrush(grad))
        # quina: filete claro em cima-esquerda, escuro embaixo-direita (por dentro da letra)
        p.save()
        p.setClipPath(letras, Qt.ClipOperation.IntersectClip)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 150 if not claro else 110), 2.2))
        p.drawPath(letras.translated(1.4, 1.6))
        p.setPen(QPen(QColor(0, 0, 0, 120), 2.2))
        p.drawPath(letras.translated(-1.4, -1.6))
        if nivel() >= 1:   # um brilho que passa pelas letras de vez em quando
            ciclo = (self._t * 0.22) % 1.0
            x = caixa.left() - 80 + (caixa.width() + 160) * min(1.0, ciclo * 2.2)
            if ciclo < 0.46:
                faixa = QLinearGradient(x - 46, 0, x + 46, 0)
                faixa.setColorAt(0, QColor(255, 255, 255, 0))
                faixa.setColorAt(0.5, QColor(255, 255, 255, 120))
                faixa.setColorAt(1, QColor(255, 255, 255, 0))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(faixa))
                p.drawPolygon(QPolygonF([QPointF(x - 30, caixa.bottom() + 4), QPointF(x + 22, caixa.bottom() + 4),
                                         QPointF(x + 62, caixa.top() - 4), QPointF(x + 10, caixa.top() - 4)]))
        p.restore()
