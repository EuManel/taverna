"""
Névoa de guerra e cones de visão desenhados na mesa.

- ConesDoMestre: na tela do mestre, mostra (se ele quiser) o que cada jogador está vendo.
- NevoaItem: na tela do player, cobre tudo que os tokens dele NÃO veem.
  O que ele já viu antes fica na penumbra (dá pra ver chão e paredes, mas não criaturas).
"""

import math

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsItem

from ..config import CELULA, LIMITE_CENA
from .linha_de_visao import caminho_da_visao, obstaculos, poligono

# (v0.49) A memória do que já foi visto é uma IMAGEM em ladrilhos (só onde o jogador andou), com o formato
# exato do cone. Antes era de meio em meio metro e a borda do cone na diagonal ficava em "quadradinhos".
LADRILHO_M = 32          # cada ladrilho cobre 32 × 32 m
PX_POR_M = 8             # 8 pixels por metro (borda lisa; ~64 KB por ladrilho)
LADO_LADRILHO = LADRILHO_M * CELULA
PENUMBRA_ALFA = 170      # quanto a névoa fica no que já foi explorado (0 = some, 255 = cobre)


def visoes_dos_tokens(tokens, segmentos_parede, portas):
    """{token: QPolygonF} pra cada token de jogador."""
    obst = obstaculos(segmentos_parede, portas)
    resultado = {}
    for t in tokens:
        c = t.centro_cena()
        resultado[t] = poligono(c.x(), c.y(), t.direcao, t.visao_abertura, t.visao_alcance, obst)
    return resultado


class ConesDoMestre(QGraphicsItem):
    """Mostra os cones de visão dos jogadores pro mestre (liga/desliga no menu Mesa)."""

    def __init__(self, cena):
        super().__init__()
        self.cena = cena
        self.poligonos = []   # [(QPolygonF, QColor)]
        self.setZValue(800_000)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self.recalcular)

    def boundingRect(self) -> QRectF:
        L = LIMITE_CENA
        from .camera3d import limitar
        return limitar(self, QRectF(-L, -L, 2 * L, 2 * L))   # (v0.70) câmera inclinada: só o chão visível

    def shape(self) -> QPainterPath:
        return QPainterPath()

    def agendar(self):
        if self.isVisible() and not self._timer.isActive():
            self._timer.start()

    def recalcular(self):
        cena = self.cena
        tokens = [t for t in cena.tokens_com_visao() if t.isVisible()]
        camada = cena.camada_por_tipo("paredes")
        portas = [p for p in camada.itens()] if camada and camada.isVisible() else []
        portas += cena.props_visiveis()
        segs = cena.paredes.segmentos if cena.paredes and camada and camada.isVisible() else {}
        visoes = visoes_dos_tokens(tokens, segs, portas)
        self.poligonos = [(pol, t.cor_anel()) for t, pol in visoes.items()]
        self.update()

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for pol, cor in self.poligonos:
            preenchimento = QColor(cor)
            preenchimento.setAlpha(38)
            borda = QPen(QColor(cor), 1.5, Qt.PenStyle.DashLine)
            borda.setCosmetic(True)
            painter.setPen(borda)
            painter.setBrush(preenchimento)
            painter.drawPolygon(pol)


