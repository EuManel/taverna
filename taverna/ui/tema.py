"""
Estilo visual da interface. As cores vêm do tema da aventura (taverna/temas.py):
medieval, moderno, futurista ou mágico.
"""

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPen, QPixmap

from ..temas import TEMA_PADRAO, tema as _tema

# Cores do tema medieval (usadas por quem importa direto daqui)
_m = _tema(TEMA_PADRAO)
FUNDO, PAINEL, PAINEL_2, BORDA = _m["fundo"], _m["painel"], _m["painel2"], _m["borda"]
TEXTO, TEXTO_FRACO, DOURADO, CARMIM = _m["texto"], _m["fraco"], _m["destaque"], "#a8323e"


_ATUAL = TEMA_PADRAO


def tema_atual() -> dict:
    """O tema que está na tela agora (quem desenha na mão pergunta as cores aqui)."""
    return _tema(_ATUAL)


def eh_claro() -> bool:
    return bool(tema_atual().get("claro"))


def _mix(a: str, b: str, f: float) -> str:
    ca, cb = QColor(a), QColor(b)
    return QColor(int(ca.red() + (cb.red() - ca.red()) * f), int(ca.green() + (cb.green() - ca.green()) * f),
                  int(ca.blue() + (cb.blue() - ca.blue()) * f)).name()


def _rgba(cor: str, alfa: int) -> str:
    c = QColor(cor)
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alfa})"


_FONTES_OK = False


def carregar_fontes():
    """Registra as fontes que vêm com o Taverna (pasta taverna/fontes — licença aberta OFL)."""
    global _FONTES_OK
    if _FONTES_OK:
        return
    try:
        import os
        from PyQt6.QtGui import QFontDatabase
        from PyQt6.QtWidgets import QApplication
        if QApplication.instance() is None:
            return
        pasta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fontes")
        for arq in sorted(os.listdir(pasta)):
            if arq.lower().endswith((".ttf", ".otf")):
                QFontDatabase.addApplicationFont(os.path.join(pasta, arq))
        _FONTES_OK = True
    except Exception:
        _FONTES_OK = True   # sem as fontes, cai nas do sistema


def gerar_qss(chave: str = TEMA_PADRAO) -> str:
    global _ATUAL
    carregar_fontes()
    anterior = globals().get("_ATUAL")
    _ATUAL = chave if chave in __import__("taverna.temas", fromlist=["TEMAS"]).TEMAS else TEMA_PADRAO
    if anterior != _ATUAL:   # (v0.64.1) cada tema tem o seu ponteiro do mouse: troca os que já estão na tela
        try:
            from .cursor_global import atualizar_tema
            atualizar_tema()
        except Exception:   # (nunca deixa a troca de tema cair por causa do cursor)
            pass
    t = _tema(chave)
    FUNDO, PAINEL, PAINEL_2, BORDA = t["fundo"], t["painel"], t["painel2"], t["borda"]
    TEXTO, TEXTO_FRACO, DOURADO, SEL = t["texto"], t["fraco"], t["destaque"], t["selecao"]
    TITULO, CORPO, R = t["fonte_titulo"], t["fonte_corpo"], t["raio"]
    D2, PERIGO = t["destaque2"], t["perigo"]
    # QSS só desenha títulos pequenos (painéis, seções): usam a fonte "de painel" do tema
    TITULO, ESP = t["fonte_painel"], t["espaco_painel"]
    claro = t["claro"]
    R2 = max(1, R - 2)
    # degradês discretos dão "volume" aos painéis e botões
    PAINEL_ALTO = _mix(PAINEL, "#ffffff" if not claro else "#fffaf0", 0.045 if not claro else 0.35)
    PAINEL_BAIXO = _mix(PAINEL, "#000000", 0.16 if not claro else 0.05)
    BOTAO_ALTO = _mix(PAINEL_2, "#ffffff", 0.07 if not claro else 0.4)
    BOTAO_BAIXO = _mix(PAINEL_2, "#000000", 0.14 if not claro else 0.06)
    BORDA_FORTE = _mix(BORDA, DOURADO, 0.35)
    SOBRE_DESTAQUE = "#ffffff" if claro else FUNDO
    try:   # a paleta acompanha o tema (quem usa palette(highlight) no estilo pega a cor certa)
        from PyQt6.QtGui import QPalette
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            pal = app.palette()
            for papel, cor in ((QPalette.ColorRole.Highlight, DOURADO), (QPalette.ColorRole.Window, FUNDO),
                               (QPalette.ColorRole.Base, FUNDO), (QPalette.ColorRole.AlternateBase, PAINEL),
                               (QPalette.ColorRole.WindowText, TEXTO), (QPalette.ColorRole.Text, TEXTO),
                               (QPalette.ColorRole.ButtonText, TEXTO), (QPalette.ColorRole.Button, PAINEL_2),
                               (QPalette.ColorRole.HighlightedText, SOBRE_DESTAQUE),
                               (QPalette.ColorRole.PlaceholderText, TEXTO_FRACO),
                               (QPalette.ColorRole.Link, DOURADO), (QPalette.ColorRole.Mid, TEXTO_FRACO),
                               (QPalette.ColorRole.ToolTipBase, PAINEL), (QPalette.ColorRole.ToolTipText, TEXTO)):
                pal.setColor(papel, QColor(cor))
            app.setPalette(pal)
    except Exception:
        pass
    extras = {
        "medieval": f"""
QDockWidget::title {{ border-top: 1px solid {_mix(BORDA, DOURADO, 0.5)}; }}
QPushButton#primario {{ border-width: 1px 1px 2px 1px; }}
""",
        "futurista": f"""
QDockWidget::title {{ border-left: 3px solid {DOURADO}; }}
QPushButton, QToolBar QToolButton {{ border-bottom: 1px solid {_mix(BORDA, DOURADO, 0.55)}; }}
QPushButton:hover, QToolBar QToolButton:hover {{ border-bottom: 1px solid {D2}; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border-bottom: 2px solid {D2}; }}
""",
        "magico": f"""
QDockWidget::title {{ border-bottom: 1px solid {_mix(BORDA, D2, 0.5)}; }}
QPushButton#primario {{ border-color: {D2}; }}
QSlider::handle:horizontal {{ background: {D2}; }}
""",
        "terror": f"""
QDockWidget::title {{ border-left: 2px solid {DOURADO}; color: {_mix(TEXTO, DOURADO, 0.25)}; }}
QPushButton:hover {{ color: {TEXTO}; border-color: {DOURADO}; background: {_mix(PAINEL_2, DOURADO, 0.22)}; }}
QToolTip {{ border-color: {_mix(BORDA, DOURADO, 0.7)}; }}
""",
        "steampunk": f"""
QDockWidget::title {{ border-top: 1px solid {_mix(BORDA, DOURADO, 0.6)}; border-bottom: 1px solid {_mix(BORDA, D2, 0.5)}; }}
QPushButton#primario {{ border-color: {DOURADO}; border-width: 1px 1px 2px 1px; }}
QSlider::handle:horizontal {{ background: {D2}; }}
""",
        "posapoc": f"""
QDockWidget::title {{ border-left: 3px solid {DOURADO}; }}
QPushButton:hover {{ border-color: {DOURADO}; background: {_mix(PAINEL_2, DOURADO, 0.18)}; }}
""",
        "claro": f"""
QDockWidget::title {{ border-top: 2px solid {DOURADO}; }}
QToolBar QToolButton:checked, QPushButton#primario {{ color: {_mix(DOURADO, "#000000", 0.25)}; }}
QSlider::handle:horizontal {{ background: {DOURADO}; }}
""",
        "moderno": f"""
QDockWidget::title {{ border-left: 3px solid {DOURADO}; }}
""",
        "escuro": f"""
QDockWidget::title {{ border-left: 3px solid {DOURADO}; }}
QPushButton#primario {{ background: {DOURADO}; color: {FUNDO}; border-color: {DOURADO}; }}
QPushButton#primario:hover {{ background: {_mix(DOURADO, "#ffffff", 0.2)}; color: {FUNDO}; }}
""",
    }.get(_ATUAL, "")
    # (v0.69) HUD de metal: botões, barras, painéis… com peças de metal de verdade (segue os Gráficos)
    try:
        from ..graficos import nivel as _nivel
        from . import hud
        _ligar_graficos()
        extras += hud.qss(_ATUAL, t, _nivel())
    except Exception:
        pass
    return f"""
* {{
    color: {TEXTO};
    font-family: {CORPO};
    font-size: 10pt;
}}
QMainWindow, QDialog {{ background: {FUNDO}; }}
QMainWindow::separator {{ background: {FUNDO}; width: 5px; height: 5px; }}
QMainWindow::separator:hover {{ background: {BORDA_FORTE}; }}
QMenuBar {{ background: {PAINEL_BAIXO}; border-bottom: 1px solid {BORDA}; padding: 2px; }}
QMenuBar::item {{ padding: 5px 10px; background: transparent; border-radius: {R2}px; }}
QMenuBar::item:selected {{ background: {PAINEL_2}; color: {DOURADO}; }}
QMenu {{ background: {PAINEL}; border: 1px solid {BORDA_FORTE}; padding: 5px; border-radius: {R}px; }}
QMenu::item {{ padding: 6px 26px 6px 22px; border-radius: {R2}px; }}
QMenu::item:selected {{ background: {SEL}; color: {DOURADO}; }}
QMenu::item:disabled {{ color: {TEXTO_FRACO}; }}
QMenu::separator {{ height: 1px; background: {BORDA}; margin: 4px 8px; }}

QToolBar {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {PAINEL_ALTO}, stop:1 {PAINEL_BAIXO});
            border: none; border-bottom: 1px solid {BORDA}; spacing: 3px; padding: 4px 6px; }}
QToolBar::separator {{ background: {BORDA}; width: 1px; margin: 5px 4px; }}
QToolBar QToolButton {{ padding: 5px 7px; border: 1px solid transparent; border-radius: {R}px; }}
QToolBar QToolButton[popupMode="1"] {{ padding-right: 18px; }}
QToolBar QToolButton::menu-button {{ border: none; background: transparent; width: 16px; }}
QToolBar QToolButton::menu-arrow {{ width: 8px; height: 8px; }}
QToolBar QToolButton:hover {{ background: {PAINEL_2}; border-color: {BORDA_FORTE}; }}
QToolBar QToolButton:pressed {{ background: {SEL}; }}
QToolBar QToolButton:checked {{ background: {SEL}; border-color: {DOURADO}; color: {DOURADO}; }}
QToolBar QLabel {{ color: {TEXTO_FRACO}; padding-left: 6px; }}
QToolBar#barra_ferramentas {{ padding: 3px 6px; spacing: 2px; }}
QToolBar#barra_ferramentas QToolButton {{ font-size: 8pt; padding: 4px 7px 3px 7px; min-width: 46px; }}
QToolBar#barra_ferramentas QToolButton#primario {{ background: {SEL}; border: 1px solid {DOURADO}; color: {DOURADO};
                                                   font-weight: bold; padding: 4px 12px 3px 12px; }}
QToolBar#barra_ferramentas QToolButton#primario:hover {{ background: {_mix(SEL, DOURADO, 0.3)}; }}
QTabBar::tab {{ icon-size: 14px; }}

QDockWidget {{ titlebar-close-icon: none; }}
QDockWidget::title {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {PAINEL_ALTO}, stop:1 {PAINEL});
    padding: 7px 10px; border-bottom: 1px solid {BORDA};
    font-family: {TITULO}; color: {DOURADO}; letter-spacing: {ESP}px;
}}
QDockWidget > QWidget {{ background: {PAINEL}; }}

QListWidget, QTreeWidget {{ background: {FUNDO}; border: 1px solid {BORDA}; border-radius: {R}px; padding: 3px; outline: 0; }}
QListWidget::item {{ padding: 7px 6px; border-radius: {R2}px; margin: 1px 0; }}
QTreeWidget::item {{ padding: 5px 4px; border-radius: {R2}px; }}
QListWidget::item:selected, QTreeWidget::item:selected {{ background: {SEL}; color: {DOURADO}; }}
QListWidget::item:hover, QTreeWidget::item:hover {{ background: {PAINEL_2}; }}

QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {BOTAO_ALTO}, stop:1 {BOTAO_BAIXO});
               border: 1px solid {BORDA}; border-radius: {R}px; padding: 6px 12px; }}
QPushButton:hover {{ border-color: {DOURADO}; color: {DOURADO}; }}
QPushButton:pressed {{ background: {SEL}; }}
QPushButton:checked {{ background: {SEL}; border-color: {DOURADO}; color: {DOURADO}; }}
QPushButton:disabled {{ color: {TEXTO_FRACO}; border-color: {PAINEL_2}; background: {PAINEL}; }}
QPushButton#primario {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {_mix(SEL, DOURADO, 0.22)}, stop:1 {SEL});
                        border-color: {DOURADO}; color: {DOURADO}; font-weight: bold; }}
QPushButton#primario:hover {{ background: {_mix(SEL, DOURADO, 0.35)}; }}
QPushButton#perigo {{ border-color: {PERIGO}; color: {PERIGO}; }}

QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {{
    background: {FUNDO}; border: 1px solid {BORDA}; border-radius: {R}px; padding: 5px 7px;
    selection-background-color: {DOURADO}; selection-color: {SOBRE_DESTAQUE};
}}
QLineEdit:hover, QDoubleSpinBox:hover, QSpinBox:hover, QComboBox:hover {{ border-color: {BORDA_FORTE}; }}
QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {{ border-color: {DOURADO}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{ background: {PAINEL}; border: 1px solid {BORDA_FORTE};
                               selection-background-color: {SEL}; selection-color: {DOURADO}; }}
QCheckBox {{ spacing: 7px; }}
QCheckBox::indicator {{ width: 15px; height: 15px; border: 1px solid {BORDA_FORTE}; border-radius: {min(R, 4)}px; background: {FUNDO}; }}
QCheckBox::indicator:hover {{ border-color: {DOURADO}; }}
QCheckBox::indicator:checked {{ background: {DOURADO}; border-color: {DOURADO}; }}
QGroupBox {{ border: 1px solid {BORDA}; border-radius: {R}px; margin-top: 12px; padding-top: 8px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; color: {DOURADO}; }}
QGroupBox::indicator {{ width: 15px; height: 15px; border: 1px solid {BORDA_FORTE}; border-radius: {min(R, 4)}px; background: {FUNDO}; }}
QGroupBox::indicator:checked {{ background: {DOURADO}; border-color: {DOURADO}; }}

QSlider::groove:horizontal {{ height: 4px; background: {BORDA}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {DOURADO}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: {TEXTO}; width: 12px; margin: -5px 0; border-radius: 6px; }}
QSlider::handle:horizontal:hover {{ background: {DOURADO}; }}

QWidget#linha_abas {{ background: {PAINEL}; border-bottom: 1px solid {BORDA}; }}
QTabBar {{ background: transparent; }}
QTabBar::tab {{ background: {FUNDO}; border: 1px solid {BORDA}; border-bottom: none;
               padding: 6px 14px; margin-right: 3px; border-top-left-radius: {R}px;
               border-top-right-radius: {R}px; color: {TEXTO_FRACO}; }}
QTabBar::tab:selected {{ background: {PAINEL_2}; color: {DOURADO}; border-color: {DOURADO}; }}
QTabBar::tab:hover {{ color: {TEXTO}; }}
QWidget#linha_abas QToolButton {{ padding: 4px 10px; border: 1px solid {BORDA}; border-radius: {R}px; }}
QWidget#linha_abas QToolButton:hover {{ border-color: {DOURADO}; color: {DOURADO}; }}
QWidget#linha_abas QPushButton {{ padding: 4px 12px; }}

QTabWidget::pane {{ border: 1px solid {BORDA}; border-radius: {R}px; top: -1px; }}
QTextBrowser {{ background: {FUNDO}; border: 1px solid {BORDA}; border-radius: {R}px; padding: 8px;
               font-size: 11pt; }}
QScrollArea {{ background: {FUNDO}; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QTableWidget {{ background: {FUNDO}; alternate-background-color: {PAINEL}; color: {TEXTO};
               border: 1px solid {BORDA}; border-radius: {R}px; gridline-color: {BORDA}; outline: 0; }}
QTableWidget::item {{ padding: 4px; }}
QTableWidget::item:selected {{ background: {SEL}; color: {DOURADO}; }}
QHeaderView::section {{ background: {PAINEL_2}; color: {TEXTO_FRACO}; border: none;
                       border-bottom: 1px solid {BORDA}; padding: 4px 6px; }}
QTableCornerButton::section {{ background: {PAINEL_2}; border: none; }}
QToolButton#efeito_btn {{ background: {PAINEL_2}; border: 1px solid {BORDA}; border-radius: {R2}px;
                          padding: 3px 6px; text-align: left; }}
QToolButton#efeito_btn:hover {{ border-color: {DOURADO}; }}
QToolButton#efeito_btn:checked {{ background: {SEL}; border-color: {DOURADO}; color: {DOURADO}; }}
QToolButton#primario {{ background: {SEL}; border: 1px solid {DOURADO}; color: {DOURADO};
                       font-weight: bold; border-radius: {R}px; padding: 6px 10px; }}
QToolButton#primario:hover {{ background: {PAINEL_2}; }}
QToolButton#primario::menu-indicator {{ subcontrol-position: right center; right: 6px; }}
QPlainTextEdit {{ background: {FUNDO}; color: {TEXTO}; border: 1px solid {BORDA}; border-radius: {R}px; padding: 4px;
                 selection-background-color: {DOURADO}; selection-color: {SOBRE_DESTAQUE}; }}
QPlainTextEdit:focus {{ border-color: {DOURADO}; }}

QStatusBar {{ background: {PAINEL_BAIXO}; border-top: 1px solid {BORDA}; color: {TEXTO_FRACO}; }}
QStatusBar QLabel {{ color: {TEXTO_FRACO}; padding: 0 8px; }}
QLabel#titulo {{ font-family: {TITULO}; font-size: 12pt; color: {DOURADO}; letter-spacing: {ESP}px; }}
QLabel#dica {{ color: {TEXTO_FRACO}; }}
QToolTip {{ background: {PAINEL}; color: {TEXTO}; border: 1px solid {DOURADO}; padding: 5px; border-radius: {R2}px; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle {{ background: {BORDA}; border-radius: 3px; min-height: 28px; min-width: 28px; }}
QScrollBar::handle:hover {{ background: {BORDA_FORTE}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QSplitter::handle {{ background: {BORDA}; }}
QProgressBar {{ background: {FUNDO}; border: 1px solid {BORDA}; border-radius: {R2}px; text-align: center; }}
QProgressBar::chunk {{ background: {DOURADO}; border-radius: {R2}px; }}

QFrame#sobreposicao {{ background: {_rgba(PAINEL_BAIXO, 236)}; border: 1px solid {DOURADO}; border-radius: {R + 4}px; }}
QFrame#sobreposicao QLabel {{ background: transparent; color: {TEXTO}; }}
QFrame#sobreposicao QPushButton {{ padding: 3px 9px; border-radius: {R}px; }}
{extras}
"""



_LIGADO = False


def _ligar_graficos():
    """Trocou o nível de Gráficos: o HUD muda na hora (o QSS da aplicação é refeito com o tema atual)."""
    global _LIGADO
    if _LIGADO:
        return
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        return
    from ..graficos import graficos
    _LIGADO = True

    def refazer(_chave):
        a = QApplication.instance()
        if a is not None and a.styleSheet():
            a.setStyleSheet(gerar_qss(_ATUAL))
    graficos().mudou.connect(refazer)


def tema_preferido() -> str:
    """Tema da tela inicial (preferência deste PC)."""
    from PyQt6.QtCore import QSettings
    from ..temas import TEMAS
    v = QSettings("Taverna", "Geral").value("tema_inicio", TEMA_PADRAO)
    return v if v in TEMAS else TEMA_PADRAO


def guardar_tema_preferido(chave: str):
    from PyQt6.QtCore import QSettings
    QSettings("Taverna", "Geral").setValue("tema_inicio", chave)


QSS = gerar_qss(TEMA_PADRAO)


def aplicar_tema(app, chave: str):
    app.setStyleSheet(gerar_qss(chave))


def icone_app() -> QIcon:
    """Desenha o ícone do Taverna (um T dourado num medalhão escuro)."""
    icone = QIcon()
    for tam in (16, 24, 32, 48, 64, 128, 256):
        pm = QPixmap(tam, tam)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        k = tam / 128
        p.setBrush(QBrush(QColor("#241c15")))
        p.setPen(QPen(QColor(DOURADO), max(1.0, 6 * k)))
        p.drawEllipse(QRectF(8 * k, 8 * k, 112 * k, 112 * k))
        fonte = QFont("Georgia")
        fonte.setPixelSize(max(8, int(76 * k)))
        fonte.setBold(True)
        p.setFont(fonte)
        p.setPen(QColor(DOURADO))
        p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "T")
        p.end()
        icone.addPixmap(pm)
    return icone


def preparar_icone_windows(app_id: str):
    """
    No Windows, sem isso a barra de tarefas mostra o ícone do Python
    (porque quem roda o programa é o python.exe).
    """
    import sys
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass


def rolavel(widget):
    """Põe o painel dentro de uma área com rolagem: assim o painel pode ficar baixinho
    (o divisor entre os painéis consegue redimensionar) e o resto rola."""
    from PyQt6.QtWidgets import QFrame, QScrollArea
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    area.setWidget(widget)
    area.setMinimumHeight(60)
    return area
