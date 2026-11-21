"""Diálogo do 🗺 Importar mapa Universal VTT (v0.60): escala, material das paredes e onde colocar."""

from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
                             QLabel, QVBoxLayout)

from ..mesa import materiais


class DialogoUVTT(QDialog):
    def __init__(self, parent, nome: str, dados: dict):
        super().__init__(parent)
        self.setWindowTitle("Importar mapa (Universal VTT)")
        lay = QVBoxLayout(self)
        tw, th = dados["tamanho"]
        info = QLabel(f"<b>{nome}</b><br>{tw:g} × {th:g} quadrados · {len(dados['paredes'])} trechos de parede · "
                      f"{len(dados['portas'])} portas · {len(dados['luzes'])} luzes")
        info.setWordWrap(True)
        lay.addWidget(info)
        form = QFormLayout()
        self.escala = QComboBox()
        self.escala.addItem("1,5 m (padrão D&D: 5 pés)", 1.5)
        self.escala.addItem("1 m", 1.0)
        self.escala.addItem("Outro…", 0.0)
        self.outro = QDoubleSpinBox()
        self.outro.setRange(0.1, 50)
        self.outro.setDecimals(2)
        self.outro.setSuffix(" m")
        self.outro.setValue(1.5)
        self.outro.setVisible(False)
        self.escala.currentIndexChanged.connect(lambda _i: self.outro.setVisible(self.escala.currentData() == 0.0))
        form.addRow("1 quadrado do mapa =", self.escala)
        form.addRow("", self.outro)
        self.material = QComboBox()
        for chave, (rotulo, *_r) in materiais.PAREDES.items():
            self.material.addItem(rotulo, chave)
        self.material.setCurrentIndex(max(0, self.material.findData("pedra")))
        form.addRow("Material das paredes:", self.material)
        self.aba_nova = QCheckBox("Criar numa aba nova")
        self.aba_nova.setChecked(True)
        form.addRow("", self.aba_nova)
        lay.addLayout(form)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Ok).setText("Importar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        lay.addWidget(botoes)
        from .acabamento import iconizar
        iconizar(self)

    def metros(self) -> float:
        v = self.escala.currentData()
        return float(self.outro.value() if not v else v)
