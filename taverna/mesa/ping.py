"""
Ping: um sinal pulsando no mapa ("é aqui!") que todo mundo vê por uns segundos.
"""

from PyQt6.QtCore import QRectF, Qt, QVariantAnimation
from PyQt6.QtGui import QColor, QFont, QPen
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsObject


class PingItem(QGraphicsObject):
    DURACAO = 2600

    def __init__(self, x, y, nome, cor):
        super().__init__()
        self.nome = nome
        self.cor = QColor(cor)
        self._t = 0.0
        self.setPos(x, y)
        self.setZValue(1e6)
        # mesmo tamanho na tela em qualquer zoom
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(self.DURACAO)
        self._anim.valueChanged.connect(self._passo)
        self._anim.finished.connect(self._acabou)
        self._anim.start()

    def _passo(self, t):
        self._t = float(t)
        self.update()

    def _acabou(self):
        cena = self.scene()
        if cena is not None:
            cena.removeItem(self)
        self.deleteLater()

    def boundingRect(self):
        return QRectF(-70, -70, 140, 110)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(painter.RenderHint.Antialiasing)
        t = self._t
        sumir = 1.0 if t < 0.7 else max(0.0, 1 - (t - 0.7) / 0.3)
        # três ondas saindo do ponto
        for k in range(3):
            fase = (t * 2.2 - k * 0.25) % 1.0
            cor = QColor(self.cor)
            cor.setAlphaF(max(0.0, (1 - fase)) * sumir)
            painter.setPen(QPen(cor, 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r = 6 + fase * 44
            painter.drawEllipse(QRectF(-r, -r, 2 * r, 2 * r))
        centro = QColor(self.cor)
        centro.setAlphaF(sumir)
        painter.setPen(QPen(QColor(15, 12, 10, int(255 * sumir)), 2))
        painter.setBrush(centro)
        painter.drawEllipse(QRectF(-6, -6, 12, 12))
        if self.nome:
            fonte = QFont()
            fonte.setPixelSize(12)
            fonte.setBold(True)
            painter.setFont(fonte)
            larg = painter.fontMetrics().horizontalAdvance(self.nome) + 12
            placa = QRectF(-larg / 2, 14, larg, 18)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(18, 14, 11, int(215 * sumir)))
            painter.drawRoundedRect(placa, 5, 5)
            texto = QColor(self.cor)
            texto.setAlphaF(sumir)
            painter.setPen(texto)
            painter.drawText(placa, Qt.AlignmentFlag.AlignCenter, self.nome)


def pingar(cena, x, y, nome, cor):
    cena.addItem(PingItem(x, y, nome, cor))
