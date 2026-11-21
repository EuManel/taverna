"""
🌍 Montar a cidade e o mundo (v0.62 — item 9, etapa 1).

À esquerda: o mundo e as cidades (importar imagem, renomear, remover). À direita: a imagem escolhida, com três
ferramentas:
  - Olhar: arrastar e rodinha;
  - Marcar lugar: arraste um retângulo → escolha qual ABA fica ali (na cidade) ou qual CIDADE (no mundo);
  - Calibrar escala: trace uma linha → diga quanto ela mede (metros na cidade, km no mundo).
Embaixo, a lista dos lugares marcados (dá pra remover).
"""

import os

from PyQt6.QtCore import QLineF, QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (QButtonGroup, QDialog, QFileDialog, QGraphicsLineItem, QGraphicsPixmapItem,
                             QGraphicsRectItem, QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView,
                             QHBoxLayout, QInputDialog, QLabel, QListWidget, QListWidgetItem, QMessageBox,
                             QPushButton, QRadioButton, QSplitter, QVBoxLayout, QWidget)

from ..config import COR_DESTAQUE
from ..mesa import atlas as A

FILTRO_IMAGEM = "Imagens (*.png *.jpg *.jpeg *.webp *.bmp)"


class _Editor(QGraphicsView):
    retangulo = pyqtSignal(QRectF)
    linha = pyqtSignal(QLineF)

    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setBackgroundBrush(QColor(24, 20, 16))
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.ferramenta = "olhar"
        self._ini = None
        self._previa = None
        self._definir_arrasto()

    def _definir_arrasto(self):
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag if self.ferramenta == "olhar"
                         else QGraphicsView.DragMode.NoDrag)
        self.viewport().setCursor(Qt.CursorShape.OpenHandCursor if self.ferramenta == "olhar"
                                  else Qt.CursorShape.CrossCursor)

    def definir_ferramenta(self, nome):
        self.ferramenta = nome
        self._definir_arrasto()

    def wheelEvent(self, ev):
        f = 1.15 ** (ev.angleDelta().y() / 120.0)
        self.scale(f, f)

    def mousePressEvent(self, ev):
        if self.ferramenta != "olhar" and ev.button() == Qt.MouseButton.LeftButton:
            self._ini = self.mapToScene(ev.position().toPoint())
            caneta = QPen(QColor(COR_DESTAQUE), 2)
            caneta.setCosmetic(True)
            if self.ferramenta == "lugar":
                self._previa = self.scene().addRect(QRectF(self._ini, self._ini), caneta)
            else:
                self._previa = self.scene().addLine(QLineF(self._ini, self._ini), caneta)
            return
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self._ini is not None and self._previa is not None:
            p = self.mapToScene(ev.position().toPoint())
            if isinstance(self._previa, QGraphicsRectItem):
                self._previa.setRect(QRectF(self._ini, p).normalized())
            else:
                self._previa.setLine(QLineF(self._ini, p))
            return
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        if self._ini is not None:
            p = self.mapToScene(ev.position().toPoint())
            ini, self._ini = self._ini, None
            if self._previa is not None:
                self.scene().removeItem(self._previa)
                self._previa = None
            if self.ferramenta == "lugar":
                r = QRectF(ini, p).normalized()
                if r.width() > 3 and r.height() > 3:
                    self.retangulo.emit(r)
            elif QLineF(ini, p).length() > 3:
                self.linha.emit(QLineF(ini, p))
            return
        super().mouseReleaseEvent(ev)


