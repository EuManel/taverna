"""
💡 Dicas de primeiro acesso (v0.66 — item 11 dos PEDIDOS_v0.58, só a parte das dicas: o Manel decidiu NÃO ter
aventura de exemplo).

Na primeira vez que a mesa aparece (mestre e jogador, cada um com as suas), a janela escurece, a coisa explicada
fica DESTACADA (um "buraco" com borda dourada) e um balão do lado explica, com Anterior / Próxima / Pular.
Uma vez só (guardado nas preferências); dá pra rever pelo menu Ajuda → "Dicas de primeiro acesso".
Esc pula, Enter/→ avança, ← volta. Nos testes sem tela (offscreen) não abre sozinho.
"""

import os

from PyQt6.QtCore import QPoint, QRect, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

CHAVE = "dicas_vistas_v1"


# ====================================================================== o que cada um vê
def passos_mestre(j) -> list:
    """(título, texto, alvo) — alvo: função que devolve o widget a destacar (ou None = nada destacado)."""
    def acao(nome):
        return lambda: (j.barra.widgetForAction(getattr(j, nome)) if getattr(j, nome, None) is not None else None)
    return [
        ("Bem-vindo ao Taverna, mestre!",
         "Umas dicas rápidas pra começar. Dá pra pular (Esc) e rever depois no menu <b>Ajuda</b>.", None),
        ("A barra de ferramentas",
         "Daqui saem quase todas as coisas: <b>Mapa</b> (importar imagem), <b>Token</b>, <b>Objetos</b>, "
         "<b>Biblioteca</b>, <b>Combate</b>, <b>Dados</b>…", lambda: j.barra),
        ("Botão direito na mesa",
         "Em qualquer lugar da mesa, o <b>botão direito</b> abre o menu do que dá pra fazer ali: colocar porta, "
         "trocar material da parede, criar área, adicionar criatura, mexer num token…", lambda: j.visao),
        ("Andar pela mesa",
         "<b>Rodinha</b> = zoom. <b>Botão do meio</b> (ou segurar <b>Espaço</b>) arrasta a mesa. "
         "<b>M</b> (segure e arraste) = régua. <b>P</b> = marcar um ponto pra todos. "
         "<b>Shift+P</b> = levar a câmera de todos os jogadores até ali.", lambda: j.visao),
        ("Construir",
         "A barra de construção (Chão, Parede, Sala, Porta…) monta o cenário. A porta fica presa onde você pôs; "
         "pra tirar, botão direito → <b>Excluir porta</b> (a parede fecha sozinha).",
         lambda: getattr(j, "barra_construcao", None)),
        ("Os jogadores entram por aqui",
         "<b>Abrir taverna</b> (menu Sessão). Se o roteador deixar, aparece um <b>código da sala</b> lá embaixo pra "
         "mandar pros amigos; se não, eles entram pelo IP do Radmin.", acao("a_taverna")),
        ("Cidade e mundo",
         "No menu <b>Mesa → Cidade e mundo</b> você importa o mapa da cidade e do mundo. Depois, dando "
         "<b>zoom out</b>, a mesa vira um pedacinho da cidade, e a cidade um ponto no mundo.", lambda: j.visao),
        ("Pronto!",
         "<b>F1</b> mostra todos os atalhos. Estas dicas voltam no menu <b>Ajuda → Dicas de primeiro acesso</b>. "
         "Boa sessão!", None),
    ]


