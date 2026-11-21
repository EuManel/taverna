"""
☢ Cenários do tema Pós-apocalíptico (v0.59, pedido do Manel). Sorteia um (50/50, e de novo ao escolher o tema):

  CIDADE — cidade tomada pelas plantas ao entardecer: carros enferrujados (uma árvore crescendo de dentro de um),
           prédios cobertos de hera, semáforo caído, pólen/poeira na luz do sol, um cervo passando de vez em
           quando. O MENU É PICHADO COM SPRAY na lateral de um ônibus tombado; no hover a tinta da opção escorre
           fresca. Raramente (como o Cthulhu no farol) um zumbi cambaleia lá no fundo.
  ABRIGO — abrigo à noite: cerca de arame, fogo num tambor, rádio velho chiando, latas, lanterna, mapa com
           marcações. CADA OPÇÃO É UMA PLACA DE MADEIRA PINTADA À MÃO pregada na cerca; no hover o facho da
           lanterna ilumina a placa e ela balança. O rádio solta umas frases picotadas de vez em quando.

Aqui ficam as texturas (gravadas em arquivo, ver `estilizado.caminho_textura_3d`).
"""

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF,
                         QRadialGradient)

from .estilizado import _c, _caixa_borrar, _rgb_img, _rng, _ruido, _suave
from .terror_cenas import _guardado, _pintar, _rgba

# frases picotadas do rádio (inventadas)
FRASES_RADIO = ["...aqui é a estação... repito... zona norte...", "...não saiam depois que escurecer...",
                "...água limpa na represa... três dias...", "...alguém na escuta?... câmbio...",
                "...os portões fecham ao pôr do sol...", "...se ouvir isso... siga a estrada velha..."]


def textura(nome):
    f = {"ferrugem": _ferrugem, "madeira_placa": _madeira_placa,
         "cerca_arame": _cerca_arame, "terra_noite": _terra_noite, "mapa_marcado": _mapa_marcado,
         # cidade de dia (v0.59.1, refeita a pedido do Manel)
         "pa_ceu": _pa_ceu, "pa_lateral": _pa_lateral, "pa_frente": _pa_frente, "pa_teto": _pa_teto,
         "pa_amarelo": _pa_amarelo, "pa_compensado": _pa_compensado, "pa_folhas": _pa_folhas,
         "pa_capim": _pa_capim, "pa_casca": _pa_casca, "pa_hera": _pa_hera, "pa_calcada": _pa_calcada,
         "pa_asfalto": _pa_asfalto, "pa_tinta_carro": _pa_tinta_carro,
         "pa_predio0": lambda: _pa_predio(0), "pa_predio1": lambda: _pa_predio(1),
         "pa_predio2": lambda: _pa_predio(2), "pa_predio3": lambda: _pa_predio(3),
         "pa_loja0": lambda: _pa_loja(0), "pa_loja1": lambda: _pa_loja(1), "pa_loja2": lambda: _pa_loja(2),
         "pa_loja3": lambda: _pa_loja(3), "pa_loja4": lambda: _pa_loja(4), "pa_loja5": lambda: _pa_loja(5)}.get(nome)
    return _guardado(("posapoc", nome), f) if f else None


def _ferrugem(lado=512):
    rng = _rng("ferrugem")
    n = _ruido(lado, lado, 6, rng) * 0.5 + _ruido(lado, lado, 30, rng) * 0.5
    cor = _c("#4a2210") * (1 - n[..., None]) + _c("#b0582a") * n[..., None]
    buraco = _suave((_ruido(lado, lado, 14, rng) - 0.78) * 8)
    cor *= (1 - 0.7 * buraco)[..., None]
    return _rgb_img(np.clip(cor, 0, 1))


def _madeira_placa(lado=512):
    """Tábua velha pras placas pintadas à mão (o texto é do QML)."""
    rng = _rng("madeira-placa")
    n = _caixa_borrar(rng.random((lado, lado)).astype(np.float32), 1)
    n = _caixa_borrar(n, 30)
    n = (n - n.min()) / max(1e-6, float(np.ptp(n)))
    n2 = _caixa_borrar(_rng("placa2").random((lado, lado)).astype(np.float32).T, 40).T
    n2 = (n2 - n2.min()) / max(1e-6, float(np.ptp(n2)))
    v = 0.3 + 0.4 * n2 + 0.2 * n
    cor = _c("#3a2a1a") * (1 - v[..., None]) + _c("#9a7a52") * v[..., None]
    return _rgb_img(np.clip(cor, 0, 1))


def _cerca_arame(lado=256):
    """Tela de alambrado (losangos, alfa)."""
    def d(p, W, H):
        p.setPen(QPen(QColor(150, 150, 140), 3))
        passo = W / 4
        for k in range(-4, 9):
            p.drawLine(QPointF(k * passo, 0), QPointF(k * passo + H, H))
            p.drawLine(QPointF(k * passo, H), QPointF(k * passo + H, 0))
    return _pintar(lado, lado, d)


def _terra_noite(lado=512):
    rng = _rng("terra-noite")
    n = _ruido(lado, lado, 4, rng) * 0.5 + _ruido(lado, lado, 40, rng) * 0.5
    cor = _c("#2a2418") * (0.7 + 0.5 * n[..., None])
    return _rgb_img(np.clip(cor, 0, 1))


def _mapa_marcado(W=512, H=384):
    """Mapa velho com estradas, rio e marcações a caneta vermelha (X, círculos)."""
    rng = _rng("mapa")

    def d(p, w, h):
        p.fillRect(QRectF(0, 0, w, h), QColor("#d8c8a0"))
        p.setPen(QPen(QColor(90, 130, 170), 6))
        cam = [QPointF(0, h * 0.3)]
        for k in range(1, 8):
            cam.append(QPointF(w * k / 7, h * 0.3 + rng.uniform(-40, 40)))
        for a, b in zip(cam, cam[1:]):
            p.drawLine(a, b)
        p.setPen(QPen(QColor(120, 100, 70), 3))
        for _ in range(7):
            p.drawLine(QPointF(rng.uniform(0, w), rng.uniform(0, h)), QPointF(rng.uniform(0, w), rng.uniform(0, h)))
        p.setPen(QPen(QColor(180, 30, 30), 4))
        for _ in range(3):
            x, y = rng.uniform(40, w - 40), rng.uniform(40, h - 40)
            p.drawLine(QPointF(x - 12, y - 12), QPointF(x + 12, y + 12))
            p.drawLine(QPointF(x - 12, y + 12), QPointF(x + 12, y - 12))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(w * 0.62, h * 0.58), 40, 28)
        p.setPen(QPen(QColor(60, 40, 20, 60), 2))
        p.drawLine(QPointF(w / 2, 0), QPointF(w / 2, h))
        p.drawLine(QPointF(0, h / 2), QPointF(w, h / 2))
    return _pintar(W, H, d)


