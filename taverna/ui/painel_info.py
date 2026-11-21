"""
Painel de informações dos personagens: PV, condições, raça, classe e anotações.

Mestre: edita tudo e decide, campo por campo, quem vê:
  🔒 só o mestre e o dono do token · 👁 todos os jogadores · 👤 só alguns jogadores.
Player: vê tudo do próprio personagem e o que o mestre revelou dos outros.
"""

import html

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (QComboBox, QDoubleSpinBox, QFormLayout, QListWidget, QGridLayout, QHBoxLayout, QLabel,
                             QMenu, QPlainTextEdit, QPushButton, QScrollArea, QSpinBox,
                             QStackedWidget, QTextBrowser, QToolButton, QVBoxLayout, QWidget)

from ..jogo.condicoes import CAMPOS, CONDICOES
from ..mesa.token import TokenItem


def _texto_vis(vis) -> tuple[str, str]:
    if vis == "todos":
        return "👁", "Todos os jogadores veem"
    if isinstance(vis, list) and vis:
        return "👤", "Só veem: " + ", ".join(vis)
    return "🔒", "Só você (mestre) e o dono do token"


from .tema import tema_atual as _tema_atual


class BotaoVisibilidade(QToolButton):
    """🔒 / 👁 / 👤 — com menu pra escolher quem vê."""

    def __init__(self, chave, painel):
        super().__init__()
        self.chave = chave
        self.painel = painel
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.setFixedWidth(38)
        # sem cor fixa: o tema pinta o botão (antes era marrom em todos os temas)
        self.setStyleSheet("QToolButton { padding: 3px; } QToolButton::menu-indicator { image: none; }")
        self.menu_vis = QMenu(self)
        self.menu_vis.aboutToShow.connect(self._montar_menu)
        self.setMenu(self.menu_vis)

    def mostrar(self, vis):
        icone, dica = _texto_vis(vis)
        from .acabamento import com_icone
        com_icone(self, icone)
        self.setToolTip(f"Quem vê este campo: {dica}\n(clique pra mudar)")

    def _montar_menu(self):
        self.menu_vis.clear()
        token = self.painel.token
        if token is None:
            return
        vis = token.info.get(self.chave, {}).get("vis", "oculto")

        def acao(texto, valor, marcado):
            a = QAction(texto, self.menu_vis)
            a.setCheckable(True)
            a.setChecked(marcado)
            a.triggered.connect(lambda: self.painel.mudar_vis(self.chave, valor))
            self.menu_vis.addAction(a)

        acao("🔒  Só eu e o dono", "oculto", vis == "oculto")
        acao("👁  Todos os jogadores", "todos", vis == "todos")
        self.menu_vis.addSeparator()
        titulo = self.menu_vis.addAction("👤  Só estes jogadores:")
        titulo.setEnabled(False)
        escolhidos = vis if isinstance(vis, list) else []
        for nome in self.painel.nomes_jogadores():
            def alternar(_=False, n=nome):
                atual = token.info.get(self.chave, {}).get("vis", "oculto")
                lista = list(atual) if isinstance(atual, list) else []
                if any(x.casefold() == n.casefold() for x in lista):
                    lista = [x for x in lista if x.casefold() != n.casefold()]
                else:
                    lista.append(n)
                self.painel.mudar_vis(self.chave, lista or "oculto")
            a = QAction(f"     {nome}", self.menu_vis)
            a.setCheckable(True)
            a.setChecked(any(x.casefold() == nome.casefold() for x in escolhidos))
            a.triggered.connect(alternar)
            self.menu_vis.addAction(a)
        if not self.painel.nomes_jogadores():
            sem = self.menu_vis.addAction("     (nenhum jogador conectado)")
            sem.setEnabled(False)
        from .acabamento import iconizar_menu
        iconizar_menu(self.menu_vis)


