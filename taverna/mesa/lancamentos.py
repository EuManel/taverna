"""
Lançar efeitos (v0.41) — "um personagem joga uma bola de fogo".

Três jeitos, pra cada elemento:
  projétil — bola de fogo, cristal de gelo, bolha de ácido/veneno, orbe… voa em arco de quem lança até
             o alvo (com rastro) e ESTOURA lá;
  cone     — jato em cone: o elemento sai de quem lança e VAI PRA FRENTE de verdade, abrindo;
  linha    — jato reto (um raio, um jato de fogo/água).
O mestre (ou o jogador) ajusta a distância (arrastando), a abertura do cone, a largura da linha e a
velocidade. Opcional: deixar a área no chão quando termina (fogo onde a bola caiu, poça de ácido…).

Só animação: nada dá dano sozinho. Na Mesa 3D as partículas têm altura (a bola sobe em arco e vem pra
câmera); no 2D, o mesmo desenho rente ao chão. Respeita Gráficos (Médio = menos partículas).
Sem estado: tudo é função do tempo (desenha igual em todo PC).
"""

import math
import random
import time
import uuid

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QGraphicsObject

from ..config import CELULA

M = CELULA
TIPOS_LANCE = {"projetil": "☄ Projétil (bola, cristal, bolha…)", "cone": "🔺 Jato em cone",
               "linha": "➖ Jato em linha / raio"}
# elemento → (nome do projétil, cor principal, cor do miolo, brilha?)
ELEMENTOS = {
    "fogo": ("Bola de fogo", "#ff7a1a", "#fff1a0", True),
    "gelo": ("Cristal de gelo", "#9fdcff", "#ffffff", True),
    "acido": ("Bolha de ácido", "#9be02e", "#e8ff9a", False),
    "veneno": ("Bolha de veneno", "#7cb83a", "#cfeaa0", False),
    "eletrico": ("Raio", "#8ab8ff", "#ffffff", True),
    "agua": ("Bolha d'água", "#4aa3e0", "#dff3ff", False),
    "magia": ("Orbe mágico", "#b07aff", "#f3e8ff", True),
    "trevas": ("Orbe sombrio", "#3a1a55", "#8a5ab0", False),
    "luz": ("Lança de luz", "#fff2b0", "#ffffff", True),
    "sagrado": ("Raio radiante", "#ffd96a", "#ffffff", True),
    "lava": ("Bola de magma", "#ff5a10", "#ffd060", True),
}
# formato do projétil (v0.42): "auto" = o normal do elemento
PROJETEIS = {"auto": "Do elemento", "bola": "● Bola", "orbe": "◉ Orbe (com faíscas girando)",
             "missil": "➶ Míssil mágico (3 setas)", "cristal": "◆ Cristal", "bolha": "○ Bolha",
             "lanca": "➝ Lança", "raio": "⚡ Raio (risco de luz)"}
PROJETIL_DO_ELEMENTO = {"fogo": "bola", "lava": "bola", "gelo": "cristal", "acido": "bolha", "veneno": "bolha",
                        "agua": "bolha", "eletrico": "raio", "luz": "lanca", "sagrado": "raio",
                        "magia": "orbe", "trevas": "orbe"}
# elementos com cor escolhível (fogo negro, raio vermelho, magia de qualquer cor…)
CORES_LANCE = {"magia", "fogo", "eletrico", "luz", "sagrado", "trevas"}
CORES_PRONTAS = {
    "fogo": [("Normal", ""), ("Fogo azul", "#3a8cff"), ("Fogo verde", "#46e04a"), ("Fogo negro", "#2a1236"),
             ("Fogo roxo", "#a040ff"), ("Fogo branco", "#f4f0ff")],
    "eletrico": [("Normal", ""), ("Vermelho", "#ff3a3a"), ("Roxo", "#b05aff"), ("Verde", "#4aff6a"),
                 ("Dourado", "#ffd040"), ("Negro", "#30203a")],
}
LIMITES = {"dist": (0.5, 60.0), "abertura": (5.0, 120.0), "largura": (0.25, 6.0),
           "velocidade": (2.0, 80.0), "tam": (0.5, 12.0)}
