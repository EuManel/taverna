"""
🌍 A camada da CIDADE e do MUNDO por cima da mesa (v0.62 — item 9, etapa 1: navegação do mestre).

Três "quadros" de câmera:
  - mesa:   quem manda é a MesaVisao de sempre. Esta camada fica transparente pro mouse e só desenha a cidade
            por cima com opacidade t (0 → 1) enquanto o cenário encolhe de "cabe na tela" até "1/3 da tela";
  - cidade: a câmera é uma transformação M (pixels da imagem da cidade → tela). Esta camada pega o mouse;
  - mundo:  M em pixels do mapa-múndi.
Trocar de quadro é só trocar o referencial (as transformações de encaixe estão em mesa/atlas.py), então a imagem
na tela não pula. Histerese: sobe em 1/3, volta em 1/3 × FOLGA.
"""

import math

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, QVariantAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QTransform
from PyQt6.QtWidgets import QHBoxLayout, QToolButton, QWidget

from ..config import COR_DESTAQUE, COR_FUNDO_MESA, ZOOM_MIN, ZOOM_PASSO
from ..mesa import atlas as A

ESCALA_MAX = 10.0   # zoom máximo dentro da cidade/mundo (pixels da tela por pixel da imagem)



def _esc(t):
    """(v0.70) Zoom da transformação (a mesa pode estar girada: m11 sozinho não é o zoom)."""
    import math
    return math.hypot(t.m11(), t.m12()) or 1e-9

class BotoesNivel(QWidget):
    """Mesa · Cidade · Mundo, no canto de cima da mesa."""

    def __init__(self, camada, pai):
        super().__init__(pai)
        self.camada = camada
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        self.botoes = {}
        for chave, texto in (("mesa", "Mesa"), ("cidade", "Cidade"), ("mundo", "Mundo")):
            b = QToolButton(self)
            b.setText(texto)
            b.setCheckable(True)
            b.setAutoRaise(False)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _c=False, k=chave: self.camada.ir_para(k))
            lay.addWidget(b)
            self.botoes[chave] = b
        self.setStyleSheet("QToolButton { padding: 3px 10px; }")

    def atualizar(self, atual: str, tem_cidade: bool, tem_mundo: bool):
        self.botoes["cidade"].setEnabled(tem_cidade)
        self.botoes["mundo"].setEnabled(tem_mundo)
        for k, b in self.botoes.items():
            b.setChecked(k == atual)
        self.setVisible(tem_cidade or tem_mundo)
        self.adjustSize()


