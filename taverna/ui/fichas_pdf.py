"""
📄 Fichas em PDF (Etapa 14): importar a ficha de QUALQUER sistema e preencher dentro do Taverna.

- A ficha é copiada pra Documentos/Taverna/Fichas (o arquivo original fica intacto).
- O editor mostra as páginas e coloca os campos editáveis por cima: é só clicar e digitar,
  marcar as caixinhas, escolher nas listas.
- Salva sozinho (a cada 30 s e ao fechar) e dá pra exportar uma cópia pra mandar pra alguém.
- PDF sem campos editáveis abre só pra leitura.
Tudo fica no seu PC — nada vai pela rede.
"""

import os
import re
import shutil

from PyQt6.QtCore import QStandardPaths, Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices, QFont, QImage, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (QComboBox, QDialog, QFileDialog, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                             QListWidget, QListWidgetItem, QMessageBox, QPlainTextEdit, QPushButton,
                             QScrollArea, QVBoxLayout, QWidget)

from ..jogo.pdf_form import gravar_formulario, ler_formulario

ESTILO_CAMPO = ("background: rgba(70, 120, 230, 38); border: 1px solid rgba(70, 120, 230, 90); "
                "color: #111; padding: 0px 2px; selection-background-color: #7aa7ff;")
ESTILO_FOCO = "border: 1px solid #2d6bff; background: rgba(255, 255, 230, 235);"


def pasta_fichas() -> str:
    docs = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation) \
        or os.path.expanduser("~")
    pasta = os.path.join(docs, "Taverna", "Fichas")
    os.makedirs(pasta, exist_ok=True)
    return pasta


def _livre(pasta, nome):
    base = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", nome).strip().rstrip(".") or "Ficha"
    caminho, k = os.path.join(pasta, base + ".pdf"), 2
    while os.path.exists(caminho):
        caminho, k = os.path.join(pasta, f"{base} ({k}).pdf"), k + 1
    return caminho


def _renderizar(dados: bytes, escala: float) -> list[QPixmap]:
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(dados)
    paginas = []
    for i in range(len(doc)):
        bitmap = doc[i].render(scale=escala, may_draw_forms=False)
        qimg = QImage(bitmap.buffer, bitmap.width, bitmap.height, bitmap.stride, QImage.Format.Format_BGR888)
        paginas.append(QPixmap.fromImage(qimg.copy()))
    doc.close()
    return paginas


class _Caixa(QPushButton):
    """Checkbox / botão de opção desenhado por cima do PDF."""

    def __init__(self, radio: bool):
        super().__init__()
        self.radio = radio
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggled.connect(lambda v: self.setText(("●" if self.radio else "✔") if v else ""))


