"""
Terreno e paredes da mesa.

TERRENO = tinta. Cada pincelada é uma operação guardada em ordem:
  {"t": "traco", "m": "grama", "r": 32, "p": [[x, y], ...]}   pincel redondo livre
  {"t": "ret",   "m": "pedra", "x":.., "y":.., "w":.., "h":..}  retângulo (ferramenta Sala)
  {"t": "cel",   "m": "terra", "c": [[i, j], ...]}             quadrado por quadrado do grid
  "m": None = borracha (apaga o que estiver embaixo).
  Pintar por cima cobre o que estava antes, como tinta de verdade.
  Pra ficar rápido, o resultado é desenhado em "azulejos" (tiles) guardados em cache.

PAREDES = segmentos livres, em qualquer ângulo:
  {"id": "...", "a": [x0, y0], "b": [x1, y1], "m": "pedra"}
  As pontas grudam nos cantos do grid (segure Alt pra soltar; Shift trava o ângulo de 15 em 15°).
"""

import math
import uuid
from collections import OrderedDict

from PyQt6.QtCore import QLineF, QPointF, QRectF, Qt
from PyQt6.QtGui import (QBrush, QColor, QPainter, QPainterPath, QPainterPathStroker,
                         QPen, QPixmap, QPolygonF, QTransform)
from PyQt6.QtWidgets import QGraphicsItem

from ..config import CELULA
from . import materiais

ESPESSURA = 12  # espessura padrão da parede em pixels de cena
TRONCOS = {"palicada"}   # (v0.67) no 3D, essas paredes viram troncos redondos com ponta (não um bloco)


# ====================================================================== geometria
def vertice_mais_proximo(pos: QPointF) -> QPointF:
    return QPointF(round(pos.x() / CELULA) * CELULA, round(pos.y() / CELULA) * CELULA)


def restringir_angulo(a: QPointF, b: QPointF, passo_graus: float = 15) -> QPointF:
    linha = QLineF(a, b)
    angulo = round(linha.angle() / passo_graus) * passo_graus
    linha.setAngle(angulo)
    return linha.p2()


def distancia_segmento(p: QPointF, a: QPointF, b: QPointF) -> tuple[float, float]:
    """(distância, t) do ponto até o segmento a-b; t vai de 0 (em a) a 1 (em b)."""
    dx, dy = b.x() - a.x(), b.y() - a.y()
    comp2 = dx * dx + dy * dy
    if comp2 == 0:
        return math.hypot(p.x() - a.x(), p.y() - a.y()), 0.0
    t = max(0.0, min(1.0, ((p.x() - a.x()) * dx + (p.y() - a.y()) * dy) / comp2))
    qx, qy = a.x() + t * dx, a.y() + t * dy
    return math.hypot(p.x() - qx, p.y() - qy), t


def pedacos_livres(a, b, existentes, tol: float = 1.5) -> list[tuple]:
    """(v0.60.1) O que sobra do segmento a-b tirando os trechos que JÁ TÊM parede em cima (mesma linha).
    Duas salas encostadas faziam duas paredes uma sobre a outra — e aí o 3D não desenhava nenhuma das duas.
    a, b: (x, y). existentes: iterável de dicts {"a", "b"}. Devolve [((x0, y0), (x1, y1)), ...]."""
    ax, ay = float(a[0]), float(a[1])
    bx, by = float(b[0]), float(b[1])
    comp = math.hypot(bx - ax, by - ay)
    if comp < 1:
        return []
    ux, uy = (bx - ax) / comp, (by - ay) / comp
    x0, x1 = min(ax, bx) - tol, max(ax, bx) + tol
    y0, y1 = min(ay, by) - tol, max(ay, by) + tol
    cobertos = []
    for s in existentes:
        (sx, sy), (tx, ty) = s["a"], s["b"]
        if max(sx, tx) < x0 or min(sx, tx) > x1 or max(sy, ty) < y0 or min(sy, ty) > y1:
            continue
        if abs((sx - ax) * uy - (sy - ay) * ux) > tol or abs((tx - ax) * uy - (ty - ay) * ux) > tol:
            continue   # não está na mesma linha
        t1 = ((sx - ax) * ux + (sy - ay) * uy) / comp
        t2 = ((tx - ax) * ux + (ty - ay) * uy) / comp
        lo, hi = min(t1, t2), max(t1, t2)
        if hi > 0 and lo < 1:
            cobertos.append((max(0.0, lo), min(1.0, hi)))
    if not cobertos:
        return [((ax, ay), (bx, by))]
    cobertos.sort()
    livres, t = [], 0.0
    for lo, hi in cobertos:
        if lo > t:
            livres.append((t, lo))
        t = max(t, hi)
    if t < 1:
        livres.append((t, 1.0))
    ponto = lambda k: (round(ax + (bx - ax) * k, 1), round(ay + (by - ay) * k, 1))
    return [(ponto(i), ponto(f)) for i, f in livres if (f - i) * comp >= 2]


def sem_sobreposicao(segmentos: dict) -> dict:
    """Tira as paredes repetidas (uma em cima da outra) de um conjunto inteiro. Mantém a ordem e os ids."""
    aceitos: dict = {}
    for uid, seg in segmentos.items():
        pedacos = pedacos_livres(seg["a"], seg["b"], aceitos.values())
        for k, (pa, pb) in enumerate(pedacos):
            novo = dict(seg)
            novo["a"], novo["b"] = list(pa), list(pb)
            aceitos[uid if k == 0 else uuid.uuid4().hex[:12]] = novo
    return aceitos