# ====================================================================== CIDADE DE DIA (v0.59.1, refeita)
# Dia nublado, ônibus escolar amarelo abandonado com o menu pichado, prédios com janelas e lojas, árvores de folha.

def _tile_h(n):
    """Deixa um ruído emendável na horizontal (o céu dá a volta)."""
    W = n.shape[1]
    t = _suave((np.abs(np.linspace(-1, 1, W, dtype=np.float32)) - 0.55) / 0.45)[None, :]
    return n * (1 - t) + np.roll(n, W // 2, axis=1) * t


def _norm(a):
    return (a - a.min()) / max(1e-6, float(np.ptp(a)))


def _misturar(cor, outra, m):
    m = np.clip(m, 0, 1)[..., None]
    return cor * (1 - m) + outra * m


def _pa_ceu(W=2048, H=1024):
    """Céu NUBLADO (equiretangular: serve de fundo e de luz ambiente): cinza claro, nuvens baixas pesadas."""
    rng = _rng("pa-ceu")
    e = (0.5 - (np.arange(H, dtype=np.float32) + 0.5) / H) * 2          # elevação: 1 = zênite, -1 = chão
    e = np.repeat(e[:, None], W, axis=1)
    alto = np.clip(e, 0, 1)
    a = (alto ** 0.45)[..., None]
    ceu = _c("#cdd0cd") * (1 - a) + _c("#8b9398") * a
    n = (_tile_h(_ruido(H, W, 70, rng)) * 0.5 + _tile_h(_ruido(H, W, 22, rng)) * 0.32
         + _tile_h(_ruido(H, W, 7, rng)) * 0.18)
    peso = _suave(alto * 7)                                                # perto do horizonte some na névoa
    ceu = ceu * (1 + ((n - 0.5) * 0.5 * peso)[..., None])
    ceu = ceu * (1 - 0.2 * (_suave((0.42 - n) * 6) * peso)[..., None])  # barriga escura das nuvens
    b = np.clip(-e, 0, 1)[..., None]
    chao = _c("#77746c") * (1 - b) + _c("#4c4a45") * b
    m = _suave((e + 0.015) / 0.03)[..., None]
    return _rgb_img(np.clip(ceu * m + chao * (1 - m), 0, 1))


def _escorridos(H, W, rng, quantos, comp=(40, 220), larg=(1.5, 5), y0=(0.05, 0.7)):
    """Escorridos verticais (ferrugem, chuva) que vão sumindo pra baixo."""
    esc = np.zeros((H, W), np.float32)
    for _ in range(quantos):
        x0 = rng.uniform(0, W)
        ya = int(rng.uniform(*y0) * H)
        c = rng.uniform(*comp)
        lg = rng.uniform(*larg)
        xa, xb = int(max(0, x0 - 4 * lg)), int(min(W, x0 + 4 * lg + 1))
        yb = int(min(H, ya + c))
        if xb <= xa or yb <= ya:
            continue
        xx = np.arange(xa, xb, dtype=np.float32)
        yy = np.arange(ya, yb, dtype=np.float32)
        esc[ya:yb, xa:xb] += (np.exp(-((xx[None, :] - x0) / lg) ** 2) * (1 - (yy[:, None] - ya) / c)
                              * rng.uniform(0.35, 1))
    return np.clip(esc, 0, 1)


def _pintura_amarela(H, W, rng):
    """Amarelo-gema de ônibus escolar: desbotado em cima, sujeira subindo de baixo, tinta descascando até o
    primer e a ferrugem, escorridos de ferrugem."""
    ys = np.mgrid[0:H, 0:W][0].astype(np.float32)
    n = _ruido(H, W, 40, rng)
    n2 = _ruido(H, W, 3, rng)
    cor = _c("#eaa814") * (0.9 + 0.12 * n + 0.06 * n2)[..., None]
    cor = _misturar(cor, _c("#f4dc96"), _suave(1 - ys / (H * 0.4)) * 0.16)
    cor = _misturar(cor, _c("#5e4b2e"), _suave((ys / H - 0.45) * 2.0) * (0.3 + 0.35 * _ruido(H, W, 12, rng)))
    combo = _ruido(H, W, 14, rng) * 0.6 + _ruido(H, W, 3, rng) * 0.4
    baixo = _suave((ys / H - 0.6) * 3)
    ferr_m = _suave((combo - 0.8 + 0.16 * baixo) * 14)
    primer = np.clip(_suave((combo - 0.76 + 0.16 * baixo) * 14) - ferr_m, 0, 1)
    ferr = _c("#6a3216") * (0.6 + 0.7 * _ruido(H, W, 2, rng))[..., None]
    cor = _misturar(cor, _c("#8c887c"), primer * 0.7)
    cor = cor * (1 - ferr_m[..., None]) + ferr * ferr_m[..., None]
    cor = _misturar(cor, _c("#7a3c16"), _escorridos(H, W, rng, int(W * H / 16000)) * 0.7)
    return cor


def _rebite(p, x, y, r=3.2):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(70, 52, 24, 200))
    p.drawEllipse(QPointF(x + 0.8, y + 0.8), r, r)
    p.setBrush(QColor(255, 236, 170, 150))
    p.drawEllipse(QPointF(x - 0.6, y - 0.6), r * 0.55, r * 0.55)


def _vidro(p, r, escuro=False):
    """Vidro velho refletindo o céu nublado (gradiente + um reflexo na diagonal)."""
    g = QLinearGradient(r.topLeft(), r.bottomLeft())
    if escuro:
        g.setColorAt(0, QColor(60, 66, 70))
        g.setColorAt(1, QColor(16, 18, 20))
    else:
        g.setColorAt(0, QColor(158, 168, 172))
        g.setColorAt(0.5, QColor(96, 106, 112))
        g.setColorAt(1, QColor(38, 44, 48))
    p.fillRect(r, QBrush(g))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 255, 255, 26))
    w, h = r.width(), r.height()
    p.drawPolygon(QPolygonF([QPointF(r.left() + w * 0.15, r.top()), QPointF(r.left() + w * 0.45, r.top()),
                             QPointF(r.left() + w * 0.1, r.bottom()), QPointF(r.left() - w * 0.2, r.bottom())]))


def _trinca(p, x, y, rng, raio=60):
    """Vidro trincado: raios saindo do ponto do impacto + anéis."""
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(QColor(225, 230, 230, 190), 1.3))
    for i in range(11):
        a = i / 11 * 2 * math.pi + rng.uniform(-0.2, 0.2)
        px, py = x, y
        for _k in range(5):
            a += rng.uniform(-0.25, 0.25)
            nx, ny = px + math.cos(a) * raio / 5 * rng.uniform(0.7, 1.3), py + math.sin(a) * raio / 5 * rng.uniform(0.7, 1.3)
            p.drawLine(QPointF(px, py), QPointF(nx, ny))
            px, py = nx, ny
    for rr in (raio * 0.25, raio * 0.55):
        pts = [QPointF(x + math.cos(t / 9 * 2 * math.pi) * rr * rng.uniform(0.8, 1.2),
                       y + math.sin(t / 9 * 2 * math.pi) * rr * rng.uniform(0.8, 1.2)) for t in range(10)]
        for a, b in zip(pts, pts[1:]):
            p.drawLine(a, b)
    p.setBrush(QColor(20, 22, 24, 220))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(x, y), raio * 0.08, raio * 0.07)


def _pa_lateral(W=2048, H=512):
    """Lateral do ônibus (1200 x 300 cm, frente à esquerda): pintura amarela gasta, caixas de roda, porta de vidro,
    os vãos das janelas (as tábuas e vidros vêm em 3D por cima), costuras com rebites."""
    rng = _rng("pa-lateral")
    k = W / 1200.0

    def X(x):
        return (x + 600) * k

    def Y(y):
        return (340 - y) * k
    cor = _pintura_amarela(H, W, rng)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    for cx in (-430, 400):                                                  # ferrugem em volta das caixas de roda
        d = np.hypot(xs - X(cx), ys - Y(52)) / k
        cor = _misturar(cor, _c("#5a2a12") * 1.1, _suave((95 - d) / 25) * (0.5 + 0.5 * _ruido(H, W, 5, rng)))
    img = _rgb_img(np.clip(cor, 0, 1))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # caixas de roda
    for cx in (-430, 400):
        r = 74 * k
        c = QPointF(X(cx), Y(52))
        caminho = QPainterPath(QPointF(c.x() - r, H))
        caminho.lineTo(c.x() - r, c.y())
        caminho.arcTo(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r), 180, -180)
        caminho.lineTo(c.x() + r, H)
        caminho.closeSubpath()
        p.setPen(QPen(QColor(30, 26, 22), 7))
        p.setBrush(QColor(14, 13, 12))
        p.drawPath(caminho)
    # vãos das janelas (borracha preta)
    for i in range(8):
        x0 = -470 + i * 125
        r = QRectF(X(x0), Y(322), 105 * k, 107 * k)
        p.setPen(QPen(QColor(12, 12, 12), 9))
        p.setBrush(QColor(10, 11, 12))
        p.drawRoundedRect(r, 14, 14)
    # porta sanfonada de vidro (frente, antes da roda)
    porta = QRectF(X(-595), Y(325), 85 * k, 280 * k)
    p.setPen(QPen(QColor(16, 16, 16), 8))
    p.setBrush(QColor(20, 20, 20))
    p.drawRect(porta)
    meio = porta.center().x()
    for lx in (porta.left(), meio):
        folha = QRectF(lx + 6, porta.top() + 6, porta.width() / 2 - 12, porta.height() - 12)
        alto = QRectF(folha.left(), folha.top(), folha.width(), folha.height() * 0.48)
        baixo = QRectF(folha.left(), folha.top() + folha.height() * 0.53, folha.width(), folha.height() * 0.47)
        _vidro(p, alto)
        _vidro(p, baixo, escuro=True)
    _trinca(p, porta.left() + porta.width() * 0.7, porta.top() + porta.height() * 0.3, rng, 40)
    p.setPen(QPen(QColor(16, 16, 16), 7))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(meio, porta.top()), QPointF(meio, porta.bottom()))
    # costuras e rebites
    for i in range(9):
        x = X(-470 + i * 125 - 10)
        p.setPen(QPen(QColor(70, 50, 20, 120), 2))
        p.drawLine(QPointF(x, Y(205)), QPointF(x, Y(46)))
        yy = Y(200)
        while yy < Y(50):
            if not any(abs(x - X(cx)) < 82 * k and yy > Y(130) for cx in (-430, 400)):
                _rebite(p, x - 5, yy)
                _rebite(p, x + 5, yy)
            yy += 22
    for yv in (Y(208), Y(120)):
        xx = X(-505)
        while xx < W - 6:
            if not any(abs(xx - X(cx)) < 82 * k for cx in (-430, 400)) or yv < Y(130):
                _rebite(p, xx, yv)
            xx += 26
    # o número do ônibus, lá atrás
    f = QFont("Arial", 1)
    f.setPixelSize(int(46 * k))
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor(24, 22, 20, 210))
    p.drawText(QRectF(X(515), Y(320), 80 * k, 60 * k), Qt.AlignmentFlag.AlignCenter, "07")
    p.end()
    return img


