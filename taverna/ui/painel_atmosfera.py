"""
Painel ATMOSFERA: clima, efeitos de área (templates) e lápis.

O mesmo painel serve pro mestre e pro player:
- mestre: escolhe o clima, coloca áreas de efeito, rabisca, apaga de todo mundo
- player: coloca o template da magia dele e rabisca (se o mestre deixar)
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QFrame, QGridLayout,
                             QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QSlider, QToolButton,
                             QVBoxLayout, QWidget)

from ..mesa.desenhos import CORES_LAPIS
from ..mesa.efeitos import CORES_LIVRES, CORES_MAGIA, EFEITOS, FORMAS, TAMANHO_PADRAO
from .clima import CLIMAS


def _desmarcavel(grupo):
    """(v0.48, pedido do Manel) Grupo de botões em que só um fica marcado, MAS clicar de novo no marcado
    tira a seleção. Chamar antes de ligar os outros buttonClicked."""
    grupo.setExclusive(False)

    def clicou(b):
        if b.isChecked():
            for outro in grupo.buttons():
                if outro is not b and outro.isChecked():
                    outro.setChecked(False)
    grupo.buttonClicked.connect(clicou)


def _marcado(grupo):
    return next((b for b in grupo.buttons() if b.isChecked()), None)


def _dica(texto):
    l = QLabel(texto)
    l.setWordWrap(True)
    l.setObjectName("dica")
    l.setStyleSheet("font-size: 11px; opacity: 0.8;")
    return l


class PainelAtmosfera(QWidget):
    clima_mudou = pyqtSignal(str, int)       # mestre
    relampago = pyqtSignal()                 # mestre
    mostrar_clima = pyqtSignal(bool)         # só na minha tela
    ferramenta = pyqtSignal(str)             # "efeito" / "lapis" / "selecionar"
    impacto_tela = pyqtSignal(str)           # mestre: efeito que não precisa de lugar (tremor, clarão, apagão)
    sons_efeitos = pyqtSignal()              # mestre: abrir "Sons dos efeitos"
    apagar_templates = pyqtSignal()
    limpar_marcas = pyqtSignal()
    limpar_fluidos = pyqtSignal(bool)   # True = tira as fontes também
    apagar_desenhos = pyqtSignal()

    def __init__(self, mestre: bool = True, parent=None):
        super().__init__(parent)
        self.mestre = mestre
        self.cena = None
        self._mudando = False
        self.setMinimumWidth(330)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setFrameShape(QFrame.Shape.NoFrame)
        rolagem.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        raiz.addWidget(rolagem)
        miolo = QWidget()
        rolagem.setWidget(miolo)
        lay = QVBoxLayout(miolo)
        lay.setContentsMargins(6, 4, 8, 10)
        lay.setSpacing(2)
        self.layout_principal = lay
        from .acabamento import Secao
        self.secoes = {}

        def secao(chave, titulo, aberta=True):
            """Abre um bloco que fecha com um clique; o que vier depois entra dentro dele."""
            s = Secao(f"atmosfera/{chave}", titulo, aberta)
            self.layout_principal.addWidget(s)
            self.secoes[chave] = s
            return s.lay

        # ---------------------------------------------------------------- clima
        if mestre:
            lay = secao("clima", "🌦 Clima")
            linha = QHBoxLayout()
            self.cb_clima = QComboBox()
            for chave, nome in CLIMAS.items():
                self.cb_clima.addItem(nome, chave)
            self.cb_clima.currentIndexChanged.connect(self._clima_editado)
            from .acabamento import separar
            resumo = lambda t: self.secoes["clima"].definir_resumo(separar(t)[1])
            self.cb_clima.currentTextChanged.connect(resumo)
            resumo(self.cb_clima.currentText())
            linha.addWidget(self.cb_clima, 1)
            lay.addLayout(linha)
            linha = QHBoxLayout()
            linha.addWidget(QLabel("Força"))
            self.sl_forca = QSlider(Qt.Orientation.Horizontal)
            self.sl_forca.setRange(1, 3)
            self.sl_forca.setPageStep(1)
            self.sl_forca.setValue(2)
            self.sl_forca.setTickPosition(QSlider.TickPosition.TicksBelow)
            self.sl_forca.valueChanged.connect(self._clima_editado)
            linha.addWidget(self.sl_forca, 1)
            self.btn_raio = QPushButton("⚡ Raio")
            self.btn_raio.setToolTip("Clarão na tela de todo mundo, agora")
            self.btn_raio.clicked.connect(self.relampago.emit)
            linha.addWidget(self.btn_raio)
            lay.addLayout(linha)
            self.ck_ver_clima = QCheckBox("Mostrar o clima na minha tela também")
            self.ck_ver_clima.setChecked(True)
            self.ck_ver_clima.toggled.connect(self.mostrar_clima.emit)
            lay.addWidget(self.ck_ver_clima)
        else:
            self.ck_ver_clima = QCheckBox("🌦 Mostrar chuva/neve/neblina na tela")
            self.ck_ver_clima.setChecked(True)
            self.ck_ver_clima.toggled.connect(self.mostrar_clima.emit)
            lay.addWidget(self.ck_ver_clima)

        # ---------------------------------------------------------------- impactos (só o mestre)
        self.botoes_impacto = {}
        if mestre:
            from ..mesa.impactos import IMPACTOS, TAMANHO_PADRAO as _TAM
            lay = secao("impactos", "💥 Efeitos rápidos")
            grade_i = QGridLayout()
            grade_i.setSpacing(3)
            for k, (chave, (nome, no_mapa, _dur)) in enumerate(IMPACTOS.items()):
                b = QToolButton()
                b.setText(nome)
                b.setObjectName("efeito_btn")
                b.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
                b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                if no_mapa:
                    b.setCheckable(True)
                    b.setToolTip("Clique aqui e depois no mapa, onde quer o efeito. Dá pra clicar várias vezes. Esc sai.")
                    b.clicked.connect(lambda v, c=chave: self._armar_impacto(c, v))
                else:
                    b.setToolTip("Acontece na hora, na tela de todo mundo.")
                    b.clicked.connect(lambda _v, c=chave: self.impacto_tela.emit(c))
                self.botoes_impacto[chave] = b
                grade_i.addWidget(b, k // 2, k % 2)
            lay.addLayout(grade_i)
            linha = QHBoxLayout()
            linha.addWidget(QLabel("Tamanho"))
            self.sp_impacto = QDoubleSpinBox()
            self.sp_impacto.setRange(1, 30)
            self.sp_impacto.setSingleStep(1.5)
            self.sp_impacto.setDecimals(1)
            self.sp_impacto.setSuffix(" m")
            self.sp_impacto.setValue(_TAM)
            self.sp_impacto.valueChanged.connect(lambda _v: self._impacto_editado())
            linha.addWidget(self.sp_impacto)
            linha.addStretch(1)
            b_sons = QPushButton("🔊 Sons dos efeitos…")
            b_sons.setToolTip("Atrelar um som a cada efeito (explosão, raio, desabamento…)")
            b_sons.clicked.connect(self.sons_efeitos.emit)
            linha.addWidget(b_sons)
            lay.addLayout(linha)
            lay.addWidget(_dica("Explosão treme a tela, raio clareia. Funcionam com qualquer clima "
                                "(e também como ação de armadilha)."))

        # ---------------------------------------------------------------- efeitos
        lay = secao("area", "✨ Área de efeito" if mestre else "✨ Template de magia")
        grade = QGridLayout()
        grade.setSpacing(3)
        self.grupo_efeito = QButtonGroup(self)
        self.grupo_efeito.setExclusive(True)
        for k, (chave, (nome, cor, _, _)) in enumerate(EFEITOS.items()):
            b = QToolButton()
            b.setText(nome)
            b.setCheckable(True)
            b.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.setObjectName("efeito_btn")
            b.setStyleSheet(f"QToolButton#efeito_btn {{ border-left: 4px solid {cor}; }}")
            b.setProperty("chave", chave)
            self.grupo_efeito.addButton(b)
            grade.addWidget(b, k // 2, k % 2)
            if chave == "fogo":
                b.setChecked(True)
        _desmarcavel(self.grupo_efeito)   # (v0.48) clicou de novo = tira a seleção
        self.grupo_efeito.buttonClicked.connect(self._efeito_clicado)
        lay.addLayout(grade)

        # cor livre (só magia, luz, radiante e escuridão): bolinhas de cor + "outra cor…"
        self.cor_efeito = ""
        self.linha_cor = QWidget()
        lc = QHBoxLayout(self.linha_cor)
        lc.setContentsMargins(0, 2, 0, 2)
        lc.setSpacing(3)
        lc.addWidget(QLabel("Cor"))
        self.grupo_cor_efeito = QButtonGroup(self)
        self.grupo_cor_efeito.setExclusive(True)
        for nome_cor, hexa in [("Padrão do efeito", "")] + CORES_MAGIA:
            b = QToolButton()
            b.setCheckable(True)
            b.setFixedSize(22, 22)
            b.setToolTip(nome_cor)
            fundo = hexa or "transparent"
            b.setStyleSheet(f"QToolButton {{ background: {fundo}; border: 2px solid #333; border-radius: 11px; }}"
                            f"QToolButton:checked {{ border: 3px solid white; }}")
            if not hexa:
                b.setText("·")
            b.setProperty("cor", hexa)
            self.grupo_cor_efeito.addButton(b)
            lc.addWidget(b)
            if not hexa:
                b.setChecked(True)
        self.btn_outra_cor = QToolButton()
        self.btn_outra_cor.setText("…")
        self.btn_outra_cor.setToolTip("Outra cor…")
        self.btn_outra_cor.clicked.connect(self._escolher_outra_cor)
        lc.addWidget(self.btn_outra_cor)
        lc.addStretch(1)
        _desmarcavel(self.grupo_cor_efeito)
        self.grupo_cor_efeito.buttonClicked.connect(
            lambda b: self._definir_cor_efeito((b.property("cor") or "") if b.isChecked() else ""))
        lay.addWidget(self.linha_cor)

        linha = QHBoxLayout()
        self.cb_forma = QComboBox()
        for chave, nome in FORMAS.items():
            self.cb_forma.addItem(nome, chave)
        self.cb_forma.currentIndexChanged.connect(self._forma_editada)
        linha.addWidget(self.cb_forma, 1)
        lay.addLayout(linha)
        linha = QHBoxLayout()
        linha.addWidget(QLabel("Tamanho"))
        self.sp_tamanho = QDoubleSpinBox()
        self.sp_tamanho.setRange(0.5, 60)
        self.sp_tamanho.setSingleStep(1.5)
        self.sp_tamanho.setDecimals(1)
        self.sp_tamanho.setSuffix(" m")
        self.sp_tamanho.setValue(6.0)
        self.sp_tamanho.valueChanged.connect(self._efeito_editado)
        linha.addWidget(self.sp_tamanho)
        self.lbl_largura = QLabel("Largura")
        linha.addWidget(self.lbl_largura)
        self.sp_largura = QDoubleSpinBox()
        self.sp_largura.setRange(0.5, 12)
        self.sp_largura.setSingleStep(0.5)
        self.sp_largura.setDecimals(1)
        self.sp_largura.setSuffix(" m")
        self.sp_largura.setValue(1.5)
        self.sp_largura.valueChanged.connect(self._efeito_editado)
        linha.addWidget(self.sp_largura)
        linha.addStretch(1)
        lay.addLayout(linha)
        self.btn_colocar = QPushButton("📍 Colocar na mesa")
        self.btn_colocar.setObjectName("primario")
        self.btn_colocar.setCheckable(True)
        self.btn_colocar.toggled.connect(lambda v: self._ferramenta("efeito", v))
        lay.addWidget(self.btn_colocar)
        lay.addWidget(_dica("Clique no mapa = usa o tamanho acima. Clique e ARRASTE = escolhe a direção "
                            "e o tamanho (de 1,5 em 1,5 m). Shift = ângulo livre · Alt = mantém o tamanho. "
                            "Esc sai." + ("\nDuplo clique na área = editar · botão direito = apagar/girar."
                                          if mestre else "")))
        self.btn_apagar_templates = QPushButton("🗑 Apagar os templates dos jogadores" if mestre
                                                else "🗑 Apagar os meus templates")
        self.btn_apagar_templates.clicked.connect(self.apagar_templates.emit)
        lay.addWidget(self.btn_apagar_templates)
        if mestre:   # marcas no chão (queimado, corroído…) ficam até o mestre limpar
            self.btn_limpar_marcas = QPushButton("🧽 Limpar marcas do chão")
            self.btn_limpar_marcas.setToolTip("A área parada no lugar por uns segundos deixa o chão marcado "
                                              "(queimado, corroído, congelado…). Isso tira todas as marcas.\n"
                                              "Pra tirar só uma: selecione na ferramenta de seleção do terreno e apague.")
            self.btn_limpar_marcas.clicked.connect(self.limpar_marcas.emit)
            lay.addWidget(self.btn_limpar_marcas)

        # ---------------------------------------------------------------- cenário: gás e líquidos (v0.45)
        if mestre:
            from ..mesa.fluidos import TIPOS as TIPOS_FLUIDO
            lay = secao("fluidos", "🏞 Cenário: gás e líquidos", aberta=False)
            lay.addWidget(_dica("Gás e líquido de VERDADE: se espalham, não atravessam parede nem porta "
                                "fechada. Gás sem fonte vai ralando até sumir; líquido escorre e para. "
                                "(A área de efeito é a mágica: não espalha.)"))
            self.cb_fluido = QComboBox()
            for chave, (nome, *_r) in TIPOS_FLUIDO.items():
                self.cb_fluido.addItem(nome, chave)
            self.cb_fluido.currentIndexChanged.connect(self._fluido_editado)
            lay.addWidget(self.cb_fluido)
            grade = QGridLayout()
            self.cb_vazao = QComboBox()
            for chave, nome in (("fraca", "Fraca"), ("media", "Média"), ("forte", "Forte")):
                self.cb_vazao.addItem(nome, chave)
            self.cb_vazao.setCurrentIndex(1)
            self.cb_vazao.currentIndexChanged.connect(self._fluido_editado)
            self.sp_duracao = QDoubleSpinBox()
            self.sp_duracao.setRange(0, 3600)
            self.sp_duracao.setDecimals(0)
            self.sp_duracao.setSingleStep(10)
            self.sp_duracao.setSuffix(" s")
            self.sp_duracao.setSpecialValueText("sem parar")
            self.sp_duracao.valueChanged.connect(self._fluido_editado)
            self.sp_fluido_tam = QDoubleSpinBox()
            self.sp_fluido_tam.setRange(0.5, 15)
            self.sp_fluido_tam.setValue(2)
            self.sp_fluido_tam.setSingleStep(0.5)
            self.sp_fluido_tam.setSuffix(" m")
            self.sp_fluido_tam.valueChanged.connect(self._fluido_editado)
            for i, (rot, w) in enumerate((("Vazão da fonte", self.cb_vazao), ("Por quanto tempo", self.sp_duracao),
                                          ("Tamanho (soltar)", self.sp_fluido_tam))):
                grade.addWidget(QLabel(rot), i, 0)
                grade.addWidget(w, i, 1)
            lay.addLayout(grade)
            linha = QHBoxLayout()
            self.btn_fonte = QPushButton("📍 Pôr fonte")
            self.btn_fonte.setToolTip("Clique no mapa onde sai o gás/líquido (a boca da estátua, um cano…).\n"
                                      "Botão direito na fonte: ligar/desligar, tirar.")
            self.btn_soltar = QPushButton("💨 Soltar / derramar")
            self.btn_soltar.setToolTip("Clique no mapa: uma nuvem solta (gás) ou uma poça (líquido), sem fonte.")
            for b, nome in ((self.btn_fonte, "fonte_fluido"), (self.btn_soltar, "soltar_fluido")):
                b.setCheckable(True)
                b.toggled.connect(lambda v, n=nome: self._ferramenta(n, v))
                linha.addWidget(b)
            lay.addLayout(linha)
            self.btn_limpar_fluidos = QPushButton("🧽 Limpar gás e líquidos")
            self.btn_limpar_fluidos.clicked.connect(lambda: self.limpar_fluidos.emit(False))
            self.btn_tirar_fontes = QPushButton("Tirar todas as fontes")
            self.btn_tirar_fontes.clicked.connect(lambda: self.limpar_fluidos.emit(True))
            linha = QHBoxLayout()
            linha.addWidget(self.btn_limpar_fluidos)
            linha.addWidget(self.btn_tirar_fontes)
            lay.addLayout(linha)

        # ---------------------------------------------------------------- lançar (v0.41)
        from ..mesa.lancamentos import ELEMENTOS, LIMITES, TIPOS_LANCE
        lay = secao("lancar", "🎯 Lançar (bola de fogo, jato…)", aberta=False)
        self.cb_lance_el = QComboBox()
        for chave, (nome_proj, *_r) in ELEMENTOS.items():
            rotulo = EFEITOS[chave][0] if chave in EFEITOS else chave
            self.cb_lance_el.addItem(f"{rotulo}  ·  {nome_proj}", chave)
        self.cb_lance_el.currentIndexChanged.connect(self._lance_editado)
        lay.addWidget(self.cb_lance_el)
        self.cb_lance_tipo = QComboBox()
        for chave, nome in TIPOS_LANCE.items():
            self.cb_lance_tipo.addItem(nome, chave)
        self.cb_lance_tipo.currentIndexChanged.connect(self._lance_editado)
        lay.addWidget(self.cb_lance_tipo)
        from ..mesa.lancamentos import PROJETEIS
        self.cb_lance_proj = QComboBox()   # formato do projétil (orbe, míssil mágico, lança…)
        for chave, nome in PROJETEIS.items():
            self.cb_lance_proj.addItem(nome, chave)
        self.cb_lance_proj.currentIndexChanged.connect(self._lance_editado)
        lay.addWidget(self.cb_lance_proj)
        self.cb_lance_cor = QComboBox()    # cor (magia, fogo negro, raio vermelho…)
        self.cb_lance_cor.activated.connect(self._lance_cor_escolhida)
        lay.addWidget(self.cb_lance_cor)
        self._lance_cor = ""
        grade = QGridLayout()

        def spin(minimo, maximo, valor, passo, sufixo):
            s = QDoubleSpinBox()
            s.setRange(minimo, maximo)
            s.setValue(valor)
            s.setSingleStep(passo)
            s.setDecimals(1)
            s.setSuffix(sufixo)
            s.valueChanged.connect(self._lance_editado)
            return s
        self.sp_lance_abertura = spin(*LIMITES["abertura"], 53, 5, "°")
        self.sp_lance_largura = spin(*LIMITES["largura"], 1.5, 0.5, " m")
        self.sp_lance_vel = spin(*LIMITES["velocidade"], 14, 1, " m/s")
        self.sp_lance_tam = spin(*LIMITES["tam"], 3, 0.5, " m")
        self.lb_lance_abertura = QLabel("Abertura")
        self.lb_lance_largura = QLabel("Largura")
        self.lb_lance_tam = QLabel("Raio no alvo")
        for i, (rot, sp) in enumerate(((self.lb_lance_abertura, self.sp_lance_abertura),
                                       (self.lb_lance_largura, self.sp_lance_largura),
                                       (QLabel("Velocidade"), self.sp_lance_vel),
                                       (self.lb_lance_tam, self.sp_lance_tam))):
            grade.addWidget(rot, i, 0)
            grade.addWidget(sp, i, 1)
        lay.addLayout(grade)
        self.ck_lance_deixar = QCheckBox("Deixar a área no chão quando chegar")
        self.ck_lance_deixar.setToolTip("Ex.: a bola de fogo deixa fogo onde caiu; a bolha de ácido, uma poça.")
        self.ck_lance_deixar.toggled.connect(self._lance_editado)
        lay.addWidget(self.ck_lance_deixar)
        self.btn_lancar = QPushButton("🎯 Lançar")
        self.btn_lancar.setObjectName("primario")
        self.btn_lancar.setCheckable(True)
        self.btn_lancar.toggled.connect(lambda v: self._ferramenta("lancar", v))
        lay.addWidget(self.btn_lancar)
        lay.addWidget(_dica("Arraste de quem lança até o alvo (começando em cima do token, sai do centro dele). "
                            "A distância é o arrasto. Esc sai."))
        self._lance_editado()

        # ---------------------------------------------------------------- lápis
        lay = secao("lapis", "✏ Lápis", aberta=False)
        self.btn_lapis = QPushButton("✏ Rabiscar no mapa")
        self.btn_lapis.setCheckable(True)
        self.btn_lapis.toggled.connect(lambda v: self._ferramenta("lapis", v))
        lay.addWidget(self.btn_lapis)
        cores = QHBoxLayout()
        cores.setSpacing(3)
        self.grupo_cor = QButtonGroup(self)
        for cor in CORES_LAPIS:
            b = QToolButton()
            b.setCheckable(True)
            b.setFixedSize(22, 22)
            b.setStyleSheet(f"QToolButton {{ background: {cor}; border: 2px solid #333; border-radius: 11px; }}"
                            f"QToolButton:checked {{ border: 3px solid white; }}")
            b.setProperty("cor", cor)
            self.grupo_cor.addButton(b)
            cores.addWidget(b)
        cores.addStretch(1)
        _desmarcavel(self.grupo_cor)
        self.grupo_cor.buttonClicked.connect(self._lapis_editado)
        lay.addLayout(cores)
        linha = QHBoxLayout()
        self.cb_esp = QComboBox()
        for nome, v in (("Fino", 2.0), ("Médio", 4.0), ("Grosso", 8.0)):
            self.cb_esp.addItem(nome, v)
        self.cb_esp.setCurrentIndex(1)
        self.cb_esp.currentIndexChanged.connect(self._lapis_editado)
        linha.addWidget(self.cb_esp)
        self.ck_temp = QCheckBox("Some sozinho (10 s)")
        self.ck_temp.setChecked(True)
        self.ck_temp.toggled.connect(self._lapis_editado)
        linha.addWidget(self.ck_temp, 1)
        lay.addLayout(linha)
        self.btn_apagar_desenhos = QPushButton("🧽 Apagar TODOS os rabiscos" if mestre else "🧽 Apagar os meus rabiscos")
        self.btn_apagar_desenhos.clicked.connect(self.apagar_desenhos.emit)
        lay.addWidget(self.btn_apagar_desenhos)

        # o mestre põe aqui as regras "jogadores podem…" (janela_mestre)
        if mestre:
            self.layout_extra = secao("jogadores", "👥 Jogadores podem…", aberta=False)
        else:
            self.layout_extra = QVBoxLayout()
            self.layout_principal.addLayout(self.layout_extra)
        self.layout_principal.addStretch(1)
        self._forma_editada()
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    # ------------------------------------------------------------ cena
    def definir_cena(self, cena):
        self.cena = cena
        self._mudando = True
        try:
            if self.mestre:
                clima = getattr(cena, "clima", {"tipo": "nenhum", "forca": 2})
                i = self.cb_clima.findData(clima.get("tipo", "nenhum"))
                self.cb_clima.setCurrentIndex(max(0, i))
                self.sl_forca.setValue(int(clima.get("forca", 2)))
            ef = getattr(cena, "efeito_atual", None)
            if ef:
                for b in self.grupo_efeito.buttons():
                    b.setChecked(b.property("chave") == ef.get("efeito"))
                self.cb_forma.setCurrentIndex(max(0, self.cb_forma.findData(ef.get("forma", "circulo"))))
                self.sp_tamanho.setValue(float(ef.get("tamanho", 6)))
                self.sp_largura.setValue(float(ef.get("largura", 1.5)))
            lp = getattr(cena, "lapis", None)
            if lp:
                for b in self.grupo_cor.buttons():
                    b.setChecked(b.property("cor") == lp.get("cor"))
                self.cb_esp.setCurrentIndex(max(0, self.cb_esp.findData(float(lp.get("esp", 4)))))
                self.ck_temp.setChecked(bool(lp.get("temp", True)))
            self.ferramenta_atual(getattr(cena, "ferramenta", "selecionar"))
        finally:
            self._mudando = False
        self._forma_editada(atualizar_tamanho=False)
        self._lance_editado()
        self._fluido_editado()

    def ferramenta_atual(self, nome: str):
        """A cena trocou de ferramenta (ex.: Esc): acerta os botões sem disparar nada."""
        for chave, botao in self._botoes_ferramenta():
            botao.blockSignals(True)
            botao.setChecked(nome == chave)
            botao.blockSignals(False)
        if nome != "efeito":   # saiu de colocar área (Esc, outra ferramenta): o efeito fica desmarcado
            for b in self.grupo_efeito.buttons():
                b.setChecked(False)
        atual = (getattr(self.cena, "impacto_atual", None) or {}).get("tipo") if nome == "impacto" else None
        for chave, b in self.botoes_impacto.items():
            if b.isCheckable():
                b.setChecked(chave == atual)

    def _armar_impacto(self, chave, ligado):
        if self.cena is None:
            return
        if ligado:
            self.cena.impacto_atual = {"tipo": chave, "tam": self.sp_impacto.value()}
            self.ferramenta.emit("impacto")
        else:
            self.ferramenta.emit("selecionar")

    def _impacto_editado(self):
        if self.cena is not None and getattr(self.cena, "impacto_atual", None):
            self.cena.impacto_atual["tam"] = self.sp_impacto.value()

    def permitir(self, templates: bool, lapis: bool):
        """Player: o mestre pode desligar templates e/ou lápis."""
        self.btn_colocar.setEnabled(templates)
        self.btn_lapis.setEnabled(lapis)
        self.btn_colocar.setToolTip("" if templates else "O mestre desligou os templates dos jogadores")
        self.btn_lapis.setToolTip("" if lapis else "O mestre desligou o lápis dos jogadores")
        if not templates and self.btn_colocar.isChecked():
            self.btn_colocar.setChecked(False)
        if not lapis and self.btn_lapis.isChecked():
            self.btn_lapis.setChecked(False)

    # ------------------------------------------------------------ mudanças
    def _ferramenta(self, nome, ligado):
        if self._mudando:
            return
        if ligado:
            for chave, outro in self._botoes_ferramenta():
                if chave != nome:
                    outro.blockSignals(True)
                    outro.setChecked(False)
                    outro.blockSignals(False)
            if nome == "lancar":
                self._lance_editado()
            if nome == "efeito":
                self._marcar_efeito_atual()
            self.ferramenta.emit(nome)
        else:
            self.ferramenta.emit("selecionar")

    def _clima_editado(self, *_):
        if self._mudando:
            return
        self.clima_mudou.emit(self.cb_clima.currentData(), self.sl_forca.value())

    def _forma_editada(self, *_, atualizar_tamanho=True):
        forma = self.cb_forma.currentData()
        linha = forma == "linha"
        self.lbl_largura.setVisible(linha)
        self.sp_largura.setVisible(linha)
        if atualizar_tamanho and not self._mudando and self.cena is not None:
            self._mudando = True
            self.sp_tamanho.setValue(TAMANHO_PADRAO[forma])
            self._mudando = False
        self._efeito_editado()

    def _definir_cor_efeito(self, cor: str):
        self.cor_efeito = cor
        if cor and not any(b.property("cor") == cor for b in self.grupo_cor_efeito.buttons()):
            for b in self.grupo_cor_efeito.buttons():   # cor de fora da lista: marca o "…"
                b.setChecked(False)
            self.btn_outra_cor.setStyleSheet(f"QToolButton {{ background: {cor}; border: 3px solid white;"
                                             f" border-radius: 11px; min-width: 18px; }}")
        else:
            self.btn_outra_cor.setStyleSheet("")
        self._efeito_editado()

    def _escolher_outra_cor(self):
        from PyQt6.QtWidgets import QColorDialog
        cor = QColorDialog.getColor(QColor(self.cor_efeito or "#b07aff"), self, "Cor da magia")
        if cor.isValid():
            self._definir_cor_efeito(cor.name())

    def _marcar_efeito_atual(self):
        """Armou o "Colocar na mesa" sem efeito marcado: marca o que está valendo."""
        ef = (getattr(self.cena, "efeito_atual", None) or {}).get("efeito", "fogo") if self.cena is not None else "fogo"
        if _marcado(self.grupo_efeito) is None:
            for b in self.grupo_efeito.buttons():
                b.setChecked(b.property("chave") == ef)

    def _efeito_clicado(self, b):
        """(v0.48) Escolheu um efeito = já arma o "Colocar na mesa"; clicou de novo no mesmo = desarma."""
        self._efeito_editado()
        if b.isChecked():
            if self.btn_colocar.isEnabled() and not self.btn_colocar.isChecked():
                self.btn_colocar.setChecked(True)
        elif self.btn_colocar.isChecked():
            self.btn_colocar.setChecked(False)

    def _efeito_editado(self, *_):
        b = _marcado(self.grupo_efeito)
        anterior = (getattr(self.cena, "efeito_atual", None) or {}).get("efeito") if self.cena is not None else None
        chave = b.property("chave") if b else (anterior or "fogo")
        self.linha_cor.setVisible(chave in CORES_LIVRES)   # só os efeitos "mágicos" têm cor livre
        if self._mudando or self.cena is None:
            return
        self.cena.efeito_atual = {"efeito": chave,
                                  "forma": self.cb_forma.currentData(),
                                  "tamanho": self.sp_tamanho.value(), "largura": self.sp_largura.value(),
                                  "cor": self.cor_efeito if chave in CORES_LIVRES else ""}

    def _botoes_ferramenta(self):
        lista = [("efeito", self.btn_colocar), ("lapis", self.btn_lapis), ("lancar", self.btn_lancar)]
        if self.mestre:
            lista += [("fonte_fluido", self.btn_fonte), ("soltar_fluido", self.btn_soltar)]
        return lista

    def _fluido_editado(self, *_):
        if self.cena is None or not self.mestre:
            return
        self.cena.fluido_atual = {"tipo": self.cb_fluido.currentData(), "vazao": self.cb_vazao.currentData(),
                                  "duracao": self.sp_duracao.value(), "tam": self.sp_fluido_tam.value()}

    def _cores_do_lance(self, el):
        """Enche a lista de cores do elemento escolhido (a que estava escolhida continua, se der)."""
        from PyQt6.QtGui import QIcon, QPixmap
        from ..mesa.lancamentos import CORES_PRONTAS
        if getattr(self, "_cores_de", None) == el:
            return
        self._cores_de = el
        opcoes = CORES_PRONTAS.get(el) or ([("Normal", "")] + list(CORES_MAGIA))
        self.cb_lance_cor.blockSignals(True)
        self.cb_lance_cor.clear()
        for nome, hexa in opcoes:
            if hexa:
                pm = QPixmap(14, 14)
                pm.fill(QColor(hexa))
                self.cb_lance_cor.addItem(QIcon(pm), nome, hexa)
            else:
                self.cb_lance_cor.addItem(nome, "")
        self.cb_lance_cor.addItem("Outra cor…", "__outra__")
        self._lance_cor = ""
        self.cb_lance_cor.setCurrentIndex(0)
        self.cb_lance_cor.blockSignals(False)

    def _lance_cor_escolhida(self, _i):
        dado = self.cb_lance_cor.currentData()
        if dado == "__outra__":
            from PyQt6.QtGui import QIcon, QPixmap
            from PyQt6.QtWidgets import QColorDialog
            cor = QColorDialog.getColor(QColor(self._lance_cor or "#b07aff"), self, "Cor do poder")
            if not cor.isValid():
                self.cb_lance_cor.setCurrentIndex(0)
                dado = ""
            else:
                pm = QPixmap(14, 14)
                pm.fill(cor)
                self.cb_lance_cor.insertItem(self.cb_lance_cor.count() - 1, QIcon(pm), f"Outra ({cor.name()})", cor.name())
                self.cb_lance_cor.setCurrentIndex(self.cb_lance_cor.count() - 2)
                dado = cor.name()
        self._lance_cor = dado or ""
        self._lance_editado()

    def _lance_editado(self, *_):
        from ..mesa.lancamentos import CORES_LANCE
        el = self.cb_lance_el.currentData()
        self.cb_lance_cor.setVisible(el in CORES_LANCE)
        if el in CORES_LANCE:
            self._cores_do_lance(el)
        tipo = self.cb_lance_tipo.currentData()
        self.cb_lance_proj.setVisible(tipo == "projetil")
        self.lb_lance_abertura.setVisible(tipo == "cone")
        self.sp_lance_abertura.setVisible(tipo == "cone")
        self.lb_lance_largura.setVisible(tipo == "linha")
        self.sp_lance_largura.setVisible(tipo == "linha")
        alvo = tipo == "projetil" and self.ck_lance_deixar.isChecked()
        self.lb_lance_tam.setVisible(alvo)
        self.sp_lance_tam.setVisible(alvo)
        if self.cena is None:
            return
        self.cena.lance_atual = {"elemento": el, "tipo": tipo, "projetil": self.cb_lance_proj.currentData(),
                                 "abertura": self.sp_lance_abertura.value(),
                                 "largura": self.sp_lance_largura.value(), "velocidade": self.sp_lance_vel.value(),
                                 "tam": self.sp_lance_tam.value(), "deixar": self.ck_lance_deixar.isChecked(),
                                 "cor": self._lance_cor if el in CORES_LANCE else ""}

    def _lapis_editado(self, *_):
        if self._mudando or self.cena is None:
            return
        b = _marcado(self.grupo_cor)
        self.cena.lapis = {"cor": b.property("cor") if b else CORES_LAPIS[0],
                           "esp": self.cb_esp.currentData(), "temp": self.ck_temp.isChecked()}
