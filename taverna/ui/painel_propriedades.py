"""
Painel de propriedades: mostra o que está selecionado.
  - Mapa: digitar largura/altura em metros, manter proporção, voltar à proporção original
  - Token: resumo + botão de editar
"""

from PyQt6.QtWidgets import (QLineEdit, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QLabel,
                             QPushButton, QStackedWidget, QVBoxLayout, QWidget)

from ..config import MAPA_MIN_METROS, TIPOS_TOKEN
from ..mesa.mapa import MapaItem
from ..mesa.luzes import TIPOS_LUZ, LuzItem
from ..mesa.portas import TIPOS_PORTA, PortaItem
from ..mesa.token import TokenItem


def nomes_de_itens(cena) -> list[str]:
    """Nomes de todos os itens do cenário (baús, itens soltos, inventários) — pra sugerir a chave."""
    from ..mesa.props import PropItem
    from ..mesa.token import TokenItem
    nomes = set()
    for i in cena.itens_do_usuario():
        if isinstance(i, PropItem):
            nomes.update(str(x.get("nome", "")) for x in i.itens)
        elif isinstance(i, TokenItem):
            nomes.update(str(x.get("nome", "")) for x in i.info.get("inventario", {}).get("v") or [])
    return sorted(n for n in nomes if n)


