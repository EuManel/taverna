"""
Props: objetos de cenário (móveis, baús, barris, estátuas, árvores, computadores...).

- Desenhados pelo próprio programa (vista de cima), em qualquer tamanho, ou a partir de
  uma imagem PNG do mestre.
- Alguns BLOQUEIAM A VISÃO (pilar, estátua, estante...) e entram na linha de visão/luz.
- Alguns ILUMINAM (lareira, lustre, poste...) e funcionam como fonte de luz.
- INTERATIVOS (baú, barril, armário...): o mestre guarda itens dentro; o jogador chega perto,
  abre (duplo clique) e vê o que tem. Pode pegar, se o mestre deixar.
"""

import base64
import hashlib
import math
import random
import uuid
import zlib

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath,
                         QPen, QPixmap, QPolygonF, QRadialGradient)
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsObject

from ..config import CELULA, COR_DESTAQUE

# ====================================================================== cores
MADEIRA = QColor("#7a5232")
MADEIRA_ESC = QColor("#4e3220")
MADEIRA_CLA = QColor("#9c7048")
METAL = QColor("#8d939b")
METAL_ESC = QColor("#4b5058")
PEDRA = QColor("#8b867e")
PEDRA_ESC = QColor("#5c5852")
TECIDO = QColor("#8a2f2f")
TECIDO_AZUL = QColor("#2f4f7a")
VERDE = QColor("#3f6e3a")
VERDE_ESC = QColor("#24451f")
OURO = QColor("#c9a24a")
CONTORNO = QColor(18, 13, 9)


def _caneta(cor=CONTORNO, larg=2.0):
    p = QPen(cor, larg)
    p.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return p


def _ret(p, r, cor, raio=4, borda=CONTORNO, larg=2.0):
    p.setPen(_caneta(borda, larg) if borda is not None else Qt.PenStyle.NoPen)
    p.setBrush(cor)
    p.drawRoundedRect(r, raio, raio)


def _circ(p, c, raio, cor, borda=CONTORNO, larg=2.0):
    p.setPen(_caneta(borda, larg) if borda is not None else Qt.PenStyle.NoPen)
    p.setBrush(cor)
    p.drawEllipse(c, raio, raio)


def _tabuas(p, r, n, cor=MADEIRA_ESC, vertical=False):
    p.setPen(_caneta(cor, 1.2))
    for k in range(1, n):
        if vertical:
            x = r.left() + r.width() * k / n
            p.drawLine(QPointF(x, r.top() + 2), QPointF(x, r.bottom() - 2))
        else:
            y = r.top() + r.height() * k / n
            p.drawLine(QPointF(r.left() + 2, y), QPointF(r.right() - 2, y))


def _sombra(p, r, raio=6):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(0, 0, 0, 70))
    p.drawRoundedRect(r.translated(3, 4), raio, raio)


def _m(r, f):
    """Recuo proporcional ao tamanho."""
    d = min(r.width(), r.height()) * f
    return r.adjusted(d, d, -d, -d)


# ====================================================================== desenhos
def d_mesa(p, r):
    t = _m(r, 0.08)
    _sombra(p, t)
    _ret(p, t, MADEIRA)
    _tabuas(p, t, max(2, round(t.width() / CELULA * 2)), vertical=t.width() >= t.height())


