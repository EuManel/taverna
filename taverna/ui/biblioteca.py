"""
Biblioteca (v0.42: sem o compêndio de D&D — pedido do Manel, pra publicar o Taverna neutro).

- 📕 PDFs: cada pessoa importa os PRÓPRIOS documentos (livros, regras da casa, mapas…).
- 📄 Fichas: modelos de ficha em PDF (de qualquer sistema) e as fichas preenchidas.
- 🧙 Tokens (só o mestre): tokens prontos, salvos, pra colocar na mesa quando quiser.
"""

import json
import os

from PyQt6.QtCore import QRectF, QSettings, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QKeySequence, QPainter, QPixmap, QShortcut
from PyQt6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                             QListWidgetItem, QMainWindow, QMessageBox, QPushButton,
                             QScrollArea, QSpinBox, QSplitter, QTabWidget, QTextBrowser,
                             QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
                             QWidget)

from ..compendio.compendio import sem_acento
from .acabamento import item_com_icone

class _EstiloFicha:
    """Estilo das fichas do compêndio, nas cores do tema atual (vira texto na hora de usar)."""

    def __str__(self):
        from .tema import tema_atual
        t = tema_atual()
        return f"""
<style>
 body {{ font-family: Georgia, serif; }}
 h2 {{ color: {t['destaque']}; margin-bottom: 2px; }}
 h3 {{ color: {t['destaque']}; margin-top: 14px; margin-bottom: 4px; border-bottom: 1px solid {t['borda']}; }}
 h4 {{ margin-bottom: 2px; }}
 hr {{ border: 0; border-top: 1px solid {t['perigo']}; }}
 table.tab {{ border-collapse: collapse; margin: 6px 0; }}
 table.tab th {{ background: {t['painel2']}; border: 1px solid {t['borda']}; }}
 table.tab td {{ border: 1px solid {t['borda']}; }}
 a {{ color: {t['destaque']}; }}
 p.orig {{ color: {t['fraco']}; margin-top: 0; font-size: 9pt; }}
</style>
"""

    def __add__(self, outro):
        return str(self) + outro


ESTILO_FICHA = _EstiloFicha()


