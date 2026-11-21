"""
Portas livres: qualquer lugar, qualquer ângulo.

Coordenadas locais da porta: o vão vai de x = -largura/2 até +largura/2, deitado no eixo x,
com o centro na posição do item. "lado" = pra qual lado ela abre (+1 ou -1, dentro/fora).

Tipos:
  madeira, pedra, metal -> folha que gira na dobradiça
  mecanica              -> folha que desliza pra dentro da parede
  magica                -> não tem folha: é uma barreira de energia que some ao abrir
  grade                 -> grade de ferro que sobe (dá pra ver através)
  secreta               -> fechada, parece parede (só o mestre vê o contorno)
  cortina               -> pano que se recolhe pros lados
"""

import uuid

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import (QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF,
                         QTransform)
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsObject

from ..config import CELULA, COR_DESTAQUE

TIPOS_PORTA = {
    # chave: (nome, cor da folha, cor do detalhe)
    "madeira": ("Porta de madeira", "#8a5a2b", "#d8b45a"),
    "pedra": ("Porta de pedra", "#7d786f", "#4a4640"),
    "metal": ("Porta de metal", "#8d959e", "#d0d6dd"),
    "mecanica": ("Porta mecânica", "#5a6470", "#e0b020"),
    "magica": ("Porta mágica", "#b48cff", "#efe4ff"),
    "grade": ("Grade de ferro (levadiça)", "#5b6169", "#a9b2bc"),
    "secreta": ("Porta secreta", "#7b766f", "#3a3632"),
    "cortina": ("Cortina", "#7a1f2a", "#c9a24a"),
    "janela": ("Janela de vidro", "#9fd0e4", "#6a4a2a"),
    "janela_persiana": ("Janela com persiana", "#7a5232", "#4e3220"),
}
JANELAS = {"janela", "janela_persiana"}


