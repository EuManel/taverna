"""
Editor de gatilho/armadilha: nome, quando dispara, uma vez ou sempre, e a lista de ações.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
                             QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu,
                             QPlainTextEdit, QPushButton, QSpinBox, QToolButton, QVBoxLayout)

from ..jogo.condicoes import CONDICOES
from ..jogo.gatilhos import QUANDO, TIPOS_ACAO, copia, descrever_acao


def _itens_da_cena(cena):
    from ..mesa.luzes import LuzItem
    from ..mesa.portas import PortaItem
    from ..mesa.props import PropItem
    from ..mesa.token import TokenItem
    itens = cena.itens_do_usuario()
    return {
        "portas": [i for i in itens if isinstance(i, PortaItem)],
        "luzes": [i for i in itens if isinstance(i, LuzItem) or (isinstance(i, PropItem) and i.luz)],
        "coisas": [i for i in itens if isinstance(i, (TokenItem, PropItem))],
    }


def _nome(i):
    from ..mesa.portas import PortaItem
    nome = getattr(i, "nome", "?")
    if isinstance(i, PortaItem):
        nome = f"{nome} ({'aberta' if i.aberta else 'fechada'})"
    if not i.isVisible():
        nome += "  [escondido]"
    return nome


class DialogoAcao(QDialog):
    def __init__(self, acao: dict, cena, parent=None):
        super().__init__(parent)
        self.acao = dict(acao)
        t = self.acao["tipo"]
        self.setWindowTitle(TIPOS_ACAO.get(t, t))
        form = QFormLayout()
        self.lista = None
        if t == "mensagem":
            self.texto = QPlainTextEdit(self.acao.get("texto", ""))
            self.texto.setPlaceholderText("ex.: Um clique… e o chão se abre sob seus pés!")
            self.para = QComboBox()
            self.para.addItem("Só pra quem disparou", "quem")
            self.para.addItem("Pra todos os jogadores", "todos")
            self.para.setCurrentIndex(max(0, self.para.findData(self.acao.get("para", "quem"))))
            form.addRow("Texto", self.texto)
            form.addRow("Pra quem", self.para)
        elif t == "dano":
            self.expr = QLineEdit(self.acao.get("expr", "2d6"))
            self.expr.setPlaceholderText("ex.: 2d6, 1d10+2 (vazio = sem dano)")
            self.cond = QComboBox()
            self.cond.addItem("— nenhuma —", "")
            from .icones import icone_tema
            for chave, (nome, _emoji) in CONDICOES.items():
                self.cond.addItem(icone_tema(f"cond_{chave}"), nome, chave)
            self.cond.setCurrentIndex(max(0, self.cond.findData(self.acao.get("condicao", ""))))
            self.rodadas = QSpinBox()
            self.rodadas.setRange(0, 999)
            self.rodadas.setSpecialValueText("sem duração")
            self.rodadas.setValue(int(self.acao.get("rodadas", 0) or 0))
            form.addRow("Dano", self.expr)
            form.addRow("Condição", self.cond)
            form.addRow("Por (rodadas)", self.rodadas)
            dica = QLabel("A rolagem aparece pra todos. Se o PV chegar a 0, ele cai (✚).")
            dica.setObjectName("dica")
            form.addRow(dica)
        elif t in ("porta", "luz", "revelar", "esconder"):
            grupos = _itens_da_cena(cena)
            chave = {"porta": "portas", "luz": "luzes"}.get(t, "coisas")
            if t in ("porta", "luz"):
                self.estado = QComboBox()
                opcoes = (("fechar", "Fechar"), ("trancar", "Fechar e TRANCAR"), ("destrancar", "Destrancar"),
                          ("abrir", "Abrir"), ("alternar", "Inverter")) if t == "porta" else \
                    (("apagar", "Apagar"), ("acender", "Acender"), ("alternar", "Inverter"))
                for v, n in opcoes:
                    self.estado.addItem(n, v)
                self.estado.setCurrentIndex(max(0, self.estado.findData(self.acao.get("estado", opcoes[0][0]))))
                form.addRow("Fazer", self.estado)
            self.todas = None
            if t == "luz":
                self.todas = QCheckBox("Todas as luzes do cenário")
                self.todas.setChecked(self.acao.get("ids") == "todas")
                form.addRow(self.todas)
            self.lista = QListWidget()
            marcados = set(self.acao.get("ids") or []) if isinstance(self.acao.get("ids"), list) else set()
            itens = grupos[chave]
            if t == "revelar":
                itens = sorted(itens, key=lambda i: i.isVisible())   # escondidos primeiro
            for i in itens:
                li = QListWidgetItem(_nome(i))
                li.setData(Qt.ItemDataRole.UserRole, i.uid)
                li.setFlags(li.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                li.setCheckState(Qt.CheckState.Checked if i.uid in marcados else Qt.CheckState.Unchecked)
                self.lista.addItem(li)
            if not itens:
                self.lista.addItem("(nada desse tipo neste cenário)")
            if self.todas is not None:
                self.todas.toggled.connect(lambda v: self.lista.setEnabled(not v))
                self.lista.setEnabled(not self.todas.isChecked())
            dica = {"revelar": "Dica: esconda os monstros antes (olhinho na lista de camadas) e marque aqui.",
                    "esconder": "O que some quando a armadilha dispara.",
                    "porta": "Marque as portas.", "luz": "Marque as luzes (ou todas)."}[t]
            d = QLabel(dica)
            d.setObjectName("dica")
            d.setWordWrap(True)
            form.addRow(self.lista)
            form.addRow(d)
        elif t == "ambiente":
            from ..mesa.luzes import AMBIENTES
            self.valor = QComboBox()
            for k, (n, _) in AMBIENTES.items():
                self.valor.addItem(n, k)
            self.valor.setCurrentIndex(max(0, self.valor.findData(self.acao.get("valor", "escuro"))))
            form.addRow("Luz ambiente", self.valor)
        elif t == "impacto":
            from PyQt6.QtWidgets import QDoubleSpinBox
            from ..mesa.impactos import IMPACTOS
            self.valor = QComboBox()
            for k, (n, _pos, _d) in IMPACTOS.items():
                self.valor.addItem(n, k)
            self.valor.setCurrentIndex(max(0, self.valor.findData(self.acao.get("efeito", "explosao"))))
            self.tam = QDoubleSpinBox()
            self.tam.setRange(1, 20)
            self.tam.setSingleStep(1.5)
            self.tam.setSuffix(" m")
            self.tam.setValue(float(self.acao.get("tam", 3.0)))
            form.addRow("Efeito", self.valor)
            form.addRow("Tamanho", self.tam)
            form.addRow(QLabel("Acontece no lugar da armadilha, na tela de todo mundo\n(a explosão treme a tela, o raio clareia…)."))
        else:
            form.addRow(QLabel("Um sinal pulsando no lugar, pra todo mundo ver."))
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(botoes)
        self.resize(440, 420 if self.lista is not None else 220)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def resultado(self) -> dict:
        a = self.acao
        t = a["tipo"]
        if t == "mensagem":
            a.update(texto=self.texto.toPlainText().strip(), para=self.para.currentData())
        elif t == "dano":
            a.update(expr=self.expr.text().strip(), condicao=self.cond.currentData(), rodadas=self.rodadas.value())
        elif t in ("porta", "luz", "revelar", "esconder"):
            if t in ("porta", "luz"):
                a["estado"] = self.estado.currentData()
            if getattr(self, "todas", None) is not None and self.todas.isChecked():
                a["ids"] = "todas"
            else:
                a["ids"] = [self.lista.item(k).data(Qt.ItemDataRole.UserRole) for k in range(self.lista.count())
                            if self.lista.item(k).data(Qt.ItemDataRole.UserRole)
                            and self.lista.item(k).checkState() == Qt.CheckState.Checked]
        elif t == "ambiente":
            a["valor"] = self.valor.currentData()
        elif t == "impacto":
            a["efeito"] = self.valor.currentData()
            a["tam"] = self.tam.value()
        return a


class DialogoGatilho(QDialog):
    def __init__(self, gatilho: dict, cena, origem: str = "prop", parent=None):
        super().__init__(parent)
        self.cena = cena
        self.g = copia(gatilho)
        self.setWindowTitle("⚡ Armadilha / gatilho")
        self.nome = QLineEdit(self.g.get("nome", ""))
        self.ativo = QCheckBox("Armada (ativa)")
        self.ativo.setChecked(self.g.get("ativo", True))
        self.uma_vez = QCheckBox("Dispara uma vez só")
        self.uma_vez.setChecked(self.g.get("uma_vez", True))
        self.quando = QComboBox()
        for k in (("abrir", "mover") if origem == "prop" else ("entrar",)):
            self.quando.addItem(QUANDO[k], k)
        self.quando.setCurrentIndex(max(0, self.quando.findData(self.g.get("quando"))))
        self.estado = QLabel()
        rearmar = QPushButton("Rearmar")
        rearmar.setToolTip("Marca como não disparada (pra disparar de novo)")
        rearmar.clicked.connect(lambda: (self.g.update(disparado=False), self._estado()))
        linha_estado = QHBoxLayout()
        linha_estado.addWidget(self.estado, 1)
        linha_estado.addWidget(rearmar)

        self.lista = QListWidget()
        self.lista.itemDoubleClicked.connect(lambda _: self._editar())
        add = QToolButton()
        add.setText("＋ Ação")
        add.setObjectName("primario")
        add.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(self)
        for tipo, texto in TIPOS_ACAO.items():
            a = QAction(texto, menu)
            a.triggered.connect(lambda _=False, t=tipo: self._adicionar(t))
            menu.addAction(a)
        add.setMenu(menu)
        editar = QPushButton("Editar")
        editar.clicked.connect(self._editar)
        remover = QPushButton("Remover")
        remover.clicked.connect(self._remover)
        linha = QHBoxLayout()
        linha.addWidget(add)
        linha.addWidget(editar)
        linha.addWidget(remover)
        linha.addStretch()

        form = QFormLayout()
        form.addRow("Nome", self.nome)
        form.addRow("Dispara", self.quando)
        form.addRow(self.ativo)
        form.addRow(self.uma_vez)
        form.addRow(linha_estado)
        dica = QLabel("Os jogadores não sabem que tem armadilha. Quando dispara, você é avisado e fica\n"
                      "no histórico. Clique direito no objeto/área → “Disparar agora” pra testar.")
        dica.setObjectName("dica")
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(QLabel("<b>O que acontece</b> (em ordem)"))
        lay.addWidget(self.lista, 1)
        lay.addLayout(linha)
        lay.addWidget(dica)
        lay.addWidget(botoes)
        self.resize(520, 560)
        self._recarregar()
        self._estado()
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def _estado(self):
        self.estado.setText("Já disparou." if self.g.get("disparado") else "Ainda não disparou.")

    def _nomes(self):
        return {i.uid: getattr(i, "nome", "?") for i in self.cena.itens_do_usuario() if hasattr(i, "uid")}

    def _recarregar(self):
        nomes = self._nomes()
        self.lista.clear()
        for a in self.g.get("acoes", []):
            self.lista.addItem(descrever_acao(a, nomes))
        if not self.g.get("acoes"):
            vazio = QListWidgetItem("(nenhuma ação — clique em ＋ Ação)")
            vazio.setFlags(Qt.ItemFlag.NoItemFlags)
            self.lista.addItem(vazio)

    def _adicionar(self, tipo):
        padrao = {"tipo": tipo}
        if tipo == "dano":
            padrao.update(expr="2d6")
        d = DialogoAcao(padrao, self.cena, self)
        if d.exec():
            self.g.setdefault("acoes", []).append(d.resultado())
            self._recarregar()

    def _editar(self):
        k = self.lista.currentRow()
        acoes = self.g.get("acoes", [])
        if 0 <= k < len(acoes):
            d = DialogoAcao(acoes[k], self.cena, self)
            if d.exec():
                acoes[k] = d.resultado()
                self._recarregar()

    def _remover(self):
        k = self.lista.currentRow()
        acoes = self.g.get("acoes", [])
        if 0 <= k < len(acoes):
            del acoes[k]
            self._recarregar()

    def resultado(self) -> dict:
        self.g.update(nome=self.nome.text().strip() or "Armadilha", ativo=self.ativo.isChecked(),
                      uma_vez=self.uma_vez.isChecked(), quando=self.quando.currentData())
        return self.g
