"""
Volume pros objetos da mesa (acabamento): a partir do desenho "chapado" do objeto, gera
  - o CORPO com relevo (luz de cima-esquerda, quina clara de um lado e escura do outro)
  - a SOMBRA macia que ele projeta no chão
Tudo calculado uma vez e guardado (cache), então depois é só colar duas imagens — fica até
mais leve do que redesenhar o objeto toda hora.
"""

from collections import OrderedDict

from PyQt6.QtGui import QImage, QPixmap

try:
    import numpy as np
except ImportError:      # sem numpy: os objetos ficam como antes
    np = None

_CACHE: OrderedDict = OrderedDict()
MAX_CACHE = 260


def _desfocar(a, raio: int):
    """Desfoque de caixa (rápido, com somas acumuladas), 2 passadas ≈ sombra macia."""
    for _ in range(2):
        for eixo in (0, 1):
            pad = [(0, 0), (0, 0)]
            pad[eixo] = (raio + 1, raio)
            c = np.cumsum(np.pad(a, pad, mode="constant"), axis=eixo)
            n = a.shape[eixo]
            if eixo == 0:
                a = (c[2 * raio + 1:2 * raio + 1 + n] - c[:n]) / (2 * raio + 1)
            else:
                a = (c[:, 2 * raio + 1:2 * raio + 1 + n] - c[:, :n]) / (2 * raio + 1)
    return a


def _desloca(a, dy, dx):
    """a deslocado (com zero entrando pelas bordas): saída[y, x] = a[y - dy, x - dx]."""
    s = np.zeros_like(a)
    h, w = a.shape
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    s[yd, xd] = a[ys, xs]
    return s


def com_volume(chave, pm: QPixmap, forca: float = 1.0, margem: int = 14):
    """
    Devolve (corpo, sombra, margem). `sombra` é maior que o corpo: tem `margem` pixels de sobra
    em volta. `chave` identifica o objeto no cache (tipo, tamanho, nível…).
    """
    if chave in _CACHE:
        _CACHE.move_to_end(chave)
        return _CACHE[chave]
    if np is None or pm.isNull():
        return pm, None, 0
    img = pm.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
    w, h = img.width(), img.height()
    ptr = img.bits()
    ptr.setsize(img.sizeInBytes())
    arr = np.frombuffer(ptr, np.uint8).reshape(h, img.bytesPerLine())[:, :w * 4].reshape(h, w, 4).astype(np.float32)
    alfa = arr[:, :, 3] / 255.0
    lum = arr[:, :, 0] * 0.30 + arr[:, :, 1] * 0.59 + arr[:, :, 2] * 0.11
    # relevo interno (o claro/escuro do desenho vira altura)
    dx = _desloca(lum, 0, -1) - _desloca(lum, 0, 1)
    dy = _desloca(lum, -1, 0) - _desloca(lum, 1, 0)
    luz = np.clip(-(dx + dy) * 0.45 * forca, -30 * forca, 26 * forca) * (alfa > 0.9)
    # quina do contorno: clara em cima-esquerda, escura embaixo-direita
    e = max(2, int(round(min(w, h) * 0.02)))
    clara = np.clip(alfa - _desloca(alfa, e, e), 0, 1)
    escura = np.clip(alfa - _desloca(alfa, -e, -e), 0, 1)
    ajuste = luz + clara * 42 * forca - escura * 56 * forca
    arr[:, :, :3] = np.clip(arr[:, :, :3] + ajuste[:, :, None], 0, 255)
    corpo = np.ascontiguousarray(arr.astype(np.uint8))
    pm_corpo = QPixmap.fromImage(QImage(corpo.data, w, h, w * 4, QImage.Format.Format_RGBA8888).copy())
    # sombra projetada
    m = int(margem)
    sombra_a = _desfocar(np.pad(alfa, m, mode="constant"), max(2, m // 3))
    sh = np.zeros((h + 2 * m, w + 2 * m, 4), np.uint8)
    sh[:, :, 3] = np.clip(sombra_a * 150 * min(1.2, forca), 0, 255).astype(np.uint8)
    pm_sombra = QPixmap.fromImage(QImage(sh.data, w + 2 * m, h + 2 * m, (w + 2 * m) * 4,
                                         QImage.Format.Format_RGBA8888).copy())
    _CACHE[chave] = (pm_corpo, pm_sombra, m)
    while len(_CACHE) > MAX_CACHE:
        _CACHE.popitem(last=False)
    return _CACHE[chave]
