"""Editar uma área de efeito (duplo clique nela, no mestre)."""

from PyQt6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
                             QLineEdit, QVBoxLayout)

from ..mesa.efeitos import EFEITOS, FORMAS


class DialogoEfeito(QDialog):
    def __init__(self, item, parent=None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle("Área de efeito")
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.nome = QLineEdit(item.nome)
        self.nome.setPlaceholderText(item.dono or "ex.: Bola de fogo, Nuvem fétida… (opcional)")
        self.efeito = QComboBox()
        for chave, (nome, *_r) in EFEITOS.items():
            self.efeito.addItem(nome, chave)
        self.efeito.setCurrentIndex(max(0, self.efeito.findData(item.efeito)))
        self.forma = QComboBox()
        for chave, nome in FORMAS.items():
            self.forma.addItem(nome, chave)
        if item.forma == "livre":   # pedaço que sobrou/virou outra coisa numa reação
            self.forma.addItem("Forma livre (de uma reação)", "livre")
        self.forma.setCurrentIndex(max(0, self.forma.findData(item.forma)))
        self.tamanho = self._spin(item.tamanho, 0.5, 60, 1.5, " m")
        self.largura = self._spin(item.largura, 0.5, 12, 0.5, " m")
        self.angulo = self._spin(item.angulo, 0, 359, 15, "°")
        # cor livre (magia, luz, radiante, escuridão)
        from PyQt6.QtGui import QColor, QIcon, QPixmap
        from ..mesa.efeitos import CORES_LIVRES, CORES_MAGIA
        self._cores_livres = CORES_LIVRES
        self.cor = QComboBox()
        self.cor.addItem("Padrão do efeito", "")
        for nome_cor, hexa in CORES_MAGIA:
            pm = QPixmap(14, 14)
            pm.fill(QColor(hexa))
            self.cor.addItem(QIcon(pm), nome_cor, hexa)
        if item.cor and self.cor.findData(item.cor) < 0:
            pm = QPixmap(14, 14)
            pm.fill(QColor(item.cor))
            self.cor.addItem(QIcon(pm), f"Outra ({item.cor})", item.cor)
        self.cor.addItem("Outra cor…", "__outra__")
        self.cor.setCurrentIndex(max(0, self.cor.findData(item.cor or "")))
        self.cor.activated.connect(self._talvez_outra)
        self.efeito.currentIndexChanged.connect(
            lambda _i: self.cor.setEnabled(self.efeito.currentData() in self._cores_livres))
        self.cor.setEnabled(item.efeito in CORES_LIVRES)
        form.addRow("Nome", self.nome)
        form.addRow("Efeito", self.efeito)
        form.addRow("Cor", self.cor)
        form.addRow("Forma", self.forma)
        form.addRow("Tamanho", self.tamanho)
        form.addRow("Largura (linha)", self.largura)
        form.addRow("Ângulo", self.angulo)
        lay.addLayout(form)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        lay.addWidget(botoes)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    @staticmethod
    def _spin(valor, mini, maxi, passo, sufixo):
        s = QDoubleSpinBox()
        s.setRange(mini, maxi)
        s.setSingleStep(passo)
        s.setDecimals(1)
        s.setSuffix(sufixo)
        s.setValue(float(valor))
        return s

    def _talvez_outra(self, _i):
        if self.cor.currentData() != "__outra__":
            return
        from PyQt6.QtGui import QColor, QIcon, QPixmap
        from PyQt6.QtWidgets import QColorDialog
        escolhida = QColorDialog.getColor(QColor(self.item.cor or "#b07aff"), self, "Cor da magia")
        if not escolhida.isValid():
            self.cor.setCurrentIndex(0)
            return
        pm = QPixmap(14, 14)
        pm.fill(escolhida)
        self.cor.insertItem(self.cor.count() - 1, QIcon(pm), f"Outra ({escolhida.name()})", escolhida.name())
        self.cor.setCurrentIndex(self.cor.count() - 2)

    def aplicar(self):
        cor = self.cor.currentData() if self.cor.currentData() != "__outra__" else ""
        self.item.aplicar(efeito=self.efeito.currentData(), forma=self.forma.currentData(),
                          tamanho=self.tamanho.value(), largura=self.largura.value(),
                          angulo=self.angulo.value(), nome=self.nome.text().strip(), cor=cor or "")
