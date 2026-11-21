"""
Camada das coisas ALTAS da mesa 3D (v0.34): o corpo das paredes e das portas.

Fica por cima dos tokens e objetos (z 700.000) e por baixo dos cones de visão do mestre, da luz e
da névoa. Assim um token do outro lado de uma parede alta fica escondido atrás dela, e a névoa e o
escuro continuam cobrindo as paredes dos lugares que ninguém viu.

No 2D (Gráficos → Mesa em 3D desligado, ou Baixo) ela não desenha nada: as paredes e portas se
desenham sozinhas, como sempre.
"""

import weakref

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainterPath
from PyQt6.QtWidgets import QGraphicsItem

from ..config import CELULA, LIMITE_CENA
from . import camera3d

PORTAS = weakref.WeakSet()   # toda PortaItem se registra aqui (a camada acha as portas da cena)
STANDEES = weakref.WeakSet()   # tokens da Mesa 3D (v0.73: standee; v0.77: ficha também) — o corpo fica por aqui
OBJETOS = weakref.WeakSet()    # (v0.84) objetos com altura: o corpo entra na mesma fila de profundidade das fichas


def _centro(item) -> QPointF:
    if hasattr(item, "centro_cena"):
        return item.centro_cena()
    return item.mapToScene(QPointF(item.largura / 2, item.altura / 2))


def _casco(pts):
    from .token import _casco as c
    return c(pts)


class _ParedesDoQuadro:
    """(v0.84) As paredes vistas pela câmera NUM quadro: a parte que não depende do token (lado da câmera, silhueta
    na tela) é feita uma vez só e serve pra todos os tokens — antes era refeita por token, por parede, por quadro."""

    def __init__(self, cam, paredes):
        self.cam = cam
        pe = cam.pe_cena()
        self.segs = []
        for seg in list(getattr(paredes, "segmentos", {}).values()):
            try:
                a, b = paredes._pontos(seg)
            except Exception:
                continue
            ax, ay = a.x(), a.y()
            dx, dy = b.x() - ax, b.y() - ay
            comp2 = dx * dx + dy * dy
            if comp2 < 1:
                continue
            lado_cam = dx * (pe.y() - ay) - dy * (pe.x() - ax)
            self.segs.append([ax, ay, dx, dy, comp2, lado_cam, a, b, None])

    def _silhueta(self, s):
        if s[8] is None:
            from PyQt6.QtGui import QPolygonF
            from .construcao import ESPESSURA
            a, b, dx, dy, comp2 = s[6], s[7], s[2], s[3], s[4]
            comp = comp2 ** 0.5
            nx, ny = -dy / comp * ESPESSURA / 2, dx / comp * ESPESSURA / 2
            cam = self.cam
            pts = []
            for q in (QPointF(a.x() + nx, a.y() + ny), QPointF(a.x() - nx, a.y() - ny),
                      QPointF(b.x() + nx, b.y() + ny), QPointF(b.x() - nx, b.y() - ny)):
                pts.append(cam.projetar(q, 0.0))
                pts.append(cam.projetar(q, camera3d.ALTURA_PAREDE))
            s[8] = QPolygonF(_casco(pts))
        return s[8]

    def na_frente(self, base_cena: QPointF):
        bx, by = base_cena.x(), base_cena.y()
        saida = []
        for s in self.segs:
            ax, ay, dx, dy, comp2, lado_cam = s[0], s[1], s[2], s[3], s[4], s[5]
            lado_tok = dx * (by - ay) - dy * (bx - ax)
            if lado_cam * lado_tok >= 0:
                continue   # câmera e token do mesmo lado: essa parede não fica na frente
            t = ((bx - ax) * dx + (by - ay) * dy) / comp2
            if t < -0.6 or t > 1.6:
                continue
            saida.append(self._silhueta(s))
        return saida


def _na_frente(cam, paredes, base_cena: QPointF):
    """Silhuetas (na tela) das paredes que estão ENTRE a câmera e o ponto `base_cena` — só elas tapam o cartão."""
    return _ParedesDoQuadro(cam, paredes).na_frente(base_cena)


def _visivel(item) -> bool:
    while item is not None:
        if not item.isVisible():
            return False
        item = item.parentItem()
    return True


def luzes_da_cena(cena):
    """[(centro, raio, cor, polígono que a luz alcança)] — pra iluminar as laterais das paredes."""
    overlay = getattr(cena, "luz_overlay", None)
    saida = []
    for d, pol in (getattr(overlay, "luzes", None) or []):
        try:
            saida.append((QPointF(d["x"], d["y"]), float(d["fraco"]) * CELULA, QColor(d["cor"]), pol))
        except (KeyError, TypeError, ValueError):
            continue
    return saida


