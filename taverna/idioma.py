"""
🌐 Idiomas do Taverna (v1.0): português (o original, escrito no código) e inglês.

Ninguém precisa mudar o código das janelas: os textos continuam escritos em português, e no inglês eles são
trocados NA HORA DE IR PRA TELA — quando um botão, rótulo, menu, aviso, dica, aba, lista ou desenho recebe o
texto (`instalar()` embrulha esses pontos do Qt). A tradução fica em `idiomas/en.json`:
  - "textos": português → inglês, frase inteira (o emoji do começo e a pontuação do fim são mantidos);
  - "modelos": frases montadas na hora ("Rodada {0}", "{0} entrou na taverna.") → o mesmo em inglês.
Texto que não está lá (nome de token, mensagem de chat, o que o usuário escreveu) fica como está.

O idioma é escolhido na tela inicial (as bandeirinhas) e fica salvo. Mestre e jogador podem usar idiomas
diferentes: o que vem pela rede do mestre também passa pela tradução de quem recebe.
"""

import json
import os
import re

from PyQt6.QtCore import QSettings

IDIOMAS = (("pt", "Português"), ("en", "English"))
PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "idiomas")

_ESTADO = {"idioma": None}
_DIC = {}        # português → inglês (frase inteira)
_NUCLEO = {}     # o mesmo, sem o emoji do começo
_MODELOS = []    # [(regex, modelo inglês, pedaços literais)]
_CACHE = {}
_INICIO = re.compile(r"^([^\wÀ-ÿ<\"“(\[]+)", re.U)          # emoji/símbolos/espaço do começo
_FIM = re.compile(r"([\s:：…!?.–—]+)$")                       # pontuação/espaço do fim
_TAG = re.compile(r"(<[^>]+>|&[a-z]+;|&#\d+;)")


def atual() -> str:
    if _ESTADO["idioma"] is None:
        v = os.environ.get("TAVERNA_IDIOMA") or QSettings("Taverna", "Geral").value("idioma", "pt", type=str)
        _ESTADO["idioma"] = v if v in dict(IDIOMAS) else "pt"
        if _ESTADO["idioma"] != "pt":
            _carregar()
    return _ESTADO["idioma"]


def ingles() -> bool:
    return atual() == "en"


def definir(codigo: str):
    if codigo not in dict(IDIOMAS):
        return
    QSettings("Taverna", "Geral").setValue("idioma", codigo)
    _ESTADO["idioma"] = codigo
    _CACHE.clear()
    if codigo != "pt":
        _carregar()


def _carregar():
    if _DIC:
        return
    caminho = os.path.join(PASTA, "en.json")
    try:
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
    except (OSError, ValueError):
        return
    _DIC.update(dados.get("textos", {}))
    # o mesmo texto SEM o emoji do começo (o acabamento troca o emoji por ícone e regrava o texto sem ele)
    for pt, en in list(_DIC.items()):
        m, n = _INICIO.match(pt), _INICIO.match(en)
        if m:
            _NUCLEO.setdefault(pt[m.end():], en[n.end():] if n else en)
    for pt, en in dados.get("modelos", {}).items():
        pedacos = re.split(r"\{(\d+)\}", pt)
        literais = [p for i, p in enumerate(pedacos) if i % 2 == 0]
        if not any(re.search(r"[A-Za-zÀ-ÿ]", p) for p in literais):
            continue
        rx = ""
        for i, p in enumerate(pedacos):
            if i % 2 == 0:
                rx += re.escape(p.replace("{{", "{").replace("}}", "}"))
            else:
                rx += f"(?P<g{p}>.+?)"
        try:
            _MODELOS.append((re.compile("^" + rx + "$", re.S), en, [x for x in literais if x]))
        except re.error:
            continue
    _MODELOS.sort(key=lambda m: -sum(len(x) for x in m[2]))   # o mais específico primeiro


def _exato(s):
    v = _DIC.get(s)
    if v is not None:
        return v
    if len(s) > 2 and s.isupper() and s != s.capitalize():   # "NOVA SESSÃO" (o texto foi pra maiúsculas)
        v = _exato_base(s.capitalize()) or _exato_base(s.lower())
        if v is not None:
            return v.upper()
    return _exato_base(s)


