"""
Biblioteca de objetos (props): escolha a categoria, arraste pra mesa ou dê duplo clique
(coloca no meio da tela). Também dá pra importar uma imagem PNG sua como objeto.
"""

from PyQt6.QtCore import QMimeData, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QDrag, QIcon
from PyQt6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QLineEdit, QListView, QListWidget,
                             QListWidgetItem, QPushButton, QVBoxLayout, QWidget)

from ..mesa.props import CATALOGO, CATEGORIAS, desenhar_miniatura, temas_do_prop

MIME_PROP = "application/x-taverna-prop"
AMBIENTACOES = ("medieval", "moderno", "futurista", "magico", "terror", "steampunk", "posapoc")   # Claro/Escuro são só estilo


class ListaProps(QListWidget):
    def startDrag(self, acoes):
        item = self.currentItem()
        if item is None:
            return
        mime = QMimeData()
        mime.setData(MIME_PROP, item.data(Qt.ItemDataRole.UserRole).encode())
        arrasto = QDrag(self)
        arrasto.setMimeData(mime)
        arrasto.setPixmap(item.icon().pixmap(56, 56))
        arrasto.exec(Qt.DropAction.CopyAction)


class PainelObjetos(QWidget):
    colocar = pyqtSignal(str)          # tipo do catálogo
    importar_imagem = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # Filtro: primeiro os temas (abre no tema da aventura), depois as categorias de sempre.
        # Dado do item: ("tema", chave) · ("cat", nome) · None = tudo
        from ..temas import TEMAS
        self.categoria = QComboBox()
        self.categoria.setMaxVisibleItems(20)
        self.categoria.addItem("Todos os objetos", None)
        self.categoria.insertSeparator(self.categoria.count())
        for chave in AMBIENTACOES:
            self.categoria.addItem(f"Tema: {TEMAS[chave]['nome']}", ("tema", chave))
        self.categoria.insertSeparator(self.categoria.count())
        for c in CATEGORIAS:
            self.categoria.addItem(c, ("cat", c))
        self.categoria.currentIndexChanged.connect(self._filtrar)
        self._tema = None
        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Buscar…")
        self.busca.setClearButtonEnabled(True)
        self.busca.textChanged.connect(self._filtrar)

        self.lista = ListaProps()
        self.lista.setViewMode(QListView.ViewMode.IconMode)
        self.lista.setIconSize(QSize(56, 56))
        self.lista.setGridSize(QSize(86, 92))
        self.lista.setResizeMode(QListView.ResizeMode.Adjust)
        self.lista.setMovement(QListView.Movement.Static)
        self.lista.setWordWrap(True)
        self.lista.setDragEnabled(True)
        self.lista.setSpacing(2)
        self.lista.itemDoubleClicked.connect(
            lambda item: self.colocar.emit(item.data(Qt.ItemDataRole.UserRole)))
        for chave, (nome, cat, w, h, _d, extras) in CATALOGO.items():
            item = QListWidgetItem(QIcon(desenhar_miniatura(chave, 56)), nome)
            item.setData(Qt.ItemDataRole.UserRole, chave)
            item.setData(Qt.ItemDataRole.UserRole + 1, cat)
            dicas = [f"{w:g} × {h:g} m"]
            if extras.get("interativo"):
                dicas.append("Interativo (dá pra guardar itens)")
            if extras.get("bloqueia"):
                dicas.append("Bloqueia a visão")
            if extras.get("luz"):
                dicas.append("Ilumina")
            item.setToolTip(f"{nome}\n" + "\n".join(dicas))
            self.lista.addItem(item)

        importar = QPushButton("🖼  Importar imagem como objeto…")
        importar.setToolTip("Use um PNG seu (de preferência com fundo transparente, visto de cima)")
        importar.clicked.connect(self.importar_imagem)
        dica = QLabel("Arraste pra mesa ou dê duplo clique. Passe o mouse num objeto pra ver se ele "
                      "é interativo, bloqueia a visão ou ilumina.")
        dica.setObjectName("dica")
        dica.setWordWrap(True)

        topo = QHBoxLayout()
        topo.addWidget(self.categoria, 1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addLayout(topo)
        layout.addWidget(self.busca)
        layout.addWidget(self.lista, 1)
        layout.addWidget(importar)
        layout.addWidget(dica)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def definir_tema(self, chave: str):
        """A aventura mudou de tema: o filtro passa pro tema novo (Claro/Escuro = todos os objetos)."""
        if chave == self._tema:
            return
        self._tema = chave
        k = 0   # (findData do Qt não compara tuplas do Python: procura na mão)
        if chave in AMBIENTACOES:
            k = next((i for i in range(self.categoria.count()) if self.categoria.itemData(i) == ("tema", chave)), 0)
        self.categoria.setCurrentIndex(k)
        self._ordenar()
        self._filtrar()

    def _ordenar(self):
        """Os objetos próprios do tema da aventura vêm primeiro; depois os comuns, na ordem do catálogo."""
        from ..mesa.props_temas import CATALOGO_TEMAS
        ordem = {chave: n for n, chave in enumerate(CATALOGO)}

        def prioridade(it):
            chave = it.data(Qt.ItemDataRole.UserRole)
            do_tema = self._tema in temas_do_prop(chave)
            # 0 = feitos pra este tema · 1 = antigos que combinam com ele · 2 = comuns
            return (0 if do_tema and chave in CATALOGO_TEMAS else 1 if do_tema else 2, ordem.get(chave, 0))

        itens = [self.lista.takeItem(0) for _ in range(self.lista.count())]
        itens.sort(key=prioridade)
        for it in itens:
            self.lista.addItem(it)

    def _filtrar(self):
        from ..compendio.compendio import sem_acento
        filtro = self.categoria.currentData()
        termo = sem_acento(self.busca.text().strip())
        for k in range(self.lista.count()):
            item = self.lista.item(k)
            if termo:   # buscando pelo nome: procura em tudo, sem filtro
                ok = termo in sem_acento(item.text())
            elif filtro is None:
                ok = True
            elif filtro[0] == "cat":
                ok = item.data(Qt.ItemDataRole.UserRole + 1) == filtro[1]
            else:       # tema: os do tema + os comuns (que servem em qualquer um)
                temas = temas_do_prop(item.data(Qt.ItemDataRole.UserRole))
                ok = not temas or filtro[1] in temas
            item.setHidden(not ok)
