"""
Ícones das ferramentas, desenhados pelo programa (não dependem de fonte de emoji).
"""

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF

TAM = 64


def _caneta(cor, larg=4):
    p = QPen(QColor(cor), larg)
    p.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return p


def _selecionar(p, cor):
    seta = QPolygonF([QPointF(18, 10), QPointF(18, 50), QPointF(28, 40), QPointF(35, 55),
                      QPointF(42, 52), QPointF(35, 37), QPointF(48, 37)])
    p.setPen(_caneta(cor, 3.5))
    p.setBrush(QColor(cor))
    p.drawPolygon(seta)


def _terreno(p, cor):
    p.setPen(_caneta(cor, 5))
    p.drawLine(QPointF(46, 12), QPointF(30, 34))
    p.setBrush(QColor(cor))
    p.setPen(Qt.PenStyle.NoPen)
    ponta = QPainterPath(QPointF(28, 32))
    ponta.cubicTo(QPointF(18, 34), QPointF(14, 44), QPointF(10, 54))
    ponta.cubicTo(QPointF(22, 54), QPointF(34, 48), QPointF(34, 38))
    ponta.closeSubpath()
    p.drawPath(ponta)


def _parede(p, cor):
    p.save()
    p.setClipRect(QRectF(8, 12, 48, 40))
    p.setPen(_caneta(cor, 3))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for linha in range(3):
        y = 14 + linha * 12.5
        desloc = 0 if linha % 2 == 0 else -9
        for x in range(8 + desloc, 60, 18):
            p.drawRect(QRectF(x, y, 16, 10))
    p.restore()


def _sala(p, cor):
    c = QColor(cor)
    c.setAlpha(60)
    p.setBrush(c)
    p.setPen(_caneta(cor, 5))
    p.drawRect(QRectF(12, 14, 40, 36))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(cor))
    for x, y in ((12, 14), (52, 14), (12, 50), (52, 50)):
        p.drawEllipse(QPointF(x, y), 4, 4)


def _porta(p, cor):
    p.setPen(_caneta(cor, 4))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRect(QRectF(16, 8, 32, 48))          # batente
    c = QColor(cor)
    c.setAlpha(70)
    p.setBrush(c)
    p.setPen(_caneta(cor, 3))
    p.drawPolygon(QPolygonF([QPointF(16, 8), QPointF(38, 14),
                             QPointF(38, 60), QPointF(16, 56)]))  # folha entreaberta
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(cor))
    p.drawEllipse(QPointF(33, 36), 3, 3)


def _borracha(p, cor):
    p.save()
    p.translate(32, 32)
    p.rotate(-35)
    c = QColor(cor)
    c.setAlpha(70)
    p.setPen(_caneta(cor, 3.5))
    p.setBrush(c)
    p.drawRoundedRect(QRectF(-18, -10, 36, 20), 4, 4)
    p.setBrush(QColor(cor))
    p.drawRoundedRect(QRectF(-18, -10, 14, 20), 4, 4)
    p.restore()
    p.setPen(_caneta(cor, 2.5))
    p.drawLine(QPointF(14, 56), QPointF(52, 56))


def _borracha_parede(p, cor):
    # tijolinhos atrás + borracha na frente
    p.save()
    p.setPen(_caneta(cor, 2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for x, y in ((6, 8), (24, 8), (42, 8), (15, 20), (33, 20)):
        p.drawRect(QRectF(x, y, 16, 10))
    p.restore()
    p.save()
    p.translate(36, 42)
    p.rotate(-35)
    c = QColor(cor)
    c.setAlpha(70)
    p.setPen(_caneta(cor, 3))
    p.setBrush(c)
    p.drawRoundedRect(QRectF(-15, -8, 30, 16), 3, 3)
    p.setBrush(QColor(cor))
    p.drawRoundedRect(QRectF(-15, -8, 11, 16), 3, 3)
    p.restore()


def _luz(p, cor):
    c = QColor(cor)
    c.setAlpha(60)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(c)
    p.drawEllipse(QPointF(32, 34), 24, 24)
    p.setBrush(QColor(cor))
    chama = QPainterPath(QPointF(32, 12))
    chama.cubicTo(QPointF(46, 26), QPointF(44, 44), QPointF(32, 46))
    chama.cubicTo(QPointF(20, 44), QPointF(18, 26), QPointF(32, 12))
    p.drawPath(chama)
    p.setPen(_caneta(cor, 4))
    p.drawLine(QPointF(32, 46), QPointF(32, 58))


# ====================================================================== ícones da interface
# (traço arredondado numa grade 64×64; a cor vem do tema — nada de emoji)
def _linha(p, *pts):
    p.drawPolyline(QPolygonF([QPointF(x, y) for x, y in pts]))


def _traco(p, cor, larg=4.4):
    p.setPen(_caneta(cor, larg))
    p.setBrush(Qt.BrushStyle.NoBrush)


def _i_mapa(p, cor):
    _traco(p, cor)
    p.drawPolygon(QPolygonF([QPointF(*q) for q in ((9, 17), (24, 11), (40, 17), (55, 11), (55, 47), (40, 53), (24, 47), (9, 53))]))
    p.drawLine(QPointF(24, 11), QPointF(24, 47))
    p.drawLine(QPointF(40, 17), QPointF(40, 53))


def _i_token(p, cor):
    _traco(p, cor)
    p.drawEllipse(QPointF(32, 32), 22, 22)
    p.setBrush(QColor(cor))
    p.drawEllipse(QPointF(32, 26), 6.5, 6.5)
    corpo = QPainterPath(QPointF(19, 46))
    corpo.cubicTo(QPointF(21, 34), QPointF(43, 34), QPointF(45, 46))
    corpo.cubicTo(QPointF(38, 52), QPointF(26, 52), QPointF(19, 46))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPath(corpo)


def _i_snap(p, cor):
    _traco(p, cor, 3.6)
    for v in (20, 32, 44):
        p.drawLine(QPointF(v, 10), QPointF(v, 54))
        p.drawLine(QPointF(10, v), QPointF(54, v))
    p.setBrush(QColor(cor))
    p.drawEllipse(QPointF(32, 32), 5, 5)


def _i_objetos(p, cor):
    _traco(p, cor)
    p.drawRoundedRect(QRectF(10, 28, 44, 24), 3, 3)
    tampa = QPainterPath(QPointF(10, 28))
    tampa.cubicTo(QPointF(10, 10), QPointF(54, 10), QPointF(54, 28))
    p.drawPath(tampa)
    p.setBrush(QColor(cor))
    p.drawRoundedRect(QRectF(28, 24, 8, 10), 2, 2)


def _i_biblioteca(p, cor):
    _traco(p, cor)
    esq = QPainterPath(QPointF(32, 18))
    esq.cubicTo(QPointF(24, 12), QPointF(14, 12), QPointF(8, 15))
    esq.lineTo(8, 48)
    esq.cubicTo(QPointF(14, 45), QPointF(24, 45), QPointF(32, 51))
    dirr = QPainterPath(QPointF(32, 18))
    dirr.cubicTo(QPointF(40, 12), QPointF(50, 12), QPointF(56, 15))
    dirr.lineTo(56, 48)
    dirr.cubicTo(QPointF(50, 45), QPointF(40, 45), QPointF(32, 51))
    p.drawPath(esq)
    p.drawPath(dirr)
    p.drawLine(QPointF(32, 18), QPointF(32, 51))


def _i_combate(p, cor):
    _traco(p, cor, 4.6)
    p.drawLine(QPointF(12, 12), QPointF(46, 46))
    p.drawLine(QPointF(52, 12), QPointF(18, 46))
    _traco(p, cor, 4)
    p.drawLine(QPointF(36, 50), QPointF(50, 36))
    p.drawLine(QPointF(14, 36), QPointF(28, 50))
    p.drawLine(QPointF(46, 46), QPointF(54, 54))
    p.drawLine(QPointF(18, 46), QPointF(10, 54))


def _i_chat(p, cor):
    _traco(p, cor)
    balao = QPainterPath()
    balao.addRoundedRect(QRectF(8, 10, 48, 32), 9, 9)
    p.drawPath(balao)
    p.setBrush(QColor(cor))
    p.drawPolygon(QPolygonF([QPointF(18, 41), QPointF(30, 41), QPointF(16, 54)]))
    p.setPen(Qt.PenStyle.NoPen)
    for x in (22, 32, 42):
        p.drawEllipse(QPointF(x, 26), 3, 3)


def _i_dados(p, cor):
    _traco(p, cor, 4)
    import math
    hexa = [QPointF(32 + 24 * math.cos(math.radians(a)), 32 + 24 * math.sin(math.radians(a))) for a in range(-90, 270, 60)]
    p.drawPolygon(QPolygonF(hexa))
    tri = [QPointF(32, 17), QPointF(45, 40), QPointF(19, 40)]
    p.drawPolygon(QPolygonF(tri))
    for a, b in ((hexa[0], tri[0]), (hexa[2], tri[1]), (hexa[4], tri[2]), (hexa[1], tri[1]), (hexa[5], tri[2]), (hexa[3], QPointF(32, 40))):
        p.drawLine(a, b)


def _i_historico(p, cor):
    _traco(p, cor)
    p.drawRoundedRect(QRectF(14, 10, 36, 44), 4, 4)
    _traco(p, cor, 3.6)
    for y in (22, 31, 40):
        p.drawLine(QPointF(22, y), QPointF(42 if y != 40 else 34, y))


def _i_atmosfera(p, cor):
    _traco(p, cor)
    nuvem = QPainterPath(QPointF(16, 36))
    nuvem.cubicTo(QPointF(4, 36), QPointF(6, 20), QPointF(18, 22))
    nuvem.cubicTo(QPointF(20, 8), QPointF(40, 8), QPointF(42, 20))
    nuvem.cubicTo(QPointF(58, 18), QPointF(60, 36), QPointF(48, 36))
    nuvem.closeSubpath()
    p.drawPath(nuvem)
    p.setBrush(QColor(cor))
    p.setPen(_caneta(cor, 2))
    p.drawPolygon(QPolygonF([QPointF(34, 34), QPointF(24, 47), QPointF(31, 47), QPointF(27, 58), QPointF(40, 43), QPointF(33, 43), QPointF(38, 34)]))


def _i_projetor(p, cor):
    _traco(p, cor)
    p.drawRoundedRect(QRectF(8, 10, 48, 32), 3, 3)
    p.drawLine(QPointF(32, 42), QPointF(32, 50))
    p.drawLine(QPointF(20, 56), QPointF(32, 50))
    p.drawLine(QPointF(44, 56), QPointF(32, 50))
    _traco(p, cor, 3.4)
    _linha(p, (14, 36), (25, 24), (33, 32), (39, 27), (50, 36))


def _i_nevoa(p, cor):
    _traco(p, cor, 4.6)
    for y, x0, x1 in ((18, 14, 50), (30, 8, 44), (42, 20, 56), (54, 12, 40)):
        onda = QPainterPath(QPointF(x0, y))
        onda.cubicTo(QPointF(x0 + (x1 - x0) * 0.33, y - 7), QPointF(x0 + (x1 - x0) * 0.66, y + 7), QPointF(x1, y))
        p.drawPath(onda)


def _i_taverna(p, cor):
    _traco(p, cor)
    p.drawRoundedRect(QRectF(14, 22, 28, 32), 3, 3)
    alca = QPainterPath(QPointF(42, 28))
    alca.cubicTo(QPointF(56, 28), QPointF(56, 46), QPointF(42, 46))
    p.drawPath(alca)
    p.setBrush(QColor(cor))
    espuma = QPainterPath(QPointF(12, 22))
    espuma.cubicTo(QPointF(8, 10), QPointF(22, 8), QPointF(24, 14))
    espuma.cubicTo(QPointF(28, 6), QPointF(40, 8), QPointF(38, 16))
    espuma.cubicTo(QPointF(48, 14), QPointF(48, 22), QPointF(44, 22))
    espuma.closeSubpath()
    p.drawPath(espuma)
    _traco(p, cor, 3.2)
    p.drawLine(QPointF(23, 30), QPointF(23, 46))
    p.drawLine(QPointF(33, 30), QPointF(33, 46))


def _i_olho(p, cor):
    _traco(p, cor)
    olho = QPainterPath(QPointF(6, 32))
    olho.cubicTo(QPointF(18, 12), QPointF(46, 12), QPointF(58, 32))
    olho.cubicTo(QPointF(46, 52), QPointF(18, 52), QPointF(6, 32))
    p.drawPath(olho)
    p.setBrush(QColor(cor))
    p.drawEllipse(QPointF(32, 32), 7.5, 7.5)


def _i_ficha(p, cor):
    _traco(p, cor)
    p.drawPolygon(QPolygonF([QPointF(*q) for q in ((14, 8), (40, 8), (50, 18), (50, 56), (14, 56))]))
    _linha(p, (40, 8), (40, 18), (50, 18))
    _traco(p, cor, 3.4)
    p.drawEllipse(QPointF(25, 26), 5, 5)
    p.drawLine(QPointF(34, 28), QPointF(43, 28))
    p.drawLine(QPointF(21, 38), QPointF(43, 38))
    p.drawLine(QPointF(21, 47), QPointF(36, 47))


def _i_pdf(p, cor):
    _traco(p, cor)
    p.drawPolygon(QPolygonF([QPointF(*q) for q in ((14, 8), (40, 8), (50, 18), (50, 56), (14, 56))]))
    _linha(p, (40, 8), (40, 18), (50, 18))
    p.setBrush(QColor(cor))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(8, 30, 36, 16), 3, 3)


def _i_diario(p, cor):
    _traco(p, cor)
    p.drawRoundedRect(QRectF(16, 8, 36, 48), 4, 4)
    p.drawLine(QPointF(24, 8), QPointF(24, 56))
    p.setBrush(QColor(cor))
    p.drawPolygon(QPolygonF([QPointF(36, 8), QPointF(46, 8), QPointF(46, 28), QPointF(41, 22), QPointF(36, 28)]))
    _traco(p, cor, 3.6)
    for y in (18, 30, 42):
        p.drawLine(QPointF(11, y), QPointF(19, y))


def _i_som(p, cor):
    _traco(p, cor)
    p.drawLine(QPointF(26, 46), QPointF(26, 14))
    p.drawLine(QPointF(26, 14), QPointF(50, 9))
    p.drawLine(QPointF(50, 9), QPointF(50, 40))
    p.setBrush(QColor(cor))
    p.drawEllipse(QPointF(19, 47), 8, 6.5)
    p.drawEllipse(QPointF(43, 41), 8, 6.5)


def _i_imagens(p, cor):
    _traco(p, cor)
    p.drawRoundedRect(QRectF(8, 12, 48, 40), 4, 4)
    _traco(p, cor, 3.6)
    _linha(p, (12, 46), (26, 28), (36, 40), (42, 34), (52, 46))
    p.setBrush(QColor(cor))
    p.drawEllipse(QPointF(42, 23), 4, 4)


def _i_banco(p, cor):
    _traco(p, cor, 3.8)
    p.drawRoundedRect(QRectF(16, 8, 40, 32), 3, 3)
    p.setBrush(Qt.BrushStyle.NoBrush)
    _linha(p, (8, 20), (8, 54), (46, 54))
    _linha(p, (22, 34), (32, 22), (40, 30), (50, 34))


def _i_sair(p, cor):
    _traco(p, cor)
    _linha(p, (34, 10), (12, 10), (12, 54), (34, 54))
    p.drawLine(QPointF(26, 32), QPointF(54, 32))
    _linha(p, (44, 22), (54, 32), (44, 42))


def _i_alvo(p, cor):
    _traco(p, cor)
    p.drawEllipse(QPointF(32, 32), 18, 18)
    for a, b in (((32, 6), (32, 20)), ((32, 44), (32, 58)), ((6, 32), (20, 32)), ((44, 32), (58, 32))):
        p.drawLine(QPointF(*a), QPointF(*b))
    p.setBrush(QColor(cor))
    p.drawEllipse(QPointF(32, 32), 4.5, 4.5)


def _i_enquadrar(p, cor):
    _traco(p, cor, 4.8)
    for (cx, cy), (dx, dy) in (((10, 10), (1, 1)), ((54, 10), (-1, 1)), ((10, 54), (1, -1)), ((54, 54), (-1, -1))):
        _linha(p, (cx, cy + dy * 14), (cx, cy), (cx + dx * 14, cy))
    p.drawRoundedRect(QRectF(24, 24, 16, 16), 2, 2)


def _i_magia(p, cor):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(cor))
    for cx, cy, r in ((27, 32, 21), (49, 14, 9), (50, 50, 7)):
        p.drawPolygon(QPolygonF([QPointF(cx, cy - r), QPointF(cx + r * 0.24, cy - r * 0.24), QPointF(cx + r, cy),
                                 QPointF(cx + r * 0.24, cy + r * 0.24), QPointF(cx, cy + r), QPointF(cx - r * 0.24, cy + r * 0.24),
                                 QPointF(cx - r, cy), QPointF(cx - r * 0.24, cy - r * 0.24)]))


