"""
🗺 Importar mapa Universal VTT (v0.60, pedido do Manel): `.dd2vtt` (Dungeondraft), `.uvtt`, `.df2vtt`
(DungeonFog) e afins. É um JSON com:

  resolution: map_origin {x,y}, map_size {x,y} (em quadrados), pixels_per_grid
  image: o mapa (PNG/WebP em base64)
  line_of_sight / objects_line_of_sight: listas de polilinhas [{x,y}, ...] (em quadrados) → PAREDES
  portals: {position, bounds: [p0, p1], rotation, closed, freestanding} → PORTAS (aberta/fechada)
  lights: {position, range (quadrados), intensity, color "AARRGGBB", shadows} → LUZES

Escala: o Taverna é 1 quadrado = 1 m; mapa de D&D é 5 pés = 1,5 m (padrão da importação).
Material das paredes: pedra por padrão (decisão do Manel); portas de madeira.
"""

import base64
import json
import math
import uuid

from PyQt6.QtCore import QLineF, QPointF
from PyQt6.QtGui import QColor

from ..config import CELULA

EXTENSOES = (".dd2vtt", ".uvtt", ".df2vtt", ".json")
FILTRO = "Mapa Universal VTT (*.dd2vtt *.uvtt *.df2vtt *.json)"


class ErroUVTT(ValueError):
    pass


def _ponto(p):
    if isinstance(p, dict):
        return float(p.get("x", 0)), float(p.get("y", 0))
    return float(p[0]), float(p[1])


def ler(fonte) -> dict:
    """Lê o arquivo (caminho, bytes ou dict já carregado) e devolve tudo em QUADRADOS DO MAPA, já com a
    origem descontada (0,0 = canto de cima-esquerda da imagem)."""
    if isinstance(fonte, dict):
        d = fonte
    else:
        try:
            if isinstance(fonte, (bytes, bytearray)):
                texto = bytes(fonte).decode("utf-8-sig")
            else:
                with open(fonte, "r", encoding="utf-8-sig") as f:
                    texto = f.read()
            d = json.loads(texto)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as erro:
            raise ErroUVTT(f"Não consegui ler o arquivo: {erro}") from erro
    if not isinstance(d, dict) or "resolution" not in d:
        raise ErroUVTT("Esse arquivo não parece ser um mapa Universal VTT (falta \"resolution\").")
    res = d.get("resolution") or {}
    ox, oy = _ponto(res.get("map_origin", {"x": 0, "y": 0}))
    tw, th = _ponto(res.get("map_size", {"x": 0, "y": 0}))
    ppg = float(res.get("pixels_per_grid") or 0)
    imagem = None
    if d.get("image"):
        try:
            texto_img = d["image"]
            if "," in texto_img[:80] and texto_img.startswith("data:"):
                texto_img = texto_img.split(",", 1)[1]
            imagem = base64.b64decode(texto_img)
        except (ValueError, TypeError) as erro:
            raise ErroUVTT(f"A imagem do mapa veio estragada: {erro}") from erro
    if tw <= 0 or th <= 0:
        if imagem and ppg > 0:   # sem tamanho: tira da imagem
            from PyQt6.QtGui import QImage
            img = QImage.fromData(imagem)
            tw, th = img.width() / ppg, img.height() / ppg
        else:
            raise ErroUVTT("O arquivo não diz o tamanho do mapa.")

    def rel(p):
        x, y = _ponto(p)
        return x - ox, y - oy

    paredes = []
    for chave in ("line_of_sight", "objects_line_of_sight"):
        for linha in d.get(chave) or []:
            pts = [rel(p) for p in linha or []]
            for a, b in zip(pts, pts[1:]):
                if math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-3:
                    paredes.append((a, b))
    portas = []
    for p in d.get("portals") or []:
        limites = p.get("bounds") or []
        if len(limites) < 2:
            continue
        a, b = rel(limites[0]), rel(limites[1])
        if math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-3:
            continue
        portas.append({"a": a, "b": b, "fechada": bool(p.get("closed", True))})
    luzes = []
    for l in d.get("lights") or []:
        cor = str(l.get("color") or "ffffffff").lstrip("#")
        if len(cor) == 8:          # AARRGGBB
            cor = cor[2:]
        if len(cor) != 6:
            cor = "ffffff"
        luzes.append({"pos": rel(l.get("position", {"x": 0, "y": 0})), "alcance": float(l.get("range") or 4),
                      "intensidade": float(l.get("intensity") or 1), "cor": "#" + cor.lower()})
    return {"imagem": imagem, "tamanho": (tw, th), "paredes": paredes, "portas": portas, "luzes": luzes,
            "formato": d.get("format")}