def _pa_frente(W=512, H=616):
    """Frente do ônibus (250 x 300 cm): para-brisa trincado, letreiro apagado, ESCOLAR, faróis, grade."""
    rng = _rng("pa-frente")
    k = W / 250.0

    def X(u):
        return u * k

    def Y(y):
        return (340 - y) * k
    img = _rgb_img(np.clip(_pintura_amarela(H, W, rng), 0, 1))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # para-brisa em duas partes
    for u0 in (10, 128):
        r = QRectF(X(u0), Y(306), 112 * k, 122 * k)
        _vidro(p, r)
        p.setPen(QPen(QColor(14, 14, 14), 9))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(r, 10, 10)
    _trinca(p, X(190), Y(240), rng, 70)
    # letreiro de destino
    let = QRectF(X(28), Y(337), 194 * k, 26 * k)
    p.fillRect(let, QColor(14, 14, 12))
    f = QFont("Consolas", 1)
    f.setPixelSize(int(17 * k))
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor(255, 160, 40, 120))
    p.drawText(let, Qt.AlignmentFlag.AlignCenter, "FORA DE SERVIÇO")
    # ESCOLAR
    f = QFont("Arial Black", 1)
    f.setPixelSize(int(24 * k))
    p.setFont(f)
    p.setPen(QColor(20, 18, 14, 225))
    p.drawText(QRectF(0, Y(178), W, 30 * k), Qt.AlignmentFlag.AlignCenter, "ESCOLAR")
    # grade
    gr = QRectF(X(78), Y(128), 94 * k, 58 * k)
    p.fillRect(gr, QColor(20, 20, 18))
    p.setPen(QPen(QColor(110, 108, 100), 3))
    yy = gr.top() + 8
    while yy < gr.bottom() - 4:
        p.drawLine(QPointF(gr.left() + 6, yy), QPointF(gr.right() - 6, yy))
        yy += 14
    # faróis (um quebrado) + setas
    for u, quebrado in ((36, False), (214, True)):
        r = QRectF(X(u - 26), Y(112), 52 * k, 32 * k)
        p.setPen(QPen(QColor(170, 170, 162), 6))
        if quebrado:
            p.setBrush(QColor(22, 22, 22))
        else:
            g = QRadialGradient(r.center(), r.width() * 0.6)
            g.setColorAt(0, QColor(236, 236, 226))
            g.setColorAt(1, QColor(150, 154, 150))
            p.setBrush(QBrush(g))
        p.drawRoundedRect(r, 16, 16)
        if quebrado:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(200, 204, 200, 200))
            p.drawPolygon(QPolygonF([r.topLeft() + QPointF(8, 6), r.topLeft() + QPointF(40, 8),
                                     r.topLeft() + QPointF(14, 30)]))
        p.setPen(QPen(QColor(60, 40, 10), 3))
        p.setBrush(QColor(220, 130, 30))
        p.drawRoundedRect(QRectF(X(u - 16), Y(132), 32 * k, 12 * k), 5, 5)
    p.end()
    return img


def _pa_teto(W=1024, H=256):
    """Teto do ônibus: branco-amarelado sujo, musgo, folhas secas, escotilhas."""
    rng = _rng("pa-teto")
    n = _ruido(H, W, 30, rng) * 0.6 + _ruido(H, W, 3, rng) * 0.4
    cor = _c("#d2c9a6") * (0.75 + 0.3 * n)[..., None]
    cor = _misturar(cor, _c("#4e5a2c"), _suave((_ruido(H, W, 16, rng) - 0.62) * 7) * 0.85)
    cor = _misturar(cor, _c("#6a3a1a"), _suave((_ruido(H, W, 6, rng) - 0.75) * 10))
    img = _rgb_img(np.clip(cor, 0, 1))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    for x in (W * 0.25, W * 0.68):
        r = QRectF(x - 60, H / 2 - 55, 120, 110)
        p.setPen(QPen(QColor(90, 86, 74), 6))
        p.setBrush(QColor(160, 156, 140))
        p.drawRoundedRect(r, 8, 8)
    p.setPen(Qt.PenStyle.NoPen)
    for _ in range(500):                                                     # folhas secas
        p.setBrush(QColor(int(rng.uniform(90, 150)), int(rng.uniform(60, 90)), int(rng.uniform(20, 40)), 220))
        p.save()
        p.translate(rng.uniform(0, W), rng.uniform(0, H))
        p.rotate(rng.uniform(0, 360))
        s = rng.uniform(3, 7)
        p.drawEllipse(QPointF(0, 0), s, s * 0.5)
        p.restore()
    p.end()
    return img


def _pa_amarelo(lado=512):
    return _rgb_img(np.clip(_pintura_amarela(lado, lado, _rng("pa-amarelo")), 0, 1))