class EditorFichaPDF(QDialog):
    def __init__(self, caminho: str, parent=None):
        super().__init__(parent)
        self.caminho = caminho
        self.setWindowTitle(f"📄 {os.path.splitext(os.path.basename(caminho))[0]}")
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.resize(980, 860)
        with open(caminho, "rb") as f:
            self.dados = f.read()
        self.form = ler_formulario(self.dados)
        self.valores = {c["nome"]: c["valor"] for c in self.form["campos"]}
        self.widgets: dict[str, list] = {}
        self.modificado = False
        self.zoom = 1.4

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        barra = QHBoxLayout()
        barra.setContentsMargins(8, 6, 8, 2)
        self.b_salvar = QPushButton("💾 Salvar")
        self.b_salvar.setObjectName("primario")
        self.b_salvar.clicked.connect(self.salvar)
        barra.addWidget(self.b_salvar)
        b = QPushButton("📤 Exportar cópia…")
        b.setToolTip("Salvar uma cópia em outro lugar (pra mandar pro mestre, imprimir…)")
        b.clicked.connect(self.exportar)
        barra.addWidget(b)
        barra.addSpacing(12)
        for texto, f in (("－", 1 / 1.2), ("＋", 1.2)):
            b = QPushButton(texto)
            b.setFixedWidth(34)
            b.clicked.connect(lambda _=False, f=f: self.definir_zoom(self.zoom * f))
            barra.addWidget(b)
        self.lbl_zoom = QLabel()
        barra.addWidget(self.lbl_zoom)
        barra.addStretch(1)
        self.status = QLabel()
        barra.addWidget(self.status)
        lay.addLayout(barra)
        self.rolagem = QScrollArea()
        self.rolagem.setWidgetResizable(False)
        self.rolagem.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.rolagem.setStyleSheet("QScrollArea { background: #2a2620; }")
        lay.addWidget(self.rolagem, 1)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.salvar)
        QShortcut(QKeySequence("Ctrl++"), self, activated=lambda: self.definir_zoom(self.zoom * 1.2))
        QShortcut(QKeySequence("Ctrl+-"), self, activated=lambda: self.definir_zoom(self.zoom / 1.2))
        self._auto = QTimer(self)
        self._auto.setInterval(30_000)
        self._auto.timeout.connect(lambda: self.modificado and self.salvar(silencioso=True))
        self._auto.start()
        self._montar()
        n = len(self.form["campos"])
        if not n:
            self.status.setText("ℹ Esse PDF não tem campos editáveis — dá pra ler, mas não preencher.")
        else:
            self.status.setText(f"{n} campos · clique e digite · salva sozinho")
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    # ------------------------------------------------------------ montar páginas e campos
    def definir_zoom(self, z):
        self.zoom = max(0.6, min(3.5, z))
        self._montar()

    def _montar(self):
        self.lbl_zoom.setText(f"{self.zoom * 100 / 1.4:.0f}%")
        rolar_y = self.rolagem.verticalScrollBar().value()
        miolo = QWidget()
        miolo.setStyleSheet("background: transparent;")
        col = QVBoxLayout(miolo)
        col.setContentsMargins(16, 16, 16, 16)
        col.setSpacing(16)
        self.widgets = {}
        pixmaps = _renderizar(self.dados, self.zoom)
        for i, pm in enumerate(pixmaps):
            pagina = QLabel()
            pagina.setPixmap(pm)
            pagina.setFixedSize(pm.size())
            pagina.setStyleSheet("background: white;")
            col.addWidget(pagina, 0, Qt.AlignmentFlag.AlignHCenter)
            larg_pt, alt_pt, x0, y0, _rot = self.form["paginas"][i]
            esc = pm.width() / larg_pt if larg_pt else self.zoom
            for c in self.form["campos"]:
                if c["pagina"] == i:
                    self._campo(pagina, c, esc, alt_pt, x0, y0)
        miolo.adjustSize()
        self.rolagem.setWidget(miolo)
        self.rolagem.verticalScrollBar().setValue(rolar_y)

    def _campo(self, pagina, c, esc, alt_pt, x0, y0):
        x1, y1, x2, y2 = c["rect"]
        x, y = (x1 - x0) * esc, (alt_pt - (y2 - y0)) * esc
        w, h = (x2 - x1) * esc, (y2 - y1) * esc
        nome = c["nome"]
        valor = self.valores.get(nome, "")
        tam_fonte = c["fonte"] * esc * 0.95 if c["fonte"] else min(h * 0.62, 13 * esc / 1.4)
        fonte = QFont("Helvetica")
        fonte.setPixelSize(max(7, int(tam_fonte)))
        if c["tipo"] in ("texto", "multilinha"):
            if c["tipo"] == "multilinha":
                wid = QPlainTextEdit(pagina)
                wid.setPlainText(valor)
                wid.textChanged.connect(lambda n=nome, wd=wid: self._mudou(n, wd.toPlainText(), wd))
            else:
                wid = QLineEdit(pagina)
                wid.setText(valor)
                if c["max_len"]:
                    wid.setMaxLength(c["max_len"])
                wid.setAlignment({1: Qt.AlignmentFlag.AlignHCenter, 2: Qt.AlignmentFlag.AlignRight}
                                 .get(c["alinhar"], Qt.AlignmentFlag.AlignLeft) | Qt.AlignmentFlag.AlignVCenter)
                wid.textEdited.connect(lambda t, n=nome, wd=wid: self._mudou(n, t, wd))
            wid.setFont(fonte)
            wid.setStyleSheet(f"QLineEdit, QPlainTextEdit {{ {ESTILO_CAMPO} }}"
                              f"QLineEdit:focus, QPlainTextEdit:focus {{ {ESTILO_FOCO} }}")
        elif c["tipo"] in ("caixa", "radio"):
            wid = _Caixa(c["tipo"] == "radio")
            wid.setParent(pagina)
            wid.setChecked(valor == c["ligado"])
            wid.setText(("●" if wid.radio else "✔") if wid.isChecked() else "")
            fonte.setPixelSize(max(7, int(h * 0.75)))
            wid.setFont(fonte)
            wid.setStyleSheet(f"QPushButton {{ {ESTILO_CAMPO} border-radius: {int(h / 2) if wid.radio else 2}px;"
                              f" color: #0a2a8a; padding: 0; }}")
            wid.ligado = c["ligado"]
            wid.clicked.connect(lambda v, n=nome, wd=wid: self._marcou(n, wd, v))
        else:
            wid = QComboBox(pagina)
            wid.addItem("")
            wid.addItems(c["opcoes"])
            wid.setEditable(True)
            wid.setCurrentText(valor)
            wid.setFont(fonte)
            wid.setStyleSheet(f"QComboBox {{ {ESTILO_CAMPO} }}")
            wid.currentTextChanged.connect(lambda t, n=nome, wd=wid: self._mudou(n, t, wd))
        wid.setGeometry(int(x), int(y), max(6, int(w)), max(6, int(h)))
        wid.setToolTip(nome)
        if c["so_leitura"]:
            wid.setEnabled(False)
        self.widgets.setdefault(nome, []).append(wid)

    # ------------------------------------------------------------ mudanças
    def _marcar_modificado(self):
        if not self.modificado:
            self.modificado = True
            self.status.setText("Alterações ainda não salvas")

    def _mudou(self, nome, valor, origem):
        self.valores[nome] = valor
        # o mesmo campo pode aparecer em mais de um lugar (ex.: nome do personagem em toda página)
        for wd in self.widgets.get(nome, []):
            if wd is origem:
                continue
            wd.blockSignals(True)
            if isinstance(wd, QLineEdit):
                wd.setText(valor)
            elif isinstance(wd, QPlainTextEdit):
                wd.setPlainText(valor)
            elif isinstance(wd, QComboBox):
                wd.setCurrentText(valor)
            wd.blockSignals(False)
        self._marcar_modificado()

    def _marcou(self, nome, origem, marcado):
        valor = origem.ligado if marcado else "/Off"
        self.valores[nome] = valor
        for wd in self.widgets.get(nome, []):
            if wd is not origem and isinstance(wd, _Caixa):
                wd.blockSignals(True)
                wd.setChecked(marcado and wd.ligado == origem.ligado)
                wd.setText(("●" if wd.radio else "✔") if wd.isChecked() else "")
                wd.blockSignals(False)
        self._marcar_modificado()

    # ------------------------------------------------------------ salvar
    def salvar(self, silencioso=False) -> bool:
        if not self.form["campos"]:
            return True
        try:
            novo = gravar_formulario(self.dados, self.valores)
            temporario = self.caminho + ".salvando"
            with open(temporario, "wb") as f:
                f.write(novo)
            os.replace(temporario, self.caminho)
            self.dados = novo
        except Exception as erro:
            QMessageBox.warning(self, "Não deu", f"Não consegui salvar a ficha:\n{erro}")
            return False
        self.modificado = False
        import time
        self.status.setText(f"✔ Salvo às {time.strftime('%H:%M:%S')}")
        return True

    def exportar(self):
        if self.modificado:
            self.salvar(silencioso=True)
        destino, _ = QFileDialog.getSaveFileName(self, "Exportar cópia da ficha",
                                                 os.path.basename(self.caminho), "PDF (*.pdf)")
        if destino:
            shutil.copy2(self.caminho, destino)
            self.status.setText(f"✔ Cópia salva em {destino}")

    def closeEvent(self, ev):
        if self.modificado:
            self.salvar(silencioso=True)
        super().closeEvent(ev)

    def reject(self):
        if self.modificado:
            self.salvar(silencioso=True)
        super().reject()