def _i_engrenagem(p, cor):
    import math
    _traco(p, cor, 5)
    for k in range(8):
        a = math.radians(k * 45)
        p.drawLine(QPointF(32 + math.cos(a) * 18, 32 + math.sin(a) * 18), QPointF(32 + math.cos(a) * 25, 32 + math.sin(a) * 25))
    _traco(p, cor)
    p.drawEllipse(QPointF(32, 32), 17, 17)
    p.drawEllipse(QPointF(32, 32), 6, 6)


def _i_chama(p, cor):
    _traco(p, cor)
    chama = QPainterPath(QPointF(32, 6))
    chama.cubicTo(QPointF(50, 24), QPointF(52, 44), QPointF(32, 58))
    chama.cubicTo(QPointF(12, 44), QPointF(16, 30), QPointF(24, 24))
    chama.cubicTo(QPointF(26, 32), QPointF(32, 30), QPointF(32, 6))
    p.drawPath(chama)
    p.setBrush(QColor(cor))
    miolo = QPainterPath(QPointF(32, 36))
    miolo.cubicTo(QPointF(40, 44), QPointF(38, 52), QPointF(32, 54))
    miolo.cubicTo(QPointF(26, 52), QPointF(24, 44), QPointF(32, 36))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPath(miolo)


def _i_camadas(p, cor):
    _traco(p, cor)
    for dy in (0, 12, 24):
        p.drawPolygon(QPolygonF([QPointF(32, 8 + dy), QPointF(56, 20 + dy), QPointF(32, 32 + dy), QPointF(8, 20 + dy)]))


def _i_propriedades(p, cor):
    _traco(p, cor)
    for y, x in ((16, 40), (32, 22), (48, 34)):
        p.drawLine(QPointF(8, y), QPointF(56, y))
        p.setBrush(QColor(cor))
        p.drawEllipse(QPointF(x, y), 6, 6)
        p.setBrush(Qt.BrushStyle.NoBrush)


def _i_jogadores(p, cor):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(cor))
    for cx, cy, r in ((22, 22, 8), (44, 24, 6.5)):
        p.drawEllipse(QPointF(cx, cy), r, r)
    for x0, x1, y in ((6, 38, 34), (34, 58, 36)):
        corpo = QPainterPath(QPointF(x0, 54))
        corpo.cubicTo(QPointF(x0, y - 2), QPointF(x1, y - 2), QPointF(x1, 54))
        corpo.closeSubpath()
        p.drawPath(corpo)


def _i_info(p, cor):
    _traco(p, cor)
    p.drawEllipse(QPointF(32, 32), 23, 23)
    p.drawLine(QPointF(32, 29), QPointF(32, 46))
    p.setBrush(QColor(cor))
    p.drawEllipse(QPointF(32, 19), 3, 3)


def _i_fechar(p, cor):
    _traco(p, cor, 6)
    p.drawLine(QPointF(16, 16), QPointF(48, 48))
    p.drawLine(QPointF(48, 16), QPointF(16, 48))


# ---------------------------------------------------------------- 2ª passada (botões, menus, diálogos)
def _cheio(p, cor):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(cor))


def _i_cadeado(p, cor, aberto=False):
    _traco(p, cor)
    arco = QPainterPath(QPointF(20, 30))
    arco.lineTo(20, 20)
    arco.cubicTo(QPointF(20, 4), QPointF(44, 4), QPointF(44, 20))
    if not aberto:
        arco.lineTo(44, 30)
    p.drawPath(arco)
    _cheio(p, cor)
    p.drawRoundedRect(QRectF(12, 29, 40, 28), 4, 4)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
    p.drawEllipse(QPointF(32, 40), 4, 4)
    p.drawRect(QRectF(30.5, 40, 3, 9))
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)


def _i_cadeado_aberto(p, cor):
    p.save()
    p.translate(6, -2)
    _i_cadeado(p, cor, aberto=True)
    p.restore()


