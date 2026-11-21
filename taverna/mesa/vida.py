"""
Coisas que deixam a mesa "viva":

- Suavizador: em vez de teletransportar um token pra posição nova que chegou pela rede,
  ele desliza até lá (a rede manda ~16 posições por segundo; o suavizador preenche o meio).
- Cursores: a setinha de cada pessoa na mesa, com o nome, vista por todo mundo.
"""

import time
import zlib

from PyQt6.QtCore import QObject, QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF
from PyQt6.QtWidgets import QGraphicsItem


class Suavizador(QObject):
    """Faz itens deslizarem até a posição-alvo (60 quadros por segundo)."""

    def __init__(self, cena, ao_mover=None):
        super().__init__(cena)
        self.cena = cena
        self.alvos: dict = {}            # item -> QPointF (posição no pai)
        self.ao_mover = ao_mover         # chamado depois de cada passo (opcional)
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._passo)

    def mover(self, item, alvo: QPointF):
        atual = item.pos()
        if (alvo - atual).manhattanLength() < 0.5:
            self.alvos.pop(item, None)
            return
        # Se for longe demais (ex.: teleporte do mestre), vai direto
        if (alvo - atual).manhattanLength() > 64 * 12:
            self.alvos.pop(item, None)
            self._definir(item, alvo)
            return
        self.alvos[item] = QPointF(alvo)
        if not self.timer.isActive():
            self.timer.start()

    def esquecer(self, item):
        self.alvos.pop(item, None)

    def _definir(self, item, pos):
        bloqueio = getattr(self.cena, "_aplicando", None)
        if bloqueio is not None:
            self.cena._aplicando = True   # não confundir com movimento do próprio player
        try:
            item.setPos(pos)
        finally:
            if bloqueio is not None:
                self.cena._aplicando = bloqueio

    def _passo(self):
        for item, alvo in list(self.alvos.items()):
            try:
                if item.scene() is None:
                    raise RuntimeError
                atual = item.pos()
            except RuntimeError:
                self.alvos.pop(item, None)
                continue
            if self.cena.mouseGrabberItem() is item:
                self.alvos.pop(item, None)   # a pessoa pegou o token: ela manda
                continue
            delta = alvo - atual
            if delta.manhattanLength() < 0.6:
                self._definir(item, alvo)
                self.alvos.pop(item, None)
            else:
                self._definir(item, atual + delta * 0.35)
        if self.ao_mover:
            self.ao_mover()
        if not self.alvos:
            self.timer.stop()


def cor_do_nome(nome: str) -> QColor:
    """Cada nome ganha sempre a mesma cor."""
    paleta = ["#e8b04a", "#5ab0e0", "#e05a7a", "#6ad08a", "#b48cff", "#f08a3a",
              "#4fd1c5", "#f2d24b", "#d06ad0", "#8ab4ff"]
    return QColor(paleta[zlib.crc32(nome.casefold().encode()) % len(paleta)])


class CursorItem(QGraphicsItem):
    """Setinha + nome. Tamanho fixo na tela (não muda com o zoom)."""

    def __init__(self, nome: str):
        super().__init__()
        self.nome = nome
        self.cor = cor_do_nome(nome)
        self.visto = time.monotonic()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setZValue(1_000_000)

    def boundingRect(self) -> QRectF:
        return QRectF(-2, -2, 160, 46)

    def shape(self) -> QPainterPath:
        return QPainterPath()

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        from .luva import PONTA, desenhar_luva   # (v0.48) 🧤 a luvinha, na cor do token de quem mexe
        painter.save()
        painter.translate(-PONTA[0] * 0.75, -PONTA[1] * 0.75)
        desenhar_luva(painter, self.cor, 0.75)
        painter.restore()
        fonte = QFont()
        fonte.setPixelSize(11)
        fonte.setBold(True)
        painter.setFont(fonte)
        larg = painter.fontMetrics().horizontalAdvance(self.nome) + 12
        placa = QRectF(16, 20, larg, 18)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.cor)
        painter.drawRoundedRect(placa, 4, 4)
        painter.setPen(QColor(15, 12, 10))
        painter.drawText(placa, Qt.AlignmentFlag.AlignCenter, self.nome)