def _exato_base(s):
    v = _DIC.get(s)
    if v is not None:
        return v
    m = _INICIO.match(s)
    ini = m.group(1) if m else ""
    resto = s[len(ini):]
    m = _FIM.search(resto)
    fim = m.group(1) if m else ""
    meio = resto[:len(resto) - len(fim)] if fim else resto
    for cand, pre, pos in ((resto, ini, ""), (meio, ini, fim)):
        if cand and cand != s:
            v = _DIC.get(cand)
            if v is not None:
                return pre + v + pos
    for cand, pre, pos in ((resto, ini, ""), (meio, ini, fim)):   # o texto veio sem o emoji
        if cand:
            v = _NUCLEO.get(cand)
            if v is not None:
                return pre + v + pos
    return None


def _modelo(s, fundo=0):
    for rx, en, literais in _MODELOS:
        if not all(x in s for x in literais):
            continue
        m = rx.match(s)
        if m:
            brutos = {k[1:]: v for k, v in m.groupdict().items()}
            # "{0}{1}" grudados: o corte entre os dois é chute — traduz os dois juntos
            for a, b in re.findall(r"\{(\d+)\}\{(\d+)\}", en):
                if a in brutos and b in brutos:
                    brutos[a], brutos[b] = brutos[a] + brutos[b], ""
            vals = {k: (v if not v else _traduzir(v, fundo + 1) if fundo < 2 else (_exato(v) or v))
                    for k, v in brutos.items()}
            try:
                return re.sub(r"\{(\d+)\}", lambda g: vals.get(g.group(1), g.group(0)), en)
            except re.error:
                return None
    return None


def _traduzir(s, fundo=0):
    v = _exato(s)
    if v is not None:
        return v
    if fundo < 2 and "<" in s and ">" in s:        # HTML: traduz o texto entre as marcas
        v = _modelo(s, fundo)
        if v is not None:
            return v
        partes = _TAG.split(s)
        mudou = False
        for i, p in enumerate(partes):
            if i % 2 == 0 and p.strip() and re.search(r"[A-Za-zÀ-ÿ]", p):
                q = _traduzir(p, fundo + 1)
                if q != p:
                    partes[i], mudou = q, True
        if mudou:
            return "".join(partes)
    m = _INICIO.match(s)
    ini = m.group(1) if m else ""
    v = _modelo(s[len(ini):], fundo) if ini else _modelo(s, fundo)
    if v is not None:
        return ini + v
    if fundo < 2 and " · " in s:                   # "Gelo  ·  Cristal de gelo": pedaço por pedaço
        partes = re.split(r"(\s+·\s+)", s)
        novas = [p if i % 2 else _traduzir(p, fundo + 1) for i, p in enumerate(partes)]
        if novas != partes:
            return "".join(novas)
    if fundo < 2 and "\n" in s:                    # linha por linha
        linhas = s.split("\n")
        novas = [_traduzir(x, fundo + 1) if x.strip() else x for x in linhas]
        if novas != linhas:
            return "\n".join(novas)
    return s


def t(s):
    """O texto no idioma escolhido (português: ele mesmo)."""
    if not isinstance(s, str) or not s or _ESTADO["idioma"] == "pt":
        return s
    if _ESTADO["idioma"] is None and atual() == "pt":
        return s
    v = _CACHE.get(s)
    if v is not None:
        return v
    if not re.search(r"[A-Za-zÀ-ÿ]", s) or len(s) > 4000:
        v = s
    else:
        try:
            v = _traduzir(s)
        except Exception:
            v = s
    if len(_CACHE) > 30000:
        _CACHE.clear()
    _CACHE[s] = v
    return v


def tl(lista):
    return [t(x) for x in lista] if lista is not None else lista


# ====================================================================== a tela inicial (QML)
_LITERAL_QML = re.compile(r'"((?:[^"\\\n]|\\.)*)"')