def _caminho_traco(pontos, raio) -> QPainterPath:
    if len(pontos) == 1:
        cam = QPainterPath()
        cam.addEllipse(QPointF(*pontos[0]), raio, raio)
        return cam
    linha = QPainterPath(QPointF(*pontos[0]))
    for x, y in pontos[1:]:
        linha.lineTo(x, y)
    contorno = QPainterPathStroker()
    contorno.setWidth(2 * raio)
    contorno.setCapStyle(Qt.PenCapStyle.RoundCap)
    contorno.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return contorno.createStroke(linha)


def caminho_da_operacao(op) -> QPainterPath:
    if op["t"] == "cel":
        cam = QPainterPath()
        for i, j in op["c"]:
            cam.addRect(QRectF(i * CELULA, j * CELULA, CELULA, CELULA))
        return cam.simplified() if len(op["c"]) < 400 else cam
    if op["t"] == "ret":
        cam = QPainterPath()
        cam.addRect(QRectF(op["x"], op["y"], op["w"], op["h"]))
        return cam
    if op["t"] == "marca":   # marca deixada por uma área de efeito (mesa/marcas.py)
        from PyQt6.QtGui import QPolygonF
        cam = QPainterPath()
        cam.addPolygon(QPolygonF([QPointF(float(x), float(y)) for x, y in op.get("p", [])]))
        cam.closeSubpath()
        return cam
    return _caminho_traco(op["p"], op["r"])


