"""
Gerador de texturas naturais (v0.35) — feito com numpy, sem imagem de fora.

Por que existe: as texturas antigas eram desenhadas com formas "perfeitas" (retângulos, degradês)
e tinham uma LUZ PINTADA dentro (sempre de cima-esquerda). Com a mesa 3D e as luzes de verdade,
isso parecia plástico moldado. Aqui:
  - variação natural em várias escalas (ruído fractal), pedras de formato orgânico (Voronoi),
    veio de madeira, ondulação de areia, rachaduras…;
  - NADA de luz pintada: só a cor do material e a sujeira/sombra dentro dos vãos (oclusão);
    o relevo e o brilho vêm só das luzes de verdade (shader do piso, relevo_gl);
  - tudo emenda sem costura (ruído e Voronoi "dão a volta" nas bordas).

1 m = 64 px. Os chãos naturais têm 4×4 m antes de repetir (256 px).
Cada função devolve um array float32 (h, w, 3) com a cor, de 0 a 1.
"""

import numpy as np

# (v0.68) ESCALA do gerador: os chãos saem no DOBRO da resolução (2 px por unidade da cena) com o MESMO desenho —
# as medidas em pixel (células do ruído, das pedras, juntas, tábuas…) são multiplicadas por ESC, e as distâncias do
# Voronoi voltam "em medida de 1×". Só o grão fininho não escala: é ele que vira o detalhe a mais.
ESC = 1.0
ESCALA_CHAO = 2

