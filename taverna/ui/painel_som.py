"""
SOM E MÚSICA (mestre): efeitos sonoros importados + fila de músicas do YouTube.
"""

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QCheckBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                             QListWidgetItem, QPushButton, QScrollArea, QSlider, QVBoxLayout, QWidget)

from .audio import EXTENSOES, TEM_AUDIO, BibliotecaSons
from .musica import PlayerYouTube, extrair_id


def _titulo(texto):
    l = QLabel(texto)
    l.setStyleSheet("font-weight: bold; letter-spacing: 1px; margin-top: 8px;")
    return l


def _dica(texto):
    l = QLabel(texto)
    l.setWordWrap(True)
    l.setStyleSheet("font-size: 11px;")
    return l


def _slider_volume(valor=80):
    s = QSlider(Qt.Orientation.Horizontal)
    s.setRange(0, 100)
    s.setValue(valor)
    return s


class PainelSom(QWidget):
    # efeitos sonoros
    tocar_som = pyqtSignal(str, float, bool, bool)   # caminho, volume, ambiente, pra_todos
    parar_sons = pyqtSignal()
    volume_sons = pyqtSignal(float)
    # música
    musica = pyqtSignal(dict)                       # mudanças pro servidor (id, tocando, pos, titulo)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.biblioteca = BibliotecaSons("Mestre")
        self.fila: list[dict] = []        # [{"id", "titulo"}]
        self.atual = -1
        self.tocando = False
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setFrameShape(QFrame.Shape.NoFrame)
        rolagem.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        raiz.addWidget(rolagem)
        miolo = QWidget()
        rolagem.setWidget(miolo)
        lay = QVBoxLayout(miolo)
        lay.setContentsMargins(10, 4, 10, 10)
        lay.setSpacing(6)

        # ---------------------------------------------------------------- música
        lay.addWidget(_titulo("🎵  MÚSICA (YOUTUBE)"))
        linha = QHBoxLayout()
        self.ed_link = QLineEdit()
        self.ed_link.setPlaceholderText("Cole o link do YouTube…")
        self.ed_link.returnPressed.connect(self._adicionar_link)
        linha.addWidget(self.ed_link, 1)
        b = QPushButton("➕ Fila")
        b.clicked.connect(self._adicionar_link)
        linha.addWidget(b)
        lay.addLayout(linha)
        self.lista_fila = QListWidget()
        self.lista_fila.setMaximumHeight(110)
        self.lista_fila.itemDoubleClicked.connect(lambda it: self.tocar_indice(self.lista_fila.row(it)))
        lay.addWidget(self.lista_fila)
        linha = QHBoxLayout()
        self.btn_play = QPushButton("▶ Tocar")
        self.btn_play.setObjectName("primario")
        self.btn_play.clicked.connect(self._play_pause)
        self.btn_prox = QPushButton("⏭")
        self.btn_prox.setToolTip("Próxima da fila")
        self.btn_prox.clicked.connect(self.proxima)
        self.btn_parar = QPushButton("⏹")
        self.btn_parar.setToolTip("Parar a música pra todo mundo")
        self.btn_parar.clicked.connect(self.parar_musica)
        self.btn_tirar = QPushButton("🗑")
        self.btn_tirar.setToolTip("Tirar da fila a música selecionada")
        self.btn_tirar.clicked.connect(self._tirar_da_fila)
        for w in (self.btn_play, self.btn_prox, self.btn_parar, self.btn_tirar):
            linha.addWidget(w)
        lay.addLayout(linha)
        self.ck_repetir = QCheckBox("🔁 Repetir a fila")
        self.ck_repetir.setChecked(True)
        lay.addWidget(self.ck_repetir)
        self.lbl_tocando = QLabel("Nada tocando.")
        self.lbl_tocando.setWordWrap(True)
        lay.addWidget(self.lbl_tocando)
        self.player = PlayerYouTube()
        self.player.setMinimumHeight(170)
        self.player.info_mudou.connect(self._info)
        self.player.acabou.connect(self._acabou)
        lay.addWidget(self.player)
        linha = QHBoxLayout()
        linha.addWidget(QLabel("Meu volume"))
        self.vol_musica = _slider_volume(70)
        self.vol_musica.valueChanged.connect(self.player.volume)
        linha.addWidget(self.vol_musica, 1)
        lay.addLayout(linha)
        lay.addWidget(_dica("Todo mundo vê e ouve o player oficial do YouTube, seguindo o seu. "
                            "Cada jogador ajusta o próprio volume."))

        # ---------------------------------------------------------------- efeitos
        lay.addWidget(_titulo("🔊  EFEITOS SONOROS"))
        linha = QHBoxLayout()
        b = QPushButton("➕ Importar sons…")
        b.clicked.connect(self._importar)
        linha.addWidget(b)
        self.btn_remover = QPushButton("🗑")
        self.btn_remover.setToolTip("Tirar da lista (o arquivo não é apagado)")
        self.btn_remover.clicked.connect(self._remover)
        linha.addWidget(self.btn_remover)
        linha.addStretch(1)
        lay.addLayout(linha)
        self.lista_sons = QListWidget()
        self.lista_sons.setMinimumHeight(150)
        self.lista_sons.itemDoubleClicked.connect(lambda _it: self._tocar(True))
        self.lista_sons.currentRowChanged.connect(self._som_selecionado)
        lay.addWidget(self.lista_sons)
        self.ck_ambiente = QCheckBox("🔁 Ambiente (fica repetindo até parar)")
        self.ck_ambiente.toggled.connect(self._som_editado)
        lay.addWidget(self.ck_ambiente)
        linha = QHBoxLayout()
        linha.addWidget(QLabel("Volume deste som"))
        self.vol_som = _slider_volume(80)
        self.vol_som.sliderReleased.connect(self._som_editado)
        linha.addWidget(self.vol_som, 1)
        lay.addLayout(linha)
        linha = QHBoxLayout()
        self.btn_todos = QPushButton("▶ Tocar pra todos")
        self.btn_todos.setObjectName("primario")
        self.btn_todos.clicked.connect(lambda: self._tocar(True))
        self.btn_eu = QPushButton("🎧 Só pra mim")
        self.btn_eu.clicked.connect(lambda: self._tocar(False))
        linha.addWidget(self.btn_todos, 1)
        linha.addWidget(self.btn_eu)
        lay.addLayout(linha)
        self.btn_parar_sons = QPushButton("⏹ Parar todos os sons")
        self.btn_parar_sons.clicked.connect(self.parar_sons.emit)
        lay.addWidget(self.btn_parar_sons)
        linha = QHBoxLayout()
        linha.addWidget(QLabel("Meu volume"))
        self.vol_geral = _slider_volume(80)
        self.vol_geral.valueChanged.connect(lambda v: self.volume_sons.emit(v / 100))
        linha.addWidget(self.vol_geral, 1)
        lay.addLayout(linha)
        lay.addWidget(_dica("Use sons que você baixou (Pixabay, Freesound, MyInstants…). Duplo clique = "
                            "tocar pra todos. O arquivo vai uma vez pra cada jogador."
                            + ("" if TEM_AUDIO else "\n⚠ Este computador está sem o módulo de áudio do Qt.")))
        lay.addStretch(1)
        self.recarregar_sons()
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    # ================================================================ efeitos sonoros
    def recarregar_sons(self):
        atual = self.lista_sons.currentRow()
        self.lista_sons.blockSignals(True)
        self.lista_sons.clear()
        for s in self.biblioteca.lista():
            existe = os.path.isfile(s["caminho"])
            texto = ("🔁 " if s.get("ambiente") else "🔊 ") + s["nome"] + ("" if existe else "  (arquivo sumiu)")
            it = QListWidgetItem(texto)
            it.setToolTip(s["caminho"])
            if not existe:
                it.setForeground(Qt.GlobalColor.gray)
            self.lista_sons.addItem(it)
        self.lista_sons.blockSignals(False)
        if self.lista_sons.count():
            self.lista_sons.setCurrentRow(max(0, min(atual, self.lista_sons.count() - 1)))

    def _som(self) -> dict | None:
        i = self.lista_sons.currentRow()
        lista = self.biblioteca.lista()
        return lista[i] if 0 <= i < len(lista) else None

    def _som_selecionado(self, _i):
        s = self._som()
        for w in (self.ck_ambiente, self.vol_som):
            w.blockSignals(True)
        self.ck_ambiente.setChecked(bool(s and s.get("ambiente")))
        self.vol_som.setValue(int(s.get("vol", 80)) if s else 80)
        for w in (self.ck_ambiente, self.vol_som):
            w.blockSignals(False)

    def _som_editado(self, *_):
        i = self.lista_sons.currentRow()
        lista = self.biblioteca.lista()
        if not (0 <= i < len(lista)):
            return
        lista[i]["ambiente"] = self.ck_ambiente.isChecked()
        lista[i]["vol"] = self.vol_som.value()
        self.biblioteca.salvar(lista)
        self.recarregar_sons()

    def _importar(self):
        filtro = "Sons (" + " ".join(f"*.{e}" for e in EXTENSOES) + ")"
        caminhos, _ = QFileDialog.getOpenFileNames(self, "Importar sons", "", filtro)
        if caminhos:
            self.biblioteca.adicionar(caminhos)
            self.recarregar_sons()
            self.lista_sons.setCurrentRow(self.lista_sons.count() - 1)

    def _remover(self):
        i = self.lista_sons.currentRow()
        lista = self.biblioteca.lista()
        if 0 <= i < len(lista):
            del lista[i]
            self.biblioteca.salvar(lista)
            self.recarregar_sons()

    def _tocar(self, pra_todos: bool):
        s = self._som()
        if s and os.path.isfile(s["caminho"]):
            self.tocar_som.emit(s["caminho"], s.get("vol", 80) / 100, bool(s.get("ambiente")), pra_todos)

    # ================================================================ música
    def _adicionar_link(self):
        vid = extrair_id(self.ed_link.text())
        if not vid:
            self.ed_link.setPlaceholderText("Esse link não parece do YouTube. Tenta de novo…")
            self.ed_link.clear()
            return
        self.fila.append({"id": vid, "titulo": ""})
        self.ed_link.clear()
        self._recarregar_fila()

    def _recarregar_fila(self):
        antes = self.lista_fila.currentRow()
        self.lista_fila.clear()
        for k, f in enumerate(self.fila):
            marca = ("▶ " if self.tocando else "⏸ ") if k == self.atual else "    "
            self.lista_fila.addItem(marca + (f["titulo"] or f"youtu.be/{f['id']}"))
        if 0 <= self.atual < len(self.fila):
            self.lista_fila.setCurrentRow(self.atual)
        elif self.fila:
            self.lista_fila.setCurrentRow(max(0, min(antes, len(self.fila) - 1)))

    def _tirar_da_fila(self):
        i = self.lista_fila.currentRow()
        if not (0 <= i < len(self.fila)):
            return
        del self.fila[i]
        if i == self.atual:
            self.parar_musica()
        elif i < self.atual:
            self.atual -= 1
        self._recarregar_fila()

    def tocar_indice(self, i: int):
        if not (0 <= i < len(self.fila)):
            return
        self.atual = i
        self.tocando = True
        f = self.fila[i]
        self.player.carregar(f["id"], 0, True)
        self.musica.emit({"id": f["id"], "tocando": True, "pos": 0.0, "titulo": f["titulo"]})
        self._atualizar_botoes()
        self._recarregar_fila()

    def _play_pause(self):
        if self.atual < 0 or self.atual >= len(self.fila):
            i = self.lista_fila.currentRow()
            self.tocar_indice(i if i >= 0 else 0)
            return
        t = float(self.player.info.get("t", 0) or 0)
        if self.tocando:
            self.player.pausar()
            self.tocando = False
            self.musica.emit({"tocando": False, "pos": t})
        else:
            self.player.tocar()
            self.tocando = True
            self.musica.emit({"tocando": True, "pos": t})
        self._atualizar_botoes()
        self._recarregar_fila()

    def proxima(self):
        if not self.fila:
            return
        i = self.atual + 1
        if i >= len(self.fila):
            if not self.ck_repetir.isChecked():
                self.parar_musica()
                return
            i = 0
        self.tocar_indice(i)

    def parar_musica(self):
        self.player.parar()
        self.atual = -1
        self.tocando = False
        self.musica.emit({"id": None})
        self._atualizar_botoes()
        self._recarregar_fila()

    def _acabou(self):
        if self.tocando:
            self.proxima()

    def _info(self, info):
        if not (0 <= self.atual < len(self.fila)):
            return
        f = self.fila[self.atual]
        titulo = info.get("titulo") or ""
        if titulo and titulo != f["titulo"] and info.get("id") in ("", f["id"]):
            f["titulo"] = titulo
            self.musica.emit({"titulo": titulo})
            self._recarregar_fila()
        if info.get("erro") in (101, 150, 153):
            self.lbl_tocando.setText("O dono desse vídeo não deixa tocar fora do YouTube. Pulei pra próxima.")
            info["erro"] = None
            self.proxima()
            return
        # de tempos em tempos, acerta o relógio do servidor com o player do mestre
        if self.tocando and info.get("estado") == 1:
            self._contagem = getattr(self, "_contagem", 0) + 1
            if self._contagem % 5 == 0:
                self.musica.emit({"pos": float(info.get("t", 0))})
        self._atualizar_botoes()

    def _atualizar_botoes(self):
        self.btn_play.setText("⏸ Pausar" if self.tocando else "▶ Tocar")
        if 0 <= self.atual < len(self.fila):
            f = self.fila[self.atual]
            self.lbl_tocando.setText(("▶ Tocando: " if self.tocando else "⏸ Pausado: ")
                                     + (f["titulo"] or f"youtu.be/{f['id']}"))
        else:
            self.lbl_tocando.setText("Nada tocando.")
