"""
Materiais da INTERFACE (v0.49): cada tema tem o seu "kit" — a textura das placas e botões e a cantoneira
das molduras. Tudo gerado pelo programa (numpy + QPainter), nenhuma imagem de fora.

  medieval  madeira escura de tábuas, cantoneira de ferro com rebites e filete dourado
  moderno   painel fosco com grão fino, cantoneira de alumínio
  futurista metal escovado com hexágonos e linhas de luz, cantoneira chanfrada com LED
  magico    pedra arroxeada com veios brilhando, cantoneira de cristal
  terror    madeira podre manchada, cantoneira de ferro enferrujado com prego
  claro     pergaminho, cantoneira de latão
  escuro    ardósia lisa, cantoneira discreta

Usado pela tela inicial em QML (lancador.py → provedor de imagens "taverna") e, depois, pelos botões e
painéis do resto do programa.
"""

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient

from ..mesa import texturas as T

LADO = 256
_CACHE = {}


def _img(rgb: np.ndarray) -> QImage:
    a = np.clip(rgb * 255, 0, 255).astype(np.uint8)
    h, w = a.shape[:2]
    rgba = np.concatenate([a, np.full((h, w, 1), 255, np.uint8)], axis=2)
    return QImage(rgba.tobytes(), w, h, w * 4, QImage.Format.Format_RGBA8888).copy()


def _cor(h):
    return T.cor(h)


# ====================================================================== texturas (tileáveis)
def _madeira(rng, base="#3a2416", claro="#6a4428", tabuas=4, podre=False):
    w = h = LADO
    veio = T.ruido(w, h, 9, rng, cel_y=90)                   # fibras compridas na vertical
    nos = T.fbm(w, h, rng, [(48, 1.0), (16, 0.4)])
    t = np.clip(veio * 0.75 + nos * 0.35, 0, 1)
    rgb = T.misturar(_cor(base), _cor(claro), t)
    larg = w // tabuas
    x = np.arange(w)
    junta = (x % larg) < 2                                  # vão entre as tábuas
    rgb[:, junta] *= 0.35
    borda = ((x % larg) == 2) | ((x % larg) == larg - 1)
    rgb[:, borda] *= 1.18
    for k in range(tabuas):                                 # cada tábua num tom
        rgb[:, k * larg:(k + 1) * larg] *= 0.86 + 0.24 * rng.random()
    if podre:
        mancha = T.fbm(w, h, rng, [(70, 1.0), (24, 0.5)])
        rgb *= (1 - np.clip((mancha - 0.55) * 2.2, 0, 0.6))[..., None]
    return rgb


def _metal(rng, base="#1b2433", claro="#3a4a63", hexa=False, escovado=True):
    w = h = LADO
    risco = T.ruido(w, h, 3, rng, cel_y=120) if escovado else T.fbm(w, h, rng, [(32, 1)])
    rgb = T.misturar(_cor(base), _cor(claro), risco * 0.6 + 0.2)
    if hexa:
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        s = 32.0                                            # hexágonos (repete certinho em 256)
        q = xs / (s * 1.5)
        r = ys / (s * np.sqrt(3)) - (np.floor(q) % 2) * 0.5
        fq, fr = q - np.floor(q), r - np.floor(r)
        borda = np.minimum(np.minimum(fq, 1 - fq) * 3.0, np.minimum(fr, 1 - fr) * 4.0)
        linha = np.clip(1 - borda * 6, 0, 1)
        rgb = rgb * (1 - linha[..., None] * 0.45)
    return rgb


def _pedra(rng, base="#241a33", claro="#4a3a66", veio="#b48cff"):
    w = h = LADO
    n = T.fbm(w, h, rng, [(64, 1.0), (22, 0.5), (7, 0.25)])
    rgb = T.misturar(_cor(base), _cor(claro), n)
    v = T.sulcos(T.fbm(w, h, rng, [(90, 1.0), (30, 0.4)]), 0.02)
    rgb = rgb * (1 - v[..., None] * 0.2) + _cor(veio)[None, None, :] * v[..., None] * 0.55
    return rgb


def _pergaminho(rng):
    w = h = LADO
    n = T.fbm(w, h, rng, [(80, 1.0), (24, 0.4), (6, 0.15)])
    rgb = T.misturar(_cor("#d9c79f"), _cor("#f4ead2"), n)
    fibra = T.ruido(w, h, 2, rng, cel_y=40)
    return rgb * (0.94 + fibra[..., None] * 0.08)


