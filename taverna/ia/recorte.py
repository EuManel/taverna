"""
✂🧠 Removedor de fundo com IA (v0.47) — pedido do Manel na reta final.

Usa modelos abertos de recorte (formato ONNX), rodados pelo nosso motor em numpy (`motor.py`), sem
instalar nada: o programa só BAIXA o arquivo do modelo na primeira vez (fica em Documentos/Taverna/IA).
  - Rápido  : U²-Netp  (~4,6 MB)  · Xuebin Qin et al., Apache-2.0
  - Caprichado: IS-Net (DIS) geral (~170 MB) · Xuebin Qin et al., Apache-2.0
Os arquivos .onnx são os convertidos pelo projeto rembg (Daniel Gatis, MIT). Créditos em LICENCAS.md.
"""

import os
import threading

import numpy as np

URL_BASE = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/"

# chave: (nome, arquivo, tamanho aproximado em MB, lado da entrada, média, desvio, descrição)
MODELOS = {
    "rapido": ("Rápido", "u2netp.onnx", 4.6, 320, (0.485, 0.456, 0.406), (0.229, 0.224, 0.225),
               "Leve e rápido (uns segundos). Bom pra token e objeto com contorno simples."),
    "caprichado": ("Caprichado", "isnet-general-use.onnx", 170, 1024, (0.5, 0.5, 0.5), (1.0, 1.0, 1.0),
                   "Recorte bem mais fino (cabelo, capa, armas). Demora mais e baixa ~170 MB uma vez."),
}
TAMANHO_MIN = {"u2netp.onnx": 4_000_000, "isnet-general-use.onnx": 150_000_000}


def pasta_ia() -> str:
    """Documentos/Taverna/IA (ou TAVERNA_PASTA_IA, pros testes)."""
    p = os.environ.get("TAVERNA_PASTA_IA")
    if not p:
        from PyQt6.QtCore import QStandardPaths
        docs = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation) \
            or os.path.expanduser("~")
        p = os.path.join(docs, "Taverna", "IA")
    os.makedirs(p, exist_ok=True)
    return p


def caminho_modelo(chave: str) -> str:
    return os.path.join(pasta_ia(), MODELOS[chave][1])


def modelo_instalado(chave: str) -> bool:
    c = caminho_modelo(chave)
    return os.path.isfile(c) and os.path.getsize(c) >= TAMANHO_MIN.get(MODELOS[chave][1], 1)


def baixar_modelo(chave: str, progresso=None, cancelado=None) -> str:
    """Baixa o modelo (só quando o usuário pede). Grava num .parcial e renomeia no fim."""
    import urllib.request
    arquivo = MODELOS[chave][1]
    destino = caminho_modelo(chave)
    parcial = destino + ".parcial"
    req = urllib.request.Request(URL_BASE + arquivo, headers={"User-Agent": "Taverna"})
    with urllib.request.urlopen(req, timeout=30) as r, open(parcial, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0) or int(MODELOS[chave][2] * 1e6)
        feito = 0
        while True:
            if cancelado is not None and cancelado():
                break
            bloco = r.read(1 << 20)
            if not bloco:
                break
            f.write(bloco)
            feito += len(bloco)
            if progresso is not None:
                progresso(min(1.0, feito / total))
    if cancelado is not None and cancelado():
        os.remove(parcial)
        raise InterruptedError("cancelado")
    if os.path.getsize(parcial) < TAMANHO_MIN.get(arquivo, 1):
        os.remove(parcial)
        raise IOError("O download veio incompleto. Tente de novo.")
    os.replace(parcial, destino)
    return destino


# ====================================================================== rodar
_motores = {}
_trava = threading.Lock()


def _motor(chave: str):
    with _trava:
        if chave not in _motores:
            from .motor import Motor
            from .onnx_leve import Modelo
            _motores[chave] = Motor(Modelo(caminho_modelo(chave)))
        return _motores[chave]


def _redimensionar(arr: np.ndarray, w: int, h: int) -> np.ndarray:
    """Redimensiona um array float (H, W, C) com bilinear (Qt não precisa: numpy puro)."""
    from .motor import _pesos_linear
    h0, w0 = arr.shape[:2]
    y0, y1, fy = _pesos_linear(h0, h, "half_pixel")
    x0, x1, fx = _pesos_linear(w0, w, "half_pixel")
    fy = fy[:, None, None] if arr.ndim == 3 else fy[:, None]
    cima = arr[y0] * (1 - fy) + arr[y1] * fy
    fx = fx[None, :, None] if arr.ndim == 3 else fx[None, :]
    return cima[:, x0] * (1 - fx) + cima[:, x1] * fx


def mascara(rgba: np.ndarray, chave: str = "rapido", progresso=None, cancelado=None) -> np.ndarray | None:
    """rgba (H, W, 4) uint8 → máscara float32 (H, W) de 0 (fundo) a 1 (o que fica)."""
    _nome, _arq, _mb, lado, media, desvio, _d = MODELOS[chave]
    h, w = rgba.shape[:2]
    rgb = rgba[:, :, :3].astype(np.float32)
    # o que já era transparente conta como fundo preto (igual ao rembg)
    rgb *= (rgba[:, :, 3:4].astype(np.float32) / 255.0)
    entrada = _redimensionar(rgb, lado, lado)
    entrada /= max(float(entrada.max()), 1e-6)
    entrada = (entrada - np.array(media, np.float32)) / np.array(desvio, np.float32)
    entrada = entrada.transpose(2, 0, 1)[None].astype(np.float32)
    saidas = _motor(chave).rodar(entrada, progresso, cancelado)
    if not saidas:
        return None
    pred = saidas[0][0, 0]
    mi, ma = float(pred.min()), float(pred.max())
    pred = (pred - mi) / max(ma - mi, 1e-6)
    m = _redimensionar(pred.astype(np.float32), w, h)
    return np.clip(m, 0, 1).astype(np.float32)


def aplicar_mascara(rgba: np.ndarray, m: np.ndarray, firmeza: float = 0.5) -> np.ndarray:
    """Usa a máscara como transparência. `firmeza` 0 = borda bem suave · 1 = recorte seco."""
    k = 1.0 + 9.0 * firmeza                   # contraste em volta de 0,5
    a = np.clip((m - 0.5) * k + 0.5, 0, 1)
    a[m < 0.04] = 0                           # resto de fundo vira transparente de vez
    novo = rgba.copy()
    novo[:, :, 3] = (rgba[:, :, 3].astype(np.float32) * a).astype(np.uint8)
    return novo
