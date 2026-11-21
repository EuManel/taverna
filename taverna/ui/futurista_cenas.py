"""
🌆 Cenários do tema Futurista / cyberpunk (v0.58, pacote do Manel). Sorteia um (50/50, e de novo ao escolher o tema):

  BECO — beco de neon na chuva: poças refletindo as luzes, vapor saindo do bueiro, fios pendurados. CADA OPÇÃO
         É UMA PLACA DE NEON na parede: o mouse liga a placa piscando ("tz-tz") e a luz dela pinta a parede e a
         poça. Letreiros de fundo com palavras inventadas (nada de marca de verdade).
  NAVE — cabine de nave: painel de controle na frente, janela pro espaço com um planeta e uma estação passando
         devagar. As opções são HOLOGRAMAS que sobem do console; parados têm interferência, o mouse firma.

Aqui ficam as texturas (gravadas em arquivo, ver `estilizado.caminho_textura_3d`).
"""

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPen

from .estilizado import _c, _caixa_borrar, _rgb_img, _rng, _ruido, _suave
from .terror_cenas import _guardado, _pintar, _rgba

LETREIROS = ["RAMEN-KAI", "BAR ÓRBITA", "HOTEL ÉDEN", "PIXEL 24H", "NEO-DOJO", "SAKE", "CYBER-CAFÉ", "LOJA 77"]


def textura(nome):
    f = {"parede_beco": _parede_beco, "concreto_cyber": _concreto_cyber, "chao_beco": _chao_beco, "planeta": _planeta, "painel_nave": _painel_nave,
         "linhas_holo": _linhas_holo, "estrelas_nave": _estrelas_nave}.get(nome)
    return _guardado(("futurista", nome), f) if f else None


def _parede_beco(lado=1024):
    """Parede do beco: concreto/tijolo escuro molhado, com manchas de chuva escorrendo e pichações apagadas."""
    rng = _rng("parede-beco")
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
    lin = np.floor(ys / 36)
    lu = (xs + (lin % 2) * 40) % 80
    junta = np.minimum(np.minimum(lu, 80 - lu), np.minimum(ys % 36, 36 - ys % 36))
    n = _ruido(lado, lado, 6, rng)
    tons = _rng("tons-beco").random(64).astype(np.float32)
    k = ((lin * 7 + np.floor((xs + (lin % 2) * 40) / 80) * 13).astype(int)) % 64
    cor = _c("#4a4858") * (0.7 + 0.4 * tons[k])[..., None] * (0.8 + 0.3 * n[..., None])
    cor *= (0.45 + 0.55 * _suave(junta / 3))[..., None]
    escorre = _caixa_borrar(rng.random((lado, lado)).astype(np.float32), 1)
    escorre = _caixa_borrar(escorre.T, 26).T
    escorre = (escorre - escorre.min()) / max(1e-6, float(np.ptp(escorre)))
    cor *= (0.7 + 0.45 * escorre[..., None])
    musgo = _suave((_ruido(lado, lado, 30, rng) - 0.72) * 5)
    cor = cor * (1 - musgo[..., None] * 0.4) + _c("#1e3a34") * musgo[..., None] * 0.4
    return _rgb_img(cor)


def _concreto_cyber(lado=1024):
    """Concreto bruto LISO (o Manel: "cyberpunk é concreto liso, nada de tijolinho"): placas de fôrma grandes com
    as juntas finas, os furinhos dos tirantes em grade, manchas de chuva escorrendo, remendos e rachaduras."""
    rng = _rng("concreto-cyber")
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
    n = _ruido(lado, lado, 5, rng) * 0.5 + _ruido(lado, lado, 40, rng) * 0.5
    cor = _c("#7a7c84") * (0.82 + 0.3 * n[..., None])
    painel = (np.floor(xs / 256) * 3 + np.floor(ys / 512) * 7).astype(int)          # cada placa de fôrma num tom
    cor *= (0.85 + 0.25 * _rng("tons-concreto").random(64).astype(np.float32)[painel % 64])[..., None]
    junta = np.minimum(np.minimum(xs % 256, 256 - xs % 256), np.minimum(ys % 512, 512 - ys % 512))
    cor *= (0.62 + 0.38 * _suave(junta / 2.5))[..., None]
    for cx in range(64, lado, 128):                                                # furos dos tirantes
        for cy in range(64, lado, 128):
            d = np.hypot(xs - cx, ys - cy)
            cor *= (1 - 0.55 * np.exp(-(d / 5) ** 2))[..., None]
            cor *= (1 - 0.12 * np.exp(-(d / 12) ** 2))[..., None]
    col = rng.random(lado).astype(np.float32) ** 4                                # chuva escorrendo (riscos verticais)
    col = np.convolve(col, np.ones(3, np.float32) / 3, mode="same")
    comp = _ruido(lado, lado, 70, rng)                                            # (cada risco some numa altura)
    escorre = col[xs.astype(int)] * _suave((comp - 0.35) * 3)
    cor *= (1 - 0.55 * np.clip(escorre * 2.2, 0, 1))[..., None]
    sob_junta = np.exp(-((ys % 512) / 90)) * 0.25                                  # sujeira escorrendo das juntas
    cor *= (1 - sob_junta * (0.5 + 0.5 * comp))[..., None]
    mancha = _suave((_ruido(lado, lado, 60, rng) - 0.55) * 4)                     # umidade escura
    cor *= (1 - 0.45 * mancha[..., None])
    remendo = _suave((_ruido(lado, lado, 90, rng) - 0.78) * 8)                    # remendo mais claro
    cor = cor * (1 - remendo[..., None] * 0.5) + _c("#8e9098") * remendo[..., None] * 0.5
    img = _rgb_img(np.clip(cor, 0, 1))
    from PyQt6.QtGui import QPainter
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    for _ in range(9):                                                            # rachaduras
        x, y = rng.uniform(0, lado), rng.uniform(0, lado)
        p.setPen(QPen(QColor(20, 20, 26, int(rng.uniform(120, 200))), rng.uniform(0.8, 1.8)))
        ang = rng.uniform(0, 2 * math.pi)
        for _k in range(int(rng.uniform(8, 22))):
            ang += rng.uniform(-0.7, 0.7)
            nx, ny = x + math.cos(ang) * rng.uniform(6, 18), y + math.sin(ang) * rng.uniform(6, 18)
            p.drawLine(QPointF(x, y), QPointF(nx, ny))
            x, y = nx, ny
    p.end()
    return img