def d_mesa_redonda(p, r):
    c, raio = r.center(), min(r.width(), r.height()) * 0.44
    _circ(p, c + QPointF(3, 4), raio, QColor(0, 0, 0, 70), None)
    _circ(p, c, raio, MADEIRA)
    p.setPen(_caneta(MADEIRA_ESC, 1.2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(c, raio * 0.7, raio * 0.7)


def d_cadeira(p, r):
    a = _m(r, 0.18)
    _sombra(p, a)
    _ret(p, a, MADEIRA, 3)
    encosto = QRectF(a.left(), a.top(), a.width(), a.height() * 0.22)
    _ret(p, encosto, MADEIRA_ESC, 3)


def d_banco(p, r):
    a = r.adjusted(r.width() * 0.05, r.height() * 0.28, -r.width() * 0.05, -r.height() * 0.28)
    _sombra(p, a)
    _ret(p, a, MADEIRA, 3)
    _tabuas(p, a, 2)


def d_cama(p, r, cor=TECIDO):
    a = _m(r, 0.06)
    _sombra(p, a)
    _ret(p, a, MADEIRA_ESC, 4)
    colchao = a.adjusted(4, 4, -4, -4)
    _ret(p, colchao, QColor("#d9cfba"), 3, None)
    coberta = QRectF(colchao.left(), colchao.top() + colchao.height() * 0.3,
                     colchao.width(), colchao.height() * 0.7)
    _ret(p, coberta, cor, 3, None)
    n = 2 if a.width() > a.height() * 0.8 else 1
    larg = colchao.width() / n
    for k in range(n):
        trav = QRectF(colchao.left() + k * larg + 4, colchao.top() + 3, larg - 8, colchao.height() * 0.2)
        _ret(p, trav, QColor("#f2ead9"), 4, QColor("#9a9080"), 1)


def d_cama_casal(p, r):
    d_cama(p, r, TECIDO_AZUL)


def d_penteadeira(p, r):
    a = r.adjusted(r.width() * 0.04, r.height() * 0.25, -r.width() * 0.04, -r.height() * 0.05)
    _sombra(p, a)
    _ret(p, a, MADEIRA, 3)
    espelho = QRectF(a.center().x() - a.width() * 0.2, a.top() - a.height() * 0.35, a.width() * 0.4,
                     a.height() * 0.45)
    _ret(p, espelho, QColor("#a8c4cf"), 10, MADEIRA_ESC)
    for k in (0.2, 0.8):
        _circ(p, QPointF(a.left() + a.width() * k, a.center().y()), 2.5, OURO, None)


def d_guarda_roupa(p, r):
    a = r.adjusted(r.width() * 0.03, r.height() * 0.1, -r.width() * 0.03, -r.height() * 0.1)
    _sombra(p, a)
    _ret(p, a, MADEIRA_ESC, 3)
    _ret(p, a.adjusted(4, 4, -4, -4), MADEIRA, 2, None)
    p.setPen(_caneta(MADEIRA_ESC, 2))
    p.drawLine(QPointF(a.center().x(), a.top() + 4), QPointF(a.center().x(), a.bottom() - 4))
    for dx in (-5, 5):
        _circ(p, QPointF(a.center().x() + dx, a.center().y()), 2.2, OURO, None)


def d_estante(p, r):
    a = r.adjusted(r.width() * 0.02, r.height() * 0.2, -r.width() * 0.02, -r.height() * 0.2)
    _sombra(p, a)
    _ret(p, a, MADEIRA_ESC, 2)
    aleat = random.Random(int(a.width() * 7 + a.height()))
    x = a.left() + 4
    cores = ["#7a2e2e", "#2e4f7a", "#3f6e3a", "#8a6a2a", "#5a3a6a", "#a07848"]
    while x < a.right() - 6:
        larg = aleat.uniform(4, 9)
        livro = QRectF(x, a.top() + 3, min(larg, a.right() - 4 - x), a.height() - 6)
        _ret(p, livro, QColor(aleat.choice(cores)), 1, CONTORNO, 0.8)
        x += larg + 0.8


def d_armario(p, r):
    a = _m(r, 0.1)
    _sombra(p, a)
    _ret(p, a, MADEIRA, 3)
    _ret(p, a.adjusted(5, 5, -5, -5), MADEIRA_CLA, 2, MADEIRA_ESC, 1.2)
    _circ(p, QPointF(a.right() - 9, a.center().y()), 2.5, OURO, None)


def d_sofa(p, r):
    a = _m(r, 0.06)
    _sombra(p, a)
    _ret(p, a, QColor("#6a3a2a"), 8)
    assento = a.adjusted(a.width() * 0.12, a.height() * 0.32, -a.width() * 0.12, -3)
    _ret(p, assento, QColor("#8a4a36"), 5, QColor("#4a2418"), 1.2)
    n = max(1, round(assento.width() / (CELULA * 0.9)))
    p.setPen(_caneta(QColor("#4a2418"), 1))
    for k in range(1, n):
        x = assento.left() + assento.width() * k / n
        p.drawLine(QPointF(x, assento.top() + 2), QPointF(x, assento.bottom() - 2))


def d_tapete(p, r):
    a = _m(r, 0.04)
    _ret(p, a, QColor("#7a2a2a"), 2, QColor("#3a1414"), 1.5)
    _ret(p, a.adjusted(6, 6, -6, -6), QColor("#9a4a2a"), 2, OURO, 1.5)
    p.setPen(_caneta(OURO, 1.2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    c = a.center()
    p.drawPolygon(QPolygonF([QPointF(c.x(), a.top() + 12), QPointF(a.right() - 12, c.y()),
                             QPointF(c.x(), a.bottom() - 12), QPointF(a.left() + 12, c.y())]))


def d_balcao(p, r):
    a = r.adjusted(r.width() * 0.02, r.height() * 0.15, -r.width() * 0.02, -r.height() * 0.15)
    _sombra(p, a)
    _ret(p, a, MADEIRA_ESC, 3)
    _ret(p, a.adjusted(3, 3, -3, -a.height() * 0.45), MADEIRA_CLA, 2, None)
    for k in range(3):
        _circ(p, QPointF(a.left() + a.width() * (0.25 + k * 0.25), a.center().y() + 3), 4,
              QColor("#c8b890"), CONTORNO, 1)


# ---------------------------------------------------------------------- recipientes
def d_bau(p, r):
    a = r.adjusted(r.width() * 0.1, r.height() * 0.2, -r.width() * 0.1, -r.height() * 0.12)
    _sombra(p, a)
    _ret(p, a, MADEIRA, 3)
    _tabuas(p, a, 3)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(METAL_ESC)
    for k in (0.18, 0.82):
        p.drawRect(QRectF(a.left() + a.width() * k - 3, a.top(), 6, a.height()))
    tampa = QRectF(a.left(), a.top(), a.width(), a.height() * 0.32)
    _ret(p, tampa, MADEIRA_ESC, 3)
    _ret(p, QRectF(a.center().x() - 5, a.top() + a.height() * 0.22, 10, 10), OURO, 2, CONTORNO, 1.2)


def d_caixote(p, r):
    a = _m(r, 0.12)
    _sombra(p, a, 2)
    _ret(p, a, MADEIRA_CLA, 2)
    _ret(p, a.adjusted(4, 4, -4, -4), MADEIRA, 1, MADEIRA_ESC, 1.2)
    p.setPen(_caneta(MADEIRA_ESC, 3))
    p.drawLine(a.topLeft() + QPointF(5, 5), a.bottomRight() - QPointF(5, 5))


def d_barril(p, r):
    c, raio = r.center(), min(r.width(), r.height()) * 0.38
    _circ(p, c + QPointF(3, 4), raio, QColor(0, 0, 0, 70), None)
    _circ(p, c, raio, MADEIRA)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(_caneta(METAL_ESC, 3))
    p.drawEllipse(c, raio * 0.82, raio * 0.82)
    p.setPen(_caneta(MADEIRA_ESC, 1))
    for k in range(-2, 3):
        x = c.x() + k * raio * 0.3
        h = math.sqrt(max(0, (raio * 0.75) ** 2 - (x - c.x()) ** 2))
        p.drawLine(QPointF(x, c.y() - h), QPointF(x, c.y() + h))


def d_cacifo(p, r):
    a = r.adjusted(r.width() * 0.2, r.height() * 0.08, -r.width() * 0.2, -r.height() * 0.08)
    _sombra(p, a, 2)
    _ret(p, a, METAL, 2)
    p.setPen(_caneta(METAL_ESC, 1))
    for k in range(3):
        y = a.top() + 6 + k * 4
        p.drawLine(QPointF(a.left() + 5, y), QPointF(a.right() - 5, y))
    _circ(p, QPointF(a.right() - 6, a.center().y()), 2, METAL_ESC, None)


def d_saco(p, r):
    c = r.center()
    caminho = QPainterPath()
    w, h = r.width() * 0.34, r.height() * 0.36
    caminho.moveTo(c.x() - w * 0.4, c.y() - h)
    caminho.cubicTo(c.x() - w * 1.3, c.y() - h * 0.2, c.x() - w * 1.1, c.y() + h, c.x(), c.y() + h)
    caminho.cubicTo(c.x() + w * 1.1, c.y() + h, c.x() + w * 1.3, c.y() - h * 0.2, c.x() + w * 0.4, c.y() - h)
    caminho.closeSubpath()
    p.setPen(_caneta())
    p.setBrush(QColor("#a08a62"))
    p.drawPath(caminho)
    p.setPen(_caneta(QColor("#5a4a32"), 2))
    p.drawLine(QPointF(c.x() - w * 0.45, c.y() - h * 0.75), QPointF(c.x() + w * 0.45, c.y() - h * 0.75))


def d_urna(p, r):
    c, raio = r.center(), min(r.width(), r.height()) * 0.34
    _circ(p, c, raio, QColor("#9a5a3a"))
    _circ(p, c, raio * 0.45, QColor("#5a2a1a"), CONTORNO, 1.5)
    p.setPen(_caneta(OURO, 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(c, raio * 0.75, raio * 0.75)


def d_cofre(p, r):
    a = _m(r, 0.14)
    _sombra(p, a, 2)
    _ret(p, a, METAL_ESC, 3)
    _ret(p, a.adjusted(4, 4, -4, -4), METAL, 2, None)
    _circ(p, a.center(), min(a.width(), a.height()) * 0.18, METAL_ESC, CONTORNO, 1.5)
    p.setPen(_caneta(OURO, 1.5))
    c = a.center()
    raio = min(a.width(), a.height()) * 0.18
    for ang in range(0, 360, 60):
        rad = math.radians(ang)
        p.drawLine(c, c + QPointF(math.cos(rad) * raio, math.sin(rad) * raio))


def d_caixao(p, r):
    a = _m(r, 0.08)
    w, h = a.width(), a.height()
    if w > h:
        pts = [QPointF(a.left(), a.center().y()), QPointF(a.left() + w * 0.25, a.top()),
               QPointF(a.right(), a.top() + h * 0.15), QPointF(a.right(), a.bottom() - h * 0.15),
               QPointF(a.left() + w * 0.25, a.bottom())]
    else:
        pts = [QPointF(a.center().x(), a.top()), QPointF(a.right(), a.top() + h * 0.25),
               QPointF(a.right() - w * 0.15, a.bottom()), QPointF(a.left() + w * 0.15, a.bottom()),
               QPointF(a.left(), a.top() + h * 0.25)]
    p.setPen(_caneta())
    p.setBrush(MADEIRA_ESC)
    p.drawPolygon(QPolygonF(pts))
    p.setPen(_caneta(OURO, 1.5))
    c = a.center()
    p.drawLine(c + QPointF(0, -h * 0.18), c + QPointF(0, h * 0.18))
    p.drawLine(c + QPointF(-w * 0.12, -h * 0.06), c + QPointF(w * 0.12, -h * 0.06))


# ---------------------------------------------------------------------- cenário
def _chamas(p, c, raio):
    grad = QRadialGradient(c, raio)
    grad.setColorAt(0, QColor(255, 240, 160))
    grad.setColorAt(0.5, QColor(255, 150, 40))
    grad.setColorAt(1, QColor(200, 50, 20, 0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(grad))
    p.drawEllipse(c, raio, raio)


def d_fogueira(p, r):
    c, raio = r.center(), min(r.width(), r.height()) * 0.38
    for k in range(8):
        ang = math.radians(k * 45)
        _circ(p, c + QPointF(math.cos(ang) * raio * 0.85, math.sin(ang) * raio * 0.85), raio * 0.2,
              PEDRA, CONTORNO, 1.2)
    p.setPen(_caneta(MADEIRA_ESC, 4))
    p.drawLine(c + QPointF(-raio * 0.5, -raio * 0.3), c + QPointF(raio * 0.5, raio * 0.3))
    p.drawLine(c + QPointF(-raio * 0.5, raio * 0.3), c + QPointF(raio * 0.5, -raio * 0.3))
    _chamas(p, c, raio * 0.55)


def d_lareira(p, r):
    a = r.adjusted(r.width() * 0.03, r.height() * 0.05, -r.width() * 0.03, -r.height() * 0.3)
    _ret(p, a, PEDRA, 3)
    _ret(p, a.adjusted(3, 3, -3, -a.height() * 0.6), PEDRA_ESC, 2, None)
    boca = QRectF(a.left() + a.width() * 0.2, a.top() + a.height() * 0.3, a.width() * 0.6, a.height() * 0.65)
    _ret(p, boca, QColor(30, 18, 12), 4, CONTORNO)
    _chamas(p, QPointF(boca.center().x(), boca.bottom() - boca.height() * 0.3), boca.height() * 0.5)


def d_poco(p, r):
    c, raio = r.center(), min(r.width(), r.height()) * 0.42
    _circ(p, c + QPointF(3, 4), raio, QColor(0, 0, 0, 70), None)
    _circ(p, c, raio, PEDRA)
    _circ(p, c, raio * 0.7, QColor(20, 30, 40), CONTORNO)
    _circ(p, c + QPointF(-raio * 0.15, -raio * 0.15), raio * 0.25, QColor(60, 90, 110, 120), None)
    p.setPen(_caneta(MADEIRA_ESC, 4))
    p.drawLine(QPointF(c.x() - raio * 1.05, c.y()), QPointF(c.x() + raio * 1.05, c.y()))


def d_estatua(p, r):
    c, raio = r.center(), min(r.width(), r.height()) * 0.44
    _ret(p, QRectF(c.x() - raio, c.y() - raio, raio * 2, raio * 2), PEDRA_ESC, 3)
    _circ(p, c, raio * 0.62, PEDRA)
    _circ(p, c + QPointF(0, -raio * 0.1), raio * 0.3, QColor("#a8a39a"), CONTORNO, 1.5)
    p.setPen(_caneta(PEDRA_ESC, 2))
    p.drawLine(c + QPointF(-raio * 0.55, raio * 0.15), c + QPointF(raio * 0.55, raio * 0.15))


def d_altar(p, r):
    a = r.adjusted(r.width() * 0.05, r.height() * 0.15, -r.width() * 0.05, -r.height() * 0.15)
    _sombra(p, a)
    _ret(p, a, QColor("#a8a39a"), 3)
    _ret(p, a.adjusted(5, 5, -5, -5), QColor("#d8d0c0"), 2, None)
    pano = QRectF(a.center().x() - a.width() * 0.15, a.top(), a.width() * 0.3, a.height())
    _ret(p, pano, TECIDO, 0, None)
    for k in (0.15, 0.85):
        cv = QPointF(a.left() + a.width() * k, a.center().y())
        _circ(p, cv, 3, QColor("#efe6c8"), CONTORNO, 1)
        _chamas(p, cv, 5)


def d_pilar(p, r):
    c, raio = r.center(), min(r.width(), r.height()) * 0.42
    _circ(p, c + QPointF(4, 5), raio, QColor(0, 0, 0, 90), None)
    grad = QRadialGradient(c - QPointF(raio * 0.3, raio * 0.3), raio * 1.4)
    grad.setColorAt(0, QColor("#bdb7ad"))
    grad.setColorAt(1, PEDRA_ESC)
    _circ(p, c, raio, QBrush(grad))
    p.setPen(_caneta(PEDRA_ESC, 1))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(c, raio * 0.7, raio * 0.7)


def d_arvore(p, r):
    c, raio = r.center(), min(r.width(), r.height()) * 0.47
    aleat = random.Random(int(r.width() * 13 + r.height()))
    _circ(p, c + QPointF(6, 8), raio, QColor(0, 0, 0, 80), None)
    for _ in range(9):
        ang = aleat.uniform(0, math.tau)
        d = aleat.uniform(0.2, 0.55) * raio
        _circ(p, c + QPointF(math.cos(ang) * d, math.sin(ang) * d), raio * aleat.uniform(0.38, 0.5),
              VERDE_ESC, None)
    for _ in range(7):
        ang = aleat.uniform(0, math.tau)
        d = aleat.uniform(0.1, 0.45) * raio
        _circ(p, c + QPointF(math.cos(ang) * d, math.sin(ang) * d), raio * aleat.uniform(0.25, 0.38),
              VERDE, None)
    _circ(p, c, raio * 0.12, MADEIRA_ESC, None)


def d_pedra(p, r, cor=PEDRA):
    c = r.center()
    aleat = random.Random(int(r.width() * 31 + r.height() * 7))
    pts = []
    for k in range(9):
        ang = k / 9 * math.tau
        d = aleat.uniform(0.32, 0.46) * min(r.width(), r.height())
        pts.append(c + QPointF(math.cos(ang) * d, math.sin(ang) * d))
    pol = QPolygonF(pts)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(0, 0, 0, 80))
    p.drawPolygon(pol.translated(3, 4))
    p.setPen(_caneta())
    p.setBrush(cor)
    p.drawPolygon(pol)
    p.setPen(_caneta(QColor(255, 255, 255, 50), 2))
    p.drawLine(pts[5], pts[6])


def d_pedra_grande(p, r):
    d_pedra(p, r, PEDRA_ESC)


def d_arbusto(p, r):
    c, raio = r.center(), min(r.width(), r.height()) * 0.4
    aleat = random.Random(int(r.width() * 5 + 3))
    for _ in range(6):
        ang = aleat.uniform(0, math.tau)
        d = aleat.uniform(0.15, 0.45) * raio
        _circ(p, c + QPointF(math.cos(ang) * d, math.sin(ang) * d), raio * 0.5, VERDE_ESC, None)
    for _ in range(4):
        ang = aleat.uniform(0, math.tau)
        _circ(p, c + QPointF(math.cos(ang) * raio * 0.25, math.sin(ang) * raio * 0.25), raio * 0.35,
              QColor("#4f8a46"), None)


def d_escombros(p, r):
    aleat = random.Random(int(r.width() * 3 + r.height() * 11))
    for _ in range(14):
        c = QPointF(aleat.uniform(r.left() + 6, r.right() - 6), aleat.uniform(r.top() + 6, r.bottom() - 6))
        t = aleat.uniform(4, min(r.width(), r.height()) * 0.16)
        pts = [c + QPointF(math.cos(a) * t * aleat.uniform(0.6, 1.1), math.sin(a) * t * aleat.uniform(0.6, 1.1))
               for a in (0, 1.6, 3.1, 4.5)]
        p.setPen(_caneta(CONTORNO, 1.2))
        p.setBrush(aleat.choice([PEDRA, PEDRA_ESC, QColor("#9a948a")]))
        p.drawPolygon(QPolygonF(pts))


def d_tumulo(p, r):
    a = _m(r, 0.06)
    _sombra(p, a)
    _ret(p, a, QColor("#7f7a72"), 4)
    _ret(p, a.adjusted(5, 5, -5, -5), QColor("#97928a"), 3, PEDRA_ESC, 1.2)
    p.setPen(_caneta(PEDRA_ESC, 2))
    c = a.center()
    p.drawLine(c + QPointF(0, -a.height() * 0.25), c + QPointF(0, a.height() * 0.25))
    p.drawLine(c + QPointF(-a.width() * 0.2, -a.height() * 0.08), c + QPointF(a.width() * 0.2, -a.height() * 0.08))


def d_lapide(p, r):
    a = r.adjusted(r.width() * 0.22, r.height() * 0.3, -r.width() * 0.22, -r.height() * 0.3)
    _sombra(p, a, 8)
    _ret(p, a, QColor("#8a857c"), 8)
    p.setPen(_caneta(PEDRA_ESC, 1.2))
    p.drawLine(QPointF(a.left() + 5, a.center().y()), QPointF(a.right() - 5, a.center().y()))


# ---------------------------------------------------------------------- luzes
def d_tocha_parede(p, r):
    """(v0.48) Tocha presa na parede, vista de cima: suporte de ferro no lado de CIMA do desenho (encosta
    na parede; gire pra virar pra outra parede), o cabo saindo pra frente e a chama na ponta."""
    cx = r.center().x()
    larg = r.width()
    # chapa de ferro presa na parede
    chapa = QRectF(cx - larg * 0.16, r.top() + r.height() * 0.04, larg * 0.32, r.height() * 0.12)
    p.setPen(_caneta(CONTORNO, 1.4))
    p.setBrush(METAL_ESC)
    p.drawRoundedRect(chapa, 2, 2)
    for fx in (0.3, 0.7):   # rebites
        _circ(p, QPointF(chapa.left() + chapa.width() * fx, chapa.center().y()), larg * 0.02, METAL, None)
    # braço de ferro até o anel
    anel_y = r.top() + r.height() * 0.32
    p.setPen(_caneta(METAL_ESC, larg * 0.05))
    p.drawLine(QPointF(cx, chapa.bottom()), QPointF(cx, anel_y))
    # cabo de madeira (inclinado pra frente)
    p.setPen(_caneta(CONTORNO, 1.2))
    p.setBrush(MADEIRA)
    cabo = QRectF(cx - larg * 0.06, anel_y - r.height() * 0.06, larg * 0.12, r.height() * 0.36)
    p.drawRoundedRect(cabo, larg * 0.05, larg * 0.05)
    p.setPen(_caneta(METAL_ESC, larg * 0.035))   # anel
    p.drawLine(QPointF(cx - larg * 0.09, anel_y), QPointF(cx + larg * 0.09, anel_y))
    # pano enrolado + chama
    ponta = QPointF(cx, cabo.bottom() + r.height() * 0.02)
    _circ(p, ponta, larg * 0.08, QColor("#3a2a1c"), CONTORNO, 1.0)
    brilho = QRadialGradient(QPointF(ponta.x(), ponta.y() + r.height() * 0.08), larg * 0.42)
    brilho.setColorAt(0, QColor(255, 190, 90, 150))
    brilho.setColorAt(1, QColor(255, 140, 40, 0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(brilho))
    p.drawEllipse(QPointF(ponta.x(), ponta.y() + r.height() * 0.08), larg * 0.42, larg * 0.42)
    _chamas(p, QPointF(ponta.x(), ponta.y() + r.height() * 0.07), larg * 0.16)


def d_lustre(p, r):
    c, raio = r.center(), min(r.width(), r.height()) * 0.4
    p.setPen(_caneta(OURO, 3))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(c, raio, raio)
    p.drawEllipse(c, raio * 0.4, raio * 0.4)
    for k in range(6):
        ang = math.radians(k * 60)
        pt = c + QPointF(math.cos(ang) * raio, math.sin(ang) * raio)
        p.setPen(_caneta(OURO, 1.5))
        p.drawLine(c + QPointF(math.cos(ang) * raio * 0.4, math.sin(ang) * raio * 0.4), pt)
        _circ(p, pt, 3, QColor("#efe6c8"), CONTORNO, 1)
        _chamas(p, pt, 6)


def d_poste(p, r):
    c, raio = r.center(), min(r.width(), r.height()) * 0.2
    _circ(p, c, raio, METAL_ESC)
    grad = QRadialGradient(c, raio * 1.8)
    grad.setColorAt(0, QColor(255, 250, 220))
    grad.setColorAt(1, QColor(255, 220, 140, 0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(grad))
    p.drawEllipse(c, raio * 1.8, raio * 1.8)
    _circ(p, c, raio * 0.5, QColor(255, 248, 210), CONTORNO, 1)


def d_braseiro(p, r):
    c, raio = r.center(), min(r.width(), r.height()) * 0.36
    _circ(p, c, raio, METAL_ESC)
    _circ(p, c, raio * 0.75, QColor(60, 25, 15), None)
    _chamas(p, c, raio * 0.8)


def d_candelabro(p, r):
    c, raio = r.center(), min(r.width(), r.height()) * 0.3
    p.setPen(_caneta(OURO, 2.5))
    p.drawLine(c + QPointF(-raio, 0), c + QPointF(raio, 0))
    for dx in (-raio, 0, raio):
        pt = c + QPointF(dx, 0)
        _circ(p, pt, 3, QColor("#efe6c8"), CONTORNO, 1)
        _chamas(p, pt, 6)


# ---------------------------------------------------------------------- temáticos
def d_computador(p, r):
    a = r.adjusted(r.width() * 0.08, r.height() * 0.2, -r.width() * 0.08, -r.height() * 0.15)
    _sombra(p, a, 3)
    _ret(p, a, QColor("#3a3f46"), 3)
    tela = QRectF(a.left() + a.width() * 0.1, a.top() + 3, a.width() * 0.8, a.height() * 0.35)
    _ret(p, tela, QColor("#38e1ff"), 2, CONTORNO, 1.2)
    p.setPen(_caneta(QColor("#1a2228"), 1))
    for k in range(3):
        y = a.top() + a.height() * (0.55 + k * 0.13)
        p.drawLine(QPointF(a.left() + 6, y), QPointF(a.right() - 6, y))


def d_terminal(p, r):
    a = _m(r, 0.12)
    _sombra(p, a, 3)
    _ret(p, a, QColor("#2a2f36"), 4)
    tela = a.adjusted(5, 5, -5, -a.height() * 0.4)
    grad = QLinearGradient(tela.topLeft(), tela.bottomRight())
    grad.setColorAt(0, QColor("#1cff9a"))
    grad.setColorAt(1, QColor("#0a6a50"))
    _ret(p, tela, QBrush(grad), 2, CONTORNO, 1)
    for k in range(4):
        _circ(p, QPointF(a.left() + 8 + k * (a.width() - 16) / 3, a.bottom() - 8), 2.5,
              QColor("#ff5050" if k == 0 else "#ffd040"), None)


def d_carro(p, r):
    a = _m(r, 0.04)
    _sombra(p, a, 14)
    _ret(p, a, QColor("#8a2a2a"), min(a.width(), a.height()) * 0.35)
    vertical = a.height() > a.width()
    vidro = QColor("#6a8aa0")
    if vertical:
        pb = QRectF(a.left() + a.width() * 0.15, a.top() + a.height() * 0.22, a.width() * 0.7, a.height() * 0.14)
        tr = QRectF(a.left() + a.width() * 0.15, a.top() + a.height() * 0.66, a.width() * 0.7, a.height() * 0.1)
    else:
        pb = QRectF(a.left() + a.width() * 0.64, a.top() + a.height() * 0.15, a.width() * 0.14, a.height() * 0.7)
        tr = QRectF(a.left() + a.width() * 0.24, a.top() + a.height() * 0.15, a.width() * 0.1, a.height() * 0.7)
    _ret(p, pb, vidro, 4, CONTORNO, 1.2)
    _ret(p, tr, vidro, 4, CONTORNO, 1.2)


def d_capsula(p, r):
    a = _m(r, 0.08)
    raio = min(a.width(), a.height()) / 2
    _sombra(p, a, raio)
    _ret(p, a, QColor("#c8ccd2"), raio)
    vidro = a.adjusted(5, 5, -5, -5)
    grad = QLinearGradient(vidro.topLeft(), vidro.bottomRight())
    grad.setColorAt(0, QColor(160, 230, 255, 220))
    grad.setColorAt(1, QColor(40, 110, 160, 220))
    _ret(p, vidro, QBrush(grad), raio - 5, QColor("#5a6a78"), 1.2)


def d_cristal(p, r):
    c, raio = r.center(), min(r.width(), r.height()) * 0.38
    grad = QRadialGradient(c, raio * 1.6)
    grad.setColorAt(0, QColor(160, 220, 255, 140))
    grad.setColorAt(1, QColor(80, 140, 255, 0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(grad))
    p.drawEllipse(c, raio * 1.6, raio * 1.6)
    pts = [c + QPointF(math.cos(math.radians(a)) * raio * (1 if k % 2 == 0 else 0.5),
                       math.sin(math.radians(a)) * raio * (1 if k % 2 == 0 else 0.5))
           for k, a in enumerate(range(-90, 270, 45))]
    p.setPen(_caneta(QColor("#2a4a8a"), 1.5))
    p.setBrush(QColor("#9fd8ff"))
    p.drawPolygon(QPolygonF(pts))
    p.setPen(_caneta(QColor(255, 255, 255, 160), 1))
    for pt in pts[::2]:
        p.drawLine(c, pt)


def d_circulo_magico(p, r):
    c, raio = r.center(), min(r.width(), r.height()) * 0.46
    cor = QColor(140, 90, 255, 200)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(_caneta(cor, 2.5))
    p.drawEllipse(c, raio, raio)
    p.drawEllipse(c, raio * 0.82, raio * 0.82)
    pts = [c + QPointF(math.cos(math.radians(-90 + k * 144)) * raio * 0.82,
                       math.sin(math.radians(-90 + k * 144)) * raio * 0.82) for k in range(5)]
    p.setPen(_caneta(QColor(180, 140, 255, 220), 1.8))
    p.drawPolygon(QPolygonF(pts))
    fonte = QFont("Segoe UI Symbol")
    fonte.setPixelSize(max(8, int(raio * 0.12)))
    p.setFont(fonte)
    for k in range(12):
        ang = math.radians(k * 30)
        pt = c + QPointF(math.cos(ang) * raio * 0.91, math.sin(ang) * raio * 0.91)
        p.drawText(QRectF(pt.x() - 8, pt.y() - 8, 16, 16), Qt.AlignmentFlag.AlignCenter, "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃ"[k])


def d_servidor(p, r):
    a = r.adjusted(r.width() * 0.15, r.height() * 0.08, -r.width() * 0.15, -r.height() * 0.08)
    _sombra(p, a, 2)
    _ret(p, a, QColor("#22262c"), 2)
    for k in range(5):
        y = a.top() + 4 + k * (a.height() - 8) / 5
        _ret(p, QRectF(a.left() + 3, y, a.width() - 6, (a.height() - 8) / 5 - 2), QColor("#363c44"), 1, None)
        _circ(p, QPointF(a.right() - 7, y + (a.height() - 8) / 10), 1.6,
              QColor("#38ff9a" if k % 2 else "#38e1ff"), None)


def d_caixa_suprimentos(p, r):
    a = _m(r, 0.12)
    _sombra(p, a, 2)
    _ret(p, a, QColor("#4a5a3a"), 2)
    p.setPen(_caneta(QColor("#2a3420"), 2))
    p.drawLine(QPointF(a.left() + 4, a.center().y()), QPointF(a.right() - 4, a.center().y()))
    _ret(p, QRectF(a.center().x() - 6, a.center().y() - 6, 12, 12), QColor("#e8e0c8"), 1, CONTORNO, 1)
    p.setPen(_caneta(QColor("#b03030"), 2.5))
    p.drawLine(a.center() + QPointF(-4, 0), a.center() + QPointF(4, 0))
    p.drawLine(a.center() + QPointF(0, -4), a.center() + QPointF(0, 4))


# ---------------------------------------------------------------------- documentos
PAPEL = QColor("#e8dcbc")


def d_pergaminho(p, r):
    a = r.adjusted(r.width() * 0.18, r.height() * 0.3, -r.width() * 0.18, -r.height() * 0.3)
    _sombra(p, a, 2)
    _ret(p, a, PAPEL, 2, QColor("#7a6040"), 1.5)
    for x in (a.left(), a.right()):
        _ret(p, QRectF(x - 4, a.top() - 3, 8, a.height() + 6), QColor("#c8b488"), 4, QColor("#7a6040"), 1.2)
    p.setPen(_caneta(QColor("#8a7458"), 1))
    for k in range(3):
        y = a.top() + a.height() * (0.3 + k * 0.2)
        p.drawLine(QPointF(a.left() + 6, y), QPointF(a.right() - 6, y))


def d_carta(p, r):
    a = r.adjusted(r.width() * 0.22, r.height() * 0.28, -r.width() * 0.22, -r.height() * 0.28)
    _sombra(p, a, 1)
    _ret(p, a, PAPEL, 1, QColor("#7a6040"), 1.2)
    p.setPen(_caneta(QColor("#7a6040"), 1.2))
    p.drawLine(a.topLeft(), a.center())
    p.drawLine(a.topRight(), a.center())
    _circ(p, a.center() + QPointF(0, a.height() * 0.15), min(a.width(), a.height()) * 0.12,
          QColor("#a02828"), CONTORNO, 1)


def d_livro(p, r):
    a = r.adjusted(r.width() * 0.15, r.height() * 0.25, -r.width() * 0.15, -r.height() * 0.25)
    _sombra(p, a, 2)
    _ret(p, a, QColor("#5a2a1a"), 3)
    meio = a.center().x()
    for lado in (QRectF(a.left() + 3, a.top() + 3, meio - a.left() - 4, a.height() - 6),
                 QRectF(meio + 1, a.top() + 3, a.right() - meio - 4, a.height() - 6)):
        _ret(p, lado, PAPEL, 1, None)
        p.setPen(_caneta(QColor("#8a7458"), 0.8))
        for k in range(4):
            y = lado.top() + lado.height() * (0.2 + k * 0.18)
            p.drawLine(QPointF(lado.left() + 3, y), QPointF(lado.right() - 3, y))


def d_bilhete(p, r):
    a = r.adjusted(r.width() * 0.3, r.height() * 0.32, -r.width() * 0.3, -r.height() * 0.32)
    p.save()
    p.translate(a.center())
    p.rotate(-12)
    b = QRectF(-a.width() / 2, -a.height() / 2, a.width(), a.height())
    _ret(p, b, QColor("#f2ecd8"), 1, QColor("#8a7458"), 1)
    p.setPen(_caneta(QColor("#6a5a48"), 0.8))
    for k in range(3):
        y = b.top() + b.height() * (0.3 + k * 0.2)
        p.drawLine(QPointF(b.left() + 3, y), QPointF(b.right() - 3, y))
    p.restore()


# ---------------------------------------------------------------------- itens soltos
def d_chave(p, r):
    c = r.center()
    t = min(r.width(), r.height())
    p.save()
    p.translate(c)
    p.rotate(-25)
    ouro = QColor("#d4a83a")
    p.setPen(_caneta(QColor("#5a4010"), 1.5))
    p.setBrush(ouro)
    p.drawEllipse(QPointF(-t * 0.18, 0), t * 0.12, t * 0.12)
    p.drawRect(QRectF(-t * 0.07, -t * 0.03, t * 0.3, t * 0.06))
    p.drawRect(QRectF(t * 0.14, 0, t * 0.04, t * 0.08))
    p.drawRect(QRectF(t * 0.19, 0, t * 0.04, t * 0.06))
    p.setBrush(QColor(30, 20, 10))
    p.drawEllipse(QPointF(-t * 0.18, 0), t * 0.05, t * 0.05)
    p.restore()


def d_pocao(p, r):
    c = r.center()
    t = min(r.width(), r.height())
    _circ(p, c + QPointF(0, t * 0.05), t * 0.16, QColor("#c0303a"), CONTORNO, 1.5)
    _ret(p, QRectF(c.x() - t * 0.05, c.y() - t * 0.22, t * 0.1, t * 0.14), QColor("#cfd8dc"), 1, CONTORNO, 1)
    _ret(p, QRectF(c.x() - t * 0.06, c.y() - t * 0.27, t * 0.12, t * 0.06), MADEIRA, 1, CONTORNO, 1)
    _circ(p, c + QPointF(-t * 0.05, 0), t * 0.04, QColor(255, 255, 255, 140), None)


def d_moedas(p, r):
    c = r.center()
    t = min(r.width(), r.height())
    aleat = random.Random(7)
    for _ in range(7):
        q = c + QPointF(aleat.uniform(-t * 0.18, t * 0.18), aleat.uniform(-t * 0.18, t * 0.18))
        _circ(p, q, t * 0.08, QColor("#e0b84a"), QColor("#7a5a10"), 1.2)


def d_saquinho(p, r):
    d_saco(p, _m(r, 0.2))


# ---------------------------------------------------------------------- armas no chão (v0.48, coletáveis)
LAMINA, LAMINA_ESC, COURO = QColor("#c9d0d6"), QColor("#7d868f"), QColor("#5a3a24")


def _arma(p, r, angulo=-35):
    """Abre um desenho de arma deitada na diagonal: devolve o comprimento útil (t)."""
    p.save()
    p.translate(r.center())
    p.rotate(angulo)
    return max(r.width(), r.height()) * 0.92


def _lamina(p, x0, x1, larg, ponta=True):
    """Lâmina de x0 a x1 (eixo x), com fio claro e sulco no meio."""
    pol = QPolygonF([QPointF(x0, -larg / 2), QPointF(x1 - (larg * 1.4 if ponta else 0), -larg / 2),
                     QPointF(x1, 0), QPointF(x1 - (larg * 1.4 if ponta else 0), larg / 2),
                     QPointF(x0, larg / 2)])
    g = QLinearGradient(QPointF(0, -larg / 2), QPointF(0, larg / 2))
    g.setColorAt(0, QColor("#f2f5f7"))
    g.setColorAt(0.5, LAMINA)
    g.setColorAt(1, LAMINA_ESC)
    p.setPen(_caneta(CONTORNO, 1.2))
    p.setBrush(QBrush(g))
    p.drawPolygon(pol)
    p.setPen(_caneta(LAMINA_ESC, 0.8))
    p.drawLine(QPointF(x0 + 2, 0), QPointF(x1 - larg * 2, 0))


def _cabo(p, x0, x1, larg, cor=COURO):
    p.setPen(_caneta(CONTORNO, 1.1))
    p.setBrush(cor)
    p.drawRoundedRect(QRectF(x0, -larg / 2, x1 - x0, larg), larg * 0.4, larg * 0.4)
    p.setPen(_caneta(cor.darker(150), 0.8))
    passo = max(3.0, larg * 0.9)
    x = x0 + passo
    while x < x1 - 1:   # tiras de couro enroladas
        p.drawLine(QPointF(x, -larg / 2 + 0.6), QPointF(x - passo * 0.5, larg / 2 - 0.6))
        x += passo


def d_espada(p, r):
    t = _arma(p, r)
    _cabo(p, -t * 0.48, -t * 0.28, t * 0.07)
    _circ(p, QPointF(-t * 0.5, 0), t * 0.045, OURO, CONTORNO, 1.1)          # pomo
    p.setPen(_caneta(CONTORNO, 1.1))
    p.setBrush(OURO)
    p.drawRoundedRect(QRectF(-t * 0.29, -t * 0.13, t * 0.05, t * 0.26), 2, 2)   # guarda
    _lamina(p, -t * 0.24, t * 0.5, t * 0.085)
    p.restore()


def d_adaga(p, r):
    t = _arma(p, r, -20) * 0.7
    _cabo(p, -t * 0.45, -t * 0.18, t * 0.1)
    p.setPen(_caneta(CONTORNO, 1.1))
    p.setBrush(METAL_ESC)
    p.drawRoundedRect(QRectF(-t * 0.19, -t * 0.12, t * 0.05, t * 0.24), 2, 2)
    _lamina(p, -t * 0.14, t * 0.45, t * 0.11)
    p.restore()


def d_lanca(p, r):
    t = _arma(p, r, -40) * 1.05
    p.setPen(_caneta(CONTORNO, 1.1))
    p.setBrush(MADEIRA)
    p.drawRoundedRect(QRectF(-t * 0.5, -t * 0.022, t * 0.8, t * 0.044), 2, 2)   # haste
    _cabo(p, -t * 0.12, t * 0.02, t * 0.055)
    pol = QPolygonF([QPointF(t * 0.28, -t * 0.05), QPointF(t * 0.5, 0), QPointF(t * 0.28, t * 0.05),
                     QPointF(t * 0.31, 0)])
    p.setPen(_caneta(CONTORNO, 1.2))
    p.setBrush(LAMINA)
    p.drawPolygon(pol)
    p.restore()


def d_machado(p, r):
    t = _arma(p, r, -30)
    p.setPen(_caneta(CONTORNO, 1.1))
    p.setBrush(MADEIRA)
    p.drawRoundedRect(QRectF(-t * 0.45, -t * 0.03, t * 0.8, t * 0.06), 2, 2)
    _cabo(p, -t * 0.45, -t * 0.22, t * 0.07)
    lam = QPainterPath(QPointF(t * 0.22, -t * 0.04))
    lam.cubicTo(QPointF(t * 0.26, -t * 0.22), QPointF(t * 0.4, -t * 0.3), QPointF(t * 0.46, -t * 0.28))
    lam.cubicTo(QPointF(t * 0.42, -t * 0.1), QPointF(t * 0.42, t * 0.1), QPointF(t * 0.46, t * 0.28))
    lam.cubicTo(QPointF(t * 0.4, t * 0.3), QPointF(t * 0.26, t * 0.22), QPointF(t * 0.22, t * 0.04))
    lam.closeSubpath()
    g = QLinearGradient(QPointF(t * 0.22, 0), QPointF(t * 0.46, 0))
    g.setColorAt(0, LAMINA_ESC)
    g.setColorAt(1, QColor("#eef2f4"))
    p.setPen(_caneta(CONTORNO, 1.2))
    p.setBrush(QBrush(g))
    p.drawPath(lam)
    p.restore()


def d_martelo(p, r):
    t = _arma(p, r, -30)
    p.setPen(_caneta(CONTORNO, 1.1))
    p.setBrush(MADEIRA)
    p.drawRoundedRect(QRectF(-t * 0.45, -t * 0.03, t * 0.78, t * 0.06), 2, 2)
    _cabo(p, -t * 0.45, -t * 0.22, t * 0.07)
    g = QLinearGradient(QPointF(0, -t * 0.16), QPointF(0, t * 0.16))
    g.setColorAt(0, QColor("#b8bfc6"))
    g.setColorAt(1, METAL_ESC)
    p.setPen(_caneta(CONTORNO, 1.3))
    p.setBrush(QBrush(g))
    p.drawRoundedRect(QRectF(t * 0.24, -t * 0.17, t * 0.2, t * 0.34), 3, 3)
    p.restore()


def d_arco(p, r):
    t = _arma(p, r, -40)
    arco = QPainterPath(QPointF(-t * 0.1, -t * 0.46))
    arco.cubicTo(QPointF(t * 0.32, -t * 0.25), QPointF(t * 0.32, t * 0.25), QPointF(-t * 0.1, t * 0.46))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(_caneta(CONTORNO, t * 0.07))
    p.drawPath(arco)
    p.setPen(_caneta(MADEIRA_CLA, t * 0.045))
    p.drawPath(arco)
    p.setPen(_caneta(QColor("#e8e0c8"), 1.0))   # corda
    p.drawLine(QPointF(-t * 0.1, -t * 0.46), QPointF(-t * 0.1, t * 0.46))
    _cabo(p, t * 0.12, t * 0.26, t * 0.06)
    p.restore()


def d_escudo_item(p, r):
    c = r.center()
    raio = min(r.width(), r.height()) * 0.36
    g = QRadialGradient(c - QPointF(raio * 0.3, raio * 0.3), raio * 1.3)
    g.setColorAt(0, MADEIRA_CLA)
    g.setColorAt(1, MADEIRA_ESC)
    p.setPen(_caneta(CONTORNO, 1.4))
    p.setBrush(QBrush(g))
    p.drawEllipse(c, raio, raio)
    p.setPen(_caneta(METAL_ESC, raio * 0.12))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(c, raio * 0.92, raio * 0.92)
    _circ(p, c, raio * 0.25, QColor("#b8bfc6"), CONTORNO, 1.2)   # umbo


# ====================================================================== catálogo
# chave: (nome, categoria, largura, altura, desenho, extras)
#   extras: "interativo", "bloqueia", "luz": tipo de luz (em luzes.TIPOS_LUZ)
CATEGORIAS = ["Móveis", "Recipientes", "Itens soltos", "Documentos", "Cenário", "Luzes", "Tecnologia", "Magia"]
CATALOGO = {
    # móveis
    "mesa": ("Mesa", "Móveis", 2, 1, d_mesa, {"movel": True}),
    "mesa_grande": ("Mesa grande", "Móveis", 3, 2, d_mesa, {}),
    "mesa_redonda": ("Mesa redonda", "Móveis", 2, 2, d_mesa_redonda, {"movel": True}),
    "cadeira": ("Cadeira", "Móveis", 1, 1, d_cadeira, {"movel": True}),
    "banco": ("Banco", "Móveis", 2, 1, d_banco, {"movel": True}),
    "cama_solteiro": ("Cama de solteiro", "Móveis", 1, 2, d_cama, {"movel": True}),
    "cama_casal": ("Cama de casal", "Móveis", 2, 2, d_cama_casal, {"movel": True}),
    "penteadeira": ("Penteadeira", "Móveis", 2, 1, d_penteadeira, {"interativo": True}),
    "guarda_roupa": ("Guarda-roupa", "Móveis", 2, 1, d_guarda_roupa, {"interativo": True}),
    "estante": ("Estante de livros", "Móveis", 2, 1, d_estante, {"bloqueia": True, "interativo": True}),
    "armario": ("Armário", "Móveis", 1, 1, d_armario, {"interativo": True}),
    "sofa": ("Sofá", "Móveis", 2, 1, d_sofa, {"movel": True}),
    "tapete": ("Tapete", "Móveis", 3, 2, d_tapete, {}),
    "balcao": ("Balcão de taverna", "Móveis", 3, 1, d_balcao, {}),
    # recipientes
    "bau": ("Baú", "Recipientes", 1, 1, d_bau, {"interativo": True, "movel": True}),
    "bau_grande": ("Baú grande", "Recipientes", 2, 1, d_bau, {"interativo": True}),
    "caixote": ("Caixote", "Recipientes", 1, 1, d_caixote, {"interativo": True, "movel": True}),
    "barril": ("Barril", "Recipientes", 1, 1, d_barril, {"interativo": True, "movel": True}),
    "cacifo": ("Cacifo", "Recipientes", 1, 1, d_cacifo, {"interativo": True}),
    "saco": ("Saco", "Recipientes", 1, 1, d_saco, {"interativo": True, "movel": True}),
    "urna": ("Urna", "Recipientes", 1, 1, d_urna, {"interativo": True, "movel": True}),
    "cofre": ("Cofre", "Recipientes", 1, 1, d_cofre, {"interativo": True}),
    "caixao": ("Caixão", "Recipientes", 1, 2, d_caixao, {"interativo": True}),
    # itens soltos no chão (o jogador pega)
    "chave": ("Chave", "Itens soltos", 1, 1, d_chave, {"interativo": True, "solto": True}),
    "pocao": ("Poção", "Itens soltos", 1, 1, d_pocao, {"interativo": True, "solto": True}),
    "moedas": ("Moedas", "Itens soltos", 1, 1, d_moedas, {"interativo": True, "solto": True}),
    "saquinho": ("Saquinho", "Itens soltos", 1, 1, d_saquinho, {"interativo": True, "solto": True}),
    # armas no chão (v0.48): coletáveis, vão direto pro inventário
    "espada": ("Espada", "Itens soltos", 1, 1, d_espada, {"interativo": True, "solto": True}),
    "adaga": ("Adaga", "Itens soltos", 1, 1, d_adaga, {"interativo": True, "solto": True}),
    "lanca": ("Lança", "Itens soltos", 2, 1, d_lanca, {"interativo": True, "solto": True}),
    "machado": ("Machado", "Itens soltos", 1, 1, d_machado, {"interativo": True, "solto": True}),
    "martelo": ("Martelo de guerra", "Itens soltos", 1, 1, d_martelo, {"interativo": True, "solto": True}),
    "arco": ("Arco", "Itens soltos", 1, 1, d_arco, {"interativo": True, "solto": True}),
    "escudo_item": ("Escudo", "Itens soltos", 1, 1, d_escudo_item, {"interativo": True, "solto": True}),
    # documentos (o jogador lê; pode pegar)
    "pergaminho": ("Pergaminho", "Documentos", 1, 1, d_pergaminho, {"interativo": True, "documento": True}),
    "carta": ("Carta", "Documentos", 1, 1, d_carta, {"interativo": True, "documento": True}),
    "livro": ("Livro aberto", "Documentos", 1, 1, d_livro, {"interativo": True, "documento": True}),
    "bilhete": ("Bilhete", "Documentos", 1, 1, d_bilhete, {"interativo": True, "documento": True}),
    # cenário
    "fogueira": ("Fogueira", "Cenário", 1, 1, d_fogueira, {"luz": "fogueira"}),
    "poco": ("Poço", "Cenário", 2, 2, d_poco, {"interativo": True}),
    "estatua": ("Estátua", "Cenário", 1, 1, d_estatua, {"bloqueia": True}),
    "altar": ("Altar", "Cenário", 2, 1, d_altar, {"interativo": True}),
    "pilar": ("Pilar", "Cenário", 1, 1, d_pilar, {"bloqueia": True}),
    "arvore": ("Árvore", "Cenário", 3, 3, d_arvore, {}),
    "pedra": ("Pedra", "Cenário", 1, 1, d_pedra, {}),
    "pedra_grande": ("Rochedo", "Cenário", 2, 2, d_pedra_grande, {"bloqueia": True}),
    "arbusto": ("Arbusto", "Cenário", 1, 1, d_arbusto, {}),
    "escombros": ("Escombros", "Cenário", 2, 2, d_escombros, {}),
    "tumulo": ("Túmulo", "Cenário", 1, 2, d_tumulo, {"interativo": True}),
    "lapide": ("Lápide", "Cenário", 1, 1, d_lapide, {}),
    # luzes
    "tocha_parede": ("Tocha de parede", "Luzes", 1, 1, d_tocha_parede, {"luz": "tocha"}),
    "lareira": ("Lareira", "Luzes", 2, 1, d_lareira, {"luz": "lareira", "bloqueia": False}),
    "lustre": ("Lustre", "Luzes", 2, 2, d_lustre, {"luz": "lustre"}),
    "poste": ("Poste de luz", "Luzes", 1, 1, d_poste, {"luz": "poste"}),
    "braseiro": ("Braseiro", "Luzes", 1, 1, d_braseiro, {"luz": "braseiro"}),
    "candelabro": ("Candelabro", "Luzes", 1, 1, d_candelabro, {"luz": "candelabro"}),
    "fogueira_luz": ("Fogueira de acampamento", "Luzes", 2, 2, d_fogueira, {"luz": "fogueira"}),
    # tecnologia e magia (antes "Temáticos")
    "computador": ("Computador", "Tecnologia", 1, 1, d_computador, {"interativo": True}),
    "terminal": ("Terminal", "Tecnologia", 1, 1, d_terminal, {"interativo": True, "luz": "terminal"}),
    "servidor": ("Rack de servidor", "Tecnologia", 1, 1, d_servidor, {"bloqueia": True}),
    "carro": ("Carro", "Cenário", 2, 4, d_carro, {"interativo": True}),
    "capsula": ("Cápsula", "Tecnologia", 1, 2, d_capsula, {"interativo": True}),
    "cristal": ("Cristal arcano", "Magia", 1, 1, d_cristal, {"luz": "cristal"}),
    "circulo_magico": ("Círculo mágico", "Magia", 3, 3, d_circulo_magico, {}),
    "caixa_suprimentos": ("Caixa de suprimentos", "Recipientes", 1, 1, d_caixa_suprimentos,
                          {"interativo": True, "movel": True}),
}

# ~10 objetos por ambientação (Medieval, Moderno, Futurista, Mágico, Terror) — v0.30
from .props_temas import CATALOGO_TEMAS, temas_do_prop  # noqa: E402  (precisa dos desenhos acima)

CATALOGO.update(CATALOGO_TEMAS)

# 🏢 escada entre andares (v0.46): ligada a outra escada (botão direito → "Ligar ao andar…")
from .andares import desenhar_escada  # noqa: E402
# (v0.46.2) NÃO é interativa como baú (sem conteúdo/chave): o duplo clique do jogador só sobe/desce.
# A permissão do mestre fica em `trancado` (= bloqueada: o jogador não usa).
CATALOGO["escada"] = ("Escada", "Cenário", 1, 2, desenhar_escada, {})


def desenhar_miniatura(tipo: str, tamanho: int = 64) -> QPixmap:
    """Ícone do prop pra biblioteca."""
    nome, _cat, w, h, desenho, _ = CATALOGO[tipo]
    pm = QPixmap(tamanho, tamanho)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    escala = (tamanho - 6) / max(w, h) / CELULA
    p.translate((tamanho - w * CELULA * escala) / 2, (tamanho - h * CELULA * escala) / 2)
    p.scale(escala, escala)
    desenho(p, QRectF(0, 0, w * CELULA, h * CELULA))
    p.end()
    return pm


# ====================================================================== altura na Mesa 3D (v0.37)
# Metros. O contorno do desenho vira um bloco dessa altura e o desenho de sempre fica no topo.
# 0 = rente ao chão (tapete, papel, poça…): fica no 2D.
# (v0.48) presos no alto (na parede): na Mesa 3D o desenho fica lá em cima, SEM o bloco embaixo
SUSPENSOS = {"tocha_parede"}

ALTURA_CATEGORIA = {"Móveis": 0.8, "Recipientes": 0.7, "Itens soltos": 0.0, "Documentos": 0.0,
                    "Cenário": 0.6, "Luzes": 0.8, "Tecnologia": 1.0, "Magia": 0.9}
ALTURA_3D = {
    "mesa": 0.8, "mesa_grande": 0.8, "mesa_redonda": 0.8, "cadeira": 0.5, "banco": 0.45,
    "cama_solteiro": 0.5, "cama_casal": 0.55, "penteadeira": 0.85, "guarda_roupa": 2.0, "estante": 1.9,
    "armario": 1.8, "sofa": 0.75, "tapete": 0.0, "balcao": 1.05, "trono": 1.4, "mesa_banquete": 0.8,
    "suporte_armas": 1.5, "geladeira": 1.8, "fogao": 0.9, "pia": 0.9, "vaso_sanitario": 0.45,
    "banheira": 0.6, "tv": 0.6, "escrivaninha": 0.8, "maquina_venda": 1.8, "mesa_tortura": 0.85,
    "bau": 0.6, "bau_grande": 0.7, "caixote": 0.8, "barril": 1.0, "cacifo": 1.8, "saco": 0.5,
    "urna": 0.8, "cofre": 0.9, "caixao": 0.6, "caixa_suprimentos": 0.7, "cacamba": 1.3,
    "conteiner": 2.4, "jaula": 1.8,
    "fogueira": 0.25, "poco": 0.9, "estatua": 2.2, "altar": 1.0, "pilar": 3.0, "arvore": 2.6,
    "pedra": 0.5, "pedra_grande": 1.6, "arbusto": 0.9, "escombros": 0.5, "tumulo": 0.5,
    "lapide": 1.0, "carro": 1.4, "bigorna": 0.7, "carroca": 1.3, "tenda": 2.2, "estandarte": 2.4,
    "feno": 0.9, "moto": 1.0, "nave": 2.2, "cogumelos": 0.6, "forca": 2.8, "cadaver": 0.25,
    "teia_gigante": 0.0, "espelho_quebrado": 0.2, "ossos": 0.3, "poca_sangue": 0.0,
    "tocha_parede": 1.7, "lareira": 1.5, "lustre": 0.0, "poste": 2.6, "braseiro": 0.9, "candelabro": 1.4,
    "fogueira_luz": 0.3, "forja": 1.1, "tocheiro": 1.7, "velas_ritual": 0.15,
    "computador": 0.9, "terminal": 1.3, "servidor": 2.0, "capsula": 1.0, "holomesa": 0.9,
    "robo": 1.6, "drone": 0.0, "console": 1.0, "reator": 2.2, "tubo_estase": 2.2,
    "teleporte": 0.15, "torreta": 1.3,
    "cristal": 1.3, "circulo_magico": 0.0, "caldeirao": 0.7, "mesa_alquimia": 0.85,
    "pedestal_orbe": 1.2, "estante_grimorios": 1.9, "portal": 2.6, "pedra_runica": 1.5,
    "esfera_armilar": 1.2, "telescopio": 1.4, "fonte_magica": 1.0,
    # (v0.59) steampunk e pós-apocalíptico
    "caldeira": 1.8, "bancada_engrenagens": 0.9, "automato": 1.7, "cano_valvula": 0.4, "relogio_pendulo": 2.0,
    "lampiao_gas": 1.6, "bau_rebites": 0.6, "globo_mundi": 1.1, "telescopio_latao": 1.4, "balao_carga": 2.4,
    "carro_ferrugem": 1.4, "barricada": 1.2, "tambor_fogo": 0.9, "saco_areia": 0.8, "placa_perigo": 1.6,
    "prateleira_saqueada": 1.8, "galao": 0.0, "pneu": 0.25, "cerca_arame": 2.0, "zumbi_caido": 0.25,
}


_LATERAIS = {}


ORGANICOS = {"arvore", "arbusto", "feno", "cogumelos", "tenda", "teia_gigante", "estandarte"}

# (v0.67.1) MÓVEIS COM PERNAS na Mesa 3D: em vez de um bloco maciço até o chão, o TAMPO (a fração de cima da altura)
# e as pernas embaixo. tipo: (fração do tampo, lado da perna em fração do menor lado, "quatro" | "centro")
PERNAS = {
    "mesa": (0.12, 0.08, "quatro"), "mesa_grande": (0.1, 0.06, "quatro"), "mesa_banquete": (0.1, 0.05, "quatro"),
    "escrivaninha": (0.14, 0.07, "quatro"), "banco": (0.3, 0.12, "quatro"), "cadeira": (0.45, 0.12, "quatro"),
    "mesa_alquimia": (0.14, 0.07, "quatro"), "mesa_tortura": (0.16, 0.06, "quatro"),
    "bancada_engrenagens": (0.16, 0.07, "quatro"), "mesa_redonda": (0.12, 0.14, "centro"),
    "holomesa": (0.2, 0.22, "centro"), "pedestal_orbe": (0.25, 0.3, "centro"),
}

# (v0.67.1) FAIXAS nas laterais: o material aparecendo de lado (aro de ferro no barril, ferragem do baú, fiadas de
# pedra, prateleiras…). tipo → [(de, até) em fração da altura, cor por cima (RGBA)]
_FERRO, _FRESTA, _FIADA = (40, 38, 36, 215), (10, 6, 4, 150), (12, 10, 8, 120)
_LUZ_AZUL, _PRATELEIRA = (90, 220, 255, 150), (255, 236, 200, 60)
FAIXAS = {
    "barril": [(0.08, 0.17, _FERRO), (0.46, 0.54, _FERRO), (0.83, 0.92, _FERRO)],
    "bau": [(0.0, 0.1, _FERRO), (0.6, 0.66, _FRESTA), (0.88, 0.97, _FERRO)],
    "bau_grande": [(0.0, 0.1, _FERRO), (0.6, 0.66, _FRESTA), (0.88, 0.97, _FERRO)],
    "bau_rebites": [(0.0, 0.12, _FERRO), (0.6, 0.66, _FRESTA), (0.86, 0.98, _FERRO)],
    "caixote": [(0.31, 0.35, _FRESTA), (0.64, 0.68, _FRESTA)],
    "caixa_suprimentos": [(0.45, 0.5, _FRESTA)],
    "cofre": [(0.48, 0.52, _FRESTA)],
    "urna": [(0.75, 0.82, _FRESTA)],
    "pilar": [(k / 6, k / 6 + 0.025, _FIADA) for k in range(1, 6)],
    "estatua": [(0.0, 0.12, _FIADA)],
    "lapide": [(0.0, 0.08, _FIADA)],
    "tumulo": [(0.45, 0.5, _FIADA)],
    "altar": [(0.33, 0.36, _FIADA), (0.66, 0.69, _FIADA), (0.9, 1.0, (255, 240, 220, 40))],
    "pedra_runica": [(0.3, 0.33, (120, 200, 255, 110)), (0.62, 0.65, (120, 200, 255, 110))],
    "lareira": [(k / 5, k / 5 + 0.03, _FIADA) for k in range(1, 5)],
    "forja": [(k / 4, k / 4 + 0.04, _FIADA) for k in range(1, 4)],
    "poco": [(0.45, 0.52, _FIADA), (0.9, 1.0, (40, 30, 20, 120))],
    "estante": [(k / 5, k / 5 + 0.03, _PRATELEIRA) for k in range(1, 5)],
    "estante_grimorios": [(k / 5, k / 5 + 0.03, _PRATELEIRA) for k in range(1, 5)],
    "prateleira_saqueada": [(k / 4, k / 4 + 0.04, _PRATELEIRA) for k in range(1, 4)],
    "guarda_roupa": [(0.0, 0.06, _FRESTA), (0.94, 1.0, _FRESTA)],
    "armario": [(0.48, 0.52, _FRESTA)],
    "servidor": [(k / 6, k / 6 + 0.02, _LUZ_AZUL) for k in range(1, 6)],
    "terminal": [(0.55, 0.62, _LUZ_AZUL)],
    "console": [(0.7, 0.76, _LUZ_AZUL)],
    "reator": [(0.3, 0.36, _LUZ_AZUL), (0.62, 0.68, _LUZ_AZUL)],
    "tubo_estase": [(0.0, 0.1, _FERRO), (0.9, 1.0, _FERRO), (0.35, 0.65, (120, 255, 200, 50))],
    "capsula": [(0.0, 0.15, _FERRO)],
    "robo": [(0.45, 0.5, _FERRO)],
    "torreta": [(0.0, 0.3, _FERRO)],
    "caldeirao": [(0.8, 0.92, _FERRO)],
    "caldeira": [(0.15, 0.22, _FERRO), (0.72, 0.8, _FERRO)],
    "tambor_fogo": [(0.1, 0.16, _FERRO), (0.84, 0.9, _FERRO)],
    "relogio_pendulo": [(0.6, 0.64, _FRESTA)],
    "cacifo": [(0.48, 0.52, _FRESTA)],
}


def _laterais(corpo: QPixmap, suave: bool = False) -> list[QPixmap]:
    """O desenho escurecido em 4 tons (do pé, mais escuro, até perto do topo) — as laterais do bloco.
    suave = folhagem/pano: escurece bem menos (senão vira um bloco preto)."""
    chave = (corpo.cacheKey(), suave)
    tons = _LATERAIS.get(chave)
    if tons is None:
        tons = []
        for escuro in ((110, 85, 60, 40) if suave else (165, 140, 115, 90)):
            pm = QPixmap(corpo)
            p = QPainter(pm)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
            p.fillRect(pm.rect(), QColor(14, 10, 8, escuro))
            p.end()
            tons.append(pm)
        if len(_LATERAIS) > 300:
            _LATERAIS.clear()
        _LATERAIS[chave] = tons
    return tons


_TINGIDOS: dict = {}
_MEDIAS: dict = {}


def _tingido(pm: QPixmap, rgba) -> QPixmap:
    """A camada com uma cor por cima só onde tem desenho (faixa de ferro, fresta, luz…). Guardada."""
    chave = (pm.cacheKey(), tuple(rgba))
    t = _TINGIDOS.get(chave)
    if t is None:
        t = QPixmap(pm)
        p = QPainter(t)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
        p.fillRect(t.rect(), QColor(*rgba))
        p.end()
        if len(_TINGIDOS) > 600:
            _TINGIDOS.clear()
        _TINGIDOS[chave] = t
    return t


def _cor_media(pm: QPixmap) -> QColor:
    """A cor média do desenho (só onde tem desenho) — pra pintar as pernas do móvel."""
    c = _MEDIAS.get(pm.cacheKey())
    if c is None:
        img = pm.toImage().scaled(8, 8, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
        soma, peso = [0.0, 0.0, 0.0], 0.0
        for x in range(8):
            for y in range(8):
                q = img.pixelColor(x, y)
                a = q.alphaF()
                if a > 0.1:
                    soma = [soma[0] + q.redF() * a, soma[1] + q.greenF() * a, soma[2] + q.blueF() * a]
                    peso += a
        c = QColor.fromRgbF(*(s / peso for s in soma)) if peso else QColor("#6b4a2c")
        _MEDIAS[pm.cacheKey()] = c
    return QColor(c)


def _pes(r: QRectF, lado: float, arranjo: str) -> list:
    """Os pés do móvel (polígonos no sistema do objeto): quatro nos cantos ou um no centro (octógono)."""
    menor = min(r.width(), r.height())
    if arranjo == "centro":
        raio = max(3.0, menor * lado / 2)
        c = r.center()
        return [QPolygonF([QPointF(c.x() + math.cos(k * math.pi / 4) * raio, c.y() + math.sin(k * math.pi / 4) * raio)
                           for k in range(8)])]
    s = max(3.0, menor * lado)
    m = menor * 0.07
    saida = []
    for x in (r.left() + m, r.right() - m - s):
        for y in (r.top() + m, r.bottom() - m - s):
            saida.append(QPolygonF([QPointF(x, y), QPointF(x + s, y), QPointF(x + s, y + s), QPointF(x, y + s)]))
    return saida


def altura_3d(tipo: str, tem_imagem: bool = False) -> float:
    """Altura (em unidades da cena) do objeto na Mesa 3D."""
    if tipo in ALTURA_3D:
        return ALTURA_3D[tipo] * CELULA
    entrada = CATALOGO.get(tipo)
    if entrada:
        return ALTURA_CATEGORIA.get(entrada[1], 0.6) * CELULA
    return 0.6 * CELULA if tem_imagem else 0.0


# ====================================================================== item na mesa
class PropItem(QGraphicsObject):
    def __init__(self, tipo: str = "bau", imagem: bytes | None = None):
        super().__init__()
        self.uid = uuid.uuid4().hex
        entrada = CATALOGO.get(tipo)
        extras = entrada[5] if entrada else {}
        self.tipo = tipo if entrada or imagem else "bau"
        self.nome = entrada[0] if entrada else "Objeto"
        self.w = float(entrada[2] if entrada else 1)     # em quadrados
        self.h = float(entrada[3] if entrada else 1)
        self.angulo = 0.0
        self.interativo = bool(extras.get("interativo", False))
        self.bloqueia = bool(extras.get("bloqueia", False))
        self.luz = extras.get("luz")                    # tipo de luz, se ilumina
        self.luz_acesa = True
        self.movel = bool(extras.get("movel", False))   # jogadores podem empurrar/levar
        self.documento = bool(extras.get("documento", False))   # papel solto: abre direto pra ler
        self.solto = bool(extras.get("solto", False) or self.documento)   # some do chão quando pegam
        self.efeito = ""                # em chamas, congelado... (mesa/efeitos.py)
        self._cache_efeito = {}
        self.sorteio = None             # recompensa aleatória (jogo/sorteio.py) — None = conteúdo fixo
        self.chave = ""                 # nome do item que destranca (baú trancado)
        self.gasta_chave = False
        self.gatilho = None             # armadilha/gatilho (ver jogo/gatilhos.py)
        self.trancado = False
        self.perto = True               # precisa estar perto (1,5 m) pra abrir
        self.pode_pegar = True          # jogadores podem pegar os itens
        self.itens: list[dict] = []     # {"id","nome","qtd","desc","img"(b64 ou None)}
        self.ligacao = None             # escada: {"andar": n, "id": uid da escada de lá} (mesa/andares.py)
        self.travado = False
        self.imagem = None
        self.hash_imagem = None
        self._pixmap = None
        self.definir_imagem(imagem)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable
                      | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
                      | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._atualizar_origem()

    # ------------------------------------------------------------ dados
    def definir_imagem(self, imagem: bytes | None):
        self.imagem = imagem
        self.hash_imagem = hashlib.sha1(imagem).hexdigest() if imagem else None
        self._pixmap = None
        if imagem:
            pm = QPixmap()
            if pm.loadFromData(imagem):
                self._pixmap = pm
        self.update()

    @property
    def largura(self):
        return self.w * CELULA

    @property
    def altura(self):
        return self.h * CELULA

    def _atualizar_origem(self):
        self.setTransformOriginPoint(self.largura / 2, self.altura / 2)
        self.setRotation(self.angulo)

    def definir_tamanho(self, w, h):
        self.prepareGeometryChange()
        self.w, self.h = max(0.5, float(w)), max(0.5, float(h))
        self._atualizar_origem()
        self._mudou()

    def girar(self, graus):
        self.angulo = (self.angulo + graus) % 360
        self._atualizar_origem()
        self._mudou()

    def _mudou(self):
        self.update()
        cena = self.scene()
        if cena is not None:
            if hasattr(cena, "marcar_modificada"):
                cena.marcar_modificada()
            if (self.bloqueia or self.luz) and hasattr(cena, "visao_mudou"):
                cena.visao_mudou()
            if self.luz and hasattr(cena, "recalcular_luzes"):
                cena.recalcular_luzes()

    def centro_cena(self) -> QPointF:
        return self.mapToScene(QPointF(self.largura / 2, self.altura / 2))

    def cantos_cena(self) -> list[QPointF]:
        r = QRectF(0, 0, self.largura, self.altura)
        return [self.mapToScene(p) for p in (r.topLeft(), r.topRight(), r.bottomRight(), r.bottomLeft())]

    # ------------------------------------------------------------ forma
    @property
    def altura_3d(self) -> float:
        return altura_3d(self.tipo, self._pixmap is not None)

    def boundingRect(self):
        m = max(6.0, self.altura * 0.45) if self.efeito else 22.0   # (sobra pra sombra projetada)
        from . import camera3d
        if camera3d.ligada() and self.altura_3d > 0:
            m += camera3d.margem(self.altura_3d)   # o topo se desloca na perspectiva
        return QRectF(-m, -m, self.largura + 2 * m, self.altura + 2 * m)

    def animado(self) -> bool:
        return bool(self.efeito)

    def definir_efeito(self, efeito: str):
        efeito = efeito or ""
        if efeito != self.efeito:
            self.prepareGeometryChange()
            self.efeito = efeito
            self._cache_efeito = {}
            self.update()
            self._mudou()
            cena = self.scene()
            if cena is not None and hasattr(cena, "mesa_mudou"):
                cena.mesa_mudou.emit()

    def shape(self):
        caminho = QPainterPath()
        caminho.addRect(QRectF(0, 0, self.largura, self.altura))
        return caminho

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(0, 0, self.largura, self.altura)
        from ..graficos import nivel as _nivel
        n = _nivel()
        from . import camera3d
        if n >= 1 and camera3d.ligada() and self.altura_3d > 0 and self.tipo not in SUSPENSOS:
            # (v0.84) o CORPO vai pra camada das coisas altas (altura3d), na fila do mais LONGE pro mais PERTO junto
            # com as fichas, recortado pelas paredes da frente — antes ficava sempre por baixo de fichas e paredes
            # (com a câmera inclinada, a ficha de trás passava por cima do objeto). Aqui no chão fica só a sombra.
            try:
                if self._corpo_e_sombra(r, n) is not None:
                    self._desenhar_3d(painter, r, n, corpo=False)
                    from .altura3d import OBJETOS
                    OBJETOS.add(self)
                    if self.efeito:
                        from .efeitos import animacao
                        animacao().registrar(self)
                    return
            except Exception as erro:   # (erro dentro de paint() fecha o programa)
                from ..seguranca import registrar_erro
                registrar_erro(f"Sombra do objeto 3D ({self.tipo}) falhou: {erro!r}")
        from .altura3d import OBJETOS
        OBJETOS.discard(self)   # (desenhado inteiro aqui: a camada alta não desenha de novo)
        self._pintar_tudo(painter, r, n)

    def pintar_corpo_3d(self, painter, n: int):
        """(v0.84) Chamado pela camada altura3d, com o painter nas coordenadas do objeto: corpo, efeito e marcas."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._pintar_tudo(painter, QRectF(0, 0, self.largura, self.altura), n, sombra=False)

    def _pintar_tudo(self, painter, r, n, sombra=True):
        from . import camera3d
        if n >= 1 and camera3d.ligada() and self.altura_3d > 0 and self._desenhar_3d(painter, r, n, sombra=sombra):
            pass   # (o painter ficou no plano do topo: marcas e efeito vão lá em cima)
        elif n >= 1 and self._desenhar_com_volume(painter, r, n):
            pass
        elif self._pixmap is not None:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawPixmap(r, self._pixmap, QRectF(self._pixmap.rect()))
        else:
            entrada = CATALOGO.get(self.tipo)
            if entrada:
                entrada[4](painter, r)
        if self.efeito:
            from .efeitos import agora, animacao, desenhar_sobre
            animacao().registrar(self)
            desenhar_sobre(painter, r, self.efeito, agora(), hash(self.uid) % 99991,
                           self._cache_efeito, redondo=False)
        if self.isSelected():
            caneta = QPen(QColor(COR_DESTAQUE), 2, Qt.PenStyle.DashLine)
            caneta.setCosmetic(True)
            painter.setPen(caneta)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(r.adjusted(-3, -3, 3, 3))
        if self.interativo:
            # brilhozinho no canto: "dá pra mexer aqui"
            c = QPointF(r.right() - 4, r.top() + 4)
            painter.setPen(QPen(QColor(20, 16, 12), 1))
            painter.setBrush(QColor(255, 215, 100))
            estrela = [c + QPointF(math.cos(math.radians(a)) * (5 if k % 2 == 0 else 2),
                                   math.sin(math.radians(a)) * (5 if k % 2 == 0 else 2))
                       for k, a in enumerate(range(-90, 270, 45))]
            painter.drawPolygon(QPolygonF(estrela))
            if self.gatilho and getattr(self, "mostrar_tranca", True):
                from ..jogo.gatilhos import pode_disparar
                fonte = QFont()
                fonte.setPixelSize(12)
                painter.setFont(fonte)
                painter.setPen(QColor(255, 90, 70) if pode_disparar(self.gatilho) else QColor(150, 140, 130))
                painter.drawText(QRectF(r.left() - 6, r.top() - 8, 16, 16), Qt.AlignmentFlag.AlignCenter, "⚡")
            if self.sorteio and self.sorteio.get("ativo") and getattr(self, "mostrar_tranca", True):
                fonte = QFont()
                fonte.setPixelSize(11)
                painter.setFont(fonte)
                painter.drawText(QRectF(r.left() - 6, r.bottom() - 8, 16, 16), Qt.AlignmentFlag.AlignCenter,
                                 "✓" if self.sorteio.get("sorteado") else "🎲")
            if self.trancado and getattr(self, "mostrar_tranca", True):
                fonte = QFont()
                fonte.setPixelSize(11)
                painter.setFont(fonte)
                painter.drawText(QRectF(r.right() - 22, r.top() - 4, 14, 14),
                                 Qt.AlignmentFlag.AlignCenter, "🔒")

    def _desenhar_3d(self, painter, r, n, sombra=True, corpo=True) -> bool:
        """MESA 3D: sombra no chão, o contorno empilhado até a altura (laterais) e o corpo no topo.
        Deixa o painter no plano do topo. Falhou? devolve False e fica o desenho de sempre."""
        try:
            pecas = self._corpo_e_sombra(r, n)
            if pecas is None:
                return False
            com_sombra, com_corpo = sombra, corpo
            corpo, sombra, m, E = pecas
            if not com_sombra:
                sombra = None
            from . import camera3d
            cam = camera3d.Camera(painter)
            h = self.altura_3d
            nevoa = camera3d.nevoa_da_cena(self.scene())   # (v0.70) tela do jogador: escondido na névoa = some
            if nevoa is not None and nevoa.amostrar(cam.projetar(r.center(), 0.0)) >= 0.97:
                painter.setWorldTransform(cam.transformacao_topo(h))
                painter.setOpacity(0.0)   # (quem chamou ainda desenha o corpo "no topo": fica invisível)
                return True
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            if self.tipo in SUSPENSOS:   # preso na parede: só o desenho, lá no alto
                painter.setWorldTransform(cam.transformacao_topo(h))
                painter.drawPixmap(r, corpo, QRectF(corpo.rect()))
                return True
            if sombra is not None:   # sombra no chão, pro lado contrário da luz, mais longa se é alto
                d = max(3.0, min(9.0 if self.tipo in ORGANICOS else 14.0, h * 0.1))
                ang = math.radians(-self.rotation())
                dx = (d * 0.75) * math.cos(ang) - d * math.sin(ang)
                dy = (d * 0.75) * math.sin(ang) + d * math.cos(ang)
                mm = m / E
                painter.drawPixmap(QRectF(r.left() - mm + dx, r.top() - mm + dy, r.width() + 2 * mm,
                                          r.height() + 2 * mm), sombra, QRectF(sombra.rect()))
            if not com_corpo:
                return True   # (v0.84) só a sombra (o corpo é a camada altura3d que desenha)
            # quantas camadas pra lateral ficar maciça: ~1 a cada 1,5 px de deslocamento na tela
            c = r.center()
            pe, topo = cam.projetar(c, 0), cam.projetar(c, h)
            canto = cam.projetar(r.topLeft(), h) - cam.projetar(r.topLeft(), 0)
            desloc = max(math.hypot(topo.x() - pe.x(), topo.y() - pe.y()), math.hypot(canto.x(), canto.y()))
            camadas = max(2, min(28 if n == 2 else 16, int(desloc / 1.5) + 1))
            if camera3d.em_movimento():   # (v0.76) câmera mexendo: metade das camadas (ninguém vê a diferença)
                camadas = max(2, camadas // 2)
            escuros = _laterais(corpo, self.tipo in ORGANICOS)
            z0 = 0.0
            pernas = PERNAS.get(self.tipo)
            if pernas is not None:   # (v0.67.1) móvel: pernas até o tampo, e só o tampo é "maciço"
                tampo, lado, arranjo = pernas
                z0 = h * (1 - tampo)
                cor_perna = _cor_media(corpo).darker(145)
                for pol in _pes(r, lado, arranjo):
                    camera3d.desenhar_laterais(painter, cam, [pol], z0, cor_perna, None, 0.0)
                camadas = max(2, int(camadas * tampo) + 2)
            faixas = FAIXAS.get(self.tipo, ())
            for k in range(camadas):
                f = k / camadas
                z = z0 + (h - z0) * f
                painter.setWorldTransform(cam.transformacao_topo(z))
                # embaixo mais escuro (oclusão), subindo clareia
                pm = escuros[min(len(escuros) - 1, k * len(escuros) // camadas)]
                for de, ate, rgba in faixas:   # (v0.67.1) o material aparecendo de lado
                    if de <= f < ate:
                        pm = _tingido(pm, rgba)
                        break
                painter.drawPixmap(r, pm, QRectF(corpo.rect()))
            painter.setWorldTransform(cam.transformacao_topo(h))
            painter.drawPixmap(r, corpo, QRectF(corpo.rect()))
            return True
        except Exception as erro:   # (erro dentro de paint() fecha o programa)
            from ..seguranca import registrar_erro
            registrar_erro(f"Objeto 3D ({self.tipo}) falhou: {erro!r}")
            return False

    def _corpo_e_sombra(self, r, n):
        """(corpo, sombra, margem, escala) do desenho com relevo, guardados por tipo/tamanho."""
        from .volume import com_volume, np as _np
        if _np is None:
            return None
        E = 2   # desenha com o dobro de pontos (fica nítido no zoom)
        w, h = max(2, int(self.largura * E)), max(2, int(self.altura * E))
        if w * h > 1400 * 1400:
            return None
        chave = (self.hash_imagem or self.tipo, w, h, n)
        from .volume import _CACHE
        if chave in _CACHE:
            corpo, sombra, m = com_volume(chave, None)
        else:
            base = QPixmap(w, h)
            base.fill(Qt.GlobalColor.transparent)
            p = QPainter(base)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            if self._pixmap is not None:
                p.drawPixmap(QRectF(0, 0, w, h), self._pixmap, QRectF(self._pixmap.rect()))
            else:
                entrada = CATALOGO.get(self.tipo)
                if not entrada:
                    p.end()
                    return None
                p.scale(E, E)
                entrada[4](p, r)
            p.end()
            corpo, sombra, m = com_volume(chave, base, 0.8 if n == 1 else 1.15,
                                          margem=int(max(8, min(26, min(w, h) * 0.14))))
        return corpo, sombra, m, E

    def _desenhar_com_volume(self, painter, r, n) -> bool:
        """Corpo com relevo + sombra macia (calculados uma vez por tipo/tamanho e guardados)."""
        pecas = self._corpo_e_sombra(r, n)
        if pecas is None:
            return False
        corpo, sombra, m, E = pecas
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if sombra is not None:
            # a sombra cai sempre pro mesmo lado da mesa (baixo-direita), mesmo com o objeto girado
            d = max(3.0, min(9.0, min(self.largura, self.altura) * 0.09)) * (1.0 if n == 1 else 1.3)
            ang = math.radians(-self.rotation())
            dx = (d * 0.75) * math.cos(ang) - d * math.sin(ang)
            dy = (d * 0.75) * math.sin(ang) + d * math.cos(ang)
            mm = m / E
            painter.drawPixmap(QRectF(r.left() - mm + dx, r.top() - mm + dy, r.width() + 2 * mm, r.height() + 2 * mm),
                               sombra, QRectF(sombra.rect()))
        painter.drawPixmap(r, corpo, QRectF(corpo.rect()))
        return True

    # ------------------------------------------------------------ mouse
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        cena = self.scene()
        if cena is not None and hasattr(cena, "prop_arrastado"):
            cena.prop_arrastado(self)   # no player: pede pro mestre
            return
        if cena is not None and getattr(cena, "snap_ativo", False) and not self.travado:
            p = self.pos()
            self.setPos(round(p.x() / (CELULA / 2)) * (CELULA / 2), round(p.y() / (CELULA / 2)) * (CELULA / 2))

    def mouseDoubleClickEvent(self, event):
        cena = self.scene()
        if cena is not None and hasattr(cena, "prop_duplo_clique"):
            cena.prop_duplo_clique(self)
        event.accept()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._mudou()
        return super().itemChange(change, value)

    def aplicar_trava(self, travado: bool):
        self.travado = travado
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not travado)

    # ------------------------------------------------------------ luz e obstáculo
    def luz_dict(self) -> dict | None:
        if not self.luz or not self.luz_acesa or not self.isVisible():
            return None
        from .luzes import TIPOS_LUZ
        nome, forte, fraco, cor, tremula = TIPOS_LUZ.get(self.luz, TIPOS_LUZ["tocha"])
        c = self.centro_cena()
        return {"classe": "luz", "id": self.uid + ":luz", "x": c.x(), "y": c.y(), "tipo": self.luz,
                "forte": forte, "fraco": fraco, "cor": cor, "tremula": tremula, "acesa": True,
                "visivel": True}

    # ------------------------------------------------------------ salvar / rede
    def para_dict(self, com_itens: bool = True) -> dict:
        p = self.pos()
        d = {"classe": "prop", "id": self.uid, "x": p.x(), "y": p.y(), "z": self.zValue(),
             "tipo": self.tipo, "nome": self.nome, "w": self.w, "h": self.h, "angulo": self.angulo,
             "interativo": self.interativo, "bloqueia": self.bloqueia, "luz": self.luz,
             "luz_acesa": self.luz_acesa, "visivel": self.isVisible(), "movel": self.movel,
             "efeito": self.efeito, "ligacao": self.ligacao,
             "cantos": [[q.x(), q.y()] for q in self.cantos_cena()]}
        if com_itens:
            d.update({"gatilho": self.gatilho, "documento": self.documento, "solto": self.solto,
                      "sorteio": self.sorteio,
                      "chave": self.chave, "gasta_chave": self.gasta_chave,
                      "trancado": self.trancado, "perto": self.perto, "pode_pegar": self.pode_pegar,
                      "itens": self.itens,
                      "imagem": base64.b64encode(self.imagem).decode("ascii") if self.imagem else None})
        return d

    def aplicar_dict(self, d: dict):
        self.prepareGeometryChange()
        self.tipo = d.get("tipo", self.tipo)
        self.nome = d.get("nome", self.nome)
        self.w, self.h = float(d.get("w", self.w)), float(d.get("h", self.h))
        self.angulo = float(d.get("angulo", 0))
        self.interativo = bool(d.get("interativo", self.interativo))
        self.bloqueia = bool(d.get("bloqueia", self.bloqueia))
        self.luz = d.get("luz", self.luz)
        self.luz_acesa = bool(d.get("luz_acesa", True))
        if (d.get("efeito") or "") != self.efeito:
            self.efeito = d.get("efeito") or ""
            self._cache_efeito = {}
        self.movel = bool(d.get("movel", self.movel))
        self.documento = bool(d.get("documento", self.documento))
        self.solto = bool(d.get("solto", self.solto))
        self.chave = d.get("chave", self.chave) or ""
        self.gasta_chave = bool(d.get("gasta_chave", self.gasta_chave))
        if "gatilho" in d:
            self.gatilho = d.get("gatilho")
        if "sorteio" in d:
            self.sorteio = d.get("sorteio")
        self.trancado = bool(d.get("trancado", False))
        self.perto = bool(d.get("perto", True))
        self.pode_pegar = bool(d.get("pode_pegar", True))
        self.itens = list(d.get("itens", self.itens) or [])
        lig = d.get("ligacao")
        self.ligacao = lig if isinstance(lig, dict) and "andar" in lig and "id" in lig else None
        if self.tipo == "escada":   # aventuras da v0.46.0 salvaram a escada como "baú"
            self.interativo = False
            self.itens = []
        self._atualizar_origem()
        self.update()

    @classmethod
    def de_dict(cls, d: dict) -> "PropItem":
        imagem = base64.b64decode(d["imagem"]) if d.get("imagem") else None
        item = cls(d.get("tipo", "bau"), imagem)
        item.uid = d.get("id") or item.uid
        item.aplicar_dict(d)
        item.setPos(d["x"], d["y"])
        item.setZValue(d.get("z", 0))
        item.setVisible(d.get("visivel", True))
        return item


def obstaculos_de_prop(d) -> list[tuple]:
    """As 4 bordas de um prop que bloqueia a visão."""
    if isinstance(d, PropItem):
        if not d.bloqueia or not d.isVisible():
            return []
        cantos = [(q.x(), q.y()) for q in d.cantos_cena()]
    else:
        if not d.get("bloqueia") or not d.get("visivel", True) or not d.get("cantos"):
            return []
        cantos = [tuple(c) for c in d["cantos"]]
    return [(cantos[k][0], cantos[k][1], cantos[(k + 1) % 4][0], cantos[(k + 1) % 4][1])
            for k in range(4)]


def novo_id_item() -> str:
    return uuid.uuid4().hex[:12]
