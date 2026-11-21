"""
🍺 Cenários do tema Medieval (v0.56, referências do Manel). Cada vez que o programa abre, sorteia um:

  MESA   — a mesa da taverna em 3D (`qml/MesaTaverna3D.qml`), agora com um CONTRATO no meio: as opções do menu
           são escritas nele a tinta e o mouse RISCA UM CÍRCULO em volta (como quem marca o que vai assinar).
  QUADRO — o quadro de missões num muro de pedra (`qml/MedievalQuadro.qml`): o menu fica no cartaz grande do
           meio e o mouse circula a "missão" escolhida. Lamparina acesa tremendo à direita, hera nos cantos.

Aqui ficam os desenhos (jeitão pintado/pixelado das referências).
"""

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QLinearGradient, QPainterPath, QPen, QPolygonF, QRadialGradient

from .estilizado import _c, _caixa_borrar, _rgb_img, _rng, _ruido, _suave
from .terror_cenas import _guardado, _pintar, _pixelar, _rgba

# onde fica o cartaz grande dentro da imagem do quadro (frações) — o menu vai ali
QUADRO_W, QUADRO_H = 1600, 940
CARTAZ = (0.3, 0.25, 0.7, 0.74)


def imagem(partes):
    """quadro/<peca>/..."""
    peca = partes[1]
    if peca == "muro":
        w, h = int(float(partes[2])), int(float(partes[3]))
        return _guardado(("muro", w, h), lambda: _muro(w, h))
    f = {"quadro": _quadro, "lamparina": _lamparina, "hera": _hera_viva}[peca]
    return _guardado(("quadro", peca), f)


def textura(nome):
    """Texturas das cenas 3D do Medieval (contrato da mesa e as peças do quadro de missões)."""
    f = {"contrato": _contrato, "pedra_tijolo": _pedra_tijolo, "madeira_escura": lambda: _madeira_tex("#3e2814", True),
         "viga": lambda: _madeira_tex("#6a4424", False), "cartaz_texto": lambda: _cartaz_img("texto"),
         "cartaz_mapa": lambda: _cartaz_img("mapa"), "cartaz_grande": lambda: _cartaz_img("grande"),
         "bilhete": lambda: _cartaz_img("bussola"), "estandarte": _estandarte, "flamula": _flamula,
         "brasao_lobo": lambda: _brasao("lobo"), "brasao_torre": lambda: _brasao("torre"),
         "folha_hera": _folha_hera, "ferro_preto": _ferro_preto}.get(nome)
    return _guardado(("tex", nome), f) if f else None


def _pedra_tijolo(lado=256):
    rng = _rng("pedra-tijolo")
    n = _ruido(lado, lado, 10, rng) * 0.6 + _ruido(lado, lado, 3, rng) * 0.4
    cor = _c("#7a7680") * (0.6 + 0.6 * n[..., None])
    musgo = _suave((_ruido(lado, lado, 16, rng) - 0.7) * 6)
    cor = cor * (1 - musgo[..., None] * 0.5) + _c("#4a6a30") * musgo[..., None] * 0.5
    return _rgb_img(cor)


def _madeira_tex(base, vertical, lado=512):
    rng = _rng("madeira-tex", base)
    fibra = _caixa_borrar(rng.random((lado, lado)).astype(np.float32), 1)
    fibra = _caixa_borrar(fibra.T, 14).T if vertical else _caixa_borrar(fibra, 14)
    fibra = (fibra - fibra.min()) / max(1e-6, float(np.ptp(fibra)))
    n = _ruido(lado, lado, 30, rng)
    cor = _c(base) * (0.65 + 0.5 * fibra[..., None]) * (0.8 + 0.35 * n[..., None])
    return _rgb_img(cor)


def _ferro_preto(lado=128):
    rng = _rng("ferro-preto")
    n = _ruido(lado, lado, 6, rng)
    return _rgb_img(_c("#2e2e34") * (0.6 + 0.7 * n[..., None]))


def _cartaz_img(tipo):
    rng = _rng("cartaz-img", tipo)
    W, H = {"grande": (900, 960), "bussola": (240, 220)}.get(tipo, (600, 440))

    def d(p, W, H):
        if tipo == "grande":
            cam = _borda_rasgada(14, 14, W - 14, H - 14, rng, 14)
            _papel(p, cam, (0, 0, W, H), rng, "#c49a62")
            _floreio_cantos(p, 46, 46, W - 46, H - 46, QColor(70, 38, 14, 170), 40)
        elif tipo == "bussola":
            cam = _borda_rasgada(10, 10, W - 10, H - 10, rng, 5)
            _papel(p, cam, (0, 0, W, H), rng, queimado=False)
            cx, cy = W / 2, H / 2
            p.setPen(QPen(QColor(70, 40, 15, 220), 2))
            p.setBrush(QColor(70, 40, 15, 200))
            for a in range(0, 360, 45):
                comp = 70 if a % 90 == 0 else 38
                ra = math.radians(a)
                p.drawPolygon(QPolygonF([QPointF(cx, cy), QPointF(cx + math.cos(ra + 0.2) * 14, cy + math.sin(ra + 0.2) * 14),
                                         QPointF(cx + math.cos(ra) * comp, cy + math.sin(ra) * comp)]))
        else:
            _cartaz(p, 14, 14, W - 14, H - 14, rng, mapa=(tipo == "mapa"), pregos=False)
    return _pintar(W, H, d)