def _fosco(rng, base, claro, grao=0.06):
    w = h = LADO
    n = T.fbm(w, h, rng, [(96, 1.0), (4, grao)])
    return T.misturar(_cor(base), _cor(claro), n * 0.5 + 0.25)


def textura(tema: str) -> QImage:
    """Textura 256×256 (repete sem emenda) das placas/botões do tema."""
    chave = ("tex", tema)
    if chave in _CACHE:
        return _CACHE[chave]
    import zlib
    rng = np.random.default_rng(zlib.crc32(tema.encode()))   # (hash() muda a cada vez que abre)
    rgb = {
        "medieval": lambda: _madeira(rng),
        "terror": lambda: _madeira(rng, "#1c1416", "#3a2a26", 5, podre=True),
        "futurista": lambda: _metal(rng, hexa=True),
        "moderno": lambda: _fosco(rng, "#1a1d22", "#2c3138"),
        "magico": lambda: _pedra(rng),
        "steampunk": lambda: _metal(rng, "#2a1c10", "#5a3e22", escovado=True),      # couro/cobre escuro
        "posapoc": lambda: _madeira(rng, "#24221a", "#4a4632", 3, podre=True),       # tábua velha e suja
        "claro": lambda: _pergaminho(rng),
        "escuro": lambda: _fosco(rng, "#16171a", "#23252a", 0.03),
    }.get(tema, lambda: _madeira(rng))()
    img = _img(rgb)
    _CACHE[chave] = img
    return img


