"""
🪵 Relevo com luz pra interface (v0.51) — o que tira a cara de "jogo de Flash".

Cada painel/botão é "esculpido": um mapa de ALTURA da peça (bisel arredondado, moldura entalhada, botão
afundado quando apertado) somado ao relevo REAL do material (veio da madeira, poro do couro, placas do
metal — texturas CC0 do ambientCG em `ui/materiais/`), e iluminado por uma luz de cima-esquerda:
difusa + brilho especular (forte no metal, fraco no papel) + sombra nas quinas (oclusão).
Fica tudo numa imagem pronta (cache), então a tela não pesa — a luz é "assada".

Níveis (Gráficos): 1 (Médio) = bisel simples, material discreto · 2 (Alto) = material forte, moldura
entalhada dupla, brilho especular.
"""

import os

import numpy as np
from PyQt6.QtGui import QImage

PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "materiais")
LUZ = np.array([-0.45, -0.62, 0.64])          # vem de cima-esquerda, inclinada (y pra baixo na tela)
LUZ = LUZ / np.linalg.norm(LUZ)
ESTILIZADO = 0.5     # 1 = textura de foto · 0 = cor lisa (o relevo da peça continua)
_MATS = {}
_CACHE = {}

# material: (arquivo, força do brilho especular, quão "metal" — o brilho pega a cor do material)
MATERIAIS = {
    "WoodFloor043": (0.30, 0.0), "Leather037": (0.35, 0.0), "MetalPlates013": (0.95, 0.8),
    "Planks037A": (0.25, 0.0), "Metal041B": (0.70, 0.6), "MetalPlates006": (0.95, 0.7),
    "Metal049A": (1.10, 0.9), "Leather026": (0.45, 0.0), "Onyx015": (0.90, 0.2), "Paper006": (0.12, 0.0),
}

# tema → peça → (material, tinta (cor que multiplica), ganho de brilho, escala da textura)
KITS = {
    "medieval": {"placa": ("WoodFloor043", "#c8a888", 0.78, 0.9), "botao": ("Leather037", "#ffffff", 0.95, 0.7),
                 "principal": ("Metal049A", "#d8a440", 0.95, 0.9)},   # latão escovado
    "terror": {"placa": ("Planks037A", "#d0b8b0", 0.62, 0.9), "botao": ("Metal041B", "#7a6a66", 0.62, 0.8),
               "principal": ("Metal041B", "#c03838", 0.72, 0.8)},
    "futurista": {"placa": ("MetalPlates006", "#a8c8ff", 0.78, 0.8), "botao": ("Metal049A", "#304868", 0.85, 0.9),
                  "principal": ("Metal049A", "#30c8f0", 0.80, 0.9)},
    "moderno": {"placa": ("Leather026", "#c0c8d0", 1.75, 0.8), "botao": ("Metal049A", "#3a4250", 0.85, 0.9),
                "principal": ("Metal049A", "#4fb3a9", 0.80, 0.9)},
    "magico": {"placa": ("Onyx015", "#7a5ab8", 0.58, 1.0), "botao": ("Onyx015", "#4a3478", 0.62, 0.8),
               "principal": ("Onyx015", "#c0a0ff", 0.80, 0.8)},
    "steampunk": {"placa": ("Leather037", "#b08868", 0.85, 0.8), "botao": ("MetalPlates013", "#c8a050", 0.80, 0.8),
                  "principal": ("Metal049A", "#c88a50", 0.95, 0.9)},   # couro, latão e cobre
    "posapoc": {"placa": ("Planks037A", "#a8a080", 0.62, 0.9), "botao": ("Metal041B", "#8a6a48", 0.70, 0.8),
                "principal": ("Metal041B", "#d0702a", 0.80, 0.8)},     # tábua velha e lata enferrujada
    "claro": {"placa": ("Paper006", "#f6e8c8", 1.20, 1.0), "botao": ("Paper006", "#efe0bc", 1.18, 0.8),
              "principal": ("Leather037", "#e09060", 1.15, 0.7)},
    "escuro": {"placa": ("Leather026", "#c8ccd8", 2.0, 0.8), "botao": ("Metal049A", "#2c3038", 0.85, 0.9),
               "principal": ("Metal049A", "#7c9cff", 0.75, 0.9)},
}


def _ler(caminho) -> np.ndarray:
    img = QImage(caminho).convertToFormat(QImage.Format.Format_RGB888)
    w, h = img.width(), img.height()
    ptr = img.constBits()
    ptr.setsize(img.sizeInBytes())
    a = np.frombuffer(ptr, np.uint8).reshape(h, img.bytesPerLine())[:, :w * 3].reshape(h, w, 3)
    return a.astype(np.float32) / 255.0


def material(mid):
    """(cor, normal, rugosidade) do material, 512×512, em float."""
    m = _MATS.get(mid)
    if m is None:
        cor = _ler(os.path.join(PASTA, f"{mid}_cor.jpg"))
        nor = _ler(os.path.join(PASTA, f"{mid}_normal.jpg")) * 2 - 1
        nor[..., 1] *= -1                      # normal "GL" tem o verde pra cima; a tela tem y pra baixo
        rug = _ler(os.path.join(PASTA, f"{mid}_rugosidade.jpg"))[..., 0]
        m = _MATS[mid] = (cor, nor, rug)
    return m


