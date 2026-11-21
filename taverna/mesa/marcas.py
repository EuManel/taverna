"""
Marcas no chão deixadas pelas áreas de efeito (v0.39) — "o cenário reage".

Fogo queima o chão (carvão, cinza, borda marrom chamuscada), lava deixa rocha vulcânica rachada,
raio deixa a marca ramificada, ácido corrói, veneno mancha, gelo deixa geada, água molha, vinhas
deixam musgo, magia deixa um resíduo na cor dela, radiante descora, escuridão deixa veios de corrupção.

Como funciona:
  - enquanto a área está PARADA no lugar, o chão embaixo vai "pegando" (a própria área desenha a marca
    aparecendo aos poucos, em ~3 s). Arrastar pra posicionar não deixa rastro;
  - quando a área é apagada (ou movida depois de ter "pegado"), a marca vira uma pincelada do TERRENO
    ({"t": "marca"}) — vai pro arquivo da aventura, pros jogadores e entra no relevo do piso;
  - fica até o mestre limpar (Atmosfera → Limpar marcas do chão, ou selecionar e apagar como pincelada).

A marca é gerada aqui (numpy): contorno da área com borda irregular × textura do tipo.
"""

from collections import OrderedDict

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPolygonF

from . import texturas as T

ESCALA = 0.8          # pixels da marca por unidade da cena (1 m ≈ 51 px)
TEX = 320             # textura de cada tipo (repete a cada ~6 m)
TEMPO_QUEIMA = 3.0    # segundos parada até a marca "pegar" de vez
ATRASO = 0.4          # (antes disso nada aparece: é o tempo de soltar o mouse)

# efeito → tipo de marca (efeitos sem marca: luz, fumaça, teia)
MARCA_DO_EFEITO = {"fogo": "queimado", "lava": "basalto", "eletrico": "chamuscado", "acido": "corroido",
                   "veneno": "mancha", "gelo": "geada", "agua": "molhado", "planta": "musgo",
                   "magia": "residuo", "sagrado": "descorado", "trevas": "corrupcao"}

_TEXTURAS = {}
_IMAGENS = OrderedDict()


