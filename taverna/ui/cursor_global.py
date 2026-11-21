"""
🧤 Luvinha no programa INTEIRO (v0.51, pedido do Manel): antes ela só valia na mesa; em botões, listas,
menus, janelinhas e na tela inicial voltava a setinha/mãozinha do Windows.

Um filtro de eventos no app troca, em QUALQUER janela do Taverna, os cursores "comuns" (seta, mãozinha de
link, mão aberta/fechada de arrastar, "proibido") pela luvinha na cor do jogador. Ficam os cursores que
ajudam a usar: o de texto (onde se digita), os de redimensionar e a cruz das ferramentas de construção.
Fora do programa, o Windows continua com o dele.
"""

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication, QWidget

TROCAR = {Qt.CursorShape.ArrowCursor, Qt.CursorShape.PointingHandCursor, Qt.CursorShape.OpenHandCursor,
          Qt.CursorShape.ClosedHandCursor, Qt.CursorShape.ForbiddenCursor, Qt.CursorShape.WhatsThisCursor,
          Qt.CursorShape.DragMoveCursor, Qt.CursorShape.DragCopyCursor, Qt.CursorShape.DragLinkCursor}


class _Filtro(QObject):
    def __init__(self):
        super().__init__()
        from ..mesa.luva import COR_MESTRE
        self.cor = QColor(COR_MESTRE)
        self._trocando = False

    def luva(self):
        from ..mesa.luva import cursor_luva
        return cursor_luva(self.cor)

    def eventFilter(self, obj, ev):
        t = ev.type()
        if self._trocando or not isinstance(obj, QWidget):
            return False
        if t == QEvent.Type.CursorChange:
            if obj.testAttribute(Qt.WidgetAttribute.WA_SetCursor) and obj.cursor().shape() in TROCAR:
                self._trocar(obj)
        elif t == QEvent.Type.Show and obj.isWindow():
            # janela nova (diálogo, menu, a tela inicial…): a luva vira o cursor de base dela
            if not obj.testAttribute(Qt.WidgetAttribute.WA_SetCursor) or obj.cursor().shape() in TROCAR:
                self._trocar(obj)
        return False

    def _trocar(self, w):
        self._trocando = True
        try:
            w.setCursor(self.luva())
        finally:
            self._trocando = False

    def recolorir(self, cor):
        self.cor = QColor(cor)
        luva = self.luva()
        self._trocando = True
        try:
            for w in QApplication.allWidgets():
                if w.testAttribute(Qt.WidgetAttribute.WA_SetCursor) and \
                        w.cursor().shape() == Qt.CursorShape.BitmapCursor and w.cursor().pixmap().width() == 32:
                    w.setCursor(luva)
                elif w.isWindow() and not w.testAttribute(Qt.WidgetAttribute.WA_SetCursor):
                    w.setCursor(luva)
        finally:
            self._trocando = False


_FILTRO = None


def instalar(app=None):
    global _FILTRO
    app = app or QApplication.instance()
    if _FILTRO is None and app is not None:
        _FILTRO = _Filtro()
        app.installEventFilter(_FILTRO)
        for w in app.topLevelWidgets():
            if w.isVisible():
                _FILTRO._trocar(w)
    return _FILTRO


def atualizar_tema():
    """(v0.64.1) O tema mudou: o ponteiro de todas as janelas vira o do tema novo (mesma cor)."""
    if _FILTRO is not None:
        _FILTRO.recolorir(_FILTRO.cor)


def definir_cor(cor):
    """A cor da luvinha no programa todo (a do token do jogador; o mestre: dourado)."""
    if _FILTRO is not None:
        _FILTRO.recolorir(cor)
