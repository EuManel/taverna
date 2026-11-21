"""
(v0.70) 🧭 BÚSSOLA da câmera livre — fica no canto de baixo à direita da mesa (mestre e jogador).

  • cadeado (em cima à esquerda): TRAVADA = reto de cima, como sempre · LIVRE = dá pra girar e inclinar
  • arrastar na bússola: pro lado GIRA, pra cima/baixo INCLINA (igual a Alt+arrastar na mesa)
  • rodinha do mouse em cima dela: inclina · setinhas ◀ ▶: giram 45° · clique duplo: volta pro reto de cima
  • a agulha aponta pro "norte" da mesa; o anel em volta mostra o quanto está inclinada
Cada pessoa mexe só na SUA câmera (nada vai pela rede).
"""

import math

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QRadialGradient
from PyQt6.QtWidgets import QWidget

LADO = 92


class Bussola(QWidget):
    def __init__(self, visao):
        super().__init__(visao)
        self.visao = visao
        self.setFixedSize(QSize(LADO, LADO))
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._arrasto = None
        self._sobre = None
        self._atualizar_dica()
        visao.camera_mudou.connect(self._mudou)
        self.show()

    # ------------------------------------------------------------ posição
    def reposicionar(self):
        vp = self.visao.viewport().geometry()
        self.move(vp.right() - LADO - 12, vp.bottom() - LADO - 12)
        self.raise_()

    def _mudou(self):
        self._atualizar_dica()
        self.update()

    def _atualizar_dica(self):
        v = self.visao
        if v.camera_livre:
            self.setToolTip(f"Câmera LIVRE — giro {v._cam_giro:.0f}°, inclinação {v._cam_incl:.0f}°\n"
                            "Arraste aqui (ou Alt+arrastar na mesa): pro lado gira, pra cima/baixo inclina.\n"
                            "Rodinha: inclina · ◀ ▶: giram 45° · clique duplo: reto de cima · cadeado: travar")
        else:
            self.setToolTip("Câmera TRAVADA (reto de cima). Clique no cadeado pra soltar e poder girar/inclinar.")

    # ------------------------------------------------------------ áreas clicáveis
    def _regiao(self, p: QPointF) -> str:
        if QRectF(0, 0, 26, 26).contains(p):
            return "cadeado"
        c = QPointF(LADO / 2, LADO / 2 + 4)
        if (p - c).manhattanLength() < 14:
            return "centro"
        if QRectF(0, LADO - 26, 24, 26).contains(p):
            return "esq"
        if QRectF(LADO - 24, LADO - 26, 24, 26).contains(p):
            return "dir"
        return "disco"

    def mousePressEvent(self, ev):
        r = self._regiao(ev.position())
        v = self.visao
        if r == "cadeado":
            v.definir_camera(livre=not v.camera_livre)
        elif not v.camera_livre:
            v.definir_camera(livre=True)   # mexeu na bússola travada: solta
        elif r == "esq":
            v.definir_camera(giro=v._cam_giro - 45)
        elif r == "dir":
            v.definir_camera(giro=v._cam_giro + 45)
        else:
            self._arrasto = ev.position()
        ev.accept()

    def mouseMoveEvent(self, ev):
        if self._arrasto is not None:
            d = ev.position() - self._arrasto
            self._arrasto = ev.position()
            self.visao._orbitar(QPointF(d.x() * 2.2, d.y() * 2.0))
        else:
            r = self._regiao(ev.position())
            if r != self._sobre:
                self._sobre = r
                self.update()
        ev.accept()

    def mouseReleaseEvent(self, ev):
        self._arrasto = None
        ev.accept()

    def mouseDoubleClickEvent(self, ev):
        self.visao.camera_de_cima()
        ev.accept()

    def wheelEvent(self, ev):
        v = self.visao
        if v.camera_livre:
            v.definir_camera(inclinacao=v._cam_incl + ev.angleDelta().y() / 120.0 * 5)
        ev.accept()

    def leaveEvent(self, ev):
        self._sobre = None
        self.update()

    # ------------------------------------------------------------ desenho
    def paintEvent(self, ev):
        from ..ui.tema import tema_atual
        t = tema_atual()
        dest = QColor(t["destaque"])
        texto = QColor(t["texto"])
        v = self.visao
        livre = v.camera_livre
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QPointF(LADO / 2, LADO / 2 + 4)
        R = LADO / 2 - 12
        # disco escuro com aro de metal
        g = QRadialGradient(c, R)
        g.setColorAt(0, QColor(30, 26, 22, 220))
        g.setColorAt(1, QColor(8, 7, 6, 230))
        p.setBrush(QBrush(g))
        p.setPen(QPen(dest.darker(140), 3))
        p.drawEllipse(c, R, R)
        p.setPen(QPen(dest, 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(c, R - 3, R - 3)
        # anel da inclinação (o quanto está deitada)
        from .camera3d import INCLINACAO_MAX
        incl = v._cam_incl if livre else 0.0
        if incl > 0.5:
            cor = QColor(dest)
            cor.setAlpha(200)
            p.setPen(QPen(cor, 4, cap=Qt.PenCapStyle.RoundCap))
            p.drawArc(QRectF(c.x() - R - 5, c.y() - R - 5, 2 * R + 10, 2 * R + 10), 90 * 16,
                      int(-360 * 16 * incl / INCLINACAO_MAX))
        # marquinhas
        p.setPen(QPen(texto, 1))
        giro = math.radians(v._cam_giro if livre else 0.0)
        for k in range(8):
            a = giro + k * math.pi / 4
            r0 = R - (8 if k % 2 == 0 else 5)
            p.drawLine(QPointF(c.x() + math.sin(a) * r0, c.y() - math.cos(a) * r0),
                       QPointF(c.x() + math.sin(a) * (R - 3), c.y() - math.cos(a) * (R - 3)))
        # agulha: norte da mesa (vermelho) e sul
        def ponta(ang, comp, cor):
            cam = QPainterPath()
            cam.moveTo(c.x() + math.sin(ang) * comp, c.y() - math.cos(ang) * comp)
            cam.lineTo(c.x() + math.sin(ang + math.pi / 2) * 5, c.y() - math.cos(ang + math.pi / 2) * 5)
            cam.lineTo(c.x() + math.sin(ang - math.pi / 2) * 5, c.y() - math.cos(ang - math.pi / 2) * 5)
            cam.closeSubpath()
            p.setPen(QPen(QColor(0, 0, 0, 160), 0.8))
            p.setBrush(cor)
            p.drawPath(cam)
        ponta(-giro + math.pi, R - 10, QColor(200, 196, 186))
        ponta(-giro, R - 10, QColor(214, 64, 52))
        fonte = QFont()
        fonte.setPixelSize(9)
        fonte.setBold(True)
        p.setFont(fonte)
        n = QPointF(c.x() + math.sin(-giro) * (R + 1), c.y() - math.cos(-giro) * (R + 1))
        p.setPen(QColor(255, 220, 200))
        p.drawText(QRectF(n.x() - 6, n.y() - 6, 12, 12), Qt.AlignmentFlag.AlignCenter, "N")
        # miolo: "de cima"
        p.setPen(QPen(dest, 1.4))
        p.setBrush(QColor(20, 16, 12) if self._sobre != "centro" else dest.darker(160))
        p.drawEllipse(c, 6, 6)
        # cadeado
        self._cadeado(p, QRectF(4, 4, 18, 18), livre, dest, texto)
        # setinhas de girar
        for x, sinal, reg in ((4, -1, "esq"), (LADO - 20, 1, "dir")):
            cor = dest if (self._sobre == reg and livre) else (texto if livre else QColor(texto.red(), texto.green(), texto.blue(), 90))
            seta = QPainterPath()
            y = LADO - 14
            if sinal < 0:
                seta.moveTo(x + 12, y - 6); seta.lineTo(x + 3, y); seta.lineTo(x + 12, y + 6)
            else:
                seta.moveTo(x + 4, y - 6); seta.lineTo(x + 13, y); seta.lineTo(x + 4, y + 6)
            p.setPen(QPen(cor, 2.2, cap=Qt.PenCapStyle.RoundCap, join=Qt.PenJoinStyle.RoundJoin))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(seta)
        p.end()

    @staticmethod
    def _cadeado(p, r: QRectF, aberto: bool, dest: QColor, texto: QColor):
        p.setBrush(QColor(14, 12, 10, 220))
        p.setPen(QPen(dest if aberto else texto, 1))
        p.drawRoundedRect(r, 4, 4)
        corpo = QRectF(r.x() + 4, r.y() + 8, r.width() - 8, r.height() - 11)
        p.setPen(QPen(dest if aberto else texto, 1.6))
        p.setBrush(Qt.BrushStyle.NoBrush)
        arco = QRectF(corpo.x() + 1.5, r.y() + 3, corpo.width() - 3, 9)
        if aberto:
            arco.translate(3, -1.5)
        p.drawArc(arco, 0, 180 * 16)
        p.setBrush(dest if aberto else texto)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(corpo, 1.5, 1.5)