def _suave(a, b, x):
    t = np.clip((x - a) / max(1e-6, b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ====================================================================== texturas por tipo (rgb, alfa)
def _textura(tipo: str, cor_livre: str = ""):
    chave = (tipo, cor_livre)
    if chave in _TEXTURAS:
        return _TEXTURAS[chave]
    rng = np.random.default_rng(abs(hash(tipo)) % (2 ** 31))
    w = h = TEX
    n = T.fbm(w, h, rng, [(64, 1.0), (24, 0.6), (8, 0.3)])
    # Duas partes: (mrgb, m) ESCURECE/TINGE o chão que já está lá (as tábuas continuam aparecendo,
    # só queimadas) e (rgb, a) COBRE por cima (cinza, geada, musgo…).
    mrgb, m = np.ones((h, w, 3), np.float32), np.zeros((h, w), np.float32)
    if tipo == "queimado":
        cinza = T.fbm(w, h, rng, [(20, 1.0), (6, 0.5)])
        racha = T.fissuras(w, h, rng, 14, 1.0)
        mrgb = T.misturar(T.cor("#1e120a"), T.cor("#3a2414"), n)
        m = np.clip(0.78 + 0.22 * n + 0.3 * racha, 0, 1)          # madeira/pedra torrada
        rgb = T.misturar(T.cor("#3a3530"), T.cor("#6a645d"), cinza) * T.grao(w, h, rng, 0.15)[..., None]
        rgb = T.misturar(rgb, T.cor("#050302"), racha)
        a = np.clip(_suave(0.55, 0.85, cinza) * 0.55 + racha * 0.8, 0, 1)   # cinza e rachaduras por cima
    elif tipo == "basalto":
        bolha = T.fbm(w, h, rng, [(10, 1.0), (4, 0.6), (2, 0.3)])
        rgb = T.misturar(T.cor("#141010"), T.cor("#2e2724"), n * 0.6 + bolha * 0.4)
        rgb = rgb * T.oclusao(bolha, 0.6, 2)[..., None] * T.grao(w, h, rng, 0.2)[..., None]
        racha = T.fissuras(w, h, rng, 22, 1.4)
        rgb = T.misturar(rgb, T.cor("#521407"), racha * 0.85)
        a = np.full((h, w), 0.96, np.float32)
    elif tipo == "chamuscado":
        v1 = T.sulcos(T.fbm(w, h, rng, [(48, 1.0), (16, 0.5), (6, 0.2)]), 0.022)
        v2 = T.sulcos(T.fbm(w, h, rng, [(30, 1.0), (10, 0.4)]), 0.016)
        veio = np.clip(v1 + 0.7 * v2, 0, 1)
        mrgb = np.broadcast_to(T.cor("#1d1712"), (h, w, 3)).copy()
        m = np.clip(0.25 + 0.75 * veio, 0, 1)
        rgb = np.broadcast_to(T.cor("#06050a"), (h, w, 3)).copy()
        a = veio * 0.6
    elif tipo == "corroido":
        rgb = T.misturar(T.cor("#6f7d1a"), T.cor("#bdb873"), _suave(0.45, 0.75, n))
        pts = (rng.random((180, 2)) * [w, h]).astype(np.float32)
        d1, _d2, _ = T.voronoi(w, h, pts)
        furo = np.clip(1 - d1 / 2.6, 0, 1)
        mrgb = T.misturar(T.cor("#8a9a40"), T.cor("#1d2008"), furo)
        m = 0.45 + 0.5 * furo
        a = 0.2 + 0.3 * _suave(0.5, 0.8, n)
    elif tipo == "mancha":
        m2 = T.fbm(w, h, rng, [(40, 1.0), (12, 0.5)])
        mrgb = T.misturar(T.cor("#6f9a4a"), T.cor("#8a6a90"), _suave(0.4, 0.7, m2))
        m = 0.45 + 0.4 * _suave(0.3, 0.8, n)
        rgb, a = T.misturar(T.cor("#3b5a1e"), T.cor("#4f3552"), m2), 0.12 * n
    elif tipo == "geada":
        f1 = T.sulcos(T.fbm(w, h, rng, [(36, 1.0), (12, 0.5), (4, 0.25)]), 0.03)
        f2 = T.sulcos(T.fbm(w, h, rng, [(20, 1.0), (6, 0.5)]), 0.02)
        cristal = np.clip(f1 + 0.8 * f2, 0, 1)
        rgb = T.misturar(T.cor("#cfe6f5"), T.cor("#ffffff"), cristal) * T.grao(w, h, rng, 0.06)[..., None]
        a = 0.38 + 0.22 * n + 0.38 * cristal
    elif tipo == "molhado":   # chão molhado = mais escuro e um pouco azulado; poça com reflexo
        poca = _suave(0.55, 0.75, n)
        mrgb = T.misturar(T.cor("#55636e"), T.cor("#33414d"), poca)
        m = 0.55 + 0.35 * poca
        rgb = np.broadcast_to(T.cor("#bcd6ea"), (h, w, 3)).copy()
        a = poca * 0.12 * T.fbm(w, h, rng, [(6, 1.0)])
    elif tipo == "musgo":
        rgb = T.misturar(T.cor("#334f17"), T.cor("#5f8a2c"), T.fbm(w, h, rng, [(10, 1.0), (3, 0.6)]))
        pts = (rng.random((260, 2)) * [w, h]).astype(np.float32)
        d1, _d2, _ = T.voronoi(w, h, pts)
        folha = np.clip(1 - d1 / 3.2, 0, 1)
        rgb = T.misturar(rgb, T.cor("#7cb043"), folha * 0.8)
        a = np.clip((n - 0.2) * 1.7, 0, 1) * 0.85 + folha * 0.15
    elif tipo == "residuo":
        base = T.cor(cor_livre or "#b07aff")
        linhas = np.clip(T.sulcos(T.fbm(w, h, rng, [(40, 1.0), (14, 0.5)]), 0.03)
                         + T.sulcos(T.fbm(w, h, rng, [(24, 1.0)]), 0.02), 0, 1)
        rgb = T.misturar(base * 0.45, np.clip(base * 1.25, 0, 1), linhas)
        a = 0.14 + 0.5 * linhas
    elif tipo == "descorado":
        rgb = T.misturar(T.cor("#e9dcae"), T.cor("#fff6d8"), n)
        a = 0.18 + 0.2 * n
    elif tipo == "corrupcao":
        veio = np.clip(T.sulcos(T.fbm(w, h, rng, [(36, 1.0), (12, 0.5)]), 0.03) * 1.2, 0, 1)
        mrgb = np.broadcast_to(T.cor("#3a2a48"), (h, w, 3)).copy()
        m = 0.5 + 0.35 * n
        rgb = np.broadcast_to(T.cor("#5a2a78"), (h, w, 3)).copy()
        a = 0.6 * veio
    else:
        rgb, a = np.zeros((h, w, 3), np.float32), np.zeros((h, w), np.float32)
    f32 = lambda v: np.clip(np.asarray(v, np.float32), 0, 1)
    a = np.broadcast_to(f32(a), (h, w)).copy()
    _TEXTURAS[chave] = (f32(rgb), a, f32(mrgb), np.broadcast_to(f32(m), (h, w)).copy())
    return _TEXTURAS[chave]


# ====================================================================== a marca de uma área
def imagem(tipo: str, pontos, semente: int, cor_livre: str = ""):
    """(QImage, retângulo na cena) da marca com o contorno 'pontos' (polígono na cena)."""
    chave = (tipo, tuple(map(tuple, pontos)), int(semente), cor_livre)
    if chave in _IMAGENS:
        _IMAGENS.move_to_end(chave)
        return _IMAGENS[chave]
    pol = QPolygonF([QPointF(float(x), float(y)) for x, y in pontos])
    r = pol.boundingRect().adjusted(-20, -20, 20, 20)
    W = max(8, min(1400, int(r.width() * ESCALA) + 1))
    H = max(8, min(1400, int(r.height() * ESCALA) + 1))
    sx, sy = W / r.width(), H / r.height()
    # contorno → máscara
    masc = QImage(W, H, QImage.Format.Format_Grayscale8)
    masc.fill(0)
    p = QPainter(masc)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(sx, sy)
    p.translate(-r.x(), -r.y())
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 255, 255))
    p.drawPolygon(pol)
    p.end()
    ptr = masc.constBits()
    ptr.setsize(masc.sizeInBytes())
    m = np.frombuffer(ptr, np.uint8).reshape(H, masc.bytesPerLine())[:, :W].astype(np.float32) / 255.0
    macia = T.borrar(m, 9)
    rng = np.random.default_rng(int(semente) % (2 ** 31))
    n = T.fbm(W, H, rng, [(40, 1.0), (17, 0.6), (6, 0.3)])
    irregular = 0.6 if tipo in ("basalto", "geada") else 1.15   # (lava e gelo: placa mais inteira)
    borda = _suave(0.0, 1.0, (macia + (n - 0.5) * irregular - 0.45) * 2.4)   # contorno irregular
    miolo = _suave(0.55, 0.95, macia)
    # textura do tipo, presa à CENA (marcas vizinhas emendam)
    rgb_t, a_t, mrgb_t, m_t = _textura(tipo, cor_livre)
    k = ESCALA
    xs = ((r.x() + (np.arange(W) + 0.5) / sx) * k).astype(np.int64) % TEX
    ys = ((r.y() + (np.arange(H) + 0.5) / sy) * k).astype(np.int64) % TEX
    rgb, a = rgb_t[ys][:, xs], a_t[ys][:, xs]
    mrgb, mm = mrgb_t[ys][:, xs], m_t[ys][:, xs]
    if tipo == "queimado":   # mais forte no meio; borda marrom chamuscada
        a = a * miolo
        mm = mm * (0.45 + 0.55 * miolo)
        aro = borda * (1 - miolo)
        mrgb = T.misturar(mrgb, T.cor("#7a4a26"), aro)
    elif tipo in ("chamuscado", "descorado", "residuo"):
        a = a * (0.45 + 0.55 * miolo)
        mm = mm * (0.45 + 0.55 * miolo)
    else:
        a = a * (0.8 + 0.2 * miolo)
    img_m = _rgba(mrgb, borda * mm)    # escurece/tinge (Multiply)
    img_c = _rgba(rgb, borda * a)      # cobre (por cima)
    _IMAGENS[chave] = (img_m, img_c, r)
    while len(_IMAGENS) > 48:
        _IMAGENS.popitem(last=False)
    return img_m, img_c, r