class JanelaFichasPDF(QDialog):
    """Lista das fichas em PDF do jogador/mestre (qualquer sistema)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📄 Fichas em PDF — qualquer sistema")
        self.resize(560, 460)
        lay = QVBoxLayout(self)
        dica = QLabel("Importe a ficha do seu sistema (Ordem Paranormal, Tormenta, Call of Cthulhu…) e "
                      "preencha aqui dentro. Funciona com PDF <b>editável</b> (com campos). "
                      "A ficha fica só no seu PC.")
        dica.setWordWrap(True)
        lay.addWidget(dica)
        self.lista = QListWidget()
        self.lista.itemDoubleClicked.connect(lambda _it: self.abrir())
        lay.addWidget(self.lista, 1)
        linha = QHBoxLayout()
        for texto, f, prim in (("➕ Importar ficha…", self.importar, True), ("📖 Abrir", self.abrir, False),
                               ("✏ Renomear", self.renomear, False), ("🗑", self.apagar, False)):
            b = QPushButton(texto)
            if prim:
                b.setObjectName("primario")
            if texto == "🗑":
                b.setToolTip("Apagar a ficha")
            b.clicked.connect(f)
            linha.addWidget(b)
        lay.addLayout(linha)
        b = QPushButton("📂 Abrir a pasta das fichas")
        b.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(pasta_fichas())))
        lay.addWidget(b)
        self.recarregar()
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def recarregar(self, selecionar: str | None = None):
        self.lista.clear()
        for a in sorted(os.listdir(pasta_fichas()), key=str.casefold):
            if a.lower().endswith(".pdf"):
                from .acabamento import item_com_icone
                it = item_com_icone(QListWidgetItem(), "📄 " + os.path.splitext(a)[0])
                it.setData(Qt.ItemDataRole.UserRole, os.path.join(pasta_fichas(), a))
                self.lista.addItem(it)
                if selecionar and os.path.join(pasta_fichas(), a) == selecionar:
                    self.lista.setCurrentItem(it)
        if self.lista.currentRow() < 0 and self.lista.count():
            self.lista.setCurrentRow(0)

    def _atual(self):
        it = self.lista.currentItem()
        return it.data(Qt.ItemDataRole.UserRole) if it else None

    def importar(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Importar ficha em PDF", "", "PDF (*.pdf)")
        if not caminho:
            return
        destino = _livre(pasta_fichas(), os.path.splitext(os.path.basename(caminho))[0])
        try:
            shutil.copy2(caminho, destino)
            n = len(ler_formulario(destino)["campos"])
        except Exception as erro:
            QMessageBox.warning(self, "Não deu", f"Não consegui abrir esse PDF:\n{erro}")
            return
        self.recarregar(destino)
        if not n:
            QMessageBox.information(self, "Ficha sem campos",
                                    "Esse PDF não tem campos editáveis — vai abrir só pra leitura.\n"
                                    "Procure a versão 'preenchível' / 'editável' da ficha do seu sistema.")
        self.abrir()

    def abrir(self):
        c = self._atual()
        if c:
            ed = EditorFichaPDF(c, self.parent() or self)
            ed.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            ed.show()

    def renomear(self):
        c = self._atual()
        if not c:
            return
        nome, ok = QInputDialog.getText(self, "Renomear ficha", "Nome:", text=os.path.splitext(os.path.basename(c))[0])
        if ok and nome.strip():
            novo = _livre(pasta_fichas(), nome.strip())
            os.rename(c, novo)
            self.recarregar(novo)

    def apagar(self):
        c = self._atual()
        if c and QMessageBox.question(self, "Apagar ficha", f"Apagar “{os.path.basename(c)}”?") \
                == QMessageBox.StandardButton.Yes:
            os.remove(c)
            self.recarregar()
