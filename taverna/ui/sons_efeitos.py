"""
🔊 Som atrelado aos efeitos rápidos (explosão, raio, desabamento, clarão arcano…).

O mestre escolhe um som pra cada efeito (da lista de Efeitos sonoros dele, ou um arquivo novo).
Quando o efeito dispara — pelo botão, pelo botão direito no mapa ou por uma armadilha —
o som toca junto, pra todo mundo. Fica salvo no PC do mestre.
"""

import os

from PyQt6.QtCore import QSettings, Qt, pyqtSignal
from PyQt6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFileDialog, QGridLayout, QLabel,
                             QPushButton, QSlider, QVBoxLayout)

from ..mesa.impactos import IMPACTOS
from .audio import EXTENSOES, BibliotecaSons

_ESCOLHER = "\x00escolher"


def sons_dos_efeitos() -> dict:
    """{tipo: {"caminho", "vol"}} — só os que têm som e o arquivo ainda existe."""
    v = QSettings("Taverna", "Mestre").value("sons_impactos", {}) or {}
    return {k: dict(d) for k, d in v.items() if isinstance(d, dict) and d.get("caminho")
            and k in IMPACTOS}


def som_do_efeito(tipo: str):
    d = sons_dos_efeitos().get(tipo)
    if d and os.path.isfile(d["caminho"]):
        return d["caminho"], max(0.0, min(1.0, float(d.get("vol", 80)) / 100))
    return None


class DialogoSonsEfeitos(QDialog):
    testar = pyqtSignal(str, float)   # caminho, volume — toca só pro mestre

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔊 Sons dos efeitos rápidos")
        self.resize(620, 420)
        self.biblioteca = BibliotecaSons("Mestre")
        atuais = sons_dos_efeitos()
        lay = QVBoxLayout(self)
        dica = QLabel("Escolha um som pra cada efeito. Ele toca <b>pra todo mundo</b> quando o efeito acontece "
                      "(inclusive em armadilhas). Use sons que você baixou (Pixabay, Freesound, MyInstants…).")
        dica.setWordWrap(True)
        lay.addWidget(dica)
        grade = QGridLayout()
        grade.addWidget(QLabel("<b>Efeito</b>"), 0, 0)
        grade.addWidget(QLabel("<b>Som</b>"), 0, 1)
        grade.addWidget(QLabel("<b>Volume</b>"), 0, 2)
        self.linhas = {}
        for k, (tipo, (nome, _mapa, _dur)) in enumerate(IMPACTOS.items(), start=1):
            grade.addWidget(QLabel(nome), k, 0)
            cb = QComboBox()
            cb.setMinimumWidth(240)
            vol = QSlider(Qt.Orientation.Horizontal)
            vol.setRange(0, 100)
            vol.setValue(int(atuais.get(tipo, {}).get("vol", 80)))
            vol.setFixedWidth(110)
            ouvir = QPushButton("▶")
            ouvir.setFixedWidth(34)
            ouvir.setToolTip("Ouvir (só você)")
            ouvir.clicked.connect(lambda _=False, t=tipo: self._ouvir(t))
            grade.addWidget(cb, k, 1)
            grade.addWidget(vol, k, 2)
            grade.addWidget(ouvir, k, 3)
            self.linhas[tipo] = (cb, vol)
            self._encher(cb, atuais.get(tipo, {}).get("caminho", ""))
            cb.activated.connect(lambda _i, t=tipo: self._escolheu(t))
        grade.setColumnStretch(1, 1)
        lay.addLayout(grade)
        lay.addStretch(1)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(self._ok)
        botoes.rejected.connect(self.reject)
        lay.addWidget(botoes)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def _encher(self, cb: QComboBox, atual: str):
        cb.clear()
        cb.addItem("— sem som —", "")
        caminhos = set()
        for s in self.biblioteca.lista():
            if os.path.isfile(s["caminho"]):
                cb.addItem("🔊 " + s["nome"], s["caminho"])
                caminhos.add(os.path.normcase(s["caminho"]))
        if atual and os.path.normcase(atual) not in caminhos and os.path.isfile(atual):
            cb.addItem("🔊 " + os.path.splitext(os.path.basename(atual))[0], atual)
        cb.addItem("📂 Escolher um arquivo…", _ESCOLHER)
        i = cb.findData(atual)
        cb.setCurrentIndex(i if i >= 0 else 0)

    def _escolheu(self, tipo):
        cb, _vol = self.linhas[tipo]
        if cb.currentData() != _ESCOLHER:
            return
        filtro = "Sons (" + " ".join(f"*.{e}" for e in EXTENSOES) + ")"
        caminho, _ = QFileDialog.getOpenFileName(self, "Som do efeito", "", filtro)
        if caminho:
            self.biblioteca.adicionar([caminho])   # já entra na lista de Efeitos sonoros
            for t, (outro, _v) in self.linhas.items():
                self._encher(outro, caminho if t == tipo else (outro.currentData() or ""))
        else:
            cb.setCurrentIndex(0)

    def _ouvir(self, tipo):
        cb, vol = self.linhas[tipo]
        caminho = cb.currentData()
        if caminho and caminho != _ESCOLHER and os.path.isfile(caminho):
            self.testar.emit(caminho, vol.value() / 100)

    def _ok(self):
        dados = {}
        for tipo, (cb, vol) in self.linhas.items():
            caminho = cb.currentData()
            if caminho and caminho != _ESCOLHER:
                dados[tipo] = {"caminho": caminho, "vol": vol.value()}
        QSettings("Taverna", "Mestre").setValue("sons_impactos", dados)
        self.accept()
