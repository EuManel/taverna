"""
Janela de leitura de um documento (bilhete, carta, página de diário, mapa do tesouro...).
O item tem "doc": {"texto": "...", "img": base64 ou None}.
"""

import base64
import html

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout,
                             QWidget)

PAPEL = ("QDialog { background: #e9dcc0; }"
         "QLabel { color: #2a1e12; background: transparent; }"
         "QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }"
         "QPushButton { background: #c9b48a; color: #2a1e12; border: 1px solid #7a6040; border-radius: 6px;"
         " padding: 6px 14px; } QPushButton:hover { background: #d8c49a; }")


def texto_em_html(texto: str) -> str:
    """Texto simples com um pouquinho de formatação: **negrito**, *itálico*, # título."""
    import re
    linhas = []
    for l in (texto or "").split("\n"):
        e = html.escape(l)
        e = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", e)
        e = re.sub(r"(?<!\*)\*(?!\s)(.+?)\*", r"<i>\1</i>", e)
        if e.startswith("# "):
            e = f"<h2 style='margin:6px 0'>{e[2:]}</h2>"
        linhas.append(e)
    return "<br>".join(linhas)


class JanelaLeitura(QDialog):
    pegar = pyqtSignal()

    def __init__(self, item: dict, pode_pegar: bool = False, parent=None):
        super().__init__(parent)
        self.setModal(False)
        self.setStyleSheet(PAPEL)
        doc = item.get("doc") or {}
        self.setWindowTitle(f"📜 {item.get('nome', 'Documento')}")
        titulo = QLabel(item.get("nome", "Documento"))
        titulo.setStyleSheet("font-family: Georgia; font-size: 17pt; font-weight: bold;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        corpo = QWidget()
        lc = QVBoxLayout(corpo)
        if doc.get("img"):
            pm = QPixmap()
            if pm.loadFromData(base64.b64decode(doc["img"])):
                img = QLabel()
                img.setAlignment(Qt.AlignmentFlag.AlignCenter)
                img.setPixmap(pm.scaled(620, 620, Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation))
                lc.addWidget(img)
        if doc.get("texto"):
            t = QLabel(texto_em_html(doc["texto"]))
            t.setTextFormat(Qt.TextFormat.RichText)
            t.setWordWrap(True)
            t.setStyleSheet("font-family: Georgia; font-size: 12.5pt; line-height: 140%;")
            t.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lc.addWidget(t)
        if not doc.get("img") and not doc.get("texto"):
            vazio = QLabel("<i>(A página está em branco.)</i>")
            vazio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lc.addWidget(vazio)
        lc.addStretch()
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setWidget(corpo)
        botoes = QHBoxLayout()
        botoes.addStretch()
        if pode_pegar:
            b = QPushButton("🎒 Pegar")
            b.clicked.connect(lambda: (self.pegar.emit(), self.close()))
            botoes.addWidget(b)
        fechar = QPushButton("Fechar")
        fechar.clicked.connect(self.close)
        botoes.addWidget(fechar)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 20, 26, 16)
        lay.addWidget(titulo)
        lay.addWidget(area, 1)
        lay.addLayout(botoes)
        self.resize(680, 720 if doc.get("img") else 520)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema
