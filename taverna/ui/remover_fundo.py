"""
✂ Removedor de fundo (Etapa 13 + IA na v0.47).

- 🧠 Com IA (v0.47): recorta a figura sozinho, até em fundo cheio de detalhes (`taverna/ia/`).
  Dois modelos: Rápido (~4,6 MB) e Caprichado (~170 MB); baixados só quando o usuário pede.
- 🪄 Automático: pega a cor que mais aparece nas bordas e apaga o fundo ligado a ela.
- 🎯 Clicar numa cor: apaga a região daquela cor ligada ao clique (ou a cor na imagem toda).
- 🧽 Borracha: apaga na mão, arrastando.
- Tolerância, suavizar a borda, desfazer e voltar ao original.
"""

import numpy as np
from PyQt6.QtCore import QBuffer, QIODevice, QPointF, QRectF, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QImage, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QDialog, QHBoxLayout, QLabel, QMessageBox,
                             QProgressBar, QPushButton, QSlider, QVBoxLayout, QWidget)


class _TrabalhoIA(QThread):
    """Roda a IA (ou baixa o modelo) fora da tela, pra janela não travar."""
    progresso = pyqtSignal(float)
    pronto = pyqtSignal(object)    # máscara (np.ndarray) / caminho do modelo baixado
    falhou = pyqtSignal(str)

    def __init__(self, tarefa, chave, arr=None, parent=None):
        super().__init__(parent)
        self.tarefa, self.chave, self.arr = tarefa, chave, arr
        self.parar = False

    def run(self):
        from ..ia import recorte
        try:
            if self.tarefa == "baixar":
                r = recorte.baixar_modelo(self.chave, self.progresso.emit, lambda: self.parar)
            else:
                r = recorte.mascara(self.arr, self.chave, self.progresso.emit, lambda: self.parar)
            if not self.parar:
                self.pronto.emit(r)
        except InterruptedError:
            pass
        except Exception as erro:   # noqa: BLE001 — sem internet, arquivo ruim, memória…
            if not self.parar:
                self.falhou.emit(str(erro) or erro.__class__.__name__)

LADO_MAXIMO = 2048   # imagens maiores são reduzidas (fica rápido e leve)


# ====================================================================== contas (numpy)
def _para_array(img: QImage) -> np.ndarray:
    img = img.convertToFormat(QImage.Format.Format_RGBA8888)
    w, h = img.width(), img.height()
    ptr = img.constBits()
    ptr.setsize(img.sizeInBytes())
    arr = np.frombuffer(ptr, np.uint8).reshape(h, img.bytesPerLine())[:, :w * 4].reshape(h, w, 4)
    return arr.copy()


def _para_qimage(arr: np.ndarray) -> QImage:
    h, w, _ = arr.shape
    arr = np.ascontiguousarray(arr)
    return QImage(arr.data, w, h, w * 4, QImage.Format.Format_RGBA8888).copy()


def _parecidos(arr: np.ndarray, cor, tol: int) -> np.ndarray:
    """Pixels com cor perto de `cor` (diferença máxima por canal <= tol) e ainda visíveis."""
    dif = np.abs(arr[:, :, :3].astype(np.int16) - np.array(cor[:3], np.int16)).max(axis=2)
    return (dif <= tol) & (arr[:, :, 3] > 0)


def preencher(mascara: np.ndarray, sementes) -> np.ndarray:
    """Balde de tinta (scanline): pixels da máscara ligados às sementes."""
    h, w = mascara.shape
    cheio = np.zeros_like(mascara)
    pilha = [(y, x) for y, x in sementes if 0 <= y < h and 0 <= x < w and mascara[y, x]]
    while pilha:
        y, x = pilha.pop()
        if cheio[y, x] or not mascara[y, x]:
            continue
        linha = mascara[y]
        esq = linha[:x + 1][::-1]
        e = x - (int(np.argmin(esq)) - 1 if not esq.all() else x)
        dirr = linha[x:]
        d = x + (int(np.argmin(dirr)) - 1 if not dirr.all() else len(dirr) - 1)
        cheio[y, e:d + 1] = True
        for ny in (y - 1, y + 1):
            if 0 <= ny < h:
                seg = mascara[ny, e:d + 1] & ~cheio[ny, e:d + 1]
                if seg.any():
                    inicio = seg & ~np.concatenate(([False], seg[:-1]))
                    pilha.extend((ny, e + int(i)) for i in np.flatnonzero(inicio))
    return cheio


