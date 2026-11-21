"""
Tokens: jogadores, criaturas e NPCs.

O token ocupa N×N quadrados (1×1 médio, 2×2 grande...). A posição do token
é o canto superior esquerdo da "pegada" dele. Por isso o snap é simples:
basta arredondar a posição para a linha do grid mais próxima, e o token
fica certinho dentro dos quadrados, seja de que tamanho for.

O snap é opcional: o mestre liga e desliga na barra de ferramentas.
"""

import base64
import math
import hashlib
import uuid

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QTransform, QLinearGradient, QBrush, QColor, QFont, QPainter, QPainterPath, QPen,
                         QPixmap, QRadialGradient)
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsObject

from ..config import CELULA, COR_DESTAQUE, TIPOS_TOKEN

ESPESSURA_3D = 0.3 * CELULA   # na Mesa 3D o token é uma ficha de 30 cm de altura


def escala_valida(v) -> float:
    """(v0.78) A escala do standee, conferida (0,3 a 3)."""
    try:
        return max(0.3, min(3.0, float(v)))
    except (TypeError, ValueError):
        return 1.0


_ANGULOS_FICHA = __import__("numpy").linspace(0, 2 * math.pi, 24, endpoint=False)


def _casco(pts):
    """Contorno convexo (monotone chain) dos pontos — a silhueta da ficha vista pela câmera."""
    return [QPointF(x, y) for x, y in _casco_xy([(p.x(), p.y()) for p in pts])]


def _casco_xy(xy):
    """(v0.84) O mesmo casco, em tuplas (x, y) e com a conta do giro em linha (era o que mais pesava por quadro)."""
    s = sorted({(round(x, 3), round(y, 3)) for x, y in xy})
    if len(s) < 3:
        return s

    def meia(seq):
        h = []
        for q in seq:
            qx, qy = q
            while len(h) >= 2:
                ox, oy = h[-2]
                ax, ay = h[-1]
                if (ax - ox) * (qy - oy) - (ay - oy) * (qx - ox) <= 0:
                    h.pop()
                else:
                    break
            h.append(q)
        return h
    baixo = meia(s)
    cima = meia(reversed(s))
    return baixo[:-1] + cima[:-1]


