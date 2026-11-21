"""
🖼 Banco de imagens (Etapa 13): uma biblioteca de imagens que vale pra TODAS as aventuras.

Fica em Documentos/Taverna/Banco de imagens, com pastas (Mapas, Tokens, Objetos, Projetor, Outros…).
O mestre importa várias de uma vez (ou arrasta do Windows pra cá), e usa:
- duplo clique / arrastar pra mesa: vira mapa, token ou objeto (depende da pasta)
- botão direito: pôr como mapa / token / objeto, mandar pro projetor, ✂ remover fundo, renomear, mover, apagar
"""

import os
import re
import shutil

from PyQt6.QtCore import QMimeData, QSize, QStandardPaths, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QDrag, QIcon, QImageReader, QPixmap
from PyQt6.QtWidgets import (QComboBox, QFileDialog, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                             QListWidget, QListWidgetItem, QMenu, QMessageBox, QPushButton, QVBoxLayout,
                             QWidget)

EXTENSOES = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")
PASTAS_PADRAO = ["Mapas", "Tokens", "Objetos", "Projetor", "Outros"]
MIME_BANCO = "application/x-taverna-banco"
# o que o duplo clique faz em cada pasta (as pastas que o mestre criar usam "perguntar")
USO_DA_PASTA = {"mapas": "mapa", "tokens": "token", "objetos": "objeto", "projetor": "projetor"}


def pasta_banco() -> str:
    docs = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation) \
        or os.path.expanduser("~")
    pasta = os.path.join(docs, "Taverna", "Banco de imagens")
    for p in PASTAS_PADRAO:
        os.makedirs(os.path.join(pasta, p), exist_ok=True)
    return pasta


