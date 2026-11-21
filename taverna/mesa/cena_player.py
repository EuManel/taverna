"""
A mesa vista pelo Player.

Ela é um "espelho" da mesa do mestre: recebe o estado e atualiza só o que
mudou (assim o token que você está arrastando não pula na sua mão).
O player só consegue pegar os tokens que têm o nome dele como dono.
"""

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsScene

from ..config import CELULA, LIMITE_CENA
from ..rede.protocolo import mesmo_nome
from ..temas import TEMA_PADRAO, tema as dados_tema
from .camadas import Camada
from .construcao import ParedesItem, TerrenoItem
from .grid import GridItem
from .luzes import LuzItem, LuzOverlay, luzes_acesas, poligonos_de_luz
from .mapa import MapaItem
from .portas import PortaItem
from .props import PropItem
from .token import TokenItem
from .efeitos import EfeitoItem
from .desenhos import DesenhosItem


class CenaPlayer(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        L = LIMITE_CENA
        self.setSceneRect(QRectF(-L, -L, 2 * L, 2 * L))
        self.escala_visao = 1.0
        self.snap_ativo = False
        self.meu_nome = ""
        self.ao_mover = None          # função(uid, x, y) que manda pro mestre
        self.ao_interagir = None      # função(uid) quando o jogador abre um prop
        self.ao_mover_prop = None     # função(uid, x, y) quando o jogador arrasta um objeto
        self.ao_abrir_porta = None    # função(uid) quando o jogador abre/fecha uma porta
        self.ao_mudar_clima = None    # função(dict) — a janela liga o clima na tela
        self.ferramenta = "selecionar"   # "efeito" (template) ou "lapis"
        self.efeito_atual = {"efeito": "fogo", "forma": "circulo", "tamanho": 6.0, "largura": 1.5}
        self.lapis = {"cor": "#4cc9f0", "esp": 3.0, "temp": True}
        self.clima = {"tipo": "nenhum", "forca": 2}
        self.combate = {"ativo": False}
        self.regras = {"movem": True}
        self.camadas: list[Camada] = []
        self.itens: dict[str, QGraphicsItem] = {}
        self.grid = GridItem()
        self.addItem(self.grid)
        self.terreno = TerrenoItem()
        self.addItem(self.terreno)
        self.paredes = ParedesItem()
        self.addItem(self.paredes)
        self.paredes.criar_camada_alta(self)   # corpo 3D das paredes/portas, por cima dos tokens
        self.tema = TEMA_PADRAO
        self.nome_aventura = ""
        self.ao_mudar_tema = None     # função(chave)
        from .nevoa import NevoaItem
        self.nevoa = NevoaItem()
        self.addItem(self.nevoa)
        self.luz_ambiente = "dia"
        self.luz_overlay = LuzOverlay(self, limite_escuro=255)
        self.addItem(self.luz_overlay)
        self.desenhos_item = DesenhosItem()
        self.addItem(self.desenhos_item)
        self.nevoa_ativa = False
        self._timer_nevoa = QTimer(self)
        self._timer_nevoa.setSingleShot(True)
        self._timer_nevoa.setInterval(30)
        self._timer_nevoa.timeout.connect(self.recalcular_nevoa)
        self._aplicando = False
        from .vida import Cursores, Suavizador
        self.suavizador = Suavizador(self)
        self.cursores = Cursores(self)
        self._pendentes = {}
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._enviar_movimentos)

    # --- coisas que os itens procuram na cena
    def marcar_modificada(self, valor=True):
        pass

    def definir_escala(self, escala: float):
        self.escala_visao = escala
        for item in self.itens.values():
            if isinstance(item, MapaItem):
                item.escala_mudou()

    def itens_do_usuario(self):
        return [i for i in self.itens.values() if i.isVisible()]

    def meus_tokens(self):
        return [i for i in self.itens.values()
                if isinstance(i, TokenItem) and mesmo_nome(i.dono, self.meu_nome)]

    # --- movimento do meu token -> mestre
    def visao_mudou(self):
        self._agendar_nevoa()

    def _agendar_nevoa(self):
        if self.nevoa_ativa and not self._timer_nevoa.isActive():
            self._timer_nevoa.start()

    def chao_caminho(self):
        """Onde tem cenário (chão pintado + mapas). None = sem chão (não corta nada)."""
        from .chao import caminho_do_chao
        from .mapa import MapaItem
        mapas = [i for i in self.itens.values() if isinstance(i, MapaItem)]
        return caminho_do_chao(self, self.terreno if self.terreno.isVisible() else None, mapas)

    def obstaculos_gas(self):
        """O que segura o gás: paredes, portas fechadas e objetos que bloqueiam."""
        from .linha_de_visao import obstaculos
        portas = [i for i in self.itens.values() if isinstance(i, (PortaItem, PropItem)) and i.isVisible()]
        return obstaculos(self.paredes.segmentos, portas)

    def recalcular_nevoa(self):
        """Recalcula o que os MEUS tokens veem (e a luz) e redesenha a névoa."""
        from .linha_de_visao import obstaculos, poligono
        from .luzes import luzes_extras
        portas = [i for i in self.itens.values() if isinstance(i, (PortaItem, PropItem, EfeitoItem))]
        obst = obstaculos(self.paredes.segmentos, portas)
        luzes = luzes_acesas([i for i in self.itens.values()
                              if isinstance(i, LuzItem) and i.isVisible()])
        luzes += luzes_extras([i for i in self.itens.values()
                               if isinstance(i, (PropItem, TokenItem, EfeitoItem)) and i.isVisible()])
        polys_luz = poligonos_de_luz(luzes, obst) if luzes else []
        from .luzes import iluminar_objetos
        polys_luz = iluminar_objetos(polys_luz, [i for i in self.itens.values() if isinstance(i, PropItem)])
        # Brilho das luzes (e escuridão quando não tem névoa) + as passageiras (bola de fogo…)
        from . import luz_dinamica
        self._polys_fixos, self._obst_luz = polys_luz, obst
        self.luz_overlay.so_brilho = self.nevoa_ativa
        self.luz_overlay.definir(self.luz_ambiente, polys_luz + luz_dinamica.poligonos(self))
        if not self.nevoa_ativa:
            self.nevoa.ativa = False
            self.nevoa.setVisible(False)
            return
        meus = [t for t in self.meus_tokens() if t.tem_visao]
        visoes = []
        for t in meus:
            c = t.centro_cena()
            cone = poligono(c.x(), c.y(), t.direcao, t.visao_abertura, t.visao_alcance, obst)
            ve = min(t.visao_escuro, t.visao_alcance)
            escuro = poligono(c.x(), c.y(), 0, 360, ve, obst) if ve > 0 else None
            visoes.append((cone, escuro))
        self.nevoa.ativa = True
        self.nevoa.setVisible(True)
        # Meus tokens sempre aparecem (com a plaquinha do nome), mesmo fora do cone
        self.nevoa.meus_circulos = [
            QRectF(t.scenePos(), t.scenePos() + QPointF(t.diametro, t.diametro)).adjusted(-4, -4, 4, 26)
            for t in self.meus_tokens()]
        self.nevoa.atualizar(visoes, polys_luz, self.luz_ambiente)

    def token_movido(self, token):
        self._agendar_nevoa()
        if self._aplicando or not mesmo_nome(token.dono, self.meu_nome):
            return
        self._pendentes[token.uid] = token
        if not self._timer.isActive():
            self._timer.start()

    def _enviar_movimentos(self):
        pendentes, self._pendentes = self._pendentes, {}
        if not self.ao_mover:
            return
        for uid, token in pendentes.items():
            p = token.scenePos()
            self.ao_mover(uid, p.x(), p.y())

    # --- estado vindo do mestre
    def limpar(self):
        for item in list(self.itens.values()):
            self.removeItem(item)
        self.itens.clear()
        self.cursores.limpar()
        self.desenhos_item.definir([])
        self.terreno.definir({})
        self.paredes.definir({})
        for especial in (self.grid, self.terreno, self.paredes):
            especial.setParentItem(None)
        for camada in self.camadas:
            self.removeItem(camada)
        self.camadas.clear()

    def aplicar_estado(self, estado: dict, imagens: dict):
        self._aplicando = True
        try:
            self._aplicar(estado, imagens)
        finally:
            self._aplicando = False

    def _aplicar(self, estado, imagens):
        self.combate = estado.get("combate") or {"ativo": False}
        self.regras = estado.get("regras") or {"movem": True}
        self.snap_ativo = bool(estado.get("snap", False))
        self.grid.setOpacity(float(estado.get("opacidade_grid", 0.35)))
        self.nome_aventura = estado.get("aventura", "")
        tema = estado.get("tema", TEMA_PADRAO)
        if tema != self.tema:
            self.tema = tema
            self.grid.cor = QColor(dados_tema(tema)["grid"])
            self.grid.update()
            if self.ao_mudar_tema:
                self.ao_mudar_tema(tema)
        nevoa = bool(estado.get("nevoa", False))
        cenario = estado.get("cenario", "")
        if cenario != getattr(self, "_cenario_nevoa", None):
            self._cenario_nevoa = cenario
            self.nevoa.esquecer()   # cenário novo: nada explorado ainda
        self.nevoa_ativa = nevoa
        self.luz_ambiente = estado.get("ambiente", "dia")
        self.nevoa.cor = QColor(dados_tema(self.tema)["mesa"])
        clima = estado.get("clima") or {"tipo": "nenhum", "forca": 2}
        if clima != self.clima:
            self.clima = dict(clima)
            if self.ao_mudar_clima:
                self.ao_mudar_clima(self.clima)
        self.desenhos_item.definir(estado.get("desenhos") or [])
        construcao = estado.get("construcao")
        if construcao is not None:
            self.terreno.definir(TerrenoItem.de_lista(construcao.get("terreno", [])))
            self.paredes.definir(ParedesItem.de_lista(construcao.get("paredes", [])))
        infos = estado.get("camadas", [])

        # Ajusta a quantidade de camadas
        while len(self.camadas) < len(infos):
            camada = Camada("", "livre")
            self.addItem(camada)
            self.camadas.append(camada)
        while len(self.camadas) > len(infos):
            camada = self.camadas.pop()
            for filho in camada.childItems():
                filho.setParentItem(None)
            self.removeItem(camada)
        for i, camada in enumerate(self.camadas):
            camada.setZValue(i)

        arrastando = self.mouseGrabberItem()
        vistos = set()
        for camada, info in zip(self.camadas, infos):
            if info.get("grid"):
                self.grid.setParentItem(camada)
                self.grid.setVisible(info.get("visivel", True))
                continue
            especial = info.get("especial")
            if especial == "luzes":
                pass
            elif especial == "terreno":
                self.terreno.setParentItem(camada)
            elif especial == "paredes":
                self.paredes.setParentItem(camada)
            for z, d in enumerate(info.get("itens", [])):
                uid = d.get("id")
                if not uid:
                    continue
                item = self.itens.get(uid)
                if d["classe"] == "mapa":
                    item = self._mapa(item, d, imagens)
                elif d["classe"] == "token":
                    item = self._token(item, d, imagens)
                elif d["classe"] == "porta":
                    item = self._porta(item, d)
                elif d["classe"] == "luz":
                    item = self._luz(item, d)
                elif d["classe"] == "prop":
                    item = self._prop(item, d, imagens)
                elif d["classe"] == "efeito":
                    item = self._efeito(item, d)
                else:
                    continue
                if item is None:
                    continue
                self.itens[uid] = item
                vistos.add(uid)
                if item.parentItem() is not camada:
                    item.setParentItem(camada)
                item.setZValue(z)
                if item is not arrastando:
                    if getattr(item, "_novo", True):
                        item.setPos(d["x"], d["y"])     # acabou de aparecer: vai direto
                        item._novo = False
                    else:
                        self.suavizador.mover(item, QPointF(d["x"], d["y"]))

        for uid in list(self.itens):
            if uid not in vistos:
                item = self.itens.pop(uid)
                if item is arrastando:
                    item.ungrabMouse()
                self.suavizador.esquecer(item)
                self.removeItem(item)
        self.recalcular_nevoa()

    def _mapa(self, item, d, imagens):
        dados = imagens.get(d.get("img"))
        if item is not None and not isinstance(item, MapaItem):
            self.removeItem(item)
            item = None
        if item is not None and item.hash_imagem != d.get("img"):
            self.removeItem(item)
            item = None
        if item is None:
            if not dados:
                return None
            try:
                item = MapaItem(dados)
            except ValueError:
                return None
            item.uid = d["id"]
            item.aplicar_trava(True)
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            item.setAcceptHoverEvents(False)
            self.addItem(item)
        if abs(item.w - d["w"]) > 0.01 or abs(item.h - d["h"]) > 0.01:
            item.definir_tamanho_metros(d["w"] / CELULA, d["h"] / CELULA)
        return item

    def _token(self, item, d, imagens):
        if item is not None and not isinstance(item, TokenItem):
            self.removeItem(item)
            item = None
        imagem = imagens.get(d.get("img")) if d.get("img") else None
        if item is None:
            item = TokenItem(d["nome"], d["tipo"], d["cor"], d["tamanho"], imagem, d["dono"])
            item.uid = d["id"]
            self.addItem(item)
        else:
            mudou = (item.nome != d["nome"] or item.tipo != d["tipo"]
                     or item.cor != QColor(d["cor"]) or item.tamanho != d["tamanho"]
                     or item.dono != d["dono"] or item.hash_imagem != d.get("img"))
            if mudou:
                item.atualizar(d["nome"], d["tipo"], d["cor"], d["tamanho"], imagem, d["dono"])
        item.visao_alcance = float(d.get("va", 24))
        item.visao_abertura = float(d.get("vb", 60))
        item.pode_girar = bool(d.get("giro", True))
        estilo = d.get("es") if d.get("es") in ("ficha", "standee") else "ficha"   # (v0.73)
        sb = bool(d.get("sb", False))   # (v0.77) standee sem bordas
        from .token import escala_valida
        se = escala_valida(d.get("se", 1.0))   # (v0.78) escala do standee
        if item.estilo != estilo or item.sem_borda != sb or item.escala_standee != se:
            item.prepareGeometryChange()
            item.estilo = estilo
            item.sem_borda = sb
            item.escala_standee = se
            item.update()
        item.luz = d.get("luz")
        if "ficha" in d:
            item.ficha = d["ficha"]
        if item.efeito != (d.get("efeito") or ""):
            item.efeito = d.get("efeito") or ""
            item._cache_efeito = {}
            self._agendar_nevoa()
        if item.estado != d.get("estado"):
            item.estado = d.get("estado")
            item.update()
        import time
        # Logo depois que EU girei, ignora por um instante o valor antigo que ainda vem do mestre
        if time.monotonic() >= getattr(item, "_giro_local_ate", 0):
            item.direcao = float(d.get("dir", 0))
        item.update()
        # Informações que o mestre liberou pra mim (o dono vê tudo do próprio token)
        from ..jogo.condicoes import info_vazia
        item.info = info_vazia()
        for chave in list(item.info):
            item.info[chave]["v"] = None if chave == "pv" else ([] if chave == "condicoes" else "")
            item.info[chave]["vis"] = "-"     # "-" = não liberado
        item.info.update(d.get("info") or {})
        item.ver_ocultos = False
        da_vez = bool(self.combate.get("ativo")) and self.combate.get("vez") == item.uid
        item.definir_vez(da_vez)
        origem = self.combate.get("origem") if da_vez else None
        from PyQt6.QtCore import QPointF
        item.origem_turno = QPointF(origem[0], origem[1]) if origem else None
        item.limite_turno = self.combate.get("limite") if da_vez else None
        item.prender_no_limite = True
        meu = mesmo_nome(item.dono, self.meu_nome)
        if self.combate.get("ativo"):
            pode = meu and self.combate.get("vez") == item.uid
        else:
            pode = meu and bool(self.regras.get("movem", True))
        item.aplicar_trava(not pode)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, meu)
        return item

    def _porta(self, item, d):
        if item is not None and not isinstance(item, PortaItem):
            self.removeItem(item)
            item = None
        if item is None:
            item = PortaItem()
            item.uid = d["id"]
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            item.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
            item.mostrar_tranca = False
            self.addItem(item)
            item.aplicar_dict(d)
            item.pular_animacao()
            item.setCursor(Qt.CursorShape.PointingHandCursor if item.jogadores_abrem else Qt.CursorShape.ArrowCursor)
            return item
        item.aplicar_dict(d)
        return item

    def _prop(self, item, d, imagens):
        img = imagens.get(d.get("img")) if d.get("img") else None
        if item is not None and (not isinstance(item, PropItem) or item.hash_imagem != d.get("img")):
            self.removeItem(item)
            item = None
        if item is None:
            item = PropItem(d.get("tipo", "bau"), img)
            item.uid = d["id"]
            item.mostrar_tranca = False
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            item.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
            self.addItem(item)
            item.aplicar_dict(d)
            self._prop_movel(item)
            return item
        luz_antes, bloq_antes = (item.luz, item.luz_acesa, item.efeito), item.bloqueia
        item.aplicar_dict(d)
        self._prop_movel(item)
        if (item.luz, item.luz_acesa, item.efeito) != luz_antes or item.bloqueia != bloq_antes:
            self._agendar_nevoa()
        return item

    def _prop_movel(self, prop):
        # objeto que o mestre deixou os jogadores moverem (no combate, só na minha vez)
        meus = {t.uid for t in self.meus_tokens()}
        pode = prop.movel and (not self.combate.get("ativo") or self.combate.get("vez") in meus)
        prop.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, pode)
        prop.setCursor(Qt.CursorShape.OpenHandCursor if pode else Qt.CursorShape.ArrowCursor)

    def prop_arrastado(self, prop):
        if self.ao_mover_prop and prop.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable:
            p = prop.scenePos()
            self.ao_mover_prop(prop.uid, p.x(), p.y())

    def porta_duplo_clique(self, porta):
        if porta.jogadores_abrem and self.ao_abrir_porta:
            self.ao_abrir_porta(porta.uid)

    def token_duplo_clique(self, token):
        if token.dono and mesmo_nome(token.dono, self.meu_nome):   # (v0.64.1) o meu: editar nome, cor, imagem
            editar = getattr(self, "ao_editar_meu", None)
            if editar is not None:
                editar(token)
            return
        # revistar uma criatura caída/morta
        if not mesmo_nome(token.dono, self.meu_nome) and token.estado and self.ao_interagir:
            self.ao_interagir(token.uid)

    def prop_duplo_clique(self, prop):
        # o jogador quer abrir/mexer: pede pro mestre
        if (prop.interativo or prop.tipo == "escada") and self.ao_interagir:   # escada: subir/descer
            self.ao_interagir(prop.uid)

    def _efeito(self, item, d):
        if item is not None and not isinstance(item, EfeitoItem):
            self.removeItem(item)
            item = None
        if item is None:
            item = EfeitoItem()
            item.uid = d["id"]
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            self.addItem(item)
            item.aplicar_dict(d)
            self._agendar_nevoa()
            return item
        antes = (item.efeito, item.chave_forma(), item.angulo, item.pos().x(), item.pos().y())
        item.aplicar_dict(d)
        if antes != (item.efeito, item.chave_forma(), item.angulo, d["x"], d["y"]):
            self._agendar_nevoa()
        return item

    def meus_efeitos(self):
        return [i for i in self.itens.values() if isinstance(i, EfeitoItem) and mesmo_nome(i.dono, self.meu_nome)]

    def _luz(self, item, d):
        if item is not None and not isinstance(item, LuzItem):
            self.removeItem(item)
            item = None
        if item is None:
            item = LuzItem(d.get("tipo", "tocha"))
            item.uid = d["id"]
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            item.icone_oculto = True   # (v0.48) o jogador vê a LUZ, mas não o "ponto de luz" (só o mestre vê)
            item.unsetCursor()
            self.addItem(item)
        item.aplicar_dict(d)
        return item
