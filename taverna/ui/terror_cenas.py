"""
👻 Cenários do tema Terror (v0.55, referências do Manel). Cada vez que o programa abre, sorteia um:

  TV    — sala abandonada em 3D (`qml/TerrorTV.qml`): TV velha enferrujada com o MENU DENTRO DA TELA (chiado
          preto e branco que pisca e, de vez em quando, mostra um ROSTO), luminária que falha, caneca rachada,
          fotos velhas, chaves, lanterna apagada e um pano manchado de sangue.
  FAROL — tempestade no mar (`qml/TerrorFarol.qml`): penhasco com o farol girando, ondas batendo nas pedras,
          chuva, barco balançando e RAIOS — e às vezes, no clarão, a silhueta do Cthulhu lá no fundo
          (Lovecraft, domínio público).

Aqui ficam os desenhos: texturas da cena 3D (gravadas em arquivo, ver `estilizado.caminho_textura_3d`) e as
imagens 2D do farol (pelo provedor `image://taverna/farol/...`).
"""

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QBrush, QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF,
                         QRadialGradient)

from .estilizado import _c, _caixa_borrar, _qimg, _rgb_img, _rng, _ruido, _suave

_CACHE = {}


def _rgba(rgb, a):
    """rgb 0..1 + alfa 0..1 → QImage (pré-multiplicada)."""
    h, w = a.shape
    out = np.empty((h, w, 4), np.uint8)
    a = np.clip(a, 0, 1)
    out[..., :3] = (np.clip(rgb, 0, 1) * a[..., None] * 255).astype(np.uint8)
    out[..., 3] = (a * 255).astype(np.uint8)
    return _qimg(out)


def _pixelar(img, fator=3):
    """Dá o jeitão "pixel pintado" das referências: reduz e amplia sem suavizar."""
    if fator <= 1:
        return img
    w, h = img.width(), img.height()
    p = img.scaled(max(1, w // fator), max(1, h // fator), Qt.AspectRatioMode.IgnoreAspectRatio,
                   Qt.TransformationMode.SmoothTransformation)
    return p.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)


