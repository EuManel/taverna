"""
🎒 Item coletável (v0.48, pedido do Manel): chave, poção, moedas, espada, lança, machado, imagem própria…
O jogador dá duplo clique (de perto) e o item vai DIRETO pro inventário; o objeto some do chão.

A janela do mestre é enxuta: nome, quantidade, descrição e imagem. Na CHAVE, só o que importa:
"Esta chave abre: [porta / baú]" (a porta/baú fica trancada e abre com ela).
"""

import base64

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QSpinBox,
                             QVBoxLayout)


def alvos_de_chave(cena) -> list:
    """[(rótulo, item)] das portas e objetos interativos (baús…) do cenário, pra chave abrir."""
    from ..config import CELULA
    from ..mesa.portas import PortaItem
    from ..mesa.props import PropItem
    saida = []
    for it in cena.items():
        try:
            if isinstance(it, PortaItem):
                p = it.scenePos()
            elif isinstance(it, PropItem) and it.interativo and not it.solto and it.tipo != "escada":
                p = it.centro_cena()
            else:
                continue
        except RuntimeError:
            continue
        rot = f"{'🚪' if isinstance(it, PortaItem) else '📦'} {it.nome}  ({p.x() / CELULA:.0f}, {p.y() / CELULA:.0f})"
        saida.append((rot, it))
    saida.sort(key=lambda r: r[0])
    return saida


class DialogoColetavel(QDialog):
    def __init__(self, prop, parent=None):
        super().__init__(parent)
        self.prop = prop
        if not prop.itens:
            from ..mesa.props import novo_id_item
            prop.itens = [{"id": novo_id_item(), "nome": prop.nome, "qtd": 1, "desc": "", "img": None}]
        self.item = dict(prop.itens[0])
        self.eh_chave = prop.tipo == "chave"
        self.setWindowTitle("🗝 Chave" if self.eh_chave else "🎒 Item coletável")
        self.setMinimumWidth(420)

        self.nome = QLineEdit(self.item.get("nome") or prop.nome)
        self.qtd = QSpinBox()
        self.qtd.setRange(1, 99999)
        self.qtd.setValue(int(self.item.get("qtd") or 1))
        self.desc = QPlainTextEdit(self.item.get("desc") or "")
        self.desc.setPlaceholderText("O que o jogador lê no inventário (opcional)")
        self.desc.setFixedHeight(70)
        self.preview = QLabel()
        self.preview.setFixedSize(56, 56)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imagem = prop.imagem
        b_img = QPushButton("📥 Importar imagem…")
        b_img.setToolTip("A imagem aparece no chão (no lugar do desenho) e no inventário do jogador.")
        b_img.clicked.connect(self._importar)
        b_tira = QPushButton("Usar o desenho")
        b_tira.clicked.connect(self._tirar_imagem)
        linha_img = QHBoxLayout()
        linha_img.addWidget(self.preview)
        linha_img.addWidget(b_img)
        linha_img.addWidget(b_tira)
        linha_img.addStretch()

        form = QFormLayout()
        form.addRow("Nome", self.nome)
        self.cb_abre = QComboBox()
        self.ck_gasta = QCheckBox("A chave some ao usar")
        if self.eh_chave:
            self.cb_abre.addItem("— nada ainda —", None)
            atual = None
            for rot, alvo in alvos_de_chave(prop.scene()) if prop.scene() is not None else []:
                self.cb_abre.addItem(rot, alvo)
                if (getattr(alvo, "chave", "") or "").strip().casefold() == self.nome.text().strip().casefold():
                    atual = self.cb_abre.count() - 1
                    self.ck_gasta.setChecked(bool(getattr(alvo, "gasta_chave", False)))
            if atual is not None:
                self.cb_abre.setCurrentIndex(atual)
            self._alvo_antes = self.cb_abre.currentData()
            form.addRow("Esta chave abre", self.cb_abre)
            form.addRow("", self.ck_gasta)
        else:
            form.addRow("Quantidade", self.qtd)
            form.addRow("Descrição", self.desc)
        form.addRow("Imagem", linha_img)
        dica = QLabel("O jogador dá duplo clique no item (de perto) e ele vai direto pro inventário."
                      + (" A porta/baú escolhido fica trancado e abre com esta chave." if self.eh_chave else ""))
        dica.setWordWrap(True)
        dica.setObjectName("dica")
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(self._ok)
        botoes.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(dica)
        lay.addWidget(botoes)
        self._atualizar_preview()
        from .acabamento import iconizar
        iconizar(self)

    def _atualizar_preview(self):
        pm = QPixmap()
        if self.imagem:
            pm.loadFromData(self.imagem)
        else:
            from ..mesa.props import desenhar_miniatura
            try:
                pm = desenhar_miniatura(self.prop.tipo, 56)
            except (KeyError, ValueError):
                pm = QPixmap()
        if not pm.isNull():
            self.preview.setPixmap(pm.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation))

    def _importar(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Imagem do item", "", "Imagens (*.png *.jpg *.jpeg *.webp)")
        if not caminho:
            return
        from .dialogos import reduzir_imagem
        with open(caminho, "rb") as f:
            self.imagem = reduzir_imagem(f.read(), 512)
        self._atualizar_preview()

    def _tirar_imagem(self):
        self.imagem = None
        self._atualizar_preview()

    def _ok(self):
        p = self.prop
        nome = self.nome.text().strip() or p.nome
        p.nome = nome
        if self.imagem != p.imagem:
            p.definir_imagem(self.imagem)
        item = dict(self.item, nome=nome, qtd=1 if self.eh_chave else self.qtd.value(),
                    desc=self.desc.toPlainText().strip(),
                    img=base64.b64encode(self.imagem).decode() if self.imagem else self.item.get("img"))
        if self.eh_chave:
            alvo = self.cb_abre.currentData()
            antes = self._alvo_antes
            if antes is not None and antes is not alvo:   # deixou de abrir o de antes
                antes.chave = ""
            if alvo is not None:
                alvo.chave = nome
                alvo.gasta_chave = self.ck_gasta.isChecked()
                if hasattr(alvo, "trancada"):
                    alvo.trancada = True
                    if getattr(alvo, "aberta", False):
                        alvo.alternar()
                    alvo.mudou()
                else:
                    alvo.trancado = True
                    alvo._mudou()
                item["desc"] = f"Abre: {alvo.nome}"
        p.itens = [item]
        p.interativo, p.solto = True, True
        p.update()
        p._mudou()
        self.accept()