def _i_mais(p, cor):
    _traco(p, cor, 6)
    p.drawLine(QPointF(32, 12), QPointF(32, 52))
    p.drawLine(QPointF(12, 32), QPointF(52, 32))


def _i_menos(p, cor):
    _traco(p, cor, 6)
    p.drawLine(QPointF(12, 32), QPointF(52, 32))


def _i_lixeira(p, cor):
    _traco(p, cor)
    p.drawLine(QPointF(10, 16), QPointF(54, 16))
    _linha(p, (24, 16), (26, 9), (38, 9), (40, 16))
    _linha(p, (15, 16), (19, 56), (45, 56), (49, 16))
    _traco(p, cor, 3.4)
    for x in (26, 32, 38):
        p.drawLine(QPointF(x, 25), QPointF(x, 47))


def _i_salvar(p, cor):
    _traco(p, cor)
    p.drawPolygon(QPolygonF([QPointF(*q) for q in ((10, 10), (46, 10), (54, 18), (54, 54), (10, 54))]))
    p.drawRect(QRectF(20, 10, 20, 13))
    _cheio(p, cor)
    p.drawRoundedRect(QRectF(18, 34, 28, 20), 2, 2)


def _i_aviso(p, cor):
    _traco(p, cor)
    p.drawPolygon(QPolygonF([QPointF(32, 8), QPointF(57, 54), QPointF(7, 54)]))
    p.drawLine(QPointF(32, 24), QPointF(32, 39))
    _cheio(p, cor)
    p.drawEllipse(QPointF(32, 47), 3, 3)


def _i_raio(p, cor):
    _cheio(p, cor)
    p.drawPolygon(QPolygonF([QPointF(*q) for q in ((38, 4), (14, 36), (30, 36), (24, 60), (50, 26), (34, 26), (42, 4))]))


def _i_lapis(p, cor):
    p.save()
    p.translate(32, 32)
    p.rotate(45)
    _traco(p, cor)
    p.drawRect(QRectF(-7, -26, 14, 38))
    p.drawLine(QPointF(-7, -18), QPointF(7, -18))
    _cheio(p, cor)
    p.drawPolygon(QPolygonF([QPointF(-7, 14), QPointF(7, 14), QPointF(0, 27)]))
    p.restore()


def _i_tesoura(p, cor):
    _traco(p, cor)
    p.drawEllipse(QPointF(18, 46), 8, 8)
    p.drawEllipse(QPointF(46, 46), 8, 8)
    p.drawLine(QPointF(24, 40), QPointF(46, 8))
    p.drawLine(QPointF(40, 40), QPointF(18, 8))


def _i_pasta(p, cor):
    _traco(p, cor)
    p.drawPolygon(QPolygonF([QPointF(*q) for q in ((8, 14), (26, 14), (31, 20), (56, 20), (56, 52), (8, 52))]))
    p.drawLine(QPointF(8, 27), QPointF(56, 27))


def _i_chave(p, cor):
    _traco(p, cor)
    p.drawEllipse(QPointF(18, 32), 10, 10)
    p.drawLine(QPointF(28, 32), QPointF(56, 32))
    p.drawLine(QPointF(46, 32), QPointF(46, 42))
    p.drawLine(QPointF(54, 32), QPointF(54, 40))


def _i_mochila(p, cor):
    _traco(p, cor)
    alca = QPainterPath(QPointF(24, 16))
    alca.cubicTo(QPointF(24, 6), QPointF(40, 6), QPointF(40, 16))
    p.drawPath(alca)
    p.drawRoundedRect(QRectF(13, 16, 38, 40), 9, 9)
    p.drawRoundedRect(QRectF(21, 34, 22, 14), 3, 3)


def _i_caveira(p, cor):
    _cheio(p, cor)
    cab = QPainterPath()
    cab.addEllipse(QPointF(32, 28), 20, 19)
    cab.addRoundedRect(QRectF(21, 36, 22, 18), 3, 3)
    p.drawPath(cab.simplified())
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
    p.drawEllipse(QPointF(24, 29), 5.5, 6)
    p.drawEllipse(QPointF(40, 29), 5.5, 6)
    p.drawPolygon(QPolygonF([QPointF(32, 36), QPointF(29, 42), QPointF(35, 42)]))
    for x in (27, 32, 37):
        p.drawRect(QRectF(x - 1, 47, 2, 7))
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)


def _i_cruz(p, cor):
    _cheio(p, cor)
    p.drawRoundedRect(QRectF(25, 8, 14, 48), 3, 3)
    p.drawRoundedRect(QRectF(8, 25, 48, 14), 3, 3)


def _i_lista(p, cor):
    _traco(p, cor)
    p.drawRoundedRect(QRectF(12, 10, 40, 46), 4, 4)
    _cheio(p, cor)
    p.drawRoundedRect(QRectF(23, 6, 18, 9), 2, 2)
    _traco(p, cor, 3.4)
    for y in (26, 36, 46):
        p.drawLine(QPointF(20, y), QPointF(44, y))


def _i_pessoa(p, cor):
    _cheio(p, cor)
    p.drawEllipse(QPointF(32, 20), 11, 11)
    corpo = QPainterPath(QPointF(10, 58))
    corpo.cubicTo(QPointF(10, 30), QPointF(54, 30), QPointF(54, 58))
    corpo.closeSubpath()
    p.drawPath(corpo)


def _i_alto_falante(p, cor, mudo=False):
    _cheio(p, cor)
    p.drawPolygon(QPolygonF([QPointF(*q) for q in ((8, 24), (20, 24), (34, 10), (34, 54), (20, 40), (8, 40))]))
    _traco(p, cor, 4)
    if mudo:
        p.drawLine(QPointF(42, 24), QPointF(56, 40))
        p.drawLine(QPointF(56, 24), QPointF(42, 40))
        return
    for r in (9, 18):
        arco = QPainterPath()
        arco.arcMoveTo(QRectF(34 - r, 32 - r, 2 * r, 2 * r), -45)
        arco.arcTo(QRectF(34 - r, 32 - r, 2 * r, 2 * r), -45, 90)
        p.drawPath(arco)


def _i_mudo(p, cor):
    _i_alto_falante(p, cor, mudo=True)


def _i_repetir(p, cor):
    _traco(p, cor)
    _linha(p, (12, 34), (12, 22), (50, 22))
    _linha(p, (52, 30), (52, 42), (14, 42))
    _cheio(p, cor)
    p.drawPolygon(QPolygonF([QPointF(44, 13), QPointF(56, 22), QPointF(44, 31)]))
    p.drawPolygon(QPolygonF([QPointF(20, 33), QPointF(8, 42), QPointF(20, 51)]))


def _i_teclado(p, cor):
    """(v0.58) Teclado: a tela de atalhos (F1)."""
    _traco(p, cor, 4)
    p.drawRoundedRect(QRectF(6, 16, 52, 34), 6, 6)
    p.setBrush(QColor(cor))
    for lin, y in enumerate((24, 33)):
        for k in range(5 - lin):
            p.drawRect(QRectF(12 + lin * 4 + k * 9, y, 5, 4))
    p.drawRect(QRectF(18, 42, 28, 4))


