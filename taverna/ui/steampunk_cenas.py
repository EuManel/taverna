"""
⚙ Cenários do tema Steampunk (v0.59, pedido do Manel). Sorteia um (50/50, e de novo ao escolher o tema):

  OFICINA   — oficina do inventor: engrenagens girando na parede, canos de cobre, vapor escapando, autômato pela
              metade na bancada, luz de lampião a gás. AS OPÇÕES SÃO PLAQUINHAS DE LATÃO num painel de controle,
              cada uma com um mostrador: no hover o ponteiro sobe e uma válvula solta vapor; no clique, uma
              alavanca desce.
  DIRIGIVEL — ponte de comando de um dirigível: janela pras nuvens, cidade de chaminés lá embaixo, outros
              dirigíveis ao longe. O MENU É O TELÉGRAFO DE ORDENS (mostrador redondo com alavanca): cada fatia é
              uma opção; no hover a alavanca vai até ela; no clique toca a campainha "plim-plim".

Aqui ficam as texturas (gravadas em arquivo, ver `estilizado.caminho_textura_3d`).
"""

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainterPath, QPen, QRadialGradient

from .estilizado import _c, _caixa_borrar, _rgb_img, _rng, _ruido, _suave
from .terror_cenas import _guardado, _pintar, _rgba


def textura(nome):
    f = {"latao": _latao, "cobre": _cobre, "madeira_oficina": _madeira_oficina, "parede_oficina": _parede_oficina,
         "mostrador": _mostrador, "ceu_nuvens": _ceu_nuvens, "cidade_chamines": _cidade_chamines,
         "nuvem": _nuvem, "lona_dirigivel": _lona_dirigivel, "telegrafo": _telegrafo}.get(nome)
    return _guardado(("steampunk", nome), f) if f else None


def _metal_escovado(semente, escuro, claro, lado=512, patina=0.0):
    rng = _rng(semente)
    fino = _caixa_borrar(rng.random((lado, lado)).astype(np.float32), 1)                    # grão
    n = _ruido(lado, lado, 40, rng)
    linhas = np.repeat(rng.random((lado, 1)).astype(np.float32), lado, axis=1)              # riscos de polimento
    v = 0.35 + 0.2 * linhas + 0.2 * fino + 0.25 * n
    cor = _c(escuro) * (1 - v[..., None]) + _c(claro) * v[..., None]
    if patina:
        m = _suave((_ruido(lado, lado, 50, rng) - 0.6) * 5) * patina
        cor = cor * (1 - m[..., None]) + _c("#4a8a72") * m[..., None]
    return _rgb_img(np.clip(cor, 0, 1))


def _latao():
    return _metal_escovado("latao", "#6a4a18", "#e8c070", patina=0.25)


def _cobre():
    return _metal_escovado("cobre", "#5a2a12", "#e08a58", patina=0.45)


def _madeira_oficina(lado=512):
    rng = _rng("madeira-oficina")
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
    n = _caixa_borrar(rng.random((lado, lado)).astype(np.float32), 1)
    n = _caixa_borrar(n.T, 30).T                                       # veio comprido (vertical)
    n = (n - n.min()) / max(1e-6, float(np.ptp(n)))
    tabua = (np.floor(xs / 128) * 7) % 5 / 5
    v = 0.3 + 0.45 * n + 0.15 * tabua
    cor = _c("#2a160a") * (1 - v[..., None]) + _c("#7a4a26") * v[..., None]
    junta = np.minimum(xs % 128, 128 - xs % 128)
    cor *= (0.55 + 0.45 * _suave(junta / 2))[..., None]
    return _rgb_img(np.clip(cor, 0, 1))


