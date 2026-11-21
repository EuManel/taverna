"""
Luzes da mesa.

- LuzItem: uma fonte de luz (tocha, lampião, vela, fogueira, lâmpada, cristal, neon).
  A luz se espalha em volta e PARA NAS PAREDES (mesmo motor da linha de visão).
  Porta aberta deixa a luz passar; porta fechada segura.
- Cada aba tem uma luz ambiente: "dia" (tudo claro), "penumbra" ou "escuro".
- LuzOverlay: escurece a mesa conforme a luz ambiente e "acende" as áreas iluminadas,
  com um brilho colorido e tremulação nas chamas.
"""

import math
import random
import time
import uuid

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import (QBrush, QColor, QImage, QPainter, QPainterPath, QPen,
                         QPolygonF, QRadialGradient)
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsObject

from ..config import CELULA, COR_DESTAQUE, LIMITE_CENA
from .linha_de_visao import obstaculos, poligono

# tipo: (nome, raio forte m, raio fraco m, cor, tremula)
TIPOS_LUZ = {
    "tocha": ("Tocha", 4, 8, "#ffb050", True),
    "lampiao": ("Lampião", 5, 10, "#ffd27a", True),
    "vela": ("Vela", 1, 3, "#ffc070", True),
    "fogueira": ("Fogueira", 6, 12, "#ff9a3a", True),
    "lampada": ("Lâmpada", 6, 12, "#fff4dc", False),
    "cristal": ("Cristal brilhante", 3, 6, "#9fd8ff", False),
    "neon": ("Luz neon", 4, 8, "#38e1ff", False),
    "lareira": ("Lareira", 5, 10, "#ff9440", True),
    "lustre": ("Lustre", 7, 14, "#ffd890", True),
    "poste": ("Poste de luz", 6, 12, "#fff0c8", False),
    "braseiro": ("Braseiro", 4, 9, "#ff8a30", True),
    "candelabro": ("Candelabro", 3, 6, "#ffc878", True),
    "terminal": ("Brilho de tela", 1.5, 3, "#40ffb0", False),
    "lanterna": ("Lanterna de mão", 5, 10, "#ffd27a", True),
}

# Luzes que um token pode carregar (acompanha ele)
LUZES_DE_MAO = ["tocha", "lanterna", "vela", "cristal", "lampada"]


def luz_em(tipo: str, x: float, y: float, uid: str = "") -> dict:
    nome, forte, fraco, cor, tremula = TIPOS_LUZ.get(tipo, TIPOS_LUZ["tocha"])
    return {"classe": "luz", "id": uid, "x": x, "y": y, "tipo": tipo, "forte": forte, "fraco": fraco,
            "cor": cor, "tremula": tremula, "acesa": True, "visivel": True}


def luzes_extras(itens) -> list[dict]:
    # Luz que vem de props (lareira, lustre...) e de tokens carregando tocha/lanterna.
    # Aceita itens da mesa ou dicts da rede.
    lista = []
    for i in itens:
        if isinstance(i, dict):
            if i.get("classe") == "prop" and i.get("luz") and i.get("luz_acesa", True) \
                    and i.get("visivel", True) and i.get("cantos"):
                cx = sum(c[0] for c in i["cantos"]) / 4
                cy = sum(c[1] for c in i["cantos"]) / 4
                lista.append(luz_em(i["luz"], cx, cy, i["id"] + ":luz"))
            elif i.get("classe") == "token" and i.get("luz"):
                meio = i.get("tamanho", 1) * CELULA / 2
                lista.append(luz_em(i["luz"], i["x"] + meio, i["y"] + meio, i["id"] + ":luz"))
            elif i.get("classe") == "token" and i.get("efeito") in ("fogo", "luz", "eletrico"):
                from .efeitos import luz_de_efeito
                meio = i.get("tamanho", 1) * CELULA / 2
                lista.append(luz_de_efeito(i["efeito"], i["x"] + meio, i["y"] + meio, i["id"], 4))
            elif i.get("classe") == "prop" and i.get("efeito") in ("fogo", "luz", "eletrico") \
                    and i.get("visivel", True) and i.get("cantos"):
                from .efeitos import luz_de_efeito
                cx = sum(c[0] for c in i["cantos"]) / 4
                cy = sum(c[1] for c in i["cantos"]) / 4
                lista.append(luz_de_efeito(i["efeito"], cx, cy, i["id"], 5))
            elif i.get("classe") == "efeito":
                from .efeitos import luz_de_dict
                d = luz_de_dict(i)
                if d:
                    lista.append(d)
        else:
            if hasattr(i, "luz_dict"):
                d = i.luz_dict()
                if d:
                    lista.append(d)
            elif getattr(i, "luz", None) and i.isVisible():
                c = i.centro_cena()
                lista.append(luz_em(i.luz, c.x(), c.y(), i.uid + ":luz"))
            if not isinstance(i, dict) and not hasattr(i, "efeito_area") and i.isVisible() \
                    and getattr(i, "efeito", "") in ("fogo", "luz", "eletrico") \
                    and not (hasattr(i, "luz_dict") and i.luz_dict()):
                from .efeitos import luz_de_efeito
                c = i.centro_cena()
                lista.append(luz_de_efeito(i.efeito, c.x(), c.y(), i.uid + ":ef", 4 if hasattr(i, "dono") else 5))
    return lista

