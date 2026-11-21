"""
🌫 Névoa DESENHADA da cidade/mundo no jogador (v0.83).

O jogador recebe a imagem da cidade/mundo só com a parte revelada (o resto chega transparente, com a borda suave —
rede/atlas_rede.py). Antes a parte coberta era o fundo escuro liso. Agora, por cima do "buraco", vai uma névoa no
estilo do TEMA: pergaminho (medieval), estática de radar (futurista), fumaça (steampunk), poeira (pós-apocalíptico),
breu com névoa (terror), nuvens arroxeadas com brilhos (mágico), nuvens (moderno/claro/escuro) — e uma BORDA onde o
revelado acaba (queimada, brilhando ou de neon, conforme o tema).

Gráficos: Baixo = como antes (nada desenhado) · Médio = névoa parada · Alto = a névoa anda devagar.
Tudo em numpy numa grade de até 512 px (a imagem é ampliada com suavização): barato, e só refaz quando a névoa muda
(ou, no Alto, ~10× por segundo enquanto o atlas está na tela).
"""

import math

import numpy as np
from PyQt6.QtGui import QImage, QTransform

LADO_MAX = 512        # resolução da grade da névoa (o lado maior)
LADO_TEXTURA = 256    # a textura repete sem emenda

# cores em (R, G, B). estilo: nuvem · pergaminho · estatica
ESTILOS = {
    "medieval": dict(estilo="pergaminho", claro=(201, 178, 133), escuro=(124, 96, 60), borda=(46, 24, 8),
                     brilho=(255, 150, 50), vel=(0.0, 0.0)),
    "moderno": dict(estilo="nuvem", claro=(150, 156, 164), escuro=(70, 76, 84), borda=(28, 31, 35),
                    brilho=(170, 230, 222), vel=(6.0, 2.0)),
    "futurista": dict(estilo="estatica", claro=(40, 90, 130), escuro=(6, 14, 28), borda=(0, 0, 0),
                      brilho=(56, 225, 255), vel=(0.0, 18.0)),
    "magico": dict(estilo="nuvem", claro=(132, 96, 186), escuro=(34, 18, 60), borda=(16, 6, 30),
                   brilho=(214, 170, 255), vel=(5.0, -3.0), faiscas=True),
    "terror": dict(estilo="nuvem", claro=(70, 52, 52), escuro=(10, 6, 7), borda=(70, 0, 0),
                   brilho=(150, 20, 20), vel=(3.0, 1.0)),
    "steampunk": dict(estilo="nuvem", claro=(150, 132, 108), escuro=(56, 46, 36), borda=(30, 20, 10),
                      brilho=(230, 170, 70), vel=(8.0, -4.0)),
    "posapoc": dict(estilo="nuvem", claro=(176, 150, 106), escuro=(92, 72, 46), borda=(52, 26, 12),
                    brilho=(200, 96, 40), vel=(14.0, 3.0)),
    "claro": dict(estilo="nuvem", claro=(246, 246, 248), escuro=(196, 200, 208), borda=(120, 126, 136),
                  brilho=(255, 255, 255), vel=(5.0, 2.0)),
    "escuro": dict(estilo="nuvem", claro=(64, 66, 74), escuro=(16, 17, 21), borda=(4, 4, 6),
                   brilho=(120, 130, 160), vel=(4.0, 2.0)),
}

_texturas: dict = {}
_cache: dict = {}


def _ruido(lado: int, semente: int, queda: float) -> np.ndarray:
    """Ruído de nuvem que repete sem emenda (espectro 1/f^queda, feito por FFT): 0..1."""
    rng = np.random.default_rng(semente)
    f = np.fft.fftfreq(lado)
    r = np.sqrt(f[:, None] ** 2 + f[None, :] ** 2)
    r[0, 0] = 1.0
    amp = 1.0 / r ** queda
    amp[0, 0] = 0.0
    fase = rng.uniform(0, 2 * np.pi, (lado, lado))
    n = np.real(np.fft.ifft2(amp * np.exp(1j * fase)))
    n -= n.min()
    return n / max(1e-9, n.max())