def _i_lupa(p, cor):
    _traco(p, cor, 5)
    p.drawEllipse(QPointF(27, 27), 15, 15)
    p.drawLine(QPointF(38, 38), QPointF(54, 54))


def _seta_bandeja(p, cor, pra_cima):
    _traco(p, cor)
    _linha(p, (10, 40), (10, 54), (54, 54), (54, 40))
    p.drawLine(QPointF(32, 8), QPointF(32, 42))
    if pra_cima:
        _linha(p, (20, 20), (32, 8), (44, 20))
    else:
        _linha(p, (20, 30), (32, 42), (44, 30))


def _i_exportar(p, cor):
    _seta_bandeja(p, cor, True)


def _i_importar(p, cor):
    _seta_bandeja(p, cor, False)


def _i_explosao(p, cor):
    import math
    _cheio(p, cor)
    pts = []
    for k in range(16):
        r = 26 if k % 2 == 0 else 12
        a = math.radians(k * 22.5 - 90)
        pts.append(QPointF(32 + math.cos(a) * r, 32 + math.sin(a) * r))
    p.drawPolygon(QPolygonF(pts))


def _i_ao_vivo(p, cor):
    _traco(p, cor, 4)
    for r in (14, 24):
        for ang in (135, -45):
            arco = QPainterPath()
            arco.arcMoveTo(QRectF(32 - r, 32 - r, 2 * r, 2 * r), ang - 35)
            arco.arcTo(QRectF(32 - r, 32 - r, 2 * r, 2 * r), ang - 35, 70)
            p.drawPath(arco)
    _cheio(p, cor)
    p.drawEllipse(QPointF(32, 32), 7, 7)


def _i_sussurro(p, cor):
    _traco(p, cor)
    balao = QPainterPath()
    balao.addRoundedRect(QRectF(8, 10, 48, 32), 9, 9)
    p.drawPath(balao)
    _linha(p, (18, 41), (16, 54), (30, 41))
    _traco(p, cor, 3.4)
    p.drawLine(QPointF(32, 18), QPointF(32, 34))
    p.drawLine(QPointF(20, 26), QPointF(44, 26))


def _i_correr(p, cor):
    _cheio(p, cor)
    p.drawEllipse(QPointF(40, 12), 6, 6)
    _traco(p, cor, 5)
    _linha(p, (22, 26), (34, 21), (30, 38), (40, 46), (38, 58))
    _linha(p, (30, 38), (20, 46), (10, 46))
    _linha(p, (34, 21), (42, 32), (52, 30))


def _i_mao(p, cor):
    _traco(p, cor, 4)
    for x, topo in ((20, 18), (28, 10), (36, 10), (44, 16)):
        p.drawLine(QPointF(x, 34), QPointF(x, topo))
    _linha(p, (12, 34), (20, 40))
    palma = QPainterPath(QPointF(16, 36))
    palma.cubicTo(QPointF(16, 58), QPointF(48, 60), QPointF(48, 34))
    palma.lineTo(48, 18)
    p.drawPath(palma)


def _i_monstro(p, cor):
    _cheio(p, cor)
    cab = QPainterPath(QPointF(12, 8))
    cab.lineTo(22, 22)
    cab.lineTo(42, 22)
    cab.lineTo(52, 8)
    cab.lineTo(54, 34)
    cab.cubicTo(QPointF(54, 56), QPointF(10, 56), QPointF(10, 34))
    cab.closeSubpath()
    p.drawPath(cab)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
    p.drawPolygon(QPolygonF([QPointF(19, 31), QPointF(29, 35), QPointF(20, 38)]))
    p.drawPolygon(QPolygonF([QPointF(45, 31), QPointF(35, 35), QPointF(44, 38)]))
    p.drawPolygon(QPolygonF([QPointF(22, 44), QPointF(42, 44), QPointF(38, 49), QPointF(26, 49)]))
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)


def _i_calendario(p, cor):
    _traco(p, cor)
    p.drawRoundedRect(QRectF(9, 13, 46, 42), 4, 4)
    p.drawLine(QPointF(9, 25), QPointF(55, 25))
    p.drawLine(QPointF(21, 7), QPointF(21, 18))
    p.drawLine(QPointF(43, 7), QPointF(43, 18))
    _cheio(p, cor)
    for x in (20, 32, 44):
        for y in (35, 45):
            p.drawEllipse(QPointF(x, y), 2.6, 2.6)


def _i_castelo(p, cor):
    _traco(p, cor)
    p.drawPolygon(QPolygonF([QPointF(*q) for q in (
        (8, 56), (8, 14), (16, 14), (16, 20), (22, 20), (22, 14), (30, 14), (30, 26), (34, 26), (34, 14),
        (42, 14), (42, 20), (48, 20), (48, 14), (56, 14), (56, 56))]))
    porta = QPainterPath(QPointF(26, 56))
    porta.lineTo(26, 44)
    porta.cubicTo(QPointF(26, 36), QPointF(38, 36), QPointF(38, 44))
    porta.lineTo(38, 56)
    p.drawPath(porta)


def _i_escudo(p, cor):
    _traco(p, cor)
    esc = QPainterPath(QPointF(32, 6))
    esc.lineTo(54, 14)
    esc.cubicTo(QPointF(54, 38), QPointF(44, 50), QPointF(32, 58))
    esc.cubicTo(QPointF(20, 50), QPointF(10, 38), QPointF(10, 14))
    esc.closeSubpath()
    p.drawPath(esc)
    p.drawLine(QPointF(32, 14), QPointF(32, 48))


def _i_pino(p, cor):
    _traco(p, cor)
    gota = QPainterPath(QPointF(32, 58))
    gota.cubicTo(QPointF(18, 40), QPointF(12, 32), QPointF(12, 26))
    gota.cubicTo(QPointF(12, 2), QPointF(52, 2), QPointF(52, 26))
    gota.cubicTo(QPointF(52, 32), QPointF(46, 40), QPointF(32, 58))
    p.drawPath(gota)
    _cheio(p, cor)
    p.drawEllipse(QPointF(32, 25), 7, 7)


def _i_paleta(p, cor):
    _traco(p, cor)
    pal = QPainterPath(QPointF(32, 8))
    pal.cubicTo(QPointF(6, 8), QPointF(4, 46), QPointF(26, 56))
    pal.cubicTo(QPointF(36, 60), QPointF(36, 46), QPointF(42, 44))
    pal.cubicTo(QPointF(56, 42), QPointF(60, 8), QPointF(32, 8))
    p.drawPath(pal)
    _cheio(p, cor)
    for x, y in ((22, 22), (34, 18), (44, 26), (18, 36)):
        p.drawEllipse(QPointF(x, y), 4, 4)


def _i_proximo(p, cor):
    _cheio(p, cor)
    p.drawPolygon(QPolygonF([QPointF(10, 14), QPointF(30, 32), QPointF(10, 50)]))
    p.drawPolygon(QPolygonF([QPointF(30, 14), QPointF(50, 32), QPointF(30, 50)]))
    p.drawRect(QRectF(50, 14, 5, 36))


