"""Gerenciar as tabelas de sorteio personalizadas (qualquer sistema)."""

import copy

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QHeaderView, QInputDialog,
                             QLabel, QLineEdit, QListWidget, QMessageBox, QPlainTextEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from ..jogo import tabelas as T

DICA_COLAR = ("Cole a lista (um item por linha). Dá pra marcar:\n"
              "  quantidade:  Munição ×2d10   ou   Granada ×2\n"
              "  chance:      Fuzil de assalto [raro]   (comum · incomum · raro · muito raro)\n"
              "  descrição:   Kit médico | Recupera 2d8 PV\n\n"
              "Dica: abra o livro no leitor de PDF do Taverna, copie a tabela de itens e cole aqui.")


class DialogoColar(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Colar lista de itens")
        self.resize(560, 460)
        lay = QVBoxLayout(self)
        dica = QLabel(DICA_COLAR)
        dica.setWordWrap(True)
        lay.addWidget(dica)
        self.texto = QPlainTextEdit()
        self.texto.setPlaceholderText("Pistola\nFuzil de assalto [raro]\nMunição ×2d10\nKit médico | Recupera 2d8 PV")
        lay.addWidget(self.texto, 1)
        self.modo = QComboBox()
        self.modo.addItem("Somar aos itens que já estão na tabela", "somar")
        self.modo.addItem("Trocar tudo por essa lista", "trocar")
        lay.addWidget(self.modo)
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)
        lay.addWidget(b)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema


class DialogoTabelas(QDialog):
    COLUNAS = ["Item", "Quantidade", "Chance", "Descrição"]

    def __init__(self, parent=None, selecionar: str = ""):
        super().__init__(parent)
        self.setWindowTitle("🎲 Tabelas de sorteio")
        self.resize(940, 580)
        self.tabelas = T.listar()
        self.atual = -1
        self._nome_salvo = None
        raiz = QHBoxLayout(self)

        # --- lista de tabelas
        esq = QVBoxLayout()
        esq.addWidget(QLabel("<b>Suas tabelas</b> (valem pra todas as aventuras)"))
        self.lista = QListWidget()
        self.lista.currentRowChanged.connect(self._trocar)
        esq.addWidget(self.lista, 1)
        linha = QHBoxLayout()
        for texto, funcao in (("＋ Nova", self._nova), ("⧉ Duplicar", self._duplicar), ("🗑", self._apagar)):
            b = QPushButton(texto)
            b.clicked.connect(funcao)
            linha.addWidget(b)
        esq.addLayout(linha)
        b = QPushButton("📂 Abrir a pasta das tabelas")
        b.setToolTip("Cada tabela é um arquivo .json — dá pra mandar pros amigos")
        b.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(T.pasta_tabelas())))
        esq.addWidget(b)
        caixa_esq = QWidget()
        caixa_esq.setLayout(esq)
        caixa_esq.setFixedWidth(260)
        raiz.addWidget(caixa_esq)

        # --- editor
        dir_ = QVBoxLayout()
        linha = QHBoxLayout()
        linha.addWidget(QLabel("Nome"))
        self.nome = QLineEdit()
        self.nome.setPlaceholderText("ex.: Ordem Paranormal — Armas")
        linha.addWidget(self.nome, 1)
        dir_.addLayout(linha)
        linha = QHBoxLayout()
        linha.addWidget(QLabel("Dinheiro"))
        self.moeda = QLineEdit()
        self.moeda.setPlaceholderText("nome (ex.: Créditos, R$) — vazio = sem dinheiro")
        linha.addWidget(self.moeda, 1)
        linha.addWidget(QLabel("quantia"))
        self.moeda_dados = QLineEdit()
        self.moeda_dados.setPlaceholderText("ex.: 2d10, 3d6+5, 50")
        self.moeda_dados.setMaximumWidth(140)
        linha.addWidget(self.moeda_dados)
        dir_.addLayout(linha)
        self.tabela = QTableWidget(0, len(self.COLUNAS))
        self.tabela.setHorizontalHeaderLabels(self.COLUNAS)
        h = self.tabela.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        dir_.addWidget(self.tabela, 1)
        linha = QHBoxLayout()
        for texto, funcao in (("＋ Item", self._mais_linha), ("− Tirar item", self._menos_linha),
                              ("📋 Colar lista…", self._colar), ("🎲 Testar", self._testar)):
            b = QPushButton(texto)
            b.clicked.connect(funcao)
            linha.addWidget(b)
        linha.addStretch(1)
        dir_.addLayout(linha)
        self.resultado = QLabel("Quantidade aceita dados (2d10). Chance: comum sai mais, muito raro quase nunca.")
        self.resultado.setWordWrap(True)
        dir_.addWidget(self.resultado)
        botoes = QDialogButtonBox()
        salvar = botoes.addButton("💾 Salvar", QDialogButtonBox.ButtonRole.ApplyRole)
        salvar.clicked.connect(self._salvar_atual)
        fechar = botoes.addButton("Fechar", QDialogButtonBox.ButtonRole.AcceptRole)
        fechar.clicked.connect(self.accept)
        dir_.addWidget(botoes)
        self.editor = QWidget()
        self.editor.setLayout(dir_)
        raiz.addWidget(self.editor, 1)

        self._recarregar_lista()
        nomes = [t["nome"] for t in self.tabelas]
        if selecionar in nomes:
            self.lista.setCurrentRow(nomes.index(selecionar))
        elif self.tabelas:
            self.lista.setCurrentRow(0)
        self.editor.setEnabled(bool(self.tabelas))
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    # ------------------------------------------------------------ lista
    def _recarregar_lista(self):
        self.lista.blockSignals(True)
        self.lista.clear()
        for t in self.tabelas:
            self.lista.addItem(f"{t['nome']}  ({len(t.get('linhas', []))} itens)")
        self.lista.blockSignals(False)

    def _trocar(self, i):
        if self.atual >= 0:
            self._salvar_atual(silencioso=True)
        self.atual = i
        self.editor.setEnabled(0 <= i < len(self.tabelas))
        if not (0 <= i < len(self.tabelas)):
            return
        t = self.tabelas[i]
        self._nome_salvo = t["nome"]
        self.nome.setText(t["nome"])
        self.moeda.setText(t.get("moeda", ""))
        self.moeda_dados.setText(t.get("moeda_dados", ""))
        self.tabela.setRowCount(0)
        for l in t.get("linhas", []):
            self._mais_linha(l)

    def _nome_livre(self, base):
        nomes = {t["nome"].casefold() for t in self.tabelas}
        nome, k = base, 2
        while nome.casefold() in nomes:
            nome, k = f"{base} {k}", k + 1
        return nome

    def _nova(self):
        nome, ok = QInputDialog.getText(self, "Nova tabela", "Nome da tabela:",
                                        text=self._nome_livre("Nova tabela"))
        if not ok or not nome.strip():
            return
        t = T.tabela_vazia(self._nome_livre(nome.strip()))
        T.salvar(t)
        self.tabelas.append(t)
        self._recarregar_lista()
        self.lista.setCurrentRow(len(self.tabelas) - 1)

    def _duplicar(self):
        if not (0 <= self.atual < len(self.tabelas)):
            return
        self._salvar_atual(silencioso=True)
        t = copy.deepcopy(self.tabelas[self.atual])
        t["nome"] = self._nome_livre(t["nome"] + " (cópia)")
        T.salvar(t)
        self.tabelas.append(t)
        self._recarregar_lista()
        self.lista.setCurrentRow(len(self.tabelas) - 1)

    def _apagar(self):
        if not (0 <= self.atual < len(self.tabelas)):
            return
        t = self.tabelas[self.atual]
        if QMessageBox.question(self, "Apagar tabela", f"Apagar a tabela “{t['nome']}”?\n"
                                "(Baús que já usam ela continuam com a cópia deles.)") \
                != QMessageBox.StandardButton.Yes:
            return
        T.apagar(t["nome"])
        del self.tabelas[self.atual]
        self.atual = -1
        self._recarregar_lista()
        self.lista.setCurrentRow(min(len(self.tabelas) - 1, 0) if self.tabelas else -1)
        self.editor.setEnabled(bool(self.tabelas))

    # ------------------------------------------------------------ linhas
    def _mais_linha(self, l=None):
        l = l if isinstance(l, dict) else {"nome": "", "qtd": "1", "chance": "comum", "desc": ""}
        r = self.tabela.rowCount()
        self.tabela.insertRow(r)
        self.tabela.setItem(r, 0, QTableWidgetItem(l.get("nome", "")))
        self.tabela.setItem(r, 1, QTableWidgetItem(str(l.get("qtd", "1"))))
        cb = QComboBox()
        for c in T.CHANCES:
            cb.addItem(c, c)
        cb.setCurrentIndex(max(0, cb.findData(l.get("chance", "comum"))))
        self.tabela.setCellWidget(r, 2, cb)
        self.tabela.setItem(r, 3, QTableWidgetItem(l.get("desc", "")))
        if not l.get("nome"):
            self.tabela.setCurrentCell(r, 0)
            self.tabela.editItem(self.tabela.item(r, 0))

    def _menos_linha(self):
        r = self.tabela.currentRow()
        if r >= 0:
            self.tabela.removeRow(r)

    def _linhas(self) -> list[dict]:
        saida = []
        for r in range(self.tabela.rowCount()):
            nome = (self.tabela.item(r, 0).text() if self.tabela.item(r, 0) else "").strip()
            if not nome:
                continue
            saida.append({"nome": nome,
                          "qtd": (self.tabela.item(r, 1).text() if self.tabela.item(r, 1) else "1").strip() or "1",
                          "chance": self.tabela.cellWidget(r, 2).currentData(),
                          "desc": (self.tabela.item(r, 3).text() if self.tabela.item(r, 3) else "").strip()})
        return saida

    def _colar(self):
        d = DialogoColar(self)
        if not d.exec():
            return
        novas = T.ler_texto(d.texto.toPlainText())
        if d.modo.currentData() == "trocar":
            self.tabela.setRowCount(0)
        for l in novas:
            self._mais_linha(l)
        self.resultado.setText(f"✔ {len(novas)} item(ns) adicionados. Confira as chances e salve.")

    def _testar(self):
        from ..jogo.sorteio import config_padrao, sortear
        t = self._tabela_editada()
        cfg = dict(config_padrao(), vazio=0, itens_min=1, itens_max=3, tabela=t)
        exemplos = [sortear(cfg)[1] for _ in range(3)]
        self.resultado.setText("<b>Exemplos (1 a 3 itens):</b><br>• " + "<br>• ".join(exemplos))

    def _tabela_editada(self) -> dict:
        return {"nome": self.nome.text().strip() or "Tabela", "moeda": self.moeda.text().strip(),
                "moeda_dados": self.moeda_dados.text().strip(), "linhas": self._linhas()}

    def _salvar_atual(self, silencioso=False):
        if not (0 <= self.atual < len(self.tabelas)):
            return
        t = self._tabela_editada()
        outros = {x["nome"].casefold() for k, x in enumerate(self.tabelas) if k != self.atual}
        if t["nome"].casefold() in outros:
            t["nome"] = self._nome_livre(t["nome"])
            self.nome.setText(t["nome"])
        T.salvar(t, self._nome_salvo)
        self._nome_salvo = t["nome"]
        self.tabelas[self.atual] = t
        linha = self.atual
        self._recarregar_lista()
        self.lista.blockSignals(True)
        self.lista.setCurrentRow(linha)
        self.lista.blockSignals(False)
        if not silencioso:
            self.resultado.setText(f"💾 “{t['nome']}” salva ({len(t['linhas'])} itens).")

    def accept(self):
        self._salvar_atual(silencioso=True)
        super().accept()

    def nome_atual(self) -> str:
        return self.tabelas[self.atual]["nome"] if 0 <= self.atual < len(self.tabelas) else ""