def _chao_beco(lado=1024):
    """Asfalto molhado (escuro, liso) — as poças são pedaços mais lisos ainda (o QML põe o reflexo)."""
    rng = _rng("chao-beco")
    n = _ruido(lado, lado, 3, rng) * 0.6 + _ruido(lado, lado, 18, rng) * 0.4
    cor = _c("#26262e") * (0.65 + 0.6 * n[..., None])
    return _rgb_img(cor)


def _planeta(W=1024, H=512):
    """Planeta (mapa equiretangular): faixas de gás azul/roxo com tempestades."""
    rng = _rng("planeta")
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    v = ys / H
    n = _ruido(H, W, 14, rng)
    faixa = np.sin(v * 38 + n * 4) * 0.5 + 0.5
    cor = _c("#2a4a9a")[None, None] * (1 - faixa[..., None]) + _c("#7a4ac8")[None, None] * faixa[..., None]
    cor = cor * (0.75 + 0.4 * _ruido(H, W, 4, rng)[..., None])
    for _ in range(4):                                       # tempestades (ovais claras)
        cx, cy, r = rng.uniform(0, W), rng.uniform(H * 0.2, H * 0.8), rng.uniform(20, 50)
        d = ((xs - cx) / (r * 2)) ** 2 + ((ys - cy) / r) ** 2
        cor += _c("#c8d8ff")[None, None] * (np.exp(-d * 2) * 0.5)[..., None]
    return _rgb_img(np.clip(cor, 0, 1))


def _estrelas_nave(W=2048, H=1024):
    """Espaço pra janela da nave: preto azulado, nebulosa ciano/magenta e estrelas."""
    rng = _rng("estrelas-nave")
    h2, w2 = H // 2, W // 2
    n1, n2 = _ruido(h2, w2, 40, rng), _ruido(h2, w2, 12, rng)
    neb = _suave((n1 * 0.7 + n2 * 0.3 - 0.5) * 2.5)
    cor = _c("#03050c")[None, None] * np.ones((h2, w2, 1), np.float32)
    cor += (_c("#0e5a6a") * (1 - n2[..., None]) + _c("#5a1a5a") * n2[..., None]) * neb[..., None] * 0.7
    cor = np.repeat(np.repeat(cor, 2, axis=0), 2, axis=1)
    ys, xs = rng.integers(0, H, 1800), rng.integers(0, W, 1800)
    b = rng.random(1800) ** 3
    for y, x, v in zip(ys, xs, b):
        cor[y, x] = np.maximum(cor[y, x], 0.45 + 0.55 * v)
    return _rgb_img(np.clip(cor, 0, 1))


def _painel_nave(lado=512):
    """Chapa do painel da nave: metal escuro com recortes, parafusos e frisos."""
    rng = _rng("painel-nave")

    def d(p, W, H):
        p.fillRect(0, 0, W, H, QColor("#454e62"))
        for _ in range(500):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, int(rng.uniform(2, 10))) if rng.random() < 0.5 else QColor(0, 0, 0, int(rng.uniform(5, 25))))
            r = rng.uniform(2, 14)
            p.drawEllipse(QPointF(rng.uniform(0, W), rng.uniform(0, H)), r, r)
        p.setPen(QPen(QColor(20, 24, 32), 3))
        for k in range(4):                                     # recortes (placas)
            x0, y0 = rng.uniform(20, W * 0.6), rng.uniform(20, H * 0.6)
            p.drawRect(QRectF(x0, y0, rng.uniform(80, 200), rng.uniform(60, 160)))
        p.setPen(QPen(QColor(110, 124, 150), 2))
        for y in (H * 0.25, H * 0.75):
            p.drawLine(QPointF(0, y), QPointF(W, y))
        p.setPen(Qt.PenStyle.NoPen)
        for (x, y) in ((16, 16), (W - 16, 16), (16, H - 16), (W - 16, H - 16)):
            p.setBrush(QColor(90, 96, 110))
            p.drawEllipse(QPointF(x, y), 6, 6)
    return _pintar(lado, lado, d)


def _linhas_holo(W=8, H=8):
    """Linhas de varredura do holograma (repete)."""
    a = np.zeros((H, W), np.float32)
    a[::2, :] = 0.55
    return _rgba(np.ones((H, W, 3), np.float32), a)
