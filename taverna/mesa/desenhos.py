"""
Lápis: rabiscos por cima do mapa (mestre e jogadores).

Cada traço: {"id", "pts": [[x,y],...], "cor", "esp", "autor", "temp": bool, "ate": float|None}
- temp=True: some sozinho depois de alguns segundos (tipo "apontar" algo)
- temp=False: fica até alguém limpar
Quem guarda a lista "de verdade" é a cena do mestre; os players recebem pelo estado.
"""

import time
import uuid

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsItem

from ..config import LIMITE_CENA

SEGUNDOS_TEMPORARIO = 10
CORES_LAPIS = ["#ffd166", "#ef476f", "#06d6a0", "#4cc9f0", "#f8f8f2", "#b388ff", "#ff9f1c", "#111111"]


def traco_novo(pts, cor="#ffd166", esp=3.0, autor="", temp=True) -> dict:
    return {"id": uuid.uuid4().hex[:12], "pts": [[round(x, 1), round(y, 1)] for x, y in pts],
            "cor": cor, "esp": float(esp), "autor": autor, "temp": bool(temp)}


def caminho_do_traco(pts) -> QPainterPath:
    p = QPainterPath()
    if not pts:
        return p
    p.moveTo(QPointF(*pts[0]))
    if len(pts) == 1:
        p.lineTo(QPointF(pts[0][0] + 0.1, pts[0][1]))
    for x, y in pts[1:]:
        p.lineTo(QPointF(x, y))
    return p


class DesenhosItem(QGraphicsItem):
    """Desenha todos os traços (fica por cima de tudo, até da névoa)."""

    def __init__(self):
        super().__init__()
        self.tracos: list[dict] = []
        self.atual: dict | None = None      # traço sendo feito agora (ainda não confirmado)
        self.pendentes: dict[str, dict] = {}   # player: meus traços esperando o mestre devolver
        self.setZValue(950_000)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    def boundingRect(self):
        L = LIMITE_CENA
        from .camera3d import limitar
        return limitar(self, QRectF(-L, -L, 2 * L, 2 * L))   # (v0.70) câmera inclinada: só o chão visível

    def definir(self, tracos: list[dict]):
        self.tracos = list(tracos or [])
        ids = {t["id"] for t in self.tracos}
        agora = time.monotonic()
        self.pendentes = {k: v for k, v in self.pendentes.items()
                          if k not in ids and v.get("_desde", agora) > agora - 4}
        self.update()

    def paint(self, painter: QPainter, option, widget=None):
        lista = list(self.tracos) + list(self.pendentes.values()) + ([self.atual] if self.atual else [])
        if not lista:
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for t in lista:
            pts = t.get("pts") or []
            if not pts:
                continue
            caminho = caminho_do_traco(pts)
            sombra = QPen(QColor(0, 0, 0, 120), float(t.get("esp", 3)) + 3, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            sombra.setCosmetic(True)
            painter.setPen(sombra)
            painter.drawPath(caminho)
            caneta = QPen(QColor(t.get("cor", "#ffd166")), float(t.get("esp", 3)), Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            caneta.setCosmetic(True)
            painter.setPen(caneta)
            painter.drawPath(caminho)
