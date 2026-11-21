"""
Objetos de cada ambientação (v0.30): ~10 por tema — Medieval, Moderno, Futurista, Mágico e Terror.

Mesmo jeito dos objetos de props.py: desenhados pelo programa, vistos de cima, `d_nome(p, r)` onde
`r` é o retângulo do objeto na mesa (1 quadrado = CELULA px). O volume (relevo, sombra macia) é
aplicado depois, igual aos outros (props.py, cache de imagem).

TEMAS_PROP diz em quais temas cada objeto aparece primeiro no painel Objetos (os comuns, sem
entrada aqui, aparecem em todos).
"""

import math
import random

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QLinearGradient, QPainterPath, QPolygonF, QRadialGradient

from ..config import CELULA
from .props import (CONTORNO, MADEIRA, MADEIRA_CLA, MADEIRA_ESC, METAL, METAL_ESC, OURO, PEDRA, PEDRA_ESC,
                    TECIDO, TECIDO_AZUL, VERDE, VERDE_ESC, _caneta, _circ, _m, _ret, _sombra, _tabuas)


def _brilho(p, c, raio, cor: QColor, alfa=150):
    """Halo de luz em volta (cristais, telas, reator…)."""
    g = QRadialGradient(c, raio)
    g.setColorAt(0, QColor(cor.red(), cor.green(), cor.blue(), alfa))
    g.setColorAt(1, QColor(cor.red(), cor.green(), cor.blue(), 0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(g))
    p.drawEllipse(c, raio, raio)


def _poligono(p, pts, cor, borda=CONTORNO, larg=2.0):
    p.setPen(_caneta(borda, larg) if borda is not None else Qt.PenStyle.NoPen)
    p.setBrush(cor)
    p.drawPolygon(QPolygonF([QPointF(*q) if isinstance(q, tuple) else q for q in pts]))


def _linha(p, a, b, cor=CONTORNO, larg=2.0):
    p.setPen(_caneta(cor, larg))
    p.drawLine(a, b)


def _aleat(r):
    return random.Random(int(r.width() * 13 + r.height() * 7))


# ====================================================================== MEDIEVAL
def d_trono(p, r):
    a = _m(r, 0.1)
    _sombra(p, a)
    _ret(p, a, QColor("#6a4a1a"), 5)                               # base dourada escura
    encosto = QRectF(a.left(), a.top(), a.width(), a.height() * 0.32)
    _ret(p, encosto, OURO, 5)
    for k in (0.2, 0.5, 0.8):                                       # pontas da coroa no encosto
        x = a.left() + a.width() * k
        _poligono(p, [QPointF(x - 5, encosto.top() + 2), QPointF(x, encosto.top() - 6),
                      QPointF(x + 5, encosto.top() + 2)], OURO, CONTORNO, 1.2)
    assento = QRectF(a.left() + a.width() * 0.16, a.top() + a.height() * 0.36, a.width() * 0.68, a.height() * 0.58)
    _ret(p, assento, TECIDO, 6, CONTORNO, 1.5)
    for x in (a.left() + a.width() * 0.08, a.right() - a.width() * 0.08):   # braços
        _ret(p, QRectF(x - a.width() * 0.07, assento.top(), a.width() * 0.14, assento.height()), OURO, 4, CONTORNO, 1.2)
    _circ(p, encosto.center(), min(encosto.width(), encosto.height()) * 0.22, QColor("#a02030"), CONTORNO, 1.2)


def d_forja(p, r):
    a = _m(r, 0.06)
    _sombra(p, a)
    _ret(p, a, PEDRA_ESC, 6)
    _ret(p, a.adjusted(6, 6, -6, -6), PEDRA, 4, None)
    brasa = _m(a, 0.26)
    g = QRadialGradient(brasa.center(), brasa.width() * 0.6)
    g.setColorAt(0, QColor("#fff0a0"))
    g.setColorAt(0.4, QColor("#ff8a20"))
    g.setColorAt(1, QColor("#7a1a08"))
    _ret(p, brasa, QBrush(g), 5, QColor("#3a1a0a"), 1.5)
    rnd = _aleat(r)
    for _ in range(14):
        q = brasa.center() + QPointF(rnd.uniform(-1, 1) * brasa.width() * 0.4, rnd.uniform(-1, 1) * brasa.height() * 0.4)
        _circ(p, q, rnd.uniform(1.2, 2.6), QColor("#ffd060"), None)
    # fole ao lado
    fole = QRectF(a.right() - a.width() * 0.2, a.bottom() - a.height() * 0.32, a.width() * 0.16, a.height() * 0.26)
    _ret(p, fole, MADEIRA, 4, CONTORNO, 1.2)


def d_bigorna(p, r):
    c = r.center()
    w, h = r.width() * 0.62, r.height() * 0.3
    _sombra(p, QRectF(c.x() - w / 2, c.y() - h / 2, w, h), 3)
    corpo = QPainterPath(QPointF(c.x() - w * 0.5, c.y() - h * 0.5))
    corpo.lineTo(c.x() + w * 0.25, c.y() - h * 0.5)
    corpo.quadTo(QPointF(c.x() + w * 0.55, c.y() - h * 0.45), QPointF(c.x() + w * 0.62, c.y()))  # chifre
    corpo.quadTo(QPointF(c.x() + w * 0.55, c.y() + h * 0.45), QPointF(c.x() + w * 0.25, c.y() + h * 0.5))
    corpo.lineTo(c.x() - w * 0.5, c.y() + h * 0.5)
    corpo.closeSubpath()
    p.setPen(_caneta(CONTORNO, 2))
    p.setBrush(METAL_ESC)
    p.drawPath(corpo)
    _ret(p, QRectF(c.x() - w * 0.42, c.y() - h * 0.3, w * 0.5, h * 0.6), METAL, 2, None)


def d_carroca(p, r):
    a = r.adjusted(r.width() * 0.2, r.height() * 0.04, -r.width() * 0.2, -r.height() * 0.14)
    _sombra(p, a)
    roda_l, roda_a = r.width() * 0.13, a.height() * 0.3
    for y in (a.top() + a.height() * 0.24, a.bottom() - a.height() * 0.24):   # rodas grandes, pra fora da caçamba
        _linha(p, QPointF(a.left() - roda_l * 0.6, y), QPointF(a.right() + roda_l * 0.6, y), METAL_ESC, 3)   # eixo
        for x in (a.left() - roda_l * 0.55, a.right() + roda_l * 0.55):
            _ret(p, QRectF(x - roda_l / 2, y - roda_a / 2, roda_l, roda_a), MADEIRA_ESC, 4, CONTORNO, 1.5)
            _linha(p, QPointF(x, y - roda_a / 2 + 2), QPointF(x, y + roda_a / 2 - 2), MADEIRA_CLA, 1.2)
    _ret(p, a, MADEIRA, 3)
    _tabuas(p, a.adjusted(3, 3, -3, -3), 5)
    _ret(p, a.adjusted(5, 5, -5, -5), QColor(0, 0, 0, 0), 2, MADEIRA_ESC, 1.5)
    for k in range(2):   # sacas de carga
        _circ(p, QPointF(a.center().x(), a.top() + a.height() * (0.35 + k * 0.28)), a.width() * 0.26,
              QColor("#b89a6a"), CONTORNO, 1.2)
    # timão (onde vai o cavalo)
    _linha(p, QPointF(a.center().x() - 5, a.bottom()), QPointF(a.center().x() - 5, r.bottom() - 2), MADEIRA_ESC, 3)
    _linha(p, QPointF(a.center().x() + 5, a.bottom()), QPointF(a.center().x() + 5, r.bottom() - 2), MADEIRA_ESC, 3)


def d_tenda(p, r):
    a = _m(r, 0.05)
    c = a.center()
    _sombra(p, a, a.width() * 0.2)
    lona = [a.topLeft() + QPointF(a.width() * 0.1, 0), a.topRight() - QPointF(a.width() * 0.1, 0),
            a.topRight() + QPointF(0, a.height() * 0.1), a.bottomRight() - QPointF(0, a.height() * 0.1),
            a.bottomRight() - QPointF(a.width() * 0.1, 0), a.bottomLeft() + QPointF(a.width() * 0.1, 0),
            a.bottomLeft() - QPointF(0, a.height() * 0.1), a.topLeft() + QPointF(0, a.height() * 0.1)]
    _poligono(p, lona, QColor("#c8b48a"))
    # gomos da lona (clarinho / escurinho alternando)
    for k, pt in enumerate(lona):
        prox = lona[(k + 1) % len(lona)]
        _poligono(p, [c, pt, prox], QColor(255, 255, 255, 28) if k % 2 else QColor(0, 0, 0, 30), None)
    for pt in lona:
        _linha(p, c, pt, QColor("#7a6040"), 1.2)
    _circ(p, c, min(a.width(), a.height()) * 0.05, TECIDO, CONTORNO, 1.2)


def d_mesa_banquete(p, r):
    a = r.adjusted(r.width() * 0.04, r.height() * 0.2, -r.width() * 0.04, -r.height() * 0.2)
    _sombra(p, a)
    _ret(p, a, MADEIRA, 4)
    toalha = a.adjusted(a.width() * 0.04, a.height() * 0.18, -a.width() * 0.04, -a.height() * 0.18)
    _ret(p, toalha, QColor("#e8dcc0"), 2, QColor("#a89878"), 1)
    rnd = _aleat(r)
    n = max(3, int(toalha.width() / (CELULA * 0.6)))
    for k in range(n):   # pratos, taças, um pernil no meio
        x = toalha.left() + toalha.width() * (k + 0.5) / n
        _circ(p, QPointF(x, toalha.center().y()), toalha.height() * 0.28, QColor("#c8c8c8"), CONTORNO, 1)
        _circ(p, QPointF(x + toalha.height() * 0.3, toalha.top() + 4), 2.6, OURO, CONTORNO, 0.8)
        if k == n // 2:
            _circ(p, QPointF(x, toalha.center().y()), toalha.height() * 0.2, QColor("#8a4a20"), CONTORNO, 1)
        elif rnd.random() < 0.5:
            _circ(p, QPointF(x, toalha.center().y()), toalha.height() * 0.1, QColor("#b03028"), None)


def d_estandarte(p, r):
    c = r.center()
    larg = r.width() * 0.7
    pano = QRectF(c.x() - larg / 2, c.y() - r.height() * 0.08, larg, r.height() * 0.36)
    _sombra(p, pano, 2)
    _ret(p, pano, TECIDO, 1, CONTORNO, 1.5)
    _poligono(p, [pano.bottomLeft(), pano.bottomRight(), QPointF(c.x(), pano.bottom() + r.height() * 0.14)],
              TECIDO, CONTORNO, 1.5)
    _circ(p, pano.center() + QPointF(0, 3), pano.height() * 0.28, OURO, CONTORNO, 1)
    _ret(p, QRectF(c.x() - larg * 0.56, pano.top() - 4, larg * 1.12, 5), MADEIRA_ESC, 2, CONTORNO, 1)   # travessa
    _circ(p, c + QPointF(0, -r.height() * 0.2), r.width() * 0.07, METAL, CONTORNO, 1.2)                   # mastro


def d_suporte_armas(p, r):
    a = r.adjusted(r.width() * 0.04, r.height() * 0.3, -r.width() * 0.04, -r.height() * 0.3)
    _sombra(p, a)
    _ret(p, a, MADEIRA_ESC, 2)
    n = 5
    for k in range(n):
        x = a.left() + a.width() * (k + 0.5) / n
        if k % 2 == 0:   # espada
            _linha(p, QPointF(x, a.top() - a.height() * 0.6), QPointF(x, a.bottom() + 2), METAL, 3)
            _linha(p, QPointF(x - 5, a.top() + 2), QPointF(x + 5, a.top() + 2), OURO, 2.2)
        else:            # lança
            _linha(p, QPointF(x, a.top() - a.height() * 0.9), QPointF(x, a.bottom() + 2), MADEIRA_CLA, 2.2)
            _poligono(p, [QPointF(x - 3, a.top() - a.height() * 0.8), QPointF(x, a.top() - a.height() * 1.15),
                          QPointF(x + 3, a.top() - a.height() * 0.8)], METAL, CONTORNO, 1)


def d_feno(p, r):
    a = _m(r, 0.14)
    _sombra(p, a, 4)
    _ret(p, a, QColor("#c8a848"), 4)
    p.setPen(_caneta(QColor("#9a7a28"), 1))
    rnd = _aleat(r)
    for _ in range(22):
        y = rnd.uniform(a.top() + 3, a.bottom() - 3)
        x = rnd.uniform(a.left() + 2, a.right() - 12)
        p.drawLine(QPointF(x, y), QPointF(x + rnd.uniform(5, 11), y + rnd.uniform(-2, 2)))
    for k in (0.3, 0.7):   # amarras
        x = a.left() + a.width() * k
        _linha(p, QPointF(x, a.top()), QPointF(x, a.bottom()), QColor("#6a4a20"), 2)


def d_tocheiro(p, r):
    c = r.center()
    _circ(p, c + QPointF(2, 3), r.width() * 0.2, QColor(0, 0, 0, 70), None)
    _circ(p, c, r.width() * 0.2, METAL_ESC)
    _circ(p, c, r.width() * 0.13, QColor("#3a2a1a"), None)
    _brilho(p, c, r.width() * 0.3, QColor("#ffb050"), 160)
    _circ(p, c, r.width() * 0.08, QColor("#ffe090"), None)


# ====================================================================== MODERNO
BRANCO = QColor("#e6e8ea")
BRANCO_ESC = QColor("#a9aeb4")


def d_geladeira(p, r):
    a = _m(r, 0.1)
    _sombra(p, a, 3)
    _ret(p, a, BRANCO, 3)
    _linha(p, QPointF(a.left() + 2, a.top() + a.height() * 0.38), QPointF(a.right() - 2, a.top() + a.height() * 0.38),
           BRANCO_ESC, 1.5)
    _ret(p, QRectF(a.right() - 7, a.top() + 5, 3, a.height() * 0.22), METAL_ESC, 1, None)
    _ret(p, QRectF(a.right() - 7, a.top() + a.height() * 0.45, 3, a.height() * 0.3), METAL_ESC, 1, None)


def d_fogao(p, r):
    a = _m(r, 0.1)
    _sombra(p, a, 3)
    _ret(p, a, BRANCO, 3)
    _ret(p, a.adjusted(3, 3, -3, -a.height() * 0.22), QColor("#2a2c30"), 2, None)
    for dx in (-1, 1):
        for dy in (-1, 1):
            q = QPointF(a.center().x() + dx * a.width() * 0.2, a.top() + a.height() * 0.4 + dy * a.height() * 0.17)
            _circ(p, q, a.width() * 0.12, QColor("#4a4c52"), QColor("#18191c"), 1)
            _circ(p, q, a.width() * 0.05, QColor("#2a2c30"), None)
    for k in range(4):
        _circ(p, QPointF(a.left() + a.width() * (0.2 + k * 0.2), a.bottom() - a.height() * 0.1), 2, METAL_ESC, None)


def d_pia(p, r):
    a = r.adjusted(r.width() * 0.06, r.height() * 0.2, -r.width() * 0.06, -r.height() * 0.2)
    _sombra(p, a, 3)
    _ret(p, a, QColor("#c9c3b4"), 3)
    cuba = a.adjusted(a.width() * 0.12, a.height() * 0.2, -a.width() * 0.12, -a.height() * 0.12)
    _ret(p, cuba, METAL, cuba.height() * 0.4, METAL_ESC, 1.5)
    _circ(p, cuba.center(), 2, METAL_ESC, None)
    _ret(p, QRectF(a.center().x() - 2, a.top() + 1, 4, a.height() * 0.3), METAL_ESC, 1, None)


def d_vaso_sanitario(p, r):
    c = r.center()
    tanque = QRectF(c.x() - r.width() * 0.28, r.top() + r.height() * 0.12, r.width() * 0.56, r.height() * 0.2)
    assento = QRectF(c.x() - r.width() * 0.22, tanque.bottom() - 2, r.width() * 0.44, r.height() * 0.52)
    _sombra(p, tanque.united(assento), 8)
    _ret(p, tanque, BRANCO, 3)
    p.setPen(_caneta(CONTORNO, 2))
    p.setBrush(BRANCO)
    p.drawEllipse(assento)
    p.setPen(_caneta(BRANCO_ESC, 1.2))
    p.setBrush(QColor("#b8d4dc"))
    p.drawEllipse(_m(assento, 0.22))


def d_banheira(p, r):
    a = _m(r, 0.06)
    _sombra(p, a, a.width() * 0.3)
    _ret(p, a, BRANCO, a.width() * 0.3)
    agua = a.adjusted(5, 5, -5, -5)
    g = QLinearGradient(agua.topLeft(), agua.bottomRight())
    g.setColorAt(0, QColor("#bfe4ee"))
    g.setColorAt(1, QColor("#7ab4c8"))
    _ret(p, agua, QBrush(g), agua.width() * 0.3, BRANCO_ESC, 1.2)
    _circ(p, QPointF(a.center().x(), a.top() + 7), 2.5, METAL_ESC, None)


def d_tv(p, r):
    # rack baixo com a TV em cima (vista de cima: rack de madeira + tela fininha com borda clara)
    rack = r.adjusted(r.width() * 0.06, r.height() * 0.3, -r.width() * 0.06, -r.height() * 0.12)
    _sombra(p, rack, 2)
    _ret(p, rack, QColor("#5a4434"), 2)
    _brilho(p, QPointF(rack.center().x(), rack.top()), rack.width() * 0.5, QColor("#7ab4ff"), 70)
    tela = QRectF(rack.left() + rack.width() * 0.06, rack.top() + rack.height() * 0.18, rack.width() * 0.88,
                  rack.height() * 0.24)
    _ret(p, tela, QColor("#16181c"), 2, QColor("#8a9098"), 1.5)
    _ret(p, QRectF(rack.center().x() - rack.width() * 0.12, tela.bottom(), rack.width() * 0.24, rack.height() * 0.2),
         QColor("#2a2c30"), 1, CONTORNO, 1)
    _circ(p, QPointF(rack.right() - 8, rack.bottom() - 6), 2, QColor("#ff4040"), None)


def d_escrivaninha(p, r):
    a = r.adjusted(r.width() * 0.04, r.height() * 0.15, -r.width() * 0.04, -r.height() * 0.15)
    _sombra(p, a)
    _ret(p, a, QColor("#6a5444"), 3)
    _ret(p, QRectF(a.left() + a.width() * 0.08, a.top() + a.height() * 0.2, a.width() * 0.3, a.height() * 0.5),
         QColor("#e8e6e0"), 1, CONTORNO, 1)                                  # folhas
    _ret(p, QRectF(a.left() + a.width() * 0.5, a.top() + a.height() * 0.15, a.width() * 0.34, a.height() * 0.4),
         QColor("#2a2c30"), 2, CONTORNO, 1.2)                                # notebook
    _circ(p, QPointF(a.right() - a.width() * 0.08, a.bottom() - a.height() * 0.25), a.height() * 0.12,
          QColor("#e8e0d0"), CONTORNO, 1)                                    # caneca


def d_moto(p, r):
    c = r.center()
    larg, alt = r.width() * 0.34, r.height() * 0.86
    corpo = QRectF(c.x() - larg / 2, c.y() - alt / 2, larg, alt)
    _sombra(p, corpo, larg / 2)
    for y in (corpo.top() + 2, corpo.bottom() - alt * 0.22 - 2):   # rodas
        _ret(p, QRectF(c.x() - larg * 0.22, y, larg * 0.44, alt * 0.22), QColor("#1a1a1c"), 4)
    _ret(p, QRectF(c.x() - larg * 0.4, c.y() - alt * 0.22, larg * 0.8, alt * 0.44), QColor("#b02a2a"), larg * 0.3)
    _ret(p, QRectF(c.x() - larg * 0.24, c.y() + alt * 0.02, larg * 0.48, alt * 0.2), QColor("#2a2a2c"), 4, None)  # banco
    _linha(p, QPointF(c.x() - larg * 0.7, c.y() - alt * 0.26), QPointF(c.x() + larg * 0.7, c.y() - alt * 0.26),
           METAL_ESC, 3)   # guidão


def d_cacamba(p, r):
    a = _m(r, 0.08)
    _sombra(p, a, 2)
    _ret(p, a, QColor("#2f6a3a"), 2)
    for x in (a.center().x() - 1,):
        _linha(p, QPointF(x, a.top() + 2), QPointF(x, a.bottom() - 2), QColor("#1c4024"), 2)
    rnd = _aleat(r)
    for _ in range(5):   # saco de lixo escapando
        q = QPointF(rnd.uniform(a.left() + 6, a.right() - 6), a.top() + rnd.uniform(2, 6))
        _circ(p, q, rnd.uniform(3, 5), QColor("#1a1a1c"), None)


def d_maquina_venda(p, r):
    a = r.adjusted(r.width() * 0.12, r.height() * 0.2, -r.width() * 0.12, -r.height() * 0.2)
    _sombra(p, a, 2)
    _ret(p, a, QColor("#a02a2a"), 2)
    vidro = QRectF(a.left() + 3, a.top() + 3, a.width() * 0.66, a.height() - 6)
    _ret(p, vidro, QColor("#a8d8e8"), 1, CONTORNO, 1)
    rnd = _aleat(r)
    for k in range(6):
        _ret(p, QRectF(vidro.left() + 2 + (k % 3) * vidro.width() / 3, vidro.top() + 2 + (k // 3) * vidro.height() / 2,
                       vidro.width() / 3 - 3, vidro.height() / 2 - 3),
             QColor(rnd.choice(["#e8c040", "#40a0e8", "#e85040", "#50c060"])), 1, None)
    _brilho(p, a.center(), a.width() * 0.8, QColor("#fff4dc"), 40)


# ====================================================================== FUTURISTA
NEON = QColor("#38e1ff")
NEON2 = QColor("#ff3fa4")
CASCO = QColor("#3a4250")
CASCO_CLA = QColor("#6a7484")


def d_holomesa(p, r):
    a = _m(r, 0.08)
    c, raio = a.center(), min(a.width(), a.height()) / 2
    _circ(p, c + QPointF(3, 4), raio, QColor(0, 0, 0, 70), None)
    _circ(p, c, raio, CASCO)
    _circ(p, c, raio * 0.8, QColor("#141a24"), CASCO_CLA, 1.2)
    _brilho(p, c, raio * 0.9, NEON, 110)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(_caneta(QColor(120, 240, 255, 220), 1.2))
    for k in range(3):   # mapa holográfico (anéis + grade)
        p.drawEllipse(c, raio * (0.25 + k * 0.17), raio * (0.25 + k * 0.17))
    for ang in range(0, 180, 45):
        d = QPointF(math.cos(math.radians(ang)), math.sin(math.radians(ang))) * raio * 0.7
        p.drawLine(c - d, c + d)


def d_robo(p, r):
    c = r.center()
    corpo = QRectF(c.x() - r.width() * 0.26, c.y() - r.height() * 0.22, r.width() * 0.52, r.height() * 0.44)
    _sombra(p, corpo, 6)
    for dx in (-1, 1):   # ombros/braços
        _ret(p, QRectF(c.x() + dx * r.width() * 0.32 - r.width() * 0.08, c.y() - r.height() * 0.14,
                       r.width() * 0.16, r.height() * 0.3), CASCO_CLA, 4)
    _ret(p, corpo, QColor("#9aa4b0"), 6)
    _circ(p, c, r.width() * 0.14, CASCO, CONTORNO, 1.2)                          # cabeça
    _ret(p, QRectF(c.x() - r.width() * 0.1, c.y() - r.height() * 0.08, r.width() * 0.2, r.height() * 0.05),
         QColor("#ff5050"), 1, None)                                             # visor


def d_drone(p, r):
    c = r.center()
    s = r.width() * 0.3
    for dx in (-1, 1):
        for dy in (-1, 1):
            q = c + QPointF(dx * s, dy * s)
            _linha(p, c, q, CASCO, 3)
            _circ(p, q, s * 0.45, QColor(200, 210, 220, 90), CONTORNO, 1)
            _circ(p, q, 2, CONTORNO, None)
    _ret(p, QRectF(c.x() - s * 0.4, c.y() - s * 0.4, s * 0.8, s * 0.8), CASCO_CLA, 4)
    _circ(p, c, s * 0.15, NEON2, None)


def d_console(p, r):
    a = r.adjusted(r.width() * 0.04, r.height() * 0.2, -r.width() * 0.04, -r.height() * 0.2)
    _sombra(p, a, 3)
    _ret(p, a, CASCO, 4)
    tela = QRectF(a.left() + 4, a.top() + 3, a.width() - 8, a.height() * 0.45)
    _ret(p, tela, QColor("#0a1a20"), 2, NEON, 1)
    p.setPen(_caneta(QColor(64, 255, 176, 200), 1))
    for k in range(3):
        y = tela.top() + tela.height() * (0.3 + k * 0.22)
        p.drawLine(QPointF(tela.left() + 4, y), QPointF(tela.left() + tela.width() * (0.4 + 0.2 * k), y))
    rnd = _aleat(r)
    for k in range(10):   # botões
        q = QPointF(a.left() + 8 + k * (a.width() - 16) / 9, a.bottom() - a.height() * 0.22)
        _circ(p, q, 2.2, QColor(rnd.choice(["#38e1ff", "#ff3fa4", "#ffe94a", "#38ff9a"])), None)


def d_reator(p, r):
    a = _m(r, 0.06)
    c, raio = a.center(), min(a.width(), a.height()) / 2
    _circ(p, c + QPointF(3, 4), raio, QColor(0, 0, 0, 80), None)
    _circ(p, c, raio, CASCO)
    for k in range(8):   # aletas
        ang = math.radians(k * 45 + 22.5)
        q = c + QPointF(math.cos(ang), math.sin(ang)) * raio * 0.82
        _circ(p, q, raio * 0.09, CASCO_CLA, CONTORNO, 1)
    _circ(p, c, raio * 0.6, QColor("#101820"), CASCO_CLA, 1.5)
    _brilho(p, c, raio * 0.75, NEON, 220)
    _circ(p, c, raio * 0.22, QColor("#e8fbff"), None)


def d_tubo_estase(p, r):
    c = r.center()
    raio = min(r.width(), r.height()) * 0.4
    _circ(p, c + QPointF(3, 4), raio, QColor(0, 0, 0, 70), None)
    _circ(p, c, raio, CASCO_CLA)
    g = QRadialGradient(c, raio * 0.8)
    g.setColorAt(0, QColor(150, 255, 220, 230))
    g.setColorAt(1, QColor(30, 120, 110, 230))
    _circ(p, c, raio * 0.78, QBrush(g), QColor("#2a5a5a"), 1.2)
    _circ(p, c + QPointF(0, -raio * 0.1), raio * 0.28, QColor(20, 60, 60, 160), None)   # vulto lá dentro
    p.setPen(_caneta(QColor(255, 255, 255, 140), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(c.x() - raio * 0.6, c.y() - raio * 0.6, raio * 1.2, raio * 1.2), 100 * 16, 60 * 16)


def d_nave(p, r):
    a = _m(r, 0.04)
    c = a.center()
    _poligono(p, [QPointF(c.x(), a.top()), QPointF(a.right(), a.bottom() - a.height() * 0.1),
                  QPointF(c.x(), a.bottom() - a.height() * 0.25), QPointF(a.left(), a.bottom() - a.height() * 0.1)],
              QColor(0, 0, 0, 70), None)
    casco = [QPointF(c.x(), a.top()), QPointF(c.x() + a.width() * 0.14, a.top() + a.height() * 0.4),
             QPointF(a.right(), a.bottom() - a.height() * 0.16), QPointF(c.x() + a.width() * 0.12, a.bottom() - a.height() * 0.2),
             QPointF(c.x(), a.bottom() - a.height() * 0.05), QPointF(c.x() - a.width() * 0.12, a.bottom() - a.height() * 0.2),
             QPointF(a.left(), a.bottom() - a.height() * 0.16), QPointF(c.x() - a.width() * 0.14, a.top() + a.height() * 0.4)]
    _poligono(p, casco, QColor("#9aa4b0"))
    _poligono(p, [QPointF(c.x(), a.top() + a.height() * 0.18), QPointF(c.x() + a.width() * 0.06, a.top() + a.height() * 0.42),
                  QPointF(c.x(), a.top() + a.height() * 0.5), QPointF(c.x() - a.width() * 0.06, a.top() + a.height() * 0.42)],
              QColor("#3a8ab0"), CONTORNO, 1.2)   # cabine
    for dx in (-1, 1):   # motores
        q = QPointF(c.x() + dx * a.width() * 0.1, a.bottom() - a.height() * 0.1)
        _brilho(p, q, a.width() * 0.08, NEON, 200)


def d_conteiner(p, r):
    a = _m(r, 0.05)
    _sombra(p, a, 1)
    _ret(p, a, QColor("#b0652a"), 1)
    p.setPen(_caneta(QColor("#7a4018"), 1.5))
    vertical = a.width() < a.height()
    n = 9
    for k in range(1, n):   # chapa ondulada
        if vertical:
            y = a.top() + a.height() * k / n
            p.drawLine(QPointF(a.left() + 2, y), QPointF(a.right() - 2, y))
        else:
            x = a.left() + a.width() * k / n
            p.drawLine(QPointF(x, a.top() + 2), QPointF(x, a.bottom() - 2))
    for pt in (a.topLeft(), a.topRight(), a.bottomLeft(), a.bottomRight()):
        _ret(p, QRectF(pt.x() - 3, pt.y() - 3, 6, 6), METAL_ESC, 1, CONTORNO, 1)


def d_teleporte(p, r):
    a = _m(r, 0.06)
    c, raio = a.center(), min(a.width(), a.height()) / 2
    _circ(p, c + QPointF(3, 4), raio, QColor(0, 0, 0, 70), None)
    _poligono(p, [c + QPointF(math.cos(math.radians(k * 60)), math.sin(math.radians(k * 60))) * raio
                  for k in range(6)], CASCO)
    _circ(p, c, raio * 0.72, QColor("#141a24"), CASCO_CLA, 1.2)
    _brilho(p, c, raio * 0.75, NEON2, 160)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(_caneta(QColor(255, 140, 210, 220), 1.4))
    for k in range(3):
        p.drawEllipse(c, raio * (0.2 + k * 0.17), raio * (0.2 + k * 0.17))


def d_torreta(p, r):
    c = r.center()
    raio = r.width() * 0.3
    _circ(p, c + QPointF(2, 3), raio, QColor(0, 0, 0, 70), None)
    _poligono(p, [c + QPointF(math.cos(math.radians(k * 60 + 30)), math.sin(math.radians(k * 60 + 30))) * raio
                  for k in range(6)], CASCO)
    _circ(p, c, raio * 0.55, CASCO_CLA, CONTORNO, 1.2)
    for dx in (-3, 3):   # canos duplos
        _ret(p, QRectF(c.x() + dx - 2, c.y() - raio * 1.35, 4, raio * 1.1), METAL_ESC, 1, CONTORNO, 1)
    _circ(p, c, raio * 0.15, QColor("#ff3030"), None)


# ====================================================================== MÁGICO
ROXO = QColor("#7a4ac8")
ROXO_CLA = QColor("#b48aff")
ARCANO = QColor("#9fd8ff")


def d_caldeirao(p, r):
    c = r.center()
    raio = min(r.width(), r.height()) * 0.38
    _circ(p, c + QPointF(3, 4), raio, QColor(0, 0, 0, 80), None)
    _circ(p, c, raio, QColor("#2a2a2c"))
    g = QRadialGradient(c, raio * 0.8)
    g.setColorAt(0, QColor("#b8ff60"))
    g.setColorAt(1, QColor("#3a8a20"))
    _circ(p, c, raio * 0.78, QBrush(g), QColor("#18181a"), 1.5)
    rnd = _aleat(r)
    for _ in range(6):   # bolhas
        q = c + QPointF(rnd.uniform(-0.5, 0.5) * raio, rnd.uniform(-0.5, 0.5) * raio)
        _circ(p, q, rnd.uniform(1.5, 3.5), QColor(220, 255, 160, 200), QColor("#2a6a18"), 0.8)


def d_mesa_alquimia(p, r):
    a = r.adjusted(r.width() * 0.04, r.height() * 0.15, -r.width() * 0.04, -r.height() * 0.15)
    _sombra(p, a)
    _ret(p, a, MADEIRA_ESC, 3)
    rnd = _aleat(r)
    cores = ["#e84a6a", "#4ae8c8", "#e8c84a", "#8a6aff", "#6ae84a"]
    n = 5
    for k in range(n):   # frascos coloridos
        q = QPointF(a.left() + a.width() * (k + 0.5) / n, a.center().y() + rnd.uniform(-0.2, 0.2) * a.height())
        raio = a.height() * rnd.uniform(0.13, 0.2)
        _circ(p, q, raio, QColor(cores[k % len(cores)]), CONTORNO, 1)
        _circ(p, q + QPointF(-raio * 0.3, -raio * 0.3), raio * 0.25, QColor(255, 255, 255, 160), None)
    _ret(p, QRectF(a.left() + 4, a.top() + 3, a.width() * 0.2, a.height() * 0.22), QColor("#e8dcbc"), 1, CONTORNO, 0.8)


def d_pedestal_orbe(p, r):
    c = r.center()
    raio = r.width() * 0.32
    _poligono(p, [c + QPointF(math.cos(math.radians(k * 45 + 22.5)), math.sin(math.radians(k * 45 + 22.5))) * raio
                  for k in range(8)], PEDRA)
    _brilho(p, c, raio * 1.3, ROXO_CLA, 150)
    g = QRadialGradient(c - QPointF(raio * 0.2, raio * 0.2), raio * 0.6)
    g.setColorAt(0, QColor("#f0e8ff"))
    g.setColorAt(1, ROXO)
    _circ(p, c, raio * 0.5, QBrush(g), QColor("#3a1a6a"), 1.2)


def d_estante_grimorios(p, r):
    a = r.adjusted(r.width() * 0.02, r.height() * 0.2, -r.width() * 0.02, -r.height() * 0.2)
    _sombra(p, a)
    _ret(p, a, QColor("#3a2618"), 2)
    rnd = _aleat(r)
    x = a.left() + 4
    cores = ["#4a1a6a", "#1a3a6a", "#6a1a2a", "#1a5a4a", "#3a3a3a"]
    while x < a.right() - 7:
        larg = rnd.uniform(5, 10)
        livro = QRectF(x, a.top() + 3, min(larg, a.right() - 4 - x), a.height() - 6)
        _ret(p, livro, QColor(rnd.choice(cores)), 1, CONTORNO, 0.8)
        if rnd.random() < 0.35:   # runa brilhando na lombada
            _circ(p, livro.center(), 1.6, ARCANO, None)
        x += larg + 0.8
    _brilho(p, a.center(), a.width() * 0.4, ROXO_CLA, 40)


def d_portal(p, r):
    a = _m(r, 0.04)
    c, raio = a.center(), min(a.width(), a.height()) / 2
    _circ(p, c + QPointF(3, 4), raio, QColor(0, 0, 0, 70), None)
    for k in range(12):   # pedras do arco
        ang = math.radians(k * 30)
        q = c + QPointF(math.cos(ang), math.sin(ang)) * raio * 0.88
        _circ(p, q, raio * 0.15, PEDRA, PEDRA_ESC, 1.2)
    g = QRadialGradient(c, raio * 0.75)
    g.setColorAt(0, QColor("#ffffff"))
    g.setColorAt(0.35, QColor("#b48aff"))
    g.setColorAt(1, QColor("#2a0a5a"))
    _circ(p, c, raio * 0.72, QBrush(g), None)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(_caneta(QColor(230, 210, 255, 180), 1.5))
    caminho = QPainterPath(c)
    for k in range(70):   # espiral
        ang = k * 0.32
        caminho.lineTo(c + QPointF(math.cos(ang), math.sin(ang)) * raio * 0.66 * k / 70)
    p.drawPath(caminho)


def d_pedra_runica(p, r):
    c = r.center()
    raio = min(r.width(), r.height()) * 0.36
    pts = [c + QPointF(math.cos(math.radians(k * 60 + 10)), math.sin(math.radians(k * 60 + 10))) * raio *
           (1 if k % 2 else 0.86) for k in range(6)]
    _poligono(p, [q + QPointF(3, 4) for q in pts], QColor(0, 0, 0, 70), None)
    _poligono(p, pts, PEDRA_ESC)
    _brilho(p, c, raio, ARCANO, 120)
    p.setPen(_caneta(QColor("#c8f0ff"), 2))
    p.drawLine(c + QPointF(0, -raio * 0.5), c + QPointF(0, raio * 0.5))
    p.drawLine(c + QPointF(0, -raio * 0.2), c + QPointF(raio * 0.35, -raio * 0.45))
    p.drawLine(c + QPointF(0, raio * 0.05), c + QPointF(raio * 0.35, -raio * 0.2))


def d_cogumelos(p, r):
    rnd = _aleat(r)
    a = _m(r, 0.08)
    for k in range(5):
        raio = a.width() * rnd.uniform(0.14, 0.24)
        q = QPointF(rnd.uniform(a.left() + raio, a.right() - raio), rnd.uniform(a.top() + raio, a.bottom() - raio))
        _circ(p, q + QPointF(3, 4), raio, QColor(0, 0, 0, 70), None)
        _brilho(p, q, raio * 1.5, QColor("#5affd8"), 70)
        _circ(p, q, raio, QColor(rnd.choice(["#3a8aa8", "#6a4ab8", "#2a9a8a"])))
        for _ in range(4):   # pintas brilhantes
            d = QPointF(rnd.uniform(-0.55, 0.55), rnd.uniform(-0.55, 0.55)) * raio
            _circ(p, q + d, raio * 0.12, QColor("#c8fff0"), None)


def d_esfera_armilar(p, r):
    c = r.center()
    raio = r.width() * 0.36
    _circ(p, c + QPointF(2, 3), raio, QColor(0, 0, 0, 60), None)
    p.setBrush(Qt.BrushStyle.NoBrush)
    for k, ang in enumerate((0, 60, 120)):
        p.save()
        p.translate(c)
        p.rotate(ang)
        p.setPen(_caneta(OURO if k != 1 else QColor("#a07830"), 2.2))
        p.drawEllipse(QPointF(0, 0), raio, raio * 0.42)
        p.restore()
    p.setPen(_caneta(OURO, 2.2))
    p.drawEllipse(c, raio, raio)
    _circ(p, c, raio * 0.18, QColor("#3a6ab8"), CONTORNO, 1)


def d_telescopio(p, r):
    c = r.center()
    _circ(p, c + QPointF(2, 3), r.width() * 0.22, QColor(0, 0, 0, 60), None)
    for ang in (90, 210, 330):   # tripé
        q = c + QPointF(math.cos(math.radians(ang)), math.sin(math.radians(ang))) * r.width() * 0.28
        _linha(p, c, q, MADEIRA_ESC, 2.5)
    p.save()
    p.translate(c)
    p.rotate(-35)
    tubo = QRectF(-r.width() * 0.08, -r.height() * 0.42, r.width() * 0.16, r.height() * 0.6)
    _ret(p, tubo, OURO, 3)
    _ret(p, QRectF(tubo.left() - 2, tubo.top(), tubo.width() + 4, 5), QColor("#a07830"), 2, CONTORNO, 1)
    p.restore()


def d_fonte_magica(p, r):
    a = _m(r, 0.05)
    c, raio = a.center(), min(a.width(), a.height()) / 2
    _circ(p, c + QPointF(3, 4), raio, QColor(0, 0, 0, 70), None)
    _poligono(p, [c + QPointF(math.cos(math.radians(k * 45 + 22.5)), math.sin(math.radians(k * 45 + 22.5))) * raio
                  for k in range(8)], PEDRA)
    g = QRadialGradient(c, raio * 0.8)
    g.setColorAt(0, QColor("#e8f8ff"))
    g.setColorAt(1, QColor("#3a8ad8"))
    _circ(p, c, raio * 0.76, QBrush(g), PEDRA_ESC, 1.5)
    _brilho(p, c, raio * 0.8, ARCANO, 120)
    _circ(p, c, raio * 0.2, PEDRA, CONTORNO, 1.2)   # pedestal do meio
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(_caneta(QColor(255, 255, 255, 130), 1.2))
    for k in (0.35, 0.5, 0.62):
        p.drawEllipse(c, raio * k, raio * k)


# ====================================================================== TERROR
OSSO = QColor("#d8ceb4")
SANGUE = QColor("#6a0a10")


def d_forca(p, r):
    a = _m(r, 0.06)
    _sombra(p, a, 2)
    _ret(p, a, MADEIRA_ESC, 2)
    _tabuas(p, a, 4, QColor("#2a1a10"))
    alcapao = QRectF(a.center().x() - a.width() * 0.16, a.center().y() - a.height() * 0.16, a.width() * 0.32,
                     a.height() * 0.32)
    _ret(p, alcapao, QColor("#1a120a"), 1, CONTORNO, 1.5)
    # viga por cima e a corda com o laço
    _ret(p, QRectF(a.left() + a.width() * 0.1, a.center().y() - 4, a.width() * 0.6, 8), MADEIRA, 2, CONTORNO, 1.5)
    _circ(p, QPointF(a.left() + a.width() * 0.1, a.center().y()), 6, MADEIRA, CONTORNO, 1.5)
    p.setPen(_caneta(QColor("#a08a5a"), 2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(alcapao.center(), alcapao.width() * 0.18, alcapao.width() * 0.18)


def d_jaula(p, r):
    a = _m(r, 0.1)
    _sombra(p, a, 2)
    _ret(p, a, QColor(0, 0, 0, 40), 2, METAL_ESC, 2.5)
    p.setPen(_caneta(METAL_ESC, 2))
    for k in range(1, 5):
        x = a.left() + a.width() * k / 5
        p.drawLine(QPointF(x, a.top()), QPointF(x, a.bottom()))
    _linha(p, QPointF(a.left(), a.center().y()), QPointF(a.right(), a.center().y()), METAL_ESC, 2)
    _circ(p, QPointF(a.right() - 4, a.center().y()), 3, OURO, CONTORNO, 1)   # cadeado


def d_mesa_tortura(p, r):
    a = r.adjusted(r.width() * 0.16, r.height() * 0.04, -r.width() * 0.16, -r.height() * 0.04)
    _sombra(p, a)
    _ret(p, a, MADEIRA_ESC, 2)
    _tabuas(p, a, 6, QColor("#2a1a10"))
    for frac in (0.12, 0.88):   # rolos e correntes
        y = a.top() + a.height() * frac
        _ret(p, QRectF(a.left() - 3, y - 4, a.width() + 6, 8), METAL_ESC, 3, CONTORNO, 1.2)
    rnd = _aleat(r)
    for _ in range(4):   # manchas
        q = QPointF(rnd.uniform(a.left() + 4, a.right() - 4), rnd.uniform(a.top() + 10, a.bottom() - 10))
        _circ(p, q, rnd.uniform(2, 5), QColor(110, 10, 16, 170), None)


def d_cadaver(p, r):
    c = r.center()
    larg, alt = r.width() * 0.5, r.height() * 0.8
    _circ(p, c + QPointF(4, 6), larg * 0.7, QColor(90, 8, 12, 150), None)   # poça
    corpo = QRectF(c.x() - larg * 0.32, c.y() - alt * 0.24, larg * 0.64, alt * 0.5)
    _ret(p, corpo, QColor("#5a5248"), 6, CONTORNO, 1.5)                      # roupa
    _circ(p, QPointF(c.x(), corpo.top() - larg * 0.18), larg * 0.2, QColor("#a89c88"), CONTORNO, 1.5)   # cabeça
    for dx in (-1, 1):
        _ret(p, QRectF(c.x() + dx * larg * 0.42 - 3, corpo.top() + 3, 6, alt * 0.36), QColor("#a89c88"), 3, CONTORNO, 1)
        _ret(p, QRectF(c.x() + dx * larg * 0.16 - 4, corpo.bottom() - 2, 8, alt * 0.32), QColor("#3a3430"), 3,
             CONTORNO, 1)


def d_teia_gigante(p, r):
    c = r.center()
    raio = min(r.width(), r.height()) * 0.48
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(_caneta(QColor(235, 235, 235, 190), 1.3))
    pontas = [c + QPointF(math.cos(math.radians(k * 40 + 10)), math.sin(math.radians(k * 40 + 10))) * raio
              for k in range(9)]
    for q in pontas:
        p.drawLine(c, q)
    for f in (0.18, 0.34, 0.5, 0.66, 0.82):
        anel = QPainterPath(c + (pontas[0] - c) * f)
        for q in pontas[1:] + pontas[:1]:
            anel.lineTo(c + (q - c) * f)
        p.drawPath(anel)
    _circ(p, c + QPointF(raio * 0.2, -raio * 0.1), raio * 0.08, QColor("#1a1a1a"), None)   # aranha
    for k in range(4):
        for dx in (-1, 1):
            _linha(p, c + QPointF(raio * 0.2, -raio * 0.1),
                   c + QPointF(raio * 0.2 + dx * raio * 0.14, -raio * 0.1 + (k - 1.5) * raio * 0.06), QColor("#1a1a1a"), 1)


def d_espelho_quebrado(p, r):
    a = r.adjusted(r.width() * 0.22, r.height() * 0.12, -r.width() * 0.22, -r.height() * 0.12)
    _sombra(p, a, a.width() * 0.4)
    _ret(p, a, QColor("#4a3a20"), a.width() * 0.45)
    vidro = a.adjusted(4, 4, -4, -4)
    _ret(p, vidro, QColor("#8aa0a8"), vidro.width() * 0.45, None)
    c = vidro.center() + QPointF(vidro.width() * 0.1, -vidro.height() * 0.15)
    p.setPen(_caneta(QColor(240, 250, 255, 220), 1.2))
    for ang in (20, 80, 150, 210, 260, 320):   # rachaduras saindo do ponto de impacto
        d = QPointF(math.cos(math.radians(ang)), math.sin(math.radians(ang))) * vidro.height() * 0.4
        p.drawLine(c, c + d)


def d_boneca(p, r):
    c = r.center()
    s = min(r.width(), r.height())
    _circ(p, c + QPointF(2, 3), s * 0.18, QColor(0, 0, 0, 60), None)
    vestido = [QPointF(c.x(), c.y() - s * 0.08), QPointF(c.x() + s * 0.18, c.y() + s * 0.26),
               QPointF(c.x() - s * 0.18, c.y() + s * 0.26)]
    _poligono(p, vestido, QColor("#7a3a4a"), CONTORNO, 1.2)
    _circ(p, QPointF(c.x(), c.y() - s * 0.16), s * 0.12, QColor("#e8dcd0"), CONTORNO, 1.2)
    _circ(p, QPointF(c.x() - s * 0.045, c.y() - s * 0.17), s * 0.025, CONTORNO, None)   # um olho só…
    p.setPen(_caneta(CONTORNO, 1))
    p.drawLine(QPointF(c.x() + s * 0.02, c.y() - s * 0.19), QPointF(c.x() + s * 0.07, c.y() - s * 0.15))
    p.drawLine(QPointF(c.x() + s * 0.07, c.y() - s * 0.19), QPointF(c.x() + s * 0.02, c.y() - s * 0.15))
    p.setPen(_caneta(QColor("#3a2410"), 2))   # cabelo
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(c.x() - s * 0.13, c.y() - s * 0.29, s * 0.26, s * 0.24), 20 * 16, 140 * 16)


def d_ossos(p, r):
    rnd = _aleat(r)
    a = _m(r, 0.14)
    for _ in range(7):
        q = QPointF(rnd.uniform(a.left(), a.right()), rnd.uniform(a.top(), a.bottom()))
        ang = rnd.uniform(0, 180)
        comp = a.width() * rnd.uniform(0.25, 0.45)
        d = QPointF(math.cos(math.radians(ang)), math.sin(math.radians(ang))) * comp / 2
        _linha(p, q - d, q + d, OSSO, 3.2)
        for ponta in (q - d, q + d):
            _circ(p, ponta, 2.6, OSSO, QColor("#7a7058"), 0.8)
    _circ(p, a.center(), a.width() * 0.16, OSSO, QColor("#7a7058"), 1.2)   # crânio
    for dx in (-1, 1):
        _circ(p, a.center() + QPointF(dx * a.width() * 0.06, -a.width() * 0.02), a.width() * 0.04, CONTORNO, None)


def d_velas_ritual(p, r):
    a = _m(r, 0.06)
    c, raio = a.center(), min(a.width(), a.height()) * 0.42
    p.setPen(_caneta(SANGUE, 2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(c, raio * 0.9, raio * 0.9)
    pts = [c + QPointF(math.cos(math.radians(-90 + k * 144)), math.sin(math.radians(-90 + k * 144))) * raio * 0.9
           for k in range(5)]
    p.drawPolygon(QPolygonF(pts))
    for k in range(5):
        q = c + QPointF(math.cos(math.radians(-90 + k * 72)), math.sin(math.radians(-90 + k * 72))) * raio * 1.05
        _brilho(p, q, raio * 0.22, QColor("#ffc070"), 170)
        _circ(p, q, raio * 0.07, QColor("#e8e0c8"), CONTORNO, 1)
        _circ(p, q, raio * 0.03, QColor("#ffd060"), None)


def d_poca_sangue(p, r):
    c = r.center()
    rnd = _aleat(r)
    raio = min(r.width(), r.height()) * 0.32
    caminho = QPainterPath()
    pts = []
    for k in range(14):
        ang = math.radians(k * 360 / 14)
        pts.append(c + QPointF(math.cos(ang), math.sin(ang)) * raio * rnd.uniform(0.7, 1.15))
    caminho.moveTo(pts[0])
    for k in range(len(pts)):
        a, b = pts[k], pts[(k + 1) % len(pts)]
        caminho.quadTo(a, (a + b) / 2)
    caminho.closeSubpath()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(90, 6, 12, 220))
    p.drawPath(caminho)
    _circ(p, c + QPointF(-raio * 0.25, -raio * 0.25), raio * 0.15, QColor(255, 120, 120, 70), None)   # reflexo
    for _ in range(4):   # respingos
        ang = rnd.uniform(0, 2 * math.pi)
        _circ(p, c + QPointF(math.cos(ang), math.sin(ang)) * raio * rnd.uniform(1.25, 1.5), rnd.uniform(1.5, 3),
              QColor(90, 6, 12, 220), None)


# ====================================================================== STEAMPUNK (v0.59)
LATAO = QColor("#c9a24a")
LATAO_ESC = QColor("#7a5a22")
COBRE = QColor("#b8653a")
COBRE_ESC = QColor("#6a3418")
PATINA = QColor("#5e8a7a")


def _engrenagem(p, c, raio, dentes, cor, borda=CONTORNO):
    pts = []
    for k in range(dentes * 2):
        a = k * math.pi / dentes
        r = raio * (1.0 if k % 2 == 0 else 0.82)
        for da in (-0.3, 0.3):
            aa = a + da * math.pi / dentes
            pts.append(c + QPointF(math.cos(aa), math.sin(aa)) * r)
    _poligono(p, pts, cor, borda, 1.2)
    _circ(p, c, raio * 0.28, QColor("#2a2018"), borda, 1)


def d_caldeira(p, r):
    a = _m(r, 0.06)
    c, raio = a.center(), min(a.width(), a.height()) * 0.46
    _circ(p, c + QPointF(3, 4), raio, QColor(0, 0, 0, 70), None)
    g = QRadialGradient(c - QPointF(raio * 0.3, raio * 0.3), raio * 1.2)
    g.setColorAt(0, QColor("#e89a68"))
    g.setColorAt(1, COBRE_ESC)
    _circ(p, c, raio, QBrush(g))
    for k in range(12):                                                  # rebites em volta
        q = c + QPointF(math.cos(k * math.pi / 6), math.sin(k * math.pi / 6)) * raio * 0.86
        _circ(p, q, 2.2, LATAO, CONTORNO, 0.8)
    portinha = QRectF(c.x() - raio * 0.3, c.y() + raio * 0.1, raio * 0.6, raio * 0.5)
    _ret(p, portinha, QColor("#2a1a10"), 3)
    _brilho(p, portinha.center(), raio * 0.5, QColor("#ff8a30"), 170)
    _circ(p, c + QPointF(raio * 0.35, -raio * 0.35), raio * 0.16, LATAO, CONTORNO, 1.2)   # manômetro
    _linha(p, c + QPointF(raio * 0.35, -raio * 0.35), c + QPointF(raio * 0.42, -raio * 0.44), CONTORNO, 1.2)


def d_bancada_engrenagens(p, r):
    a = r.adjusted(r.width() * 0.04, r.height() * 0.12, -r.width() * 0.04, -r.height() * 0.12)
    _sombra(p, a)
    _ret(p, a, MADEIRA, 3)
    _tabuas(p, a, 3)
    rnd = _aleat(r)
    for k in range(4):
        c = QPointF(a.left() + a.width() * (0.18 + k * 0.22), a.center().y() + rnd.uniform(-6, 6))
        _engrenagem(p, c, a.height() * rnd.uniform(0.18, 0.3), rnd.choice([8, 10, 12]), LATAO if k % 2 else COBRE)
    _ret(p, QRectF(a.right() - a.width() * 0.12, a.top() + 4, a.width() * 0.08, a.height() * 0.3), METAL_ESC, 2)   # torno


def d_automato(p, r):
    c = r.center()
    s = min(r.width(), r.height())
    _circ(p, c + QPointF(3, 4), s * 0.36, QColor(0, 0, 0, 70), None)
    _ret(p, QRectF(c.x() - s * 0.3, c.y() - s * 0.2, s * 0.6, s * 0.42), LATAO, 6)      # ombros/tronco
    _circ(p, c, s * 0.2, LATAO_ESC, CONTORNO, 1.5)                                   # cabeça
    for dx in (-1, 1):
        _circ(p, c + QPointF(dx * s * 0.07, -s * 0.03), s * 0.045, QColor("#ffb040"), CONTORNO, 1)   # olhos
    _engrenagem(p, c + QPointF(0, s * 0.14), s * 0.06, 8, COBRE)


def d_cano_valvula(p, r):
    a = r.adjusted(r.width() * 0.02, r.height() * 0.36, -r.width() * 0.02, -r.height() * 0.36)
    _sombra(p, a, 3)
    g = QLinearGradient(a.topLeft(), a.bottomLeft())
    g.setColorAt(0, QColor("#e09060"))
    g.setColorAt(0.5, COBRE)
    g.setColorAt(1, COBRE_ESC)
    _ret(p, a, QBrush(g), a.height() / 2)
    for f in (0.15, 0.85):
        _ret(p, QRectF(a.left() + a.width() * f - 4, a.top() - 3, 8, a.height() + 6), LATAO, 2, CONTORNO, 1)
    c = a.center()
    _circ(p, c, a.height() * 1.0, QColor("#8a1a10"), CONTORNO, 1.5)                  # volante da válvula
    for k in range(4):
        _linha(p, c, c + QPointF(math.cos(k * math.pi / 2 + 0.4), math.sin(k * math.pi / 2 + 0.4)) * a.height() * 0.9,
               QColor("#4a0a06"), 2)


def d_relogio_pendulo(p, r):
    a = r.adjusted(r.width() * 0.2, r.height() * 0.1, -r.width() * 0.2, -r.height() * 0.1)
    _sombra(p, a)
    _ret(p, a, MADEIRA_ESC, 3)
    _circ(p, QPointF(a.center().x(), a.top() + a.width() * 0.5), a.width() * 0.4, QColor("#f0e4c4"), LATAO_ESC, 2)
    c = QPointF(a.center().x(), a.top() + a.width() * 0.5)
    _linha(p, c, c + QPointF(0, -a.width() * 0.3), CONTORNO, 1.5)
    _linha(p, c, c + QPointF(a.width() * 0.2, 0), CONTORNO, 1.5)
    _circ(p, QPointF(a.center().x(), a.bottom() - a.height() * 0.2), a.width() * 0.18, LATAO, CONTORNO, 1.2)   # pêndulo


def d_lampiao_gas(p, r):
    c = r.center()
    s = min(r.width(), r.height())
    _brilho(p, c, s * 0.5, QColor("#ffc070"), 160)
    _circ(p, c, s * 0.18, LATAO, CONTORNO, 1.5)
    _circ(p, c, s * 0.1, QColor("#fff0c0"), None)
    for k in range(4):
        _linha(p, c + QPointF(math.cos(k * math.pi / 2), math.sin(k * math.pi / 2)) * s * 0.18,
               c + QPointF(math.cos(k * math.pi / 2), math.sin(k * math.pi / 2)) * s * 0.26, LATAO_ESC, 2)


def d_bau_rebites(p, r):
    a = _m(r, 0.12)
    _sombra(p, a)
    _ret(p, a, QColor("#5a3a20"), 3)
    _tabuas(p, a, 3, QColor("#3a2412"))
    for x in (a.left() + a.width() * 0.2, a.right() - a.width() * 0.2):          # cintas de latão
        _ret(p, QRectF(x - 5, a.top(), 10, a.height()), LATAO, 1, CONTORNO, 1)
        for k in range(4):
            _circ(p, QPointF(x, a.top() + a.height() * (0.15 + k * 0.23)), 1.8, LATAO_ESC, None)
    _ret(p, QRectF(a.center().x() - 7, a.center().y() - 6, 14, 12), LATAO, 2, CONTORNO, 1.2)   # fechadura


def d_globo_mundi(p, r):
    c = r.center()
    s = min(r.width(), r.height())
    _circ(p, c + QPointF(3, 4), s * 0.38, QColor(0, 0, 0, 70), None)
    _circ(p, c, s * 0.4, LATAO_ESC, CONTORNO, 1.5)                                   # o aro
    g = QRadialGradient(c - QPointF(s * 0.1, s * 0.1), s * 0.36)
    g.setColorAt(0, QColor("#c8d8b8"))
    g.setColorAt(1, QColor("#5a7a8a"))
    _circ(p, c, s * 0.32, QBrush(g), CONTORNO, 1.2)
    rnd = _aleat(r)
    for _ in range(4):                                                               # continentes
        q = c + QPointF(rnd.uniform(-1, 1), rnd.uniform(-1, 1)) * s * 0.16
        _circ(p, q, s * rnd.uniform(0.05, 0.1), QColor("#a89060"), None)


def d_telescopio_latao(p, r):
    a = r.adjusted(r.width() * 0.08, r.height() * 0.3, -r.width() * 0.08, -r.height() * 0.3)
    p.save()
    p.translate(r.center())
    p.rotate(-30)
    p.translate(-r.center())
    _sombra(p, a, 6)
    tubo = QRectF(a.left(), a.center().y() - a.height() * 0.3, a.width() * 0.85, a.height() * 0.6)
    _ret(p, tubo, LATAO, 5)
    _ret(p, QRectF(tubo.right() - 4, a.top(), a.width() * 0.15, a.height()), LATAO_ESC, 4)   # a boca larga
    for f in (0.3, 0.6):
        _ret(p, QRectF(tubo.left() + tubo.width() * f, tubo.top() - 2, 6, tubo.height() + 4), COBRE, 2, CONTORNO, 1)
    p.restore()
    for k in range(3):                                                              # tripé
        ang = math.radians(90 + k * 120)
        _linha(p, r.center(), r.center() + QPointF(math.cos(ang), math.sin(ang)) * r.width() * 0.35, MADEIRA_ESC, 3)


def d_balao_carga(p, r):
    c = r.center()
    s = min(r.width(), r.height())
    _circ(p, c + QPointF(6, 8), s * 0.44, QColor(0, 0, 0, 60), None)
    g = QRadialGradient(c - QPointF(s * 0.12, s * 0.12), s * 0.5)
    g.setColorAt(0, QColor("#e8d8b8"))
    g.setColorAt(1, QColor("#8a6a48"))
    _circ(p, c, s * 0.44, QBrush(g))
    p.setPen(_caneta(QColor("#6a4a2a"), 1.2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for k in range(6):                                                              # gomos
        p.drawLine(c, c + QPointF(math.cos(k * math.pi / 3), math.sin(k * math.pi / 3)) * s * 0.44)
    _ret(p, QRectF(c.x() - s * 0.12, c.y() - s * 0.1, s * 0.24, s * 0.2), MADEIRA, 2)   # cesto


# ====================================================================== PÓS-APOCALÍPTICO (v0.59)
FERRUGEM = QColor("#8a4a24")
FERRUGEM_ESC = QColor("#4a2210")


def d_carro_ferrugem(p, r):
    a = r.adjusted(r.width() * 0.08, r.height() * 0.04, -r.width() * 0.08, -r.height() * 0.04)
    _sombra(p, a, 10)
    _ret(p, a, FERRUGEM, 10)
    rnd = _aleat(r)
    for _ in range(10):                                                             # manchas de ferrugem
        q = QPointF(rnd.uniform(a.left() + 4, a.right() - 4), rnd.uniform(a.top() + 4, a.bottom() - 4))
        _circ(p, q, rnd.uniform(3, 9), FERRUGEM_ESC, None)
    teto = QRectF(a.left() + a.width() * 0.12, a.top() + a.height() * 0.3, a.width() * 0.76, a.height() * 0.38)
    _ret(p, teto, QColor("#6a4028"), 6, CONTORNO, 1.5)
    _ret(p, QRectF(teto.left() + 3, teto.top() - a.height() * 0.08, teto.width() - 6, a.height() * 0.08),
         QColor("#1a1a18"), 2, CONTORNO, 1)                                         # para-brisa quebrado
    _linha(p, QPointF(teto.left() + 6, teto.top() - a.height() * 0.07), QPointF(teto.center().x(), teto.top() - 2),
           QColor(200, 200, 200, 120), 1)
    _circ(p, QPointF(a.right() - a.width() * 0.3, a.bottom() - a.height() * 0.15), a.width() * 0.12,
          QColor(60, 100, 40, 200), None)                                           # mato saindo


def d_barricada(p, r):
    a = r.adjusted(r.width() * 0.02, r.height() * 0.25, -r.width() * 0.02, -r.height() * 0.25)
    _sombra(p, a, 2)
    rnd = _aleat(r)
    for k in range(3):                                                              # tábuas cruzadas
        y = a.top() + a.height() * (0.2 + k * 0.3)
        _ret(p, QRectF(a.left(), y - 5, a.width(), 10), MADEIRA if k % 2 else MADEIRA_ESC, 2)
    for x in (a.left() + a.width() * 0.25, a.right() - a.width() * 0.25):
        _poligono(p, [QPointF(x - 6, a.top()), QPointF(x + 6, a.top()), QPointF(x + 14, a.bottom()),
                      QPointF(x + 2, a.bottom())], METAL_ESC, CONTORNO, 1.2)
    for _ in range(6):
        _circ(p, QPointF(rnd.uniform(a.left(), a.right()), rnd.uniform(a.top(), a.bottom())), 2, QColor("#8a8a80"), None)


def d_tambor_fogo(p, r):
    c = r.center()
    s = min(r.width(), r.height())
    _circ(p, c + QPointF(3, 4), s * 0.36, QColor(0, 0, 0, 70), None)
    _circ(p, c, s * 0.36, FERRUGEM, CONTORNO, 2)
    _brilho(p, c, s * 0.42, QColor("#ff8a30"), 190)
    g = QRadialGradient(c, s * 0.26)
    g.setColorAt(0, QColor("#fff0a0"))
    g.setColorAt(0.5, QColor("#ff8a20"))
    g.setColorAt(1, QColor("#5a1a08"))
    _circ(p, c, s * 0.26, QBrush(g), None)


def d_saco_areia(p, r):
    a = r.adjusted(r.width() * 0.04, r.height() * 0.2, -r.width() * 0.04, -r.height() * 0.2)
    _sombra(p, a, 8)
    n = max(2, round(a.width() / (CELULA * 0.45)))
    for lin in range(2):
        for k in range(n):
            w = a.width() / n
            q = QRectF(a.left() + k * w + (w / 2 if lin else 0) * 0.5, a.top() + lin * a.height() * 0.5,
                       w * 0.96, a.height() * 0.5)
            _ret(p, q, QColor("#b8a478") if (k + lin) % 2 else QColor("#a89468"), q.height() * 0.4, CONTORNO, 1.2)


def d_placa_perigo(p, r):
    c = r.center()
    s = min(r.width(), r.height())
    tri = [c + QPointF(0, -s * 0.36), c + QPointF(s * 0.38, s * 0.3), c + QPointF(-s * 0.38, s * 0.3)]
    _poligono(p, [q + QPointF(3, 4) for q in tri], QColor(0, 0, 0, 70), None)
    _poligono(p, tri, QColor("#e8c040"), CONTORNO, 2.5)
    _ret(p, QRectF(c.x() - s * 0.03, c.y() - s * 0.16, s * 0.06, s * 0.24), CONTORNO, 1, None)   # "!"
    _circ(p, c + QPointF(0, s * 0.17), s * 0.035, CONTORNO, None)


def d_prateleira_saqueada(p, r):
    a = r.adjusted(r.width() * 0.04, r.height() * 0.25, -r.width() * 0.04, -r.height() * 0.25)
    _sombra(p, a, 2)
    _ret(p, a, METAL_ESC, 2)
    rnd = _aleat(r)
    for _ in range(5):                                                              # o que sobrou
        q = QPointF(rnd.uniform(a.left() + 6, a.right() - 6), rnd.uniform(a.top() + 4, a.bottom() - 4))
        _ret(p, QRectF(q.x() - 4, q.y() - 3, 8, 6), rnd.choice([QColor("#a83a2a"), QColor("#c8a840"), QColor("#8a8a80")]), 1, CONTORNO, 0.8)
    for _ in range(3):                                                              # coisas caídas no chão
        q = QPointF(rnd.uniform(r.left() + 6, r.right() - 6), rnd.uniform(a.bottom() + 4, r.bottom() - 4))
        _circ(p, q, 3, QColor("#8a8a80"), CONTORNO, 0.8)


def d_galao(p, r):
    a = _m(r, 0.26)
    _sombra(p, a, 4)
    _ret(p, a, QColor("#a8302a"), 5)
    _ret(p, QRectF(a.left() + a.width() * 0.15, a.top() + 3, a.width() * 0.4, a.height() * 0.18), QColor("#6a1a14"), 3)   # alça
    _circ(p, QPointF(a.right() - a.width() * 0.2, a.top() + a.height() * 0.15), a.width() * 0.1, QColor("#e8c040"), CONTORNO, 1)


def d_pneu(p, r):
    c = r.center()
    s = min(r.width(), r.height())
    _circ(p, c + QPointF(3, 4), s * 0.36, QColor(0, 0, 0, 70), None)
    _circ(p, c, s * 0.36, QColor("#1c1c1a"), CONTORNO, 2)
    _circ(p, c, s * 0.18, QColor("#3a3a34"), CONTORNO, 1.5)
    p.setPen(_caneta(QColor("#3a3a36"), 2))
    for k in range(12):                                                             # banda de rodagem
        a = k * math.pi / 6
        p.drawLine(c + QPointF(math.cos(a), math.sin(a)) * s * 0.28, c + QPointF(math.cos(a), math.sin(a)) * s * 0.35)


def d_cerca_arame(p, r):
    a = r.adjusted(0, r.height() * 0.42, 0, -r.height() * 0.42)
    p.setPen(_caneta(QColor("#9a9a90"), 1.2))
    passo = 6
    x = a.left()
    while x < a.right():                                                            # alambrado em zigue-zague
        p.drawLine(QPointF(x, a.top()), QPointF(x + passo, a.bottom()))
        p.drawLine(QPointF(x + passo, a.bottom()), QPointF(x + passo * 2, a.top()))
        x += passo * 2
    n = max(2, round(a.width() / CELULA) + 1)
    for k in range(n):                                                              # postes
        _circ(p, QPointF(a.left() + 4 + (a.width() - 8) * k / (n - 1), a.center().y()), 4, METAL_ESC, CONTORNO, 1.2)


def d_zumbi_caido(p, r):
    c = r.center()
    larg, alt = r.width() * 0.5, r.height() * 0.8
    _circ(p, c + QPointF(4, 6), larg * 0.6, QColor(50, 60, 30, 120), None)          # mancha escura
    corpo = QRectF(c.x() - larg * 0.32, c.y() - alt * 0.24, larg * 0.64, alt * 0.5)
    _ret(p, corpo, QColor("#4a4a3a"), 6, CONTORNO, 1.5)                              # roupa rasgada
    _circ(p, QPointF(c.x(), corpo.top() - larg * 0.18), larg * 0.2, QColor("#7a8a5a"), CONTORNO, 1.5)   # pele esverdeada
    for dx in (-1, 1):
        _ret(p, QRectF(c.x() + dx * larg * 0.44 - 3, corpo.top() - alt * 0.1, 6, alt * 0.36), QColor("#7a8a5a"), 3, CONTORNO, 1)
        _ret(p, QRectF(c.x() + dx * larg * 0.16 - 4, corpo.bottom() - 2, 8, alt * 0.32), QColor("#2a2a24"), 3, CONTORNO, 1)
    _ret(p, QRectF(corpo.right() - 10, corpo.center().y(), 12, 9), QColor("#6a5030"), 2, CONTORNO, 1)   # bolsa (dá pra revistar)


# ====================================================================== catálogo dos temas
# chave: (nome, categoria, largura, altura, desenho, extras) — mesmo formato de props.CATALOGO
CATALOGO_TEMAS = {
    # medieval
    "trono": ("Trono", "Móveis", 2, 2, d_trono, {}),
    "forja": ("Forja", "Luzes", 2, 2, d_forja, {"luz": "braseiro"}),
    "bigorna": ("Bigorna", "Cenário", 1, 1, d_bigorna, {"movel": True}),
    "carroca": ("Carroça", "Cenário", 2, 3, d_carroca, {"interativo": True}),
    "tenda": ("Tenda", "Cenário", 3, 3, d_tenda, {"bloqueia": True}),
    "mesa_banquete": ("Mesa de banquete", "Móveis", 4, 2, d_mesa_banquete, {}),
    "estandarte": ("Estandarte", "Cenário", 1, 1, d_estandarte, {}),
    "suporte_armas": ("Suporte de armas", "Móveis", 2, 1, d_suporte_armas, {"interativo": True}),
    "feno": ("Fardo de feno", "Cenário", 1, 1, d_feno, {"movel": True}),
    "tocheiro": ("Tocheiro", "Luzes", 1, 1, d_tocheiro, {"luz": "tocha"}),
    # moderno
    "geladeira": ("Geladeira", "Móveis", 1, 1, d_geladeira, {"interativo": True}),
    "fogao": ("Fogão", "Móveis", 1, 1, d_fogao, {}),
    "pia": ("Pia", "Móveis", 1, 1, d_pia, {}),
    "vaso_sanitario": ("Vaso sanitário", "Móveis", 1, 1, d_vaso_sanitario, {}),
    "banheira": ("Banheira", "Móveis", 1, 2, d_banheira, {}),
    "tv": ("TV", "Móveis", 2, 1, d_tv, {"luz": "terminal"}),
    "escrivaninha": ("Escrivaninha", "Móveis", 2, 1, d_escrivaninha, {"interativo": True}),
    "moto": ("Moto", "Cenário", 1, 2, d_moto, {"interativo": True}),
    "cacamba": ("Caçamba de lixo", "Recipientes", 2, 1, d_cacamba, {"interativo": True}),
    "maquina_venda": ("Máquina de lanches", "Móveis", 1, 1, d_maquina_venda, {"interativo": True, "luz": "terminal"}),
    # futurista
    "holomesa": ("Mesa holográfica", "Tecnologia", 2, 2, d_holomesa, {"interativo": True, "luz": "neon"}),
    "robo": ("Robô", "Tecnologia", 1, 1, d_robo, {"movel": True}),
    "drone": ("Drone", "Tecnologia", 1, 1, d_drone, {"movel": True}),
    "console": ("Console de controle", "Tecnologia", 2, 1, d_console, {"interativo": True, "luz": "terminal"}),
    # (objeto que ilumina não pode bloquear a visão: a luz ficaria presa dentro dele)
    "reator": ("Reator", "Tecnologia", 2, 2, d_reator, {"luz": "neon"}),
    "tubo_estase": ("Tubo de estase", "Tecnologia", 1, 1, d_tubo_estase, {"interativo": True, "luz": "cristal"}),
    "nave": ("Nave pequena", "Cenário", 3, 3, d_nave, {"interativo": True}),
    "conteiner": ("Contêiner", "Recipientes", 2, 1, d_conteiner, {"interativo": True}),
    "teleporte": ("Plataforma de teleporte", "Tecnologia", 2, 2, d_teleporte, {"luz": "neon"}),
    "torreta": ("Torreta", "Tecnologia", 1, 1, d_torreta, {}),
    # mágico
    "caldeirao": ("Caldeirão", "Magia", 1, 1, d_caldeirao, {"interativo": True}),
    "mesa_alquimia": ("Mesa de alquimia", "Magia", 2, 1, d_mesa_alquimia, {"interativo": True}),
    "pedestal_orbe": ("Pedestal com orbe", "Magia", 1, 1, d_pedestal_orbe, {"interativo": True, "luz": "cristal"}),
    "estante_grimorios": ("Estante de grimórios", "Magia", 2, 1, d_estante_grimorios,
                          {"bloqueia": True, "interativo": True}),
    "portal": ("Portal mágico", "Magia", 2, 2, d_portal, {"luz": "cristal"}),
    "pedra_runica": ("Pedra rúnica", "Magia", 1, 1, d_pedra_runica, {"luz": "cristal"}),
    "cogumelos": ("Cogumelos brilhantes", "Cenário", 2, 2, d_cogumelos, {"luz": "cristal"}),
    "esfera_armilar": ("Esfera armilar", "Magia", 1, 1, d_esfera_armilar, {}),
    "telescopio": ("Telescópio", "Magia", 1, 1, d_telescopio, {}),
    "fonte_magica": ("Fonte mágica", "Magia", 2, 2, d_fonte_magica, {"interativo": True, "luz": "cristal"}),
    # terror
    "forca": ("Forca", "Cenário", 2, 2, d_forca, {}),
    "jaula": ("Jaula", "Recipientes", 1, 1, d_jaula, {"interativo": True}),
    "mesa_tortura": ("Mesa de tortura", "Móveis", 1, 2, d_mesa_tortura, {}),
    "cadaver": ("Cadáver", "Cenário", 1, 2, d_cadaver, {"interativo": True}),
    "teia_gigante": ("Teia gigante", "Cenário", 2, 2, d_teia_gigante, {}),
    "espelho_quebrado": ("Espelho quebrado", "Cenário", 1, 1, d_espelho_quebrado, {}),
    "boneca": ("Boneca velha", "Itens soltos", 1, 1, d_boneca, {"interativo": True, "solto": True}),
    "ossos": ("Pilha de ossos", "Cenário", 1, 1, d_ossos, {}),
    "velas_ritual": ("Círculo de velas", "Luzes", 2, 2, d_velas_ritual, {"luz": "vela"}),
    "poca_sangue": ("Poça de sangue", "Cenário", 1, 1, d_poca_sangue, {}),
    # steampunk (v0.59)
    "caldeira": ("Caldeira", "Luzes", 2, 2, d_caldeira, {"luz": "braseiro"}),
    "bancada_engrenagens": ("Bancada com engrenagens", "Móveis", 2, 1, d_bancada_engrenagens, {"interativo": True}),
    "automato": ("Autômato", "Tecnologia", 1, 1, d_automato, {"movel": True}),
    "cano_valvula": ("Cano com válvula", "Cenário", 2, 1, d_cano_valvula, {}),
    "relogio_pendulo": ("Relógio de pêndulo", "Móveis", 1, 1, d_relogio_pendulo, {}),
    "lampiao_gas": ("Lampião a gás", "Luzes", 1, 1, d_lampiao_gas, {"luz": "candelabro"}),
    "bau_rebites": ("Baú com rebites", "Recipientes", 1, 1, d_bau_rebites, {"interativo": True, "movel": True}),
    "globo_mundi": ("Globo mapa-múndi", "Cenário", 1, 1, d_globo_mundi, {}),
    "telescopio_latao": ("Telescópio de latão", "Cenário", 1, 1, d_telescopio_latao, {}),
    "balao_carga": ("Balão de carga", "Cenário", 2, 2, d_balao_carga, {"interativo": True}),
    # pós-apocalíptico (v0.59)
    "carro_ferrugem": ("Carro enferrujado", "Cenário", 2, 4, d_carro_ferrugem, {"interativo": True}),
    "barricada": ("Barricada", "Cenário", 2, 1, d_barricada, {"bloqueia": True}),
    "tambor_fogo": ("Tambor com fogo", "Luzes", 1, 1, d_tambor_fogo, {"luz": "braseiro"}),
    "saco_areia": ("Sacos de areia", "Cenário", 2, 1, d_saco_areia, {}),
    "placa_perigo": ("Placa de PERIGO", "Cenário", 1, 1, d_placa_perigo, {}),
    "prateleira_saqueada": ("Prateleira saqueada", "Móveis", 2, 1, d_prateleira_saqueada, {"interativo": True}),
    "galao": ("Galão", "Itens soltos", 1, 1, d_galao, {"interativo": True, "solto": True}),
    "pneu": ("Pneu", "Cenário", 1, 1, d_pneu, {"movel": True}),
    "cerca_arame": ("Cerca de arame", "Cenário", 3, 1, d_cerca_arame, {}),
    "zumbi_caido": ("Zumbi caído", "Cenário", 1, 2, d_zumbi_caido, {"interativo": True}),
}

# Em que tema(s) cada objeto aparece no filtro "do tema". Sem entrada = serve pra todos.
_MED, _MOD, _FUT, _MAG, _TER = "medieval", "moderno", "futurista", "magico", "terror"
TEMAS_PROP = {}
for _k in ("trono", "forja", "bigorna", "carroca", "tenda", "mesa_banquete", "estandarte", "suporte_armas",
           "feno", "tocheiro"):
    TEMAS_PROP[_k] = {_MED}
for _k in ("geladeira", "fogao", "pia", "vaso_sanitario", "banheira", "tv", "escrivaninha", "moto", "cacamba",
           "maquina_venda"):
    TEMAS_PROP[_k] = {_MOD}
for _k in ("holomesa", "robo", "drone", "console", "reator", "tubo_estase", "nave", "conteiner", "teleporte",
           "torreta"):
    TEMAS_PROP[_k] = {_FUT}
for _k in ("caldeirao", "mesa_alquimia", "pedestal_orbe", "estante_grimorios", "portal", "pedra_runica",
           "cogumelos", "esfera_armilar", "telescopio", "fonte_magica"):
    TEMAS_PROP[_k] = {_MAG}
for _k in ("forca", "jaula", "mesa_tortura", "cadaver", "teia_gigante", "espelho_quebrado", "boneca", "ossos",
           "velas_ritual", "poca_sangue"):
    TEMAS_PROP[_k] = {_TER}
_STE, _POS = "steampunk", "posapoc"
for _k in ("caldeira", "bancada_engrenagens", "automato", "cano_valvula", "relogio_pendulo", "lampiao_gas", "bau_rebites",
           "globo_mundi", "telescopio_latao", "balao_carga"):
    TEMAS_PROP[_k] = {_STE}
for _k in ("carro_ferrugem", "barricada", "tambor_fogo", "saco_areia", "placa_perigo", "prateleira_saqueada", "galao",
           "pneu", "cerca_arame", "zumbi_caido"):
    TEMAS_PROP[_k] = {_POS}
# alguns servem em mais de um tema
TEMAS_PROP["caldeirao"] |= {_MED, _TER}
TEMAS_PROP["tocheiro"] |= {_MAG, _TER}
TEMAS_PROP["jaula"] |= {_MED}
TEMAS_PROP["ossos"] |= {_MED, _MAG}
TEMAS_PROP["teia_gigante"] |= {_MED, _MAG}
TEMAS_PROP["fogao"] |= {_TER}
TEMAS_PROP["banheira"] |= {_TER}
TEMAS_PROP["conteiner"] |= {_MOD}
TEMAS_PROP["drone"] |= {_MOD}
TEMAS_PROP["estante_grimorios"] |= {_TER}
TEMAS_PROP["telescopio"] |= {_MED}
TEMAS_PROP["zumbi_caido"] |= {_TER}
TEMAS_PROP["tambor_fogo"] |= {_MOD, _TER}
TEMAS_PROP["barricada"] |= {_MOD, _TER}
TEMAS_PROP["saco_areia"] |= {_MOD}
TEMAS_PROP["relogio_pendulo"] |= {_MED, _TER, _MAG}
# objetos antigos que só combinam com alguns temas
TEMAS_PROP.update({
    "computador": {_MOD, _FUT}, "terminal": {_FUT, _MOD}, "servidor": {_FUT, _MOD}, "carro": {_MOD, _TER, _POS},
    "cadaver": {_TER, _POS}, "esfera_armilar": {_MAG, _STE},
    "capsula": {_FUT}, "cristal": {_MAG, _FUT}, "circulo_magico": {_MAG, _TER},
    "caixa_suprimentos": {_MOD, _FUT}, "poste": {_MOD, _TER, _FUT},
    "lustre": {_MED, _MAG, _TER, _MOD}, "candelabro": {_MED, _MAG, _TER}, "braseiro": {_MED, _MAG, _TER},
    "lareira": {_MED, _MAG, _TER, _MOD}, "pergaminho": {_MED, _MAG, _TER}, "pocao": {_MED, _MAG},
    "balcao": {_MED, _MAG, _MOD}, "tumulo": {_MED, _MAG, _TER}, "lapide": {_MED, _MAG, _TER},
    "caixao": {_MED, _MAG, _TER}, "urna": {_MED, _MAG, _TER}, "cacifo": {_MOD, _FUT, _TER},
    "altar": {_MED, _MAG, _TER}, "poco": {_MED, _MAG, _TER}, "estatua": {_MED, _MAG, _TER},
    "fogueira": {_MED, _MAG, _TER}, "fogueira_luz": {_MED, _MAG, _TER, _MOD},
})


def temas_do_prop(chave: str) -> set:
    """Temas onde o objeto aparece no filtro do tema (vazio = serve pra todos)."""
    return TEMAS_PROP.get(chave, set())