class PainelInfoMestre(QWidget):
    def __init__(self, cena, nomes_jogadores, parent=None):
        super().__init__(parent)
        self.cena = None
        self.token: TokenItem | None = None
        self.nomes_jogadores = nomes_jogadores   # função -> lista de nomes
        self.ao_mudar_desl = None                # avisa o combate (o limite muda na hora)
        self.ao_abrir_ficha = None               # função(token)
        self._carregando = False

        vazio = QLabel("Selecione um token para ver e editar\nas informações dele.\n\n"
                       "Cada campo tem um cadeado:\n🔒 só você e o dono · 👁 todos · 👤 alguns")
        vazio.setObjectName("dica")
        vazio.setWordWrap(True)
        vazio.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.titulo = QLabel()
        self.titulo.setStyleSheet("font-size: 12pt; font-weight: bold;")
        self.vis = {chave: BotaoVisibilidade(chave, self) for chave, _ in CAMPOS}

        # PV
        self.pv = QSpinBox()
        self.pv.setRange(-999, 9999)
        self.pv_max = QSpinBox()
        self.pv_max.setRange(0, 9999)
        for spin in (self.pv, self.pv_max):
            spin.setMinimumWidth(50)
        self.pv.valueChanged.connect(self._salvar_pv)
        self.pv_max.valueChanged.connect(self._salvar_pv)
        self.qtd = QSpinBox()
        self.qtd.setRange(1, 999)
        self.qtd.setMinimumWidth(44)
        self.qtd.setValue(5)
        dano = QPushButton("− dano")
        dano.setMinimumWidth(10)
        dano.setToolTip("Tira esse tanto de PV")
        dano.clicked.connect(lambda: self.pv.setValue(self.pv.value() - self.qtd.value()))
        cura = QPushButton("+ cura")
        cura.setMinimumWidth(10)
        cura.setToolTip("Devolve esse tanto de PV (até o máximo)")
        cura.clicked.connect(lambda: self.pv.setValue(min(self.pv_max.value() or 9999,
                                                          self.pv.value() + self.qtd.value())))
        linha_pv = QHBoxLayout()
        linha_pv.addWidget(self.pv)
        linha_pv.addWidget(QLabel("/"))
        linha_pv.addWidget(self.pv_max)
        linha_pv.addWidget(self.vis["pv"])
        linha_dano = QHBoxLayout()
        for b in (dano, cura):
            b.setStyleSheet("padding: 4px 2px;")
        linha_dano.addWidget(self.qtd, 2)
        linha_dano.addWidget(dano, 2)
        linha_dano.addWidget(cura, 2)

        # Condições
        self.botoes_cond = {}
        grade = QGridLayout()
        grade.setSpacing(3)
        for k, (chave, (nome, icone)) in enumerate(CONDICOES.items()):
            b = QPushButton(nome)
            b.setMinimumWidth(10)
            b.setCheckable(True)
            b.setStyleSheet("QPushButton { text-align: left; padding: 3px 6px; }")   # marcado: cor do tema
            from .acabamento import ICONES_GLOBAIS
            ICONES_GLOBAIS.ligar(b, b.setIcon, f"cond_{chave}")   # o mesmo desenho de cima do token
            b.toggled.connect(self._salvar_condicoes)
            b.setToolTip("Clique: liga/desliga · Clique direito: duração em rodadas")
            b.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            b.customContextMenuRequested.connect(lambda _p, k=chave: self._menu_duracao(k))
            self.botoes_cond[chave] = b
            grade.addWidget(b, k // 2, k % 2)
        cab_cond = QHBoxLayout()
        cab_cond.addWidget(QLabel("Quem vê:"))
        cab_cond.addStretch()
        cab_cond.addWidget(self.vis["condicoes"])

        # Raça / classe / notas
        from ..compendio.compendio import compendio
        try:
            c = compendio()
            racas = [e["nome"] for e in c.entradas["racas"]]
            classes = [e["nome"] for e in c.entradas["classes"]]
        except Exception:
            racas, classes = [], []
        self.raca = QComboBox()
        self.raca.setMinimumWidth(40)
        self.raca.setEditable(True)
        self.raca.addItems([""] + racas)
        self.raca.currentTextChanged.connect(lambda t: self._salvar_texto("raca", t))
        self.classe = QComboBox()
        self.classe.setMinimumWidth(40)
        self.classe.setEditable(True)
        self.classe.addItems([""] + classes)
        self.classe.currentTextChanged.connect(lambda t: self._salvar_texto("classe", t))
        self.notas = QPlainTextEdit()
        self.notas.setPlaceholderText("Anotações sobre o personagem…")
        self.notas.setMinimumHeight(80)
        self._timer_notas = QTimer(self)
        self._timer_notas.setSingleShot(True)
        self._timer_notas.setInterval(500)
        self._timer_notas.timeout.connect(
            lambda: self._salvar_texto("notas", self.notas.toPlainText()))
        self.notas.textChanged.connect(self._timer_notas.start)
        self.segredo = QPlainTextEdit()
        self.segredo.setPlaceholderText("Só você vê. Nunca vai pra rede, nem pro dono do personagem.")
        self.segredo.setMinimumHeight(70)
        self.segredo.setStyleSheet("QPlainTextEdit { border-color: #7a2a2a; }")
        self._timer_segredo = QTimer(self)
        self._timer_segredo.setSingleShot(True)
        self._timer_segredo.setInterval(500)
        self._timer_segredo.timeout.connect(
            lambda: self._salvar_texto("segredo", self.segredo.toPlainText()))
        self.segredo.textChanged.connect(self._timer_segredo.start)

        def com_vis(widget, chave):
            linha = QHBoxLayout()
            linha.addWidget(widget, 1)
            linha.addWidget(self.vis[chave])
            return linha

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.estado = QComboBox()
        self.estado.addItem("Normal", None)
        self.estado.addItem("✚ Caído (pode ser ajudado)", "caido")
        self.estado.addItem("💀 Morto", "morto")
        self.estado.setToolTip("Todo mundo vê o ícone no token.\nPV chegando a 0: criatura → 💀, jogador → ✚\n"
                               "Caído ou morto pode ser revistado pelos jogadores (inventário).")
        self.estado.currentIndexChanged.connect(self._salvar_estado)
        self.desl = QDoubleSpinBox()
        self.desl.setRange(0, 999)
        self.desl.setSingleStep(1.5)
        self.desl.setDecimals(1)
        self.desl.setSuffix(" m")
        self.desl.setMinimumWidth(40)
        self.desl.setToolTip("Quanto ele anda por turno. No combate o movimento fica limitado a isso\n"
                             "(dá pra mudar a qualquer hora: ferido, lento, magia…)")
        self.desl.valueChanged.connect(self._salvar_desl)
        form.addRow("Deslocam.", com_vis(self.desl, "desl"))
        form.addRow("Raça", com_vis(self.raca, "raca"))
        form.addRow("Classe", com_vis(self.classe, "classe"))

        cab_notas = QHBoxLayout()
        rot_notas = QLabel("Quem vê:")
        rot_notas.setToolTip("Quem vê depende do botão ao lado (🔒 você e o dono · 👁 todos · 👤 alguns)")
        cab_notas.addWidget(rot_notas)
        cab_notas.addStretch()
        cab_notas.addWidget(self.vis["notas"])

        b_ficha = QPushButton("📜 Abrir a ficha completa")
        b_ficha.setObjectName("primario")
        b_ficha.clicked.connect(lambda: self.token and self.ao_abrir_ficha and self.ao_abrir_ficha(self.token))
        # Arranjo (v0.29): o essencial (nome, ficha, PV, dano/cura, estado) sempre à vista;
        # o resto em seções que abrem/fecham (o Taverna lembra quais ficaram abertas).
        from .acabamento import Secao
        conteudo = QWidget()
        lc = QVBoxLayout(conteudo)
        lc.setSpacing(4)
        lc.addWidget(self.titulo)
        lc.addWidget(b_ficha)
        topo = QFormLayout()
        topo.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        topo.addRow("PV", linha_pv)
        topo.addRow("Dano/cura", linha_dano)
        topo.addRow("Estado", self.estado)
        lc.addLayout(topo)
        self.secoes = {}

        def secao(chave, titulo, aberta=True):
            s = Secao(f"info/{chave}", titulo, aberta)
            lc.addWidget(s)
            self.secoes[chave] = s
            return s.lay

        secao("condicoes", "⚠ Condições").addLayout(grade)
        self.secoes["condicoes"].lay.addLayout(cab_cond)
        secao("detalhes", "📋 Deslocamento, raça e classe").addLayout(form)
        lay_notas = secao("notas", "✏ Anotações")
        lay_notas.addWidget(self.notas)
        lay_notas.addLayout(cab_notas)
        lay_inv = secao("inventario", "🎒 Inventário")
        cab_inv = QHBoxLayout()
        cab_inv.addWidget(QLabel("Quem vê:"))
        cab_inv.addStretch()
        cab_inv.addWidget(self.vis["inventario"])
        self.inventario = QListWidget()
        self.inventario.setMaximumHeight(110)
        self.inventario.setToolTip("Itens que o personagem pegou (baús…). A ficha completa vem na etapa 8.")
        tirar = QPushButton("Tirar item")
        tirar.clicked.connect(self._tirar_item)
        por = QPushButton("＋ Item")
        por.setToolTip("Coloca um item no inventário (ex.: o que o goblin carrega — os jogadores\n"
                       "pegam quando ele estiver caído ou morto)")
        por.clicked.connect(self._por_item)
        linha_inv = QHBoxLayout()
        linha_inv.addWidget(por)
        linha_inv.addWidget(tirar)
        lay_inv.addWidget(self.inventario)
        lay_inv.addLayout(linha_inv)
        lay_inv.addLayout(cab_inv)
        secao("segredo", "🔒 Notas secretas do mestre", aberta=False).addWidget(self.segredo)
        lc.addStretch()
        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        rolagem.setWidget(conteudo)

        self.pilha = QStackedWidget()
        self.pilha.addWidget(vazio)
        self.pilha.addWidget(rolagem)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.pilha)
        self.definir_cena(cena)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    # ------------------------------------------------------------ cena / seleção
    def definir_cena(self, cena):
        if self.cena is not None:
            try:
                self.cena.selectionChanged.disconnect(self.atualizar)
            except (TypeError, RuntimeError):
                pass
        self.cena = cena
        cena.selectionChanged.connect(self.atualizar)
        self.atualizar()

    def atualizar(self):
        try:
            tokens = [i for i in self.cena.selectedItems() if isinstance(i, TokenItem)]
        except RuntimeError:
            return
        self.token = tokens[0] if len(tokens) == 1 else None
        if self.token is None:
            self.pilha.setCurrentIndex(0)
            return
        self.pilha.setCurrentIndex(1)
        self._carregando = True
        t = self.token
        dono = f"  · de {html.escape(t.dono)}" if t.dono else ""
        self.titulo.setText(f"{html.escape(t.nome)}<span style='font-size:9pt; color:{_tema_atual()['fraco']}'>"
                            f"{dono}</span>")
        pv = t.info.get("pv", {}).get("v") or [0, 0]
        self.pv_max.setValue(int(pv[1]))
        self.pv.setValue(int(pv[0]))
        self.desl.setValue(t.deslocamento)
        self.estado.setCurrentIndex(max(0, self.estado.findData(t.estado)))
        cond = t.info.get("condicoes", {}).get("v") or []
        dur = t.info.get("condicoes", {}).get("dur") or {}
        for chave, b in self.botoes_cond.items():
            b.setChecked(chave in cond)
            nome, _emoji = CONDICOES[chave]
            b.setText(nome + (f" ({dur[chave]})" if chave in dur and chave in cond else ""))
        self.raca.setCurrentText(t.info.get("raca", {}).get("v") or "")
        self.classe.setCurrentText(t.info.get("classe", {}).get("v") or "")
        notas = t.info.get("notas", {}).get("v") or ""
        if self.notas.toPlainText() != notas:
            self.notas.setPlainText(notas)
        self.inventario.clear()
        for it in t.info.get("inventario", {}).get("v") or []:
            qtd = it.get("qtd", 1)
            self.inventario.addItem(f"{it.get('nome', '?')}{f'  ×{qtd}' if qtd and qtd != 1 else ''}"
                                    + (f"   (de {it['origem']})" if it.get("origem") else ""))
        segredo = t.info.get("segredo", {}).get("v") or ""
        if self.segredo.toPlainText() != segredo:
            self.segredo.setPlainText(segredo)
        # resumo no título das seções (aparece mesmo com a seção fechada)
        n_cond = len([c for c in cond if c in CONDICOES])
        self.secoes["condicoes"].definir_resumo(f"{n_cond} ativa{'s' if n_cond != 1 else ''}" if n_cond else "")
        n_inv = self.inventario.count()
        self.secoes["inventario"].definir_resumo(f"{n_inv} ite{'ns' if n_inv != 1 else 'm'}" if n_inv else "")
        self.secoes["detalhes"].definir_resumo(f"{t.deslocamento:g} m".replace(".", ","))
        self.secoes["segredo"].definir_resumo("tem nota" if segredo.strip() else "")
        for chave, botao in self.vis.items():
            botao.mostrar(t.info.get(chave, {}).get("vis", "oculto"))
        self._carregando = False

    # ------------------------------------------------------------ salvar no token
    def _salvar_pv(self):
        if self._carregando or self.token is None:
            return
        maximo = self.pv_max.value()
        self.token.definir_info("pv", [self.pv.value(), maximo] if maximo > 0 else None)
        # PV chegou a 0: criatura morre, jogador cai (✚). Curou: o caído levanta.
        t = self.token
        if maximo > 0 and self.pv.value() <= 0 and t.estado is None:
            t.definir_estado("caido" if t.tipo == "jogador" else "morto")
        elif self.pv.value() > 0 and t.estado == "caido":
            t.definir_estado(None)
        self._carregando = True
        self.estado.setCurrentIndex(max(0, self.estado.findData(t.estado)))
        self._carregando = False

    def _por_item(self):
        if self.token is None:
            return
        from .dialogo_prop import DialogoItem
        d = DialogoItem(self)
        if d.exec():
            lista = list(self.token.info.get("inventario", {}).get("v") or [])
            lista.append(d.resultado())
            self.token.definir_info("inventario", lista)
            self.atualizar()

    def _salvar_estado(self):
        if self._carregando or self.token is None:
            return
        self.token.definir_estado(self.estado.currentData())
        if self.ao_mudar_desl:
            self.ao_mudar_desl()   # atualiza o combate (morto é pulado)

    def _tirar_item(self):
        k = self.inventario.currentRow()
        if self.token is None or k < 0:
            return
        lista = list(self.token.info.get("inventario", {}).get("v") or [])
        if k < len(lista):
            del lista[k]
            self.token.definir_info("inventario", lista)
            self.atualizar()

    def _salvar_desl(self):
        if self._carregando or self.token is None:
            return
        self.token.definir_info("desl", float(self.desl.value()))
        if self.ao_mudar_desl:
            self.ao_mudar_desl()

    def _salvar_condicoes(self):
        if self._carregando or self.token is None:
            return
        lista = [k for k, b in self.botoes_cond.items() if b.isChecked()]
        campo = self.token.info.setdefault("condicoes", {"v": [], "vis": "oculto"})
        campo["dur"] = {k: n for k, n in (campo.get("dur") or {}).items() if k in lista}
        self.token.definir_info("condicoes", lista)
        self.atualizar()

    def _menu_duracao(self, chave):
        if self.token is None:
            return
        menu = QMenu(self)
        titulo = menu.addAction(f"Duração de {CONDICOES[chave][0]}:")
        titulo.setEnabled(False)
        escolha = {}
        for n, texto in ((0, "Sem duração (até eu tirar)"), (1, "1 rodada"), (2, "2 rodadas"),
                         (3, "3 rodadas"), (5, "5 rodadas"), (10, "10 rodadas (1 minuto)")):
            escolha[menu.addAction(texto)] = n
        menu.addSeparator()
        outro = menu.addAction("Outro valor…")
        from .acabamento import iconizar_menu
        acao = iconizar_menu(menu).exec(self.cursor().pos())
        if acao is None:
            return
        if acao is outro:
            from PyQt6.QtWidgets import QInputDialog
            n, ok = QInputDialog.getInt(self, "Duração", "Quantas rodadas?", 1, 1, 999)
            if not ok:
                return
        else:
            n = escolha.get(acao)
            if n is None:
                return
        campo = self.token.info.setdefault("condicoes", {"v": [], "vis": "oculto"})
        lista = list(campo.get("v") or [])
        dur = dict(campo.get("dur") or {})
        if n > 0:
            dur[chave] = n
            if chave not in lista:
                lista.append(chave)
        else:
            dur.pop(chave, None)
        campo["dur"] = dur
        self.token.definir_info("condicoes", lista)
        self.atualizar()

    def _salvar_texto(self, chave, texto):
        if self._carregando or self.token is None:
            return
        self.token.definir_info(chave, texto, vis="mestre" if chave == "segredo" else None)

    def mudar_vis(self, chave, vis):
        if self.token is None:
            return
        self.token.definir_info(chave, vis=vis)
        self.vis[chave].mostrar(vis)


