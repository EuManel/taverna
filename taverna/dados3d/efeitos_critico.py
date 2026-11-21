"""
💀 Efeitos da FALHA CRÍTICA (1 natural) — v0.65.1, pedido do Manel ("a tela fica preta", "fumaça volumétrica",
"rachado com profundidade").

  - a fumaça é feita de "bolotas" com VOLUME: um sprite gerado uma vez (ruído fractal → densidade), iluminado de
    cima (o alto da bolota claro, a barriga escura) e com borda macia; várias, girando, crescendo e subindo;
  - o rachado é uma FENDA de verdade: largura que afina até a ponta, fundo escuro com um brilho vermelho lá dentro,
    a borda de um lado pegando luz e a do outro em sombra, rachadurinhas saindo dos lados e lascas soltas.

Tudo isso é desenhado numa QImage comum (no processador) e só depois colado por cima do dado: desenhar degradê com
transparência direto na superfície da placa de vídeo saía PRETO (era a "tela toda preta").
"""

import math
import random

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QImage, QPainter, QPainterPath, QPen, QPolygonF, QRadialGradient

_SPRITES: list = []


def _ruido(n: int, rng: np.random.Generator, oitavas: int = 5) -> np.ndarray:
    """Ruído fractal (somando escalas de ruído suave), 0..1."""
    saida = np.zeros((n, n), np.float32)
    amp, total = 1.0, 0.0
    for o in range(oitavas):
        tam = 2 ** (o + 2)
        base = rng.random((tam + 1, tam + 1)).astype(np.float32)
        idx = np.linspace(0, tam, n, dtype=np.float32)
        i0 = np.floor(idx).astype(int).clip(0, tam - 1)
        f = idx - i0
        f = f * f * (3 - 2 * f)
        a = base[i0][:, i0] * (1 - f)[None, :] + base[i0][:, i0 + 1] * f[None, :]
        b = base[i0 + 1][:, i0] * (1 - f)[None, :] + base[i0 + 1][:, i0 + 1] * f[None, :]
        saida += amp * (a * (1 - f)[:, None] + b * f[:, None])
        total += amp
        amp *= 0.55
    return saida / total


def sprites_fumaca(n: int = 128) -> list:
    """3 bolotas de fumaça (QImage pré-multiplicada), com volume (luz de cima)."""
    if _SPRITES:
        return _SPRITES
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) / (n - 1) * 2 - 1
    raio = np.sqrt(xx * xx + yy * yy)
    for semente in (11, 23, 37):
        rng = np.random.default_rng(semente)
        r = _ruido(n, rng)
        dens = np.clip((1.0 - raio * (0.85 + 0.45 * r)) * 1.8, 0, 1) * (0.55 + 0.6 * r)
        dens = np.clip(dens, 0, 1)
        # luz de cima-esquerda: onde a densidade "sobe" na direção da luz fica claro; a barriga fica escura
        sombra = np.clip(np.roll(np.roll(dens, -5, 0), -3, 1) - dens, -1, 1)
        luz = np.clip(0.55 + 0.32 * (-yy) - 2.2 * sombra + 0.3 * (r - 0.5), 0.08, 1.0)
        cor = np.stack([luz * 0.70, luz * 0.62, luz * 0.72], -1)          # cinza-fumaça levemente arroxeado
        alfa = np.clip(dens * 1.25, 0, 1) ** 1.15
        img = np.zeros((n, n, 4), np.uint8)
        img[..., 0] = (cor[..., 2] * alfa * 255).astype(np.uint8)            # B
        img[..., 1] = (cor[..., 1] * alfa * 255).astype(np.uint8)            # G
        img[..., 2] = (cor[..., 0] * alfa * 255).astype(np.uint8)            # R
        img[..., 3] = (alfa * 255).astype(np.uint8)
        _SPRITES.append(QImage(img.tobytes(), n, n, n * 4, QImage.Format.Format_ARGB32_Premultiplied).copy())
    return _SPRITES


def desenhar_fumaca(p: QPainter, c: QPointF, raio: float, dt: float, some: float, semente: int):
    """Bolotas subindo do dado, crescendo, girando devagar e se desfazendo."""
    sprites = sprites_fumaca()
    rnd = random.Random(semente * 7 + 3)
    for j in range(22):
        atraso = j * 0.05
        s = dt - atraso
        vida = rnd.uniform(1.6, 2.2)
        lado = rnd.uniform(-0.7, 0.7)
        giro0, giro_v = rnd.uniform(0, 360), rnd.uniform(-40, 40)
        qual = rnd.randrange(len(sprites))
        if s <= 0 or s > vida:
            continue
        sobe = s / vida
        x = c.x() + lado * raio + math.sin(s * 2.2 + j) * raio * 0.35
        y = c.y() - raio * 0.9 - (sobe ** 0.9) * raio * 2.1    # nasce atrás/acima do dado (o "1" continua à vista)
        tam = raio * (1.1 + sobe * 2.5)
        a = min(0.85, math.sin(math.pi * min(1.0, s / vida)) ** 0.7 * 0.95) * some
        p.save()
        p.translate(x, y)
        p.rotate(giro0 + giro_v * s)
        p.setOpacity(a)
        p.drawImage(QRectF(-tam / 2, -tam / 2, tam, tam), sprites[qual])
        p.restore()
    p.setOpacity(1.0)