def _pa_compensado(W=512, H=256):
    """Chapa de compensado velha (tapando janela): veio, acinzentado pelo tempo, manchas d'água, pregos."""
    rng = _rng("pa-compensado")
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    veio = _norm(_caixa_borrar(np.repeat(rng.random((H, W // 32)).astype(np.float32), 32, axis=1), 3))
    ondas = 0.5 + 0.5 * np.sin(ys * 0.22 + 7 * _ruido(H, W, 30, rng))
    v = 0.5 * veio + 0.3 * ondas + 0.2 * _ruido(H, W, 3, rng)
    cor = _c("#6e583c") * (1 - v[..., None]) + _c("#c0a476") * v[..., None]
    cor = _misturar(cor, _c("#8e8a80"), (_ruido(H, W, 25, rng) * 0.5 + 0.15))
    cor *= (1 - 0.35 * _suave((_ruido(H, W, 18, rng) - 0.68) * 6))[..., None]
    borda = np.minimum(np.minimum(xs, W - 1 - xs), np.minimum(ys, H - 1 - ys))
    cor *= (0.55 + 0.45 * _suave(borda / 10))[..., None]
    cor = _misturar(cor, _c("#5a2c12"), _escorridos(H, W, rng, 8, (30, 120), (1.5, 3), (0.02, 0.1)) * 0.6)
    img = _rgb_img(np.clip(cor, 0, 1))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    for x in (16, W / 2, W - 16):
        for y in (16, H - 16):
            p.setBrush(QColor(36, 32, 28))
            p.drawEllipse(QPointF(x, y), 4.5, 4.5)
            p.setBrush(QColor(150, 140, 120, 160))
            p.drawEllipse(QPointF(x - 1, y - 1), 1.6, 1.6)
    p.end()
    return img


def _pa_folhas(lado=512):
    """Um galho cheio de folhas (alfa recortado): as copas das árvores e as moitas são feitas de várias destas."""
    rng = _rng("pa-folhas")

    def d(p, W, H):
        cx, cy, R = W / 2, H / 2, W * 0.44
        p.setPen(QPen(QColor(64, 48, 32), 6))
        for _ in range(7):
            a = rng.uniform(0, 2 * math.pi)
            r = R * rng.uniform(0.4, 0.85)
            p.drawLine(QPointF(cx, cy + R * 0.55), QPointF(cx + math.cos(a) * r, cy + math.sin(a) * r * 0.8))
        for camada in range(3):
            for _ in range(340):
                a = rng.uniform(0, 2 * math.pi)
                r = R * math.sqrt(rng.random()) * (0.78 + 0.11 * camada)
                x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.9
                L = rng.uniform(22, 36)
                w = L * rng.uniform(0.3, 0.45)
                luz = (0.62 + 0.24 * camada) * (1.25 - 0.5 * (y / H)) * rng.uniform(0.85, 1.15)
                base = (120, 122, 44) if rng.random() < 0.07 else ((40, 84, 30) if rng.random() < 0.5 else (58, 96, 34))
                c = QColor(*[int(min(255, v * luz)) for v in base])
                p.save()
                p.translate(x, y)
                p.rotate(math.degrees(a) + rng.uniform(-60, 60))
                folha = QPainterPath(QPointF(0, 0))
                folha.quadTo(L * 0.5, -w, L, 0)
                folha.quadTo(L * 0.5, w, 0, 0)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(c)
                p.drawPath(folha)
                p.setPen(QPen(c.darker(145), 1.2))
                p.drawLine(QPointF(1, 0), QPointF(L * 0.85, 0))
                p.restore()
    return _pintar(lado, lado, d)


def _pa_capim(lado=256):
    """Tufo de capim (alfa): folhas finas saindo de baixo, umas verdes, umas secas."""
    rng = _rng("pa-capim")

    def d(p, W, H):
        p.setPen(Qt.PenStyle.NoPen)
        for _ in range(110):
            x = W / 2 + rng.normal(0, W * 0.15)
            h = rng.uniform(0.3, 0.97) * H
            lg = rng.uniform(3, 7)
            curva = rng.uniform(-0.4, 0.4) * h
            seco = rng.random() ** 2
            c0 = QColor(int(46 + 110 * seco), int(84 + 70 * seco), int(26 + 40 * seco))
            folha = QPainterPath(QPointF(x - lg / 2, H))
            folha.quadTo(x - lg / 2 + curva * 0.2, H - h * 0.6, x + curva, H - h)
            folha.quadTo(x + lg / 2 + curva * 0.2, H - h * 0.6, x + lg / 2, H)
            g = QLinearGradient(0, H, 0, H - h)
            g.setColorAt(0, c0.darker(190))
            g.setColorAt(1, c0.lighter(125))
            p.setBrush(QBrush(g))
            p.drawPath(folha)
    return _pintar(lado, lado, d)


def _pa_casca(W=256, H=512):
    """Casca de árvore: sulcos verticais, musgo."""
    rng = _rng("pa-casca")
    v = _norm(_caixa_borrar(np.repeat(rng.random((H // 16, W)).astype(np.float32), 16, axis=0), 2))
    n = _ruido(H, W, 6, rng)
    cor = _c("#544a3e") * (0.75 + 0.4 * n)[..., None]
    cor *= (1 - 0.65 * _suave((0.32 - v) * 6))[..., None]
    cor = _misturar(cor, _c("#4a5a2a"), _suave((_ruido(H, W, 20, rng) - 0.62) * 6) * 0.6)
    return _rgb_img(np.clip(cor, 0, 1))


def _pa_hera(W=512, H=1024):
    """Hera (alfa): uma massa de folhas no alto e ramos pendurados descendo pela parede."""
    rng = _rng("pa-hera")

    def folha(p, x, y, s, c):
        p.setBrush(c)
        p.drawEllipse(QPointF(x - s * 0.3, y), s * 0.45, s * 0.4)
        p.drawEllipse(QPointF(x + s * 0.3, y), s * 0.45, s * 0.4)
        p.drawPolygon(QPolygonF([QPointF(x - s * 0.7, y + s * 0.1), QPointF(x + s * 0.7, y + s * 0.1),
                                 QPointF(x, y + s * 0.85)]))

    def cor():
        g = rng.uniform(0.7, 1.35)
        return QColor(int(min(255, 40 * g)), int(min(255, 82 * g)), int(min(255, 30 * g)))

    def d(p, W, H):
        for _ in range(48):                                                   # ramos pendurados
            x = rng.uniform(0, W)
            comp = H * rng.uniform(0.25, 0.97)
            fase = rng.uniform(0, 6)
            p.setPen(QPen(QColor(70, 56, 36), 2))
            ramo = QPainterPath(QPointF(x, 0))
            y = 0.0
            while y < comp:
                y += 20
                ramo.lineTo(x + math.sin(y * 0.01 + fase) * 14, y)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(ramo)
            p.setPen(Qt.PenStyle.NoPen)
            y = 0.0
            while y < comp:
                if rng.random() < 0.85:
                    folha(p, x + math.sin(y * 0.01 + fase) * 14 + rng.uniform(-9, 9), y, rng.uniform(9, 18), cor())
                y += rng.uniform(6, 12)
        p.setPen(Qt.PenStyle.NoPen)
        for _ in range(1700):                                                 # a massa lá no alto
            folha(p, rng.uniform(0, W), H * 0.24 * rng.random() ** 1.7, rng.uniform(10, 20), cor())
    return _pintar(W, H, d)


def _pa_calcada(lado=512):
    """Calçada de placas de concreto (100 cm cada): juntas com mato, rachaduras, sujeira."""
    rng = _rng("pa-calcada")
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
    passo = lado // 4
    tom = rng.random((4, 4)).astype(np.float32)[(ys // passo).astype(int), (xs // passo).astype(int)]
    n = _ruido(lado, lado, 30, rng) * 0.5 + _ruido(lado, lado, 2, rng) * 0.5
    cor = _c("#a7a398") * (0.78 + 0.12 * tom + 0.16 * n)[..., None]
    cor = _misturar(cor, _c("#6a604a"), _suave((_ruido(lado, lado, 40, rng) - 0.5) * 3) * 0.35)
    junta = ((xs % passo) < 3) | ((ys % passo) < 3)
    cor[junta] *= 0.42
    img = _rgb_img(np.clip(cor, 0, 1))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    for _ in range(260):                                                      # mato nas juntas
        if rng.random() < 0.5:
            x, y = rng.integers(0, 4) * passo + 1.5, rng.uniform(0, lado)
        else:
            x, y = rng.uniform(0, lado), rng.integers(0, 4) * passo + 1.5
        g = rng.uniform(0.7, 1.3)
        p.setPen(QPen(QColor(int(60 * g), int(100 * g), int(36 * g), 230), rng.uniform(2, 5)))
        p.drawLine(QPointF(x, y), QPointF(x + rng.uniform(-5, 5), y + rng.uniform(-5, 5)))
    for _ in range(8):                                                        # rachaduras
        x, y = rng.uniform(0, lado), rng.uniform(0, lado)
        a = rng.uniform(0, 2 * math.pi)
        p.setPen(QPen(QColor(40, 38, 34, 200), 1.6))
        for _k in range(8):
            a += rng.uniform(-0.6, 0.6)
            nx, ny = x + math.cos(a) * 10, y + math.sin(a) * 10
            p.drawLine(QPointF(x, y), QPointF(nx, ny))
            x, y = nx, ny
    p.end()
    return img


def _pa_asfalto(W=2048, H=1024):
    """Asfalto de dia (2200 x 1100 cm): pista dupla amarela no meio, faixas brancas tracejadas, tudo gasto;
    remendos, manchas de óleo, rachaduras com mato."""
    rng = _rng("pa-asfalto")
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    k = W / 2200.0
    n = _ruido(H, W, 60, rng) * 0.45 + _ruido(H, W, 8, rng) * 0.25 + rng.random((H, W)).astype(np.float32) * 0.3
    cor = _c("#67645d") * (0.78 + 0.35 * n)[..., None]
    for _ in range(5):                                                        # remendos
        x0, y0 = rng.uniform(0, W - 300), rng.uniform(0, H - 200)
        rem = (xs > x0) & (xs < x0 + rng.uniform(120, 300)) & (ys > y0) & (ys < y0 + rng.uniform(80, 200))
        cor[rem] *= 0.78
    gasta = _suave((_ruido(H, W, 4, rng) * 0.7 + _ruido(H, W, 30, rng) * 0.3 - 0.38) * 5)

    def faixa(xc, larg, tracejada=False):
        m = (np.abs(xs - xc) < larg * k / 2).astype(np.float32)
        if tracejada:
            m *= ((ys % (H / 2)) < H * 0.27)
        return m * gasta
    amarela = np.maximum(faixa(W / 2 - 12 * k, 12), faixa(W / 2 + 12 * k, 12))
    branca = np.maximum.reduce([faixa(W * 0.25, 12, True), faixa(W * 0.75, 12, True), faixa(40 * k, 15),
                                faixa(W - 40 * k, 15)])
    cor = _misturar(cor, _c("#c9a43a"), amarela * 0.75)
    cor = _misturar(cor, _c("#d2d0c6"), branca * 0.7)
    oleo = np.maximum(_suave(1 - np.abs(xs - W * 0.375) / (90 * k)), _suave(1 - np.abs(xs - W * 0.625) / (90 * k)))
    cor *= (1 - 0.25 * oleo * _suave((_ruido(H, W, 20, rng) - 0.5) * 4))[..., None]
    img = _rgb_img(np.clip(cor, 0, 1))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    for _ in range(46):                                                       # rachaduras com mato
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        a = rng.uniform(0, 2 * math.pi)
        for _k in range(int(rng.uniform(10, 34))):
            a += rng.uniform(-0.6, 0.6)
            nx, ny = x + math.cos(a) * rng.uniform(8, 20), y + math.sin(a) * rng.uniform(8, 20)
            p.setPen(QPen(QColor(22, 20, 18, 220), rng.uniform(1.5, 3.2)))
            p.drawLine(QPointF(x, y), QPointF(nx, ny))
            if rng.random() < 0.4:
                g = rng.uniform(0.7, 1.3)
                p.setPen(QPen(QColor(int(64 * g), int(104 * g), int(38 * g), 235), rng.uniform(3, 7)))
                p.drawPoint(QPointF(nx + rng.uniform(-3, 3), ny + rng.uniform(-3, 3)))
            x, y = nx, ny
    p.end()
    return img


def _pa_tinta_carro(lado=512):
    """Lataria clara gasta (a cor do carro vem do QML): desbotada, ferrugem em bolhas e embaixo, poeira."""
    rng = _rng("pa-carro")
    ys = np.mgrid[0:lado, 0:lado][0].astype(np.float32)
    n = _ruido(lado, lado, 30, rng) * 0.6 + _ruido(lado, lado, 3, rng) * 0.4
    cor = _c("#e2ded6") * (0.8 + 0.22 * n)[..., None]
    cor = _misturar(cor, _c("#a89a80"), _suave((ys / lado - 0.5) * 2.5) * 0.5)
    combo = _ruido(lado, lado, 10, rng) * 0.6 + _ruido(lado, lado, 2, rng) * 0.4
    ferr = _suave((combo - 0.72 + 0.25 * _suave((ys / lado - 0.6) * 3)) * 14)
    cor = _misturar(cor, _c("#8a5a3a"), ferr)                                # (fica marrom com a cor por cima)
    return _rgb_img(np.clip(cor, 0, 1))


# fachadas: (tipo, cor da parede, cor da esquadria)
_PREDIOS = [("reboco", "#bdb197", "#e2dccf"), ("tijolo", "#8c4b37", "#d0c9bb"),
            ("concreto", "#8d9597", "#3c3c3a"), ("reboco", "#a3b19f", "#ece6da")]


def _pa_predio(var, lado=1024):
    """Fachada de prédio abandonado (4 janelas x 3 andares = 1400 x 1050 cm, repete): reboco caindo e mostrando
    o tijolo, escorridos de chuva, janelas — vidro sujo refletindo o céu, quebradas, tapadas com tábua, com
    cortina velha; ar-condicionado enferrujado."""
    tipo, base, esq = _PREDIOS[var]
    rng = _rng("pa-predio", var)
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
    n = _ruido(lado, lado, 50, rng) * 0.6 + _ruido(lado, lado, 3, rng) * 0.4
    cor = _c(base) * (0.82 + 0.25 * n)[..., None]
    if tipo in ("tijolo", "reboco"):
        fila = (ys // 22).astype(int)
        desl = (fila % 2) * 28
        col = ((xs + desl) // 56).astype(int)
        tom = rng.random((fila.max() + 1, col.max() + 2)).astype(np.float32)[fila, col]
        tij = _c("#8c4b37") * ((0.72 + 0.38 * tom) * (0.9 + 0.2 * n))[..., None]
        arg = ((ys % 22) < 3) | (((xs + desl) % 56) < 3)
        tij[arg] = _c("#a89c8a") * 0.9
        if tipo == "tijolo":
            cor = tij
        else:
            caiu = _suave((_ruido(lado, lado, 30, rng) - 0.66) * 10)
            cor = _misturar(cor, tij, caiu)
    else:
        cor[((xs % 256) < 3) | ((ys % 341) < 3)] *= 0.72
    andar = np.zeros_like(n)
    for f in range(3):
        andar += ((ys >= f * 341 + 318) & (ys < f * 341 + 336)).astype(np.float32)
    cor = _misturar(cor, _c(base) * 1.1, andar * 0.7)
    chuva = _norm(_caixa_borrar(rng.random((1, lado)).astype(np.float32), 3)) ** 3
    chuva = np.repeat(chuva, lado, axis=0) * (0.5 + 0.5 * _ruido(lado, lado, 40, rng))
    cor *= (1 - 0.4 * chuva)[..., None]
    cor = _misturar(cor, _c("#4e5a30"), _suave((_ruido(lado, lado, 25, rng) - 0.7) * 6) * 0.5)
    img = _rgb_img(np.clip(cor, 0, 1))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    parede = QColor(base).lighter(118)
    estados = rng.choice(["vidro", "quebrado", "tabuas", "escuro", "cortina"], size=12, p=[.3, .27, .17, .13, .13])
    for f in range(3):
        for c in range(4):
            x0, y0, w, h = c * 256 + 58, f * 341 + 70, 140, 200
            r = QRectF(x0, y0, w, h)
            p.fillRect(QRectF(x0 - 10, y0 - 12, w + 20, 12), parede)              # verga
            g = QLinearGradient(0, y0 + h + 10, 0, y0 + h + 120)                 # escorrido do peitoril
            g.setColorAt(0, QColor(30, 30, 22, 120))
            g.setColorAt(1, QColor(30, 30, 22, 0))
            p.fillRect(QRectF(x0 + 8, y0 + h + 10, w - 16, 110), QBrush(g))
            p.fillRect(QRectF(x0 - 12, y0 + h, w + 24, 11), parede)               # peitoril
            g = QLinearGradient(r.topLeft(), r.bottomLeft())
            g.setColorAt(0, QColor(30, 30, 30))
            g.setColorAt(1, QColor(12, 12, 13))
            p.fillRect(r, QBrush(g))
            e = estados[f * 4 + c]
            if e == "vidro":
                _vidro(p, r.adjusted(6, 6, -6, -6))
            elif e == "quebrado":
                p.setPen(Qt.PenStyle.NoPen)
                for _ in range(rng.integers(3, 7)):
                    lado_v = rng.integers(0, 4)
                    t0, t1 = sorted(rng.uniform(0, 1, 2))
                    if lado_v == 0:
                        a, b = QPointF(x0 + w * t0, y0), QPointF(x0 + w * t1, y0)
                    elif lado_v == 1:
                        a, b = QPointF(x0 + w * t0, y0 + h), QPointF(x0 + w * t1, y0 + h)
                    elif lado_v == 2:
                        a, b = QPointF(x0, y0 + h * t0), QPointF(x0, y0 + h * t1)
                    else:
                        a, b = QPointF(x0 + w, y0 + h * t0), QPointF(x0 + w, y0 + h * t1)
                    ponta = QPointF(x0 + w * rng.uniform(0.2, 0.8), y0 + h * rng.uniform(0.2, 0.8))
                    ponta = (a + b) / 2 + (ponta - (a + b) / 2) * rng.uniform(0.3, 0.7)
                    p.setBrush(QColor(120, 130, 134, 200))
                    p.drawPolygon(QPolygonF([a, b, ponta]))
            elif e == "tabuas":
                for t in range(3):
                    p.save()
                    p.translate(x0 + w / 2, y0 + 40 + t * 60)
                    p.rotate(rng.uniform(-14, 14))
                    gm = rng.uniform(0.75, 1.15)
                    p.fillRect(QRectF(-w * 0.62, -15, w * 1.24, 30), QColor(int(132 * gm), int(104 * gm), int(70 * gm)))
                    p.setPen(QPen(QColor(60, 44, 30), 1.5))
                    p.drawLine(QPointF(-w * 0.6, -6), QPointF(w * 0.6, -4))
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QColor(30, 26, 22))
                    p.drawEllipse(QPointF(-w * 0.5, 0), 3, 3)
                    p.drawEllipse(QPointF(w * 0.5, 0), 3, 3)
                    p.restore()
            elif e == "cortina":
                cc = QColor(*[(150, 64, 54), (60, 84, 130), (140, 120, 70)][rng.integers(0, 3)])
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(cc)
                p.drawPolygon(QPolygonF([QPointF(x0 + 6, y0 + 6), QPointF(x0 + w * 0.55, y0 + 6),
                                         QPointF(x0 + w * 0.3, y0 + h * 0.7), QPointF(x0 + w * 0.2, y0 + h - 6),
                                         QPointF(x0 + 6, y0 + h - 6)]))
                p.setPen(QPen(cc.darker(150), 2))
                for i in range(4):
                    p.drawLine(QPointF(x0 + 14 + i * 14, y0 + 8), QPointF(x0 + 12 + i * 10, y0 + h - 10))
            p.setPen(QPen(QColor(esq), 8))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(r.adjusted(4, 4, -4, -4))
            if e in ("vidro", "escuro", "cortina"):
                p.drawLine(QPointF(x0 + w / 2, y0 + 4), QPointF(x0 + w / 2, y0 + h - 4))
            if rng.random() < 0.18:                                          # ar-condicionado velho
                ac = QRectF(x0 + w - 70, y0 + h + 14, 64, 44)
                p.setPen(QPen(QColor(70, 66, 58), 2))
                p.setBrush(QColor(150, 144, 130))
                p.drawRect(ac)
                p.setPen(QPen(QColor(90, 60, 30, 180), 3))
                p.drawLine(QPointF(ac.left() + 8, ac.bottom()), QPointF(ac.left() + 8, ac.bottom() + 40))
    for _ in range(5):                                                        # rachaduras
        x, y = rng.uniform(0, lado), rng.uniform(0, lado)
        a = rng.uniform(1.2, 1.9)
        p.setPen(QPen(QColor(40, 36, 30, 190), 1.8))
        for _k in range(14):
            a += rng.uniform(-0.5, 0.5)
            nx, ny = x + math.cos(a) * 12, y + math.sin(a) * 12
            p.drawLine(QPointF(x, y), QPointF(nx, ny))
            x, y = nx, ny
    p.end()
    return img


# lojas do térreo: (nome, cor da placa, cor da porta de enrolar) — nomes genéricos, inventados
_LOJAS = [("MERCADO", "#2a5a8a", "#8a8a84"), ("FARMÁCIA", "#2a7a4a", "#9a948a"), ("PADARIA", "#8a3a2a", "#7a7a74"),
          ("FERRAGENS", "#c8a030", "#86827a"), ("LANCHONETE", "#a03a6a", "#8e8a80"), ("ÓTICA", "#3a3a7a", "#7e7c76")]


def _pa_loja(var, W=1024, H=336):
    """Térreo de loja abandonada (1400 x 460 cm): placa desbotada, porta de enrolar enferrujada meio aberta e
    pichada, porta de vidro tapada, vitrine quebrada."""
    nome, placa, porta = _LOJAS[var % len(_LOJAS)]
    rng = _rng("pa-loja", var)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    n = _ruido(H, W, 20, rng) * 0.6 + _ruido(H, W, 2, rng) * 0.4
    cor = _c("#b8b0a0") * (0.78 + 0.25 * n)[..., None]
    cor[((xs % 24) < 2) | ((ys % 24) < 2)] *= 0.75                          # pastilhas
    cor = _misturar(cor, _c("#4a4230"), _suave((ys / H - 0.6) * 3) * 0.5)
    img = _rgb_img(np.clip(cor, 0, 1))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # placa
    pl = QRectF(10, 6, W - 20, 60)
    cp = QColor(placa)
    cp = QColor((cp.red() + 150) // 2, (cp.green() + 150) // 2, (cp.blue() + 150) // 2)
    p.fillRect(pl, cp)
    f = QFont("Arial Black", 1)
    f.setPixelSize(42)
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 6)
    p.setFont(f)
    p.setPen(QColor(236, 232, 220, 215))
    p.drawText(pl, Qt.AlignmentFlag.AlignCenter, nome)
    p.setPen(Qt.PenStyle.NoPen)
    for _ in range(14):                                                       # tinta descascada da placa
        p.setBrush(QColor(cp.red(), cp.green(), cp.blue(), int(rng.uniform(120, 230))))
        p.drawEllipse(QPointF(rng.uniform(pl.left(), pl.right()), rng.uniform(pl.top(), pl.bottom())),
                      rng.uniform(6, 22), rng.uniform(4, 12))
    p.setPen(QPen(QColor(40, 36, 30), 3))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRect(pl)
    # porta de enrolar
    pe = QRectF(30, 78, 520, 246)
    abre = rng.uniform(0.15, 0.4)
    p.fillRect(QRectF(pe.left(), pe.bottom() - pe.height() * abre, pe.width(), pe.height() * abre), QColor(10, 10, 10))
    fecha = QRectF(pe.left(), pe.top(), pe.width(), pe.height() * (1 - abre))
    p.fillRect(fecha, QColor(porta))
    yy = fecha.top()
    while yy < fecha.bottom():
        p.setPen(QPen(QColor(40, 40, 38, 160), 2))
        p.drawLine(QPointF(fecha.left(), yy), QPointF(fecha.right(), yy))
        p.setPen(QPen(QColor(220, 220, 210, 70), 2))
        p.drawLine(QPointF(fecha.left(), yy + 3), QPointF(fecha.right(), yy + 3))
        yy += 9
    p.setPen(Qt.PenStyle.NoPen)
    for _ in range(40):                                                       # ferrugem
        p.setBrush(QColor(110, 56, 24, int(rng.uniform(60, 170))))
        p.drawEllipse(QPointF(rng.uniform(fecha.left(), fecha.right()), rng.uniform(fecha.top(), fecha.bottom())),
                      rng.uniform(4, 26), rng.uniform(3, 12))
    for _ in range(3):                                                        # pichações (rabiscos)
        cor_t = QColor(*[(30, 30, 30), (200, 40, 40), (40, 90, 200), (230, 230, 230)][rng.integers(0, 4)])
        p.setPen(QPen(cor_t, rng.uniform(5, 9), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        x, y = rng.uniform(fecha.left() + 40, fecha.right() - 160), rng.uniform(fecha.top() + 30, fecha.bottom() - 30)
        risco = QPainterPath(QPointF(x, y))
        for _k in range(5):
            risco.cubicTo(x + rng.uniform(0, 30), y - rng.uniform(10, 40), x + rng.uniform(20, 50),
                          y + rng.uniform(10, 40), x + rng.uniform(25, 40), y)
            x += rng.uniform(25, 40)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(risco)
    # porta de vidro tapada
    pv = QRectF(580, 80, 170, 244)
    _vidro(p, pv, escuro=True)
    p.setPen(QPen(QColor(150, 150, 145), 7))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRect(pv)
    for ang in (-34, 34):
        p.save()
        p.translate(pv.center())
        p.rotate(ang)
        p.fillRect(QRectF(-150, -14, 300, 28), QColor(132, 104, 70))
        p.restore()
    # vitrine quebrada
    vt = QRectF(780, 80, 224, 244)
    g = QLinearGradient(vt.topLeft(), vt.bottomLeft())
    g.setColorAt(0, QColor(34, 34, 34))
    g.setColorAt(1, QColor(10, 10, 10))
    p.fillRect(vt, QBrush(g))
    p.setPen(QPen(QColor(56, 54, 50), 4))
    for yy in (150, 210, 270):
        p.drawLine(QPointF(vt.left() + 10, yy), QPointF(vt.right() - 10, yy))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(140, 150, 152, 190))
    p.drawPolygon(QPolygonF([vt.topLeft(), vt.topLeft() + QPointF(90, 0), vt.topLeft() + QPointF(20, 70)]))
    p.drawPolygon(QPolygonF([vt.bottomRight(), vt.bottomRight() - QPointF(120, 0), vt.bottomRight() - QPointF(10, 90)]))
    p.setPen(QPen(QColor(150, 150, 145), 7))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRect(vt)
    p.fillRect(QRectF(0, H - 12, W, 12), QColor(58, 56, 52))
    p.end()
    return img
