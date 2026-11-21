"""
🧤 O ponteiro do mouse do Taverna, na COR do token do jogador (o mestre: dourado). É o mesmo desenho que os
outros veem andando pela mesa (vida.CursorItem) e o cursor do programa inteiro (ui/cursor_global.py).

(v0.64.1, pedido do Manel) CADA TEMA TEM O SEU:
  medieval  — a luvinha de desenho animado (a de sempre)
  futurista — seta holográfica angulosa com brilho neon
  steampunk — ponteiro de latão rebitado com uma engrenagem
  terror    — punhal ritual sujo de sangue, cabo enrolado na cor
  magico    — varinha com o cristal brilhando na ponta e faíscas
  moderno   — seta lisa e limpa (estilo sistema), com sombra
  posapoc   — seta de chapa enferrujada com parafusos e fita adesiva
  claro     — seta fina com contorno escuro · escuro — seta grafite com contorno brilhando na cor
Todos apontam pro mesmo lugar (a ponta em PONTA, no tamanho 32) e a parte principal fica na cor do jogador.
"""

import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QBrush, QColor, QCursor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
                         QPolygonF, QRadialGradient)

COR_MESTRE = QColor("#e8c25a")
PONTA = (3, 2)   # hotspot (px, no tamanho 32)
_CACHE = {}


def tema_atual() -> str:
    try:
        from ..ui import tema
        return getattr(tema, "_ATUAL", None) or "medieval"
    except ImportError:
        return "medieval"


def _tons(cor: QColor):
    cor = QColor(cor)
    lum = (0.299 * cor.red() + 0.587 * cor.green() + 0.114 * cor.blue()) / 255
    linha = QColor(15, 12, 10) if lum > 0.5 else QColor(250, 248, 242)
    return cor, linha, cor.lighter(128), cor.darker(155)


def _caminho(pontos):
    cam = QPainterPath(QPointF(*pontos[0]))
    for x, y in pontos[1:]:
        cam.lineTo(x, y)
    cam.closeSubpath()
    return cam


# a seta "de sistema", com a ponta em (0, 0), apontando pra cima-esquerda
SETA = [(0, 0), (0, 21), (5.2, 16.2), (9.0, 24.8), (12.6, 23.2), (8.9, 14.8), (15.4, 14.8)]


