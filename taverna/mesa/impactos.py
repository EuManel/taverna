"""
💥 Efeitos de impacto (acabamento): coisas rápidas que o mestre dispara na hora que quiser.

  No mapa:  explosão · raio · onda de choque · clarão arcano · desabamento
  Na tela:  tremor (terremoto) · clarão · apagão

Cada um combina um desenho animado no lugar + um efeito na tela de todo mundo
(a tela TREME na explosão, CLAREIA no raio…). Cada pessoa pode desligar o tremor e o clarão
em Gráficos, e o nível Baixo/Médio/Alto muda a quantidade de partículas.
"""

import math
import random
import time

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF, QRadialGradient
from PyQt6.QtWidgets import QGraphicsObject

from ..config import CELULA

# chave: (nome, precisa de um ponto no mapa?, duração em segundos)
IMPACTOS = {
    "explosao": ("💥 Explosão", True, 1.7),
    "raio": ("⚡ Raio", True, 0.9),
    "onda": ("🌀 Onda de choque", True, 0.9),
    "arcano": ("🔮 Clarão arcano", True, 1.3),
    "desabamento": ("🪨 Desabamento / poeira", True, 2.4),
    "tremor": ("📳 Tremor (terremoto)", False, 2.2),
    "clarao": ("✨ Clarão na tela", False, 0.6),
    "apagao": ("🌑 Apagão (tela escurece)", False, 1.8),
}
TAMANHO_PADRAO = 3.0   # metros (raio da explosão etc.)


def _suave(f):   # começa rápido e vai parando
    f = max(0.0, min(1.0, f))
    return 1 - (1 - f) ** 3


def _cor(r, g, b, a):
    return QColor(int(r), int(g), int(b), max(0, min(255, int(a))))