class ParedesAltas(QGraphicsItem):
    def __init__(self, paredes):
        super().__init__()
        self.paredes = paredes
        self.setZValue(700_000)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemUsesExtendedStyleOption, True)

    def boundingRect(self) -> QRectF:
        L = LIMITE_CENA
        from .camera3d import limitar
        return limitar(self, QRectF(-L, -L, 2 * L, 2 * L))   # (v0.70) câmera inclinada: só o chão visível

    def shape(self) -> QPainterPath:
        return QPainterPath()   # nunca pega clique

    def _particulas(self, painter, cena):
        """Partículas 3D das áreas de efeito (fogo subindo, neve caindo…)."""
        from ..graficos import nivel
        from .efeitos import agora
        from .efeitos3d import AREAS, desenhar
        areas = []
        for area in list(AREAS):
            try:
                if area.scene() is cena and _visivel(area):
                    areas.append(area)
            except RuntimeError:   # área já apagada
                AREAS.discard(area)
        if not areas:
            return
        cam = camera3d.Camera(painter)
        t = agora()
        n = nivel()
        painter.save()
        painter.resetTransform()
        for area in areas:
            try:
                desenhar(painter, cam, area, t, n)
            except Exception as erro:
                from ..seguranca import registrar_erro
                registrar_erro(f"Partículas 3D ({getattr(area, 'efeito', '?')}) falharam: {erro!r}")
                AREAS.discard(area)
        painter.restore()

    def _cartoes(self, painter, cena):
        """(v0.73) Os cartões dos STANDEES: depois das paredes (a parede de TRÁS não corta mais o cartão), mas
        recortados pelas paredes que estão entre a câmera e o token (a da frente continua escondendo)."""
        from ..graficos import nivel
        lista = []
        for grupo in (STANDEES, OBJETOS):
            for tok in list(grupo):
                try:
                    if tok.scene() is None:
                        grupo.discard(tok)   # saiu da mesa
                        continue
                    if tok.scene() is not cena or not _visivel(tok):
                        continue   # (é de outra cena — mestre e jogador no mesmo programa —, fica na lista)
                    lista.append(tok)
                except RuntimeError:
                    grupo.discard(tok)
        if not lista:
            return
        cam = camera3d.Camera(painter)
        pe = cam.pe_cena()
        def dist(t):
            c = _centro(t)
            return (c.x() - pe.x()) ** 2 + (c.y() - pe.y()) ** 2
        lista.sort(key=lambda t: -dist(t))   # do mais longe pro mais perto
        n = nivel()
        base_cena = painter.worldTransform()
        quadro = _ParedesDoQuadro(cam, self.paredes) if self.paredes is not None else None
        recortes = {}   # (v0.84) tokens atrás das MESMAS paredes usam o mesmo recorte (feito uma vez só)
        dev = painter.device()
        painter.save()
        painter.resetTransform()
        for tok in lista:
            try:
                painter.save()
                frente = quadro.na_frente(_centro(tok)) if quadro is not None else []
                if frente:
                    chave = tuple(id(pol) for pol in frente)
                    recorte = recortes.get(chave)
                    if recorte is None:
                        clip = QPainterPath()
                        clip.addRect(QRectF(0, 0, dev.width() if dev else 4000, dev.height() if dev else 4000))
                        tapa = QPainterPath()
                        tapa.setFillRule(Qt.FillRule.WindingFill)
                        for pol in frente:
                            tapa.addPolygon(pol)
                        recorte = recortes[chave] = clip.subtracted(tapa.simplified())
                    painter.setClipPath(recorte)
                if tok in OBJETOS:   # (v0.84) objeto com altura
                    if tok.effectiveOpacity() > 0.0:
                        painter.setWorldTransform(tok.sceneTransform() * base_cena)
                        painter.setOpacity(tok.effectiveOpacity())
                        tok.pintar_corpo_3d(painter, n)
                    continue
                if getattr(tok, "estilo", "ficha") == "standee":
                    if camera3d.camera_livre():   # (v0.77) livre: foto em pé de verdade, parada no mundo
                        tok.pintar_cartao_no_mundo(painter, cam, n)
                    else:                         # travada: o cartão virado pra câmera
                        tok.pintar_cartao(painter, cam, n)
                else:   # (v0.77) a ficha também, na ordem certa de profundidade
                    painter.setWorldTransform(tok.sceneTransform() * base_cena)
                    tok.pintar_corpo_3d(painter, n)
                # (v0.79) status com partículas (em chamas, envenenado, sangrando…) — logo depois do corpo dele
                from .efeitos3d import desenhar_status, status_do_token
                if status_do_token(tok):
                    from .efeitos import agora
                    painter.resetTransform()
                    desenhar_status(painter, cam, tok, agora(), n)
            except Exception as erro:
                from ..seguranca import registrar_erro
                registrar_erro(f"Cartão do standee não desenhou: {erro!r}")
            finally:
                painter.restore()
        painter.restore()

    def paint(self, painter, option, widget=None):
        # ATENÇÃO: erro dentro de paint() o PyQt6 trata como fatal (fecha o programa). Por isso tudo
        # aqui é protegido, e porta/parede que já foi apagada (aventura reaberta…) é ignorada.
        if not camera3d.ligada():
            return
        try:
            cena = self.scene()
            luzes = luzes_da_cena(cena)
            self._particulas(painter, cena)   # (antes das paredes: ficam atrás delas)
            if self.paredes is not None and _visivel(self.paredes):
                self.paredes.pintar_corpo_3d(painter, luzes)
        except RuntimeError:   # as paredes já foram apagadas pelo Qt
            return
        self._cartoes(painter, cena)
        base = painter.worldTransform()
        for porta in list(PORTAS):
            try:
                if porta.scene() is not cena or not _visivel(porta):
                    continue
            except RuntimeError:   # porta apagada (ex.: a aventura foi reaberta)
                PORTAS.discard(porta)
                continue
            painter.save()
            try:
                painter.setWorldTransform(porta.sceneTransform() * base)
                porta.pintar_3d(painter, luzes)
            except Exception as erro:
                from ..seguranca import registrar_erro
                registrar_erro(f"Porta 3D não desenhou: {erro!r}")
            finally:
                painter.restore()