class AbaMeusPdfs(QWidget):
    """PDFs desta pessoa: arquivos avulsos e pastas inteiras."""
    mudou = pyqtSignal()   # importou/tirou (o jogador avisa o mestre da lista nova)

    def __init__(self, app_nome: str, parent=None, livros_mestre=None, jogadores=None):
        super().__init__(parent)
        self.config = QSettings("Taverna", app_nome)
        self.janelas = []
        self.livros_mestre = livros_mestre   # (mestre) pra liberar livros pros jogadores
        self.jogadores = jogadores or (lambda: [])

        if livros_mestre is not None:
            aviso = QLabel("📁 Seus documentos. Pra um jogador ver um livro, selecione e use "
                           "<b>👥 Liberar pros jogadores</b>: o PDF vai pela rede pra ele.")
        else:
            aviso = QLabel("📁 Seus próprios documentos (livros que você tem, regras da casa, mapas…). "
                           "O mestre consegue ver a lista da sua biblioteca.")
        aviso.setWordWrap(True)
        aviso.setObjectName("dica")

        self.filtro = QLineEdit()
        self.filtro.setPlaceholderText("Filtrar pelo nome do arquivo…")
        self.filtro.setClearButtonEnabled(True)
        self.filtro.textChanged.connect(self._filtrar)

        self.arvore = QTreeWidget()
        self.arvore.setHeaderHidden(True)
        self.arvore.itemDoubleClicked.connect(lambda item, _: self._abrir(item))

        importar = QPushButton("＋  Importar PDF…")
        importar.setObjectName("primario")
        importar.clicked.connect(self._importar)
        pasta = QPushButton("📁  Adicionar pasta…")
        pasta.setObjectName("primario")
        pasta.setToolTip("Mostra todos os PDFs de uma pasta (e das subpastas). "
                         "PDFs novos que você colocar lá aparecem sozinhos.")
        pasta.clicked.connect(self._adicionar_pasta)
        abrir = QPushButton("Abrir")
        abrir.clicked.connect(lambda: self._abrir(self.arvore.currentItem()))
        atualizar = QPushButton("⟳")
        atualizar.setToolTip("Procurar de novo os PDFs das pastas")
        atualizar.clicked.connect(self._recarregar)
        remover = QPushButton("Tirar da lista")
        remover.setToolTip("Só tira da lista (o arquivo ou a pasta). Nada é apagado do seu computador.")
        remover.clicked.connect(self._remover)
        botoes = QHBoxLayout()
        for b in (importar, pasta, abrir, atualizar, remover):
            botoes.addWidget(b)
        if livros_mestre is not None:
            liberar = QPushButton("👥  Liberar pros jogadores…")
            liberar.setToolTip("Escolha quais jogadores podem ver este livro. O PDF vai pela rede pra eles.")
            liberar.clicked.connect(self._liberar)
            botoes.addWidget(liberar)
            livros_mestre.mudou.connect(self._recarregar)
        botoes.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(aviso)
        layout.addWidget(self.filtro)
        layout.addWidget(self.arvore, 1)
        layout.addLayout(botoes)
        self._recarregar()
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    # ------------------------------------------------------------ guardado
    def _lista(self, chave) -> list[str]:
        try:
            return json.loads(self.config.value(chave, "[]"))
        except (TypeError, ValueError):
            return []

    def _salvar(self, chave, valores):
        self.config.setValue(chave, json.dumps(valores, ensure_ascii=False))

    # compatível com a versão anterior
    def _caminhos(self):
        return self._lista("meus_pdfs")

    # ------------------------------------------------------------ árvore
    def _item_pdf(self, pai, caminho, rotulo=None):
        nome = rotulo or os.path.splitext(os.path.basename(caminho))[0]
        existe = os.path.exists(caminho)
        if self.livros_mestre is not None:   # mostra pra quem está liberado
            info = self.livros_mestre.liberados().get(caminho)
            if info:
                quem = info.get("jogadores", [])
                nome += "   👥 " + ("todos" if "*" in quem else ", ".join(quem))
        item = QTreeWidgetItem(pai)
        item_com_icone(item, ("📕 " if existe else "⚠ ") + nome, 0)
        item.setToolTip(0, caminho if existe else f"Arquivo não encontrado: {caminho}")
        item.setData(0, Qt.ItemDataRole.UserRole, ("arquivo", caminho))
        return item

    def _recarregar(self):
        self.arvore.clear()
        for pasta in self._lista("pastas_pdf"):
            existe = os.path.isdir(pasta)
            nome_pasta = os.path.basename(os.path.normpath(pasta)) or pasta
            topo = QTreeWidgetItem(self.arvore)
            item_com_icone(topo, f"📁 {nome_pasta}", 0)
            topo.setData(0, Qt.ItemDataRole.UserRole, ("pasta", pasta))
            topo.setToolTip(0, pasta if existe else f"Pasta não encontrada: {pasta}")
            achados = []
            if existe:
                for raiz, _, arquivos in os.walk(pasta):
                    for a in arquivos:
                        if a.lower().endswith(".pdf"):
                            achados.append(os.path.join(raiz, a))
            achados.sort(key=lambda c: os.path.relpath(c, pasta).lower())
            for c in achados:
                rel = os.path.splitext(os.path.relpath(c, pasta))[0].replace("\\", " / ").replace("/", " / ")
                self._item_pdf(topo, c, rel)
            topo.setText(0, topo.text(0) + f"   ({len(achados)})" if existe else topo.text(0) + "   (não encontrada)")
            topo.setExpanded(True)
        avulsos = self._caminhos()
        if avulsos:
            topo = QTreeWidgetItem(self.arvore)
            item_com_icone(topo, f"📌 Arquivos avulsos   ({len(avulsos)})", 0)
            topo.setData(0, Qt.ItemDataRole.UserRole, ("grupo", None))
            for c in avulsos:
                self._item_pdf(topo, c)
            topo.setExpanded(True)
        self._filtrar(self.filtro.text())

    def _filtrar(self, texto):
        termo = sem_acento(texto.strip())
        for k in range(self.arvore.topLevelItemCount()):
            topo = self.arvore.topLevelItem(k)
            visiveis = 0
            for n in range(topo.childCount()):
                filho = topo.child(n)
                ok = not termo or termo in sem_acento(filho.text(0))
                filho.setHidden(not ok)
                visiveis += ok
            topo.setHidden(bool(termo) and visiveis == 0)

    # ------------------------------------------------------------ ações
    def _importar(self):
        arquivos, _ = QFileDialog.getOpenFileNames(self, "Importar PDF", "", "PDF (*.pdf)")
        if not arquivos:
            return
        caminhos = self._caminhos()
        caminhos += [a for a in arquivos if a not in caminhos]
        self._salvar("meus_pdfs", caminhos)
        self._recarregar()
        self.mudou.emit()

    def _adicionar_pasta(self):
        pasta = QFileDialog.getExistingDirectory(self, "Escolha a pasta com os seus PDFs")
        if not pasta:
            return
        pastas = self._lista("pastas_pdf")
        if pasta not in pastas:
            pastas.append(pasta)
            self._salvar("pastas_pdf", pastas)
        self._recarregar()
        self.mudou.emit()

    def _remover(self):
        item = self.arvore.currentItem()
        if not item:
            return
        tipo, caminho = item.data(0, Qt.ItemDataRole.UserRole)
        if tipo == "pasta":
            self._salvar("pastas_pdf", [p for p in self._lista("pastas_pdf") if p != caminho])
        elif tipo == "arquivo":
            pai = item.parent()
            if pai and pai.data(0, Qt.ItemDataRole.UserRole)[0] == "pasta":
                QMessageBox.information(self, "Está numa pasta",
                                        "Esse PDF aparece porque está numa pasta da lista.\n"
                                        "Pra tirar, remova a pasta inteira (selecione a pasta).")
                return
            self._salvar("meus_pdfs", [c for c in self._caminhos() if c != caminho])
        self._recarregar()
        self.mudou.emit()

    def _liberar(self):
        """Mestre: quais jogadores podem ver este livro (o PDF vai pela rede pra eles)."""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox
        from ..rede.livros import AVISO
        item = self.arvore.currentItem()
        dado = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if not dado or dado[0] != "arquivo" or not os.path.isfile(dado[1]):
            QMessageBox.information(self, "Escolha um livro", "Selecione um PDF na lista primeiro.")
            return
        caminho = dado[1]
        atual = self.livros_mestre.liberados().get(caminho, {}).get("jogadores", [])
        nomes = sorted(set(self.jogadores()) | {n for n in atual if n != "*"}, key=str.casefold)
        dlg = QDialog(self)
        dlg.setWindowTitle("Liberar pros jogadores")
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(f"<b>{os.path.splitext(os.path.basename(caminho))[0]}</b>"))
        lista = QListWidget()
        todos = QListWidgetItem("Todos os jogadores (inclusive quem entrar depois)")
        todos.setData(Qt.ItemDataRole.UserRole, "*")
        for it_texto, valor in [(None, None)] + [(n, n) for n in nomes]:
            it = todos if it_texto is None else QListWidgetItem(it_texto)
            if it_texto is not None:
                it.setData(Qt.ItemDataRole.UserRole, valor)
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(Qt.CheckState.Checked if (it.data(Qt.ItemDataRole.UserRole) in atual)
                             else Qt.CheckState.Unchecked)
            lista.addItem(it)
        lay.addWidget(lista)
        if not nomes:
            lay.addWidget(QLabel("(Ninguém conectado agora: marque “Todos” ou libere quando eles entrarem.)"))
        aviso = QLabel("⚠ " + AVISO)
        aviso.setWordWrap(True)
        aviso.setObjectName("dica")
        lay.addWidget(aviso)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay.addWidget(bb)
        if not dlg.exec():
            return
        escolhidos = [lista.item(i).data(Qt.ItemDataRole.UserRole) for i in range(lista.count())
                      if lista.item(i).checkState() == Qt.CheckState.Checked]
        self.livros_mestre.liberar(caminho, ["*"] if "*" in escolhidos else escolhidos)

    def _abrir(self, item):
        if not item:
            return
        tipo, caminho = item.data(0, Qt.ItemDataRole.UserRole)
        if tipo != "arquivo":
            item.setExpanded(not item.isExpanded())
            return
        if not os.path.exists(caminho):
            QMessageBox.warning(self, "Não achei", f"O arquivo não está mais lá:\n{caminho}")
            return
        try:
            janela = LeitorPdf(caminho)
        except Exception as erro:  # PDF protegido, corrompido...
            QMessageBox.warning(self, "Não deu", f"Não consegui abrir esse PDF:\n{erro}")
            return
        janela.show()
        self.janelas.append(janela)