# ====================================================================== utilidades
def cor(hex_):
    hex_ = hex_.lstrip("#")
    return np.array([int(hex_[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


def misturar(a, b, t):
    """a, b: (…,3) ou cor; t: (…) — mistura com t por pixel."""
    t = np.asarray(t, np.float32)[..., None]
    return a * (1 - t) + b * t


def suave(t):
    return t * t * (3 - 2 * t)


def ruido(w, h, cel, rng, cel_y=None, escalar=True):
    """Ruído de PERLIN periódico (emenda nas bordas), células de ~cel px (cel_y: outra altura de
    célula, pra ruído "esticado" — fios de grama, metal escovado). Saída 0–1.
    (Perlin, não "ruído de valor": o de valor deixava blocos quadrados aparecendo na terra/lama.)"""
    if escalar:
        cel, cel_y = cel * ESC, (cel_y * ESC if cel_y else None)
    gx, gy = max(1, round(w / cel)), max(1, round(h / (cel_y or cel)))
    ang = rng.random((gy, gx)) * 2 * np.pi
    gxv, gyv = np.cos(ang).astype(np.float32), np.sin(ang).astype(np.float32)
    x = np.arange(w, dtype=np.float32) * gx / w
    y = np.arange(h, dtype=np.float32) * gy / h
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    X, Y = np.meshgrid(fx, fy)
    i0, j0 = x0 % gx, y0 % gy
    i1, j1 = (i0 + 1) % gx, (j0 + 1) % gy

    def canto(jj, ii, dx, dy):
        return gxv[jj][:, ii] * dx + gyv[jj][:, ii] * dy

    n00 = canto(j0, i0, X, Y)
    n10 = canto(j0, i1, X - 1, Y)
    n01 = canto(j1, i0, X, Y - 1)
    n11 = canto(j1, i1, X - 1, Y - 1)
    u = X * X * X * (X * (X * 6 - 15) + 10)
    v = Y * Y * Y * (Y * (Y * 6 - 15) + 10)
    a = n00 + (n10 - n00) * u
    b = n01 + (n11 - n01) * u
    return np.clip((a + (b - a) * v) * 0.72 + 0.5, 0, 1)


def fbm(w, h, rng, oitavas, escalar=True):
    """Soma de ruídos: oitavas = [(célula, peso), …]. Saída normalizada 0–1."""
    total = np.zeros((h, w), np.float32)
    soma = 0.0
    for cel, peso in oitavas:
        total += ruido(w, h, cel, rng, escalar=escalar) * peso
        soma += peso
    total /= soma
    lo, hi = total.min(), total.max()
    return (total - lo) / max(1e-6, hi - lo)


def sulcos(campo, largura=0.04):
    """Linhas finas onde o campo cruza 0,5 (rachaduras, veios): 1 na linha, 0 longe."""
    return np.clip(1 - np.abs(campo - 0.5) / largura, 0, 1)


def voronoi(w, h, pontos):
    """Voronoi PERIÓDICO. Devolve (d1, d2, id) — distância ao 1º e 2º ponto mais perto e o índice.
    (v0.68) As distâncias voltam em medida de 1× (divididas por ESC) e a conta é feita em faixas de linhas
    (no dobro da resolução, de uma vez só, passava de meio giga de memória)."""
    px = pontos[:, 0][None, None, :]
    py = pontos[:, 1][None, None, :]
    xs = np.arange(w, dtype=np.float32)[None, :, None]
    D1 = np.empty((h, w), np.float32)
    D2 = np.empty((h, w), np.float32)
    I1 = np.empty((h, w), int)
    passo = max(1, int(4_000_000 // max(1, w * len(pontos))))
    for y0 in range(0, h, passo):
        ys = np.arange(y0, min(h, y0 + passo), dtype=np.float32)[:, None, None]
        dx = np.abs(xs - px)
        dy = np.abs(ys - py)
        dx = np.minimum(dx, w - dx)
        dy = np.minimum(dy, h - dy)
        d = np.sqrt(dx * dx + dy * dy)
        ordem = np.argpartition(d, 1, axis=2)[..., :2]
        d1 = np.take_along_axis(d, ordem[..., :1], 2)[..., 0]
        d2 = np.take_along_axis(d, ordem[..., 1:2], 2)[..., 0]
        troca = d1 > d2
        I1[y0:y0 + passo] = np.where(troca, ordem[..., 1], ordem[..., 0])
        D1[y0:y0 + passo] = np.minimum(d1, d2) / ESC
        D2[y0:y0 + passo] = np.maximum(d1, d2) / ESC
    return D1, D2, I1


def grade_tremida(w, h, cel, tremor, rng):
    """Pontos numa grade com tremidinha (pedras de tamanho parecido, formato orgânico)."""
    cel = cel * ESC
    nx, ny = max(2, round(w / cel)), max(2, round(h / cel))   # (o Voronoi precisa de 2+ pontos)
    pts = []
    for j in range(ny):
        for i in range(nx):
            pts.append(((i + 0.5 + rng.uniform(-tremor, tremor)) * w / nx,
                        (j + 0.5 + rng.uniform(-tremor, tremor)) * h / ny))
    return np.array(pts, np.float32) % np.array([w, h], np.float32)


def borrar(a, raio):
    s = a.astype(np.float32).copy()
    for eixo in (0, 1):
        acum = s.copy()
        for k in range(1, raio + 1):
            acum += np.roll(s, k, eixo) + np.roll(s, -k, eixo)
        s = acum / (2 * raio + 1)
    return s


def oclusao(altura, forca=0.5, raio=3):
    """Sombra nos vãos (o que está abaixo da vizinhança escurece). Sem direção de luz. 1 = sem sombra."""
    cav = np.clip((borrar(altura, max(1, int(round(raio * ESC)))) - altura) * 6.0, 0, 1)
    return 1 - cav * forca


def paleta_por_id(ids, cores, rng, variacao=0.06):
    """Uma cor (da lista) pra cada pedra/tábua/tijolo, com uma variaçãozinha de brilho."""
    n = int(ids.max()) + 1
    escolha = np.array([cores[rng.integers(len(cores))] for _ in range(n)], np.float32)
    escolha *= (1 + rng.uniform(-variacao, variacao, (n, 1))).astype(np.float32)
    return escolha[ids]


def grao(w, h, rng, forca=0.08):
    """Grão fininho multiplicativo (1 ± forca)."""
    return 1 + (fbm(w, h, rng, [(2, 1.0), (4, 0.6)], escalar=False) - 0.5) * 2 * forca   # (detalhe a mais no 2×)


# ====================================================================== pedras e afins
def _pedras(w, h, rng, cel, tremor, cores, argamassa, junta=2.0, gasto=5.0, manchas=0.22):
    pts = grade_tremida(w, h, cel, tremor, rng)
    d1, d2, ids = voronoi(w, h, pts)
    borda = d2 - d1                                   # 0 na junta
    dentro = np.clip((borda - junta * 0.5) / junta, 0, 1)
    base = paleta_por_id(ids, [cor(c) for c in cores], rng)
    mancha = fbm(w, h, rng, [(64, 1.0), (24, 0.6), (10, 0.3)])
    base = base * (1 - manchas + manchas * 1.6 * mancha)[..., None]
    base = base * (0.9 + 0.1 * np.clip(borda / gasto, 0, 1))[..., None]   # beira gasta, mais escura
    base = base * grao(w, h, rng, 0.09)[..., None]
    arg = cor(argamassa) * grao(w, h, rng, 0.18)[..., None]
    final = misturar(arg, base, dentro)
    altura = dentro * (0.8 + 0.2 * mancha)
    return final * oclusao(altura, 0.55)[..., None]


def chao_pedra(w, h, rng):
    return _pedras(w, h, rng, 32, 0.32, ["#7e7870", "#8a847a", "#6f6a63", "#938c81", "#78726a", "#857c70"], "#3a352f")


def chao_paralelepipedo(w, h, rng):
    return _pedras(w, h, rng, 17, 0.28, ["#5c5a57", "#67635d", "#53514e", "#6d6862", "#5f5a52"], "#2e2a25",
                   junta=1.6, gasto=4.0)


def chao_cascalho(w, h, rng):
    terra = cor("#4e463c") * grao(w, h, rng, 0.2)[..., None]
    pts = (rng.random((int(w * h // (70 * ESC * ESC)), 2)) * [w, h]).astype(np.float32)
    d1, d2, ids = voronoi(w, h, pts)
    pedra = np.clip((d2 - d1 - 0.8) / 1.4, 0, 1) * np.clip(1 - d1 / 4.5, 0, 1)
    cores = paleta_por_id(ids, [cor(c) for c in ("#8a857c", "#6f6a62", "#9a948a", "#5d5953", "#7d776c")], rng, 0.1)
    final = misturar(terra, cores * grao(w, h, rng, 0.1)[..., None], np.clip(pedra * 1.6, 0, 1))
    return final * oclusao(pedra, 0.5, 2)[..., None]


def fissuras(w, h, rng, n, largura=1.3):
    """Rachaduras de verdade: as bordas de um Voronoi com poucos pontos, tortas pelo ruído."""
    torto = (fbm(w, h, rng, [(24, 1.0), (9, 0.5)]) - 0.5) * 10
    pts = (rng.random((n, 2)) * [w, h]).astype(np.float32)
    d1, d2, _ = voronoi(w, h, pts)
    return np.clip(1 - (d2 - d1 + torto * 0.15) / largura, 0, 1) * (fbm(w, h, rng, [(40, 1.0)]) > 0.35)


def chao_rocha_caverna(w, h, rng):
    alt = fbm(w, h, rng, [(96, 1.0), (40, 0.6), (14, 0.35), (5, 0.15)])
    racha = fissuras(w, h, rng, max(4, int(w * h // (5000 * ESC * ESC))))
    base = misturar(cor("#3a3631"), cor("#5e574e"), alt)
    base = base * grao(w, h, rng, 0.1)[..., None]
    base = base * (1 - racha * 0.6)[..., None]
    return base * oclusao(alt - racha * 0.3, 0.45, 4)[..., None]


def chao_obsidiana(w, h, rng):
    pts = grade_tremida(w, h, 48, 0.4, rng)
    d1, d2, ids = voronoi(w, h, pts)
    faceta = fbm(w, h, rng, [(48, 1.0), (16, 0.4)])
    base = misturar(cor("#0d0b11"), cor("#2a2236"), faceta * 0.7)
    brilho = np.clip(1 - (d2 - d1) / 1.5, 0, 1)     # quina vítrea fininha
    base = base + brilho[..., None] * cor("#5a4f73") * 0.6
    return base * grao(w, h, rng, 0.05)[..., None]


def chao_marmore_branco(w, h, rng):
    campo = fbm(w, h, rng, [(128, 1.0), (48, 0.5), (16, 0.25)])
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    veio = np.abs(np.sin((xs + ys) * (2 * np.pi * 2 / w) + campo * 7.0))
    veio = np.clip(1 - veio / 0.16, 0, 1) ** 1.3
    fino = sulcos(fbm(w, h, rng, [(40, 1.0), (14, 0.5)]), 0.012)
    base = misturar(cor("#ece8e0"), cor("#d8d2c6"), fbm(w, h, rng, [(80, 1.0), (20, 0.4)]))
    base = misturar(base, cor("#8c877e"), np.clip(veio * 0.8 + fino * 0.45, 0, 1))
    # placas de 1 m com rejunte fininho
    jx = (xs % (64 * ESC) < ESC) | (ys % (64 * ESC) < ESC)
    base = np.where(jx[..., None], base * 0.78, base)
    return base * grao(w, h, rng, 0.03)[..., None]


def chao_ceramica(w, h, rng):
    lado = int(32 * ESC)
    ys, xs = np.mgrid[0:h, 0:w]
    ids = (ys // lado) * (w // lado) + (xs // lado)
    cores = paleta_por_id(ids, [cor(c) for c in ("#a49d92", "#9a938a", "#ada597", "#968f84")], rng, 0.04)
    esmalte = fbm(w, h, rng, [(32, 1.0), (8, 0.4)])
    base = cores * (0.94 + 0.12 * esmalte)[..., None]
    jx = np.minimum(xs % lado, lado - 1 - xs % lado)
    jy = np.minimum(ys % lado, lado - 1 - ys % lado)
    junta = np.clip(np.minimum(jx, jy) / (1.5 * ESC), 0, 1)
    final = misturar(cor("#6e685f") * grao(w, h, rng, 0.15)[..., None], base, junta)
    return final * oclusao(junta.astype(np.float32), 0.35, 2)[..., None]


def chao_ouro(w, h, rng):
    fundo = cor("#3a2a0c") * grao(w, h, rng, 0.3)[..., None]
    pts = (rng.random((420, 2)) * [w, h]).astype(np.float32)
    d1, d2, ids = voronoi(w, h, pts)
    raio = 5.5
    moeda = np.clip((raio - d1) / 1.2, 0, 1)
    aro = np.clip(1 - np.abs(d1 - (raio - 1.3)) / 0.8, 0, 1)
    tons = paleta_por_id(ids, [cor(c) for c in ("#d9ae45", "#c99a32", "#e8c25a", "#b8892a")], rng, 0.08)
    moedas = tons * (1 - aro * 0.35)[..., None]
    return misturar(fundo, moedas, moeda) * oclusao(moeda, 0.45, 2)[..., None]


# ====================================================================== terrenos naturais
def chao_terra(w, h, rng):
    alt = fbm(w, h, rng, [(80, 1.0), (28, 0.6), (9, 0.35), (3, 0.2)])
    base = misturar(cor("#4a3524"), cor("#7a5a3c"), alt)
    umido = fbm(w, h, rng, [(100, 1.0), (40, 0.4)])
    base = base * (1 - np.clip((umido - 0.6) * 1.6, 0, 0.3))[..., None]
    pts = (rng.random((140, 2)) * [w, h]).astype(np.float32)
    d1, _, ids = voronoi(w, h, pts)
    tem = (rng.random(len(pts)) < 0.5).astype(np.float32)[ids]     # metade dos pontos vira pedrinha
    pedrinha = np.clip((2.4 - d1) / 0.8, 0, 1) * tem
    base = misturar(base, cor("#8a8378") * grao(w, h, rng, 0.1)[..., None], pedrinha)
    return base * grao(w, h, rng, 0.1)[..., None]


def chao_lama(w, h, rng):
    alt = fbm(w, h, rng, [(90, 1.0), (30, 0.5), (8, 0.3)])
    base = misturar(cor("#2e2216"), cor("#5a4430"), alt)
    poca = np.clip((fbm(w, h, rng, [(110, 1.0), (40, 0.5)]) - 0.62) * 4, 0, 1)
    base = misturar(base, cor("#241a10"), poca * 0.8)
    return base * grao(w, h, rng, 0.07)[..., None]


def chao_areia(w, h, rng):
    campo = fbm(w, h, rng, [(128, 1.0), (40, 0.4)])
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    onda = np.sin(ys * (2 * np.pi * 10 / h) + campo * 6.0 + xs * (2 * np.pi * 1 / w)) * 0.5 + 0.5
    base = misturar(cor("#b89a64"), cor("#ddc58f"), campo * 0.6 + onda * 0.4)
    pontos = fbm(w, h, rng, [(2, 1.0)])
    base = base * (1 + (pontos - 0.5) * 0.16)[..., None]
    return base


def chao_grama(w, h, rng):
    base = misturar(cor("#2f5220"), cor("#5d8a3a"), fbm(w, h, rng, [(90, 1.0), (30, 0.6), (10, 0.3)]))
    # folhinhas: ruído esticado na vertical (fios finos e compridos), em três tamanhos
    fios = (ruido(w, h, 2, rng, 7) * 1.0 + ruido(w, h, 3, rng, 10) * 0.7 + ruido(w, h, 2, rng, 5) * 0.6) / 2.3
    base = base * (0.75 + 0.45 * fios)[..., None]
    tufo = fbm(w, h, rng, [(24, 1.0), (8, 0.5)])
    base = base * (0.85 + 0.25 * tufo)[..., None]
    flor = (rng.random((h, w)) > 0.9985).astype(np.float32)
    flor = np.maximum(flor, np.roll(flor, 1, 0) * 0.6)
    base = misturar(base, cor("#efe6a0"), flor * 0.8)
    return base


def chao_neve(w, h, rng):
    base = misturar(cor("#dfe7ef"), cor("#f7fafc"), fbm(w, h, rng, [(100, 1.0), (30, 0.5), (8, 0.2)]))
    brilho = (rng.random((h, w)) > 0.997).astype(np.float32)
    return np.clip(base + brilho[..., None] * 0.25, 0, 1)


def chao_gelo(w, h, rng):
    nuvem = fbm(w, h, rng, [(110, 1.0), (40, 0.6), (12, 0.25)])
    base = misturar(cor("#7fb8d4"), cor("#d4eef8"), nuvem)
    racha = sulcos(fbm(w, h, rng, [(60, 1.0), (24, 0.4)]), 0.015)
    racha2 = sulcos(fbm(w, h, rng, [(90, 1.0), (30, 0.5)]), 0.01)
    base = misturar(base, cor("#f4fbff"), np.clip(racha + racha2 * 0.7, 0, 1) * 0.8)
    funda = np.clip((0.35 - nuvem) * 3, 0, 1)
    return misturar(base, cor("#4d87a8"), funda * 0.5)


def chao_agua(w, h, rng):
    campo = fbm(w, h, rng, [(90, 1.0), (32, 0.6)])
    base = misturar(cor("#1d4a66"), cor("#2f6f8f"), campo)
    c1 = sulcos(fbm(w, h, rng, [(40, 1.0), (16, 0.4)]), 0.05)
    c2 = sulcos(fbm(w, h, rng, [(28, 1.0), (12, 0.4)]), 0.04)
    caustica = np.clip(c1 * 0.7 + c2 * 0.5, 0, 1)
    return np.clip(base + caustica[..., None] * cor("#7fd0e8") * 0.35, 0, 1)


def chao_pantano(w, h, rng):
    agua = misturar(cor("#1d2616"), cor("#34402a"), fbm(w, h, rng, [(80, 1.0), (24, 0.5)]))
    alga = np.clip((fbm(w, h, rng, [(60, 1.0), (20, 0.6), (7, 0.3)]) - 0.55) * 4, 0, 1)
    base = misturar(agua, cor("#4c6a2a") * grao(w, h, rng, 0.2)[..., None], alga)
    lentilha = (rng.random((h, w)) > 0.993).astype(np.float32) * (1 - alga)
    return misturar(base, cor("#7ba040"), lentilha * 0.8)


def chao_lava(w, h, rng):
    crosta = fbm(w, h, rng, [(70, 1.0), (24, 0.5), (8, 0.25)])
    pts = grade_tremida(w, h, 40, 0.45, rng)
    d1, d2, _ = voronoi(w, h, pts)
    fenda = np.clip(1 - (d2 - d1) / 5.0, 0, 1) ** 1.5
    calor = np.clip(fenda + np.clip((0.3 - crosta) * 3, 0, 1), 0, 1)
    pedra = misturar(cor("#1a100c"), cor("#3a2418"), crosta)
    brasa = misturar(cor("#c8320c"), cor("#ffd060"), calor ** 2)
    return misturar(pedra, brasa, calor)


def chao_acido(w, h, rng):
    campo = fbm(w, h, rng, [(70, 1.0), (24, 0.5)])
    base = misturar(cor("#3f7a10"), cor("#9be02e"), campo)
    pts = (rng.random((70, 2)) * [w, h]).astype(np.float32)
    d1, _, _ = voronoi(w, h, pts)
    bolha = np.clip(1 - np.abs(d1 - 4.0) / 1.0, 0, 1)
    return np.clip(base + bolha[..., None] * cor("#d8ff8a") * 0.5, 0, 1)


# ====================================================================== madeira, concreto, metal
def _tabuas(w, h, rng, alt_tabua, cores, junta_cor, velho=False):
    alt_tabua = int(alt_tabua * ESC)
    linhas = h // alt_tabua
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    linha = (ys // alt_tabua).astype(int)
    y_dentro = ys - linha * alt_tabua
    final = np.zeros((h, w, 3), np.float32)
    ids = np.zeros((h, w), int)
    proximo = 0
    for k in range(linhas):
        # emendas das pontas: comprimentos 1,5–3 m, posição sorteada; a tábua "dá a volta"
        cortes = []
        x = rng.uniform(0, w)
        while len(cortes) < 6:
            cortes.append(x % w)
            x += rng.uniform(96, 190) * ESC
            if x - cortes[0] >= w - 40 * ESC:
                break
        cortes = sorted(cortes)
        sel = linha == k
        idx = np.searchsorted(cortes, xs[sel]) % max(1, len(cortes))
        ids[sel] = proximo + idx
        proximo += len(cortes)
    base = paleta_por_id(ids, [cor(c) for c in cores], rng, 0.07)
    # veio: linhas ao longo da tábua, onduladas pelo ruído
    torce = fbm(w, h, rng, [(64, 1.0), (24, 0.5)])
    veio = np.sin((y_dentro / ESC + torce * 9.0 + (ids % 7) * 1.7) * 1.9) * 0.5 + 0.5
    veio2 = fbm(w, h, rng, [(48, 1.0)])
    base = base * (0.86 + 0.14 * veio)[..., None] * (0.92 + 0.12 * veio2)[..., None]
    # nós (raros)
    for _ in range(int(w * h / (9000 * ESC * ESC))):
        cx, cy = rng.uniform(0, w), rng.uniform(0, h)
        dx = np.minimum(np.abs(xs - cx), w - np.abs(xs - cx))
        dy = np.minimum(np.abs(ys - cy), h - np.abs(ys - cy))
        d = np.sqrt((dx / 1.8) ** 2 + dy ** 2) / ESC
        base = base * (1 - np.clip(1 - d / 4.0, 0, 1) * 0.45)[..., None]
    # juntas: entre linhas e nas emendas
    jy = np.minimum(y_dentro, alt_tabua - 1 - y_dentro)
    emenda = np.zeros((h, w), bool)
    emenda[:, 1:] = ids[:, 1:] != ids[:, :-1]
    emenda |= np.roll(emenda, 1, 1)
    junta = np.clip(jy / ((1.4 if velho else 0.9) * ESC), 0, 1) * np.where(emenda, 0.0, 1.0)
    final = misturar(cor(junta_cor), base * grao(w, h, rng, 0.06)[..., None], junta)
    if velho:   # tábua velha: acinzentada e com pregos
        cinza = fbm(w, h, rng, [(60, 1.0), (20, 0.5)])
        final = misturar(final, final.mean(axis=2, keepdims=True) * cor("#c8c0b4"), cinza * 0.35)
    return final * oclusao(junta.astype(np.float32), 0.4, 2)[..., None]


def chao_madeira(w, h, rng):
    return _tabuas(w, h, rng, 16, ["#7a5232", "#6b4529", "#86603c", "#734b2d", "#8f673f"], "#2b1b10")


def chao_tabuas_velhas(w, h, rng):
    return _tabuas(w, h, rng, 16, ["#5a3e26", "#4d3420", "#664a30", "#574029"], "#160d07", velho=True)


def chao_concreto(w, h, rng):
    base = misturar(cor("#7e7c77"), cor("#a19e97"), fbm(w, h, rng, [(90, 1.0), (30, 0.5), (8, 0.3)]))
    poro = (rng.random((h, w)) > 0.985).astype(np.float32)
    racha = sulcos(fbm(w, h, rng, [(80, 1.0), (30, 0.4)]), 0.008)
    mancha = np.clip((fbm(w, h, rng, [(70, 1.0), (24, 0.4)]) - 0.6) * 2.5, 0, 1)
    base = base * (1 - poro * 0.25 - racha * 0.35 - mancha * 0.12)[..., None]
    return base * grao(w, h, rng, 0.07)[..., None]


def chao_asfalto(w, h, rng):
    base = misturar(cor("#2c2c30"), cor("#45454a"), fbm(w, h, rng, [(80, 1.0), (24, 0.5), (6, 0.3)]))
    brita = (rng.random((h, w)) > 0.93).astype(np.float32) * rng.uniform(0.1, 0.3, (h, w)).astype(np.float32)
    return np.clip(base + brita[..., None] * 0.6, 0, 1) * grao(w, h, rng, 0.06)[..., None]


def chao_sangue(w, h, rng):
    base = chao_concreto(w, h, rng)
    sangue = np.clip((fbm(w, h, rng, [(60, 1.0), (20, 0.6), (6, 0.3)]) - 0.64) * 5, 0, 1)
    respingo = (rng.random((h, w)) > 0.996).astype(np.float32)
    respingo = np.clip(respingo + np.roll(respingo, 1, 0) + np.roll(respingo, 1, 1), 0, 1)
    return misturar(base, cor("#5e0a0e") * grao(w, h, rng, 0.2)[..., None], np.clip(sangue + respingo, 0, 1) * 0.9)


def _placas(w, h, rng, lado, base_cor, enferrujar=0.0):
    lado = int(lado * ESC)
    ys, xs = np.mgrid[0:h, 0:w]
    ids = (ys // lado) * (w // lado) + (xs // lado)
    base = paleta_por_id(ids, [cor(base_cor)], rng, 0.05)
    # metal escovado: riscos finos numa direção (horizontal ou vertical, alternando por placa)
    horiz = ruido(w, h, 24, rng, 1)        # esticado na horizontal
    vert = ruido(w, h, 1, rng, 24)         # esticado na vertical
    linhas = np.where(((ys // lado + xs // lado) % 2) == 0, horiz, vert)
    base = base * (0.9 + 0.2 * linhas)[..., None]
    risco = sulcos(fbm(w, h, rng, [(30, 1.0), (10, 0.5)]), 0.01)
    base = base * (1 + risco * 0.18)[..., None]
    jx = np.minimum(xs % lado, lado - 1 - xs % lado)
    jy = np.minimum(ys % lado, lado - 1 - ys % lado)
    junta = np.clip(np.minimum(jx, jy) / (1.2 * ESC), 0, 1)
    # rebites nos cantos
    rx = np.minimum(np.abs(xs % lado - 4 * ESC), np.abs(xs % lado - (lado - 5 * ESC)))
    ry = np.minimum(np.abs(ys % lado - 4 * ESC), np.abs(ys % lado - (lado - 5 * ESC)))
    rebite = np.clip((1.8 * ESC - np.sqrt(rx ** 2 + ry ** 2)) / ESC, 0, 1)
    base = misturar(base, base * 1.25, rebite)
    if enferrujar:
        ferrugem = np.clip((fbm(w, h, rng, [(40, 1.0), (14, 0.6), (5, 0.3)]) - (0.62 - enferrujar * 0.3)) * 3, 0, 1)
        tom = misturar(cor("#5a2e14"), cor("#a85a24"), fbm(w, h, rng, [(8, 1.0), (3, 0.5)]))
        base = misturar(base, tom, ferrugem)
    final = misturar(cor("#1c1f24"), base, junta)
    return final * oclusao(junta.astype(np.float32), 0.35, 2)[..., None]


def chao_placa_metal(w, h, rng):
    return _placas(w, h, rng, 64, "#6a727b")


def chao_metal_enferrujado(w, h, rng):
    return _placas(w, h, rng, 64, "#5d646c", enferrujar=0.6)


# ====================================================================== paredes: TOPO (visto de cima, 64×12)
def topo_pedra(w, h, rng):
    return _pedras(w, h, rng, 12, 0.25, ["#8a857d", "#7b766f", "#958f86", "#837d74"], "#3a3530", junta=1.2, gasto=3)


def topo_tijolo(w, h, rng):
    return _tijolos(w, h, rng, 16, 6, ["#8a4a34", "#7a3e2b", "#94553b", "#6f3a28"], "#4a3e33")


def topo_madeira(w, h, rng):
    return _tabuas(w, h, rng, 6, ["#5a3a22", "#4c311c", "#654328"], "#1a0f08")


def topo_rocha(w, h, rng):
    return chao_rocha_caverna(w, h, rng) * 0.9


def topo_concreto(w, h, rng):
    return chao_concreto(w, h, rng)


def topo_gesso(w, h, rng):
    base = misturar(cor("#cfc8b8"), cor("#e2dccd"), fbm(w, h, rng, [(24, 1.0), (6, 0.4)]))
    return base * grao(w, h, rng, 0.04)[..., None]


def topo_ferro(w, h, rng):
    return _placas(w, h, rng, 32 if w >= 32 else w, "#5c636b")


def topo_enferrujado(w, h, rng):
    return _placas(w, h, rng, 32 if w >= 32 else w, "#5a5048", enferrujar=0.8)


def topo_palicada(w, h, rng):
    """De cima: as pontas dos troncos (círculos com anéis), lado a lado."""
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    raio = h / 2
    cx = (np.floor(xs / h) + 0.5) * h
    d = np.sqrt((xs - cx) ** 2 + (ys - h / 2) ** 2)
    tronco = np.clip((raio - d) / 0.8, 0, 1)
    aneis = np.sin(d * 2.4) * 0.5 + 0.5
    madeira = misturar(cor("#6b4a2a"), cor("#8a6440"), aneis * 0.6) * grao(w, h, rng, 0.08)[..., None]
    casca = cor("#3a2614")
    final = misturar(casca, madeira, np.clip((raio - 1.6 - d) / 0.8, 0, 1))
    return misturar(cor("#1a1008"), final, tronco)


# ====================================================================== paredes: FACE (vista de frente, 64×64)
def _tijolos(w, h, rng, comp, alt, cores, argamassa):
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    fiada = (ys // alt).astype(int)
    desloc = (fiada % 2) * comp / 2
    col = ((xs + desloc) // comp).astype(int) % max(1, w // comp)
    ids = fiada * 1000 + col
    _, ids = np.unique(ids, return_inverse=True)
    ids = ids.reshape(h, w)
    base = paleta_por_id(ids, [cor(c) for c in cores], rng, 0.08)
    base = base * (0.88 + 0.22 * fbm(w, h, rng, [(16, 1.0), (5, 0.5)]))[..., None]
    ux = (xs + desloc) % comp
    uy = ys % alt
    junta = np.clip(np.minimum(np.minimum(ux, comp - 1 - ux), np.minimum(uy, alt - 1 - uy)) / 1.0, 0, 1)
    final = misturar(cor(argamassa) * grao(w, h, rng, 0.15)[..., None], base * grao(w, h, rng, 0.08)[..., None], junta)
    return final * oclusao(junta.astype(np.float32), 0.45, 2)[..., None]


def face_tijolo(w, h, rng):
    return _tijolos(w, h, rng, 22, 8, ["#8a4a34", "#7a3e2b", "#94553b", "#6f3a28", "#844630"], "#5a4e42")


def face_pedra(w, h, rng):
    """Fiadas de blocos de pedra de alturas diferentes (aparelho irregular)."""
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    alturas = []
    y = 0
    while y < h:
        a = int(rng.integers(12, 20))
        alturas.append((y, min(h, y + a)))
        y += a
    ids = np.zeros((h, w), int)
    junta = np.ones((h, w), np.float32)
    proximo = 0
    for (y0, y1) in alturas:
        x = rng.uniform(0, 20)
        cortes = []
        while x < w + 20:
            cortes.append(x % w)
            x += rng.uniform(16, 30)
        cortes = sorted(set(round(c, 1) for c in cortes))
        sel = (ys >= y0) & (ys < y1)
        idx = np.searchsorted(cortes, xs[sel]) % len(cortes)
        ids[sel] = proximo + idx
        proximo += len(cortes)
        junta[sel] = np.minimum(junta[sel], np.clip(np.minimum(ys[sel] - y0, y1 - 1 - ys[sel]) / 1.2, 0, 1))
        for c in cortes:
            dx = np.abs(xs[sel] - c)
            dx = np.minimum(dx, w - dx)
            junta[sel] = np.minimum(junta[sel], np.clip(dx / 1.2, 0, 1))
    base = paleta_por_id(ids, [cor(c) for c in ("#8a857d", "#7b766f", "#958f86", "#837d74", "#706a63")], rng, 0.08)
    base = base * (0.84 + 0.3 * fbm(w, h, rng, [(24, 1.0), (8, 0.5), (3, 0.25)]))[..., None]
    final = misturar(cor("#3a3530") * grao(w, h, rng, 0.15)[..., None], base, junta)
    return final * oclusao(junta, 0.5, 2)[..., None]


def face_madeira(w, h, rng):
    return _tabuas(w, h, rng, 16, ["#5a3a22", "#4c311c", "#654328", "#523620"], "#1a0f08")


def face_palicada(w, h, rng):
    """De frente: troncos em pé, roliços (mais claro no meio, escuro nas bordas)."""
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    larg = 12
    u = (xs % larg) / larg
    rolico = np.sin(u * np.pi) ** 0.6
    ids = (xs // larg).astype(int)
    base = paleta_por_id(ids, [cor(c) for c in ("#5a3c20", "#6b4a2a", "#4e331b")], rng, 0.08)
    casca = fbm(w, h, rng, [(3, 1.0), (8, 0.5)])
    estrias = ruido(w, h, 2, rng)
    base = base * (0.55 + 0.55 * rolico)[..., None] * (0.85 + 0.25 * casca)[..., None]
    base = base * (0.9 + 0.15 * borrar(estrias, 0))[..., None]
    return base


def face_rocha(w, h, rng):
    alt = fbm(w, h, rng, [(32, 1.0), (16, 0.6), (6, 0.35), (3, 0.15)])
    racha = fissuras(w, h, rng, 5, 1.0)
    base = misturar(cor("#332f2a"), cor("#5a534a"), alt) * grao(w, h, rng, 0.1)[..., None]
    base = base * (1 - racha * 0.55)[..., None]
    return base * oclusao(alt - racha * 0.3, 0.45, 3)[..., None]


def face_concreto(w, h, rng):
    base = chao_concreto(w, h, rng)
    ys = np.mgrid[0:h, 0:w][0]
    forma = ((ys % 32) < 1).astype(np.float32)   # marca das fôrmas
    return base * (1 - forma * 0.2)[..., None]


def face_gesso(w, h, rng):
    return topo_gesso(w, h, rng)


def face_ferro(w, h, rng):
    return _placas(w, h, rng, 32, "#5c636b")


def face_enferrujado(w, h, rng):
    return _placas(w, h, rng, 32, "#5a5048", enferrujar=0.8)


def chao_carpete(w, h, rng):
    """Tecido: trama fininha (fios nas duas direções), partes gastas e um tom que varia."""
    trama = (ruido(w, h, 1, rng, 3) + ruido(w, h, 3, rng, 1)) / 2
    base = misturar(cor("#5a242a"), cor("#7a343b"), fbm(w, h, rng, [(80, 1.0), (24, 0.5)]))
    gasto = np.clip((fbm(w, h, rng, [(60, 1.0), (20, 0.5)]) - 0.6) * 2, 0, 1)
    base = base * (0.85 + 0.25 * trama)[..., None]
    return misturar(base, base * 1.18 + 0.03, gasto * 0.6)


def face_sebe(w, h, rng):
    """Arbusto podado: folhagem densa, com buracos escuros e folhas claras."""
    folhas = fbm(w, h, rng, [(12, 1.0), (5, 0.7), (2, 0.4)])
    base = misturar(cor("#14290f"), cor("#4c7a30"), folhas)
    clara = np.clip((ruido(w, h, 2, rng, 3) - 0.72) * 5, 0, 1)
    return misturar(base, cor("#6f9a46"), clara * 0.6) * oclusao(folhas, 0.5, 2)[..., None]


def face_gelo(w, h, rng):
    return chao_gelo(w, h, rng)


def face_obsidiana(w, h, rng):
    return chao_obsidiana(w, h, rng)


# ====================================================================== registro
# chave: (função, tamanho em px)
CHAOS = {
    "pedra": (chao_pedra, 256), "paralelepipedo": (chao_paralelepipedo, 256), "cascalho": (chao_cascalho, 128),
    "rocha_caverna": (chao_rocha_caverna, 256), "obsidiana": (chao_obsidiana, 256),
    "marmore_branco": (chao_marmore_branco, 256), "ceramica": (chao_ceramica, 128), "ouro": (chao_ouro, 192),
    "terra": (chao_terra, 256), "lama": (chao_lama, 256), "areia": (chao_areia, 256), "grama": (chao_grama, 256),
    "neve": (chao_neve, 256), "gelo": (chao_gelo, 256), "agua": (chao_agua, 256), "pantano": (chao_pantano, 256),
    "lava": (chao_lava, 256), "acido": (chao_acido, 256), "madeira": (chao_madeira, 256),
    "tabuas_velhas": (chao_tabuas_velhas, 256), "concreto": (chao_concreto, 256), "asfalto": (chao_asfalto, 256),
    "sangue": (chao_sangue, 256), "placa_metal": (chao_placa_metal, 128),
    "metal_enferrujado": (chao_metal_enferrujado, 128), "carpete": (chao_carpete, 256),
}
TOPOS = {
    "pedra": topo_pedra, "tijolo": topo_tijolo, "madeira": topo_madeira, "rocha": topo_rocha,
    "concreto": topo_concreto, "gesso": topo_gesso, "ferro": topo_ferro, "metal": topo_ferro,
    "enferrujado": topo_enferrujado, "palicada": topo_palicada,
}
FACES = {
    "pedra": face_pedra, "tijolo": face_tijolo, "madeira": face_madeira, "rocha": face_rocha,
    "concreto": face_concreto, "gesso": face_gesso, "ferro": face_ferro, "metal": face_ferro,
    "enferrujado": face_enferrujado, "palicada": face_palicada, "sebe": face_sebe, "gelo": face_gelo,
    "obsidiana": face_obsidiana,
}


def para_imagem(arr):
    """Array (h, w, 3) 0–1 → QImage."""
    from PyQt6.QtGui import QImage
    h, w = arr.shape[:2]
    rgba = np.empty((h, w, 4), np.uint8)
    rgba[..., :3] = np.clip(arr * 255, 0, 255)
    rgba[..., 3] = 255
    return QImage(rgba.tobytes(), w, h, w * 4, QImage.Format.Format_RGBA8888).copy()


def _semente(chave):
    import zlib
    return np.random.default_rng(zlib.crc32(chave.encode()))


def gerar(tipo: str, chave: str, larg_parede: int = 64, esp_parede: int = 12):
    """QImage da textura nova, ou None se esse material ainda usa o desenho antigo."""
    if tipo == "chao" and chave in CHAOS:
        global ESC
        f, tam = CHAOS[chave]
        ESC = float(ESCALA_CHAO)   # (v0.68) no dobro da resolução, com o mesmo desenho
        try:
            return para_imagem(f(tam * ESCALA_CHAO, tam * ESCALA_CHAO, _semente("chao:" + chave)))
        finally:
            ESC = 1.0
    if tipo == "parede" and chave in TOPOS:
        return para_imagem(TOPOS[chave](larg_parede, esp_parede, _semente("topo:" + chave)))
    if tipo == "parede_face" and chave in FACES:
        return para_imagem(FACES[chave](64, 64, _semente("face:" + chave)))
    return None


def acabamento(img):
    """Pros materiais que continuam com o desenho antigo (runas, neon, xadrez…): tira nada de luz
    (eles não têm mais a luz pintada) e põe só grão natural e sombra nos vãos."""
    from PyQt6.QtGui import QImage
    img = img.convertToFormat(QImage.Format.Format_RGBA8888)
    w, h = img.width(), img.height()
    ptr = img.constBits()
    ptr.setsize(img.sizeInBytes())
    arr = np.frombuffer(ptr, np.uint8).reshape(h, img.bytesPerLine() // 4, 4)[:, :w, :].astype(np.float32)
    rgb = arr[..., :3] / 255.0
    lum = rgb.mean(axis=2)
    rng = np.random.default_rng(w * 31 + h)
    rgb = rgb * oclusao(lum, 0.35, 2)[..., None] * grao(w, h, rng, 0.05)[..., None]
    saida = np.empty((h, w, 4), np.uint8)
    saida[..., :3] = np.clip(rgb * 255, 0, 255)
    saida[..., 3] = arr[..., 3]
    return QImage(saida.tobytes(), w, h, w * 4, QImage.Format.Format_RGBA8888).copy()
