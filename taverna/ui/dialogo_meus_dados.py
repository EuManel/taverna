"""
(v0.74) 🎨 Janela "Meus dados": material, cor do corpo e cor dos números dos SEUS dados 3D, com uma prévia de
um d20 de verdade (a mesma cena dos dados que rolam na mesa, parada). Fica salvo neste PC e vai junto com cada
rolagem — todo mundo vê seus dados do seu jeito.
"""

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import (QCheckBox, QColorDialog, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
                             QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout)

from ..dados3d.visual import MATERIAIS, guardar, limpar, meus_dados

LARG, ALT = 300, 190


def previa(visual, tema: str, fonte: str, w: int = LARG, h: int = ALT) -> QImage:
    """Um d20 e um d6 parados, desenhados com a cara escolhida (o desenho 2D dos dados, que todo PC tem)."""
    from ..dados3d.cena3d import Rolagem
    from ..dados3d.render_2d import desenhar
    r = {"fisicos": [{"lados": 20, "valor": 20}, {"lados": 6, "valor": 6}], "semente": 11, "dv": visual}
    W, H = w * 3, h * 3   # desenha grande e enquadra nos dados (a câmera mostra a mesa de rolagem inteira)
    rol = Rolagem(r, W, H, tema, fonte)
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(QColor(0, 0, 0, 0))
    p = QPainter(img)
    desenhar(p, rol, rol.duracao + 5.0, W, H)
    p.end()
    import numpy as np
    ptr = img.constBits()
    ptr.setsize(img.sizeInBytes())
    a = np.frombuffer(ptr, np.uint8).reshape(H, img.bytesPerLine() // 4, 4)[:, :W, 3]
    ys, xs = np.nonzero(a > 160)   # (só o corpo dos dados, sem a sombra macia)
    if len(xs):
        from PyQt6.QtCore import QRect
        cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
        meia_w = max(xs.max() - xs.min(), (ys.max() - ys.min()) * w / h) / 2 * 1.35 + 8
        meia_h = meia_w * h / w
        img = img.copy(QRect(int(cx - meia_w), int(cy - meia_h), int(2 * meia_w), int(2 * meia_h)))
    from PyQt6.QtCore import Qt as _Qt
    return img.scaled(w, h, _Qt.AspectRatioMode.KeepAspectRatio, _Qt.TransformationMode.SmoothTransformation)


class DialogoMeusDados(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Meus dados")
        from .tema import tema_atual
        t = tema_atual()
        self._tema = t.get("chave", "medieval")
        self._fonte = t["fonte_titulo"].split(",")[0].strip("'\" ")
        atual = meus_dados() or {"m": "tema"}
        self.material = QComboBox()
        for chave, (nome, *_r) in MATERIAIS.items():
            self.material.addItem(nome, chave)
        self.material.setCurrentIndex(max(0, self.material.findData(atual["m"])))
        self.material.currentIndexChanged.connect(self._material_mudou)
        self._cores = {"c": atual.get("c"), "n": atual.get("n")}
        self.translucido = QCheckBox("Translúcido")
        self.translucido.setChecked(bool(atual.get("t")))
        self.translucido.toggled.connect(lambda _v: self._atualizar())
        self.brilho = QSlider(Qt.Orientation.Horizontal)
        self.brilho.setRange(0, 100)
        self.brilho.setValue(int(round(float(atual.get("b", 0.5)) * 100)))
        self.brilho.setToolTip("Fosco ↔ polido")
        self.brilho.sliderReleased.connect(self._atualizar)
        self.brilho.valueChanged.connect(lambda _v: None if self.brilho.isSliderDown() else self._atualizar())
        self.b_corpo = QPushButton()
        self.b_corpo.clicked.connect(lambda: self._escolher("c", "Cor do corpo do dado"))
        self.b_num = QPushButton()
        self.b_num.clicked.connect(lambda: self._escolher("n", "Cor dos números"))
        self.imagem = QLabel()
        self.imagem.setFixedSize(QSize(LARG, ALT))
        self.imagem.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imagem.setStyleSheet("background: rgba(0,0,0,90); border-radius: 8px;")
        form = QFormLayout()
        form.addRow("Material", self.material)
        linha = QHBoxLayout()
        linha.addWidget(self.b_corpo)
        linha.addWidget(self.b_num)
        form.addRow("Cores", linha)
        linha_b = QHBoxLayout()
        linha_b.addWidget(QLabel("fosco"))
        linha_b.addWidget(self.brilho, 1)
        linha_b.addWidget(QLabel("polido"))
        form.addRow("Brilho", linha_b)
        form.addRow("", self.translucido)
        dica = QLabel("Todo mundo vê os seus dados assim quando você rola. “Do tema da mesa” = como era antes.")
        dica.setObjectName("dica")
        dica.setWordWrap(True)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(self._ok)
        botoes.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addWidget(self.imagem, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addLayout(form)
        lay.addWidget(dica)
        lay.addWidget(botoes)
        self._material_mudou(manter=True)
        from .acabamento import iconizar
        iconizar(self)

    def visual(self) -> dict | None:
        return limpar({"m": self.material.currentData(), "c": self._cores.get("c"), "n": self._cores.get("n"),
                       "t": self.translucido.isChecked(), "b": self.brilho.value() / 100})

    def _material_mudou(self, *_a, manter=False):
        m = self.material.currentData()
        do_tema = m == "tema"
        _n, brilho, transl, _d, corpo, numero, _metal = MATERIAIS[m]
        if not manter or not self._cores.get("c"):   # trocou o material: começa no jeito dele
            self._cores = {"c": corpo, "n": numero}
            if not do_tema:
                for w, valor in ((self.translucido, bool(transl)), (self.brilho, int(round(brilho * 100)))):
                    w.blockSignals(True)
                    (w.setChecked if w is self.translucido else w.setValue)(valor)
                    w.blockSignals(False)
        for w in (self.b_corpo, self.b_num, self.translucido, self.brilho):
            w.setEnabled(not do_tema)
        self._atualizar()

    def _escolher(self, qual, titulo):
        cor = QColorDialog.getColor(QColor(self._cores.get(qual) or "#ffffff"), self, titulo)
        if cor.isValid():
            self._cores[qual] = cor.name()
            self._atualizar()

    def _botao_cor(self, b, cor, texto):
        pm = QPixmap(16, 16)
        pm.fill(QColor(cor or "#555555"))
        from PyQt6.QtGui import QIcon
        b.setIcon(QIcon(pm))
        b.setText(texto)

    def _atualizar(self):
        v = self.visual()
        self._botao_cor(self.b_corpo, v["c"] if v else None, "Corpo")
        self._botao_cor(self.b_num, v["n"] if v else None, "Números")
        try:
            self.imagem.setPixmap(QPixmap.fromImage(previa(v, self._tema, self._fonte)))
        except Exception as erro:   # a prévia nunca impede de escolher
            from ..seguranca import registrar_erro
            registrar_erro(f"Prévia dos dados falhou: {erro!r}")

    def _ok(self):
        guardar(self.visual())
        self.accept()