AMBIENTES = {
    "dia": ("☀  Dia (tudo claro)", 0),
    "penumbra": ("🌗  Penumbra", 130),
    "escuro": ("🌑  Escuro total", 240),
}


class LuzItem(QGraphicsObject):
    def __init__(self, tipo: str = "tocha"):
        super().__init__()
        self.uid = uuid.uuid4().hex
        nome, forte, fraco, cor, tremula = TIPOS_LUZ.get(tipo, TIPOS_LUZ["tocha"])
        self.tipo = tipo
        self.raio_forte = float(forte)
        self.raio_fraco = float(fraco)
        self.cor = QColor(cor)
        self.tremula = tremula
        self.acesa = True
        self.travado = False
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable
                      | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
                      | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    @property
    def nome(self):
        estado = "" if self.acesa else " (apagada)"
        return f"{TIPOS_LUZ.get(self.tipo, ('Luz',))[0]}{estado}"

    def boundingRect(self) -> QRectF:
        return QRectF(-16, -16, 32, 32)

    def shape(self) -> QPainterPath:
        cam = QPainterPath()
        cam.addEllipse(QRectF(-12, -12, 24, 24))
        return cam

    icone_oculto = False   # (v0.48) no jogador: a luz ilumina, mas o desenho do ponto não aparece

    def paint(self, painter: QPainter, option, widget=None):
        if self.icone_oculto:
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cor = QColor(self.cor) if self.acesa else QColor("#5a5550")
        if self.acesa:
            brilho = QRadialGradient(QPointF(0, 0), 15)
            c1 = QColor(cor)
            c1.setAlpha(200)
            c2 = QColor(cor)
            c2.setAlpha(0)
            brilho.setColorAt(0, c1)
            brilho.setColorAt(1, c2)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(brilho))
            painter.drawEllipse(QRectF(-15, -15, 30, 30))
        painter.setPen(QPen(QColor(20, 14, 8), 1.5))
        painter.setBrush(QColor(40, 30, 20))
        painter.drawEllipse(QRectF(-8, -8, 16, 16))
        # chaminha / lampadazinha
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(cor)
        if self.tipo in ("lampada", "neon", "cristal"):
            painter.drawEllipse(QRectF(-4.5, -4.5, 9, 9))
        else:
            chama = QPainterPath(QPointF(0, -6))
            chama.cubicTo(QPointF(5, -1), QPointF(4, 5), QPointF(0, 5))
            chama.cubicTo(QPointF(-4, 5), QPointF(-5, -1), QPointF(0, -6))
            painter.drawPath(chama)
        if self.isSelected():
            caneta = QPen(QColor(COR_DESTAQUE), 1.5, Qt.PenStyle.DashLine)
            caneta.setCosmetic(True)
            painter.setPen(caneta)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(0, 0), self.raio_fraco * CELULA, self.raio_fraco * CELULA)
            painter.drawEllipse(QPointF(0, 0), self.raio_forte * CELULA, self.raio_forte * CELULA)

    # ------------------------------------------------------------ edição
    def mudou(self):
        self.prepareGeometryChange()
        self.update()
        cena = self.scene()
        if cena is not None and hasattr(cena, "marcar_modificada"):
            cena.marcar_modificada()
            if hasattr(cena, "camadas_mudaram"):
                cena.camadas_mudaram.emit()

    def alternar(self):
        self.acesa = not self.acesa
        self.mudou()

    def aplicar_trava(self, travado):
        self.travado = travado
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not travado)

    def mouseDoubleClickEvent(self, event):
        self.alternar()
        event.accept()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            cena = self.scene()
            if cena is not None and hasattr(cena, "marcar_modificada"):
                cena.marcar_modificada()
        return super().itemChange(change, value)

    # ------------------------------------------------------------ dados
    def para_dict(self) -> dict:
        p = self.pos()
        return {"classe": "luz", "id": self.uid, "x": p.x(), "y": p.y(), "z": self.zValue(),
                "tipo": self.tipo, "forte": self.raio_forte, "fraco": self.raio_fraco,
                "cor": self.cor.name(), "tremula": self.tremula, "acesa": self.acesa,
                "visivel": self.isVisible()}

    def aplicar_dict(self, d: dict):
        self.tipo = d.get("tipo", "tocha")
        self.raio_forte = float(d.get("forte", 4))
        self.raio_fraco = float(d.get("fraco", 8))
        self.cor = QColor(d.get("cor", "#ffb050"))
        self.tremula = bool(d.get("tremula", True))
        self.acesa = bool(d.get("acesa", True))
        self.update()

    @classmethod
    def de_dict(cls, d: dict) -> "LuzItem":
        item = cls(d.get("tipo", "tocha"))
        item.aplicar_dict(d)
        item.uid = d.get("id") or item.uid
        item.setPos(d.get("x", 0), d.get("y", 0))
        item.setZValue(d.get("z", 0))
        item.setVisible(d.get("visivel", True))
        return item