def _pintar(W, H, desenhar, fundo=None):
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(QColor(fundo) if fundo else Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    desenhar(p, W, H)
    p.end()
    return img


def _guardado(chave, fazer):
    if chave not in _CACHE:
        _CACHE[chave] = fazer()
    return _CACHE[chave]


# ====================================================================== texturas da cena 3D (TV)
def textura(nome):
    """Textura da sala da TV pelo nome (None se não for daqui)."""
    f = {"ferrugem": _ferrugem, "parede_verde": _parede_verde, "mesa_suja": _mesa_suja, "foto_casa": _foto_casa,
         "foto_arvore": lambda: _foto_casa(2), "pano_sangue": _pano_sangue, "ceramica": _ceramica,
         "janela_noite": _janela_noite, "latao_velho": _latao_velho, "papel_velho": _papel_velho,
         # farol 3D (v0.56)
         "ceu_farol": lambda: _ceu(1600, 900), "nuvem_farol0": lambda: _nuvem(0), "nuvem_farol1": lambda: _nuvem(1),
         "cthulhu": _cthulhu, "raio0": lambda: _raio(0), "raio1": lambda: _raio(1), "raio2": lambda: _raio(2),
         "gota": _gota, "pedra_rocha": _pedra_rocha, "pedra_farol": _pedra_farol, "feixe_grad": _feixe_grad,
         "madeira_barco": _madeira_barco, "grama": _grama}.get(nome)
    return _guardado(("tex", nome), f) if f else None


def _ferrugem(lado=512):
    rng = _rng("ferrugem")
    base = _c("#4c4640")
    n1, n2, n3 = _ruido(lado, lado, 40, rng), _ruido(lado, lado, 10, rng), _ruido(lado, lado, 3, rng)
    cor = base[None, None, :] * (0.75 + 0.4 * n1[..., None]) * (0.9 + 0.2 * n3[..., None])
    ferr = _suave((n1 * 0.55 + n2 * 0.45 - 0.5) * 5)            # manchas de ferrugem
    ponto = _suave((n3 - 0.72) * 8) * (n2 > 0.4)                 # pintinhas
    marrom = _c("#6e3518") * (0.7 + 0.6 * n3[..., None])
    laranja = _c("#9a4a1c")
    cor = cor * (1 - ferr[..., None]) + marrom * ferr[..., None]
    cor = cor * (1 - ponto[..., None] * 0.7) + laranja * ponto[..., None] * 0.7
    escorrido = _caixa_borrar(rng.random((lado, lado)).astype(np.float32), 1)
    escorrido = _caixa_borrar(escorrido.T, 14).T                 # escorridos de sujeira, de cima pra baixo
    escorrido = (escorrido - escorrido.min()) / max(1e-6, float(np.ptp(escorrido)))
    cor *= (0.8 + 0.3 * escorrido[..., None])
    return _rgb_img(cor)


def _parede_verde(lado=1024):
    rng = _rng("parede-verde")
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
    larg = lado / 7
    tab = np.floor(xs / larg)
    lu = xs - tab * larg
    fibra = _caixa_borrar(rng.random((lado, lado)).astype(np.float32), 1)
    fibra = _caixa_borrar(fibra.T, 10).T
    fibra = (fibra - fibra.min()) / max(1e-6, float(np.ptp(fibra)))
    tons = _rng("tons-parede").random(16).astype(np.float32)
    mancha = _ruido(lado, lado, 50, rng)
    cor = _c("#22301e") * (0.7 + 0.5 * tons[tab.astype(int) % 16])[..., None] * (0.75 + 0.4 * fibra[..., None])
    cor = cor * (0.7 + 0.5 * mancha[..., None])
    cor *= (0.3 + 0.7 * _suave(np.minimum(lu, larg - lu) / 5))[..., None]
    mofo = _suave((_ruido(lado, lado, 18, rng) - 0.62) * 6)
    cor = cor * (1 - mofo[..., None] * 0.5) + _c("#3a4a26") * mofo[..., None] * 0.5
    return _rgb_img(cor)


def _mesa_suja(lado=1024):
    rng = _rng("mesa-suja")
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
    larg = lado / 5
    tab = np.floor(ys / larg)
    lu = ys - tab * larg
    fibra = _caixa_borrar(rng.random((lado, lado)).astype(np.float32), 1)
    fibra = _caixa_borrar(fibra, 12)
    fibra = (fibra - fibra.min()) / max(1e-6, float(np.ptp(fibra)))
    tons = _rng("tons-mesa-suja").random(16).astype(np.float32)
    cor = _c("#3a3424") * (0.7 + 0.45 * tons[tab.astype(int) % 16])[..., None] * (0.75 + 0.4 * fibra[..., None])
    cor *= (0.35 + 0.65 * _suave(np.minimum(lu, larg - lu) / 4))[..., None]
    sujo = _ruido(lado, lado, 40, rng)
    cor *= (0.65 + 0.5 * sujo[..., None])
    musgo = _suave((_ruido(lado, lado, 12, rng) - 0.65) * 6)
    cor = cor * (1 - musgo[..., None] * 0.4) + _c("#34401e") * musgo[..., None] * 0.4
    return _rgb_img(cor)


def _foto_casa(variante=1):
    rng = _rng("foto", variante)

    def d(p, W, H):
        p.fillRect(0, 0, W, H, QColor("#d8ceb0"))                  # borda branca amarelada
        m = W * 0.07
        dentro = QRectF(m, m, W - 2 * m, H - 2 * m - W * 0.08)
        g = QLinearGradient(0, dentro.top(), 0, dentro.bottom())
        g.setColorAt(0, QColor("#8a8470"))
        g.setColorAt(0.7, QColor("#4a4636"))
        g.setColorAt(1, QColor("#2a2820"))
        p.fillRect(dentro, QBrush(g))
        p.save()
        p.setClipRect(dentro)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#1a1812"))
        chao = dentro.top() + dentro.height() * 0.78
        p.drawRect(QRectF(dentro.left(), chao, dentro.width(), dentro.height()))
        if variante == 1:                                           # casa assombrada
            cx = dentro.left() + dentro.width() * 0.58
            corpo = QRectF(cx - 90, chao - 120, 180, 120)
            p.drawRect(corpo)
            p.drawPolygon(QPolygonF([QPointF(cx - 105, chao - 118), QPointF(cx, chao - 190), QPointF(cx + 105, chao - 118)]))
            p.drawRect(QRectF(cx + 40, chao - 210, 26, 70))          # chaminé
            p.drawRect(QRectF(cx - 150, chao - 80, 70, 80))          # puxadinho
            p.setBrush(QColor("#6a6450"))
            for (jx, jy) in ((-60, -95), (20, -95), (-60, -50), (20, -50)):
                p.drawRect(QRectF(cx + jx, chao + jy, 22, 26))
            p.setBrush(QColor("#1a1812"))
        # árvore morta
        tx = dentro.left() + dentro.width() * (0.22 if variante == 1 else 0.5)
        p.setPen(QPen(QColor("#1a1812"), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))

        def galho(x, y, ang, comp, esp):
            if comp < 8:
                return
            x2, y2 = x + math.cos(ang) * comp, y - math.sin(ang) * comp
            p.setPen(QPen(QColor("#1a1812"), esp, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(x, y), QPointF(x2, y2))
            for _ in range(2):
                galho(x2, y2, ang + rng.uniform(-0.8, 0.8), comp * rng.uniform(0.55, 0.75), max(1, esp * 0.65))
        galho(tx, chao, math.pi / 2, 90 if variante == 1 else 120, 12)
        p.restore()
        # grão, manchas e amarelado
        for _ in range(1600):
            c = QColor(255, 255, 255, int(rng.uniform(5, 30))) if rng.random() < 0.5 else QColor(0, 0, 0, int(rng.uniform(5, 40)))
            p.setPen(QPen(c, 1))
            p.drawPoint(QPointF(rng.uniform(0, W), rng.uniform(0, H)))
        for _ in range(6):
            r = rng.uniform(10, 50)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(110, 80, 30, int(rng.uniform(20, 60))))
            p.drawEllipse(QPointF(rng.uniform(0, W), rng.uniform(0, H)), r, r * rng.uniform(0.5, 1))
        p.fillRect(0, 0, W, H, QColor(140, 110, 50, 40))
    return _pintar(512, 420, d)


def _pano_sangue(lado=512):
    rng = _rng("pano-sangue")
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
    trama = 0.85 + 0.15 * (np.sin(xs * 1.6) * np.sin(ys * 1.6))
    sujo = _ruido(lado, lado, 30, rng)
    cor = _c("#8a7e62") * trama[..., None] * (0.6 + 0.55 * sujo[..., None])
    sangue = np.zeros((lado, lado), np.float32)
    for _ in range(7):                                          # manchas de sangue (bordas irregulares)
        cx, cy, r = rng.uniform(60, lado - 60), rng.uniform(60, lado - 60), rng.uniform(25, 85)
        d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2) / r
        sangue = np.maximum(sangue, _suave((1.1 - d - _ruido(lado, lado, 8, _rng("sg", cx)) * 0.5) * 4))
    seco = _ruido(lado, lado, 6, rng)
    vermelho = _c("#5a0e0c") * (0.6 + 0.6 * seco[..., None])
    cor = cor * (1 - sangue[..., None] * 0.9) + vermelho * sangue[..., None] * 0.9
    return _rgb_img(cor)


def _ceramica():
    def d(p, W, H):
        p.fillRect(0, 0, W, H, QColor("#c8c0aa"))
        rng = _rng("ceramica")
        for _ in range(500):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(60, 50, 30, int(rng.uniform(6, 30))))
            r = rng.uniform(2, 16)
            p.drawEllipse(QPointF(rng.uniform(0, W), rng.uniform(0, H)), r, r)
        g = QLinearGradient(0, 0, 0, H)                             # encardido perto da boca e do fundo
        g.setColorAt(0, QColor(50, 40, 20, 110))
        g.setColorAt(0.2, QColor(0, 0, 0, 0))
        g.setColorAt(0.85, QColor(0, 0, 0, 0))
        g.setColorAt(1, QColor(50, 40, 20, 140))
        p.fillRect(0, 0, W, H, QBrush(g))
        caminho = QPainterPath(QPointF(W * 0.3, H * 0.98))           # a rachadura
        x, y = W * 0.3, H * 0.98
        while y > H * 0.25:
            x += rng.uniform(-14, 14)
            y -= rng.uniform(18, 36)
            caminho.lineTo(QPointF(x, y))
            if rng.random() < 0.3:
                ramo = QPainterPath(QPointF(x, y))
                ramo.lineTo(QPointF(x + rng.uniform(-40, 40), y - rng.uniform(10, 40)))
                p.setPen(QPen(QColor("#1a120a"), 2))
                p.drawPath(ramo)
        p.setPen(QPen(QColor("#140c06"), 4))
        p.drawPath(caminho)
    return _pintar(512, 512, d)


