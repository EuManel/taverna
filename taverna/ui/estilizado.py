"""
🎨 Interface ESTILIZADA (v0.52) — pedido do Manel: "não quero nada realista; quero detalhado, com cara de
jogo, fantasioso". Nada de textura de foto: tudo é PINTADO pelo programa (cores chapadas com degradê,
veios desenhados, rebites, pregos) e ganha VOLUME com um mapa de altura bem exagerado + luz "de jogo":
  - bisel gordo e arredondado (as peças parecem de brinquedo/miniatura);
  - luz de cima-esquerda com realce forte na quina de cima e sombra na de baixo;
  - contorno escuro onde a peça dobra (o "traço" de desenho animado);
  - brilho especular só no metal.

Peças: placa (tábuas com moldura de vigas e cantoneiras de ferro), botões, título em metal, parede de
tijolos 3D. Cada tema tem a sua paleta (madeira, metal sci-fi, pedra rúnica, papel…).
"""

import math
import zlib

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath

TOCHAS = ((0.19, 0.36), (0.81, 0.36))   # emoldurando o menu (que fica no meio)   # onde ficam as tochas na tela inicial (0..1) — o QML usa as mesmas
LUZ = np.array([-0.42, -0.70, 0.58])
LUZ /= np.linalg.norm(LUZ)
_CACHE = {}