# ====================================================================== terreno
class TerrenoItem(QGraphicsItem):
    TILE = 512          # tamanho do azulejo em pixels de imagem
    MAX_CACHE = 160     # quantos azulejos guardar na memória (v0.76: perto em alta + longe em baixa)

    def __init__(self):
        super().__init__()
        self.ops: list[dict] = []
        self._caminhos: list[QPainterPath] = []
        self.selecionados: set[int] = set()   # índices das pinceladas selecionadas
        self._cache: OrderedDict = OrderedDict()
        self._limites = QRectF()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemUsesExtendedStyleOption, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    def boundingRect(self) -> QRectF:
        from .camera3d import limitar
        return limitar(self, self._limites)   # (v0.70) câmera inclinada: só o chão visível

    def shape(self) -> QPainterPath:
        return QPainterPath()

    # ---------------------------------------------------------------- edição
    def _mudou(self, area: QRectF):
        area = area.adjusted(-22, -22, 22, 22)   # (a marca de efeito passa um pouco do contorno)
        for chave in [k for k in self._cache if self._area_tile(*k).intersects(area)]:
            del self._cache[chave]
        if not area.isEmpty():
            novo = self._limites.united(area) if not self._limites.isEmpty() else area
            if novo != self._limites:
                self.prepareGeometryChange()
                self._limites = novo
        self.update(area)

    def iniciar_traco(self, material, raio, pos: QPointF):
        op = {"t": "traco", "m": material, "r": raio, "p": [[round(pos.x(), 1), round(pos.y(), 1)]]}
        self.ops.append(op)
        cam = caminho_da_operacao(op)
        self._caminhos.append(cam)
        self._mudou(cam.boundingRect())

    def estender_traco(self, pos: QPointF):
        if not self.ops or self.ops[-1]["t"] != "traco":
            return
        op = self.ops[-1]
        ux, uy = op["p"][-1]
        passo = max(3.0, op["r"] * 0.3)
        if math.hypot(pos.x() - ux, pos.y() - uy) < passo:
            return
        op["p"].append([round(pos.x(), 1), round(pos.y(), 1)])
        antigo = self._caminhos[-1].boundingRect()
        self._caminhos[-1] = caminho_da_operacao(op)
        r = op["r"]
        trecho = QRectF(QPointF(min(ux, pos.x()) - r, min(uy, pos.y()) - r),
                        QPointF(max(ux, pos.x()) + r, max(uy, pos.y()) + r))
        self._mudou(trecho if not antigo.isEmpty() else self._caminhos[-1].boundingRect())

    def iniciar_celulas(self, material, celulas):
        op = {"t": "cel", "m": material, "c": []}
        self.ops.append(op)
        self._caminhos.append(QPainterPath())
        self._conjunto = set()
        self.adicionar_celulas(celulas)

    def adicionar_celulas(self, celulas):
        if not self.ops or self.ops[-1]["t"] != "cel":
            return
        op = self.ops[-1]
        conjunto = getattr(self, "_conjunto", set(map(tuple, op["c"])))
        novas = []
        for c in celulas:
            chave = (int(c[0]), int(c[1]))
            if chave not in conjunto:
                conjunto.add(chave)
                novas.append(chave)
                op["c"].append([chave[0], chave[1]])
        if not novas:
            return
        self._conjunto = conjunto
        self._caminhos[-1] = caminho_da_operacao(op)
        xs = [c[0] for c in novas]
        ys = [c[1] for c in novas]
        self._mudou(QRectF(min(xs) * CELULA, min(ys) * CELULA,
                           (max(xs) - min(xs) + 1) * CELULA, (max(ys) - min(ys) + 1) * CELULA))

    def adicionar_retangulo(self, material, rect: QRectF):
        op = {"t": "ret", "m": material, "x": rect.x(), "y": rect.y(),
              "w": rect.width(), "h": rect.height()}
        self.ops.append(op)
        cam = caminho_da_operacao(op)
        self._caminhos.append(cam)
        self._mudou(cam.boundingRect())

    def adicionar_marca(self, op: dict):
        """Marca deixada por uma área de efeito (chão queimado, corroído…). Ver mesa/marcas.py."""
        self.ops.append(dict(op))
        cam = caminho_da_operacao(op)
        self._caminhos.append(cam)
        self._mudou(cam.boundingRect())

    def limpar_marcas(self) -> int:
        """Tira todas as marcas de efeito do chão. Devolve quantas eram."""
        idx = [i for i, op in enumerate(self.ops) if op.get("t") == "marca"]
        for i in reversed(idx):
            self.remover_operacao(i)
        self.selecionados.clear()
        return len(idx)

    def operacao_em(self, pos: QPointF):
        """Índice da pincelada de tinta mais de cima nesse ponto (ignora borracha)."""
        for i in range(len(self.ops) - 1, -1, -1):
            if self.ops[i]["t"] == "marca":
                continue
            if self._caminhos[i].contains(pos):
                return None if self.ops[i]["m"] is None else i
        return None

    def trocar_material(self, indice, material):
        if self.ops[indice]["t"] == "marca":
            return
        self.ops[indice]["m"] = material
        self._mudou(self._caminhos[indice].boundingRect())

    def remover_operacao(self, indice):
        area = self._caminhos[indice].boundingRect()
        del self.ops[indice]
        del self._caminhos[indice]
        self._mudou(area)

    def definir(self, ops):
        self._conjunto = set()
        self.ops = [dict(o) for o in ops]
        self._caminhos = [caminho_da_operacao(o) for o in self.ops]
        self._cache.clear()
        self.prepareGeometryChange()
        limites = QRectF()
        for cam in self._caminhos:
            limites = limites.united(cam.boundingRect())
        self._limites = limites
        self.update()

    # ---------------------------------------------------------------- desenho
    @staticmethod
    def _escala_nivel(nivel):
        # 0 = normal (1 px por unidade) · 1 = de longe (¼) · 2 = de perto (v0.68: 2 px por unidade — a textura
        # do chão já sai no dobro, então o zoom perto mostra o detalhe em vez de borrar)
        return {0: 1.0, 1: 0.25, 2: 2.0}.get(nivel, 1.0)

    def _area_tile(self, tx, ty, nivel) -> QRectF:
        lado = self.TILE / self._escala_nivel(nivel)
        return QRectF(tx * lado, ty * lado, lado, lado)

    def _tile(self, tx, ty, nivel) -> QPixmap:
        chave = (tx, ty, nivel)
        if chave in self._cache:
            self._cache.move_to_end(chave)
            return self._cache[chave]
        area = self._area_tile(tx, ty, nivel)
        escala = self._escala_nivel(nivel)
        pm = QPixmap(self.TILE, self.TILE)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.scale(escala, escala)
        p.translate(-area.x(), -area.y())
        pinceis = {}
        for op, cam in zip(self.ops, self._caminhos):
            if not cam.boundingRect().adjusted(-20, -20, 20, 20).intersects(area):
                continue
            if op["t"] == "marca":   # chão queimado/corroído/congelado… (por cima do que já tem)
                try:
                    from .marcas import desenhar_op
                    desenhar_op(p, op)
                except Exception as erro:
                    from ..seguranca import registrar_erro
                    registrar_erro(f"Marca no chão não desenhou: {erro!r}")
                continue
            if op["m"] is None:
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                p.fillPath(cam, QColor(0, 0, 0))
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            else:
                if op["m"] not in pinceis:
                    pinceis[op["m"]] = materiais.pincel_chao(op["m"])
                p.fillPath(cam, pinceis[op["m"]])
        from ..graficos import nivel as _nivel
        if _nivel() >= 1:
            # manchas grandes de claro/escuro por cima (quebra a repetição do ladrilho, dá "chão de verdade")
            import random as _random
            from PyQt6.QtGui import QRadialGradient
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
            p.setPen(Qt.PenStyle.NoPen)
            G = 224
            for gx in range(math.floor(area.left() / G) - 1, math.floor(area.right() / G) + 2):
                for gy in range(math.floor(area.top() / G) - 1, math.floor(area.bottom() / G) + 2):
                    rnd = _random.Random(gx * 73856093 ^ gy * 19349663)
                    for _ in range(2 if _nivel() == 2 else 1):
                        c = QPointF((gx + rnd.random()) * G, (gy + rnd.random()) * G)
                        r = rnd.uniform(110, 250)
                        escura = rnd.random() < 0.62
                        cor = (0, 0, 0, rnd.randint(22, 46)) if escura else (255, 244, 225, rnd.randint(10, 24))
                        g = QRadialGradient(c, r)
                        g.setColorAt(0, QColor(*cor))
                        g.setColorAt(1, QColor(cor[0], cor[1], cor[2], 0))
                        p.setBrush(QBrush(g))
                        p.drawEllipse(c, r, r)
        p.end()
        self._cache[chave] = pm
        while len(self._cache) > self.MAX_CACHE:
            self._cache.popitem(last=False)
        return pm

    def paint(self, painter: QPainter, option, widget=None):
        if not self.ops:
            return
        from .camera3d import escala_de
        escala = escala_de(painter.worldTransform())   # (v0.70) girada/inclinada também
        from ..graficos import nivel as _nivel_graf
        nivel = (2 if escala >= 1.2 and _nivel_graf() >= 1 else 0) if escala >= 0.4 else 1
        lado = self.TILE / self._escala_nivel(nivel)
        area = option.exposedRect.intersected(self._limites)
        if area.isEmpty():
            return
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        azulejos = []
        t_mundo = painter.worldTransform()
        if not t_mundo.isAffine():
            # (v0.76) câmera inclinada: resolução POR PEDAÇO — perto em alta, longe em baixa (como nos jogos).
            # Antes era uma só pra tela toda; com o horizonte na tela, montava dezenas de pedaços em alta lá longe.
            lado1 = self.TILE / self._escala_nivel(1)
            graf = _nivel_graf()
            for gx in range(math.floor(area.left() / lado1), math.floor(area.right() / lado1) + 1):
                for gy in range(math.floor(area.top() / lado1), math.floor(area.bottom() / lado1) + 1):
                    r1 = self._area_tile(gx, gy, 1)
                    pol = t_mundo.map(QPolygonF(r1))
                    a2 = abs(sum(pol[i].x() * pol[(i + 1) % 4].y() - pol[(i + 1) % 4].x() * pol[i].y()
                                 for i in range(4))) / 2
                    s = math.sqrt(a2) / lado1   # quantos pixels por unidade, mais ou menos, nesse pedaço
                    # longe (pouco pixel por unidade) = baixa; alta só se a pessoa deu zoom perto (como de cima)
                    niv = 1 if s < 0.35 else (2 if escala >= 1.2 and s >= 1.2 and graf >= 1 else 0)
                    if niv == 1:
                        pm = self._tile(gx, gy, 1)
                        azulejos.append((r1, pm, (gx, gy, 1, pm.cacheKey())))
                        continue
                    ld = self.TILE / self._escala_nivel(niv)
                    sub = r1.intersected(area)
                    for tx in range(math.floor(sub.left() / ld), math.floor((sub.right() - 0.01) / ld) + 1):
                        for ty in range(math.floor(sub.top() / ld), math.floor((sub.bottom() - 0.01) / ld) + 1):
                            pm = self._tile(tx, ty, niv)
                            azulejos.append((self._area_tile(tx, ty, niv), pm, (tx, ty, niv, pm.cacheKey())))
        else:
            for tx in range(math.floor(area.left() / lado), math.floor(area.right() / lado) + 1):
                for ty in range(math.floor(area.top() / lado), math.floor(area.bottom() / lado) + 1):
                    pm = self._tile(tx, ty, nivel)
                    azulejos.append((self._area_tile(tx, ty, nivel), pm, (tx, ty, nivel, pm.cacheKey())))
        # mesa na placa de vídeo: o piso ganha relevo que reage à luz (v0.34); senão, o de sempre
        from . import relevo_gl
        if not (azulejos and relevo_gl.ativo(painter) and relevo_gl.desenhar(painter, azulejos, self.scene())):
            for r, pm, _chave in azulejos:
                painter.drawPixmap(r, pm, QRectF(0, 0, self.TILE, self.TILE))
        if self.selecionados:
            caneta = QPen(QColor("#e8c25a"), 2, Qt.PenStyle.DashLine)
            caneta.setCosmetic(True)
            painter.setPen(caneta)
            painter.setBrush(QColor(232, 194, 90, 45))
            for i in self.selecionados:
                if 0 <= i < len(self._caminhos):
                    painter.drawPath(self._caminhos[i])

    # ---------------------------------------------------------------- dados
    def para_lista(self):
        return [dict(o) for o in self.ops]

    @staticmethod
    def de_lista(lista):
        return [dict(o) for o in lista]

    @staticmethod
    def converter_celulas(celulas):
        """Arquivos antigos (quadrado por quadrado) viram retângulos de tinta."""
        ops = []
        for linha in sorted({j for _, j in celulas}):
            i_s = sorted(i for i, j in celulas if j == linha)
            k = 0
            while k < len(i_s):
                ini, mat = i_s[k], celulas[(i_s[k], linha)]
                fim = ini
                while k + 1 < len(i_s) and i_s[k + 1] == fim + 1 and \
                        celulas[(i_s[k + 1], linha)] == mat:
                    k += 1
                    fim = i_s[k]
                ops.append({"t": "ret", "m": mat, "x": ini * CELULA, "y": linha * CELULA,
                            "w": (fim - ini + 1) * CELULA, "h": CELULA})
                k += 1
        return ops


