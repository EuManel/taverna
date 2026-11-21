"""
📓 Diário da campanha.

Mestre: entradas por tipo (📅 Sessão, 👤 NPC, 🏰 Lugar, 📜 Missão, 📝 Nota), escritas com
formatação simples (# título, **negrito**, *itálico*, - listas). Cada entrada é 🔒 só do mestre
ou 👁 compartilhada com os jogadores. Fica salvo dentro da aventura (.taverna).

Jogador: lê o que o mestre compartilhou + "Minhas anotações" (só dele, salvas no PC dele).
"""

import time
import uuid

from PyQt6.QtCore import QSettings, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                             QListWidgetItem, QMessageBox, QPlainTextEdit, QPushButton, QSplitter,
                             QTabWidget, QTextBrowser, QVBoxLayout, QWidget)

from .acabamento import item_com_icone

TIPOS = {"sessao": "📅 Sessão", "npc": "👤 NPC", "lugar": "🏰 Lugar", "missao": "📜 Missão", "nota": "📝 Nota"}
MODELOS = {
    "sessao": "## O que aconteceu\n\n\n## NPCs que apareceram\n\n\n## Pistas e ganchos\n\n\n## Recompensas\n",
    "npc": "**Quem é:** \n**Onde fica:** \n**O que quer:** \n**O que o grupo sabe:** \n",
    "lugar": "**Onde fica:** \n**Como é:** \n**Quem mora lá:** \n**Segredos:** \n",
    "missao": "**Quem pediu:** \n**Objetivo:** \n**Recompensa:** \n**Situação:** em andamento\n",
    "nota": "",
}
DICA = "Formatação: # título · **negrito** · *itálico* · - item de lista"


def nova_entrada(tipo: str, numero: int = 1) -> dict:
    hoje = time.strftime("%d/%m/%Y")
    titulo = {"sessao": f"Sessão {numero} — {hoje}", "npc": "Novo NPC", "lugar": "Novo lugar",
              "missao": "Nova missão", "nota": "Nota"}[tipo]
    return {"id": uuid.uuid4().hex[:12], "tipo": tipo, "titulo": titulo, "texto": MODELOS[tipo],
            "compartilhado": False, "criado": hoje}


