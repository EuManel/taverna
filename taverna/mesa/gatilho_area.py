"""
Área de armadilha no chão (placa de pressão, alçapão, runa...).
Só o mestre vê. Nunca vai pros jogadores (o protocolo não manda esse tipo de item).
"""

import uuid

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPen
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsObject

from ..config import CELULA


class AreaGatilhoItem(QGraphicsObject):
    def __init__(self, w: float = 2, h: float = 2, gatilho: dict | None = None):
        super().__init__()
        from ..jogo.gatilhos import gatilho_novo
        self.uid = uuid.uuid4().hex
        self.w, self.h = float(w), float(h)
        self.gatilho = gatilho or gatilho_novo("area")
        self.travado = False
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable
                      | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
                      | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setZValue(50)

    @property
    def nome(self):
        return self.gatilho.get("nome", "Área")

    def retangulo_cena(self) -> QRectF:
        return self.mapRectToScene(QRectF(0, 0, self.w * CELULA, self.h * CELULA))

    def contem(self, ponto: QPointF) -> bool:
        return self.retangulo_cena().contains(ponto)

    def definir_tamanho(self, w, h):
        self.prepareGeometryChange()
        self.w, self.h = max(0.5, float(w)), max(0.5, float(h))
        self.update()
        self._mudou()

    def _mudou(self):
        cena = self.scene()
        if cena is not None and hasattr(cena, "marcar_modificada"):
            cena.marcar_modificada()

    def boundingRect(self):
        return QRectF(-2, -2, self.w * CELULA + 4, self.h * CELULA + 4)

    def paint(self, painter, option, widget=None):
        from ..jogo.gatilhos import pode_disparar
        r = QRectF(0, 0, self.w * CELULA, self.h * CELULA)
        armada = pode_disparar(self.gatilho)
        cor = QColor(220, 60, 60) if armada else QColor(140, 130, 120)
        fundo = QColor(cor)
        fundo.setAlpha(45 if armada else 25)
        caneta = QPen(cor, 2 if not self.isSelected() else 3, Qt.PenStyle.DashLine)
        caneta.setCosmetic(True)
        painter.setPen(caneta)
        painter.setBrush(fundo)
        painter.drawRect(r)
        fonte = QFont()
        fonte.setPixelSize(12)
        fonte.setBold(True)
        painter.setFont(fonte)
        painter.setPen(QColor(255, 225, 200))
        situacao = "" if armada else (" (já disparou)" if self.gatilho.get("disparado") else " (desarmada)")
        texto = ("⚡ " if armada else "◌ ") + self.nome + situacao
        painter.drawText(r.adjusted(4, 4, -4, -4), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
                         | Qt.TextFlag.TextWordWrap, texto)

    def mouseDoubleClickEvent(self, event):
        cena = self.scene()
        if cena is not None and hasattr(cena, "editar_gatilho_pedido"):
            cena.editar_gatilho_pedido.emit(self)
        event.accept()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        cena = self.scene()
        if cena is not None and getattr(cena, "snap_ativo", False):
            p = self.pos()
            self.setPos(round(p.x() / (CELULA / 2)) * (CELULA / 2), round(p.y() / (CELULA / 2)) * (CELULA / 2))

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._mudou()
        return super().itemChange(change, value)

    def aplicar_trava(self, travado):
        self.travado = travado
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not travado)

    # ------------------------------------------------------------ salvar
    def para_dict(self) -> dict:
        p = self.pos()
        return {"classe": "gatilho", "id": self.uid, "x": p.x(), "y": p.y(), "z": self.zValue(),
                "w": self.w, "h": self.h, "gatilho": self.gatilho, "visivel": self.isVisible()}

    @classmethod
    def de_dict(cls, d: dict) -> "AreaGatilhoItem":
        item = cls(d.get("w", 2), d.get("h", 2), d.get("gatilho"))
        item.uid = d.get("id") or item.uid
        item.setPos(d["x"], d["y"])
        item.setZValue(d.get("z", 50))
        item.setVisible(d.get("visivel", True))
        return item