def _pagina_para_tela(pagina, largura, altura, x, y):
    """Coordenada do PDF (pontos) -> pixel da imagem renderizada."""
    import ctypes

    import pypdfium2.raw as pdfium_c
    dx, dy = ctypes.c_int(), ctypes.c_int()
    pdfium_c.FPDF_PageToDevice(pagina.raw, 0, 0, largura, altura, 0,
                               ctypes.c_double(x), ctypes.c_double(y),
                               ctypes.byref(dx), ctypes.byref(dy))
    return dx.value, dy.value


class LeitorPdf(QMainWindow):
    """Leitor de PDF simples: páginas, zoom e busca de texto. Tudo local, nada vai pra rede."""

    def __init__(self, caminho: str, parent=None):
        super().__init__(parent)
        import pypdfium2 as pdfium
        self.doc = pdfium.PdfDocument(caminho)
        self.total = len(self.doc)
        self.pagina = 0
        self.zoom = 1.3
        self._termo = ""
        self.achados = []        # [(pagina, [retângulos em pontos do PDF])]
        self.achado_atual = -1
        self.setWindowTitle(f"{os.path.basename(caminho)} — Taverna")
        self.resize(900, 1000)

        self.imagem = QLabel()
        self.imagem.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rolagem = QScrollArea()
        self.rolagem.setWidget(self.imagem)
        self.rolagem.setWidgetResizable(True)
        self.rolagem.setAlignment(Qt.AlignmentFlag.AlignCenter)

        def botao(texto, dica, funcao):
            b = QToolButton()
            b.setText(texto)
            b.setToolTip(dica)
            b.clicked.connect(funcao)
            return b

        self.num = QSpinBox()
        self.num.setRange(1, max(1, self.total))
        self.num.setSuffix(f" / {self.total}")
        self.num.setKeyboardTracking(False)
        self.num.valueChanged.connect(lambda v: self.ir_para(v - 1))
        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Buscar no PDF… (Enter = próxima, Shift+Enter = anterior)")
        self.busca.setClearButtonEnabled(True)
        self.busca.returnPressed.connect(self.buscar)
        self.busca.textChanged.connect(lambda t: None if t.strip() else self.limpar_busca())
        self.status = QLabel()
        self.status.setObjectName("dica")

        barra = QHBoxLayout()
        barra.addWidget(botao("◀", "Página anterior (PgUp)", lambda: self.ir_para(self.pagina - 1)))
        barra.addWidget(self.num)
        barra.addWidget(botao("▶", "Próxima página (PgDn)", lambda: self.ir_para(self.pagina + 1)))
        barra.addSpacing(12)
        barra.addWidget(botao("−", "Diminuir zoom", lambda: self.definir_zoom(self.zoom / 1.2)))
        barra.addWidget(botao("＋", "Aumentar zoom", lambda: self.definir_zoom(self.zoom * 1.2)))
        barra.addWidget(botao("↔", "Caber na largura", self.caber_largura))
        barra.addSpacing(12)
        barra.addWidget(self.busca, 1)
        barra.addWidget(botao("▲", "Ocorrência anterior (Shift+Enter)", lambda: self.buscar(voltar=True)))
        barra.addWidget(botao("▼", "Próxima ocorrência (Enter / F3)", self.buscar))
        self.statusBar().addWidget(self.status)

        central = QWidget()
        lay = QVBoxLayout(central)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.addLayout(barra)
        lay.addWidget(self.rolagem, 1)
        self.setCentralWidget(central)

        QShortcut(QKeySequence("PgDown"), self, lambda: self.ir_para(self.pagina + 1))
        QShortcut(QKeySequence("PgUp"), self, lambda: self.ir_para(self.pagina - 1))
        QShortcut(QKeySequence("Ctrl+F"), self, lambda: (self.busca.setFocus(), self.busca.selectAll()))
        QShortcut(QKeySequence("F3"), self, self.buscar)
        QShortcut(QKeySequence("Shift+F3"), self, lambda: self.buscar(voltar=True))
        QShortcut(QKeySequence("Shift+Return"), self.busca, lambda: self.buscar(voltar=True))
        QShortcut(QKeySequence("Escape"), self.busca, lambda: self.busca.clear())
        self.desenhar()
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def ir_para(self, pagina: int):
        pagina = max(0, min(self.total - 1, pagina))
        if pagina != self.pagina:
            self.pagina = pagina
            self.desenhar()
            self.rolagem.verticalScrollBar().setValue(0)

    def definir_zoom(self, zoom: float):
        self.zoom = max(0.3, min(5.0, zoom))
        self.desenhar()

    def caber_largura(self):
        largura_pt = self.doc[self.pagina].get_width()
        self.definir_zoom((self.rolagem.viewport().width() - 20) / max(1, largura_pt))

    def desenhar(self):
        if self.total == 0:
            self.imagem.setText("PDF vazio.")
            return
        dpr = self.devicePixelRatioF()
        escala = self.zoom * dpr
        pagina = self.doc[self.pagina]
        bitmap = pagina.render(scale=escala)
        img = QImage(bitmap.buffer, bitmap.width, bitmap.height, bitmap.stride,
                     QImage.Format.Format_BGR888).copy()
        img = img.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)

        # destaca as ocorrências da busca nesta página (amarelo; a atual em laranja)
        alvo_y = None
        achados = [(k, a) for k, a in enumerate(self.achados) if a[0] == self.pagina]
        if achados:
            pintor = QPainter(img)
            pintor.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
            for k, (_, retangulos) in achados:
                atual = k == self.achado_atual
                cor = QColor(255, 150, 40) if atual else QColor(255, 235, 60)
                for (esq, baixo, dir_, topo) in retangulos:
                    # o próprio PDFium converte (considera recorte e rotação da página)
                    x1, y1 = _pagina_para_tela(pagina, img.width(), img.height(), esq, topo)
                    x2, y2 = _pagina_para_tela(pagina, img.width(), img.height(), dir_, baixo)
                    r = QRectF(min(x1, x2), min(y1, y2),
                               abs(x2 - x1), abs(y2 - y1)).adjusted(-2, -2, 2, 2)
                    pintor.fillRect(r, cor)
                    if atual:
                        alvo_y = r.center().y() / dpr
            pintor.end()

        pm = QPixmap.fromImage(img)
        pm.setDevicePixelRatio(dpr)
        self.imagem.setPixmap(pm)
        self.num.blockSignals(True)
        self.num.setValue(self.pagina + 1)
        self.num.blockSignals(False)
        if alvo_y is not None:
            QTimer.singleShot(0, lambda: self._rolar_para(alvo_y))

    def _rolar_para(self, y):
        barra = self.rolagem.verticalScrollBar()
        topo_img = max(0, (self.imagem.height() - self.imagem.pixmap().deviceIndependentSize().height()) / 2)
        barra.setValue(int(topo_img + y - self.rolagem.viewport().height() / 2))

    # ------------------------------------------------------------ busca (estilo Ctrl+F)
    def _procurar_tudo(self, texto):
        """Acha todas as ocorrências do documento: [(pagina, [retângulos])]."""
        achados = []
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            for p in range(self.total):
                tp = self.doc[p].get_textpage()
                busca = tp.search(texto, match_case=False)
                while (achou := busca.get_next()) is not None:
                    inicio, qtd = achou
                    n = tp.count_rects(inicio, qtd)
                    achados.append((p, [tp.get_rect(k) for k in range(n)]))
        finally:
            QApplication.restoreOverrideCursor()
        return achados

    def buscar(self, voltar=False):
        texto = self.busca.text().strip()
        if not texto:
            self.limpar_busca()
            return
        if texto != self._termo:
            self._termo = texto
            self.achados = self._procurar_tudo(texto)
            # começa na primeira ocorrência a partir da página atual
            self.achado_atual = next((k for k, a in enumerate(self.achados) if a[0] >= self.pagina), 0)
        elif self.achados:
            passo = -1 if voltar else 1
            self.achado_atual = (self.achado_atual + passo) % len(self.achados)
        if not self.achados:
            self.status.setText(f"Nenhuma ocorrência de \"{texto}\"")
            self.busca.setStyleSheet("background: #5a2020;")
            self.desenhar()
            return
        self.busca.setStyleSheet("")
        pagina = self.achados[self.achado_atual][0]
        paginas = len({a[0] for a in self.achados})
        self.status.setText(f"{self.achado_atual + 1} de {len(self.achados)} "
                            f"(em {paginas} página{'s' if paginas > 1 else ''})")
        if pagina != self.pagina:
            self.pagina = pagina
        self.desenhar()

    def limpar_busca(self):
        self._termo = ""
        self.achados = []
        self.achado_atual = -1
        self.status.setText("")
        self.busca.setStyleSheet("")
        self.desenhar()