def _estandarte(W=512, H=420):
    """Estandarte vermelho com escudo, espadas, louros e franja dourada (ponta embaixo; fundo transparente)."""
    def d(p, W, H):
        bx = W / 2
        est = QPolygonF([QPointF(0, 0), QPointF(W, 0), QPointF(W, H * 0.72), QPointF(bx, H * 0.96), QPointF(0, H * 0.72)])
        g = QLinearGradient(0, 0, W, 0)
        g.setColorAt(0, QColor("#5a1210"))
        g.setColorAt(0.5, QColor("#9a2018"))
        g.setColorAt(1, QColor("#4a0e0c"))
        p.setPen(QPen(QColor("#2a0806"), 4))
        p.setBrush(QBrush(g))
        p.drawPolygon(est)
        p.setPen(QPen(QColor("#d8a84a"), 5))
        for k in range(30):
            t = k / 29
            x = W * t
            y = H * 0.72 + H * 0.24 * (1 - abs(t - 0.5) * 2) - 6
            p.drawLine(QPointF(x, y - 4), QPointF(x, y + 12))
        for lado in (-1, 1):
            p.save()
            p.translate(bx, H * 0.4)
            p.rotate(lado * 40)
            p.setPen(QPen(QColor("#1a1a20"), 2))
            p.setBrush(QColor("#b8bcc4"))
            p.drawPolygon(QPolygonF([QPointF(-7, -130), QPointF(7, -130), QPointF(7, 70), QPointF(0, 90), QPointF(-7, 70)]))
            p.setBrush(QColor("#8a6a3a"))
            p.drawRect(QRectF(-28, -134, 56, 10))
            p.setBrush(QColor("#4a2a14"))
            p.drawRect(QRectF(-6, -170, 12, 36))
            p.restore()
        esc = QPainterPath(QPointF(bx - 70, H * 0.2))
        esc.lineTo(QPointF(bx + 70, H * 0.2))
        esc.lineTo(QPointF(bx + 70, H * 0.38))
        esc.quadTo(QPointF(bx + 64, H * 0.52), QPointF(bx, H * 0.6))
        esc.quadTo(QPointF(bx - 64, H * 0.52), QPointF(bx - 70, H * 0.38))
        esc.closeSubpath()
        p.setPen(QPen(QColor("#2a1a0c"), 5))
        p.setBrush(QColor("#d8c08a"))
        p.drawPath(esc)
        p.save()
        p.setClipPath(esc)
        p.fillRect(QRectF(bx - 70, H * 0.2, 70, H * 0.2), QColor("#5a3a20"))
        p.fillRect(QRectF(bx, H * 0.4, 70, H * 0.3), QColor("#5a3a20"))
        p.restore()
        p.setPen(QPen(QColor("#d8a84a"), 5))
        for lado in (-1, 1):
            for k in range(6):
                a = math.radians(200 - k * 22) if lado < 0 else math.radians(-20 + k * 22)
                p.drawEllipse(QPointF(bx + math.cos(a) * 120, H * 0.42 + math.sin(a) * 90), 9, 5)
    return _pintar(W, H, d)


def _flamula(W=96, H=320):
    def d(p, W, H):
        p.setPen(QPen(QColor("#2a0a08"), 2))
        p.setBrush(QColor("#7a1a16"))
        p.drawPolygon(QPolygonF([QPointF(0, 0), QPointF(W, 0), QPointF(W, H), QPointF(W / 2, H * 0.82), QPointF(0, H)]))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#d8c08a"))
        p.drawRect(QRectF(W * 0.34, 0, W * 0.32, H * 0.8))
    return _pintar(W, H, d)