# ====================================================================== cálculo
def luzes_acesas(dicts_ou_itens):
    """Normaliza pra lista de dicts das luzes acesas e visíveis."""
    lista = []
    for l in dicts_ou_itens:
        d = l if isinstance(l, dict) else l.para_dict()
        if not d.get("acesa", True) or not d.get("visivel", True):
            continue
        if not isinstance(l, dict):   # posição na mesa (o item mora dentro de uma camada)
            p = l.scenePos()
            d["x"], d["y"] = p.x(), p.y()
        lista.append(d)
    return lista


def poligonos_de_luz(luzes: list[dict], obst: list) -> list[tuple]:
    """[(dict da luz, polígono até o raio fraco)]"""
    return [(d, poligono(d["x"], d["y"], 0, 360, d["fraco"], obst)) for d in luzes]


def iluminar_objetos(polys_luz, props) -> list:
    # Objeto que bloqueia a luz (pilar, estátua...) recebe a luz que bate nele,
    # senão o chão embaixo dele fica escuro.
    extra = []
    for p in props:
        if isinstance(p, dict):
            if not p.get("bloqueia") or not p.get("cantos"):
                continue
            cantos = [QPointF(c[0], c[1]) for c in p["cantos"]]
        else:
            if not getattr(p, "bloqueia", False) or not p.isVisible():
                continue
            cantos = p.cantos_cena()
        cx = sum(c.x() for c in cantos) / 4
        cy = sum(c.y() for c in cantos) / 4
        for d, _pol in polys_luz:
            if math.hypot(d["x"] - cx, d["y"] - cy) < d["fraco"] * CELULA:
                extra.append((d, QPolygonF(cantos)))
    return polys_luz + extra


def ponto_iluminado(polys_luz, x, y) -> bool:
    p = QPointF(x, y)
    for d, pol in polys_luz:
        if pol.containsPoint(p, Qt.FillRule.OddEvenFill):
            return True
    return False