class NevoaItem(QGraphicsItem):
    """
    A névoa de guerra na tela do player (já levando a LUZ em conta).

    Desenho (sem operações de "recortar" caminhos, que falham com formas complicadas):
      1. pinta uma imagem do tamanho da tela toda com a cor da névoa (opaca);
      2. nas áreas JÁ EXPLORADAS, troca por névoa meio transparente (penumbra);
      3. dentro do cone de cada token meu:
           - dia: limpa tudo;
           - penumbra: deixa meio escuro e limpa onde tem luz;
           - escuro: só limpa onde tem luz (e um pouco na visão no escuro);
      4. cola essa imagem na tela.
    """

    def __init__(self):
        super().__init__()
        self.ativa = False
        self.cor = QColor("#0f0d0b")
        self.ambiente = "dia"
        self.visoes = []                     # [(cone, polígono da visão no escuro)]
        self.luzes = []                      # [(dict, polígono)]
        self.meus_circulos = []              # meus próprios tokens (sempre aparecem)
        self.explorado: dict = {}             # (i, j) do ladrilho → QImage Alpha8 (255 = já visto)
        self.setZValue(900_000)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemUsesExtendedStyleOption, True)
        self.setVisible(False)

    def boundingRect(self) -> QRectF:
        L = LIMITE_CENA
        from .camera3d import limitar
        return limitar(self, QRectF(-L, -L, 2 * L, 2 * L))   # (v0.70) câmera inclinada: só o chão visível

    def shape(self) -> QPainterPath:
        return QPainterPath()

    def esquecer(self):
        """Cenário novo: esquece o que já foi explorado."""
        self.explorado.clear()

    def _ve_o_ponto(self, ponto, escuro_pol) -> bool:
        if self.ambiente != "escuro":
            return True
        if escuro_pol is not None and not escuro_pol.isEmpty() and \
                escuro_pol.containsPoint(ponto, Qt.FillRule.OddEvenFill):
            return True
        return any(pol.containsPoint(ponto, Qt.FillRule.OddEvenFill) for _, pol in self.luzes)

    def atualizar(self, visoes, luzes=None, ambiente="dia"):
        self.visoes = [(c, e) for c, e in visoes if not c.isEmpty()]
        self.luzes = luzes or []
        self.ambiente = ambiente
        for cone, escuro in self.visoes:
            self._gravar_explorado(cone, escuro)
        self.update()

    def _ladrilho(self, i, j):
        from PyQt6.QtGui import QImage
        img = self.explorado.get((i, j))
        if img is None:
            lado = LADRILHO_M * PX_POR_M
            img = QImage(lado, lado, QImage.Format.Format_Alpha8)
            img.fill(0)
            self.explorado[(i, j)] = img
        return img

    def _gravar_explorado(self, cone, escuro):
        """Pinta o que este cone vê agora na memória (de dia: o cone todo; no escuro: só onde tem luz ou
        visão no escuro, dentro do cone)."""
        r = cone.boundingRect()
        if r.isEmpty():
            return
        cheio = QColor(0, 0, 0, 255)
        caminho_cone = QPainterPath()
        caminho_cone.addPolygon(cone)
        for i in range(math.floor(r.left() / LADO_LADRILHO), math.floor(r.right() / LADO_LADRILHO) + 1):
            for j in range(math.floor(r.top() / LADO_LADRILHO), math.floor(r.bottom() / LADO_LADRILHO) + 1):
                img = self._ladrilho(i, j)
                p = QPainter(img)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                esc = PX_POR_M / CELULA
                p.scale(esc, esc)
                p.translate(-i * LADO_LADRILHO, -j * LADO_LADRILHO)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(cheio)
                if self.ambiente != "escuro":
                    p.drawPolygon(cone)
                else:
                    p.setClipPath(caminho_cone)
                    if escuro is not None and not escuro.isEmpty():
                        p.drawPolygon(escuro)
                    for _d, pol in self.luzes:
                        p.drawPolygon(pol)
                p.end()

    def paint(self, painter: QPainter, option, widget=None):
        if not self.ativa:
            return
        from PyQt6.QtGui import QBrush, QImage
        from .luzes import gradiente_luz
        transf = painter.worldTransform()
        area = transf.mapRect(option.exposedRect).toAlignedRect()
        if area.isEmpty():
            return
        # QImage com canal alfa (um QPixmap opaco não deixaria "apagar" a névoa)
        imagem = QImage(area.size(), QImage.Format.Format_ARGB32_Premultiplied)
        cor = QColor(self.cor)
        cor.setAlpha(255)
        imagem.fill(cor)
        p = QPainter(imagem)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(-area.topLeft().x(), -area.topLeft().y())
        p.setWorldTransform(transf, True)
        p.setPen(Qt.PenStyle.NoPen)
        Modo = QPainter.CompositionMode

        # 1) Penumbra: o que já foi explorado (a memória tira um terço da névoa, com a borda lisa)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setCompositionMode(Modo.CompositionMode_DestinationOut)
        p.setOpacity(1 - PENUMBRA_ALFA / 255)
        vis = option.exposedRect
        for (i, j), img in self.explorado.items():
            alvo = QRectF(i * LADO_LADRILHO, j * LADO_LADRILHO, LADO_LADRILHO, LADO_LADRILHO)
            if alvo.intersects(vis):
                p.drawImage(alvo, img)
        p.setOpacity(1.0)

        # 2) Dentro de cada cone
        for cone, escuro in self.visoes:
            caminho_cone = QPainterPath()
            caminho_cone.addPolygon(cone)
            p.save()
            p.setClipPath(caminho_cone)
            if self.ambiente == "dia":
                p.setCompositionMode(Modo.CompositionMode_Clear)
                p.setBrush(QColor(0, 0, 0))
                p.drawPolygon(cone)
            else:
                if self.ambiente == "penumbra":
                    meio = QColor(self.cor)
                    meio.setAlpha(120)
                    p.setCompositionMode(Modo.CompositionMode_Source)
                    p.setBrush(meio)
                    p.drawPolygon(cone)
                elif escuro is not None and not escuro.isEmpty():
                    # visão no escuro: enxerga, mas apagadinho
                    vista = QColor(self.cor)
                    vista.setAlpha(95)
                    p.setCompositionMode(Modo.CompositionMode_Source)
                    p.setBrush(vista)
                    p.drawPolygon(escuro)
                # onde a luz chega, clareia
                p.setCompositionMode(Modo.CompositionMode_DestinationOut)
                for d, pol in self.luzes:
                    caminho_luz = QPainterPath()
                    caminho_luz.addPolygon(pol)
                    p.save()
                    p.setClipPath(caminho_luz, Qt.ClipOperation.IntersectClip)
                    p.setBrush(QBrush(gradiente_luz(d, 1.0, revelar=True)))
                    r = d["fraco"] * CELULA
                    p.drawEllipse(QPointF(d["x"], d["y"]), r, r)
                    p.restore()
            p.restore()

        # 3) Meus tokens sempre aparecem
        p.setCompositionMode(Modo.CompositionMode_Clear)
        p.setBrush(QColor(0, 0, 0))
        for r in self.meus_circulos:
            p.drawEllipse(r)
        p.end()
        painter.save()
        painter.resetTransform()
        painter.drawImage(area.topLeft(), imagem)
        painter.restore()
        self._ultima = (imagem, area.topLeft(), transf)   # (v0.70) o 3D consulta (amostrar / pintar_no_plano)

    # ---------------------------------------------------------------- (v0.70) névoa no 3D
    # A névoa é "tinta no chão". Com a câmera inclinada, o alto de uma parede cai na tela em cima do chão de TRÁS
    # dela — pegava a névoa do lugar errado (e o topo de parede de sala não explorada aparecia). Então o corpo 3D
    # consulta a névoa do PÉ dele (amostrar) e o topo das paredes recebe a névoa do chão logo embaixo (pintar_no_plano).
    # (Usa a imagem do quadro anterior: o 3D é desenhado antes da névoa — 1 quadro de atraso, não dá pra ver.)
    def amostrar(self, ponto_tela: QPointF) -> float:
        """0 = limpo · 1 = coberto, no ponto do CHÃO que aparece em `ponto_tela`."""
        ult = getattr(self, "_ultima", None)
        if ult is None or not self.ativa:
            return 0.0
        img, tl, _transf = ult
        x, y = int(ponto_tela.x() - tl.x()), int(ponto_tela.y() - tl.y())
        if x < 0 or y < 0 or x >= img.width() or y >= img.height():
            return 1.0 if not self.explorado else 0.65
        return img.pixelColor(x, y).alphaF()

    def pintar_no_plano(self, painter: QPainter, plano):
        """Cola a névoa do chão num plano mais alto (`plano` = transformação cena → tela daquela altura)."""
        ult = getattr(self, "_ultima", None)
        if ult is None or not self.ativa:
            return
        img, tl, transf = ult
        inv, ok = transf.inverted()
        if not ok:
            return
        painter.save()
        painter.setWorldTransform(inv * plano)
        painter.drawImage(tl, img)
        painter.restore()