class PortaItem(QGraphicsObject):
    def __init__(self, tipo="madeira", largura_m=1.0, espessura_m=0.12):
        super().__init__()
        self.uid = uuid.uuid4().hex
        self.tipo = tipo
        self.largura_m = largura_m
        self.espessura_m = espessura_m
        self.dupla = False
        self.lado = 1            # +1 / -1: pra que lado abre
        self.dobradica = -1      # -1 = esquerda, +1 = direita (porta simples)
        self.aberta = False
        self.travado = False
        self.jogadores_abrem = tipo != "secreta"   # o mestre deixa os jogadores abrirem/fecharem?
        self.trancada = False
        self.nome_proprio = ""        # ex.: "Porta armadilha"
        self.chave = ""               # nome do item que destranca (ex.: "Chave armadilha")
        self.gasta_chave = False      # a chave some do inventário ao usar
        # Animação: _prog vai de 0 (fechada) até 1 (aberta)
        self._prog = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._passo_animacao)
        from .altura3d import PORTAS
        PORTAS.add(self)   # a camada 3D acha as portas por aqui
        # (v0.60.1, pedido do Manel) a porta fica PRESA onde foi colocada: clicar e arrastar não move.
        # Pra tirar: botão direito → Excluir porta (a parede fecha de novo).
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
                      | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

    # ------------------------------------------------------------ medidas
    @property
    def L(self):
        return self.largura_m * CELULA

    @property
    def T(self):
        return max(3.0, self.espessura_m * CELULA)

    @property
    def nome(self):
        if getattr(self, "nome_proprio", ""):
            return self.nome_proprio
        tam = f"{self.largura_m:g} m".replace(".", ",")
        dupla = " dupla" if self.dupla else ""
        return f"{TIPOS_PORTA.get(self.tipo, ('Porta',))[0]}{dupla} ({tam})"

    def boundingRect(self) -> QRectF:
        L, T = self.L, self.T
        from .camera3d import ALTURA_PAREDE, margem
        m = margem(ALTURA_PAREDE)   # no 3D o topo se desloca pra fora na tela
        return QRectF(-L / 2 - L - 12, -L - 12, 2 * L + 24 + L, 2 * L + 24).adjusted(-m, -m, m, m)

    def shape(self) -> QPainterPath:
        cam = QPainterPath()
        cam.addRect(QRectF(-self.L / 2 - 4, -max(self.T, 14) / 2 - 4,
                           self.L + 8, max(self.T, 14) + 8))
        return cam

    def mudou(self):
        self.prepareGeometryChange()
        self.animar()
        cena = self.scene()
        if cena is not None and hasattr(cena, "marcar_modificada"):
            cena.marcar_modificada()
            if hasattr(cena, "camadas_mudaram"):
                cena.camadas_mudaram.emit()
            if hasattr(cena, "registrar"):
                cena.registrar()

    # ------------------------------------------------------------ animação
    DURACAO = 0.35  # segundos pra abrir/fechar

    def animar(self):
        alvo = 1.0 if self.aberta else 0.0
        if abs(self._prog - alvo) > 1e-3 and not self._timer.isActive():
            self._timer.start()
        self.update()

    def pular_animacao(self):
        self._prog = 1.0 if self.aberta else 0.0
        self._timer.stop()
        self.update()
        self._avisar_luz()

    def _passo_animacao(self):
        alvo = 1.0 if self.aberta else 0.0
        passo = 0.016 / self.DURACAO
        if abs(alvo - self._prog) <= passo:
            self._prog = alvo
            self._timer.stop()
        else:
            self._prog += passo if alvo > self._prog else -passo
        self.update()
        self._avisar_luz()

    def _avisar_luz(self):
        """(v0.60) A folha se mexeu: luz, visão e gás olham de novo onde ela está (a luz vai entrando
        conforme a porta abre, e a folha aberta faz sombra)."""
        cena = self.scene()
        if cena is None:
            return
        timer = getattr(cena, "_timer_luz", None)
        if timer is not None and not timer.isActive():
            timer.start()
        for nome in ("_agendar_cones", "_agendar_nevoa"):
            f = getattr(cena, nome, None)
            if f is not None:
                f()

    # ------------------------------------------------------------ física (luz, visão, gás)
    TRANSPARENTES = {"grade", "janela"}   # dá pra ver através mesmo fechada

    def segmentos_bloqueio(self) -> list[tuple]:
        """Onde a porta está AGORA, como segmentos na cena [(x1, y1, x2, y2)]: a folha girando na dobradiça,
        deslizando pra dentro da parede, a cortina se recolhendo… Fechada = o vão inteiro; aberta = só a
        folha (que faz sombra). Grade e janela de vidro não seguram a luz."""
        if self.tipo in self.TRANSPARENTES or not self.isVisible():
            return []
        import math
        L, p = self.L, self._p
        locais = []   # segmentos no sistema da porta
        if self.tipo in ("madeira", "pedra", "metal", "janela_persiana"):
            if self.tipo == "janela_persiana":
                folhas, giro = [(-L / 2, L / 2, 1), (L / 2, L / 2, -1)], 80
            else:
                folhas = [(-L / 2, L / 2, 1), (L / 2, L / 2, -1)] if self.dupla else \
                         [(self.dobradica * L / 2, L, -self.dobradica)]
                giro = 90
            for x0, comp, sentido in folhas:
                a = math.radians(giro * self.lado * sentido * p)
                locais.append((x0, 0.0, x0 + sentido * comp * math.cos(a), sentido * comp * math.sin(a)))
        elif self.tipo == "mecanica":
            folhas = [(-L / 2, L / 2, -1), (0, L / 2, 1)] if self.dupla else [(-L / 2, L, -1)]
            for x0, comp, sai_para in folhas:
                d = comp * 0.9 * sai_para * p
                x1, x2 = max(-L / 2, x0 + d), min(L / 2, x0 + d + comp)   # o que entrou na parede some
                if x2 - x1 > 1:
                    locais.append((x1, 0.0, x2, 0.0))
        elif self.tipo == "secreta":
            d = -L * 0.95 * p
            x1, x2 = max(-L / 2, -L / 2 + d), min(L / 2, L / 2 + d)
            if x2 - x1 > 1:
                locais.append((x1, 0.0, x2, 0.0))
        elif self.tipo == "cortina":
            metade = L / 2 * (1 - p) + L * 0.12 * p
            locais += [(-L / 2, 0.0, -L / 2 + metade, 0.0), (L / 2 - metade, 0.0, L / 2, 0.0)]
        elif self.tipo == "magica":
            if p < 0.5:
                locais.append((-L / 2, 0.0, L / 2, 0.0))
        else:
            if p < 0.5:
                locais.append((-L / 2, 0.0, L / 2, 0.0))
        t = self.sceneTransform()
        saida = []
        for x1, y1, x2, y2 in locais:
            a, b = t.map(QPointF(x1, y1)), t.map(QPointF(x2, y2))
            saida.append((a.x(), a.y(), b.x(), b.y()))
        return saida

    @property
    def _p(self):
        """Progresso com suavização (começa e termina devagar)."""
        x = self._prog
        return x * x * (3 - 2 * x)

    def aplicar_trava(self, travado):
        self.travado = travado   # (porta nunca é arrastável — v0.60.1)

    def alternar(self):
        self.aberta = not self.aberta
        self.mudou()

    # ------------------------------------------------------------ mouse
    def mouseDoubleClickEvent(self, event):
        cena = self.scene()
        if cena is not None and hasattr(cena, "porta_duplo_clique"):
            cena.porta_duplo_clique(self)   # no player: pede pro mestre
        else:
            self.alternar()
        event.accept()

    def pontas_cena(self):
        meio = self.L / 2
        return self.mapToScene(QPointF(-meio, 0)), self.mapToScene(QPointF(meio, 0))

    def mousePressEvent(self, event):
        self._pos_inicial = self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        cena = self.scene()
        moveu = getattr(self, "_pos_inicial", self.pos()) != self.pos()
        # Gruda de novo na parede/grid ao soltar (segure Alt pra deixar solta)
        if moveu and cena is not None and hasattr(cena, "encaixar_porta_existente") and \
                not (event.modifiers() & Qt.KeyboardModifier.AltModifier):
            cena.encaixar_porta_existente(self)
        if cena is not None and hasattr(cena, "registrar"):
            cena.registrar()  # arrastar a porta entra no Ctrl+Z

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            cena = self.scene()
            if cena is not None and hasattr(cena, "marcar_modificada"):
                cena.marcar_modificada()
        return super().itemChange(change, value)

    # ------------------------------------------------------------ desenho
    def paint(self, painter: QPainter, option, widget=None):
        from . import camera3d
        if not camera3d.ligada():
            self._pintar_2d(painter)
        # no 3D quem desenha é a camada das coisas altas (altura3d), por cima dos tokens

    def pintar_3d(self, painter: QPainter, luzes=()):
        """3D (chamado pela camada ParedesAltas): laterais de cada parte com a altura dela, iluminadas
        pelas luzes da cena; o desenho de sempre vai pro topo."""
        from . import camera3d
        cam = camera3d.Camera(painter)
        # as luzes vêm em coordenadas da cena: passa pras da porta
        local = self.sceneTransform().inverted()[0]
        luzes_locais = [(local.map(c), r, cor, local.map(pol) if pol is not None else None)
                        for c, r, cor, pol in luzes]
        camera_local = local.map(cam.pe_cena())   # onde a câmera está (no chão), na porta
        nevoa = camera3d.nevoa_da_cena(self.scene())   # (v0.70) tela do jogador
        if nevoa is not None and min(nevoa.amostrar(cam.projetar(QPointF(0, s * 0.4 * CELULA), 0.0))
                                     for s in (1, -1)) >= 0.97:   # (dos dois lados da porta)
            return   # porta num lugar que o jogador nunca viu: nada do corpo 3D aparece
        mexendo = camera3d.em_movimento()
        for poligono, base, altura, cor, *extra in self._volumes_3d(camera_local):
            if mexendo and altura - base < 0.2 * CELULA:
                continue   # (v0.76) câmera mexendo: maçaneta/dobradiças (miudezas) ficam pra quando parar
            camera3d.desenhar_laterais(painter, cam, [poligono], altura, cor, None, base,
                                       textura=extra[0] if extra else None, luzes=luzes_locais,
                                       escala_tex=extra[1] if len(extra) > 1 else 1.0, nevoa=nevoa)
        if self.tipo not in ("secreta", "magica"):   # tampa dos batentes, na altura da parede
            painter.save()
            painter.setWorldTransform(cam.transformacao_topo(camera3d.ALTURA_PAREDE))
            painter.setPen(QPen(QColor(0, 0, 0, 180), 1))
            painter.setBrush(QColor(TIPOS_PORTA.get(self.tipo, TIPOS_PORTA["madeira"])[1]).darker(160))
            for x in (-self.L / 2, self.L / 2):
                painter.drawRect(QRectF(x - 3, -max(self.T, 12) / 2 - 1, 6, max(self.T, 12) + 2))
            painter.restore()
        painter.save()
        altura_topo = {"secreta": camera3d.ALTURA_PAREDE}.get(self.tipo, camera3d.ALTURA_PORTA)
        painter.setWorldTransform(cam.transformacao_topo(altura_topo))
        self._pintar_2d(painter)
        painter.restore()

    def _volumes_3d(self, camera_local: QPointF | None = None):
        """Partes da porta com altura: [(polígono local, base, topo, cor[, textura, escala da textura])].
        (v0.67) folha com TEXTURA (texturas_porta), MAÇANETA no lado livre e DOBRADIÇAS no lado da dobradiça — as
        duas só na face virada pra câmera (`camera_local`, o centro da tela nas coordenadas da porta), senão a
        de trás "atravessava" a folha. A GRADE agora é de barras de verdade (vazada)."""
        import math
        from . import camera3d, materiais, texturas_porta
        from .construcao import ESPESSURA
        L, T, p = self.L, self.T, self._p
        H, HP = camera3d.ALTURA_PAREDE, camera3d.ALTURA_PORTA
        cor = QColor(TIPOS_PORTA.get(self.tipo, TIPOS_PORTA["madeira"])[1])
        detalhe = QColor(TIPOS_PORTA.get(self.tipo, TIPOS_PORTA["madeira"])[2])
        tex = texturas_porta.textura(self.tipo)
        esc = texturas_porta.ESCALA
        metal = QColor("#e7c766") if self.tipo != "pedra" else QColor("#4a4640")   # maçaneta (latão / ferro)
        ferro = QColor(48, 46, 44)
        vols = []

        def ret(x0, y0, x1, y1, ang=0.0, piv=(0.0, 0.0)):
            pol = QPolygonF([QPointF(x0, y0), QPointF(x1, y0), QPointF(x1, y1), QPointF(x0, y1)])
            if ang:
                pol = QTransform().translate(*piv).rotate(ang).translate(-piv[0], -piv[1]).map(pol)
            return pol

        def face_da_camera(ang, piv, cx):
            """+1 / -1: qual face da folha (y+ ou y-) está virada pra câmera."""
            if camera_local is None:
                return 1
            a = math.radians(ang)
            nx, ny = -math.sin(a), math.cos(a)                       # a normal y+ girada
            mx = piv[0] + (cx - piv[0]) * math.cos(a)
            my = piv[1] + (cx - piv[0]) * math.sin(a)
            return 1 if nx * (camera_local.x() - mx) + ny * (camera_local.y() - my) >= 0 else -1

        def ferragens(x0, comp, sentido, ang, base=0.0):
            """Maçaneta (no lado livre, ~1 m do chão) e duas dobradiças (no lado da dobradiça)."""
            piv = (x0, 0.0)
            livre = x0 + sentido * comp
            s = face_da_camera(ang, piv, (x0 + livre) / 2)
            y0 = s * (T / 2)
            xm = livre - sentido * 7
            vols.append((ret(xm - 2.2, y0, xm + 2.2, y0 + s * 3.4, ang, piv), base + 0.95 * CELULA,
                         base + 1.06 * CELULA, metal))
            vols.append((ret(xm - 1.2, y0, xm + 1.2, y0 + s * 1.4, ang, piv), base + 0.82 * CELULA,
                         base + 0.95 * CELULA, metal.darker(130)))   # o espelho embaixo da maçaneta
            xd = x0 + sentido * 1.5
            for z0, z1 in ((0.22, 0.36), (1.48, 1.62)):
                vols.append((ret(min(xd, xd + sentido * 7), y0, max(xd, xd + sentido * 7), y0 + s * 1.2, ang, piv),
                             base + z0 * CELULA, base + z1 * CELULA, ferro))

        if self.tipo not in ("secreta", "magica"):   # batentes até a altura da parede
            prof = max(T, 12) + 2
            for x in (-L / 2, L / 2):
                vols.append((ret(x - 3, -prof / 2, x + 3, prof / 2), 0.0, H, cor.darker(160)))
        if self.tipo in ("madeira", "pedra", "metal"):
            folhas = [(-L / 2, L / 2, 1), (L / 2, L / 2, -1)] if self.dupla else \
                     [(self.dobradica * L / 2, L, -self.dobradica)]
            for x0, comp, sentido in folhas:
                x_ini, x_fim = (x0, x0 + comp) if sentido > 0 else (x0 - comp, x0)
                ang = 90 * self.lado * sentido * p
                vols.append((ret(x_ini, -T / 2, x_fim, T / 2, ang, (x0, 0.0)), 0.0, HP, cor, tex, esc))
                ferragens(x0, comp, sentido, ang)
        elif self.tipo == "mecanica":
            folhas = [(-L / 2, L / 2, -1), (0, L / 2, 1)] if self.dupla else [(-L / 2, L, -1)]
            for x0, comp, sai_para in folhas:
                d = comp * 0.9 * sai_para * p
                c = QColor(cor)
                c.setAlpha(255 if p < 0.5 else int(90 + 120 * (1 - p)))
                vols.append((ret(x0 + d, -T / 2, x0 + d + comp, T / 2), 0.0, HP, c, tex if p < 0.5 else None, esc))
        elif self.tipo == "secreta":
            if p < 0.99:
                d = -L * 0.95 * p
                c = QColor(materiais.PAREDES.get("pedra", ("", "#7b766f"))[1])
                vols.append((ret(-L / 2 - 1 + d, -ESPESSURA / 2, L / 2 + 1 + d, ESPESSURA / 2), 0.0, H, c,
                             materiais.textura("parede_face", "pedra")))   # igualzinha à parede de pedra
        elif self.tipo == "grade":
            if p < 0.98:   # (v0.67) grade de BARRAS (dá pra ver através), subindo junto
                base = HP * p
                barra = QColor(cor).darker(115)
                n = max(3, int(L / 9))
                for k in range(n + 1):
                    x = -L / 2 + 4 + (L - 8) * k / n
                    vols.append((ret(x - 1.3, -1.3, x + 1.3, 1.3), base, HP, barra))
                for f in (0.2, 0.55, 0.9):                          # travessas
                    z = base + (HP - base) * f
                    vols.append((ret(-L / 2 + 2, -1.8, L / 2 - 2, 1.8), z - 1.6, z + 1.6, barra.darker(115)))
        elif self.tipo == "cortina":
            metade = L / 2 * (1 - p) + L * 0.12 * p
            for lado in (-1, 1):
                x0 = -L / 2 if lado < 0 else L / 2 - metade
                vols.append((ret(x0, -T / 2, x0 + metade, T / 2), 0.0, HP * 0.97, cor, tex, esc))
        elif self.tipo == "magica":
            if p < 0.99:
                c = QColor(cor)
                c.setAlpha(int(110 * (1 - p)))
                vols.append((ret(-L / 2, -T / 2 - 2, L / 2, T / 2 + 2), 0.0, HP, c))
        elif self.tipo in JANELAS:
            peitoril = 0.9 * CELULA
            vols.append((ret(-L / 2, -T / 2 - 1, L / 2, T / 2 + 1), 0.0, peitoril, detalhe))
            for x0, sentido in ((-L / 2, 1), (L / 2, -1)):
                comp = L / 2
                x_ini, x_fim = (x0, x0 + comp) if sentido > 0 else (x0 - comp, x0)
                c = QColor(cor)
                if self.tipo == "janela":
                    c.setAlpha(150)
                vols.append((ret(x_ini, -T / 2, x_fim, T / 2, 80 * self.lado * sentido * p, (x0, 0.0)),
                             peitoril, HP, c, tex, esc))
        return vols

    def _pintar_2d(self, painter: QPainter):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        L, T = self.L, self.T
        nome, cor, detalhe = TIPOS_PORTA.get(self.tipo, TIPOS_PORTA["madeira"])
        cor, detalhe = QColor(cor), QColor(detalhe)

        # Batentes (as "pontas" do vão) — a porta secreta não tem, pra não se entregar
        if self.tipo != "secreta":
            painter.setPen(QPen(QColor(0, 0, 0, 180), 1))
            painter.setBrush(QColor(cor).darker(160))
            for x in (-L / 2, L / 2):
                painter.drawRect(QRectF(x - 3, -max(T, 12) / 2 - 1, 6, max(T, 12) + 2))

        if self.tipo == "magica":
            self._magica(painter, L, T, cor, detalhe)
        elif self.tipo == "grade":
            self._grade(painter, L, T, cor, detalhe)
        elif self.tipo == "secreta":
            self._secreta(painter, L, T)
        elif self.tipo == "cortina":
            self._cortina(painter, L, T, cor, detalhe)
        elif self.tipo == "mecanica":
            self._mecanica(painter, L, T, cor, detalhe)
        elif self.tipo in JANELAS:
            self._janela(painter, L, T, cor, detalhe)
        else:
            folhas = [(-L / 2, L / 2, 1), (L / 2, L / 2, -1)] if self.dupla else \
                     [(self.dobradica * L / 2, L, -self.dobradica)]
            for dobradica_x, comp, sentido in folhas:
                self._folha(painter, dobradica_x, comp, sentido, T, cor, detalhe)
        if self.trancada and getattr(self, "mostrar_tranca", True):
            from PyQt6.QtGui import QFont
            fonte = QFont()
            fonte.setPixelSize(11)
            painter.setFont(fonte)
            painter.drawText(QRectF(-8, -max(T, 12) / 2 - 16, 16, 14), Qt.AlignmentFlag.AlignCenter, "🔒")

        if self.isSelected():
            caneta = QPen(QColor(COR_DESTAQUE), 1.5, Qt.PenStyle.DashLine)
            caneta.setCosmetic(True)
            painter.setPen(caneta)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.shape().boundingRect())
            # Setinha mostrando pra que lado abre
            painter.setPen(QPen(QColor(COR_DESTAQUE), 2))
            y = self.lado * (max(T, 12) / 2 + 10)
            painter.drawLine(QPointF(0, 0), QPointF(0, y))
            painter.drawLine(QPointF(0, y), QPointF(-4, y - 5 * self.lado))
            painter.drawLine(QPointF(0, y), QPointF(4, y - 5 * self.lado))

    def _folha(self, painter, x0, comp, sentido, T, cor, detalhe):
        """Folha que gira: presa em x0, comprimento comp, sentido +1 (vai pra direita) ou -1."""
        p = self._p
        painter.save()
        painter.translate(x0, 0)
        if p > 0.01:
            arco = QPen(cor.lighter(140), 1, Qt.PenStyle.DashLine)
            arco.setCosmetic(True)
            painter.setPen(arco)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r = QRectF(-comp, -comp, 2 * comp, 2 * comp)
            inicio = 0 if sentido > 0 else 180
            painter.drawArc(r, inicio * 16, int((90 if self.lado < 0 else -90) * sentido * 16 * p))
            painter.rotate(90 * self.lado * sentido * p)
        grad = QLinearGradient(0, -T / 2, 0, T / 2)
        grad.setColorAt(0, cor.lighter(125))
        grad.setColorAt(1, cor.darker(130))
        painter.setPen(QPen(QColor(15, 10, 5), 1))
        painter.setBrush(QBrush(grad))
        x_ini, x_fim = (0, comp) if sentido > 0 else (-comp, 0)
        painter.drawRect(QRectF(x_ini, -T / 2, x_fim - x_ini, T))
        if self.tipo == "metal":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(detalhe)
            for f in (0.15, 0.5, 0.85):
                painter.drawEllipse(QPointF(x_ini + (x_fim - x_ini) * f, 0), 1.4, 1.4)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#e7c766") if self.tipo != "pedra" else detalhe)
        maca = (x_fim - 6) if sentido > 0 else (x_ini + 6)
        painter.drawEllipse(QPointF(maca, 0), 2, 2)
        painter.restore()

    def _janela(self, painter, L, T, cor, detalhe):
        # caixilho fino + duas folhas que abrem pra fora (vidro azulado ou persiana de madeira)
        moldura = QColor(detalhe)
        painter.setPen(QPen(QColor(15, 10, 5), 1))
        painter.setBrush(moldura)
        painter.drawRect(QRectF(-L / 2, -T / 2 - 1, L, 2))
        painter.drawRect(QRectF(-L / 2, T / 2 - 1, L, 2))
        p = self._p
        for x0, sentido in ((-L / 2, 1), (L / 2, -1)):
            painter.save()
            painter.translate(x0, 0)
            painter.rotate(80 * self.lado * sentido * p)
            comp = L / 2
            x_ini, x_fim = (0, comp) if sentido > 0 else (-comp, 0)
            folha = QRectF(x_ini, -T / 2, x_fim - x_ini, T)
            if self.tipo == "janela":
                vidro = QColor(cor)
                vidro.setAlpha(170)
                painter.setPen(QPen(moldura, 1.5))
                painter.setBrush(vidro)
                painter.drawRect(folha)
                painter.setPen(QPen(QColor(255, 255, 255, 160), 1))
                painter.drawLine(QPointF(x_ini + (x_fim - x_ini) * 0.2, -T / 4),
                                 QPointF(x_ini + (x_fim - x_ini) * 0.45, T / 4))
            else:
                painter.setPen(QPen(QColor(15, 10, 5), 1))
                painter.setBrush(QColor(cor))
                painter.drawRect(folha)
                painter.setPen(QPen(moldura, 1))
                passo = max(3.0, abs(x_fim - x_ini) / 6)
                x = min(x_ini, x_fim) + passo
                while x < max(x_ini, x_fim) - 1:
                    painter.drawLine(QPointF(x, -T / 2 + 1), QPointF(x, T / 2 - 1))
                    x += passo
            painter.restore()

    def _mecanica(self, painter, L, T, cor, detalhe):
        p = self._p
        folhas = [(-L / 2, L / 2, -1), (0, L / 2, 1)] if self.dupla else [(-L / 2, L, -1)]
        for x0, comp, sai_para in folhas:
            desloc = comp * 0.9 * sai_para * p   # desliza pra dentro da parede
            r = QRectF(x0 + desloc, -T / 2, comp, T)
            if p > 0.5:
                tracejado = QPen(cor.lighter(140), 1, Qt.PenStyle.DashLine)
                tracejado.setCosmetic(True)
                painter.setPen(tracejado)
                painter.setBrush(QColor(cor.red(), cor.green(), cor.blue(), int(90 + 120 * (1 - p))))
            else:
                painter.setPen(QPen(QColor(10, 10, 10), 1))
                painter.setBrush(cor)
            painter.drawRect(r)
            if p < 0.5:
                painter.save()
                painter.setClipRect(r)
                painter.setPen(QPen(detalhe, 2))
                x = r.left() - T
                while x < r.right():
                    painter.drawLine(QPointF(x, T / 2), QPointF(x + T, -T / 2))
                    x += 6
                painter.restore()

    def _magica(self, painter, L, T, cor, detalhe):
        p = self._p
        r = QRectF(-L / 2, -T / 2 - 2, L, T + 4)
        if p > 0.02:
            caneta = QPen(cor, 1, Qt.PenStyle.DotLine)
            caneta.setCosmetic(True)
            painter.setPen(caneta)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(r)
        forca = 1 - p   # some aos poucos
        if forca <= 0.01:
            return
        brilho = QColor(cor)
        brilho.setAlpha(int(60 * forca))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(brilho)
        painter.drawRoundedRect(r.adjusted(-3, -5, 3, 5), 6, 6)
        grad = QLinearGradient(0, r.top(), 0, r.bottom())
        meio = QColor(detalhe)
        meio.setAlpha(int(230 * forca))
        borda = QColor(cor)
        borda.setAlpha(int(140 * forca))
        grad.setColorAt(0, borda)
        grad.setColorAt(0.5, meio)
        grad.setColorAt(1, borda)
        painter.setBrush(QBrush(grad))
        painter.drawRoundedRect(r, 3, 3)
        painter.setBrush(QColor(255, 255, 255, int(220 * forca)))
        for f in (0.2, 0.45, 0.7, 0.9):
            painter.drawEllipse(QPointF(-L / 2 + L * f, (f - 0.5) * T * 0.6), 1.2, 1.2)

    def _grade(self, painter, L, T, cor, detalhe):
        p = self._p
        if p > 0.5:
            tracejado = QPen(cor.lighter(140), 1, Qt.PenStyle.DashLine)
            tracejado.setCosmetic(True)
            painter.setPen(tracejado)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(-L / 2, -T / 2, L, T))
        if p > 0.98:
            return
        # A grade "sobe": as barras encolhem até sumir
        painter.setPen(QPen(cor.darker(130), 2 * (1 - p)))
        painter.drawLine(QPointF(-L / 2, 0), QPointF(L / 2, 0))
        painter.setPen(QPen(QColor(10, 10, 10), 0.8))
        painter.setBrush(detalhe)
        n = max(3, int(L / 8))
        raio = 2.2 * (1 - p)
        for k in range(n + 1):
            painter.drawEllipse(QPointF(-L / 2 + L * k / n, 0), raio, raio)

    def _secreta(self, painter, L, T):
        from . import materiais
        from .construcao import ESPESSURA
        E = ESPESSURA
        p = self._p
        if p < 0.99:
            # a parede falsa desliza pro lado
            pincel = QBrush(materiais.textura("parede", "pedra"))
            desloc = -L * 0.95 * p
            pincel.setTransform(QTransform().translate(-L / 2 + desloc, -E / 2))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(pincel)
            painter.drawRect(QRectF(-L / 2 - 1 + desloc, -E / 2, L + 2, E))
        cena = self.scene()
        if cena is not None and hasattr(cena, "ferramenta"):
            caneta = QPen(QColor("#e0c060"), 1, Qt.PenStyle.DotLine)
            caneta.setCosmetic(True)
            painter.setPen(caneta)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(-L / 2, -E / 2, L, E))

    def _cortina(self, painter, L, T, cor, detalhe):
        p = self._p
        painter.setPen(QPen(detalhe, 1.5))
        painter.drawLine(QPointF(-L / 2, -T / 2 - 2), QPointF(L / 2, -T / 2 - 2))  # varão
        painter.setPen(QPen(cor.darker(150), 1))
        painter.setBrush(cor)
        # Duas metades que se recolhem pras pontas
        metade = L / 2 * (1 - p) + L * 0.12 * p
        for lado in (-1, 1):
            x0 = -L / 2 if lado < 0 else L / 2 - metade
            n = max(2, int(metade / 8))
            cam = QPainterPath(QPointF(x0, -T / 2))
            for k in range(n):
                xa = x0 + metade * k / n
                cam.quadTo(QPointF(xa + metade / n / 2, T / 2 + 3 + 3 * p),
                           QPointF(xa + metade / n, -T / 2))
            cam.closeSubpath()
            painter.drawPath(cam)

    # ------------------------------------------------------------ dados
    def para_dict(self) -> dict:
        return {"classe": "porta", "id": self.uid, "x": self.pos().x(), "y": self.pos().y(),
                "z": self.zValue(), "angulo": self.rotation(), "tipo": self.tipo,
                "largura_m": self.largura_m, "espessura_m": self.espessura_m,
                "dupla": self.dupla, "lado": self.lado, "dobradica": self.dobradica,
                "aberta": self.aberta, "visivel": self.isVisible(),
                "jogadores_abrem": self.jogadores_abrem, "trancada": self.trancada,
                "nome_proprio": self.nome_proprio, "chave": self.chave, "gasta_chave": self.gasta_chave}

    def aplicar_dict(self, d: dict):
        self.prepareGeometryChange()
        self.tipo = d.get("tipo", "madeira")
        self.largura_m = float(d.get("largura_m", 1.0))
        self.espessura_m = float(d.get("espessura_m", 0.12))
        self.dupla = bool(d.get("dupla", False))
        self.lado = 1 if d.get("lado", 1) >= 0 else -1
        self.dobradica = 1 if d.get("dobradica", -1) > 0 else -1
        self.aberta = bool(d.get("aberta", False))
        self.jogadores_abrem = bool(d.get("jogadores_abrem", self.tipo != "secreta"))
        self.trancada = bool(d.get("trancada", False))
        self.nome_proprio = d.get("nome_proprio", "") or ""
        self.chave = d.get("chave", "") or ""
        self.gasta_chave = bool(d.get("gasta_chave", False))
        self.setRotation(float(d.get("angulo", 0)))
        self.animar()

    @classmethod
    def de_dict(cls, d: dict) -> "PortaItem":
        item = cls()
        item.aplicar_dict(d)
        item.uid = d.get("id") or item.uid
        item.setPos(d.get("x", 0), d.get("y", 0))
        item.setZValue(d.get("z", 0))
        item.setVisible(d.get("visivel", True))
        item.pular_animacao()  # porta carregada já nasce no estado certo
        return item