class PainelPropriedades(QWidget):
    def __init__(self, cena, ao_editar_token, parent=None):
        super().__init__(parent)
        self.cena = cena
        self.ao_editar_token = ao_editar_token
        self.mapa: MapaItem | None = None
        self.token: TokenItem | None = None
        self._bloqueado = False

        self.pilha = QStackedWidget()

        # --- nada selecionado
        vazio = QLabel("Selecione um mapa ou token\npara ver as propriedades.\n\n"
                       "Dica: arraste uma imagem do\nWindows direto pra mesa.")
        vazio.setObjectName("dica")
        vazio.setWordWrap(True)
        self.pilha.addWidget(self._embrulhar(vazio))

        # --- mapa
        self.larg = self._spin()
        self.alt = self._spin()
        self.larg.valueChanged.connect(lambda v: self._tamanho_digitado("w"))
        self.alt.valueChanged.connect(lambda v: self._tamanho_digitado("h"))
        self.proporcao = QCheckBox("Manter proporção")
        self.proporcao.toggled.connect(self._proporcao_mudou)
        resetar = QPushButton("Voltar à proporção original")
        resetar.clicked.connect(self._resetar_proporcao)
        dica_mapa = QLabel("Alças nos cantos redimensionam.\n"
                           "Shift: alterna a proporção.\nCtrl: arredonda pra metros inteiros.")
        dica_mapa.setObjectName("dica")
        form = QFormLayout()
        form.addRow("Largura", self.larg)
        form.addRow("Altura", self.alt)
        caixa_mapa = QVBoxLayout()
        titulo_mapa = QLabel("Mapa")
        titulo_mapa.setObjectName("titulo")
        caixa_mapa.addWidget(titulo_mapa)
        caixa_mapa.addLayout(form)
        caixa_mapa.addWidget(self.proporcao)
        caixa_mapa.addWidget(resetar)
        caixa_mapa.addSpacing(8)
        caixa_mapa.addWidget(dica_mapa)
        caixa_mapa.addStretch()
        w_mapa = QWidget()
        w_mapa.setLayout(caixa_mapa)
        self.pilha.addWidget(w_mapa)

        # --- token
        self.token_titulo = QLabel()
        self.token_titulo.setObjectName("titulo")
        self.token_info = QLabel()
        self.token_info.setWordWrap(True)
        editar = QPushButton("Editar token…")
        editar.setObjectName("primario")
        editar.clicked.connect(lambda: self.token and self.ao_editar_token(self.token))
        # Visão do token (jogadores)
        from ..mesa.linha_de_visao import PRESETS_VISAO
        self.v_titulo = QLabel("Visão")
        self.v_titulo.setObjectName("titulo")
        self.v_preset = QComboBox()
        self.v_preset.addItem("Atalhos de visão…", None)
        for chave, valores in PRESETS_VISAO.items():
            self.v_preset.addItem(valores[0], chave)
        self.v_preset.currentIndexChanged.connect(self._preset_visao)
        self.v_alcance = self._spin_m(0, 100, 1, 0)
        self.v_abertura = QDoubleSpinBox()
        self.v_abertura.setRange(0, 360)
        self.v_abertura.setDecimals(0)
        self.v_abertura.setSingleStep(15)
        self.v_abertura.setSuffix("°")
        self.v_direcao = QDoubleSpinBox()
        self.v_direcao.setRange(0, 359)
        self.v_direcao.setDecimals(0)
        self.v_direcao.setSingleStep(15)
        self.v_direcao.setWrapping(True)
        self.v_direcao.setSuffix("°")
        self.v_girar = QCheckBox("Jogador pode girar pra onde olha")
        self.v_escuro = self._spin_m(0, 100, 1, 0)
        self.v_escuro.setToolTip("Enxerga até essa distância mesmo sem luz (dentro do cone)")
        for w in (self.v_alcance, self.v_abertura, self.v_direcao, self.v_escuro):
            w.valueChanged.connect(self._visao_editada)
        self.v_girar.toggled.connect(self._visao_editada)
        form_v = QFormLayout()
        form_v.addRow("Alcance", self.v_alcance)
        form_v.addRow("Abertura", self.v_abertura)
        form_v.addRow("Olhando p/", self.v_direcao)
        form_v.addRow("No escuro", self.v_escuro)
        self.caixa_visao = QWidget()
        lv = QVBoxLayout(self.caixa_visao)
        lv.setContentsMargins(0, 8, 0, 0)
        lv.addWidget(self.v_titulo)
        lv.addWidget(self.v_preset)
        lv.addLayout(form_v)
        lv.addWidget(self.v_girar)
        dica_v = QLabel("0° = direita, 90° = baixo. Atalhos: , e . giram 15° · F olha pro mouse.")
        dica_v.setObjectName("dica")
        dica_v.setWordWrap(True)
        lv.addWidget(dica_v)

        # Luz que o token carrega (tocha, lanterna...) — anda junto com ele
        from ..mesa.luzes import LUZES_DE_MAO, TIPOS_LUZ
        self.t_luz = QComboBox()
        self.t_luz.addItem("— nenhuma —", None)
        for chave in LUZES_DE_MAO:
            self.t_luz.addItem(f"🔥 {TIPOS_LUZ[chave][0]}", chave)
        self.t_luz.setToolTip("A luz anda junto com o token (vale pra luz ambiente escura)")
        self.t_luz.currentIndexChanged.connect(self._luz_do_token)
        linha_luz = QFormLayout()
        linha_luz.addRow("Carrega luz", self.t_luz)

        caixa_token = QVBoxLayout()
        caixa_token.addWidget(self.token_titulo)
        caixa_token.addWidget(self.token_info)
        caixa_token.addWidget(editar)
        caixa_token.addLayout(linha_luz)
        caixa_token.addWidget(self.caixa_visao)
        caixa_token.addStretch()
        w_token = QWidget()
        w_token.setLayout(caixa_token)
        self.pilha.addWidget(w_token)

        # --- vários
        self.varios = QLabel()
        self.varios.setObjectName("dica")
        self.pilha.addWidget(self._embrulhar(self.varios))

        # --- objeto (prop)  [página 6]
        self.prop = None
        self.ao_editar_prop = None        # função(prop)
        self.ao_mostrar_conteudo = None   # função(prop)
        self.prop_titulo = QLabel()
        self.prop_titulo.setObjectName("titulo")
        self.prop_info = QLabel()
        self.prop_info.setWordWrap(True)
        b_editar = QPushButton("Editar objeto e conteúdo…")
        b_editar.setObjectName("primario")
        b_editar.clicked.connect(lambda: self.prop and self.ao_editar_prop and self.ao_editar_prop(self.prop))
        b_girar = QPushButton("↻ Girar 90°")
        b_girar.clicked.connect(lambda: self.prop and (self.prop.girar(90), self._mostrar_prop()))
        self.prop_trancado = QCheckBox("🔒 Trancado")
        self.prop_trancado.toggled.connect(lambda v: self._prop_flag("trancado", v))
        self.prop_luz = QCheckBox("💡 Luz acesa")
        self.prop_luz.toggled.connect(lambda v: self._prop_flag("luz_acesa", v))
        self.prop_movel = QCheckBox("✋ Jogadores podem mover")
        self.prop_movel.toggled.connect(lambda v: self._prop_flag("movel", v))
        self.prop_bloqueia = QCheckBox("🧱 Bloqueia a visão")
        self.prop_bloqueia.toggled.connect(lambda v: self._prop_flag("bloqueia", v))
        self.b_mostrar = QPushButton("👁 Mostrar o conteúdo pros jogadores…")
        self.b_mostrar.clicked.connect(lambda: self.prop and self.ao_mostrar_conteudo and
                                       self.ao_mostrar_conteudo(self.prop))
        dica_prop = QLabel("Duplo clique abre a edição. Clique direito: girar, trancar, mostrar conteúdo…")
        dica_prop.setObjectName("dica")
        dica_prop.setWordWrap(True)
        caixa_prop = QVBoxLayout()
        for w in (self.prop_titulo, self.prop_info, b_editar, b_girar, self.prop_trancado,
                  self.prop_luz, self.prop_movel, self.prop_bloqueia, self.b_mostrar, dica_prop):
            caixa_prop.addWidget(w)
        caixa_prop.addStretch()
        self._pagina_prop = QWidget()
        self._pagina_prop.setLayout(caixa_prop)   # entra na pilha no fim do __init__

        # --- porta (página 4)
        self.porta: PortaItem | None = None
        self.p_tipo = QComboBox()
        for chave, (nome, _, _) in TIPOS_PORTA.items():
            self.p_tipo.addItem(nome, chave)
        self.p_largura = self._spin_m(0.5, 10, 0.5, 1)
        self.p_espessura = self._spin_m(0.05, 2, 0.05, 2)
        self.p_dupla = QCheckBox("Porta dupla")
        self.p_lado = QComboBox()
        self.p_lado.addItem("Para um lado (A)", 1)
        self.p_lado.addItem("Para o outro lado (B)", -1)
        self.p_dobradica = QComboBox()
        self.p_dobradica.addItem("Esquerda", -1)
        self.p_dobradica.addItem("Direita", 1)
        self.p_angulo = QDoubleSpinBox()
        self.p_angulo.setRange(-360, 360)
        self.p_angulo.setDecimals(0)
        self.p_angulo.setSingleStep(15)
        self.p_angulo.setSuffix("°")
        self.p_angulo.setWrapping(True)
        self.p_aberta = QCheckBox("Aberta")
        self.p_jogadores = QCheckBox("Jogadores podem abrir/fechar")
        self.p_jogadores.setToolTip("Duplo clique do jogador (perto, até 1,5 m; no combate, na vez dele)")
        self.p_trancada = QCheckBox("🔒 Trancada (o jogador não abre)")
        self.p_nome = QLineEdit()
        self.p_nome.setPlaceholderText("ex.: Porta armadilha (opcional)")
        self.p_nome.editingFinished.connect(self._porta_editada)
        self.p_chave = QLineEdit()
        self.p_chave.setPlaceholderText("nome do item, ex.: Chave armadilha")
        self.p_chave.setToolTip("Se o jogador tiver um item com esse nome no inventário,\n"
                                "a porta trancada destranca e abre pra ele.")
        self.p_chave.editingFinished.connect(self._porta_editada)
        self.p_gasta = QCheckBox("A chave some ao usar")
        self.p_gasta.toggled.connect(self._porta_editada)
        for w in (self.p_tipo, self.p_lado, self.p_dobradica):
            w.currentIndexChanged.connect(self._porta_editada)
        for w in (self.p_largura, self.p_espessura, self.p_angulo):
            w.valueChanged.connect(self._porta_editada)
        for w in (self.p_dupla, self.p_aberta, self.p_jogadores, self.p_trancada):
            w.toggled.connect(self._porta_editada)
        form_p = QFormLayout()
        form_p.addRow("Tipo", self.p_tipo)
        form_p.addRow("Largura", self.p_largura)
        form_p.addRow("Espessura", self.p_espessura)
        form_p.addRow("Abre", self.p_lado)
        form_p.addRow("Dobradiça", self.p_dobradica)
        form_p.addRow("Ângulo", self.p_angulo)
        titulo_p = QLabel("Porta")
        titulo_p.setObjectName("titulo")
        dica_p = QLabel("Duplo clique na porta abre/fecha.\nArraste pra mover. A setinha "
                        "mostra pra que lado ela abre.")
        dica_p.setObjectName("dica")
        dica_p.setWordWrap(True)
        caixa_p = QVBoxLayout()
        caixa_p.addWidget(titulo_p)
        caixa_p.addLayout(form_p)
        caixa_p.addWidget(self.p_dupla)
        caixa_p.addWidget(self.p_aberta)
        caixa_p.addWidget(self.p_jogadores)
        caixa_p.addWidget(self.p_trancada)
        form_chave = QFormLayout()
        form_chave.addRow("Nome", self.p_nome)
        form_chave.addRow("🗝 Chave", self.p_chave)
        caixa_p.addLayout(form_chave)
        caixa_p.addWidget(self.p_gasta)
        caixa_p.addWidget(dica_p)
        caixa_p.addStretch()
        w_porta = QWidget()
        w_porta.setLayout(caixa_p)
        self.pilha.addWidget(w_porta)

        # --- luz (página 5)
        from ..mesa.luzes import TIPOS_LUZ
        self.luz = None
        self.l_tipo = QComboBox()
        for chave, valores in TIPOS_LUZ.items():
            self.l_tipo.addItem(valores[0], chave)
        self.l_forte = self._spin_m(0, 60, 0.5, 1)
        self.l_fraco = self._spin_m(0.5, 80, 0.5, 1)
        self.l_cor = QPushButton()
        self.l_cor.clicked.connect(self._cor_luz)
        self.l_tremula = QCheckBox("Tremular (chama)")
        self.l_acesa = QCheckBox("Acesa")
        self.l_tipo.currentIndexChanged.connect(self._tipo_luz)
        for w in (self.l_forte, self.l_fraco):
            w.valueChanged.connect(self._luz_editada)
        for w in (self.l_tremula, self.l_acesa):
            w.toggled.connect(self._luz_editada)
        form_l = QFormLayout()
        form_l.addRow("Tipo", self.l_tipo)
        form_l.addRow("Luz forte", self.l_forte)
        form_l.addRow("Penumbra até", self.l_fraco)
        form_l.addRow("Cor", self.l_cor)
        titulo_l = QLabel("Luz")
        titulo_l.setObjectName("titulo")
        dica_l = QLabel("A luz para nas paredes e passa pelas portas abertas.\n"
                        "Duplo clique acende/apaga.")
        dica_l.setObjectName("dica")
        dica_l.setWordWrap(True)
        caixa_l = QVBoxLayout()
        caixa_l.addWidget(titulo_l)
        caixa_l.addLayout(form_l)
        caixa_l.addWidget(self.l_tremula)
        caixa_l.addWidget(self.l_acesa)
        caixa_l.addWidget(dica_l)
        caixa_l.addStretch()
        w_luz = QWidget()
        w_luz.setLayout(caixa_l)
        self.pilha.addWidget(w_luz)
        self.pilha.addWidget(self._pagina_prop)   # objeto (prop): sempre a última página

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.pilha)

        cena.selectionChanged.connect(self.atualizar)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def definir_cena(self, cena):
        try:
            self.cena.selectionChanged.disconnect(self.atualizar)
        except (TypeError, RuntimeError):
            pass
        self.soltar_referencias()
        self.cena = cena
        cena.selectionChanged.connect(self.atualizar)
        self.atualizar()

    def _embrulhar(self, widget):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(widget)
        l.addStretch()
        return w

    def _spin_m(self, minimo, maximo, passo, casas):
        s = QDoubleSpinBox()
        s.setRange(minimo, maximo)
        s.setSingleStep(passo)
        s.setDecimals(casas)
        s.setSuffix(" m")
        return s

    def _spin(self):
        s = QDoubleSpinBox()
        s.setRange(MAPA_MIN_METROS, 9999)
        s.setDecimals(1)
        s.setSingleStep(0.5)
        s.setSuffix(" m")
        s.setKeyboardTracking(False)
        return s

    # ------------------------------------------------------------ seleção
    def soltar_referencias(self):
        """Esquece os itens (chamar antes de limpar a cena)."""
        self.prop = None
        if self.mapa is not None:
            try:
                self.mapa.tamanho_mudou.disconnect(self._mapa_redimensionado)
            except (TypeError, RuntimeError):
                pass
        self.mapa = None
        self.token = None
        self.porta = None
        self.luz = None
        self.pilha.setCurrentIndex(0)

    def atualizar(self):
        try:
            selecionados = [i for i in self.cena.selectedItems() if hasattr(i, "para_dict")]
        except RuntimeError:
            return
        self.soltar_referencias()
        if len(selecionados) == 1 and isinstance(selecionados[0], MapaItem):
            self.mapa = selecionados[0]
            self.mapa.tamanho_mudou.connect(self._mapa_redimensionado)
            self._mapa_redimensionado()
            self._bloqueado = True
            self.proporcao.setChecked(self.mapa.manter_proporcao)
            self._bloqueado = False
            self.pilha.setCurrentIndex(1)
        elif len(selecionados) == 1 and isinstance(selecionados[0], TokenItem):
            self.token = selecionados[0]
            self.mostrar_token()
            self.pilha.setCurrentIndex(2)
        elif len(selecionados) == 1 and isinstance(selecionados[0], LuzItem):
            self.luz = selecionados[0]
            self._mostrar_luz()
            self.pilha.setCurrentIndex(5)
        elif len(selecionados) == 1 and isinstance(selecionados[0], PortaItem):
            self.porta = selecionados[0]
            self._mostrar_porta()
            self.pilha.setCurrentIndex(4)
        elif len(selecionados) == 1 and hasattr(selecionados[0], "efeito_area"):
            e = selecionados[0]
            self.varios.setText(f"Área de efeito\n{e.descricao()}"
                                + (f"\nColocada por {e.dono}" if e.dono else "")
                                + "\n\nDuplo clique: editar (efeito, forma, tamanho, ângulo).\n"
                                  "Botão direito: trocar efeito, girar, remover.\nArraste pra mover.")
            self.pilha.setCurrentIndex(3)
        elif len(selecionados) == 1 and hasattr(selecionados[0], "luz_dict") \
                and hasattr(selecionados[0], "itens"):
            self.prop = selecionados[0]
            self._mostrar_prop()
            self.pilha.setCurrentWidget(self._pagina_prop)
        elif len(selecionados) > 1:
            self.varios.setText(f"{len(selecionados)} itens selecionados.\n"
                                "Delete remove todos.")
            self.pilha.setCurrentIndex(3)

    def _mostrar_prop(self):
        p = self.prop
        if p is None:
            return
        self._bloqueado = True
        self.prop_titulo.setText(p.nome)
        linhas = [f"Tamanho: {p.w:g} × {p.h:g} m · girado {p.angulo:g}°".replace(".", ",")]
        if p.interativo:
            linhas.append(f"Interativo · {len(p.itens)} item(ns) dentro")
        if p.tipo == "escada":
            linhas.append("Escada · " + ("🚫 bloqueada pros jogadores" if p.trancado else "✅ liberada pros jogadores"))
        self.prop_info.setText("\n".join(linhas))
        self.prop_trancado.setVisible(p.interativo)
        self.prop_trancado.setChecked(p.trancado)
        self.b_mostrar.setVisible(p.interativo)
        self.prop_luz.setVisible(bool(p.luz))
        self.prop_luz.setChecked(p.luz_acesa)
        self.prop_bloqueia.setChecked(p.bloqueia)
        self.prop_movel.setChecked(p.movel)
        self._bloqueado = False

    def _prop_flag(self, nome, valor):
        if self._bloqueado or self.prop is None:
            return
        setattr(self.prop, nome, valor)
        self.prop._mudou()

    def _luz_do_token(self, *_):
        if self._bloqueado or not self.token:
            return
        self.token.luz = self.t_luz.currentData()
        self.token.update()
        self.token._avisar_modificacao()

    def mostrar_token(self):
        t = self.token
        if not t:
            return
        self._bloqueado = True
        self.t_luz.setCurrentIndex(max(0, self.t_luz.findData(t.luz)))
        self._bloqueado = False
        tipo = TIPOS_TOKEN.get(t.tipo, ("?",))[0]
        self.token_titulo.setText(t.nome)
        linhas = [f"Tipo: {tipo}", f"Tamanho: {t.tamanho}×{t.tamanho} quadrados"]
        if t.tipo == "jogador":
            linhas.append(f"Jogador: {t.dono or '— (ninguém ainda)'}")
        self.token_info.setText("\n".join(linhas))
        self.caixa_visao.setVisible(t.tem_visao)
        self._bloqueado = True
        self.v_preset.setCurrentIndex(0)
        self.v_alcance.setValue(t.visao_alcance)
        self.v_abertura.setValue(t.visao_abertura)
        self.v_direcao.setValue(round(t.direcao) % 360)
        self.v_girar.setChecked(t.pode_girar)
        self.v_escuro.setValue(t.visao_escuro)
        self._bloqueado = False

    def _visao_editada(self, *_):
        if self._bloqueado or not self.token:
            return
        self.token.definir_visao(self.v_alcance.value(), self.v_abertura.value(),
                                 self.v_direcao.value(), self.v_girar.isChecked(),
                                 self.v_escuro.value())

    def _preset_visao(self, indice):
        chave = self.v_preset.itemData(indice)
        if self._bloqueado or not self.token or not chave:
            return
        from ..mesa.linha_de_visao import PRESETS_VISAO
        _, alcance, abertura, escuro = PRESETS_VISAO[chave]
        self.token.definir_visao(alcance, abertura, escuro=escuro)
        self.mostrar_token()

    # ------------------------------------------------------------ mapa
    def _mapa_redimensionado(self):
        if not self.mapa:
            return
        self._bloqueado = True
        self.larg.setValue(self.mapa.largura_m)
        self.alt.setValue(self.mapa.altura_m)
        self._bloqueado = False

    def _tamanho_digitado(self, qual):
        if self._bloqueado or not self.mapa:
            return
        w, h = self.larg.value(), self.alt.value()
        if self.mapa.manter_proporcao:
            prop = self.mapa.w / max(1e-6, self.mapa.h)
            if qual == "w":
                h = w / prop
            else:
                w = h * prop
        self.mapa.definir_tamanho_metros(w, h)

    def _proporcao_mudou(self, marcado):
        if self.mapa and not self._bloqueado:
            self.mapa.manter_proporcao = marcado

    def _resetar_proporcao(self):
        if self.mapa:
            self.mapa.definir_tamanho_metros(
                self.mapa.largura_m, self.mapa.largura_m / self.mapa.proporcao_original())

    # ------------------------------------------------------------ porta
    def _mostrar_porta(self):
        p = self.porta
        self._bloqueado = True
        self.p_tipo.setCurrentIndex(self.p_tipo.findData(p.tipo))
        self.p_largura.setValue(p.largura_m)
        self.p_espessura.setValue(p.espessura_m)
        self.p_dupla.setChecked(p.dupla)
        self.p_lado.setCurrentIndex(self.p_lado.findData(p.lado))
        self.p_dobradica.setCurrentIndex(self.p_dobradica.findData(p.dobradica))
        self.p_dobradica.setEnabled(not p.dupla)
        self.p_angulo.setValue(round(p.rotation()))
        self.p_aberta.setChecked(p.aberta)
        self.p_jogadores.setChecked(p.jogadores_abrem)
        self.p_trancada.setChecked(p.trancada)
        self.p_nome.setText(p.nome_proprio)
        self.p_chave.setText(p.chave)
        self.p_gasta.setChecked(p.gasta_chave)
        from PyQt6.QtWidgets import QCompleter
        self.p_chave.setCompleter(QCompleter(nomes_de_itens(self.cena)))
        self._bloqueado = False

    def _porta_editada(self, *_):
        if self._bloqueado or not self.porta:
            return
        p = self.porta
        p.prepareGeometryChange()
        p.tipo = self.p_tipo.currentData()
        p.largura_m = self.p_largura.value()
        p.espessura_m = self.p_espessura.value()
        p.dupla = self.p_dupla.isChecked()
        p.lado = self.p_lado.currentData()
        p.dobradica = self.p_dobradica.currentData()
        p.aberta = self.p_aberta.isChecked()
        p.jogadores_abrem = self.p_jogadores.isChecked()
        p.trancada = self.p_trancada.isChecked()
        p.nome_proprio = self.p_nome.text().strip()
        p.chave = self.p_chave.text().strip()
        p.gasta_chave = self.p_gasta.isChecked()
        p.setRotation(self.p_angulo.value() % 360)
        self.p_dobradica.setEnabled(not p.dupla)
        p.mudou()

    # ------------------------------------------------------------ luz
    def _mostrar_luz(self):
        l = self.luz
        self._bloqueado = True
        self.l_tipo.setCurrentIndex(self.l_tipo.findData(l.tipo))
        self.l_forte.setValue(l.raio_forte)
        self.l_fraco.setValue(l.raio_fraco)
        self.l_tremula.setChecked(l.tremula)
        self.l_acesa.setChecked(l.acesa)
        self._pintar_cor_luz()
        self._bloqueado = False

    def _pintar_cor_luz(self):
        if self.luz:
            c = self.luz.cor
            self.l_cor.setText(c.name().upper())
            self.l_cor.setStyleSheet(f"background: {c.name()}; color: #111;")

    def _tipo_luz(self, *_):
        if self._bloqueado or not self.luz:
            return
        chave = self.l_tipo.currentData()
        _, forte, fraco, cor, tremula = TIPOS_LUZ[chave]
        from PyQt6.QtGui import QColor
        self.luz.tipo = chave
        self.luz.raio_forte, self.luz.raio_fraco = float(forte), float(fraco)
        self.luz.cor = QColor(cor)
        self.luz.tremula = tremula
        self.luz.mudou()
        self._mostrar_luz()

    def _luz_editada(self, *_):
        if self._bloqueado or not self.luz:
            return
        self.luz.raio_forte = self.l_forte.value()
        self.luz.raio_fraco = max(self.l_fraco.value(), self.luz.raio_forte)
        self.luz.tremula = self.l_tremula.isChecked()
        self.luz.acesa = self.l_acesa.isChecked()
        self.luz.mudou()

    def _cor_luz(self):
        if not self.luz:
            return
        from PyQt6.QtWidgets import QColorDialog
        cor = QColorDialog.getColor(self.luz.cor, self, "Cor da luz")
        if cor.isValid():
            self.luz.cor = cor
            self.luz.mudou()
            self._pintar_cor_luz()