def _brasao(forma, lado=256):
    def d(p, W, H):
        cx, cy = W / 2, H / 2
        p.setPen(QPen(QColor("#1a1008"), 6))
        p.setBrush(QColor("#6a4a28"))
        if forma == "lobo":
            p.drawEllipse(QPointF(cx, cy), W * 0.47, H * 0.47)
            p.setBrush(QColor("#c8a46a"))
            p.setPen(QPen(QColor("#1a1008"), 3))
            s = W / 128
            p.drawPolygon(QPolygonF([QPointF(cx + x * s, cy + y * s) for (x, y) in
                                     ((-30, -38), (-14, -10), (-26, 16), (-6, 36), (20, 30), (34, 8), (18, -6),
                                      (24, -36), (4, -20), (-10, -24))]))
            p.setBrush(QColor("#1a1008"))
            p.drawEllipse(QPointF(cx + 4 * s, cy - 4 * s), 3 * s, 3 * s)
        else:
            esc = QPainterPath(QPointF(W * 0.08, H * 0.06))
            esc.lineTo(QPointF(W * 0.92, H * 0.06))
            esc.lineTo(QPointF(W * 0.92, H * 0.6))
            esc.lineTo(QPointF(cx, H * 0.96))
            esc.lineTo(QPointF(W * 0.08, H * 0.6))
            esc.closeSubpath()
            p.drawPath(esc)
            p.setBrush(QColor("#c8a46a"))
            p.setPen(QPen(QColor("#1a1008"), 3))
            p.drawRect(QRectF(cx - 40, H * 0.36, 80, 80))
            for dx in (-40, -12, 16):
                p.drawRect(QRectF(cx + dx, H * 0.26, 24, 22))
            p.setBrush(QColor("#1a1008"))
            p.drawRect(QRectF(cx - 12, H * 0.5, 24, 38))
    return _pintar(lado, lado, d)


def _folha_hera(lado=128):
    def d(p, W, H):
        r = W * 0.46
        p.translate(W / 2, H / 2)
        folha = QPainterPath(QPointF(0, -r))
        for (x, y) in ((0.5, -0.5), (1, -0.1), (0.4, 0.2), (0, 1), (-0.4, 0.2), (-1, -0.1), (-0.5, -0.5)):
            folha.lineTo(QPointF(x * r, y * r))
        folha.closeSubpath()
        p.setPen(QPen(QColor(20, 40, 14), 3))
        p.setBrush(QColor(70, 120, 52))
        p.drawPath(folha)
        p.setPen(QPen(QColor(150, 190, 110, 160), 3))
        p.drawLine(QPointF(0, -r * 0.7), QPointF(0, r * 0.7))
    return _pintar(lado, lado, d)


