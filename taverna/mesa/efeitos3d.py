"""
Partículas 3D das áreas de efeito (Mesa 3D, parte 3 — v0.36).

Cada área ganha partículas com ALTURA, que sobem (ou caem) em direção à câmera de cima:
  fogo   — labaredas e brasas subindo, fumaça por cima (Alto)
  lava   — respingos saltando e bolhas estourando
  veneno — nuvens de gás subindo e bolhinhas
  ácido  — bolhas e vapor
  gelo   — floquinhos caindo e cristais de pé
  água   — gotinhas pulando
  raio   — faíscas saltando do chão
  escuridão / fumaça — véus subindo (cobrem o que está embaixo)
  luz / radiante — poeira de luz subindo; o radiante tem colunas de luz
  magia  — fagulhas em espiral e um anel de runas flutuando
  vinhas — talos e folhas de pé, balançando

Sem estado: a posição de cada partícula é calculada a partir do tempo (barato e sem acumular nada).
Desenhadas pela camada das coisas altas (altura3d), por cima dos tokens e atrás das paredes.
Respeita Gráficos (Médio = metade das partículas; Baixo = mesa 2D, sem partículas).
"""

import math
import weakref

import numpy as np

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap, QPolygonF, QRadialGradient

from ..config import CELULA

AREAS = weakref.WeakSet()   # toda EfeitoItem se registra aqui
M = CELULA                  # 1 metro
_SPRITES = {}


