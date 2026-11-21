"""
🚪 Texturas das FOLHAS das portas na Mesa 3D (v0.67, pedido do Manel: "porta com textura e maçaneta certa").

Cada tipo tem a sua face, desenhada aqui (numpy + QPainter), pra uma folha de 1 m × 1,85 m com ESCALA pixels por
unidade da cena (a face repete se a porta for mais larga). A textura é aplicada de baixo pra cima (v = 0 no pé da
porta), então o desenho é virado no fim.
  madeira  — tábuas na vertical com veio, frestas escuras e DUAS faixas de ferro rebitadas
  pedra    — laje com moldura entalhada (chanfro claro/escuro) e um painel no meio
  metal    — chapas de aço escovado com costuras e rebites, umas manchinhas de ferrugem
  mecanica — painéis de nave: costura no meio (a porta desliza), faixa amarela e preta embaixo, luzinha
  cortina  — pano com dobras (claro/escuro) e franja dourada
  janela_persiana — lâminas horizontais com sombra
"""

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPen, QPixmap

ESCALA = 4.0             # pixels de textura por unidade da cena
_CACHE: dict = {}


def _ruido(h, w, rng, raio):
    a = rng.random((h, w)).astype(np.float32)
    for eixo in (0, 1):
        for _ in range(2):
            c = np.cumsum(np.pad(a, [(raio + 1, raio) if k == eixo else (0, 0) for k in range(2)], mode="edge"),
                          axis=eixo)
            a = ((c[2 * raio + 1:] - c[:-2 * raio - 1]) if eixo == 0 else
                 (c[:, 2 * raio + 1:] - c[:, :-2 * raio - 1])) / (2 * raio + 1)
    return (a - a.min()) / max(1e-6, float(np.ptp(a)))


def _img(rgb):
    h, w = rgb.shape[:2]
    out = np.empty((h, w, 4), np.uint8)
    out[..., 0] = (np.clip(rgb[..., 2], 0, 1) * 255).astype(np.uint8)
    out[..., 1] = (np.clip(rgb[..., 1], 0, 1) * 255).astype(np.uint8)
    out[..., 2] = (np.clip(rgb[..., 0], 0, 1) * 255).astype(np.uint8)
    out[..., 3] = 255
    return QImage(out.tobytes(), w, h, w * 4, QImage.Format.Format_ARGB32).copy()


def _c(hexa):
    q = QColor(hexa)
    return np.array([q.redF(), q.greenF(), q.blueF()], np.float32)


def _rebite(p, x, y, r=3.4, cor=QColor(60, 58, 54)):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(0, 0, 0, 120))
    p.drawEllipse(QPointF(x + 1, y + 1.2), r, r)
    p.setBrush(cor)
    p.drawEllipse(QPointF(x, y), r, r)
    p.setBrush(QColor(255, 255, 255, 110))
    p.drawEllipse(QPointF(x - r * 0.35, y - r * 0.35), r * 0.4, r * 0.4)