def _seguro(nome: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", nome).strip().rstrip(".") or "imagem"


def nome_livre(pasta: str, nome: str, ext: str) -> str:
    base = _seguro(nome)
    caminho = os.path.join(pasta, base + ext)
    k = 2
    while os.path.exists(caminho):
        caminho = os.path.join(pasta, f"{base} ({k}){ext}")
        k += 1
    return caminho


def uso_padrao(pasta_nome: str) -> str:
    return USO_DA_PASTA.get(pasta_nome.strip().casefold(), "perguntar")


class _Grade(QListWidget):
    """A grade de miniaturas — arrastar daqui pra mesa."""

    def __init__(self, painel):
        super().__init__()
        self.painel = painel
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setIconSize(QSize(96, 96))
        self.setGridSize(QSize(116, 132))
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Static)
        self.setWordWrap(True)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def startDrag(self, _acoes):
        it = self.currentItem()
        if it is None:
            return
        caminho = it.data(Qt.ItemDataRole.UserRole)
        mime = QMimeData()
        mime.setData(MIME_BANCO, f"{self.painel.uso_atual()}|{caminho}".encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(it.icon().pixmap(72, 72))
        drag.exec(Qt.DropAction.CopyAction)

    # arrastar arquivos do Windows pra dentro do banco
    def dragEnterEvent(self, ev):
        if ev.mimeData().hasUrls():
            ev.acceptProposedAction()
        else:
            super().dragEnterEvent(ev)

    def dragMoveEvent(self, ev):
        if ev.mimeData().hasUrls():
            ev.acceptProposedAction()
        else:
            super().dragMoveEvent(ev)

    def dropEvent(self, ev):
        if ev.mimeData().hasUrls():
            self.painel.importar([u.toLocalFile() for u in ev.mimeData().urls()])
            ev.acceptProposedAction()
        else:
            super().dropEvent(ev)


class PainelBanco(QWidget):
    usar = pyqtSignal(str, str)   # uso ("mapa"/"token"/"objeto"/"projetor"), caminho

    def __init__(self, parent=None):
        super().__init__(parent)
        self._miniaturas: dict[tuple, QIcon] = {}
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 8)
        lay.setSpacing(6)
        linha = QHBoxLayout()
        self.cb_pasta = QComboBox()
        self.cb_pasta.currentIndexChanged.connect(lambda _i: self.recarregar())
        linha.addWidget(self.cb_pasta, 1)
        b = QPushButton("📁 Nova")
        b.setToolTip("Criar uma pasta nova no banco")
        b.clicked.connect(self._nova_pasta)
        linha.addWidget(b)
        lay.addLayout(linha)
        linha = QHBoxLayout()
        b = QPushButton("➕ Importar…")
        b.setObjectName("primario")
        b.setToolTip("Escolher várias imagens de uma vez (ou arraste do Windows pra cá)")
        b.clicked.connect(self._escolher)
        linha.addWidget(b)
        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Procurar…")
        self.busca.textChanged.connect(lambda _t: self.recarregar())
        linha.addWidget(self.busca, 1)
        lay.addLayout(linha)
        self.grade = _Grade(self)
        self.grade.itemDoubleClicked.connect(lambda it: self._usar(self.uso_atual(), it))
        self.grade.customContextMenuRequested.connect(self._menu)
        lay.addWidget(self.grade, 1)
        self.dica = QLabel()
        self.dica.setWordWrap(True)
        self.dica.setStyleSheet("font-size: 11px;")
        lay.addWidget(self.dica)
        b = QPushButton("📂 Abrir a pasta do banco")
        b.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(self.pasta_atual())))
        lay.addWidget(b)
        self.recarregar_pastas()
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    # ------------------------------------------------------------ pastas
    def recarregar_pastas(self, selecionar: str | None = None):
        raiz = pasta_banco()
        atual = selecionar or self.cb_pasta.currentData()
        nomes = sorted((d for d in os.listdir(raiz) if os.path.isdir(os.path.join(raiz, d))),
                       key=lambda d: (PASTAS_PADRAO.index(d) if d in PASTAS_PADRAO else 99, d.casefold()))
        self.cb_pasta.blockSignals(True)
        self.cb_pasta.clear()
        icones = {"Mapas": "🗺", "Tokens": "⬤", "Objetos": "📦", "Projetor": "📽", "Outros": "🗂"}
        for n in nomes:
            qtd = len([a for a in os.listdir(os.path.join(raiz, n)) if a.lower().endswith(EXTENSOES)])
            from .acabamento import adicionar_item
            adicionar_item(self.cb_pasta, f"{icones.get(n, '📁')} {n}  ({qtd})", n)
        i = self.cb_pasta.findData(atual)
        self.cb_pasta.setCurrentIndex(i if i >= 0 else 0)
        self.cb_pasta.blockSignals(False)
        self.recarregar()

    def pasta_atual(self) -> str:
        return os.path.join(pasta_banco(), self.cb_pasta.currentData() or "Outros")

    def uso_atual(self) -> str:
        return uso_padrao(self.cb_pasta.currentData() or "")

    def _nova_pasta(self):
        nome, ok = QInputDialog.getText(self, "Nova pasta", "Nome da pasta (ex.: Retratos de NPCs, Cidade de Vel):")
        if ok and nome.strip():
            os.makedirs(os.path.join(pasta_banco(), _seguro(nome)), exist_ok=True)
            self.recarregar_pastas(_seguro(nome))

    # ------------------------------------------------------------ imagens
    def _icone(self, caminho) -> QIcon:
        try:
            chave = (caminho, os.path.getmtime(caminho))
        except OSError:
            return QIcon()
        if chave not in self._miniaturas:
            leitor = QImageReader(caminho)
            leitor.setAutoTransform(True)
            tam = leitor.size()
            if tam.isValid() and max(tam.width(), tam.height()) > 192:
                leitor.setScaledSize(tam.scaled(192, 192, Qt.AspectRatioMode.KeepAspectRatio))
            img = leitor.read()
            self._miniaturas[chave] = QIcon(QPixmap.fromImage(img)) if not img.isNull() else QIcon()
        return self._miniaturas[chave]

    def recarregar(self):
        pasta = self.pasta_atual()
        filtro = self.busca.text().strip().casefold()
        self.grade.clear()
        try:
            arquivos = sorted(a for a in os.listdir(pasta) if a.lower().endswith(EXTENSOES))
        except OSError:
            arquivos = []
        for a in arquivos:
            nome = os.path.splitext(a)[0]
            if filtro and filtro not in nome.casefold():
                continue
            caminho = os.path.join(pasta, a)
            it = QListWidgetItem(self._icone(caminho), nome)
            it.setData(Qt.ItemDataRole.UserRole, caminho)
            it.setToolTip(nome)
            self.grade.addItem(it)
        uso = {"mapa": "vira MAPA", "token": "vira TOKEN", "objeto": "vira OBJETO",
               "projetor": "vai pro PROJETOR", "perguntar": "pergunta o que fazer"}[self.uso_atual()]
        self.dica.setText(f"{self.grade.count()} imagem(ns). Duplo clique ou arrastar pra mesa: {uso}. "
                          "Botão direito: mais opções (✂ remover fundo…).")

    def _escolher(self):
        caminhos, _ = QFileDialog.getOpenFileNames(self, "Importar imagens pro banco", "",
                                                   "Imagens (" + " ".join("*" + e for e in EXTENSOES) + ")")
        if caminhos:
            self.importar(caminhos)

    def importar(self, caminhos: list[str]) -> int:
        pasta = self.pasta_atual()
        n = 0
        for c in caminhos:
            if os.path.isdir(c):   # arrastou uma pasta inteira
                self.importar([os.path.join(c, a) for a in os.listdir(c)])
                continue
            if not c.lower().endswith(EXTENSOES) or not os.path.isfile(c):
                continue
            nome, ext = os.path.splitext(os.path.basename(c))
            try:
                shutil.copy2(c, nome_livre(pasta, nome, ext.lower()))
                n += 1
            except OSError:
                pass
        self.recarregar_pastas()
        return n

    def guardar_bytes(self, dados: bytes, nome: str, pasta: str | None = None) -> str:
        ext = ".jpg" if dados[:2] == b"\xff\xd8" else ".webp" if dados[8:12] == b"WEBP" else ".png"
        destino = nome_livre(pasta or self.pasta_atual(), nome, ext)
        with open(destino, "wb") as f:
            f.write(dados)
        self.recarregar_pastas()
        return destino

    # ------------------------------------------------------------ menu
    def _usar(self, uso, it):
        if it is None:
            return
        caminho = it.data(Qt.ItemDataRole.UserRole)
        if uso == "perguntar":
            menu = QMenu(self)
            for u, texto in (("mapa", "🗺 Pôr como mapa"), ("token", "⬤ Pôr como token"),
                             ("objeto", "📦 Pôr como objeto"), ("projetor", "📽 Mandar pro projetor")):
                menu.addAction(texto, lambda u=u: self.usar.emit(u, caminho))
            from .acabamento import iconizar_menu
            iconizar_menu(menu).exec(self.cursor().pos())
            return
        self.usar.emit(uso, caminho)

    def _menu(self, pos):
        it = self.grade.itemAt(pos)
        if it is None:
            return
        caminho = it.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        for u, texto in (("mapa", "🗺 Pôr na mesa como mapa"), ("token", "⬤ Pôr na mesa como token"),
                         ("objeto", "📦 Pôr na mesa como objeto"), ("projetor", "📽 Mandar pro projetor")):
            menu.addAction(texto, lambda u=u: self.usar.emit(u, caminho))
        menu.addSeparator()
        menu.addAction("✂ Remover fundo…", lambda: self._remover_fundo(caminho))
        menu.addAction("✏ Renomear…", lambda: self._renomear(caminho))
        mover = menu.addMenu("📁 Mover para")
        for k in range(self.cb_pasta.count()):
            destino = self.cb_pasta.itemData(k)
            a = mover.addAction(destino, lambda d=destino: self._mover(caminho, d))
            a.setEnabled(destino != self.cb_pasta.currentData())
        menu.addSeparator()
        menu.addAction("🗑 Apagar do banco", lambda: self._apagar())
        from .acabamento import iconizar_menu
        iconizar_menu(menu).exec(self.grade.viewport().mapToGlobal(pos))

    def _remover_fundo(self, caminho):
        from .remover_fundo import DialogoRemoverFundo
        try:
            with open(caminho, "rb") as f:
                dados = f.read()
        except OSError:
            return
        nome = os.path.splitext(os.path.basename(caminho))[0]
        d = DialogoRemoverFundo(dados, nome, self)
        if d.exec():
            self.guardar_bytes(d.resultado(), f"{nome} (sem fundo)", os.path.dirname(caminho))

    def _renomear(self, caminho):
        nome, ext = os.path.splitext(os.path.basename(caminho))
        novo, ok = QInputDialog.getText(self, "Renomear", "Nome:", text=nome)
        if ok and novo.strip() and novo.strip() != nome:
            try:
                os.rename(caminho, nome_livre(os.path.dirname(caminho), novo.strip(), ext))
            except OSError as erro:
                QMessageBox.warning(self, "Não deu", str(erro))
            self.recarregar()

    def _mover(self, caminho, pasta):
        nome, ext = os.path.splitext(os.path.basename(caminho))
        try:
            shutil.move(caminho, nome_livre(os.path.join(pasta_banco(), pasta), nome, ext))
        except OSError as erro:
            QMessageBox.warning(self, "Não deu", str(erro))
        self.recarregar_pastas()

    def _apagar(self):
        itens = self.grade.selectedItems()
        if not itens:
            return
        if QMessageBox.question(self, "Apagar", f"Apagar {len(itens)} imagem(ns) do banco?\n"
                                "(O que já está nas aventuras continua lá.)") != QMessageBox.StandardButton.Yes:
            return
        for it in itens:
            try:
                os.remove(it.data(Qt.ItemDataRole.UserRole))
            except OSError:
                pass
        self.recarregar_pastas()