# ====================================================================== janela
class AbaFichas(QWidget):
    """📄 Fichas: MODELOS em branco (de qualquer sistema) + as fichas preenchidas dos personagens."""

    def __init__(self, parent=None):
        super().__init__(parent)
        from .fichas_pdf import JanelaFichasPDF, pasta_fichas
        self._pasta_fichas = pasta_fichas
        dica = QLabel("<b>Modelos</b>: a ficha em branco do seu sistema (PDF editável). "
                      "<b>Nova ficha</b> cria uma cópia pra preencher. Tudo fica no seu PC.")
        dica.setWordWrap(True)
        dica.setObjectName("dica")
        self.modelos = QListWidget()
        self.modelos.setMaximumHeight(150)
        self.modelos.itemDoubleClicked.connect(lambda _it: self._nova())
        linha = QHBoxLayout()
        for texto, f, prim in (("＋ Importar modelo…", self._importar_modelo, False),
                               ("📄 Nova ficha deste modelo", self._nova, True),
                               ("🗑", self._apagar_modelo, False)):
            b = QPushButton(texto)
            if prim:
                b.setObjectName("primario")
            if texto == "🗑":
                b.setToolTip("Apagar o modelo")
            b.clicked.connect(f)
            linha.addWidget(b)
        linha.addStretch()
        # as fichas preenchidas: a mesma lista de sempre (Arquivo → Fichas em PDF), aqui dentro
        self.fichas = JanelaFichasPDF(self)
        self.fichas.setWindowFlags(Qt.WindowType.Widget)
        lay = QVBoxLayout(self)
        lay.addWidget(dica)
        titulo = QLabel("Modelos (em branco)")
        titulo.setObjectName("subtitulo")
        lay.addWidget(titulo)
        lay.addWidget(self.modelos)
        lay.addLayout(linha)
        titulo = QLabel("Fichas dos personagens")
        titulo.setObjectName("subtitulo")
        lay.addWidget(titulo)
        lay.addWidget(self.fichas, 1)
        self._recarregar_modelos()
        from .acabamento import iconizar
        iconizar(self)

    def _pasta_modelos(self) -> str:
        pasta = os.path.join(os.path.dirname(self._pasta_fichas()), "Fichas - modelos")
        os.makedirs(pasta, exist_ok=True)
        return pasta

    def _recarregar_modelos(self):
        self.modelos.clear()
        for a in sorted(os.listdir(self._pasta_modelos()), key=str.casefold):
            if a.lower().endswith(".pdf"):
                it = item_com_icone(QListWidgetItem(), "📋 " + os.path.splitext(a)[0])
                it.setData(Qt.ItemDataRole.UserRole, os.path.join(self._pasta_modelos(), a))
                self.modelos.addItem(it)

    def _modelo(self):
        it = self.modelos.currentItem()
        return it.data(Qt.ItemDataRole.UserRole) if it else None

    def _importar_modelo(self):
        import shutil
        from .fichas_pdf import _livre
        caminho, _ = QFileDialog.getOpenFileName(self, "Importar modelo de ficha (PDF)", "", "PDF (*.pdf)")
        if caminho:
            shutil.copy2(caminho, _livre(self._pasta_modelos(), os.path.splitext(os.path.basename(caminho))[0]))
            self._recarregar_modelos()

    def _nova(self):
        import shutil
        from PyQt6.QtWidgets import QInputDialog
        from .fichas_pdf import _livre
        modelo = self._modelo()
        if not modelo:
            QMessageBox.information(self, "Escolha um modelo", "Importe ou escolha um modelo de ficha primeiro.")
            return
        nome, ok = QInputDialog.getText(self, "Nova ficha", "Nome do personagem:")
        if not ok or not nome.strip():
            return
        destino = _livre(self._pasta_fichas(), nome.strip())
        shutil.copy2(modelo, destino)
        self.fichas.recarregar(destino)
        self.fichas.abrir()

    def _apagar_modelo(self):
        m = self._modelo()
        if m and QMessageBox.question(self, "Apagar modelo", f"Apagar o modelo “{os.path.basename(m)}”?\n"
                                      "(As fichas feitas com ele continuam.)") == QMessageBox.StandardButton.Yes:
            os.remove(m)
            self._recarregar_modelos()