def _texto_qml(s):
    """Uma string do QML no idioma escolhido (só frase que está no dicionário; chave de código fica)."""
    if not re.search(r"[A-Za-zÀ-ÿ]", s) or re.fullmatch(r"[a-z0-9_./#:-]*", s):
        return s
    real = s.replace("\\n", "\n")
    if real.isupper():                       # "MESTRE", "SAIR": traduz e devolve em maiúsculas
        v = _exato(real.capitalize()) or _exato(real.lower())
        v = v.upper() if v else None
    else:
        v = _exato(real)
    if v is None or v == real:
        return s
    return v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def pasta_qml(pasta):
    """A pasta do QML no idioma escolhido. Português: a original. Outro idioma: uma cópia (na pasta temporária)
    com as frases dos menus já traduzidas — o QML continua escrito em português."""
    if atual() == "pt":
        return pasta
    import hashlib
    import shutil
    import tempfile
    try:
        marcas = [atual()]
        for raiz, _d, arqs in os.walk(pasta):
            for n in sorted(arqs):
                c = os.path.join(raiz, n)
                marcas.append(f"{os.path.relpath(c, pasta)}:{int(os.path.getmtime(c))}:{os.path.getsize(c)}")
        caminho = os.path.join(PASTA, "en.json")
        if os.path.isfile(caminho):
            marcas.append(str(int(os.path.getmtime(caminho))))
        destino = os.path.join(tempfile.gettempdir(), "taverna_qml",
                               atual() + "_" + hashlib.sha1("|".join(marcas).encode()).hexdigest()[:12])
        if os.path.isfile(os.path.join(destino, "pronto")):
            return destino
        pai = os.path.dirname(destino)
        if os.path.isdir(pai):                        # cópias de versões velhas: fora
            for velha in os.listdir(pai):
                shutil.rmtree(os.path.join(pai, velha), ignore_errors=True)
        shutil.copytree(pasta, destino)
        for raiz, _d, arqs in os.walk(destino):
            for n in arqs:
                if not n.endswith(".qml"):
                    continue
                c = os.path.join(raiz, n)
                with open(c, encoding="utf-8") as f:
                    texto = f.read()
                novo = _LITERAL_QML.sub(lambda m: '"' + _texto_qml(m.group(1)) + '"', texto)
                if novo != texto:
                    with open(c, "w", encoding="utf-8") as f:
                        f.write(novo)
        with open(os.path.join(destino, "pronto"), "w") as f:
            f.write("ok")
        return destino
    except Exception as erro:   # sem conseguir traduzir: abre em português (nunca deixa de abrir)
        try:
            from .seguranca import registrar_erro
            registrar_erro(f"Tela inicial em {atual()}: {erro!r}")
        except Exception:
            pass
        return pasta


# ====================================================================== os pontos do Qt que mostram texto
_INSTALADO = [False]


def _embrulhar(classe, metodo, quais="todos"):
    """Troca classe.metodo por um que traduz os argumentos de texto (str ou lista de str)."""
    original = getattr(classe, metodo, None)
    if original is None or getattr(original, "_taverna_idioma", False):
        return

    def novo(*args, **kw):
        if _ESTADO["idioma"] not in (None, "pt"):
            args = tuple(t(a) if isinstance(a, str) else
                         ([t(x) if isinstance(x, str) else x for x in a] if isinstance(a, list) and a
                          and isinstance(a[0], str) else a) for a in args)
        return original(*args, **kw)
    novo._taverna_idioma = True
    novo.__name__ = metodo
    try:
        setattr(classe, metodo, novo)
    except (TypeError, AttributeError):
        pass


def _embrulhar_estatico(classe, metodo):
    original = getattr(classe, metodo, None)
    if original is None or getattr(original, "_taverna_idioma", False):
        return

    def novo(*args, **kw):
        if _ESTADO["idioma"] not in (None, "pt"):
            args = tuple(t(a) if isinstance(a, str) else a for a in args)
            kw = {k: (t(v) if isinstance(v, str) and k not in ("directory", "dir", "text") else v)
                  for k, v in kw.items()}
        return original(*args, **kw)
    novo._taverna_idioma = True
    try:
        setattr(classe, metodo, staticmethod(novo))
    except (TypeError, AttributeError):
        pass