JATO = 1.1   # segundos soltando o jato


def conferir(d: dict) -> dict | None:
    """Limpa um pedido (vindo de jogador pela rede): tipos e números dentro do razoável."""
    try:
        saida = {"elemento": d.get("elemento") if d.get("elemento") in ELEMENTOS else "fogo",
                 "tipo": d.get("tipo") if d.get("tipo") in TIPOS_LANCE else "projetil",
                 "projetil": d.get("projetil") if d.get("projetil") in PROJETEIS else "auto",
                 "x0": float(d["x0"]), "y0": float(d["y0"]), "x1": float(d["x1"]), "y1": float(d["y1"]),
                 "deixar": bool(d.get("deixar", False)), "cor": str(d.get("cor") or "")[:9],
                 "id": str(d.get("id") or uuid.uuid4().hex)[:40], "dono": str(d.get("dono") or "")[:60]}
        for chave, (lo, hi), padrao in (("abertura", LIMITES["abertura"], 53.0), ("largura", LIMITES["largura"], 1.5),
                                         ("velocidade", LIMITES["velocidade"], 14.0), ("tam", LIMITES["tam"], 3.0)):
            saida[chave] = max(lo, min(hi, float(d.get(chave, padrao))))
    except (KeyError, TypeError, ValueError):
        return None
    if any(math.isnan(v) or abs(v) > 1e6 for v in (saida["x0"], saida["y0"], saida["x1"], saida["y1"])):
        return None
    from .efeitos import cor_valida
    saida["cor"] = cor_valida(saida["cor"]) if saida["elemento"] in CORES_LANCE else ""
    dist = math.hypot(saida["x1"] - saida["x0"], saida["y1"] - saida["y0"]) / M
    lo, hi = LIMITES["dist"]
    if dist > hi:   # longe demais: encurta na mesma direção
        k = hi / dist
        saida["x1"] = saida["x0"] + (saida["x1"] - saida["x0"]) * k
        saida["y1"] = saida["y0"] + (saida["y1"] - saida["y0"]) * k
    elif dist < lo:
        return None
    return saida


def distancia_m(d) -> float:
    return math.hypot(d["x1"] - d["x0"], d["y1"] - d["y0"]) / M


def duracao(d) -> float:
    """Até quando a animação dura (s) — e quando a área (se 'deixar') aparece."""
    viagem = distancia_m(d) / d["velocidade"]
    if d["tipo"] == "projetil":
        return viagem + 0.9
    return JATO + viagem + 0.3


def chegada(d) -> float:
    """Quando o efeito chega (a área é deixada nessa hora)."""
    viagem = distancia_m(d) / d["velocidade"]
    return viagem if d["tipo"] == "projetil" else JATO * 0.6 + viagem


def area_deixada(d) -> dict:
    """A área de efeito que fica no chão no fim (se d['deixar'])."""
    ang = math.degrees(math.atan2(d["y1"] - d["y0"], d["x1"] - d["x0"])) % 360
    base = {"efeito": d["elemento"], "cor": d.get("cor", ""), "nome": "", "angulo": ang}
    if d["tipo"] == "projetil":
        base.update({"forma": "circulo", "tamanho": d["tam"], "x": d["x1"], "y": d["y1"], "angulo": 0})
    elif d["tipo"] == "cone":
        base.update({"forma": "cone", "tamanho": distancia_m(d), "x": d["x0"], "y": d["y0"]})
    else:
        base.update({"forma": "linha", "tamanho": distancia_m(d), "largura": d["largura"], "x": d["x0"], "y": d["y0"]})
    return base


def _mais_claro(cor: QColor) -> QColor:
    """Miolo: a cor puxada pro branco (o centro de um fogo azul é quase branco-azulado)."""
    return QColor(int(cor.red() + (255 - cor.red()) * 0.7), int(cor.green() + (255 - cor.green()) * 0.7),
                  int(cor.blue() + (255 - cor.blue()) * 0.7))


