"""
Câmera 3D da mesa (v0.33): sempre de cima, com perspectiva, ninguém gira.

A câmera fica acima do CENTRO da tela. O chão (altura 0) aparece exatamente como na mesa 2D
(grid, cliques, régua, visão: nada muda). O que tem altura "vem pra câmera": um ponto na altura z
se afasta do centro da tela pelo fator  f = H / (H − z), onde H é a altura da câmera.

Truque que deixa tudo simples: um plano inteiro numa mesma altura é só o desenho 2D AMPLIADO
pelo fator f a partir do centro da tela (uma transformação afim). Então o TOPO de uma parede é
o próprio desenho da parede, ampliado; e as LATERAIS ligam o contorno do pé ao contorno do topo.

Tudo em coordenadas do dispositivo (pixels da tela), a partir do worldTransform do QPainter.

(v0.70) CÂMERA LIVRE: a visão pode GIRAR (o giro já vem no worldTransform, é afim) e INCLINAR. Inclinada, a
câmera fica atrás e acima do centro da tela, olhando pra ele: o chão vira um plano em perspectiva (uma
homografia, `homografia(...)`, que a própria visão aplica — mesa/visao.py) e um plano na altura z também
(`transformacao_topo` continua valendo: agora é projetiva). Com inclinação 0 as contas são EXATAMENTE as de antes.
Modelo (pixels da tela, relativos ao centro c; D = altura da câmera; θ = inclinação):
    ponto (X, Y) do chão "visto de cima", na altura Z:  den = D − Y·sen θ − Z·cos θ
    tela = c + (X, Y·cos θ − Z·sen θ) · D / den
"""

import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF, QTransform

from ..config import CELULA

ALTURA_PAREDE = 2.0 * CELULA       # 2 m
ALTURA_PORTA = 1.85 * CELULA
CAMERA_ALTURA_TELAS = 1.8          # altura da câmera, em "alturas da tela" (menor = mais dramático)
INCLINACAO_MAX = 55.0              # graus — o horizonte nunca entra na tela (o grid é o limite)
# (v0.75) "Pelos olhos de…": câmera mais baixa (altura 1 tela) e bem mais deitada — o horizonte ENTRA na tela
INCLINACAO_OLHOS = 72.0
ALTURA_OLHOS_TELAS = 1.0

_ESTADO = {"inclinacao": 0.0, "telas": CAMERA_ALTURA_TELAS}   # (a visão avisa: inclinação AGORA e altura da câmera)


def definir_inclinacao(graus: float, maximo: float = INCLINACAO_OLHOS):
    _ESTADO["inclinacao"] = math.radians(max(0.0, min(maximo, float(graus))))


def definir_livre(livre: bool):
    """(v0.77) A visão avisa se a câmera está LIVRE (o standee fica em pé de verdade) ou travada (vira pra câmera)."""
    _ESTADO["livre"] = bool(livre)


def camera_livre() -> bool:
    return _ESTADO.get("livre", False)


def avisar_movimento():
    """(v0.76) A câmera mexeu agora (a visão avisa a cada mudança)."""
    import time
    _ESTADO["mexeu"] = time.monotonic()


def em_movimento() -> bool:
    """(v0.76) QUALIDADE ADAPTATIVA: enquanto a câmera gira/anda (e até 0,15 s depois) quem é caro desenha mais
    leve — a mesa inteira é redesenhada a cada quadro nessa hora. Parou, a visão redesenha com tudo."""
    import time
    return time.monotonic() - _ESTADO.get("mexeu", 0.0) < 0.15


def definir_altura_telas(telas: float):
    _ESTADO["telas"] = max(0.5, float(telas))


def altura_telas() -> float:
    """Altura da câmera em "alturas da tela" (1,8 normal; 1,0 pelos olhos)."""
    return _ESTADO.get("telas", CAMERA_ALTURA_TELAS)