class JanelaDiario(QDialog):
    """Diário do mestre."""
    mudou = pyqtSignal()

    def __init__(self, entradas: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("📓 Diário da campanha")
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.resize(980, 640)
        self.entradas = entradas          # a mesma lista da janela do mestre (edita no lugar)
        self.atual = None
        raiz = QHBoxLayout(self)
        div = QSplitter()
        raiz.addWidget(div)

        esq = QWidget()
        le = QVBoxLayout(esq)
        le.setContentsMargins(0, 0, 0, 0)
        self.filtro = QComboBox()
        self.filtro.addItem("Tudo", "")
        for k, v in TIPOS.items():
            self.filtro.addItem(v, k)
        self.filtro.currentIndexChanged.connect(lambda _i: self._recarregar())
        le.addWidget(self.filtro)
        self.busca = QLineEdit()
        self.busca.setPlaceholderText("🔎 procurar…")
        self.busca.textChanged.connect(lambda _t: self._recarregar())
        le.addWidget(self.busca)
        self.lista = QListWidget()
        self.lista.currentItemChanged.connect(self._escolheu)
        le.addWidget(self.lista, 1)
        linha = QHBoxLayout()
        self.cb_novo = QComboBox()
        for k, v in TIPOS.items():
            self.cb_novo.addItem(v, k)
        linha.addWidget(self.cb_novo, 1)
        b = QPushButton("＋ Nova")
        b.setObjectName("primario")
        b.clicked.connect(self._nova)
        linha.addWidget(b)
        le.addLayout(linha)
        b = QPushButton("🗑 Apagar entrada")
        b.clicked.connect(self._apagar)
        le.addWidget(b)
        div.addWidget(esq)

        dir_ = QWidget()
        ld = QVBoxLayout(dir_)
        ld.setContentsMargins(0, 0, 0, 0)
        linha = QHBoxLayout()
        self.tipo = QComboBox()
        for k, v in TIPOS.items():
            self.tipo.addItem(v, k)
        self.tipo.currentIndexChanged.connect(self._editou)
        linha.addWidget(self.tipo)
        self.titulo = QLineEdit()
        self.titulo.setPlaceholderText("Título")
        self.titulo.textEdited.connect(self._editou)
        linha.addWidget(self.titulo, 1)
        ld.addLayout(linha)
        self.compartilhar = QCheckBox("👁 Compartilhar com os jogadores (eles leem, não editam)")
        self.compartilhar.toggled.connect(self._editou)
        ld.addWidget(self.compartilhar)
        self.abas = QTabWidget()
        self.texto = QPlainTextEdit()
        self.texto.setPlaceholderText("Escreva aqui…")
        self.texto.textChanged.connect(self._editou)
        self.previa = QTextBrowser()
        self.previa.setOpenLinks(False)
        self.abas.addTab(self.texto, "✏ Escrever")
        self.abas.addTab(self.previa, "👁 Ver como fica")
        self.abas.currentChanged.connect(lambda i: i == 1 and self.previa.setMarkdown(self.texto.toPlainText()))
        ld.addWidget(self.abas, 1)
        rodape = QHBoxLayout()
        dica = QLabel(DICA)
        dica.setObjectName("dica")
        rodape.addWidget(dica, 1)
        self.status = QLabel()
        rodape.addWidget(self.status)
        ld.addLayout(rodape)
        div.addWidget(dir_)
        div.setSizes([280, 700])
        self._aviso = QTimer(self)
        self._aviso.setSingleShot(True)
        self._aviso.setInterval(800)
        self._aviso.timeout.connect(self.mudou.emit)
        self._recarregar()
        self.editor_ativo(False)
        if self.lista.count():
            self.lista.setCurrentRow(0)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def editor_ativo(self, ativo):
        for w in (self.tipo, self.titulo, self.compartilhar, self.abas):
            w.setEnabled(ativo)

    def _recarregar(self, selecionar: str | None = None):
        filtro = self.filtro.currentData()
        busca = self.busca.text().strip().casefold()
        sel = selecionar or (self.atual or {}).get("id")
        self.lista.blockSignals(True)
        self.lista.clear()
        for e in reversed(self.entradas):   # mais novas em cima
            if filtro and e.get("tipo") != filtro:
                continue
            if busca and busca not in (e.get("titulo", "") + " " + e.get("texto", "")).casefold():
                continue
            it = item_com_icone(QListWidgetItem(), f"{TIPOS.get(e.get('tipo'), '📝').split()[0]} {e.get('titulo', '')}"
                                + ("" if e.get("compartilhado") else "   · só você"))
            it.setData(Qt.ItemDataRole.UserRole, e["id"])
            it.setToolTip(("Compartilhada com os jogadores" if e.get("compartilhado") else "Só você vê")
                          + f" · criada em {e.get('criado', '')}")
            self.lista.addItem(it)
            if e["id"] == sel:
                self.lista.setCurrentItem(it)
        self.lista.blockSignals(False)
        it = self.lista.currentItem()
        novo = self._entrada(it.data(Qt.ItemDataRole.UserRole)) if it else None
        if novo is not self.atual:
            self._escolheu(it)

    def _entrada(self, eid):
        return next((e for e in self.entradas if e["id"] == eid), None)

    def _escolheu(self, it, _antes=None):
        self.atual = self._entrada(it.data(Qt.ItemDataRole.UserRole)) if it else None
        e = self.atual
        self.editor_ativo(e is not None)
        if e is None:
            return
        for w in (self.tipo, self.titulo, self.compartilhar, self.texto):
            w.blockSignals(True)
        self.tipo.setCurrentIndex(max(0, self.tipo.findData(e.get("tipo"))))
        self.titulo.setText(e.get("titulo", ""))
        self.compartilhar.setChecked(bool(e.get("compartilhado")))
        self.texto.setPlainText(e.get("texto", ""))
        for w in (self.tipo, self.titulo, self.compartilhar, self.texto):
            w.blockSignals(False)
        if self.abas.currentIndex() == 1:
            self.previa.setMarkdown(e.get("texto", ""))

    def _editou(self, *_):
        e = self.atual
        if e is None:
            return
        antes = (e.get("tipo"), e.get("titulo"), e.get("compartilhado"))
        e["tipo"] = self.tipo.currentData()
        e["titulo"] = self.titulo.text()
        e["compartilhado"] = self.compartilhar.isChecked()
        e["texto"] = self.texto.toPlainText()
        if antes != (e["tipo"], e["titulo"], e["compartilhado"]):
            self._recarregar(e["id"])
        self.status.setText("Os jogadores veem esta" if e["compartilhado"] else "Só você vê esta")
        self._aviso.start()

    def _nova(self):
        tipo = self.cb_novo.currentData()
        n = sum(1 for e in self.entradas if e.get("tipo") == "sessao") + 1
        e = nova_entrada(tipo, n)
        self.entradas.append(e)
        self.filtro.setCurrentIndex(0)
        self.busca.clear()
        self._recarregar(e["id"])
        self.titulo.setFocus()
        self.titulo.selectAll()
        self.mudou.emit()

    def _apagar(self):
        e = self.atual
        if e is None:
            return
        if QMessageBox.question(self, "Apagar", f"Apagar “{e.get('titulo', '')}” do diário?") \
                != QMessageBox.StandardButton.Yes:
            return
        self.entradas.remove(e)
        self.atual = None
        self._recarregar()
        if self.lista.count():
            self.lista.setCurrentRow(0)
        else:
            self.editor_ativo(False)
        self.mudou.emit()

    def closeEvent(self, ev):
        if self._aviso.isActive():
            self._aviso.stop()
            self.mudou.emit()
        super().closeEvent(ev)


class JanelaDiarioPlayer(QDialog):
    """Jogador: o que o mestre compartilhou + minhas anotações."""

    def __init__(self, entradas: list[dict], aventura: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📓 Diário da campanha")
        self.resize(900, 600)
        self.chave = f"notas/{aventura or 'sem nome'}"
        self.cfg = QSettings("Taverna", "Player")
        raiz = QVBoxLayout(self)
        abas = QTabWidget()
        raiz.addWidget(abas)

        # o que o mestre compartilhou
        div = QSplitter()
        self.lista = QListWidget()
        self.leitor = QTextBrowser()
        self.leitor.setOpenLinks(False)
        div.addWidget(self.lista)
        div.addWidget(self.leitor)
        div.setSizes([260, 620])
        self.entradas = []
        self.lista.currentRowChanged.connect(self._ler)
        abas.addTab(div, "📖 Do mestre")
        # minhas anotações
        self.notas = QPlainTextEdit(self.cfg.value(self.chave, "") or "")
        self.notas.setPlaceholderText("Suas anotações (só você vê): pistas, nomes, suspeitas…")
        self.notas.textChanged.connect(lambda: self.cfg.setValue(self.chave, self.notas.toPlainText()))
        abas.addTab(self.notas, "✏ Minhas anotações")
        self.atualizar(entradas)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def atualizar(self, entradas: list[dict]):
        atual = self.lista.currentItem().data(Qt.ItemDataRole.UserRole) if self.lista.currentItem() else None
        self.entradas = list(reversed(entradas))
        self.lista.blockSignals(True)
        self.lista.clear()
        for e in self.entradas:
            it = item_com_icone(QListWidgetItem(), f"{TIPOS.get(e.get('tipo'), '📝').split()[0]} {e.get('titulo', '')}")
            it.setData(Qt.ItemDataRole.UserRole, e.get("id"))
            self.lista.addItem(it)
        self.lista.blockSignals(False)
        if not self.entradas:
            self.leitor.setMarkdown("*O mestre ainda não compartilhou nada no diário.*")
            return
        ids = [e.get("id") for e in self.entradas]
        self.lista.setCurrentRow(ids.index(atual) if atual in ids else 0)

    def _ler(self, i):
        if 0 <= i < len(self.entradas):
            e = self.entradas[i]
            self.leitor.setMarkdown(f"# {e.get('titulo', '')}\n\n{e.get('texto', '')}")