def _i_sol(p, cor):
    import math
    _traco(p, cor, 4)
    p.drawEllipse(QPointF(32, 32), 11, 11)
    for k in range(8):
        a = math.radians(k * 45)
        p.drawLine(QPointF(32 + math.cos(a) * 18, 32 + math.sin(a) * 18), QPointF(32 + math.cos(a) * 26, 32 + math.sin(a) * 26))


def _i_floco(p, cor):
    import math
    _traco(p, cor, 4)
    for k in range(3):
        a = math.radians(k * 60)
        dx, dy = math.cos(a) * 24, math.sin(a) * 24
        p.drawLine(QPointF(32 - dx, 32 - dy), QPointF(32 + dx, 32 + dy))


def _i_gota(p, cor):
    _traco(p, cor)
    gota = QPainterPath(QPointF(32, 6))
    gota.cubicTo(QPointF(44, 24), QPointF(50, 32), QPointF(50, 40))
    gota.cubicTo(QPointF(50, 62), QPointF(14, 62), QPointF(14, 40))
    gota.cubicTo(QPointF(14, 32), QPointF(20, 24), QPointF(32, 6))
    p.drawPath(gota)


def _i_folha(p, cor):
    _traco(p, cor)
    f = QPainterPath(QPointF(10, 54))
    f.cubicTo(QPointF(8, 20), QPointF(30, 8), QPointF(56, 8))
    f.cubicTo(QPointF(56, 34), QPointF(44, 56), QPointF(10, 54))
    p.drawPath(f)
    p.drawLine(QPointF(10, 54), QPointF(40, 24))


def _i_tijolos(p, cor):
    _parede(p, cor)


def _i_brilho(p, cor):
    _i_magia(p, cor)


def _i_circulo(p, cor):
    _cheio(p, cor)
    p.drawEllipse(QPointF(32, 32), 14, 14)


def _i_circulo_vazio(p, cor):
    _traco(p, cor, 4)
    p.drawEllipse(QPointF(32, 32), 13, 13)


def _i_musica(p, cor):
    _i_som(p, cor)


def _i_fones(p, cor):
    _traco(p, cor, 5)
    arco = QPainterPath(QPointF(12, 40))
    arco.cubicTo(QPointF(8, 6), QPointF(56, 6), QPointF(52, 40))
    p.drawPath(arco)
    _cheio(p, cor)
    p.drawRoundedRect(QRectF(8, 36, 12, 20), 4, 4)
    p.drawRoundedRect(QRectF(44, 36, 12, 20), 4, 4)


def _i_livro(p, cor):
    _i_biblioteca(p, cor)


def _i_vulcao(p, cor):
    _traco(p, cor)
    _linha(p, (6, 56), (24, 24), (40, 24), (58, 56))
    _cheio(p, cor)
    for x, y, r in ((26, 14, 4), (34, 9, 3.5), (40, 16, 3)):
        p.drawEllipse(QPointF(x, y), r, r)


def _i_chuva(p, cor):
    _traco(p, cor)
    nuvem = QPainterPath(QPointF(16, 34))
    nuvem.cubicTo(QPointF(4, 34), QPointF(6, 18), QPointF(18, 20))
    nuvem.cubicTo(QPointF(20, 6), QPointF(40, 6), QPointF(42, 18))
    nuvem.cubicTo(QPointF(58, 16), QPointF(60, 34), QPointF(48, 34))
    nuvem.closeSubpath()
    p.drawPath(nuvem)
    _traco(p, cor, 3.6)
    for x in (20, 32, 44):
        p.drawLine(QPointF(x, 42), QPointF(x - 4, 54))


def _i_frasco(p, cor):
    _traco(p, cor)
    _linha(p, (24, 8), (40, 8))
    fr = QPainterPath(QPointF(27, 8))
    fr.lineTo(27, 24)
    fr.lineTo(10, 52)
    fr.cubicTo(QPointF(8, 57), QPointF(10, 58), QPointF(16, 58))
    fr.lineTo(48, 58)
    fr.cubicTo(QPointF(54, 58), QPointF(56, 57), QPointF(54, 52))
    fr.lineTo(37, 24)
    fr.lineTo(37, 8)
    p.drawPath(fr)
    _cheio(p, cor)
    p.drawPolygon(QPolygonF([QPointF(17, 42), QPointF(47, 42), QPointF(53, 53), QPointF(11, 53)]))


def _i_lua(p, cor):
    _cheio(p, cor)
    lua = QPainterPath()
    lua.addEllipse(QPointF(32, 32), 24, 24)
    corte = QPainterPath()
    corte.addEllipse(QPointF(44, 24), 20, 20)
    p.drawPath(lua.subtracted(corte))


def _i_teia(p, cor):
    import math
    _traco(p, cor, 3)
    for k in range(8):
        a = math.radians(k * 45)
        p.drawLine(QPointF(32, 32), QPointF(32 + math.cos(a) * 27, 32 + math.sin(a) * 27))
    for r in (9, 17, 25):
        pts = [QPointF(32 + math.cos(math.radians(k * 45)) * r, 32 + math.sin(math.radians(k * 45)) * r) for k in range(8)]
        p.drawPolygon(QPolygonF(pts))


def _i_quadrado(p, cor):
    _traco(p, cor, 5)
    p.drawRect(QRectF(13, 13, 38, 38))


def _i_cone(p, cor):
    _traco(p, cor)
    c = QColor(cor)
    c.setAlpha(70)
    p.setBrush(c)
    p.drawPolygon(QPolygonF([QPointF(8, 32), QPointF(56, 10), QPointF(56, 54)]))


def _i_linha_reta(p, cor):
    _traco(p, cor)
    c = QColor(cor)
    c.setAlpha(70)
    p.setBrush(c)
    p.drawRect(QRectF(6, 26, 52, 12))


def _i_onda(p, cor):
    _traco(p, cor, 4)
    for r in (8, 16, 24):
        p.drawEllipse(QPointF(32, 32), r, r * 0.55)


def _i_pedra(p, cor):
    _traco(p, cor)
    c = QColor(cor)
    c.setAlpha(60)
    p.setBrush(c)
    p.drawPolygon(QPolygonF([QPointF(*q) for q in ((8, 50), (14, 28), (30, 14), (48, 18), (58, 40), (50, 54), (20, 56))]))
    _linha(p, (30, 14), (28, 34), (14, 28))
    _linha(p, (28, 34), (50, 54))


def _i_tremor(p, cor):
    _traco(p, cor, 4)
    p.drawRoundedRect(QRectF(22, 10, 20, 44), 4, 4)
    for x0, s in ((14, -1), (50, 1)):
        _linha(p, (x0, 20), (x0 + 4 * s, 26), (x0, 32), (x0 + 4 * s, 38), (x0, 44))


# ---------------------------------------------------------------- condições (painel + em cima do token)
def _c_envenenado(p, cor):
    # frasco com bolhas subindo
    p.save()
    p.translate(4, 8)
    p.scale(0.86, 0.86)
    _i_frasco(p, cor)
    p.restore()
    _traco(p, cor, 3)
    for x, y, r in ((40, 8, 4), (48, 16, 3), (44, 2, 2)):
        p.drawEllipse(QPointF(x, y + 2), r, r)