def gradiente_luz(d, fator=1.0, revelar=True, alfa_cor=60):
    """Gradiente radial: forte no centro, sumindo até o raio fraco."""
    raio = max(1.0, d["fraco"] * CELULA * fator)
    g = QRadialGradient(QPointF(d["x"], d["y"]), raio)
    frac_forte = max(0.0, min(0.95, d["forte"] / max(0.01, d["fraco"])))
    brilho = float(d.get("brilho", 1.0))   # luz passageira apagando (estouro, flash) — luz_dinamica
    if revelar:
        # cai suave (como luz de verdade), em vez de um degrau
        g.setColorAt(0, QColor(0, 0, 0, int(255 * brilho)))
        g.setColorAt(frac_forte * 0.85, QColor(0, 0, 0, int(255 * brilho)))
        resto = 1 - frac_forte * 0.85
        for f in (0.25, 0.5, 0.75):
            g.setColorAt(frac_forte * 0.85 + resto * f, QColor(0, 0, 0, int(255 * brilho * (1 - f) ** 1.7)))
        g.setColorAt(1, QColor(0, 0, 0, 0))
    else:
        if "brilho" in d:   # luz passageira: o clarão brilha mais que uma tocha e vai apagando
            alfa_cor = min(255, int(alfa_cor * (0.3 + 1.9 * brilho)))
        cor = QColor(d["cor"])
        c0 = QColor(cor)
        c0.setAlpha(alfa_cor)
        c1 = QColor(cor)
        c1.setAlpha(0)
        g.setColorAt(0, c0)
        g.setColorAt(frac_forte, QColor(cor.red(), cor.green(), cor.blue(), int(alfa_cor * 0.6)))
        g.setColorAt(1, c1)
    return g