# ====================================================================== os desenhos (0, 0) = a ponta
def _luva(p: QPainter, cor: QColor):
    """Medieval: luvinha de desenho animado apontando pra cima, um pouco inclinada; o punho enrolado."""
    cor, linha, claro, escuro = _tons(cor)
    p.rotate(-18)                 # inclinada ~-18° em volta da ponta do dedo
    p.translate(-5.5, -1.0)       # (desenhada "em pé" com a ponta em (5.5, 1))
    sombra_luva = QPainterPath()
    sombra_luva.addRoundedRect(QRectF(4.6, 13.4, 16.0, 13.8), 4.5, 4.5)
    sombra_luva.addRoundedRect(QRectF(4.4, 2.0, 5.4, 14.0), 2.7, 2.7)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(0, 0, 0, 55))
    p.drawPath(sombra_luva.translated(1.6, 1.8))
    contorno = QPen(linha, 1.6)
    contorno.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    contorno.setCapStyle(Qt.PenCapStyle.RoundCap)
    g = QLinearGradient(QPointF(2, 0), QPointF(20, 4))
    g.setColorAt(0, claro)
    g.setColorAt(0.5, cor)
    g.setColorAt(1, escuro)
    p.setPen(contorno)
    p.setBrush(g)
    polegar = QPainterPath()
    polegar.addRoundedRect(QRectF(0.4, 13.2, 6.6, 8.2), 3.3, 3.3)
    p.drawPath(polegar)
    mao = QPainterPath()
    mao.moveTo(3.4, 14)
    mao.lineTo(8.2, 12.6)
    mao.cubicTo(8.4, 10.6, 12.0, 10.4, 12.2, 12.6)
    mao.cubicTo(12.4, 10.9, 15.9, 10.9, 16.0, 13.2)
    mao.cubicTo(16.4, 11.8, 19.6, 12.2, 19.4, 14.8)
    mao.lineTo(19.2, 20.5)
    mao.cubicTo(19.0, 24.2, 16.4, 25.6, 13.2, 25.6)
    mao.lineTo(9.0, 25.6)
    mao.cubicTo(5.6, 25.6, 3.4, 23.2, 3.4, 20.2)
    mao.closeSubpath()
    dedo = QPainterPath()
    dedo.addRoundedRect(QRectF(3.0, 0.4, 5.4, 16.0), 2.7, 2.7)
    p.drawPath(mao.united(dedo).simplified())
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(0, 0, 0, 45))
    p.drawRoundedRect(QRectF(9.0, 15.6, 9.6, 2.2), 1.1, 1.1)
    p.setPen(QPen(linha, 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    for x in (12.2, 16.0):
        p.drawLine(QPointF(x, 13.0), QPointF(x - 0.3, 16.0))
    p.drawLine(QPointF(8.4, 13.4), QPointF(8.4, 15.6))
    punho = QPainterPath()
    punho.addRoundedRect(QRectF(4.2, 24.4, 14.6, 6.0), 2.4, 2.4)
    p.setPen(contorno)
    gc = QLinearGradient(QPointF(4, 24), QPointF(4, 31))
    gc.setColorAt(0, cor)
    gc.setColorAt(1, escuro.darker(115))
    p.setBrush(gc)
    p.drawPath(punho)
    p.setPen(QPen(linha, 0.9))
    for x in (8.6, 12.0, 15.2):
        p.drawLine(QPointF(x, 25.6), QPointF(x, 29.2))
    p.setPen(QPen(QColor(255, 255, 255, 170), 1.1, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(4.6, 2.6), QPointF(4.6, 8.0))
    p.drawLine(QPointF(5.0, 20.0), QPointF(6.0, 22.6))


def _holo(p: QPainter, cor: QColor):
    """Futurista: seta angulosa de holograma — miolo escuro translúcido, contorno neon na cor, brilho e linhas."""
    cor = QColor(cor)
    neon = cor.lighter(135)
    forma = _caminho([(0, 0), (0, 22), (5.5, 17), (10.5, 26), (14.5, 24), (9.8, 15.6), (17, 15.2), (8, 7.5)])
    for larg, alfa in ((6, 40), (3.6, 80)):           # o brilho em volta
        c = QColor(neon)
        c.setAlpha(alfa)
        p.setPen(QPen(c, larg, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.MiterJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(forma)
    g = QLinearGradient(QPointF(0, 0), QPointF(12, 24))
    meio = QColor(cor.darker(260))
    meio.setAlpha(215)
    g.setColorAt(0, QColor(cor.red(), cor.green(), cor.blue(), 120))
    g.setColorAt(0.45, meio)
    g.setColorAt(1, QColor(8, 10, 16, 230))
    p.setBrush(QBrush(g))
    p.setPen(QPen(neon, 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin))
    p.drawPath(forma)
    p.save()
    p.setClipPath(forma)
    p.setPen(QPen(QColor(neon.red(), neon.green(), neon.blue(), 70), 0.8))
    y = 3.0
    while y < 26:                                      # linhas de varredura
        p.drawLine(QPointF(0, y), QPointF(18, y))
        y += 2.4
    p.restore()
    p.setPen(QPen(QColor(255, 255, 255, 220), 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(1.3, 3.2), QPointF(1.3, 14))
    p.drawLine(QPointF(1.3, 3.2), QPointF(6.4, 8.0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(neon)
    p.drawRect(QRectF(15.5, 22.5, 2.2, 2.2))           # "pixel" solto
    p.drawRect(QRectF(19, 19.5, 1.5, 1.5))


def _latao(p: QPainter, cor: QColor):
    """Steampunk: ponteiro de latão polido com rebites, um friso e a engrenagem na cor do jogador."""
    cor, linha, claro, escuro = _tons(cor)
    # a engrenagem atrás, no rabo do ponteiro
    centro, r = QPointF(15.5, 21.5), 6.6
    dentes = QPainterPath()
    pts = []
    for k in range(16):
        a = k * math.pi / 8
        rr = r if k % 2 == 0 else r * 0.72
        a2 = a + math.pi / 16
        pts += [(centro.x() + math.cos(a) * rr, centro.y() + math.sin(a) * rr),
                (centro.x() + math.cos(a2) * rr, centro.y() + math.sin(a2) * rr)]
    dentes = _caminho(pts)
    furo = QPainterPath()
    furo.addEllipse(centro, 2.0, 2.0)
    gg = QRadialGradient(centro, r)
    gg.setColorAt(0, claro)
    gg.setColorAt(1, escuro)
    p.setPen(QPen(QColor(40, 24, 10), 1.1))
    p.setBrush(QBrush(gg))
    p.drawPath(dentes.subtracted(furo))
    # o ponteiro de latão
    forma = _caminho(SETA)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(0, 0, 0, 60))
    p.drawPath(forma.translated(1.4, 1.6))
    g = QLinearGradient(QPointF(0, 0), QPointF(14, 10))
    g.setColorAt(0, QColor("#fff0b8"))
    g.setColorAt(0.35, QColor("#d7a94a"))
    g.setColorAt(0.7, QColor("#9a6a22"))
    g.setColorAt(1, QColor("#e2b860"))
    p.setPen(QPen(QColor(52, 30, 8), 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.setBrush(QBrush(g))
    p.drawPath(forma)
    p.setPen(QPen(cor, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))   # friso na cor
    p.drawLine(QPointF(2.0, 6.0), QPointF(2.0, 16.5))
    p.setPen(Qt.PenStyle.NoPen)
    for x, y in ((2.2, 18.2), (10.6, 15.6), (8.4, 21.6)):   # rebites
        p.setBrush(QColor(70, 42, 12))
        p.drawEllipse(QPointF(x + 0.3, y + 0.3), 1.1, 1.1)
        p.setBrush(QColor(255, 236, 170))
        p.drawEllipse(QPointF(x - 0.2, y - 0.2), 0.6, 0.6)


def _osso(p: QPainter, cor: QColor):
    """Terror: dedo magro e ossudo (falanges, nós), unha escura comprida, manga rasgada na cor do jogador."""
    cor, linha, claro, escuro = _tons(cor)
    p.translate(0.6, 0.2)
    p.rotate(-24)
    pele = QColor("#d8ccb0")
    sombra = QColor("#8a7a5a")
    contorno = QPen(QColor(30, 20, 14), 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    # manga rasgada (na cor)
    manga = _caminho([(-5.5, 22), (6.5, 21.5), (7.5, 29.5), (5.4, 27.2), (3.6, 30.2), (1.6, 27.6), (-0.6, 30.4),
                      (-2.6, 27.4), (-4.8, 29.8), (-6.2, 26.6)])
    gm = QLinearGradient(QPointF(-6, 22), QPointF(7, 30))
    gm.setColorAt(0, claro)
    gm.setColorAt(1, escuro.darker(130))
    p.setPen(contorno)
    p.setBrush(QBrush(gm))
    p.drawPath(manga)
    # dedo: três falanges finas com nós mais grossos
    g = QLinearGradient(QPointF(-3, 0), QPointF(3, 0))
    g.setColorAt(0, pele.lighter(110))
    g.setColorAt(1, sombra)
    p.setBrush(QBrush(g))
    dedo = QPainterPath()
    dedo.addRoundedRect(QRectF(-1.6, 2.5, 3.2, 8.0), 1.6, 1.6)
    dedo.addRoundedRect(QRectF(-1.9, 9.6, 3.8, 6.6), 1.8, 1.8)
    dedo.addRoundedRect(QRectF(-2.3, 15.4, 4.6, 7.4), 2.2, 2.2)
    for y, r in ((10.0, 2.3), (15.8, 2.7)):   # os nós
        dedo.addEllipse(QPointF(0, y), r, 1.6)
    dedo.addRoundedRect(QRectF(-4.6, 18.5, 9.2, 5.0), 2.2, 2.2)   # o resto da mão saindo da manga
    p.drawPath(dedo.simplified())
    # a unha preta, comprida e pontuda (a ponta é o clique)
    unha = _caminho([(0, -0.2), (1.5, 3.2), (1.2, 5.0), (-1.2, 5.0), (-1.5, 3.2)])
    p.setBrush(QColor(28, 22, 20))
    p.setPen(QPen(QColor(10, 6, 6), 0.8))
    p.drawPath(unha)
    p.setPen(QPen(QColor(60, 40, 30, 200), 0.7))
    for y in (10.0, 15.8):
        p.drawLine(QPointF(-1.2, y), QPointF(1.2, y))
    p.setPen(QPen(QColor(255, 255, 255, 120), 0.8))
    p.drawLine(QPointF(-0.7, 6), QPointF(-0.7, 9))


def _punhal(p: QPainter, cor: QColor):
    """Terror: punhal ritual — lâmina de aço manchada de sangue (a ponta é o clique), guarda escura, cabo
    enrolado na cor do jogador e uma gota caindo."""
    cor, linha, claro, escuro = _tons(cor)
    p.save()
    p.rotate(-38)                                     # deitado na diagonal, ponta pra cima-esquerda
    # sombra
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(0, 0, 0, 60))
    p.drawRoundedRect(QRectF(-2.2 + 1.4, 1 + 1.4, 4.4, 26), 2, 2)
    # lâmina
    lamina = _caminho([(0, 0), (2.6, 4.5), (2.4, 15.5), (-2.4, 15.5), (-2.6, 4.5)])
    g = QLinearGradient(QPointF(-2.6, 0), QPointF(2.6, 0))
    g.setColorAt(0, QColor("#f2f4f6"))
    g.setColorAt(0.5, QColor("#a8aeb6"))
    g.setColorAt(1, QColor("#5a6068"))
    p.setPen(QPen(QColor(16, 16, 20), 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.MiterJoin))
    p.setBrush(QBrush(g))
    p.drawPath(lamina)
    p.setPen(QPen(QColor(60, 66, 74), 0.7))
    p.drawLine(QPointF(0, 2.5), QPointF(0, 15))       # o fio do meio
    # sangue na lâmina
    p.save()
    p.setClipPath(lamina)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(120, 8, 8, 230))
    sangue = _caminho([(-3, 0), (3, 0), (3, 4.6), (1.6, 6.2), (1.0, 9.4), (0.2, 6.6), (-1.2, 7.8), (-1.6, 5.2), (-3, 5.6)])
    p.drawPath(sangue)
    p.restore()
    # guarda
    p.setPen(QPen(QColor(10, 8, 8), 0.9))
    p.setBrush(QColor(44, 36, 34))
    p.drawRoundedRect(QRectF(-5.2, 15.2, 10.4, 2.6), 1.2, 1.2)
    # cabo enrolado na cor
    gc = QLinearGradient(QPointF(-2, 0), QPointF(2, 0))
    gc.setColorAt(0, claro)
    gc.setColorAt(1, escuro)
    p.setBrush(QBrush(gc))
    p.drawRoundedRect(QRectF(-1.8, 17.6, 3.6, 7.6), 1.2, 1.2)
    p.setPen(QPen(QColor(0, 0, 0, 120), 0.7))
    for y in (19.4, 21.4, 23.4):
        p.drawLine(QPointF(-1.8, y), QPointF(1.8, y + 0.8))
    # pomo
    p.setPen(QPen(QColor(10, 8, 8), 0.9))
    p.setBrush(QColor(44, 36, 34))
    p.drawEllipse(QPointF(0, 26.4), 2.0, 1.6)
    p.restore()
    # a gota caindo da ponta
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(140, 10, 10))
    gota = QPainterPath(QPointF(3.2, 5.0))
    gota.cubicTo(4.6, 7.0, 4.4, 8.4, 3.2, 8.4)
    gota.cubicTo(2.0, 8.4, 1.8, 7.0, 3.2, 5.0)
    p.drawPath(gota)


def _varinha(p: QPainter, cor: QColor):
    """Mágico: varinha de madeira escura com o cristal na cor do jogador brilhando na ponta, e faíscas."""
    cor = QColor(cor)
    claro = cor.lighter(150)
    brilho = QRadialGradient(QPointF(2.4, 2.4), 9)
    brilho.setColorAt(0, QColor(claro.red(), claro.green(), claro.blue(), 170))
    brilho.setColorAt(1, QColor(claro.red(), claro.green(), claro.blue(), 0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(brilho))
    p.drawEllipse(QPointF(2.4, 2.4), 9, 9)
    # a varinha (de baixo-direita até perto da ponta)
    p.save()
    p.translate(5.5, 5.5)
    p.rotate(45)
    g = QLinearGradient(QPointF(0, -1.8), QPointF(0, 1.8))
    g.setColorAt(0, QColor("#7a5232"))
    g.setColorAt(0.5, QColor("#4a2c16"))
    g.setColorAt(1, QColor("#22140a"))
    p.setPen(QPen(QColor(12, 6, 2), 0.9))
    p.setBrush(QBrush(g))
    corpo = QPainterPath()
    corpo.moveTo(0, -1.3)
    corpo.lineTo(24, -2.0)
    corpo.quadTo(26, 0, 24, 2.0)
    corpo.lineTo(0, 1.3)
    corpo.closeSubpath()
    p.drawPath(corpo)
    p.setPen(QPen(QColor("#c9a24a"), 1.3))                # anéis dourados do cabo
    for x in (15.5, 17.5):
        p.drawLine(QPointF(x, -1.9), QPointF(x, 1.9))
    p.restore()
    # o cristal (losango) na cor, com a ponta no clique
    cristal = _caminho([(0, 0), (4.6, 1.6), (6.2, 6.2), (1.6, 4.6)])
    gc = QLinearGradient(QPointF(0, 0), QPointF(6, 6))
    gc.setColorAt(0, QColor(255, 255, 255))
    gc.setColorAt(0.35, claro)
    gc.setColorAt(1, cor.darker(140))
    p.setPen(QPen(cor.darker(220), 0.9))
    p.setBrush(QBrush(gc))
    p.drawPath(cristal)
    # faíscas
    p.setPen(QPen(claro, 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    for cx, cy, r in ((11, 3.5, 2.0), (4, 12, 1.6), (13.5, 10, 1.1)):
        p.drawLine(QPointF(cx - r, cy), QPointF(cx + r, cy))
        p.drawLine(QPointF(cx, cy - r), QPointF(cx, cy + r))


def _seta_lisa(p: QPainter, cor: QColor, fina: bool = False):
    """Moderno (e claro/escuro, mais fina): a seta de sistema, lisa, na cor, contorno claro e sombra macia."""
    cor, linha, claro, escuro = _tons(cor)
    forma = _caminho(SETA)
    for k, alfa in ((2.2, 30), (1.4, 45)):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, alfa))
        p.drawPath(forma.translated(k * 0.7, k))
    if fina:
        p.setBrush(cor)
    else:
        g = QLinearGradient(QPointF(0, 0), QPointF(10, 22))
        g.setColorAt(0, claro)
        g.setColorAt(1, cor)
        p.setBrush(QBrush(g))
    contorno = QColor(255, 255, 255) if linha.lightness() < 128 or fina else QColor(250, 250, 250)
    p.setPen(QPen(contorno, 1.6 if not fina else 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                  Qt.PenJoinStyle.MiterJoin))
    p.drawPath(forma)
    p.setPen(QPen(QColor(0, 0, 0, 150), 0.6))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(forma.translated(0, 0))


def _sucata(p: QPainter, cor: QColor):
    """Pós-apocalíptico: seta de chapa enferrujada cortada na marra (beira torta), dois parafusos e uma volta
    de fita adesiva na cor do jogador."""
    cor, linha, claro, escuro = _tons(cor)
    forma = _caminho([(0, 0), (0.4, 7), (-0.3, 13), (0.3, 21.6), (5.4, 16.6), (8.4, 23.6), (10.2, 25.4),
                      (13.3, 23.5), (12.6, 21.4), (9.6, 15.2), (13.4, 15.6), (15.8, 14.6), (10.4, 9.4), (5.6, 4.6)])
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(0, 0, 0, 70))
    p.drawPath(forma.translated(1.4, 1.6))
    g = QLinearGradient(QPointF(0, 0), QPointF(14, 24))
    g.setColorAt(0, QColor("#b8763c"))
    g.setColorAt(0.4, QColor("#7a4220"))
    g.setColorAt(0.7, QColor("#9a5a2a"))
    g.setColorAt(1, QColor("#5a2e14"))
    p.setPen(QPen(QColor(30, 16, 8), 1.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.BevelJoin))
    p.setBrush(QBrush(g))
    p.drawPath(forma)
    p.save()
    p.setClipPath(forma)
    p.setPen(Qt.PenStyle.NoPen)
    for x, y, r in ((3, 9, 1.6), (6.5, 14, 1.2), (2.2, 17.5, 1.0), (10, 19.5, 1.4)):   # manchas de ferrugem
        p.setBrush(QColor(60, 26, 10, 150))
        p.drawEllipse(QPointF(x, y), r, r * 0.7)
    # a fita adesiva atravessada, na cor
    p.translate(5, 16)
    p.rotate(-38)
    fita = QRectF(-9, -2.2, 18, 4.4)
    gf = QLinearGradient(fita.topLeft(), fita.bottomLeft())
    gf.setColorAt(0, claro)
    gf.setColorAt(1, cor.darker(125))
    p.setBrush(QBrush(gf))
    p.drawRect(fita)
    p.setPen(QPen(QColor(0, 0, 0, 60), 0.6))
    for x in (-6, -2, 2, 6):
        p.drawLine(QPointF(x, -2.2), QPointF(x + 0.6, 2.2))
    p.restore()
    for x, y in ((2.0, 4.6), (11.0, 22.4)):                # parafusos
        p.setPen(QPen(QColor(20, 18, 16), 0.8))
        p.setBrush(QColor(140, 138, 130))
        p.drawEllipse(QPointF(x, y), 1.3, 1.3)
        p.drawLine(QPointF(x - 0.8, y), QPointF(x + 0.8, y))


def _seta_clara(p: QPainter, cor: QColor):
    """Claro: seta fina na cor com contorno ESCURO (lê bem em fundo claro)."""
    forma = _caminho(SETA)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(0, 0, 0, 35))
    p.drawPath(forma.translated(1.0, 1.4))
    p.setBrush(QColor(cor))
    p.setPen(QPen(QColor(30, 30, 34), 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.MiterJoin))
    p.drawPath(forma)
    p.setPen(QPen(QColor(255, 255, 255, 170), 0.9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(1.6, 4.0), QPointF(1.6, 14.5))


def _seta_escura(p: QPainter, cor: QColor):
    """Escuro: seta grafite com contorno brilhando na cor do jogador (lê bem em fundo escuro)."""
    cor = QColor(cor)
    forma = _caminho(SETA)
    c = QColor(cor.lighter(120))
    c.setAlpha(70)
    p.setPen(QPen(c, 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(forma)
    g = QLinearGradient(QPointF(0, 0), QPointF(10, 22))
    g.setColorAt(0, QColor(70, 72, 80))
    g.setColorAt(1, QColor(22, 22, 26))
    p.setBrush(QBrush(g))
    p.setPen(QPen(cor.lighter(115), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.MiterJoin))
    p.drawPath(forma)


DESENHOS = {"medieval": _luva, "futurista": _holo, "steampunk": _latao, "terror": _punhal, "magico": _varinha,
            "moderno": _seta_lisa, "posapoc": _sucata, "claro": _seta_clara, "escuro": _seta_escura}


def desenhar_luva(p: QPainter, cor: QColor, escala: float = 1.0, tema: str | None = None):
    """O ponteiro do tema (o nome ficou "luva" por causa do medieval). (0, 0) = a ponta. Tamanho ~32."""
    p.save()
    p.scale(escala, escala)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.translate(PONTA[0], PONTA[1])
    try:
        DESENHOS.get(tema or tema_atual(), _luva)(p, QColor(cor))
    finally:
        p.restore()


def pixmap_luva(cor: QColor, tam: int = 32, tema: str | None = None) -> QPixmap:
    pm = QPixmap(tam, tam)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    desenhar_luva(p, QColor(cor), tam / 32, tema)
    p.end()
    return pm


def cursor_luva(cor: QColor, tema: str | None = None) -> QCursor:
    tema = tema or tema_atual()
    chave = (QColor(cor).name(), tema)
    c = _CACHE.get(chave)
    if c is None:
        pm = pixmap_luva(QColor(cor), 32, tema)
        c = _CACHE[chave] = QCursor(pm, PONTA[0], PONTA[1])
    return c