def _abrir_leitor(dono, caminho):
    if not caminho or not os.path.isfile(caminho):
        return
    try:
        janela = LeitorPdf(caminho)
    except Exception as erro:  # PDF protegido, corrompido...
        QMessageBox.warning(dono, "Não deu", f"Não consegui abrir esse PDF:\n{erro}")
        return
    janela.show()
    dono.janelas.append(janela)


class AbaDoMestre(QWidget):
    """📗 Do mestre (jogador): os livros que o mestre liberou pra você."""

    def __init__(self, livros, parent=None):
        super().__init__(parent)
        self.livros = livros
        self.janelas = []
        dica = QLabel("Livros que o mestre liberou pra você. Se ele tirar a liberação, o livro some daqui.")
        dica.setWordWrap(True)
        dica.setObjectName("dica")
        self.lista = QListWidget()
        self.lista.itemDoubleClicked.connect(lambda it: _abrir_leitor(self, it.data(Qt.ItemDataRole.UserRole)))
        abrir = QPushButton("Abrir")
        abrir.setObjectName("primario")
        abrir.clicked.connect(lambda: self.lista.currentItem() and
                              _abrir_leitor(self, self.lista.currentItem().data(Qt.ItemDataRole.UserRole)))
        lay = QVBoxLayout(self)
        lay.addWidget(dica)
        lay.addWidget(self.lista, 1)
        lay.addWidget(abrir)
        livros.mudou.connect(self.recarregar)
        self.recarregar()

    def recarregar(self):
        atual = self.lista.currentRow()
        self.lista.clear()
        for d in self.livros.livros():
            if d["progresso"] is not None:
                texto = f"📥 {d['titulo']}   (chegando… {int(d['progresso'] * 100)}%)"
            elif d["caminho"]:
                texto = f"📗 {d['titulo']}"
            else:
                texto = f"📥 {d['titulo']}   (esperando o mestre mandar)"
            it = item_com_icone(QListWidgetItem(), texto)
            it.setData(Qt.ItemDataRole.UserRole, d["caminho"])
            self.lista.addItem(it)
        if self.lista.count() == 0:
            self.lista.addItem("(o mestre ainda não liberou nenhum livro)")
        self.lista.setCurrentRow(max(0, atual))