def _janela_noite():
    rng = _rng("janela")
    lado = 256
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32) / lado
    cor = _c("#1e3a34") * (1 - ys[..., None] * 0.6) + _c("#4a7a6a") * np.exp(-((xs - 0.7) ** 2 + (ys - 0.3) ** 2) * 8)[..., None] * 0.5
    img = _rgb_img(cor)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    def galho(x, y, ang, comp, esp):
        if comp < 5:
            return
        x2, y2 = x + math.cos(ang) * comp, y - math.sin(ang) * comp
        p.setPen(QPen(QColor("#0a120e"), esp, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(x, y), QPointF(x2, y2))
        for _ in range(2):
            galho(x2, y2, ang + rng.uniform(-0.7, 0.7), comp * rng.uniform(0.6, 0.75), max(1, esp * 0.6))
    galho(40, 256, 1.3, 90, 10)
    p.end()
    return img


def _latao_velho(lado=256):
    rng = _rng("latao")
    n = _ruido(lado, lado, 12, rng)
    cor = _c("#8a7444") * (0.6 + 0.6 * n[..., None])
    verde = _suave((_ruido(lado, lado, 6, rng) - 0.7) * 6)        # azinhavre
    cor = cor * (1 - verde[..., None] * 0.6) + _c("#4a6a4a") * verde[..., None] * 0.6
    return _rgb_img(cor)


def _papel_velho(lado=128):
    rng = _rng("papelzinho")
    n = _ruido(lado, lado, 10, rng)
    return _rgb_img(_c("#9a9478") * (0.65 + 0.45 * n[..., None]))


def _pedra_rocha(lado=256):
    rng = _rng("pedra-rocha")
    n = _ruido(lado, lado, 8, rng) * 0.6 + _ruido(lado, lado, 2, rng) * 0.4
    cor = _c("#33403a") * (0.6 + 0.7 * n[..., None])
    musgo = _suave((_ruido(lado, lado, 14, rng) - 0.62) * 5)
    cor = cor * (1 - musgo[..., None] * 0.5) + _c("#2e4a26") * musgo[..., None] * 0.5
    return _rgb_img(cor)


def _pedra_farol(lado=256):
    rng = _rng("pedra-farol")
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
    lin = np.floor(ys / 16)
    lu = (xs + (lin % 2) * 20) % 40
    junta = np.minimum(np.minimum(lu, 40 - lu), np.minimum(ys % 16, 16 - ys % 16))
    n = _ruido(lado, lado, 4, rng)
    cor = _c("#b4b4a6") * (0.75 + 0.35 * n[..., None]) * (0.55 + 0.45 * _suave(junta / 2))[..., None]
    sujo = _caixa_borrar(rng.random((lado, lado)).astype(np.float32), 1)
    sujo = _caixa_borrar(sujo.T, 12).T
    sujo = (sujo - sujo.min()) / max(1e-6, float(np.ptp(sujo)))
    return _rgb_img(cor * (0.75 + 0.3 * sujo[..., None]))


def _feixe_grad():
    """Opacidade do feixe do farol ao longo do comprimento (forte perto da lâmpada, some longe)."""
    # (a linha de cima da imagem = ponta longe do cone; a de baixo = perto da lâmpada)
    perto = np.linspace(0, 1, 256, dtype=np.float32)          # 0 lá longe → 1 na lâmpada
    v = perto ** 1.5 * _suave(perto * 6)                       # some devagar com a distância, sem borda no fim
    a = np.repeat(v[:, None], 8, axis=1)
    return _rgba(np.ones((256, 8, 3), np.float32), a)


def _madeira_barco(lado=256):
    rng = _rng("madeira-barco")
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
    fibra = _caixa_borrar(rng.random((lado, lado)).astype(np.float32), 1)
    fibra = _caixa_borrar(fibra, 10)
    fibra = (fibra - fibra.min()) / max(1e-6, float(np.ptp(fibra)))
    tabua = np.minimum(ys % 32, 32 - ys % 32)
    cor = _c("#4a3020") * (0.7 + 0.5 * fibra[..., None]) * (0.4 + 0.6 * _suave(tabua / 3))[..., None]
    return _rgb_img(cor)


def _grama(lado=128):
    rng = _rng("grama-farol")
    n = _ruido(lado, lado, 4, rng)
    return _rgb_img(_c("#2e4e24") * (0.6 + 0.7 * n[..., None]))


# ====================================================================== imagens 2D (provedor)
def imagem(partes):
    """terror/<peca>/... e farol/<peca>/... que não são da lua."""
    tipo, peca = partes[0], partes[1]
    if tipo == "tv":
        if peca == "chiado":                                    # tv/chiado/<variante>
            return _guardado(("chiado", partes[2]), lambda: _chiado(int(partes[2])))
        if peca == "rosto":                                     # tv/rosto/<variante>
            return _guardado(("rosto", partes[2]), lambda: _rosto(int(partes[2])))
        if peca == "teia":
            return _guardado(("teia",), _teia)
        if peca == "hera":
            return _guardado(("hera",), _hera)
    if tipo == "farol":
        w = int(float(partes[2])) if len(partes) > 2 else 0
        h = int(float(partes[3])) if len(partes) > 3 else 0
        f = {"ceu": lambda: _ceu(w, h), "cthulhu": _cthulhu, "nuvem": lambda: _nuvem(w), "onda": lambda: _onda(w),
             "penhasco": _penhasco, "barco": _barco, "feixe": _feixe, "raio": lambda: _raio(w), "gota": _gota,
             "horizonte": lambda: _horizonte(w, h)}[peca]
        return _guardado(("farol",) + tuple(partes[1:]), f)
    raise KeyError(peca)


# ---------------------------------------------------------------------- TV
def _chiado(variante, lado=256):
    """Chiado de TV fora do ar (preto e branco), repete sem emenda."""
    rng = np.random.default_rng(100 + variante)
    v = rng.random((lado, lado)).astype(np.float32)
    linha = rng.random((lado, 1)).astype(np.float32)              # algumas linhas inteiras mais claras/escuras
    v = v * 0.75 + linha * 0.25
    v = np.repeat(v[:, ::2], 2, axis=1)                           # grão um pouco esticado na horizontal
    return _rgb_img(np.repeat(v[..., None], 3, axis=2) * 0.95)


def _rosto(variante, lado=384):
    """Rosto fantasma (claro, olhos e boca fundos) pra aparecer no chiado."""
    rng = _rng("rosto", variante)
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32) / lado
    cx, cy = 0.5, 0.48
    cabeca = np.sqrt(((xs - cx) / 0.3) ** 2 + ((ys - cy) / 0.4) ** 2)
    pele = _suave((1 - cabeca) * 3) * (0.55 + 0.45 * _ruido(lado, lado, 10, rng))
    luz = pele.copy()
    for ex in (0.38, 0.62):                                       # órbitas fundas
        d = np.sqrt(((xs - ex) / 0.075) ** 2 + ((ys - 0.42) / 0.06) ** 2)
        luz *= 1 - _suave((1.4 - d) * 1.5) * 0.95
        pupila = np.sqrt(((xs - ex) / 0.012) ** 2 + ((ys - 0.43) / 0.012) ** 2)
        luz += _suave(1 - pupila) * 0.9 * (variante % 2)          # (variante ímpar: pupilas brilhando)
    nariz = np.sqrt(((xs - 0.5) / 0.03) ** 2 + ((ys - 0.56) / 0.02) ** 2)
    luz *= 1 - _suave((1.5 - nariz) * 2) * 0.7
    boca = np.sqrt(((xs - 0.5) / (0.08 + 0.03 * variante % 3)) ** 2 + ((ys - 0.72) / 0.07) ** 2)
    luz *= 1 - _suave((1.3 - boca) * 1.5) * 0.95
    bochecha = np.exp(-(((np.abs(xs - 0.5) - 0.17) / 0.05) ** 2 + ((ys - 0.62) / 0.08) ** 2))
    luz *= 1 - bochecha * 0.4                                     # cara chupada
    luz = _caixa_borrar(luz, 3)
    a = np.clip(_caixa_borrar(pele, 4) * 1.3, 0, 1)
    v = np.clip(luz * 1.2, 0, 1)
    return _rgba(np.repeat(v[..., None], 3, axis=2), a)


