"""
O grid infinito da mesa.

Ele desenha só o pedaço que está na tela (exposedRect), então não importa
o tamanho da mesa. A cada 5 metros a linha fica mais forte, pra facilitar
a contagem. Quando a câmera está muito afastada, as linhas finas somem.
"""

import math

from PyQt6.QtCore import QLineF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsItem

from ..config import CELULA, COR_GRID, LIMITE_CENA


class GridItem(QGraphicsItem):
    def __init__(self):
        super().__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemUsesExtendedStyleOption, True)
        # O grid nunca recebe clique: o clique "atravessa" pro que está embaixo
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.cor = QColor(COR_GRID)
        self.setOpacity(0.35)

    def boundingRect(self) -> QRectF:
        L = LIMITE_CENA
        from .camera3d import limitar
        return limitar(self, QRectF(-L, -L, 2 * L, 2 * L))   # (v0.70) câmera inclinada: só o chão visível

    def shape(self) -> QPainterPath:
        # Forma vazia = nada clicável
        return QPainterPath()

    def paint(self, painter, option, widget=None):
        area = option.exposedRect
        from .camera3d import escala_de
        escala = escala_de(painter.worldTransform())   # (v0.70) girada: m11 sozinho dava 0 ou negativo
        tam_na_tela = CELULA * escala

        desenhar_finas = tam_na_tela >= 7
        if tam_na_tela * 5 < 7:
            return  # longe demais, nem as linhas de 5 m fazem sentido

        caneta_fina = QPen(self.cor, 1)
        caneta_fina.setCosmetic(True)  # 1 pixel de tela, qualquer zoom
        cor_forte = QColor(self.cor)
        cor_forte.setAlphaF(1.0)
        caneta_forte = QPen(cor_forte, 2)
        caneta_forte.setCosmetic(True)

        esq = math.floor(area.left() / CELULA)
        dir_ = math.ceil(area.right() / CELULA)
        topo = math.floor(area.top() / CELULA)
        base = math.ceil(area.bottom() / CELULA)

        finas, fortes = [], []
        for i in range(esq, dir_ + 1):
            x = i * CELULA
            linha = QLineF(x, area.top(), x, area.bottom())
            (fortes if i % 5 == 0 else finas).append(linha)
        for j in range(topo, base + 1):
            y = j * CELULA
            linha = QLineF(area.left(), y, area.right(), y)
            (fortes if j % 5 == 0 else finas).append(linha)

        if desenhar_finas and finas:
            painter.setPen(caneta_fina)
            painter.drawLines(finas)
        if fortes:
            painter.setPen(caneta_forte)
            painter.setOpacity(painter.opacity() * 0.6)
            painter.drawLines(fortes)
