"""
💬 Chat da mesa (mestre e jogadores).

- Mensagem pra todos ou 🤫 sussurro (só pra uma pessoa). O mestre vê todos os sussurros.
- O mestre pode "falar como" um NPC (aparece o nome do NPC).
- As rolagens de dado aparecem no chat também. "/r 1d20+5" rola direto pelo chat.
- Quem entra depois recebe as últimas mensagens que podia ver.
"""

import html
import re

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextBrowser,
                             QVBoxLayout, QWidget)

from .painel_dados import cor_do_nome


def _texto_html(t: str) -> str:
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", t)
    return t.replace("\n", "<br>")


class PainelChat(QWidget):
    enviar = pyqtSignal(str, object, str)   # texto, para (None = todos), como (NPC, só mestre)
    nova_mensagem = pyqtSignal(dict)        # pra janela avisar quando o painel está fechado

    def __init__(self, mestre: bool, meu_nome: str = "", parent=None):
        super().__init__(parent)
        self.mestre = mestre
        self.meu_nome = meu_nome
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(5)
        self.log = QTextBrowser()
        self.log.setOpenLinks(False)
        self.log.setMinimumHeight(140)
        lay.addWidget(self.log, 1)
        linha = QHBoxLayout()
        linha.addWidget(QLabel("Para"))
        self.para = QComboBox()
        self.para.setToolTip("Todos, ou 🤫 sussurro pra uma pessoa só")
        linha.addWidget(self.para, 1)
        if mestre:
            linha.addWidget(QLabel("como"))
            self.como = QComboBox()
            self.como.setEditable(True)
            self.como.setToolTip("Falar como um NPC (escreva o nome ou escolha um token)")
            self.como.addItem("Mestre", "")
            linha.addWidget(self.como, 1)
        else:
            self.como = None
        lay.addLayout(linha)
        linha = QHBoxLayout()
        self.campo = QLineEdit()
        self.campo.setPlaceholderText("Escreva e aperte Enter…  (/r 1d20+5 rola o dado)")
        self.campo.setMaxLength(1000)
        self.campo.returnPressed.connect(self._enviar)
        linha.addWidget(self.campo, 1)
        b = QPushButton("Enviar")
        b.setObjectName("primario")
        b.clicked.connect(self._enviar)
        linha.addWidget(b)
        lay.addLayout(linha)
        self.definir_destinos([])
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    # ------------------------------------------------------------ destinos
    def definir_destinos(self, nomes: list[str]):
        atual = self.para.currentData()
        self.para.blockSignals(True)
        self.para.clear()
        from .acabamento import adicionar_item
        adicionar_item(self.para, "💬 Todos", None)
        if not self.mestre:
            adicionar_item(self.para, "🤫 Mestre (sussurro)", "Mestre")
        for n in nomes:
            if self.meu_nome and n.casefold() == self.meu_nome.casefold():
                continue
            adicionar_item(self.para, f"🤫 {n} (sussurro)", n)
        i = self.para.findData(atual)
        self.para.setCurrentIndex(i if i >= 0 else 0)
        self.para.blockSignals(False)

    def definir_npcs(self, nomes: list[str]):
        if self.como is None:
            return
        atual = self.como.currentText()
        self.como.blockSignals(True)
        self.como.clear()
        self.como.addItem("Mestre", "")
        for n in sorted(set(nomes), key=str.casefold):
            self.como.addItem(n, n)
        from ..idioma import t
        self.como.setCurrentText(atual or t("Mestre"))
        self.como.blockSignals(False)

    # ------------------------------------------------------------ enviar / mostrar
    def _enviar(self):
        texto = self.campo.text().strip()
        if not texto:
            return
        como = ""
        if self.como is not None:
            como = self.como.currentText().strip()
            from ..idioma import t
            como = "" if como in ("", "Mestre", t("Mestre")) else como
        self.enviar.emit(texto, self.para.currentData(), como)
        self.campo.clear()

    def _rolar(self):
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def adicionar(self, m: dict, avisar: bool = True):
        de = m.get("de", "?")
        como = m.get("como") or ""
        nome = f"{como} <span style='color:#8a7a62'>(Mestre)</span>" if como else html.escape(de)
        cor = cor_do_nome(como or de)
        hora = html.escape(m.get("hora", ""))
        para = m.get("para")
        if para:
            alvo = "você" if self.meu_nome and para.casefold() == self.meu_nome.casefold() else html.escape(para)
            rotulo = f"🤫 <b style='color:{cor}'>{nome}</b> <span style='color:#b08ad8'>sussurrou pra {alvo}</span>"
            corpo = f"<i style='color:#9a7fd0'>{_texto_html(m.get('texto', ''))}</i>"
        else:
            rotulo = f"<b style='color:{cor}'>{nome}</b>"
            corpo = _texto_html(m.get("texto", ""))
        self.log.append(f"<p style='margin:3px 0'><span style='color:#7a6a52'>{hora}</span> {rotulo}: {corpo}</p>")
        self._rolar()
        if avisar:
            self.nova_mensagem.emit(m)

    def adicionar_rolagem(self, r: dict):
        import time
        quem = r.get("quem", "?")
        if r.get("privada") and not self.mestre:
            return
        motivo = r.get("motivo") or ""
        if motivo == "iniciativa" and r.get("token_nome"):
            motivo = f"iniciativa de {r['token_nome']}"
        extra = " ✨" if r.get("d20") == 20 else (" 💀" if r.get("d20") == 1 else "")
        priv = " 🔒" if r.get("privada") else ""
        self.log.append(
            f"<p style='margin:3px 0'><span style='color:#7a6a52'>{time.strftime('%H:%M')}</span> "
            f"🎲 <b style='color:{cor_do_nome(quem)}'>{html.escape(quem)}</b>{priv}"
            f"{(' · ' + html.escape(motivo)) if motivo else ''}: "
            f"<b style='font-size:12pt'>{r.get('total')}</b>{extra} "
            f"<span style='color:#8f8068'>({html.escape(r.get('expr', ''))})</span></p>")
        self._rolar()