def passos_jogador(j) -> list:
    def acao(nome):
        return lambda: (j.barra.widgetForAction(getattr(j, nome)) if getattr(j, nome, None) is not None else None)
    return [
        ("Bem-vindo à mesa!",
         "Umas dicas rápidas pra começar. Dá pra pular (Esc) e rever depois no botão <b>Ajuda</b>.", None),
        ("O seu token",
         "Ainda não tem token? Crie aqui (<b>um só</b>, o seu). Já tem? O mesmo botão edita nome, cor e imagem — "
         "ou dê <b>duplo clique</b> no seu token.", acao("a_meu_token")),
        ("Andar",
         "<b>Arraste</b> o seu token pra andar. <b>Q / E</b> giram pra onde ele olha, <b>F</b> olha pro mouse. "
         "<b>C</b> centraliza a câmera nele.", lambda: j.visao),
        ("Botão direito no seu token",
         "Abre o acesso rápido: <b>Ficha</b>, <b>Inventário</b>, <b>Usar magia</b>, <b>Rolar d20</b>. "
         "Em baú, porta e escada, o duplo clique abre / mexe / sobe.", lambda: j.visao),
        ("Medir e marcar",
         "Segure <b>M</b> e arraste = régua. <b>P</b> marca um ponto no mapa pra todo mundo ver.", lambda: j.visao),
        ("Combate",
         "Quando o mestre começa o combate, aparece o pedido de <b>iniciativa</b>. Na sua vez, o botão "
         "<b>Encerrar meu turno</b> passa a vez.", None),
        ("Cidade e mundo",
         "Dando <b>zoom out</b> na mesa você vê a cidade e o mundo (só o que o grupo já descobriu).",
         lambda: j.visao),
        ("Pronto!",
         "<b>F1</b> mostra todos os atalhos. Estas dicas voltam no botão <b>Ajuda</b>. Boa aventura!",
         lambda: getattr(j, "btn_ajuda", None)),
    ]


# ====================================================================== o tour
class Tour(QWidget):
    MARGEM = 8

    def __init__(self, janela, passos: list, ao_fim=None):
        super().__init__(janela)
        self.janela = janela
        self.passos = passos
        self.i = 0
        self.ao_fim = ao_fim
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.balao = QFrame(self)
        self.balao.setObjectName("balaoDica")
        self.balao.setStyleSheet("#balaoDica { background: palette(window); border: 2px solid palette(highlight);"
                                 " border-radius: 8px; }")
        lay = QVBoxLayout(self.balao)
        lay.setContentsMargins(16, 12, 16, 12)
        self.titulo = QLabel()
        self.titulo.setObjectName("titulo")
        self.texto = QLabel()
        self.texto.setWordWrap(True)
        self.texto.setTextFormat(Qt.TextFormat.RichText)
        self.contador = QLabel()
        self.contador.setStyleSheet("color: palette(mid);")
        botoes = QHBoxLayout()
        self.b_pular = QPushButton("Pular")
        self.b_voltar = QPushButton("Anterior")
        self.b_ir = QPushButton("Próxima")
        self.b_ir.setObjectName("primario")
        self.b_pular.clicked.connect(self.terminar)
        self.b_voltar.clicked.connect(lambda: self.ir(self.i - 1))
        self.b_ir.clicked.connect(lambda: self.ir(self.i + 1))
        botoes.addWidget(self.contador)
        botoes.addStretch(1)
        for b in (self.b_pular, self.b_voltar, self.b_ir):
            botoes.addWidget(b)
        lay.addWidget(self.titulo)
        lay.addWidget(self.texto)
        lay.addLayout(botoes)
        self.balao.setFixedWidth(400)
        janela.installEventFilter(self)
        self.setGeometry(janela.rect())
        self.ir(0)
        self.show()
        self.raise_()
        self.setFocus()

    def eventFilter(self, obj, ev):
        if obj is self.janela and ev.type() == ev.Type.Resize:
            self.setGeometry(self.janela.rect())
            QTimer.singleShot(0, self._posicionar)
        return False

    # ---------------------------------------------------------------- passos
    def alvo(self) -> QRect | None:
        f = self.passos[self.i][2]
        try:
            w = f() if f else None
        except (AttributeError, RuntimeError):
            w = None
        if w is None or not w.isVisible():
            return None
        canto = w.mapTo(self.janela, QPoint(0, 0))
        return QRect(canto, w.size()).adjusted(-self.MARGEM, -self.MARGEM, self.MARGEM, self.MARGEM)

    def ir(self, i: int):
        if i >= len(self.passos):
            self.terminar()
            return
        self.i = max(0, i)
        titulo, texto, _alvo = self.passos[self.i]
        self.titulo.setText(titulo)
        self.texto.setText(texto)
        self.contador.setText(f"{self.i + 1} de {len(self.passos)}")
        self.b_voltar.setEnabled(self.i > 0)
        ultimo = self.i == len(self.passos) - 1
        self.b_ir.setText("Entendi!" if ultimo else "Próxima")
        self.b_pular.setVisible(not ultimo)
        self._posicionar()
        self.update()

    def _posicionar(self):
        self.balao.adjustSize()
        r = self.alvo()
        W, H = self.width(), self.height()
        bw, bh = self.balao.width(), self.balao.height()
        if r is None or (r.width() > W * 0.6 and r.height() > H * 0.5):
            # nada a destacar (ou é a mesa inteira): o balão no meio
            x, y = (W - bw) // 2, (H - bh) // 2 if r is None else int(H * 0.62 - bh / 2)
        elif r.bottom() + bh + 14 < H:
            x, y = r.center().x() - bw // 2, r.bottom() + 14          # embaixo do alvo
        elif r.top() - bh - 14 > 0:
            x, y = r.center().x() - bw // 2, r.top() - bh - 14       # em cima
        elif r.right() + bw + 14 < W:
            x, y = r.right() + 14, r.center().y() - bh // 2          # do lado
        else:
            x, y = r.left() - bw - 14, r.center().y() - bh // 2
        self.balao.move(max(10, min(W - bw - 10, x)), max(10, min(H - bh - 10, y)))

    def terminar(self):
        self.janela.removeEventFilter(self)
        self.hide()
        self.deleteLater()
        if self.ao_fim:
            self.ao_fim()

    # ---------------------------------------------------------------- desenho e teclas
    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        fundo = QPainterPath()
        fundo.addRect(QRectF(self.rect()))
        r = self.alvo()
        if r is not None:
            buraco = QPainterPath()
            buraco.addRoundedRect(QRectF(r), 10, 10)
            fundo = fundo.subtracted(buraco)
        p.fillPath(fundo, QColor(0, 0, 0, 160))
        if r is not None:
            p.setPen(QPen(QColor("#e8c25a"), 2.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(r), 10, 10)
        p.end()

    def mousePressEvent(self, ev):
        ev.accept()   # (a mesa embaixo não recebe clique enquanto as dicas estão abertas)

    def event(self, ev):
        # as teclas do tour vêm antes dos atalhos da janela (o Esc do mestre sai da ferramenta, por exemplo)
        if ev.type() == ev.Type.ShortcutOverride and ev.key() in (
                Qt.Key.Key_Escape, Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Right, Qt.Key.Key_Left,
                Qt.Key.Key_Space):
            ev.accept()
            return True
        return super().event(ev)

    def keyPressEvent(self, ev):
        k = ev.key()
        if k == Qt.Key.Key_Escape:
            self.terminar()
        elif k in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Right, Qt.Key.Key_Space):
            self.ir(self.i + 1)
        elif k == Qt.Key.Key_Left:
            self.ir(self.i - 1)
        else:
            super().keyPressEvent(ev)