def _fenda(p: QPainter, pontos: list, larg0: float, alfa: float):
    """Uma fenda que afina até a ponta: fundo escuro com brilho vermelho, borda clara de um lado e escura do outro."""
    if len(pontos) < 2:
        return
    esq, dir_ = [], []
    n = len(pontos)
    for i, pt in enumerate(pontos):
        a = pontos[max(0, i - 1)]
        b = pontos[min(n - 1, i + 1)]
        dx, dy = b.x() - a.x(), b.y() - a.y()
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = larg0 * (1 - i / (n - 1)) ** 0.9 + 0.3
        esq.append(QPointF(pt.x() + nx * w, pt.y() + ny * w))
        dir_.append(QPointF(pt.x() - nx * w, pt.y() - ny * w))
    poli = QPolygonF(esq + list(reversed(dir_)))
    A = int(255 * alfa)
    # sombra fora (a beira de baixo-direita afunda)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(0, 0, 0, int(70 * alfa)))
    p.drawPolygon(poli.translated(1.2, 1.4))
    # o fundo da fenda
    p.setBrush(QColor(12, 4, 4, A))
    p.drawPolygon(poli)
    # brilho vermelho lá no fundo (só no meio da fenda)
    p.setPen(QPen(QColor(170, 28, 14, int(95 * alfa)), max(0.5, larg0 * 0.28), Qt.PenStyle.SolidLine,
                  Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    meio = QPainterPath(pontos[0])
    for pt in pontos[1:max(2, int(n * 0.7))]:
        meio.lineTo(pt)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(meio)
    # as bordas: a de cima-esquerda pega luz, a outra fica na sombra
    luz = QPainterPath(esq[0])
    for pt in esq[1:]:
        luz.lineTo(pt)
    escuro = QPainterPath(dir_[0])
    for pt in dir_[1:]:
        escuro.lineTo(pt)
    p.setPen(QPen(QColor(255, 240, 220, int(150 * alfa)), 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawPath(luz)
    p.setPen(QPen(QColor(0, 0, 0, int(160 * alfa)), 1.1, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawPath(escuro)


def desenhar_rachaduras(p: QPainter, c: QPointF, raio: float, dt: float, some: float, semente: int):
    """Fendas saindo do dado (crescem rápido), com galhos e lascas."""
    rnd = random.Random(semente * 13 + 5)
    cresce = min(1.0, dt / 0.28)
    cresce = 1 - (1 - cresce) ** 3
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    for j in range(7):
        ang = j / 7 * 2 * math.pi + rnd.uniform(-0.35, 0.35)
        comp_total = raio * rnd.uniform(1.7, 2.9) * cresce
        passos = 9
        pts = [QPointF(c.x() + math.cos(ang) * raio * 0.95, c.y() + math.sin(ang) * raio * 0.78)]
        x, y = pts[0].x(), pts[0].y()
        for _s in range(passos):
            ang += rnd.uniform(-0.5, 0.5)
            passo = comp_total / passos
            x += math.cos(ang) * passo
            y += math.sin(ang) * passo * 0.75            # (a mesa em perspectiva: achata um pouco)
            pts.append(QPointF(x, y))
        _fenda(p, pts, raio * rnd.uniform(0.07, 0.11), some)
        # galhinhos finos saindo do lado
        for _g in range(2):
            i0 = rnd.randrange(2, passos - 1)
            a2 = ang + rnd.choice((-1, 1)) * rnd.uniform(0.6, 1.2)
            gx, gy = pts[i0].x(), pts[i0].y()
            galho = [QPointF(gx, gy)]
            for _s in range(4):
                a2 += rnd.uniform(-0.5, 0.5)
                gx += math.cos(a2) * comp_total / passos * 0.6
                gy += math.sin(a2) * comp_total / passos * 0.45
                galho.append(QPointF(gx, gy))
            _fenda(p, galho, raio * 0.035, some * 0.9)
    # lascas soltas pulando no começo
    if dt < 0.9:
        for _l in range(10):
            ang = rnd.uniform(0, 2 * math.pi)
            vel = rnd.uniform(1.2, 2.6) * raio
            x = c.x() + math.cos(ang) * vel * dt
            y = c.y() + math.sin(ang) * vel * dt * 0.7 - 120 * dt + 380 * dt * dt
            a = max(0.0, 1 - dt / 0.9) * some
            tam = rnd.uniform(1.6, 3.4)
            p.save()
            p.translate(x, y)
            p.rotate(rnd.uniform(0, 360) + dt * 500)
            p.setPen(QPen(QColor(20, 10, 8, int(200 * a)), 0.7))
            p.setBrush(QColor(150, 135, 120, int(230 * a)))
            p.drawPolygon(QPolygonF([QPointF(-tam, -tam * 0.4), QPointF(tam, -tam * 0.6), QPointF(tam * 0.4, tam)]))
            p.restore()
    p.restore()


def desenhar_vinheta(p: QPainter, w: int, h: int, k: float):
    """A borda da tela pulsando vermelho (no começo)."""
    if k <= 0:
        return
    g = QRadialGradient(QPointF(w / 2, h / 2), max(w, h) * 0.75)
    g.setColorAt(0.55, QColor(140, 0, 0, 0))
    g.setColorAt(1.0, QColor(150, 10, 10, int(150 * k)))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(g))
    p.drawRect(QRectF(0, 0, w, h))