def _parede_oficina(W=1024, H=1024):
    """Parede da oficina: tábuas escuras com cintas de ferro rebitado na horizontal e manchas de fuligem."""
    rng = _rng("parede-oficina")
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    n = _caixa_borrar(rng.random((H, W)).astype(np.float32), 1)
    n = _caixa_borrar(n.T, 40).T
    n = (n - n.min()) / max(1e-6, float(np.ptp(n)))
    v = 0.25 + 0.5 * n
    cor = _c("#1e1008") * (1 - v[..., None]) + _c("#5a3418") * v[..., None]
    junta = np.minimum(xs % 160, 160 - xs % 160)
    cor *= (0.5 + 0.5 * _suave(junta / 2))[..., None]
    fuligem = _suave((_ruido(H, W, 80, rng) - 0.5) * 3)
    cor *= (1 - 0.4 * fuligem)[..., None]
    for y0 in (180, 700):                                              # cintas de ferro
        faixa = (ys >= y0) & (ys < y0 + 56)
        ferro = _c("#3a3430") * (0.8 + 0.3 * _ruido(H, W, 6, rng))[..., None]
        cor = np.where(faixa[..., None], ferro, cor)
        cor = np.where(((ys == y0) | (ys == y0 + 55))[..., None], cor * 0.4, cor)
        for x0 in range(40, W, 120):                                   # rebites
            d = np.hypot(xs - x0, ys - (y0 + 28))
            reb = np.exp(-(d / 7) ** 2)
            cor = cor + reb[..., None] * 0.35 * _c("#d8c8b0")
    return _rgb_img(np.clip(cor, 0, 1))


def _mostrador(lado=256):
    """Mostrador (manômetro): fundo creme, escala com números, faixa vermelha no fim. O ponteiro é do QML."""
    def d(p, W, H):
        c = QPointF(W / 2, H / 2)
        g = QRadialGradient(c, W / 2)
        g.setColorAt(0, QColor("#f4e8c8"))
        g.setColorAt(1, QColor("#c8b488"))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(c, W / 2 - 2, H / 2 - 2)
        p.setPen(QPen(QColor(150, 30, 20), 10))
        p.setBrush(Qt.BrushStyle.NoBrush)
        r = W * 0.36
        p.drawArc(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r), int(-45 * 16), int(50 * 16))   # zona vermelha
        p.setPen(QPen(QColor(40, 28, 16), 2))
        for k in range(11):                                              # risquinhos de 225° a -45°
            a = math.radians(225 - k * 27)
            r0, r1 = W * (0.32 if k % 2 else 0.28), W * 0.4
            p.drawLine(QPointF(c.x() + math.cos(a) * r0, c.y() - math.sin(a) * r0),
                       QPointF(c.x() + math.cos(a) * r1, c.y() - math.sin(a) * r1))
            if k % 2 == 0:
                rt = W * 0.2
                p.drawText(QRectF(c.x() + math.cos(a) * rt - 14, c.y() - math.sin(a) * rt - 9, 28, 18),
                           Qt.AlignmentFlag.AlignCenter, str(k * 10))
        p.drawText(QRectF(0, H * 0.62, W, 20), Qt.AlignmentFlag.AlignCenter, "PSI")
    return _pintar(lado, lado, d)


def _telegrafo(lado=1024):
    """Fundo do telégrafo de ordens: disco creme com aro, divisões em fatias (os textos das opções são do QML)."""
    def d(p, W, H):
        c = QPointF(W / 2, H / 2)
        g = QRadialGradient(c, W / 2)
        g.setColorAt(0, QColor("#f6ecd0"))
        g.setColorAt(0.9, QColor("#d8c49a"))
        g.setColorAt(1, QColor("#a08a5a"))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(c, W / 2 - 4, H / 2 - 4)
        p.setPen(QPen(QColor(60, 36, 14), 4))
        p.setBrush(Qt.BrushStyle.NoBrush)
        for k in range(6):                                               # 5 fatias (uma por opção) no semicírculo de cima
            a = math.radians(180 - k * 36)
            p.drawLine(QPointF(c.x() + math.cos(a) * W * 0.12, c.y() - math.sin(a) * W * 0.12),
                       QPointF(c.x() + math.cos(a) * W * 0.47, c.y() - math.sin(a) * W * 0.47))
        p.drawArc(QRectF(c.x() - W * 0.47, c.y() - H * 0.47, W * 0.94, H * 0.94), 0, 180 * 16)
        p.drawArc(QRectF(c.x() - W * 0.12, c.y() - H * 0.12, W * 0.24, H * 0.24), 0, 180 * 16)
        p.setPen(QPen(QColor(120, 20, 16), 3))
        p.drawLine(QPointF(c.x() - W * 0.47, c.y()), QPointF(c.x() + W * 0.47, c.y()))
        f = p.font()
        f.setPixelSize(int(W * 0.045))
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(60, 36, 14))
        p.drawText(QRectF(0, c.y() + H * 0.06, W, H * 0.08), Qt.AlignmentFlag.AlignCenter, "TELÉGRAFO DE ORDENS")
        p.drawText(QRectF(0, c.y() + H * 0.16, W, H * 0.08), Qt.AlignmentFlag.AlignCenter, "PONTE DE COMANDO")
    return _pintar(lado, lado, d)