# ---------------------------------------------------------------------- papel
def _papel(p, caminho, caixa, rng, base="#c8a06a", queimado=True):
    """Pinta papel velho dentro de um caminho (manchas, fibras e borda escurecida)."""
    x0, y0, x1, y1 = caixa
    p.save()
    p.setClipPath(caminho)
    p.fillRect(QRectF(x0, y0, x1 - x0, y1 - y0), QColor(base))
    p.setPen(Qt.PenStyle.NoPen)
    area = (x1 - x0) * (y1 - y0)
    for _ in range(int(area / 900)):
        c = QColor(110, 70, 30, int(rng.uniform(6, 26))) if rng.random() < 0.7 else QColor(255, 230, 180, int(rng.uniform(6, 20)))
        p.setBrush(c)
        r = rng.uniform(3, 22)
        p.drawEllipse(QPointF(rng.uniform(x0, x1), rng.uniform(y0, y1)), r, r * rng.uniform(0.5, 1))
    if queimado:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        g = QRadialGradient(QPointF(cx, cy), max(x1 - x0, y1 - y0) * 0.62)
        g.setColorAt(0.55, QColor(0, 0, 0, 0))
        g.setColorAt(1, QColor(80, 40, 10, 170))
        p.fillRect(QRectF(x0, y0, x1 - x0, y1 - y0), QBrush(g))
    p.restore()
    p.setPen(QPen(QColor(70, 40, 15, 160), 2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(caminho)


def _borda_rasgada(x0, y0, x1, y1, rng, dente=10):
    """Retângulo com a borda rasgada/irregular."""
    cam = QPainterPath()
    pts = []
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        n = max(2, int(math.hypot(bx - ax, by - ay) / 18))
        for k in range(n):
            t = k / n
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            nx, ny = -(by - ay), bx - ax
            ln = math.hypot(nx, ny) or 1
            d = rng.uniform(-dente, dente * 0.3)
            pts.append(QPointF(x + nx / ln * d, y + ny / ln * d))
    cam.addPolygon(QPolygonF(pts))
    cam.closeSubpath()
    return cam


def _floreio_cantos(p, x0, y0, x1, y1, cor, tam=40):
    """Floreios de tinta nos 4 cantos (cara de documento oficial)."""
    p.setPen(QPen(cor, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        c = QPainterPath(QPointF(cx + sx * tam * 1.6, cy))
        c.cubicTo(QPointF(cx + sx * tam * 0.6, cy), QPointF(cx, cy + sy * tam * 0.2), QPointF(cx, cy + sy * tam * 1.6))
        p.drawPath(c)
        e = QPainterPath(QPointF(cx + sx * tam * 0.9, cy + sy * tam * 0.15))
        e.cubicTo(QPointF(cx + sx * tam * 0.4, cy + sy * tam * 0.3), QPointF(cx + sx * tam * 0.6, cy + sy * tam * 0.8),
                  QPointF(cx + sx * tam * 0.2, cy + sy * tam * 0.9))
        p.drawPath(e)
        p.drawEllipse(QPointF(cx + sx * tam * 0.45, cy + sy * tam * 0.45), tam * 0.12, tam * 0.12)


def _contrato():
    """Pergaminho do contrato da mesa 3D (o texto do menu é escrito por cima, no QML)."""
    rng = _rng("contrato")

    def d(p, W, H):
        cam = _borda_rasgada(14, 14, W - 14, H - 14, rng, 8)
        _papel(p, cam, (0, 0, W, H), rng, "#d8b882")
        tinta = QColor(70, 38, 14, 200)
        p.setPen(QPen(tinta, 3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(QRectF(46, 46, W - 92, H - 92))
        p.setPen(QPen(tinta, 1.5))
        p.drawRect(QRectF(56, 56, W - 112, H - 112))
        _floreio_cantos(p, 66, 66, W - 66, H - 66, tinta, 34)
    return _pintar(768, 1024, d)


# ---------------------------------------------------------------------- muro e quadro
def _muro(w, h):
    """Muro de pedra (tijolões cinza-arroxeados com reboco escuro e musgo)."""
    w2, h2 = max(64, w // 2), max(64, h // 2)
    rng = _rng("muro-quadro", w2, h2)
    ys, xs = np.mgrid[0:h2, 0:w2].astype(np.float32)
    alt, larg = 46, 92
    lin = np.floor(ys / alt)
    xo = xs + (lin % 2) * larg / 2
    col = np.floor(xo / larg)
    lu, lv = xo - col * larg, ys - lin * alt
    junta = np.minimum(np.minimum(lu, larg - lu), np.minimum(lv, alt - lv))
    tons = _rng("tons-muro").random(64).astype(np.float32)
    k = ((lin * 7 + col * 13).astype(int)) % 64
    n = _ruido(h2, w2, 6, rng)
    cor = _c("#5a5660") * (0.65 + 0.45 * tons[k])[..., None] * (0.8 + 0.3 * n[..., None])
    luz = _suave(lv / alt * 1.4) * 0.15 - _suave((lv / alt - 0.6) * 2) * 0.15     # bloco "estufado": cima clara
    cor *= (1 + luz)[..., None]
    cor *= (0.25 + 0.75 * _suave(junta / 4))[..., None]
    musgo = _suave((_ruido(h2, w2, 20, rng) - 0.68) * 6) * (junta < 6)
    cor = cor * (1 - musgo[..., None] * 0.6) + _c("#3a5a26") * musgo[..., None] * 0.6
    img = _rgb_img(cor)
    return _pixelar(img.scaled(w2 * 2, h2 * 2, Qt.AspectRatioMode.IgnoreAspectRatio,
                               Qt.TransformationMode.SmoothTransformation), 2)


def _madeira(p, ret, rng, base="#5a3a20", veio=True, vertical=False):
    p.fillRect(ret, QColor(base))
    p.save()
    p.setClipRect(ret)
    n = int((ret.width() if vertical else ret.height()) / 5)
    for _ in range(n * 3):
        if vertical:
            x = rng.uniform(ret.left(), ret.right())
            p.setPen(QPen(QColor(20, 10, 4, int(rng.uniform(20, 70))), rng.uniform(1, 2.5)))
            p.drawLine(QPointF(x, ret.top()), QPointF(x + rng.uniform(-4, 4), ret.bottom()))
        else:
            y = rng.uniform(ret.top(), ret.bottom())
            p.setPen(QPen(QColor(20, 10, 4, int(rng.uniform(20, 70))), rng.uniform(1, 2.5)))
            p.drawLine(QPointF(ret.left(), y), QPointF(ret.right(), y + rng.uniform(-4, 4)))
    g = QLinearGradient(ret.topLeft(), ret.bottomLeft() if not vertical else ret.topRight())
    g.setColorAt(0, QColor(255, 220, 160, 40))
    g.setColorAt(0.5, QColor(0, 0, 0, 0))
    g.setColorAt(1, QColor(0, 0, 0, 90))
    p.fillRect(ret, QBrush(g))
    p.restore()


def _prego(p, x, y, r=7):
    g = QRadialGradient(QPointF(x - r * 0.3, y - r * 0.3), r * 1.2)
    g.setColorAt(0, QColor("#b8b8c0"))
    g.setColorAt(1, QColor("#2a2a30"))
    p.setPen(QPen(QColor("#141418"), 1.5))
    p.setBrush(QBrush(g))
    p.drawEllipse(QPointF(x, y), r, r)


def _selo(p, x, y, r=26):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#6a1010"))
    for lado in (-1, 1):                                          # fitinhas
        p.drawPolygon(QPolygonF([QPointF(x + lado * 6, y), QPointF(x + lado * 22, y + r * 2.0),
                                 QPointF(x + lado * 12, y + r * 1.7), QPointF(x + lado * 4, y + r * 2.1)]))
    g = QRadialGradient(QPointF(x - r * 0.3, y - r * 0.3), r * 1.3)
    g.setColorAt(0, QColor("#c8302a"))
    g.setColorAt(1, QColor("#6a0e0c"))
    p.setBrush(QBrush(g))
    pts = [QPointF(x + math.cos(a) * r * (1 + 0.08 * math.sin(a * 7)), y + math.sin(a) * r * (1 + 0.08 * math.sin(a * 7)))
           for a in np.linspace(0, 2 * math.pi, 28, endpoint=False)]
    p.drawPolygon(QPolygonF(pts))
    p.setPen(QPen(QColor(60, 0, 0, 200), 2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(x, y), r * 0.6, r * 0.6)


def _cartaz(p, x0, y0, x1, y1, rng, selo=False, mapa=False, pregos=True):
    cam = _borda_rasgada(x0, y0, x1, y1, rng, 7)
    _papel(p, cam, (x0 - 10, y0 - 10, x1 + 10, y1 + 10), rng)
    tinta = QColor(70, 38, 14, 170)
    _floreio_cantos(p, x0 + 16, y0 + 16, x1 - 16, y1 - 16, tinta, 18)
    if mapa:
        p.setPen(QPen(QColor(70, 40, 15, 200), 3))
        for k in range(4):
            x, y = x0 + 50 + k * 34, y0 + 70 + (k % 2) * 10
            p.drawPolyline(QPolygonF([QPointF(x - 22, y + 24), QPointF(x, y - 18), QPointF(x + 22, y + 24)]))
        for k in range(5):
            x, y = x0 + 45 + k * 26, y1 - 50
            p.drawPolyline(QPolygonF([QPointF(x - 9, y + 14), QPointF(x, y - 12), QPointF(x + 9, y + 14)]))
        cx, cy = x1 - 70, y0 + 70
        p.drawRect(QRectF(cx - 22, cy - 10, 44, 34))
        for dx in (-22, 0, 22):
            p.drawRect(QRectF(cx + dx - 6, cy - 22, 12, 12))
        rio = QPainterPath(QPointF(x0 + 120, y1 - 20))
        rio.cubicTo(QPointF(x0 + 200, y1 - 90), QPointF(x1 - 160, y0 + 160), QPointF(x1 - 60, y0 + 120))
        p.setPen(QPen(QColor(70, 40, 15, 140), 4))
        p.drawPath(rio)
    else:
        p.setPen(QPen(QColor(70, 38, 14, 60), 2))                  # linhas de texto apagadas
        for k in range(5):
            y = y0 + (y1 - y0) * (0.32 + k * 0.1)
            p.drawLine(QPointF(x0 + 40, y), QPointF(x1 - 40 - rng.uniform(0, 60), y))
    if selo:
        _selo(p, x1 - 50, y1 - 60)
    if not pregos:
        return
    for (px, py) in ((x0 + 14, y0 + 14), (x1 - 14, y0 + 14), (x0 + 14, y1 - 14), (x1 - 14, y1 - 14)):
        _prego(p, px, py, 6)


def _quadro():
    """O quadro de missões inteiro (moldura, cartazes, fios, estandarte, espadas, cordas e brasões)."""
    rng = _rng("quadro-missoes")

    def d(p, W, H):
        # fundo de tábuas
        _madeira(p, QRectF(70, 60, W - 140, H - 130), rng, "#3e2814", vertical=True)
        for k in range(1, 9):
            x = 70 + k * (W - 140) / 9
            p.setPen(QPen(QColor(10, 5, 2, 200), 3))
            p.drawLine(QPointF(x, 60), QPointF(x, H - 70))
        # moldura (vigas grossas) + chapas de ferro nos cantos
        for ret in (QRectF(30, 40, W - 60, 56), QRectF(30, H - 120, W - 60, 60)):
            _madeira(p, ret, rng, "#6a4424")
        for ret in (QRectF(40, 40, 60, H - 60), QRectF(W - 100, 40, 60, H - 60)):
            _madeira(p, ret, rng, "#5e3c20", vertical=True)
        for (cx, cy) in ((70, 68), (W - 70, 68), (70, H - 90), (W - 70, H - 90)):
            p.setPen(QPen(QColor("#141418"), 2))
            p.setBrush(QColor("#3a3a42"))
            p.drawRect(QRectF(cx - 38, cy - 34, 76, 68))
            for (dx, dy) in ((-24, -20), (24, -20), (-24, 20), (24, 20)):
                _prego(p, cx + dx, cy + dy, 6)
        # cartazes da esquerda (2 + mapa) e da direita (2 + bússola)
        _cartaz(p, 130, 130, 420, 330, rng)
        _cartaz(p, 120, 360, 410, 560, rng, selo=True)
        _cartaz(p, 110, 590, 470, 790, rng, mapa=True)
        _cartaz(p, W - 420, 140, W - 140, 400, rng, selo=True)
        _cartaz(p, W - 380, 560, W - 130, 790, rng)
        # bilhetinho da bússola
        cam = _borda_rasgada(W - 520, 450, W - 410, 550, rng, 4)
        _papel(p, cam, (W - 530, 440, W - 400, 560), rng, queimado=False)
        cx, cy = W - 465, 500
        p.setPen(QPen(QColor(70, 40, 15, 220), 2))
        p.setBrush(QColor(70, 40, 15, 200))
        for a in range(0, 360, 45):
            comp = 34 if a % 90 == 0 else 18
            ra = math.radians(a)
            p.drawPolygon(QPolygonF([QPointF(cx, cy), QPointF(cx + math.cos(ra + 0.2) * 7, cy + math.sin(ra + 0.2) * 7),
                                     QPointF(cx + math.cos(ra) * comp, cy + math.sin(ra) * comp)]))
        # cartaz grande do meio (o menu fica nele)
        x0, y0, x1, y1 = CARTAZ[0] * W, CARTAZ[1] * H, CARTAZ[2] * W, CARTAZ[3] * H
        cam = _borda_rasgada(x0, y0, x1, y1, rng, 12)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 110))
        p.drawPath(cam.translated(8, 10))                          # sombra
        _papel(p, cam, (x0 - 20, y0 - 20, x1 + 20, y1 + 20), rng, "#c49a62")
        _floreio_cantos(p, x0 + 26, y0 + 26, x1 - 26, y1 - 26, QColor(70, 38, 14, 170), 30)
        for (px, py) in ((x0 + 18, y0 + 18), (x1 - 18, y0 + 18), (x0 + 18, y1 - 18), (x1 - 18, y1 - 18)):
            _prego(p, px, py, 8)
        # fios vermelhos ligando os cartazes (presos com alfinete)
        for (a, b) in (((420, 250), (x0 + 18, y0 + 60)), ((410, 450), (x0 + 18, y0 + 260)),
                       ((W - 420, 300), (x1 - 18, y0 + 90)), ((W - 465, 460), (x1 - 18, y1 - 140)),
                       ((W - 410, 500), (W - 300, 570)), ((W - 465, 450), (W - 280, 380))):
            p.setPen(QPen(QColor("#8a1a14"), 3))
            p.drawLine(QPointF(*a), QPointF(*b))
            for pt in (a, b):
                _prego(p, pt[0], pt[1], 5)
        # estandarte com brasão no topo
        bx = W / 2
        p.setPen(QPen(QColor("#2a1a0c"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(bx - 330, 22), QPointF(bx + 330, 22))
        for lado in (-1, 1):                                       # flâmulas
            fx = bx + lado * 270
            p.setPen(QPen(QColor("#2a0a08"), 2))
            p.setBrush(QColor("#7a1a16"))
            p.drawPolygon(QPolygonF([QPointF(fx - 22, 24), QPointF(fx + 22, 24), QPointF(fx + 22, 140), QPointF(fx, 120),
                                     QPointF(fx - 22, 140)]))
            p.setBrush(QColor("#d8c08a"))
            p.drawRect(QRectF(fx - 8, 24, 16, 100))
        est = QPolygonF([QPointF(bx - 200, 24), QPointF(bx + 200, 24), QPointF(bx + 200, 180), QPointF(bx, 240),
                         QPointF(bx - 200, 180)])
        g = QLinearGradient(bx - 200, 0, bx + 200, 0)
        g.setColorAt(0, QColor("#5a1210"))
        g.setColorAt(0.5, QColor("#8a1e18"))
        g.setColorAt(1, QColor("#4a0e0c"))
        p.setPen(QPen(QColor("#2a0806"), 3))
        p.setBrush(QBrush(g))
        p.drawPolygon(est)
        p.setPen(QPen(QColor("#d8a84a"), 4))
        for k in range(26):                                        # franja dourada
            t = k / 25
            x = bx - 200 + 400 * t
            y = 180 + 60 * (1 - abs(t - 0.5) * 2)
            p.drawLine(QPointF(x, y), QPointF(x, y + 14))
        # espadas cruzadas atrás do escudo
        for lado in (-1, 1):
            p.save()
            p.translate(bx, 120)
            p.rotate(lado * 40)
            p.setPen(QPen(QColor("#1a1a20"), 2))
            p.setBrush(QColor("#b8bcc4"))
            p.drawPolygon(QPolygonF([QPointF(-6, -110), QPointF(6, -110), QPointF(6, 60), QPointF(0, 76), QPointF(-6, 60)]))
            p.setBrush(QColor("#8a6a3a"))
            p.drawRect(QRectF(-24, -114, 48, 8))
            p.setBrush(QColor("#4a2a14"))
            p.drawRect(QRectF(-5, -146, 10, 32))
            p.restore()
        esc = QPainterPath(QPointF(bx - 52, 70))                   # escudo esquartelado
        esc.lineTo(QPointF(bx + 52, 70))
        esc.lineTo(QPointF(bx + 52, 120))
        esc.quadTo(QPointF(bx + 48, 160), QPointF(bx, 182))
        esc.quadTo(QPointF(bx - 48, 160), QPointF(bx - 52, 120))
        esc.closeSubpath()
        p.setPen(QPen(QColor("#2a1a0c"), 4))
        p.setBrush(QColor("#d8c08a"))
        p.drawPath(esc)
        p.save()
        p.setClipPath(esc)
        p.fillRect(QRectF(bx - 52, 70, 52, 56), QColor("#5a3a20"))
        p.fillRect(QRectF(bx, 126, 52, 60), QColor("#5a3a20"))
        p.restore()
        p.setPen(QPen(QColor("#d8a84a"), 4))                       # louros
        for lado in (-1, 1):
            for k in range(6):
                a = math.radians(200 - k * 22) if lado < 0 else math.radians(-20 + k * 22)
                x, y = bx + math.cos(a) * 92, 130 + math.sin(a) * 70
                p.drawEllipse(QPointF(x, y), 7, 4)
        # embaixo: cordas com brasões e as espadas cruzadas
        by = H - 92
        for lado in (-1, 1):
            corda = QPainterPath(QPointF(bx + lado * 70, by))
            corda.quadTo(QPointF(bx + lado * 200, by + 70), QPointF(bx + lado * 330, by - 4))
            p.setPen(QPen(QColor("#3a2a14"), 10))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(corda)
            p.setPen(QPen(QColor("#a08850"), 6, Qt.PenStyle.DashLine))
            p.drawPath(corda)
        for (cx, forma) in ((bx - 330, "lobo"), (bx + 330, "torre")):
            p.setPen(QPen(QColor("#1a1008"), 3))
            p.setBrush(QColor("#6a4a28"))
            if forma == "lobo":
                pts = [QPointF(cx + math.cos(a) * 46, by + 40 + math.sin(a) * 46) for a in np.linspace(0, 2 * math.pi, 8, endpoint=False) + math.pi / 8]
                p.drawPolygon(QPolygonF(pts))
                p.setBrush(QColor("#c8a46a"))
                p.drawPolygon(QPolygonF([QPointF(cx - 22, by + 22), QPointF(cx - 12, by + 40), QPointF(cx - 18, by + 60),
                                         QPointF(cx + 6, by + 64), QPointF(cx + 24, by + 50), QPointF(cx + 14, by + 34),
                                         QPointF(cx + 18, by + 16), QPointF(cx + 4, by + 28)]))
            else:
                p.drawPolygon(QPolygonF([QPointF(cx - 42, by), QPointF(cx + 42, by), QPointF(cx + 42, by + 60),
                                         QPointF(cx, by + 92), QPointF(cx - 42, by + 60)]))
                p.setBrush(QColor("#c8a46a"))
                p.drawRect(QRectF(cx - 18, by + 24, 36, 38))
                for dx in (-18, -4, 10):
                    p.drawRect(QRectF(cx + dx, by + 14, 8, 10))
        for lado in (-1, 1):
            p.save()
            p.translate(bx, by + 6)
            p.rotate(lado * 42)
            p.setPen(QPen(QColor("#1a1a20"), 2))
            p.setBrush(QColor("#c8ccd4"))
            p.drawPolygon(QPolygonF([QPointF(-7, -80), QPointF(7, -80), QPointF(7, 40), QPointF(0, 58), QPointF(-7, 40)]))
            p.setBrush(QColor("#8a6a3a"))
            p.drawRect(QRectF(-26, -84, 52, 9))
            p.setBrush(QColor("#7a1a14"))
            p.drawRect(QRectF(-6, -118, 12, 34))
            p.setBrush(QColor("#8a6a3a"))
            p.drawEllipse(QPointF(0, -122), 9, 9)
            p.restore()
    return _pixelar(_pintar(QUADRO_W, QUADRO_H, d), 2)


def _lamparina(W=300, H=520):
    """Lamparina de ferro pendurada num braço preso no muro (a chama é do QML)."""
    def d(p, W, H):
        ferro = QColor("#1e1e22")
        p.setPen(QPen(ferro, 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap))
        p.drawLine(QPointF(W - 30, 30), QPointF(W - 30, 140))          # chapa no muro
        p.drawLine(QPointF(W - 30, 46), QPointF(W * 0.42, 46))          # braço
        cur = QPainterPath(QPointF(W - 30, 120))
        cur.quadTo(QPointF(W * 0.55, 110), QPointF(W * 0.55, 50))
        p.setPen(QPen(ferro, 8))
        p.drawPath(cur)
        p.drawEllipse(QPointF(W * 0.42, 66), 14, 14)                   # argola
        cx, top = W * 0.42, 90
        p.setPen(QPen(ferro, 3))
        p.setBrush(QColor("#2a2a30"))
        p.drawPolygon(QPolygonF([QPointF(cx - 30, top + 40), QPointF(cx, top), QPointF(cx + 30, top + 40)]))   # tampa
        p.drawRect(QRectF(cx - 46, top + 40, 92, 14))
        vidro = QRectF(cx - 40, top + 54, 80, 150)
        g = QRadialGradient(QPointF(cx, top + 140), 90)
        g.setColorAt(0, QColor(255, 210, 120, 220))
        g.setColorAt(1, QColor(200, 110, 30, 160))
        p.setBrush(QBrush(g))
        p.drawRect(vidro)
        p.setPen(QPen(ferro, 7))
        for x in (cx - 40, cx - 13, cx + 13, cx + 40):                # grade
            p.drawLine(QPointF(x, top + 54), QPointF(x, top + 204))
        p.drawLine(QPointF(cx - 40, top + 130), QPointF(cx + 40, top + 130))
        p.setPen(QPen(ferro, 3))
        p.setBrush(QColor("#2a2a30"))
        p.drawRect(QRectF(cx - 48, top + 204, 96, 16))
        p.drawPolygon(QPolygonF([QPointF(cx - 30, top + 220), QPointF(cx + 30, top + 220), QPointF(cx, top + 250)]))
    return _pintar(W, H, d)


def lamparina_chama():
    """Onde fica a chama dentro da imagem da lamparina (fração)."""
    return (0.42, (90 + 150) / 520)


def _hera_viva(lado=520):
    rng = _rng("hera-viva")

    def d(p, W, H):
        cam = QPainterPath(QPointF(0, 0))
        cam.cubicTo(QPointF(W * 0.3, H * 0.2), QPointF(W * 0.1, H * 0.6), QPointF(W * 0.25, H))
        p.setPen(QPen(QColor("#2a3a18"), 6))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(cam)
        for k in range(22):
            t = k / 21
            pt = cam.pointAtPercent(t)
            x, y = pt.x() + rng.uniform(-50, 50), pt.y() + rng.uniform(-20, 20)
            r = rng.uniform(22, 40)
            p.save()
            p.translate(x, y)
            p.rotate(rng.uniform(-50, 50))
            folha = QPainterPath(QPointF(0, -r))
            folha.lineTo(QPointF(r * 0.5, -r * 0.5))
            folha.lineTo(QPointF(r, -r * 0.1))
            folha.lineTo(QPointF(r * 0.4, r * 0.2))
            folha.lineTo(QPointF(0, r))
            folha.lineTo(QPointF(-r * 0.4, r * 0.2))
            folha.lineTo(QPointF(-r, -r * 0.1))
            folha.lineTo(QPointF(-r * 0.5, -r * 0.5))
            folha.closeSubpath()
            v = rng.uniform(0.7, 1.15)
            p.setPen(QPen(QColor(20, 40, 14), 2))
            p.setBrush(QColor(min(255, int(70 * v)), min(255, int(120 * v)), min(255, int(52 * v))))
            p.drawPath(folha)
            p.setPen(QPen(QColor(150, 190, 110, 140), 2))
            p.drawLine(QPointF(0, -r * 0.7), QPointF(0, r * 0.7))
            p.restore()
    return _pixelar(_pintar(lado, lado, d), 3)
