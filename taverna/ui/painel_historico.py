"""
Histórico: tudo o que os JOGADORES fizeram (entrar/sair, mover, rolar dados, pingar,
tentar mover fora da vez...). Só o mestre vê; o que o mestre faz não aparece pra ninguém.
"""

import html
import time

from PyQt6.QtCore import QPointF, QUrl, pyqtSignal
from PyQt6.QtWidgets import (QCheckBox, QFileDialog, QHBoxLayout, QLineEdit, QPushButton,
                             QTextBrowser, QVBoxLayout, QWidget)

from .painel_dados import cor_do_nome


class PainelHistorico(QWidget):
    ir_para = pyqtSignal(QPointF)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.entradas: list[dict] = []
        self.filtro = QLineEdit()
        self.filtro.setPlaceholderText("Filtrar (nome ou ação)…")
        self.filtro.setClearButtonEnabled(True)
        self.filtro.textChanged.connect(self._redesenhar)
        self.so_avisos = QCheckBox("só ⚠")
        self.so_avisos.setToolTip("Mostrar só as tentativas recusadas (fora da vez, além do deslocamento…)")
        self.so_avisos.toggled.connect(self._redesenhar)
        topo = QHBoxLayout()
        topo.addWidget(self.filtro, 1)
        topo.addWidget(self.so_avisos)

        self.texto = QTextBrowser()
        self.texto.setOpenLinks(False)
        self.texto.anchorClicked.connect(self._link)

        salvar = QPushButton("💾 Salvar .txt")
        salvar.clicked.connect(self._salvar)
        limpar = QPushButton("Limpar")
        limpar.clicked.connect(self._limpar)
        baixo = QHBoxLayout()
        baixo.addWidget(salvar)
        baixo.addWidget(limpar)
        baixo.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addLayout(topo)
        layout.addWidget(self.texto, 1)
        layout.addLayout(baixo)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def adicionar(self, e: dict):
        self.entradas.append(e)
        if len(self.entradas) > 3000:
            self.entradas = self.entradas[-3000:]
        if self._passa(e):
            self.texto.append(self._linha(e))
            barra = self.texto.verticalScrollBar()
            barra.setValue(barra.maximum())

    def _passa(self, e):
        if self.so_avisos.isChecked() and e.get("icone") != "⚠":
            return False
        termo = self.filtro.text().strip().casefold()
        return not termo or termo in f"{e['quem']} {e['texto']}".casefold()

    @staticmethod
    def _linha(e):
        ir = ""
        if e.get("pos"):
            x, y = e["pos"]
            ir = f" <a href='ir:{x:.0f},{y:.0f}' style='color:#8a7a62'>[ver]</a>"
        cor_texto = "#e07a5f" if e.get("icone") == "⚠" else "#d8ccb4"
        return (f"<p style='margin:2px 0'><span style='color:#7a6a52'>{e['hora']}</span> "
                f"{e.get('icone', '•')} <b style='color:{cor_do_nome(e['quem'])}'>"
                f"{html.escape(e['quem'])}</b> <span style='color:{cor_texto}'>"
                f"{html.escape(e['texto'])}</span>{ir}</p>")

    def _redesenhar(self):
        self.texto.setHtml("".join(self._linha(e) for e in self.entradas if self._passa(e)))
        barra = self.texto.verticalScrollBar()
        barra.setValue(barra.maximum())

    def _link(self, url: QUrl):
        texto = url.toString()
        if texto.startswith("ir:"):
            x, y = texto[3:].split(",")
            self.ir_para.emit(QPointF(float(x), float(y)))

    def _limpar(self):
        self.entradas.clear()
        self.texto.clear()

    def _salvar(self):
        nome = time.strftime("historico_%Y-%m-%d_%H-%M.txt")
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar histórico", nome, "Texto (*.txt)")
        if not caminho:
            return
        with open(caminho, "w", encoding="utf-8") as f:
            for e in self.entradas:
                f.write(f"{e['hora']}  {e['quem']}: {e['texto']}\n")