def _c_sangrando(p, cor):
    _cheio(p, cor)
    for cx, cy, s in ((26, 30, 1.0), (46, 46, 0.5)):
        g = QPainterPath(QPointF(cx, cy - 24 * s))
        g.cubicTo(QPointF(cx + 12 * s, cy - 6 * s), QPointF(cx + 16 * s, cy + 2 * s), QPointF(cx + 16 * s, cy + 8 * s))
        g.cubicTo(QPointF(cx + 16 * s, cy + 28 * s), QPointF(cx - 16 * s, cy + 28 * s), QPointF(cx - 16 * s, cy + 8 * s))
        g.cubicTo(QPointF(cx - 16 * s, cy + 2 * s), QPointF(cx - 12 * s, cy - 6 * s), QPointF(cx, cy - 24 * s))
        p.drawPath(g)


def _c_ferido(p, cor):
    p.save()
    p.translate(32, 32)
    p.rotate(-45)
    _traco(p, cor)
    p.drawRoundedRect(QRectF(-26, -10, 52, 20), 10, 10)
    p.drawRect(QRectF(-9, -10, 18, 20))
    _cheio(p, cor)
    for x, y in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
        p.drawEllipse(QPointF(x, y), 1.8, 1.8)
    p.restore()


def _c_inconsciente(p, cor):
    _traco(p, cor, 4.4)
    _linha(p, (10, 30), (30, 30), (10, 54), (30, 54))
    _traco(p, cor, 3.6)
    _linha(p, (36, 12), (52, 12), (36, 30), (52, 30))


def _c_caido(p, cor):
    _traco(p, cor)
    p.drawLine(QPointF(8, 54), QPointF(56, 54))
    p.drawLine(QPointF(32, 8), QPointF(32, 42))
    _linha(p, (20, 30), (32, 42), (44, 30))


def _c_agarrado(p, cor):
    _traco(p, cor)
    p.drawRoundedRect(QRectF(12, 20, 38, 30), 9, 9)
    for x in (22, 31, 40):
        p.drawLine(QPointF(x, 20), QPointF(x, 32))
    _linha(p, (12, 34), (6, 30), (8, 22), (16, 22))
    p.drawLine(QPointF(24, 50), QPointF(24, 58))
    p.drawLine(QPointF(40, 50), QPointF(40, 58))


def _c_impedido(p, cor):
    # corrente: elos alternando de frente (oval aberto) e de lado (traço grosso)
    _traco(p, cor, 4)
    for k, (cx, cy) in enumerate(((16, 16), (32, 32), (48, 48))):
        p.save()
        p.translate(cx, cy)
        p.rotate(45)
        if k % 2 == 0:
            p.drawRoundedRect(QRectF(-13, -7.5, 26, 15), 7.5, 7.5)
        else:
            _traco(p, cor, 6)
            p.drawLine(QPointF(-12, 0), QPointF(12, 0))
            _traco(p, cor, 4)
        p.restore()


def _c_atordoado(p, cor):
    import math
    _traco(p, cor, 4)
    pts = []
    for k in range(60):
        a = k * 0.32
        r = 3 + k * 0.42
        pts.append((32 + math.cos(a) * r, 32 + math.sin(a) * r))
    _linha(p, *pts)


def _c_paralisado(p, cor):
    _traco(p, cor, 3.6)
    p.drawEllipse(QPointF(32, 32), 26, 26)
    p.save()
    p.translate(32, 32)
    p.scale(0.72, 0.72)
    p.translate(-32, -32)
    _i_raio(p, cor)
    p.restore()


def _c_incapacitado(p, cor):
    _traco(p, cor, 5)
    p.drawEllipse(QPointF(32, 32), 23, 23)
    p.drawLine(QPointF(16, 48), QPointF(48, 16))


def _c_amedrontado(p, cor):
    _traco(p, cor)
    p.drawEllipse(QPointF(32, 32), 24, 24)
    _cheio(p, cor)
    p.drawEllipse(QPointF(24, 26), 3.5, 4.5)
    p.drawEllipse(QPointF(40, 26), 3.5, 4.5)
    _traco(p, cor, 3.6)
    p.drawEllipse(QPointF(32, 43), 5, 7)
    _linha(p, (17, 16), (23, 18))
    _linha(p, (47, 16), (41, 18))


def _c_enfeiticado(p, cor):
    _cheio(p, cor)
    c = QPainterPath(QPointF(32, 56))
    c.cubicTo(QPointF(4, 36), QPointF(6, 10), QPointF(22, 10))
    c.cubicTo(QPointF(28, 10), QPointF(32, 16), QPointF(32, 20))
    c.cubicTo(QPointF(32, 16), QPointF(36, 10), QPointF(42, 10))
    c.cubicTo(QPointF(58, 10), QPointF(60, 36), QPointF(32, 56))
    p.drawPath(c)


def _c_cego(p, cor):
    _i_olho(p, cor)
    _traco(p, cor, 5)
    p.drawLine(QPointF(10, 54), QPointF(54, 10))


def _c_surdo(p, cor):
    _traco(p, cor)
    orelha = QPainterPath(QPointF(20, 26))
    orelha.cubicTo(QPointF(20, 6), QPointF(48, 6), QPointF(48, 26))
    orelha.cubicTo(QPointF(48, 38), QPointF(36, 40), QPointF(36, 50))
    orelha.cubicTo(QPointF(36, 58), QPointF(24, 58), QPointF(24, 50))
    p.drawPath(orelha)
    _traco(p, cor, 3.4)
    dentro = QPainterPath(QPointF(28, 26))
    dentro.cubicTo(QPointF(28, 16), QPointF(40, 16), QPointF(40, 26))
    p.drawPath(dentro)
    _traco(p, cor, 5)
    p.drawLine(QPointF(10, 54), QPointF(54, 10))


def _c_invisivel(p, cor):
    pen = _caneta(cor, 4)
    pen.setDashPattern([2.2, 1.6])
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    f = QPainterPath(QPointF(12, 56))
    f.lineTo(12, 28)
    f.cubicTo(QPointF(12, 2), QPointF(52, 2), QPointF(52, 28))
    f.lineTo(52, 56)
    f.lineTo(45, 50)
    f.lineTo(38, 56)
    f.lineTo(32, 50)
    f.lineTo(26, 56)
    f.lineTo(19, 50)
    f.closeSubpath()
    p.drawPath(f)
    _cheio(p, cor)
    p.drawEllipse(QPointF(25, 28), 3.5, 4.5)
    p.drawEllipse(QPointF(39, 28), 3.5, 4.5)


def _c_exaustao(p, cor):
    _traco(p, cor)
    p.drawRoundedRect(QRectF(6, 18, 46, 28), 4, 4)
    _cheio(p, cor)
    p.drawRoundedRect(QRectF(52, 26, 6, 12), 2, 2)
    p.drawRoundedRect(QRectF(11, 23, 9, 18), 2, 2)