class PainelInfoPlayer(QWidget):
    """O que eu sei dos personagens: tudo do meu, e o que o mestre revelou dos outros."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.texto = QTextBrowser()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.texto)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def atualizar(self, tokens, meu_nome):
        from ..rede.protocolo import mesmo_nome
        meus = [t for t in tokens if mesmo_nome(t.dono, meu_nome)]
        outros = [t for t in tokens if t not in meus and self._tem_algo(t)]
        partes = []
        for t in meus + outros:
            partes.append(self._cartao(t, t in meus))
        if not partes:
            partes.append(f"<p style='color:{_tema_atual()['fraco']}'>Nada por aqui ainda.<br>"
                          "Quando o mestre preencher ou revelar informações, elas aparecem aqui.</p>")
        rolagem = self.texto.verticalScrollBar().value()
        self.texto.setHtml("".join(partes))
        self.texto.verticalScrollBar().setValue(rolagem)

    @staticmethod
    def _tem_algo(t):
        return any(campo.get("v") for campo in t.info.values()
                   if campo.get("vis") != "-")

    @staticmethod
    def _cartao(t, meu):
        seu = f" <span style='font-size:9pt; color:{_tema_atual()['fraco']}'>(seu)</span>" if meu else ""
        linhas = [f"<h3 style='margin:8px 0 2px 0; color:{_tema_atual()['destaque']}'>{html.escape(t.nome)}{seu}</h3>"]
        pv = t.info.get("pv", {})
        if pv.get("v"):
            atual, maximo = pv["v"]
            linhas.append(f"<b>PV</b> {atual} / {maximo}")
        cond = t.info.get("condicoes", {}).get("v") or []
        if cond:
            dur = t.info.get("condicoes", {}).get("dur") or {}
            linhas.append("<b>Condições</b> " + ", ".join(
                f"{CONDICOES[k][0]}"
                + (f" ({dur[k]} rod.)" if k in dur else "") for k in cond if k in CONDICOES))
        desl = t.info.get("desl", {})
        if desl.get("v") and desl.get("vis") != "-":
            linhas.append(f"<b>Deslocamento</b> {str(desl['v']).replace('.', ',')} m")
        for chave, rotulo in (("raca", "Raça"), ("classe", "Classe")):
            v = t.info.get(chave, {}).get("v")
            if v:
                linhas.append(f"<b>{rotulo}</b> {html.escape(v)}")
        inv = t.info.get("inventario", {}).get("v") or []
        if inv:
            linhas.append("<b>Inventário</b> " + ", ".join(
                html.escape(i.get("nome", "?")) + (f" ×{i['qtd']}" if i.get("qtd", 1) != 1 else "")
                for i in inv))
        notas = t.info.get("notas", {}).get("v")
        if notas:
            linhas.append("<b>Anotações</b><br>" + html.escape(notas).replace("\n", "<br>"))
        return "<p style='margin:0 0 4px 0'>" + "<br>".join(linhas) + "</p><hr>"