def linha_horizonte(cy: float, D: float, teta: float) -> float:
    """Altura na tela (px) onde fica o horizonte; muito negativo = fora da tela (em cima)."""
    s = math.sin(teta)
    if s < 1e-4:
        return -1e9
    return cy - D * math.cos(teta) / s


def inclinacao() -> float:
    """Radianos."""
    return _ESTADO["inclinacao"]


def homografia(cx: float, cy: float, D: float, teta: float, Z: float = 0.0) -> QTransform:
    """Chão "visto de cima" (pixels de tela) → tela com a câmera inclinada, pra um plano na altura Z (px).
    teta = 0 → só o "amplia a partir do centro" de sempre (fator D/(D−Z))."""
    s, c = math.sin(teta), math.cos(teta)
    m23 = -s / D
    m33 = 1 + (cy * s - Z * c) / D
    return QTransform(1, 0, 0,
                      cx * m23, c + cy * m23, m23,
                      cx * m33 - cx, cy * m33 - cy * c - Z * s, m33)


# (v0.70) Inclinada, o Qt NÃO desenha item cujo retângulo passa por trás da câmera (grid, paredes 3D, névoa,
# mapa enorme…: o retângulo "infinito" projetado dá lixo). Então esses itens, com a câmera inclinada, dizem que
# ocupam só o pedaço do chão que aparece na tela (`limitar`). A visão avisa quando esse pedaço muda.
import weakref as _weakref

_GRANDES = _weakref.WeakSet()


def definir_visivel(r):
    """A visão inclinada informa o chão visível (cena, já com folga); None = sem limite."""
    _ESTADO["visivel"] = QRectF(r) if r is not None else None


def limitar(item, r: QRectF) -> QRectF:
    """boundingRect de item grande: com a câmera inclinada, cortado no chão visível."""
    _GRANDES.add(item)
    v = _ESTADO.get("visivel")
    if v is None or _ESTADO["inclinacao"] <= 0.0:
        return r
    try:
        vl = item.mapRectFromScene(v) if item.scene() is not None else v
    except RuntimeError:
        return r
    return r.intersected(vl)


def avisar_grandes(cena):
    """O chão visível mudou: os itens grandes daquela cena refazem o retângulo."""
    for item in list(_GRANDES):
        try:
            if item.scene() is cena:
                item.prepareGeometryChange()
        except (RuntimeError, AttributeError):
            continue


def nevoa_da_cena(cena):
    """(v0.70) A névoa de guerra da cena (só na tela do jogador), pro corpo 3D consultar; None = sem névoa."""
    nv = getattr(cena, "nevoa", None) if cena is not None else None
    try:
        if nv is None or not getattr(nv, "ativa", False) or not nv.isVisible():
            return None
    except RuntimeError:
        return None
    return nv


def escala_de(t: QTransform) -> float:
    """Zoom de uma transformação (funciona girada; inclinada, é o zoom no meio da tela)."""
    if t.isAffine():
        return math.hypot(t.m11(), t.m12()) or 1.0
    return math.hypot(t.m11(), t.m12()) / abs(t.m33() or 1.0) or 1.0


def mvp(t: QTransform, w: float, h: float):
    """Matriz pro OpenGL (pixels → clip) que respeita a perspectiva da câmera inclinada."""
    from PyQt6.QtGui import QMatrix4x4
    return QMatrix4x4(2 * t.m11() / w - t.m13(), 2 * t.m21() / w - t.m23(), 0, 2 * t.dx() / w - t.m33(),
                      t.m13() - 2 * t.m12() / h, t.m23() - 2 * t.m22() / h, 0, t.m33() - 2 * t.dy() / h,
                      0, 0, 1, 0,
                      t.m13(), t.m23(), 0, t.m33())

LUZ_2D = (-0.55, -0.83)            # de onde vem a luz no chão (cima-esquerda), normalizado