def aplicar(cena, dados: dict, metros_por_quadrado: float = 1.5, material: str = "pedra",
            centro: QPointF | None = None, nome: str = "Mapa") -> dict:
    """Põe o mapa na cena: imagem (no tamanho certo), paredes, portas e luzes. Devolve a contagem."""
    from .mapa import MapaItem
    from .luzes import LuzItem
    from .portas import PortaItem
    k = metros_por_quadrado * CELULA          # pixels de cena por quadrado do mapa
    tw, th = dados["tamanho"]
    centro = centro or QPointF(0, 0)
    # canto de cima-esquerda grudado num canto do grid do Taverna
    x0 = round((centro.x() - tw * k / 2) / CELULA) * CELULA
    y0 = round((centro.y() - th * k / 2) / CELULA) * CELULA

    def cena_xy(p):
        return QPointF(x0 + p[0] * k, y0 + p[1] * k)

    mapa = None
    if dados.get("imagem"):
        mapa = MapaItem(dados["imagem"], tw * metros_por_quadrado, th * metros_por_quadrado)
        mapa.nome = nome
        camada = cena.camada_por_tipo("mapa") or cena.camadas[0]
        cena._colocar(mapa, camada, None)
        mapa.setPos(camada.mapFromScene(QPointF(x0, y0)))
    # paredes (de uma vez só: recalcular a cada uma é lento em mapa grande)
    n_paredes = 0
    if cena.paredes is not None and dados["paredes"]:
        segs = dict(cena.paredes.segmentos)
        for a, b in dados["paredes"]:
            pa, pb = cena_xy(a), cena_xy(b)
            if QLineF(pa, pb).length() < 2:
                continue
            segs[uuid.uuid4().hex[:12]] = {"a": [round(pa.x(), 1), round(pa.y(), 1)],
                                           "b": [round(pb.x(), 1), round(pb.y(), 1)], "m": material}
            n_paredes += 1
        from .construcao import sem_sobreposicao
        cena.paredes.definir(sem_sobreposicao(segs))
    # portas: abrem o vão na parede embaixo delas
    n_portas = 0
    camada_p = cena.camada_por_tipo("paredes")
    if camada_p is not None:
        for p in dados["portas"]:
            pa, pb = cena_xy(p["a"]), cena_xy(p["b"])
            linha = QLineF(pa, pb)
            largura_m = linha.length() / CELULA
            meio = linha.pointAt(0.5)
            angulo = -linha.angle()
            cena._abrir_vao(meio, angulo, largura_m)
            porta = PortaItem("madeira", round(largura_m, 2))
            porta.setRotation(angulo)
            porta.setParentItem(camada_p)
            porta.setPos(camada_p.mapFromScene(meio))
            porta.aberta = not p["fechada"]
            porta.aplicar_trava(camada_p.travada)
            porta.pular_animacao()
            n_portas += 1
    # luzes
    n_luzes = 0
    camada_l = cena.camada_por_tipo("luzes")
    if camada_l is not None:
        for l in dados["luzes"]:
            luz = LuzItem("lampada")
            fraco = max(0.5, l["alcance"] * metros_por_quadrado)
            luz.raio_fraco = fraco
            luz.raio_forte = fraco * max(0.25, min(0.8, 0.5 * l["intensidade"]))
            luz.cor = QColor(l["cor"])
            luz.tremula = False
            luz.setParentItem(camada_l)
            luz.setPos(camada_l.mapFromScene(cena_xy(l["pos"])))
            luz.aplicar_trava(camada_l.travada)
            n_luzes += 1
    cena.marcar_modificada()
    cena.camadas_mudaram.emit()
    cena.registrar()
    cena.recalcular_luzes()
    return {"mapa": mapa, "paredes": n_paredes, "portas": n_portas, "luzes": n_luzes,
            "largura_m": tw * metros_por_quadrado, "altura_m": th * metros_por_quadrado,
            "centro": QPointF(x0 + tw * k / 2, y0 + th * k / 2)}
