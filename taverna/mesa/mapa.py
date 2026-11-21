"""
Imagem de mapa redimensionável.

O grid é fixo (1 quadrado = 1 m). O mestre arrasta as alças dos cantos
até a imagem ocupar o tamanho que ele quer, vendo "9,0 × 9,0 m" na hora.

Atalhos durante o redimensionamento:
  - Shift: alterna a trava de proporção (se estava travada, solta; e vice-versa)
  - Ctrl:  arredonda para metros inteiros
"""

import base64
import hashlib
import uuid

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsObject

from ..config import (CELULA, COR_DESTAQUE, MAPA_LARGURA_PADRAO,
                      MAPA_MIN_METROS, fmt_m)

# Cantos: (lado direito?, lado de baixo?)
CANTOS = {
    "sup_esq": (False, False),
    "sup_dir": (True, False),
    "inf_esq": (False, True),
    "inf_dir": (True, True),
}

ALCA_TELA = 12      # tamanho da alça em pixels de TELA (não muda com o zoom)
ROTULO_TELA = 30    # espaço reservado acima do mapa para o rótulo de tamanho


class MapaItem(QGraphicsObject):
    tamanho_mudou = pyqtSignal()

    def __init__(self, dados: bytes, largura_m: float | None = None,
                 altura_m: float | None = None):
        super().__init__()
        self.uid = uuid.uuid4().hex  # identidade do item na rede
        self.nome = "Mapa"
        self.dados = dados  # bytes originais da imagem (vão pro arquivo .taverna)
        self.pixmap = QPixmap()
        self.pixmap.loadFromData(dados)
        if self.pixmap.isNull():
            raise ValueError("Não consegui ler essa imagem.")

        proporcao = self.pixmap.width() / max(1, self.pixmap.height())
        if largura_m is None:
            largura_m = MAPA_LARGURA_PADRAO
        if altura_m is None:
            altura_m = largura_m / proporcao
        self.w = largura_m * CELULA
        self.h = altura_m * CELULA

        self.manter_proporcao = True
        self.travado = False
        self._redim = None  # estado do redimensionamento em andamento

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

    @property
    def hash_imagem(self) -> str:
        if not hasattr(self, "_hash"):
            self._hash = hashlib.sha1(self.dados).hexdigest()
        return self._hash

    # ------------------------------------------------------------------ medidas
    @property
    def largura_m(self) -> float:
        return self.w / CELULA

    @property
    def altura_m(self) -> float:
        return self.h / CELULA

    def _escala(self) -> float:
        cena = self.scene()
        return getattr(cena, "escala_visao", 1.0) if cena else 1.0

    def _alca(self) -> float:
        """Tamanho da alça convertido para unidades de cena."""
        return ALCA_TELA / self._escala()

    def escala_mudou(self):
        """Chamado pela cena quando o zoom muda (alças têm tamanho fixo na tela)."""
        self.prepareGeometryChange()

    def boundingRect(self) -> QRectF:
        a = self._alca()
        r = ROTULO_TELA / self._escala()
        from .camera3d import limitar
        return limitar(self, QRectF(-a, -a - r, self.w + 2 * a, self.h + 2 * a + r))   # (v0.70) inclinada

    def shape(self) -> QPainterPath:
        caminho = QPainterPath()
        caminho.addRect(QRectF(0, 0, self.w, self.h))
        if self.isSelected() and not self.travado:
            a = self._alca()
            for canto in CANTOS:
                p = self._ponto_canto(canto)
                caminho.addRect(QRectF(p.x() - a, p.y() - a, 2 * a, 2 * a))
        return caminho

    def _ponto_canto(self, canto: str) -> QPointF:
        direita, baixo = CANTOS[canto]
        return QPointF(self.w if direita else 0, self.h if baixo else 0)

    def _canto_em(self, pos: QPointF):
        if not self.isSelected() or self.travado:
            return None
        a = self._alca()
        for canto in CANTOS:
            p = self._ponto_canto(canto)
            if abs(pos.x() - p.x()) <= a and abs(pos.y() - p.y()) <= a:
                return canto
        return None

    # ------------------------------------------------------------- tamanho
    def definir_tamanho_metros(self, largura_m: float, altura_m: float):
        largura_m = max(MAPA_MIN_METROS, largura_m)
        altura_m = max(MAPA_MIN_METROS, altura_m)
        self.prepareGeometryChange()
        self.w = largura_m * CELULA
        self.h = altura_m * CELULA
        self.update()
        self.tamanho_mudou.emit()
        self._avisar_modificacao()

    def proporcao_original(self) -> float:
        return self.pixmap.width() / max(1, self.pixmap.height())

    def aplicar_trava(self, travado: bool):
        self.travado = travado
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not travado)
        self.prepareGeometryChange()
        self.update()

    # --------------------------------------------------------------- mouse
    def hoverMoveEvent(self, event):
        canto = self._canto_em(event.pos())
        if canto in ("sup_esq", "inf_dir"):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif canto in ("sup_dir", "inf_esq"):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif not self.travado:
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.unsetCursor()
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        canto = self._canto_em(event.pos())
        if event.button() == Qt.MouseButton.LeftButton and canto:
            direita, baixo = CANTOS[canto]
            # O canto oposto fica parado, em coordenadas de cena
            oposto = QPointF(0 if direita else self.w, 0 if baixo else self.h)
            self._redim = {
                "canto": canto,
                "fixo": self.mapToScene(oposto),
                "proporcao": self.w / max(1e-6, self.h),
            }
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._redim:
            super().mouseMoveEvent(event)
            return

        direita, baixo = CANTOS[self._redim["canto"]]
        fixo = self._redim["fixo"]
        p = event.scenePos()
        minimo = MAPA_MIN_METROS * CELULA

        w = (p.x() - fixo.x()) if direita else (fixo.x() - p.x())
        h = (p.y() - fixo.y()) if baixo else (fixo.y() - p.y())
        w, h = max(minimo, w), max(minimo, h)

        mods = event.modifiers()
        if mods & Qt.KeyboardModifier.ControlModifier:
            w = max(minimo, round(w / CELULA) * CELULA)
            h = max(minimo, round(h / CELULA) * CELULA)

        travar = self.manter_proporcao
        if mods & Qt.KeyboardModifier.ShiftModifier:
            travar = not travar
        if travar:
            h = w / self._redim["proporcao"]

        x = fixo.x() if direita else fixo.x() - w
        y = fixo.y() if baixo else fixo.y() - h

        self.prepareGeometryChange()
        self.w, self.h = w, h
        self.setPos(self.mapToParent(self.mapFromScene(QPointF(x, y))))
        self.update()
        self.tamanho_mudou.emit()
        event.accept()

    def mouseReleaseEvent(self, event):
        if self._redim:
            self._redim = None
            self._avisar_modificacao()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._avisar_modificacao()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.prepareGeometryChange()
        return super().itemChange(change, value)

    def _avisar_modificacao(self):
        cena = self.scene()
        if cena is not None and hasattr(cena, "marcar_modificada"):
            cena.marcar_modificada()

    # ------------------------------------------------------------- desenho
    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.drawPixmap(QRectF(0, 0, self.w, self.h), self.pixmap,
                           QRectF(self.pixmap.rect()))

        if not self.isSelected():
            return

        dourado = QColor(COR_DESTAQUE)
        escala = self._escala()

        # Moldura tracejada
        caneta = QPen(dourado, 1.5, Qt.PenStyle.DashLine)
        caneta.setCosmetic(True)
        painter.setPen(caneta)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(QRectF(0, 0, self.w, self.h))

        # Alças (desenhadas em escala de tela)
        if not self.travado:
            for canto in CANTOS:
                p = self._ponto_canto(canto)
                painter.save()
                painter.translate(p)
                painter.scale(1 / escala, 1 / escala)
                painter.setPen(QPen(QColor("#1a1510"), 1.5))
                painter.setBrush(QBrush(dourado))
                m = ALCA_TELA / 2
                painter.drawRect(QRectF(-m, -m, ALCA_TELA, ALCA_TELA))
                painter.restore()

        # Rótulo de tamanho: "20,0 × 14,5 m"
        texto = f"{fmt_m(self.largura_m)} × {fmt_m(self.altura_m)} m"
        if self.travado:
            texto += "  🔒"
        painter.save()
        painter.translate(0, 0)
        painter.scale(1 / escala, 1 / escala)
        fonte = QFont()
        fonte.setPixelSize(13)
        fonte.setBold(True)
        painter.setFont(fonte)
        largura_txt = painter.fontMetrics().horizontalAdvance(texto) + 16
        placa = QRectF(0, -26, largura_txt, 22)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(20, 16, 12, 220))
        painter.drawRoundedRect(placa, 4, 4)
        painter.setPen(dourado)
        painter.drawText(placa, Qt.AlignmentFlag.AlignCenter, texto)
        painter.restore()

    # ---------------------------------------------------------- salvar/abrir
    def para_dict(self) -> dict:
        return {
            "classe": "mapa",
            "id": self.uid,
            "nome": self.nome,
            "visivel": self.isVisible(),
            "x": self.pos().x(),
            "y": self.pos().y(),
            "z": self.zValue(),
            "largura_m": self.largura_m,
            "altura_m": self.altura_m,
            "manter_proporcao": self.manter_proporcao,
            "imagem": base64.b64encode(self.dados).decode("ascii"),
        }

    @classmethod
    def de_dict(cls, d: dict) -> "MapaItem":
        item = cls(base64.b64decode(d["imagem"]), d["largura_m"], d["altura_m"])
        item.setPos(d["x"], d["y"])
        item.setZValue(d.get("z", 0))
        item.manter_proporcao = d.get("manter_proporcao", True)
        item.nome = d.get("nome", "Mapa")
        item.uid = d.get("id") or item.uid
        item.setVisible(d.get("visivel", True))
        return item