def ligada() -> bool:
    """A mesa está em modo 3D? (Gráficos → 'Mesa em 3D'; no Baixo fica sempre 2D)."""
    from ..graficos import graficos, nivel
    return nivel() >= 1 and getattr(graficos(), "mesa3d", True)


class Camera:
    """A câmera pro desenho de UM quadro (criada a partir do QPainter)."""

    def __init__(self, painter: QPainter):
        completo = painter.worldTransform()             # cena → tela (já inclinado, se a câmera estiver)
        self.completo = completo
        dev = painter.device()
        w = dev.width() if dev is not None else 1000
        h = dev.height() if dev is not None else 800
        self.centro = QPointF(w / 2, h / 2)
        self.H = altura_telas() * max(h, 1)              # altura da câmera, em pixels de tela (v0.75: varia)
        # (v0.70) inclinada: separa a parte "de cima" (afim: zoom, giro, posição) da perspectiva
        self.teta = inclinacao() if not completo.isAffine() else 0.0
        if self.teta > 1e-4:
            H0 = homografia(self.centro.x(), self.centro.y(), self.H, self.teta)
            m = completo * H0.inverted()[0]
            k = m.m33() or 1.0
            self.mundo = QTransform(m.m11() / k, m.m12() / k, m.m21() / k, m.m22() / k, m.dx() / k, m.dy() / k)
        else:
            self.teta = 0.0
            self.mundo = completo
        self._s, self._c = math.sin(self.teta), math.cos(self.teta)
        self.escala = (self.mundo.m11() ** 2 + self.mundo.m12() ** 2) ** 0.5 or 1.0

    @property
    def inclinada(self) -> bool:
        return self.teta > 0.0

    def fator(self, z: float) -> float:
        """Quanto um plano na altura z (unidades da cena) é ampliado (no meio da tela)."""
        zpx = z * self.escala * self._c
        return self.H / max(1.0, self.H - zpx)

    def transformacao_topo(self, z: float) -> QTransform:
        """Transformação cena → tela de um plano na altura z (pra desenhar o "topo" com o 2D de sempre)."""
        c = self.centro
        if self.teta == 0.0:
            f = self.fator(z)
            amplia = QTransform(f, 0, 0, f, c.x() * (1 - f), c.y() * (1 - f))
            return self.mundo * amplia
        return self.mundo * homografia(c.x(), c.y(), self.H, self.teta, z * self.escala)

    def z_max(self) -> float:
        """Altura máxima (unidades da cena) pra algo não "estourar" na câmera (no máx. 2,2× maior)."""
        return 0.55 * self.H / self.escala

    def projetar(self, p: QPointF, z: float) -> QPointF:
        d = self.mundo.map(p)
        if self.teta == 0.0:
            f = self.fator(z)
            return self.centro + (d - self.centro) * f
        X, Y, Z = d.x() - self.centro.x(), d.y() - self.centro.y(), z * self.escala
        k = self.H / max(1.0, self.H - Y * self._s - Z * self._c)
        return QPointF(self.centro.x() + X * k, self.centro.y() + (Y * self._c - Z * self._s) * k)

    def projetar_np(self, x, y, z):
        """Muitos pontos de uma vez (numpy): devolve (sx, sy, f) — f = quanto a coisa é ampliada ali."""
        import numpy as np
        m = self.mundo
        X = m.m11() * x + m.m21() * y + m.dx() - self.centro.x()
        Y = m.m12() * x + m.m22() * y + m.dy() - self.centro.y()
        Z = z * self.escala
        f = self.H / np.maximum(1.0, self.H - Y * self._s - Z * self._c)
        return self.centro.x() + X * f, self.centro.y() + (Y * self._c - Z * self._s) * f, f

    def pe_cena(self) -> QPointF:
        """Onde a câmera está, no chão (cena). Reto de cima = o centro da tela; inclinada = mais pra trás.
        É pra esse ponto que as faces das paredes/portas precisam estar viradas pra aparecer."""
        return self.mundo.inverted()[0].map(QPointF(self.centro.x(), self.centro.y() + self.H * self._s))

    def area_visivel(self) -> QRectF:
        """O pedaço do chão (cena) que aparece na tela (inclinada, é um trapézio: o retângulo em volta).
        (v0.75) Com o horizonte na tela, vale o chão que a visão calculou (corta no horizonte e longe)."""
        w, h = self.centro.x() * 2, self.centro.y() * 2
        topo = 0.0
        if self.teta > 0.0:   # só o que fica abaixo do horizonte (e não colado nele: lá é longe demais)
            topo = max(0.0, linha_horizonte(self.centro.y(), self.H, self.teta) + 0.06 * h)
        tela = QRectF(0, topo, w, max(1.0, h - topo))
        return self.completo.inverted()[0].mapRect(tela)

    def na_frente(self, p: QPointF, z: float = 0.0) -> bool:
        """(v0.75) O ponto está na frente da câmera (longe o bastante pra projetar direito)?"""
        if self.teta == 0.0:
            return True
        d = self.mundo.map(p)
        Y, Z = d.y() - self.centro.y(), z * self.escala
        return self.H - Y * self._s - Z * self._c > 0.12 * self.H