class TokenItem(QGraphicsObject):
    def __init__(self, nome: str, tipo: str = "criatura", cor: str = "#7a4b3a",
                 tamanho: int = 1, imagem: bytes | None = None, dono: str = ""):
        super().__init__()
        self.nome = nome
        self.tipo = tipo
        self.cor = QColor(cor)
        self.tamanho = max(1, int(tamanho))
        self.uid = uuid.uuid4().hex  # identidade do item na rede
        self.dono = dono  # jogador vinculado: só ele move o token
        # Visão (usada nos tokens de jogador quando a névoa de guerra está ligada)
        self.visao_alcance = 24.0     # metros (v0.49: visão comum de uma pessoa)
        self.escala_standee = 1.0      # (v0.78) tamanho da imagem do standee (0,3 a 3)
        self.sem_borda = False         # (v0.77) standee "Sem bordas": só a imagem (PNG recortado em pé no cenário)
        self.estilo = "ficha"          # (v0.73) peça na Mesa 3D: "ficha" (redonda) ou "standee" (em pé)
        self.visao_abertura = 60.0    # graus (v0.71, o Manel: cone de 60° pra frente; era 180)
        self.direcao = 0.0            # graus: 0 = direita, 90 = baixo (sentido horário)
        self.pode_girar = True        # o jogador pode girar pra onde olha?
        self.visao_escuro = 0.0       # metros que enxerga mesmo sem luz (visão no escuro)
        self.travado = False
        # Painel de informações (PV, condições, raça, classe, notas) com visibilidade por campo
        from ..jogo.condicoes import info_vazia
        self.info = info_vazia()
        self.da_vez = False           # é a vez dele no combate?
        self.origem_turno = None      # centro de onde começou o turno (QPointF)
        self.luz = None               # luz que ele carrega (tocha, lanterna...) — acompanha o token
        self.estado = None            # None · "caido" (✚ pode ser ajudado) · "morto" (💀)
        self.efeito = ""              # em chamas, molhado, congelado... (ver mesa/efeitos.py)
        self._cache_efeito = {}
        self.ficha = None             # ficha D&D 5e (dict) — ver jogo/ficha.py
        self.srd = None               # índice do monstro do SRD (se veio da Biblioteca)
        self.limite_turno = None      # metros que pode andar neste turno (None = sem limite)
        self.prender_no_limite = False  # no player: não deixa arrastar pra fora do círculo
        self.ver_ocultos = True       # mestre vê os campos escondidos (apagadinhos)
        self._pixmap = None
        self.imagem = None
        self.definir_imagem(imagem)
        self.definir_retrato(None)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    # ------------------------------------------------------------ dados
    def definir_imagem(self, imagem: bytes | None):
        self.imagem = imagem
        self.hash_imagem = hashlib.sha1(imagem).hexdigest() if imagem else None
        self._pixmap = None
        if imagem:
            pm = QPixmap()
            if pm.loadFromData(imagem):
                self._pixmap = pm
        self.update()

    def definir_retrato(self, retrato: bytes | None):
        """Retrato opcional (em pé, tipo pintura) pros retratos do grupo/combate. Sem ele, usa a imagem."""
        self.retrato = retrato
        self.hash_retrato = hashlib.sha1(retrato).hexdigest() if retrato else None

    def imagem_retrato(self) -> tuple[bytes | None, str | None]:
        """(bytes, hash) do que aparece no retrato: o retrato próprio ou, sem ele, a imagem do token."""
        if getattr(self, "retrato", None):
            return self.retrato, self.hash_retrato
        return self.imagem, self.hash_imagem

    def atualizar(self, nome, tipo, cor, tamanho, imagem, dono):
        self.prepareGeometryChange()
        self.nome, self.tipo, self.dono = nome, tipo, dono
        self.cor = QColor(cor)
        self.tamanho = max(1, int(tamanho))
        self.definir_imagem(imagem)
        self._avisar_modificacao()

    def centro_cena(self) -> QPointF:
        d = self.diametro / 2
        return self.mapToScene(QPointF(d, d))

    @property
    def tem_visao(self) -> bool:
        return self.tipo == "jogador"

    def definir_visao(self, alcance=None, abertura=None, direcao=None, pode_girar=None,
                      escuro=None):
        if escuro is not None:
            self.visao_escuro = max(0.0, float(escuro))
        if alcance is not None:
            self.visao_alcance = max(0.0, float(alcance))
        if abertura is not None:
            self.visao_abertura = max(0.0, min(360.0, float(abertura)))
        if direcao is not None:
            self.direcao = float(direcao) % 360
        if pode_girar is not None:
            self.pode_girar = bool(pode_girar)
        self.update()
        self._avisar_modificacao()
        cena = self.scene()
        if cena is not None and hasattr(cena, "visao_mudou"):
            cena.visao_mudou()

    @property
    def diametro(self) -> float:
        return self.tamanho * CELULA

    def cor_anel(self) -> QColor:
        return QColor(TIPOS_TOKEN.get(self.tipo, TIPOS_TOKEN["criatura"])[1])

    # ------------------------------------------------------------ forma
    def boundingRect(self) -> QRectF:
        d = self.diametro
        # Sobra dos lados pro nome caber, e embaixo pra placa do nome
        from . import camera3d
        f = camera3d.margem(ESPESSURA_3D) if camera3d.ligada() else 0.0   # topo desloca na perspectiva
        if camera3d.ligada() and getattr(self, "estilo", "ficha") == "standee":
            f += self.altura_standee() * 2.2   # (v0.73) o cartão em pé sobe na tela
        return QRectF(-80 - f, -48 - f, d + 160 + 2 * f, d + 82 + 2 * f)

    def _circulo(self) -> QRectF:
        m = 4
        return QRectF(m, m, self.diametro - 2 * m, self.diametro - 2 * m)

    def shape(self) -> QPainterPath:
        caminho = QPainterPath()
        caminho.addEllipse(self._circulo())
        return caminho

    # ------------------------------------------------------------ snap
    def encaixar(self):
        p = self.pos()
        self.setPos(QPointF(round(p.x() / CELULA) * CELULA,
                            round(p.y() / CELULA) * CELULA))

    def aplicar_trava(self, travado: bool):
        self.travado = travado
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not travado)
        self.setCursor(Qt.CursorShape.ArrowCursor if travado
                       else Qt.CursorShape.OpenHandCursor)

    # ------------------------------------------------------------ mouse
    def mousePressEvent(self, event):
        if not self.travado and event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if not self.travado:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        cena = self.scene()
        if cena is not None and getattr(cena, "snap_ativo", False):
            # Encaixa todos os tokens selecionados (arrasto em grupo)
            for item in cena.selectedItems():
                if isinstance(item, TokenItem) and not item.travado:
                    item.encaixar()

    def mouseDoubleClickEvent(self, event):
        cena = self.scene()
        if cena is not None and hasattr(cena, "token_duplo_clique"):
            cena.token_duplo_clique(self)   # no player: saquear
        elif cena is not None and hasattr(cena, "editar_token_pedido"):
            cena.editar_token_pedido.emit(self)
        event.accept()

    @property
    def deslocamento(self) -> float:
        try:
            return float(self.info.get("desl", {}).get("v") or 0)
        except (TypeError, ValueError):
            return 0.0

    def itemChange(self, change, value):
        if (change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.prender_no_limite
                and self.origem_turno is not None and self.limite_turno is not None
                and self.parentItem() is not None):
            # não deixa o centro sair do círculo do deslocamento
            meio = self.diametro / 2
            centro = self.parentItem().mapToScene(value) + QPointF(meio, meio)
            d = centro - self.origem_turno
            dist = (d.x() ** 2 + d.y() ** 2) ** 0.5
            raio = self.limite_turno * CELULA
            if dist > raio > 0:
                centro = self.origem_turno + d * (raio / dist)
                return self.parentItem().mapFromScene(centro - QPointF(meio, meio))
            if raio <= 0:
                return self.pos()
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._avisar_modificacao()
            cena = self.scene()
            if cena is not None and hasattr(cena, "token_movido"):
                cena.token_movido(self)
        return super().itemChange(change, value)

    def _avisar_modificacao(self):
        cena = self.scene()
        if cena is not None and hasattr(cena, "marcar_modificada"):
            cena.marcar_modificada()

    # ------------------------------------------------------------ desenho
    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        c = self._circulo()
        d = self.diametro
        anel = self.cor_anel()

        from ..graficos import nivel as _nivel
        n = _nivel()
        from . import camera3d
        em_3d = camera3d.ligada()
        # Sombra
        painter.setPen(Qt.PenStyle.NoPen)
        if n == 0:
            painter.setBrush(QColor(0, 0, 0, 110))
            painter.drawEllipse(c.translated(2, 4))
        elif em_3d and self.estilo == "standee":
            try:
                self._pintar_standee(painter, c, anel, n)
                if self.animado():   # (v0.79) partículas dos status
                    from .efeitos import animacao
                    animacao().registrar(self)
                self._desenhar_info(painter, c, d)
                self._desenhar_estado(painter, c, d)
                if self.nome:
                    self._placa_de_pe(painter, self._ponto_do_nome(painter), anel)
                return
            except Exception as erro:   # (erro dentro de paint() fecha o programa)
                from ..seguranca import registrar_erro
                registrar_erro(f"Standee não desenhou: {erro!r}")
                self.estilo = "ficha"
        elif em_3d:
            # MESA 3D (v0.37): ficha grossa de verdade — sombra no chão, lateral, e o resto lá no topo
            for k, alfa in (((7, 18), (4, 30), (2, 44)) if n == 2 else ((5, 34), (2, 50))):
                painter.setBrush(QColor(0, 0, 0, alfa))
                painter.drawEllipse(c.adjusted(-k * 0.3, -k * 0.2, k, k).translated(2, 3))
            # (v0.77) o CORPO da ficha (lateral, topo, nome) é desenhado pela camada das coisas altas, junto com os
            # outros tokens, do mais LONGE pro mais PERTO da câmera — antes a ordem era fixa (a da camada) e um token
            # de trás aparecia por cima do da frente com a câmera inclinada. Aqui no chão fica só a sombra.
            from .altura3d import STANDEES
            STANDEES.add(self)
            if self.animado():   # (v0.79) efeito ou condição com partículas: fica animando
                from .efeitos import animacao
                animacao().registrar(self)
            return
        else:
            # sombra macia no chão + a "espessura" da ficha (como uma peça de verdade em cima da mesa)
            for k, alfa in (((9, 16), (6, 26), (3, 40)) if n == 2 else ((6, 34), (3, 48))):
                painter.setBrush(QColor(0, 0, 0, alfa))
                painter.drawEllipse(c.adjusted(-k * 0.4, -k * 0.2, k, k).translated(3, 5))
            esp = max(3.0, d * 0.055)
            borda_base = QColor(anel).darker(260)
            for k in range(int(esp), 0, -1):
                painter.setBrush(borda_base.lighter(100 + (int(esp) - k) * 6))
                painter.drawEllipse(c.translated(0, k))

        # (v0.76) o TOPO da ficha (imagem, degradês, brilho, anel de metal, setinha) fica pronto numa imagem
        # e só é reaproveitado — antes eram ~20 desenhos por token, por quadro (com a câmera girando, todo quadro)
        self._pintar_topo_guardado(painter, c, d, anel, n)

        if self.efeito:
            from .efeitos import agora, animacao, desenhar_sobre
            animacao().registrar(self)
            desenhar_sobre(painter, c, self.efeito, agora(), hash(self.uid) % 99991, self._cache_efeito)
        self._desenhar_info(painter, c, d)
        self._desenhar_estado(painter, c, d)

        # Placa com o nome
        if self.nome and not painter.worldTransform().isAffine():   # (v0.73) câmera inclinada: de pé na tela
            self._placa_de_pe(painter, painter.worldTransform().map(QPointF(d / 2, d + 4)), anel)
        elif self.nome:
            fonte = QFont()
            fonte.setPixelSize(12)
            fonte.setBold(True)
            painter.setFont(fonte)
            larg = painter.fontMetrics().horizontalAdvance(self.nome) + 14
            placa = QRectF(d / 2 - larg / 2, d + 2, larg, 20)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(18, 14, 11, 215))
            painter.drawRoundedRect(placa, 5, 5)
            painter.setPen(QPen(anel, 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(placa, 5, 5)
            painter.setPen(QColor(236, 226, 205))
            painter.drawText(placa, Qt.AlignmentFlag.AlignCenter, self.nome)

    def pintar_corpo_3d(self, painter, n: int):
        """(v0.77) Corpo da ficha na Mesa 3D — chamado pela camada altura3d, com o painter nas coordenadas do token."""
        c = self._circulo()
        d = self.diametro
        anel = self.cor_anel()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        ponto_nome = self._ponto_do_nome(painter)
        try:
            self._pintar_lateral_3d(painter, c, anel)
        except Exception as erro:   # (erro dentro de paint() fecha o programa)
            from ..seguranca import registrar_erro
            registrar_erro(f"Lateral 3D do token falhou: {erro!r}")
        self._pintar_topo_guardado(painter, c, d, anel, n)
        if self.efeito:
            from .efeitos import agora, desenhar_sobre
            desenhar_sobre(painter, c, self.efeito, agora(), hash(self.uid) % 99991, self._cache_efeito)
        self._desenhar_info(painter, c, d)
        self._desenhar_estado(painter, c, d)
        if self.nome:
            self._placa_de_pe(painter, ponto_nome, anel)

    def _ponto_do_nome(self, painter) -> QPointF:
        """Onde vai a placa do nome NA TELA: logo abaixo da peça (girada ou não, sempre embaixo na tela)."""
        from . import camera3d
        cam = camera3d.Camera(painter)
        d = self.diametro
        pe = cam.projetar(QPointF(d / 2, d / 2), 0.0)
        return QPointF(pe.x(), pe.y() + d / 2 * cam.escala * 0.85 + 3)

    # ---------------------------------------------------------- (v0.73) STANDEE
    def altura_standee(self) -> float:
        """Altura do standee (cena): ~1,75 m pra criatura média, crescendo com o tamanho."""
        return 1.75 * CELULA * (self.tamanho ** 0.85) * getattr(self, "escala_standee", 1.0)   # (v0.78) escala

    def _chave_topo(self, n, escala):
        return (self.nome, self.tipo, self.cor.name(), self.tamanho, self.hash_imagem, self.isSelected(), n,
                round(self.direcao, 1) if (self.tem_visao and self.visao_abertura < 359.5) else None, escala)

    def _pintar_topo_guardado(self, painter, c, d, anel, n):
        from .camera3d import escala_de
        import math as _m
        esc = escala_de(painter.worldTransform())
        dpr = painter.device().devicePixelRatioF() if painter.device() is not None and hasattr(painter.device(), "devicePixelRatioF") else 1.0
        # resolução em degraus (não refaz a cada zoominho); um pouco a mais pra perspectiva não borrar
        nivel = 2 ** (round(_m.log2(max(0.05, esc * dpr * 1.3)) * 2) / 2)
        chave = self._chave_topo(n, nivel)
        m = 14.0   # sobra em volta (brilho de seleção, setinha)
        g = getattr(self, "_topo_cache", None)
        if g is None or g[0] != chave:
            from PyQt6.QtGui import QImage
            lado = max(8, int((d + 2 * m) * nivel))
            img = QImage(lado, lado, QImage.Format.Format_ARGB32_Premultiplied)
            img.fill(0)
            p = QPainter(img)
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            p.scale(lado / (d + 2 * m), lado / (d + 2 * m))
            p.translate(m, m)
            p.setPen(Qt.PenStyle.NoPen)
            self._pintar_topo(p, c, d, anel, n, letra=False)
            p.end()
            g = self._topo_cache = (chave, img)
        painter.drawImage(QRectF(-m, -m, d + 2 * m, d + 2 * m), g[1])
        if not self._pixmap:   # (v0.80) a inicial fica sempre EM PÉ na tela, mesmo com a câmera girada
            from .camera3d import Camera
            mu = Camera(painter).mundo
            ang = _m.degrees(_m.atan2(mu.m12(), mu.m11()))
            painter.save()
            painter.translate(c.center())
            painter.rotate(-ang)
            painter.translate(-c.center())
            self._pintar_letra(painter, c, d)
            painter.restore()

    def _pintar_letra(self, painter, c, d):
        inicial = (self.nome.strip()[:1] or "?").upper()
        fonte = QFont("Georgia")
        fonte.setPixelSize(int(d * 0.42))
        fonte.setBold(True)
        painter.setFont(fonte)
        painter.setPen(QColor(245, 235, 215, 230))
        painter.drawText(c, Qt.AlignmentFlag.AlignCenter, inicial)

    def _pintar_topo(self, painter, c, d, anel, n, letra=True):
        """O topo da ficha: brilho de seleção, miolo (imagem ou cor + inicial), anel de metal e a setinha."""
        # Brilho de seleção
        if self.isSelected():
            brilho = QColor(COR_DESTAQUE)
            brilho.setAlpha(90)
            painter.setBrush(brilho)
            painter.drawEllipse(c.adjusted(-5, -5, 5, 5))

        # Miolo: imagem recortada em círculo, ou cor com gradiente + inicial
        if self._pixmap:
            painter.save()
            caminho = QPainterPath()
            caminho.addEllipse(c)
            painter.setClipPath(caminho)
            pm = self._pixmap
            lado = min(pm.width(), pm.height())
            origem = QRectF((pm.width() - lado) / 2, (pm.height() - lado) / 2, lado, lado)
            painter.drawPixmap(c, pm, origem)
            painter.restore()
        else:
            grad = QRadialGradient(c.center() - QPointF(c.width() * 0.2, c.height() * 0.25),
                                   c.width() * 0.75)
            grad.setColorAt(0, self.cor.lighter(150))
            grad.setColorAt(1, self.cor.darker(160))
            painter.setBrush(QBrush(grad))
            painter.drawEllipse(c)
            if letra:
                self._pintar_letra(painter, c, d)

        if n >= 1:
            # luz de cima-esquerda e sombra embaixo-direita por dentro (o miolo fica abaulado)
            caminho_c = QPainterPath()
            caminho_c.addEllipse(c)
            painter.save()
            painter.setClipPath(caminho_c, Qt.ClipOperation.IntersectClip)
            painter.setPen(Qt.PenStyle.NoPen)
            vinheta = QRadialGradient(c.center() - QPointF(c.width() * 0.16, c.height() * 0.2), c.width() * 0.72)
            vinheta.setColorAt(0.0, QColor(255, 250, 235, 26 if n == 1 else 38))
            vinheta.setColorAt(0.55, QColor(0, 0, 0, 0))
            vinheta.setColorAt(1.0, QColor(0, 0, 0, 120 if n == 1 else 150))
            painter.setBrush(QBrush(vinheta))
            painter.drawEllipse(c)
            if n == 2:   # reflexo de vidro em cima
                brilho = QPainterPath()
                brilho.addEllipse(QRectF(c.left() + c.width() * 0.12, c.top() + c.height() * 0.05,
                                         c.width() * 0.76, c.height() * 0.5))
                gb = QLinearGradient(0, c.top(), 0, c.top() + c.height() * 0.55)
                gb.setColorAt(0, QColor(255, 255, 255, 46))
                gb.setColorAt(1, QColor(255, 255, 255, 0))
                painter.fillPath(brilho, QBrush(gb))
            painter.restore()

        # Anel colorido pelo tipo (dourado = jogador, carmim = criatura...)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(15, 12, 10), 5))
        painter.drawEllipse(c)
        if n == 0:
            painter.setPen(QPen(anel, 3))
            painter.drawEllipse(c)
        else:
            # anel de metal: claro em cima-esquerda, escuro embaixo-direita, com filete interno
            metal = QLinearGradient(c.topLeft(), c.bottomRight())
            metal.setColorAt(0.0, anel.lighter(170))
            metal.setColorAt(0.45, anel)
            metal.setColorAt(1.0, anel.darker(190))
            painter.setPen(QPen(QBrush(metal), 3.6))
            painter.drawEllipse(c)
            painter.setPen(QPen(QColor(255, 250, 230, 70), 1))
            painter.drawEllipse(c.adjusted(-1.6, -1.6, 1.6, 1.6))
            painter.setPen(QPen(QColor(0, 0, 0, 110), 1))
            painter.drawEllipse(c.adjusted(2.4, 2.4, -2.4, -2.4))

        # Pra onde está olhando (setinha na borda) — só tokens de jogador com cone
        if self.tem_visao and self.visao_abertura < 359.5:
            import math
            ang = math.radians(self.direcao)
            cx, cy = d / 2, d / 2
            r = c.width() / 2
            ponta = QPointF(cx + math.cos(ang) * (r + 9), cy + math.sin(ang) * (r + 9))
            lado1 = QPointF(cx + math.cos(ang + 0.32) * (r - 1), cy + math.sin(ang + 0.32) * (r - 1))
            lado2 = QPointF(cx + math.cos(ang - 0.32) * (r - 1), cy + math.sin(ang - 0.32) * (r - 1))
            from PyQt6.QtGui import QPolygonF
            painter.setPen(QPen(QColor(15, 12, 10), 1.5))
            painter.setBrush(anel)
            painter.drawPolygon(QPolygonF([ponta, lado1, lado2]))

    def _pintar_standee(self, painter, c: QRectF, anel: QColor, n: int):
        """Peça STANDEE (Mesa 3D): base escura no chão com o anel do tipo e a imagem num cartão EM PÉ, sempre
        virado pra câmera (de cima ou inclinada). Sem imagem: a cor e a inicial no cartão."""
        import math
        from . import camera3d
        cam = camera3d.Camera(painter)
        centro = c.center()
        raio = c.width() / 2
        # --- base no chão (no plano do chão, com a perspectiva da mesa)
        base = QRectF(centro.x() - raio * 0.82, centro.y() - raio * 0.82, raio * 1.64, raio * 1.64)
        painter.setPen(Qt.PenStyle.NoPen)
        for k, alfa in ((6, 26), (3, 44)):
            painter.setBrush(QColor(0, 0, 0, alfa))
            painter.drawEllipse(base.adjusted(-k * 0.3, -k * 0.2, k, k).translated(2, 3))
        if self.isSelected():
            brilho = QColor(COR_DESTAQUE)
            brilho.setAlpha(110)
            painter.setBrush(brilho)
            painter.drawEllipse(base.adjusted(-6, -6, 6, 6))
        if not (self.sem_borda and self._pixmap is not None):
            g = QRadialGradient(base.center() - QPointF(raio * 0.2, raio * 0.25), raio)
            g.setColorAt(0, QColor(58, 50, 44))
            g.setColorAt(1, QColor(16, 13, 11))
            painter.setBrush(QBrush(g))
            painter.setPen(QPen(anel, 3))
            painter.drawEllipse(base)
        # --- o cartão em pé é desenhado pela camada das coisas altas (altura3d), depois das paredes e
        # recortado só pelas paredes que estão ENTRE a câmera e o token (profundidade certa) — v0.73
        from .altura3d import STANDEES
        STANDEES.add(self)

    def cartao_na_tela(self, cam) -> tuple:
        """(retângulo do cartão na tela, ponto da base na tela) pra esta câmera."""
        d = self.diametro
        centro = self.mapToScene(QPointF(d / 2, d / 2))
        H = self.altura_standee()
        B = cam.projetar(centro, ESPESSURA_3D * 0.4)   # (cam do painter da cena: coordenadas da cena)
        aspecto = self._aspecto_cartao()
        from . import camera3d
        if not camera3d.camera_livre():
            # (v0.77) câmera TRAVADA: a foto fica deitada, virada pra cima (pra câmera), centrada no token
            h_px = d * 1.55 * cam.escala * self.escala_standee   # (v0.78) escala da imagem
            w_px = h_px * aspecto
            meio = cam.projetar(centro, ESPESSURA_3D * 0.4)
            return QRectF(meio.x() - w_px / 2, meio.y() - h_px / 2, w_px, h_px), B
        h_px = H * cam.escala * cam.fator(H * 0.5) * 0.92
        w_px = h_px * aspecto
        return QRectF(B.x() - w_px / 2, B.y() - h_px, w_px, h_px), B

    def _aspecto_cartao(self) -> float:
        pm = self._pixmap
        if pm is None or pm.height() <= 0:
            return 0.66
        if self.sem_borda:   # PNG recortado: a proporção da própria imagem
            return max(0.25, min(2.0, pm.width() / pm.height()))
        return max(0.5, min(1.0, pm.width() / pm.height()))

    def pintar_cartao(self, painter, cam, n: int):
        """O cartão do standee, na TELA (painter sem transformação). Chamado pela camada altura3d."""
        anel = self.cor_anel()
        cartao, B = self.cartao_na_tela(cam)
        w_px, h_px = cartao.width(), cartao.height()
        pm = self._pixmap
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        r = max(2.0, w_px * 0.06)
        if not (self.sem_borda and pm is not None):   # sombrinha embaixo da foto deitada
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 90))
            painter.drawRoundedRect(cartao.translated(max(1.0, w_px * 0.03), max(1.5, w_px * 0.05)), r, r)
        self._face_cartao(painter, cartao, n, anel)
        painter.restore()

    def _face_cartao(self, painter, cartao: QRectF, n: int, anel: QColor):
        """A face do cartão (imagem ou cor + inicial, verniz e moldura) dentro de `cartao`."""
        pm = self._pixmap
        w_px = cartao.width()
        r = max(2.0, w_px * 0.06)
        if self.sem_borda and pm is not None:   # (v0.77) PNG recortado: só a imagem (sem fundo, verniz e moldura)
            painter.drawPixmap(cartao, pm, QRectF(pm.rect()))
            if self.isSelected():
                c_sel = QColor(COR_DESTAQUE)
                c_sel.setAlpha(150)
                painter.setPen(QPen(c_sel, max(1.0, w_px * 0.02), Qt.PenStyle.DashLine))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(cartao)
            return
        caminho = QPainterPath()
        caminho.addRoundedRect(cartao, r, r)
        painter.save()
        painter.setClipPath(caminho, Qt.ClipOperation.IntersectClip)   # (soma com o recorte das paredes da frente)
        if pm is not None:
            lado_w, lado_h = pm.width(), pm.height()
            alvo = cartao.width() / cartao.height()
            if lado_w / max(1, lado_h) > alvo:   # corta os lados (cobre o cartão inteiro)
                nw = lado_h * alvo
                origem = QRectF((lado_w - nw) / 2, 0, nw, lado_h)
            else:
                nh = lado_w / alvo
                origem = QRectF(0, 0, lado_w, nh)   # (pega de cima: rosto)
            fundo = QLinearGradient(cartao.topLeft(), cartao.bottomLeft())
            fundo.setColorAt(0, self.cor.lighter(130))
            fundo.setColorAt(1, self.cor.darker(170))
            painter.fillRect(cartao, QBrush(fundo))
            painter.drawPixmap(cartao, pm, origem)
        else:
            fundo = QLinearGradient(cartao.topLeft(), cartao.bottomLeft())
            fundo.setColorAt(0, self.cor.lighter(150))
            fundo.setColorAt(1, self.cor.darker(170))
            painter.fillRect(cartao, QBrush(fundo))
            fonte = QFont("Georgia")
            fonte.setPixelSize(max(6, int(w_px * 0.62)))
            fonte.setBold(True)
            painter.setFont(fonte)
            painter.setPen(QColor(245, 235, 215, 235))
            painter.drawText(cartao, Qt.AlignmentFlag.AlignCenter, (self.nome.strip()[:1] or "?").upper())
        if n >= 1:   # luz de cima e um brilho de verniz
            vern = QLinearGradient(cartao.topLeft(), cartao.topRight())
            vern.setColorAt(0.0, QColor(255, 255, 255, 34))
            vern.setColorAt(0.35, QColor(255, 255, 255, 0))
            vern.setColorAt(1.0, QColor(0, 0, 0, 60))
            painter.fillRect(cartao, QBrush(vern))
        painter.restore()
        # moldura na cor do tipo
        moldura = QColor(COR_DESTAQUE) if self.isSelected() else anel
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(10, 8, 6), max(2.0, w_px * 0.07)))
        painter.drawRoundedRect(cartao, r, r)
        painter.setPen(QPen(moldura, max(1.2, w_px * 0.035)))
        painter.drawRoundedRect(cartao, r, r)

    def _imagem_face(self, n: int):
        """A face do cartão pronta numa imagem (pro standee EM PÉ no mundo, câmera livre). Guardada."""
        pm = self._pixmap
        aspecto = 0.66
        if pm is not None and pm.height() > 0:
            aspecto = max(0.5, min(1.0, pm.width() / pm.height()))
        aspecto = self._aspecto_cartao()
        chave = (self.hash_imagem, self.cor.name(), self.nome, self.tipo, self.isSelected(), n, round(aspecto, 3),
                 self.sem_borda)
        g = getattr(self, "_face_cache", None)
        if g is None or g[0] != chave:
            from PyQt6.QtGui import QImage
            H = 256
            W = int(H * aspecto)
            img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
            img.fill(0)
            p = QPainter(img)
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            m = 0 if self.sem_borda else 3
            self._face_cartao(p, QRectF(m, m, W - 2 * m, H - 2 * m), n, self.cor_anel())
            p.end()
            g = self._face_cache = (chave, img, aspecto)
        return g[1], g[2]

    def pintar_cartao_no_mundo(self, painter, cam, n: int):
        """(v0.77) CÂMERA LIVRE: o standee é uma foto EM PÉ num suporte, parada no mundo — virada pra onde o token
        olha. Girando a câmera dá pra ver de lado (fininho) e de costas (o verso, a mesma imagem espelhada)."""
        import math
        from . import camera3d
        img, aspecto = self._imagem_face(n)
        H = self.altura_standee()
        L = H * aspecto
        d = self.diametro
        c = self.mapToScene(QPointF(d / 2, d / 2))
        ang = math.radians(self.direcao)
        fx, fy = math.cos(ang), math.sin(ang)          # a frente da foto
        ux, uy = -fy, fx                                # ao longo da foto
        z0 = H * 0.06
        cantos = [(c.x() - ux * L / 2, c.y() - uy * L / 2, z0), (c.x() + ux * L / 2, c.y() + uy * L / 2, z0),
                  (c.x() + ux * L / 2, c.y() + uy * L / 2, H), (c.x() - ux * L / 2, c.y() - uy * L / 2, H)]
        if not all(cam.na_frente(QPointF(x, y), z) for x, y, z in cantos):
            return
        # o pé do suporte: um bloquinho escuro no chão (3D de verdade)
        from PyQt6.QtGui import QPolygonF
        pe_l, pe_p = L * 0.36, H * 0.07
        pol_pe = QPolygonF([QPointF(c.x() + sx * ux * pe_l + sy * fx * pe_p, c.y() + sx * uy * pe_l + sy * fy * pe_p)
                            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
        sem_borda = self.sem_borda and self._pixmap is not None
        if not sem_borda:
            camera3d.desenhar_laterais(painter, cam, [pol_pe], z0 * 1.2, QColor(26, 22, 18), None, 0.0)
        else:
            z0 = 0.0   # (PNG em pé direto no chão)
            cantos = [(x, y, (0.0 if z < H else H)) for x, y, z in cantos]
        quad = QPolygonF([cam.projetar(QPointF(x, y), z) for x, y, z in cantos])
        pe = cam.pe_cena()
        de_costas = (pe.x() - c.x()) * fx + (pe.y() - c.y()) * fy < 0
        W, Hh = img.width(), img.height()
        origem = QPolygonF([QPointF(W, Hh), QPointF(0, Hh), QPointF(0, 0), QPointF(W, 0)]) if de_costas else \
            QPolygonF([QPointF(0, Hh), QPointF(W, Hh), QPointF(W, 0), QPointF(0, 0)])
        tr = QTransform()
        if not QTransform.quadToQuad(origem, quad, tr):
            return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if not sem_borda:
            painter.setPen(QPen(QColor(10, 8, 6, 220), 2.2))   # a borda do papelão (espessura)
            painter.setBrush(QColor(14, 12, 10))
            painter.drawPolygon(quad)
        painter.setTransform(tr)
        if de_costas and not sem_borda:   # o verso um pouco mais escuro (a luz vem do outro lado)
            painter.drawImage(0, 0, img)
            painter.resetTransform()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 70))
            painter.drawPolygon(quad)
        else:
            painter.drawImage(0, 0, img)
        painter.restore()

    def _placa_de_pe(self, painter, ponto_tela: QPointF, anel: QColor):
        """(v0.73) A placa do nome DE PÉ na tela (câmera inclinada / standee): legível, em vez de deitada no chão."""
        painter.save()
        painter.resetTransform()
        fonte = QFont()
        fonte.setPixelSize(12)
        fonte.setBold(True)
        painter.setFont(fonte)
        larg = painter.fontMetrics().horizontalAdvance(self.nome) + 14
        placa = QRectF(ponto_tela.x() - larg / 2, ponto_tela.y(), larg, 20)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(18, 14, 11, 215))
        painter.drawRoundedRect(placa, 5, 5)
        painter.setPen(QPen(anel, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(placa, 5, 5)
        painter.setPen(QColor(236, 226, 205))
        painter.drawText(placa, Qt.AlignmentFlag.AlignCenter, self.nome)
        painter.restore()

    def _pintar_lateral_3d(self, painter, c: QRectF, anel: QColor):
        """Lateral da ficha (um cilindro baixo) e deixa o painter no plano do TOPO dela."""
        import math
        from . import camera3d
        # (v0.84) com a câmera e o token parados (a tocha tremendo redesenha a mesa ~10×/s), a geometria é a mesma:
        # guarda o contorno já projetado e só redesenha
        wt = painter.worldTransform()
        dev = painter.device()
        chave = (wt.m11(), wt.m12(), wt.m13(), wt.m21(), wt.m22(), wt.m23(), wt.m31(), wt.m32(), wt.m33(),
                 dev.width() if dev is not None else 0, dev.height() if dev is not None else 0,
                 camera3d.altura_telas(), camera3d.inclinacao(), c.x(), c.y(), c.width(), c.height())
        g = getattr(self, "_lateral_cache", None)
        if g is None or g[0] != chave:
            g = self._lateral_cache = (chave, self._geometria_lateral(camera3d.Camera(painter), c))
        geo = g[1]
        painter.save()
        painter.resetTransform()
        if geo[0] is not None:
            corpo, topo, p0, p1, claro_primeiro = geo[0]
            borda = QColor(anel).darker(240)
            lg = QLinearGradient(p0, p1)
            a, b = borda.lighter(185), borda.darker(150)
            lg.setColorAt(0.0, a if claro_primeiro else b)
            lg.setColorAt(0.5, borda)
            lg.setColorAt(1.0, b if claro_primeiro else a)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(lg))
            painter.drawPath(corpo)
            # filete de metal na quina de cima
            painter.setPen(QPen(QColor(anel).darker(140), 1.2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPolygon(topo)
        painter.restore()
        painter.setWorldTransform(geo[1])

    def _geometria_lateral(self, cam, c: QRectF):
        """(corpo, topo, ponta0 e ponta1 do degradê, claro_primeiro) ou None, e a transformação do topo."""
        import math
        from . import camera3d
        h = ESPESSURA_3D
        centro = c.center()
        c0, c1 = cam.projetar(centro, 0), cam.projetar(centro, h)
        r0 = c.width() / 2 * cam.escala
        dx, dy = c1.x() - c0.x(), c1.y() - c0.y()
        dist = math.hypot(dx, dy)
        desenho = None
        if dist > 0.3:
            nx, ny = -dy / dist, dx / dist   # perpendicular ao deslocamento
            from PyQt6.QtGui import QPolygonF
            raio = c.width() / 2
            import numpy as np
            ang = _ANGULOS_FICHA
            xs = np.concatenate([centro.x() + np.cos(ang) * raio] * 2)
            ys = np.concatenate([centro.y() + np.sin(ang) * raio] * 2)
            zs = np.concatenate([np.zeros(len(ang)), np.full(len(ang), h)])
            sx, sy, _f = cam.projetar_np(xs, ys, zs)
            xy = list(zip(sx.tolist(), sy.tolist()))
            corpo = QPainterPath()
            corpo.addPolygon(QPolygonF([QPointF(x, y) for x, y in _casco_xy(xy)]))
            corpo.closeSubpath()
            topo = QPolygonF([QPointF(x, y) for x, y in xy[len(ang):]])
            luz = camera3d.LUZ_2D
            claro_primeiro = (nx * luz[0] + ny * luz[1]) > 0
            desenho = (corpo, topo, QPointF(c0.x() + nx * r0, c0.y() + ny * r0),
                       QPointF(c0.x() - nx * r0, c0.y() - ny * r0), claro_primeiro)
        return desenho, cam.transformacao_topo(h)

    # ---------------------------------------------------------- informações
    def definir_info(self, chave, valor=None, vis=None):
        campo = self.info.setdefault(chave, {"v": None, "vis": "oculto"})
        if valor is not None:
            campo["v"] = valor
        if vis is not None:
            campo["vis"] = vis
        self.update()
        self._avisar_modificacao()

    def animado(self) -> bool:
        if self.efeito:
            return True
        from .efeitos3d import status_do_token   # (v0.79) condição com partículas (queimando, sangrando…)
        return bool(status_do_token(self))

    def definir_efeito(self, efeito: str):
        efeito = efeito or ""
        if efeito != self.efeito:
            self.efeito = efeito
            self._cache_efeito = {}
            self.update()
            self._avisar_modificacao()
            cena = self.scene()
            if cena is not None and hasattr(cena, "mesa_mudou"):
                cena.mesa_mudou.emit()

    def definir_estado(self, estado):
        if estado not in (None, "caido", "morto"):
            estado = None
        if estado != self.estado:
            self.estado = estado
            self.update()
            self._avisar_modificacao()

    def _desenhar_estado(self, painter, c, d):
        if not self.estado:
            return
        if self.estado == "morto":
            # escurece o token e põe a caveira
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(20, 18, 16, 150))
            painter.drawEllipse(c)
            from ..ui.icones import pixmap_cache
            lado = d * 0.5
            alvo = QRectF(c.center().x() - lado / 2, c.center().y() - lado / 2, lado, lado)
            painter.drawPixmap(alvo, pixmap_cache("caveira", "#ebe4d2", 96), QRectF(0, 0, 96, 96))
        else:
            # ✚ de ajuda: círculo branco com a cruz vermelha, no canto
            r = max(14.0, d * 0.34)
            selo = QRectF(c.right() - r * 0.75, c.top() - r * 0.25, r, r)
            painter.setPen(QPen(QColor(20, 16, 12), 2))
            painter.setBrush(QColor(250, 248, 242))
            painter.drawEllipse(selo)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(210, 40, 40))
            b = selo.width() * 0.2
            painter.drawRect(QRectF(selo.center().x() - b / 2, selo.top() + selo.height() * 0.2,
                                    b, selo.height() * 0.6))
            painter.drawRect(QRectF(selo.left() + selo.width() * 0.2, selo.center().y() - b / 2,
                                    selo.width() * 0.6, b))

    def definir_vez(self, da_vez: bool):
        if self.da_vez != da_vez:
            self.da_vez = da_vez
            self.update()

    def _desenhar_info(self, painter, c, d):
        from ..jogo.condicoes import CONDICOES
        # Destaque de quem é a vez
        if self.da_vez:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for largura, alfa in ((14, 50), (8, 110), (3, 255)):
                cor = QColor(255, 200, 60, alfa)
                painter.setPen(QPen(cor, largura))
                painter.drawEllipse(c.adjusted(-6, -6, 6, 6))
        # Barra de vida
        pv = self.info.get("pv")
        if pv and pv.get("v"):
            try:
                atual, maximo = float(pv["v"][0]), max(1.0, float(pv["v"][1]))
            except (TypeError, ValueError, IndexError):
                atual, maximo = 0, 1
            frac = max(0.0, min(1.0, atual / maximo))
            oculto = pv.get("vis") == "oculto" and self.ver_ocultos
            barra = QRectF(c.left() + 4, -9, c.width() - 8, 6)
            painter.setOpacity(0.55 if oculto else 1.0)
            painter.setPen(QPen(QColor(10, 8, 6), 1))
            painter.setBrush(QColor(30, 22, 18, 220))
            painter.drawRoundedRect(barra, 3, 3)
            cor = (QColor(90, 190, 90) if frac > 0.5 else
                   QColor(220, 180, 60) if frac > 0.25 else QColor(210, 60, 50))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(cor)
            painter.drawRoundedRect(QRectF(barra.left() + 1, barra.top() + 1,
                                           (barra.width() - 2) * frac, barra.height() - 2), 2, 2)
            painter.setOpacity(1.0)
        # Ícones das condições
        cond = self.info.get("condicoes")
        lista = [k for k in (cond.get("v") or []) if k in CONDICOES] if cond else []
        if lista:
            from ..ui.icones import pixmap_cache   # desenhos próprios (sem depender da fonte de emoji)
            oculto = cond.get("vis") == "oculto" and self.ver_ocultos
            tam = 20
            total = len(lista) * (tam + 2) - 2
            x0 = d / 2 - total / 2
            fonte = QFont()
            fonte.setPixelSize(13)
            painter.setFont(fonte)
            painter.setOpacity(0.5 if oculto else 1.0)
            for k, chave in enumerate(lista):
                r = QRectF(x0 + k * (tam + 2), -34, tam, tam)
                painter.setPen(QPen(QColor(201, 162, 74), 1))
                painter.setBrush(QColor(20, 16, 12, 230))
                painter.drawEllipse(r)
                # pixmap grande desenhado pequeno: fica nítido com zoom
                painter.drawPixmap(r.adjusted(4, 4, -4, -4), pixmap_cache(f"cond_{chave}", "#f0e6d2", 48),
                                   QRectF(0, 0, 48, 48))
                n = (cond.get("dur") or {}).get(chave)
                if n:
                    selo = QRectF(r.right() - 9, r.top() - 4, 12, 12)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor(201, 162, 74))
                    painter.drawEllipse(selo)
                    pequena = QFont()
                    pequena.setPixelSize(9)
                    pequena.setBold(True)
                    painter.setFont(pequena)
                    painter.setPen(QColor(20, 16, 12))
                    painter.drawText(selo, Qt.AlignmentFlag.AlignCenter, str(n) if n < 100 else "+")
                    painter.setFont(fonte)
            painter.setOpacity(1.0)

    def texto_dica(self) -> str:
        from ..jogo.condicoes import CONDICOES
        linhas = [f"<b>{self.nome}</b>" + {"morto": " · morto", "caido": " · caído"}.get(self.estado, "")]
        pv = self.info.get("pv")
        if pv and pv.get("v"):
            linhas.append(f"PV {pv['v'][0]}/{pv['v'][1]}")
        cond = self.info.get("condicoes")
        if cond and cond.get("v"):
            dur = cond.get("dur") or {}
            linhas.append(", ".join(f"{CONDICOES[k][0]}"
                                    + (f" ({dur[k]} rod.)" if k in dur else "")
                                    for k in cond["v"] if k in CONDICOES))
        for chave, rotulo in (("raca", "Raça"), ("classe", "Classe")):
            campo = self.info.get(chave)
            if campo and campo.get("v"):
                linhas.append(f"{rotulo}: {campo['v']}")
        return "<br>".join(linhas)

    def hoverEnterEvent(self, event):
        self.setToolTip(self.texto_dica())
        super().hoverEnterEvent(event)

    # ---------------------------------------------------------- salvar/abrir
    def para_dict(self) -> dict:
        return {
            "classe": "token",
            "id": self.uid,
            "visivel": self.isVisible(),
            "x": self.pos().x(),
            "y": self.pos().y(),
            "z": self.zValue(),
            "nome": self.nome,
            "tipo": self.tipo,
            "cor": self.cor.name(),
            "tamanho": self.tamanho,
            "dono": self.dono,
            "visao_alcance": self.visao_alcance,
            "visao_abertura": self.visao_abertura,
            "direcao": self.direcao,
            "pode_girar": self.pode_girar,
            "visao_escuro": self.visao_escuro,
            "info": self.info,
            "luz": self.luz,
            "estado": self.estado,
            "efeito": self.efeito,
            "estilo": self.estilo,
            "sem_borda": self.sem_borda,
            "escala_standee": self.escala_standee,
            "ficha": self.ficha,
            "srd": self.srd,
            "imagem": base64.b64encode(self.imagem).decode("ascii") if self.imagem else None,
            "retrato": base64.b64encode(self.retrato).decode("ascii") if self.retrato else None,
        }

    @classmethod
    def de_dict(cls, d: dict) -> "TokenItem":
        imagem = base64.b64decode(d["imagem"]) if d.get("imagem") else None
        item = cls(d["nome"], d.get("tipo", "criatura"), d.get("cor", "#7a4b3a"),
                   d.get("tamanho", 1), imagem, d.get("dono", ""))
        item.setPos(d["x"], d["y"])
        item.setZValue(d.get("z", 0))
        if d.get("retrato"):
            item.definir_retrato(base64.b64decode(d["retrato"]))
        item.visao_alcance = float(d.get("visao_alcance", 24))
        item.visao_abertura = float(d.get("visao_abertura", 60))
        if item.visao_abertura == 180.0 and item.visao_alcance == 24.0:   # (v0.71) o padrão antigo → o novo
            item.visao_abertura = 60.0
        item.direcao = float(d.get("direcao", 0))
        item.estilo = d.get("estilo") if d.get("estilo") in ("ficha", "standee") else "ficha"
        item.sem_borda = bool(d.get("sem_borda", False))
        item.escala_standee = escala_valida(d.get("escala_standee", 1.0))
        item.pode_girar = bool(d.get("pode_girar", True))
        item.visao_escuro = float(d.get("visao_escuro", 0))
        item.luz = d.get("luz")
        item.estado = d.get("estado")
        item.efeito = d.get("efeito") or ""
        item.ficha = d.get("ficha")
        item.srd = d.get("srd")
        if isinstance(d.get("info"), dict):
            from ..jogo.condicoes import info_vazia
            item.info = info_vazia()
            item.info.update(d["info"])
        item.setVisible(d.get("visivel", True))
        item.uid = d.get("id") or item.uid
        return item