def _rgba(rgb, alfa) -> QImage:
    H, W = alfa.shape
    saida = np.empty((H, W, 4), np.uint8)
    saida[..., :3] = np.clip(rgb * 255, 0, 255)
    saida[..., 3] = np.clip(alfa * 255, 0, 255)
    return QImage(saida.tobytes(), W, H, W * 4, QImage.Format.Format_RGBA8888).copy()


def desenhar(painter: QPainter, img_m: QImage, img_c: QImage, r: QRectF, multiplicar: bool = True):
    """As duas partes da marca. multiplicar=False: o motor não sabe 'Multiply' (OpenGL) —
    aí a parte que escurece vai por cima, parecido."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    if multiplicar:
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
    painter.drawImage(r, img_m)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
    painter.drawImage(r, img_c)
    painter.restore()


def desenhar_op(painter: QPainter, op: dict):
    """Desenha a pincelada-marca do terreno (painter em coordenadas da cena, num azulejo raster)."""
    img_m, img_c, r = imagem(op.get("k", "queimado"), op.get("p", []), op.get("s", 1), op.get("c", ""))
    desenhar(painter, img_m, img_c, r)


def op_da_area(area, tipo: str | None = None) -> dict | None:
    """A pincelada-marca do terreno pra uma área de efeito (onde ela está agora).
    tipo: força um tipo de marca (ex.: o gás que explodiu deixa 'queimado')."""
    tipo = tipo or MARCA_DO_EFEITO.get(area.efeito)
    if not tipo:
        return None
    pol = area.caminho_cena().toFillPolygon()
    pts = [[round(q.x(), 1), round(q.y(), 1)] for q in pol]
    if len(pts) > 96:   # (círculo vem com muitos pontos; 96 bastam)
        passo = len(pts) / 96
        pts = [pts[int(i * passo)] for i in range(96)]
    if len(pts) < 3:
        return None
    op = {"t": "marca", "m": "marca", "k": tipo, "p": pts, "s": int(area._semente)}
    if tipo == "residuo" and area.cor:
        op["c"] = area.cor
    return op
