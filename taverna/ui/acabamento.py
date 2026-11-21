"""
Acabamento da interface: ícones que acompanham o tema e cabeçalho enfeitado dos painéis.
"""

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QDockWidget, QHBoxLayout, QMenu, QSizePolicy, QToolButton, QWidget

from .icones import icone_tema, pixmap_icone
from .tema import tema_atual


class Icones:
    """Guarda quem usa qual ícone, pra redesenhar tudo na cor certa quando o tema muda."""

    def __init__(self):
        self.itens = []

    def ligar(self, definir, nome: str):
        self.itens.append((definir, nome))
        definir(icone_tema(nome))

    def atualizar(self):
        for definir, nome in self.itens:
            try:
                definir(icone_tema(nome))
            except RuntimeError:   # o widget já foi destruído
                pass


class TituloPainel(QWidget):
    """Cabeçalho de painel: ícone + nome na fonte do tema + filete com losango + botão de fechar."""

    def __init__(self, dock: QDockWidget, icone: str):
        super().__init__(dock)
        self.dock = dock
        self.icone = icone
        self.setFixedHeight(31)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 4, 0)
        lay.addStretch(1)
        self.fechar = QToolButton(self)
        self.fechar.setFixedSize(22, 22)
        self.fechar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fechar.setToolTip("Fechar o painel (reabre pelo botão da barra)")
        self.fechar.setStyleSheet("QToolButton { border: none; background: transparent; border-radius: 4px; }"
                                  "QToolButton:hover { background: rgba(128, 128, 128, 60); }")
        self.fechar.clicked.connect(dock.close)
        self.fechar.setVisible(bool(dock.features() & QDockWidget.DockWidgetFeature.DockWidgetClosable))
        lay.addWidget(self.fechar)
        dock.windowTitleChanged.connect(lambda _t: self.update())

    def minimumSizeHint(self):
        return QSize(60, 31)

    def paintEvent(self, ev):
        t = tema_atual()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        claro = t["claro"]
        destaque = QColor(t["destaque"])
        placa = None
        try:   # (v0.77) HUD de metal: a PLACA inteira do título (moldura, medalhão, divisória) — Médio/Alto
            from . import hud
            ativo = hud.ativo()
            if ativo is not None:
                tema_k, t_h, niv = ativo
                chave = (tema_k, niv, w, h)
                g = getattr(self, "_placa", None)
                if g is None or g[0] != chave:
                    g = self._placa = (chave,) + hud.placa_titulo(tema_k, t_h, niv, w, h)
                p.drawImage(QRectF(0, 0, w, h), g[1])
                self._pintar_titulo_placa(p, t, g[2], g[3], g[4], destaque)
                p.end()
                self._trocar_icone(t)
                return
        except Exception as erro:
            from ..seguranca import registrar_erro
            registrar_erro(f"Título do painel (placa) falhou: {erro!r}")
            placa = None
        dx = 16 if placa is not None else 0
        if placa is None:
            fundo = QLinearGradient(0, 0, 0, h)
            alto, baixo = QColor(t["painel2"]), QColor(t["painel"])
            fundo.setColorAt(0, alto.lighter(112) if not claro else alto.lighter(104))
            fundo.setColorAt(1, baixo)
            p.fillRect(self.rect(), fundo)
            borda = QColor(t["borda"])
            p.setPen(QPen(borda, 1))
            p.drawLine(0, h - 1, w, h - 1)
            # faixa de destaque à esquerda
            p.fillRect(QRectF(0, 0, 3, h - 1), destaque)
        p.drawPixmap(10 + dx, (h - 16) // 2, pixmap_icone(self.icone, t["destaque"], 16))
        # nome
        familia = t.get("fonte_painel", t["fonte_titulo"])
        fonte = QFont(familia.split(",")[0].strip("'\" "))
        fonte.setPixelSize(13 if "sans" not in familia else 12)
        fonte.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, t.get("espaco_painel", t["espaco_titulo"]))
        p.setFont(fonte)
        p.setPen(destaque)
        texto = self.dock.windowTitle()
        larg_max = w - 34 - 40 - dx
        texto = p.fontMetrics().elidedText(texto, Qt.TextElideMode.ElideRight, max(20, larg_max))
        p.drawText(QRectF(33 + dx, 0, larg_max, h - 1), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, texto)
        # filete que some pra direita, com um losango
        x0 = 33 + dx + p.fontMetrics().horizontalAdvance(texto) + 12
        x1 = w - 34
        if x1 - x0 > 26:
            y = h / 2
            g = QLinearGradient(x0, 0, x1, 0)
            g.setColorAt(0, QColor(destaque.red(), destaque.green(), destaque.blue(), 150))
            g.setColorAt(1, QColor(destaque.red(), destaque.green(), destaque.blue(), 0))
            p.setPen(QPen(g, 1))
            p.drawLine(QPointF(x0 + 9, y), QPointF(x1, y))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(destaque.red(), destaque.green(), destaque.blue(), 200))
            p.drawPolygon(QPolygonF([QPointF(x0, y), QPointF(x0 + 4, y - 4), QPointF(x0 + 8, y), QPointF(x0 + 4, y + 4)]))
        p.end()
        self._trocar_icone(t)

    def _trocar_icone(self, t):
        # (v0.76) só troca o ícone quando o tema muda: trocar aqui dentro pedia OUTRO redesenho — os títulos dos
        # painéis ficavam se redesenhando em ciclo, todo quadro
        chave_tema = t.get("chave")
        if getattr(self, "_icone_tema", None) != chave_tema:
            self._icone_tema = chave_tema
            self.fechar.setIcon(icone_tema("fechar"))
            self.fechar.setIconSize(QSize(10, 10))

    def _pintar_titulo_placa(self, p, t, medalhao, x_texto, x_div, destaque):
        """(v0.77) Por cima da placa: ícone no medalhão, nome GRAVADO (sombra + brilho) e o filete de metal."""
        h = self.height()
        p.drawPixmap(int(medalhao.x() - 8), int(medalhao.y() - 8), pixmap_icone(self.icone, t["destaque"], 16))
        familia = t.get("fonte_painel", t["fonte_titulo"])
        fonte = QFont(familia.split(",")[0].strip("'\" "))
        fonte.setPixelSize(13 if "sans" not in familia else 12)
        fonte.setBold(True)
        fonte.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, t.get("espaco_painel", t["espaco_titulo"]))
        p.setFont(fonte)
        larg_max = max(20, int(x_div - x_texto - 12))
        texto = p.fontMetrics().elidedText(self.dock.windowTitle(), Qt.TextElideMode.ElideRight, larg_max)
        caixa = QRectF(x_texto, 0, larg_max, h)
        alinhar = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        p.setPen(QColor(0, 0, 0, 170))                      # gravado: sombra embaixo…
        p.drawText(caixa.translated(0, 1.2), alinhar, texto)
        claro = destaque.lighter(150)
        g = QLinearGradient(0, h * 0.25, 0, h * 0.75)       # …e o metal da letra, claro em cima
        g.setColorAt(0, claro)
        g.setColorAt(1, destaque.darker(115))
        p.setPen(QPen(QBrush(g), 1))
        p.drawText(caixa, alinhar, texto)
        # filete de metal afinando até a divisória, com um losango no começo
        x0 = x_texto + p.fontMetrics().horizontalAdvance(texto) + 10
        x1 = x_div - 8
        if x1 - x0 > 24:
            y = h / 2
            from PyQt6.QtGui import QPainterPath
            filete = QPainterPath()
            filete.moveTo(x0 + 8, y - 1.6)
            filete.lineTo(x1, y - 0.3)
            filete.lineTo(x1, y + 0.3)
            filete.lineTo(x0 + 8, y + 1.6)
            filete.closeSubpath()
            gf = QLinearGradient(x0, 0, x1, 0)
            gf.setColorAt(0, QColor(claro.red(), claro.green(), claro.blue(), 210))
            gf.setColorAt(1, QColor(destaque.red(), destaque.green(), destaque.blue(), 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(gf))
            p.drawPath(filete)
            p.setBrush(claro)
            p.drawPolygon(QPolygonF([QPointF(x0, y), QPointF(x0 + 4, y - 4), QPointF(x0 + 8, y), QPointF(x0 + 4, y + 4)]))


class _CabecalhoSecao(QWidget):
    """Faixa clicável de uma Secao: setinha + ícone + nome na fonte do tema + filete."""

    def __init__(self, secao):
        super().__init__(secao)
        self.secao = secao
        self.setFixedHeight(28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._sobre = False

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.secao.alternar()

    def enterEvent(self, ev):
        self._sobre = True
        self.update()

    def leaveEvent(self, ev):
        self._sobre = False
        self.update()

    def paintEvent(self, ev):
        t = tema_atual()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        destaque = QColor(t["destaque"])
        cor = destaque if (self._sobre or self.secao.aberta) else QColor(t["texto"])
        if self._sobre:
            fundo = QColor(t["painel2"])
            p.fillRect(self.rect(), fundo)
        # setinha
        p.setPen(QPen(cor, 1.6, cap=Qt.PenCapStyle.RoundCap, join=Qt.PenJoinStyle.RoundJoin))
        y = h / 2
        if self.secao.aberta:
            seta = [QPointF(5, y - 2), QPointF(9, y + 2), QPointF(13, y - 2)]
        else:
            seta = [QPointF(7, y - 4), QPointF(11, y), QPointF(7, y + 4)]
        p.drawPolyline(QPolygonF(seta))
        x = 20
        if self.secao.icone:
            p.drawPixmap(x, int(y - 8), pixmap_icone(self.secao.icone, cor.name(), 16))
            x += 22
        familia = t.get("fonte_painel", t["fonte_titulo"])
        fonte = QFont(familia.split(",")[0].strip("'\" "))
        fonte.setPixelSize(12)
        fonte.setBold("sans" in familia)
        fonte.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, min(2, t.get("espaco_painel", 1)))
        p.setFont(fonte)
        p.setPen(cor)
        texto = self.secao.titulo.upper()
        p.drawText(QRectF(x, 0, w - x - 40, h), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, texto)
        x0 = x + p.fontMetrics().horizontalAdvance(texto) + 10
        if self.secao.resumo:
            fonte.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0)
            fonte.setBold(False)
            p.setFont(fonte)
            p.setPen(QColor(t["fraco"]))
            larg = p.fontMetrics().horizontalAdvance(self.secao.resumo)
            p.drawText(QRectF(w - larg - 6, 0, larg + 2, h), Qt.AlignmentFlag.AlignVCenter, self.secao.resumo)
            x1 = w - larg - 14
        else:
            x1 = w - 6
        if x1 - x0 > 12:
            g = QLinearGradient(x0, 0, x1, 0)
            g.setColorAt(0, QColor(destaque.red(), destaque.green(), destaque.blue(), 110))
            g.setColorAt(1, QColor(destaque.red(), destaque.green(), destaque.blue(), 0))
            p.setPen(QPen(g, 1))
            p.drawLine(QPointF(x0, y), QPointF(x1, y))
        p.end()