# ====================================================================== quando mostrar
def ja_viu(config) -> bool:
    return str(config.value(CHAVE, "")) in ("1", "true", "True")


def mostrar(janela, papel: str, forcar: bool = False):
    """Abre as dicas (papel: "mestre" | "jogador"). Sem forcar: só se ainda não viu (e nunca nos testes)."""
    config = janela.config
    if not forcar:
        if ja_viu(config) or os.environ.get("QT_QPA_PLATFORM") in ("offscreen", "minimal") \
                or os.environ.get("TAVERNA_SEM_DICAS"):
            return None
    atual = getattr(janela, "_tour_dicas", None)
    if atual is not None:
        try:
            atual.terminar()
        except RuntimeError:
            pass
    passos = passos_mestre(janela) if papel == "mestre" else passos_jogador(janela)

    def fim():
        config.setValue(CHAVE, "1")
        janela._tour_dicas = None
    janela._tour_dicas = Tour(janela, passos, fim)
    return janela._tour_dicas


def agendar_primeira_vez(janela, papel: str, ms: int = 900):
    """Chamado quando a mesa aparece: abre as dicas daqui a pouco, se for a primeira vez."""
    if ja_viu(janela.config) or getattr(janela, "_tour_agendado", False):
        return
    janela._tour_agendado = True
    QTimer.singleShot(ms, lambda: mostrar(janela, papel))