# ====================================================================== o desenho
class LancamentoItem(QGraphicsObject):
    def __init__(self, d: dict):
        super().__init__()
        from ..graficos import nivel
        self.d = d
        self.n = nivel()
        self.t0 = time.monotonic()
        self.dur = duracao(d)
        self.setZValue(940_000)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        nome, cor, miolo, brilha = ELEMENTOS[d["elemento"]]
        self.cor, self.miolo, self.brilha = QColor(cor), QColor(miolo), brilha
        if d.get("cor") and d["elemento"] in CORES_LANCE:   # fogo negro, raio vermelho, magia verde…
            self.cor = QColor(d["cor"])
            escuro = self.cor.value() < 90
            self.miolo = self.cor.lighter(260) if escuro else _mais_claro(self.cor)
            if escuro:   # cor escura não "soma luz": desenha por cima, com o miolo aceso
                self.brilha = False
        self.forma = d.get("projetil", "auto")
        if self.forma == "auto":
            self.forma = PROJETIL_DO_ELEMENTO.get(d["elemento"], "bola")
        self.a = QPointF(d["x0"], d["y0"])
        self.b = QPointF(d["x1"], d["y1"])
        self.dist = distancia_m(d)
        self.dir = math.atan2(d["y1"] - d["y0"], d["x1"] - d["x0"])
        rnd = random.Random(hash(d.get("id", "")) & 0xFFFFFF)
        qtd = (40, 90, 160)[self.n] if d["tipo"] != "projetil" else (8, 16, 26)[self.n]
        self.parts = [(rnd.random(), rnd.random(), rnd.random(), rnd.random()) for _ in range(qtd)]
        self._timer = QTimer(self)
        self._timer.setInterval((50, 33, 16)[self.n])
        self._timer.timeout.connect(self._passo)
        self._timer.start()

    def boundingRect(self) -> QRectF:
        r = QRectF(self.a, self.b).normalized()
        folga = max(self.dist * M * 0.6, 4 * M) + 4 * M
        return r.adjusted(-folga, -folga, folga, folga)

    def _passo(self):
        from . import luz_dinamica
        t = time.monotonic() - self.t0
        cena = self.scene()
        if t >= self.dur:
            self._timer.stop()
            if cena is not None:
                luz_dinamica.definir(cena, "lance:" + self.d.get("id", ""), None)
                cena.removeItem(self)
            self.deleteLater()
            return
        if cena is not None:
            try:
                luz_dinamica.definir(cena, "lance:" + self.d.get("id", ""), self._luz(t))
            except Exception:   # (a luz é enfeite: nunca derruba o lançamento)
                pass
        self.update()

    # --- a luz que ele faz (iluminação dinâmica, paredes bloqueiam)
    LUZ = {"fogo": (4.5, 1.0), "lava": (4.5, 1.0), "eletrico": (5.0, 1.0), "magia": (3.5, 0.85),
           "luz": (5.0, 1.0), "sagrado": (5.0, 1.0), "gelo": (2.5, 0.55), "acido": (2.0, 0.45),
           "trevas": (0.0, 0.0), "veneno": (0.0, 0.0), "agua": (0.0, 0.0)}

    def _luz(self, t):
        el = self.d["elemento"]
        alcance, forca = self.LUZ.get(el, (3.0, 0.7))
        if self.d.get("cor") and self.cor.value() < 90:   # fogo negro quase não ilumina
            alcance, forca = alcance * 0.5, forca * 0.35
        if forca <= 0:
            return None
        cor = self.cor.name()
        viagem = max(0.05, self.dist / self.d["velocidade"])
        ax, ay, bx, by = self.a.x(), self.a.y(), self.b.x(), self.b.y()
        if self.d["tipo"] == "projetil":
            s = t / viagem
            if s < 1.0:
                pisca = 0.75 + 0.25 * math.sin(t * 40) if self.forma == "raio" else 1.0
                return {"x": ax + (bx - ax) * s, "y": ay + (by - ay) * s, "fraco": alcance, "cor": cor,
                        "brilho": forca * pisca}
            f = (t - viagem) / 0.9   # estouro: clarão grande que vai apagando
            if f >= 1:
                return None
            R = max(1.2, self.d["tam"]) if self.d.get("deixar") or el in ("fogo", "lava") else 1.2
            return {"x": bx, "y": by, "fraco": alcance + R * 2.2 * (1 - f * 0.5), "cor": cor,
                    "brilho": forca * (1 - f) ** 1.4}
        # jato: a luz anda com as labaredas (no meio do que já saiu)
        fim_jato = JATO + viagem
        if t > fim_jato:
            return None
        frente = min(1.0, t / viagem)
        meio = frente * 0.5
        apaga = 1.0 if t < JATO else max(0.0, 1 - (t - JATO) / viagem)
        pisca = 0.7 + 0.3 * math.sin(t * 35) if el in ("eletrico", "luz", "sagrado") else 1.0
        return {"x": ax + (bx - ax) * meio, "y": ay + (by - ay) * meio,
                "fraco": alcance + self.dist * 0.55 * frente, "cor": cor, "brilho": forca * apaga * pisca}

    # --- ajudantes (tudo desenhado em pixels da tela, com a perspectiva da Mesa 3D se ligada)
    def paint(self, p: QPainter, option, widget=None):
        t = time.monotonic() - self.t0
        if t >= self.dur:
            return
        from . import camera3d
        try:
            self._cam = camera3d.Camera(p)
            self._3d = camera3d.ligada()
            p.save()
            p.resetTransform()
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setPen(Qt.PenStyle.NoPen)
            if self.d["tipo"] == "projetil":
                self._projetil(p, t)
            else:
                self._jato(p, t)
            p.restore()
        except Exception as erro:   # (erro dentro de paint() fecha o programa)
            from ..seguranca import registrar_erro
            registrar_erro(f"Lançamento não desenhou: {erro!r}")
            self.dur = 0

    def _tela(self, x, y, z):
        """Ponto da cena (x, y) na altura z (unidades da cena) → (ponto na tela, escala de tamanho)."""
        z = z if self._3d else 0.0
        z = max(0.0, min(z, self._cam.z_max()))
        return self._cam.projetar(QPointF(x, y), z), self._cam.escala * self._cam.fator(z)

    def _bola(self, p, x, y, z, raio_m, cor, alfa, miolo=False):
        from .efeitos3d import _sprite
        c, esc = self._tela(x, y, z)
        r = raio_m * M * esc
        if r < 0.4 or alfa <= 0.01:
            return
        p.setOpacity(max(0.0, min(1.0, alfa)))
        p.drawPixmap(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r), _sprite(cor, miolo)[0], QRectF(0, 0, 64, 64))

    def _brilho(self, p, ligado):
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus if ligado
                             else QPainter.CompositionMode.CompositionMode_SourceOver)

    # --- projétil: voa em arco e estoura
    def _projetil(self, p, t):
        el = self.d["elemento"]
        forma = self.forma
        viagem = max(0.05, self.dist / self.d["velocidade"])
        ax, ay, bx, by = self.a.x(), self.a.y(), self.b.x(), self.b.y()
        alto = 1.1 * M   # sai da altura da mão
        arco = 0.0 if forma in ("raio", "lanca", "missil") else min(2.5, self.dist * 0.18) * M

        def pos(s):
            s = max(0.0, min(1.0, s))
            return ax + (bx - ax) * s, ay + (by - ay) * s, alto * (1 - s) + 4 * arco * s * (1 - s) + 0.3 * M * s

        s = t / viagem
        if forma == "raio":   # risco de luz de quem lança até a ponta
            if s <= 1.15:
                ponta = min(1.0, s)
                rnd = random.Random(int(t * 14))
                pts = []
                for k in range(13):
                    u = ponta * k / 12
                    x, y, z = pos(u)
                    tremor = (0 if k in (0, 12) else rnd.uniform(-0.35, 0.35)) * M
                    q, _e = self._tela(x - math.sin(self.dir) * tremor, y + math.cos(self.dir) * tremor, z)
                    pts.append(q)
                self._linha(p, pts, ((10, self.cor, 0.35), (4, self.cor, 0.7), (1.6, self.miolo, 1.0)))
                x, y, z = pos(ponta)
                self._brilho(p, self.brilha)
                self._bola(p, x, y, z, 0.35, self.cor, 0.9, True)
        elif forma == "missil":   # míssil mágico: 3 setinhas que vão serpenteando até o alvo
            for k in range(3):
                sk = (t - k * 0.09) / viagem
                if not 0 <= sk < 1.0:
                    continue
                onda = math.sin(sk * math.pi * 3 + k * 2.1) * 0.6 * M * (1 - sk) * (k - 1)
                x, y, z = pos(sk)
                x += -math.sin(self.dir) * onda
                y += math.cos(self.dir) * onda
                self._brilho(p, self.brilha)
                for j in range(1, 8):   # rastro
                    tx, ty, tz = pos(sk - j * 0.015)
                    self._bola(p, tx - math.sin(self.dir) * onda, ty + math.cos(self.dir) * onda, tz,
                               0.09 * (1 - j / 8), self.cor, 0.6 * (1 - j / 8))
                self._seta(p, x, y, z, 0.42, 0.13)
        elif s < 1.0:
            x, y, z = pos(s)
            self._brilho(p, self.brilha)
            for k, (r1, r2, r3, r4) in enumerate(self.parts):   # rastro
                atras = s - (k + 1) * 0.012 * (1.5 if el == "fogo" else 1)
                if atras < 0:
                    break
                tx, ty, tz = pos(atras)
                lado = (r1 - 0.5) * 0.3 * M
                tx += -math.sin(self.dir) * lado
                ty += math.cos(self.dir) * lado
                fade = 1 - k / len(self.parts)
                if el in ("fogo", "lava"):
                    cor = self.miolo if k < 3 else (self.cor if k < len(self.parts) * 0.6 else QColor(60, 50, 45))
                    self._bola(p, tx, ty, tz + r2 * 0.2 * M, 0.28 * fade + 0.1, cor, 0.7 * fade, k < 3)
                elif forma == "cristal" or el == "gelo":
                    self._bola(p, tx, ty, tz, 0.05 + 0.05 * r3, QColor("#ffffff"), fade, True)
                else:
                    self._bola(p, tx, ty, tz, 0.1 * fade + 0.03, self.cor, 0.6 * fade)
            if forma == "cristal":   # cristal girando
                c, esc = self._tela(x, y, z)
                r = 0.32 * M * esc
                giro = t * 9
                pol = QPolygonF([c + QPointF(math.cos(giro + k * math.pi / 2) * r * (1.0 if k % 2 == 0 else 0.45),
                                             math.sin(giro + k * math.pi / 2) * r * (1.0 if k % 2 == 0 else 0.45))
                                 for k in range(4)])
                self._bola(p, x, y, z, 0.45, self.cor, 0.6)
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
                p.setOpacity(1.0)
                p.setBrush(_mais_claro(self.cor))
                p.setPen(QPen(QColor(255, 255, 255), 1.2))
                p.drawPolygon(pol)
                p.setPen(Qt.PenStyle.NoPen)
            elif forma == "bolha":   # corpo + reflexo
                self._bola(p, x, y, z, 0.32, self.cor, 0.85)
                self._bola(p, x - 0.08 * M, y - 0.08 * M, z, 0.1, self.miolo, 0.9, True)
            elif forma == "lanca":   # lança de luz comprida, apontando pra frente
                self._seta(p, x, y, z, 1.1, 0.09)
            elif forma == "orbe":   # orbe com faíscas girando em volta
                self._bola(p, x, y, z, 0.45, self.cor, 0.8)
                self._bola(p, x, y, z, 0.2, self.miolo, 1.0, True)
                for k in range(4):
                    ang = t * 7 + k * math.pi / 2
                    self._bola(p, x + math.cos(ang) * 0.4 * M, y + math.sin(ang) * 0.4 * M, z, 0.07,
                               self.miolo, 0.9, True)
            else:   # bola
                self._bola(p, x, y, z, 0.42, self.cor, 0.9)
                self._bola(p, x, y, z, 0.22, self.miolo, 1.0, True)
        # estouro no alvo
        tt = t - viagem
        if tt >= 0:
            self._estouro(p, tt / 0.9)

    def _linha(self, p, pts, camadas):
        self._brilho(p, self.brilha)
        for larg, cor, alfa in camadas:
            p.setOpacity(alfa)
            p.setPen(QPen(cor, larg * self._cam.escala, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                          Qt.PenJoinStyle.RoundJoin))
            p.drawPolyline(QPolygonF(pts))
        p.setPen(Qt.PenStyle.NoPen)

    def _seta(self, p, x, y, z, comp_m, larg_m):
        """Setinha/lança brilhante apontando na direção do voo."""
        c, esc = self._tela(x, y, z)
        L, W = comp_m * M * esc, larg_m * M * esc
        dx, dy = math.cos(self.dir), math.sin(self.dir)
        nx, ny = -dy, dx
        ponta = QPointF(c.x() + dx * L * 0.5, c.y() + dy * L * 0.5)
        tras = QPointF(c.x() - dx * L * 0.5, c.y() - dy * L * 0.5)
        if comp_m < 0.8:   # míssil: ponta de flecha (com o "V" atrás)
            W *= 1.6
            corpo = QPolygonF([ponta, QPointF(tras.x() + nx * W, tras.y() + ny * W),
                               QPointF(c.x() - dx * L * 0.15, c.y() - dy * L * 0.15),
                               QPointF(tras.x() - nx * W, tras.y() - ny * W)])
        else:              # lança: losango comprido
            corpo = QPolygonF([ponta, QPointF(c.x() + nx * W, c.y() + ny * W), tras,
                               QPointF(c.x() - nx * W, c.y() - ny * W)])
        self._bola(p, x, y, z, comp_m * 0.45, self.cor, 0.55)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        p.setOpacity(1.0)
        p.setBrush(self.miolo)
        p.setPen(QPen(self.cor, 1.2))
        p.drawPolygon(corpo)
        p.setPen(Qt.PenStyle.NoPen)

    def _estouro(self, p, f):
        if f >= 1:
            return
        el = self.d["elemento"]
        bx, by = self.b.x(), self.b.y()
        R = max(0.8, self.d["tam"]) if self.d.get("deixar") or el in ("fogo", "lava") else 1.2
        self._brilho(p, self.brilha)
        if f < 0.25:   # clarão
            k = 1 - f / 0.25
            self._bola(p, bx, by, 0.4 * M, R * (0.6 + 0.6 * (1 - k)), self.miolo if self.brilha else self.cor, 0.9 * k, self.brilha)
        for i, (r1, r2, r3, r4) in enumerate(self.parts * 3):   # estilhaços / respingos
            ang = r1 * 2 * math.pi + i
            vel = 0.4 + 0.6 * r2
            d = R * vel * (1 - (1 - f) ** 2)
            z = (0.3 + 1.6 * r3 * 4 * f * (1 - f)) * M
            x, y = bx + math.cos(ang) * d * M, by + math.sin(ang) * d * M
            if el in ("fogo", "lava"):
                cor = self.miolo if r4 < 0.3 else self.cor
                self._bola(p, x, y, z + f * M, 0.35 * (1 - f) + 0.1, cor, (1 - f) * 0.8, r4 < 0.3)
            elif el == "gelo":
                self._bola(p, x, y, z, 0.07, QColor("#ffffff"), 1 - f, True)
            else:
                self._bola(p, x, y, z, 0.12 * (1 - f) + 0.04, self.cor, (1 - f) * 0.85)
        if el in ("fogo", "lava") and f > 0.25:   # fumaça subindo
            self._brilho(p, False)
            for i, (r1, r2, r3, r4) in enumerate(self.parts[:8]):
                k = (f - 0.25) / 0.75
                self._bola(p, bx + (r1 - 0.5) * R * M, by + (r2 - 0.5) * R * M, (0.6 + 2.0 * k) * M,
                           R * 0.35 * (0.6 + k), QColor(45, 40, 36), 0.45 * math.sin(math.pi * k))

    # --- jato: sai de quem lança e vai pra frente, abrindo
    def _jato(self, p, t):
        el = self.d["elemento"]
        vel = self.d["velocidade"]
        vida = max(0.05, self.dist / vel)
        cone = self.d["tipo"] == "cone"
        abertura = math.radians(self.d["abertura"]) if cone else 0.0
        meia_larg = self.d["largura"] / 2 if not cone else 0.0
        ax, ay = self.a.x(), self.a.y()
        cos_d, sin_d = math.cos(self.dir), math.sin(self.dir)
        self._brilho(p, self.brilha)
        n = len(self.parts)
        if el in ("eletrico", "luz", "sagrado"):   # arcos/feixes que piscam dentro do cone/linha
            janela = int(t * 12)
            rnd = random.Random(janela)
            vivo = t < JATO + vida
            if vivo:
                for k in range(4 if cone else 2):
                    alcance = min(1.0, t / vida) * self.dist
                    ang = self.dir + (rnd.random() - 0.5) * abertura
                    lateral = (rnd.random() - 0.5) * 2 * meia_larg
                    pts = []
                    for j in range(11):
                        u = alcance * j / 10
                        tremor = (rnd.uniform(-0.3, 0.3) if 0 < j < 10 else 0) * M
                        x = ax + math.cos(ang) * u * M - sin_d * (lateral * M + tremor)
                        y = ay + math.sin(ang) * u * M + cos_d * (lateral * M + tremor)
                        q, _e = self._tela(x, y, 1.0 * M)
                        pts.append(q)
                    for larg, cor, alfa in ((8, self.cor, 0.3), (3, self.cor, 0.7), (1.3, self.miolo, 1.0)):
                        p.setOpacity(alfa)
                        p.setPen(QPen(cor, larg * self._cam.escala, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                                      Qt.PenJoinStyle.RoundJoin))
                        p.drawPolyline(QPolygonF(pts))
                p.setPen(Qt.PenStyle.NoPen)
            return
        for i, (r1, r2, r3, r4) in enumerate(self.parts):
            nasce = (i / n) * JATO
            idade = t - nasce
            v = vel * (0.75 + 0.5 * r2)
            vida_p = self.dist / v
            if idade < 0 or idade > vida_p:
                continue
            u = idade / vida_p                     # 0 (saindo da mão) → 1 (chegou na distância)
            d = self.dist * u
            ang = self.dir + (r1 - 0.5) * abertura
            lateral = (r1 - 0.5) * 2 * meia_larg
            x = ax + math.cos(ang) * d * M - sin_d * lateral * M
            y = ay + math.sin(ang) * d * M + cos_d * lateral * M
            z = (1.1 - 0.5 * u + (r3 - 0.5) * 0.4 * u) * M
            abre = (0.2 + d * math.tan(abertura / 2) * 0.32) if cone else (0.2 + meia_larg * 0.45)
            if el in ("fogo", "lava"):   # labareda: amarela saindo, laranja, vermelha, fumaça no fim
                if u < 0.2:
                    cor, miolo = self.miolo, True
                elif u < 0.65:
                    cor, miolo = self.cor, False
                else:
                    cor, miolo = (QColor(170, 40, 10) if not self.d.get("cor") else self.cor.darker(170)), False
                self._bola(p, x, y, z + u * 0.4 * M, abre * (0.6 + 0.8 * r4), cor,
                           (0.5 if u < 0.2 else 0.32) * (1 - u ** 2), miolo)
            elif el == "gelo":   # lascas de gelo + névoa fria
                self._bola(p, x, y, z, abre * 0.7, self.cor, 0.25 * (1 - u))
                self._bola(p, x, y, z, 0.06, QColor("#ffffff"), 1 - u, True)
            elif el in ("veneno", "trevas"):   # gás/sombra se abrindo
                self._brilho(p, False)
                self._bola(p, x, y, z, abre * (0.8 + 0.8 * u), self.cor, 0.45 * math.sin(math.pi * min(1, u * 1.2)))
            elif el in ("acido", "agua"):   # jato de gotas
                self._brilho(p, False)
                self._bola(p, x, y, z, 0.07 + 0.06 * r4, self.cor, 0.9 * (1 - u))
                if r4 < 0.3:
                    self._bola(p, x, y, z, 0.03, self.miolo, 1 - u, True)
            else:   # magia
                self._bola(p, x, y, z, 0.09 + 0.08 * r4, self.cor, 0.9 * (1 - u), True)


def tocar(cena, d: dict):
    """Põe a animação na cena (cada PC anima a sua)."""
    if cena is None:
        return None
    item = LancamentoItem(d)
    cena.addItem(item)
    return item