def textura(tema: str) -> np.ndarray:
    """(L, L, 3) float32 0..255 — a "pele" da névoa desse tema."""
    if tema in _texturas:
        return _texturas[tema]
    e = ESTILOS.get(tema, ESTILOS["medieval"])
    L = LADO_TEXTURA
    claro, escuro = np.array(e["claro"], np.float32), np.array(e["escuro"], np.float32)
    if e["estilo"] == "pergaminho":
        n = _ruido(L, 7, 1.15) * 0.75 + _ruido(L, 8, 0.6) * 0.25          # manchas + grão do papel
        fibra = _ruido(L, 9, 0.35)
        n = np.clip(n * 0.85 + (fibra - 0.5) * 0.18 + 0.1, 0, 1)
        rgb = escuro + (claro - escuro) * n[..., None] ** 0.8
    elif e["estilo"] == "estatica":
        n = _ruido(L, 3, 1.3)
        grao = _ruido(L, 4, 0.1)
        linhas = (np.arange(L) % 4 < 1).astype(np.float32)[:, None]      # varredura
        k = np.clip(n * 0.55 + (grao - 0.5) * 0.5 + 0.15, 0, 1) * (1 - 0.35 * linhas)
        rgb = escuro + (claro - escuro) * k[..., None]
    else:
        n = np.clip(_ruido(L, 11, 1.25) * 0.8 + _ruido(L, 12, 0.8) * 0.2, 0, 1)
        n = n * n * (3 - 2 * n)                                              # nuvem mais "fofa"
        rgb = escuro + (claro - escuro) * n[..., None]
        if e.get("faiscas"):
            rng = np.random.default_rng(5)
            ys, xs = rng.integers(0, L, 70), rng.integers(0, L, 70)
            rgb[ys, xs] = np.array(e["brilho"], np.float32)
    _texturas[tema] = rgb.astype(np.float32)
    return _texturas[tema]


def _irregular(gh: int, gw: int) -> np.ndarray:
    """Ruído pra beirada (repete a cada LADO_TEXTURA da grade): 0..1."""
    n = _ruido(LADO_TEXTURA, 21, 0.95) * 0.7 + _ruido(LADO_TEXTURA, 22, 0.5) * 0.3
    return n[np.arange(gh)[:, None] % LADO_TEXTURA, np.arange(gw)[None, :] % LADO_TEXTURA]


def _borrar(a: np.ndarray, r: int) -> np.ndarray:
    """Borrão de caixa separável (2 passadas ≈ gaussiano), sem scipy."""
    for _ in range(2):
        for eixo in (0, 1):
            c = np.cumsum(np.pad(a, [(r + 1, r) if i == eixo else (0, 0) for i in range(2)], mode="edge"), axis=eixo)
            if eixo == 0:
                a = (c[2 * r + 1:] - c[:-2 * r - 1]) / (2 * r + 1)
            else:
                a = (c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)
    return a