# ====================================================================== paredes
class ParedesItem(QGraphicsItem):
    def __init__(self):
        super().__init__()
        self.segmentos: dict[str, dict] = {}   # id -> {"a": [x,y], "b": [x,y], "m": mat}
        self.selecionados: set[str] = set()
        self._limites = QRectF()
        self._contornos: dict[str, QPainterPath] = {}
        self._sombra = QPainterPath()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemUsesExtendedStyleOption, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    def criar_camada_alta(self, cena):
        """Põe na cena a camada das paredes ALTAS (corpo 3D por cima dos tokens). A cena chama ao
        criar as paredes (não dá pra fazer isso dentro do itemChange: derruba o Qt quando a cena some)."""
        from .altura3d import ParedesAltas
        self._alta = ParedesAltas(self)
        cena.addItem(self._alta)
        return self._alta

    def boundingRect(self) -> QRectF:
        if self._limites.isEmpty():
            return self._limites
        from .camera3d import ALTURA_PAREDE, margem
        m = margem(ALTURA_PAREDE)   # no 3D o topo da parede "sai" pra fora: não pode ser cortado
        from .camera3d import limitar
        return limitar(self, self._limites.adjusted(-m, -m, m, m))   # (v0.70) câmera inclinada

    def shape(self) -> QPainterPath:
        return QPainterPath()

    @staticmethod
    def _pontos(seg):
        return QPointF(*seg["a"]), QPointF(*seg["b"])

    @classmethod
    def caminho_segmento(cls, seg, ponta_a: bool = True, ponta_b: bool = True) -> QPainterPath:
        """O corpo da parede. ponta_a/ponta_b: a ponta passa meia espessura além do ponto (fecha o canto).
        (v0.60.1) Quando a ponta encosta no MEIO de outra parede (encontro em T), ela para no eixo da outra:
        passando, ia até a face de fora dela e abria uma frestinha no 3D."""
        a, b = cls._pontos(seg)
        dx, dy = b.x() - a.x(), b.y() - a.y()
        comp = math.hypot(dx, dy)
        cam = QPainterPath()
        if comp < 1e-6:
            return cam
        ux, uy = dx / comp, dy / comp
        nx, ny = -uy * ESPESSURA / 2, ux * ESPESSURA / 2
        ea = ESPESSURA / 2 if ponta_a else 0.0
        eb = ESPESSURA / 2 if ponta_b else 0.0
        pa = QPointF(a.x() - ux * ea, a.y() - uy * ea)
        pb = QPointF(b.x() + ux * eb, b.y() + uy * eb)
        from PyQt6.QtGui import QPolygonF
        cam.addPolygon(QPolygonF([QPointF(pa.x() + nx, pa.y() + ny), QPointF(pb.x() + nx, pb.y() + ny),
                                  QPointF(pb.x() - nx, pb.y() - ny), QPointF(pa.x() - nx, pa.y() - ny)]))
        cam.closeSubpath()
        return cam

    def _pontas(self) -> dict:
        """{uid: (ponta_a, ponta_b)} — False onde a ponta encosta no meio de outra parede (T)."""
        G = 256.0   # (separa por região: mapa importado tem centenas de paredes)
        baldes: dict = {}
        for uid, seg in self.segmentos.items():
            (x0, y0), (x1, y1) = seg["a"], seg["b"]
            for i in range(math.floor((min(x0, x1) - 2) / G), math.floor((max(x0, x1) + 2) / G) + 1):
                for j in range(math.floor((min(y0, y1) - 2) / G), math.floor((max(y0, y1) + 2) / G) + 1):
                    baldes.setdefault((i, j), []).append((uid, seg))
        saida = {}
        for uid, seg in self.segmentos.items():
            res = []
            for ponto in (seg["a"], seg["b"]):
                p = QPointF(*ponto)
                em_t = False
                for uid2, s2 in baldes.get((math.floor(p.x() / G), math.floor(p.y() / G)), ()):
                    if uid2 == uid:
                        continue
                    a2, b2 = self._pontos(s2)
                    if (min(a2.x(), b2.x()) - 2 > p.x() or max(a2.x(), b2.x()) + 2 < p.x()
                            or min(a2.y(), b2.y()) - 2 > p.y() or max(a2.y(), b2.y()) + 2 < p.y()):
                        continue
                    d, t = distancia_segmento(p, a2, b2)
                    comp2 = QLineF(a2, b2).length()
                    if d < 1.0 and comp2 > 0 and ESPESSURA / 2 < t * comp2 < comp2 - ESPESSURA / 2:
                        em_t = True
                        break
                res.append(not em_t)
            saida[uid] = tuple(res)
        return saida

    def _recalcular(self):
        self.prepareGeometryChange()
        por_material: dict[str, QPainterPath] = {}
        tudo = QPainterPath()
        self._caps = self._pontas()
        for uid, seg in self.segmentos.items():
            cam = self.caminho_segmento(seg, *self._caps.get(uid, (True, True)))
            por_material.setdefault(seg["m"], QPainterPath()).addPath(cam)
            tudo.addPath(cam)
        self._contornos = {m: c.simplified() for m, c in por_material.items()}
        self._sombra = tudo.simplified()
        self._limites = tudo.boundingRect().adjusted(-30, -30, 44, 44)
        self.update()
        alta = getattr(self, "_alta", None)
        if alta is not None:
            alta.update()

    # ---------------------------------------------------------------- edição
    def adicionar(self, a: QPointF, b: QPointF, material: str) -> str | None:
        if QLineF(a, b).length() < 4:
            return None
        # (v0.60.1) o trecho que já tem parede em cima (sala encostada em sala) não é repetido
        primeiro = None
        for pa, pb in pedacos_livres((round(a.x(), 1), round(a.y(), 1)), (round(b.x(), 1), round(b.y(), 1)),
                                     self.segmentos.values()):
            uid = uuid.uuid4().hex[:12]
            self.segmentos[uid] = {"a": [pa[0], pa[1]], "b": [pb[0], pb[1]], "m": material}
            primeiro = primeiro or uid
        if primeiro:
            self._recalcular()
        return primeiro

    def remover(self, uid) -> bool:
        if self.segmentos.pop(uid, None) is None:
            return False
        self._recalcular()
        return True

    def trocar_material(self, uid, material):
        if uid in self.segmentos:
            self.segmentos[uid]["m"] = material
            self._recalcular()

    def segmento_em(self, pos: QPointF, tolerancia: float = ESPESSURA):
        melhor, menor = None, tolerancia
        for uid, seg in self.segmentos.items():
            d, _ = distancia_segmento(pos, *self._pontos(seg))
            if d <= menor:
                melhor, menor = uid, d
        return melhor

    def apagar_no_circulo(self, centro: QPointF, raio: float) -> bool:
        """Borracha de paredes: corta só o pedaço das paredes dentro do círculo."""
        mudou = False
        for uid, seg in list(self.segmentos.items()):
            a, b = self._pontos(seg)
            dx, dy = b.x() - a.x(), b.y() - a.y()
            fx, fy = a.x() - centro.x(), a.y() - centro.y()
            qa = dx * dx + dy * dy
            if qa == 0:
                continue
            qb = 2 * (fx * dx + fy * dy)
            qc = fx * fx + fy * fy - raio * raio
            disc = qb * qb - 4 * qa * qc
            if disc < 0:
                continue
            raiz = math.sqrt(disc)
            t0, t1 = (-qb - raiz) / (2 * qa), (-qb + raiz) / (2 * qa)
            if t1 <= 0 or t0 >= 1:
                continue
            self.selecionados.discard(uid)
            self.cortar(uid, max(0.0, t0), min(1.0, t1))
            mudou = True
        return mudou

    def cortar_ao_longo(self, p0: QPointF, p1: QPointF, tolerancia: float = 3.0) -> bool:
        """
        Abre um vão de p0 até p1 em TODAS as paredes que passam por ali
        (ex.: duas salas encostadas têm duas paredes uma em cima da outra).
        """
        mudou = False
        vx, vy = p1.x() - p0.x(), p1.y() - p0.y()
        comp_vao = math.hypot(vx, vy)
        if comp_vao < 1:
            return False
        for uid, seg in list(self.segmentos.items()):
            a, b = self._pontos(seg)
            sx, sy = b.x() - a.x(), b.y() - a.y()
            comp = math.hypot(sx, sy)
            if comp < 1:
                continue
            # paralela e em cima da mesma linha?
            if abs(sx * vy - sy * vx) / (comp * comp_vao) > 0.02:
                continue
            d0, _ = distancia_segmento(p0, a, b)
            d1, _ = distancia_segmento(p1, a, b)
            dist_linha = abs((p0.x() - a.x()) * sy - (p0.y() - a.y()) * sx) / comp
            if dist_linha > tolerancia:
                continue
            t0 = ((p0.x() - a.x()) * sx + (p0.y() - a.y()) * sy) / (comp * comp)
            t1 = ((p1.x() - a.x()) * sx + (p1.y() - a.y()) * sy) / (comp * comp)
            t0, t1 = min(t0, t1), max(t0, t1)
            if t1 <= 0.0005 or t0 >= 0.9995:
                continue
            self.selecionados.discard(uid)
            self.cortar(uid, max(0.0, t0), min(1.0, t1))
            mudou = True
        return mudou

    def cortar(self, uid, t0: float, t1: float):
        """Abre um vão no segmento entre t0 e t1 (0..1). Usado pelas portas."""
        seg = self.segmentos.pop(uid, None)
        if seg is None:
            return
        a, b = self._pontos(seg)
        t0, t1 = max(0.0, min(t0, t1)), min(1.0, max(t0, t1))
        ponto = lambda t: QPointF(a.x() + (b.x() - a.x()) * t, a.y() + (b.y() - a.y()) * t)
        if t0 > 0.001:
            self.segmentos[uuid.uuid4().hex[:12]] = {
                "a": seg["a"], "b": [round(ponto(t0).x(), 1), round(ponto(t0).y(), 1)],
                "m": seg["m"]}
        if t1 < 0.999:
            self.segmentos[uuid.uuid4().hex[:12]] = {
                "a": [round(ponto(t1).x(), 1), round(ponto(t1).y(), 1)], "b": seg["b"],
                "m": seg["m"]}
        self._recalcular()

    def definir(self, segmentos: dict):
        self.segmentos = {k: dict(v) for k, v in segmentos.items()}
        self._recalcular()

    # ---------------------------------------------------------------- desenho
    def paint(self, painter: QPainter, option, widget=None):
        if not self.segmentos:
            return
        from ..graficos import nivel as _nivel
        n = _nivel()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        # 1) o chão escurece perto da parede (dá profundidade)
        if n >= 1:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for larg, alfa in (((30, 13), (18, 18), (9, 26)) if n == 2 else ((16, 30),)):
                painter.setPen(QPen(QColor(0, 0, 0, alfa), larg, Qt.PenStyle.SolidLine,
                                    Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                painter.drawPath(self._sombra)
        # 2) sombra projetada no chão (a luz vem de cima-esquerda)
        painter.setPen(Qt.PenStyle.NoPen)
        passos = ((3, 4, 90),) if n == 0 else \
            tuple((k * 5.0, k * 6.0, 46) for k in (1, 2, 3)) if n == 1 else \
            tuple((k * 2.4, k * 3.0, 24) for k in range(1, 8))
        for dx, dy, alfa in passos:
            painter.setBrush(QColor(0, 0, 0, alfa))
            painter.save()
            painter.translate(dx, dy)
            painter.drawPath(self._sombra)
            painter.restore()
        # 3D: o corpo da parede (laterais + topo) é desenhado pela camada ParedesAltas, por cima dos
        # tokens (um token do outro lado da parede fica escondido atrás dela). Aqui fica só o chão.
        from . import camera3d
        if camera3d.ligada():
            return
        # 3) (2D) a "altura" da parede: a face de baixo aparece (como se a gente olhasse um pouco de lado)
        ALTURA = 0 if n == 0 else 9
        if ALTURA:
            for mat, cam in self._contornos.items():
                base = QColor(materiais.PAREDES.get(mat, ("", "#444"))[1])
                for k in range(ALTURA, 0, -1):
                    f = k / ALTURA
                    painter.setBrush(base.darker(int(210 + 130 * f)))
                    painter.save()
                    painter.translate(0, k)
                    painter.drawPath(cam)
                    painter.restore()
        self._pintar_topo(painter, n, option.exposedRect)

    def pintar_corpo_3d(self, painter: QPainter, luzes=()):
        """3D (chamado pela camada ParedesAltas): laterais até 2 m, iluminadas pelas luzes, e o topo lá em cima."""
        if not self.segmentos:
            return
        from ..graficos import nivel as _nivel
        from . import camera3d
        cam = camera3d.Camera(painter)
        nevoa = camera3d.nevoa_da_cena(self.scene())   # (v0.70) tela do jogador: a névoa vale no 3D também
        for mat, cam_mat in self._contornos.items():
            if mat in TRONCOS:   # (v0.67) paliçada: troncos redondos, desenhados à parte
                continue
            base = QColor(materiais.PAREDES.get(mat, ("", "#555"))[1])
            camera3d.desenhar_laterais(painter, cam, cam_mat.toSubpathPolygons, camera3d.ALTURA_PAREDE,
                                       base, base.lighter(150), solido=cam_mat,
                                       textura=materiais.textura("parede_face", mat), luzes=luzes, nevoa=nevoa)
        self._pintar_troncos(painter, cam, luzes, nevoa)
        painter.save()
        topo = cam.transformacao_topo(camera3d.ALTURA_PAREDE)
        painter.setWorldTransform(topo)
        corte = camera3d._ESTADO.get("corte_y") if cam.teta > 0.0 else None
        if corte is not None:   # (v0.75) pelos olhos: só o topo das paredes que ficam NA FRENTE do token
            frente = QPainterPath()
            frente.setFillRule(Qt.FillRule.WindingFill)
            tr = QPainterPathStroker()
            tr.setWidth(ESPESSURA + 2)
            tr.setCapStyle(Qt.PenCapStyle.SquareCap)
            for seg in self.segmentos.values():
                pa, pb = self._pontos(seg)
                n = max(1, int(QLineF(pa, pb).length() // CELULA) + 1)
                for k in range(n):
                    qa = pa + (pb - pa) * (k / n)
                    qb = pa + (pb - pa) * ((k + 1) / n)
                    if cam.projetar((qa + qb) / 2, 0.0).y() <= corte:
                        linha = QPainterPath()
                        linha.moveTo(qa)
                        linha.lineTo(qb)
                        frente.addPath(tr.createStroke(linha))
            painter.setClipPath(frente, Qt.ClipOperation.IntersectClip)
        self._pintar_topo(painter, _nivel(), None, pular=TRONCOS)
        if nevoa is not None:   # o topo de cada parede pega a névoa dos lados DELA (não do chão que aparece atrás)
            cor_n = QColor(nevoa.cor)
            painter.setPen(Qt.PenStyle.NoPen)
            for seg in self.segmentos.values():
                if seg.get("m") in TRONCOS:
                    continue
                pa, pb = self._pontos(seg)
                linha = QLineF(pa, pb)
                if linha.length() < 1:
                    continue
                nx, ny = -linha.dy() / linha.length(), linha.dx() / linha.length()
                nv = camera3d.nevoa_da_parede(nevoa, cam, pa, pb, nx, ny, ESPESSURA * 0.9)
                if nv <= 0.02:
                    continue
                cor_n.setAlphaF(min(1.0, nv))
                painter.setBrush(cor_n)
                cam_seg = QPainterPath()
                cam_seg.moveTo(pa)
                cam_seg.lineTo(pb)
                tr = QPainterPathStroker()
                tr.setWidth(ESPESSURA + 2)
                tr.setCapStyle(Qt.PenCapStyle.SquareCap)
                painter.drawPath(tr.createStroke(cam_seg))
        painter.restore()

    def troncos(self) -> list[tuple]:
        """(v0.67) A paliçada como troncos: [(centro, raio, altura, ponta)] ao longo dos segmentos de paliçada.
        Alturas um pouco diferentes (sorteadas pelo lugar, sempre iguais), ponta afiada em cima."""
        import random
        saida = []
        r = ESPESSURA * 0.82                      # ~0,3 m de diâmetro
        passo = r * 1.85
        for seg in self.segmentos.values():
            if seg.get("m") not in TRONCOS:
                continue
            a, b = self._pontos(seg)
            comp = QLineF(a, b).length()
            n = max(1, round(comp / passo))
            for k in range(n + 1):
                t = k / n
                c = QPointF(a.x() + (b.x() - a.x()) * t, a.y() + (b.y() - a.y()) * t)
                rnd = random.Random(round(c.x()) * 92821 ^ round(c.y()) * 68917)
                alt = CELULA * rnd.uniform(1.85, 2.2)
                saida.append((c, r * rnd.uniform(0.9, 1.08), alt, CELULA * rnd.uniform(0.22, 0.34)))
        return saida

    def _pintar_troncos(self, painter: QPainter, cam, luzes=(), nevoa=None):
        lista = self.troncos()
        if not lista:
            return
        import math
        from . import camera3d, texturas_porta
        cc = cam.pe_cena()   # (v0.70) onde a câmera está (inclinada, fica mais pra trás)
        lista.sort(key=lambda t: -((t[0].x() - cc.x()) ** 2 + (t[0].y() - cc.y()) ** 2))   # longe → perto
        madeira = QColor("#6b4a2c")
        casca = texturas_porta.casca()
        for c, r, alt, ponta in lista:
            if nevoa is not None and nevoa.amostrar(cam.projetar(c, 0.0)) >= 0.97:
                continue   # (v0.70) tronco num lugar que o jogador nunca viu
            corte = camera3d._ESTADO.get("corte_y") if cam.teta > 0.0 else None
            if corte is not None and cam.projetar(c, 0.0).y() > corte:
                continue   # (v0.75) pelos olhos: atrás do token
            octo = QPolygonF([QPointF(c.x() + math.cos(k * math.pi / 4) * r, c.y() + math.sin(k * math.pi / 4) * r)
                              for k in range(8)])
            camera3d.desenhar_laterais(painter, cam, [octo], alt, madeira, None, 0.0, textura=casca, luzes=luzes,
                                       escala_tex=texturas_porta.ESCALA, nevoa=nevoa)
            # a ponta afiada: 8 triângulos até o bico, do de trás pro da frente, com luz
            bico = cam.projetar(c, alt + ponta)
            tri = []
            for k in range(8):
                p0, p1 = octo[k], octo[(k + 1) % 8]
                mx, my = (p0.x() + p1.x()) / 2 - c.x(), (p0.y() + p1.y()) / 2 - c.y()
                nr = math.hypot(mx, my) or 1
                luz = -(mx / nr * camera3d.LUZ_2D[0] + my / nr * camera3d.LUZ_2D[1])
                dist = (c.x() + mx - cc.x()) ** 2 + (c.y() + my - cc.y()) ** 2
                tri.append((-dist, cam.projetar(p0, alt), cam.projetar(p1, alt), luz))
            tri.sort(key=lambda x: x[0])
            painter.save()
            painter.resetTransform()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            for _d, q0, q1, luz in tri:
                f = 0.62 + 0.3 * max(-1.0, min(1.0, luz))
                cor = QColor("#c9a46a")                  # madeira clara da ponta lascada
                cor = QColor(int(cor.red() * f), int(cor.green() * f), int(cor.blue() * f))
                painter.setPen(QPen(cor.darker(125), 0.6))
                painter.setBrush(cor)
                painter.drawPolygon(QPolygonF([q0, q1, bico]))
            painter.restore()

    def _pintar_topo(self, painter: QPainter, n: int, area, pular=()):
        """O desenho de sempre da parede (textura, quinas, contorno, seleção). area=None: não recorta.
        pular: materiais que não têm "topo" chato (a paliçada vira troncos no 3D)."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        E = ESPESSURA
        caps = getattr(self, "_caps", {})
        for uid, seg in self.segmentos.items():
            if seg.get("m") in pular:
                continue
            a, b = self._pontos(seg)
            linha = QLineF(a, b)
            ca, cb = caps.get(uid, (True, True))
            r = QRectF(min(a.x(), b.x()), min(a.y(), b.y()),
                       abs(b.x() - a.x()), abs(b.y() - a.y())).adjusted(-E, -E, E, E)
            if area is not None and not r.intersects(area):   # (no 3D o topo pode estar na tela e o pé não)
                continue
            painter.save()
            painter.translate(a)
            painter.rotate(-linha.angle())  # QLineF mede o ângulo no sentido anti-horário
            pincel = QBrush(materiais.textura("parede", seg["m"]))
            pincel.setTransform(QTransform().translate(0, -E / 2))
            ea, eb = (E / 2 if ca else 0.0), (E / 2 if cb else 0.0)
            painter.fillRect(QRectF(-ea, -E / 2, linha.length() + ea + eb, E), pincel)
            painter.restore()

        painter.setBrush(Qt.BrushStyle.NoBrush)
        for mat, cam in self._contornos.items():
            if mat in pular:
                continue
            if n >= 1:
                # 4) quina: luz na borda de cima-esquerda, sombra na de baixo-direita (topo com volume)
                painter.save()
                painter.setClipPath(cam, Qt.ClipOperation.IntersectClip)
                painter.translate(1.6, 1.6)
                painter.setPen(QPen(QColor(255, 246, 228, 95 if n == 2 else 70), 2.2))
                painter.drawPath(cam)
                painter.translate(-3.2, -3.2)
                painter.setPen(QPen(QColor(0, 0, 0, 120), 2.4))
                painter.drawPath(cam)
                painter.restore()
            borda = QPen(QColor(materiais.PAREDES.get(mat, ("", "#222"))[1]).darker(190), 1.4)
            borda.setCosmetic(True)
            painter.setPen(borda)
            painter.drawPath(cam)

        if self.selecionados:
            caneta = QPen(QColor("#e8c25a"), 2)
            caneta.setCosmetic(True)
            painter.setPen(caneta)
            painter.setBrush(QColor(232, 194, 90, 110))
            for uid in self.selecionados:
                seg = self.segmentos.get(uid)
                if seg:
                    painter.drawPath(self.caminho_segmento(seg))

    # ---------------------------------------------------------------- dados
    def para_lista(self):
        return [{"id": k, **v} for k, v in self.segmentos.items()]

    @staticmethod
    def de_lista(lista) -> dict:
        return {d["id"]: {"a": list(d["a"]), "b": list(d["b"]), "m": d["m"]} for d in lista}

    @staticmethod
    def converter_arestas(lista_antiga):
        """Arquivos antigos (paredes nas arestas do grid). Retorna (segmentos, portas)."""
        segmentos, portas = {}, []
        for o, i, j, m, porta, aberta in lista_antiga:
            if o == "h":
                a, b = [i * CELULA, j * CELULA], [(i + 1) * CELULA, j * CELULA]
                angulo = 0
            else:
                a, b = [i * CELULA, j * CELULA], [i * CELULA, (j + 1) * CELULA]
                angulo = 90
            if porta:
                portas.append({"classe": "porta", "x": (a[0] + b[0]) / 2,
                               "y": (a[1] + b[1]) / 2, "angulo": angulo,
                               "aberta": bool(aberta), "tipo": "madeira"})
            else:
                segmentos[uuid.uuid4().hex[:12]] = {"a": a, "b": b, "m": m}
        return segmentos, portas
