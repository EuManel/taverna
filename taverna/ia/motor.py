"""
🧠 Motor de IA em numpy (v0.47) — roda o grafo ONNX dos modelos de recorte (U²-Net / IS-Net).

Só as operações que esses modelos usam: Conv (com dilatação/passo), Relu, Sigmoid, MaxPool, Resize
(bilinear), Add, Concat e as de "forma" (Shape, Gather, Unsqueeze, Slice, Cast, Constant).
A convolução é feita como 9 multiplicações de matriz (uma por posição do núcleo 3×3), usando o BLAS do
numpy — sem montar a matriz gigante do im2col, então cabe na memória mesmo em 1024×1024.
"""

import numpy as np


class OperacaoDesconhecida(Exception):
    pass


# ====================================================================== operações
def _conv(x, w, b, attr):
    n, cin, h, wd = x.shape
    cout, cin_g, kh, kw = w.shape
    if attr.get("group", 1) != 1:
        raise OperacaoDesconhecida("Conv com grupos")
    dh, dw = (attr.get("dilations") or [1, 1])[:2]
    sh, sw = (attr.get("strides") or [1, 1])[:2]
    p = attr.get("pads") or [0, 0, 0, 0]
    if any(p):
        x = np.pad(x, ((0, 0), (0, 0), (p[0], p[2]), (p[1], p[3])))
    hp, wp = x.shape[2], x.shape[3]
    ho = (hp - (dh * (kh - 1) + 1)) // sh + 1
    wo = (wp - (dw * (kw - 1) + 1)) // sw + 1
    out = np.empty((n, cout, ho, wo), np.float32)
    for k in range(n):
        acc = None
        for i in range(kh):
            for j in range(kw):
                y0, x0 = i * dh, j * dw
                fatia = x[k, :, y0:y0 + sh * (ho - 1) + 1:sh, x0:x0 + sw * (wo - 1) + 1:sw]
                termo = w[:, :, i, j] @ fatia.reshape(cin, -1)
                if acc is None:
                    acc = termo
                else:
                    acc += termo
        if b is not None:
            acc += b[:, None]
        out[k] = acc.reshape(cout, ho, wo)
    return out