def _ladrilhar(arr, w, h, escala, desloc=(0, 0)):
    """Repete a textura cobrindo w×h (escala = px da tela por px da textura)."""
    th, tw = arr.shape[:2]
    ys = ((np.arange(h) / escala + desloc[1]) % th).astype(int)
    xs = ((np.arange(w) / escala + desloc[0]) % tw).astype(int)
    return arr[ys][:, xs]


def _distancia_borda(w, h, raio):
    """Distância (px) até a borda de um retângulo arredondado (positiva dentro)."""
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
    cx, cy = w / 2, h / 2
    qx = np.abs(xs - cx) - (w / 2 - raio)
    qy = np.abs(ys - cy) - (h / 2 - raio)
    fora = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0)
    return -(fora - raio)


def _suave(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def esculpir(tema: str, peca: str, w: int, h: int, estado: str = "normal", nivel: int = 2,
             raio: float = 6, escala_px: float = 1.0) -> QImage:
    """A peça pronta (RGBA), iluminada. peca: placa · botao · principal. estado: normal · sobre · apertado.
    escala_px: pixels por unidade (tela de alta resolução)."""
    chave = (tema, peca, w, h, estado, nivel, round(raio, 1), round(escala_px, 2))
    img = _CACHE.get(chave)
    if img is not None:
        return img
    kit = KITS.get(tema, KITS["medieval"])
    mid, tinta, ganho, esc_tex = kit.get(peca, kit["botao"])
    especular, metal = MATERIAIS.get(mid, (0.4, 0.0))
    cor_m, nor_m, rug_m = material(mid)
    W, H = max(4, int(w * escala_px)), max(4, int(h * escala_px))
    e = escala_px
    desloc = (abs(hash((w, h))) % 300, abs(hash((h, w, peca))) % 300)   # cada peça mostra um pedaço diferente
    cor = _ladrilhar(cor_m, W, H, esc_tex * e, desloc)
    nor = _ladrilhar(nor_m, W, H, esc_tex * e, desloc)
    rug = _ladrilhar(rug_m, W, H, esc_tex * e, desloc)

    # ---- altura da PEÇA
    d = _distancia_borda(W, H, raio * e)
    alfa = np.clip(d + 0.5, 0, 1)                                   # borda lisa (antisserrilhado)
    placa = peca == "placa"
    bisel = (10 if placa else 6) * e * (1.0 if nivel == 2 else 0.7)
    altura = _suave(d / bisel)                                      # sobe na borda (bisel arredondado)
    if placa and nivel == 2:                                        # moldura entalhada: sulco + filete
        f1 = 16 * e
        altura -= 0.55 * np.exp(-((d - f1) / (2.2 * e)) ** 2)
        altura += 0.25 * np.exp(-((d - f1 - 5 * e) / (1.6 * e)) ** 2)
    if not placa and estado == "apertado":
        altura = 1 - altura * 0.6                                   # afundado: a luz inverte no bisel
    gy, gx = np.gradient(altura)
    forca = (5.0 if nivel == 2 else 3.2) * (bisel / 6)
    n_peca = np.dstack([-gx * forca, -gy * forca, np.ones_like(altura)])
    detalhe = (0.38 if nivel == 2 else 0.2) * (0.6 if peca != "placa" else 1.0)
    n = n_peca + np.dstack([nor[..., 0] * detalhe, nor[..., 1] * detalhe, np.zeros_like(altura)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)

    # ---- luz
    intens = 1.0 + (0.18 if estado == "sobre" else 0) - (0.12 if estado == "apertado" else 0)
    dif = np.clip(n @ LUZ, 0, 1)
    meio = np.array([0, 0, 1.0]) + LUZ
    meio /= np.linalg.norm(meio)
    brilho_exp = 8 + (1 - rug) * 90
    spec = np.clip(n @ meio, 0, 1) ** brilho_exp * (1 - rug) ** 1.5 * especular * (1.0 if nivel == 2 else 0.5)
    tinta_rgb = np.array([int(tinta[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255
    # (pedido do Manel: "não precisa ser tão realista") a textura entra SUAVE, como pintada à mão:
    # metade cor lisa da peça + metade a textura, e o relevo fino do material bem baixinho
    media = cor.reshape(-1, 3).mean(axis=0)
    cor = media * (1 - ESTILIZADO) + cor * ESTILIZADO
    base = np.clip(cor * tinta_rgb * ganho, 0, 1)
    oclusao = 0.55 + 0.45 * _suave(d / (bisel * 1.6))               # quina mais escura
    luz = (0.38 + 0.82 * dif) * intens * oclusao
    cor_spec = base * metal + (1 - metal)                           # metal: brilho com a cor dele
    rgb = base * luz[..., None] + spec[..., None] * cor_spec
    if estado == "sobre":                                            # um calorzinho no meio ao passar o mouse
        rgb += (0.06 * np.exp(-((d - d.max()) / (H * 0.6)) ** 2))[..., None] * tinta_rgb
    rgb = np.clip(rgb, 0, 1)

    rgba = np.empty((H, W, 4), np.uint8)
    rgba[..., :3] = (rgb * alfa[..., None] * 255).astype(np.uint8)   # pré-multiplicado
    rgba[..., 3] = (alfa * 255).astype(np.uint8)
    img = QImage(rgba.tobytes(), W, H, W * 4, QImage.Format.Format_RGBA8888_Premultiplied).copy()
    if len(_CACHE) > 300:
        _CACHE.clear()
    _CACHE[chave] = img
    return img
