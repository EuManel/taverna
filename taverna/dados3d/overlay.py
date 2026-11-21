"""
Painel transparente por cima da mesa onde os dados 3D rolam (mestre e jogadores).

- Recebe a rolagem do servidor (com "fisicos" e "semente"), calcula a física em segundo plano,
  anima ~2–3 s e mostra o PLACAR (quem rolou, total, 20/1 natural) por mais ~2,5 s.
- OpenGL quando der; se falhar (ou nos testes sem tela), desenha pelo plano B (render_2d).
- Rolou de novo durante uma animação: a anterior é cancelada e a nova entra por cima (v0.45.3).
"""

import os
import threading
import time

from PyQt6.QtCore import QObject, QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QGuiApplication, QLinearGradient, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from .geometria import suportado

TEMPO_PLACAR = 2.6
TEMPO_SUMIR = 0.5


def opengl_disponivel() -> bool:
    if os.environ.get("TAVERNA_SEM_GL") == "1":
        return False
    return QGuiApplication.platformName() not in ("offscreen", "minimal")


class _Calculadora(QObject):
    pronta = pyqtSignal(object)


class PainelDados3D(QWidget):
    terminou = pyqtSignal()
    revelar = pyqtSignal(dict)   # (v0.46.1) o dado PAROU: agora o resultado pode ir pro histórico/chat

    def __init__(self, mesa):
        super().__init__(mesa)
        self.mesa = mesa
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.rolagem = None
        self.t = 0.0
        self.fila = []
        self._calculando = False
        self._revelado = True
        self._r_calc = None
        self._inicio = 0.0
        self._calc = _Calculadora()
        self._calc.pronta.connect(self._comecar)
        # Relógio da animação. No OpenGL quem dita o ritmo é o monitor (vsync: frameSwapped pede o
        # próximo quadro); o timer só dá a partida e cobre o plano B. PreciseTimer: o timer comum do
        # Windows tem ~15,6 ms de resolução e deixava a animação aos trancos.
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.setInterval(8)
        self._timer.timeout.connect(self._passo)
        self.gl = None
        self.motivo_sem_gl = ""
        if opengl_disponivel():
            try:
                from .render_gl import DadosGL
                self.gl = DadosGL(self, self)
                self.gl.falhou.connect(self._sem_gl)
                self.gl.frameSwapped.connect(self._passo)
            except Exception as erro:   # PyQt sem o módulo de OpenGL, por exemplo
                self._sem_gl(str(erro))
        from ..ui.sobreposicoes import _Acompanhar
        self._acompanhar = _Acompanhar(mesa, self.posicionar)
        self.hide()

    # ------------------------------------------------------------ entrada
    @staticmethod
    def aceita(r: dict) -> bool:
        return any(suportado(int(f.get("lados", 0))) for f in (r.get("fisicos") or []))

    def rolar(self, r: dict) -> bool:
        """Mostra a rolagem. False = não tem dado que dê pra mostrar (quem chamou mostra o aviso de sempre).
        v0.45.3 (pedido do Manel): rolou de novo, CANCELA a anterior e a nova entra por cima — sem fila.
        (A anterior continua na tela só os milissegundos até a física da nova ficar pronta.)"""
        if not self.aceita(r):
            return False
        self.fila = []
        # a que estava rolando (ou sendo preparada) foi cancelada: o resultado dela aparece já
        if self.rolagem is not None and not getattr(self, "_revelado", True):
            self._revelado = True
            self.revelar.emit(self.rolagem.r)
        if self._calculando and getattr(self, "_r_calc", None) is not None:
            self.revelar.emit(self._r_calc)
        self._calcular(r)
        return True

    def _calcular(self, r):
        self._seq = getattr(self, "_seq", 0) + 1
        seq = self._seq
        self._r_calc = r
        from ..ui.tema import tema_atual
        t = tema_atual()
        tema = t.get("chave", "medieval")
        fonte = t["fonte_titulo"].split(",")[0].strip("'\" ")
        w, h = max(200, self.mesa.width()), max(150, self.mesa.height())
        self._calculando = True

        def trabalho():
            from .cena3d import Rolagem
            try:
                rol = Rolagem(r, w, h, tema, fonte)
            except Exception as erro:   # nunca derruba o programa por causa da animação
                from ..seguranca import registrar_erro
                registrar_erro(f"Dados 3D: não consegui preparar a rolagem {r.get('expr')}: {erro!r}")
                rol = None
            self._calc.pronta.emit((seq, rol))

        threading.Thread(target=trabalho, daemon=True).start()

    def _comecar(self, pronta):
        seq, rol = pronta
        if seq != getattr(self, "_seq", 0):
            return   # já rolaram de novo: esta ficou velha (a mais nova é que vale)
        self._calculando = False
        r_calc, self._r_calc = self._r_calc, None
        if rol is None or not rol.dados:
            if r_calc is not None:
                self.revelar.emit(r_calc)   # não deu pra animar: mostra o resultado já
            self._proxima()
            return
        self.rolagem = rol
        self._revelado = False
        self.t = 0.0
        self._inicio = time.perf_counter()
        self.posicionar()
        self.show()
        self.raise_()
        if self.gl is not None:
            self.gl.show()
            self.gl.update()          # o primeiro quadro; os próximos vêm do frameSwapped
            self._timer.setInterval(100)   # só uma garantia, se o vsync não chamar (janela escondida…)
        else:
            self._timer.setInterval(8)
        self._timer.start()

    def _passo(self):
        if self.rolagem is None:
            self._timer.stop()
            return
        self.t = time.perf_counter() - self._inicio
        if not getattr(self, "_revelado", True) and self.t >= self.rolagem.duracao:
            self._revelado = True   # o dado parou: o resultado vai pro histórico e pro chat agora
            self.revelar.emit(self.rolagem.r)
        placar = TEMPO_PLACAR * (0.5 if self.fila else 1.0)
        if self.t > self.rolagem.duracao + placar + TEMPO_SUMIR:
            self._proxima()
            return
        (self.gl or self).update()

    def _proxima(self):
        if self.rolagem is not None and not getattr(self, "_revelado", True):
            self._revelado = True
            self.revelar.emit(self.rolagem.r)
        self.rolagem = None
        if self.fila:
            self._calcular(self.fila.pop(0))
            return
        self._timer.stop()
        self.hide()
        self.terminou.emit()

    def _sem_gl(self, motivo):
        """OpenGL falhou neste PC: daqui pra frente, plano B."""
        self.motivo_sem_gl = motivo
        if self.gl is not None:
            self.gl.hide()
            self.gl.deleteLater()
            self.gl = None
        try:
            from ..seguranca import registrar_erro
            registrar_erro(f"Dados 3D sem OpenGL (usando o desenho simples): {motivo}")
        except Exception:
            pass
        self.update()

    @property
    def usando_gl(self) -> bool:
        return self.gl is not None

    # ------------------------------------------------------------ desenho
    def posicionar(self):
        self.setGeometry(0, 0, self.mesa.width(), self.mesa.height())
        if self.gl is not None:
            self.gl.setGeometry(self.rect())
        self.raise_()

    def paintEvent(self, ev):
        if self.gl is not None or self.rolagem is None:
            return
        from . import render_2d
        p = QPainter(self)
        render_2d.desenhar(p, self.rolagem, self.t, self.width(), self.height())
        self.desenhar_placar(p, self.width(), self.height())
        p.end()

    def desenhar_critico(self, p: QPainter, w: int, h: int):
        """v0.45.2 — 20 natural: onda dourada, faíscas, brilho e "ACERTO CRÍTICO!".
        1 natural: a tela pisca vermelho, fumaça escura, rachaduras e "FALHA CRÍTICA" caindo e tremendo."""
        import math
        import random
        import numpy as np
        from PyQt6.QtGui import QPainterPath, QRadialGradient
        from .cena3d import TAMANHO_DADO, camera, projetar
        rol = self.rolagem
        if rol is None or getattr(rol, "critico", None) is None:
            return
        dt = self.t - rol.duracao
        if dt < 0 or dt > 2.6:
            return
        k, valor = rol.critico
        visao, proj, *_ = camera(w, h)
        pos = np.array(rol.quadro(self.t)[k][0], dtype=float)
        xy, _z = projetar(np.array([pos, pos + np.array([TAMANHO_DADO, 0.0, 0.0])]), visao, proj, w, h)
        c = QPointF(float(xy[0][0]), float(xy[0][1]))
        raio = max(14.0, math.hypot(*(xy[1] - xy[0])) * 1.25)
        some = 1.0 if dt < 2.0 else max(0.0, 1 - (dt - 2.0) / 0.6)
        rnd = random.Random(int(rol.r.get("semente") or 7))
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        if valor == 20:
            ouro, claro = QColor(255, 196, 60), QColor(255, 246, 200)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
            # brilho pulsando em volta do dado
            rg = raio * (2.3 + 0.35 * math.sin(dt * 9))
            g = QRadialGradient(c, rg)
            g.setColorAt(0, QColor(255, 230, 140, int(150 * some)))
            g.setColorAt(0.45, QColor(255, 180, 40, int(70 * some)))
            g.setColorAt(1, QColor(255, 160, 0, 0))
            p.setBrush(g)
            p.drawEllipse(c, rg, rg)
            # raios de luz girando
            p.setPen(Qt.PenStyle.NoPen)
            for j in range(10):
                ang = j * math.pi / 5 + dt * 0.8
                comp = raio * (3.2 + 0.6 * math.sin(dt * 5 + j))
                larg = 0.09
                pol = QPainterPath()
                pol.moveTo(c)
                pol.lineTo(c + QPointF(math.cos(ang - larg) * comp, math.sin(ang - larg) * comp))
                pol.lineTo(c + QPointF(math.cos(ang + larg) * comp, math.sin(ang + larg) * comp))
                pol.closeSubpath()
                gr = QRadialGradient(c, comp)
                gr.setColorAt(0, QColor(255, 220, 120, int(90 * some)))
                gr.setColorAt(1, QColor(255, 200, 80, 0))
                p.fillPath(pol, gr)
            # onda de choque
            if dt < 0.7:
                s = dt / 0.7
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor(255, 220, 120, int(230 * (1 - s))), 3 + 9 * (1 - s)))
                p.drawEllipse(c, raio * (1 + 6 * s), raio * (1 + 6 * s))
                p.setPen(Qt.PenStyle.NoPen)
            # faíscas voando (com um pouco de gravidade)
            for _j in range(34):
                ang = rnd.uniform(0, 2 * math.pi)
                vel = rnd.uniform(2.5, 6.5) * raio
                vida = rnd.uniform(0.9, 1.7)
                if dt > vida:
                    continue
                x = c.x() + math.cos(ang) * vel * dt
                y = c.y() + math.sin(ang) * vel * dt + 260 * dt * dt
                a = (1 - dt / vida) * some
                tam = rnd.uniform(1.6, 3.6) * (1 - dt / vida * 0.5)
                p.setBrush(QColor(claro.red(), claro.green(), claro.blue(), int(255 * a)))
                p.drawEllipse(QPointF(x, y), tam, tam)
                p.setBrush(QColor(ouro.red(), ouro.green(), ouro.blue(), int(110 * a)))
                p.drawEllipse(QPointF(x, y), tam * 2.4, tam * 2.4)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            texto, cor, contorno = "ACERTO CRÍTICO!", QColor(255, 214, 80), QColor(70, 40, 0)
            escala = 1 + 0.7 * max(0.0, 1 - dt / 0.22)               # "pop"
            desloc = QPointF(0, 0)
        else:
            # (v0.65.1) borda vermelha pulsando, FENDAS com profundidade e FUMAÇA com volume (efeitos_critico.py)
            from . import efeitos_critico as fx
            semente = int(rol.r.get("semente") or 7)
            fx.desenhar_vinheta(p, w, h, max(0.0, 1 - dt / 1.1) * some)
            fx.desenhar_rachaduras(p, c, raio, dt, some, semente)
            fx.desenhar_fumaca(p, c, raio, dt, some, semente)
            texto, cor, contorno = "FALHA CRÍTICA", QColor(235, 60, 50), QColor(30, 0, 0)
            escala = 1.0
            cai = min(1.0, dt / 0.35)                                 # cai de cima e quica
            quica = abs(math.sin(cai * math.pi * 1.5)) * (1 - cai) * 30
            treme = math.sin(dt * 55) * 6 * max(0.0, 1 - dt / 0.9)
            desloc = QPointF(treme, -(1 - cai) * 60 - quica)
        p.restore()
        # o texto vai por cima de tudo (até do placar) — desenhado no fim de desenhar_placar
        self._texto_critico = (texto, cor, contorno, escala, desloc, c, raio, dt, some)

    def _desenhar_texto_critico(self, p: QPainter, w: int, h: int):
        from PyQt6.QtGui import QPainterPath
        dados = getattr(self, "_texto_critico", None)
        self._texto_critico = None
        if not dados:
            return
        texto, cor, contorno, escala, desloc, c, raio, dt, some = dados
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # embaixo do dado (com contorno escuro pra ler em qualquer fundo); sem espaço, em cima
        fonte = QFont()
        from ..ui.tema import tema_atual
        fonte.setFamily(tema_atual()["fonte_titulo"].split(",")[0].strip("'\" "))
        fonte.setPixelSize(int(34 * escala))
        fonte.setBold(True)
        caminho = QPainterPath()
        caminho.addText(0, 0, fonte, texto)
        r_t = caminho.boundingRect()
        y = c.y() + raio * 1.4 + r_t.height()
        if y > h - 10:
            y = c.y() - raio * 1.4
        alvo = QPointF(c.x() - r_t.width() / 2, y) + desloc
        alvo.setX(max(8.0, min(w - r_t.width() - 8, alvo.x())))
        alvo.setY(max(r_t.height() + 8, min(h - 8, alvo.y())))
        caminho.translate(alvo)
        p.setOpacity(min(1.0, dt / 0.12) * some)
        p.setPen(QPen(contorno, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(caminho)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(cor)
        p.drawPath(caminho)
        p.restore()

    def desenhar_placar(self, p: QPainter, w: int, h: int):
        """Quem rolou e o total, depois que os dados param. Some sozinho."""
        rol = self.rolagem
        if rol is None:
            return
        try:
            # (v0.65.1) o crítico é desenhado numa imagem comum e colado depois: degradê com transparência direto
            # na superfície da placa de vídeo saía PRETO (a tela inteira ficava preta na falha crítica)
            dt = self.t - rol.duracao
            if getattr(rol, "critico", None) is not None and 0 <= dt <= 2.6:
                from PyQt6.QtGui import QImage
                quadro = QImage(max(1, w), max(1, h), QImage.Format.Format_ARGB32_Premultiplied)
                quadro.fill(Qt.GlobalColor.transparent)
                pq = QPainter(quadro)
                try:
                    self.desenhar_critico(pq, w, h)   # (20 / 1 natural: animação em volta do d20)
                finally:
                    pq.end()
                p.drawImage(0, 0, quadro)
        except Exception as erro:   # enfeite: nunca derruba a rolagem
            from ..seguranca import registrar_erro
            registrar_erro(f"Animação de crítico falhou: {erro!r}")
            rol.critico = None
        if self.t < rol.duracao - 0.15:
            self._texto_critico = None
            return
        try:
            self._desenhar_placar(p, w, h)
        finally:
            try:
                self._desenhar_texto_critico(p, w, h)
            except Exception as erro:
                from ..seguranca import registrar_erro
                registrar_erro(f"Texto do crítico falhou: {erro!r}")

    def _desenhar_placar(self, p: QPainter, w: int, h: int):
        rol = self.rolagem
        r = rol.r
        dt = self.t - rol.duracao
        placar = TEMPO_PLACAR * (0.5 if self.fila else 1.0)
        alfa = 1.0 if dt < placar else max(0.0, 1 - (dt - placar) / TEMPO_SUMIR)
        entrada = min(1.0, max(0.0, (dt + 0.15) / 0.25))
        from ..ui.tema import tema_atual
        t = tema_atual()
        destaque = QColor(t["destaque"])
        natural = r.get("d20")
        if natural == 20:
            destaque = QColor("#ffd24a")
        elif natural == 1:
            destaque = QColor("#e04040")
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setOpacity(alfa * entrada)
        quem = r.get("quem", "?")
        motivo = r.get("motivo") or ""
        linha1 = quem + (f" · {motivo}" if motivo else "") + ("  (privada)" if r.get("privada") else "")
        linha3 = r.get("detalhes") or r.get("expr", "")
        f1, f2, f3 = QFont(), QFont(t["fonte_titulo"].split(",")[0].strip("'\" ")), QFont()
        f1.setPixelSize(15)
        f1.setBold(True)
        f2.setPixelSize(46)
        f2.setBold(True)
        f3.setPixelSize(12)
        p.setFont(f1)
        larg = max(p.fontMetrics().horizontalAdvance(linha1), 120)
        p.setFont(f3)
        larg = max(larg, p.fontMetrics().horizontalAdvance(linha3[:70])) + 48
        alt = 116 + (22 if natural in (1, 20) else 0)
        caixa = QRectF((w - larg) / 2, 26 - (1 - entrada) * 14, larg, alt)
        g = QLinearGradient(caixa.topLeft(), caixa.bottomLeft())
        g.setColorAt(0, QColor(t["painel2"]))
        g.setColorAt(1, QColor(t["painel"]))
        p.setPen(QPen(destaque, 2))
        p.setBrush(g)
        p.drawRoundedRect(caixa, 10, 10)
        y = caixa.top() + 10
        p.setFont(f1)
        p.setPen(QColor(t["texto"]))
        p.drawText(QRectF(caixa.left(), y, larg, 20), Qt.AlignmentFlag.AlignCenter, linha1)
        p.setFont(f2)
        p.setPen(destaque)
        p.drawText(QRectF(caixa.left(), y + 20, larg, 54), Qt.AlignmentFlag.AlignCenter, str(r.get("total", "")))
        y += 76
        if natural in (1, 20):
            f4 = QFont(f1)
            f4.setPixelSize(13)
            p.setFont(f4)
            p.drawText(QRectF(caixa.left(), y, larg, 20), Qt.AlignmentFlag.AlignCenter,
                       "20 NATURAL!" if natural == 20 else "1 natural…")
            y += 22
        p.setFont(f3)
        p.setPen(QColor(t["fraco"]))
        p.drawText(QRectF(caixa.left() + 10, y, larg - 20, 18), Qt.AlignmentFlag.AlignCenter,
                   p.fontMetrics().elidedText(linha3, Qt.TextElideMode.ElideRight, int(larg - 20)))
        p.restore()