# ====================================================================== desenho
class LuzOverlay(QGraphicsItem):
    """
    Escurece a mesa conforme a luz ambiente e acende as áreas iluminadas.
    - No mestre: escurece só um pouco (ele precisa ver tudo), como prévia.
    - No player sem névoa: escurece de verdade.
    - No player com névoa: só desenha o brilho colorido (a névoa cuida do escuro).
    """

    def __init__(self, cena, limite_escuro: int = 255):
        super().__init__()
        self.cena = cena
        self.limite_escuro = limite_escuro   # o mestre usa ~150 pra continuar enxergando
        self.so_brilho = False
        self.ambiente = "dia"
        self.luzes = []          # [(dict, polígono)]
        self._fase = 0.0
        self.setZValue(850_000)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemUsesExtendedStyleOption, True)
        self._timer = QTimer()
        self._timer.setInterval(90)
        self._timer.timeout.connect(self._tremular)

    def boundingRect(self) -> QRectF:
        L = LIMITE_CENA
        from .camera3d import limitar
        return limitar(self, QRectF(-L, -L, 2 * L, 2 * L))   # (v0.70) câmera inclinada: só o chão visível

    def shape(self) -> QPainterPath:
        return QPainterPath()

    def definir(self, ambiente: str, luzes_com_poligono: list):
        self.ambiente = ambiente
        self.luzes = luzes_com_poligono
        if any(d.get("tremula") for d, _ in self.luzes):
            if not self._timer.isActive():
                self._timer.start()
        else:
            self._timer.stop()
        self.update()

    def _tremular(self):
        self._fase = time.monotonic()
        self.update()

    def _fator(self, d):
        if not d.get("tremula"):
            return 1.0
        semente = (hash(d.get("id", "")) % 100) / 10
        t = self._fase
        return 0.95 + 0.035 * math.sin(t * 9.1 + semente) + 0.02 * math.sin(t * 17.3 + semente * 2)

    def paint(self, painter: QPainter, option, widget=None):
        escuro = min(self.limite_escuro, AMBIENTES.get(self.ambiente, ("", 0))[1])
        if escuro <= 0 and not self.luzes:
            return
        from ..graficos import nivel as _nivel
        n = _nivel()
        transf = painter.worldTransform()
        area = transf.mapRect(option.exposedRect).toAlignedRect()
        dev = painter.device()
        if dev is not None:   # nunca maior que a tela (desenhar a cena inteira de uma vez pedia uma imagem gigante)
            from PyQt6.QtCore import QRect
            area = area.intersected(QRect(0, 0, dev.width(), dev.height()))
        if area.isEmpty():
            return
        # (v0.47) a imagem de luz/sombra só muda com câmera, luzes, tremulação ou ambiente: reaproveita
        chave = (transf.m11(), transf.m12(), transf.m21(), transf.m22(), transf.dx(), transf.dy(),
                 transf.m13(), transf.m23(), transf.m33(),
                 area.x(), area.y(), area.width(), area.height(), self._fase, escuro, self.so_brilho, n,
                 __import__("taverna.mesa.camera3d", fromlist=["x"]).em_movimento())   # (v0.76) leve ≠ completa
        guardado = getattr(self, "_img_cache", None)
        if guardado is not None and guardado[0] == chave and guardado[1] is self.luzes:
            visiveis = guardado[3]
            painter.save()
            painter.resetTransform()
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawImage(QRectF(area), guardado[2])
            painter.restore()
            self._somar_cor(painter, visiveis, escuro, n)
            return
        # (v0.76) a imagem de luz/sombra é MACIA: feita na metade da resolução e ampliada (1/4 do trabalho por
        # quadro — com a câmera girando ela é refeita todo quadro)
        from . import camera3d as _c3
        mexendo = _c3.em_movimento()
        meia = 0.34 if mexendo else 0.5   # (v0.76) câmera mexendo: ainda mais leve
        from PyQt6.QtCore import QSize
        imagem = QImage(QSize(max(1, int(area.width() * meia)), max(1, int(area.height() * meia))),
                        QImage.Format.Format_ARGB32_Premultiplied)
        imagem.fill(QColor(0, 0, 0, 0 if self.so_brilho else escuro))
        p = QPainter(imagem)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.scale(meia, meia)
        p.translate(-area.topLeft().x(), -area.topLeft().y())
        p.setWorldTransform(transf, True)
        p.setPen(Qt.PenStyle.NoPen)
        # (v0.47) só as luzes que aparecem na tela; e cada uma pinta DIRETO o polígono dela com o degradê
        # (o degradê some no raio, então é igual a recortar o círculo pelo polígono — sem o clip, que é caro)
        visiveis = []
        vis = option.exposedRect
        for d, pol in self.luzes:
            r_luz = d["fraco"] * CELULA * 1.05
            if vis.intersects(QRectF(d["x"] - r_luz, d["y"] - r_luz, 2 * r_luz, 2 * r_luz)):
                visiveis.append((d, pol))
        for d, pol in visiveis:
            fator = self._fator(d)
            if not self.so_brilho and escuro > 0:
                # "Acende": tira a escuridão onde a luz chega
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
                p.setBrush(QBrush(gradiente_luz(d, fator, revelar=True)))
                p.drawPolygon(pol)
            # Brilho colorido
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            p.setBrush(QBrush(gradiente_luz(d, fator, revelar=False,
                                            alfa_cor=70 if escuro > 0 else 35)))
            p.drawPolygon(pol)
            if n == 2 and not self.so_brilho and escuro > 0 and not mexendo:
                caminho = QPainterPath()
                caminho.addPolygon(pol)
                # penumbra: a borda da sombra fica macia
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
                p.setBrush(Qt.BrushStyle.NoBrush)
                pincel = QBrush(gradiente_luz(d, fator, revelar=True))   # só até onde a luz alcança
                for larg, opac in ((16, 0.16), (8, 0.26)):
                    p.setOpacity(opac)
                    p.setPen(QPen(pincel, larg, Qt.PenStyle.SolidLine,
                                  Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                    p.drawPath(caminho)
                p.setOpacity(1.0)
                p.setPen(Qt.PenStyle.NoPen)
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        p.end()
        self._img_cache = (chave, self.luzes, imagem, visiveis)
        painter.save()
        painter.resetTransform()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawImage(QRectF(area), imagem)
        painter.restore()
        self._somar_cor(painter, visiveis, escuro, n)

    def _somar_cor(self, painter, visiveis, escuro, n):
        if n >= 1 and visiveis:
            # a luz "soma" cor no que ilumina (chão e paredes ficam quentes perto da tocha)
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
            forca = (34 if escuro > 0 else 14) * (1.0 if n == 1 else 1.35)
            for d, pol in visiveis:
                fator = self._fator(d)
                cor = QColor(d["cor"])
                centro = QPointF(d["x"], d["y"])
                raio = d["fraco"] * CELULA * fator
                g = QRadialGradient(centro, raio)
                g.setColorAt(0, QColor(cor.red(), cor.green(), cor.blue(), int(forca * 1.5)))
                g.setColorAt(0.35, QColor(cor.red(), cor.green(), cor.blue(), int(forca * 0.7)))
                g.setColorAt(1, QColor(cor.red(), cor.green(), cor.blue(), 0))
                painter.setBrush(QBrush(g))
                painter.drawPolygon(pol)
                if n == 2:   # miolo bem claro, pertinho da fonte
                    r2 = min(raio, CELULA * 0.9) * fator
                    g2 = QRadialGradient(centro, r2)
                    g2.setColorAt(0, QColor(255, 244, 220, 70))
                    g2.setColorAt(1, QColor(255, 244, 220, 0))
                    painter.setBrush(QBrush(g2))
                    painter.drawPolygon(pol)
            painter.restore()
