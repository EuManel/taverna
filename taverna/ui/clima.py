"""
Clima por cima da mesa: chuva, tempestade, neve, neblina, cinzas, areia, folhas.

É uma camadinha transparente em cima da tela da mesa (não mexe no mapa nem no mouse).
Cada computador anima o seu; o mestre só escolhe o tipo e a força (1 a 3).
"""

import math
import random
import time

from PyQt6.QtCore import QEvent, QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPen, QRadialGradient, QPainterPath
from PyQt6.QtWidgets import QWidget

CLIMAS = {
    "nenhum": "☀ Sem clima",
    "chuva": "🌧 Chuva",
    "tempestade": "⛈ Tempestade",
    "neve": "🌨 Neve",
    "neblina": "🌫 Neblina",
    "cinzas": "🌋 Cinzas e brasas",
    "areia": "🏜 Tempestade de areia",
    "folhas": "🍂 Folhas ao vento",
}


class ClimaOverlay(QWidget):
    def __init__(self, alvo: QWidget):
        super().__init__(alvo)
        self.alvo = alvo
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.tipo = "nenhum"
        self.forca = 2
        self.ligado = True            # o mestre pode esconder na tela dele
        self._p = []                  # partículas
        self._flash = 0.0             # relâmpago / clarão (0..1)
        self._flash_cor = (235, 240, 255)
        self._flash_forca = 1.0
        self._apagao = None           # (início, duração) — tela escurece e volta
        self._raio = None             # desenho do raio da tempestade (lista de linhas)
        self._respingos = []          # [x, y, idade] — pingos batendo no chão
        self._proximo_raio = time.monotonic() + 6
        self._ultimo = time.monotonic()
        self._modo3d = False          # Mesa 3D: partículas com altura (ver _passo3d)
        self._ref = None              # (origem da cena na tela, zoom) — pra acompanhar o mapa
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._passo)
        alvo.installEventFilter(self)
        self.setGeometry(alvo.rect())
        self.hide()

    # ------------------------------------------------------------ controle
    def eventFilter(self, obj, ev):
        if obj is self.alvo and ev.type() == QEvent.Type.Resize:
            self.setGeometry(self.alvo.rect())
            self._p = []
        return False

    def definir(self, tipo: str, forca: int = 2):
        tipo = tipo if tipo in CLIMAS else "nenhum"
        forca = max(1, min(3, int(forca or 2)))
        if (tipo, forca) != (self.tipo, self.forca):
            self.tipo, self.forca = tipo, forca
            self._p = []
        self._aplicar()

    def definir_ligado(self, ligado: bool):
        self.ligado = ligado
        self._aplicar()

    def relampago(self):
        self.clarao()

    def clarao(self, cor=(235, 240, 255), forca: float = 1.0):
        """A tela clareia e volta (raio, explosão, magia)."""
        from ..graficos import graficos
        if not graficos().clarao:
            return
        self._flash, self._flash_cor, self._flash_forca = 1.0, tuple(cor), float(forca)
        self._acordar()

    def escurecer(self, duracao: float = 1.8):
        """Apagão: a tela escurece e volta."""
        self._apagao = (time.monotonic(), max(0.3, float(duracao)))
        self._acordar()

    def _acordar(self):
        self.setGeometry(self.alvo.rect())
        self.show()
        self.raise_()
        self._ultimo = time.monotonic()
        if not self._timer.isActive():
            self._timer.start()

    def _ocupado(self) -> bool:
        return self._flash > 0 or self._apagao is not None

    def _aplicar(self):
        ativo = self.ligado and self.tipo != "nenhum"
        self.setVisible(ativo)
        if ativo:
            self.raise_()
            self._ultimo = time.monotonic()
            self._timer.start()
        elif not self._ocupado():
            self._timer.stop()
        else:
            self._acordar()

    # ------------------------------------------------------------ partículas
    def _quantas(self) -> int:
        area = max(1, self.width() * self.height()) / (1200 * 800)
        base = {"chuva": 160, "tempestade": 300, "neve": 120, "neblina": 9, "cinzas": 70,
                "areia": 220, "folhas": 26}.get(self.tipo, 0)
        from ..graficos import nivel
        return int(base * (0.45 + 0.4 * self.forca) * max(0.4, area) * (0.45, 1.0, 1.7)[nivel()])

    def _nova(self, rnd=random, topo=False):
        w, h = max(1, self.width()), max(1, self.height())
        x = rnd.uniform(-0.2 * w, 1.1 * w)
        y = rnd.uniform(-h * 0.1, 0) if topo else rnd.uniform(0, h)
        t = self.tipo
        if t in ("chuva", "tempestade"):
            v = rnd.uniform(900, 1300) * (1.2 if t == "tempestade" else 1)
            return [x, y, v, rnd.uniform(12, 24), rnd.random()]
        if t == "neve":
            return [x, y, rnd.uniform(30, 80), rnd.uniform(1.5, 3.8), rnd.random() * 6.28]
        if t == "neblina":
            return [rnd.uniform(-0.3 * w, w), rnd.uniform(0, h), rnd.uniform(8, 22),
                    rnd.uniform(0.25, 0.55) * max(w, h), rnd.random() * 6.28]
        if t == "cinzas":
            if topo:
                y = rnd.uniform(h, h * 1.1)
            return [x, y, rnd.uniform(15, 50), rnd.uniform(1.2, 3.0), rnd.random() * 6.28,
                    rnd.random() < 0.25]
        if t == "areia":
            return [rnd.uniform(-w * 0.3, 0) if topo else x, rnd.uniform(0, h),
                    rnd.uniform(500, 900), rnd.uniform(10, 40), rnd.random()]
        if t == "folhas":
            return [rnd.uniform(-w * 0.2, 0) if topo else x, rnd.uniform(-h * 0.2, h), rnd.uniform(60, 140),
                    rnd.uniform(5, 9), rnd.random() * 6.28, rnd.choice(["#c0571f", "#d98b2b", "#8a4a1c", "#b5a03a"])]
        return [x, y, 0, 0, 0]

    def _passo(self):
        agora = time.monotonic()
        dt = min(0.1, agora - self._ultimo)
        self._ultimo = agora
        from ..graficos import nivel
        n = nivel()
        intervalo = (60, 33, 22)[n]
        if self._timer.interval() != intervalo:
            self._timer.setInterval(intervalo)
        if self._flash > 0:
            self._flash = max(0.0, self._flash - dt * 2.2)
            if self._flash <= 0:
                self._raio = None
        if self._apagao and agora - self._apagao[0] >= self._apagao[1]:
            self._apagao = None
        if not self.isVisible():
            return
        if self.tipo == "nenhum" or not self.ligado:
            if not self._ocupado():
                self.hide()
                self._timer.stop()
            self.update()
            return
        from ..mesa import camera3d
        em3d = camera3d.ligada()
        if em3d != self._modo3d:   # trocou 2D ↔ 3D: recomeça as partículas
            self._modo3d = em3d
            self._p, self._respingos, self._raio, self._ref = [], [], None, None
        if em3d:
            try:
                self._passo3d(dt, agora, n)
            except Exception as erro:
                from ..seguranca import registrar_erro
                registrar_erro(f"Clima 3D falhou: {erro!r}")
                self._p = []
            self.update()
            return
        if self.tipo in ("chuva", "tempestade") and n >= 1:
            # pingos batendo no chão
            for r_ in self._respingos:
                r_[2] += dt
            self._respingos = [r_ for r_ in self._respingos if r_[2] < 0.45]
            for _ in range(int((2, 5)[n - 1] * self.forca * (1.6 if self.tipo == "tempestade" else 1))):
                self._respingos.append([random.uniform(0, self.width()), random.uniform(0, self.height()), 0.0])
        elif self._respingos:
            self._respingos = []
        n = self._quantas()
        if len(self._p) < n:
            self._p.extend(self._nova() for _ in range(n - len(self._p)))
        elif len(self._p) > n:
            del self._p[n:]
        w, h = self.width(), self.height()
        vento = 0.25 * self.forca
        t = self.tipo
        for i, p in enumerate(self._p):
            if t in ("chuva", "tempestade"):
                p[1] += p[2] * dt
                p[0] += p[2] * dt * vento * (0.6 if t == "chuva" else 1.0)
                if p[1] > h + 30 or p[0] > w + 40:
                    self._p[i] = self._nova(topo=True)
            elif t == "neve":
                p[4] += dt * 1.5
                p[1] += p[2] * dt
                p[0] += math.sin(p[4]) * 18 * dt + p[2] * dt * vento * 0.6
                if p[1] > h + 10:
                    self._p[i] = self._nova(topo=True)
            elif t == "neblina":
                p[0] += p[2] * dt * (0.5 + vento)
                p[4] += dt * 0.2
                if p[0] - p[3] > w:
                    p[0] = -p[3]
                    p[1] = random.uniform(0, h)
            elif t == "cinzas":
                p[4] += dt
                p[1] -= p[2] * dt
                p[0] += math.sin(p[4] * 1.3) * 14 * dt + 12 * vento * dt
                if p[1] < -10:
                    self._p[i] = self._nova(topo=True)
            elif t == "areia":
                p[0] += p[2] * dt
                p[1] += math.sin(p[0] * 0.01 + p[4] * 6) * 30 * dt
                if p[0] > w + 50:
                    self._p[i] = self._nova(topo=True)
            elif t == "folhas":
                p[4] += dt * 2.2
                p[0] += p[2] * dt
                p[1] += (math.sin(p[4]) * 40 + 20) * dt
                if p[0] > w + 20 or p[1] > h + 20:
                    self._p[i] = self._nova(topo=True)
        if t == "tempestade" and agora >= self._proximo_raio:
            self._flash, self._flash_cor, self._flash_forca = 1.0, (235, 240, 255), 0.9
            self._proximo_raio = agora + random.uniform(7, 18) / self.forca
            if n >= 1:   # desenha o raio rasgando o céu
                x = random.uniform(0.1, 0.9) * w
                pts, y = [QPointF(x, -10)], -10.0
                alvo = random.uniform(0.35, 0.8) * h
                ramos = []
                while y < alvo:
                    y += random.uniform(18, 46)
                    x += random.uniform(-38, 38)
                    pts.append(QPointF(x, y))
                    if random.random() < 0.22:
                        lado = random.choice((-1, 1))
                        ramos.append([QPointF(x, y), QPointF(x + lado * random.uniform(20, 60), y + random.uniform(20, 50)),
                                      QPointF(x + lado * random.uniform(50, 110), y + random.uniform(50, 110))])
                self._raio = [pts] + ramos
        self.update()

    # ------------------------------------------------------------ desenho
    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        t = self.tipo
        f = self.forca
        from ..graficos import nivel
        n = nivel()
        if self._modo3d and t != "nenhum" and self.ligado:
            try:
                self._pintar3d(p, w, h, t, f, n)
            except Exception as erro:   # (erro em paintEvent pode fechar o programa)
                from ..seguranca import registrar_erro
                registrar_erro(f"Clima 3D não desenhou: {erro!r}")
                self._p = []
        elif t in ("chuva", "tempestade"):
            p.fillRect(self.rect(), QColor(20, 30, 50, 25 + 18 * f + (25 if t == "tempestade" else 0)))
            vento = 0.25 * f * (0.6 if t == "chuva" else 1.0)
            if n == 0:
                p.setPen(QPen(QColor(190, 210, 235, 120), 1.2))
                for x, y, v, comp, a in self._p:
                    p.drawLine(QPointF(x, y), QPointF(x - comp * vento, y - comp))
            else:
                # profundidade: pingos de longe (finos, fracos) e de perto (grossos, compridos)
                for faixa, (larg, alfa, mult) in enumerate(((0.8, 60, 0.6), (1.3, 115, 1.0), (2.1, 165, 1.7))):
                    p.setPen(QPen(QColor(195, 215, 240, alfa), larg, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                    for x, y, v, comp, a in self._p:
                        if int(a * 2.999) == faixa:
                            p.drawLine(QPointF(x, y), QPointF(x - comp * mult * vento, y - comp * mult))
                p.setBrush(Qt.BrushStyle.NoBrush)
                for x, y, idade in self._respingos:   # respingo: anelzinho abrindo
                    k = idade / 0.45
                    p.setPen(QPen(QColor(210, 228, 248, int(150 * (1 - k))), 1.1))
                    p.drawEllipse(QPointF(x, y), 2 + 9 * k, 1 + 4 * k)
                if n == 2:   # névoa de chuva embaixo
                    g = QLinearGradient(0, h * 0.6, 0, h)
                    g.setColorAt(0, QColor(170, 190, 215, 0))
                    g.setColorAt(1, QColor(170, 190, 215, 26 + 10 * f))
                    p.fillRect(self.rect(), QBrush(g))
        elif t == "neve":
            p.fillRect(self.rect(), QColor(220, 230, 245, 10 + 10 * f))
            p.setPen(Qt.PenStyle.NoPen)
            if n == 0:
                p.setBrush(QColor(255, 255, 255, 215))
                for x, y, v, r, a in self._p:
                    p.drawEllipse(QPointF(x, y), r, r)
            else:
                for k, (x, y, v, r, a) in enumerate(self._p):
                    perto = k % 7 == 0
                    if perto and n == 2:   # flocos grandes e fofos na frente
                        g = QRadialGradient(QPointF(x, y), r * 3.2)
                        g.setColorAt(0, QColor(255, 255, 255, 190))
                        g.setColorAt(1, QColor(255, 255, 255, 0))
                        p.setBrush(QBrush(g))
                        p.drawEllipse(QPointF(x, y), r * 3.2, r * 3.2)
                    else:
                        p.setBrush(QColor(255, 255, 255, 120 + int(110 * (r / 3.8))))
                        p.drawEllipse(QPointF(x, y), r * (1.5 if perto else 1), r * (1.5 if perto else 1))
        elif t == "neblina":
            p.fillRect(self.rect(), QColor(200, 205, 210, 20 + 22 * f))
            p.setPen(Qt.PenStyle.NoPen)
            for x, y, v, r, a in self._p:
                g = QRadialGradient(QPointF(x, y), r)
                alfa = int((40 + 25 * f) * (0.7 + 0.3 * math.sin(a)))
                g.setColorAt(0, QColor(215, 220, 225, alfa))
                g.setColorAt(1, QColor(215, 220, 225, 0))
                p.setBrush(QBrush(g))
                p.drawEllipse(QPointF(x, y), r, r * 0.6)
        elif t == "cinzas":
            p.fillRect(self.rect(), QColor(60, 30, 15, 18 + 12 * f))
            p.setPen(Qt.PenStyle.NoPen)
            for x, y, v, r, a, brasa in self._p:
                if brasa:
                    brilho = 150 + int(100 * abs(math.sin(a * 3)))
                    p.setBrush(QColor(255, 140, 40, brilho))
                else:
                    p.setBrush(QColor(90, 85, 80, 170))
                p.drawEllipse(QPointF(x, y), r, r)
        elif t == "areia":
            p.fillRect(self.rect(), QColor(190, 150, 90, 30 + 30 * f))
            p.setPen(QPen(QColor(225, 190, 130, 110), 1.4))
            for x, y, v, comp, a in self._p:
                p.drawLine(QPointF(x, y), QPointF(x - comp, y))
        elif t == "folhas":
            p.setPen(Qt.PenStyle.NoPen)
            for x, y, v, r, a, cor in self._p:
                p.save()
                p.translate(x, y)
                p.rotate(math.degrees(a))
                folha = QPainterPath()
                folha.moveTo(-r, 0)
                folha.quadTo(0, -r * 0.6, r, 0)
                folha.quadTo(0, r * 0.6, -r, 0)
                p.setBrush(QColor(cor))
                p.drawPath(folha)
                p.restore()
        if self._raio and self._flash > 0.25 and not self._modo3d:
            br = min(1.0, (self._flash - 0.25) / 0.5)
            p.setBrush(Qt.BrushStyle.NoBrush)
            for k, linha in enumerate(self._raio):
                grosso = 1.0 if k == 0 else 0.5
                for larg, cor in ((18, QColor(120, 160, 255, int(60 * br))), (7, QColor(180, 205, 255, int(150 * br))),
                                  (2.4, QColor(255, 255, 255, int(255 * br)))):
                    p.setPen(QPen(cor, larg * grosso, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                    for i in range(len(linha) - 1):
                        p.drawLine(linha[i], linha[i + 1])
        if self._flash > 0:
            r_, g_, b_ = self._flash_cor
            p.fillRect(self.rect(), QColor(r_, g_, b_, int(190 * self._flash_forca * self._flash ** 1.5)))
        if self._apagao:
            k = (time.monotonic() - self._apagao[0]) / self._apagao[1]
            if 0 <= k < 1:   # escurece rápido, segura, volta devagar
                alfa = min(1.0, k / 0.15) if k < 0.55 else max(0.0, 1 - (k - 0.55) / 0.45)
                p.fillRect(self.rect(), QColor(0, 0, 0, int(238 * alfa)))
        p.end()

    # ================================================================ MESA 3D (v0.38)
    # Cada partícula tem um ponto no CHÃO (x, y em pixels da tela) e uma ALTURA zf (fração da altura da
    # câmera, 0 = chão, 0,5 = metade do caminho até a câmera). Na tela ela aparece afastada do centro
    # pelo fator 1/(1−zf): a chuva vira riscos apontando pro centro, o que está alto é maior e, ao
    # arrastar o mapa, anda mais (paralaxe) — tudo preso ao mundo, não à tela.
    TOPO = 0.5

    def _camera(self):
        """(v0.72) A câmera da mesa pro clima: (de_cima, s, c, D). `de_cima` = cena → pixels "visto de cima"
        (zoom, giro e posição — a parte afim); s/c = seno/cosseno da inclinação; D = altura da câmera em px."""
        import math
        from PyQt6.QtGui import QTransform
        view = self.alvo.parent()
        w, h = max(1, self.width()), max(1, self.height())
        if not hasattr(view, "_cam_escala"):
            vt = view.viewportTransform() if hasattr(view, "viewportTransform") else QTransform()
            return vt, 0.0, 1.0, 1.8 * h
        e, c = view._cam_escala, view._cam_centro
        de_cima = QTransform().translate(w / 2, h / 2).rotate(view.giro()).scale(e, e).translate(-c.x(), -c.y())
        teta = math.radians(view.inclinacao_efetiva())
        from ..mesa.camera3d import altura_telas   # (v0.75) pelos olhos a câmera fica mais baixa
        return de_cima, math.sin(teta), math.cos(teta), altura_telas() * h

    def _proj(self, x, y, zf):
        """(x, y) = ponto do chão "visto de cima" (px), zf = altura em frações da altura da câmera.
        Reto de cima é o de sempre (amplia a partir do centro); inclinada, a câmera fica atrás (v0.72)."""
        zf = min(0.6, max(0.0, zf))
        cx, cy = self.width() / 2, self.height() / 2
        s, c, D = getattr(self, "_incl", (0.0, 1.0, 1.8 * max(1, self.height())))
        X, Y, Z = x - cx, y - cy, zf * D
        f = D / max(0.2 * D, D - Y * s - Z * c)
        return QPointF(cx + X * f, cy + (Y * c - Z * s) * f), f

    def _nova3d(self, topo=False, rnd=random):
        w, h = max(1, self.width()), max(1, self.height())
        a = self._area_chao()   # (v0.72) inclinada: o chão visível vai bem mais longe
        x = rnd.uniform(a.left() - 0.1 * a.width(), a.right() + 0.1 * a.width())
        y = rnd.uniform(a.top() - 0.1 * a.height(), a.bottom() + 0.1 * a.height())
        t, T = self.tipo, self.TOPO
        if t in ("chuva", "tempestade"):
            T = 0.4   # (mais alto que isso, na borda da tela o pingo vira um risco enorme)
            return [x, y, T if topo else rnd.uniform(0, T), rnd.uniform(0.7, 1.0) * (1.2 if t == "tempestade" else 1),
                    rnd.uniform(0.012, 0.026), rnd.random()]
        if t == "neve":
            return [x, y, T if topo else rnd.uniform(0, T), rnd.uniform(0.04, 0.1), rnd.uniform(1.5, 3.8), rnd.random() * 6.28]
        if t == "neblina":
            return [rnd.uniform(-0.3 * w, w), y, rnd.uniform(0.02, 0.3), rnd.uniform(8, 22),
                    rnd.uniform(0.25, 0.55) * max(w, h), rnd.random() * 6.28]
        if t == "cinzas":
            return [x, y, 0.0 if topo else rnd.uniform(0, T), rnd.uniform(0.03, 0.08), rnd.uniform(1.2, 3.0),
                    rnd.random() * 6.28, rnd.random() < 0.25]
        if t == "areia":
            return [rnd.uniform(-w * 0.3, 0) if topo else x, y, rnd.uniform(0, 0.18), rnd.uniform(500, 900),
                    rnd.uniform(10, 40), rnd.random()]
        if t == "folhas":
            return [rnd.uniform(-w * 0.2, 0) if topo else x, y, rnd.uniform(0.05, T), rnd.uniform(60, 140),
                    rnd.uniform(5, 9), rnd.random() * 6.28, rnd.choice(["#c0571f", "#d98b2b", "#8a4a1c", "#b5a03a"])]
        return [x, y, 0.0, 0, 0, 0]

    def _acompanhar_mapa(self):
        """O mapa andou/zoom mudou: os pontos no chão acompanham (preso ao mundo = paralaxe)."""
        if not hasattr(self.alvo.parent(), "viewportTransform"):
            return
        de_cima, s, c, D = self._camera()   # (v0.72) com giro e inclinação
        self._incl = (s, c, D)
        if self._ref is not None and self._ref != de_cima:
            m = self._ref.inverted()[0] * de_cima   # pixel antigo → cena → pixel novo
            for q in self._p:
                pt = m.map(QPointF(q[0], q[1]))
                q[0], q[1] = pt.x(), pt.y()
            for q in self._respingos:
                pt = m.map(QPointF(q[0], q[1]))
                q[0], q[1] = pt.x(), pt.y()
            if self._raio:
                self._raio = [[(m.map(QPointF(x, y)).x(), m.map(QPointF(x, y)).y(), z) for x, y, z in linha]
                              for linha in self._raio]
        self._ref = de_cima

    def _area_chao(self):
        """(v0.72) O chão "visto de cima" (px) que aparece na tela: inclinada, o alto da tela mostra bem mais longe."""
        from PyQt6.QtCore import QRectF
        w, h = max(1, self.width()), max(1, self.height())
        s, c, D = getattr(self, "_incl", (0.0, 1.0, 1.8 * h))
        if s <= 1e-4:
            return QRectF(0, 0, w, h)
        import math
        from ..mesa.camera3d import homografia
        inv, ok = homografia(w / 2, h / 2, D, math.asin(s)).inverted()
        from ..mesa.camera3d import linha_horizonte   # (v0.75) só o chão abaixo do horizonte
        topo = max(0.0, linha_horizonte(h / 2, D, math.asin(s)) + 0.06 * h)
        return inv.mapRect(QRectF(0, topo, w, max(1.0, h - topo))) if ok else QRectF(0, 0, w, h)

    def _passo3d(self, dt, agora, nv):
        w, h = max(1, self.width()), max(1, self.height())
        self._acompanhar_mapa()
        t, T = self.tipo, self.TOPO
        vento = 0.25 * self.forca
        if self._respingos:
            for r_ in self._respingos:
                r_[2] += dt
            self._respingos = [r_ for r_ in self._respingos if r_[2] < 0.45]
        qtd = self._quantas()
        area = self._area_chao()
        if area.width() * area.height() > w * h * 1.05:   # inclinada: mais chão na tela = mais partículas
            qtd = int(qtd * min(2.5, (area.width() * area.height()) / (w * h)) ** 0.5)
        if len(self._p) < qtd:
            self._p.extend(self._nova3d() for _ in range(qtd - len(self._p)))
        elif len(self._p) > qtd:
            del self._p[qtd:]
        for i, p in enumerate(self._p):
            if t in ("chuva", "tempestade"):
                p[2] -= p[3] * dt
                p[0] += p[3] * dt * vento * w * 0.25 * (0.6 if t == "chuva" else 1.0)
                if p[2] <= 0:   # bateu no chão: respingo bem ali
                    if nv >= 1 and len(self._respingos) < 400 and random.random() < 0.6:
                        self._respingos.append([p[0], p[1], 0.0])
                    self._p[i] = p = self._nova3d(topo=True)
            elif t == "neve":
                p[5] += dt * 1.5
                p[2] -= p[3] * dt
                p[0] += math.sin(p[5]) * 18 * dt + vento * 20 * dt
                if p[2] <= 0:
                    self._p[i] = p = self._nova3d(topo=True)
            elif t == "neblina":
                p[0] += p[3] * dt * (0.5 + vento)
                p[5] += dt * 0.2
                if p[0] - p[4] > w * 1.2:
                    p[0] = -p[4]
                    p[1] = random.uniform(0, h)
            elif t == "cinzas":
                p[5] += dt
                p[2] += p[3] * dt
                p[0] += math.sin(p[5] * 1.3) * 14 * dt + 12 * vento * dt
                if p[2] > T:
                    self._p[i] = p = self._nova3d(topo=True)
            elif t == "areia":
                p[0] += p[3] * dt
                p[1] += math.sin(p[0] * 0.01 + p[5] * 6) * 30 * dt
                if p[0] > w + 50:
                    self._p[i] = p = self._nova3d(topo=True)
            elif t == "folhas":
                p[5] += dt * 2.2
                p[0] += p[3] * dt
                p[2] -= 0.045 * dt * (1 + 0.6 * math.sin(p[5]))
                if p[2] <= 0 or p[0] > w * 1.2:
                    self._p[i] = p = self._nova3d(topo=True)
            if t != "neblina" and not (area.left() - 0.5 * area.width() < p[0] < area.right() + 0.5 * area.width()
                                       and area.top() - 0.5 * area.height() < p[1] < area.bottom() + 0.5 * area.height()):
                self._p[i] = self._nova3d()   # saiu de vista (mapa arrastado/girado)
        if t == "tempestade" and agora >= self._proximo_raio:
            self._flash, self._flash_cor, self._flash_forca = 1.0, (235, 240, 255), 0.9
            self._proximo_raio = agora + random.uniform(7, 18) / self.forca
            if nv >= 1:   # o raio DESCE do alto até um ponto do chão
                x, y = random.uniform(0.3, 0.7) * w, random.uniform(0.3, 0.7) * h
                passos = 14
                linha, ramos = [], []
                for k in range(passos + 1):
                    z = T * (1 - k / passos)
                    jx = 0 if k == passos else random.uniform(-26, 26)
                    jy = 0 if k == passos else random.uniform(-26, 26)
                    linha.append((x + jx, y + jy, z))
                    if 2 < k < passos - 2 and random.random() < 0.25:
                        bx, by, bz = x + jx, y + jy, z
                        ramo = [(bx, by, bz)]
                        for _ in range(random.randint(2, 4)):
                            bx += random.uniform(-50, 50)
                            by += random.uniform(-50, 50)
                            bz = max(0.0, bz - random.uniform(0.03, 0.07))
                            ramo.append((bx, by, bz))
                        ramos.append(ramo)
                self._raio = [linha] + ramos

    def _pintar3d(self, p, w, h, t, f, n):
        """Desenho do clima com altura (ver _passo3d)."""
        proj = self._proj
        if t in ("chuva", "tempestade"):
            p.fillRect(self.rect(), QColor(20, 30, 50, 25 + 18 * f + (25 if t == "tempestade" else 0)))
            vento = 0.25 * f * (0.6 if t == "chuva" else 1.0)
            # (v0.76) em LOTES: 6 grupos (3 tipos de pingo × perto/longe), um desenho por grupo — antes era um por
            # pingo (centenas de trocas de caneta por quadro)
            from PyQt6.QtCore import QLineF
            lotes = {}
            for x, y, z, v, comp, a in self._p:
                cab, fa = proj(x, y, z)
                cauda, _ = proj(x - comp * vento * w * 0.25, y, z + comp)   # de onde o pingo veio
                faixa = int(a * 2.999) if n else 1
                lotes.setdefault((faixa, fa > 1.35), []).append(QLineF(cab, cauda))
            for (faixa, perto), linhas in lotes.items():
                larg, alfa = ((0.8, 70), (1.2, 120), (1.7, 165))[faixa]
                p.setPen(QPen(QColor(195, 215, 240, alfa), larg * (1.6 if perto else 1.1), Qt.PenStyle.SolidLine,
                              Qt.PenCapStyle.RoundCap))
                p.drawLines(linhas)
            p.setBrush(Qt.BrushStyle.NoBrush)
            s_, c_, D_ = getattr(self, "_incl", (0.0, 1.0, 1.8 * h))
            if s_ > 1e-4:   # (v0.72) inclinada: o respingo deitado no chão, em perspectiva
                import math as _m
                from ..mesa.camera3d import homografia
                p.save()
                p.setTransform(homografia(w / 2, h / 2, D_, _m.asin(s_)), True)
            for x, y, idade in self._respingos:   # respingo: coroa abrindo no chão (visto de cima, redondo)
                k = idade / 0.45
                caneta = QPen(QColor(210, 228, 248, int(160 * (1 - k))), 1.1)
                caneta.setCosmetic(True)
                p.setPen(caneta)
                p.drawEllipse(QPointF(x, y), 2 + 8 * k, 2 + 8 * k)
            if s_ > 1e-4:
                p.restore()
            if n == 2:   # névoa de chuva junto ao chão
                p.fillRect(self.rect(), QColor(170, 190, 215, 14 + 6 * f))
        elif t == "neve":
            p.fillRect(self.rect(), QColor(220, 230, 245, 10 + 10 * f))
            p.setPen(Qt.PenStyle.NoPen)
            for x, y, z, v, r, a in self._p:
                c, fa = proj(x, y, z)
                rr = r * fa
                if n == 2 and fa > 1.6:   # bem perto da câmera: floco grande e desfocado
                    g = QRadialGradient(c, rr * 2.4)
                    g.setColorAt(0, QColor(255, 255, 255, 170))
                    g.setColorAt(1, QColor(255, 255, 255, 0))
                    p.setBrush(QBrush(g))
                    p.drawEllipse(c, rr * 2.4, rr * 2.4)
                else:
                    p.setBrush(QColor(255, 255, 255, 120 + int(110 * (r / 3.8))))
                    p.drawEllipse(c, rr, rr)
        elif t == "neblina":
            pass   # v0.44: na Mesa 3D a neblina é VOLUMÉTRICA, desenhada dentro da mesa (mesa/neblina.py)
        elif t == "cinzas":
            p.fillRect(self.rect(), QColor(60, 30, 15, 18 + 12 * f))
            p.setPen(Qt.PenStyle.NoPen)
            for x, y, z, v, r, a, brasa in self._p:
                c, fa = proj(x, y, z)
                if brasa:
                    p.setBrush(QColor(255, 140, 40, 150 + int(100 * abs(math.sin(a * 3)))))
                else:
                    p.setBrush(QColor(90, 85, 80, 170))
                p.drawEllipse(c, r * fa, r * fa)
        elif t == "areia":
            p.fillRect(self.rect(), QColor(190, 150, 90, 30 + 30 * f))
            for x, y, z, v, comp, a in self._p:
                c, fa = proj(x, y, z)
                p.setPen(QPen(QColor(225, 190, 130, 110), 1.4 * fa))
                p.drawLine(c, QPointF(c.x() - comp * fa, c.y()))
        elif t == "folhas":
            p.setPen(Qt.PenStyle.NoPen)
            for x, y, z, v, r, a, cor in self._p:
                c, fa = proj(x, y, z)
                p.save()
                p.translate(c)
                p.rotate(math.degrees(a))
                rr = r * fa
                folha = QPainterPath()
                folha.moveTo(-rr, 0)
                folha.quadTo(0, -rr * 0.6, rr, 0)
                folha.quadTo(0, rr * 0.6, -rr, 0)
                p.setBrush(QColor(cor))
                p.drawPath(folha)
                p.restore()
        if self._raio and self._flash > 0.25:
            br = min(1.0, (self._flash - 0.25) / 0.5)
            p.setBrush(Qt.BrushStyle.NoBrush)
            for k, linha in enumerate(self._raio):
                pts = [proj(x, y, z)[0] for x, y, z in linha]
                grosso = 1.0 if k == 0 else 0.5
                for larg, cor in ((18, QColor(120, 160, 255, int(60 * br))), (7, QColor(180, 205, 255, int(150 * br))),
                                  (2.4, QColor(255, 255, 255, int(255 * br)))):
                    p.setPen(QPen(cor, larg * grosso, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                    for i in range(len(pts) - 1):
                        p.drawLine(pts[i], pts[i + 1])