class JanelaAtlas(QDialog):
    def __init__(self, janela):
        super().__init__(janela)
        self.janela = janela
        self.setWindowTitle("Cidade e mundo")
        self.resize(1050, 680)
        self.atual: dict | None = None
        lay = QHBoxLayout(self)
        div = QSplitter(Qt.Orientation.Horizontal)
        lay.addWidget(div)

        esq = QWidget()
        le = QVBoxLayout(esq)
        le.addWidget(QLabel("<b>Mapas</b>"))
        self.lista = QListWidget()
        self.lista.currentItemChanged.connect(lambda *_: self._escolher())
        le.addWidget(self.lista, 1)
        for texto, f in (("🗺 Importar mapa-múndi…", lambda: self.importar("mundo")),
                         ("🗺 Nova cidade…", lambda: self.importar("cidade")),
                         ("✏ Renomear…", self.renomear), ("🗑 Remover", self.remover)):
            b = QPushButton(texto)
            b.clicked.connect(f)
            le.addWidget(b)
        dica = QLabel("Dica: dando zoom out na mesa, o cenário vira um retângulo dentro da cidade; mais zoom out, "
                      "a cidade vira um ponto no mundo.")
        dica.setWordWrap(True)
        dica.setStyleSheet("color: #a89878;")
        le.addWidget(dica)
        div.addWidget(esq)

        dir_ = QWidget()
        ld = QVBoxLayout(dir_)
        ferr = QHBoxLayout()
        self.grupo = QButtonGroup(self)
        for chave, texto in (("olhar", "✋ Olhar"), ("lugar", "Marcar lugar"), ("escala", "Calibrar escala")):
            r = QRadioButton(texto)
            r.setChecked(chave == "olhar")
            r.toggled.connect(lambda on, k=chave: on and self.editor.definir_ferramenta(k))
            self.grupo.addButton(r)
            ferr.addWidget(r)
        ferr.addStretch(1)
        self.info = QLabel("")
        ferr.addWidget(self.info)
        ld.addLayout(ferr)
        self.editor = _Editor()
        self.editor.retangulo.connect(self._marcou)
        self.editor.linha.connect(self._tracou)
        ld.addWidget(self.editor, 1)
        ld.addWidget(QLabel("Lugares marcados neste mapa:"))
        self.lugares = QListWidget()
        self.lugares.setMaximumHeight(130)
        ld.addWidget(self.lugares)
        b = QPushButton("🗑 Tirar o lugar escolhido")
        b.clicked.connect(self.remover_lugar)
        ld.addWidget(b)
        div.addWidget(dir_)
        div.setSizes([260, 790])
        self.recarregar()
        from .acabamento import iconizar
        iconizar(self)

    # ================================================================ dados
    @property
    def atlas(self):
        return self.janela.atlas

    def _mudou(self):
        self.janela.atlas_editado()
        self.recarregar(manter=self.atual["id"] if self.atual else None)

    def recarregar(self, manter: str | None = None):
        self.lista.blockSignals(True)
        self.lista.clear()
        for n in self.atlas.niveis():
            rotulo = ("Mundo: " if n["tipo"] == "mundo" else "Cidade: ") + (n.get("nome") or "")
            it = QListWidgetItem(rotulo)
            it.setData(Qt.ItemDataRole.UserRole, n["id"])
            self.lista.addItem(it)
            if n["id"] == manter:
                self.lista.setCurrentItem(it)
        if self.lista.currentRow() < 0 and self.lista.count():
            self.lista.setCurrentRow(0)
        self.lista.blockSignals(False)
        self._escolher()

    def _escolher(self):
        it = self.lista.currentItem()
        self.atual = self.atlas.nivel(it.data(Qt.ItemDataRole.UserRole)) if it else None
        self._desenhar()

    def _desenhar(self):
        cena = self.editor.scene()
        cena.clear()
        self.lugares.clear()
        if self.atual is None:
            self.info.setText("Importe um mapa-múndi ou crie uma cidade.")
            return
        pm = self.atlas.pixmap(self.atual)
        cena.addItem(QGraphicsPixmapItem(pm))
        cena.setSceneRect(QRectF(pm.rect()).adjusted(-200, -200, 200, 200))
        caneta = QPen(QColor(COR_DESTAQUE), 2)
        caneta.setCosmetic(True)
        for l in self.atual["lugares"]:
            r = A.ret(l)
            cena.addRect(r, caneta, QBrush(QColor(232, 194, 90, 40)))
            t = QGraphicsSimpleTextItem(self._nome_lugar(l))
            t.setBrush(QColor(COR_DESTAQUE))
            f = QFont()
            f.setBold(True)
            t.setFont(f)
            t.setFlag(t.GraphicsItemFlag.ItemIgnoresTransformations)
            t.setPos(r.topLeft() + QPointF(2, 2))
            cena.addItem(t)
            it = QListWidgetItem(self._nome_lugar(l))
            it.setData(Qt.ItemDataRole.UserRole, l["id"])
            self.lugares.addItem(it)
        self.editor.fitInView(QRectF(pm.rect()), Qt.AspectRatioMode.KeepAspectRatio)
        un = A.UNIDADE[self.atual["tipo"]]
        if self.atual.get("escala"):
            self.info.setText(f"Escala: 100 px = {self.atual['escala'] * 100:.3g} {un}".replace(".", ","))
        else:
            self.info.setText(f"Sem escala ainda (Calibrar escala: trace uma linha e diga quantos {un} ela mede)")

    def _nome_lugar(self, l) -> str:
        if l.get("nome"):
            return l["nome"]
        n = self.atlas.nivel(l["alvo"])
        if n is not None:
            return n.get("nome", "")
        cena = self._cena_do_alvo(l["alvo"])
        return getattr(cena, "nome_aba", "(aba apagada)") if cena is not None else "(aba apagada)"

    def _cena_do_alvo(self, alvo):
        for c in self.janela.cenas:
            if A.chave_da_cena(c) == alvo:
                return c
        return None

    # ================================================================ ações (também chamadas nos testes)
    def importar(self, tipo: str, caminho: str | None = None, nome: str | None = None):
        if tipo == "mundo" and self.atlas.mundo is not None:
            r = QMessageBox.question(self, "Mapa-múndi", "Já tem um mapa-múndi. Trocar a imagem? "
                                     "(os lugares marcados nele continuam)") if caminho is None else \
                QMessageBox.StandardButton.Yes
            if r != QMessageBox.StandardButton.Yes:
                return None
        if caminho is None:
            caminho, _ = QFileDialog.getOpenFileName(self, "Imagem do " + ("mundo" if tipo == "mundo" else "mapa da cidade"),
                                                     "", FILTRO_IMAGEM)
            if not caminho:
                return None
        if nome is None:
            sugestao = os.path.splitext(os.path.basename(caminho))[0]
            nome, ok = QInputDialog.getText(self, "Nome", "Nome do mundo:" if tipo == "mundo" else "Nome da cidade:",
                                            text=sugestao)
            if not ok:
                return None
        try:
            with open(caminho, "rb") as f:
                novo = A.novo_nivel(tipo, nome.strip() or tipo.title(), f.read())
        except (OSError, ValueError) as erro:
            QMessageBox.warning(self, "Não deu", f"Não consegui abrir a imagem:\n{erro}")
            return None
        if tipo == "mundo":
            if self.atlas.mundo is not None:   # troca só a imagem
                self.atlas.mundo["imagem"], self.atlas.mundo["nome"] = novo["imagem"], novo["nome"]
                novo = self.atlas.mundo
            else:
                self.atlas.mundo = novo
        else:
            self.atlas.cidades.append(novo)
        self.atual = novo
        self._mudou()
        return novo

    def renomear(self):
        if self.atual is None:
            return
        nome, ok = QInputDialog.getText(self, "Renomear", "Nome:", text=self.atual.get("nome", ""))
        if ok and nome.strip():
            self.atual["nome"] = nome.strip()
            self._mudou()

    def remover(self):
        if self.atual is None:
            return
        if QMessageBox.question(self, "Remover", f"Remover “{self.atual.get('nome')}” e os lugares marcados nele?") \
                != QMessageBox.StandardButton.Yes:
            return
        self.atlas.remover_nivel(self.atual["id"])
        self.atual = None
        self._mudou()

    def remover_lugar(self):
        it = self.lugares.currentItem()
        if it is None or self.atual is None:
            return
        self.atlas.remover_lugar(self.atual, it.data(Qt.ItemDataRole.UserRole))
        self._mudou()

    def opcoes_de_alvo(self) -> list[tuple[str, str]]:
        """(rótulo, alvo) que dá pra pôr num lugar deste mapa: abas (prédio = um só) ou cidades."""
        if self.atual is None:
            return []
        if self.atual["tipo"] == "mundo":
            return [(c.get("nome", ""), c["id"]) for c in self.atlas.cidades]
        vistos, saida = set(), []
        for c in self.janela.cenas:
            chave = A.chave_da_cena(c)
            if chave in vistos:
                continue
            vistos.add(chave)
            andares = [x for x in self.janela.cenas if A.chave_da_cena(x) == chave]
            rotulo = c.nome_aba + (f"  (prédio, {len(andares)} andares)" if len(andares) > 1 else "")
            saida.append((rotulo, chave))
        return saida

    def _marcou(self, r: QRectF, alvo: str | None = None):
        opcoes = self.opcoes_de_alvo()
        if not opcoes:
            QMessageBox.information(self, "Marcar lugar", "Crie uma cidade primeiro (no mundo, cada lugar é uma cidade).")
            return None
        if alvo is None:
            rotulos = [o[0] for o in opcoes]
            pergunta = "Qual cidade fica aqui?" if self.atual["tipo"] == "mundo" else "Qual aba (cenário) fica aqui?"
            escolha, ok = QInputDialog.getItem(self, "Marcar lugar", pergunta, rotulos, 0, False)
            if not ok:
                return None
            alvo = opcoes[rotulos.index(escolha)][1]
        lugar = self.atlas.ligar(self.atual, r, alvo)
        self._mudou()
        return lugar

    def _tracou(self, linha: QLineF, distancia: float | None = None):
        if self.atual is None:
            return
        un = A.UNIDADE[self.atual["tipo"]]
        if distancia is None:
            distancia, ok = QInputDialog.getDouble(self, "Calibrar escala", f"Quantos {un} essa linha mede?",
                                                   100.0 if un == "m" else 10.0, 0.01, 1e7, 2)
            if not ok:
                return
        A.Atlas.calibrar(self.atual, linha.length(), distancia)
        self._mudou()