def _teia(lado=420):
    """Teia de aranha no canto (de cima/esquerda) — espelhar no QML pro outro canto."""
    rng = _rng("teia")

    def d(p, W, H):
        cor = QColor(200, 205, 180, 120)
        raios = [rng.uniform(0.02, 0.12) + k * (math.pi / 2 - 0.1) / 6 for k in range(7)]
        comp = [rng.uniform(0.7, 1.0) * W for _ in raios]
        p.setPen(QPen(cor, 1.6))
        for a, c in zip(raios, comp):
            p.drawLine(QPointF(0, 0), QPointF(math.cos(a) * c, math.sin(a) * c))
        for k in range(1, 9):                                      # fios em volta, caídos (barriga)
            r = W * 0.1 * k * rng.uniform(0.9, 1.05)
            caminho = QPainterPath()
            for i, (a, c) in enumerate(zip(raios, comp)):
                if r > c:
                    break
                pt = QPointF(math.cos(a) * r, math.sin(a) * r)
                if i == 0:
                    caminho.moveTo(pt)
                else:
                    a0 = raios[i - 1]
                    meio = QPointF(math.cos((a + a0) / 2) * r * 0.86, math.sin((a + a0) / 2) * r * 0.86)
                    caminho.quadTo(meio, pt)
            p.setPen(QPen(QColor(200, 205, 180, int(110 - k * 6)), 1.2))
            p.drawPath(caminho)
    return _pintar(lado, lado, d)


def _hera(lado=520):
    """Folhas de hera/papel de parede descascando (direita da sala)."""
    rng = _rng("hera")

    def d(p, W, H):
        for _ in range(26):
            x, y = rng.uniform(0.1, 0.9) * W, rng.uniform(0.05, 0.95) * H
            r = rng.uniform(26, 52)
            ang = rng.uniform(-0.6, 0.6)
            p.save()
            p.translate(x, y)
            p.rotate(math.degrees(ang))
            folha = QPainterPath(QPointF(0, -r))
            folha.cubicTo(QPointF(r * 0.9, -r * 0.6), QPointF(r * 0.8, r * 0.5), QPointF(0, r))
            folha.cubicTo(QPointF(-r * 0.8, r * 0.5), QPointF(-r * 0.9, -r * 0.6), QPointF(0, -r))
            v = rng.uniform(0.5, 1.0)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(int(52 * v), int(78 * v), int(44 * v), 235))
            p.drawPath(folha)
            p.setPen(QPen(QColor(20, 30, 16, 160), 2))
            p.drawLine(QPointF(0, -r * 0.8), QPointF(0, r * 0.8))
            p.restore()
    return _pixelar(_pintar(lado, lado, d), 3)