class ImpactoItem(QGraphicsObject):
    """O desenho animado no mapa. Some sozinho quando termina."""

    def __init__(self, tipo: str, tam_m: float = TAMANHO_PADRAO):
        super().__init__()
        from ..graficos import nivel
        self._cam = None
        self._base = None
        self.tipo = tipo
        self.n = nivel()
        self.R = max(0.5, float(tam_m)) * CELULA
        self.dur = IMPACTOS.get(tipo, ("", True, 1.2))[2]
        self.t0 = time.monotonic()
        self.setZValue(940_000)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        rnd = random.Random()
        qtd = (10, 26, 54)[self.n]
        # partículas: (ângulo, velocidade, tamanho, sorte)
        self.parts = [(rnd.uniform(0, 6.283), rnd.uniform(0.35, 1.0), rnd.uniform(0.5, 1.0), rnd.random())
                      for _ in range(qtd)]
        self.bolas = [(rnd.uniform(0, 6.283), rnd.uniform(0.1, 0.55), rnd.uniform(0.45, 0.8)) for _ in range((3, 6, 9)[self.n])]
        self.raio_pts, self.ramos = self._tracar_raio(rnd) if tipo == "raio" else ([], [])
        self._timer = QTimer(self)
        self._timer.setInterval((50, 33, 22)[self.n])
        self._timer.timeout.connect(self._passo)
        self._timer.start()

    def _tracar_raio(self, rnd):
        altura = 13 * CELULA
        x, y = rnd.uniform(-2.5, 2.5) * CELULA, -altura
        pts = [QPointF(x, y)]
        ramos = []
        passos = 16
        for k in range(1, passos + 1):
            alvo_x = x + (0 - x) * (1 / (passos - k + 1))
            x = alvo_x + (rnd.uniform(-0.55, 0.55) * CELULA if k < passos else 0)
            y = -altura + altura * k / passos
            pts.append(QPointF(x, y))
            if self.n >= 1 and k < passos - 2 and rnd.random() < 0.38:
                bx, by, lado = x, y, rnd.choice((-1, 1))
                ramo = [QPointF(bx, by)]
                for _ in range(rnd.randint(2, 4)):
                    bx += lado * rnd.uniform(0.3, 0.9) * CELULA
                    by += rnd.uniform(0.3, 0.9) * CELULA
                    ramo.append(QPointF(bx, by))
                ramos.append(QPolygonF(ramo))
        pts[-1] = QPointF(0, 0)
        return QPolygonF(pts), ramos

    def boundingRect(self) -> QRectF:
        R = self.R
        from . import camera3d
        if camera3d.ligada():   # coisas no alto se deslocam pra fora na perspectiva
            m = max(R * 3.2, 6 * CELULA) + camera3d.margem(min(4 * R, 10 * CELULA))
            return QRectF(-m, -m, 2 * m, 2 * m)
        if self.tipo == "raio":
            return QRectF(-5 * CELULA, -13.5 * CELULA, 10 * CELULA, 15.5 * CELULA)
        return QRectF(-R * 2.6, -R * 3.2, R * 5.2, R * 5.8)

    # --- Mesa 3D (v0.38): desenhar algo numa ALTURA (o painter vai pro plano daquela altura)
    def _alto(self, p, z: float):
        if self._cam is not None:
            p.setWorldTransform(self._cam.transformacao_topo(max(0.0, min(z, self._cam.z_max()))))

    def _chao(self, p):
        if self._cam is not None:
            p.setWorldTransform(self._base)

    def _ponto_alto(self, x: float, y: float, z: float) -> QPointF:
        """Ponto (local, altura z) na tela — pra linhas que atravessam alturas (o raio)."""
        return self._cam.projetar(QPointF(x, y), max(0.0, min(z, self._cam.z_max())))

    def _passo(self):
        from . import luz_dinamica
        cena = self.scene()
        f = (time.monotonic() - self.t0) / max(0.01, self.dur)
        ident = f"impacto:{id(self)}"
        if f >= 1:
            self._timer.stop()
            if cena is not None:
                luz_dinamica.definir(cena, ident, None)
                cena.removeItem(self)
            self.deleteLater()
            return
        if cena is not None:   # iluminação dinâmica: o clarão do impacto (paredes bloqueiam)
            luz = self._luz(f)
            try:
                luz_dinamica.definir(cena, ident, luz)
            except Exception:
                pass
        self.update()

    def _luz(self, f):
        p = self.scenePos()
        R = self.R / CELULA
        if self.tipo == "explosao":
            k = max(0.0, 1 - f / 0.75)
            return {"x": p.x(), "y": p.y(), "fraco": R * 3.2 + 3, "cor": "#ffa040", "brilho": k ** 1.3} if k > 0 else None
        if self.tipo == "raio":
            forca = 1.0 if f < 0.16 else 0.0 if f < 0.24 else max(0.0, 1 - (f - 0.24) / 0.5) * (0.6 + 0.4 * math.sin(f * 90))
            return {"x": p.x(), "y": p.y(), "fraco": 12, "cor": "#c8dcff", "brilho": forca} if forca > 0.02 else None
        if self.tipo == "arcano":
            k = math.sin(min(1.0, f * 1.6) * math.pi) ** 0.7
            return {"x": p.x(), "y": p.y(), "fraco": R * 2.5 + 2, "cor": "#b48cff", "brilho": k * 0.9} if k > 0.02 else None
        return None

    # ------------------------------------------------------------ desenho
    def paint(self, p: QPainter, option, widget=None):
        f = (time.monotonic() - self.t0) / self.dur
        if f >= 1:
            return
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        from . import camera3d
        self._cam = camera3d.Camera(p) if camera3d.ligada() else None
        self._base = p.worldTransform()
        try:
            getattr(self, "_" + self.tipo, self._onda)(p, f)
        except Exception as erro:   # (erro dentro de paint() fecha o programa)
            from ..seguranca import registrar_erro
            registrar_erro(f"Impacto {self.tipo} não desenhou: {erro!r}")
            self.dur = 0

    def _bola(self, p, c, raio, cores):
        g = QRadialGradient(c, max(1.0, raio))
        for pos, cor in cores:
            g.setColorAt(pos, cor)
        p.setBrush(QBrush(g))
        p.drawEllipse(c, raio, raio)

    def _explosao(self, p, f):
        R, n = self.R, self.n
        # marca de queimado (fica até o fim)
        self._bola(p, QPointF(0, 0), R * 1.05, ((0, _cor(12, 8, 6, 190 * min(1, f * 6) * (1 - f ** 3))),
                                               (0.7, _cor(20, 12, 8, 120 * min(1, f * 6) * (1 - f ** 3))),
                                               (1, _cor(20, 12, 8, 0))))
        if f < 0.16:   # clarão
            k = 1 - f / 0.16
            self._bola(p, QPointF(0, 0), R * (1.2 + 0.8 * (1 - k)), ((0, _cor(255, 255, 240, 255 * k)),
                                                                    (0.5, _cor(255, 220, 140, 180 * k)),
                                                                    (1, _cor(255, 160, 60, 0))))
        em3d = self._cam is not None
        if f < 0.55:   # bola de fogo (várias bolhas) — no 3D ela SOBE pra câmera
            k = f / 0.55
            apaga = (1 - k) ** 1.3
            # (v0.80) no 3D a bola fica mais baixa e PRESA no chão: cada bolha é desenhada em camadas do chão até
            # o alto (antes subia ~1,4 R e, inclinada, parecia solta no ar)
            camadas = (1.0,) if not em3d else ((0.35, 0.7, 1.0) if n >= 1 else (0.5, 1.0))
            for ang, dist, tam in self.bolas:
                c = QPointF(math.cos(ang) * R * dist * _suave(k),
                            math.sin(ang) * R * dist * _suave(k) - (0 if em3d else R * 0.25 * k))
                z = R * (0.12 + 0.5 * _suave(k)) * (0.6 + tam * 0.6)
                for j in camadas:
                    self._alto(p, z * j)
                    self._bola(p, c, R * tam * (0.35 + 0.75 * _suave(k)) * (0.75 + 0.25 * j),
                               ((0, _cor(255, 250, 210, 255 * apaga)), (0.35, _cor(255, 190, 60, 235 * apaga)),
                                (0.7, _cor(235, 80, 15, 190 * apaga)), (1, _cor(120, 20, 5, 0))))
            self._chao(p)
        if f < 0.45:   # onda de choque
            k = f / 0.45
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(_cor(255, 240, 215, 200 * (1 - k)), 2 + 10 * (1 - k)))
            p.drawEllipse(QPointF(0, 0), R * 1.9 * _suave(k), R * 1.9 * _suave(k))
            p.setPen(Qt.PenStyle.NoPen)
        # estilhaços e brasas
        k = _suave(f / 0.8)
        s = min(1.0, f / 0.8)
        for ang, vel, tam, sorte in self.parts:
            d = R * 2.3 * vel * k
            x, y = math.cos(ang) * d, math.sin(ang) * d + (0 if em3d else R * 0.5 * (f ** 2) * (1.2 - vel))
            alfa = 255 * (1 - f / 0.85) if f < 0.85 else 0
            if em3d:   # voa em arco: sobe e cai
                self._alto(p, R * 0.9 * (0.2 + sorte * 0.8) * 4 * s * (1 - s))   # (v0.80) era 1,4
            if sorte < 0.6:
                p.setBrush(_cor(255, 190 + 50 * sorte, 80, alfa))
                p.drawEllipse(QPointF(x, y), 1.4 + 2.4 * tam * (1 - f), 1.4 + 2.4 * tam * (1 - f))
                if n == 2:   # rastro
                    p.setBrush(_cor(255, 150, 40, alfa * 0.35))
                    p.drawEllipse(QPointF(x * 0.93, y * 0.93), 2 + 3 * tam, 2 + 3 * tam)
            else:
                p.setBrush(_cor(30, 22, 18, alfa))
                p.drawRect(QRectF(x - 2 * tam, y - 2 * tam, 4.5 * tam, 4.5 * tam))
        self._chao(p)
        if f > 0.18 and n >= 1:   # fumaça subindo (no 3D, uma coluna vindo pra câmera)
            k = (f - 0.18) / 0.82
            for i, (ang, dist, tam) in enumerate(self.bolas):
                subida = R * (0.3 + 1.6 * k) * (0.6 + tam * 0.5)
                c = QPointF(math.cos(ang) * R * dist * 0.9, math.sin(ang) * R * dist * (0.9 if em3d else 0.5) - (0 if em3d else subida))
                self._alto(p, subida * 0.55)   # (v0.80) era 1,3: no 3D a fumaça subia demais
                alfa = 150 * math.sin(min(1.0, k * 1.15) * math.pi) ** 0.8
                self._bola(p, c, R * tam * (0.5 + 0.9 * k), ((0, _cor(46, 40, 36, alfa)), (0.6, _cor(60, 54, 50, alfa * 0.6)),
                                                              (1, _cor(60, 54, 50, 0))))
            self._chao(p)

    def _raio(self, p, f):
        n = self.n
        # pisca: acende, apaga, acende de novo mais fraco
        forca = 1.0 if f < 0.16 else 0.0 if f < 0.24 else max(0.0, 1 - (f - 0.24) / 0.5) * (0.6 + 0.4 * math.sin(f * 90))
        if forca > 0.02 and self._cam is not None:
            # 3D: o raio DESCE do alto até o ponto (os pontos do traçado viram alturas)
            cam = self._cam
            p.save()
            p.resetTransform()
            p.setBrush(Qt.BrushStyle.NoBrush)
            for linha, grosso in [(self.raio_pts, 1.0)] + [(r, 0.5) for r in self.ramos]:
                tela = QPolygonF([self._ponto_alto(q.x(), q.x() * 0.35, -q.y() * 0.75) for q in linha])
                for larg, cor in ((26, _cor(90, 140, 255, 55 * forca)), (11, _cor(150, 190, 255, 120 * forca)),
                                  (3.4, _cor(255, 255, 255, 255 * forca))):
                    if n == 0 and larg == 26:
                        continue
                    p.setPen(QPen(cor, larg * grosso * cam.escala, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                                  Qt.PenJoinStyle.RoundJoin))
                    p.drawPolyline(tela)
            p.restore()
            p.setPen(Qt.PenStyle.NoPen)
            self._bola(p, QPointF(0, 0), self.R * 0.9, ((0, _cor(255, 255, 255, 240 * forca)), (0.4, _cor(170, 205, 255, 150 * forca)),
                                                        (1, _cor(120, 160, 255, 0))))
        elif forca > 0.02:
            p.setBrush(Qt.BrushStyle.NoBrush)
            for linha, grosso in [(self.raio_pts, 1.0)] + [(r, 0.5) for r in self.ramos]:
                for larg, cor in ((26, _cor(90, 140, 255, 55 * forca)), (11, _cor(150, 190, 255, 120 * forca)),
                                  (3.4, _cor(255, 255, 255, 255 * forca))):
                    if n == 0 and larg == 26:
                        continue
                    p.setPen(QPen(cor, larg * grosso, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                    p.drawPolyline(linha)
            p.setPen(Qt.PenStyle.NoPen)
            self._bola(p, QPointF(0, 0), self.R * 0.9, ((0, _cor(255, 255, 255, 240 * forca)), (0.4, _cor(170, 205, 255, 150 * forca)),
                                                        (1, _cor(120, 160, 255, 0))))
        # chão chamuscado + faíscas pulando
        self._bola(p, QPointF(0, 0), self.R * 0.4, ((0, _cor(10, 10, 14, 170 * (1 - f))), (1, _cor(10, 10, 14, 0))))
        k = _suave(f / 0.7)
        em3d = self._cam is not None
        for ang, vel, tam, sorte in self.parts[:: 1 if n else 2]:
            d = self.R * 1.3 * vel * k
            pulo = 14 * math.sin(k * math.pi) * sorte
            if em3d:
                self._alto(p, pulo * 3)
            p.setBrush(_cor(220, 235, 255, 255 * (1 - f)))
            p.drawEllipse(QPointF(math.cos(ang) * d, math.sin(ang) * d * (1.0 if em3d else 0.7) - (0 if em3d else pulo)),
                          1.6 * tam, 1.6 * tam)
        self._chao(p)

    def _onda(self, p, f):
        R = self.R
        p.setBrush(Qt.BrushStyle.NoBrush)
        for atraso in ((0.0,), (0.0, 0.16), (0.0, 0.14, 0.28))[self.n]:
            k = (f - atraso) / (1 - atraso)
            if k <= 0:
                continue
            raio = R * 2.2 * _suave(k)
            p.setPen(QPen(_cor(235, 240, 255, 190 * (1 - k)), 2 + 12 * (1 - k)))
            p.drawEllipse(QPointF(0, 0), raio, raio)
            p.setPen(QPen(_cor(255, 255, 255, 110 * (1 - k)), 1.5))
            p.drawEllipse(QPointF(0, 0), raio * 0.93, raio * 0.93)
        p.setPen(Qt.PenStyle.NoPen)
        k = _suave(f)
        for ang, vel, tam, sorte in self.parts:   # poeira empurrada
            d = R * 2.0 * (0.6 + 0.4 * vel) * k
            p.setBrush(_cor(200, 190, 170, 170 * (1 - f)))
            p.drawEllipse(QPointF(math.cos(ang) * d, math.sin(ang) * d), 2.2 * tam, 2.2 * tam)

    def _arcano(self, p, f):
        R = self.R
        brilho = math.sin(min(1.0, f * 1.6) * math.pi) ** 0.7
        self._bola(p, QPointF(0, 0), R * (0.6 + 0.9 * _suave(f)), ((0, _cor(240, 225, 255, 210 * brilho)),
                                                                  (0.5, _cor(170, 120, 255, 120 * brilho)),
                                                                  (1, _cor(120, 80, 255, 0))))
        p.setBrush(Qt.BrushStyle.NoBrush)
        raio = R * (0.3 + 1.2 * _suave(f))
        for esc, vel, marcas in ((1.0, 140, 12), (0.7, -200, 8)) if self.n else ((1.0, 120, 8),):
            # 3D: os anéis de runas flutuam e sobem (o de dentro mais alto)
            self._alto(p, R * (0.15 + 0.5 * _suave(f)) * (1.6 - esc))
            p.save()
            p.rotate(f * vel)
            p.setPen(QPen(_cor(225, 200, 255, 235 * (1 - f)), 2.2))
            rr = raio * esc
            p.drawEllipse(QPointF(0, 0), rr, rr)
            p.drawEllipse(QPointF(0, 0), rr * 0.9, rr * 0.9)
            for _ in range(marcas):
                p.rotate(360 / marcas)
                p.drawPolygon(QPolygonF([QPointF(0, -rr * 0.87), QPointF(5, -rr * 0.82), QPointF(0, -rr * 0.77), QPointF(-5, -rr * 0.82)]))
            p.restore()
        self._chao(p)
        p.setPen(Qt.PenStyle.NoPen)
        k = _suave(f)
        for ang, vel, tam, sorte in self.parts:
            d = R * 1.9 * vel * k
            giro = ang + f * 2.5 * (1 if sorte > 0.5 else -1)
            cor = (150, 240, 225) if sorte > 0.6 else (225, 190, 255)
            self._alto(p, R * 1.2 * sorte * k)   # 3D: fagulhas sobem em espiral
            p.setBrush(_cor(*cor, 255 * (1 - f)))
            s = 1.5 + 2.4 * tam * (1 - f)
            p.drawEllipse(QPointF(math.cos(giro) * d, math.sin(giro) * d), s, s)
        self._chao(p)

    def _desabamento(self, p, f):
        R = self.R
        em3d = self._cam is not None
        for i, (ang, dist, tam) in enumerate(self.bolas):   # nuvem de poeira (no 3D, sobe um pouco)
            k = _suave(f * 1.4)
            c = QPointF(math.cos(ang) * R * (0.3 + dist * 1.6 * k),
                        math.sin(ang) * R * (0.2 + dist * 1.0 * k) - (0 if em3d else R * 0.25 * f))
            self._alto(p, R * (0.1 + 0.6 * f) * (0.5 + tam))
            alfa = 185 * math.sin(min(1.0, f * 1.1) * math.pi) ** 0.6
            self._bola(p, c, R * tam * (0.6 + 1.0 * k), ((0, _cor(150, 132, 108, alfa)), (0.6, _cor(120, 104, 86, alfa * 0.55)),
                                                          (1, _cor(120, 104, 86, 0))))
        self._chao(p)
        for ang, vel, tam, sorte in self.parts:   # pedras caindo (no 3D, caem DO ALTO, vindo da câmera)
            atraso = sorte * 0.5
            k = (f - atraso) / 0.35
            if k <= 0 or k > 1.25:
                continue
            x = math.cos(ang) * R * vel * 1.3
            y = math.sin(ang) * R * vel * 0.9
            queda = -R * 2.2 * (1 - min(1.0, k)) ** 2
            p.setBrush(_cor(20, 16, 14, 90 * min(1.0, k)))                     # sombra no chão
            if em3d:
                p.drawEllipse(QPointF(x, y), 4 * tam, 4 * tam)
                self._alto(p, -queda * 1.4)
                queda = 0
            else:
                p.drawEllipse(QPointF(x, y), 5 * tam, 2.4 * tam)
            p.setBrush(_cor(96, 88, 80, 255 if k < 1 else 255 * (1.25 - k) / 0.25))
            lado = 4 + 7 * tam
            p.drawPolygon(QPolygonF([QPointF(x - lado * 0.5, y + queda), QPointF(x + lado * 0.2, y + queda - lado * 0.6),
                                     QPointF(x + lado * 0.6, y + queda), QPointF(x, y + queda + lado * 0.45)]))
            self._chao(p)


# ====================================================================== tocar (mapa + tela)
def tocar(cena, visao, tela, tipo: str, x: float = 0.0, y: float = 0.0, tam: float = TAMANHO_PADRAO):
    """
    cena: onde desenhar · visao: MesaVisao (pra tremer) · tela: ClimaOverlay (clarão/apagão).
    """
    if tipo not in IMPACTOS:
        return
    from ..graficos import graficos
    g = graficos()
    if IMPACTOS[tipo][1] and cena is not None:
        item = ImpactoItem(tipo, tam)
        item.setPos(x, y)
        cena.addItem(item)
    escala = max(0.6, min(1.8, tam / TAMANHO_PADRAO))
    tremor = {"explosao": (11 * escala, 0.55), "onda": (6 * escala, 0.35), "desabamento": (7, 1.7),
              "tremor": (9, 2.2), "raio": (3, 0.2)}.get(tipo)
    if tremor and g.tremor and visao is not None:
        visao.tremer(*tremor)
    if tela is not None:
        if g.clarao:
            clarao = {"raio": ((235, 240, 255), 1.0), "clarao": ((255, 255, 250), 1.0), "explosao": ((255, 200, 130), 0.45),
                      "arcano": ((200, 160, 255), 0.6)}.get(tipo)
            if clarao:
                tela.clarao(*clarao)
        if tipo == "apagao":
            tela.escurecer(IMPACTOS[tipo][2])