def _c(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255


def _suave(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def _rng(*chave):
    return np.random.default_rng(zlib.crc32(repr(chave).encode()))


def _caixa_borrar(a, r):
    """Borrão de caixa (separável) com raio r px — rápido, pra fazer "almofadas" de altura."""
    r = int(max(1, r))
    for eixo in (0, 1):
        c = np.cumsum(np.pad(a, [(r + 1, r) if k == eixo else (0, 0) for k in range(2)], mode="edge"), axis=eixo)
        if eixo == 0:
            a = (c[2 * r + 1:] - c[:-2 * r - 1]) / (2 * r + 1)
        else:
            a = (c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)
    return a


def _ruido(H, W, raio, rng):
    """Ruído suave normalizado 0..1 (borrão de pontos aleatórios, esticado pra usar a faixa toda)."""
    b = _caixa_borrar(rng.random((H, W)).astype(np.float32), raio)
    b = _caixa_borrar(b, max(1, raio // 2))
    return (b - b.min()) / max(1e-6, float(np.ptp(b)))


def _dist_ret(xs, ys, x0, y0, x1, y1, raio):
    """Distância até a borda (positiva dentro) de um retângulo arredondado."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    qx = np.abs(xs - cx) - ((x1 - x0) / 2 - raio)
    qy = np.abs(ys - cy) - ((y1 - y0) / 2 - raio)
    fora = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0)
    return raio - fora


# ====================================================================== a luz "de jogo"
def iluminar(albedo, altura, brilho=None, metal=None, alfa=None, forca=6.0, contorno=0.55, ambiente=0.42):
    """albedo (H,W,3) · altura (H,W, ~0..1 em px de bisel) · brilho/metal (H,W) 0..1 → RGBA uint8."""
    gy, gx = np.gradient(altura)
    n = np.dstack([-gx * forca, -gy * forca, np.ones_like(altura)])
    inclin = np.sqrt(gx * gx + gy * gy) * forca
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    dif = np.clip(n @ LUZ, 0, 1)
    dif = 0.15 + 0.85 * _suave(dif * 1.15)                       # um pouco "em degraus" (desenho)
    meio = np.array([0, 0, 1.0]) + LUZ
    meio /= np.linalg.norm(meio)
    spec = np.clip(n @ meio, 0, 1) ** 28
    brilho = np.zeros_like(altura) if brilho is None else brilho
    metal = np.zeros_like(altura) if metal is None else metal
    rgb = albedo * (ambiente + dif[..., None] * (1.05 - ambiente))
    rgb += spec[..., None] * brilho[..., None] * (albedo * metal[..., None] + (1 - metal[..., None]) * 0.9) * 1.3
    # realce na quina que olha pra luz (aro de luz) e traço escuro onde a peça dobra forte
    aro = _suave((n @ LUZ - 0.78) * 6) * _suave(inclin * 0.8)
    rgb += aro[..., None] * 0.22
    traco = _suave((inclin - 0.9) * 1.6) * contorno
    rgb *= (1 - traco[..., None] * 0.75)
    rgb = np.clip(rgb, 0, 1)
    h, w = altura.shape
    a = np.ones((h, w), np.float32) if alfa is None else np.clip(alfa, 0, 1)
    out = np.empty((h, w, 4), np.uint8)
    out[..., :3] = (rgb * a[..., None] * 255).astype(np.uint8)
    out[..., 3] = (a * 255).astype(np.uint8)
    return out


def _qimg(rgba):
    h, w = rgba.shape[:2]
    return QImage(rgba.tobytes(), w, h, w * 4, QImage.Format.Format_RGBA8888_Premultiplied).copy()


# ====================================================================== paletas por tema
# madeira/material da placa, das vigas da moldura, do botão, do botão principal; ferragens
PALETAS = {
    "medieval": dict(placa=("madeira", "#8a5a32", "#5e3a1e"), viga=("madeira", "#6a4224", "#3e2512"),
                     botao=("madeira", "#7a4a2a", "#4a2a16"), principal=("metal", "#f2c45a", "#a8701c"),
                     ferro="#4a4a52", rebite="#9a9aa4"),
    "terror": dict(placa=("madeira", "#4a3830", "#2a1e1a"), viga=("madeira", "#3a2a24", "#1e1412"),
                   botao=("madeira", "#3e2e28", "#22180f"), principal=("metal", "#c03a3a", "#5a1012"),
                   ferro="#5a3a2a", rebite="#8a6a50"),
    "futurista": dict(placa=("chapa", "#2c4a6e", "#18283e"), viga=("chapa", "#3a5878", "#1c2c40"),
                      botao=("chapa", "#2a4a70", "#16283e"), principal=("metal", "#5ae8ff", "#1a7aa0"),
                      ferro="#7a8aa0", rebite="#c8e8ff"),
    "moderno": dict(placa=("liso", "#2e333a", "#1e2227"), viga=("liso", "#3c424a", "#24282e"),
                    botao=("liso", "#3a4048", "#262a30"), principal=("metal", "#5ac8bc", "#2a7a72"),
                    ferro="#8a929c", rebite="#d0d8e0"),
    "magico": dict(placa=("pedra", "#4e3a7a", "#2c1f4a"), viga=("pedra", "#5c4690", "#30225a"),
                   botao=("pedra", "#4a3478", "#2a1c48"), principal=("metal", "#d8b8ff", "#7a4ad0"),
                   ferro="#8a70c0", rebite="#e8d8ff"),
    "steampunk": dict(placa=("chapa", "#5a3e24", "#36240f"), viga=("madeira", "#4a3020", "#2a1a10"),
                      botao=("chapa", "#6a4a28", "#3a2812"), principal=("metal", "#e0b860", "#8a5a1c"),
                      ferro="#8a6a3a", rebite="#e8c878"),
    "posapoc": dict(placa=("madeira", "#4a4636", "#2a281e"), viga=("chapa", "#5a3a22", "#2e1e10"),
                    botao=("madeira", "#3e3a2c", "#24221a"), principal=("metal", "#d8803a", "#6a2e10"),
                    ferro="#6a4a30", rebite="#a88a60"),
    "claro": dict(placa=("papel", "#f2e2bc", "#d8c090"), viga=("madeira", "#9a6a3a", "#6a4222"),
                  botao=("papel", "#ead6a8", "#c8ac78"), principal=("metal", "#d08a40", "#8a4a14"),
                  ferro="#8a6a30", rebite="#f0d080"),
    "escuro": dict(placa=("liso", "#262830", "#18191e"), viga=("liso", "#30333c", "#1c1e24"),
                   botao=("liso", "#30343e", "#1e2128"), principal=("metal", "#8aa8ff", "#3a58c0"),
                   ferro="#6a7080", rebite="#c0c8e0"),
}


def _pintar_material(tipo, cor_a, cor_b, xs, ys, mask_comp, rng, ao_longo="y"):
    """Albedo pintado (H,W,3) + altura de detalhe (H,W) + brilho + metal, pro tipo de material."""
    H, W = xs.shape
    a, b = _c(cor_a), _c(cor_b)
    det = np.zeros((H, W), np.float32)
    brilho = np.full((H, W), 0.08, np.float32)
    metal = np.zeros((H, W), np.float32)
    u = ys if ao_longo == "y" else xs      # ao longo da tábua
    v = xs if ao_longo == "y" else ys      # de lado
    if tipo == "madeira":
        # veios desenhados: ondas largas e algumas linhas escuras finas (como pincel)
        fase = rng.uniform(0, 6.28)
        onda = np.sin(v * 0.11 + np.sin(u * 0.013 + fase) * 2.2 + fase)
        veio = _suave((np.abs(onda) - 0.86) * 9)
        t = 0.5 + 0.35 * np.sin(v * 0.035 + np.sin(u * 0.008 + fase) * 1.5)
        cor = a * (1 - t[..., None]) + b * t[..., None]
        cor = cor * (1 - veio[..., None] * 0.35)
        det -= veio * 0.6
    elif tipo == "chapa":            # painel sci-fi: degradê + linhas de painel + furinhos
        t = _suave(ys / max(1, H))
        cor = a * (1 - t[..., None]) + b * t[..., None]
        brilho[:] = 0.55
        metal[:] = 0.6
    elif tipo == "pedra":            # laje de pedra arcana: manchas suaves e veios brilhantes
        rr = _rng("pedra", H, W)
        manchas = _caixa_borrar(rr.random((H, W)).astype(np.float32), 18)
        manchas = (manchas - manchas.min()) / max(1e-6, np.ptp(manchas))
        cor = a * (1 - manchas[..., None]) + b * manchas[..., None]
        brilho[:] = 0.3
    elif tipo == "papel":
        t = _suave(ys / max(1, H)) * 0.5
        cor = a * (1 - t[..., None]) + b * t[..., None]
    elif tipo == "metal":            # metal polido: faixas de reflexo (dá cara de metal na hora)
        t = ys / max(1, H)
        faixa = 0.5 + 0.5 * np.cos((t * 1.3 + 0.15) * 2 * math.pi)
        cor = b + (a - b) * (0.35 + 0.65 * faixa[..., None])
        brilho[:] = 1.0
        metal[:] = 0.85
    else:                             # liso (couro/plástico fosco)
        t = _suave(ys / max(1, H))
        cor = a * (1 - t[..., None]) + b * t[..., None]
        brilho[:] = 0.25
    return cor.astype(np.float32), det, brilho, metal


def _rebite(alt, alb, brilho, metal, xs, ys, cx, cy, r, cor):
    d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    m = d < r
    if not m.any():
        return
    alt[m] = np.maximum(alt[m], (1 - (d[m] / r) ** 2) ** 0.5 * 1.6 + 1.0)
    alb[m] = _c(cor)
    brilho[m] = 1.0
    metal[m] = 0.9


# ====================================================================== placa de tábuas
def placa(tema, w, h, escala=1.0, nivel=2):
    chave = ("placa", tema, w, h, round(escala, 2), nivel)
    if chave in _CACHE:
        return _CACHE[chave]
    P = PALETAS.get(tema, PALETAS["medieval"])
    e = escala
    W, H = max(8, int(w * e)), max(8, int(h * e))
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    rng = _rng(tema, w, h)
    raio = 10 * e
    fora = _dist_ret(xs, ys, 0, 0, W, H, raio)
    alfa = np.clip(fora + 0.5, 0, 1)
    F = (24 if nivel == 2 else 14) * e                   # largura das vigas da moldura
    dentro = _dist_ret(xs, ys, F, F, W - F, H - F, 3 * e)

    # --- miolo: tábuas na vertical, cada uma com volume próprio
    tipo, ca, cb = P["placa"]
    alb = np.zeros((H, W, 3), np.float32)
    alt = np.zeros((H, W), np.float32)
    brilho = np.zeros((H, W), np.float32)
    metal = np.zeros((H, W), np.float32)
    if tipo == "madeira":
        n_tab = max(3, int((W - 2 * F) / (64 * e)))
        larg = (W - 2 * F) / n_tab
        for k in range(n_tab):
            x0 = F + k * larg
            x1 = x0 + larg
            sub = (xs >= x0) & (xs < x1)
            d = _dist_ret(xs, ys, x0 + 1.5 * e, F - 4 * e, x1 - 1.5 * e, H - F + 4 * e, 5 * e)
            tom = rng.uniform(0.85, 1.15)
            cor, det, br, mt = _pintar_material("madeira", ca, cb, xs - x0, ys, None, _rng(tema, k), "y")
            alb[sub] = np.clip(cor[sub] * tom, 0, 1)
            alt[sub] = (_suave(d[sub] / (5 * e)) * 1.0 + det[sub] * 0.15)
            brilho[sub] = br[sub]
            # nós na madeira (de vez em quando)
            if rng.random() < 0.6:
                nx, ny = x0 + larg * rng.uniform(0.3, 0.7), rng.uniform(F + 40 * e, H - F - 40 * e)
                dn = np.sqrt(((xs - nx) / (larg * 0.18)) ** 2 + ((ys - ny) / (larg * 0.3)) ** 2)
                aneis = (dn < 1) & sub
                alb[aneis] *= (0.62 + 0.25 * np.cos(dn[aneis] * 9))[..., None]
                alt[aneis] -= 0.15 * (1 - dn[aneis])
            # pregos nas pontas
            for py in (F + 12 * e, H - F - 12 * e):
                for px in (x0 + larg * 0.28, x1 - larg * 0.28):
                    _rebite(alt, alb, brilho, metal, xs, ys, px, py, 2.6 * e, P["ferro"])
    else:
        cor, det, br, mt = _pintar_material(tipo, ca, cb, xs, ys, None, rng, "y")
        alb[:] = cor
        alt[:] = _suave(dentro / (6 * e)) * 0.6 + det * 0.15
        brilho[:] = br
        metal[:] = mt
        if tipo == "chapa":                           # linhas de painel e furinhos
            for k in range(1, 4):
                y = F + (H - 2 * F) * k / 4
                m = np.abs(ys - y) < 1.2 * e
                alt[m & (dentro > 0)] -= 0.5
            for px in np.linspace(F + 14 * e, W - F - 14 * e, 7):
                for py in (F + 10 * e, H - F - 10 * e):
                    _rebite(alt, alb, brilho, metal, xs, ys, px, py, 2.2 * e, P["rebite"])
        elif tipo == "pedra":                         # runas que brilham fraquinho
            r2 = _rng("runas", tema, w, h)
            for _ in range(6):
                cx, cy = r2.uniform(F + 30 * e, W - F - 30 * e), r2.uniform(F + 30 * e, H - F - 30 * e)
                ang = r2.uniform(0, math.pi)
                d1 = np.abs((xs - cx) * math.cos(ang) + (ys - cy) * math.sin(ang))
                d2 = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
                m = (d1 < 1.4 * e) & (d2 < 16 * e)
                alb[m] = alb[m] * 0.4 + _c(P["rebite"]) * 0.6
                alt[m] -= 0.35
    afundar = dentro < 0                              # a moldura fica por cima do miolo
    # --- moldura: quatro vigas com volume, chanfradas nos cantos
    vtipo, va, vb = P["viga"]
    vcor, vdet, vbr, vmt = _pintar_material(vtipo, va, vb, xs, ys, None, _rng("viga", tema), "x")
    vcor2, vdet2, _b2, _m2 = _pintar_material(vtipo, va, vb, xs, ys, None, _rng("viga2", tema), "y")
    lateral = (np.minimum(xs, W - xs) < np.minimum(ys, H - ys))   # vigas da esquerda/direita
    vcor = np.where(lateral[..., None], vcor2, vcor)
    vdet = np.where(lateral, vdet2, vdet)
    # altura da viga: almofada a partir da borda de fora e da de dentro
    viga_alt = np.minimum(_suave(fora / (7 * e)), _suave(-dentro / (7 * e))) * 1.5 + 0.4 + vdet * 0.12
    # emenda diagonal nos cantos (meia-esquadria)
    diag = np.abs(np.minimum(xs, W - xs) - np.minimum(ys, H - ys)) < 1.0 * e
    viga_alt = np.where(diag, viga_alt - 0.6, viga_alt)
    alb = np.where(afundar[..., None], vcor, alb)
    alt = np.where(afundar, viga_alt, alt)
    brilho = np.where(afundar, vbr, brilho)
    metal = np.where(afundar, vmt, metal)
    # --- cantoneiras de ferro com rebites (alto)
    if nivel == 2:
        L = 46 * e
        for (cx, cy, sx, sy) in ((0, 0, 1, 1), (W, 0, -1, 1), (0, H, 1, -1), (W, H, -1, -1)):
            lx = (xs - cx) * sx
            ly = (ys - cy) * sy
            perna = ((lx < L) & (ly < F * 0.9)) | ((ly < L) & (lx < F * 0.9))
            perna &= (fora > 0)
            dd = np.minimum(np.minimum(L - lx, L - ly), np.minimum(F * 0.9 - np.minimum(lx, ly), fora))
            alt[perna] = 2.2 + _suave(dd[perna] / (3 * e)) * 0.8
            alb[perna] = _c(P["ferro"]) * (0.85 + 0.15 * _suave(ly[perna] / L))[..., None]
            brilho[perna] = 0.8
            metal[perna] = 0.7
            for px, py in ((10, 10), (L - 9, 10), (10, L - 9)):
                _rebite(alt, alb, brilho, metal, xs, ys, cx + sx * px * e if False else cx + sx * px * e,
                        cy + sy * py * e, 3.2 * e, P["rebite"])
    rgba = iluminar(alb, alt * 4 * e, brilho, metal, alfa, forca=1.6 / e)
    img = _qimg(rgba)
    _CACHE[chave] = img
    return img


# ====================================================================== botão
def botao(tema, w, h, principal=False, estado="normal", escala=1.0, nivel=2):
    chave = ("botao", tema, w, h, principal, estado, round(escala, 2), nivel)
    if chave in _CACHE:
        return _CACHE[chave]
    P = PALETAS.get(tema, PALETAS["medieval"])
    e = escala
    W, H = max(8, int(w * e)), max(8, int(h * e))
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    raio = 9 * e
    d = _dist_ret(xs, ys, 0, 0, W, H, raio)
    alfa = np.clip(d + 0.5, 0, 1)
    tipo, ca, cb = P["principal" if principal else "botao"]
    if estado == "sobre":
        ca, cb = _clarear(ca, 1.18), _clarear(cb, 1.18)
    cor, det, brilho, metal = _pintar_material(tipo, ca, cb, xs, ys, None, _rng(tema, w, principal), "x")
    bisel = 8 * e
    alt = _suave(d / bisel) * 1.6 + det * 0.12
    # friso por dentro (dá cara de botão de jogo)
    alt -= 0.35 * np.exp(-((d - bisel * 1.5) / (1.4 * e)) ** 2)
    if estado == "apertado":
        alt = 1.6 - alt * 0.7
        cor *= 0.85
    for px in (12 * e, W - 12 * e):                      # rebites nas pontas
        if nivel == 2 and W > 120 * e:
            _rebite(alt, cor, brilho, metal, xs, ys, px, H / 2, 3.0 * e, P["rebite"])
    rgba = iluminar(cor, alt * 3.2 * e, brilho, metal, alfa, forca=1.7 / e)
    img = _qimg(rgba)
    _CACHE[chave] = img
    return img


def _clarear(hexa, f):
    c = np.clip(_c(hexa) * f, 0, 1)
    return "#" + "".join(f"{int(v * 255):02x}" for v in c)


# ====================================================================== título em metal
METAL_TITULO = {"medieval": ("#fff3b8", "#f0b840", "#8a5410", "#2a1606"),
                "terror": ("#ffd0c8", "#c83030", "#5a0a0e", "#120204"),
                "futurista": ("#e8fbff", "#58d8ff", "#105a80", "#02121e"),
                "moderno": ("#ffffff", "#c8d2dc", "#5a6470", "#101418"),
                "magico": ("#fff0ff", "#c8a0ff", "#5a2aa0", "#140828"),
                "steampunk": ("#fff4d0", "#d8a848", "#7a4a12", "#1e1206"),
                "posapoc": ("#ffd8b0", "#c8702a", "#5a2a0c", "#140a04"),
                "claro": ("#fff0c8", "#c88838", "#6a3a0c", "#2a1404"),
                "escuro": ("#ffffff", "#a8b8ff", "#3a4a90", "#0a0e20")}


def titulo(tema, texto, familia, px, espaco, escala=1.0):
    """O título (TAVERNA) como uma peça de METAL: letras com bisel, reflexo em faixas, contorno escuro e
    sombra. Devolve QImage com sobra em volta (pra sombra)."""
    chave = ("titulo", tema, texto, familia, px, espaco, round(escala, 2))
    if chave in _CACHE:
        return _CACHE[chave]
    e = escala
    fonte = QFont(familia)
    fonte.setPixelSize(int(px * e))
    fonte.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, espaco * e)
    caminho = QPainterPath()
    caminho.addText(QPointF(0, 0), fonte, texto)
    r = caminho.boundingRect()
    m = int(26 * e)
    W, H = int(r.width()) + 2 * m, int(r.height()) + 2 * m
    mask = QImage(W, H, QImage.Format.Format_Grayscale8)
    mask.fill(0)
    p = QPainter(mask)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.translate(m - r.left(), m - r.top())
    p.fillPath(caminho, QColor(255, 255, 255))
    p.end()
    ptr = mask.constBits()
    ptr.setsize(mask.sizeInBytes())
    a = np.frombuffer(ptr, np.uint8).reshape(H, mask.bytesPerLine())[:, :W].astype(np.float32) / 255
    borda = _c(METAL_TITULO.get(tema, METAL_TITULO["medieval"])[3])
    letras = metal(a, tema, e, perfil=4.0)       # letras de metal com reflexo de verdade
    # contorno escuro grosso + sombra caindo pra baixo-direita
    grosso = np.clip(_caixa_borrar(a, 3 * e) * 3, 0, 1)
    sombra = np.roll(np.roll(_caixa_borrar(a, 7 * e), int(5 * e), 0), int(4 * e), 1) * 0.75
    out = np.zeros((H, W, 4), np.float32)
    out[..., 3] = sombra
    for camada, cor_c in ((grosso, borda),):
        out[..., :3] = out[..., :3] * (1 - camada[..., None]) + cor_c * camada[..., None]
        out[..., 3] = out[..., 3] * (1 - camada) + camada
    la = letras[..., 3]
    out[..., :3] = out[..., :3] * (1 - la[..., None]) + letras[..., :3]   # (letras já pré-multiplicadas)
    out[..., 3] = out[..., 3] * (1 - la) + la
    rgba = np.empty((H, W, 4), np.uint8)
    rgba[..., 3] = (np.clip(out[..., 3], 0, 1) * 255).astype(np.uint8)
    rgba[..., :3] = (np.clip(out[..., :3], 0, 1) * 255).astype(np.uint8)
    img = _qimg(rgba)
    _CACHE[chave] = img
    return img


# ====================================================================== METAL de verdade (reflexo do ambiente)
# Metal não é degradê: ele ESPELHA o que está em volta. Aqui cada pixel reflete um "ambiente" de mentira —
# céu claro em cima, uma faixa escura no horizonte, chão quente embaixo — conforme a inclinação da peça.
# É o truque clássico do cromado/dourado: com o bisel arredondado, aparecem as faixas de reflexo, o brilho
# estourado nas quinas e o escuro do horizonte, e aí parece metal (e não plástico).
CORES_METAL = {   # (escuro, médio, claro, brilho) de cada tema
    "medieval": ("#3a2208", "#a8721e", "#f6d27a", "#fffbe8"),     # ouro velho
    "terror": ("#1c0606", "#6a2018", "#c86048", "#ffe0d0"),       # ferro avermelhado
    "futurista": ("#06202e", "#2a8ab0", "#9ef0ff", "#ffffff"),    # aço azulado
    "moderno": ("#20262c", "#6a7680", "#dfe6ec", "#ffffff"),      # alumínio
    "magico": ("#1e0e3a", "#7a52c0", "#e2ccff", "#ffffff"),       # prata arcana
    "steampunk": ("#3a2208", "#b07a2a", "#f2d08a", "#fff8e4"),    # latão polido
    "posapoc": ("#1e1006", "#7a3a14", "#c8804a", "#f0d0b0"),      # lata enferrujada
    "claro": ("#3a1c06", "#8a5420", "#e8b070", "#fff2dc"),        # bronze
    "escuro": ("#141826", "#5a6690", "#c8d4ff", "#ffffff"),       # aço
    "ferro": ("#0e0e10", "#3a3a3e", "#8a8a90", "#e8e8f0"),        # ferro batido (suporte da tocha)
}


def metal(mask, tema, escala=1.0, perfil=2.5, riscos=True):
    """mask (H,W) 0..1 da peça → RGBA float pré-multiplicado, com cara de metal."""
    e = escala
    escuro, medio, claro, estouro = (_c(h) for h in CORES_METAL.get(tema, CORES_METAL["medieval"]))
    # perfil arredondado (tubo/bisel) a partir da máscara
    alt = (_caixa_borrar(mask, max(1, perfil * e)) + _caixa_borrar(mask, max(1, perfil * 0.5 * e))) * 0.5
    alt = alt * mask
    if riscos:   # riscos finos de polimento (deixam o brilho "escovado")
        H, W = mask.shape
        rr = _rng("riscos", H, W)
        r = _caixa_borrar(rr.random((H, W)).astype(np.float32), 1)
        alt = alt + (r - 0.5) * 0.04
    gy, gx = np.gradient(alt)
    k = 3.2 / max(0.5, perfil * e) * 4
    n = np.dstack([-gx * k, -gy * k, np.ones_like(alt)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    # reflexo de quem olha de frente (V = 0,0,1): R = 2(n·V)n − V
    ry = 2 * n[..., 2] * n[..., 1]       # <0 = reflete o céu (em cima) · >0 = o chão
    rx = 2 * n[..., 2] * n[..., 0]
    ceu = _suave((-ry - 0.05) * 3.5)                     # céu claro
    horiz = np.exp(-((ry - 0.08) / 0.12) ** 2)           # faixa escura do horizonte
    chao = _suave((ry - 0.2) * 2.0) * 0.55               # chão quente refletido
    v = np.clip(0.42 + ceu * 0.62 - horiz * 0.45 + chao * 0.25 + rx * 0.12, 0, 1.25)
    # escuro → médio → claro → estouro
    cor = np.where((v < 0.5)[..., None], escuro + (medio - escuro) * (v / 0.5)[..., None],
                   medio + (claro - medio) * np.clip((v - 0.5) / 0.45, 0, 1)[..., None])
    spec = np.clip(n @ (LUZ + np.array([0, 0, 1.0])) / np.linalg.norm(LUZ + np.array([0, 0, 1.0])), 0, 1) ** 60
    cor = cor + (estouro - cor) * np.clip(spec * 1.4 + _suave((v - 1.0) * 6), 0, 1)[..., None]
    # quina escura (oclusão) bem na beirada
    beira = 1 - _suave(alt / max(1e-3, alt.max() * 0.35))
    cor *= (1 - beira[..., None] * 0.55)
    out = np.zeros(mask.shape + (4,), np.float32)
    out[..., :3] = np.clip(cor, 0, 1) * mask[..., None]
    out[..., 3] = mask
    return out


def _mascara(W, H, desenhar):
    """Roda desenhar(p) num QImage cinza e devolve a máscara (H,W) 0..1."""
    m = QImage(W, H, QImage.Format.Format_Grayscale8)
    m.fill(0)
    p = QPainter(m)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    desenhar(p)
    p.end()
    ptr = m.constBits()
    ptr.setsize(m.sizeInBytes())
    return np.frombuffer(ptr, np.uint8).reshape(H, m.bytesPerLine())[:, :W].astype(np.float32) / 255


def _compor(base: QImage, camada: np.ndarray) -> QImage:
    """Cola uma camada RGBA float pré-multiplicada por cima de um QImage ARGB32 pré-multiplicado."""
    b = base.convertToFormat(QImage.Format.Format_RGBA8888_Premultiplied)
    W, H = b.width(), b.height()
    ptr = b.constBits()
    ptr.setsize(b.sizeInBytes())
    arr = np.frombuffer(ptr, np.uint8).reshape(H, b.bytesPerLine())[:, :W * 4].reshape(H, W, 4).astype(np.float32) / 255
    a = camada[..., 3:4]
    arr = camada + arr * (1 - a)
    out = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
    return QImage(out.tobytes(), W, H, W * 4, QImage.Format.Format_RGBA8888_Premultiplied).copy()


# ====================================================================== botão ORNAMENTADO (estilo tela de título)
# forma · metal da borda (claro, meio, escuro) · fundo (cima, baixo, opacidade) · brilho ao passar o mouse
ESTILO_BOTAO = {
    "medieval": ("ponta", ("#fbe6a8", "#c8963c", "#5a3a14"), ("#2a1c12", "#0e0906", 0.82), "#ffb648"),
    "terror": ("ponta", ("#e8b8a0", "#8a3a2a", "#2a0a08"), ("#1e0c0c", "#080303", 0.86), "#ff3a3a"),
    "futurista": ("chanfro", ("#e8fdff", "#38d8ff", "#0a4060"), ("#06172a", "#020812", 0.78), "#38e1ff"),
    "moderno": ("redondo", ("#ffffff", "#9ab0bc", "#3a464e"), ("#1a2026", "#0c1014", 0.80), "#7fe3d8"),
    "magico": ("ponta", ("#fff2ff", "#b89aff", "#3a2270"), ("#1c1030", "#080412", 0.80), "#c8a0ff"),
    "steampunk": ("ponta", ("#fbe2a0", "#c89040", "#5a3410"), ("#2a1a0e", "#100804", 0.84), "#ffc860"),
    "posapoc": ("chanfro", ("#e8c8a0", "#a85a28", "#3a1a08"), ("#22201a", "#0c0b08", 0.84), "#ff9a4a"),
    "claro": ("ponta", ("#c8925a", "#7a4a1e", "#3a200a"), ("#f8eed6", "#e8d6b0", 0.88), "#a8601a"),
    "escuro": ("redondo", ("#e0e6ff", "#7c8cbc", "#2a3048"), ("#1a1c24", "#0c0d12", 0.82), "#7c9cff"),
}
MARGEM_BRILHO = 10   # px lógicos em volta do botão, reservados pro brilho


def _caminho_botao(forma, x0, y0, x1, y1, e):
    c = QPainterPath()
    h = y1 - y0
    if forma == "ponta":            # cápsula com pontas (losango nas extremidades)
        p = h * 0.42
        c.moveTo(x0 + p, y0)
        c.lineTo(x1 - p, y0)
        c.lineTo(x1, (y0 + y1) / 2)
        c.lineTo(x1 - p, y1)
        c.lineTo(x0 + p, y1)
        c.lineTo(x0, (y0 + y1) / 2)
        c.closeSubpath()
    elif forma == "chanfro":        # cantos cortados (sci-fi)
        k = h * 0.32
        c.moveTo(x0 + k, y0)
        c.lineTo(x1, y0)
        c.lineTo(x1, y1 - k)
        c.lineTo(x1 - k, y1)
        c.lineTo(x0, y1)
        c.lineTo(x0, y0 + k)
        c.closeSubpath()
    else:                           # pílula arredondada
        c.addRoundedRect(QRectF(x0, y0, x1 - x0, y1 - y0), h / 2, h / 2)
    return c


def botao_ornado(tema, w, h, estado="normal", escala=1.0, nivel=2):
    """Botão fino de tela de título: fundo escuro translúcido, borda de metal com reflexo, pontas
    ornamentadas, brilho suave ao passar o mouse. A imagem tem MARGEM_BRILHO de sobra em volta."""
    from PyQt6.QtGui import QBrush, QLinearGradient, QPen, QRadialGradient
    chave = ("ornado", tema, w, h, estado, round(escala, 2), nivel)
    if chave in _CACHE:
        return _CACHE[chave]
    forma, (m1, m2, m3), (f1, f2, fa), cor_brilho = ESTILO_BOTAO.get(tema, ESTILO_BOTAO["medieval"])
    e = escala
    g = MARGEM_BRILHO * e
    W, H = int((w + 2 * MARGEM_BRILHO) * e), int((h + 2 * MARGEM_BRILHO) * e)
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    x0, y0, x1, y1 = g, g, W - g, H - g
    corpo = _caminho_botao(forma, x0, y0, x1, y1, e)
    sobre, apertado = estado == "sobre", estado == "apertado"
    brilho = QColor(cor_brilho)
    # brilho por fora (alto, passando o mouse): vários traços cada vez mais largos e fracos
    if sobre and nivel == 2:
        for k in range(6, 0, -1):
            c = QColor(brilho)
            c.setAlpha(int(14 + 10 * (6 - k)))
            p.setPen(QPen(c, k * 1.6 * e))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(corpo)
    # fundo escuro translúcido, com um véu de luz no meio quando o mouse passa
    fundo = QLinearGradient(QPointF(0, y0), QPointF(0, y1))
    ca, cb = QColor(f1), QColor(f2)
    if apertado:
        ca, cb = cb, ca
    ca.setAlphaF(fa)
    cb.setAlphaF(fa)
    fundo.setColorAt(0, ca)
    fundo.setColorAt(1, cb)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(fundo))
    p.drawPath(corpo)
    if sobre or apertado:
        veu = QRadialGradient(QPointF(W / 2, (y0 + y1) / 2), (x1 - x0) * 0.55)
        c0 = QColor(brilho)
        c0.setAlpha(70 if sobre else 40)
        c1 = QColor(brilho)
        c1.setAlpha(0)
        veu.setColorAt(0, c0)
        veu.setColorAt(1, c1)
        p.setBrush(QBrush(veu))
        p.drawPath(corpo)
    if nivel == 0:   # simples: só uma linha fina
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(m2), 1.2 * e))
        p.drawPath(corpo)
        p.end()
        _CACHE[chave] = img
        return img
    # sombrinha embaixo da borda (a peça de metal "descola" do fundo)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(QColor(0, 0, 0, 140), 4.5 * e))
    p.drawPath(corpo.translated(0.8 * e, 1.6 * e))
    p.end()

    # ---- as peças de METAL (borda, filete, pontas, gemas) com reflexo de verdade
    meio_y = (y0 + y1) / 2
    larg = (3.6 if nivel == 2 else 2.6) * e
    dentro = _caminho_botao(forma, x0 + 5 * e, y0 + 5 * e, x1 - 5 * e, y1 - 5 * e, e)

    def desenhar(q):
        q.setBrush(Qt.BrushStyle.NoBrush)
        q.setPen(QPen(QColor(255, 255, 255), larg))
        q.drawPath(corpo)
        q.setPen(QPen(QColor(255, 255, 255), 1.3 * e))
        q.drawPath(dentro)
        if nivel == 2:
            q.setPen(Qt.PenStyle.NoPen)
            q.setBrush(QColor(255, 255, 255))
            for xp, sx in ((x0, -1), (x1, 1)):          # losango nas pontas
                lado = 6.5 * e
                cx = xp + sx * 1.5 * e
                los = QPainterPath()
                los.moveTo(cx, meio_y - lado)
                los.lineTo(cx + sx * lado * 0.9, meio_y)
                los.lineTo(cx, meio_y + lado)
                los.lineTo(cx - sx * lado * 0.9, meio_y)
                los.closeSubpath()
                q.drawPath(los)
            for yy in (y0, y1):                           # gema no meio de cima e de baixo
                q.drawEllipse(QPointF(W / 2, yy), 4.0 * e, 4.0 * e)
    m = _mascara(W, H, desenhar)
    camada = metal(m, tema, e, perfil=2.2 if nivel == 2 else 1.6)
    if sobre:   # passando o mouse: o metal pega um pouco da luz
        camada[..., :3] = np.clip(camada[..., :3] * 1.18, 0, camada[..., 3:4])
    img = _compor(img, camada)
    _CACHE[chave] = img
    return img


# ====================================================================== cada tema com o SEU botão (v0.52)
NEUTROS = ("claro", "escuro")


TEXTO_NA_IMAGEM = ("terror",)   # temas em que o texto do botão é desenhado aqui (letra gasta), não no QML


def botao_tema(tema, w, h, estado="normal", escala=1.0, nivel=2, texto=""):
    """O botão da tela inicial no jeito de cada tema (com MARGEM_BRILHO de sobra em volta)."""
    if (nivel == 0 and tema not in TEXTO_NA_IMAGEM) or tema in ("medieval",):
        return botao_ornado(tema, w, h, estado, escala, nivel)
    f = {"futurista": _botao_tech, "magico": _botao_cristal,
         "moderno": _botao_moderno, "claro": _botao_neutro, "escuro": _botao_neutro}.get(tema)
    if tema == "terror":
        f = lambda t, ww, hh, es, ee, nv: _botao_terror(t, ww, hh, es, ee, nv, texto)   # noqa: E731
    if f is None:
        return botao_ornado(tema, w, h, estado, escala, nivel)
    chave = ("botao_tema", tema, w, h, estado, round(escala, 2), nivel, texto)
    if chave not in _CACHE:
        _CACHE[chave] = f(tema, w, h, estado, escala, nivel)
    return _CACHE[chave]


def _tela(w, h, e):
    g = MARGEM_BRILHO * e
    W, H = int((w + 2 * MARGEM_BRILHO) * e), int((h + 2 * MARGEM_BRILHO) * e)
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    return img, W, H, g


def _botao_tabua(tema, w, h, estado, e, nivel):
    """Terror: uma tábua velha QUEBRADA — bordas lascadas, rachadura, pregos tortos, mancha escura."""
    from PyQt6.QtGui import QBrush, QPen, QRadialGradient
    img, W, H, g = _tela(w, h, e)
    rng = _rng("tabua", w, h)
    x0, y0, x1, y1 = g, g, W - g, H - g
    # contorno lascado: cima e baixo com dentinhos, a ponta direita quebrada em diagonal
    pts = [QPointF(x0 + rng.uniform(0, 5) * e, y0 + rng.uniform(0, 4) * e)]
    n = 14
    for k in range(1, n):
        pts.append(QPointF(x0 + (x1 - x0) * k / n, y0 + rng.uniform(-1, 4) * e))
    pts += [QPointF(x1 - 4 * e, y0 + 2 * e), QPointF(x1 - rng.uniform(0, 10) * e, (y0 + y1) / 2 - 4 * e),
            QPointF(x1 - rng.uniform(14, 26) * e, y1 - rng.uniform(0, 3) * e)]
    for k in range(n - 1, 0, -1):
        pts.append(QPointF(x0 + (x1 - x0) * k / n, y1 - rng.uniform(-1, 4) * e))
    pts.append(QPointF(x0 + rng.uniform(0, 6) * e, y1 - rng.uniform(0, 3) * e))
    from PyQt6.QtGui import QPolygonF
    forma = QPainterPath()
    forma.addPolygon(QPolygonF(pts))
    forma.closeSubpath()

    def mascara(q):
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QColor(255, 255, 255))
        q.drawPath(forma)
    m = _mascara(W, H, mascara)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    claro = estado == "sobre"
    cor, det, br, mt = _pintar_material("madeira", "#4e3a2e" if not claro else "#5e463a", "#26180f",
                                       xs, ys, None, rng, "x")
    alt = _caixa_borrar(m, 3 * e) * 1.4 + det * 0.25
    # rachadura no meio
    yc = (y0 + y1) / 2 + rng.uniform(-4, 4) * e
    racha = np.abs(ys - yc - np.sin(xs * 0.05) * 3 * e) < 0.9 * e
    racha &= (xs > x0 + (x1 - x0) * 0.35) & (xs < x1 - 6 * e)
    alt[racha] -= 1.2
    cor[racha] *= 0.25
    # mancha escura (sangue seco) num canto
    cx, cy = x0 + (x1 - x0) * rng.uniform(0.6, 0.85), y0 + (y1 - y0) * rng.uniform(0.2, 0.8)
    dm = np.sqrt(((xs - cx) / (26 * e)) ** 2 + ((ys - cy) / (12 * e)) ** 2)
    mancha = _suave((1 - dm) * 2) * 0.8
    cor = cor * (1 - mancha[..., None]) + _c("#3a0606") * mancha[..., None]
    for px in (x0 + 10 * e, x1 - 30 * e):                       # pregos
        _rebite(alt, cor, br, mt, xs, ys, px, (y0 + y1) / 2 + rng.uniform(-6, 6) * e, 2.6 * e, "#5a4a40")
    if estado == "apertado":
        cor *= 0.8
    rgba = iluminar(cor, alt * 3 * e, br, mt, m, forca=1.6 / e, contorno=0.7).astype(np.float32) / 255
    out = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    out.fill(Qt.GlobalColor.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.fillPath(forma.translated(2 * e, 4 * e), QColor(0, 0, 0, 150))     # sombra
    if claro and nivel == 2:                                              # brilho vermelho doentio
        for k in range(5, 0, -1):
            p.setPen(QPen(QColor(200, 20, 20, 18 + 10 * (5 - k)), k * 2 * e))
            p.drawPath(forma)
    p.end()
    return _compor(out, rgba)


def _botao_tech(tema, w, h, estado, e, nivel):
    """Futurista: SÓ o nome. Passando o mouse aparece o contorno tecnológico (cantoneiras, risquinhos, luz)."""
    from PyQt6.QtGui import QBrush, QLinearGradient, QPen
    img, W, H, g = _tela(w, h, e)
    if estado == "normal":
        return img
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    x0, y0, x1, y1 = g, g, W - g, H - g
    ciano = QColor("#38e1ff")
    fundo = QLinearGradient(QPointF(x0, 0), QPointF(x1, 0))
    fundo.setColorAt(0, QColor(56, 225, 255, 0))
    fundo.setColorAt(0.5, QColor(56, 225, 255, 70 if estado == "sobre" else 120))
    fundo.setColorAt(1, QColor(56, 225, 255, 0))
    p.fillRect(QRectF(x0, y0 + 3 * e, x1 - x0, y1 - y0 - 6 * e), QBrush(fundo))
    for k in range(4, 0, -1):            # brilho em volta das cantoneiras
        c = QColor(ciano)
        c.setAlpha(25 + 12 * (4 - k))
        p.setPen(QPen(c, k * 2 * e))
        _cantoneiras_tech(p, x0, y0, x1, y1, e)
    p.setPen(QPen(QColor("#d8faff"), 1.6 * e))
    _cantoneiras_tech(p, x0, y0, x1, y1, e)
    p.setPen(QPen(QColor(56, 225, 255, 160), 1 * e))   # risquinhos (régua)
    for k in range(6):
        x = x0 + 22 * e + k * 6 * e
        p.drawLine(QPointF(x, y1 - 2 * e), QPointF(x, y1 - (6 if k % 3 == 0 else 4) * e))
    p.setPen(QPen(QColor("#ff3fa4"), 2 * e))            # um toque magenta
    p.drawLine(QPointF(x1 - 30 * e, y0 + 1 * e), QPointF(x1 - 16 * e, y0 + 1 * e))
    p.end()
    return img


def _cantoneiras_tech(p, x0, y0, x1, y1, e):
    L = 14 * e
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        caminho = QPainterPath(QPointF(cx + sx * L, cy))
        caminho.lineTo(cx + sx * 4 * e, cy)
        caminho.lineTo(cx, cy + sy * 4 * e)
        caminho.lineTo(cx, cy + sy * L * 0.8)
        p.drawPath(caminho)


def _botao_cristal(tema, w, h, estado, e, nivel):
    """Mágico: um cristal comprido, lapidado em facetas. Apagadinho; passando o mouse ele ACENDE."""
    from PyQt6.QtGui import QBrush, QLinearGradient, QPen, QPolygonF, QRadialGradient
    img, W, H, g = _tela(w, h, e)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    x0, y0, x1, y1 = g, g, W - g, H - g
    my = (y0 + y1) / 2
    ponta = (y1 - y0) * 0.9
    aceso = estado in ("sobre", "apertado")
    contorno = [QPointF(x0, my), QPointF(x0 + ponta, y0), QPointF(x1 - ponta, y0), QPointF(x1, my),
                QPointF(x1 - ponta, y1), QPointF(x0 + ponta, y1)]
    forma = QPainterPath()
    forma.addPolygon(QPolygonF(contorno))
    forma.closeSubpath()
    if aceso and nivel == 2:
        for k in range(7, 0, -1):            # aura
            p.setPen(QPen(QColor(190, 140, 255, 14 + 8 * (7 - k)), k * 2.4 * e))
            p.drawPath(forma)
    # facetas: faixa de cima clara, meio, faixa de baixo escura, pontas
    base = QColor("#c8a0ff") if aceso else QColor("#5a3c96")
    topo = base.lighter(150 if aceso else 120)
    fundo = base.darker(220 if aceso else 260)
    meio_y1, meio_y2 = y0 + (y1 - y0) * 0.38, y0 + (y1 - y0) * 0.62
    facetas = [
        ([QPointF(x0 + ponta, y0), QPointF(x1 - ponta, y0), QPointF(x1 - ponta * 1.6, meio_y1),
          QPointF(x0 + ponta * 1.6, meio_y1)], topo),
        ([QPointF(x0 + ponta * 1.6, meio_y1), QPointF(x1 - ponta * 1.6, meio_y1), QPointF(x1 - ponta * 1.6, meio_y2),
          QPointF(x0 + ponta * 1.6, meio_y2)], base),
        ([QPointF(x0 + ponta * 1.6, meio_y2), QPointF(x1 - ponta * 1.6, meio_y2), QPointF(x1 - ponta, y1),
          QPointF(x0 + ponta, y1)], fundo),
        ([QPointF(x0, my), QPointF(x0 + ponta, y0), QPointF(x0 + ponta * 1.6, meio_y1), QPointF(x0 + ponta * 1.6, meio_y2),
          QPointF(x0 + ponta, y1)], base.darker(140)),
        ([QPointF(x1, my), QPointF(x1 - ponta, y0), QPointF(x1 - ponta * 1.6, meio_y1), QPointF(x1 - ponta * 1.6, meio_y2),
          QPointF(x1 - ponta, y1)], base.darker(170)),
    ]
    for pts, cor in facetas:
        gr = QLinearGradient(QPointF(0, y0), QPointF(0, y1))
        c1, c2 = QColor(cor), QColor(cor)
        c1.setAlpha(235 if aceso else 215)
        c2.setAlpha(205 if aceso else 185)
        gr.setColorAt(0, c1.lighter(115))
        gr.setColorAt(1, c2)
        p.setPen(QPen(QColor(255, 255, 255, 90 if aceso else 45), 0.8 * e))
        p.setBrush(QBrush(gr))
        p.drawPolygon(QPolygonF(pts))
    if aceso:                                 # luz de dentro do cristal
        luz = QRadialGradient(QPointF(W / 2, my), (x1 - x0) * 0.45)
        luz.setColorAt(0, QColor(255, 240, 255, 150))
        luz.setColorAt(1, QColor(200, 150, 255, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(luz))
        p.drawPath(forma)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(QColor("#e8d8ff") if aceso else QColor("#8a70c0"), 1.4 * e))
    p.drawPath(forma)
    # brilhinho (reflexo) na faceta de cima
    p.setPen(QPen(QColor(255, 255, 255, 200 if aceso else 110), 1.6 * e, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(x0 + ponta * 1.2, y0 + 3 * e), QPointF(x0 + ponta * 1.2 + (x1 - x0) * 0.25, y0 + 3 * e))
    p.end()
    return img


def _botao_industrial(tema, w, h, estado, e, nivel):
    """Moderno: plaqueta industrial — chapa de aço escovado com parafusos; passando o mouse, faixa de
    alerta amarela e preta na ponta."""
    from PyQt6.QtGui import QBrush, QPen, QPolygonF
    img, W, H, g = _tela(w, h, e)
    x0, y0, x1, y1 = g, g, W - g, H - g
    corte = 8 * e
    forma = QPainterPath()
    forma.addPolygon(QPolygonF([QPointF(x0 + corte, y0), QPointF(x1, y0), QPointF(x1, y1 - corte),
                                QPointF(x1 - corte, y1), QPointF(x0, y1), QPointF(x0, y0 + corte)]))
    forma.closeSubpath()
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.fillPath(forma.translated(2 * e, 3 * e), QColor(0, 0, 0, 140))
    p.end()

    def mascara(q):
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QColor(255, 255, 255))
        q.drawPath(forma)
    m = _mascara(W, H, mascara)
    aco = metal(m, "moderno", e, perfil=3.5)
    aco[..., :3] *= (0.52 if estado != "sobre" else 0.62)       # chapa escura (o texto aparece)
    img = _compor(img, aco)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    if estado in ("sobre", "apertado"):                          # faixa de alerta
        p.setClipPath(forma)
        larg = 22 * e
        p.fillRect(QRectF(x0, y0, larg, y1 - y0), QColor("#f2c12e"))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#151515"))
        for k in range(-2, 6):
            xx = x0 + k * 10 * e
            p.drawPolygon(QPolygonF([QPointF(xx, y1), QPointF(xx + 5 * e, y1), QPointF(xx + 5 * e + (y1 - y0), y0),
                                     QPointF(xx + (y1 - y0), y0)]))
        p.setClipping(False)
    p.end()
    # parafusos nos cantos
    def parafusos(q):
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QColor(255, 255, 255))
        for px, py in ((x1 - 9 * e, y0 + 8 * e), (x0 + 9 * e if estado == "normal" else x0 + 30 * e, y1 - 8 * e)):
            q.drawEllipse(QPointF(px, py), 3.2 * e, 3.2 * e)
    img = _compor(img, metal(_mascara(W, H, parafusos), "moderno", e, perfil=1.5))
    return img


def _botao_neutro(tema, w, h, estado, e, nivel):
    """Claro/Escuro: neutro, "de programa" (tipo editor de imagem) — retângulo liso e limpo."""
    from PyQt6.QtGui import QPen
    img, W, H, g = _tela(w, h, e)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    escuro = tema == "escuro"
    fundo = {("escuro", "normal"): "#2b2d31", ("escuro", "sobre"): "#35383e", ("escuro", "apertado"): "#24262a",
             ("claro", "normal"): "#ffffff", ("claro", "sobre"): "#f0f3f8", ("claro", "apertado"): "#e4e8ee"}
    borda = ("#3d4048" if estado == "normal" else "#5a7cff") if escuro else ("#c9ced6" if estado == "normal" else "#3a6df0")
    r = QRectF(g, g, W - 2 * g, H - 2 * g)
    p.setPen(QPen(QColor(borda), 1 * e))
    p.setBrush(QColor(fundo[(tema, estado)]))
    p.drawRoundedRect(r, 5 * e, 5 * e)
    p.end()
    return img


# ====================================================================== Terror "de relatório" (v0.52.1)
FONTE_TERROR = "Courier New"     # máquina de escrever (vem em todo Windows); a corrosão é feita aqui


def _corroer(a, e, rng, forca=1.0):
    """Gasta as letras: bordas roídas, furinhos e falhas de tinta (como papel datilografado velho)."""
    H, W = a.shape
    grao = _ruido(H, W, max(1, int(1 * e)), rng)
    manchas = _ruido(H, W, max(2, int(6 * e)), rng)
    borda = _caixa_borrar(a, max(1, 1.2 * e))
    limiar = 0.5 + (grao - 0.5) * 0.55 * forca
    a2 = np.clip((borda - limiar) * 6 + 0.5, 0, 1) * a
    falha = _suave((manchas - 0.70) * 5) * 0.85 * forca
    return np.clip(a2 * (1 - falha), 0, 1)


def texto_terror(texto, px, e, cor="#d9d2c4", fantasma=True, forca=1.0, negrito=True):
    """Texto de máquina de escrever corroído, com um "fantasma" deslocado atrás (RGBA float pré-mult)."""
    c = _caminho_texto(texto, FONTE_TERROR, px, 2, e, negrito)
    r = c.boundingRect()
    m = 14 * e
    W, H = int(r.width() + 2 * m), int(r.height() + 2 * m)

    def tinta(q):
        q.translate(m - r.left(), m - r.top())
        q.fillPath(c, QColor(255, 255, 255))
    rng = _rng("terror", texto, px)
    a = _corroer(_mascara(W, H, tinta), e, rng, forca)
    out = np.zeros((H, W, 4), np.float32)
    if fantasma:   # cópia vermelha bem fraca, deslocada (dá o "arrepio" sem ficar caricato)
        fx = np.roll(a, int(3 * e), 1)
        out[..., :3] += fx[..., None] * _c("#7a0a0e") * 0.35
        out[..., 3] += fx * 0.35
    out[..., :3] = out[..., :3] * (1 - a[..., None]) + a[..., None] * _c(cor)
    out[..., 3] = np.maximum(out[..., 3] * (1 - a), 0) + a
    return out, W, H


def _botao_terror(tema, w, h, estado, e, nivel, texto=""):
    """Terror: só o texto, gasto. Passando o mouse: um contorno RABISCADO à mão e uma luz de lanterna."""
    from PyQt6.QtGui import QBrush, QPen, QRadialGradient
    img, W, H, g = _tela(w, h, e)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    x0, y0, x1, y1 = g, g, W - g, H - g
    if estado in ("sobre", "apertado"):
        luz = QRadialGradient(QPointF(W / 2, (y0 + y1) / 2), (x1 - x0) * 0.55)
        luz.setColorAt(0, QColor(230, 220, 190, 60 if estado == "sobre" else 35))
        luz.setColorAt(1, QColor(230, 220, 190, 0))
        p.fillRect(QRectF(x0, y0, x1 - x0, y1 - y0), QBrush(luz))
        rng = _rng("rabisco", w, h)
        for volta in range(2):                      # duas passadas de "caneta", tremidas
            caminho = QPainterPath()
            pts = [(x0 + 6, y0 + 3), (x1 - 4, y0 + 1), (x1 - 2, y1 - 3), (x0 + 3, y1 - 1), (x0 + 8, y0 + 2)]
            for k, (px, py) in enumerate(pts):
                px += rng.uniform(-3, 3) * e
                py += rng.uniform(-2, 2) * e
                if k == 0:
                    caminho.moveTo(px, py)
                else:
                    caminho.lineTo(px, py)
            p.setPen(QPen(QColor(220, 210, 190, 170 if volta == 0 else 90), (1.4 if volta == 0 else 0.9) * e,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(caminho)
    p.end()
    if texto:
        rgba, tw, th = texto_terror(texto, 19, e, "#fff6e6" if estado == "sobre" else "#c9c1b2",
                                    fantasma=estado == "sobre", forca=1.35)
        camada = np.zeros((img.height(), img.width(), 4), np.float32)
        ox = int((img.width() - tw) / 2)
        # botão com linha pequena embaixo (mais alto): a letra sobe pra dar lugar a ela
        oy = int(g - 3 * e) if h >= 50 else int((img.height() - th) / 2) - int(2 * e)
        xa, ya = max(0, ox), max(0, oy)
        xb, yb = min(img.width(), ox + tw), min(img.height(), oy + th)
        camada[ya:yb, xa:xb] = rgba[ya - oy:yb - oy, xa - ox:xb - ox]
        img = _compor(img, camada)
    return img


def _logo_terror(tema, familia, e):
    """Terror: TAVERNA datilografado, gasto, cor de osso, com o fantasma vermelho — sem enfeite."""
    rgba, W, H = texto_terror("TAVERNA", 110, e, "#e2dccf", fantasma=True, forca=1.6)
    out = (np.clip(rgba, 0, 1) * 255).astype(np.uint8)
    return _qimg(out)


def grao(lado=256):
    """Granulado de filme (repete sem emenda) pra pôr por cima da tela no Terror."""
    chave = ("grao", lado)
    if chave in _CACHE:
        return _CACHE[chave]
    rng = np.random.default_rng(7)
    v = rng.random((lado, lado)).astype(np.float32)
    a = np.abs(v - 0.5) * 2
    rgba = np.zeros((lado, lado, 4), np.uint8)
    claro = v > 0.5
    rgba[..., 3] = (a ** 2 * 70).astype(np.uint8)
    rgba[..., 0] = rgba[..., 1] = rgba[..., 2] = np.where(claro, rgba[..., 3], 0)
    img = _qimg(rgba)
    _CACHE[chave] = img
    return img


def varredura():
    """Linhas de varredura de câmera (uma linha escura a cada 3 px) — repete."""
    chave = ("varredura",)
    if chave in _CACHE:
        return _CACHE[chave]
    rgba = np.zeros((6, 8, 4), np.uint8)
    rgba[0::3, :, 3] = 90
    img = _qimg(rgba)
    _CACHE[chave] = img
    return img


# ====================================================================== cenário do Terror (v0.52.1)
def ceu_terror(w, h, pos_lua=None, vermelha=False):
    """Céu noturno frio, com nuvens ralas e um clarão onde fica a lua (o resto é animado no QML)."""
    pos_lua = pos_lua or LUA_TERROR
    chave = ("ceu_terror", w, h, pos_lua, vermelha)
    if chave in _CACHE:
        return _CACHE[chave]
    W, H = int(w), int(h)
    rng = _rng("ceu_terror", W, H)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    t = ys / H
    cor = _c("#0b0d12") * (1 - t[..., None]) + _c("#16181c") * t[..., None]
    nuvem = _ruido(H, W, 40, rng) * 0.6 + _ruido(H, W, 12, rng) * 0.4
    nuvem = _suave((nuvem - 0.45) * 2.2) * (1 - t) * 0.5
    cor = cor + nuvem[..., None] * _c("#2a2e36")
    lx, ly = pos_lua[0] * W, pos_lua[1] * H                       # clarão da lua no céu
    d = np.sqrt((xs - lx) ** 2 + (ys - ly) ** 2) / max(W, H)
    cor += (np.exp(-(d / 0.18) ** 2) * 0.16)[..., None] * (_c("#c04030") if vermelha else _c("#9aa4b8"))
    if vermelha:   # lua de sangue: o céu todo puxa pro vermelho
        cor = cor * np.array([1.25, 0.9, 0.88], np.float32)
    for _ in range(140):                                            # estrelinhas fracas
        x, y = int(rng.uniform(0, W)), int(rng.uniform(0, H * 0.5))
        cor[y, x] += rng.uniform(0.1, 0.35)
    rgba = np.empty((H, W, 4), np.uint8)
    rgba[..., :3] = (np.clip(cor, 0, 1) * 255).astype(np.uint8)
    rgba[..., 3] = 255
    img = _qimg(rgba)
    _CACHE[chave] = img
    return img


LUA_TERROR = (0.82, 0.2)


def lua(lado=320, fase=0.5, vermelha=False):
    """A lua (v0.53, referência: foto da lua cheia do Manel): planaltos claros e quentes, MARES escuros com
    manchas por dentro, muitas crateras pequenas (borda clara do lado do sol, sombra do outro), os RAIOS
    claros saindo de duas crateras jovens e a borda levemente mais escura.
    fase: 0 = nova · 0.25 = crescente · 0.5 = cheia · 0.75 = minguante. vermelha: lua de sangue.
    O lado escuro tem um restinho de luz ("luz da Terra"), pra a lua nova não sumir de vez."""
    chave = ("lua", lado, round(fase, 2), vermelha)
    if chave in _CACHE:
        return _CACHE[chave]
    rng = _rng("lua-detalhe")
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
    c = lado / 2
    r = lado * 0.46
    dx, dy = (xs - c) / r, (ys - c) / r
    d2 = dx * dx + dy * dy
    disco = np.clip((1 - np.sqrt(d2)) * r, 0, 1)
    z = np.sqrt(np.clip(1 - d2, 0, 1))
    # --- planaltos e mares
    base_mar = _ruido(lado, lado, 34, rng) * 0.7 + _ruido(lado, lado, 12, rng) * 0.3
    limiar = float(np.percentile(base_mar, 60))
    mares = _suave((base_mar - limiar) / 0.04)
    dentro_mar = _ruido(lado, lado, 5, rng)
    fino = _ruido(lado, lado, 1, rng) * 0.6 + _ruido(lado, lado, 2, rng) * 0.4
    planalto = _c("#efe5cc") * (0.86 + 0.2 * fino[..., None])
    mar = _c("#8e877a") * (0.8 + 0.35 * dentro_mar[..., None]) * (0.92 + 0.12 * fino[..., None])
    cor = planalto * (1 - mares[..., None]) + mar * mares[..., None]
    alt = (fino - 0.5) * 0.02 - mares * 0.01               # relevo (pra sombra das crateras perto do terminador)
    # --- crateras (muitas pequenas, poucas grandes)
    for _ in range(90):
        cx, cy = rng.uniform(-0.95, 0.95), rng.uniform(-0.95, 0.95)
        if cx * cx + cy * cy > 0.92:
            continue
        rr = float(0.012 + rng.pareto(2.2) * 0.012)
        rr = min(rr, 0.09)
        dc = np.sqrt((dx - cx) ** 2 + (dy - cy) ** 2) / rr
        perto = dc < 1.6
        if not perto.any():
            continue
        bacia = _suave(1 - dc[perto]) * 1.0
        aro = np.exp(-((dc[perto] - 1) / 0.25) ** 2)
        alt[perto] += (aro * 0.5 - bacia * 0.8) * rr
        cor[perto] *= (1 - bacia * 0.06)[..., None]
        cor[perto] += (aro * 0.025)[..., None]
    # --- raios de crateras jovens (como a de baixo na foto): manchas claras compridas, irregulares e macias
    for (rx, ry, forca, n) in ((-0.12, 0.6, 0.42, 23), (-0.42, -0.05, 0.22, 15)):
        ang = np.arctan2(dy - ry, dx - rx)
        dr = np.sqrt((dx - rx) ** 2 + (dy - ry) ** 2)
        tremido = _ruido(lado, lado, 3, rng)
        quebra = _ruido(lado, lado, 4, rng)
        raios = (np.clip(np.cos(ang * n + tremido * 7) * 0.5 + 0.5, 0, 1) ** 4) * np.exp(-dr / 0.5)
        raios *= _suave((quebra - 0.3) * 2.5)                  # raios que somem e voltam
        raios = _caixa_borrar(raios.astype(np.float32), max(1, lado // 160))
        halo = np.exp(-(dr / 0.09) ** 2) * 0.6
        cor = cor + ((raios + halo) * forca)[..., None] * _c("#fff8e8")
    # --- iluminação pela fase (o sol gira em volta: cheia = de frente)
    ang_sol = (fase - 0.5) * 2 * math.pi                    # 0 = de frente (cheia), ±π = de trás (nova)
    sol = np.array([math.sin(ang_sol), -0.05, math.cos(ang_sol)], np.float32)
    sol /= np.linalg.norm(sol)
    gy, gx = np.gradient(_caixa_borrar(alt.astype(np.float32), 1) * lado)
    n = np.dstack([dx - gx * 0.12, dy - gy * 0.12, z])
    n /= np.maximum(np.linalg.norm(n, axis=2, keepdims=True), 1e-6)
    lam = n @ sol
    luz = _suave(np.clip(lam * 3 + 0.12, 0, 1)) * (0.78 + 0.22 * np.clip(lam, 0, 1))
    luz = np.maximum(luz, 0.05)                              # luz da Terra no lado escuro
    borda = 0.82 + 0.18 * z ** 0.4                           # bordinha mais escura
    cor = cor * (luz * borda)[..., None]
    if vermelha:   # lua de sangue: o vermelho cobre tudo, mais escura
        cor = cor * np.array([1.05, 0.42, 0.30], np.float32) * 0.9
    a = disco
    rgba = np.zeros((lado, lado, 4), np.uint8)
    rgba[..., :3] = (np.clip(cor, 0, 1) * a[..., None] * 255).astype(np.uint8)
    rgba[..., 3] = (a * 255).astype(np.uint8)
    img = _qimg(rgba)
    _CACHE[chave] = img
    return img


def arvore_morta(variante=0, escala=1.0):
    """Silhueta de árvore morta (galhos tortos, finos nas pontas). A base fica embaixo no meio."""
    from PyQt6.QtGui import QPen
    chave = ("arvore", variante, round(escala, 2))
    if chave in _CACHE:
        return _CACHE[chave]
    e = escala
    W, H = int(360 * e), int(420 * e)
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    rng = _rng("arvore", variante)
    cor = QColor(8, 8, 10)

    def galho(x, y, ang, comp, larg, nivel):
        if nivel > 7 or comp < 6 * e:
            return
        segs = 4
        cx, cy = x, y
        for _ in range(segs):
            ang += rng.uniform(-0.28, 0.28)
            nx = cx + math.cos(ang) * comp / segs
            ny = cy + math.sin(ang) * comp / segs
            p.setPen(QPen(cor, max(0.7 * e, larg), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(cx, cy), QPointF(nx, ny))
            larg *= 0.88
            cx, cy = nx, ny
        filhos = 2 if nivel < 2 else int(rng.integers(1, 4))
        for _ in range(filhos):
            galho(cx, cy, ang + rng.uniform(-0.9, 0.9), comp * rng.uniform(0.55, 0.78), larg * 0.72, nivel + 1)

    galho(W / 2, H, -math.pi / 2 + rng.uniform(-0.12, 0.12), H * 0.42, 15 * e, 0)
    p.end()
    _CACHE[chave] = img
    return img


def faixa_nevoa(variante=0, w=1024, h=220):
    """Faixa de névoa macia que repete na horizontal (várias dessas, em alturas e velocidades diferentes,
    dão a névoa "volumétrica")."""
    chave = ("nevoa", variante, w, h)
    if chave in _CACHE:
        return _CACHE[chave]
    rng = _rng("nevoa", variante)
    n = _ruido(h, w, 26, rng) * 0.65 + _ruido(h, w, 9, rng) * 0.35
    # emenda nas pontas (repete sem costura)
    m = 80
    t = np.linspace(0, 1, m, dtype=np.float32)[None, :]
    n[:, :m] = n[:, :m] * t + n[:, -m:][:, ::-1] * 0 + n[:, -m:] * (1 - t)
    ys = np.linspace(-1, 1, h, dtype=np.float32)[:, None]
    perfil = np.exp(-(ys / 0.55) ** 2)                      # mais densa no meio da faixa
    a = np.clip((n - 0.32) * 1.6, 0, 1) * perfil * 0.75
    rgba = np.zeros((h, w, 4), np.uint8)
    cinza = np.array([150, 156, 168], np.float32) / 255
    rgba[..., :3] = (cinza * a[..., None] * 255).astype(np.uint8)
    rgba[..., 3] = (a * 255).astype(np.uint8)
    img = _qimg(rgba)
    _CACHE[chave] = img
    return img


def morros_terror(w, h):
    """Os morros escuros da frente (silhueta), com um pouco de luz da lua na crista."""
    chave = ("morros", w, h)
    if chave in _CACHE:
        return _CACHE[chave]
    W, H = int(w), int(h)
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    for k, (base, amp, cor) in enumerate(((0.80, 0.05, QColor(18, 19, 22)), (0.88, 0.04, QColor(9, 9, 11)))):
        c = QPainterPath(QPointF(0, H))
        for i in range(0, 41):
            x = W * i / 40
            y = H * (base + amp * math.sin(i * 0.55 + k * 2) + amp * 0.5 * math.sin(i * 1.7 + k))
            c.lineTo(x, y)
        c.lineTo(W, H)
        c.closeSubpath()
        p.fillPath(c, cor)
    p.end()
    _CACHE[chave] = img
    return img


# ====================================================================== Moderno "de hoje" (v0.52.1)
def _botao_moderno(tema, w, h, estado, e, nivel):
    """Moderno: botão translúcido arredondado (vidro), e no mouse uma barrinha de destaque + preenchimento."""
    from PyQt6.QtGui import QBrush, QLinearGradient, QPen
    img, W, H, g = _tela(w, h, e)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    r = QRectF(g, g, W - 2 * g, H - 2 * g)
    raio = 10 * e
    destaque = QColor("#4fd1c5")
    if estado == "normal":
        p.setPen(QPen(QColor(255, 255, 255, 38), 1 * e))
        p.setBrush(QColor(255, 255, 255, 18))
        p.drawRoundedRect(r, raio, raio)
    else:
        cor = QLinearGradient(r.topLeft(), r.topRight())
        c0 = QColor(destaque)
        c0.setAlpha(110 if estado == "sobre" else 150)
        c1 = QColor(destaque)
        c1.setAlpha(18)
        cor.setColorAt(0, c0)
        cor.setColorAt(1, c1)
        p.setPen(QPen(QColor(79, 209, 197, 150), 1 * e))
        p.setBrush(QBrush(cor))
        p.drawRoundedRect(r, raio, raio)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(destaque)
        p.drawRoundedRect(QRectF(r.left() + 6 * e, r.top() + r.height() * 0.22, 4 * e, r.height() * 0.56), 2 * e, 2 * e)
    p.end()
    return img


def _logo_moderno(tema, familia, e):
    """Moderno: palavra-marca limpa (Bebas Neue, branca) com um tracinho de destaque — cara de app de hoje."""
    from PyQt6.QtGui import QBrush, QLinearGradient
    c = _caminho_texto("TAVERNA", "Bebas Neue", 120, 10, e)
    r = c.boundingRect()
    m = 16 * e
    W, H = int(r.width() + 2 * m), int(r.height() + 2 * m + 18 * e)
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.translate(m - r.left(), m - r.top())
    p.fillPath(c.translated(0, 3 * e), QColor(0, 0, 0, 90))
    p.fillPath(c, QColor("#f4f7fa"))
    y = r.bottom() + 12 * e
    gr = QLinearGradient(QPointF(r.left(), 0), QPointF(r.left() + r.width() * 0.3, 0))
    gr.setColorAt(0, QColor("#4fd1c5"))
    gr.setColorAt(1, QColor(79, 209, 197, 0))
    p.fillRect(QRectF(r.left() + 2 * e, y, r.width() * 0.3, 4 * e), QBrush(gr))
    p.end()
    return img


# ====================================================================== cada tema com o SEU título (v0.52)
def logo_tema(tema, familia, escala=1.0, nivel=2):
    if nivel == 0 or tema == "medieval":
        return logo(tema, familia, escala, nivel)
    chave = ("logo_tema", tema, familia, round(escala, 2), nivel)
    if chave in _CACHE:
        return _CACHE[chave]
    f = {"terror": _logo_terror, "futurista": _logo_neon, "magico": _logo_magico, "moderno": _logo_moderno,
         "claro": _logo_neutro, "escuro": _logo_neutro}.get(tema)
    img = f(tema, familia, escala) if f else logo(tema, familia, escala, nivel)
    _CACHE[chave] = img
    return img


def _caminho_texto(texto, familia, px, espaco, e, negrito=False):
    fonte = QFont(familia)
    fonte.setPixelSize(int(px * e))
    fonte.setBold(negrito)
    fonte.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, espaco * e)
    c = QPainterPath()
    c.addText(QPointF(0, 0), fonte, texto)
    return c


def _logo_neutro(tema, familia, e):
    """Claro/Escuro: só a palavra, bem objetiva."""
    c = _caminho_texto("Taverna", "Segoe UI Semibold", 88, 1, e)
    r = c.boundingRect()
    m = 8 * e
    img = QImage(int(r.width() + 2 * m), int(r.height() + 2 * m), QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.translate(m - r.left(), m - r.top())
    p.fillPath(c, QColor("#e9eaee" if tema == "escuro" else "#1d1f24"))
    p.end()
    return img


def _logo_neon(tema, familia, e):
    """Futurista: letras de TUBO DE NEON (contorno aceso, com brilho) e um traço magenta."""
    from PyQt6.QtGui import QPen
    c = _caminho_texto("TAVERNA", familia, 100, 14, e)
    r = c.boundingRect()
    m = 34 * e
    W, H = int(r.width() + 2 * m), int(r.height() + 2 * m + 26 * e)
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.translate(m - r.left(), m - r.top())
    for k in range(9, 0, -1):                       # brilho do neon (largo e fraco → fino e forte)
        p.setPen(QPen(QColor(56, 225, 255, 10 + 9 * (9 - k)), k * 2.6 * e, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.drawPath(c)
    p.setPen(QPen(QColor("#7ff0ff"), 3.2 * e, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.drawPath(c)
    p.setPen(QPen(QColor("#ffffff"), 1.2 * e, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.drawPath(c)                                   # o filamento branco no meio do tubo
    y = r.bottom() + 18 * e
    for k in range(5, 0, -1):
        p.setPen(QPen(QColor(255, 63, 164, 16 + 14 * (5 - k)), k * 2.4 * e, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(r.left() + r.width() * 0.08, y), QPointF(r.right() - r.width() * 0.08, y))
    p.setPen(QPen(QColor("#ffd0ea"), 1.4 * e, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(r.left() + r.width() * 0.08, y), QPointF(r.right() - r.width() * 0.08, y))
    p.end()
    return img


def _logo_magico(tema, familia, e):
    """Mágico: as letras desenhadas por uma LINHA MÁGICA brilhando (violeta e azul-água), com faíscas."""
    from PyQt6.QtGui import QBrush, QLinearGradient, QPen
    c = _caminho_texto("TAVERNA", familia, 104, 8, e)
    r = c.boundingRect()
    m = 34 * e
    W, H = int(r.width() + 2 * m), int(r.height() + 2 * m)
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.translate(m - r.left(), m - r.top())
    p.fillPath(c, QColor(30, 10, 60, 150))          # dentro: um véu escuro
    grad = QLinearGradient(QPointF(r.left(), 0), QPointF(r.right(), 0))
    grad.setColorAt(0, QColor("#b48cff"))
    grad.setColorAt(0.5, QColor("#e8d8ff"))
    grad.setColorAt(1, QColor("#5fe0d0"))
    for k in range(7, 0, -1):
        p.setPen(QPen(QColor(180, 140, 255, 12 + 10 * (7 - k)), k * 2.4 * e, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawPath(c)
    p.setPen(QPen(QBrush(grad), 2.0 * e, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.drawPath(c)
    # faíscas (estrelinhas de 4 pontas) em volta das letras
    rng = _rng("faiscas", W)
    for _ in range(26):
        x = rng.uniform(r.left(), r.right())
        y = rng.uniform(r.top() - 10 * e, r.bottom() + 10 * e)
        t = rng.uniform(2, 6) * e
        estrela = QPainterPath(QPointF(x, y - t))
        estrela.quadTo(QPointF(x, y), QPointF(x + t, y))
        estrela.quadTo(QPointF(x, y), QPointF(x, y + t))
        estrela.quadTo(QPointF(x, y), QPointF(x - t, y))
        estrela.quadTo(QPointF(x, y), QPointF(x, y - t))
        p.fillPath(estrela, QColor(255, 250, 255, int(rng.uniform(120, 255))))
    p.end()
    return img


def _logo_sangue(tema, familia, e):
    """Terror: letras de sangue seco, escorrendo, com arranhões."""
    c = _caminho_texto("TAVERNA", familia, 112, 10, e)
    r = c.boundingRect()
    m = 20 * e
    W, H = int(r.width() + 2 * m), int(r.height() + 2 * m + 60 * e)
    rng = _rng("sangue", W)

    def mascara(q):
        q.translate(m - r.left(), m - r.top())
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QColor(255, 255, 255))
        q.drawPath(c)
        for _ in range(16):                          # escorridos (gotas descendo da base das letras)
            x = rng.uniform(r.left() + 8, r.right() - 8)
            comp = rng.uniform(10, 58) * e
            larg = rng.uniform(2.0, 4.4) * e
            if not c.contains(QPointF(x, r.bottom() - 6 * e)):
                continue
            q.drawRoundedRect(QRectF(x - larg / 2, r.bottom() - 10 * e, larg, comp), larg / 2, larg / 2)
            q.drawEllipse(QPointF(x, r.bottom() - 10 * e + comp), larg * 0.85, larg * 1.1)
    a = _mascara(W, H, mascara)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    arranhao = np.zeros_like(a)
    for _ in range(5):
        y = rng.uniform(m, H - 60 * e)
        incl = rng.uniform(-0.12, 0.12)
        arranhao = np.maximum(arranhao, (np.abs(ys - (y + (xs - W / 2) * incl)) < 0.8 * e).astype(np.float32))
    a = a * (1 - arranhao * 0.9)
    t = _suave((ys - m) / max(1, H - m))
    cor = _c("#9a1018") * (1 - t[..., None]) + _c("#3a0306") * t[..., None]
    cor *= (0.75 + 0.35 * _ruido(H, W, 3, rng))[..., None]
    alt = _caixa_borrar(a, 2 * e) * a
    rgba = iluminar(cor.astype(np.float32), alt * 6 * e, np.full_like(a, 0.7), None, a, forca=1.2 / e,
                    contorno=0.2, ambiente=0.5).astype(np.float32) / 255
    sombra = np.roll(np.roll(_caixa_borrar(a, 5 * e), int(4 * e), 0), int(3 * e), 1) * 0.7
    base = np.zeros((H, W, 4), np.float32)
    base[..., 3] = sombra
    la = rgba[..., 3:4]
    base = rgba + base * (1 - la)
    out = (np.clip(base, 0, 1) * 255).astype(np.uint8)
    return _qimg(out)


def _logo_industrial(tema, familia, e):
    """Moderno: placa de aço industrial — letras de aço sobre uma chapa com parafusos e faixa de alerta."""
    from PyQt6.QtGui import QPolygonF
    c = _caminho_texto("TAVERNA", "Bebas Neue", 108, 12, e)
    r = c.boundingRect()
    m = 26 * e
    W, H = int(r.width() + 2 * m), int(r.height() + 2 * m + 16 * e)

    def chapa(q):
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QColor(255, 255, 255))
        k = 10 * e
        q.drawPolygon(QPolygonF([QPointF(k, 0), QPointF(W, 0), QPointF(W, H - k), QPointF(W - k, H),
                                 QPointF(0, H), QPointF(0, k)]))
    placa = metal(_mascara(W, H, chapa), "moderno", e, perfil=4)
    placa[..., :3] *= 0.32
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    img = _compor(img, placa)

    def letras(q):
        q.translate(m - r.left(), m - r.top())
        q.fillPath(c, QColor(255, 255, 255))
    img = _compor(img, metal(_mascara(W, H, letras), "moderno", e, perfil=2.6))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # faixa de alerta embaixo
    faixa = QRectF(14 * e, H - 14 * e, W - 28 * e, 6 * e)
    p.setClipRect(faixa)
    p.fillRect(faixa, QColor("#f2c12e"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#151515"))
    xx = faixa.left() - 20 * e
    while xx < faixa.right():
        p.drawPolygon(QPolygonF([QPointF(xx, faixa.bottom()), QPointF(xx + 6 * e, faixa.bottom()),
                                 QPointF(xx + 12 * e, faixa.top()), QPointF(xx + 6 * e, faixa.top())]))
        xx += 12 * e
    p.end()

    def parafusos(q):
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QColor(255, 255, 255))
        for px, py in ((12 * e, 12 * e), (W - 12 * e, 12 * e), (12 * e, H - 22 * e), (W - 12 * e, H - 22 * e)):
            q.drawEllipse(QPointF(px, py), 4 * e, 4 * e)
    return _compor(img, metal(_mascara(W, H, parafusos), "moderno", e, perfil=1.6))


def logo(tema, familia, escala=1.0, nivel=2):
    """TAVERNA em metal + ornamento (filigrana e gema em cima, risco embaixo)."""
    from PyQt6.QtGui import QBrush, QLinearGradient, QPen, QRadialGradient
    chave = ("logo", tema, familia, round(escala, 2), nivel)
    if chave in _CACHE:
        return _CACHE[chave]
    e = escala
    letras = titulo(tema, "TAVERNA", familia, 104, 10, e)
    c1, c2, c3, borda = METAL_TITULO.get(tema, METAL_TITULO["medieval"])
    W = letras.width()
    topo = int(46 * e)
    base = int(40 * e)
    H = letras.height() + topo + base
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    cx = W / 2
    y = topo - 8 * e
    yb = topo + letras.height() - 22 * e

    def ornamento(q):
        branco = QColor(255, 255, 255)
        q.setBrush(Qt.BrushStyle.NoBrush)
        for sx in (-1, 1):   # filigrana: arcos saindo da ponta central, com voltinhas nas pontas
            q.setPen(QPen(branco, 3.6 * e, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            arco = QPainterPath(QPointF(cx + sx * 14 * e, y))
            arco.cubicTo(QPointF(cx + sx * 80 * e, y - 30 * e), QPointF(cx + sx * 160 * e, y + 6 * e),
                         QPointF(cx + sx * W * 0.40, y - 4 * e))
            q.drawPath(arco)
            q.drawEllipse(QPointF(cx + sx * W * 0.40 + sx * 4 * e, y - 8 * e), 4 * e, 4 * e)
            q.setPen(QPen(branco, 2.0 * e, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            arco2 = QPainterPath(QPointF(cx + sx * 34 * e, y + 6 * e))
            arco2.cubicTo(QPointF(cx + sx * 64 * e, y - 10 * e), QPointF(cx + sx * 96 * e, y + 12 * e),
                          QPointF(cx + sx * 128 * e, y + 3 * e))
            q.drawPath(arco2)
            # traço de baixo, afinando
            q.setPen(QPen(branco, 2.6 * e, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            q.drawLine(QPointF(cx + sx * 16 * e, yb + 30 * e), QPointF(cx + sx * W * 0.34, yb + 30 * e))
            q.setPen(QPen(branco, 1.4 * e, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            q.drawLine(QPointF(cx + sx * W * 0.34, yb + 30 * e), QPointF(cx + sx * W * 0.42, yb + 30 * e))
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(branco)
        ponta = QPainterPath()   # ponta de lança em cima
        ponta.moveTo(cx, y - 40 * e)
        ponta.lineTo(cx + 11 * e, y - 6 * e)
        ponta.lineTo(cx, y + 8 * e)
        ponta.lineTo(cx - 11 * e, y - 6 * e)
        ponta.closeSubpath()
        q.drawPath(ponta)
        los = QPainterPath()     # losango embaixo
        los.moveTo(cx, yb + 20 * e)
        los.lineTo(cx + 10 * e, yb + 30 * e)
        los.lineTo(cx, yb + 40 * e)
        los.lineTo(cx - 10 * e, yb + 30 * e)
        los.closeSubpath()
        q.drawPath(los)

    if nivel >= 1:
        img = _compor(img, metal(_mascara(W, H, ornamento), tema, e, perfil=2.4))
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cor_gema = QColor(ESTILO_BOTAO.get(tema, ESTILO_BOTAO["medieval"])[3])
        for gx, gy, r in ((cx, y - 10 * e, 4.6 * e), (cx, yb + 30 * e, 3.6 * e)):   # gemas engastadas
            gema = QRadialGradient(QPointF(gx - r * 0.4, gy - r * 0.4), r * 1.6)
            gema.setColorAt(0, QColor("#ffffff"))
            gema.setColorAt(0.35, cor_gema)
            gema.setColorAt(1, cor_gema.darker(320))
            p.setPen(QPen(QColor(0, 0, 0, 160), 0.8 * e))
            p.setBrush(QBrush(gema))
            p.drawEllipse(QPointF(gx, gy), r, r)
        p.drawImage(0, topo, letras)
        p.end()
    else:
        p = QPainter(img)
        p.drawImage(0, topo, letras)
        p.end()
    _CACHE[chave] = img
    return img


# ====================================================================== MESA DA TAVERNA (fundo do Medieval, v0.53)
# Ideia do Manel: em vez do muro, a mesa da taverna (o nome do programa!) — suja, com moedas, caneca de
# cerveja, um d20 e uma vela que ilumina tudo. Vista de quem está sentado: perspectiva, tábuas fugindo.
VELA = (0.18, 0.45)         # onde fica a chama da vela (0..1 da tela) — o QML põe o fogo aí


def _amostrar(tex, u, v):
    """Lê uma textura (N×N) em coordenadas quaisquer (repete)."""
    N = tex.shape[0]
    return tex[(v.astype(np.int64)) % N, (u.astype(np.int64)) % N]


def mesa_taverna(w, h):
    chave = ("mesa_taverna", w, h)
    if chave in _CACHE:
        return _CACHE[chave]
    W, H = int(w), int(h)
    rng = _rng("mesa", 1)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    # --- perspectiva: o horizonte fica acima da tela; quanto mais pra cima, mais longe
    yh = -2.4 * H                                          # horizonte bem acima: perspectiva suave
    prof = (ys - yh) / H                                   # 2.4 (fundo) .. 3.4 (perto)
    u = (xs - W / 2) * (2.9 / prof)                        # lado (as tábuas convergem de leve)
    v = 2600.0 / prof                                      # distância
    larg_tab = 165.0
    tab = np.floor(u / larg_tab)
    lu = u - tab * larg_tab
    ruido_a = _ruido(256, 256, 8, rng)
    ruido_b = _ruido(256, 256, 2, rng)
    tom_tab = _rng("tons").random(256).astype(np.float32)
    t_id = (tab.astype(np.int64) % 256)
    # veio da madeira: linhas FINAS correndo ao longo da tábua + fibras (desenhado, não foto)
    onda = np.sin(lu * 0.16 + _amostrar(ruido_a, lu * 0.35, v * 0.12) * 3.0 + t_id * 1.7)
    veio = _suave((np.abs(onda) - 0.94) * 14)
    fibra = _amostrar(ruido_b, lu * 3, v * 0.25)
    base = _c("#5e3c22") * (0.78 + 0.4 * tom_tab[t_id])[..., None]
    cor = base * (1 - veio[..., None] * 0.28) * (0.88 + 0.2 * fibra[..., None])
    # juntas entre as tábuas (escuras e fundas) e quina gasta (clara)
    junta = np.minimum(lu, larg_tab - lu) * prof
    sulco = _suave(1 - junta / 3.5)
    quina = np.exp(-((junta - 4.5) / 1.6) ** 2) * 0.18
    cor = cor * (1 - sulco[..., None] * 0.8) + quina[..., None] * _c("#b88a58")
    # sujeira: marcas de caneca (anéis), bebida derramada, arranhões, gotas de cera
    sujo = np.zeros((H, W), np.float32)
    for (ru, rv, rr) in ((-420, 900, 50), (520, 880, 44), (-160, 1020, 40), (330, 1050, 56)):
        d = np.sqrt((u - ru) ** 2 + ((v - rv) * 2.2) ** 2)
        sujo += np.exp(-((d - rr) / 4) ** 2) * 0.55
    mancha = np.exp(-(((u + 60) / 240) ** 2 + ((v - 960) / 50) ** 2) ** 1.2) * \
        (0.6 + 0.4 * _amostrar(ruido_a, u * 0.3, v * 0.6))
    sujo += _suave(mancha * 1.5) * 0.6
    cor = cor * (1 - sujo[..., None] * 0.45)
    for _ in range(30):                                    # arranhões de faca
        a0u, a0v = rng.uniform(-900, 900), rng.uniform(770, 1080)
        ang = rng.uniform(0, math.pi)
        comp = rng.uniform(30, 120)
        du, dv = math.cos(ang), math.sin(ang) * 0.4
        t = np.clip(((u - a0u) * du + (v - a0v) * dv) / comp, 0, 1)
        dist = np.sqrt((u - a0u - t * comp * du) ** 2 + (v - a0v - t * comp * dv) ** 2) * prof
        risco = np.exp(-(dist / 0.9) ** 2) * 0.35
        cor = cor + risco[..., None] * _c("#c09060")
    # --- luz: a vela (quente) + um pouco de luz ambiente fria de cima
    vx, vy = VELA[0] * W, VELA[1] * H + 0.17 * H           # o pé da vela
    dist = np.sqrt((xs - vx) ** 2 + ((ys - vy) * 1.5) ** 2) / H          # distância na tela (≈ na mesa)
    luz_vela = 2.3 / (1 + (dist / 0.32) ** 2)
    ambiente = 0.10 + 0.06 * (1 - ys / H)
    luz = ambiente + luz_vela
    rgb = cor * luz[..., None] * np.array([1.0, 0.80, 0.58], np.float32)
    rgb += (np.exp(-(dist / 0.12) ** 2) * 0.10)[..., None] * _c("#ffb060")
    # vinheta
    vin = 1 - _suave(np.sqrt(((xs / W - 0.5) * 1.5) ** 2 + ((ys / H - 0.5) * 1.6) ** 2) - 0.3) * 0.7
    rgb *= vin[..., None]
    rgba = np.empty((H, W, 4), np.uint8)
    rgba[..., :3] = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    rgba[..., 3] = 255
    img = _objetos_mesa(_qimg(rgba), W, H, (vx, vy - 0.17 * H))
    _CACHE[chave] = img
    return img


# ---- texturas da MESA 3D (v0.53): vistas de cima, sem perspectiva (o 3D faz a perspectiva)
def _tampo(lado=1024):
    """(cor, altura) do tampo da mesa: tábuas com veios, juntas, nós, marcas de caneca, mancha e arranhões."""
    chave = ("tampo", lado)
    if chave in _CACHE:
        return _CACHE[chave]
    rng = _rng("tampo")
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
    larg = lado / 6
    tab = np.floor(xs / larg)
    lu = xs - tab * larg
    ra = _ruido(lado, lado, 24, rng)
    rb = _ruido(lado, lado, 2, rng)
    fibra = _caixa_borrar(rng.random((lado, lado)).astype(np.float32), 1)
    fibra = _caixa_borrar(fibra.T, 6).T                     # fibras compridas ao longo da tábua
    fibra = (fibra - fibra.min()) / max(1e-6, float(np.ptp(fibra)))
    tons = _rng("tons-tampo").random(16).astype(np.float32)
    t_id = tab.astype(np.int64) % 16
    onda = np.sin(lu * 0.12 + ra * 7 + t_id * 1.7 + ys * 0.004)
    veio = _suave((np.abs(onda) - 0.9) * 10)
    cor = _c("#6a4426") * (0.75 + 0.45 * tons[t_id])[..., None]
    cor = cor * (1 - veio[..., None] * 0.3) * (0.82 + 0.3 * fibra[..., None]) * (0.92 + 0.1 * rb[..., None])
    junta = np.minimum(lu, larg - lu)
    alt = _suave(junta / 6) * 1.0 - veio * 0.08 + fibra * 0.06
    cor *= (0.35 + 0.65 * _suave(junta / 4))[..., None]
    for _ in range(3):                                      # nós (poucos e suaves: repetidos viram "furos")
        cx, cy = rng.uniform(0, lado), rng.uniform(0, lado)
        dn = np.sqrt(((xs - cx) / 14) ** 2 + ((ys - cy) / 30) ** 2)
        m = dn < 1.3
        cor[m] *= (0.78 + 0.16 * np.cos(dn[m] * 8))[..., None]
        alt[m] -= 0.1
    sujo = np.zeros((lado, lado), np.float32)
    for _ in range(5):                                      # marcas de caneca (anéis)
        cx, cy, rr = rng.uniform(80, lado - 80), rng.uniform(80, lado - 80), rng.uniform(34, 52)
        d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
        sujo += np.exp(-((d - rr) / 3) ** 2) * rng.uniform(0.4, 0.7)
    mancha = _suave((_ruido(lado, lado, 40, rng) - 0.7) * 5)
    sujo += mancha * 0.5
    cor *= (1 - sujo[..., None] * 0.5)
    for _ in range(60):                                     # arranhões de faca (claros e fundos)
        x0, y0 = rng.uniform(0, lado), rng.uniform(0, lado)
        ang = rng.uniform(0, math.pi)
        comp = rng.uniform(20, 120)
        dx, dy = math.cos(ang), math.sin(ang)
        t = np.clip(((xs - x0) * dx + (ys - y0) * dy) / comp, 0, 1)
        d = np.sqrt((xs - x0 - t * comp * dx) ** 2 + (ys - y0 - t * comp * dy) ** 2)
        risco = np.exp(-(d / 0.8) ** 2)
        cor += risco[..., None] * _c("#a07040") * 0.35
        alt -= risco * 0.25
    _CACHE[chave] = (np.clip(cor, 0, 1).astype(np.float32), alt.astype(np.float32))
    return _CACHE[chave]


def _rgb_img(rgb):
    h, w = rgb.shape[:2]
    rgba = np.empty((h, w, 4), np.uint8)
    rgba[..., :3] = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    rgba[..., 3] = 255
    return _qimg(rgba)


def _normal_de(alt, forca=4.0):
    gy, gx = np.gradient(alt)
    n = np.dstack([-gx * forca, gy * forca, np.ones_like(alt)])   # (normal "GL": y pra cima)
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return _rgb_img(n * 0.5 + 0.5)


def textura_3d(nome):
    """Texturas da cena 3D: tampo, tampo_normal, caneca, d20, ambiente."""
    chave = ("tex3d", nome)
    if chave in _CACHE:
        return _CACHE[chave]
    if nome == "tampo":
        img = _rgb_img(_tampo()[0])
    elif nome == "tampo_normal":
        img = _normal_de(_tampo()[1], 3.0)
    elif nome == "caneca":                      # aduelas de madeira (em pé), mais claras
        lado = 512
        rng = _rng("caneca")
        ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
        larg = lado / 14
        k = np.floor(xs / larg)
        lu = xs - k * larg
        fibra = _caixa_borrar(_caixa_borrar(rng.random((lado, lado)).astype(np.float32), 1), 5)
        fibra = (fibra - fibra.min()) / max(1e-6, float(np.ptp(fibra)))
        tons = rng.random(32).astype(np.float32)
        cor = _c("#8a5a32") * (0.8 + 0.35 * tons[k.astype(int) % 32])[..., None] * (0.85 + 0.25 * fibra[..., None])
        cor *= (0.45 + 0.55 * _suave(np.minimum(lu, larg - lu) / 3))[..., None]
        img = _rgb_img(cor)
    elif nome == "d20":                         # resina vermelha com os números (5×4 casas)
        W, H = 1000, 800
        img = QImage(W, H, QImage.Format.Format_RGB32)
        img.fill(QColor("#a8141c"))
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        f = QFont("Georgia")
        f.setPixelSize(70)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("#f6e8c8"))
        for k in range(20):
            cu, cv = (k % 5) * 200, (k // 5) * 200
            # o meio do triângulo dessa face (ver Icosaedro): ~ (0.5, 0.4) da casa, com v de baixo pra cima
            p.drawText(QRectF(cu, H - (cv + 0.62 * 200) - 50, 200, 100), Qt.AlignmentFlag.AlignCenter, str(k + 1))
        p.end()
    else:                                       # ambiente (pros metais refletirem): sala escura e quente
        W, H = 512, 256
        ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
        t = ys / H
        cor = _c("#3a2414") * (1 - t[..., None]) * 0.6 + _c("#120a05") * t[..., None]
        for (fx, fy, r, c) in ((0.22, 0.42, 0.06, "#ffb860"), (0.7, 0.3, 0.12, "#ff9040"), (0.5, 0.05, 0.3, "#5a4030")):
            d = np.sqrt(((xs / W - fx) * 2) ** 2 + (ys / H - fy) ** 2)
            cor += np.exp(-(d / r) ** 2)[..., None] * _c(c) * 1.6
        img = _rgb_img(np.clip(cor, 0, 1))
    _CACHE[chave] = img
    return img


def _pintura(W, H, desenhar, fundo=None):
    img = QImage(W, H, QImage.Format.Format_ARGB32)
    img.fill(QColor(fundo) if fundo else Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    desenhar(p, W, H)
    p.end()
    return img


def _textura_extra(nome):
    """Texturas dos objetos da mesa 3D (desenhadas aqui): mapa, livro, moedas, dados, pão, pano, selo."""
    from PyQt6.QtGui import QBrush, QPen, QRadialGradient, QPolygonF
    rng = _rng("tex", nome)

    def papel(p, W, H, base="#d9c49a"):
        p.fillRect(0, 0, W, H, QColor(base))
        for _ in range(900):                              # manchinhas e fibras do papel velho
            c = QColor(120, 90, 50, int(rng.uniform(5, 28)))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(c)
            r = rng.uniform(2, 18)
            p.drawEllipse(QPointF(rng.uniform(0, W), rng.uniform(0, H)), r, r)
        g = QRadialGradient(QPointF(W / 2, H / 2), max(W, H) * 0.7)
        g.setColorAt(0.6, QColor(0, 0, 0, 0))
        g.setColorAt(1, QColor(90, 50, 15, 150))           # bordas queimadinhas
        p.fillRect(0, 0, W, H, QBrush(g))

    if nome == "mapa":
        def d(p, W, H):
            papel(p, W, H)
            tinta = QColor(70, 45, 25, 210)
            p.setPen(QPen(tinta, 3))
            for k in range(7):                              # montanhas
                x, y = 120 + k * 70, 170 + (k % 3) * 22
                p.drawPolyline(QPolygonF([QPointF(x - 40, y + 40), QPointF(x, y - 30), QPointF(x + 40, y + 40)]))
                p.drawLine(QPointF(x, y - 30), QPointF(x + 12, y + 10))
            for k in range(14):                             # árvores
                x, y = 90 + (k % 7) * 52, 560 + (k // 7) * 70
                p.drawPolyline(QPolygonF([QPointF(x - 14, y + 22), QPointF(x, y - 18), QPointF(x + 14, y + 22)]))
                p.drawLine(QPointF(x, y + 22), QPointF(x, y + 32))
            rio = QPainterPath(QPointF(200, 900))
            rio.cubicTo(QPointF(380, 760), QPointF(260, 560), QPointF(520, 420))
            rio.cubicTo(QPointF(640, 330), QPointF(720, 300), QPointF(900, 330))
            p.setPen(QPen(QColor(60, 80, 110, 200), 7))
            p.drawPath(rio)
            p.setPen(QPen(tinta, 3))                        # castelinho
            cx, cy = 560, 330
            p.drawRect(QRectF(cx - 50, cy - 20, 100, 70))
            for dx in (-50, 50):
                p.drawRect(QRectF(cx + dx - 14, cy - 60, 28, 110))
                p.drawPolyline(QPolygonF([QPointF(cx + dx - 18, cy - 60), QPointF(cx + dx, cy - 90), QPointF(cx + dx + 18, cy - 60)]))
            p.drawRect(QRectF(cx - 12, cy + 15, 24, 35))
            tracejado = QPen(QColor(150, 30, 20, 220), 4, Qt.PenStyle.DashLine)   # caminho vermelho
            p.setPen(tracejado)
            cam = QPainterPath(QPointF(150, 420))
            cam.cubicTo(QPointF(300, 470), QPointF(420, 380), QPointF(530, 380))
            p.drawPath(cam)
            p.setPen(QPen(tinta, 3))                        # rosa dos ventos
            rx, ry = 820, 760
            for a in range(0, 360, 45):
                comp = 70 if a % 90 == 0 else 38
                p.drawLine(QPointF(rx, ry), QPointF(rx + comp * math.cos(math.radians(a)), ry + comp * math.sin(math.radians(a))))
            p.drawEllipse(QPointF(rx, ry), 22, 22)
            p.setPen(QPen(QColor(110, 80, 45, 120), 3))      # dobras do mapa
            for x in (W / 3, 2 * W / 3):
                p.drawLine(QPointF(x, 0), QPointF(x, H))
            p.drawLine(QPointF(0, H / 2), QPointF(W, H / 2))
        return _pintura(1024, 1024, d)
    if nome == "livro":
        def d(p, W, H):
            p.fillRect(0, 0, W, H, QColor("#6e1c1a"))
            for _ in range(500):
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(0, 0, 0, int(rng.uniform(5, 30))))
                r = rng.uniform(2, 10)
                p.drawEllipse(QPointF(rng.uniform(0, W), rng.uniform(0, H)), r, r)
            ouro = QPen(QColor("#d8a84a"), 10)
            p.setPen(ouro)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(QRectF(40, 40, W - 80, H - 80))
            p.setPen(QPen(QColor("#d8a84a"), 22, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(W / 2, H * 0.3), QPointF(W / 2, H * 0.7))
            p.drawLine(QPointF(W * 0.33, H / 2), QPointF(W * 0.67, H / 2))
            for (x, y) in ((W / 2, H * 0.3), (W / 2, H * 0.7), (W * 0.33, H / 2), (W * 0.67, H / 2)):
                p.setBrush(QColor("#d8a84a"))
                p.drawEllipse(QPointF(x, y), 16, 16)
        return _pintura(512, 512, d)
    if nome in ("moeda_ouro", "moeda_cobre"):
        base, escuro = ("#e8b84a", "#8a5a14") if nome == "moeda_ouro" else ("#c8743a", "#6a3010")

        def d(p, W, H):
            p.fillRect(0, 0, W, H, QColor(base))
            p.setPen(QPen(QColor(escuro), 14))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(W / 2, H / 2), W * 0.4, H * 0.4)
            p.setPen(QPen(QColor(escuro), 26, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(W / 2, H * 0.28), QPointF(W / 2, H * 0.72))
            p.drawLine(QPointF(W * 0.28, H / 2), QPointF(W * 0.72, H / 2))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(escuro))
            for (x, y) in ((W / 2, H * 0.28), (W / 2, H * 0.72), (W * 0.28, H / 2), (W * 0.72, H / 2)):
                p.drawEllipse(QPointF(x, y), 18, 18)
        return _pintura(256, 256, d)
    if nome[:4] == "dado" and nome[4:].isdigit():
        n = int(nome[-1])

        def d(p, W, H):
            p.fillRect(0, 0, W, H, QColor("#efe6d2"))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor("#1a1410"))
            pos = {1: [(0.5, 0.5)], 2: [(0.25, 0.25), (0.75, 0.75)], 3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
                   4: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)],
                   5: [(0.25, 0.25), (0.75, 0.25), (0.5, 0.5), (0.25, 0.75), (0.75, 0.75)],
                   6: [(0.25, 0.22), (0.75, 0.22), (0.25, 0.5), (0.75, 0.5), (0.25, 0.78), (0.75, 0.78)]}[n]
            for x, y in pos:
                p.drawEllipse(QPointF(x * W, y * H), W * 0.09, H * 0.09)
        return _pintura(256, 256, d)
    if nome == "dados":                                    # as 6 faces do d6 numa folha só (3×2)
        def d(p, W, H):
            p.fillRect(0, 0, W, H, QColor("#efe6d2"))
            casa = W / 3
            pips = {1: [(0.5, 0.5)], 2: [(0.27, 0.27), (0.73, 0.73)], 3: [(0.27, 0.27), (0.5, 0.5), (0.73, 0.73)],
                    4: [(0.27, 0.27), (0.73, 0.27), (0.27, 0.73), (0.73, 0.73)],
                    5: [(0.27, 0.27), (0.73, 0.27), (0.5, 0.5), (0.27, 0.73), (0.73, 0.73)],
                    6: [(0.27, 0.24), (0.73, 0.24), (0.27, 0.5), (0.73, 0.5), (0.27, 0.76), (0.73, 0.76)]}
            ordem = [1, 6, 3, 4, 2, 5]
            for k, n in enumerate(ordem):
                x0, y0 = (k % 3) * casa, H - (k // 3 + 1) * casa
                g = QRadialGradient(QPointF(x0 + casa / 2, y0 + casa / 2), casa * 0.75)
                g.setColorAt(0.6, QColor(0, 0, 0, 0))
                g.setColorAt(1, QColor(90, 60, 30, 90))
                p.fillRect(QRectF(x0, y0, casa, casa), QBrush(g))
                p.setPen(Qt.PenStyle.NoPen)
                for x, y in pips[n]:
                    p.setBrush(QColor("#2a0e0a"))
                    p.drawEllipse(QPointF(x0 + x * casa, y0 + y * casa), casa * 0.085, casa * 0.085)
            p.fillRect(QRectF(W - 6, 0, 6, 6), QColor("#cfc2a4"))
        return _pintura(768, 512, d)
    if nome == "mancha":                                   # anel de caneca molhada no tampo
        def d(p, W, H):
            for k in range(3):
                p.setPen(QPen(QColor(30, 14, 4, 70 - k * 18), 10 + k * 8))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(QPointF(W / 2 + k * 6, H / 2 - k * 4), W * 0.38 - k * 3, H * 0.38 - k * 2)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(30, 14, 4, 25))
            p.drawEllipse(QPointF(W / 2, H / 2), W * 0.36, H * 0.36)
        return _pintura(256, 256, d)
    if nome == "riscos":                                   # arranhões de faca no tampo
        def d(p, W, H):
            for _ in range(26):
                x, y = rng.uniform(0, W), rng.uniform(0, H)
                a, comp = rng.uniform(-0.5, 0.5), rng.uniform(40, 220)
                x2, y2 = x + math.cos(a) * comp, y + math.sin(a) * comp
                p.setPen(QPen(QColor(20, 8, 2, int(rng.uniform(60, 140))), rng.uniform(1.5, 3.5)))
                p.drawLine(QPointF(x, y), QPointF(x2, y2))
                p.setPen(QPen(QColor(220, 170, 110, 40), 1))
                p.drawLine(QPointF(x, y + 2), QPointF(x2, y2 + 2))
        return _pintura(512, 512, d)
    if nome == "couro":                                    # saquinho de moedas
        def d(p, W, H):
            p.fillRect(0, 0, W, H, QColor("#9a6a3c"))
            for _ in range(600):
                p.setPen(Qt.PenStyle.NoPen)
                c = QColor(30, 15, 5, int(rng.uniform(10, 50))) if rng.random() < 0.6 else QColor(160, 110, 70, int(rng.uniform(10, 35)))
                p.setBrush(c)
                r = rng.uniform(2, 12)
                p.drawEllipse(QPointF(rng.uniform(0, W), rng.uniform(0, H)), r, r)
            p.setPen(QPen(QColor(40, 20, 8, 160), 3, Qt.PenStyle.DashLine))   # costura
            p.drawLine(QPointF(0, H * 0.82), QPointF(W, H * 0.82))
        return _pintura(256, 256, d)
    if nome == "pao":
        def d(p, W, H):
            p.fillRect(0, 0, W, H, QColor("#b8692a"))
            for _ in range(400):
                p.setPen(Qt.PenStyle.NoPen)
                c = QColor("#e0a050") if rng.random() < 0.5 else QColor("#7a3a12")
                c.setAlpha(int(rng.uniform(30, 90)))
                p.setBrush(c)
                r = rng.uniform(3, 14)
                p.drawEllipse(QPointF(rng.uniform(0, W), rng.uniform(0, H)), r, r * 0.6)
        return _pintura(256, 256, d)
    if nome == "pano":
        def d(p, W, H):
            p.fillRect(0, 0, W, H, QColor("#e2d6bc"))
            for x0 in (W * 0.18, W * 0.24, W * 0.8):
                p.fillRect(QRectF(x0, 0, W * 0.035, H), QColor("#8a2420"))
            for _ in range(300):
                p.setPen(QPen(QColor(120, 100, 70, 30), 1))
                y = rng.uniform(0, H)
                p.drawLine(QPointF(0, y), QPointF(W, y))
        return _pintura(512, 512, d)
    return None


def caminho_textura_3d(nome) -> str:
    """Grava a textura num arquivo (o Qt Quick 3D só lê textura de arquivo) e devolve o caminho."""
    import os
    import tempfile
    pasta = os.path.join(tempfile.gettempdir(), "taverna_3d")
    if os.environ.get("QT_QPA_PLATFORM", "") in ("offscreen", "minimal"):   # (testes: fontes erradas, pasta à parte)
        pasta += "_teste"
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, f"{nome}_v9.png")   # (suba o número quando um desenho mudar)
    if not os.path.isfile(caminho):
        img = _textura_extra(nome)
        if img is None:
            from .terror_cenas import textura as textura_terror
            img = textura_terror(nome)
        if img is None:
            from .medieval_cenas import textura as textura_medieval
            img = textura_medieval(nome)
        if img is None:
            from .magico_cenas import textura as textura_magico
            img = textura_magico(nome)
        if img is None:
            from .moderno_cenas import textura as textura_moderno
            img = textura_moderno(nome)
        if img is None:
            from .futurista_cenas import textura as textura_futurista
            img = textura_futurista(nome)
        if img is None:
            from .steampunk_cenas import textura as textura_steampunk
            img = textura_steampunk(nome)
        if img is None:
            from .posapoc_cenas import textura as textura_posapoc
            img = textura_posapoc(nome)
        if img is None:
            if nome.startswith("sprite_"):
                img = sprite_fogo(64, nome[7:])
            else:
                img = textura_3d(nome)
        img.save(caminho)
    return caminho


def _sombra_objeto(p, cx, cy, rx, ry, luz, forca=0.55, comp=1.0):
    """Sombra no tampo, esticada pro lado oposto da vela."""
    from PyQt6.QtGui import QBrush, QRadialGradient
    dx, dy = cx - luz[0], cy - luz[1]
    n = math.hypot(dx, dy) or 1
    ox, oy = dx / n * rx * 0.9 * comp, dy / n * ry * 1.6 * comp
    g = QRadialGradient(QPointF(cx + ox, cy + oy), max(rx, ry) * 1.4)
    g.setColorAt(0, QColor(0, 0, 0, int(255 * forca)))
    g.setColorAt(1, QColor(0, 0, 0, 0))
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(g))
    p.translate(cx + ox, cy + oy)
    p.rotate(math.degrees(math.atan2(dy, dx)))
    p.drawEllipse(QPointF(0, 0), max(rx, ry) * 1.5 * comp, min(rx, ry) * 0.9)
    p.restore()


def _objetos_mesa(img, W, H, luz):
    """Caneca de cerveja, moedas de ouro, um d20 e a vela no castiçal — com sombra e luz da vela."""
    from PyQt6.QtGui import QBrush, QLinearGradient, QPen, QPolygonF, QRadialGradient
    e = H / 800.0 * 1.45
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # ---- sombras primeiro
    caneca = (W * 0.82, H * 0.74, 70 * e, 104 * e)        # centro da base, raio, altura
    vela = (VELA[0] * W, VELA[1] * H + 0.17 * H)
    moedas = [(W * 0.26, H * 0.86, 1.0), (W * 0.30, H * 0.82, 0.95), (W * 0.34, H * 0.88, 1.05),
              (W * 0.70, H * 0.90, 1.0), (W * 0.93, H * 0.50, 0.8), (W * 0.62, H * 0.95, 1.1)]
    pilha = (W * 0.21, H * 0.93)
    dado = (W * 0.90, H * 0.93, 34 * e)
    _sombra_objeto(p, caneca[0], caneca[1], caneca[2], caneca[2] * 0.4, luz, 0.65, 2.2)
    _sombra_objeto(p, vela[0], vela[1] + 4 * e, 34 * e, 12 * e, (vela[0] - 1, vela[1] - 40 * e), 0.5, 0.8)
    _sombra_objeto(p, pilha[0], pilha[1], 30 * e, 12 * e, luz, 0.6, 1.6)
    _sombra_objeto(p, dado[0], dado[1], dado[2], dado[2] * 0.5, luz, 0.6, 1.5)
    for mx, my, s in moedas:
        _sombra_objeto(p, mx, my, 22 * e * s, 8 * e * s, luz, 0.45, 0.6)
    p.end()

    # ---- moedas (ouro de verdade, com o metal refletindo)
    def desenhar_moedas(q):
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QColor(255, 255, 255))
        for mx, my, s in moedas:
            q.drawEllipse(QPointF(mx, my), 22 * e * s, 9 * e * s)
        for k in range(6):                                  # pilha
            q.drawEllipse(QPointF(pilha[0], pilha[1] - k * 5 * e), 24 * e, 9.5 * e)
            q.drawRect(QRectF(pilha[0] - 24 * e, pilha[1] - k * 5 * e - 5 * e, 48 * e, 5 * e))
    m = _mascara(W, H, desenhar_moedas)
    ouro = metal(m, "medieval", e, perfil=1.3, riscos=False)
    ouro[..., :3] = np.minimum(ouro[..., :3] * 1.7, ouro[..., 3:4])   # ouro brilhando à luz da vela
    img = _compor(img, ouro)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(90, 55, 10, 160), 1.0 * e))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for mx, my, s in moedas:                                 # aro e "cara" cunhada
        p.drawEllipse(QPointF(mx, my), 16 * e * s, 6 * e * s)
    for k in range(6):
        y = pilha[1] - k * 5 * e
        p.drawLine(QPointF(pilha[0] - 24 * e, y), QPointF(pilha[0] + 24 * e, y))
    p.drawEllipse(QPointF(pilha[0], pilha[1] - 25 * e), 17 * e, 6.5 * e)

    # ---- d20 (dado de RPG): facetas com luz
    cx, cy, r = dado
    pts = [QPointF(cx + r * math.cos(math.radians(a)), cy - r * 0.85 + r * 0.85 * math.sin(math.radians(a)))
           for a in range(-90, 270, 60)]
    meio = QPointF(cx, cy - r * 0.85)
    tons = ["#c03030", "#e04848", "#8a1a1a", "#6a1212", "#a02424", "#d03a3a"]
    for k in range(6):
        tri = QPolygonF([meio, pts[k], pts[(k + 1) % 6]])
        p.setPen(QPen(QColor("#3a0808"), 1.2 * e))
        p.setBrush(QColor(tons[k]))
        p.drawPolygon(tri)
    p.setPen(QPen(QColor("#ffe8d0"), 1))
    f = QFont()
    f.setPixelSize(int(14 * e))
    f.setBold(True)
    p.setFont(f)
    p.drawText(QRectF(cx - r * 0.5, cy - r * 1.25, r, r * 0.8), Qt.AlignmentFlag.AlignCenter, "20")

    # ---- caneca de madeira com aros de metal e espuma
    bx, by, rr, alt = caneca
    topo = by - alt
    corpo = QPainterPath()
    corpo.moveTo(bx - rr, topo)
    corpo.lineTo(bx - rr * 0.92, by)
    corpo.arcTo(QRectF(bx - rr * 0.92, by - rr * 0.32, rr * 1.84, rr * 0.64), 180, 180)
    corpo.lineTo(bx + rr, topo)
    corpo.closeSubpath()
    g = QLinearGradient(QPointF(bx - rr, 0), QPointF(bx + rr, 0))
    g.setColorAt(0, QColor("#a06a38"))      # lado virado pra vela (esquerda) mais claro
    g.setColorAt(0.35, QColor("#7a4a24"))
    g.setColorAt(1, QColor("#2a160a"))
    p.setPen(QPen(QColor("#1a0c04"), 1.4 * e))
    p.setBrush(QBrush(g))
    p.drawPath(corpo)
    p.setPen(QPen(QColor(30, 15, 5, 140), 1.2 * e))         # aduelas
    for k in range(1, 7):
        x = bx - rr + 2 * rr * k / 7
        p.drawLine(QPointF(x, topo + 4 * e), QPointF(x * 0.995 + bx * 0.005, by + 2 * e))
    # asa
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(QColor("#5a3418"), 13 * e, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    asa = QPainterPath(QPointF(bx + rr * 0.95, topo + alt * 0.22))
    asa.cubicTo(QPointF(bx + rr * 1.75, topo + alt * 0.2), QPointF(bx + rr * 1.75, topo + alt * 0.8),
                QPointF(bx + rr * 0.95, topo + alt * 0.78))
    p.drawPath(asa)
    p.end()

    def aros(q):
        q.setPen(QPen(QColor(255, 255, 255), 7 * e))
        q.setBrush(Qt.BrushStyle.NoBrush)
        for f in (0.2, 0.78):
            y = topo + alt * f
            q.drawArc(QRectF(bx - rr * 0.99, y - rr * 0.18, rr * 1.98, rr * 0.36), 180 * 16, 180 * 16)
    img = _compor(img, metal(_mascara(W, H, aros), "ferro", e, perfil=2.0))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # espuma: boca escura + espuma cremosa transbordando
    boca = QRectF(bx - rr, topo - rr * 0.34, rr * 2, rr * 0.68)
    p.setPen(QPen(QColor("#1a0c04"), 1.4 * e))
    p.setBrush(QColor("#3a2410"))
    p.drawEllipse(boca)
    espuma = QPainterPath()
    espuma.setFillRule(Qt.FillRule.WindingFill)        # (sem isso, onde as bolhas se cruzam virava buraco)
    espuma.addEllipse(boca.adjusted(2 * e, -6 * e, -2 * e, 2 * e))
    for k in range(9):
        ax = bx - rr * 0.9 + k * rr * 0.22
        espuma.addEllipse(QPointF(ax, topo - rr * 0.25 - math.sin(k * 1.3) * 5 * e), 11 * e, 8 * e)
    espuma.addRoundedRect(QRectF(bx - rr * 0.55, topo - 4 * e, 14 * e, 30 * e), 7 * e, 7 * e)   # escorrendo
    ge = QLinearGradient(QPointF(0, topo - rr * 0.5), QPointF(0, topo + 24 * e))
    ge.setColorAt(0, QColor("#fffaf0"))
    ge.setColorAt(1, QColor("#d8c8a0"))
    p.setPen(QPen(QColor(150, 130, 90, 160), 1 * e))
    p.setBrush(QBrush(ge))
    p.drawPath(espuma.simplified())
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 255, 255, 200))
    rngb = _rng("bolhas")
    for _ in range(14):
        p.drawEllipse(QPointF(bx + rngb.uniform(-rr * 0.8, rr * 0.8), topo - rr * 0.3 + rngb.uniform(-6, 6) * e),
                      rngb.uniform(1, 2.5) * e, rngb.uniform(1, 2.5) * e)

    # ---- vela no castiçal (a chama é do QML)
    vx, vy = vela
    p.setPen(Qt.PenStyle.NoPen)
    p.end()

    def castical(q):
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QColor(255, 255, 255))
        q.drawEllipse(QPointF(vx, vy), 40 * e, 13 * e)                   # prato
        q.drawRect(QRectF(vx - 9 * e, vy - 18 * e, 18 * e, 18 * e))       # pezinho
        q.drawEllipse(QPointF(vx, vy - 18 * e), 16 * e, 6 * e)
    img = _compor(img, metal(_mascara(W, H, castical), "medieval", e, perfil=2.6, riscos=False))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    cera = QLinearGradient(QPointF(vx - 13 * e, 0), QPointF(vx + 13 * e, 0))
    cera.setColorAt(0, QColor("#fff2d8"))
    cera.setColorAt(0.5, QColor("#ead7b0"))
    cera.setColorAt(1, QColor("#a08a66"))
    p.setPen(QPen(QColor("#8a7450"), 1 * e))
    p.setBrush(QBrush(cera))
    vela_topo = VELA[1] * H + 4 * e
    p.drawRoundedRect(QRectF(vx - 13 * e, vela_topo, 26 * e, vy - 20 * e - vela_topo), 4 * e, 4 * e)
    for k, (dxx, comp) in enumerate(((-9, 22), (4, 34), (10, 14))):   # cera escorrida
        p.drawRoundedRect(QRectF(vx + dxx * e - 3 * e, vela_topo + 2 * e, 6 * e, comp * e), 3 * e, 3 * e)
    p.setPen(QPen(QColor("#1a1008"), 2 * e))                          # pavio
    p.drawLine(QPointF(vx, vela_topo), QPointF(vx, vela_topo - 7 * e))
    p.end()
    return img


# ====================================================================== parede de PEDRA 3D (fundo do Medieval)
def parede_pedra(w, h, tochas=TOCHAS):
    """Muro de blocos de pedra cinza, irregulares e lascados, cada um levemente inclinado, com argamassa
    funda — e iluminado DE VERDADE pelas tochas (a luz vem da direção de cada uma, então cada pedra pega luz
    de um lado e faz sombra do outro). tochas: posições 0..1 na tela."""
    chave = ("pedra", w, h, tuple(tochas))
    if chave in _CACHE:
        return _CACHE[chave]
    W, H = int(w), int(h)
    rng = _rng("pedra-muro", W, H)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    # bordas tortinhas (feito à mão): desloca as coordenadas com ruído suave
    warp_x = (_ruido(H, W, 10, rng) - 0.5) * 9 + (_ruido(H, W, 3, rng) - 0.5) * 3
    warp_y = (_ruido(H, W, 10, rng) - 0.5) * 9 + (_ruido(H, W, 3, rng) - 0.5) * 3
    X, Y = xs + warp_x, ys + warp_y
    # fileiras de alturas diferentes e blocos de larguras diferentes
    alturas = rng.uniform(44, 66, 64)
    topos = np.concatenate([[-80], np.cumsum(alturas) - 80])
    fila = np.clip(np.searchsorted(topos, Y, side="right") - 1, 0, len(alturas) - 1)
    y0 = topos[fila]
    hf = alturas[fila]
    cortes = {}
    for f in range(len(alturas)):
        larg = rng.uniform(70, 150, 40)
        cortes[f] = np.concatenate([[-rng.uniform(0, 120)], np.cumsum(larg) - rng.uniform(0, 120)])
    x0 = np.zeros_like(X)
    bw = np.zeros_like(X)
    bloco = np.zeros(X.shape, np.int64)
    for f in np.unique(fila):
        m = fila == f
        c = cortes[f]
        k = np.clip(np.searchsorted(c, X[m], side="right") - 1, 0, len(c) - 2)
        x0[m] = c[k]
        bw[m] = c[k + 1] - c[k]
        bloco[m] = f * 64 + k
    lx, ly = X - x0, Y - y0
    junta = 4.5
    d = np.minimum(np.minimum(lx, bw - lx), np.minimum(ly, hf - ly)) - junta
    pedra = d > 0
    tab = _rng("blocos").random((8192, 5)).astype(np.float32)
    v = tab[bloco % 8192]
    # altura: quina chanfrada curta + inclinação própria do bloco + aspereza + lascas
    aspero = _ruido(H, W, 2, rng)
    aspero2 = _ruido(H, W, 9, rng)
    inclina = ((lx / np.maximum(bw, 1) - 0.5) * (v[..., 0] - 0.5) + (ly / np.maximum(hf, 1) - 0.5) * (v[..., 1] - 0.5)) * 3.0
    # quina arredondada e gasta (não "almofada"): sobe rápido e fica quase plano, com aspereza por cima
    alt = np.where(pedra, np.clip(d / 7, 0, 1) ** 0.5 * 2.4 + inclina + (aspero - 0.5) * 0.9 + (aspero2 - 0.5) * 1.8, -0.8)
    lasca = pedra & (d < 12) & (aspero2 > 0.62)
    alt = np.where(lasca, alt - (aspero2 - 0.62) * 9, alt)
    # cor: cinzas de pedra, um puxando pro frio, outro pro quente, com manchas
    tons = np.array([_c("#7e7d79"), _c("#6c6b68"), _c("#8b8985"), _c("#5d5c5a"), _c("#77736d"), _c("#6a6e70")])
    cor = tons[(v[..., 2] * len(tons)).astype(int) % len(tons)]
    cor = cor * (0.82 + 0.3 * aspero2[..., None]) * (0.95 + 0.1 * aspero[..., None])
    musgo = _suave((aspero2 - 0.78) * 6) * (ly / np.maximum(hf, 1) > 0.6)
    cor = cor * (1 - musgo[..., None] * 0.25) + _c("#4a5a38") * musgo[..., None] * 0.25
    argamassa = _c("#2b2926") * (0.85 + 0.3 * aspero[..., None])
    alb = np.where(pedra[..., None], cor, argamassa).astype(np.float32)
    # normais
    gy, gx = np.gradient(alt)
    n = np.dstack([-gx * 1.6, -gy * 1.6, np.ones_like(alt)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    # luz: um pouco de luar frio vindo de cima + as tochas (quentes), de cada direção
    luz = np.zeros((H, W, 3), np.float32)
    lua = np.array([0.15, -0.55, 0.82])
    lua /= np.linalg.norm(lua)
    luz += np.clip(n @ lua, 0, 1)[..., None] * np.array([0.26, 0.28, 0.33], np.float32)
    quente = np.array([1.0, 0.80, 0.58], np.float32)     # luz de fogo, mas sem deixar a pedra bege
    for tx, ty in tochas:
        dx, dy, dz = tx * W - xs, ty * H - ys, np.full_like(xs, 120.0)
        dist = np.sqrt(dx * dx + dy * dy + dz * dz)
        l = np.dstack([dx / dist, dy / dist, dz / dist])
        lam = np.clip((n * l).sum(axis=2), 0, 1)
        atenua = 1.0 / (1 + (dist / (0.24 * max(W, H))) ** 2)
        luz += (lam * atenua * 1.7)[..., None] * quente
    luz += 0.06
    rgb = alb * luz
    # oclusão na argamassa e vinheta
    rgb *= np.where(pedra, 1.0, 0.55)[..., None]
    vinheta = 1 - _suave(np.sqrt(((xs / W - 0.5) * 1.5) ** 2 + ((ys / H - 0.45) * 1.8) ** 2) - 0.3) * 0.75
    rgb *= vinheta[..., None]
    rgba = np.empty((H, W, 4), np.uint8)
    rgba[..., :3] = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    rgba[..., 3] = 255
    img = _qimg(rgba)
    _CACHE[chave] = img
    return img


def suporte_tocha(escala=1.0):
    """O suporte de ferro da tocha (placa na parede, braço e cesto) + o cabo de madeira, com volume."""
    chave = ("suporte", round(escala, 2))
    if chave in _CACHE:
        return _CACHE[chave]
    e = escala
    W, H = int(70 * e), int(170 * e)
    cx = W / 2

    def ferro(q):
        b = QColor(255, 255, 255)
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(b)
        q.drawRoundedRect(QRectF(cx - 13 * e, 96 * e, 26 * e, 58 * e), 4 * e, 4 * e)     # placa na parede
        braco = QPainterPath()
        braco.moveTo(cx - 4 * e, 120 * e)
        braco.lineTo(cx + 4 * e, 120 * e)
        braco.lineTo(cx + 5 * e, 58 * e)
        braco.lineTo(cx - 5 * e, 58 * e)
        braco.closeSubpath()
        q.drawPath(braco)
        cesto = QPainterPath()                                                        # cesto (copo)
        cesto.moveTo(cx - 20 * e, 30 * e)
        cesto.lineTo(cx + 20 * e, 30 * e)
        cesto.lineTo(cx + 11 * e, 62 * e)
        cesto.lineTo(cx - 11 * e, 62 * e)
        cesto.closeSubpath()
        q.drawPath(cesto)
        q.setBrush(Qt.BrushStyle.NoBrush)
        from PyQt6.QtGui import QPen as _P
        q.setPen(_P(b, 3 * e))
        q.drawLine(QPointF(cx - 20 * e, 30 * e), QPointF(cx + 20 * e, 30 * e))         # aro
        q.setPen(_P(b, 2.2 * e))
        for fx in (-1, 1):                                                             # volutas
            v = QPainterPath(QPointF(cx + fx * 5 * e, 100 * e))
            v.cubicTo(QPointF(cx + fx * 22 * e, 96 * e), QPointF(cx + fx * 24 * e, 78 * e), QPointF(cx + fx * 14 * e, 74 * e))
            q.drawPath(v)

    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    from PyQt6.QtGui import QBrush, QLinearGradient
    g = QLinearGradient(QPointF(cx - 7 * e, 0), QPointF(cx + 7 * e, 0))      # cabo de madeira (atrás)
    g.setColorAt(0, QColor("#6a4426"))
    g.setColorAt(0.4, QColor("#9a6a3e"))
    g.setColorAt(1, QColor("#3a2414"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(g))
    p.drawRoundedRect(QRectF(cx - 7 * e, 8 * e, 14 * e, 40 * e), 3 * e, 3 * e)
    p.setBrush(QColor("#2a1a10"))                                                # pano queimado na ponta
    p.drawEllipse(QPointF(cx, 14 * e), 10 * e, 8 * e)
    p.end()
    m = _mascara(W, H, ferro)
    ferro_rgba = metal(m, "ferro", e, perfil=2.0)       # ferro batido escuro
    img = _compor(img, ferro_rgba)
    # (v0.52) o FOGO ilumina o próprio suporte: o que olha pra cima pega laranja, embaixo fica no escuro
    b = img.convertToFormat(QImage.Format.Format_RGBA8888_Premultiplied)
    ptr = b.constBits()
    ptr.setsize(b.sizeInBytes())
    arr = np.frombuffer(ptr, np.uint8).reshape(H, b.bytesPerLine())[:, :W * 4].reshape(H, W, 4).astype(np.float32) / 255
    alfa = arr[..., 3]
    tudo = np.maximum(alfa, 0)
    borrado = _caixa_borrar(tudo, 2 * e)
    gy, _gx = np.gradient(borrado)
    de_cima = np.clip(-gy * 6, 0, 1)                         # bordas viradas pra cima (pro fogo)
    ys = np.mgrid[0:H, 0:W][0].astype(np.float32)
    perto = np.clip(1 - ys / (H * 0.9), 0, 1) ** 1.4          # mais perto do fogo = mais luz
    quente = np.array([1.0, 0.55, 0.18], np.float32)
    arr[..., :3] += (de_cima * 0.9 + perto * 0.35)[..., None] * quente * alfa[..., None]
    arr[..., :3] *= (0.55 + 0.45 * perto)[..., None]           # a parte de baixo fica na sombra
    arr[..., :3] = np.minimum(arr[..., :3], alfa[..., None])
    # sombra NA PAREDE: o fogo está em cima, então o suporte joga uma sombra comprida pra baixo
    # (esticada e borrada) + sombra de contato onde a placa encosta na pedra
    Hs = int(H * 1.7)
    out = np.zeros((Hs, W, 4), np.float32)
    estica = np.clip((np.arange(Hs) - 40 * e) / 1.55, 0, H - 1).astype(int)
    sombra = _caixa_borrar(tudo[estica], 6 * e) * 0.62
    contato = _caixa_borrar(np.pad(tudo, ((0, Hs - H), (0, 0))), 3 * e) * 0.5
    out[..., 3] = np.clip(np.maximum(sombra, contato), 0, 0.75)
    out[:H] = arr + out[:H] * (1 - arr[..., 3:4])
    final = (np.clip(out, 0, 1) * 255).astype(np.uint8)
    img = QImage(final.tobytes(), W, Hs, W * 4, QImage.Format.Format_RGBA8888_Premultiplied).copy()
    _CACHE[chave] = img
    return img


def sprite_fogo(lado=64, tipo="chama"):
    """Bolinha de luz macia pras partículas (chama, faísca, fumaça)."""
    from PyQt6.QtGui import QBrush, QRadialGradient
    chave = ("sprite", lado, tipo)
    if chave in _CACHE:
        return _CACHE[chave]
    img = QImage(lado, lado, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    g = QRadialGradient(QPointF(lado / 2, lado / 2), lado / 2)
    if tipo == "faisca":
        g.setColorAt(0, QColor(255, 255, 255, 255))
        g.setColorAt(0.25, QColor(255, 255, 255, 200))
        g.setColorAt(1, QColor(255, 255, 255, 0))
    elif tipo == "fumaca":
        g.setColorAt(0, QColor(255, 255, 255, 90))
        g.setColorAt(1, QColor(255, 255, 255, 0))
    elif tipo == "brilho":            # luz da tocha batendo na parede
        g.setColorAt(0, QColor(255, 170, 70, 200))
        g.setColorAt(0.35, QColor(255, 120, 40, 90))
        g.setColorAt(1, QColor(255, 90, 20, 0))
    elif tipo == "chama_parada":      # (Baixo) uma chama desenhada, sem animação
        g = QRadialGradient(QPointF(lado / 2, lado * 0.62), lado / 2)
        g.setColorAt(0, QColor(255, 245, 190, 255))
        g.setColorAt(0.35, QColor(255, 160, 40, 230))
        g.setColorAt(1, QColor(220, 60, 10, 0))
    else:
        g.setColorAt(0, QColor(255, 255, 255, 230))
        g.setColorAt(0.45, QColor(255, 255, 255, 110))
        g.setColorAt(1, QColor(255, 255, 255, 0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(g))
    p.drawEllipse(QRectF(0, 0, lado, lado))
    p.end()
    _CACHE[chave] = img
    return img


def vinheta(w, h, forca=0.85):
    """Escurece as bordas (cinema): transparente no meio, preto nas beiradas."""
    from PyQt6.QtGui import QBrush, QRadialGradient
    chave = ("vinheta", w, h, forca)
    if chave in _CACHE:
        return _CACHE[chave]
    img = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    g = QRadialGradient(QPointF(w * 0.55, h * 0.45), max(w, h) * 0.75)
    g.setColorAt(0, QColor(0, 0, 0, 0))
    g.setColorAt(0.55, QColor(0, 0, 0, int(70 * forca)))
    g.setColorAt(1, QColor(0, 0, 0, int(245 * forca)))
    p.fillRect(QRectF(0, 0, w, h), QBrush(g))
    p.end()
    _CACHE[chave] = img
    return img


# ====================================================================== parede de tijolos 3D (fundo)
def parede_tijolos(w, h, tochas=(), escala=1.0):
    """Muro de tijolos estilizado, com volume e iluminado por tochas (posições 0..1)."""
    chave = ("parede", w, h, tuple(tochas), round(escala, 2))
    if chave in _CACHE:
        return _CACHE[chave]
    W, H = int(w), int(h)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    rng = _rng("tijolos", W, H)
    bh, bw, junta = 46.0, 104.0, 5.0
    fila = np.floor(ys / bh)
    desl = (fila % 2) * bw * 0.5
    col = np.floor((xs + desl) / bw)
    lx = (xs + desl) - col * bw
    ly = ys - fila * bh
    # cada tijolo: um pouco torto e de tamanho diferente (feito à mão)
    ids = (fila * 997 + col).astype(np.int64)
    tab = rng.random((4096, 4)).astype(np.float32)
    v = tab[ids % 4096]
    d = np.minimum(np.minimum(lx - junta * (0.6 + v[..., 0] * 0.8), bw - lx - junta * (0.6 + v[..., 1] * 0.8)),
                   np.minimum(ly - junta * 0.7, bh - ly - junta * 0.7))
    tijolo = d > 0
    alt = np.where(tijolo, _suave(d / 9) * 1.4 + 0.3, 0.0)
    # lasquinhas e manchas pintadas
    mancha = _caixa_borrar(rng.random((H, W)).astype(np.float32), 6)
    mancha = (mancha - mancha.min()) / max(1e-6, np.ptp(mancha))
    alt -= np.where(tijolo, _suave((mancha - 0.72) * 8) * 0.5, 0)
    tons = np.array([_c("#8a6a52"), _c("#7a5a46"), _c("#96745a"), _c("#6e5242"), _c("#a07c60")])
    cor_t = tons[(v[..., 2] * len(tons)).astype(int) % len(tons)]
    cor_t = cor_t * (0.88 + 0.24 * mancha[..., None])
    argamassa = _c("#2e2620") * (0.9 + 0.2 * mancha[..., None])
    alb = np.where(tijolo[..., None], cor_t, argamassa).astype(np.float32)
    rgba = iluminar(alb, alt * 6, np.full((H, W), 0.15, np.float32), None, None, forca=1.0,
                    contorno=0.45, ambiente=0.36).astype(np.float32)
    # luz quente das tochas + escurecer longe delas (vinheta)
    luz = np.full((H, W), 0.30, np.float32)
    for tx, ty in tochas:
        dd = np.sqrt((xs - tx * W) ** 2 + ((ys - ty * H) * 1.2) ** 2) / (0.42 * max(W, H))
        luz += np.clip(1 - dd, 0, 1) ** 1.6 * 1.25
    vinheta = 1 - _suave(np.sqrt(((xs / W - 0.5) * 1.6) ** 2 + ((ys / H - 0.48) * 1.9) ** 2) - 0.25) * 0.6
    quente = np.array([1.0, 0.78, 0.52], np.float32)
    fator = (luz * vinheta)[..., None]
    rgb = rgba[..., :3] / 255 * (fator * quente + (1 - quente) * 0.25 * fator)
    rgba[..., :3] = np.clip(rgb, 0, 1) * 255
    img = _qimg(rgba.astype(np.uint8))
    _CACHE[chave] = img
    return img