class AbaDosJogadores(QWidget):
    """👥 Dos jogadores (mestre): a biblioteca de cada jogador conectado + as cópias que você pegou."""

    def __init__(self, livros, parent=None):
        super().__init__(parent)
        self.livros = livros
        self.janelas = []
        dica = QLabel("A lista de PDFs de cada jogador conectado. <b>📥 Pegar uma cópia</b> traz o arquivo pra "
                      "você (o jogador é avisado). As cópias ficam em Documentos/Taverna/Livros dos jogadores.")
        dica.setWordWrap(True)
        dica.setObjectName("dica")
        self.arvore = QTreeWidget()
        self.arvore.setHeaderHidden(True)
        self.arvore.itemDoubleClicked.connect(lambda it, _c: self._acao(it))
        pegar = QPushButton("📥  Pegar uma cópia / abrir")
        pegar.setObjectName("primario")
        pegar.clicked.connect(lambda: self._acao(self.arvore.currentItem()))
        lay = QVBoxLayout(self)
        lay.addWidget(dica)
        lay.addWidget(self.arvore, 1)
        lay.addWidget(pegar)
        livros.biblioteca_jogador.connect(lambda _n: self.recarregar())
        livros.copia_recebida.connect(lambda _n, _c: self.recarregar())
        self.recarregar()

    def _copias(self, nome) -> dict:
        pasta = self.livros.pasta_copias(nome)
        return {os.path.splitext(a)[0]: os.path.join(pasta, a) for a in os.listdir(pasta)
                if a.lower().endswith(".pdf")}

    def recarregar(self):
        from ..rede.livros import _nome_arquivo
        self.arvore.clear()
        for nome, lista in sorted(self.livros.dos_jogadores.items(), key=lambda kv: kv[0].casefold()):
            topo = QTreeWidgetItem(self.arvore)
            item_com_icone(topo, f"👤 {nome}   ({len(lista)})", 0)
            copias = self._copias(nome)
            for d in lista:
                tem = copias.get(_nome_arquivo(d["titulo"]))
                it = QTreeWidgetItem(topo)
                item_com_icone(it, ("📗 " if tem else "📕 ") + d["titulo"] + ("   (cópia com você)" if tem else ""), 0)
                it.setData(0, Qt.ItemDataRole.UserRole, (nome, d["id"], tem))
            topo.setExpanded(True)
        if self.arvore.topLevelItemCount() == 0:
            QTreeWidgetItem(self.arvore, ["(nenhum jogador conectado)"])

    def _acao(self, item):
        dado = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if not dado:
            return
        nome, ident, copia = dado
        if copia:
            _abrir_leitor(self, copia)
        elif self.livros.pedir_copia(nome, ident):
            QMessageBox.information(self, "Pedido", f"Pedi a cópia pro {nome}. Ela aparece aqui quando chegar.")


