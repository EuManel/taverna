"""
🔮 Cenários do tema Mágico (v0.57, referências do Manel). Sorteia um cada vez que o programa abre (50/50):

  CÍRCULO — plataforma de pedra rachada flutuando no espaço roxo, com um CÍRCULO MÁGICO enorme no meio
            (pentagrama, runas, lua, sol, símbolos dos elementos) — o menu fica dentro dele. Cristais,
            cristal flutuando com anel de runas, poções, alambique soltando fumaça roxa, pilão com pó brilhando.
  TORRE   — céu roxo com lua, galáxia e mar de nuvens com pôr do sol; TORRE DE MAGO numa ilha flutuante com
            janelas acesas, estrela no topo e ANÉIS DE RUNAS girando; ilhotas com cristais flutuando.

Aqui ficam as texturas (gravadas em arquivo, ver `estilizado.caminho_textura_3d`).
"""

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainterPath, QPen, QPolygonF

from .estilizado import _c, _caixa_borrar, _rgb_img, _rng, _ruido, _suave
from .terror_cenas import _guardado, _pintar, _pixelar, _rgba

ROXO = QColor(200, 110, 255)


def textura(nome):
    if nome.startswith("runa_") and nome[5:].isdigit():          # runa solta (acende no hover do menu)
        return _guardado(("magico", nome), lambda: _runa_solta(int(nome[5:])))
    f = {"pedra_magica": _pedra_magica, "circulo_magico": _circulo, "circulo_runas": _circulo_runas,
         "runas_anel": _runas_anel, "ceu_magico": _ceu_magico, "espaco": _espaco, "nuvem_magica": _nuvem_magica,
         "rachaduras": _rachaduras, "pedra_torre": _pedra_torre, "lua_magica": _lua_magica,
         "grama_magica": _grama_magica, "rocha_magica": _rocha_magica,
         "pedra_rachada": lambda: _fendas()[0], "fendas_luz": lambda: _fendas()[1],
         "fendas_normal": lambda: _fendas()[2], "brilho_disco": _brilho_disco}.get(nome)
    return _guardado(("magico", nome), f) if f else None


def _runa_solta(k, lado=128):
    def d(p, W, H):
        def tudo():
            _runa(p, k, W / 2, H / 2, W * 0.62)
        _brilhar(p, tudo, ((16, 40), (8, 110), (3.5, 255)), QColor(255, 255, 255))
    return _pintar(lado, lado, d)


def _brilho_disco(lado=256):
    """Disco escuro e liso no miolo do círculo (apaga o pentagrama atrás das letras), borda suave."""
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
    r = np.sqrt((xs - lado / 2) ** 2 + (ys - lado / 2) ** 2) / (lado / 2)
    a = _suave((1 - r) * 5) * 0.93
    cor = np.ones((lado, lado, 3), np.float32) * _c("#0a0614")
    return _rgba(cor, a)


