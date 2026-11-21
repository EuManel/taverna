"""
Coisas que flutuam por cima da mesa, sem ocupar espaço fixo na tela:

- FaixaTurnos: só aparece no combate. Mostra a rodada e a ordem de iniciativa,
  com quem é a vez destacado. O mestre passa a vez por ela mesmo (◀ ▶).
- AvisoRolagem: quando o painel de dados está fechado, cada rolagem aparece
  num cartãozinho no canto e some sozinha.
"""

import html

from PyQt6.QtCore import QEvent, QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from .painel_dados import cor_do_nome
from .retratos import CartaoRetrato
from .tema import tema_atual

ESTILO = ""   # (o visual das sobreposições agora vem do tema — ui/tema.py)


class _Acompanhar(QObject):
    """Reposiciona o widget flutuante quando a mesa muda de tamanho."""

    def __init__(self, alvo, funcao):
        super().__init__(alvo)
        self.funcao = funcao
        alvo.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Resize:
            self.funcao()
        return False


MAX_RETRATOS = 12


class FaixaTurnos(QFrame):
    proximo = pyqtSignal()
    anterior = pyqtSignal()
    abrir_painel = pyqtSignal()
    centralizar = pyqtSignal(str)   # clicou num retrato

    def __init__(self, mesa, mestre: bool):
        super().__init__(mesa)
        self.mesa = mesa
        self.mestre = mestre
        self.setObjectName("sobreposicao")
        self.setStyleSheet(ESTILO)
        self.lay = QHBoxLayout(self)
        self.lay.setContentsMargins(10, 6, 10, 6)
        self.lay.setSpacing(6)
        self.rodada = QLabel()
        self.rodada.setStyleSheet("font-weight: bold; color: palette(highlight);")
        self.chips = QLabel()
        self.chips.setTextFormat(Qt.TextFormat.RichText)
        self.resolver = None   # função(id) -> (cartão, imagens) ou None; quem cria a faixa define
        self.cartoes = []
        self.fila = QWidget()
        self.fila.setStyleSheet("background: transparent;")
        self.lay_fila = QHBoxLayout(self.fila)
        self.lay_fila.setContentsMargins(0, 0, 0, 0)
        self.lay_fila.setSpacing(4)
        self.mais = QLabel()
        self.mais.setObjectName("dica")
        self.lay.addWidget(self.rodada)
        self.lay.addWidget(self.chips)
        self.lay.addWidget(self.fila)
        self.lay.addWidget(self.mais)
        self.btn_ant = QPushButton("◀")
        self.btn_ant.setToolTip("Voltar a vez")
        self.btn_ant.clicked.connect(self.anterior)
        self.btn_prox = QPushButton("Próximo ▶")
        self.btn_prox.setObjectName("primario")
        self.btn_prox.setToolTip("Passar a vez (N)")
        self.btn_prox.clicked.connect(self.proximo)
        self.btn_rolar = QPushButton("🎲 Rolar iniciativa")
        self.btn_rolar.setObjectName("primario")
        self.btn_rolar.clicked.connect(self.abrir_painel)
        self.btn_painel = QPushButton("⚙")
        self.btn_painel.setToolTip("Abrir o painel de combate")
        self.btn_painel.clicked.connect(self.abrir_painel)
        for b in (self.btn_ant, self.btn_prox):
            b.setVisible(mestre)
            self.lay.addWidget(b)
        self.lay.addWidget(self.btn_rolar)
        self.lay.addWidget(self.btn_painel)
        self.btn_rolar.hide()
        self._acompanhar = _Acompanhar(mesa, self.posicionar)
        self.hide()
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def changeEvent(self, ev):
        # o tema mudou: redesenha os nomes com as cores novas
        if ev.type() == QEvent.Type.StyleChange and getattr(self, "_ultimo", None):
            QTimer.singleShot(0, lambda: self.atualizar(*self._ultimo))
        super().changeEvent(ev)

    def atualizar(self, combate: dict, meus_ids=(), falta_rolar=False):
        self._ultimo = (combate, meus_ids, falta_rolar)
        if not combate or not combate.get("ativo"):
            self.hide()
            return
        vez = combate.get("vez")
        ordem = combate.get("ordem", [])
        self.rodada.setText("Iniciativa" if vez is None else f"Rodada {combate.get('rodada')}")
        # retratos pequenos na ordem do combate (estilo Baldur's Gate)
        visiveis = ordem[:MAX_RETRATOS]
        while len(self.cartoes) < len(visiveis):
            c = CartaoRetrato(pequeno=True, parent=self.fila)
            c.clicado.connect(self.centralizar)
            self.lay_fila.addWidget(c)
            self.cartoes.append(c)
        while len(self.cartoes) > len(visiveis):
            c = self.cartoes.pop()
            self.lay_fila.removeWidget(c)
            c.deleteLater()
        for c, p in zip(self.cartoes, visiveis):
            achado = self.resolver(p["id"]) if (self.resolver and p.get("nome") != "???") else None
            if achado:
                dados, imagens = achado
                dados = dict(dados, nome=p["nome"])
            else:   # criatura que você não está vendo
                dados, imagens = {"id": None, "nome": "???"}, {}
            from .painel_combate import INI_ROLANDO   # (v0.65.1) dado ainda rolando: "…"
            ini = "—" if p.get("ini") is None else ("…" if p["id"] in INI_ROLANDO else p["ini"])
            c.definir(dados, imagens, vez=p["id"] == vez, ini=ini, meu=p["id"] in meus_ids)
        sobra = len(ordem) - len(visiveis)
        self.mais.setText(f"+{sobra}" if sobra > 0 else "")
        self.mais.setVisible(sobra > 0)
        self.chips.setVisible(not ordem)
        self.chips.setText("<i>ninguém no combate</i>")
        if self.mestre:
            self.btn_prox.setText("Começar ▶" if vez is None else "Próximo ▶")
        self.btn_rolar.setVisible(falta_rolar)
        self.show()
        self.raise_()
        self.adjustSize()
        self.posicionar()

    def posicionar(self):
        largura = min(self.sizeHint().width(), self.mesa.width() - 20)
        self.resize(largura, self.sizeHint().height())
        self.move(max(10, (self.mesa.width() - largura) // 2), 10)


class AvisoRolagem(QFrame):
    def __init__(self, mesa):
        super().__init__(mesa)
        self.mesa = mesa
        self.setObjectName("sobreposicao")
        self.setStyleSheet(ESTILO)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        self.texto = QLabel()
        self.texto.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(self.texto)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self._linhas = []
        self._acompanhar = _Acompanhar(mesa, self.posicionar)
        self.hide()
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def mostrar(self, r: dict):
        quem = r.get("quem", "?")
        motivo = r.get("motivo", "")
        especial = " ✨" if r.get("d20") == 20 else (" 💀" if r.get("d20") == 1 else "")
        privada = " 🔒" if r.get("privada") else ""
        linha = (f"<b style='color:{cor_do_nome(quem)}'>{html.escape(quem)}</b>{privada}"
                 f"{(' · ' + html.escape(motivo)) if motivo else ''}: "
                 f"<b style='font-size:13pt'>{r.get('total')}</b>{especial} "
                 f"<span style='color:{tema_atual()['fraco']}'>"
                 f"({html.escape(r.get('expr', ''))})</span>")
        self._linhas = (self._linhas + [linha])[-3:]
        self.texto.setText("<br>".join(self._linhas))
        self.show()
        self.raise_()
        self.adjustSize()
        self.posicionar()
        self._timer.start(6000)

    def mostrar_texto(self, html_texto: str, segundos: int = 8):
        self._linhas = (self._linhas + [html_texto])[-3:]
        self.texto.setText("<br>".join(self._linhas))
        self.show()
        self.raise_()
        self.adjustSize()
        self.posicionar()
        self._timer.start(segundos * 1000)

    def hideEvent(self, event):
        self._linhas = []
        super().hideEvent(event)

    def posicionar(self):
        self.adjustSize()
        self.move(self.mesa.width() - self.width() - 16, self.mesa.height() - self.height() - 16)


class MiniPlayer(QFrame):
    """Player da música no canto da mesa (jogador). Pequeno, mas visível — o YouTube não deixa
    esconder o player oficial. Dá pra trocar de canto e de tamanho."""

    TAMANHOS = ((356, 200), (480, 270))   # 200 px de altura = o mínimo que o YouTube aceita
    CANTOS = ("inf_dir", "inf_esq", "sup_dir", "sup_esq")

    def __init__(self, mesa, player):
        super().__init__(mesa)
        from PyQt6.QtWidgets import QVBoxLayout
        self.mesa = mesa
        self.player = player
        self.tamanho = 0
        self.canto = 0
        self.setObjectName("sobreposicao")
        self.setStyleSheet(ESTILO)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 6)
        lay.setSpacing(4)
        topo = QHBoxLayout()
        topo.setSpacing(4)
        self.titulo = QLabel("🎵")
        self.titulo.setStyleSheet("font-size: 11px;")
        topo.addWidget(self.titulo, 1)
        for texto, dica, funcao in (("⇲", "Trocar de canto", self._trocar_canto),
                                    ("⤢", "Maior / menor", self._trocar_tamanho)):
            b = QPushButton(texto)
            b.setToolTip(dica)
            b.setFixedWidth(28)
            b.clicked.connect(funcao)
            topo.addWidget(b)
        lay.addLayout(topo)
        lay.addWidget(player, 1)
        _Acompanhar(mesa, self.posicionar)
        self.hide()
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def definir_titulo(self, texto):
        self.titulo.setText(self.fontMetrics().elidedText(texto, Qt.TextElideMode.ElideRight, 260))
        self.titulo.setToolTip(texto)

    def _trocar_canto(self):
        self.canto = (self.canto + 1) % len(self.CANTOS)
        self.posicionar()

    def _trocar_tamanho(self):
        self.tamanho = (self.tamanho + 1) % len(self.TAMANHOS)
        self.posicionar()

    def posicionar(self):
        w, h = self.TAMANHOS[self.tamanho]
        w, h = w + 12, h + 40
        self.resize(w, h)
        m = 12
        canto = self.CANTOS[self.canto]
        x = self.mesa.width() - w - m if canto.endswith("dir") else m
        y = self.mesa.height() - h - m if canto.startswith("inf") else m + 44
        self.move(max(0, x), max(0, y))
        self.raise_()