def _get_item():
    """QInputDialog.getItem: mostra traduzido, mas devolve o item ORIGINAL (o código compara com ele)."""
    from PyQt6.QtWidgets import QInputDialog
    original = QInputDialog.getItem
    if getattr(original, "_taverna_idioma", False):
        return

    def novo(parent, titulo, rotulo, itens, *args, **kw):
        if _ESTADO["idioma"] in (None, "pt"):
            return original(parent, titulo, rotulo, itens, *args, **kw)
        itens = list(itens)
        trad = [t(x) for x in itens]
        escolha, ok = original(parent, t(titulo), t(rotulo), trad, *args, **kw)
        if escolha in trad:
            escolha = itens[trad.index(escolha)]
        return escolha, ok
    novo._taverna_idioma = True
    QInputDialog.getItem = staticmethod(novo)


class _Filtro:
    """Texto que já veio no construtor (QLabel("…"), QAction("…", pai)…): traduz quando o widget é preparado
    pra aparecer (Polish) e quando uma ação entra num menu/barra."""

    def __init__(self):
        from PyQt6.QtCore import QObject

        class F(QObject):
            def eventFilter(s, obj, ev):
                try:
                    if _ESTADO["idioma"] not in (None, "pt"):
                        tp = ev.type()
                        if tp == ev.Type.Polish:
                            _widget(obj)
                        elif tp == ev.Type.ActionAdded:
                            _acao(ev.action())
                except Exception:
                    pass
                return False
        self.obj = F()


def _acao(a):
    if a is None or a.property("_t_idioma"):
        return
    a.setProperty("_t_idioma", True)
    for get, put in ((a.text, a.setText), (a.toolTip, a.setToolTip), (a.statusTip, a.setStatusTip),
                     (a.iconText, a.setIconText)):
        v = get()
        if v:
            n = t(v)
            if n != v:
                put(n)
    m = a.menu()
    if m is not None and m.title():
        m.setTitle(t(m.title()))


def _widget(w):
    from PyQt6.QtWidgets import (QAbstractButton, QComboBox, QDockWidget, QGroupBox, QLabel, QLineEdit, QMenu,
                                 QPlainTextEdit, QTabWidget, QTextEdit, QWidget)
    if not isinstance(w, QWidget) or w.property("_t_idioma"):
        return
    w.setProperty("_t_idioma", True)
    if isinstance(w, (QLabel, QAbstractButton)):
        v = w.text()
        if v:
            n = t(v)
            if n != v:
                w.setText(n)
    elif isinstance(w, QGroupBox):
        w.setTitle(t(w.title()))
    elif isinstance(w, QMenu):
        w.setTitle(t(w.title()))
        for a in w.actions():
            _acao(a)
    elif isinstance(w, QTabWidget):
        for k in range(w.count()):
            w.setTabText(k, t(w.tabText(k)))
            if w.tabToolTip(k):
                w.setTabToolTip(k, t(w.tabToolTip(k)))
    elif isinstance(w, QComboBox):
        for k in range(w.count()):
            v = w.itemText(k)
            n = t(v)
            if n != v:
                w.setItemText(k, n)
    elif isinstance(w, (QLineEdit, QTextEdit, QPlainTextEdit)):
        if w.placeholderText():
            w.setPlaceholderText(t(w.placeholderText()))
    if w.toolTip():
        w.setToolTip(t(w.toolTip()))
    if w.isWindow() or isinstance(w, QDockWidget) or w.windowTitle():
        if w.windowTitle():
            w.setWindowTitle(t(w.windowTitle()))
    for a in w.actions():
        _acao(a)