def _madeira(W, H, rng):
    xs = np.arange(W, dtype=np.float32)[None, :]
    veio = _ruido((H + 7) // 8, W, rng, 2)
    veio = np.repeat(veio, 8, axis=0)[:H]          # (arredonda pra cima: a altura nem sempre é múltipla de 8)
    tabua = (xs // (W / 4)).astype(int)
    tom = rng.uniform(0.82, 1.12, 4).astype(np.float32)[tabua]
    linhas = 0.5 + 0.5 * np.sin(xs * 0.9 + veio * 9)
    base = _c("#8a5a2b") * (tom * (0.78 + 0.18 * linhas + 0.14 * veio))[..., None]
    rgb = np.broadcast_to(base, (H, W, 3)).copy()
    fresta = (xs % (W / 4)) < 3
    rgb[:, fresta[0]] *= 0.35
    ys = np.arange(H, dtype=np.float32)[:, None]
    rgb *= (0.8 + 0.2 * np.clip(ys / (H * 0.2), 0, 1))[..., None]          # (desenhado de cima pra baixo)
    img = _img(rgb)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    for fy in (0.2, 0.74):                                                  # faixas de ferro
        y = H * fy
        g = QLinearGradient(QPointF(0, y), QPointF(0, y + 20))
        g.setColorAt(0, QColor(96, 92, 86))
        g.setColorAt(0.5, QColor(58, 55, 52))
        g.setColorAt(1, QColor(34, 32, 30))
        p.fillRect(QRectF(0, y, W, 20), g)
        p.fillRect(QRectF(0, y + 20, W, 3), QColor(0, 0, 0, 90))
        for k in range(4):
            _rebite(p, W / 8 + k * W / 4, y + 10, 3.6)
    p.end()
    return img


def _pedra(W, H, rng):
    n = _ruido(H, W, rng, 6) * 0.6 + _ruido(H, W, rng, 1) * 0.4
    rgb = _c("#7d786f") * (0.78 + 0.32 * n)[..., None]
    img = _img(rgb)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    for k, (claro, escuro) in enumerate(((QColor(255, 250, 240, 70), QColor(0, 0, 0, 110)),
                                         (QColor(0, 0, 0, 90), QColor(255, 250, 240, 55)))):
        m = 14 + k * 26                                                    # moldura em dois degraus
        r = QRectF(m, m, W - 2 * m, H - 2 * m)
        p.setPen(QPen(claro, 4))
        p.drawLine(r.topLeft(), r.topRight())
        p.drawLine(r.topLeft(), r.bottomLeft())
        p.setPen(QPen(escuro, 4))
        p.drawLine(r.bottomLeft(), r.bottomRight())
        p.drawLine(r.topRight(), r.bottomRight())
    p.setPen(QPen(QColor(40, 36, 32, 140), 2.2))                           # um símbolo entalhado no meio
    p.setBrush(Qt.BrushStyle.NoBrush)
    c = QPointF(W / 2, H * 0.46)
    p.drawEllipse(c, W * 0.18, W * 0.18)
    for a in range(6):
        ang = a * math.pi / 3
        p.drawLine(c, c + QPointF(math.cos(ang) * W * 0.18, math.sin(ang) * W * 0.18))
    p.end()
    return img


def _metal(W, H, rng):
    escovado = np.repeat(_ruido(H, W // 16, rng, 1), 16, axis=1)[:, :W]
    escovado = escovado * 0.6 + _ruido(H, W, rng, 1) * 0.4
    rgb = _c("#8d959e") * (0.72 + 0.34 * escovado)[..., None]
    ferr = np.clip((_ruido(H, W, rng, 8) - 0.78) * 6, 0, 1)
    rgb = rgb * (1 - ferr[..., None] * 0.7) + _c("#7a4a24") * ferr[..., None] * 0.7
    img = _img(rgb)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(30, 32, 36, 180), 2))
    for fy in (1 / 3, 2 / 3):
        p.drawLine(QPointF(0, H * fy), QPointF(W, H * fy))
    p.drawLine(QPointF(W / 2, 0), QPointF(W / 2, H))
    for fy in (8, H / 3 - 8, H / 3 + 8, 2 * H / 3 - 8, 2 * H / 3 + 8, H - 8):
        for k in range(6):
            _rebite(p, 10 + k * (W - 20) / 5, fy, 2.8, QColor(150, 156, 164))
    p.end()
    return img


def _mecanica(W, H, rng):
    n = _ruido(H, W, rng, 3)
    rgb = _c("#5a6470") * (0.82 + 0.2 * n)[..., None]
    img = _img(rgb)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(20, 24, 30), 3))
    p.drawLine(QPointF(W / 2, 0), QPointF(W / 2, H))                        # costura (desliza)
    p.setPen(QPen(QColor(130, 140, 150, 160), 1.5))
    for r in (QRectF(16, 24, W / 2 - 30, H * 0.36), QRectF(W / 2 + 14, 24, W / 2 - 30, H * 0.36),
              QRectF(16, H * 0.45, W - 32, H * 0.3)):
        p.drawRoundedRect(r, 6, 6)
    faixa = QRectF(0, H * 0.84, W, H * 0.1)                                 # amarelo e preto
    p.save()
    p.setClipRect(faixa)
    p.fillRect(faixa, QColor(230, 180, 30))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(25, 25, 25))
    for k in range(-4, 14):
        x = k * 30
        p.drawPolygon([QPointF(x, faixa.bottom()), QPointF(x + 15, faixa.bottom()),
                       QPointF(x + 15 + faixa.height(), faixa.top()), QPointF(x + faixa.height(), faixa.top())])
    p.restore()
    p.setBrush(QColor(80, 255, 140))
    p.setPen(QPen(QColor(10, 40, 20), 1.5))
    p.drawEllipse(QPointF(W - 22, H * 0.5), 5, 5)
    p.end()
    return img