def margem(z: float) -> float:
    """Folga (unidades da cena) no boundingRect de algo com altura z: o topo se desloca pra fora na
    borda da tela e não pode ser cortado. Com a câmera a 1,8 telas, ~1 m de folga por 2 m de altura."""
    return 1.2 * CELULA * (z / ALTURA_PAREDE) + 4


_ARESTAS = {}   # id(solido) -> (solido, arestas): as paredes só mudam quando o contorno muda


def _arestas(poligonos, solido):
    """[(a, b, nx, ny, meio, luz)] de cada aresta, com a normal já virada pra FORA. Guardado por contorno
    (`solido`): a conta do "lado de fora" (solido.contains) é cara e não muda com a câmera.
    `poligonos` pode ser uma função (só é chamada se não tiver guardado)."""
    if solido is not None:
        ent = _ARESTAS.get(id(solido))
        if ent is not None and ent[0] is solido:
            return ent[1]
    if callable(poligonos):
        poligonos = poligonos()
    saida = []
    for pol in poligonos:
        n = pol.count()
        if n < 3:
            continue
        # sentido do contorno (pra saber qual lado é "fora")
        area = sum(pol[i].x() * pol[(i + 1) % n].y() - pol[(i + 1) % n].x() * pol[i].y() for i in range(n))
        sinal = 1 if area > 0 else -1
        for i in range(n):
            a, b = QPointF(pol[i]), QPointF(pol[(i + 1) % n])
            dx, dy = b.x() - a.x(), b.y() - a.y()
            comp = (dx * dx + dy * dy) ** 0.5
            if comp < 0.5:
                continue
            nx, ny = dy / comp * sinal, -dx / comp * sinal   # normal pra fora
            meio = QPointF((a.x() + b.x()) / 2, (a.y() + b.y()) / 2)
            if solido is not None and solido.contains(QPointF(meio.x() + nx * 1.5, meio.y() + ny * 1.5)):
                nx, ny = -nx, -ny   # o "fora" estava do lado de dentro da parede: inverte
            luz = -(nx * LUZ_2D[0] + ny * LUZ_2D[1])           # 1 = de frente pra luz
            saida.append((a, b, nx, ny, meio, luz))
    if solido is not None:
        if len(_ARESTAS) > 256:
            _ARESTAS.clear()
        _ARESTAS[id(solido)] = (solido, saida)
    return saida


