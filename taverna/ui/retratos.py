"""
Retratos estilo Baldur's Gate (v0.31).

- PainelGrupo: coluna de retratos dos jogadores na lateral esquerda da mesa (mestre e jogadores).
  Nome, barra de PV, condições, moldura dourada em quem está na vez; caído fica cinza com a cruz,
  morto escurece com a caveira. Clique = câmera no token · duplo clique = ficha.
- CartaoRetrato também é usado pequeno na faixa da ordem do combate (sobreposicoes.FaixaTurnos).

Os dados vêm de mesa/grupo.py (o servidor já filtra o que cada jogador pode ver).
"""

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import (QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
                         QRadialGradient)
from PyQt6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

from .icones import pixmap_cache
from .tema import tema_atual

_CACHE = {}


def _imagem_cortada(dados: bytes, chave: str, w: int, h: int, dpr: float = 1.0) -> QPixmap | None:
    """Imagem preenchendo w×h (corta as sobras), alinhada em cima (rosto costuma estar no alto)."""
    k = (chave, w, h, dpr)
    if k in _CACHE:
        return _CACHE[k]
    pm = QPixmap()
    if not dados or not pm.loadFromData(dados):
        _CACHE[k] = None
        return None
    W, H = int(w * dpr), int(h * dpr)
    pm = pm.scaled(W, H, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
    pm = pm.copy((pm.width() - W) // 2, 0, W, H)
    pm.setDevicePixelRatio(dpr)
    if len(_CACHE) > 300:
        _CACHE.clear()
    _CACHE[k] = pm
    return pm


class CartaoRetrato(QWidget):
    clicado = pyqtSignal(str)
    duplo = pyqtSignal(str)

    def __init__(self, pequeno: bool = False, parent=None):
        super().__init__(parent)
        self.pequeno = pequeno
        self.dados = {}
        self.imagens = {}
        self.vez = False
        self.ini = None
        self.meu = False
        self._sobre = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
        self.definir_escala(1.0)

    def definir_escala(self, k: float):
        if self.pequeno:
            self.setFixedSize(int(46 * k), int(58 * k))
        else:
            self.setFixedSize(int(78 * k), int(108 * k))

    def definir(self, dados: dict, imagens: dict, vez=False, ini=None, meu=False):
        self.dados, self.imagens, self.vez, self.ini, self.meu = dados, imagens, vez, ini, meu
        nome = dados.get("nome", "")
        dicas = [f"<b>{nome}</b>" + (f" ({dados['dono']})" if dados.get("dono") else "")]
        if dados.get("pv"):
            dicas.append(f"PV {dados['pv'][0]}/{dados['pv'][1]}")
        if dados.get("estado"):
            dicas.append({"morto": "Morto", "caido": "Caído (pode ser ajudado)"}.get(dados["estado"], ""))
        if not self.pequeno and nome != "???":
            dicas.append("<i>Clique: câmera no token · duplo clique: ficha</i>")
        self.setToolTip("<br>".join(d for d in dicas if d))
        self.update()

    # ------------------------------------------------------------ mouse
    def enterEvent(self, ev):
        self._sobre = True
        self.update()

    def leaveEvent(self, ev):
        self._sobre = False
        self.update()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton and self.dados.get("id"):
            self.clicado.emit(self.dados["id"])

    def mouseDoubleClickEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton and self.dados.get("id"):
            self.duplo.emit(self.dados["id"])

    # ------------------------------------------------------------ desenho
    def paintEvent(self, ev):
        """(v0.76) O cartão fica pronto numa imagem: a mesa redesenha a cada quadro (câmera girando) e o retrato
        por cima dela era refeito junto, sem ter mudado nada."""
        dpr = self.devicePixelRatioF()
        chave = (repr(sorted((k, v) for k, v in self.dados.items() if not isinstance(v, (bytes, bytearray)))),
                 id(self.imagens), len(self.imagens), self.vez, self.ini, self.meu, self._sobre, self.width(),
                 self.height(), dpr, tema_atual().get("chave"))
        g = getattr(self, "_guardado", None)
        if g is None or g[0] != chave:
            from PyQt6.QtGui import QPixmap
            pm = QPixmap(max(1, int(self.width() * dpr)), max(1, int(self.height() * dpr)))
            pm.setDevicePixelRatio(dpr)
            pm.fill(Qt.GlobalColor.transparent)
            self._pintar_em(pm)
            g = self._guardado = (chave, pm)
        p = QPainter(self)
        p.drawPixmap(0, 0, g[1])
        p.end()

    def _pintar_em(self, alvo):
        t = tema_atual()
        d = self.dados
        p = QPainter(alvo)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if d.get("escondido"):
            p.setOpacity(0.45)   # mestre: token escondido dos jogadores
        w, h = self.width(), self.height()
        raio = 5 if not self.pequeno else 4
        destaque = QColor(t["destaque"])
        tem_pv = not self.pequeno and d.get("pv")
        alt_pv = 7 if tem_pv else 0
        moldura = QRectF(1.5, 1.5, w - 3, h - 3)
        # sombra + fundo
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 90))
        p.drawRoundedRect(moldura.translated(1.5, 2), raio, raio)
        p.setBrush(QColor(t["painel"]))
        p.drawRoundedRect(moldura, raio, raio)
        # retrato
        quadro = moldura.adjusted(3, 3, -3, -3 - alt_pv - (2 if alt_pv else 0))
        caminho = QPainterPath()
        caminho.addRoundedRect(quadro, raio - 2, raio - 2)
        p.save()
        p.setClipPath(caminho)
        desconhecido = d.get("nome") == "???"
        img = None if desconhecido else _imagem_cortada(self.imagens.get(d.get("img")), d.get("img") or "",
                                                        int(quadro.width()), int(quadro.height()),
                                                        self.devicePixelRatioF())
        if img is not None:
            p.drawPixmap(quadro.topLeft(), img)
        else:
            cor = QColor("#2a2a30") if desconhecido else QColor(d.get("cor") or "#555555")
            g = QRadialGradient(quadro.center() - QPointF(0, quadro.height() * 0.15), quadro.height() * 0.8)
            g.setColorAt(0, cor.lighter(140))
            g.setColorAt(1, cor.darker(170))
            p.fillRect(quadro, g)
            if desconhecido:
                lado = quadro.width() * 0.62
                p.drawPixmap(QRectF(quadro.center().x() - lado / 2, quadro.top() + quadro.height() * 0.12, lado, lado),
                             pixmap_cache("pessoa", "#6a6a72", 96), QRectF(0, 0, 96, 96))
            else:
                f = QFont()
                f.setPixelSize(int(quadro.height() * 0.42))
                f.setBold(True)
                p.setFont(f)
                p.setPen(QColor(245, 235, 215, 220))
                p.drawText(quadro.adjusted(0, -quadro.height() * 0.12, 0, 0), Qt.AlignmentFlag.AlignCenter,
                           (d.get("nome") or "?")[:1].upper())
        # estado: caído (cinza + cruz) · morto (escuro + caveira)
        estado = d.get("estado")
        if estado == "morto":
            p.fillRect(quadro, QColor(10, 8, 8, 170))
            lado = quadro.width() * 0.5
            p.drawPixmap(QRectF(quadro.center().x() - lado / 2, quadro.center().y() - lado * 0.7, lado, lado),
                         pixmap_cache("caveira", "#e8e0d0", 96), QRectF(0, 0, 96, 96))
        elif estado == "caido":
            p.fillRect(quadro, QColor(90, 90, 90, 140))
        # degradê embaixo + nome
        nome_h = quadro.height() * (0.32 if not self.pequeno else 0.36)
        g = QLinearGradient(0, quadro.bottom() - nome_h, 0, quadro.bottom())
        g.setColorAt(0, QColor(0, 0, 0, 0))
        g.setColorAt(1, QColor(0, 0, 0, 210))
        p.fillRect(QRectF(quadro.left(), quadro.bottom() - nome_h, quadro.width(), nome_h), g)
        f = QFont()
        f.setPixelSize(11 if not self.pequeno else 9)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("#f4ecdc"))
        area_nome = QRectF(quadro.left() + 3, quadro.bottom() - 16 if not self.pequeno else quadro.bottom() - 13,
                           quadro.width() - 6, 14 if not self.pequeno else 12)
        nome = p.fontMetrics().elidedText(d.get("nome", ""), Qt.TextElideMode.ElideRight, int(area_nome.width()))
        p.drawText(area_nome, Qt.AlignmentFlag.AlignCenter, nome)
        p.restore()
        # cruz do caído, no canto
        if estado == "caido":
            r = QRectF(quadro.right() - 17, quadro.top() + 2, 15, 15)
            p.setPen(QPen(QColor("#b02020"), 1))
            p.setBrush(QColor("#f4f0e8"))
            p.drawEllipse(r)
            p.drawPixmap(r.adjusted(3, 3, -3, -3), pixmap_cache("cruz", "#c02020", 48), QRectF(0, 0, 48, 48))
        # condições (coluna no canto esquerdo de cima)
        if not self.pequeno and d.get("cond"):
            from ..jogo.condicoes import CONDICOES
            lista = [c for c in d["cond"] if c in CONDICOES]
            if d.get("cond_oculto"):
                p.setOpacity(p.opacity() * 0.6)
            mostrar = lista[:4] if len(lista) <= 4 else lista[:3]
            for k, chave in enumerate(mostrar):
                r = QRectF(quadro.left() + 2, quadro.top() + 2 + k * 16, 15, 15)
                p.setPen(QPen(QColor(201, 162, 74), 1))
                p.setBrush(QColor(20, 16, 12, 220))
                p.drawEllipse(r)
                p.drawPixmap(r.adjusted(3, 3, -3, -3), pixmap_cache(f"cond_{chave}", "#f0e6d2", 48), QRectF(0, 0, 48, 48))
            if len(lista) > 4:
                r = QRectF(quadro.left() + 2, quadro.top() + 2 + 3 * 16, 15, 15)
                p.setBrush(QColor(20, 16, 12, 220))
                p.drawEllipse(r)
                f2 = QFont()
                f2.setPixelSize(8)
                f2.setBold(True)
                p.setFont(f2)
                p.setPen(QColor("#f0e6d2"))
                p.drawText(r, Qt.AlignmentFlag.AlignCenter, f"+{len(lista) - 3}")
            p.setOpacity(0.45 if d.get("escondido") else 1.0)
        # barra de PV
        if tem_pv:
            try:
                atual, maximo = float(d["pv"][0]), max(1.0, float(d["pv"][1]))
            except (TypeError, ValueError, IndexError):
                atual, maximo = 0, 1
            frac = max(0.0, min(1.0, atual / maximo))
            barra = QRectF(quadro.left(), quadro.bottom() + 3, quadro.width(), alt_pv - 1)
            if d.get("pv_oculto"):
                p.setOpacity(p.opacity() * 0.55)
            p.setPen(QPen(QColor(10, 8, 6), 1))
            p.setBrush(QColor(30, 22, 18, 230))
            p.drawRoundedRect(barra, 2.5, 2.5)
            cor = (QColor(90, 190, 90) if frac > 0.5 else QColor(220, 180, 60) if frac > 0.25 else QColor(210, 60, 50))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(cor)
            p.drawRoundedRect(QRectF(barra.left() + 1, barra.top() + 1, (barra.width() - 2) * frac, barra.height() - 2),
                              2, 2)
            p.setOpacity(0.45 if d.get("escondido") else 1.0)
        # iniciativa (faixa do combate)
        if self.ini is not None:
            f = QFont()
            f.setPixelSize(9)
            f.setBold(True)
            p.setFont(f)
            txt = str(self.ini)
            larg = p.fontMetrics().horizontalAdvance(txt) + 7
            r = QRectF(w - larg - 2, 2, larg, 13)
            p.setPen(QPen(destaque, 1))
            p.setBrush(QColor(20, 16, 12, 230))
            p.drawRoundedRect(r, 6, 6)
            p.setPen(QColor("#f4ecdc"))
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, txt)
        # moldura (dourada na vez; destacada no mouse; dupla no seu personagem)
        if self.vez:
            for larg, alfa in ((6, 60), (3, 140)):
                p.setPen(QPen(QColor(destaque.red(), destaque.green(), destaque.blue(), alfa), larg))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRoundedRect(moldura, raio, raio)
            p.setPen(QPen(QColor("#ffd86a"), 2))
        elif self._sobre:
            p.setPen(QPen(destaque, 1.6))
        else:
            p.setPen(QPen(QColor(t["borda"]).lighter(130), 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(moldura, raio, raio)
        if self.meu and not self.vez:
            p.setPen(QPen(destaque, 1))
            p.drawRoundedRect(moldura.adjusted(2, 2, -2, -2), raio - 1, raio - 1)
        p.end()


class PainelGrupo(QWidget):
    """Coluna de retratos por cima da mesa, encostada na esquerda."""
    centralizar = pyqtSignal(str)
    abrir_ficha = pyqtSignal(str)

    def __init__(self, mesa):
        super().__init__(mesa)
        self.mesa = mesa
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(6)
        self.cartoes: list[CartaoRetrato] = []
        self.ligado = True
        from .sobreposicoes import _Acompanhar
        self._acompanhar = _Acompanhar(mesa, self.posicionar)
        self.hide()

    def definir_ligado(self, v: bool):
        self.ligado = bool(v)
        self.setVisible(self.ligado and bool(self.cartoes))

    def atualizar(self, grupo: list[dict], imagens: dict, vez=None, meus=()):
        while len(self.cartoes) < len(grupo):
            c = CartaoRetrato(parent=self)
            c.clicado.connect(self.centralizar)
            c.duplo.connect(self.abrir_ficha)
            self.lay.addWidget(c)
            self.cartoes.append(c)
        while len(self.cartoes) > len(grupo):
            c = self.cartoes.pop()
            self.lay.removeWidget(c)
            c.deleteLater()
        for c, dados in zip(self.cartoes, grupo):
            c.definir(dados, imagens, vez=dados.get("id") == vez, meu=dados.get("id") in meus)
        self.setVisible(self.ligado and bool(grupo))
        self.posicionar()

    def posicionar(self):
        if not self.cartoes:
            return
        disponivel = self.mesa.height() - 24
        n = len(self.cartoes)
        k = 1.0
        while k > 0.55 and n * (108 * k + 6) > disponivel:   # grupo grande: encolhe pra caber
            k -= 0.05
        for c in self.cartoes:
            c.definir_escala(k)
        self.adjustSize()
        self.move(10, 12)
        self.raise_()