class CamadaAtlas(QWidget):
    def __init__(self, visao, janela, mestre: bool = True):
        super().__init__(visao)
        self.visao = visao
        self.janela = janela            # precisa de: .atlas, .cena, .cenas, .trocar_aba(i)
        self.mestre = mestre
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setMouseTracking(True)
        self.quadro = "mesa"            # mesa | cidade | mundo
        self.cidade: dict | None = None
        self.M = QTransform()           # imagem do quadro → tela (cidade/mundo)
        self.t = 0.0                    # mistura mesa → cidade (no quadro mesa)
        self._alvo = 1.0                # zoom suave (escala alvo de M)
        self._ancora = QPointF()
        self._arrasto = None
        self._viajando = None           # {"m", "ini", "nivel"} enquanto o mestre arrasta um marcador
        self._medindo = False           # segurando M: régua
        self._regua = None              # [início, fim] no mapa
        self._pincel = None             # (etapa 3) "revelar" | "esconder" | None
        self._pincel_raio = 36          # raio do pincel na TELA (px)
        self._pincelando = False
        self._mouse = None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._passo_zoom)
        self._anim = None
        self.botoes = BotoesNivel(self, visao)
        visao.zoom_mudou.connect(self._mesa_zoom)
        visao.installEventFilter(self)
        self._encaixar()
        self.hide()
        self.atlas_mudou()

    # ================================================================ o básico
    @property
    def atlas(self):
        return self.janela.atlas

    def _encaixar(self):
        self.setGeometry(self.visao.viewport().geometry())
        self.botoes.adjustSize()
        self.botoes.move(self.visao.viewport().geometry().right() - self.botoes.width() - 10,
                         self.visao.viewport().geometry().top() + 10)
        self.botoes.raise_()

    def eventFilter(self, obj, ev):
        if obj is self.visao and ev.type() == ev.Type.Resize:
            QTimer.singleShot(0, self._encaixar)
        return False

    def _chao(self, cena=None) -> QRectF | None:
        if not self.mestre:   # (jogador) o mestre manda o chão da aba dele: o encaixe fica igual nos dois
            return getattr(self.atlas, "chao", None)
        cena = cena or self.janela.cena
        try:
            cam = cena.chao_caminho()
        except (AttributeError, RuntimeError):
            return None
        if cam is None or cam.isEmpty():
            return None
        return cam.boundingRect()

    def _cidade_para_mesa(self, cena=None):
        """(cidade, T: pixels da cidade → mesa) da aba atual, ou (None, None)."""
        cena = cena or self.janela.cena
        return self.atlas.cidade_para_mesa(cena, self._chao(cena))

    def _mundo_para_cidade(self, cidade):
        return self.atlas.mundo_para_cidade(cidade) if cidade else None

    def atlas_mudou(self):
        """O mestre mexeu na montagem (ou abriu outra aventura): volta pra mesa se o quadro sumiu."""
        if self.quadro == "cidade" and (self.cidade is None or self.atlas.nivel(self.cidade["id"]) is None):
            self._voltar_pra_mesa_sem_animar()
        elif self.quadro == "mundo" and self.atlas.mundo is None:
            self._voltar_pra_mesa_sem_animar()
        self._mesa_zoom(self.visao.escala)
        self._atualizar_botoes()

    def aba_mudou(self):
        if self.quadro == "mesa":
            self._mesa_zoom(self.visao.escala)
        self._atualizar_botoes()

    def _atualizar_botoes(self):
        cidade, _T = self._cidade_para_mesa()
        if self.quadro != "mesa" and self.cidade is not None:
            cidade = cidade or self.cidade
        tem_mundo = self.atlas.mundo is not None and (cidade is None or self.atlas.lugar_da_cidade(cidade) is not None
                                                     or self.quadro == "mundo")
        self.botoes.atualizar(self.quadro, cidade is not None, tem_mundo and not self.atlas.vazio())
        self._encaixar()

    # ================================================================ quadro mesa (quem manda é a MesaVisao)
    def _mesa_zoom(self, escala):
        if self.quadro != "mesa":
            return
        cidade, T = self._cidade_para_mesa()
        chao = self._chao()
        if cidade is None or chao is None:
            self.t = 0.0
            self.visao.zoom_min = ZOOM_MIN
            self.hide()
            self._atualizar_botoes()
            return
        w, h = self.width(), self.height()
        s_cabe = min(w / max(1.0, chao.width()), h / max(1.0, chao.height()))
        self.visao.zoom_min = min(ZOOM_MIN, s_cabe * A.TROCA * 0.995)
        V = self.visao.viewportTransform()
        fr = A.tamanho_na_tela(chao, V, w, h)
        self.t = A.mistura(fr)
        self.cidade = cidade
        self.setVisible(self.t > 0)
        self.update()
        if fr <= A.TROCA * 1.002:      # afastou até o cenário ocupar 1/3: agora estamos na cidade
            self._entrar("cidade", cidade, T * V)

    def _entrar(self, quadro, cidade, M):
        """Passa a câmera pra esta camada (cidade/mundo). O zoom que faltava continua aqui."""
        resto = 1.0
        if self.visao._zoom_timer.isActive():
            resto = self.visao._zoom_alvo / max(1e-9, self.visao.escala)
            self.visao._zoom_timer.stop()
            self._ancora = QPointF(self.visao._zoom_ancora)
        self.quadro, self.cidade, self.M = quadro, cidade, QTransform(M)
        self.t = 1.0
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.show()
        self.raise_()
        self.botoes.raise_()
        self.setFocus()
        if resto < 0.999:
            self._alvo = _esc(self.M) * resto
            self._timer.start()
        self._atualizar_botoes()
        self.update()

    def _descer_pra_mesa(self, lugar, M_cidade):
        """Zoom in num lugar da cidade até ele ocupar 1/3 da tela: vai pra aba dele (o zoom continua lá)."""
        cena = self._cena_do_alvo(lugar["alvo"])
        if cena is None:
            return False
        resto = self._alvo / max(1e-9, _esc(self.M)) if self._timer.isActive() else 1.0
        self._timer.stop()
        if cena is not self.janela.cena:
            self.janela.trocar_aba(self.janela.cenas.index(cena), manter_camera=True)
        chao = self._chao(cena)
        self.quadro = "mesa"
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        if chao is None:
            self.visao.enquadrar_tudo()
        else:
            T = A.encaixe(A.ret(lugar), chao)
            V = T.inverted()[0] * M_cidade
            self._aplicar_na_mesa(V)
            if resto > 1.001:
                self.visao._zoom_alvo = self.visao.escala * resto
                self.visao._zoom_ancora = QPointF(self._ancora)
                self.visao._zoom_timer.start()
        self.visao.zoom_mudou.emit(self.visao.escala)   # (o rótulo de zoom e esta camada se acertam)
        self._atualizar_botoes()
        return True

    def _aplicar_na_mesa(self, V: QTransform):
        """Põe a câmera da mesa exatamente em V (cena → tela)."""
        s = max(1e-6, _esc(V))
        w, h = self.width(), self.height()
        meio = V.inverted()[0].map(QPointF(w / 2, h / 2))
        self.visao.zoom_min = min(self.visao.zoom_min, s)
        self.visao.setTransform(QTransform.fromScale(s, s))
        self.visao.centerOn(meio)
        self.visao.scene().definir_escala(s)
        self.visao._zoom_alvo = s

    def _cena_do_alvo(self, alvo: str):
        if alvo == "__minha__":   # (jogador) o único lugar que ele conhece: a aba onde está o token dele
            return self.janela.cena
        cenas = list(self.janela.cenas)
        if alvo.startswith("predio:"):
            predio = alvo[len("predio:"):]
            do_predio = [c for c in cenas if getattr(c, "predio", None) == predio]
            if not do_predio:
                return None
            atual = self.janela.cena
            if atual in do_predio:
                return atual
            return min(do_predio, key=lambda c: abs(getattr(c, "andar", 0)))   # o térreo
        return next((c for c in cenas if str(getattr(c, "uid", "")) == alvo), None)

    def _voltar_pra_mesa_sem_animar(self):
        self._timer.stop()
        self.quadro = "mesa"
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hide()

    # ================================================================ zoom dentro da cidade/mundo
    def _area(self, nivel):
        return self.atlas.area(nivel)

    def _limites(self) -> tuple[float, float]:
        """(escala mínima, máxima) de M no quadro atual."""
        w, h = self.width(), self.height()
        if self.quadro == "mundo":
            a = self._area(self.atlas.mundo)
            return min(w / max(1.0, a.width()), h / max(1.0, a.height())), ESCALA_MAX
        a = self._area(self.cidade)
        cabe = min(w / max(1.0, a.width()), h / max(1.0, a.height()))
        if self._mundo_para_cidade(self.cidade) is not None:
            return 1e-9, ESCALA_MAX    # dá pra continuar afastando: vira o mundo
        return cabe, ESCALA_MAX

    def wheelEvent(self, ev):
        if self.quadro == "mesa":
            ev.ignore()
            return
        passos = ev.angleDelta().y() / 120.0
        if passos == 0:
            return
        if not self._timer.isActive():
            self._alvo = _esc(self.M)
        self._alvo *= ZOOM_PASSO ** passos
        self._ancora = ev.position()
        self._timer.start()
        ev.accept()

    def _passo_zoom(self):
        atual = _esc(self.M)
        novo = math.exp(math.log(atual) + (math.log(self._alvo) - math.log(atual)) * 0.28)
        if abs(math.log(self._alvo) - math.log(novo)) < 0.002:
            novo = self._alvo
            self._timer.stop()
        self._escalar(novo / atual, self._ancora)

    def _escalar(self, fator: float, ancora: QPointF):
        mn, mx = self._limites()
        s = _esc(self.M)
        fator = max(mn / s, min(mx / s, fator))
        if abs(fator - 1) < 1e-9:
            self._timer.stop()
            return
        S = QTransform().translate(ancora.x(), ancora.y()).scale(fator, fator).translate(-ancora.x(), -ancora.y())
        self.M = self.M * S
        self._checar_troca(fator > 1, ancora)
        self._prender()
        self.update()

    def _prender(self):
        """O mapa mais de fora (o mundo, ou a cidade sem mundo) não foge da tela: se é menor que a tela fica no
        meio; se é maior, não deixa aparecer o vazio dos lados."""
        if self.quadro == "mundo":
            area = self._area(self.atlas.mundo)
        elif self.quadro == "cidade" and self._mundo_para_cidade(self.cidade) is None:
            area = self._area(self.cidade)
        else:
            return
        r = self.M.mapRect(area)
        w, h = self.width(), self.height()
        dx = dy = 0.0
        if r.width() <= w:
            dx = w / 2 - r.center().x()
        elif r.left() > 0:
            dx = -r.left()
        elif r.right() < w:
            dx = w - r.right()
        if r.height() <= h:
            dy = h / 2 - r.center().y()
        elif r.top() > 0:
            dy = -r.top()
        elif r.bottom() < h:
            dy = h - r.bottom()
        if dx or dy:
            self.M = self.M * QTransform().translate(dx, dy)

    def _checar_troca(self, aproximando: bool, ancora: QPointF):
        w, h = self.width(), self.height()
        if self.quadro == "cidade":
            W = self._mundo_para_cidade(self.cidade)
            if not aproximando and W is not None:
                fr = A.tamanho_na_tela(self._area(self.cidade), self.M, w, h)
                if fr <= A.TROCA:                       # a cidade ficou pequena: agora é o mundo
                    self.quadro, self.M = "mundo", W * self.M
                    self._atualizar_botoes()
                    return
            if aproximando:
                lugar = self._lugar_perto(self.cidade, ancora)
                if lugar is not None and A.tamanho_na_tela(A.ret(lugar), self.M, w, h) >= A.TROCA * A.FOLGA:
                    self._descer_pra_mesa(lugar, self.M)
        elif self.quadro == "mundo" and aproximando:
            for lugar in self.atlas.mundo["lugares"]:
                cidade = self.atlas.nivel(lugar["alvo"])
                if cidade is None or not self.M.mapRect(A.ret(lugar)).contains(ancora):
                    continue
                W = self._mundo_para_cidade(cidade)
                Mc = W.inverted()[0] * self.M
                if A.tamanho_na_tela(self._area(cidade), Mc, w, h) >= A.TROCA * A.FOLGA:
                    self.quadro, self.cidade, self.M = "cidade", cidade, Mc
                    self._atualizar_botoes()
                    return

    def _lugar_perto(self, cidade, ancora: QPointF):
        """O lugar (com aba que existe) embaixo do mouse; senão, o mais perto do mouse na tela."""
        melhor, menor = None, None
        for l in cidade["lugares"]:
            if self._cena_do_alvo(l["alvo"]) is None:
                continue
            r = self.M.mapRect(A.ret(l))
            if r.contains(ancora):
                return l
            d = math.hypot(r.center().x() - ancora.x(), r.center().y() - ancora.y())
            if d < max(r.width(), r.height()) and (menor is None or d < menor):
                melhor, menor = l, d
        return melhor

    # ================================================================ marcadores do grupo (etapa 2)
    def _nivel_do_quadro(self):
        return self.atlas.mundo if self.quadro == "mundo" else self.cidade

    def _tokens_jogadores(self):
        """[(cena, token)] dos tokens de jogador visíveis, em todas as abas."""
        from ..mesa.token import TokenItem
        saida = []
        for cena in list(self.janela.cenas):
            try:
                itens = cena.itens_do_usuario()
            except RuntimeError:
                continue
            for t in itens:
                if isinstance(t, TokenItem) and t.tipo == "jogador" and t.isVisible():
                    saida.append((cena, t))
        return saida

    def _pos_na_cidade(self, cena, token, cidade):
        """Onde o token fica na imagem da cidade (o encaixe da aba, ao contrário)."""
        c, lugar = self.atlas.lugar_da_cena(cena)
        if c is None or c["id"] != cidade["id"]:
            return None
        chao = self._chao(cena)
        if chao is None:
            return A.ret(lugar).center()
        return A.encaixe(A.ret(lugar), chao).inverted()[0].map(token.centro_cena())

    def marcadores(self, quadro=None, cidade=None) -> list[dict]:
        """Os marcadores do quadro: UM do grupo (todos na mesma aba/prédio) ou um por jogador (separados), na cor
        do token. Cada um: {"id", "pos" (no mapa), "auto" (onde os tokens estão), "cor", "nome", "base"}."""
        quadro = quadro or self.quadro
        if not self.mestre:   # (jogador) quem calcula é o mestre; aqui só chegam as posições
            return self.atlas.marcadores_de(quadro) if hasattr(self.atlas, "marcadores_de") else []
        cidade = cidade if cidade is not None else self.cidade
        nivel = self.atlas.mundo if quadro == "mundo" else cidade
        if nivel is None or quadro == "mesa":
            return []
        brutos = []
        for cena, tok in self._tokens_jogadores():
            c, _l = self.atlas.lugar_da_cena(cena)
            if c is None:
                continue
            if quadro == "cidade":
                if c["id"] != cidade["id"]:
                    continue
                pos = self._pos_na_cidade(cena, tok, c)
            else:
                W = self._mundo_para_cidade(c)
                if W is None:
                    continue
                pos = W.inverted()[0].map(self._pos_na_cidade(cena, tok, c))
            if pos is not None:
                brutos.append((A.chave_da_cena(cena), tok, pos))
        if not brutos:
            return []
        lugares = {k for k, _t, _p in brutos}
        if len(lugares) == 1:
            base = next(iter(lugares))
            media = QPointF(sum(p.x() for *_r, p in brutos) / len(brutos), sum(p.y() for *_r, p in brutos) / len(brutos))
            lista = [{"id": "grupo", "auto": media, "cor": QColor(COR_DESTAQUE), "nome": "Grupo", "base": base}]
        else:
            lista = [{"id": "jog:" + (tok.dono or tok.nome), "auto": p, "cor": QColor(tok.cor), "nome": tok.nome,
                      "base": k} for k, tok, p in brutos]
        for m in lista:
            m["pos"] = self.atlas.posicao_viagem(nivel["id"], m["id"], m["base"]) or m["auto"]
        return lista

    def _marcador_em(self, p: QPointF):
        for m in self.marcadores():
            s = self.M.map(m["pos"])
            if math.hypot(s.x() - p.x(), s.y() - 16 - p.y()) < 14 or math.hypot(s.x() - p.x(), s.y() - p.y()) < 8:
                return m
        return None

    # ---------------------------------------------------------------- mouse: arrastar o mapa, viajar, régua
    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key.Key_M and not ev.isAutoRepeat():
            self._medindo = True
            self.setCursor(Qt.CursorShape.CrossCursor)
            return
        super().keyPressEvent(ev)

    def keyReleaseEvent(self, ev):
        if ev.key() == Qt.Key.Key_M and not ev.isAutoRepeat():
            self._medindo = False
            self._regua = None
            self.unsetCursor()
            self.update()
            return
        super().keyReleaseEvent(ev)

    def mousePressEvent(self, ev):
        inv = self.M.inverted()[0]
        if ev.button() == Qt.MouseButton.LeftButton and getattr(self, "_medindo", False):
            p = inv.map(ev.position())
            self._regua = [p, p]
            return
        if ev.button() == Qt.MouseButton.LeftButton and self.mestre and self._pincel:
            self._pincelando = True
            self._pincelar(ev.position())
            return
        if ev.button() == Qt.MouseButton.LeftButton and self.mestre:
            m = self._marcador_em(ev.position())
            if m is not None:   # 🧭 viagem: o mestre arrasta o marcador
                self._viajando = {"m": m, "ini": QPointF(m["pos"]), "nivel": self._nivel_do_quadro()}
                rastro = self.atlas.rastros.setdefault(self._nivel_do_quadro()["id"], [])
                if not rastro or QPointF(*rastro[-1]) != m["pos"]:   # o rastro começa de onde ele saiu
                    rastro.append([round(m["pos"].x(), 1), round(m["pos"].y(), 1)])
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                return
        if ev.button() == Qt.MouseButton.RightButton and self.mestre:
            self._menu(ev)
            return
        if ev.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton):
            self._arrasto = ev.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, ev):
        inv = self.M.inverted()[0]
        if getattr(self, "_regua", None) is not None and ev.buttons() & Qt.MouseButton.LeftButton:
            self._regua[1] = inv.map(ev.position())
            self.update()
            return
        self._mouse = ev.position()
        if self._pincelando:
            self._pincelar(ev.position())
            return
        if self._pincel:
            self.update()   # (o círculo do pincel segue o mouse)
        v = getattr(self, "_viajando", None)
        if v is not None:
            nova = inv.map(ev.position())
            self.atlas.mover_marcador(v["nivel"]["id"], v["m"]["id"], v["m"]["base"], nova)
            if self.atlas.nevoa_ligada(v["nivel"]):   # o grupo revela por onde passa
                self.atlas.pintar_nevoa(v["nivel"], nova, self.atlas.raio_revela(v["nivel"]))
            self.update()
            return
        if self._arrasto is not None:
            d = ev.position() - self._arrasto
            self._arrasto = ev.position()
            self.M = self.M * QTransform().translate(d.x(), d.y())
            self._prender()
            self.update()
        elif self.mestre:
            self.setCursor(Qt.CursorShape.OpenHandCursor if self._marcador_em(ev.position()) else
                           (Qt.CursorShape.CrossCursor if getattr(self, "_medindo", False) else Qt.CursorShape.ArrowCursor))

    def mouseReleaseEvent(self, ev):
        if self._pincelando:
            self._pincelando = False
            self.janela.atlas_editado()
            return
        if getattr(self, "_viajando", None) is not None:
            self._viajando = None
            self.janela.atlas_editado()
        self._arrasto = None
        self.unsetCursor()
        self.update()

    def _menu(self, ev):
        from PyQt6.QtWidgets import QMenu
        nivel = self._nivel_do_quadro()
        if nivel is None:
            return
        menu = QMenu(self)
        m = self._marcador_em(ev.position())
        if m is not None and (self.atlas.viagem.get(nivel["id"]) or {}).get(m["id"]):
            menu.addAction(f"Voltar “{m['nome']}” pro lugar dos tokens",
                           lambda: (self.atlas.voltar_pro_automatico(nivel["id"], m["id"]), self.janela.atlas_editado()))
        if self.atlas.rastros.get(nivel["id"]):
            menu.addAction("Apagar o rastro deste mapa",
                           lambda: (self.atlas.rastros.pop(nivel["id"], None), self.janela.atlas_editado()))
        self._menu_nevoa(menu)
        menu.addSeparator()
        menu.addAction("Montar cidade e mundo…", self.janela.abrir_atlas)
        menu.exec(ev.globalPosition().toPoint())

    def mouseDoubleClickEvent(self, ev):
        """Duplo clique num lugar (cidade) / numa cidade (mundo): desce pra ela."""
        p = ev.position()
        if self.quadro == "cidade":
            for l in self.cidade["lugares"]:
                if self._cena_do_alvo(l["alvo"]) is not None and self.M.mapRect(A.ret(l)).contains(p):
                    self._voar(self.M, self._enquadrar(A.ret(l), self.M, 1 / (A.TROCA * A.FOLGA * 1.02)),
                               lambda l=l: self._descer_pra_mesa(l, self.M))
                    return
        elif self.quadro == "mundo":
            for l in self.atlas.mundo["lugares"]:
                cidade = self.atlas.nivel(l["alvo"])
                if cidade is not None and self.M.mapRect(A.ret(l)).contains(p):
                    W = self._mundo_para_cidade(cidade)
                    self._voar(self.M, self._enquadrar(A.ret(l), self.M, 1.0),
                               lambda c=cidade, W=W: self._mudar_quadro("cidade", c, W.inverted()[0] * self.M))
                    return

    def _mudar_quadro(self, quadro, cidade, M):
        self.quadro, self.cidade, self.M = quadro, cidade, M
        self._atualizar_botoes()
        self.update()

    # ================================================================ botões Mesa · Cidade · Mundo
    def _enquadrar(self, r: QRectF, M_atual: QTransform, folga: float = 0.92) -> QTransform:
        """M que faz o retângulo r (nas coordenadas do quadro) caber na tela, centralizado."""
        w, h = self.width(), self.height()
        s = min(w / max(1e-6, r.width()), h / max(1e-6, r.height())) * folga
        return QTransform().translate(w / 2, h / 2).scale(s, s).translate(-r.center().x(), -r.center().y())

    def _voar(self, de: QTransform, ate: QTransform, ao_fim=None, ms: int = 450):
        """Animação rápida de zoom (no quadro atual), depois chama ao_fim."""
        if self._anim is not None:
            self._anim.stop()
        self._timer.stop()
        w, h = self.width(), self.height()
        meio = QPointF(w / 2, h / 2)
        c0, c1 = de.inverted()[0].map(meio), ate.inverted()[0].map(meio)
        s0, s1 = _esc(de), _esc(ate)
        anim = self._anim = QVariantAnimation(self)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(ms)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        def passo(x):
            x = float(x)
            s = math.exp(math.log(s0) + (math.log(s1) - math.log(s0)) * x)
            c = c0 + (c1 - c0) * x
            self.M = QTransform().translate(w / 2, h / 2).scale(s, s).translate(-c.x(), -c.y())
            self.update()
        anim.valueChanged.connect(passo)
        if ao_fim is not None:
            anim.finished.connect(ao_fim)
        anim.start()

    def ir_para(self, alvo: str):
        cidade_aba, T = self._cidade_para_mesa()
        w, h = self.width(), self.height()
        # câmera atual em pixels da cidade (pra animar dali)
        if self.quadro == "mesa":
            if cidade_aba is None:
                self._atualizar_botoes()
                return
            if alvo == "mesa":
                self._atualizar_botoes()
                return
            self._entrar("cidade", cidade_aba, T * self.visao.viewportTransform())
        if alvo == "mesa":
            cidade = cidade_aba
            if cidade is None:
                self._voltar_pra_mesa_sem_animar()
                self.visao.enquadrar_tudo()
                self._atualizar_botoes()
                return
            if self.quadro == "mundo":
                W = self._mundo_para_cidade(cidade)
                if W is None:
                    self._voltar_pra_mesa_sem_animar()
                    return
                self._mudar_quadro("cidade", cidade, W.inverted()[0] * self.M)
            elif self.cidade is not cidade:
                self._voltar_pra_mesa_sem_animar()
                self.visao.enquadrar_tudo()
                self._mesa_zoom(self.visao.escala)
                return
            _c, lugar = self.atlas.lugar_da_cena(self.janela.cena)
            alvo_M = self._enquadrar(A.ret(lugar), self.M, 1 / (A.TROCA * A.FOLGA * 1.02))
            self._voar(self.M, alvo_M, lambda l=lugar: self._chegar_na_mesa(l))
        elif alvo == "cidade":
            cidade = self.cidade if self.quadro != "mesa" else cidade_aba
            cidade = cidade_aba or cidade
            if self.quadro == "mundo":
                W = self._mundo_para_cidade(cidade)
                if W is None:
                    return
                self._mudar_quadro("cidade", cidade, W.inverted()[0] * self.M)
            self._voar(self.M, self._enquadrar(self._area(cidade), self.M))
        elif alvo == "mundo" and self.atlas.mundo is not None:
            if self.quadro == "cidade":
                W = self._mundo_para_cidade(self.cidade)
                if W is not None:
                    self._mudar_quadro("mundo", self.cidade, W * self.M)
                else:
                    self._mudar_quadro("mundo", self.cidade, self._enquadrar(self._area(self.atlas.mundo), QTransform()))
            self._voar(self.M, self._enquadrar(self._area(self.atlas.mundo), self.M, 1.0))
        self._atualizar_botoes()

    def _chegar_na_mesa(self, lugar):
        self._descer_pra_mesa(lugar, self.M)
        chao = self._chao()
        if chao is not None:   # termina com o cenário enchendo a tela
            QTimer.singleShot(0, lambda: self.visao.voar_para(chao.center(), min(
                self.width() / chao.width(), self.height() / chao.height()) * 0.92, 350))

    # ================================================================ desenho
    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        try:
            if self.quadro == "mesa":
                if self.t <= 0 or self.cidade is None:
                    return
                cidade, T = self._cidade_para_mesa()
                if cidade is None:
                    return
                M = T * self.visao.viewportTransform()
                p.setOpacity(self.t)
                p.fillRect(self.rect(), QColor(COR_FUNDO_MESA))
                self._desenhar_cidade(p, cidade, M, 1.0, mundo_atras=True)
                p.setOpacity(1.0)
                return
            p.fillRect(self.rect(), QColor(COR_FUNDO_MESA))
            if self.quadro == "cidade":
                self._desenhar_cidade(p, self.cidade, self.M, 1.0, mundo_atras=True)
            else:
                self._desenhar_mundo(p, self.M)
            self._desenhar_rastro(p)
            self._desenhar_marcadores(p)
            self._desenhar_regua(p)
            if self._pincel and self._mouse is not None:   # o círculo do pincel
                p.setPen(QPen(QColor(255, 255, 255, 200), 1.5, Qt.PenStyle.DashLine))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(self._mouse, self._pincel_raio, self._pincel_raio)
            self._rotulo(p)
        finally:
            p.end()

    def _desenhar_cidade(self, p, cidade, M, opacidade, mundo_atras=False):
        w, h = self.width(), self.height()
        u = 0.0
        if mundo_atras:
            W = self._mundo_para_cidade(cidade)
            if W is not None:
                u = A.mistura(A.tamanho_na_tela(self._area(cidade), M, w, h))
                if u > 0:
                    base = p.opacity()
                    p.setOpacity(base * u)
                    p.setTransform(W * M)
                    p.drawPixmap(0, 0, self.atlas.pixmap(self.atlas.mundo))
                    p.resetTransform()
                    p.setOpacity(base)
        base = p.opacity()
        p.setOpacity(base * opacidade * (1 - u))
        p.setTransform(M)
        p.drawPixmap(0, 0, self.atlas.pixmap(cidade))
        p.resetTransform()
        self._desenhar_nevoa(p, cidade, M)
        p.setOpacity(base)
        if self.mestre and self.quadro == "cidade" and u < 0.5:
            self._lugares(p, cidade["lugares"], M, lambda l: self._cena_do_alvo(l["alvo"]) is not None)

    def _desenhar_mundo(self, p, M):
        w, h = self.width(), self.height()
        p.setTransform(M)
        p.drawPixmap(0, 0, self.atlas.pixmap(self.atlas.mundo))
        p.resetTransform()
        self._desenhar_nevoa(p, self.atlas.mundo, M)
        for l in self.atlas.mundo["lugares"]:          # chegando perto de uma cidade, ela vai aparecendo
            cidade = self.atlas.nivel(l["alvo"])
            if cidade is None:
                continue
            Mc = self._mundo_para_cidade(cidade).inverted()[0] * M
            u = A.mistura(A.tamanho_na_tela(self._area(cidade), Mc, w, h))
            if u < 1:
                p.setOpacity(1 - u)
                p.setTransform(Mc)
                p.drawPixmap(0, 0, self.atlas.pixmap(cidade))
                p.resetTransform()
                self._desenhar_nevoa(p, cidade, Mc)
                p.setOpacity(1.0)
        if self.mestre:
            self._lugares(p, self.atlas.mundo["lugares"], M, lambda l: self.atlas.nivel(l["alvo"]) is not None,
                          nomes={c["id"]: c["nome"] for c in self.atlas.cidades})

    def _lugares(self, p, lugares, M, valido, nomes=None):
        """(só o mestre) os retângulos marcados, com o nome — o da aba atual em destaque."""
        from ..mesa.atlas import chave_da_cena
        atual = chave_da_cena(self.janela.cena)
        f = QFont()
        f.setPixelSize(12)
        f.setBold(True)
        p.setFont(f)
        for l in lugares:
            if not valido(l):
                continue
            r = M.mapRect(A.ret(l))
            if r.width() < 6:
                continue
            destaque = l["alvo"] == atual or (self.cidade is not None and l["alvo"] == self.cidade["id"])
            cor = QColor(COR_DESTAQUE) if destaque else QColor(240, 230, 210, 170)
            caneta = QPen(cor, 2 if destaque else 1.2, Qt.PenStyle.SolidLine if destaque else Qt.PenStyle.DashLine)
            p.setPen(caneta)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(r)
            nome = l.get("nome") or (nomes or {}).get(l["alvo"]) or self._nome_alvo(l["alvo"])
            if nome and r.width() > 30:
                p.setPen(QColor(0, 0, 0, 200))
                p.drawText(r.adjusted(1, -18, 1, 0).topLeft() + QPointF(1, 14), nome)
                p.setPen(cor)
                p.drawText(r.adjusted(0, -18, 0, 0).topLeft() + QPointF(0, 13), nome)

    # ================================================================ névoa (etapa 3)
    def _desenhar_nevoa(self, p, nivel, M):
        """Mestre: a névoa escurece (ele enxerga através). Jogador: a imagem já chega só com o revelado — e (v0.83)
        por cima do que falta vai a névoa DESENHADA no estilo do tema (ui/nevoa_atlas.py)."""
        if not self.mestre:
            self._nevoa_desenhada(p, nivel, M)
            return
        if not self.atlas.nevoa_ligada(nivel):
            return
        img = self._imagem_nevoa(nivel)
        k = self.atlas.fator_mascara(nivel)
        p.setTransform(QTransform().scale(1 / k, 1 / k) * M)
        p.drawImage(0, 0, img)
        p.resetTransform()

    def _nevoa_desenhada(self, p, nivel, M):
        tela_de = getattr(self.atlas, "_tela", None)
        if tela_de is None:
            return
        try:
            import time
            from . import nevoa_atlas, tema
            from ..graficos import nivel as nivel_graficos
            anda = nevoa_atlas.desenhar(p, nivel["id"], self.atlas._versao.get(nivel["id"], 0), tela_de(nivel), M,
                                        getattr(tema, "_ATUAL", "medieval"), nivel_graficos(), time.monotonic())
        except Exception as erro:   # (erro dentro de paint() fecha o programa)
            from ..seguranca import registrar_erro
            registrar_erro(f"Névoa do atlas não desenhou: {erro!r}")
            return
        if anda and self.isVisible() and not getattr(self, "_nevoa_agendada", False):
            from PyQt6.QtCore import QTimer
            self._nevoa_agendada = True

            def _de_novo():
                self._nevoa_agendada = False
                self.update()
            QTimer.singleShot(100, _de_novo)

    def _imagem_nevoa(self, nivel):
        import numpy as np
        from PyQt6.QtGui import QImage
        chave = (nivel["id"], self.atlas.versao_nevoa.get(nivel["id"], 0))
        cache = self.__dict__.setdefault("_cache_nevoa", {})
        if cache.get(nivel["id"], (None,))[0] == chave:
            return cache[nivel["id"]][1]
        m = self.atlas.mascara(nivel)
        bits = m.constBits()
        bits.setsize(m.sizeInBytes())
        arr = np.frombuffer(bits, np.uint8).reshape(m.height(), m.bytesPerLine())[:, :m.width()].astype(np.float32)
        a = (255 - arr) * 0.62                          # o mestre vê através
        saida = np.empty((m.height(), m.width(), 4), np.uint8)
        for i, v in enumerate((14, 12, 18)):           # B, G, R (pré-multiplicado)
            saida[..., i] = (v * a / 255).astype(np.uint8)
        saida[..., 3] = a.astype(np.uint8)
        img = QImage(saida.tobytes(), m.width(), m.height(), m.width() * 4,
                     QImage.Format.Format_ARGB32_Premultiplied).copy()
        cache[nivel["id"]] = (chave, img)
        return img

    def agendar_revelar(self):
        """Algo mudou na mesa (token andou, mudou de aba): daqui a pouco o grupo revela em volta dele."""
        if not self.mestre or self.atlas.vazio():
            return
        t = self.__dict__.get("_timer_revela")
        if t is None:
            t = self._timer_revela = QTimer(self)
            t.setSingleShot(True)
            t.setInterval(400)
            t.timeout.connect(lambda: self.revelar_pelos_marcadores() and self.janela.atlas_editado())
        if not t.isActive():
            t.start()

    def revelar_pelos_marcadores(self) -> bool:
        """O grupo revela em volta de onde está (em cada cidade e no mundo). Devolve se revelou algo novo."""
        if not self.mestre:
            return False
        mudou = False
        alvos = [("cidade", c) for c in self.atlas.cidades] + ([("mundo", None)] if self.atlas.mundo else [])
        for quadro, cidade in alvos:
            nivel = cidade if quadro == "cidade" else self.atlas.mundo
            if not self.atlas.nevoa_ligada(nivel):
                continue
            for m in self.marcadores(quadro, cidade):
                if self.atlas.revelado(nivel, m["pos"]) < 250:
                    self.atlas.pintar_nevoa(nivel, m["pos"], self.atlas.raio_revela(nivel))
                    mudou = True
        if mudou:
            self.update()
        return mudou

    def _pincelar(self, pos_tela: QPointF):
        nivel = self._nivel_do_quadro()
        if nivel is None:
            return
        raio = self._pincel_raio / max(1e-9, _esc(self.M))
        self.atlas.pintar_nevoa(nivel, self.M.inverted()[0].map(pos_tela), raio, self._pincel == "revelar")
        self.update()

    def _menu_nevoa(self, menu):
        from PyQt6.QtWidgets import QInputDialog
        nivel = self._nivel_do_quadro()
        menu.addSection("Névoa deste mapa")
        a = menu.addAction("Névoa ligada (os jogadores só veem o revelado)",
                           lambda: (self.atlas.ligar_nevoa(nivel, not self.atlas.nevoa_ligada(nivel)),
                                    self.janela.atlas_editado()))
        a.setCheckable(True)
        a.setChecked(self.atlas.nevoa_ligada(nivel))
        for chave, texto in (("revelar", "Pincel: revelar"), ("esconder", "Pincel: cobrir")):
            b = menu.addAction(texto, lambda k=chave: self._definir_pincel(None if self._pincel == k else k))
            b.setCheckable(True)
            b.setChecked(self._pincel == chave)
        menu.addAction("Revelar o mapa todo", lambda: (self.atlas.revelar_tudo(nivel, True), self.janela.atlas_editado()))
        menu.addAction("Cobrir o mapa todo", lambda: (self.atlas.revelar_tudo(nivel, False), self.janela.atlas_editado()))

        def raio():
            esc, un = nivel.get("escala"), A.UNIDADE[nivel["tipo"]]
            atual = self.atlas.raio_revela(nivel)
            if esc:
                v, ok = QInputDialog.getDouble(self, "Raio que o grupo revela", f"Quantos {un} em volta do grupo?",
                                               atual * esc, 0.01, 1e7, 2)
                if ok:
                    self.atlas.definir_raio(nivel, v / esc)
            else:
                a_ = self.atlas.area(nivel)
                v, ok = QInputDialog.getDouble(self, "Raio que o grupo revela",
                                               "Quanto do mapa em volta do grupo (%)? (calibre a escala pra usar "
                                               + un + ")", 100 * atual / max(a_.width(), a_.height()), 0.1, 100, 1)
                if ok:
                    self.atlas.definir_raio(nivel, v / 100 * max(a_.width(), a_.height()))
            self.janela.atlas_editado()
        menu.addAction("Raio que o grupo revela…", raio)

    def _definir_pincel(self, modo):
        self._pincel = modo
        self.setCursor(Qt.CursorShape.CrossCursor if modo else Qt.CursorShape.ArrowCursor)
        self.update()

    def _desenhar_rastro(self, p):
        """(só o mestre) o caminho que o grupo fez neste mapa."""
        nivel = self._nivel_do_quadro()
        pts = self.atlas.rastros.get(nivel["id"]) if (self.mestre and nivel) else None
        if not pts or len(pts) < 2:
            return
        caneta = QPen(QColor(232, 194, 90, 150), 2, Qt.PenStyle.DashLine)
        p.setPen(caneta)
        tela = [self.M.map(QPointF(x, y)) for x, y in pts]
        for a, b in zip(tela, tela[1:]):
            p.drawLine(a, b)

    def _desenhar_marcadores(self, p):
        nivel = self._nivel_do_quadro()
        f = QFont()
        f.setPixelSize(12)
        f.setBold(True)
        p.setFont(f)
        v = self._viajando
        for m in self.marcadores():
            s = self.M.map(m["pos"])
            if v is not None and v["m"]["id"] == m["id"]:   # viajando: linha de onde saiu + a distância
                ini = self.M.map(v["ini"])
                p.setPen(QPen(QColor(255, 255, 255, 200), 2, Qt.PenStyle.DashLine))
                p.drawLine(ini, s)
                texto = A.Atlas.texto_distancia(nivel, math.hypot(m["pos"].x() - v["ini"].x(),
                                                                   m["pos"].y() - v["ini"].y()))
                self._placa(p, (ini + s) / 2, texto)
            # o alfinete: bolinha na cor + ponta no lugar exato
            from PyQt6.QtGui import QPainterPath
            cam = QPainterPath()
            cam.moveTo(s)
            cam.lineTo(s + QPointF(-6, -11))
            cam.arcTo(QRectF(s.x() - 10, s.y() - 26, 20, 20), 210, -240)
            cam.closeSubpath()
            p.setPen(QPen(QColor(15, 12, 8), 2))
            p.setBrush(m["cor"])
            p.drawPath(cam)
            p.setBrush(QColor(255, 255, 255, 220))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(s.x(), s.y() - 16), 3.5, 3.5)
            self._placa(p, s + QPointF(0, -38), m["nome"])

    def _desenhar_regua(self, p):
        if not self._regua:
            return
        a, b = self._regua
        nivel = self._nivel_do_quadro()
        sa, sb = self.M.map(a), self.M.map(b)
        p.setPen(QPen(QColor(COR_DESTAQUE), 2))
        p.drawLine(sa, sb)
        for s in (sa, sb):
            p.drawEllipse(s, 3, 3)
        self._placa(p, sb + QPointF(0, -18), A.Atlas.texto_distancia(nivel, math.hypot(b.x() - a.x(), b.y() - a.y())))

    def _placa(self, p, centro: QPointF, texto: str):
        f = QFont()
        f.setPixelSize(12)
        f.setBold(True)
        p.setFont(f)
        larg = p.fontMetrics().horizontalAdvance(texto) + 14
        r = QRectF(centro.x() - larg / 2, centro.y() - 10, larg, 20)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(20, 16, 12, 215))
        p.drawRoundedRect(r, 4, 4)
        p.setPen(QColor(COR_DESTAQUE))
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, texto)

    def _nome_alvo(self, alvo: str) -> str:
        cena = self._cena_do_alvo(alvo)
        return getattr(cena, "nome_aba", "") if cena is not None else ""

    def _rotulo(self, p):
        nivel = self.cidade if self.quadro == "cidade" else self.atlas.mundo
        if not nivel:
            return
        texto = ("Cidade: " if self.quadro == "cidade" else "Mundo: ") + (nivel.get("nome") or "")
        f = QFont()
        f.setPixelSize(15)
        f.setBold(True)
        p.setFont(f)
        r = QRectF(12, 10, p.fontMetrics().horizontalAdvance(texto) + 20, 26)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(20, 16, 12, 200))
        p.drawRoundedRect(r, 5, 5)
        p.setPen(QColor(COR_DESTAQUE))
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, texto)