def nevoa_da_parede(nevoa, cam, a: QPointF, b: QPointF, nx: float, ny: float, folga: float = 0.35 * CELULA,
                    pontos=(0.2, 0.5, 0.8)) -> float:
    """(v0.70) Quanto a névoa cobre uma parede/face de `a` a `b` (normal nx, ny): o MENOR valor entre os dois
    lados, em 3 pontos ao longo (a parede é conhecida se o chão de qualquer lado dela foi visto)."""
    melhor = 1.0
    for t in pontos:
        x, y = a.x() + (b.x() - a.x()) * t, a.y() + (b.y() - a.y()) * t
        for s in (1, -1):
            melhor = min(melhor, nevoa.amostrar(cam.projetar(QPointF(x + nx * folga * s, y + ny * folga * s), 0.0)))
            if melhor <= 0.0:
                return 0.0
    return melhor


def desenhar_laterais(painter: QPainter, cam: Camera, poligonos, altura: float, cor: QColor,
                      cor_alto: QColor | None = None, base: float = 0.0, solido=None, textura=None,
                      luzes=(), escala_tex: float = 1.0, nevoa=None):
    """
    `nevoa` (v0.70): a névoa de guerra do jogador (camera3d.nevoa_da_cena) — cada face pega a névoa do PÉ
    dela: coberta = não aparece; meio coberta (já explorada / no escuro) = escurecida na mesma medida.
    As 'paredes laterais' de uma extrusão: cada aresta do contorno vira um quadrilátero da altura
    `base` até `altura`. Só as faces viradas pro centro da tela aparecem (as outras ficam escondidas).
    A cor muda conforme a face está de frente ou de costas pra luz; o alfa da cor é respeitado.
    Os polígonos estão nas coordenadas do QPainter (cena ou as do próprio item).
    `solido` (QPainterPath): se vier, decide qual lado de cada aresta é "fora" testando um ponto ao
    lado dela (necessário em contornos com buraco, como o anel de paredes de uma sala).
    `textura` (QPixmap): se vier, a face é pintada com ela (pedra, tijolo…) e só escurecida pela luz.
    `luzes`: [(centro, raio, cor, polígono alcançado ou None)] — tocha perto pinta a face de frente
    pra ela com a cor da luz (a luz "lambe" a parede), se a luz alcança aquele ponto.
    """
    faces = []
    c_cena = cam.pe_cena()
    # (v0.47) só as faces perto da tela (o topo "anda" pra fora até ~margem(altura))
    folga = margem(altura) + CELULA
    vis = cam.area_visivel().adjusted(-folga, -folga, folga, folga)
    vx0, vy0, vx1, vy1 = vis.left(), vis.top(), vis.right(), vis.bottom()
    cx, cy = c_cena.x(), c_cena.y()
    for a, b, nx, ny, meio, luz in _arestas(poligonos, solido):
        mx, my = meio.x(), meio.y()
        if (max(a.x(), b.x()) < vx0 or min(a.x(), b.x()) > vx1
                or max(a.y(), b.y()) < vy0 or min(a.y(), b.y()) > vy1):
            continue
        # aparece se a face olha pro lado do centro da tela (onde está a câmera)
        if nx * (cx - mx) + ny * (cy - my) <= 0:
            continue
        if cam.teta > 0.0 and not (cam.na_frente(a, base) and cam.na_frente(b, base)
                                   and cam.na_frente(a, altura) and cam.na_frente(b, altura)):
            continue   # (v0.75) pelos olhos: o que ficou atrás da câmera não aparece
        dist = (cx - mx) ** 2 + (cy - my) ** 2
        pedacos = None
        corte = _ESTADO.get("corte_y") if cam.teta > 0.0 else None
        if nevoa is not None or corte is not None:
            # névoa de guerra: a face em pedaços de ~1 m, cada um com a névoa dos lados dele;
            # (v0.75) pelos olhos: pedaço com o pé ATRÁS do token (entre ele e a câmera) não aparece
            comp = math.hypot(b.x() - a.x(), b.y() - a.y())
            n = max(1, min(24, math.ceil(comp / CELULA)))
            pedacos = []
            for k in range(n):
                t0, t1 = k / n, (k + 1) / n
                pa = QPointF(a.x() + (b.x() - a.x()) * t0, a.y() + (b.y() - a.y()) * t0)
                pb = QPointF(a.x() + (b.x() - a.x()) * t1, a.y() + (b.y() - a.y()) * t1)
                nv_p = nevoa_da_parede(nevoa, cam, pa, pb, nx, ny, pontos=(0.5,)) if nevoa is not None else 0.0
                if corte is not None:
                    meio_p = QPointF((pa.x() + pb.x()) / 2, (pa.y() + pb.y()) / 2)
                    if cam.projetar(meio_p, base).y() > corte:
                        nv_p = 1.0
                pedacos.append((pa, pb, nv_p))
            if all(p[2] >= 0.97 for p in pedacos):
                continue
        faces.append((dist, a, b, luz, meio, nx, ny, pedacos))
    faces.sort(key=lambda f: -f[0])   # mais longe do centro primeiro
    if not faces:
        return
    # (v0.76) as quinas de TODAS as faces projetadas de uma vez (numpy) — antes, 4 a 6 chamadas por face, por quadro
    import numpy as np
    n_f = len(faces)
    ax = np.array([f_[1].x() for f_ in faces]); ay = np.array([f_[1].y() for f_ in faces])
    bx = np.array([f_[2].x() for f_ in faces]); by = np.array([f_[2].y() for f_ in faces])
    zb, za = np.full(n_f, float(base)), np.full(n_f, float(altura))
    za9 = np.full(n_f, float(altura) * 0.93)
    px, py, _f = cam.projetar_np(np.concatenate([ax, bx, bx, ax, bx, ax]), np.concatenate([ay, by, by, ay, by, ay]),
                                 np.concatenate([zb, zb, za, za, za9, za9]))
    px, py = px.reshape(6, n_f), py.reshape(6, n_f)
    painter.save()
    painter.resetTransform()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    cor_nevoa = QColor(getattr(nevoa, "cor", QColor(15, 13, 11)))
    for i_f, (_, a, b, luz, meio, nx, ny, pedacos) in enumerate(faces):
        quad = QPolygonF([QPointF(float(px[k, i_f]), float(py[k, i_f])) for k in range(4)])
        quads_p = []
        if pedacos:   # só os pedaços que o jogador conhece aparecem (o resto nem é desenhado)
            quads_p = [(QPolygonF([cam.projetar(pa, base), cam.projetar(pb, base), cam.projetar(pb, altura),
                                   cam.projetar(pa, altura)]), nv) for pa, pb, nv in pedacos]
            painter.save()
            if any(nv >= 0.97 for _q, nv in quads_p):
                clip = QPainterPath()
                clip.setFillRule(Qt.FillRule.WindingFill)
                for q, nv in quads_p:
                    if nv < 0.97:
                        clip.addPolygon(q)
                painter.setClipPath(clip)
        # entre ~0.6 (de costas pra luz) e ~0.95 (de frente). v0.34.1: antes ia até 0.17 e as faces
        # viradas pra baixo/direita ficavam quase pretas (o Manel achou que era mancha)
        fator = 0.78 + 0.17 * max(-1.0, min(1.0, luz))
        if textura is not None:
            # textura "colada" na face: u ao longo da aresta, v na altura (em unidades da cena)
            d0, d1, d2 = quad[0], quad[1], quad[3]
            comp = max(1e-3, ((b.x() - a.x()) ** 2 + (b.y() - a.y()) ** 2) ** 0.5)
            alt = max(1e-3, altura - base)
            pincel = QBrush(textura)
            face = None
            if cam.teta > 0.0:
                # (v0.77) câmera inclinada: a face vira um TRAPÉZIO — a textura vai com perspectiva de verdade,
                # canto a canto (a conta "afim" de antes usava a escala da ponta perto na parede toda: "zoom")
                e = escala_tex
                origem = QPolygonF([QPointF(0, 0), QPointF(comp * e, 0), QPointF(comp * e, alt * e), QPointF(0, alt * e)])
                destino = QPolygonF([quad[0], quad[1], quad[2], quad[3]])
                tq = QTransform()
                if QTransform.quadToQuad(origem, destino, tq):
                    face = tq
            if face is None:
                face = QTransform((d1.x() - d0.x()) / comp, (d1.y() - d0.y()) / comp,
                                  (d2.x() - d0.x()) / alt, (d2.y() - d0.y()) / alt, d0.x(), d0.y())
                if escala_tex != 1.0:   # (v0.67) textura com mais pixels por unidade da cena (porta nítida)
                    face = QTransform.fromScale(1 / escala_tex, 1 / escala_tex) * face
            pincel.setTransform(face)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(pincel)
            painter.drawPolygon(quad)
            # luz: escurece as faces de costas, e um degradê do pé (mais escuro) pro alto
            g = QLinearGradient(QPointF((d0.x() + d1.x()) / 2, (d0.y() + d1.y()) / 2), QPointF(
                (quad[2].x() + quad[3].x()) / 2, (quad[2].y() + quad[3].y()) / 2))
            sombra = int(200 * (1 - fator))
            g.setColorAt(0, QColor(0, 0, 0, min(255, sombra + 30)))   # pé só um pouco mais escuro
            g.setColorAt(1, QColor(0, 0, 0, sombra))
            painter.setBrush(QBrush(g))
            painter.setPen(QPen(QColor(0, 0, 0, 120), 1))
            painter.drawPolygon(quad)
        else:
            tom = QColor(int(cor.red() * fator), int(cor.green() * fator), int(cor.blue() * fator), cor.alpha())
            painter.setPen(tom.darker(115))
            painter.setBrush(tom)
            painter.drawPolygon(quad)
        if luzes:   # tochas, lampiões, cristais… iluminando a face (soma a cor da luz)
            r, g_, b_ = 0.0, 0.0, 0.0
            frente = QPointF(meio.x() + nx * 3, meio.y() + ny * 3)
            for centro, raio, cor_luz, alcance in luzes:
                vx, vy = centro.x() - meio.x(), centro.y() - meio.y()
                d = (vx * vx + vy * vy) ** 0.5
                if d >= raio or d < 1e-3:
                    continue
                de_frente = (vx * nx + vy * ny) / d
                if de_frente <= 0:
                    continue
                if alcance is not None and not alcance.containsPoint(frente, Qt.FillRule.OddEvenFill):
                    continue   # tem parede no caminho
                k = (1 - d / raio) ** 1.6 * (0.35 + 0.65 * de_frente)
                r += cor_luz.red() * k
                g_ += cor_luz.green() * k
                b_ += cor_luz.blue() * k
            if r + g_ + b_ > 6:
                painter.save()
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
                painter.setPen(Qt.PenStyle.NoPen)
                forca = 0.55
                painter.setBrush(QColor(min(255, int(r * forca)), min(255, int(g_ * forca)), min(255, int(b_ * forca))))
                painter.drawPolygon(quad)
                painter.restore()
        if cor_alto is not None:   # filete claro no alto da face (a quina pega luz)
            topo = QPolygonF([QPointF(float(px[5, i_f]), float(py[5, i_f])), QPointF(float(px[4, i_f]), float(py[4, i_f])),
                              quad[2], quad[3]])
            painter.setPen(QColor(0, 0, 0, 0))
            painter.setBrush(QColor(cor_alto.red(), cor_alto.green(), cor_alto.blue(), int(60 + 50 * max(0, luz))))
            painter.drawPolygon(topo)
        if pedacos:   # (v0.70) névoa de guerra / escuro de cada pedaço
            painter.setPen(Qt.PenStyle.NoPen)
            for q, nv in quads_p:
                if 0.02 < nv < 0.97:
                    cn = QColor(cor_nevoa)
                    cn.setAlphaF(nv)
                    painter.setBrush(cn)
                    painter.drawPolygon(q)
            painter.restore()
    painter.restore()