class JanelaBiblioteca(QMainWindow):
    def __init__(self, mestre: bool, parent=None, livros=None, jogadores=None):
        super().__init__(parent)
        self.setWindowTitle("📚 Biblioteca — Taverna")
        self.resize(1000, 720)
        self.abas = QTabWidget()
        self.pdfs = AbaMeusPdfs("Mestre" if mestre else "Player",
                                livros_mestre=livros if mestre else None, jogadores=jogadores)
        self.abas.addTab(self.pdfs, "📕 PDFs")
        self.do_mestre = self.dos_jogadores = None
        if livros is not None and not mestre:
            self.do_mestre = AbaDoMestre(livros)
            self.abas.addTab(self.do_mestre, "📗 Do mestre")
            self.pdfs.mudou.connect(livros.enviar_minha_biblioteca)   # o mestre vê a lista nova
        self.fichas = AbaFichas()
        self.abas.addTab(self.fichas, "📄 Fichas")
        self.tokens = None
        if mestre:
            from .biblioteca_tokens import AbaTokens
            self.tokens = AbaTokens()
            self.abas.addTab(self.tokens, "🧙 Tokens")
            if livros is not None:
                self.dos_jogadores = AbaDosJogadores(livros)
                self.abas.addTab(self.dos_jogadores, "👥 Dos jogadores")
        self.setCentralWidget(self.abas)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def mostrar_tokens(self):
        if self.tokens is not None:
            self.abas.setCurrentWidget(self.tokens)