def _maxpool(x, attr):
    kh, kw = attr.get("kernel_shape", [2, 2])
    sh, sw = attr.get("strides", [kh, kw])
    if (kh, kw, sh, sw) != (2, 2, 2, 2) or any(attr.get("pads") or [0]):
        raise OperacaoDesconhecida("MaxPool diferente de 2×2/2")
    n, c, h, w = x.shape
    if attr.get("ceil_mode", 0):
        ho, wo = -(-h // 2), -(-w // 2)
    else:
        ho, wo = h // 2, w // 2
    if ho * 2 != h or wo * 2 != w:
        x2 = np.full((n, c, ho * 2, wo * 2), -np.inf, np.float32)
        hh, ww = min(h, ho * 2), min(w, wo * 2)
        x2[:, :, :hh, :ww] = x[:, :, :hh, :ww]
        x = x2
    return x.reshape(n, c, ho, 2, wo, 2).max(axis=(3, 5))


def _pesos_linear(tam_in, tam_out, modo):
    """Índices e pesos da interpolação linear num eixo (half_pixel / pytorch_half_pixel)."""
    escala = tam_out / tam_in
    d = np.arange(tam_out, dtype=np.float64)
    if modo == "pytorch_half_pixel" and tam_out == 1:
        src = np.zeros_like(d)
    elif modo == "align_corners":
        src = d * (tam_in - 1) / max(1, tam_out - 1)
    elif modo == "asymmetric":
        src = d / escala
    else:
        src = (d + 0.5) / escala - 0.5
    src = np.clip(src, 0, tam_in - 1)
    i0 = np.floor(src).astype(np.int64)
    i1 = np.minimum(i0 + 1, tam_in - 1)
    f = (src - i0).astype(np.float32)
    return i0, i1, f


def _resize(x, escalas, tamanhos, attr):
    if attr.get("mode", "nearest") != "linear":
        raise OperacaoDesconhecida(f"Resize {attr.get('mode')}")
    n, c, h, w = x.shape
    if tamanhos is not None and len(tamanhos):
        ho, wo = int(tamanhos[-2]), int(tamanhos[-1])
    else:
        ho, wo = int(np.floor(h * escalas[-2])), int(np.floor(w * escalas[-1]))
    if (ho, wo) == (h, w):
        return x
    modo = attr.get("coordinate_transformation_mode", "half_pixel")
    y0, y1, fy = _pesos_linear(h, ho, modo)
    x0, x1, fx = _pesos_linear(w, wo, modo)
    cima = x[:, :, y0, :] * (1 - fy)[:, None] + x[:, :, y1, :] * fy[:, None]
    return (cima[:, :, :, x0] * (1 - fx) + cima[:, :, :, x1] * fx).astype(np.float32)


def _slice(x, starts, ends, axes=None, steps=None):
    axes = list(range(len(starts))) if axes is None else [int(a) for a in np.ravel(axes)]
    steps = [1] * len(axes) if steps is None else [int(s) for s in np.ravel(steps)]
    fatias = [slice(None)] * x.ndim
    for s, e, a, p in zip(np.ravel(starts), np.ravel(ends), axes, steps):
        e = int(e)
        e = None if (p > 0 and e >= 2 ** 62) else e
        fatias[a] = slice(int(s), e, p)
    return x[tuple(fatias)]


# ====================================================================== o grafo
class Motor:
    def __init__(self, modelo):
        self.m = modelo
        # pesos das convoluções já em float32 contíguo
        for k, v in list(modelo.pesos.items()):
            if v.dtype == np.float64 or v.dtype == np.float16:
                modelo.pesos[k] = v.astype(np.float32)
        # último uso de cada tensor, pra liberar memória cedo
        self._ultimo = {}
        for i, no in enumerate(modelo.nos):
            for e in no.entradas:
                self._ultimo[e] = i

    def rodar(self, entrada: np.ndarray, progresso=None, cancelado=None) -> list:
        m = self.m
        vals = dict(m.pesos)
        vals[m.entradas[0]] = entrada.astype(np.float32)
        manter = set(m.saidas) | set(m.pesos)
        total = len(m.nos)
        for i, no in enumerate(m.nos):
            if cancelado is not None and cancelado():
                return []
            ent = [vals.get(e) if e else None for e in no.entradas]
            saida = self._op(no, ent)
            vals[no.saidas[0]] = saida
            for e in no.entradas:   # libera o que ninguém mais usa
                if e and self._ultimo.get(e) == i and e not in manter:
                    vals.pop(e, None)
            if progresso is not None and (no.op == "Conv" or i == total - 1):
                progresso((i + 1) / total)
        return [vals[s] for s in m.saidas]

    @staticmethod
    def _op(no, ent):
        op, a = no.op, no.attr
        if op == "Conv":
            return _conv(ent[0], ent[1], ent[2] if len(ent) > 2 else None, a)
        if op == "Relu":
            return np.maximum(ent[0], 0)
        if op == "Sigmoid":
            return (0.5 * (1.0 + np.tanh(0.5 * ent[0]))).astype(np.float32)   # sigmoide sem estourar
        if op == "Add":
            return ent[0] + ent[1]
        if op == "MaxPool":
            return _maxpool(ent[0], a)
        if op == "Concat":
            return np.concatenate([e for e in ent if e is not None], axis=int(a.get("axis", 0)))
        if op == "Resize":
            escalas = ent[2] if len(ent) > 2 and ent[2] is not None and ent[2].size else None
            tam = ent[3] if len(ent) > 3 and ent[3] is not None and ent[3].size else None
            return _resize(ent[0], escalas, tam, a)
        if op == "Upsample":
            return _resize(ent[0], ent[1], None, {"mode": "linear" if a.get("mode") != "nearest" else "nearest",
                                                   "coordinate_transformation_mode": "asymmetric"})
        if op == "Constant":
            v = a.get("value")
            return np.asarray(v)
        if op == "Shape":
            return np.asarray(ent[0].shape, np.int64)
        if op == "Gather":
            return np.take(ent[0], ent[1].astype(np.int64), axis=int(a.get("axis", 0)))
        if op == "Unsqueeze":
            eixos = a.get("axes")
            if eixos is None and len(ent) > 1:
                eixos = ent[1].tolist()
            x = np.asarray(ent[0])
            for e in sorted(int(v) for v in np.ravel(eixos)):
                x = np.expand_dims(x, e)
            return x
        if op == "Slice":
            return _slice(ent[0], ent[1], ent[2], ent[3] if len(ent) > 3 else None,
                          ent[4] if len(ent) > 4 else None)
        if op == "Cast":
            from .onnx_leve import _TIPOS
            return np.asarray(ent[0]).astype(_TIPOS.get(int(a.get("to", 1)), np.float32))
        raise OperacaoDesconhecida(op)