class Secao(QWidget):
    """Bloco de painel que abre/fecha com um clique no título. Lembra se ficou aberto (por PC).

    Uso: s = Secao("atmosfera/clima", "🌦 Clima"); s.lay.addWidget(...)."""

    def __init__(self, chave: str, titulo: str, aberta: bool = True, parent=None):
        super().__init__(parent)
        from PyQt6.QtCore import QSettings
        from PyQt6.QtWidgets import QVBoxLayout
        self.chave = chave
        self.icone, self.titulo = separar(titulo)
        self.resumo = ""
        self._cfg = QSettings("Taverna", "Interface")
        guardado = self._cfg.value(f"secoes/{chave}")
        self.aberta = aberta if guardado is None else str(guardado).lower() in ("true", "1")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(2)
        self.cabecalho = _CabecalhoSecao(self)
        lay.addWidget(self.cabecalho)
        self.corpo = QWidget()
        self.lay = QVBoxLayout(self.corpo)   # é aqui que entra o conteúdo
        self.lay.setContentsMargins(6, 2, 2, 8)
        self.lay.setSpacing(6)
        lay.addWidget(self.corpo)
        self.corpo.setVisible(self.aberta)

    def alternar(self):
        self.definir_aberta(not self.aberta)

    def definir_aberta(self, v: bool, guardar: bool = True):
        self.aberta = bool(v)
        self.corpo.setVisible(self.aberta)
        if guardar:
            self._cfg.setValue(f"secoes/{self.chave}", self.aberta)
        self.cabecalho.update()

    def definir_resumo(self, texto: str):
        """Textinho apagado no fim do título (ex.: "Chuva" quando a seção está fechada)."""
        self.resumo = texto or ""
        self.cabecalho.update()


def enfeitar_dock(dock: QDockWidget, icone: str):
    dock.setTitleBarWidget(TituloPainel(dock, icone))
    from PyQt6.QtWidgets import QTabWidget, QVBoxLayout
    miolo = dock.widget()
    if isinstance(miolo, QTabWidget):   # dá um respiro entre o cabeçalho e as abas
        caixa = QWidget()
        lay = QVBoxLayout(caixa)
        lay.setContentsMargins(5, 7, 5, 5)
        lay.addWidget(miolo)
        dock.setWidget(caixa)


# ====================================================================== emoji → ícone desenhado
# O texto continua escrito com o emoji no código (fica fácil de ler); na hora de mostrar,
# o emoji do começo sai e entra o ícone do tema no lugar. Símbolos de texto (▶ ◀ ● ✔ → …) ficam.
EMOJI_ICONE = {
    "🔒": "cadeado", "🔓": "cadeado_aberto", "👁": "olho", "👤": "pessoa", "👥": "jogadores",
    "🧑": "pessoa", "🧙": "pessoa", "🙂": "pessoa", "👹": "monstro", "🐉": "escudo", "🛡": "escudo",
    "➕": "mais", "＋": "mais", "🗑": "lixeira", "💾": "salvar", "⚠": "aviso", "⚡": "raio",
    "✏": "lapis", "📝": "lapis", "✂": "tesoura", "📁": "pasta", "📂": "pasta", "🗂": "pasta",
    "🗝": "chave", "🎒": "mochila", "💀": "caveira", "✚": "cruz", "📋": "lista",
    "🎲": "dados", "💬": "chat", "🤫": "sussurro", "🎵": "musica", "🎧": "fones", "🔊": "alto_falante",
    "🔇": "mudo", "🔁": "repetir", "⟳": "repetir", "🖼": "imagens", "📽": "projetor", "🗺": "mapa",
    "📦": "objetos", "📚": "biblioteca", "📖": "livro", "📕": "livro", "📗": "livro", "📓": "diario", "📜": "ficha",
    "📄": "pdf", "📤": "exportar", "📥": "importar", "🍺": "taverna", "✨": "magia", "✦": "magia",
    "🪄": "magia", "💡": "luz", "🔥": "chama", "🌋": "vulcao", "🌦": "atmosfera", "⛈": "atmosfera",
    "🌧": "chuva", "🌨": "floco", "❄": "floco", "🍂": "folha", "🏜": "sol", "☀": "sol", "🌫": "nevoa",
    "⚔": "combate", "🎯": "alvo", "🔎": "lupa", "🔍": "lupa", "⌨": "teclado", "❓": "info", "🐞": "aviso", "🧱": "tijolos", "🚪": "porta",
    "🧽": "borracha", "💥": "explosao", "📡": "ao_vivo", "🔴": "ao_vivo", "🏃": "correr", "✋": "mao",
    "👆": "mao", "📅": "calendario", "🏰": "castelo", "⚙": "engrenagem", "🎨": "paleta",
    "📍": "pino", "📌": "pino", "⏭": "proximo", "🟢": "circulo", "⚪": "circulo_vazio",
    "⬤": "token", "⌗": "snap", "🟫": "terreno",
    # áreas de efeito, efeitos rápidos e formas
    "☠": "caveira", "🧪": "frasco", "💧": "gota", "🌑": "lua", "💨": "nevoa", "🕸": "teia",
    "🌿": "folha", "🔮": "magia", "⭕": "circulo_vazio", "⬛": "quadrado", "🔺": "cone",
    "➖": "linha_reta", "🌀": "onda", "🪨": "pedra", "📳": "tremor",
}
_EXTRAS = "️‍ "


def separar(texto: str):
    """'🔒 Trancar' → ('cadeado', 'Trancar'). Sem emoji conhecido no começo → (None, texto)."""
    if not texto:
        return None, texto
    for emoji, nome in EMOJI_ICONE.items():
        if texto.startswith(emoji):
            return nome, texto[len(emoji):].lstrip(_EXTRAS)
    return None, texto


class _Registro:
    """Ícones postos pelo conversor; quando o tema muda, são redesenhados na cor nova."""

    def __init__(self):
        import weakref
        self._ref = weakref.ref
        self.itens = []

    def ligar(self, dono, definir, nome):
        definir(icone_tema(nome))
        try:
            self.itens.append((self._ref(dono), definir, nome))
        except TypeError:
            pass
        if len(self.itens) > 4000:
            self.limpar()

    def limpar(self):
        from PyQt6 import sip
        self.itens = [x for x in self.itens if x[0]() is not None and not sip.isdeleted(x[0]())]

    def atualizar(self):
        self.limpar()
        for _ref, definir, nome in self.itens:
            try:
                definir(icone_tema(nome))
            except RuntimeError:
                pass


ICONES_GLOBAIS = _Registro()


def com_icone(alvo, texto: str = None):
    """QAction ou botão: troca o emoji do começo do texto por um ícone do tema. Devolve o alvo."""
    if texto is None:
        texto = alvo.text()
    nome, limpo = separar(texto)
    alvo.setText(limpo)
    if nome:
        ICONES_GLOBAIS.ligar(alvo, alvo.setIcon, nome)
        if isinstance(alvo, QToolButton) and alvo.toolButtonStyle() == Qt.ToolButtonStyle.ToolButtonTextOnly:
            alvo.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
    elif hasattr(alvo, "property") and alvo.property("_icone_emoji"):
        alvo.setIcon(QIcon())
    if hasattr(alvo, "setProperty"):
        alvo.setProperty("_icone_emoji", bool(nome))
    return alvo


def item_com_icone(item, texto: str, coluna: int = None):
    """Item de lista/árvore: mesmo esquema (ícone na hora; não acompanha troca de tema)."""
    nome, limpo = separar(texto)
    if coluna is None:
        item.setText(limpo)
        item.setIcon(icone_tema(nome) if nome else QIcon())
    else:
        item.setText(coluna, limpo)
        item.setIcon(coluna, icone_tema(nome) if nome else QIcon())
    return item


def adicionar_item(combo, texto: str, dado=None):
    """QComboBox.addItem com o emoji do começo virando ícone."""
    nome, limpo = separar(texto)
    if nome:
        combo.addItem(icone_tema(nome), limpo, dado)
    else:
        combo.addItem(limpo, dado)


def iconizar_menu(menu):
    """Passa por todas as ações (e submenus) de um menu. Chamar antes do exec()."""
    for acao in menu.actions():
        if acao.isSeparator():
            continue
        sub = acao.menu()
        nome, limpo = separar(acao.text())
        if nome:
            acao.setText(limpo)
            ICONES_GLOBAIS.ligar(acao, acao.setIcon, nome)
        if sub is not None:
            iconizar_menu(sub)
    return menu


def iconizar(raiz):
    """Passa uma vez por uma janela/painel já montado trocando os emojis do começo dos textos:
    botões e ações ganham ícone; abas e caixas de opções também; títulos de grupo, rótulos e
    títulos de janela só perdem o emoji (ícone ali não cabe ou não combina)."""
    from PyQt6.QtWidgets import (QAbstractButton, QComboBox, QDialog, QDockWidget, QGroupBox, QLabel,
                                 QTabWidget, QToolBar)
    ws = [raiz] + raiz.findChildren(QWidget)
    for w in ws:
        try:
            if w.property("manter_emoji"):
                continue   # ex.: condições, que ainda não têm desenho próprio
            if isinstance(w, QAbstractButton):
                if isinstance(w.parentWidget(), QToolBar):
                    continue   # a barra de ferramentas já tem os ícones dela
                if separar(w.text())[0]:
                    com_icone(w)
            elif isinstance(w, QGroupBox):
                w.setTitle(separar(w.title())[1])
            elif isinstance(w, QLabel):
                txt = w.text()
                if txt.startswith("<"):   # "<b>🎒 Inventário</b>" → "<b>Inventário</b>"
                    import re
                    m = re.match(r"((?:<[^>]+>)+)(.*)", txt, re.S)
                    if m and separar(m.group(2))[0]:
                        w.setText(m.group(1) + separar(m.group(2))[1])
                    continue
                nome, limpo = separar(txt)
                if nome:
                    if limpo.strip():
                        w.setText(limpo)
                    else:   # rótulo que era só o emoji → vira o desenho
                        tam = max(14, w.fontMetrics().height())
                        w.setText("")
                        ICONES_GLOBAIS.ligar(w, lambda ic, w=w, t=tam: w.setPixmap(ic.pixmap(t, t)), nome)
            elif isinstance(w, QTabWidget):
                for k in range(w.count()):
                    nome, limpo = separar(w.tabText(k))
                    if nome:
                        w.setTabText(k, limpo)
                        ICONES_GLOBAIS.ligar(w, lambda ic, w=w, k=k: w.setTabIcon(k, ic), nome)
            elif isinstance(w, QComboBox):
                for k in range(w.count()):
                    nome, limpo = separar(w.itemText(k))
                    if nome:
                        w.setItemText(k, limpo)
                        w.setItemIcon(k, icone_tema(nome))
            if isinstance(w, (QDialog, QDockWidget)) or w is raiz:
                if w.isWindow() or isinstance(w, QDockWidget):
                    w.setWindowTitle(separar(w.windowTitle())[1])
        except RuntimeError:
            continue
    for menu in raiz.findChildren(QMenu):
        iconizar_menu(menu)
    return raiz


def estilo_barra(barra):
    """Barra de ferramentas com ícone em cima e nome embaixo."""
    barra.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    barra.setIconSize(QSize(22, 22))
    barra.setObjectName("barra_ferramentas")


def espacador():
    w = QWidget()
    w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    w.setStyleSheet("background: transparent;")
    return w
