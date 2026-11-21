"""
🏢 Andares (v0.46) — pedido do Manel: "um prédio de 3 andares… cada jogador vê só o andar dele".

Cada ANDAR é uma aba (cenário) com o próprio chão, paredes, camadas, luz, névoa, gás… As abas de um
mesmo PRÉDIO ficam ligadas (cena.predio = o mesmo id; cena.andar = 0 térreo, 1, 2… ou -1 subsolo).
  - Ao vivo é o PRÉDIO inteiro: cada jogador recebe só o andar onde está o token dele.
  - ESCADA: objeto ligado a outra escada no andar de cima/baixo. O jogador dá duplo clique na escada
    (perto dela) e o token vai pro outro andar, chegando na escada correspondente.
  - O mestre troca de andar pelas abas, cria andar acima/abaixo e move token de andar (botão direito).
"""

import uuid

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPen


def nome_andar(n: int) -> str:
    if n == 0:
        return "Térreo"
    if n > 0:
        return f"{n}º andar"
    return f"Subsolo {abs(n)}" if n < -1 else "Subsolo"


def do_predio(cenas, cena) -> list:
    """Os andares do prédio da cena (de baixo pra cima). Sem prédio: só ela."""
    predio = getattr(cena, "predio", None)
    if not predio:
        return [cena]
    return sorted([c for c in cenas if getattr(c, "predio", None) == predio], key=lambda c: c.andar)


def garantir_predio(cena):
    if not getattr(cena, "predio", None):
        cena.predio = uuid.uuid4().hex[:12]
        cena.andar = getattr(cena, "andar", 0) or 0


def andar_vizinho(cenas, cena, delta: int):
    alvo = getattr(cena, "andar", 0) + delta
    return next((c for c in do_predio(cenas, cena) if c.andar == alvo), None)


# ====================================================================== desenho da escada (catálogo)
def desenhar_escada(p: QPainter, r: QRectF):
    """Escada vista de cima: degraus que sobem (mais claros) em direção à seta."""
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(30, 22, 16), 2))
    p.setBrush(QColor(92, 70, 50))
    p.drawRect(r.adjusted(2, 2, -2, -2))
    n = 7
    passo = (r.height() - 8) / n
    for k in range(n):
        y = r.top() + 4 + k * passo
        g = QLinearGradient(0, y, 0, y + passo)
        claro = 150 - k * 11
        g.setColorAt(0, QColor(claro + 30, claro + 12, claro - 10))
        g.setColorAt(1, QColor(claro - 10, claro - 25, claro - 40))
        p.setPen(QPen(QColor(35, 26, 18), 1.4))
        p.setBrush(g)
        p.drawRect(QRectF(r.left() + 6, y, r.width() - 12, passo))
    # corrimãos
    p.setPen(QPen(QColor(55, 40, 28), 3))
    p.drawLine(QPointF(r.left() + 5, r.top() + 4), QPointF(r.left() + 5, r.bottom() - 4))
    p.drawLine(QPointF(r.right() - 5, r.top() + 4), QPointF(r.right() - 5, r.bottom() - 4))
    # seta "sobe"
    p.setPen(QPen(QColor(240, 225, 190, 200), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    cx = r.center().x()
    p.drawLine(QPointF(cx, r.bottom() - 10), QPointF(cx, r.top() + 12))
    p.drawLine(QPointF(cx, r.top() + 12), QPointF(cx - 7, r.top() + 20))
    p.drawLine(QPointF(cx, r.top() + 12), QPointF(cx + 7, r.top() + 20))
    p.restore()
