"""
Barra de construção vertical (lado esquerdo), estilo Photoshop:

   [seta]   Selecionar (V)
   [pincel] Terreno (B)
   [tijolo] Parede (W)
   [sala]   Sala (R)
   [porta]  Porta (D)
   ─────
   [■] chão atual    ← clique: abre a paleta de chãos
   [■] parede atual  ← clique: abre a paleta de paredes
   [1×1] pincel      ← clique: tamanho do pincel

Botão esquerdo constrói, botão direito apaga.
"""

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup, QIcon
from PyQt6.QtWidgets import (QCheckBox, QGridLayout, QLabel, QMenu, QToolBar,
                             QToolButton, QVBoxLayout, QWidget, QWidgetAction)

from ..mesa import materiais
from ..mesa.luzes import TIPOS_LUZ
from ..mesa.portas import TIPOS_PORTA
from ..temas import tema as dados_tema
from .icones import icone

FERRAMENTAS = [
    ("selecionar", "Selecionar  (V)",
     "Mexe em mapas, tokens e portas. Duplo clique na porta abre/fecha."),
    ("terreno", "Pincel de terreno  (B)",
     "Pinte o chão como tinta, livre. Botão direito: menu da pincelada."),
    ("borracha", "Borracha de terreno  (E)", "Apaga o terreno por onde passar."),
    ("parede", "Parede  (W)",
     "Arraste de um ponto a outro, em qualquer ângulo. Gruda nos cantos do grid "
     "(Alt solta) · Shift trava de 15 em 15°."),
    ("borracha_parede", "Borracha de paredes  (Shift+E)",
     "Apaga só o pedaço de parede por onde passar (o tamanho é o do Pincel)."),
    ("sala", "Sala  (R)", "Arraste um retângulo: chão + quatro paredes em volta."),
    ("luz", "Luz  (L)",
     "Clique pra colocar uma fonte de luz. A luz para nas paredes e passa pelas portas abertas."),
    ("porta", "Porta  (D)",
     "Clique numa parede: a porta se alinha e abre o vão. Edite tipo e tamanho em Propriedades."),
]
DICAS = {k: f"{n.split('  ')[0]}: {d}" for k, n, d in FERRAMENTAS}


class PaletaMateriais(QWidget):
    """Grade de materiais que aparece no popup do seletor."""
    escolhido = pyqtSignal(str)

    def __init__(self, tipo, titulo, parent=None):
        super().__init__(parent)
        self.tipo = tipo
        self.lbl = QLabel(titulo)
        self.lbl.setObjectName("titulo")
        self.grade = QGridLayout()
        self.grade.setSpacing(4)
        self.todos = QCheckBox("Todos os temas")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.addWidget(self.lbl)
        layout.addLayout(self.grade)
        layout.addWidget(self.todos)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def preencher(self, chaves, atual):
        while self.grade.count():
            w = self.grade.takeAt(0).widget()
            if w:
                w.deleteLater()
        for n, chave in enumerate(chaves):
            b = QToolButton()
            b.setIcon(QIcon(materiais.amostra(self.tipo, chave, 40)))
            b.setIconSize(QSize(40, 40))
            b.setFixedSize(48, 48)
            b.setCheckable(True)
            b.setChecked(chave == atual)
            b.setToolTip(materiais.nome(self.tipo, chave))
            b.clicked.connect(lambda _=False, k=chave: self.escolhido.emit(k))
            self.grade.addWidget(b, n // 4, n % 4)
            b.show()
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)
        self.layout().activate()
        self.setFixedSize(self.sizeHint())