def _itens_de_lista():
    """Itens criados com texto no construtor e só depois postos na lista/tabela/árvore."""
    from PyQt6.QtWidgets import QListWidget, QTableWidget, QTreeWidget, QTreeWidgetItem

    def lista(orig):
        def novo(self, item, *a):
            if _ESTADO["idioma"] not in (None, "pt") and not isinstance(item, str):
                try:
                    item.setText(t(item.text()))
                    if item.toolTip():
                        item.setToolTip(t(item.toolTip()))
                except Exception:
                    pass
            elif isinstance(item, str):
                item = t(item)
            return orig(self, item, *a)
        novo._taverna_idioma = True
        return novo

    def arvore(item):
        try:
            for c in range(item.columnCount()):
                if item.text(c):
                    item.setText(c, t(item.text(c)))
                if item.toolTip(c):
                    item.setToolTip(c, t(item.toolTip(c)))
            for k in range(item.childCount()):
                arvore(item.child(k))
        except Exception:
            pass

    for cls, met in ((QListWidget, "addItem"), (QListWidget, "insertItem")):
        o = getattr(cls, met)
        if not getattr(o, "_taverna_idioma", False):
            setattr(cls, met, lista(o) if met == "addItem" else
                    (lambda orig: (lambda self, row, item: orig(self, row, t(item) if isinstance(item, str)
                                                                  else (item.setText(t(item.text())) or item)
                                                                  if _ESTADO["idioma"] not in (None, "pt")
                                                                  else item)))(o))
    o = QTableWidget.setItem
    if not getattr(o, "_taverna_idioma", False):
        def set_item(self, r, c, item, _o=o):
            if _ESTADO["idioma"] not in (None, "pt") and item is not None:
                try:
                    item.setText(t(item.text()))
                    if item.toolTip():
                        item.setToolTip(t(item.toolTip()))
                except Exception:
                    pass
            return _o(self, r, c, item)
        set_item._taverna_idioma = True
        QTableWidget.setItem = set_item
    for met in ("addTopLevelItem", "insertTopLevelItem", "addTopLevelItems"):
        o = getattr(QTreeWidget, met)
        if getattr(o, "_taverna_idioma", False):
            continue

        def novo(self, *a, _o=o):
            if _ESTADO["idioma"] not in (None, "pt"):
                for x in a:
                    for it in (x if isinstance(x, list) else [x]):
                        if isinstance(it, QTreeWidgetItem):
                            arvore(it)
            return _o(self, *a)
        novo._taverna_idioma = True
        setattr(QTreeWidget, met, novo)
    for met in ("addChild", "insertChild", "addChildren"):
        o = getattr(QTreeWidgetItem, met)
        if getattr(o, "_taverna_idioma", False):
            continue

        def novo(self, *a, _o=o):
            if _ESTADO["idioma"] not in (None, "pt"):
                for x in a:
                    for it in (x if isinstance(x, list) else [x]):
                        if isinstance(it, QTreeWidgetItem):
                            arvore(it)
            return _o(self, *a)
        novo._taverna_idioma = True
        setattr(QTreeWidgetItem, met, novo)


