"""
A "câmera" da mesa: zoom com a rodinha, arrastar a visão com o botão do meio
(ou segurando Espaço), seleção em caixa com o botão esquerdo, e
arrastar-e-soltar imagens direto do Windows pra virar mapa.
"""

import math

from PyQt6.QtCore import QLineF, QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QGraphicsView

from ..config import CELULA, COR_DESTAQUE, COR_FUNDO_MESA, ZOOM_MAX, ZOOM_MIN, ZOOM_PASSO
from ..config import fmt_m
from .construcao import (ESPESSURA, distancia_segmento, restringir_angulo,
                         vertice_mais_proximo)

EXTENSOES_IMAGEM = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")


FERRAMENTAS_CLIQUE = ("fonte_fluido", "soltar_fluido")   # um clique no mapa e pronto (v0.45)


class MesaVisao(QGraphicsView):
    zoom_mudou = pyqtSignal(float)
    camera_mudou = pyqtSignal()                        # (v0.70) giro/inclinação/livre
    cursor_moveu = pyqtSignal(QPointF)
    cursor_saiu = pyqtSignal()
    imagem_solta = pyqtSignal(str, QPointF)
    menu_pedido = pyqtSignal(object, object, object)  # item, pos_tela, pos_cena
    ping_pedido = pyqtSignal(QPointF)                  # tecla P: sinal no mapa
    olhar_pedido = pyqtSignal(QPointF)                 # (v0.58) Shift+P: 📣 todos olhem pra cá (só o mestre usa)
    prop_solto = pyqtSignal(str, QPointF)              # objeto arrastado da biblioteca
    banco_solto = pyqtSignal(str, str, QPointF)        # uso, caminho (banco de imagens), posição
    efeito_pedido = pyqtSignal(dict)                   # área de efeito / template colocado
    traco_pedido = pyqtSignal(dict)                    # traço do lápis terminado
    ferramenta_saiu = pyqtSignal()                     # Esc no lápis/template
    impacto_pedido = pyqtSignal(QPointF)               # clique com a ferramenta de impacto (explosão, raio…)
    lancar_pedido = pyqtSignal(dict)                   # arrastou de quem lança até o alvo (bola de fogo…)
    clique_ferramenta = pyqtSignal(str, QPointF)       # ferramentas de um clique (fonte de gás, derramar…)

    def __init__(self, cena, parent=None):
        super().__init__(cena, parent)
        # (v0.70) 🎥 CÂMERA: centro (cena), zoom, giro e inclinação (graus). A visão aplica tudo de uma vez
        # (_aplicar_camera); com giro e inclinação 0 é a mesa de cima de sempre.
        self._cam_centro = QPointF(0, 0)
        self._cam_escala = 1.0
        self._cam_giro = 0.0
        self._cam_incl = 0.0
        self.camera_livre = False      # Travada = reto de cima (como sempre). Livre = Alt+arrastar gira/inclina
        self._aplicando = False
        self._orbitando = None
        self._olhos = None             # (v0.75) "pelos olhos de…": o token que a câmera acompanha
        self._olhos_antes = None
        self._olhos_timer = None
        from .luva import COR_MESTRE, cursor_luva
        self._cor_cursor = QColor(COR_MESTRE)   # (v0.48) 🧤 o ponteiro na cor do token (mestre: dourado)
        self.usa_placa_de_video = self._viewport_opengl()
        self.viewport().setCursor(self.cursor_padrao)
        self.setRenderHints(QPainter.RenderHint.Antialiasing
                            | QPainter.RenderHint.SmoothPixmapTransform
                            | QPainter.RenderHint.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        # Ancoragem feita "na mão" (ver _escalar_em): o ponto embaixo do mouse fica parado
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        # (v0.46.1) NoAnchor: o Qt recentralizava num centro ANTIGO ao abrir/fechar um painel (a mesa
        # "pulava"); quem segura o meio da tela no lugar agora é o resizeEvent abaixo.
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setBackgroundBrush(QBrush(QColor(COR_FUNDO_MESA)))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)

        self._arrastando_visao = False
        self._ultimo_pos = None
        self._espaco = False
        self._medindo = False        # segurando M: régua
        self._regua = None           # [início, fim] da régua (coordenadas da mesa)
        self._arrasto_token = None   # (token, centro inicial) enquanto arrasta um token
        self._op = None          # operação de construção em andamento
        self._hover: QPointF | None = None
        self._mods = Qt.KeyboardModifier.NoModifier
        # Zoom suave
        self.zoom_min = ZOOM_MIN   # (v0.62) com cidade ligada, dá pra afastar até a cidade aparecer
        self._zoom_alvo = 1.0
        self._zoom_ancora = QPointF()
        self._zoom_timer = QTimer(self)
        self._zoom_timer.setInterval(16)
        self._zoom_timer.timeout.connect(self._passo_zoom)
        # Seleção por arrasto: só pega item que estiver INTEIRO dentro (assim o mapa
        # de fundo não entra junto sem querer). Paredes e terreno: qualquer pedaço.
        self.setRubberBandSelectionMode(Qt.ItemSelectionMode.ContainsItemShape)
        self._area_arrasto = None
        self._somar_selecao = False
        self._op_efeito = None     # {"a": origem, "b": ponta} enquanto arrasta um template
        self._op_lance = None      # {"a": quem lança, "b": alvo} enquanto arrasta um lançamento
        self._cache_previa = {}
        self.rubberBandChanged.connect(self._arrasto_mudou)
        self.centerOn(0, 0)
        from ..graficos import graficos
        graficos().mudou.connect(self._graficos_mudou)
        from .bussola import Bussola   # (v0.70) bussola da camera livre (canto de baixo a direita)
        self.bussola = Bussola(self)
        self.bussola.reposicionar()

    @property
    def cursor_padrao(self):
        """O ponteiro do TEMA atual na cor do jogador (v0.64.1: cada tema tem o seu)."""
        from .luva import cursor_luva
        return cursor_luva(self._cor_cursor)

    # ------------------------------------------------------------ placa de vídeo
    def _viewport_opengl(self) -> bool:
        """
        Mesa 3D, parte 2 (v0.34): a mesa passa a ser desenhada pela PLACA DE VÍDEO (o mesmo desenho
        de sempre, mas o Qt manda pro OpenGL em vez de pintar no processador) — e o piso ganha relevo
        que reage à luz (relevo_gl). Só ao abrir o programa (trocar a 'tela' da mesa depois apagaria
        o que está por cima dela). Plano B: sem OpenGL, a mesa é desenhada como sempre.
        """
        from ..graficos import graficos
        from ..dados3d.overlay import opengl_disponivel
        if not opengl_disponivel() or not getattr(graficos(), "mesa3d", True):
            return False
        try:
            from PyQt6.QtGui import QSurfaceFormat
            from PyQt6.QtOpenGLWidgets import QOpenGLWidget
            tela = QOpenGLWidget()
            fmt = QSurfaceFormat()
            fmt.setSamples(4)          # borda lisa
            fmt.setStencilBufferSize(8)  # o Qt usa pra recortes (clip) no OpenGL
            fmt.setSwapInterval(1)
            tela.setFormat(fmt)
            self.setViewport(tela)
            return True
        except Exception as erro:
            from ..seguranca import registrar_erro
            registrar_erro(f"Mesa sem placa de vídeo (OpenGL não abriu): {erro!r}")
            return False

    # ------------------------------------------------------------ tremor de tela
    def resizeEvent(self, event):
        """Abriu/fechou um painel (a mesa mudou de tamanho): o que estava no meio da tela continua no meio
        (v0.70: o meio é o próprio estado da câmera)."""
        super().resizeEvent(event)
        self._aplicar_camera()
        if getattr(self, 'bussola', None) is not None:
            self.bussola.reposicionar()

    # ------------------------------------------------------------ (v0.70) 🎥 câmera livre
    def inclinacao_efetiva(self) -> float:
        """Graus. Afastando muito (pra cidade/mundo aparecerem), a câmera volta a ficar reto de cima."""
        k = max(0.0, min(1.0, (self._cam_escala - 0.3) / 0.25))
        return self._cam_incl * k if self.camera_livre else 0.0

    def giro(self) -> float:
        return self._cam_giro if self.camera_livre else 0.0

    def _aplicar_camera(self):
        """Monta a transformação: zoom + giro (afim) e, inclinada, a perspectiva em volta do meio da tela.
        O sceneRect da visão é um pontinho no centro da câmera: o Qt só centraliza (sem barras de rolagem)."""
        if self._aplicando:
            return
        self._aplicando = True
        try:
            from PyQt6.QtGui import QTransform
            from . import camera3d
            e = self._cam_escala
            A = QTransform().rotate(self.giro()).scale(e, e)
            c = self._cam_centro
            incl = self.inclinacao_efetiva()
            telas = camera3d.ALTURA_OLHOS_TELAS if self._olhos is not None else camera3d.CAMERA_ALTURA_TELAS
            camera3d.definir_altura_telas(telas)
            T = A
            h = max(1, self.viewport().height())
            if incl > 0.01:
                q = A.map(c)
                T = A * camera3d.homografia(q.x(), q.y(), telas * h, math.radians(incl))
            camera3d.definir_inclinacao(incl)
            camera3d.avisar_movimento()   # (v0.76) qualidade adaptativa enquanto mexe
            camera3d.definir_livre(self.camera_livre)   # (v0.77) standee: em pé no mundo (livre) ou virado (travada)
            if getattr(self, "_timer_parou", None) is None:
                self._timer_parou = QTimer(self)
                self._timer_parou.setSingleShot(True)
                self._timer_parou.setInterval(180)
                self._timer_parou.timeout.connect(self.viewport().update)   # parou: redesenha com tudo
            self._timer_parou.start()
            # (v0.75) pelos olhos o horizonte entra na tela: o chão "visível" é só o que fica abaixo dele
            self._horizonte = camera3d.linha_horizonte(h / 2, telas * h, math.radians(incl)) if incl > 0.01 else -1e9
            camera3d._ESTADO["corte_y"] = None
            QGraphicsView.setSceneRect(self, QRectF(c.x() - 0.5, c.y() - 0.5, 1.0, 1.0))
            QGraphicsView.setTransform(self, T)
            if self._olhos is not None:   # CORTE: parede entre a câmera e o token não tapa a visão
                try:
                    camera3d._ESTADO["corte_y"] = self.viewportTransform().map(self._olhos.centro_cena()).y() + 0.04 * h
                except RuntimeError:
                    pass
            # inclinada: os itens "infinitos" (grid, paredes 3D, névoa…) passam a ocupar só o chão visível
            if incl > 0.01:
                vp = QRectF(self.viewport().rect())
                if self._horizonte > -0.5 * vp.height():
                    topo = max(0.0, self._horizonte + 0.06 * vp.height())
                    vp = QRectF(0, topo, vp.width(), max(1.0, vp.height() - topo))
                inv, ok = self.viewportTransform().inverted()
                if ok:
                    folga = (0.15 if self._olhos is not None else 0.5) * self.viewport().height() / max(1e-4, e)
                    camera3d.definir_visivel(inv.mapRect(vp).adjusted(-folga, -folga, folga, folga))
                    camera3d.avisar_grandes(self.scene())
                    self._tinha_visivel = True
            elif getattr(self, "_tinha_visivel", False):
                camera3d.definir_visivel(None)
                camera3d.avisar_grandes(self.scene())
                self._tinha_visivel = False
        finally:
            self._aplicando = False
        self.viewport().update()

    def definir_camera(self, giro=None, inclinacao=None, livre=None):
        if livre is not None:
            self.camera_livre = bool(livre)
        if giro is not None:
            self._cam_giro = float(giro) % 360.0
        if inclinacao is not None:
            from .camera3d import INCLINACAO_MAX
            self._cam_incl = max(0.0, min(INCLINACAO_MAX, float(inclinacao)))
        self._aplicar_camera()
        self.camera_mudou.emit()

    # ------------------------------------------------------------ (v0.75) 👁 pelos olhos de…
    def ver_pelos_olhos(self, token):
        """A câmera vai pra trás do token, baixa e bem deitada, virada pra onde ele olha — e acompanha."""
        if token is None:
            return
        if self._olhos is None:   # guarda como estava, pra voltar igualzinho
            self._olhos_antes = (self.camera_livre, self._cam_giro, self._cam_incl, self._cam_escala)
        self._olhos = token
        self.camera_livre = True
        self._cam_escala = max(self._cam_escala, 1.1)
        if self._olhos_timer is None:
            self._olhos_timer = QTimer(self)
            self._olhos_timer.setInterval(16)
            self._olhos_timer.timeout.connect(self._seguir_olhos)
        # (v0.80) entra DESLIZANDO em ~0,3 s em vez de pular: pular pra longe/deitado refazia tudo num quadro só
        # (engasgo de ~0,6 s); deslizando, os quadros do meio vão no modo "em movimento" (mais leve)
        import time as _t
        self._olhos_ida = (_t.monotonic(), QPointF(self._cam_centro), self._cam_giro, self._cam_incl)
        self._seguir_olhos()
        self._olhos_timer.start()
        self.camera_mudou.emit()

    def pelos_olhos(self):
        return self._olhos

    def event(self, ev):
        # (v0.75) no "pelos olhos" o Esc é da mesa (senão um atalho da janela pega antes)
        from PyQt6.QtCore import QEvent
        if (ev.type() == QEvent.Type.ShortcutOverride and self._olhos is not None
                and ev.key() == Qt.Key.Key_Escape):
            ev.accept()
            return True
        return super().event(ev)

    def sair_dos_olhos(self):
        if self._olhos is None:
            return
        self._olhos = None
        self._olhos_ida = None
        if self._olhos_timer is not None:
            self._olhos_timer.stop()
        if self._olhos_antes is not None:
            livre, giro, incl, escala = self._olhos_antes
            self.camera_livre, self._cam_giro, self._cam_incl, self._cam_escala = livre, giro, incl, escala
            self._olhos_antes = None
        self._aplicar_camera()
        self.camera_mudou.emit()

    def _seguir_olhos(self, pular=False):
        tok = self._olhos
        try:
            if tok is None or tok.scene() is not self.scene() or not tok.isVisible():
                raise RuntimeError
            c = tok.centro_cena()
            dirr = math.radians(getattr(tok, "direcao", 0.0))
        except RuntimeError:
            self.sair_dos_olhos()
            return
        from .camera3d import INCLINACAO_OLHOS
        # o meio da tela fica um pouco À FRENTE do token (ele aparece embaixo, a câmera atrás dele)
        frente = 4.5 * CELULA
        alvo_c = QPointF(c.x() + math.cos(dirr) * frente, c.y() + math.sin(dirr) * frente)
        alvo_g = (-90.0 - math.degrees(dirr)) % 360.0
        ida = getattr(self, "_olhos_ida", None)
        if ida is not None and not pular:
            import time as _t
            t0, c0, g0, i0 = ida
            s = min(1.0, (_t.monotonic() - t0) / 0.3)
            s = s * s * (3 - 2 * s)
            dg = (alvo_g - g0 + 540.0) % 360.0 - 180.0
            self._cam_giro = (g0 + dg * s) % 360.0
            self._cam_centro = c0 + (alvo_c - c0) * s
            self._cam_incl = i0 + (INCLINACAO_OLHOS - i0) * s
            if s >= 1.0:
                self._olhos_ida = None
                self._cam_centro, self._cam_giro, self._cam_incl = alvo_c, alvo_g, INCLINACAO_OLHOS
            self._aplicar_camera()
            return
        if pular:
            self._cam_centro, self._cam_giro, self._cam_incl = alvo_c, alvo_g, INCLINACAO_OLHOS
        else:   # suave (gira pelo lado mais curto)
            k = 0.22
            dg = (alvo_g - self._cam_giro + 540.0) % 360.0 - 180.0
            mov = alvo_c - self._cam_centro
            if abs(dg) < 0.05 and mov.manhattanLength() < 0.3 and abs(self._cam_incl - INCLINACAO_OLHOS) < 0.05:
                return
            self._cam_giro = (self._cam_giro + dg * k) % 360.0
            self._cam_centro = self._cam_centro + mov * k
            self._cam_incl += (INCLINACAO_OLHOS - self._cam_incl) * k
        self._aplicar_camera()

    def camera_de_cima(self):
        """Volta pro reto de cima, sem giro (o "travar" da câmera)."""
        self.sair_dos_olhos()
        self.definir_camera(0.0, 0.0)

    # (os métodos de câmera do Qt viram mudanças no estado da câmera — quem chama continua igual)
    def scale(self, sx, sy=None):
        self._cam_escala = max(1e-4, self._cam_escala * float(sx))
        self._aplicar_camera()

    def translate(self, dx, dy):
        """Igual ao do Qt (sem âncora): o conteúdo anda (dx, dy) na cena = o centro anda ao contrário."""
        self._cam_centro = QPointF(self._cam_centro.x() - float(dx), self._cam_centro.y() - float(dy))
        self._aplicar_camera()

    def rotate(self, graus):
        self._cam_giro = (self._cam_giro + float(graus)) % 360.0
        self._aplicar_camera()

    def centerOn(self, *args):
        if len(args) == 2:
            alvo = QPointF(float(args[0]), float(args[1]))
        elif isinstance(args[0], QPointF):
            alvo = QPointF(args[0])
        elif hasattr(args[0], "sceneBoundingRect"):
            alvo = args[0].sceneBoundingRect().center()
        else:
            alvo = QPointF(args[0])
        self._cam_centro = alvo
        self._aplicar_camera()

    def setTransform(self, t, combine=False):
        """(o atlas usa) só o zoom e o giro vêm da transformação; o centro fica."""
        self._cam_escala = max(1e-4, math.hypot(t.m11(), t.m12()))
        self._cam_giro = math.degrees(math.atan2(t.m12(), t.m11())) % 360.0
        self._aplicar_camera()

    def resetTransform(self):
        self._cam_escala, self._cam_giro = 1.0, 0.0
        self._aplicar_camera()

    def fitInView(self, rect, modo=None):
        vp = self.viewport().rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return
        self._cam_escala = max(1e-4, min(vp.width() / rect.width(), vp.height() / rect.height()))
        self._cam_centro = rect.center()
        self._aplicar_camera()

    def _orbitar(self, delta: QPointF):
        """Alt+arrastar: pro lado gira, pra cima/baixo inclina."""
        self.definir_camera(self._cam_giro + delta.x() * 0.35, self._cam_incl + delta.y() * 0.25)

    def tremer(self, forca: float = 8.0, duracao: float = 0.5):
        """Chacoalha a câmera (explosão, terremoto). Volta exatamente pro lugar no fim."""
        import time as _t
        if not hasattr(self, "_tremor_timer"):
            self._tremor_timer = QTimer(self)
            self._tremor_timer.setInterval(16)
            self._tremor_timer.timeout.connect(self._passo_tremor)
            self._tremor_desvio = QPointF(0, 0)
        self._tremor = (float(forca), _t.monotonic(), max(0.05, float(duracao)))
        self._tremor_timer.start()

    def _passo_tremor(self):
        import math as _m
        import random as _r
        import time as _t
        forca, inicio, dur = self._tremor
        f = (_t.monotonic() - inicio) / dur
        antigo = self._tremor_desvio
        if f >= 1:
            novo = QPointF(0, 0)
            self._tremor_timer.stop()
        else:
            amp = forca * (1 - f) ** 1.5 / max(0.05, self.escala)
            novo = QPointF(_r.uniform(-1, 1) * amp, _r.uniform(-1, 1) * amp * 0.8 + _m.sin(f * 60) * amp * 0.3)
        self.translate(novo.x() - antigo.x(), novo.y() - antigo.y())
        self._tremor_desvio = novo

    def _graficos_mudou(self, _chave):
        # trocou Baixo/Médio/Alto: refaz o que estava guardado em cache e redesenha
        cena = self.scene()
        terreno = getattr(cena, "terreno", None)
        if terreno is not None:
            terreno._cache.clear()
            terreno.update()
        if cena is not None:
            cena.update()
        self.viewport().update()

    # ------------------------------------------------------------ zoom
    @property
    def escala(self) -> float:
        return self._cam_escala

    def _vp_para_cena(self, ponto: QPointF) -> QPointF:
        inversa, _ = self.viewportTransform().inverted()
        return inversa.map(ponto)

    def _escalar_em(self, escala: float, ancora: QPointF):
        """Muda o zoom mantendo parado o ponto da mesa que está em `ancora` (na tela)."""
        escala = max(self.zoom_min, min(ZOOM_MAX, escala))
        antes = self._vp_para_cena(ancora)
        fator = escala / self.escala
        self.scale(fator, fator)
        depois = self._vp_para_cena(ancora)
        delta = depois - antes
        self.translate(delta.x(), delta.y())
        self.scene().definir_escala(self.escala)
        self.zoom_mudou.emit(self.escala)

    def definir_zoom(self, escala: float):
        self._zoom_timer.stop()
        self._zoom_alvo = max(self.zoom_min, min(ZOOM_MAX, escala))
        self._escalar_em(escala, QPointF(self.viewport().rect().center()))

    def wheelEvent(self, event):
        passos = event.angleDelta().y() / 120.0   # funciona com mouse e touchpad
        if passos == 0 or self.camera_travada():
            event.accept()
            return
        if not self._zoom_timer.isActive():
            self._zoom_alvo = self.escala
        self._zoom_alvo = max(self.zoom_min, min(ZOOM_MAX, self._zoom_alvo * (ZOOM_PASSO ** passos)))
        self._zoom_ancora = event.position()
        self._zoom_timer.start()
        event.accept()

    def _passo_zoom(self):
        atual, alvo = math.log(self.escala), math.log(self._zoom_alvo)
        novo = atual + (alvo - atual) * 0.28
        if abs(alvo - novo) < 0.002:
            novo = alvo
            self._zoom_timer.stop()
        self._escalar_em(math.exp(novo), self._zoom_ancora)

    def zoom_100(self):
        self.definir_zoom(1.0)

    def centro_da_visao(self) -> QPointF:
        return self.mapToScene(self.viewport().rect().center())

    def enquadrar_tudo(self):
        if self.camera_travada():
            return
        cena = self.scene()
        itens = list(cena.itens_do_usuario())
        for especial in (getattr(cena, "terreno", None), getattr(cena, "paredes", None)):
            if especial is not None and especial.isVisible() and \
                    not especial.boundingRect().isEmpty():
                itens.append(especial)
        if not itens:
            self.centerOn(0, 0)
            return
        r = itens[0].sceneBoundingRect()
        for item in itens[1:]:
            r = r.united(item.sceneBoundingRect())
        self.fitInView(r.adjusted(-64, -64, 64, 64), Qt.AspectRatioMode.KeepAspectRatio)
        # fitInView pode passar dos limites
        self.definir_zoom(self.escala)

    # ------------------------------------------------------------ (v0.58) 📣 "todos olhem pra cá"
    def voar_para(self, ponto: QPointF, escala: float | None = None, duracao_ms: int = 900):
        """Desliza a câmera (centro e zoom) até `ponto`, suave."""
        from PyQt6.QtCore import QEasingCurve, QVariantAnimation
        anim = getattr(self, "_anim_voo", None)
        if anim is not None:
            anim.stop()
        self._zoom_timer.stop()
        de_c, de_e = self.centro_da_visao(), self.escala
        ate_e = max(self.zoom_min, min(ZOOM_MAX, escala or de_e))
        anim = self._anim_voo = QVariantAnimation(self)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(max(1, int(duracao_ms)))
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        def passo(t):
            t = float(t)
            e = math.exp(math.log(de_e) + (math.log(ate_e) - math.log(de_e)) * t)
            self._escalar_em(e, QPointF(self.viewport().rect().center()))
            self.centerOn(de_c + (ponto - de_c) * t)
        anim.valueChanged.connect(passo)
        anim.start()
        return anim

    def travar_camera(self, segundos: float):
        """Trava zoom/arrastar da câmera por alguns segundos (cena dramática do mestre)."""
        import time
        self._travada_ate = time.monotonic() + max(0.0, float(segundos))

    def camera_travada(self) -> bool:
        import time
        return time.monotonic() < getattr(self, "_travada_ate", 0.0)

    def _arrasto_mudou(self, retangulo, de_cena, ate_cena):
        if retangulo.isNull():
            # Terminou de arrastar: seleciona paredes e pinceladas na área também
            area, self._area_arrasto = self._area_arrasto, None
            cena = self.scene()
            if area is not None and area.width() > 2 and area.height() > 2 and \
                    hasattr(cena, "selecionar_construcao_em"):
                cena.selecionar_construcao_em(area, somar=self._somar_selecao)
        else:
            self._area_arrasto = QRectF(de_cena, ate_cena).normalized()

    def definir_fundo(self, cor: str):
        self.setBackgroundBrush(QBrush(QColor(cor)))

    # ------------------------------------------------------------ construção
    def _ferramenta(self) -> str:
        return getattr(self.scene(), "ferramenta", "selecionar")

    def definir_cor_cursor(self, cor):
        """🧤 A luvinha do mouse na cor escolhida (a cor do token do jogador)."""
        if QColor(cor).name() == self._cor_cursor.name():
            return
        self._cor_cursor = QColor(cor)
        try:
            from ..ui.cursor_global import definir_cor
            definir_cor(cor)   # (v0.51) a luvinha do programa todo acompanha
        except ImportError:
            pass
        if self._ferramenta() == "selecionar":
            self.viewport().setCursor(self.cursor_padrao)

    def atualizar_modo(self, *_):
        construindo = self._ferramenta() != "selecionar"
        self.setInteractive(not construindo)
        self.setDragMode(QGraphicsView.DragMode.NoDrag if construindo
                         else QGraphicsView.DragMode.RubberBandDrag)
        self.viewport().setCursor(Qt.CursorShape.CrossCursor if construindo
                                  else self.cursor_padrao)
        self._op = None
        self.viewport().update()

    @staticmethod
    def _ponto(pos: QPointF, mods) -> QPointF:
        """Ponta de parede/sala: gruda no canto do grid (Alt = livre)."""
        if mods & Qt.KeyboardModifier.AltModifier:
            return pos
        return vertice_mais_proximo(pos)

    def _fim_parede(self, a: QPointF, pos: QPointF, mods) -> QPointF:
        if mods & Qt.KeyboardModifier.ShiftModifier:
            return restringir_angulo(a, pos, 15)
        return self._ponto(pos, mods)

    def _press_construcao(self, event):
        cena = self.scene()
        pos = self.mapToScene(event.position().toPoint())
        mods = event.modifiers()
        ferramenta = self._ferramenta()
        if ferramenta in ("terreno", "borracha"):
            if cena.comecar_pincelada(pos, apagar=(ferramenta == "borracha")):
                self._op = {"tipo": "pincel"}
        elif ferramenta == "borracha_parede":
            cena.apagar_paredes_em(pos)
            self._op = {"tipo": "borracha_parede", "ultimo": pos}
        elif ferramenta in ("parede", "sala"):
            self._op = {"tipo": ferramenta, "a": self._ponto(pos, mods)}
        elif ferramenta == "porta":
            porta = cena.colocar_porta(pos)
            if porta:
                cena.clearSelection()
                porta.setSelected(True)
        elif ferramenta == "luz":
            luz = cena.colocar_luz(pos)
            if luz:
                cena.clearSelection()
                luz.setSelected(True)
        self.viewport().update()

    def _release_construcao(self, event):
        cena = self.scene()
        op, self._op = self._op, None
        if not op:
            return
        pos = self.mapToScene(event.position().toPoint())
        mods = event.modifiers()
        if op["tipo"] == "pincel":
            cena.terminar_pincelada()
        elif op["tipo"] == "borracha_parede":
            cena.registrar()
        elif op["tipo"] == "parede":
            cena.adicionar_parede(op["a"], self._fim_parede(op["a"], pos, mods))
        elif op["tipo"] == "sala":
            cena.criar_sala(op["a"], self._ponto(pos, mods))
        self.viewport().update()

    # ------------------------------------------------------------ régua e distâncias
    def _rotulo_distancia(self, painter, a, b, texto=None, cor=QColor(COR_DESTAQUE)):
        dist = QLineF(a, b).length() / CELULA
        if texto is None:
            texto = f"{fmt_m(dist)} m"
        caneta = QPen(cor, 2, Qt.PenStyle.DashLine)
        caneta.setCosmetic(True)
        painter.setPen(caneta)
        painter.drawLine(a, b)
        r = 4 / max(0.01, self.escala)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(cor)
        painter.drawEllipse(a, r, r)
        painter.drawEllipse(b, r, r)
        # placa com o texto, sempre do mesmo tamanho na tela
        painter.save()
        painter.resetTransform()
        p = self.mapFromScene(b)
        from PyQt6.QtGui import QFont
        fonte = QFont()
        fonte.setPixelSize(13)
        fonte.setBold(True)
        painter.setFont(fonte)
        larg = painter.fontMetrics().horizontalAdvance(texto) + 14
        placa = QRectF(p.x() + 12, p.y() - 26, larg, 22)
        painter.setBrush(QColor(18, 14, 11, 225))
        painter.setPen(QPen(cor, 1))
        painter.drawRoundedRect(placa, 5, 5)
        painter.setPen(QColor(240, 230, 210))
        painter.drawText(placa, Qt.AlignmentFlag.AlignCenter, texto)
        painter.restore()

    def _desenhar_medidas(self, painter):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cena = self.scene()
        # quanto o token da vez já andou neste turno
        from .token import TokenItem
        for item in cena.items() if cena is not None else []:
            if isinstance(item, TokenItem) and item.da_vez and item.isVisible():
                origem = getattr(item, "origem_turno", None)
                if origem is not None:
                    fim = item.centro_cena()
                    dist = QLineF(origem, fim).length() / CELULA
                    limite = getattr(item, "limite_turno", None)
                    if limite is not None:
                        # área que ele ainda alcança neste turno
                        raio = limite * CELULA
                        cor = QColor(255, 200, 60, 28)
                        borda = QPen(QColor(255, 200, 60, 150), 1.5, Qt.PenStyle.DashLine)
                        borda.setCosmetic(True)
                        painter.setPen(borda)
                        painter.setBrush(cor)
                        painter.drawEllipse(origem, raio, raio)
                    if dist >= 0.05:
                        texto = (f"andou {fmt_m(dist)} de {fmt_m(limite)} m" if limite is not None
                                 else f"andou {fmt_m(dist)} m")
                        self._rotulo_distancia(painter, origem, fim, texto, QColor(255, 200, 60))
        # arrastando um token: distância desde onde ele estava
        if self._arrasto_token is not None:
            token, inicio = self._arrasto_token
            fim = token.centro_cena()
            if QLineF(inicio, fim).length() > 2:
                self._rotulo_distancia(painter, inicio, fim)
        # régua (M + arrastar)
        if self._regua is not None:
            a, b = self._regua
            self._rotulo_distancia(painter, a, b, cor=QColor(120, 200, 255))

    # ------------------------------------------------------------ templates / lápis
    def _origem_efeito(self, pos: QPointF) -> QPointF:
        if getattr(self.scene(), "snap_ativo", False):
            meio = CELULA / 2
            return QPointF(round(pos.x() / meio) * meio, round(pos.y() / meio) * meio)
        return pos

    def _dados_efeito(self) -> dict:
        """O template que seria colocado agora (origem, direção e tamanho)."""
        import math
        base = dict(getattr(self.scene(), "efeito_atual", {}) or {})
        base.setdefault("efeito", "fogo")
        base.setdefault("forma", "circulo")
        if self._op_efeito is not None:
            a, b = self._op_efeito["a"], self._op_efeito["b"]
        else:
            a = b = self._origem_efeito(self._hover or QPointF())
        linha = QLineF(a, b)
        tamanho = float(base.get("tamanho") or 3)
        angulo = 0.0
        if linha.length() > CELULA * 0.3:
            angulo = (360 - linha.angle()) % 360
            if not (self._mods & Qt.KeyboardModifier.ShiftModifier):
                angulo = round(angulo / 15) * 15
            metros = linha.length() / CELULA
            if base["forma"] == "quadrado":
                metros *= 2
            if not (self._mods & Qt.KeyboardModifier.AltModifier):   # Alt = mantém o tamanho do painel
                tamanho = max(1.5, round(metros / 1.5) * 1.5)
        if base["forma"] in ("circulo", "quadrado"):
            angulo = 0.0 if base["forma"] == "circulo" else angulo
        base.update({"x": a.x(), "y": a.y(), "tamanho": tamanho, "angulo": angulo})
        return base

    def _desenhar_previa_efeito(self, painter):
        from .efeitos import EFEITOS, agora, caminho_local, desenhar_efeito
        d = self._dados_efeito()
        painter.save()
        painter.translate(QPointF(d["x"], d["y"]))
        painter.rotate(d["angulo"])
        caminho = caminho_local(d["forma"], d["tamanho"], d.get("largura", 1.5))
        desenhar_efeito(painter, caminho, d["efeito"], agora(), 7, self._cache_previa, 0.6, d.get("cor", ""))
        caneta = QPen(QColor(EFEITOS.get(d["efeito"], EFEITOS["magia"])[1]), 2, Qt.PenStyle.DashLine)
        caneta.setCosmetic(True)
        painter.setPen(caneta)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(caminho)
        painter.restore()
        medida = {"circulo": "raio", "quadrado": "lado", "cone": "cone", "linha": "linha"}[d["forma"]]
        self._rotulo(painter, QPointF(d["x"], d["y"]), f"{medida} {fmt_m(d['tamanho'])} m")
        if self._op_efeito is None:   # só passando o mouse: atualiza a animação
            QTimer.singleShot(80, self.viewport().update)

    def _desenhar_previa_lance(self, painter):
        """Arrastando: a trajetória (projétil), o cone ou a faixa (jato), e a distância."""
        import math
        op = getattr(self, "_op_lance", None)
        if op is None:
            return
        a, b = op["a"], op["b"]
        linha = QLineF(a, b)
        if linha.length() < 2:
            return
        from .lancamentos import ELEMENTOS
        d = dict(getattr(self.scene(), "lance_atual", {}) or {})
        cor = QColor(d.get("cor") or ELEMENTOS.get(d.get("elemento", "fogo"), ELEMENTOS["fogo"])[1])
        caneta = QPen(cor, 2, Qt.PenStyle.DashLine)
        caneta.setCosmetic(True)
        painter.save()
        painter.setPen(caneta)
        fundo = QColor(cor)
        fundo.setAlpha(40)
        painter.setBrush(fundo)
        tipo = d.get("tipo", "projetil")
        ang = math.atan2(b.y() - a.y(), b.x() - a.x())
        L = linha.length()
        if tipo == "cone":
            meio = math.radians(float(d.get("abertura", 53))) / 2
            pts = [a] + [QPointF(a.x() + math.cos(ang + k * meio / 6) * L, a.y() + math.sin(ang + k * meio / 6) * L)
                         for k in range(-6, 7)]
            painter.drawPolygon(QPolygonF(pts))
        elif tipo == "linha":
            w = float(d.get("largura", 1.5)) * CELULA / 2
            nx, ny = -math.sin(ang) * w, math.cos(ang) * w
            painter.drawPolygon(QPolygonF([QPointF(a.x() + nx, a.y() + ny), QPointF(b.x() + nx, b.y() + ny),
                                           QPointF(b.x() - nx, b.y() - ny), QPointF(a.x() - nx, a.y() - ny)]))
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawLine(linha)
            painter.setBrush(fundo)
            r = float(d.get("tam", 3)) * CELULA if d.get("deixar") else CELULA * 0.6
            painter.drawEllipse(b, r, r)
        painter.restore()
        self._rotulo(painter, b, f"{fmt_m(L / CELULA)} m")

    def _sair_da_ferramenta(self):
        self._op_lance = None
        self._op_efeito = None
        cena = self.scene()
        if getattr(cena, "desenhos_item", None) is not None:
            cena.desenhos_item.atual = None
            cena.desenhos_item.update()
        self.ferramenta_saiu.emit()

    def drawBackground(self, painter: QPainter, rect):
        """(v0.75) Com o horizonte na tela (pelos olhos), o fundo vira CÉU em cima dele."""
        hz = getattr(self, "_horizonte", -1e9)
        if hz < -5:
            return super().drawBackground(painter, rect)
        from PyQt6.QtGui import QLinearGradient
        painter.save()
        painter.resetTransform()
        vp = QRectF(self.viewport().rect())
        painter.fillRect(vp, self.backgroundBrush())
        amb = getattr(self.scene(), "luz_ambiente", "dia")
        topo, meio = {"dia": (QColor("#3a5878"), QColor("#9fb4c8")), "penumbra": (QColor("#0e1424"), QColor("#3a3a52")),
                      "escuro": (QColor("#040406"), QColor("#121218"))}.get(amb, (QColor("#3a5878"), QColor("#9fb4c8")))
        g = QLinearGradient(0, 0, 0, hz)
        g.setColorAt(0, topo)
        g.setColorAt(1, meio)
        painter.fillRect(QRectF(0, 0, vp.width(), hz + 2), QBrush(g))
        painter.restore()

    def _nevoa_horizonte(self, painter: QPainter):
        """(v0.75) Névoa ao longe: o chão some suave perto do horizonte (e esconde o fim do mundo)."""
        hz = getattr(self, "_horizonte", -1e9)
        vp = QRectF(self.viewport().rect())
        if hz < -0.3 * vp.height():
            return
        from PyQt6.QtGui import QLinearGradient
        amb = getattr(self.scene(), "luz_ambiente", "dia")
        cor = {"dia": QColor("#9fb4c8"), "penumbra": QColor("#3a3a52"), "escuro": QColor("#121218")}.get(amb, QColor("#9fb4c8"))
        painter.save()
        painter.resetTransform()
        faixa = 0.15 * vp.height()   # (fina: só esconde o fim do chão; coisa alta perto não fica "lavada")
        g = QLinearGradient(0, hz, 0, hz + faixa)
        c0 = QColor(cor)
        c1 = QColor(cor)
        c1.setAlpha(0)
        g.setColorAt(0, c0)
        g.setColorAt(0.12, c0)
        g.setColorAt(1, c1)
        painter.fillRect(QRectF(0, min(hz, vp.height()) - 2, vp.width(), faixa + 2), QBrush(g))
        painter.restore()

    def drawForeground(self, painter: QPainter, rect):
        try:
            self._nevoa_horizonte(painter)
        except Exception as erro:   # (erro aqui fecha o programa)
            from ..seguranca import registrar_erro
            registrar_erro(f"Névoa do horizonte: {erro!r}")
        self._desenhar_frente(painter, rect)

    def _desenhar_frente(self, painter: QPainter, rect):
        self._desenhar_medidas(painter)
        ferramenta = self._ferramenta()
        if ferramenta == "efeito" and self._hover is not None:
            self._desenhar_previa_efeito(painter)
            return
        if ferramenta == "lancar":
            self._desenhar_previa_lance(painter)
            return
        if ferramenta in ("lapis", "impacto") + FERRAMENTAS_CLIQUE:
            return
        if ferramenta == "selecionar" or self._hover is None:
            return
        cena = self.scene()
        cor = QColor("#e05a5a") if ferramenta in ("borracha", "borracha_parede") \
            else QColor(COR_DESTAQUE)
        tracejado = QPen(cor, 2, Qt.PenStyle.DashLine)
        tracejado.setCosmetic(True)
        translucido = QColor(cor)
        translucido.setAlpha(110)
        pos = self._hover
        mods = self._mods
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        raio_ponto = 5 / max(0.01, self.escala)

        if ferramenta in ("terreno", "borracha"):
            painter.setPen(tracejado)
            painter.setBrush(QColor(cor.red(), cor.green(), cor.blue(), 35))
            if getattr(cena, "forma_pincel", "livre") == "grid":
                celulas = cena.celulas_do_pincel(pos)
                i0 = min(c[0] for c in celulas)
                j0 = min(c[1] for c in celulas)
                n = max(1, round(cena.pincel))
                painter.drawRect(QRectF(i0 * CELULA, j0 * CELULA, n * CELULA, n * CELULA))
            else:
                r = cena.raio_pincel()
                painter.drawEllipse(pos, r, r)

        elif ferramenta == "borracha_parede":
            r = cena.raio_pincel()
            painter.setPen(tracejado)
            painter.setBrush(QColor(cor.red(), cor.green(), cor.blue(), 35))
            painter.drawEllipse(pos, r, r)
            painter.drawLine(pos - QPointF(r * 0.5, 0), pos + QPointF(r * 0.5, 0))

        elif ferramenta in ("parede", "sala"):
            if self._op:
                a = self._op["a"]
                if ferramenta == "parede":
                    b = self._fim_parede(a, pos, mods)
                    painter.setPen(QPen(translucido, ESPESSURA, Qt.PenStyle.SolidLine,
                                        Qt.PenCapStyle.SquareCap))
                    painter.drawLine(a, b)
                    linha = QLineF(a, b)
                    angulo = (360 - linha.angle()) % 360
                    self._rotulo(painter, b, f"{fmt_m(linha.length() / CELULA)} m · "
                                             f"{angulo:.0f}°")
                else:
                    b = self._ponto(pos, mods)
                    r = QRectF(a, b).normalized()
                    painter.setPen(QPen(translucido, ESPESSURA))
                    painter.setBrush(QColor(cor.red(), cor.green(), cor.blue(), 30))
                    painter.drawRect(r)
                    self._rotulo(painter, b, f"{fmt_m(r.width() / CELULA)} × "
                                             f"{fmt_m(r.height() / CELULA)} m")
            alvo = self._ponto(pos, mods) if not self._op or ferramenta == "sala" else \
                self._fim_parede(self._op["a"], pos, mods)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(cor)
            painter.drawEllipse(alvo, raio_ponto, raio_ponto)

        elif ferramenta == "luz":
            from .luzes import TIPOS_LUZ
            _, forte, fraco, cor_luz, _ = TIPOS_LUZ[getattr(cena, "tipo_luz", "tocha")]
            c = QColor(cor_luz)
            caneta = QPen(c, 1.5, Qt.PenStyle.DashLine)
            caneta.setCosmetic(True)
            painter.setPen(caneta)
            painter.setBrush(QColor(c.red(), c.green(), c.blue(), 25))
            painter.drawEllipse(pos, fraco * CELULA, fraco * CELULA)
            painter.setBrush(c)
            painter.drawEllipse(pos, raio_ponto * 1.5, raio_ponto * 1.5)

        elif ferramenta == "porta":
            largura = getattr(cena, "largura_porta", 1.0)
            centro, angulo, _, _, _ = cena.encaixe_porta(pos, largura)
            L = largura * CELULA
            painter.save()
            painter.translate(centro)
            painter.rotate(angulo)
            painter.setPen(tracejado)
            painter.setBrush(QColor(cor.red(), cor.green(), cor.blue(), 60))
            painter.drawRect(QRectF(-L / 2, -ESPESSURA, L, 2 * ESPESSURA))
            painter.restore()

    def _rotulo(self, painter, ponto, texto):
        painter.save()
        painter.translate(ponto)
        painter.scale(1 / self.escala, 1 / self.escala)
        fonte = painter.font()
        fonte.setPixelSize(13)
        fonte.setBold(True)
        painter.setFont(fonte)
        larg = painter.fontMetrics().horizontalAdvance(texto) + 14
        placa = QRectF(12, 10, larg, 22)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(20, 16, 12, 220))
        painter.drawRoundedRect(placa, 4, 4)
        painter.setPen(QColor(COR_DESTAQUE))
        painter.drawText(placa, Qt.AlignmentFlag.AlignCenter, texto)
        painter.restore()

    # ------------------------------------------------------------ pan
    def _inicia_pan(self, pos):
        if self.camera_travada():   # (v0.58) o mestre travou a câmera por uns segundos
            return
        self.sair_dos_olhos()   # (v0.75)
        self._arrastando_visao = True
        self._ultimo_pos = pos
        self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)

    def mousePressEvent(self, event):
        if (self.camera_livre and event.modifiers() & Qt.KeyboardModifier.AltModifier
                and event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton)
                and not self.camera_travada()):
            self.sair_dos_olhos()
            self._orbitando = event.position()   # (v0.70) Alt+arrastar = girar/inclinar
            self.viewport().setCursor(Qt.CursorShape.SizeAllCursor)
            event.accept()
            return
        if self._medindo and event.button() == Qt.MouseButton.LeftButton:
            p = self.mapToScene(event.position().toPoint())
            self._regua = [p, p]
            self.viewport().update()
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton and self._ferramenta() == "selecionar":
            from .token import TokenItem
            item = self.itemAt(event.position().toPoint())
            while item is not None and not isinstance(item, TokenItem):
                item = item.parentItem()
            if item is not None and not item.travado:
                self._arrasto_token = (item, item.centro_cena())
        if event.button() == Qt.MouseButton.MiddleButton or (
                self._espaco and event.button() == Qt.MouseButton.LeftButton):
            self._inicia_pan(event.position())
            event.accept()
            return
        if self._ferramenta() == "impacto":
            if event.button() == Qt.MouseButton.LeftButton:
                self.impacto_pedido.emit(self.mapToScene(event.position().toPoint()))
            event.accept()
            return
        if self._ferramenta() in FERRAMENTAS_CLIQUE:
            if event.button() == Qt.MouseButton.LeftButton:
                self.clique_ferramenta.emit(self._ferramenta(), self.mapToScene(event.position().toPoint()))
            event.accept()
            return
        if self._ferramenta() == "lancar":
            if event.button() == Qt.MouseButton.LeftButton:
                a = self.mapToScene(event.position().toPoint())
                item = self.itemAt(event.position().toPoint())
                while item is not None and not hasattr(item, "centro_cena"):
                    item = item.parentItem()
                if item is not None and hasattr(item, "tem_visao"):   # começou num token: sai do centro dele
                    a = item.centro_cena()
                self._op_lance = {"a": a, "b": a}
            event.accept()
            return
        if self._ferramenta() == "efeito":
            if event.button() == Qt.MouseButton.LeftButton:
                a = self._origem_efeito(self.mapToScene(event.position().toPoint()))
                self._op_efeito = {"a": a, "b": a}
                self._mods = event.modifiers()
            event.accept()
            return
        if self._ferramenta() == "lapis":
            cena = self.scene()
            if event.button() == Qt.MouseButton.LeftButton and getattr(cena, "desenhos_item", None):
                from .desenhos import traco_novo
                p = self.mapToScene(event.position().toPoint())
                lapis = getattr(cena, "lapis", {}) or {}
                cena.desenhos_item.atual = traco_novo([(p.x(), p.y())], lapis.get("cor", "#ffd166"),
                                                      lapis.get("esp", 3), "", lapis.get("temp", True))
                cena.desenhos_item.update()
            event.accept()
            return
        if self._ferramenta() != "selecionar":
            if event.button() == Qt.MouseButton.LeftButton:
                self._press_construcao(event)
            event.accept()  # o direito vira menu (contextMenuEvent)
            return
        if event.button() == Qt.MouseButton.LeftButton:
            cena = self.scene()
            self._somar_selecao = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
            if hasattr(cena, "limpar_selecao_construcao") and not self._somar_selecao:
                item = self.itemAt(event.position().toPoint())
                while item is not None and not hasattr(item, "para_dict"):
                    item = item.parentItem()
                if item is None:
                    cena.limpar_selecao_construcao()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._orbitando is not None:
            self._orbitar(event.position() - self._orbitando)
            self._orbitando = event.position()
            event.accept()
            return
        pos_cena = self.mapToScene(event.position().toPoint())
        self.cursor_moveu.emit(pos_cena)
        self._ultima_pos_cena = pos_cena
        if self._regua is not None:
            self._regua[1] = pos_cena
            self.viewport().update()
            event.accept()
            return
        if self._arrasto_token is not None:
            self.viewport().update()
        if self._ferramenta() == "lancar":
            self._hover = pos_cena
            if getattr(self, "_op_lance", None) is not None:
                self._op_lance["b"] = pos_cena
            self.viewport().update()
            if not self._arrastando_visao:
                return
        if self._ferramenta() == "efeito":
            self._hover = pos_cena
            self._mods = event.modifiers()
            if self._op_efeito is not None:
                self._op_efeito["b"] = pos_cena
            self.viewport().update()
            if not self._arrastando_visao:
                return
        if self._ferramenta() == "lapis":
            cena = self.scene()
            atual = getattr(getattr(cena, "desenhos_item", None), "atual", None)
            if atual is not None and not self._arrastando_visao:
                ultimo = atual["pts"][-1]
                if QLineF(QPointF(*ultimo), pos_cena).length() * self.escala >= 3:
                    atual["pts"].append([round(pos_cena.x(), 1), round(pos_cena.y(), 1)])
                    cena.desenhos_item.update()
                return
        if self._ferramenta() != "selecionar" and self._ferramenta() not in ("efeito", "lapis", "impacto", "lancar") + FERRAMENTAS_CLIQUE:
            self._hover = pos_cena
            self._mods = event.modifiers()
            if self._op and self._op["tipo"] == "pincel":
                self.scene().continuar_pincelada(pos_cena)
            elif self._op and self._op["tipo"] == "borracha_parede":
                # passa a borracha em todo o caminho, mesmo se o mouse correr
                a = self._op["ultimo"]
                passos = max(1, int(QLineF(a, pos_cena).length() / 8))
                for k in range(1, passos + 1):
                    self.scene().apagar_paredes_em(a + (pos_cena - a) * (k / passos))
                self._op["ultimo"] = pos_cena
            self.viewport().update()
        if self._arrastando_visao:
            delta = event.position() - self._ultimo_pos
            self._ultimo_pos = event.position()
            # (v0.70) o ponto da mesa que estava embaixo do mouse continua embaixo dele (girada/inclinada também)
            antes = self.mapToScene((event.position() - delta).toPoint())
            agora = self.mapToScene(event.position().toPoint())
            self._cam_centro = self._cam_centro + (antes - agora)
            self._aplicar_camera()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._orbitando is not None:
            self._orbitando = None
            self.viewport().setCursor(self.cursor_padrao)
            event.accept()
            return
        if self._regua is not None and event.button() == Qt.MouseButton.LeftButton:
            self._regua = None
            self.viewport().update()
            event.accept()
            return
        if self._arrasto_token is not None and event.button() == Qt.MouseButton.LeftButton:
            self._arrasto_token = None
            self.viewport().update()
        if self._arrastando_visao and event.button() in (
                Qt.MouseButton.MiddleButton, Qt.MouseButton.LeftButton):
            self._arrastando_visao = False
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor if self._espaco
                                      else self.cursor_padrao)
            event.accept()
            return
        if getattr(self, "_op_lance", None) is not None and event.button() == Qt.MouseButton.LeftButton:
            a, b = self._op_lance["a"], self.mapToScene(event.position().toPoint())
            self._op_lance = None
            self.viewport().update()
            if QLineF(a, b).length() >= CELULA * 0.5:
                dados = dict(getattr(self.scene(), "lance_atual", {}) or {})
                dados.update({"x0": a.x(), "y0": a.y(), "x1": b.x(), "y1": b.y()})
                self.lancar_pedido.emit(dados)
            event.accept()
            return
        if self._op_efeito is not None and event.button() == Qt.MouseButton.LeftButton:
            self._op_efeito["b"] = self.mapToScene(event.position().toPoint())
            self._mods = event.modifiers()
            dados = self._dados_efeito()
            self._op_efeito = None
            self.viewport().update()
            self.efeito_pedido.emit(dados)
            event.accept()
            return
        if self._ferramenta() == "lapis" and event.button() == Qt.MouseButton.LeftButton:
            cena = self.scene()
            item = getattr(cena, "desenhos_item", None)
            if item is not None and item.atual is not None:
                traco = item.atual
                item.atual = None
                if hasattr(cena, "adicionar_traco"):
                    item.update()
                else:   # player: mostra já, até o mestre devolver
                    import time
                    traco["_desde"] = time.monotonic()
                    item.pendentes[traco["id"]] = traco
                    item.update()
                self.traco_pedido.emit({k: v for k, v in traco.items() if not k.startswith("_")})
            event.accept()
            return
        if self._op is not None:
            self._release_construcao(event)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        sem_mods = not (event.modifiers() & (Qt.KeyboardModifier.ControlModifier
                                             | Qt.KeyboardModifier.AltModifier))
        if event.key() == Qt.Key.Key_M and sem_mods and not event.isAutoRepeat():
            self._medindo = True
            self.viewport().setCursor(Qt.CursorShape.CrossCursor)
            event.accept()
            return
        if event.key() == Qt.Key.Key_P and sem_mods and not event.isAutoRepeat():
            pos = self.mapToScene(self.mapFromGlobal(self.cursor().pos()))
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:   # (v0.58) Shift+P = 📣 todos olhem pra cá
                self.olhar_pedido.emit(pos)
            else:
                self.ping_pedido.emit(pos)
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape and self._olhos is not None:   # (v0.75) sai do "pelos olhos"
            self.sair_dos_olhos()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape and self._ferramenta() in ("efeito", "lapis", "impacto", "lancar") + FERRAMENTAS_CLIQUE:
            self._sair_da_ferramenta()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._espaco = True
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_M and not event.isAutoRepeat():
            self._medindo = False
            self._regua = None
            self.viewport().setCursor(self.cursor_padrao)
            self.viewport().update()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._espaco = False
            self.viewport().setCursor(self.cursor_padrao)
            event.accept()
            return
        super().keyReleaseEvent(event)

    def leaveEvent(self, event):
        self.cursor_saiu.emit()
        self._hover = None
        self.viewport().update()
        super().leaveEvent(event)

    # ------------------------------------------------------------ menu
    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        while item is not None and not hasattr(item, "para_dict"):
            item = item.parentItem()
        self.menu_pedido.emit(item, event.globalPos(), self.mapToScene(event.pos()))

    # ------------------------------------------------------------ arrastar arquivos
    def _caminhos_imagem(self, event):
        if not event.mimeData().hasUrls():
            return []
        return [u.toLocalFile() for u in event.mimeData().urls()
                if u.toLocalFile().lower().endswith(EXTENSOES_IMAGEM)]

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-taverna-prop") \
                or event.mimeData().hasFormat("application/x-taverna-banco"):
            event.acceptProposedAction()
            return
        if self._caminhos_imagem(event):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-taverna-prop") \
                or event.mimeData().hasFormat("application/x-taverna-banco"):
            event.acceptProposedAction()
            return
        if self._caminhos_imagem(event):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-taverna-banco"):
            uso, _, caminho = bytes(event.mimeData().data("application/x-taverna-banco")).decode("utf-8").partition("|")
            self.banco_solto.emit(uso, caminho, self.mapToScene(event.position().toPoint()))
            event.acceptProposedAction()
            return
        if event.mimeData().hasFormat("application/x-taverna-prop"):
            tipo = bytes(event.mimeData().data("application/x-taverna-prop")).decode()
            self.prop_solto.emit(tipo, self.mapToScene(event.position().toPoint()))
            event.acceptProposedAction()
            return
        caminhos = self._caminhos_imagem(event)
        if not caminhos:
            super().dropEvent(event)
            return
        pos = self.mapToScene(event.position().toPoint())
        for caminho in caminhos:
            self.imagem_solta.emit(caminho, pos)
        event.acceptProposedAction()