# ---------------------------------------------------------------------- FAROL
def _ceu(w, h):
    """Céu de tempestade verde-escuro com nuvens pesadas (sem o mar)."""
    w, h = max(64, w // 2), max(64, h // 2)                       # (meia resolução: fica pintado e é rápido)
    rng = _rng("ceu-farol", w, h)
    ys = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    cor = _c("#07120c") * (1 - ys[..., None]) + _c("#1e3a28") * ys[..., None]
    for raio, peso, lim in ((60, 0.55, 0.45), (22, 0.3, 0.5), (8, 0.15, 0.5)):
        n = _ruido(h, w, raio, rng)
        massa = _suave((n - lim) * 3)
        topo = _suave((n - lim - 0.12) * 4)                       # o lado de cima das nuvens pega mais luz
        cor = cor * (1 - massa[..., None] * peso) + _c("#0a1a10")[None, None] * massa[..., None] * peso
        cor += _c("#1e3a26")[None, None] * topo[..., None] * peso * 0.8
    brilho = np.exp(-(((np.linspace(0, 1, w)[None, :] - 0.66) / 0.18) ** 2 + ((ys - 0.12) / 0.12) ** 2))
    cor += _c("#2a5a3a") * brilho[..., None] * 0.5                 # clarão onde caem os raios
    img = _rgb_img(cor)
    return _pixelar(img.scaled(w * 2, h * 2, Qt.AspectRatioMode.IgnoreAspectRatio,
                               Qt.TransformationMode.SmoothTransformation), 4)


def _horizonte(w, h):
    """O mar lá longe (do horizonte até embaixo): verde-escuro com riscos de onda."""
    w, h = max(64, w // 2), max(64, h // 2)
    rng = _rng("mar-fundo", w, h)
    ys = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    xs = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    cor = (_c("#16302a") * (1 - ys[..., None]) + _c("#06100c") * ys[..., None]) * np.ones((1, w, 1), np.float32)
    riscos = _caixa_borrar(rng.random((h, w)).astype(np.float32), 1)
    riscos = _caixa_borrar(riscos.T, 6).T                         # riscos compridos na horizontal
    riscos = (riscos - riscos.min()) / max(1e-6, float(np.ptp(riscos)))
    cor += _c("#2a5a48") * _suave((riscos - 0.62) * 6)[..., None] * 0.5
    img = _rgb_img(cor)
    return _pixelar(img.scaled(w * 2, h * 2, Qt.AspectRatioMode.IgnoreAspectRatio,
                               Qt.TransformationMode.SmoothTransformation), 4)


def _nuvem(variante, w=1024, h=300):
    """Faixa de nuvem escura (repete na horizontal) que passa na frente do Cthulhu e da luz."""
    rng = _rng("nuvem-farol", variante)
    n = _ruido(h, w, 30, rng) * 0.7 + _ruido(h, w, 10, rng) * 0.3
    m = 120
    t = np.linspace(0, 1, m, dtype=np.float32)[None, :]
    n[:, :m] = n[:, :m] * t + n[:, -m:] * (1 - t)
    ys = np.linspace(-1, 1, h, dtype=np.float32)[:, None]
    a = _suave((n - 0.42) * 3) * _suave((1 - np.abs(ys)) * 2.5) * 0.9
    cor = _c("#0c1c12") * (0.8 + 0.5 * n[..., None])
    return _pixelar(_rgba(cor, a), 3)


def _tentaculo(p, pts, w0, w1, cor, ventosas=None):
    """Tentáculo grosso afinando: polígono em volta de uma linha (pts), de w0 (base) a w1 (ponta)."""
    n = len(pts)
    esq, dir_ = [], []
    for k, (x, y) in enumerate(pts):
        xa, ya = pts[max(0, k - 1)]
        xb, yb = pts[min(n - 1, k + 1)]
        dx, dy = xb - xa, yb - ya
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        w = w0 + (w1 - w0) * (k / (n - 1)) ** 0.8
        esq.append(QPointF(x + nx * w, y + ny * w))
        dir_.append(QPointF(x - nx * w, y - ny * w))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(cor)
    p.drawPolygon(QPolygonF(esq + dir_[::-1]))
    if ventosas is not None:                                     # ventosas claras do lado de dentro
        p.setBrush(ventosas)
        for k in range(3, n - 4, 3):
            x, y = pts[k]
            w = w0 + (w1 - w0) * (k / (n - 1)) ** 0.8
            e = esq[k]
            vx, vy = x + (e.x() - x) * 0.62, y + (e.y() - y) * 0.62
            p.drawEllipse(QPointF(vx, vy), w * 0.26, w * 0.2)


def _arco_enrolado(x0, y0, lado, alto, largo, enrola, passos=70):
    """Linha de um tentáculo que sai da água, SOBE fazendo um arco pro lado e ENROLA a ponta pra dentro (espiral)."""
    pts = []
    corpo = int(passos * 0.7)
    for k in range(corpo):
        u = k / (corpo - 1)
        x = x0 + lado * largo * math.sin(u * math.pi * 0.82)        # abre pro lado e volta (arco)
        y = y0 - alto * (1 - (1 - u) ** 1.8)
        pts.append((x, y))
    bx, by = pts[-1]
    ax, ay = pts[-2]
    ang0 = math.atan2(by - ay, bx - ax)                      # direção em que o tentáculo vinha
    for k in range(1, passos - corpo + 1):
        u = k / (passos - corpo)
        ang = ang0 - lado * u * math.pi * 1.7                 # vai virando pra dentro
        r = enrola * (1 - u * 0.7)
        bx += math.cos(ang) * r * 0.18
        by += math.sin(ang) * r * 0.18
        pts.append((bx, by))
    return pts

def _cthulhu(W=900, H=640):
    """(v0.58, pela imagem do Manel) Cthulhu-polvo GIGANTE saindo do mar: cabeça alta e bulbosa, olhos acesos,
    tentáculos grossos saindo da água pros dois lados, fazendo arcos e ENROLANDO nas pontas, com ventosas.
    Bem escuro (aparece no clarão do raio)."""
    def d(p, W, H):
        cx = W / 2
        escuro = QColor(6, 14, 12, 240)
        menos = QColor(14, 30, 26, 235)
        vent = QColor(120, 150, 130, 90)
        agua = H * 0.97
        # tentáculos de TRÁS (mais claros = mais longe), arcos grandes
        for lado, x0, alto, largo, enr, w in ((-1, 200, H * 0.66, W * 0.26, 70, 26), (1, 190, H * 0.78, W * 0.24, 80, 28),
                                              (-1, 90, H * 0.9, W * 0.2, 60, 22), (1, 300, H * 0.52, W * 0.18, 60, 22)):
            pts = _arco_enrolado(cx + lado * x0, agua, lado, alto, largo, enr)
            _tentaculo(p, pts, w, 4, menos, vent)
        # a CABEÇA (manto alto e bulboso, um pouco torto)
        cab = QPainterPath(QPointF(cx - 70, H * 0.74))
        cab.cubicTo(QPointF(cx - 150, H * 0.62), QPointF(cx - 200, H * 0.32), QPointF(cx - 120, H * 0.1))
        cab.cubicTo(QPointF(cx - 60, H * 0.0), QPointF(cx + 90, H * 0.0), QPointF(cx + 140, H * 0.14))
        cab.cubicTo(QPointF(cx + 200, H * 0.34), QPointF(cx + 150, H * 0.62), QPointF(cx + 70, H * 0.74))
        cab.quadTo(QPointF(cx, H * 0.8), QPointF(cx - 70, H * 0.74))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(escuro)
        p.drawPath(cab)
        # sobrancelhas pesadas e o "rosto"
        p.setBrush(QColor(2, 6, 6, 250))
        for lado in (-1, 1):
            sob = QPainterPath(QPointF(cx + lado * 18, H * 0.47))
            sob.quadTo(QPointF(cx + lado * 60, H * 0.40), QPointF(cx + lado * 112, H * 0.47))
            sob.quadTo(QPointF(cx + lado * 60, H * 0.45), QPointF(cx + lado * 18, H * 0.50))
            p.drawPath(sob)
        # os tentáculos da cara (grossos, descendo até a água)
        for k, (dx, curva, w) in enumerate(((-70, -40, 22), (-35, -18, 26), (0, 6, 28), (35, 22, 26), (70, 44, 22))):
            pts = [(cx + dx + curva * (t / 20) ** 1.6 + math.sin(t * 0.4 + k) * 4, H * 0.55 + (agua - H * 0.55) * t / 20)
                   for t in range(21)]
            _tentaculo(p, pts, w, w * 0.55, escuro)
        # tentáculos da FRENTE saindo da água (os mais escuros)
        for lado, x0, alto, largo, enr, w in ((-1, 260, H * 0.5, W * 0.22, 60, 30), (1, 250, H * 0.58, W * 0.22, 64, 32)):
            pts = _arco_enrolado(cx + lado * x0, agua, lado, alto, largo, enr)
            _tentaculo(p, pts, w, 5, escuro, vent)
        # olhos acesos
        for lado in (-1, 1):
            g = QRadialGradient(QPointF(cx + lado * 62, H * 0.5), 26)
            g.setColorAt(0, QColor(255, 250, 200, 255))
            g.setColorAt(0.35, QColor(220, 255, 170, 200))
            g.setColorAt(1, QColor(160, 255, 160, 0))
            p.setBrush(QBrush(g))
            p.drawEllipse(QPointF(cx + lado * 62, H * 0.5), 26, 13)
        # espuma onde ele sai da água
        rng = _rng("espuma-cthulhu")
        for _ in range(90):
            x = rng.uniform(cx - W * 0.42, cx + W * 0.42)
            r = rng.uniform(4, 16)
            p.setBrush(QColor(200, 230, 215, int(rng.uniform(40, 120))))
            p.drawEllipse(QPointF(x, agua - rng.uniform(0, 26)), r, r * 0.6)
    return _pixelar(_pintar(W, H, d), 3)

def _onda(variante, w=1024, h=260):
    """Faixa de ondas (repete na horizontal): crista com espuma, corpo verde-escuro descendo."""
    rng = _rng("onda", variante)
    xs = np.arange(w, dtype=np.float32)
    ys = np.arange(h, dtype=np.float32)[:, None]
    crista = np.zeros(w, np.float32)
    for k, amp in ((2, 26), (3, 16), (5, 10), (9, 6), (14, 3)):
        crista += amp * np.sin(xs / w * 2 * math.pi * k + rng.uniform(0, 6.28))
    crista = h * 0.35 + crista * (0.7 + variante * 0.15)
    dy = ys - crista[None, :]
    a = _suave(dy / 3 + 0.5)
    prof = np.clip(dy / (h * 0.7), 0, 1)
    cor = _c("#1e4a3a") * (1 - prof[..., None]) + _c("#06140e") * prof[..., None]
    inclin = np.gradient(crista)[None, :]                         # o lado da onda virado pra luz é mais claro
    cor += _c("#2a6a50") * np.clip(-inclin * 0.15, 0, 0.5)[..., None] * np.exp(-dy / 40)[..., None]
    espuma = np.exp(-np.maximum(dy, 0) / (6 + 10 * _ruido(1, w, 8, rng)[0][None, :])) * (dy > -2)
    rasgo = _ruido(h, w, 3, rng)
    espuma = espuma * _suave((rasgo - 0.25) * 3)
    linhas = _suave((_ruido(h, w, 2, rng) - 0.7) * 6) * np.exp(-np.maximum(dy, 0) / 60) * (dy > 0)
    cor = cor * (1 - espuma[..., None]) + _c("#cfe8dc") * espuma[..., None]
    cor = cor * (1 - linhas[..., None] * 0.5) + _c("#8ab8a4") * linhas[..., None] * 0.5
    return _pixelar(_rgba(cor, a), 3)


def _facetas(p, caminho, caixa, tons, luz, rng, passo=46):
    """Pinta uma área (rocha) com triângulos de tons diferentes = cara de low-poly / pintura facetada."""
    x0, y0, x1, y1 = caixa
    cols, lins = int((x1 - x0) / passo) + 2, int((y1 - y0) / passo) + 2
    pts = [[QPointF(x0 + i * passo + rng.uniform(-0.35, 0.35) * passo, y0 + j * passo + rng.uniform(-0.35, 0.35) * passo)
            for i in range(cols)] for j in range(lins)]
    p.save()
    p.setClipPath(caminho)
    p.setPen(Qt.PenStyle.NoPen)
    for j in range(lins - 1):
        for i in range(cols - 1):
            a, b, c, d = pts[j][i], pts[j][i + 1], pts[j + 1][i], pts[j + 1][i + 1]
            for tri in ((a, b, c), (b, d, c)):
                v = rng.uniform(0, 1)
                cx = (tri[0].x() + tri[1].x() + tri[2].x()) / 3
                k = min(len(tons) - 1, int(v * len(tons)))
                cor = QColor(tons[k])
                f = 0.75 + 0.5 * luz(cx, (tri[0].y() + tri[1].y() + tri[2].y()) / 3) + rng.uniform(-0.08, 0.08)
                cor = QColor(min(255, int(cor.red() * f)), min(255, int(cor.green() * f)), min(255, int(cor.blue() * f)))
                p.setBrush(cor)
                p.drawPolygon(QPolygonF(list(tri)))
    p.restore()


def _penhasco(W=900, H=1100):
    """Penhasco facetado com a casinha e o FAROL em cima (a luz e o feixe são do QML)."""
    rng = _rng("penhasco")

    def d(p, W, H):
        topo = H * 0.42
        rocha = QPainterPath(QPointF(0, topo + 10))
        rocha.lineTo(QPointF(W * 0.2, topo))
        rocha.lineTo(QPointF(W * 0.5, topo + 6))
        rocha.lineTo(QPointF(W * 0.62, topo + 30))
        rocha.lineTo(QPointF(W * 0.66, H * 0.52))
        rocha.lineTo(QPointF(W * 0.72, H * 0.6))
        rocha.lineTo(QPointF(W * 0.7, H * 0.66))
        rocha.lineTo(QPointF(W * 0.84, H * 0.76))
        rocha.lineTo(QPointF(W * 0.92, H * 0.86))
        rocha.lineTo(QPointF(W, H))
        rocha.lineTo(QPointF(0, H))
        rocha.closeSubpath()
        _facetas(p, rocha, (0, topo - 20, W, H), ["#1e2a24", "#26342c", "#2e3e32", "#344636", "#1a241e"],
                 lambda x, y: 0.4 * (1 - x / W) - 0.3 * (y / H) + 0.2, rng, 54)
        p.setPen(QPen(QColor(10, 18, 14, 200), 3))                # rachaduras verticais
        for _ in range(9):
            x = rng.uniform(0.05, 0.6) * W
            y = rng.uniform(0.32, 0.6) * H
            p.drawLine(QPointF(x, y), QPointF(x + rng.uniform(-30, 30), y + rng.uniform(80, 220)))
        grama = QPainterPath(QPointF(0, topo + 14))               # capim/musgo por cima
        grama.lineTo(QPointF(W * 0.2, topo - 6))
        grama.lineTo(QPointF(W * 0.5, topo))
        grama.lineTo(QPointF(W * 0.63, topo + 26))
        grama.lineTo(QPointF(W * 0.6, topo + 46))
        grama.lineTo(QPointF(W * 0.3, topo + 30))
        grama.lineTo(QPointF(0, topo + 48))
        grama.closeSubpath()
        _facetas(p, grama, (0, topo - 30, W * 0.7, topo + 60), ["#2a4a26", "#345a2c", "#3e6a32", "#24401e"],
                 lambda x, y: 0.2, rng, 26)
        # casinha
        cx = W * 0.14
        p.setPen(QPen(QColor("#141a16"), 2))
        p.setBrush(QColor("#9a9a8a"))
        p.drawRect(QRectF(cx - 70, topo - 70, 150, 72))
        p.setBrush(QColor("#7a7a6c"))
        p.drawRect(QRectF(cx + 50, topo - 70, 30, 72))
        p.setBrush(QColor("#6a2a1e"))
        p.drawPolygon(QPolygonF([QPointF(cx - 84, topo - 66), QPointF(cx - 40, topo - 118), QPointF(cx + 70, topo - 118),
                                 QPointF(cx + 94, topo - 66)]))
        p.setBrush(QColor("#1a2420"))
        p.drawRect(QRectF(cx - 40, topo - 50, 22, 26))
        p.drawRect(QRectF(cx + 10, topo - 50, 22, 26))
        # o farol (torre de pedra afinando)
        fx, base, alto = W * 0.36, topo + 4, H * 0.2
        torre = QPolygonF([QPointF(fx - 58, base), QPointF(fx - 40, base - alto), QPointF(fx + 40, base - alto),
                           QPointF(fx + 58, base)])
        g = QLinearGradient(fx - 58, 0, fx + 58, 0)
        g.setColorAt(0, QColor("#b8b8a8"))
        g.setColorAt(0.55, QColor("#8a8a7c"))
        g.setColorAt(1, QColor("#4a4e46"))
        p.setBrush(QBrush(g))
        p.drawPolygon(torre)
        p.setPen(Qt.PenStyle.NoPen)
        for _ in range(140):                                       # pedras/manchas da torre
            yy = rng.uniform(base - alto, base)
            meia = 40 + 18 * (yy - (base - alto)) / alto
            p.setBrush(QColor(0, 0, 0, int(rng.uniform(15, 50))))
            p.drawRect(QRectF(fx + rng.uniform(-meia, meia - 10), yy, rng.uniform(6, 14), rng.uniform(3, 6)))
        p.setBrush(QColor("#1a2420"))
        p.drawRect(QRectF(fx - 12, base - 46, 24, 46))             # porta
        p.drawRect(QRectF(fx - 7, base - alto * 0.6, 14, 20))      # janelinha
        topo_t = base - alto
        p.setPen(QPen(QColor("#141a16"), 2))
        p.setBrush(QColor("#3a3e38"))
        p.drawRect(QRectF(fx - 58, topo_t - 10, 116, 12))          # galeria
        for k in range(9):
            x = fx - 54 + k * 13.5
            p.drawLine(QPointF(x, topo_t - 10), QPointF(x, topo_t - 30))
        p.drawLine(QPointF(fx - 56, topo_t - 30), QPointF(fx + 56, topo_t - 30))
        p.setBrush(QColor("#2a3028"))
        p.drawRect(QRectF(fx - 34, topo_t - 76, 68, 66))           # sala da lâmpada (o brilho vem do QML)
        p.setBrush(QColor("#c8e870"))
        p.drawRect(QRectF(fx - 26, topo_t - 70, 52, 54))
        p.setBrush(QColor("#5a2a1e"))
        p.drawPolygon(QPolygonF([QPointF(fx - 44, topo_t - 76), QPointF(fx, topo_t - 118), QPointF(fx + 44, topo_t - 76)]))
        p.drawLine(QPointF(fx, topo_t - 118), QPointF(fx, topo_t - 134))
    img = _pintar(W, H, d)
    return _pixelar(img, 3)


def farol_lampada():
    """Onde fica a lâmpada no desenho do penhasco (fração da imagem) — o QML põe o brilho e o feixe ali."""
    W, H = 900, 1100
    topo = H * 0.42
    return (W * 0.36 / W, (topo + 4 - H * 0.2 - 43) / H)


def _barco(W=760, H=820):
    """A proa do barco (canto de baixo, direita), com amurada, cabeço, cordas e a escada de corda subindo."""
    rng = _rng("barco")

    def d(p, W, H):
        # casco (lado de fora): tábuas
        casco = QPolygonF([QPointF(W * 0.02, H * 0.38), QPointF(W * 0.12, H * 0.42), QPointF(W, H * 0.6),
                           QPointF(W, H), QPointF(W * 0.42, H), QPointF(W * 0.1, H * 0.6)])
        g = QLinearGradient(0, H * 0.4, 0, H)
        g.setColorAt(0, QColor("#4a3020"))
        g.setColorAt(1, QColor("#1e140c"))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawPolygon(casco)
        p.save()
        cam = QPainterPath()
        cam.addPolygon(casco)
        p.setClipPath(cam)
        for k in range(14):                                         # linhas das tábuas
            y0 = H * 0.42 + k * 32
            p.setPen(QPen(QColor(10, 6, 2, 170), 3))
            p.drawLine(QPointF(0, y0 + 10), QPointF(W, y0 + 10 + W * 0.22))
            p.setPen(QPen(QColor(120, 80, 50, 50), 2))
            p.drawLine(QPointF(0, y0 + 14), QPointF(W, y0 + 14 + W * 0.22))
        p.fillRect(QRectF(0, H * 0.55, W, H * 0.06), QColor(110, 30, 20, 90))   # faixa vermelha velha
        p.restore()
        # convés (de cima)
        conves = QPolygonF([QPointF(W * 0.02, H * 0.38), QPointF(W * 0.38, H * 0.3), QPointF(W, H * 0.33),
                            QPointF(W, H * 0.6), QPointF(W * 0.12, H * 0.42)])
        p.setBrush(QColor("#5a3e28"))
        p.drawPolygon(conves)
        p.save()
        cam = QPainterPath()
        cam.addPolygon(conves)
        p.setClipPath(cam)
        for k in range(16):                                         # tábuas do convés + brilho molhado
            x = W * 0.1 + k * 48
            p.setPen(QPen(QColor(20, 12, 6, 180), 3))
            p.drawLine(QPointF(x, H * 0.25), QPointF(x - 120, H * 0.62))
        for _ in range(60):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(170, 210, 190, int(rng.uniform(20, 70))))
            p.drawEllipse(QPointF(rng.uniform(0.2, 1) * W, rng.uniform(0.33, 0.55) * H), rng.uniform(4, 16), rng.uniform(1, 3))
        p.restore()
        # amurada (corrimão) com postes
        p.setPen(QPen(QColor("#2a1a10"), 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(W * 0.06, H * 0.36), QPointF(W * 0.38, H * 0.27))
        p.drawLine(QPointF(W * 0.38, H * 0.27), QPointF(W, H * 0.28))
        p.setPen(QPen(QColor("#2a1a10"), 9))
        for k in range(9):
            x = W * 0.42 + k * 66
            p.drawLine(QPointF(x, H * 0.275), QPointF(x - 6, H * 0.33))
        # cabeço de amarração
        p.setPen(QPen(QColor("#141008"), 2))
        p.setBrush(QColor("#4a3626"))
        p.drawRect(QRectF(W * 0.5 - 22, H * 0.3, 44, 44))
        p.setBrush(QColor("#5e4632"))
        p.drawEllipse(QRectF(W * 0.5 - 28, H * 0.29, 56, 20))
        # cordas: enrolada no cabeço e caindo pelo casco
        corda = QColor("#8a7a48")
        for k in range(4):
            p.setPen(QPen(corda.darker(100 + k * 12), 7))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(W * 0.5 - 30 - k, H * 0.315 + k * 7, 60 + 2 * k, 14))
        for (x0, comp) in ((W * 0.22, 0.42), (W * 0.62, 0.32)):
            cam = QPainterPath(QPointF(x0, H * 0.4))
            cam.cubicTo(QPointF(x0 - 30, H * 0.6), QPointF(x0 + 20, H * (0.4 + comp * 0.7)), QPointF(x0 - 10, H * (0.4 + comp)))
            p.setPen(QPen(QColor("#2a2414"), 11))
            p.drawPath(cam)
            p.setPen(QPen(corda, 7, Qt.PenStyle.DashLine))
            p.drawPath(cam)
        # escada de corda subindo pro mastro (canto de cima)
        p.setPen(QPen(QColor("#6a5a34"), 6))
        p.drawLine(QPointF(W * 0.82, H * 0.3), QPointF(W * 0.98, 0))
        p.drawLine(QPointF(W * 0.94, H * 0.32), QPointF(W * 1.08, 0))
        for k in range(9):
            t = k / 9
            p.drawLine(QPointF(W * (0.82 + 0.16 * t), H * 0.3 * (1 - t)), QPointF(W * (0.94 + 0.14 * t), H * 0.32 * (1 - t)))
    img = _pintar(W, H, d)
    return _pixelar(img, 3)


def _feixe(W=1000, H=300):
    """O feixe de luz do farol (cone saindo da esquerda)."""
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    u = xs / W
    meia = 0.04 + 0.46 * u                                         # abre conforme se afasta
    v = np.abs(ys / H - 0.5) / meia
    a = _suave((1 - v) * 2.2) * (1 - u) ** 1.2 * 0.75
    rng = _rng("feixe")
    a *= 0.8 + 0.25 * _ruido(H, W, 18, rng)                        # chuva/neblina dentro da luz
    cor = _c("#d8f080") * np.ones((H, W, 1), np.float32)
    return _pixelar(_rgba(cor, a), 4)


def _raio(variante, W=360, H=700):
    """Um raio ramificado com brilho (variantes diferentes)."""
    rng = _rng("raio", variante)

    def d(p, W, H):
        def trecho(x, y, ang, comp, esp, nivel):
            pts = [QPointF(x, y)]
            for _ in range(int(comp / 22)):
                ang += rng.uniform(-0.5, 0.5)
                x += math.cos(ang) * 22
                y += math.sin(ang) * 22
                pts.append(QPointF(x, y))
                if nivel < 2 and rng.random() < 0.12:
                    trecho(x, y, ang + rng.choice([-0.7, 0.7]), comp * 0.35, esp * 0.5, nivel + 1)
            for larg, alfa in ((esp * 6, 40), (esp * 3, 90), (esp, 255)):
                p.setPen(QPen(QColor(200, 255, 210, alfa), larg, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                              Qt.PenJoinStyle.RoundJoin))
                p.drawPolyline(QPolygonF(pts))
        trecho(W * 0.5, 0, math.pi / 2, H * 0.95, 4, 0)
    return _pintar(W, H, d)


def _gota():
    """Risco de chuva inclinado (imagem quadrada: as partículas são desenhadas em quadrado)."""
    def d(p, W, H):
        g = QLinearGradient(W * 0.3, 0, W * 0.5, H)
        g.setColorAt(0, QColor(170, 220, 190, 0))
        g.setColorAt(1, QColor(200, 240, 220, 220))
        p.setPen(QPen(QBrush(g), 1.6))
        p.drawLine(QPointF(W * 0.3, 0), QPointF(W * 0.5, H))
    return _pintar(48, 48, d)