def _cortina(W, H, rng):
    xs = np.arange(W, dtype=np.float32)[None, :]
    dobra = 0.5 + 0.5 * np.sin(xs / W * math.pi * 7 + 0.4 * np.sin(xs * 0.05))
    n = _ruido(H, W, rng, 2)
    rgb = _c("#7a1f2a") * (0.55 + 0.55 * dobra + 0.08 * n)[..., None]
    rgb = np.broadcast_to(rgb, (H, W, 3)).copy()
    img = _img(rgb)
    p = QPainter(img)
    p.fillRect(QRectF(0, H - 26, W, 14), QColor(201, 162, 74))              # barra dourada
    p.setPen(QPen(QColor(201, 162, 74), 2))
    for x in range(2, W, 5):                                                # franja
        p.drawLine(QPointF(x, H - 12), QPointF(x + rng.uniform(-1, 1), H))
    p.end()
    return img


def _persiana(W, H, rng):
    ys = np.arange(H, dtype=np.float32)[:, None]
    lamina = (ys % 22) / 22
    n = _ruido(H, W, rng, 2)
    rgb = _c("#7a5232") * (0.62 + 0.45 * (1 - lamina) + 0.08 * n)[..., None]
    rgb[(ys % 22 > 19)[:, 0]] *= 0.35
    return _img(np.broadcast_to(rgb, (H, W, 3)).copy())


def casca() -> QPixmap:
    """Casca de tronco (paliçada): sulcos na vertical, nós, musgo embaixo. ~0,3 m de largura, repete."""
    pm = _CACHE.get("_casca")
    if pm is None:
        rng = np.random.default_rng(77)
        W, H = 64, 256
        sulco = _ruido((H + 15) // 16, W, rng, 1)
        sulco = np.repeat(sulco, 16, axis=0)[:H]
        n = _ruido(H, W, rng, 2)
        v = 0.55 * sulco + 0.45 * n
        rgb = _c("#5a3e24") * (0.55 + 0.7 * v)[..., None]
        ys = np.arange(H, dtype=np.float32)[:, None]
        musgo = np.clip((ys / H - 0.8) * 4, 0, 1) * np.clip((_ruido(H, W, rng, 4) - 0.4) * 3, 0, 1)
        rgb = rgb * (1 - musgo[..., None] * 0.6) + _c("#4a5a2a") * musgo[..., None] * 0.6
        img = _img(rgb)
        try:
            img = img.flipped(Qt.Orientation.Vertical)
        except AttributeError:
            img = img.mirrored(False, True)
        pm = _CACHE["_casca"] = QPixmap.fromImage(img)
    return pm


FEITOS = {"madeira": _madeira, "pedra": _pedra, "metal": _metal, "mecanica": _mecanica, "cortina": _cortina,
          "janela_persiana": _persiana}


def textura(tipo: str) -> QPixmap | None:
    """A face da folha desse tipo de porta (None = esse tipo não tem textura, usa a cor)."""
    if tipo not in FEITOS:
        return None
    pm = _CACHE.get(tipo)
    if pm is None:
        from ..config import CELULA
        from .camera3d import ALTURA_PORTA
        W, H = int(CELULA * ESCALA), int(ALTURA_PORTA * ESCALA)
        import zlib
        img = FEITOS[tipo](W, H, np.random.default_rng(zlib.crc32(tipo.encode())))   # (igual toda vez)
        try:
            virada = img.flipped(Qt.Orientation.Vertical)
        except AttributeError:
            virada = img.mirrored(False, True)
        pm = _CACHE[tipo] = QPixmap.fromImage(virada)   # v = 0 no pé da porta
    return pm
