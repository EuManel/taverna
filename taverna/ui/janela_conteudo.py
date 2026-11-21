"""
Janela do jogador quando ele abre um baú (ou o mestre mostra o conteúdo pra ele).
"""

import html

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
                             QVBoxLayout, QWidget)

from .dialogo_prop import pixmap_b64
from .tema import tema_atual


class JanelaConteudo(QDialog):
    pegar = pyqtSignal(str, str)   # id do prop, id do item

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(False)
        self.setMinimumSize(420, 320)
        self.resize(460, 480)
        self.uid = None
        self.titulo = QLabel()
        self.titulo.setStyleSheet("font-size: 15pt; font-weight: bold; color: palette(highlight);")
        self.subtitulo = QLabel()
        self.subtitulo.setObjectName("dica")
        self.area = QScrollArea()
        self.area.setWidgetResizable(True)
        fechar = QPushButton("Fechar")
        fechar.clicked.connect(self.close)
        baixo = QHBoxLayout()
        baixo.addStretch()
        baixo.addWidget(fechar)
        layout = QVBoxLayout(self)
        layout.addWidget(self.titulo)
        layout.addWidget(self.subtitulo)
        layout.addWidget(self.area, 1)
        layout.addLayout(baixo)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def mostrar(self, msg: dict):
        self.uid = msg.get("id")
        itens = msg.get("itens") or []
        # papel solto no cenário: abre direto pra ler
        if msg.get("documento") and len(itens) == 1 and itens[0].get("doc") and not msg.get("do_mestre_lista"):
            self._ler(itens[0], bool(msg.get("pode_pegar")))
            return
        nome = msg.get("nome", "Objeto")
        self.setWindowTitle(nome)
        criatura = bool(msg.get("criatura"))
        self.titulo.setText(nome)
        itens = msg.get("itens") or []
        pode = bool(msg.get("pode_pegar"))
        if msg.get("do_mestre"):
            self.subtitulo.setText("O mestre está mostrando isto pra você.")
        else:
            self.subtitulo.setText(("Você revistou e encontrou:" if criatura else "Você abriu e encontrou:")
                                   if itens else "")
        corpo = QWidget()
        lc = QVBoxLayout(corpo)
        if not itens:
            vazio = QLabel("Não tem nada." if msg.get("criatura") else "Está vazio.")
            vazio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vazio.setStyleSheet("font-size: 12pt; padding: 30px;")
            vazio.setObjectName("dica")
            lc.addWidget(vazio)
        for it in itens:
            cartao = QFrame()
            t = tema_atual()   # cartão nas cores do tema (antes marrom fixo, ruim no tema claro)
            cartao.setStyleSheet(f"QFrame {{ background: {t['painel2']}; border: 1px solid {t['borda']}; "
                                 f"border-radius: {t['raio']}px; }}"
                                 "QLabel { border: none; background: transparent; }")
            h = QHBoxLayout(cartao)
            img = QLabel()
            img.setFixedSize(64, 64)
            img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pm = pixmap_b64(it.get("img"), 62)
            if pm:
                img.setPixmap(pm)
            else:
                from .icones import pixmap_icone
                img.setPixmap(pixmap_icone("objetos", tema_atual()["destaque"], 36))
            h.addWidget(img, 0, Qt.AlignmentFlag.AlignTop)
            texto = QLabel()
            texto.setWordWrap(True)
            texto.setTextFormat(Qt.TextFormat.RichText)
            qtd = it.get("qtd", 1)
            texto.setText(f"<b style='font-size:12pt'>{html.escape(it.get('nome', '?'))}</b>"
                          + (f" <span style='color:{t['destaque']}'>×{qtd}</span>" if qtd and qtd != 1 else "")
                          + (f"<br><span style='color:{t['fraco']}'>{html.escape(it.get('desc', '')).replace(chr(10), '<br>')}</span>"
                             if it.get("desc") else ""))
            h.addWidget(texto, 1)
            if it.get("doc"):
                ler = QPushButton("📖 Ler")
                ler.clicked.connect(lambda _=False, i=it: self._ler(i, False))
                h.addWidget(ler, 0, Qt.AlignmentFlag.AlignTop)
            if pode:
                b = QPushButton("🎒 Pegar")
                b.setObjectName("primario")
                b.clicked.connect(lambda _=False, i=it.get("id"): self.pegar.emit(self.uid, i))
                h.addWidget(b, 0, Qt.AlignmentFlag.AlignTop)
            lc.addWidget(cartao)
        lc.addStretch()
        self.area.setWidget(corpo)
        if msg.get("documento") and not itens:
            return   # papel que já foi pego
        self.show()
        self.raise_()
        self.activateWindow()

    def _ler(self, item, pode_pegar):
        from .janela_leitura import JanelaLeitura
        janela = JanelaLeitura(item, pode_pegar, self.parent())
        uid = self.uid
        janela.pegar.connect(lambda: self.pegar.emit(uid, item.get("id")))
        janela.show()
        self._leitura = janela