def instalar(app):
    """Uma vez, logo depois de criar o QApplication. Em português nada muda (os embrulhos só repassam)."""
    if _INSTALADO[0]:
        return
    _INSTALADO[0] = True
    atual()
    from PyQt6.QtGui import QAction, QFontMetrics, QFontMetricsF, QPainter, QPainterPath, QStandardItem
    from PyQt6.QtWidgets import (QAbstractButton, QComboBox, QDialogButtonBox, QDockWidget, QDoubleSpinBox,
                                 QFileDialog, QGroupBox, QInputDialog, QLabel, QLineEdit, QListWidgetItem, QMenu,
                                 QMenuBar, QMessageBox, QPlainTextEdit, QProgressDialog, QSpinBox, QStatusBar,
                                 QTabBar, QTableWidget, QTableWidgetItem, QTabWidget, QTextBrowser, QTextEdit,
                                 QToolBar, QToolBox, QToolButton, QTreeWidget, QTreeWidgetItem, QWidget)
    pontos = {
        QLabel: ("setText",),
        QAbstractButton: ("setText",),
        QAction: ("setText", "setToolTip", "setStatusTip", "setIconText"),
        QWidget: ("setToolTip", "setWindowTitle", "setStatusTip", "setWhatsThis", "setAccessibleName"),
        QLineEdit: ("setPlaceholderText",),
        QTextEdit: ("setPlaceholderText", "setHtml", "setPlainText", "append", "insertHtml", "setText"),
        QPlainTextEdit: ("setPlaceholderText", "setPlainText", "appendPlainText"),
        QGroupBox: ("setTitle",),
        QMenu: ("setTitle", "addAction", "addMenu", "addSection", "insertSection"),
        QMenuBar: ("addMenu", "addAction"),
        QToolBar: ("addAction",),
        QComboBox: ("addItem", "addItems", "insertItem", "insertItems", "setItemText", "setPlaceholderText"),
        QTabWidget: ("addTab", "insertTab", "setTabText", "setTabToolTip"),
        QTabBar: ("addTab", "insertTab", "setTabText", "setTabToolTip"),
        QToolBox: ("addItem", "insertItem", "setItemText"),
        QStatusBar: ("showMessage",),
        QMessageBox: ("setText", "setInformativeText", "setDetailedText", "addButton", "setWindowTitle"),
        QSpinBox: ("setSuffix", "setPrefix", "setSpecialValueText"),
        QDoubleSpinBox: ("setSuffix", "setPrefix", "setSpecialValueText"),
        QListWidgetItem: ("setText", "setToolTip"),
        QTableWidgetItem: ("setText", "setToolTip"),
        QTreeWidgetItem: ("setText", "setToolTip"),
        QStandardItem: ("setText", "setToolTip"),
        QTableWidget: ("setHorizontalHeaderLabels", "setVerticalHeaderLabels"),
        QTreeWidget: ("setHeaderLabels", "setHeaderLabel"),
        QProgressDialog: ("setLabelText", "setCancelButtonText"),
        QInputDialog: ("setLabelText", "setOkButtonText", "setCancelButtonText"),
        QDockWidget: ("setWindowTitle",),
        QDialogButtonBox: ("addButton",),
        QPainter: ("drawText",),
        QPainterPath: ("addText",),
        QFontMetrics: ("horizontalAdvance", "boundingRect", "elidedText", "size", "tightBoundingRect"),
        QFontMetricsF: ("horizontalAdvance", "boundingRect", "elidedText", "size", "tightBoundingRect"),
        QTextBrowser: ("setHtml", "setText", "append"),
        QToolButton: ("setText",),
    }
    for cls, mets in pontos.items():
        for m in mets:
            _embrulhar(cls, m)
    for m in ("question", "information", "warning", "critical", "about"):
        _embrulhar_estatico(QMessageBox, m)
    for m in ("getText", "getInt", "getDouble", "getMultiLineText"):
        _embrulhar_estatico(QInputDialog, m)
    _get_item()
    for m in ("getOpenFileName", "getOpenFileNames", "getSaveFileName", "getExistingDirectory"):
        _embrulhar_estatico_arquivo(QFileDialog, m)
    _itens_de_lista()
    f = _Filtro()
    _INSTALADO.append(f)          # (guardado: senão o Python apaga o filtro)
    app.installEventFilter(f.obj)


def _embrulhar_estatico_arquivo(classe, metodo):
    """QFileDialog: traduz o título e o filtro ("Imagens (*.png …)"), nunca a pasta. O filtro escolhido volta no
    original (o código às vezes compara)."""
    original = getattr(classe, metodo, None)
    if original is None or getattr(original, "_taverna_idioma", False):
        return

    def novo(*args, **kw):
        if _ESTADO["idioma"] in (None, "pt"):
            return original(*args, **kw)
        args = list(args)
        if len(args) > 1 and isinstance(args[1], str):
            args[1] = t(args[1])
        if "caption" in kw:
            kw["caption"] = t(kw["caption"])
        if metodo == "getExistingDirectory":
            return original(*args, **kw)
        filtro = None
        if len(args) > 3 and isinstance(args[3], str):
            filtro = args[3]
        elif isinstance(kw.get("filter"), str):
            filtro = kw["filter"]
        if not filtro:
            return original(*args, **kw)
        trad = ";;".join(t(x) for x in filtro.split(";;"))
        if len(args) > 3:
            args[3] = trad
        else:
            kw["filter"] = trad
        r = original(*args, **kw)
        if isinstance(r, tuple) and len(r) == 2:
            orig, tr_ = filtro.split(";;"), trad.split(";;")
            if r[1] in tr_:
                r = (r[0], orig[tr_.index(r[1])])
        return r
    novo._taverna_idioma = True
    setattr(classe, metodo, staticmethod(novo))