class SeletorMaterial(QToolButton):
    """Quadradinho com o material atual; clique abre a paleta."""

    def __init__(self, cena, tipo, titulo, parent=None):
        super().__init__(parent)
        self.cena = cena
        self.tipo = tipo
        self.titulo = titulo
        self.setIconSize(QSize(34, 34))
        self.setFixedSize(46, 46)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.setObjectName("seletor_material")
        self.setStyleSheet("QToolButton::menu-indicator { image: none; }"
                           "QToolButton#seletor_material { padding: 2px; }")

        self.menu_ = QMenu(self)
        self.paleta = PaletaMateriais(tipo, titulo)
        self.paleta.escolhido.connect(self._escolher)
        self.paleta.todos.toggled.connect(lambda _: self.recarregar())
        self.acao_paleta = QWidgetAction(self.menu_)
        self.acao_paleta.setDefaultWidget(self.paleta)
        self.menu_.addAction(self.acao_paleta)
        self.setMenu(self.menu_)

    @property
    def atual(self):
        return self.cena.material_chao if self.tipo == "chao" else self.cena.material_parede

    def _opcoes(self):
        if self.paleta.todos.isChecked():
            if self.tipo == "chao":
                return list(materiais.CHAO)
            return [k for k in materiais.PAREDES if k != "metal"]
        return dados_tema(self.cena.tema)["chao" if self.tipo == "chao" else "paredes"]

    def recarregar(self):
        opcoes = self._opcoes()
        if self.atual not in opcoes and not self.paleta.todos.isChecked():
            self._definir(opcoes[0])
        self.paleta.preencher(opcoes, self.atual)
        # A paleta mudou de tamanho: avisa o menu pra ele crescer junto
        # (antes os materiais novos ficavam por cima da caixinha "Todos os temas")
        self.acao_paleta.setVisible(False)
        self.acao_paleta.setVisible(True)
        if self.menu_.isVisible():
            self.menu_.adjustSize()
        self.setIcon(QIcon(materiais.amostra(self.tipo, self.atual, 34)))
        self.setToolTip(f"{self.titulo}: {materiais.nome(self.tipo, self.atual)}\n"
                        "Clique pra trocar")

    def _definir(self, chave):
        if self.tipo == "chao":
            self.cena.material_chao = chave
        else:
            self.cena.material_parede = chave

    def _escolher(self, chave):
        self._definir(chave)
        self.menu_.close()
        # Escolher um material já pega a ferramenta que usa ele
        if self.tipo == "chao" and self.cena.ferramenta not in ("terreno", "sala"):
            self.cena.definir_ferramenta("terreno")
        elif self.tipo == "parede" and self.cena.ferramenta not in ("parede", "sala", "porta"):
            self.cena.definir_ferramenta("parede")
        self.recarregar()