def _c_concentrando(p, cor):
    _traco(p, cor, 3.6)
    for r in (24, 15):
        p.drawEllipse(QPointF(32, 32), r, r)
    _cheio(p, cor)
    p.drawEllipse(QPointF(32, 32), 6, 6)


def _c_abencoado(p, cor):
    _traco(p, cor, 4)
    p.drawEllipse(QPointF(32, 14), 16, 6)
    _cheio(p, cor)
    cx, cy, r = 32, 40, 16
    p.drawPolygon(QPolygonF([QPointF(cx, cy - r), QPointF(cx + r * 0.24, cy - r * 0.24), QPointF(cx + r, cy),
                             QPointF(cx + r * 0.24, cy + r * 0.24), QPointF(cx, cy + r), QPointF(cx - r * 0.24, cy + r * 0.24),
                             QPointF(cx - r, cy), QPointF(cx - r * 0.24, cy - r * 0.24)]))


DESENHOS = {"selecionar": _selecionar, "terreno": _terreno, "borracha": _borracha,
            "luz": _luz,
            "borracha_parede": _borracha_parede,
            "parede": _parede, "sala": _sala, "porta": _porta}


DESENHOS.update({
    "mapa": _i_mapa, "token": _i_token, "snap": _i_snap, "objetos": _i_objetos, "biblioteca": _i_biblioteca,
    "combate": _i_combate, "chat": _i_chat, "dados": _i_dados, "historico": _i_historico,
    "atmosfera": _i_atmosfera, "projetor": _i_projetor, "nevoa": _i_nevoa, "taverna": _i_taverna,
    "olho": _i_olho, "ficha": _i_ficha, "pdf": _i_pdf, "diario": _i_diario, "som": _i_som,
    "imagens": _i_imagens, "banco": _i_banco, "sair": _i_sair, "alvo": _i_alvo, "enquadrar": _i_enquadrar,
    "magia": _i_magia, "engrenagem": _i_engrenagem, "chama": _i_chama, "camadas": _i_camadas,
    "propriedades": _i_propriedades, "jogadores": _i_jogadores, "info": _i_info, "fechar": _i_fechar,
    "cursor": _selecionar,
    # 2ª passada
    "cadeado": _i_cadeado, "cadeado_aberto": _i_cadeado_aberto, "mais": _i_mais, "menos": _i_menos,
    "lixeira": _i_lixeira, "salvar": _i_salvar, "aviso": _i_aviso, "raio": _i_raio, "lapis": _i_lapis,
    "tesoura": _i_tesoura, "pasta": _i_pasta, "chave": _i_chave, "mochila": _i_mochila,
    "caveira": _i_caveira, "cruz": _i_cruz, "lista": _i_lista, "pessoa": _i_pessoa,
    "alto_falante": _i_alto_falante, "mudo": _i_mudo, "repetir": _i_repetir, "lupa": _i_lupa, "teclado": _i_teclado,
    "exportar": _i_exportar, "importar": _i_importar, "explosao": _i_explosao, "ao_vivo": _i_ao_vivo,
    "sussurro": _i_sussurro, "correr": _i_correr, "mao": _i_mao, "monstro": _i_monstro,
    "calendario": _i_calendario, "castelo": _i_castelo, "escudo": _i_escudo, "pino": _i_pino,
    "paleta": _i_paleta, "proximo": _i_proximo, "sol": _i_sol, "floco": _i_floco, "gota": _i_gota,
    "folha": _i_folha, "tijolos": _i_tijolos, "brilho": _i_brilho, "circulo": _i_circulo,
    "circulo_vazio": _i_circulo_vazio, "musica": _i_musica, "fones": _i_fones, "livro": _i_livro,
    "vulcao": _i_vulcao, "chuva": _i_chuva,
    "frasco": _i_frasco, "lua": _i_lua, "teia": _i_teia, "quadrado": _i_quadrado, "cone": _i_cone,
    "linha_reta": _i_linha_reta, "onda": _i_onda, "pedra": _i_pedra, "tremor": _i_tremor,
    # condições: "cond_" + a chave de jogo/condicoes.py
    "cond_envenenado": _c_envenenado, "cond_sangrando": _c_sangrando, "cond_ferido": _c_ferido,
    "cond_inconsciente": _c_inconsciente, "cond_caido": _c_caido, "cond_agarrado": _c_agarrado,
    "cond_impedido": _c_impedido, "cond_atordoado": _c_atordoado, "cond_paralisado": _c_paralisado,
    "cond_incapacitado": _c_incapacitado, "cond_petrificado": _i_pedra, "cond_amedrontado": _c_amedrontado,
    "cond_enfeiticado": _c_enfeiticado, "cond_cego": _c_cego, "cond_surdo": _c_surdo,
    "cond_invisivel": _c_invisivel, "cond_exaustao": _c_exaustao, "cond_queimando": _i_chama,
    "cond_molhado": _i_gota, "cond_congelado": _i_floco, "cond_concentrando": _c_concentrando,
    "cond_abencoado": _c_abencoado,
})


_CACHE_PM = {}


def pixmap_cache(nome: str, cor: str, tam: int = TAM) -> QPixmap:
    """Igual a pixmap_icone, mas guarda o resultado (pra quem desenha toda hora, como o token)."""
    chave = (nome, cor, tam)
    pm = _CACHE_PM.get(chave)
    if pm is None:
        pm = _CACHE_PM[chave] = pixmap_icone(nome, cor, tam)
    return pm


def pixmap_icone(nome: str, cor: str, tam: int = TAM) -> QPixmap:
    pm = QPixmap(TAM, TAM)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    DESENHOS.get(nome, _i_info)(p, cor)
    p.end()
    if tam != TAM:
        pm = pm.scaled(tam, tam, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    return pm


_CACHE_TEMA = {}


def icone_tema(nome: str) -> QIcon:
    """Ícone nas cores do tema atual: normal = cor do texto · ligado/passando o mouse = cor de destaque."""
    from .tema import tema_atual
    t = tema_atual()
    chave = (nome, t["texto"], t["destaque"], t["fraco"])
    if chave in _CACHE_TEMA:
        return _CACHE_TEMA[chave]
    ic = QIcon()
    _CACHE_TEMA[chave] = ic
    ic.addPixmap(pixmap_icone(nome, t["texto"]), QIcon.Mode.Normal, QIcon.State.Off)
    ic.addPixmap(pixmap_icone(nome, t["destaque"]), QIcon.Mode.Normal, QIcon.State.On)
    ic.addPixmap(pixmap_icone(nome, t["destaque"]), QIcon.Mode.Active, QIcon.State.Off)
    ic.addPixmap(pixmap_icone(nome, t["destaque"]), QIcon.Mode.Active, QIcon.State.On)
    ic.addPixmap(pixmap_icone(nome, t["fraco"]), QIcon.Mode.Disabled, QIcon.State.Off)
    return ic


def icone(nome: str, cor: str = "#e8dcc4") -> QIcon:
    pm = QPixmap(TAM, TAM)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    DESENHOS[nome](p, cor)
    p.end()
    return QIcon(pm)
