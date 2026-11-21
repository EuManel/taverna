"""
Painel de dados: rolar (2d6+3, d20, vantagem...) e o histórico de rolagens da mesa.

- Player: toda rolagem é pública (todo mundo vê).
- Mestre: pode marcar "🔒 Privada" (só ele vê).
As rolagens acontecem no computador do mestre, então ninguém trapaceia.
"""

import html
import time

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QCheckBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTextBrowser, QVBoxLayout, QWidget)

CORES_NOMES = ["#e0b452", "#7fc4e8", "#9fd68a", "#e889a8", "#c9a0ff", "#f0a060", "#7fe0c8"]


def cor_do_nome(nome: str) -> str:
    if nome == "Mestre":
        return "#d9534f"
    import zlib
    cor = CORES_NOMES[zlib.crc32(nome.casefold().encode()) % len(CORES_NOMES)]
    from .tema import eh_claro
    if eh_claro():   # no tema claro, os tons pastel somem no papel: escurece
        from PyQt6.QtGui import QColor
        return QColor(cor).darker(190).name()
    return cor


class PainelDados(QWidget):
    pedir_rolagem = pyqtSignal(str, bool)   # expressão, privada
    pedir_pronta = pyqtSignal(str, str, bool)   # expressão, nome (motivo), privada — rolagem pronta

    def __init__(self, mestre: bool, parent=None):
        super().__init__(parent)
        self.mestre = mestre

        self.expr = QLineEdit()
        self.expr.setPlaceholderText("ex.: 1d20+5 · 2d6+3 · 4d6kh3")
        self.expr.returnPressed.connect(self._rolar_texto)
        rolar = QPushButton("🎲 Rolar")
        rolar.setObjectName("primario")
        rolar.clicked.connect(self._rolar_texto)
        meus = QPushButton("🎨")
        meus.setToolTip("Meus dados: material e cores dos SEUS dados 3D (todo mundo vê do seu jeito)")
        meus.clicked.connect(self.abrir_meus_dados)
        linha = QHBoxLayout()
        linha.addWidget(self.expr, 1)
        linha.addWidget(rolar)
        linha.addWidget(meus)

        grade = QGridLayout()
        grade.setSpacing(4)
        for k, lados in enumerate((4, 6, 8, 10, 12, 20, 100)):
            b = QPushButton(f"d{lados}")
            b.setToolTip(f"Rolar 1d{lados} (+ o modificador digitado, se tiver)")
            b.clicked.connect(lambda _=False, n=lados: self._rolar_dado(n))
            grade.addWidget(b, 0, k)
        van = QPushButton("Vantagem")
        van.setToolTip("2d20, fica com o maior (+ modificador)")
        van.clicked.connect(lambda: self._rolar_d20("kh1"))
        des = QPushButton("Desvantagem")
        des.setToolTip("2d20, fica com o menor (+ modificador)")
        des.clicked.connect(lambda: self._rolar_d20("kl1"))
        grade.addWidget(van, 1, 0, 1, 4)
        grade.addWidget(des, 1, 4, 1, 3)

        self.privada = QCheckBox("🔒 Rolagem privada (só eu vejo)")
        self.privada.setVisible(mestre)
        self.privada.setToolTip("Os jogadores não ficam sabendo dessa rolagem")

        self.historico = QTextBrowser()
        self.historico.setOpenLinks(False)
        self.historico.setMinimumHeight(120)
        self.erro = QLabel()
        self.erro.setObjectName("dica")
        self.erro.setStyleSheet("color: #e07a5f;")
        self.erro.hide()
        dica = QLabel("Dica: escreva só o modificador (ex.: +5) e clique num dado."
                      + ("" if mestre else "\nSuas rolagens são vistas por todos."))
        dica.setObjectName("dica")
        dica.setWordWrap(True)

        # ⚡ Rolagens prontas (cada um cria as suas e elas ficam salvas no PC)
        self.titulo_prontas = QLabel("<b>⚡ Rolagens prontas</b>")
        self.grade_prontas = QGridLayout()
        self.grade_prontas.setSpacing(4)
        nova = QPushButton("＋ Salvar rolagem")
        nova.setToolTip("Cria um botão pra uma rolagem que você usa sempre (ex.: Ataque com espada: 1d20+5)")
        nova.clicked.connect(lambda: self._editar_pronta(None))
        linha_p = QHBoxLayout()
        linha_p.addWidget(self.titulo_prontas)
        linha_p.addStretch(1)
        linha_p.addWidget(nova)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addLayout(linha)
        layout.addLayout(grade)
        layout.addLayout(linha_p)
        layout.addLayout(self.grade_prontas)
        layout.addWidget(self.privada)
        layout.addWidget(self.erro)
        layout.addWidget(self.historico, 1)
        layout.addWidget(dica)

        self._recarregar_prontas()
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def abrir_meus_dados(self):
        """(v0.74) 🎨 Escolher a cara dos MEUS dados."""
        from .dialogo_meus_dados import DialogoMeusDados
        return DialogoMeusDados(self).exec()

    # ------------------------------------------------------------ rolagens prontas
    def _cfg(self):
        from PyQt6.QtCore import QSettings
        return QSettings("Taverna", "Mestre" if self.mestre else "Player")

    def prontas(self) -> list[dict]:
        v = self._cfg().value("rolagens_prontas", []) or []
        return [dict(x) for x in v if isinstance(x, dict) and x.get("expr")]

    def _salvar_prontas(self, lista):
        self._cfg().setValue("rolagens_prontas", lista)
        self._recarregar_prontas()

    def _recarregar_prontas(self):
        while self.grade_prontas.count():
            w = self.grade_prontas.takeAt(0).widget()
            if w is not None:
                w.deleteLater()
        lista = self.prontas()
        for k, p in enumerate(lista):
            b = QPushButton(p["nome"])
            b.setToolTip(f"{p['expr']}  ·  botão direito: editar / apagar")
            b.clicked.connect(lambda _=False, p=p: self.pedir_pronta.emit(
                p["expr"], p["nome"][:40], self.mestre and self.privada.isChecked()))
            b.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            b.customContextMenuRequested.connect(lambda _pos, k=k, b=b: self._menu_pronta(k, b))
            self.grade_prontas.addWidget(b, k // 2, k % 2)
        self.titulo_prontas.setToolTip("" if lista else "Clique em ＋ pra criar a primeira")
        if not lista:
            vazio = QLabel("Nenhuma ainda. Ex.: “Ataque com espada” = 1d20+5")
            vazio.setObjectName("dica")
            self.grade_prontas.addWidget(vazio, 0, 0, 1, 2)

    def _menu_pronta(self, k, botao):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.addAction("✏ Editar…", lambda: self._editar_pronta(k))
        menu.addAction("◀ Mover pra trás", lambda: self._mover_pronta(k, -1))
        menu.addAction("▶ Mover pra frente", lambda: self._mover_pronta(k, +1))
        menu.addSeparator()
        menu.addAction("🗑 Apagar", lambda: self._apagar_pronta(k))
        from .acabamento import iconizar_menu
        iconizar_menu(menu).exec(botao.mapToGlobal(botao.rect().bottomLeft()))

    def _mover_pronta(self, k, d):
        lista = self.prontas()
        j = k + d
        if 0 <= j < len(lista):
            lista[k], lista[j] = lista[j], lista[k]
            self._salvar_prontas(lista)

    def _apagar_pronta(self, k):
        lista = self.prontas()
        if 0 <= k < len(lista):
            del lista[k]
            self._salvar_prontas(lista)

    def _editar_pronta(self, k):
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout
        from ..jogo.dados import ErroDados, rolar
        lista = self.prontas()
        atual = lista[k] if k is not None and 0 <= k < len(lista) else \
            {"nome": "", "expr": self.expr.text().strip()}
        dlg = QDialog(self)
        dlg.setWindowTitle("Rolagem pronta")
        form = QFormLayout(dlg)
        nome = QLineEdit(atual["nome"])
        nome.setPlaceholderText("ex.: Ataque com espada, Furtividade, Bola de fogo")
        expr = QLineEdit(atual["expr"])
        expr.setPlaceholderText("ex.: 1d20+5 · 2d6+3 · 8d6 · 2d20kh1+4")
        aviso = QLabel()
        aviso.setStyleSheet("color: #e07a5f;")
        form.addRow("Nome", nome)
        form.addRow("Rolagem", expr)
        form.addRow(aviso)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        form.addRow(botoes)

        def ok():
            try:
                rolar(expr.text())
            except ErroDados as e:
                aviso.setText(str(e))
                return
            if not nome.text().strip():
                aviso.setText("Dê um nome pra rolagem.")
                return
            dlg.accept()
        botoes.accepted.connect(ok)
        botoes.rejected.connect(dlg.reject)
        if dlg.exec():
            novo = {"nome": nome.text().strip()[:40], "expr": expr.text().strip()}
            if k is not None and 0 <= k < len(lista):
                lista[k] = novo
            else:
                lista.append(novo)
            self._salvar_prontas(lista)

    # ------------------------------------------------------------ montar a expressão
    def _modificador(self) -> str:
        """Se o campo só tem um modificador (+5, -1), usa ele junto do dado clicado."""
        t = self.expr.text().replace(" ", "")
        if t and t[0] in "+-" and t[1:].isdigit():
            return t
        if t.isdigit():
            return "+" + t
        return ""

    def _rolar_texto(self):
        t = self.expr.text().strip()
        if t:
            self._pedir(t)

    def _rolar_dado(self, lados):
        self._pedir(f"1d{lados}{self._modificador()}")

    def _rolar_d20(self, modo):
        self._pedir(f"2d20{modo}{self._modificador()}")

    def _pedir(self, expr):
        self.erro.hide()
        self.pedir_rolagem.emit(expr, self.mestre and self.privada.isChecked())

    def mostrar_erro(self, texto):
        self.erro.setText(texto)
        self.erro.show()

    # ------------------------------------------------------------ histórico
    def adicionar(self, r: dict):
        quem = r.get("quem", "?")
        cor = cor_do_nome(quem)
        hora = time.strftime("%H:%M")
        motivo = r.get("motivo", "")
        if motivo == "iniciativa":
            motivo_txt = f" · iniciativa{(' de ' + html.escape(r['token_nome'])) if r.get('token_nome') else ''}"
        else:
            motivo_txt = f" · {html.escape(motivo)}" if motivo else ""
        especial = ""
        if r.get("d20") == 20:
            especial = " <span style='color:#d9a400'>✨ 20 natural!</span>"
        elif r.get("d20") == 1:
            especial = " <span style='color:#e05a4a'>💀 1 natural</span>"
        privada = " <span style='color:#8a7a62'>🔒 privada</span>" if r.get("privada") else ""
        self.historico.append(
            f"<p style='margin:4px 0'><span style='color:#7a6a52'>{hora}</span> "
            f"<b style='color:{cor}'>{html.escape(quem)}</b>{privada}{motivo_txt}<br>"
            f"<span style='font-size:15pt; font-weight:bold'>{r.get('total')}</span>"
            f"&nbsp; <span style='color:#8f8068'>{html.escape(r.get('expr', ''))} → "
            f"{html.escape(r.get('detalhes', ''))}</span>{especial}</p>")
        barra = self.historico.verticalScrollBar()
        barra.setValue(barra.maximum())