# ====================================================================== cantoneiras (canto de cima-esquerda)
def cantoneira(tema: str, lado: int = 96) -> QImage:
    """Enfeite do canto da moldura, desenhado pro canto de CIMA-ESQUERDA (o QML gira pros outros)."""
    chave = ("canto", tema, lado)
    if chave in _CACHE:
        return _CACHE[chave]
    img = QImage(lado, lado, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(lado / 96, lado / 96)
    {"medieval": _canto_ferro, "terror": _canto_ferrugem, "futurista": _canto_chanfro,
     "magico": _canto_cristal, "claro": _canto_latao, "moderno": _canto_aluminio,
     "escuro": _canto_discreto, "steampunk": _canto_latao, "posapoc": _canto_ferrugem}.get(tema, _canto_ferro)(p)
    p.end()
    _CACHE[chave] = img
    return img


def _metal_grad(a, b, c, x0=0, y0=0, x1=60, y1=60):
    g = QLinearGradient(QPointF(x0, y0), QPointF(x1, y1))
    g.setColorAt(0, QColor(a))
    g.setColorAt(0.5, QColor(b))
    g.setColorAt(1, QColor(c))
    return QBrush(g)


def _rebite(p, x, y, r=4.2, cor="#9a9286"):
    g = QRadialGradient(QPointF(x - r * 0.35, y - r * 0.35), r * 1.4)
    g.setColorAt(0, QColor("#f2ece0"))
    g.setColorAt(0.45, QColor(cor))
    g.setColorAt(1, QColor("#2a2622"))
    p.setPen(QPen(QColor(10, 8, 6), 1))
    p.setBrush(QBrush(g))
    p.drawEllipse(QPointF(x, y), r, r)


def _l(p, larg, comp, brush, borda=QColor(8, 6, 5), raio=3):
    """Peça em L no canto."""
    cam = QPainterPath()
    cam.moveTo(2, 2)
    cam.lineTo(comp, 2)
    cam.lineTo(comp, larg)
    cam.lineTo(larg, larg)
    cam.lineTo(larg, comp)
    cam.lineTo(2, comp)
    cam.closeSubpath()
    p.setPen(QPen(borda, 1.6))
    p.setBrush(brush)
    p.drawPath(cam)
    return cam


def _canto_ferro(p):
    _l(p, 22, 90, _metal_grad("#6c665e", "#3a3632", "#1c1a18"))
    p.setPen(QPen(QColor("#c9a24a"), 1.4))            # filete dourado
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(8, 8), QPointF(84, 8))
    p.drawLine(QPointF(8, 8), QPointF(8, 84))
    # floreio de ferro batido
    p.setPen(QPen(QColor("#2a2622"), 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    f = QPainterPath(QPointF(22, 22))
    f.cubicTo(QPointF(40, 26), QPointF(44, 40), QPointF(34, 44))
    f.cubicTo(QPointF(28, 46), QPointF(26, 38), QPointF(31, 36))
    p.drawPath(f)
    for x, y in ((13, 13), (60, 13), (13, 60), (80, 13), (13, 80)):
        _rebite(p, x, y)


def _canto_ferrugem(p):
    _l(p, 18, 86, _metal_grad("#6a3a24", "#3a2018", "#160c0a"))
    rng = np.random.default_rng(4)
    p.setPen(Qt.PenStyle.NoPen)
    for _ in range(40):                               # pintas de ferrugem
        x, y = rng.uniform(3, 84), rng.uniform(3, 17)
        if rng.random() < 0.5:
            x, y = y, x
        p.setBrush(QColor(140, 70, 30, int(rng.uniform(60, 150))))
        p.drawEllipse(QPointF(x, y), rng.uniform(0.8, 2.2), rng.uniform(0.8, 2.2))
    _rebite(p, 11, 11, 5, "#5a3a2a")
    p.setPen(QPen(QColor(120, 20, 20, 170), 1.2))     # escorrido
    p.drawLine(QPointF(11, 16), QPointF(12, 34))


def _canto_chanfro(p):
    cam = QPainterPath()
    cam.moveTo(18, 2)
    cam.lineTo(92, 2)
    cam.lineTo(92, 12)
    cam.lineTo(26, 12)
    cam.lineTo(12, 26)
    cam.lineTo(12, 92)
    cam.lineTo(2, 92)
    cam.lineTo(2, 18)
    cam.closeSubpath()
    p.setPen(QPen(QColor("#38e1ff"), 1.4))
    p.setBrush(_metal_grad("#5a6a82", "#26324a", "#0e1424"))
    p.drawPath(cam)
    for x0, y0, x1, y1 in ((30, 7, 70, 7), (7, 30, 7, 70)):   # LED
        g = QLinearGradient(QPointF(x0, y0), QPointF(x1, y1))
        g.setColorAt(0, QColor(56, 225, 255, 0))
        g.setColorAt(0.5, QColor(170, 245, 255, 255))
        g.setColorAt(1, QColor(56, 225, 255, 0))
        p.setPen(QPen(QBrush(g), 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(x0, y0), QPointF(x1, y1))
    p.setPen(QPen(QColor("#ff3fa4"), 2))
    p.drawLine(QPointF(14, 22), QPointF(22, 14))


def _canto_cristal(p):
    _l(p, 14, 80, _metal_grad("#4a3a66", "#2a1f3d", "#120c1c"), QColor("#7d5bc4"))
    cam = QPainterPath()
    cam.moveTo(8, 30)
    cam.lineTo(16, 8)
    cam.lineTo(30, 4)
    cam.lineTo(24, 22)
    cam.closeSubpath()
    g = QLinearGradient(QPointF(8, 4), QPointF(30, 30))
    g.setColorAt(0, QColor("#ffffff"))
    g.setColorAt(0.4, QColor("#cdb0ff"))
    g.setColorAt(1, QColor("#6a3fd0"))
    p.setPen(QPen(QColor("#f0e6ff"), 1))
    p.setBrush(QBrush(g))
    p.drawPath(cam)
    brilho = QRadialGradient(QPointF(18, 16), 26)
    brilho.setColorAt(0, QColor(200, 160, 255, 140))
    brilho.setColorAt(1, QColor(200, 160, 255, 0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(brilho))
    p.drawEllipse(QPointF(18, 16), 26, 26)


def _canto_latao(p):
    _l(p, 12, 70, _metal_grad("#f0d48a", "#b8892e", "#6a4a14"), QColor("#4a3410"))
    _rebite(p, 9, 9, 3.6, "#c9a24a")


def _canto_aluminio(p):
    _l(p, 8, 54, _metal_grad("#e8ecf0", "#9aa4ae", "#5a636c"), QColor("#2a2f34"), 2)


def _canto_discreto(p):
    p.setPen(QPen(QColor("#7c9cff"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(4, 4), QPointF(40, 4))
    p.drawLine(QPointF(4, 4), QPointF(4, 40))