class Cursores(QObject):
    """Guarda os cursores dos outros na cena. Some quem ficar parado/sem sinal por 8 s."""

    SUMIR_DEPOIS = 8.0

    def __init__(self, cena):
        super().__init__(cena)
        self.cena = cena
        self.itens: dict[str, CursorItem] = {}
        self.visiveis = True
        self.suave = Suavizador(cena)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._limpar_velhos)
        self.timer.start()

    def atualizar(self, nome: str, x, y):
        if x is None or y is None:
            self.remover(nome)
            return
        item = self.itens.get(nome)
        try:
            if item is not None:
                item.scene()  # o item ainda existe? (a cena pode ter sido limpa)
        except RuntimeError:
            self.itens.pop(nome, None)
            item = None
        if item is None:
            item = CursorItem(nome)
            item._cor_t = 0.0
            item.setPos(x, y)
            item.setVisible(self.visiveis)
            self.cena.addItem(item)
            self.itens[nome] = item
        else:
            self.suave.mover(item, QPointF(x, y))
        item.visto = time.monotonic()
        if item.visto - getattr(item, "_cor_t", 0.0) > 2.0:   # a cor segue a do token (confere a cada 2 s)
            item._cor_t = item.visto
            cor = self._cor_de(nome)
            if cor.name() != item.cor.name():
                item.cor = cor
                item.update()

    def _cor_de(self, nome: str) -> QColor:
        """(v0.48) Cor da luvinha: a do token de quem mexe (o mestre: dourado; sem token: a cor do nome)."""
        from .luva import COR_MESTRE
        if nome.strip().casefold() == "mestre":
            return QColor(COR_MESTRE)
        try:
            from ..rede.protocolo import mesmo_nome
            from .token import TokenItem
            itens = self.cena.itens.values() if isinstance(getattr(self.cena, "itens", None), dict) \
                else self.cena.items()
            for it in itens:
                if isinstance(it, TokenItem) and it.dono and mesmo_nome(it.dono, nome):
                    return QColor(it.cor)
        except (RuntimeError, AttributeError, ImportError):
            pass
        return cor_do_nome(nome)

    def remover(self, nome: str):
        item = self.itens.pop(nome, None)
        if item is not None:
            self.suave.esquecer(item)
            try:
                if item.scene() is not None:
                    self.cena.removeItem(item)
            except RuntimeError:
                pass

    def limpar(self):
        for nome in list(self.itens):
            self.remover(nome)

    def definir_visiveis(self, visiveis: bool):
        self.visiveis = visiveis
        for item in self.itens.values():
            item.setVisible(visiveis)

    def _limpar_velhos(self):
        agora = time.monotonic()
        for nome, item in list(self.itens.items()):
            if agora - item.visto > self.SUMIR_DEPOIS:
                self.remover(nome)


class Limitador:
    """Deixa passar no máximo uma chamada a cada `intervalo` segundos (e a última sempre passa)."""

    def __init__(self, intervalo: float, funcao):
        self.intervalo = intervalo
        self.funcao = funcao
        self.ultimo = 0.0
        self.pendente = None
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._soltar)

    def __call__(self, *args):
        agora = time.monotonic()
        if agora - self.ultimo >= self.intervalo:
            self.ultimo = agora
            self.pendente = None
            self.funcao(*args)
        else:
            self.pendente = args
            if not self.timer.isActive():
                self.timer.start(int(self.intervalo * 1000))

    def _soltar(self):
        if self.pendente is not None:
            args, self.pendente = self.pendente, None
            self.ultimo = time.monotonic()
            self.funcao(*args)