def _cobertura(tela: QImage):
    """A parte coberta (1 = coberto) numa grade de até LADO_MAX, borrada (borda macia). Devolve (cob, k)."""
    w, h = tela.width(), tela.height()
    k = min(1.0, LADO_MAX / max(w, h))
    gw, gh = max(2, int(round(w * k))), max(2, int(round(h * k)))
    from PyQt6.QtCore import Qt
    pequena = tela.scaled(gw, gh, Qt.AspectRatioMode.IgnoreAspectRatio,
                          Qt.TransformationMode.SmoothTransformation).convertToFormat(QImage.Format.Format_ARGB32)
    bits = pequena.constBits()
    bits.setsize(pequena.sizeInBytes())
    arr = np.frombuffer(bits, np.uint8).reshape(gh, pequena.bytesPerLine() // 4, 4)[:, :gw]
    alfa = arr[..., 3].astype(np.float32) / 255.0
    cob = _borrar(1.0 - alfa, max(1, int(round(min(gw, gh) / 160))))
    return np.clip(cob, 0, 1), gw / w


def _camadas(tela: QImage, tema: str):
    """O que não muda com o tempo: alfa da névoa e a borda (cor + alfa)."""
    e = ESTILOS.get(tema, ESTILOS["medieval"])
    cob, k = _cobertura(tela)
    gh, gw = cob.shape
    # a beirada fica IRREGULAR (desfiada/queimada), não um contorno de compasso: empurra a cobertura com ruído,
    # só na faixa de transição (no meio do revelado e no fundo da névoa nada muda)
    irreg = _irregular(gh, gw)
    cob = np.clip(cob + (irreg - 0.5) * 0.9 * (4 * cob * (1 - cob)), 0, 1)
    alfa = np.clip((cob - 0.08) / 0.5, 0, 1)
    alfa = alfa * alfa * (3 - 2 * alfa)
    # borda: uma faixa escura (queimado/fuligem) logo DENTRO da névoa + um fio de brilho na beirada
    faixa = np.exp(-((cob - 0.42) / 0.16) ** 2)
    fio = np.exp(-((cob - 0.2) / 0.06) ** 2)
    ri = irreg
    faixa = faixa * (0.55 + 0.45 * ri)
    fio = fio * (0.35 + 0.65 * ri)
    return dict(alfa=alfa, faixa=faixa, fio=fio, k=k, borda=np.array(e["borda"], np.float32),
                brilho=np.array(e["brilho"], np.float32))


def _compor(c: dict, tema: str, t: float) -> QImage:
    e = ESTILOS.get(tema, ESTILOS["medieval"])
    tex = textura(tema)
    gh, gw = c["alfa"].shape
    vx, vy = e["vel"]
    ox, oy = int(t * vx) % LADO_TEXTURA, int(t * vy) % LADO_TEXTURA
    ys = (np.arange(gh) + oy) % LADO_TEXTURA
    xs = (np.arange(gw) + ox) % LADO_TEXTURA
    rgb = tex[ys[:, None], xs[None, :]]
    if e["estilo"] == "estatica" and t:   # a estática "chia" um pouco
        rgb = rgb * (0.92 + 0.08 * math.sin(t * 7.0))
    f = c["faixa"][..., None] * 0.85
    rgb = rgb * (1 - f) + c["borda"] * f                       # queimado / fuligem
    g = c["fio"][..., None]
    rgb = rgb + c["brilho"] * g * 1.15                          # o fio de brilho na beirada
    a = np.clip(c["alfa"] + c["fio"] * 0.6, 0, 1)
    saida = np.empty((gh, gw, 4), np.uint8)
    saida[..., 0] = np.clip(rgb[..., 2] * a, 0, 255)            # B, G, R pré-multiplicado
    saida[..., 1] = np.clip(rgb[..., 1] * a, 0, 255)
    saida[..., 2] = np.clip(rgb[..., 0] * a, 0, 255)
    saida[..., 3] = np.clip(a * 255, 0, 255)
    return QImage(saida.tobytes(), gw, gh, gw * 4, QImage.Format.Format_ARGB32_Premultiplied).copy()


def imagem(chave_nivel, versao, tela: QImage, tema: str, nivel_graficos: int, t: float):
    """A névoa pronta (QImage) e o fator de escala da grade. None no Baixo."""
    if nivel_graficos <= 0 or tela is None or tela.isNull():
        return None, 1.0
    base = (chave_nivel, versao, tela.width(), tela.height(), tema)
    guardado = _cache.get(chave_nivel)
    if guardado is None or guardado["base"] != base:
        guardado = _cache[chave_nivel] = dict(base=base, camadas=_camadas(tela, tema), quadro=None)
    passo = round(t * 10) / 10 if nivel_graficos >= 2 else 0.0      # Alto: anda (~10 quadros/s)
    if guardado["quadro"] is None or guardado["quadro"][0] != passo:
        guardado["quadro"] = (passo, _compor(guardado["camadas"], tema, passo))
    return guardado["quadro"][1], guardado["camadas"]["k"]


def desenhar(p, chave_nivel, versao, tela: QImage, M: QTransform, tema: str, nivel_graficos: int, t: float) -> bool:
    """Desenha a névoa por cima da imagem do nível (M = imagem → tela). Devolve True se ela anda (pedir repintura)."""
    img, k = imagem(chave_nivel, versao, tela, tema, nivel_graficos, t)
    if img is None:
        return False
    p.setTransform(QTransform().scale(1 / k, 1 / k) * M)
    p.drawImage(0, 0, img)
    p.resetTransform()
    vx, vy = ESTILOS.get(tema, ESTILOS["medieval"])["vel"]
    return nivel_graficos >= 2 and (vx or vy or ESTILOS.get(tema, {}).get("estilo") == "estatica")