def cor_da_borda(arr: np.ndarray):
    """A cor mais comum nas bordas (arredondada), ignorando o que já é transparente."""
    borda = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]])
    borda = borda[borda[:, 3] > 0]
    if not len(borda):
        return None
    q = (borda[:, :3] // 16).astype(np.int32)
    chave = q[:, 0] * 256 + q[:, 1] * 16 + q[:, 2]
    valores, contagem = np.unique(chave, return_counts=True)
    escolhida = valores[np.argmax(contagem)]
    return tuple(int(c) for c in borda[chave == escolhida][:, :3].mean(axis=0))


def apagar(arr: np.ndarray, area: np.ndarray, suavizar: bool) -> np.ndarray:
    novo = arr.copy()
    novo[area, 3] = 0
    if suavizar:
        # quem encosta na área apagada fica meio transparente (borda menos serrilhada)
        viz = np.zeros_like(area)
        viz[1:] |= area[:-1]
        viz[:-1] |= area[1:]
        viz[:, 1:] |= area[:, :-1]
        viz[:, :-1] |= area[:, 1:]
        borda = viz & ~area & (novo[:, :, 3] > 0)
        novo[borda, 3] = (novo[borda, 3].astype(np.uint16) * 55 // 100).astype(np.uint8)
    return novo


def remover_automatico(arr: np.ndarray, tol: int = 40, suavizar: bool = True) -> np.ndarray:
    cor = cor_da_borda(arr)
    if cor is None:
        return arr
    h, w = arr.shape[:2]
    masc = _parecidos(arr, cor, tol)
    sementes = [(0, x) for x in range(w)] + [(h - 1, x) for x in range(w)] + \
               [(y, 0) for y in range(h)] + [(y, w - 1) for y in range(h)]
    sementes = [(y, x) for y, x in sementes if masc[y, x]]
    return apagar(arr, preencher(masc, sementes), suavizar)


def imagem_png(img: QImage) -> bytes:
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG")
    return bytes(buf.data())


# ====================================================================== tela
class _Tela(QWidget):
    clicou = pyqtSignal(int, int)          # pixel (x, y)
    borracha = pyqtSignal(int, int, bool)  # pixel, começando?

    def __init__(self):
        super().__init__()
        self.img = QImage()
        self.modo = "cor"   # "cor" ou "borracha"
        self.raio = 12
        self.setMinimumSize(420, 360)
        self.setMouseTracking(True)
        self._mouse = None
        self._xadrez = QPixmap(20, 20)
        self._xadrez.fill(QColor("#cfcfcf"))
        p = QPainter(self._xadrez)
        p.fillRect(0, 0, 10, 10, QColor("#9a9a9a"))
        p.fillRect(10, 10, 10, 10, QColor("#9a9a9a"))
        p.end()

    def _area(self) -> QRectF:
        if self.img.isNull():
            return QRectF()
        esc = min(self.width() / self.img.width(), self.height() / self.img.height())
        w, h = self.img.width() * esc, self.img.height() * esc
        return QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h)

    def _pixel(self, pos):
        a = self._area()
        if a.isEmpty() or not a.contains(pos):
            return None
        return (int((pos.x() - a.left()) / a.width() * self.img.width()),
                int((pos.y() - a.top()) / a.height() * self.img.height()))

    def paintEvent(self, ev):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#1a1612"))
        a = self._area()
        if not a.isEmpty():
            p.fillRect(a, QBrush(self._xadrez))
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            p.drawImage(a, self.img)
        if self.modo == "borracha" and self._mouse is not None and not a.isEmpty():
            r = self.raio * a.width() / self.img.width()
            p.setPen(QPen(QColor("#ffffff"), 1.5, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(self._mouse, r, r)
        p.end()

    def mousePressEvent(self, ev):
        px = self._pixel(ev.position())
        if px is None:
            return
        if self.modo == "cor":
            self.clicou.emit(*px)
        else:
            self.borracha.emit(px[0], px[1], True)

    def mouseMoveEvent(self, ev):
        self._mouse = ev.position()
        if self.modo == "borracha":
            if ev.buttons() & Qt.MouseButton.LeftButton:
                px = self._pixel(ev.position())
                if px is not None:
                    self.borracha.emit(px[0], px[1], False)
            self.update()

    def leaveEvent(self, ev):
        self._mouse = None
        self.update()


class DialogoRemoverFundo(QDialog):
    """Abre com os bytes da imagem; depois de OK, `resultado()` devolve o PNG sem fundo."""

    def __init__(self, dados: bytes, titulo: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("✂ Remover fundo" + (f" — {titulo}" if titulo else ""))
        self.resize(940, 680)
        img = QImage.fromData(dados)
        if max(img.width(), img.height()) > LADO_MAXIMO:
            img = img.scaled(LADO_MAXIMO, LADO_MAXIMO, Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
        self.original = _para_array(img)
        self.arr = self.original.copy()
        self.desfazer_pilha = []

        raiz = QHBoxLayout(self)
        self.tela = _Tela()
        self.tela.clicou.connect(self._clicou)
        self.tela.borracha.connect(self._apagar_mao)
        raiz.addWidget(self.tela, 1)

        lado = QVBoxLayout()
        self._criar_ia(lado)
        lado.addSpacing(8)
        lado.addWidget(QLabel("<b>Sem IA</b>"))
        b = QPushButton("🪄 Automático")
        b.setToolTip("Apaga o fundo a partir das bordas da imagem (bom pra fundo liso: branco, verde…)")
        b.clicked.connect(self._automatico)
        lado.addWidget(b)
        lado.addSpacing(6)
        lado.addWidget(QLabel("<b>Ferramenta</b>"))
        self.grupo = QButtonGroup(self)
        self.b_cor = QPushButton("🎯 Clicar numa cor")
        self.b_cor.setToolTip("Clique no fundo: apaga aquela cor (a parte ligada ao clique)")
        self.b_borracha = QPushButton("🧽 Borracha")
        self.b_borracha.setToolTip("Arraste pra apagar na mão")
        for k, bt in enumerate((self.b_cor, self.b_borracha)):
            bt.setCheckable(True)
            self.grupo.addButton(bt, k)
            lado.addWidget(bt)
        self.b_cor.setChecked(True)
        self.grupo.idClicked.connect(lambda i: self._modo("cor" if i == 0 else "borracha"))
        self.ck_tudo = QCheckBox("Apagar essa cor na imagem toda")
        self.ck_tudo.setToolTip("Desligado: só a região ligada ao clique.\nLigado: todo pixel parecido, até 'ilhas' no meio.")
        lado.addWidget(self.ck_tudo)
        lado.addSpacing(6)
        lado.addWidget(QLabel("Tolerância (quão parecida a cor)"))
        self.tol = QSlider(Qt.Orientation.Horizontal)
        self.tol.setRange(0, 120)
        self.tol.setValue(40)
        lado.addWidget(self.tol)
        lado.addWidget(QLabel("Tamanho da borracha"))
        self.raio = QSlider(Qt.Orientation.Horizontal)
        self.raio.setRange(2, 80)
        self.raio.setValue(12)
        self.raio.valueChanged.connect(lambda v: setattr(self.tela, "raio", v))
        lado.addWidget(self.raio)
        self.ck_suave = QCheckBox("Suavizar a borda")
        self.ck_suave.setChecked(True)
        lado.addWidget(self.ck_suave)
        lado.addSpacing(6)
        linha = QHBoxLayout()
        b = QPushButton("↶ Desfazer")
        b.clicked.connect(self._desfazer)
        linha.addWidget(b)
        b = QPushButton("⟲ Original")
        b.clicked.connect(self._original)
        linha.addWidget(b)
        lado.addLayout(linha)
        self.info = QLabel()
        self.info.setWordWrap(True)
        lado.addWidget(self.info)
        lado.addStretch(1)
        dica = QLabel("Dica: a IA faz o grosso; a borracha e o \"Clicar numa cor\" limpam o que sobrar.")
        dica.setWordWrap(True)
        dica.setStyleSheet("font-size: 11px;")
        lado.addWidget(dica)
        linha = QHBoxLayout()
        b = QPushButton("Cancelar")
        b.clicked.connect(self.reject)
        linha.addWidget(b)
        b = QPushButton("✔ Usar")
        b.setObjectName("primario")
        b.clicked.connect(self.accept)
        linha.addWidget(b)
        lado.addLayout(linha)
        caixa = QWidget()
        caixa.setLayout(lado)
        caixa.setFixedWidth(270)
        raiz.addWidget(caixa)
        self._mostrar()
        self._atualizar_ia()
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    # ------------------------------------------------------------ 🧠 IA (v0.47)
    def _criar_ia(self, lado):
        from ..ia.recorte import MODELOS
        self._trabalho = None
        self._mascara_ia = None     # (máscara, imagem antes da IA) — a firmeza reaplica sem rodar de novo
        lado.addWidget(QLabel("<b>Com IA</b> (recorta a figura sozinho)"))
        self.cb_modelo = QComboBox()
        for chave, (nome, _a, mb, *_r, desc) in MODELOS.items():
            self.cb_modelo.addItem(f"{nome} (~{mb:g} MB)".replace(".", ","), chave)
            self.cb_modelo.setItemData(self.cb_modelo.count() - 1, desc, Qt.ItemDataRole.ToolTipRole)
        self.cb_modelo.currentIndexChanged.connect(lambda _i: self._atualizar_ia())
        lado.addWidget(self.cb_modelo)
        self.b_ia = QPushButton("✨ Remover fundo com IA")
        self.b_ia.setObjectName("primario")
        self.b_ia.clicked.connect(self._clicou_ia)
        lado.addWidget(self.b_ia)
        self.barra_ia = QProgressBar()
        self.barra_ia.setRange(0, 1000)
        self.barra_ia.setTextVisible(False)
        self.barra_ia.setFixedHeight(8)
        self.barra_ia.hide()
        lado.addWidget(self.barra_ia)
        self.info_ia = QLabel()
        self.info_ia.setWordWrap(True)
        self.info_ia.setStyleSheet("font-size: 11px;")
        lado.addWidget(self.info_ia)
        self.lb_firmeza = QLabel("Borda do recorte: suave / seca")
        lado.addWidget(self.lb_firmeza)
        self.firmeza = QSlider(Qt.Orientation.Horizontal)
        self.firmeza.setRange(0, 100)
        self.firmeza.setValue(50)
        self.firmeza.setToolTip("Depois da IA: deixa a borda do recorte mais suave ou mais seca")
        self.firmeza.valueChanged.connect(self._reaplicar_ia)
        lado.addWidget(self.firmeza)

    def _chave_ia(self) -> str:
        return self.cb_modelo.currentData()

    def _atualizar_ia(self):
        from ..ia.recorte import MODELOS, modelo_instalado
        chave = self._chave_ia()
        ocupado = self._trabalho is not None
        tem = modelo_instalado(chave)
        if ocupado:
            self.b_ia.setText("Cancelar")
        elif tem:
            self.b_ia.setText("✨ Remover fundo com IA")
        else:
            self.b_ia.setText(f"📥 Baixar o modelo ({MODELOS[chave][2]:g} MB)".replace(".", ","))
        self.cb_modelo.setEnabled(not ocupado)
        if not ocupado:
            self.info_ia.setText(MODELOS[chave][6] if tem else
                                 "Baixa uma vez só (fica em Documentos/Taverna/IA) e depois funciona sem internet.")
        tem_mascara = self._mascara_ia is not None
        self.lb_firmeza.setVisible(tem_mascara)
        self.firmeza.setVisible(tem_mascara)
        try:
            from .acabamento import com_icone
            com_icone(self.b_ia)
        except Exception:   # noqa: BLE001 — ícone é só enfeite
            pass

    def _clicou_ia(self):
        from ..ia.recorte import modelo_instalado
        if self._trabalho is not None:   # cancelar
            self._trabalho.parar = True
            self._fim_trabalho()
            self.info_ia.setText("Cancelado.")
            return
        chave = self._chave_ia()
        if not modelo_instalado(chave):
            self._comecar("baixar", chave)
            self.info_ia.setText("Baixando o modelo…")
        else:
            self._comecar("rodar", chave, self.arr.copy())
            self.info_ia.setText("A IA está olhando a imagem…" +
                                 ("  (o caprichado leva uns 10–30 s)" if chave == "caprichado" else ""))

    def _comecar(self, tarefa, chave, arr=None):
        t = _TrabalhoIA(tarefa, chave, arr, self)
        t.progresso.connect(lambda f: self.barra_ia.setValue(int(f * 1000)))
        t.pronto.connect(lambda r, tf=tarefa: self._pronto_ia(tf, r))
        t.falhou.connect(self._falhou_ia)
        self._trabalho = t
        self.barra_ia.setValue(0)
        self.barra_ia.show()
        t.start()
        self._atualizar_ia()

    def _fim_trabalho(self):
        t, self._trabalho = self._trabalho, None
        if t is not None:
            t.progresso.disconnect()
            t.pronto.disconnect()
            t.falhou.disconnect()
            self._threads_velhas = getattr(self, "_threads_velhas", [])
            self._threads_velhas.append(t)   # deixa terminar sozinha (cancelada) sem o Python apagar
        self.barra_ia.hide()
        self._atualizar_ia()

    def _pronto_ia(self, tarefa, r):
        self._fim_trabalho()
        if tarefa == "baixar":
            self.info_ia.setText("Modelo baixado! Rodando…")
            self._clicou_ia()
            return
        self._guardar()
        self._mascara_ia = (r, self.arr.copy())
        self._reaplicar_ia()
        self._atualizar_ia()

    def _reaplicar_ia(self):
        if self._mascara_ia is None:
            return
        from ..ia.recorte import aplicar_mascara
        m, antes = self._mascara_ia
        if antes.shape[:2] != self.arr.shape[:2]:
            return
        self.arr = aplicar_mascara(antes, m, self.firmeza.value() / 100)
        self._mostrar()

    def _falhou_ia(self, msg):
        self._fim_trabalho()
        self.info_ia.setText("Não deu certo.")
        QMessageBox.warning(self, "Removedor com IA",
                            f"Não consegui terminar:\n{msg}\n\nSe foi o download, confira a internet e tente de novo.")

    def done(self, r):
        if self._trabalho is not None:   # fechou no meio: para o trabalho
            self._trabalho.parar = True
            self._trabalho.wait(3000)
        super().done(r)

    # ------------------------------------------------------------ ações
    def _guardar(self):
        self.desfazer_pilha.append(self.arr.copy())
        del self.desfazer_pilha[:-15]
        self._soltar_mascara()

    def _soltar_mascara(self):
        """Mexeu na imagem depois da IA: a régua da borda não pode mais desfazer o que foi feito."""
        if self._mascara_ia is not None:
            self._mascara_ia = None
            self.lb_firmeza.hide()
            self.firmeza.hide()

    def _mostrar(self):
        self.tela.img = _para_qimage(self.arr)
        self.tela.update()
        tirado = int((self.arr[:, :, 3] == 0).sum() * 100 / max(1, self.arr.shape[0] * self.arr.shape[1]))
        self.info.setText(f"Transparente: {tirado}% da imagem.")

    def _modo(self, modo):
        self.tela.modo = modo
        self.tela.setCursor(Qt.CursorShape.CrossCursor if modo == "cor" else Qt.CursorShape.BlankCursor)

    def _automatico(self):
        self._guardar()
        self.arr = remover_automatico(self.arr, self.tol.value(), self.ck_suave.isChecked())
        self._mostrar()

    def _clicou(self, x, y):
        if self.arr[y, x, 3] == 0:
            return
        self._guardar()
        masc = _parecidos(self.arr, self.arr[y, x], self.tol.value())
        area = masc if self.ck_tudo.isChecked() else preencher(masc, [(y, x)])
        self.arr = apagar(self.arr, area, self.ck_suave.isChecked())
        self._mostrar()

    def _apagar_mao(self, x, y, comecando):
        if comecando:
            self._guardar()
        r = self.raio.value()
        h, w = self.arr.shape[:2]
        y0, y1, x0, x1 = max(0, y - r), min(h, y + r + 1), max(0, x - r), min(w, x + r + 1)
        yy, xx = np.ogrid[y0:y1, x0:x1]
        circulo = (yy - y) ** 2 + (xx - x) ** 2 <= r * r
        self.arr[y0:y1, x0:x1, 3][circulo] = 0
        self._mostrar()

    def _desfazer(self):
        if self.desfazer_pilha:
            self._soltar_mascara()
            self.arr = self.desfazer_pilha.pop()
            self._mostrar()

    def _original(self):
        self._guardar()
        self.arr = self.original.copy()
        self._mostrar()

    def resultado(self) -> bytes:
        # corta a sobra transparente em volta
        alfa = self.arr[:, :, 3] > 0
        if alfa.any():
            ys, xs = np.where(alfa)
            arr = self.arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        else:
            arr = self.arr
        return imagem_png(_para_qimage(arr))
