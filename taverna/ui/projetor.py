"""
Projetor (Etapa 11): o mestre mostra uma imagem na tela dos jogadores.

- Mestre: galeria de imagens da aventura (fica salva no .taverna), escolhe pra quem
  (todos ou alguns), projeta e recolhe. Dá pra projetar o retrato de um token ou a imagem
  de um documento direto pelo botão direito.
- Jogador: a imagem aparece por cima da mesa (com legenda), dá pra ampliar com zoom e
  fechar. Tudo que ele recebeu fica em "📽 Imagens" pra rever depois.
"""

import hashlib

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, QPropertyAnimation, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication, QIcon, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import (QCheckBox, QDialog, QFileDialog, QFrame, QGraphicsOpacityEffect,
                             QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QHBoxLayout, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget)

from .sobreposicoes import ESTILO, _Acompanhar

LADO_MAXIMO = 1920   # imagens maiores são reduzidas antes de mandar (fica leve na rede)


def preparar_imagem(dados: bytes) -> bytes | None:
    """Reduz pra no máx. 1920 px e regrava (JPEG, ou PNG se tiver transparência)."""
    img = QImage.fromData(dados)
    if img.isNull():
        return None
    if max(img.width(), img.height()) > LADO_MAXIMO:
        img = img.scaled(LADO_MAXIMO, LADO_MAXIMO, Qt.AspectRatioMode.KeepAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)
    elif len(dados) < 1_500_000:
        return dados   # já está leve: manda como veio
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    if img.hasAlphaChannel():
        img.save(buf, "PNG")
    else:
        img.save(buf, "JPG", 88)
    return bytes(buf.data())


def id_imagem(dados: bytes) -> str:
    return hashlib.sha1(dados).hexdigest()[:16]


def miniatura(dados: bytes, lado: int = 96) -> QIcon:
    pm = QPixmap()
    pm.loadFromData(dados)
    if pm.isNull():
        return QIcon()
    return QIcon(pm.scaled(lado, lado, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation))


# ====================================================================== ver com zoom
class VisorImagem(QGraphicsView):
    def __init__(self, dados: bytes, parent=None):
        super().__init__(parent)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setStyleSheet("background: #0d0b09; border: none;")
        cena = QGraphicsScene(self)
        pm = QPixmap()
        pm.loadFromData(dados)
        self.item = QGraphicsPixmapItem(pm)
        self.item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        cena.addItem(self.item)
        self.setScene(cena)

    def enquadrar(self):
        self.fitInView(self.item, Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, ev):
        f = 1.15 if ev.angleDelta().y() > 0 else 1 / 1.15
        self.scale(f, f)

    def showEvent(self, ev):
        super().showEvent(ev)
        self.enquadrar()


class JanelaImagem(QDialog):
    def __init__(self, dados: bytes, titulo: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo or "Imagem")
        self.resize(1000, 720)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.visor = VisorImagem(dados, self)
        lay.addWidget(self.visor, 1)
        rodape = QHBoxLayout()
        rodape.setContentsMargins(8, 4, 8, 6)
        rodape.addWidget(QLabel("Roda do mouse = zoom · arraste = mover"))
        rodape.addStretch(1)
        b = QPushButton("Enquadrar")
        b.clicked.connect(self.visor.enquadrar)
        rodape.addWidget(b)
        b = QPushButton("Fechar")
        b.clicked.connect(self.close)
        rodape.addWidget(b)
        lay.addLayout(rodape)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema


# ====================================================================== jogador: aparece na mesa
class ProjecaoOverlay(QFrame):
    """A imagem projetada por cima da mesa do jogador."""

    def __init__(self, mesa):
        super().__init__(mesa)
        self.mesa = mesa
        self.dados = b""
        self.titulo_txt = ""
        self.setObjectName("sobreposicao")
        self.setStyleSheet(ESTILO + "QFrame#sobreposicao { border-width: 2px; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 10)
        lay.setSpacing(6)
        topo = QHBoxLayout()
        self.titulo = QLabel()
        self.titulo.setStyleSheet("font-weight: bold; font-size: 13px; color: palette(highlight);")
        topo.addWidget(self.titulo, 1)
        b = QPushButton("🔍 Ampliar")
        b.clicked.connect(self.ampliar)
        topo.addWidget(b)
        b = QPushButton("✕")
        b.setToolTip("Fechar (fica guardada em 📽 Imagens)")
        b.setFixedWidth(30)
        b.clicked.connect(self.hide)
        topo.addWidget(b)
        lay.addLayout(topo)
        self.imagem = QLabel()
        self.imagem.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imagem.setCursor(Qt.CursorShape.PointingHandCursor)
        self.imagem.mouseDoubleClickEvent = lambda _e: self.ampliar()
        lay.addWidget(self.imagem, 1)
        self._efeito = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._efeito)
        self._anim = QPropertyAnimation(self._efeito, b"opacity", self)
        self._anim.setDuration(350)
        _Acompanhar(mesa, self.posicionar)
        self.hide()
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def mostrar(self, dados: bytes, titulo: str = ""):
        self.dados, self.titulo_txt = dados, titulo
        self.titulo.setText(titulo or "O mestre mostrou uma imagem")
        self.posicionar()
        self.show()
        self.raise_()
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()

    def posicionar(self):
        if not self.dados:
            return
        pm = QPixmap()
        pm.loadFromData(self.dados)
        if pm.isNull():
            return
        max_w = int(self.mesa.width() * 0.72)
        max_h = int(self.mesa.height() * 0.72) - 50
        pm = pm.scaled(max(50, max_w), max(50, max_h), Qt.AspectRatioMode.KeepAspectRatio,
                       Qt.TransformationMode.SmoothTransformation)
        self.imagem.setPixmap(pm)
        w = max(pm.width() + 20, 320)
        h = pm.height() + 60
        self.resize(w, h)
        self.move((self.mesa.width() - w) // 2, max(50, (self.mesa.height() - h) // 2))

    def ampliar(self):
        if self.dados:
            JanelaImagem(self.dados, self.titulo_txt, self.window()).exec()


class GaleriaRecebidas(QDialog):
    """Jogador: tudo que o mestre já mostrou nesta sessão."""

    def __init__(self, imagens: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("📽 Imagens que o mestre mostrou")
        self.resize(640, 460)
        self.imagens = imagens
        lay = QVBoxLayout(self)
        self.lista = QListWidget()
        self.lista.setViewMode(QListWidget.ViewMode.IconMode)
        self.lista.setIconSize(QSize(140, 140))
        self.lista.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.lista.setSpacing(8)
        self.lista.setWordWrap(True)
        for i, im in enumerate(reversed(imagens)):
            it = QListWidgetItem(miniatura(im["dados"], 140), im.get("titulo") or "Sem título")
            it.setData(Qt.ItemDataRole.UserRole, len(imagens) - 1 - i)
            self.lista.addItem(it)
        self.lista.itemDoubleClicked.connect(self._abrir)
        lay.addWidget(self.lista, 1)
        dica = QLabel("Nada ainda. Quando o mestre projetar uma imagem, ela fica guardada aqui."
                      if not imagens else "Duplo clique pra ampliar.")
        lay.addWidget(dica)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def _abrir(self, it):
        im = self.imagens[it.data(Qt.ItemDataRole.UserRole)]
        JanelaImagem(im["dados"], im.get("titulo", ""), self).exec()


# ====================================================================== mestre: painel
class PainelProjetor(QWidget):
    projetar = pyqtSignal(bytes, str, object)   # dados, legenda, para (None = todos, ou lista de nomes)
    recolher = pyqtSignal()
    mudou = pyqtSignal()                        # a galeria mudou (marcar a aventura como modificada)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.galeria: list[dict] = []   # [{"titulo", "dados"}]
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 10)
        lay.setSpacing(6)
        linha = QHBoxLayout()
        for texto, dica, funcao in (("➕ Imagem…", "Escolher imagens do computador", self._importar),
                                    ("📋 Colar", "Colar a imagem copiada (Ctrl+C em qualquer lugar)", self.colar),
                                    ("🗑", "Tirar da galeria", self._remover)):
            b = QPushButton(texto)
            b.setToolTip(dica)
            b.clicked.connect(funcao)
            linha.addWidget(b)
        linha.addStretch(1)
        lay.addLayout(linha)
        self.lista = QListWidget()
        self.lista.setViewMode(QListWidget.ViewMode.IconMode)
        self.lista.setIconSize(QSize(92, 92))
        self.lista.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.lista.setSpacing(6)
        self.lista.setWordWrap(True)
        self.lista.setMinimumHeight(140)
        self.lista.currentRowChanged.connect(self._selecionou)
        self.lista.itemDoubleClicked.connect(lambda _it: self._projetar())
        lay.addWidget(self.lista, 1)
        linha = QHBoxLayout()
        linha.addWidget(QLabel("Legenda"))
        self.legenda = QLineEdit()
        self.legenda.setPlaceholderText("ex.: Retrato da Duquesa Velmora (opcional)")
        self.legenda.editingFinished.connect(self._legenda_editada)
        linha.addWidget(self.legenda, 1)
        lay.addLayout(linha)
        lay.addWidget(QLabel("Mostrar para:"))
        self.ck_todos = QCheckBox("Todos os jogadores")
        self.ck_todos.setChecked(True)
        self.ck_todos.toggled.connect(lambda v: self.lista_jog.setEnabled(not v))
        lay.addWidget(self.ck_todos)
        self.lista_jog = QListWidget()
        self.lista_jog.setMaximumHeight(90)
        self.lista_jog.setEnabled(False)
        lay.addWidget(self.lista_jog)
        linha = QHBoxLayout()
        self.btn_projetar = QPushButton("📽 Projetar")
        self.btn_projetar.setObjectName("primario")
        self.btn_projetar.clicked.connect(self._projetar)
        self.btn_recolher = QPushButton("⏹ Recolher")
        self.btn_recolher.setToolTip("Tira a imagem da tela de todo mundo")
        self.btn_recolher.clicked.connect(self.recolher.emit)
        self.btn_ver = QPushButton("👁")
        self.btn_ver.setToolTip("Ver em tamanho grande (só você)")
        self.btn_ver.clicked.connect(self._ver)
        linha.addWidget(self.btn_projetar, 1)
        linha.addWidget(self.btn_recolher)
        linha.addWidget(self.btn_ver)
        lay.addLayout(linha)
        self.status = QLabel("Nada projetado.")
        self.status.setWordWrap(True)
        lay.addWidget(self.status)
        dica = QLabel("Dica: duplo clique numa imagem = projetar. Também dá pra projetar o retrato de um "
                      "token ou a imagem de um documento pelo botão direito na mesa. As imagens ficam "
                      "salvas na aventura — prepare antes da sessão.")
        dica.setWordWrap(True)
        dica.setStyleSheet("font-size: 11px;")
        lay.addWidget(dica)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    # ------------------------------------------------------------ galeria
    def definir_galeria(self, lista: list[dict]):
        self.galeria = [dict(x) for x in lista if x.get("dados")]
        self._recarregar()

    def _recarregar(self, selecionar: int | None = None):
        self.lista.blockSignals(True)
        self.lista.clear()
        for im in self.galeria:
            self.lista.addItem(QListWidgetItem(miniatura(im["dados"], 92), im.get("titulo") or "Sem título"))
        self.lista.blockSignals(False)
        if self.galeria:
            i = selecionar if selecionar is not None else max(0, self.lista.currentRow())
            self.lista.setCurrentRow(max(0, min(i, len(self.galeria) - 1)))
        else:
            self.legenda.clear()

    def adicionar(self, dados: bytes, titulo: str = "") -> int | None:
        dados = preparar_imagem(dados)
        if not dados:
            return None
        for i, im in enumerate(self.galeria):   # mesma imagem: não duplica
            if id_imagem(im["dados"]) == id_imagem(dados):
                self._recarregar(i)
                return i
        self.galeria.append({"titulo": titulo, "dados": dados})
        self._recarregar(len(self.galeria) - 1)
        self.mudou.emit()
        return len(self.galeria) - 1

    def _importar(self):
        caminhos, _ = QFileDialog.getOpenFileNames(self, "Imagens pro projetor", "",
                                                   "Imagens (*.png *.jpg *.jpeg *.webp *.bmp *.gif)")
        for c in caminhos:
            try:
                with open(c, "rb") as f:
                    import os
                    nome = os.path.splitext(os.path.basename(c))[0].replace("_", " ")
                    self.adicionar(f.read(), nome)
            except OSError:
                pass

    def colar(self):
        img = QGuiApplication.clipboard().image()
        if img.isNull():
            self.status.setText("A área de transferência não tem imagem. Copie uma imagem (Ctrl+C) e tente de novo.")
            return
        buf = QBuffer()
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        img.save(buf, "PNG")
        self.adicionar(bytes(buf.data()), "Imagem colada")

    def _remover(self):
        i = self.lista.currentRow()
        if 0 <= i < len(self.galeria):
            del self.galeria[i]
            self._recarregar(i)
            self.mudou.emit()

    def _selecionou(self, i):
        self.legenda.setText(self.galeria[i].get("titulo", "") if 0 <= i < len(self.galeria) else "")

    def _legenda_editada(self):
        i = self.lista.currentRow()
        if 0 <= i < len(self.galeria) and self.galeria[i].get("titulo", "") != self.legenda.text().strip():
            self.galeria[i]["titulo"] = self.legenda.text().strip()
            self.lista.item(i).setText(self.galeria[i]["titulo"] or "Sem título")
            self.mudou.emit()

    def _ver(self):
        i = self.lista.currentRow()
        if 0 <= i < len(self.galeria):
            JanelaImagem(self.galeria[i]["dados"], self.galeria[i].get("titulo", ""), self).exec()

    # ------------------------------------------------------------ jogadores
    def definir_jogadores(self, nomes: list[str]):
        marcados = {self.lista_jog.item(k).text() for k in range(self.lista_jog.count())
                    if self.lista_jog.item(k).checkState() == Qt.CheckState.Checked}
        self.lista_jog.clear()
        for n in nomes:
            it = QListWidgetItem(n)
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(Qt.CheckState.Checked if n in marcados else Qt.CheckState.Unchecked)
            self.lista_jog.addItem(it)

    def _para(self):
        if self.ck_todos.isChecked():
            return None
        return [self.lista_jog.item(k).text() for k in range(self.lista_jog.count())
                if self.lista_jog.item(k).checkState() == Qt.CheckState.Checked]

    def _projetar(self):
        i = self.lista.currentRow()
        if not (0 <= i < len(self.galeria)):
            self.status.setText("Escolha (ou adicione) uma imagem primeiro.")
            return
        self._legenda_editada()
        para = self._para()
        if para == []:
            self.status.setText("Marque pelo menos um jogador (ou 'Todos').")
            return
        im = self.galeria[i]
        self.projetar.emit(im["dados"], im.get("titulo", ""), para)

    def mostrar_status(self, titulo: str, para):
        quem = "todos" if para is None else ", ".join(para)
        self.status.setText(f"Projetando: {titulo or 'imagem'} → {quem}")