def _ceu_nuvens(W=2048, H=1024):
    """Céu do fim de tarde visto do dirigível: dourado embaixo, azul em cima, mar de nuvens."""
    rng = _rng("ceu-nuvens")
    h2, w2 = H // 2, W // 2
    v = np.linspace(0, 1, h2, dtype=np.float32)[:, None] * np.ones((1, w2), np.float32)
    cor = (_c("#3a5a8a")[None, None] * (1 - v[..., None]) + _c("#f0b070")[None, None] * v[..., None])
    nuv = _ruido(h2, w2, 60, rng) * 0.6 + _ruido(h2, w2, 18, rng) * 0.4
    m = _suave((nuv - 0.55) * 4) * _suave((v - 0.35) * 3)
    cor = cor * (1 - m[..., None]) + _c("#fff0d8") * m[..., None] * (0.7 + 0.3 * nuv[..., None])
    cor = np.repeat(np.repeat(cor, 2, axis=0), 2, axis=1)
    return _rgb_img(np.clip(cor, 0, 1))


def _cidade_chamines(W=2048, H=512):
    """Cidade lá embaixo: silhueta de telhados e chaminés soltando fumaça (com alfa)."""
    rng = _rng("chamines")
    a = np.zeros((H, W), np.float32)
    x = 0
    topos = []
    while x < W:
        lw = int(rng.uniform(40, 120))
        topo = int(rng.uniform(H * 0.45, H * 0.8))
        a[topo:, x:x + lw] = 1
        if rng.random() < 0.5:                                           # chaminé
            cx = x + int(rng.uniform(5, max(6, lw - 20)))
            ct = topo - int(rng.uniform(40, 140))
            a[ct:, cx:cx + 14] = 1
            topos.append((cx + 7, ct))
        x += lw
    cor = np.ones((H, W, 3), np.float32) * _c("#3a2a30")
    jan = (rng.random((H, W)) > 0.9985).astype(np.float32)
    jan = _caixa_borrar(jan, 1) * 6
    cor = cor + np.clip(jan, 0, 1)[..., None] * _c("#ffc870")
    return _rgba(np.clip(cor, 0, 1), a)


def _nuvem(lado=256):
    rng = _rng("nuvem")
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32) / lado - 0.5
    d = np.hypot(xs * 1.2, ys * 2.2)
    a = _suave((0.45 - d) * 5) * (0.6 + 0.6 * _ruido(lado, lado, 20, rng))
    cor = np.ones((lado, lado, 3), np.float32) * _c("#fff4e4")
    cor *= (0.75 + 0.25 * (0.5 - ys))[..., None]
    return _rgba(np.clip(cor, 0, 1), np.clip(a, 0, 1))


def _lona_dirigivel(lado=512):
    """Lona do balão: gomos com costura e remendos."""
    rng = _rng("lona")
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
    gomo = np.minimum(xs % 64, 64 - xs % 64)
    cor = _c("#a89070") * (0.8 + 0.25 * _ruido(lado, lado, 30, rng))[..., None]
    cor *= (0.7 + 0.3 * _suave(gomo / 6))[..., None]
    return _rgb_img(np.clip(cor, 0, 1))