def _fendas(lado=1024):
    """FENDAS de verdade na pedra (v0.58): sulco escuro com bordas (cor), a luz só no fundo da fenda (emissão) e
    o relevo afundado (normal). As 3 texturas batem certinho (mesmo desenho)."""
    if "fendas" in _CACHE_FENDAS:
        return _CACHE_FENDAS["fendas"]
    from PyQt6.QtGui import QImage, QPainter
    from .estilizado import _normal_de
    rng = _rng("fendas")
    caminhos = []

    def uma(x, y, ang, comp, esp):
        pts = [QPointF(x, y)]
        for _ in range(int(comp / 12)):
            ang += rng.uniform(-0.55, 0.55)
            x += math.cos(ang) * 12
            y += math.sin(ang) * 12
            pts.append(QPointF(x, y))
            if rng.random() < 0.07 and esp > 1.4:
                uma(x, y, ang + rng.choice([-0.9, 0.9]), comp * 0.45, esp * 0.6)
        caminhos.append((pts, esp))
    for _ in range(10):
        uma(rng.uniform(0, lado), rng.uniform(0, lado), rng.uniform(0, 6.28), rng.uniform(180, 460), rng.uniform(1.6, 3.4))

    def mascara(fator):
        img = QImage(lado, lado, QImage.Format.Format_Grayscale8)
        img.fill(0)
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for pts, esp in caminhos:
            p.setPen(QPen(QColor(255, 255, 255), esp * fator, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                          Qt.PenJoinStyle.RoundJoin))
            p.drawPolyline(QPolygonF(pts))
        p.end()
        b = img.bits()
        b.setsize(img.sizeInBytes())
        arr = np.frombuffer(b, np.uint8).reshape(lado, img.bytesPerLine())[:, :lado].astype(np.float32) / 255
        return arr.copy()
    miolo = _caixa_borrar(mascara(1.0), 1)
    sulco = _caixa_borrar(mascara(3.2), 2)
    borda = _caixa_borrar(mascara(6.0), 4)
    # cor: a pedra (4 lajes) escurecendo pra dentro da fenda
    base = textura("pedra_magica")
    pedra = np.zeros((lado, lado, 3), np.float32)
    pb = base.convertToFormat(QImage.Format.Format_RGB888)
    bb = pb.bits()
    bb.setsize(pb.sizeInBytes())
    tile = np.frombuffer(bb, np.uint8).reshape(pb.height(), pb.bytesPerLine())[:, :pb.width() * 3]
    tile = tile.reshape(pb.height(), pb.width(), 3).astype(np.float32) / 255
    reps = (lado // tile.shape[0] + 1, lado // tile.shape[1] + 1, 1)
    pedra[:] = np.tile(tile, reps)[:lado, :lado]
    cor = pedra * (1 - 0.55 * borda[..., None]) * (1 - 0.8 * sulco[..., None])
    cor += _c("#6a2aa0")[None, None] * (miolo * 0.5)[..., None]          # o fundo da fenda já tem cor de luz
    luz = _c("#d080ff")[None, None] * np.clip(miolo * 1.4, 0, 1)[..., None]
    altura = -(sulco * 1.0 + borda * 0.35)
    res = (_rgb_img(cor), _rgb_img(luz), _normal_de(altura, 6.0))
    _CACHE_FENDAS["fendas"] = res
    return res


_CACHE_FENDAS = {}


# ---------------------------------------------------------------------- runas e símbolos (desenhados com traços)
# Runas (alfabeto futhark antigo, domínio público) como linhas num quadradinho 0..1
RUNAS = [
    [((0.3, 0), (0.3, 1)), ((0.3, 0.1), (0.75, 0.3)), ((0.3, 0.35), (0.75, 0.55))],          # fehu
    [((0.3, 0), (0.3, 1)), ((0.3, 0), (0.75, 0.4)), ((0.75, 0.4), (0.75, 1))],               # uruz
    [((0.35, 0), (0.35, 1)), ((0.35, 0.25), (0.75, 0.5)), ((0.75, 0.5), (0.35, 0.75))],      # thurisaz
    [((0.3, 0), (0.3, 1)), ((0.3, 0), (0.7, 0.25)), ((0.3, 0.3), (0.7, 0.55))],              # ansuz
    [((0.3, 0), (0.3, 1)), ((0.3, 0), (0.7, 0.25)), ((0.7, 0.25), (0.3, 0.5)), ((0.3, 0.5), (0.75, 1))],   # raidho
    [((0.7, 0), (0.3, 0.5)), ((0.3, 0.5), (0.7, 1))],                                        # kenaz
    [((0.25, 0), (0.75, 1)), ((0.75, 0), (0.25, 1))],                                        # gebo
    [((0.25, 0), (0.25, 1)), ((0.75, 0), (0.75, 1)), ((0.25, 0.3), (0.75, 0.7))],            # hagalaz
    [((0.5, 0), (0.5, 1)), ((0.3, 0.35), (0.7, 0.55))],                                      # naudhiz
    [((0.5, 0), (0.5, 1))],                                                                  # isa
    [((0.5, 0), (0.5, 1)), ((0.2, 0.3), (0.5, 0)), ((0.8, 0.3), (0.5, 0))],                  # tiwaz (seta)
    [((0.5, 0), (0.5, 1)), ((0.5, 0), (0.2, 0.35)), ((0.5, 0), (0.8, 0.35))],                # algiz invertido
    [((0.3, 0), (0.3, 1)), ((0.3, 0), (0.7, 0.2)), ((0.7, 0.2), (0.3, 0.45)), ((0.3, 0.45), (0.7, 0.7)),
     ((0.7, 0.7), (0.3, 1))],                                                                # berkanan
    [((0.25, 1), (0.25, 0)), ((0.25, 0), (0.5, 0.4)), ((0.5, 0.4), (0.75, 0)), ((0.75, 0), (0.75, 1))],   # ehwaz
    [((0.3, 0), (0.3, 1)), ((0.3, 0), (0.7, 0.3)), ((0.7, 0.3), (0.3, 0.55))],               # wunjo
    [((0.2, 0.5), (0.5, 0)), ((0.5, 0), (0.8, 0.5)), ((0.8, 0.5), (0.5, 1)), ((0.5, 1), (0.2, 0.5))],     # ingwaz
]


def _runa(p, k, x, y, tam, ang=0.0):
    p.save()
    p.translate(x, y)
    p.rotate(math.degrees(ang))
    for (a, b) in RUNAS[k % len(RUNAS)]:
        p.drawLine(QPointF((a[0] - 0.5) * tam, (a[1] - 0.5) * tam), QPointF((b[0] - 0.5) * tam, (b[1] - 0.5) * tam))
    p.restore()


def _simbolo(p, tipo, x, y, r):
    """Lua, sol e os triângulos dos elementos (fogo, água, ar, terra), mercúrio — traços simples."""
    p.save()
    p.translate(x, y)
    p.setBrush(Qt.BrushStyle.NoBrush)
    if tipo == "lua":
        cam = QPainterPath()
        cam.addEllipse(QPointF(0, 0), r, r)
        corte = QPainterPath()
        corte.addEllipse(QPointF(r * 0.45, -r * 0.2), r * 0.9, r * 0.9)
        p.drawPath(cam.subtracted(corte))
    elif tipo == "sol":
        p.drawEllipse(QPointF(0, 0), r * 0.45, r * 0.45)
        for k in range(12):
            a = k * math.pi / 6
            p.drawLine(QPointF(math.cos(a) * r * 0.6, math.sin(a) * r * 0.6), QPointF(math.cos(a) * r, math.sin(a) * r))
    elif tipo in ("fogo", "ar", "agua", "terra"):
        s = -1 if tipo in ("agua", "terra") else 1
        tri = QPolygonF([QPointF(0, -r * s), QPointF(r * 0.9, r * 0.6 * s), QPointF(-r * 0.9, r * 0.6 * s)])
        p.drawPolygon(tri)
        if tipo in ("ar", "terra"):
            p.drawLine(QPointF(-r * 0.75, r * 0.1 * s), QPointF(r * 0.75, r * 0.1 * s))
    elif tipo == "mercurio":
        p.drawEllipse(QPointF(0, -r * 0.1), r * 0.35, r * 0.35)
        p.drawArc(QRectF(-r * 0.4, -r * 0.95, r * 0.8, r * 0.5), 180 * 16, 180 * 16)
        p.drawLine(QPointF(0, r * 0.25), QPointF(0, r))
        p.drawLine(QPointF(-r * 0.3, r * 0.65), QPointF(r * 0.3, r * 0.65))
    elif tipo == "tres":
        for k in range(3):
            a = -math.pi / 2 + k * 2 * math.pi / 3
            p.drawEllipse(QPointF(math.cos(a) * r * 0.5, math.sin(a) * r * 0.5), r * 0.32, r * 0.32)
    p.restore()


def _brilhar(p, desenho, larguras=((14, 30), (7, 70), (2.6, 255)), cor=ROXO):
    """Desenha a mesma coisa várias vezes, larga e fraca → fina e forte = traço brilhando."""
    for larg, alfa in larguras:
        c = QColor(cor)
        c.setAlpha(alfa)
        p.setPen(QPen(c, larg, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        desenho()


def _circulo(lado=1536):
    """O círculo de dentro: pentagrama, anéis e os 5 símbolos nas pontas (gira devagar num sentido)."""
    def d(p, W, H):
        cx, cy = W / 2, H / 2
        R = W * 0.47

        def tudo():
            p.setBrush(Qt.BrushStyle.NoBrush)
            for f in (1.0, 0.97, 0.78, 0.75):
                p.drawEllipse(QPointF(cx, cy), R * f, R * f)
            pts = [QPointF(cx + math.cos(-math.pi / 2 + k * 2 * math.pi / 5) * R * 0.75,
                           cy + math.sin(-math.pi / 2 + k * 2 * math.pi / 5) * R * 0.75) for k in range(5)]
            estrela = QPolygonF([pts[(k * 2) % 5] for k in range(5)])
            p.drawPolygon(estrela)
            for k, tipo in enumerate(("lua", "agua", "tres", "terra", "fogo")):
                a = -math.pi / 2 + k * 2 * math.pi / 5
                x, y = cx + math.cos(a) * R * 0.875, cy + math.sin(a) * R * 0.875
                p.drawEllipse(QPointF(x, y), R * 0.085, R * 0.085)
                _simbolo(p, tipo, x, y, R * 0.055)
            for k in range(10):                                # pontinhos entre os símbolos
                a = -math.pi / 2 + (k + 0.5) * 2 * math.pi / 10
                p.drawEllipse(QPointF(cx + math.cos(a) * R * 0.875, cy + math.sin(a) * R * 0.875), R * 0.012, R * 0.012)
        _brilhar(p, tudo, ((22, 22), (10, 60), (3.5, 255)))
    return _pintar(lado, lado, d)


def _circulo_runas(lado=1536):
    """O anel de fora: runas, sol, mercúrio e tracinhos (gira devagar no sentido contrário)."""
    rng = _rng("anel-runas")

    def d(p, W, H):
        cx, cy = W / 2, H / 2
        R = W * 0.49

        def tudo():
            p.setBrush(Qt.BrushStyle.NoBrush)
            for f in (1.0, 0.985, 0.86, 0.845):
                p.drawEllipse(QPointF(cx, cy), R * f, R * f)
            n = 28
            for k in range(n):
                a = k * 2 * math.pi / n
                x, y = cx + math.cos(a) * R * 0.922, cy + math.sin(a) * R * 0.922
                if k % 7 == 0:
                    _simbolo(p, ("sol", "mercurio", "ar", "lua")[(k // 7) % 4], x, y, R * 0.045)
                else:
                    _runa(p, int(rng.integers(0, len(RUNAS))), x, y, R * 0.06, a + math.pi / 2)
            for k in range(120):                               # régua fininha por fora
                a = k * 2 * math.pi / 120
                f = 1.0 if k % 5 else 1.03
                p.drawLine(QPointF(cx + math.cos(a) * R * 0.985, cy + math.sin(a) * R * 0.985),
                           QPointF(cx + math.cos(a) * R * 0.985 * f + math.cos(a) * 6, cy + math.sin(a) * R * 0.985 * f + math.sin(a) * 6))
        _brilhar(p, tudo, ((18, 22), (8, 60), (3, 255)))
    return _pintar(lado, lado, d)


def _runas_anel(W=2048, H=128):
    """Faixa de runas que dá a volta num anel (cristal flutuando, anéis da torre)."""
    rng = _rng("runas-faixa")

    def d(p, W, H):
        def tudo():
            p.drawLine(QPointF(0, H * 0.12), QPointF(W, H * 0.12))
            p.drawLine(QPointF(0, H * 0.88), QPointF(W, H * 0.88))
            n = 26
            for k in range(n):
                _runa(p, int(rng.integers(0, len(RUNAS))), (k + 0.5) * W / n, H / 2, H * 0.52)
        _brilhar(p, tudo, ((12, 30), (6, 80), (2.5, 255)))
    return _pintar(W, H, d)


# ---------------------------------------------------------------------- pedras e céus
def _pedra_magica(lado=512):
    """Laje escura arroxeada com rachaduras (as rachaduras brilham por outra textura)."""
    rng = _rng("pedra-magica")
    n = _ruido(lado, lado, 10, rng) * 0.55 + _ruido(lado, lado, 3, rng) * 0.45
    cor = _c("#3a3442") * (0.55 + 0.6 * n[..., None])
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
    lajes = np.minimum(np.minimum(xs % 128, 128 - xs % 128), np.minimum(ys % 128, 128 - ys % 128))
    cor *= (0.45 + 0.55 * _suave(lajes / 4))[..., None]
    return _rgb_img(cor)


def _rachaduras(lado=1024):
    """Rachaduras que BRILHAM (roxo) — fundo transparente, vai como emissão por cima da pedra."""
    rng = _rng("rachaduras")

    def d(p, W, H):
        def uma(x, y, ang, comp, esp):
            pts = [QPointF(x, y)]
            for _ in range(int(comp / 14)):
                ang += rng.uniform(-0.6, 0.6)
                x += math.cos(ang) * 14
                y += math.sin(ang) * 14
                pts.append(QPointF(x, y))
                if rng.random() < 0.08 and esp > 1.2:
                    uma(x, y, ang + rng.choice([-0.9, 0.9]), comp * 0.4, esp * 0.6)
            for larg, alfa in ((esp * 5, 40), (esp * 2.2, 110), (esp, 255)):
                p.setPen(QPen(QColor(210, 120, 255, alfa), larg, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawPolyline(QPolygonF(pts))
        for _ in range(9):
            uma(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0, 6.28), rng.uniform(150, 420), rng.uniform(1.5, 3.2))
    return _pintar(lado, lado, d)


def _pedra_torre(lado=256):
    rng = _rng("pedra-torre")
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
    lin = np.floor(ys / 22)
    lu = (xs + (lin % 2) * 26) % 52
    junta = np.minimum(np.minimum(lu, 52 - lu), np.minimum(ys % 22, 22 - ys % 22))
    n = _ruido(lado, lado, 5, rng)
    cor = _c("#8e8a86") * (0.7 + 0.4 * n[..., None]) * (0.5 + 0.5 * _suave(junta / 2))[..., None]
    musgo = _suave((_ruido(lado, lado, 12, rng) - 0.7) * 6)
    cor = cor * (1 - musgo[..., None] * 0.4) + _c("#4a5a2e") * musgo[..., None] * 0.4
    return _rgb_img(cor)


def _rocha_magica(lado=256):
    rng = _rng("rocha-magica")
    n = _ruido(lado, lado, 9, rng) * 0.6 + _ruido(lado, lado, 2, rng) * 0.4
    cor = _c("#6a6070") * (0.55 + 0.6 * n[..., None])
    musgo = _suave((_ruido(lado, lado, 14, rng) - 0.68) * 6)
    cor = cor * (1 - musgo[..., None] * 0.45) + _c("#4a5a2e") * musgo[..., None] * 0.45
    return _rgb_img(cor)


def _grama_magica(lado=128):
    rng = _rng("grama-magica")
    n = _ruido(lado, lado, 4, rng)
    return _rgb_img(_c("#3e4a2a") * (0.6 + 0.6 * n[..., None]))


def _estrelas(cor, rng, W, H, n=900):
    ys = rng.integers(0, H, n)
    xs = rng.integers(0, W, n)
    b = rng.random(n) ** 3
    for y, x, v in zip(ys, xs, b):
        cor[y, x] = np.maximum(cor[y, x], 0.5 + 0.5 * v)
        if v > 0.85:
            for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                yy, xx = min(H - 1, max(0, y + dy)), min(W - 1, max(0, x + dx))
                cor[yy, xx] = np.maximum(cor[yy, xx], 0.45 * v)
    return cor


def _espaco(W=2048, H=1024):
    """Espaço roxo com nebulosa e estrelas (fundo do círculo mágico)."""
    rng = _rng("espaco")
    n1 = _ruido(H // 2, W // 2, 40, rng)
    n2 = _ruido(H // 2, W // 2, 12, rng)
    neb = _suave((n1 * 0.7 + n2 * 0.3 - 0.45) * 2.5)
    cor = _c("#07041a") * (1 - neb[..., None]) + (_c("#3a1468") * (1 - n2[..., None]) + _c("#1a2a8a") * n2[..., None]) * neb[..., None]
    cor = np.repeat(np.repeat(cor, 2, axis=0), 2, axis=1)
    cor = _estrelas(cor, rng, W, H, 1400)
    return _rgb_img(cor)


def _ceu_magico(W=2048, H=1152):
    """Céu da torre: roxo de noite em cima, REDEMOINHO de galáxia, pôr do sol laranja lá embaixo no horizonte."""
    rng = _rng("ceu-magico")
    h2, w2 = H // 2, W // 2
    ys, xs = np.mgrid[0:h2, 0:w2].astype(np.float32)
    v = ys / h2
    cor = _c("#2a1660")[None, None] * (1 - v[..., None]) + _c("#5a3290")[None, None] * v[..., None]
    poente = np.exp(-((v - 0.86) / 0.06) ** 2)
    cor += (_c("#e86a3a") * 0.9)[None, None] * poente[..., None] + (_c("#a03a7a") * 0.6)[None, None] * np.exp(-((v - 0.78) / 0.08) ** 2)[..., None]
    # redemoinho (em cima, à direita)
    cx, cy = w2 * 0.72, h2 * 0.18
    dx, dy = (xs - cx) / w2, (ys - cy) / h2 * 1.6
    r = np.sqrt(dx ** 2 + dy ** 2)
    a = np.arctan2(dy, dx)
    braco = (np.sin(a * 2 - r * 22) * 0.5 + 0.5) ** 3 * np.exp(-r * 3.2)
    braco *= 0.6 + 0.6 * _ruido(h2, w2, 6, rng)
    cor += _c("#c060f0")[None, None] * braco[..., None] * 1.1
    cor = np.repeat(np.repeat(cor, 2, axis=0), 2, axis=1)
    cor = _estrelas(cor, rng, W, int(H * 0.7), 900)
    return _pixelar(_rgb_img(cor), 2)


def _nuvem_magica(W=1024, H=320):
    rng = _rng("nuvem-magica")
    n = _ruido(H, W, 24, rng) * 0.65 + _ruido(H, W, 7, rng) * 0.35
    m = 120
    t = np.linspace(0, 1, m, dtype=np.float32)[None, :]
    n[:, :m] = n[:, :m] * t + n[:, -m:] * (1 - t)
    ys = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a = _suave((n - 0.38) * 3) * _suave((1 - np.abs(ys * 2 - 1)) * 2.2)
    topo = _suave((n - 0.55) * 4) * (1 - ys)                     # o alto das nuvens pega luz
    cor = _c("#7a5aaa") * (0.75 + 0.4 * n[..., None]) + _c("#e0a8f0")[None, None] * topo[..., None] * 0.55
    return _pixelar(_rgba(cor, a), 3)


def _lua_magica():
    from .estilizado import lua
    img = lua(512, 0.5, False)
    # tinge de lilás
    from PyQt6.QtGui import QPainter
    p = QPainter(img)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
    p.fillRect(img.rect(), QColor(190, 150, 255, 120))
    p.end()
    return img