def _sprite(cor: QColor, miolo: bool = False) -> tuple:
    """Bolinha macia (degradê) de 64 px, guardada. miolo = centro esbranquiçado (brilho).
    (v0.47) A cor é arredondada (de 8 em 8): o fogo mistura cores a cada quadro e, sem isso, o cache
    estourava e as bolinhas eram redesenhadas do zero o tempo todo."""
    chave = (cor.red() >> 3, cor.green() >> 3, cor.blue() >> 3, miolo)
    pm = _SPRITES.get(chave)
    if pm is None:
        cor = QColor((chave[0] << 3) | 4, (chave[1] << 3) | 4, (chave[2] << 3) | 4)
        pm = QPixmap(64, 64)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        g = QRadialGradient(QPointF(32, 32), 32)
        if miolo:
            g.setColorAt(0, QColor(255, 255, 240, 255))
            g.setColorAt(0.25, QColor(cor.red(), cor.green(), cor.blue(), 230))
        else:
            g.setColorAt(0, QColor(cor.red(), cor.green(), cor.blue(), 200))
        g.setColorAt(1, QColor(cor.red(), cor.green(), cor.blue(), 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(g)
        p.drawEllipse(QPointF(32, 32), 32, 32)
        p.end()
        if len(_SPRITES) > 1500:
            _SPRITES.clear()
        _SPRITES[chave] = pm
    return pm, chave


def _misturar(a: QColor, b: QColor, t: float) -> QColor:
    t = max(0.0, min(1.0, t))
    return QColor(int(a.red() + (b.red() - a.red()) * t), int(a.green() + (b.green() - a.green()) * t),
                  int(a.blue() + (b.blue() - a.blue()) * t))


_FONTE = QRectF(0, 0, 64, 64)
_Frag = QPainter.PixmapFragment


class _Desenho:
    """Ajuda a desenhar partículas na tela a partir de (x, y, z) da cena.
    (v0.47) As bolinhas vão num LOTE por desenho de bolinha (drawPixmapFragments): uma chamada pra
    dezenas de partículas, em vez de uma por partícula. `modo()` e `traco()` descarregam o lote antes."""

    def __init__(self, painter, cam):
        self.p = painter
        self.cam = cam
        self._lotes = {}

    def bolinha(self, x, y, z, raio_m, cor, alfa=1.0, miolo=False):
        if alfa <= 0.01 or raio_m <= 0:
            return
        c = self.cam.projetar(QPointF(x, y), z)
        r = raio_m * M * self.cam.escala * self.cam.fator(z)
        if r < 0.4:
            return
        pm, chave = _sprite(cor, miolo)
        lote = self._lotes.get(chave)
        if lote is None:
            lote = self._lotes[chave] = (pm, [])
        e = r / 32.0
        lote[1].append(_Frag.create(c, _FONTE, e, e, 0.0, alfa if alfa < 1.0 else 1.0))

    def bolinhas(self, x, y, z, raio_m, cor, alfa, miolo=False):
        """(v0.47) Muitas bolinhas de uma vez (arrays numpy): projeção e cortes em numpy; só a criação
        dos fragmentos fica em Python. `cor`: QColor (todas iguais) ou array (N, 3) de 0..255."""
        x, y, z, raio_m, alfa = np.broadcast_arrays(np.asarray(x, np.float64), np.asarray(y, np.float64),
                                                    np.asarray(z, np.float64), np.asarray(raio_m, np.float64),
                                                    np.asarray(alfa, np.float64))
        if x.size == 0:
            return
        cam = self.cam
        sx, sy, f = cam.projetar_np(x, y, z)   # (v0.70) também com a câmera inclinada
        r = raio_m * (M * cam.escala) * f
        ok = (alfa > 0.01) & (raio_m > 0) & (r >= 0.4)
        if not ok.any():
            return
        idx = np.flatnonzero(ok)
        esc = (r[idx] / 32.0).tolist()
        al = np.minimum(alfa[idx], 1.0).tolist()
        px, py = sx[idx].tolist(), sy[idx].tolist()
        if isinstance(cor, QColor):
            grupos = {(cor.red() >> 3, cor.green() >> 3, cor.blue() >> 3): range(len(idx))}
            amostra = {next(iter(grupos)): cor}
        else:
            q = (np.asarray(cor, np.int32)[idx] >> 3)
            chave = (q[:, 0] << 10) | (q[:, 1] << 5) | q[:, 2]
            grupos, amostra = {}, {}
            for k, ch in enumerate(chave.tolist()):
                g = grupos.get(ch)
                if g is None:
                    g = grupos[ch] = []
                    amostra[ch] = QColor(int(q[k, 0]) << 3, int(q[k, 1]) << 3, int(q[k, 2]) << 3)
                g.append(k)
        cria = _Frag.create
        for ch, ks in grupos.items():
            pm, chave_s = _sprite(amostra[ch], miolo)
            lote = self._lotes.get(chave_s)
            if lote is None:
                lote = self._lotes[chave_s] = (pm, [])
            lista = lote[1]
            for k in ks:
                e = esc[k]
                lista.append(cria(QPointF(px[k], py[k]), _FONTE, e, e, 0.0, al[k]))

    def descarregar(self):
        if not self._lotes:
            return
        self.p.setOpacity(1.0)
        for pm, frags in self._lotes.values():
            self.p.drawPixmapFragments(frags, pm)
        self._lotes = {}

    def modo(self, modo):
        self.descarregar()
        self.p.setCompositionMode(modo)

    def traco(self, pontos, cor, largura_m, alfa=1.0):
        """Linha passando por pontos (x, y, z)."""
        if len(pontos) < 2 or alfa <= 0.01:
            return
        self.descarregar()
        tela = QPolygonF([self.cam.projetar(QPointF(x, y), z) for x, y, z in pontos])
        z_medio = sum(q[2] for q in pontos) / len(pontos)
        larg = max(0.8, largura_m * M * self.cam.escala * self.cam.fator(z_medio))
        self.p.setOpacity(max(0.0, min(1.0, alfa)))
        self.p.setPen(QPen(cor, larg, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        self.p.drawPolyline(tela)


def _pontos(area, qtd):
    """Pontos (na CENA) dentro da área, com dois números aleatórios fixos por ponto. Em cache."""
    from .efeitos import _pontos_dentro
    chave = (round(area.pos().x()), round(area.pos().y()), round(area.rotation()), area.chave_forma(),
             round(area.tamanho, 2), round(area.largura, 2), qtd, area._semente)
    cache = getattr(area, "_cache_3d", None)
    if cache and cache[0] == chave:
        return cache[1]
    locais = _pontos_dentro(area.caminho(), qtd, area._semente + 17)
    pts = _Pts()
    for x, y, a, b in locais:
        s = area.mapToScene(QPointF(x, y))
        pts.append((s.x(), s.y(), a, b))
    area._cache_3d = (chave, pts)
    return pts


class _Pts(list):
    """Lista de (x, y, a, b) que também dá os arrays numpy (.X .Y .A .B), e fatia continua _Pts."""

    def __getitem__(self, k):
        r = super().__getitem__(k)
        return _Pts(r) if isinstance(k, slice) else r

    @property
    def arr(self):
        a = self.__dict__.get("_arr")
        if a is None:
            a = self.__dict__["_arr"] = np.asarray(self, np.float64).reshape(-1, 4)
        return a

    X = property(lambda s: s.arr[:, 0])
    Y = property(lambda s: s.arr[:, 1])
    A = property(lambda s: s.arr[:, 2])
    B = property(lambda s: s.arr[:, 3])


def _mix(a: QColor, b: QColor, t) -> np.ndarray:
    """Mistura de cores pra vários t de uma vez → (N, 3)."""
    t = np.clip(np.asarray(t, np.float64), 0, 1)[:, None]
    ca = np.array([a.red(), a.green(), a.blue()], np.float64)
    cb = np.array([b.red(), b.green(), b.blue()], np.float64)
    return ca + (cb - ca) * t


def _cic(t, vel, fase):
    return np.mod(t * vel + fase, 1.0)


def desenhar(painter: QPainter, cam, area, t: float, nivel: int):
    """Partículas 3D de UMA área de efeito (painter já em coordenadas de tela, sem transformação)."""
    efeito = area.efeito
    r = area.caminho().boundingRect()
    m2 = max(1.0, (r.width() * r.height()) / (M * M))
    dens = 0.5 if nivel < 2 else 1.0
    d = _Desenho(painter, cam)
    cor = QColor(area.cor_efetiva)
    painter.save()
    try:
        if efeito == "fogo":
            _fogo(d, _pontos(area, int(min(110, m2 * 7.0) * dens) + 4), t, nivel)
        elif efeito == "lava":
            _lava(d, _pontos(area, int(min(60, m2 * 3.5) * dens) + 3), t)
        elif efeito in ("veneno", "acido"):
            _gas(d, _pontos(area, int(min(40, m2 * 2.2) * dens) + 3), t, efeito)
        elif efeito == "gelo":
            _gelo(d, _pontos(area, int(min(60, m2 * 3.0) * dens) + 4), t)
        elif efeito == "agua":
            _agua(d, _pontos(area, int(min(30, m2 * 1.5) * dens) + 3), t)
        elif efeito == "eletrico":
            _eletrico(d, _pontos(area, int(min(14, m2 * 0.8) * dens) + 2), t)
        elif efeito in ("trevas", "fumaca"):
            _veu(d, _pontos(area, int(min(36, m2 * 1.6) * dens) + 3), t, efeito, cor)
        elif efeito in ("luz", "sagrado"):
            _luz(d, _pontos(area, int(min(50, m2 * 2.6) * dens) + 4), t, efeito, cor, area, r)
        elif efeito == "magia":
            _magia(d, _pontos(area, int(min(40, m2 * 2.0) * dens) + 4), t, cor, area, r, cam)
        elif efeito == "planta":
            _planta(d, _pontos(area, int(min(60, m2 * 3.0) * dens) + 4), t)
        d.descarregar()
    finally:
        painter.restore()


# ====================================================================== cada efeito
def _ciclo(t, vel, fase):
    return (t * vel + fase) % 1.0


def _fogo(d, pts, t, nivel):
    amarelo, laranja, vermelho = QColor("#ffc84a"), QColor("#ff7010"), QColor("#b82406")
    d.modo(QPainter.CompositionMode.CompositionMode_Plus)
    x, y, a, b = pts.X, pts.Y, pts.A, pts.B   # labaredas: sobem e encolhem, amarelo → vermelho
    idade = _cic(t, 1.0 / (0.7 + 0.5 * a), b)
    cor = np.where((idade < 0.6)[:, None], _mix(amarelo, laranja, idade * 1.6),
                   _mix(laranja, vermelho, (idade - 0.6) * 2.5))
    xx = x + np.sin(t * 3 + a * 9) * 0.12 * M * idade
    zz = idade * (1.0 + 0.7 * a) * M
    novas = idade < 0.1
    for sel, miolo in ((novas, True), (~novas, False)):
        d.bolinhas(xx[sel], y[sel], zz[sel], 0.5 * (1 - idade[sel] * 0.6), cor[sel], (1 - idade[sel]) * 0.8, miolo)
    p2 = pts[::2]                              # brasas: sobem alto, piscando
    x, y, a, b = p2.X, p2.Y, p2.A, p2.B
    idade = _cic(t, 0.45 + 0.3 * a, b * 1.7)
    d.bolinhas(x + np.sin(t * 2 + b * 11) * 0.3 * M * idade, y + np.cos(t + a * 7) * 0.1 * M,
               idade * (1.8 + 1.2 * b) * M, 0.05, QColor("#ffd060"),
               (1 - idade) * (0.6 + 0.4 * np.sin(t * 15 + a * 30)), True)
    d.modo(QPainter.CompositionMode.CompositionMode_SourceOver)
    if nivel >= 2:                             # fumaça escura, bem alto
        p4 = pts[::4]
        x, y, a, b = p4.X, p4.Y, p4.A, p4.B
        idade = _cic(t, 0.22 + 0.1 * a, b)
        d.bolinhas(x + np.sin(t * 0.7 + a * 5) * 0.4 * M, y, (1.3 + idade * 1.8) * M, 0.5 + idade * 0.9,
                   QColor(28, 24, 22), 0.28 * np.sin(np.pi * idade))


def _lava(d, pts, t):
    d.modo(QPainter.CompositionMode.CompositionMode_Plus)
    x, y, a, b = pts.X, pts.Y, pts.A, pts.B   # respingos: saltam em arco e caem
    periodo = 1.6 + 1.4 * a
    fase = np.mod(t + b * periodo, periodo) / periodo
    sal = fase < 0.45
    s = fase[sal] / 0.45
    ang = a[sal] * 6.28
    alc = 0.4 * M * s
    d.bolinhas(x[sal] + np.cos(ang) * alc, y[sal] + np.sin(ang) * alc, 4 * (0.5 + 0.9 * b[sal]) * M * s * (1 - s),
               0.11, QColor("#ff9a20"), 1.0, True)
    s = (fase[~sal] - 0.45) / 0.55             # bolha inchando e estourando na superfície
    d.bolinhas(x[~sal], y[~sal], 0.02 * M, 0.08 + 0.12 * s, QColor("#ff7a10"), 0.5 * (1 - s))
    d.modo(QPainter.CompositionMode.CompositionMode_SourceOver)
    p3 = pts[::3]                              # calor subindo (fumacinha bem leve)
    idade = _cic(t, 0.3, p3.A)
    d.bolinhas(p3.X, p3.Y, (0.3 + idade * 1.6) * M, 0.3 + idade * 0.5, QColor(60, 30, 20),
               0.18 * np.sin(np.pi * idade))


def _gas(d, pts, t, efeito):
    nuvem = QColor("#86c840") if efeito == "veneno" else QColor("#b8f040")
    bolha = QColor("#c8ff7a") if efeito == "veneno" else QColor("#e8ff9a")
    x, y, a, b = pts.X, pts.Y, pts.A, pts.B   # nuvens subindo devagar e se abrindo
    idade = _cic(t, 0.18 + 0.12 * a, b)
    d.bolinhas(x + np.sin(t * 0.6 + a * 7) * 0.35 * M, y + np.cos(t * 0.5 + b * 7) * 0.2 * M,
               idade * (1.2 if efeito == "veneno" else 0.8) * M, 0.45 + idade * 0.8, nuvem,
               (0.32 if efeito == "veneno" else 0.22) * np.sin(np.pi * idade))
    d.modo(QPainter.CompositionMode.CompositionMode_Plus)
    p2 = pts[::2]                              # bolhinhas subindo e estourando
    idade = _cic(t, 0.7 + 0.5 * p2.A, p2.B * 1.3)
    d.bolinhas(p2.X, p2.Y, idade * 0.5 * M, 0.04 + 0.03 * idade, bolha, 0.8 * (1 - idade))
    d.modo(QPainter.CompositionMode.CompositionMode_SourceOver)


def _gelo(d, pts, t):
    branco, cristal = QColor("#ffffff"), QColor("#bfefff")
    for x, y, a, b in pts[::3]:                # cristais de pé (agulhas de gelo)
        alt = (0.25 + 0.45 * a) * M
        incl = (b - 0.5) * 0.12 * M
        d.traco([(x, y, 0), (x + incl, y, alt)], cristal, 0.05, 0.75)
        d.traco([(x, y, 0), (x + incl * 0.6, y, alt * 0.7)], branco, 0.02, 0.8)
    d.modo(QPainter.CompositionMode.CompositionMode_Plus)
    x, y, a, b = pts.X, pts.Y, pts.A, pts.B   # floquinhos caindo, rodopiando
    idade = _cic(t, 0.22 + 0.15 * a, b)
    d.bolinhas(x + np.sin(t * 1.3 + a * 9) * 0.3 * M, y + np.cos(t + b * 9) * 0.2 * M, (1 - idade) * 2.4 * M,
               0.065, branco, 0.95 * np.minimum(1, idade * 4))
    d.modo(QPainter.CompositionMode.CompositionMode_SourceOver)


def _agua(d, pts, t):
    gota = QColor("#bfe8ff")
    x, y, a, b = pts.X, pts.Y, pts.A, pts.B   # gotinhas pulando
    periodo = 1.2 + a
    s = np.mod(t + b * periodo, periodo) / periodo
    k = s < 0.35
    u = s[k] / 0.35
    d.bolinhas(x[k] + (a[k] - 0.5) * 0.3 * M * u, y[k], 4 * 0.3 * M * u * (1 - u), 0.035, gota, 0.75)


def _eletrico(d, pts, t):
    import random
    janela = int(t * 9)                        # o desenho do raio troca ~9× por segundo
    d.modo(QPainter.CompositionMode.CompositionMode_Plus)
    for k, (x, y, a, b) in enumerate(pts):
        rnd = random.Random(janela * 131 + k * 17)
        if rnd.random() > 0.55:
            continue
        alt = (0.4 + 0.9 * rnd.random()) * M
        pontos = [(x, y, 0.0)]
        for s in range(1, 6):
            pontos.append((x + rnd.uniform(-0.18, 0.18) * M, y + rnd.uniform(-0.18, 0.18) * M, alt * s / 5))
        d.traco(pontos, QColor("#8ab8ff"), 0.08, 0.5)
        d.traco(pontos, QColor("#ffffff"), 0.025, 0.95)
        d.bolinha(pontos[-1][0], pontos[-1][1], alt, 0.12, QColor("#bcd8ff"), 0.6, miolo=True)
    d.modo(QPainter.CompositionMode.CompositionMode_SourceOver)


def _veu(d, pts, t, efeito, cor):
    if efeito == "trevas":
        base = QColor(6, 4, 10)
        borda = cor.darker(200)
    else:
        base = QColor(150, 150, 154)
        borda = QColor(110, 110, 114)
    x, y, a, b = pts.X, pts.Y, pts.A, pts.B   # véus/nuvens subindo e se abrindo (tapam o que está embaixo)
    idade = _cic(t, 0.12 + 0.08 * a, b)
    d.bolinhas(x + np.sin(t * 0.4 + a * 6) * 0.4 * M, y + np.cos(t * 0.35 + b * 6) * 0.3 * M,
               idade * (1.8 if efeito == "trevas" else 2.2) * M, 0.6 + idade * 0.9, _mix(base, borda, b * 0.6),
               (0.55 if efeito == "trevas" else 0.32) * np.sin(np.pi * idade))


def _luz(d, pts, t, efeito, cor, area, r):
    d.modo(QPainter.CompositionMode.CompositionMode_Plus)
    if efeito == "sagrado":                    # colunas de luz descendo do alto
        centro = area.mapToScene(r.center())
        for k in range(3):
            ang = t * 0.4 + k * 2.09
            raio = min(r.width(), r.height()) * 0.25
            x = centro.x() + math.cos(ang) * raio
            y = centro.y() + math.sin(ang) * raio
            pulso = 0.5 + 0.5 * math.sin(t * 1.7 + k)
            d.traco([(x, y, 0), (x, y, 2.0 * M)], cor, 0.35, 0.22 * pulso)
            d.traco([(x, y, 0), (x, y, 2.0 * M)], QColor("#fffbe8"), 0.08, 0.4 * pulso)
    x, y, a, b = pts.X, pts.Y, pts.A, pts.B   # poeira de luz subindo
    idade = _cic(t, 0.16 + 0.14 * a, b)
    d.bolinhas(x + np.sin(t * 0.9 + a * 8) * 0.25 * M, y, idade * 2.2 * M, 0.08, cor,
               np.sin(np.pi * idade) * (0.55 + 0.45 * np.sin(t * 4 + a * 20)), True)
    d.modo(QPainter.CompositionMode.CompositionMode_SourceOver)


def _magia(d, pts, t, cor, area, r, cam):
    centro = area.mapToScene(r.center())
    R = min(r.width(), r.height()) * 0.45
    d.modo(QPainter.CompositionMode.CompositionMode_Plus)
    # anel de runas flutuando a ~0,9 m, girando devagar
    z_anel = (0.9 + 0.08 * math.sin(t * 1.3)) * M
    n = 36
    anel = []
    for k in range(n + 1):
        ang = k * 2 * math.pi / n + t * 0.3
        anel.append((centro.x() + math.cos(ang) * R * 0.7, centro.y() + math.sin(ang) * R * 0.7, z_anel))
    d.traco(anel, cor, 0.05, 0.55)
    for k in range(8):                         # runas (marcas) no anel
        ang = k * 2 * math.pi / 8 - t * 0.3
        cx, cy = centro.x() + math.cos(ang) * R * 0.7, centro.y() + math.sin(ang) * R * 0.7
        d.bolinha(cx, cy, z_anel, 0.12, cor, 0.7, miolo=True)
    x, y, a, b = pts.X, pts.Y, pts.A, pts.B   # fagulhas subindo em espiral
    idade = _cic(t, 0.25 + 0.2 * a, b)
    ang = a * 6.28 + idade * 4
    raio = (1 - idade) * 0.35 * M
    d.bolinhas(x + np.cos(ang) * raio, y + np.sin(ang) * raio, idade * 1.8 * M, 0.075, cor,
               np.sin(np.pi * idade), True)
    d.modo(QPainter.CompositionMode.CompositionMode_SourceOver)


def _planta(d, pts, t):
    for x, y, a, b in pts:                     # talos de pé, balançando, com folha na ponta
        alt = (0.25 + 0.5 * a) * M
        bal = math.sin(t * 1.3 + a * 7) * 0.1 * M
        cor = QColor("#3f7a24") if b < 0.5 else QColor("#5a9a32")
        d.traco([(x, y, 0), (x + bal * 0.4, y, alt * 0.55), (x + bal, y, alt)], cor, 0.045, 0.95)
        d.bolinha(x + bal, y, alt, 0.08, QColor("#7cc848"), 0.8)


# ====================================================================== (v0.79) STATUS do token com partículas
# O token "em chamas", "envenenado", "sangrando"… solta as mesmas partículas das áreas, só que em volta DELE e
# no tamanho dele (além do simbolozinho de sempre). Vale o "efeito em cima" do token e as condições da ficha.
STATUS_DO_EFEITO = {"fogo": "fogo", "veneno": "veneno", "acido": "acido", "gelo": "gelo", "eletrico": "eletrico",
                    "agua": "molhado", "luz": "luz", "planta": "planta"}
STATUS_DA_CONDICAO = {"queimando": "fogo", "envenenado": "veneno", "congelado": "gelo", "molhado": "molhado",
                      "sangrando": "sangue", "abencoado": "luz", "paralisado": "eletrico"}


def status_do_token(tok) -> list:
    """Quais partículas esse token solta agora (sem repetir)."""
    saida = []
    ef = STATUS_DO_EFEITO.get(getattr(tok, "efeito", "") or "")
    if ef:
        saida.append(ef)
    cond = (getattr(tok, "info", None) or {}).get("condicoes") or {}
    for k in (cond.get("v") or []):
        s = STATUS_DA_CONDICAO.get(k)
        if s and s not in saida:
            saida.append(s)
    return saida


def _pontos_token(tok, qtd: int):
    """Pontos (na cena) em volta do token, com dois números fixos por ponto (sempre os mesmos pra ele)."""
    import zlib
    d = tok.diametro
    c = tok.mapToScene(QPointF(d / 2, d / 2))
    chave = (round(c.x(), 1), round(c.y(), 1), d, qtd)
    cache = getattr(tok, "_cache_status", None)
    if cache and cache[0] == chave:
        return cache[1]
    rng = np.random.default_rng(zlib.crc32(str(getattr(tok, "uid", "")).encode()))
    ang = rng.random(qtd) * 2 * np.pi
    raio = np.sqrt(rng.random(qtd)) * d * 0.48
    pts = _Pts((float(c.x() + math.cos(a) * r), float(c.y() + math.sin(a) * r), float(u), float(v))
               for a, r, u, v in zip(ang, raio, rng.random(qtd), rng.random(qtd)))
    tok._cache_status = (chave, pts)
    return pts


def _pingos(d, pts, t, cor, alto, raio=0.05):
    """Gotas caindo do corpo até o chão (molhado / sangrando)."""
    x, y, a, b = pts.X, pts.Y, pts.A, pts.B
    periodo = 0.9 + 0.8 * a
    s = np.mod(t + b * periodo, periodo) / periodo
    d.bolinhas(x, y, (1 - s * s) * alto * (0.6 + 0.4 * a), raio, cor, 0.9 * np.minimum(1, (1 - s) * 3), True)


def desenhar_status(painter: QPainter, cam, tok, t: float, nivel: int):
    """Partículas dos status de UM token (painter em coordenadas de tela, sem transformação)."""
    lista = status_do_token(tok)
    if not lista or nivel < 1:
        return
    tam = max(1, int(getattr(tok, "tamanho", 1)))
    dens = 0.5 if nivel < 2 else 1.0
    alto = (0.9 + 0.35 * tam) * M
    d = _Desenho(painter, cam)
    painter.save()
    try:
        for s in lista:
            if s == "fogo":
                _fogo(d, _pontos_token(tok, int(14 * tam * dens) + 4), t, nivel)
            elif s in ("veneno", "acido"):
                _gas(d, _pontos_token(tok, int(8 * tam * dens) + 3), t, s)
            elif s == "gelo":
                _gelo(d, _pontos_token(tok, int(9 * tam * dens) + 3), t)
            elif s == "eletrico":
                _eletrico(d, _pontos_token(tok, int(3 * tam * dens) + 2), t)
            elif s == "molhado":
                _pingos(d, _pontos_token(tok, int(8 * tam * dens) + 3), t, QColor("#bfe8ff"), alto * 0.5)
            elif s == "sangue":   # gotas maiores e vivas (escuras demais sumiam no chão)
                pts_s = _pontos_token(tok, int(10 * tam * dens) + 4)
                _pingos(d, pts_s, t, QColor("#d42020"), alto * 0.5, raio=0.085)
                x, y = pts_s.X[::2], pts_s.Y[::2]           # manchinhas no chão, pulsando devagar
                d.bolinhas(x, y, 0.01 * M, 0.11, QColor("#7a0c0c"), 0.55 + 0.15 * np.sin(t * 2 + x))
            elif s == "luz":
                _luz(d, _pontos_token(tok, int(10 * tam * dens) + 3), t, "luz", QColor("#fff2b0"), None, None)
            elif s == "planta":
                _planta(d, _pontos_token(tok, int(6 * tam * dens) + 3), t)
        d.descarregar()
    finally:
        painter.restore()