class BarraConstrucao(QToolBar):
    dica = pyqtSignal(str)

    def __init__(self, cena, parent=None):
        super().__init__("Construção", parent)
        self.cena = cena
        self.setObjectName("barra_construcao")
        self.setOrientation(Qt.Orientation.Vertical)
        self.setMovable(False)
        self.setIconSize(QSize(26, 26))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

        self.grupo = QActionGroup(self)
        self.grupo.setExclusive(True)
        self.acoes = {}
        for chave, nome, _ in FERRAMENTAS:
            a = QAction(nome, self)
            a.setToolTip(f"{nome}\n{DICAS[chave].split(': ', 1)[1]}")
            a.setCheckable(True)
            a.triggered.connect(lambda _=False, k=chave: self.cena.definir_ferramenta(k))
            self.grupo.addAction(a)
            self.addAction(a)
            self.acoes[chave] = a

        self.addSeparator()
        self.addWidget(self._rotulo("Chão"))
        self.sel_chao = SeletorMaterial(cena, "chao", "Chão")
        self.addWidget(self._embrulhar(self.sel_chao))
        self.addWidget(self._rotulo("Parede"))
        self.sel_parede = SeletorMaterial(cena, "parede", "Parede / Porta")
        self.addWidget(self._embrulhar(self.sel_parede))

        self.addWidget(self._rotulo("Porta"))
        self.btn_porta = QToolButton()
        self.btn_porta.setObjectName("seletor_material")
        self.btn_porta.setFixedSize(46, 46)
        self.btn_porta.setIconSize(QSize(34, 34))
        self.btn_porta.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btn_porta.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        menu_porta = QMenu(self.btn_porta)
        self.grupo_tipo_porta = QActionGroup(menu_porta)
        for chave, (nome, cor, _) in TIPOS_PORTA.items():
            a = menu_porta.addAction(icone("porta", cor), nome,
                                     lambda k=chave: self._tipo_porta(k))
            a.setCheckable(True)
            a.setChecked(chave == cena.tipo_porta)
            self.grupo_tipo_porta.addAction(a)
        menu_porta.addSeparator()
        self.grupo_larg_porta = QActionGroup(menu_porta)
        for larg in (1, 1.5, 2, 3, 4):
            a = menu_porta.addAction(f"Largura {larg:g} m".replace(".", ","),
                                     lambda l=larg: self._largura_porta(l))
            a.setCheckable(True)
            a.setChecked(larg == cena.largura_porta)
            self.grupo_larg_porta.addAction(a)
        self.btn_porta.setMenu(menu_porta)
        self.addWidget(self._embrulhar(self.btn_porta))
        self._atualizar_btn_porta()

        self.addWidget(self._rotulo("Luz"))
        self.btn_luz = QToolButton()
        self.btn_luz.setObjectName("seletor_material")
        self.btn_luz.setFixedSize(46, 46)
        self.btn_luz.setIconSize(QSize(34, 34))
        self.btn_luz.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btn_luz.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        menu_luz = QMenu(self.btn_luz)
        self.grupo_tipo_luz = QActionGroup(menu_luz)
        for chave, valores in TIPOS_LUZ.items():
            a = menu_luz.addAction(icone("luz", valores[3]), valores[0],
                                   lambda k=chave: self._tipo_luz(k))
            a.setCheckable(True)
            a.setChecked(chave == getattr(cena, "tipo_luz", "tocha"))
            self.grupo_tipo_luz.addAction(a)
        self.btn_luz.setMenu(menu_luz)
        self.addWidget(self._embrulhar(self.btn_luz))
        self._atualizar_btn_luz()

        self.addWidget(self._rotulo("Pincel"))
        self.btn_pincel = QToolButton()
        self.btn_pincel.setFixedSize(44, 30)
        self.btn_pincel.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btn_pincel.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        self.btn_pincel.setToolTip("Pincel do terreno e da borracha\n"
                                   "[ diminui · ] aumenta")
        menu = QMenu(self.btn_pincel)
        titulo = menu.addAction("Forma")
        titulo.setEnabled(False)
        self.grupo_forma = QActionGroup(menu)
        self.acoes_forma = {}
        for chave, nome in (("livre", "●  Redondo livre (tinta)"),
                            ("grid", "■  Quadrado por quadrado do grid")):
            a = menu.addAction(nome, lambda k=chave: self._forma(k))
            a.setCheckable(True)
            self.grupo_forma.addAction(a)
            self.acoes_forma[chave] = a
        menu.addSeparator()
        titulo = menu.addAction("Tamanho")
        titulo.setEnabled(False)
        for n in self.TAMANHOS:
            menu.addAction(f"{n:g} m".replace(".", ","), lambda n=n: self._pincel(n))
        self.btn_pincel.setMenu(menu)
        self.acoes_forma[cena.forma_pincel].setChecked(True)
        self.addWidget(self.btn_pincel)
        self._pincel(cena.pincel)

        cena.ferramenta_mudou.connect(self._ferramenta_mudou)
        cena.tema_mudou.connect(self._tema_mudou)
        self._tema_mudou(cena.tema)
        self._ferramenta_mudou(cena.ferramenta)

    CONFIG_FERRAMENTAS = ("ferramenta", "material_chao", "material_parede", "pincel",
                          "forma_pincel", "tipo_porta", "largura_porta", "tipo_luz")

    def definir_cena(self, cena):
        """Troca de aba: as ferramentas continuam as mesmas, agora mexendo na outra cena."""
        antiga = self.cena
        for sinal, slot in ((antiga.ferramenta_mudou, self._ferramenta_mudou),
                            (antiga.tema_mudou, self._tema_mudou)):
            try:
                sinal.disconnect(slot)
            except (TypeError, RuntimeError):
                pass
        for nome in self.CONFIG_FERRAMENTAS:
            setattr(cena, nome, getattr(antiga, nome))
        self.cena = cena
        self.sel_chao.cena = cena
        self.sel_parede.cena = cena
        cena.ferramenta_mudou.connect(self._ferramenta_mudou)
        cena.tema_mudou.connect(self._tema_mudou)
        self._tema_mudou(cena.tema)
        self._ferramenta_mudou(cena.ferramenta)

    @staticmethod
    def _embrulhar(widget):
        """Põe o botão dentro de um QWidget pra barra não encolher o ícone."""
        caixa = QWidget()
        lay = QVBoxLayout(caixa)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        return caixa

    def _tipo_porta(self, chave):
        self.cena.tipo_porta = chave
        self.cena.definir_ferramenta("porta")
        self._atualizar_btn_porta()

    def _tipo_luz(self, chave):
        self.cena.tipo_luz = chave
        self.cena.definir_ferramenta("luz")
        self._atualizar_btn_luz()

    def _atualizar_btn_luz(self):
        valores = TIPOS_LUZ[getattr(self.cena, "tipo_luz", "tocha")]
        self.btn_luz.setIcon(icone("luz", valores[3]))
        self.btn_luz.setToolTip(f"{valores[0]} — clique pra trocar o tipo das próximas luzes")

    def _largura_porta(self, larg):
        self.cena.largura_porta = larg
        self.cena.definir_ferramenta("porta")
        self._atualizar_btn_porta()

    def _atualizar_btn_porta(self):
        nome, cor, _ = TIPOS_PORTA[self.cena.tipo_porta]
        self.btn_porta.setIcon(icone("porta", cor))
        self.btn_porta.setToolTip(f"{nome}, {self.cena.largura_porta:g} m\n"
                                  "Clique pra trocar o tipo e a largura das próximas portas")

    def _rotulo(self, texto):
        lbl = QLabel(texto)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 8pt; padding: 6px 0 1px 0;")
        return lbl

    TAMANHOS = (0.5, 1, 2, 3, 4, 5, 8)

    def _pincel(self, n):
        if self.cena.forma_pincel == "grid":
            n = max(1, round(n))
        self.cena.pincel = n
        simbolo = "■" if self.cena.forma_pincel == "grid" else "●"
        self.btn_pincel.setText(f"{simbolo}{n:g}".replace(".", ","))

    def _forma(self, chave):
        self.cena.forma_pincel = chave
        self.acoes_forma[chave].setChecked(True)
        self._pincel(self.cena.pincel)
        if self.cena.ferramenta not in ("terreno", "borracha"):
            self.cena.definir_ferramenta("terreno")

    def mudar_tamanho(self, direcao):
        """[ e ]: anda pela lista de tamanhos."""
        lista = list(self.TAMANHOS)
        if self.cena.forma_pincel == "grid":
            lista = [n for n in lista if n >= 1 and float(n).is_integer()]
        atual = self.cena.pincel
        if direcao > 0:
            maiores = [n for n in lista if n > atual]
            self._pincel(maiores[0] if maiores else lista[-1])
        else:
            menores = [n for n in lista if n < atual]
            self._pincel(menores[-1] if menores else lista[0])

    def _ferramenta_mudou(self, chave):
        a = self.acoes.get(chave)
        if a and not a.isChecked():
            a.setChecked(True)
        self.btn_pincel.setEnabled(chave in ("terreno", "borracha", "borracha_parede"))
        self.dica.emit(DICAS.get(chave, ""))

    def _tema_mudou(self, chave):
        t = dados_tema(chave)
        for nome, acao in self.acoes.items():
            acao.setIcon(icone(nome, t["texto"]))
        self.setStyleSheet(
            f"QToolBar#barra_construcao {{ background: {t['painel']}; border: none; "
            f"border-right: 1px solid {t['borda']}; padding: 6px 4px; spacing: 3px; }}"
            f"QToolBar#barra_construcao QToolButton {{ padding: 6px; border-radius: 6px; "
            f"border: 1px solid transparent; }}"
            f"QToolBar#barra_construcao QToolButton:hover {{ background: {t['painel2']}; "
            f"border-color: {t['borda']}; }}"
            f"QToolBar#barra_construcao QToolButton:checked {{ background: {t['selecao']}; "
            f"border-color: {t['destaque']}; }}"
            f"QToolButton#seletor_material {{ padding: 1px; border-radius: 6px; "
            f"border: 1px solid {t['borda']}; background: {t['fundo']}; }}"
            f"QToolButton#seletor_material:hover {{ border-color: {t['destaque']}; }}")
        self.sel_chao.recarregar()
        self.sel_parede.recarregar()
