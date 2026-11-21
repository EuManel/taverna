"""
A mesa em si: guarda as camadas, os itens e as configurações (snap, grid).

Ordem padrão das camadas (de baixo pra cima):
    Mapa -> Terreno -> Grid -> Paredes -> Criaturas e NPCs -> Jogadores
O mestre pode reordenar, esconder, travar e criar camadas novas.
"""

import math

from PyQt6.QtCore import QTimer, QLineF, QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsScene

from ..config import CELULA, LIMITE_CENA, TIPOS_TOKEN
from ..temas import TEMA_PADRAO, tema as dados_tema
from .camadas import Camada
from .construcao import ESPESSURA, ParedesItem, TerrenoItem, distancia_segmento
from .portas import PortaItem
from .grid import GridItem
from .mapa import MapaItem
from .token import TokenItem


class MesaCena(QGraphicsScene):
    camadas_mudaram = pyqtSignal()   # camadas OU itens dentro delas mudaram
    modificacao_mudou = pyqtSignal(bool)
    snap_mudou = pyqtSignal(bool)
    editar_token_pedido = pyqtSignal(object)
    mesa_mudou = pyqtSignal()        # qualquer mudança que os players precisam ver
    tema_mudou = pyqtSignal(str)
    selecao_construcao_mudou = pyqtSignal(int, int)   # paredes, pinceladas
    editar_prop_pedido = pyqtSignal(object)
    editar_gatilho_pedido = pyqtSignal(object)
    editar_efeito_pedido = pyqtSignal(object)
    ferramenta_mudou = pyqtSignal(str)
    reacoes_sugeridas = pyqtSignal(list)   # [(par, área, área)] — água em cima do fogo etc.

    NOMES = {"mapa": "Mapa", "terreno": "Terreno", "grid": "Grid", "paredes": "Paredes",
             "props": "Objetos", "luzes": "Luzes", "criaturas": "Criaturas e NPCs",
             "jogadores": "Jogadores"}
    ORDEM_PADRAO = ["mapa", "terreno", "grid", "paredes", "props", "luzes", "criaturas", "jogadores"]

    def __init__(self, parent=None):
        super().__init__(parent)
        L = LIMITE_CENA
        self.setSceneRect(QRectF(-L, -L, 2 * L, 2 * L))
        self.escala_visao = 1.0
        self.snap_ativo = False
        self.opacidade_grid = 0.35
        self.modificada = False
        self.predio = None      # 🏢 andares (mesa/andares.py): abas do mesmo prédio têm o mesmo id
        self.andar = 0
        # reações entre áreas (mesa/reacoes.py): o mestre confirma cada uma
        self._areas_mudadas = set()
        self._reagidos = set()      # pares (uids) que já reagiram
        self._recusados = {}        # par → assinatura (o mestre disse "agora não")
        self.reacoes_ligadas = True
        self._timer_reacoes = QTimer(self)
        self._timer_reacoes.setSingleShot(True)
        self._timer_reacoes.setInterval(600)
        self._timer_reacoes.timeout.connect(self._procurar_reacoes)
        self.camadas: list[Camada] = []
        self.camada_ativa: Camada | None = None
        self.grid: GridItem | None = None
        self.terreno: TerrenoItem | None = None
        self.paredes: ParedesItem | None = None
        self.nome_aventura = ""
        self.nome_aba = "Cenário 1"     # cada aba (cenário) da aventura é uma MesaCena
        import uuid
        self.uid = uuid.uuid4().hex
        self.tema = TEMA_PADRAO
        # Ferramentas de construção
        self.ferramenta = "selecionar"
        self.material_chao = "pedra"
        self.material_parede = "pedra"
        self.pincel = 1            # diâmetro do pincel em metros (ou lado, no modo grid)
        self.forma_pincel = "livre"  # "livre" (redondo) ou "grid" (quadrado por quadrado)
        self.tipo_porta = "madeira"
        self.largura_porta = 1.0
        from .vida import Cursores, Suavizador
        self.suavizador = Suavizador(self)
        self.cursores = Cursores(self)
        # Visão / névoa de guerra (por aba)
        self.nevoa_ativa = False
        self.mostrar_cones = False
        self.cones = None
        # Luz
        self.luz_ambiente = "dia"
        self.previa_luz = True
        self.luz_overlay = None
        self.tipo_luz = "tocha"
        self._timer_luz = QTimer(self)
        self._timer_luz.setSingleShot(True)
        self._timer_luz.setInterval(40)
        self._timer_luz.timeout.connect(self.recalcular_luzes)
        self.mesa_mudou.connect(self._timer_luz.start)
        self.mesa_mudou.connect(self._agendar_cones)
        # Atmosfera (Etapa 10)
        self.clima = {"tipo": "nenhum", "forca": 2}
        self.efeito_atual = {"efeito": "fogo", "forma": "circulo", "tamanho": 6.0, "largura": 1.5}
        self.lapis = {"cor": "#ffd166", "esp": 3.0, "temp": True}
        self.impacto_atual = None   # {"tipo", "tam"} — efeito rápido armado pra clicar no mapa
        self.tracos: list[dict] = []
        self.desenhos_item = None
        self._timer_tracos = QTimer(self)
        self._timer_tracos.setInterval(1000)
        self._timer_tracos.timeout.connect(self._limpar_tracos_vencidos)
        self._historico: list[str] = []   # estados da construção (JSON)
        self._posicao_hist = -1
        self.criar_camadas_padrao()

    # ============================================================ camadas
    def criar_camada(self, tipo: str, nome: str | None = None,
                     indice: int | None = None) -> Camada:
        """Cria uma camada. As especiais (grid, terreno, paredes) já vêm com conteúdo."""
        camada = self._adicionar_camada(Camada(nome or self.NOMES.get(tipo, "Camada"), tipo),
                                        indice)
        if tipo == "grid":
            self.grid = GridItem()
            self.grid.setOpacity(self.opacidade_grid)
            self.grid.cor = QColor(dados_tema(self.tema)["grid"])
            self.grid.setParentItem(camada)
        elif tipo == "terreno":
            self.terreno = TerrenoItem()
            self.terreno.setParentItem(camada)
        elif tipo == "paredes":
            antiga = getattr(self.paredes, "_alta", None) if self.paredes is not None else None
            try:
                if antiga is not None and antiga.scene() is self:
                    self.removeItem(antiga)
            except RuntimeError:   # a cena foi limpa (clear): a antiga já não existe
                pass
            self.paredes = ParedesItem()
            self.paredes.setParentItem(camada)
            self.paredes.criar_camada_alta(self)   # corpo 3D das paredes/portas, por cima dos tokens
        return camada

    def garantir_camadas_especiais(self):
        """Arquivos antigos podem não ter Terreno/Paredes: cria no lugar certo."""
        for pos, tipo in enumerate(self.ORDEM_PADRAO):
            if self.camada_por_tipo(tipo):
                continue
            indice = 0
            for anterior in reversed(self.ORDEM_PADRAO[:pos]):
                c = self.camada_por_tipo(anterior)
                if c:
                    indice = self.camadas.index(c) + 1
                    break
            self.criar_camada(tipo, indice=indice)

    def criar_camadas_padrao(self):
        self.clear()
        self.camadas = []
        self.limpar_restos()
        for tipo in self.ORDEM_PADRAO:
            self.criar_camada(tipo)
        self.camada_ativa = self.camadas[-1]
        self.adicionar_extras()
        self.camadas_mudaram.emit()
        self.mesa_mudou.emit()
        self.reiniciar_historico()

    def limpar_restos(self):
        """Mesa nova/aberta (v0.46.1): nada da sessão anterior fica pendurado — gás/líquido de cenário e as
        fontes, as luzes passageiras (a luz da lava ficava acesa no vazio), andar."""
        f = getattr(self, "fluidos", None)
        if f is not None:
            f.limpar(fontes=True)
        self.__dict__.pop("_luzes_temp", None)
        self.__dict__.pop("_polys_fixos", None)
        self.__dict__.pop("_obst_luz", None)
        self.predio, self.andar = None, 0

    def _adicionar_camada(self, camada: Camada, indice: int | None = None) -> Camada:
        self.addItem(camada)
        if indice is None:
            self.camadas.append(camada)
        else:
            self.camadas.insert(indice, camada)
        self._renumerar_camadas()
        return camada

    def _renumerar_camadas(self):
        for i, camada in enumerate(self.camadas):
            camada.setZValue(i)

    def camada_por_tipo(self, tipo: str) -> Camada | None:
        for camada in self.camadas:
            if camada.tipo == tipo:
                return camada
        return None

    def nova_camada(self, nome: str) -> Camada:
        """Cria uma camada livre logo acima da camada ativa."""
        indice = len(self.camadas)
        if self.camada_ativa in self.camadas:
            indice = self.camadas.index(self.camada_ativa) + 1
        camada = self._adicionar_camada(Camada(nome, "livre"), indice)
        self.camada_ativa = camada
        self.marcar_modificada()
        self.camadas_mudaram.emit()
        return camada

    def remover_camada(self, camada: Camada) -> bool:
        if camada.fixa or camada not in self.camadas:
            return False
        self.camadas.remove(camada)
        self.removeItem(camada)
        self._renumerar_camadas()
        if self.camada_ativa is camada:
            self.camada_ativa = self.camadas[-1]
        self.marcar_modificada()
        self.camadas_mudaram.emit()
        return True

    def mover_camada(self, camada: Camada, delta: int):
        """delta = +1 sobe (fica mais por cima), -1 desce."""
        i = self.camadas.index(camada)
        j = max(0, min(len(self.camadas) - 1, i + delta))
        if i == j:
            return
        self.camadas.insert(j, self.camadas.pop(i))
        self._renumerar_camadas()
        self.marcar_modificada()
        self.camadas_mudaram.emit()

    def definir_visivel(self, camada: Camada, visivel: bool):
        camada.setVisible(visivel)
        if not visivel:
            for item in camada.itens():
                item.setSelected(False)
        self.marcar_modificada()
        self.camadas_mudaram.emit()

    def definir_travada(self, camada: Camada, travada: bool):
        camada.definir_travada(travada)
        self.marcar_modificada()
        self.camadas_mudaram.emit()

    def renomear_camada(self, camada: Camada, nome: str):
        camada.nome = nome
        self.marcar_modificada()
        self.camadas_mudaram.emit()

    def mover_item_para_camada(self, item, camada: Camada):
        pos_cena = item.scenePos()
        item.setParentItem(camada)
        item.setPos(camada.mapFromScene(pos_cena))
        item.aplicar_trava(camada.travada)
        self.marcar_modificada()
        self.camadas_mudaram.emit()

    def definir_item_visivel(self, item, visivel: bool):
        item.setVisible(visivel)
        if not visivel:
            item.setSelected(False)
        self.marcar_modificada()
        self.camadas_mudaram.emit()

    def mover_item_na_camada(self, item, direcao: int):
        """direcao +1 = trazer pra frente, -1 = enviar pra trás (dentro da camada)."""
        irmaos = sorted((i for i in item.parentItem().itens() if i is not item),
                        key=lambda i: i.zValue())
        if not irmaos:
            return
        item.setZValue(irmaos[-1].zValue() + 1 if direcao > 0 else irmaos[0].zValue() - 1)
        self.marcar_modificada()
        self.camadas_mudaram.emit()

    # ============================================================ itens
    def _colocar(self, item, camada: Camada, centro: QPointF | None):
        item.setParentItem(camada)
        item.aplicar_trava(camada.travada)
        # Novo item fica por cima dos outros da mesma camada
        zs = [i.zValue() for i in camada.itens() if i is not item]
        item.setZValue((max(zs) + 1) if zs else 0)
        if centro is not None:
            if isinstance(item, MapaItem):
                item.setPos(centro.x() - item.w / 2, centro.y() - item.h / 2)
            else:
                d = item.diametro
                item.setPos(centro.x() - d / 2, centro.y() - d / 2)
                if self.snap_ativo:
                    item.encaixar()
        self.marcar_modificada()
        self.camadas_mudaram.emit()
        return item

    def adicionar_mapa(self, dados: bytes, centro: QPointF | None = None,
                       nome: str = "Mapa") -> MapaItem:
        mapa = MapaItem(dados)
        mapa.nome = nome
        camada = self.camada_por_tipo("mapa") or self.camadas[0]
        return self._colocar(mapa, camada, centro or QPointF(0, 0))

    def adicionar_token(self, dados: dict, centro: QPointF | None = None) -> TokenItem:
        token = TokenItem(dados["nome"], dados["tipo"], dados["cor"],
                          dados["tamanho"], dados.get("imagem"), dados.get("dono", ""))
        tipo_camada = TIPOS_TOKEN.get(dados["tipo"], TIPOS_TOKEN["criatura"])[2]
        camada = self.camada_por_tipo(tipo_camada) or self.camadas[-1]
        return self._colocar(token, camada, centro or QPointF(CELULA / 2, CELULA / 2))

    # --- reações entre áreas (água apaga fogo…): espera soltar o mouse e pergunta ao mestre
    def area_mudou(self, area):
        if not self.reacoes_ligadas:
            return
        self._areas_mudadas.add(area)
        self._timer_reacoes.start()

    def _procurar_reacoes(self):
        from PyQt6.QtWidgets import QApplication
        if QApplication.mouseButtons() != Qt.MouseButton.NoButton:
            self._timer_reacoes.start()   # ainda arrastando
            return
        mudadas, self._areas_mudadas = list(self._areas_mudadas), set()
        try:
            from .reacoes import aplicar, procurar
            achadas = procurar(self, [a for a in mudadas if a.scene() is self])
        except RuntimeError:   # área apagada no meio do caminho
            return
        # v0.42: AUTOMÁTICO (o Manel tirou o aviso): encostou, reage
        janela = self.parent()
        impacto = (lambda tipo, x, y, tam: janela.impacto_de_reacao(self, tipo, x, y, tam)) \
            if hasattr(janela, "impacto_de_reacao") else None
        feitas = []
        for par, a, b in achadas:
            try:
                if a.scene() is not self or b.scene() is not self:
                    continue   # (uma reação anterior já tirou uma delas)
                feitas.append(aplicar(self, par, a, b, impacto))
            except RuntimeError:
                continue
        if feitas:
            self.reacoes_sugeridas.emit(feitas)   # (a janela só mostra na barra de status)

    def recusar_reacao(self, a, b):
        from .reacoes import assinatura
        self._recusados[frozenset((a.uid, b.uid))] = assinatura(a, b)

    def gravar_marca(self, area):
        """A área de efeito ficou tempo bastante: o chão embaixo fica marcado (queimado, corroído…)."""
        from .marcas import op_da_area
        op = op_da_area(area)
        if op and self.terreno is not None:
            self.terreno.adicionar_marca(op)
            self.marcar_modificada()
            self.registrar()

    def limpar_marcas(self) -> int:
        """Tira as marcas de efeito do chão (Atmosfera → Limpar marcas do chão)."""
        n = self.terreno.limpar_marcas() if self.terreno is not None else 0
        if n:
            self.marcar_modificada()
            self.registrar()
        return n

    def remover_itens(self, itens):
        tinha_porta = False
        for item in list(itens):
            if hasattr(item, "para_dict"):
                if isinstance(item, PortaItem):
                    tinha_porta = True
                    self._fechar_vao(item)   # (v0.60.1) tirou a porta: a parede fecha de novo
                if hasattr(item, "gravar_se_marcou"):
                    item.gravar_se_marcou()   # área de efeito: deixa a marca no chão
                self.removeItem(item)
        self.marcar_modificada()
        self.camadas_mudaram.emit()
        if tinha_porta:
            self.registrar()

    def itens_do_usuario(self):
        return [i for c in self.camadas for i in c.itens()]

    # ============================================================ opções
    def definir_snap(self, ativo: bool):
        self.snap_ativo = ativo
        self.snap_mudou.emit(ativo)
        self.mesa_mudou.emit()

    def definir_opacidade_grid(self, valor: float):
        self.opacidade_grid = valor
        if self.grid:
            self.grid.setOpacity(valor)
        self.marcar_modificada()

    def definir_escala(self, escala: float):
        self.escala_visao = escala
        for item in self.itens_do_usuario():
            if isinstance(item, MapaItem):
                item.escala_mudou()

    def item_por_id(self, uid: str):
        for item in self.itens_do_usuario():
            if item.uid == uid:
                return item
        return None

    # ============================================================ aventura e tema
    def definir_tema(self, chave: str):
        self.tema = chave
        if self.grid:
            self.grid.cor = QColor(dados_tema(chave)["grid"])
            self.grid.update()
        self.tema_mudou.emit(chave)
        self.marcar_modificada()

    # ============================================================ visão
    def adicionar_extras(self):
        """Itens auxiliares que não são camadas (recriados depois de limpar a cena)."""
        from .nevoa import ConesDoMestre
        from .luzes import LuzOverlay
        self.cones = ConesDoMestre(self)
        self.cones.setVisible(self.mostrar_cones)
        self.addItem(self.cones)
        from .desenhos import DesenhosItem
        self.desenhos_item = DesenhosItem()
        self.addItem(self.desenhos_item)
        self.desenhos_item.definir(self.tracos)
        self.luz_overlay = LuzOverlay(self, limite_escuro=150)  # o mestre ainda enxerga
        self.luz_overlay.setVisible(self.previa_luz)
        self.addItem(self.luz_overlay)
        self.recalcular_luzes()

    def tokens_com_visao(self):
        return [i for i in self.itens_do_usuario()
                if isinstance(i, TokenItem) and i.tem_visao and i.parentItem().isVisible()]

    def _agendar_cones(self):
        if self.cones is not None:
            try:
                self.cones.agendar()
            except RuntimeError:
                self.cones = None

    def visao_mudou(self):
        self._agendar_cones()

    # ============================================================ luz
    def itens_de_luz(self):
        from .luzes import luzes_extras
        camada = self.camada_por_tipo("luzes")
        lista = [i for i in camada.itens() if i.isVisible()] if camada and camada.isVisible() else []
        tokens = [t for t in self.itens_do_usuario()
                  if isinstance(t, TokenItem) and t.isVisible() and t.parentItem().isVisible()]
        return lista + luzes_extras(self.props_visiveis() + tokens + self.efeitos_visiveis())

    def efeitos_visiveis(self):
        from .efeitos import EfeitoItem
        return [i for c in self.camadas if c.isVisible() for i in c.itens()
                if isinstance(i, EfeitoItem) and i.isVisible()]

    def criar_efeito(self, d: dict, dono: str = ""):
        """Área de efeito/template. d: efeito, forma, tamanho, largura, angulo, x, y (origem)."""
        from .efeitos import EfeitoItem
        camada = self.camada_por_tipo("props") or self.criar_camada("props")
        item = EfeitoItem(d.get("efeito", "fogo"), d.get("forma", "circulo"), d.get("tamanho"),
                          float(d.get("largura", 1.5)), float(d.get("angulo", 0)), dono)
        item.nome = str(d.get("nome", ""))[:60]
        from .efeitos import cor_valida
        item.cor = cor_valida(d.get("cor", ""))   # cor livre (magia, luz, radiante, escuridão)
        item.pontos = EfeitoItem._poligonos(d.get("pontos"))      # forma livre (pedaço de uma reação)
        item.recortes = EfeitoItem._poligonos(d.get("recortes"))
        if d.get("forma") == "livre" and item.pontos:
            item.forma = "livre"
        # (v0.45.1) já no lugar ANTES de entrar na mesa — senão o corte "fora do mapa" era feito no (0,0)
        item.setPos(camada.mapFromScene(QPointF(float(d.get("x", 0)), float(d.get("y", 0)))))
        item.setZValue(-1)   # embaixo dos objetos da mesma camada
        item.setParentItem(camada)
        if self.chao_caminho() is not None and item.caminho_cena().isEmpty():
            self.removeItem(item)   # caiu todo no vazio (fora do mapa): efeito não existe ali
            self.efeito_no_vazio = True
            return None
        self.efeito_no_vazio = False
        self.marcar_modificada()
        self.camadas_mudaram.emit()
        self.mesa_mudou.emit()
        self.area_mudou(item)   # caiu em cima de outra? (água no fogo…)
        return item

    def remover_efeitos(self, dono: str | None = None, ids=None) -> int:
        n = 0
        for e in list(self.efeitos_visiveis()):
            if (dono is None or e.dono.casefold() == dono.casefold()) and (ids is None or e.uid in ids):
                e.gravar_se_marcou()   # deixa a marca no chão (se ficou tempo bastante)
                self.removeItem(e)
                n += 1
        if n:
            self.marcar_modificada()
            self.camadas_mudaram.emit()
            self.mesa_mudou.emit()
        return n

    # ============================================================ lápis
    def adicionar_traco(self, traco: dict):
        import time
        if traco.get("temp"):
            from .desenhos import SEGUNDOS_TEMPORARIO
            traco["ate"] = time.time() + SEGUNDOS_TEMPORARIO
            self._timer_tracos.start()
        self.tracos.append(traco)
        if len(self.tracos) > 400:
            del self.tracos[:-400]
        if self.desenhos_item is not None:
            self.desenhos_item.definir(self.tracos)
        if not traco.get("temp"):
            self.marcar_modificada()
        self.mesa_mudou.emit()

    def apagar_tracos(self, autor: str | None = None) -> int:
        antes = len(self.tracos)
        if autor is None:
            self.tracos = []
        else:
            self.tracos = [t for t in self.tracos if t.get("autor", "").casefold() != autor.casefold()]
        if self.desenhos_item is not None:
            self.desenhos_item.definir(self.tracos)
        if len(self.tracos) != antes:
            self.marcar_modificada()
            self.mesa_mudou.emit()
        return antes - len(self.tracos)

    def _limpar_tracos_vencidos(self):
        import time
        agora = time.time()
        restam = [t for t in self.tracos if not t.get("ate") or t["ate"] > agora]
        if len(restam) != len(self.tracos):
            self.tracos = restam
            if self.desenhos_item is not None:
                self.desenhos_item.definir(self.tracos)
            self.mesa_mudou.emit()
        if not any(t.get("ate") for t in self.tracos):
            self._timer_tracos.stop()

    def definir_clima(self, tipo: str | None = None, forca: int | None = None):
        if tipo is not None:
            self.clima["tipo"] = tipo
        if forca is not None:
            self.clima["forca"] = int(forca)
        self.marcar_modificada()
        self.mesa_mudou.emit()

    def props_visiveis(self):
        from .props import PropItem
        camada = self.camada_por_tipo("props")
        if not camada or not camada.isVisible():
            return []
        return [i for i in camada.itens() if isinstance(i, PropItem) and i.isVisible()]

    def colocar_prop(self, tipo: str, pos: QPointF, imagem: bytes | None = None):
        from .props import PropItem
        camada = self.camada_por_tipo("props")
        if camada is None:
            camada = self.criar_camada("props")
        prop = PropItem(tipo, imagem)
        if imagem:
            prop.nome = "Objeto (imagem)"
        p = QPointF(pos.x() - prop.largura / 2, pos.y() - prop.altura / 2)
        if self.snap_ativo:
            p = QPointF(round(p.x() / CELULA) * CELULA, round(p.y() / CELULA) * CELULA)
        if (prop.documento or prop.solto) and not prop.itens:
            from .props import novo_id_item
            item = {"id": novo_id_item(), "nome": prop.nome, "qtd": 1, "desc": "", "img": None}
            if prop.documento:
                item["doc"] = {"texto": "", "img": None}
            prop.itens = [item]
        prop.setParentItem(camada)
        prop.setPos(camada.mapFromScene(p))
        prop.aplicar_trava(camada.travada)
        self.marcar_modificada()
        self.camadas_mudaram.emit()
        self.visao_mudou()
        return prop

    def areas_gatilho(self):
        from .gatilho_area import AreaGatilhoItem
        return [i for i in self.itens_do_usuario() if isinstance(i, AreaGatilhoItem) and i.isVisible()]

    def criar_area_gatilho(self, pos: QPointF):
        from .gatilho_area import AreaGatilhoItem
        camada = self.camada_por_tipo("props") or self.criar_camada("props")
        area = AreaGatilhoItem(2, 2)
        p = QPointF(pos.x() - CELULA, pos.y() - CELULA)
        if self.snap_ativo:
            p = QPointF(round(p.x() / CELULA) * CELULA, round(p.y() / CELULA) * CELULA)
        area.setParentItem(camada)
        area.setPos(camada.mapFromScene(p))
        self.marcar_modificada()
        self.camadas_mudaram.emit()
        return area

    def prop_duplo_clique(self, prop):
        self.editar_prop_pedido.emit(prop)

    def obstaculos_visiveis(self):
        from .linha_de_visao import obstaculos
        camada = self.camada_por_tipo("paredes")
        if not camada or not camada.isVisible():
            return []
        return obstaculos(self.paredes.segmentos if self.paredes else {},
                          list(camada.itens()) + self.props_visiveis() + self.efeitos_visiveis())

    def chao_caminho(self):
        """Onde tem cenário (chão pintado + mapas importados). None = mesa sem chão (não corta nada)."""
        from .chao import caminho_do_chao
        from .mapa import MapaItem
        mapas = [i for c in self.camadas if c.isVisible() for i in c.itens() if isinstance(i, MapaItem)]
        camada_t = self.camada_por_tipo("terreno")
        terreno = self.terreno if camada_t is None or camada_t.isVisible() else None
        return caminho_do_chao(self, terreno, mapas)

    def obstaculos_gas(self):
        """O que segura o gás: paredes, portas fechadas e objetos que bloqueiam (não as outras áreas)."""
        from .linha_de_visao import obstaculos
        camada = self.camada_por_tipo("paredes")
        if not camada or not camada.isVisible():
            return []
        return obstaculos(self.paredes.segmentos if self.paredes else {},
                          list(camada.itens()) + self.props_visiveis())

    def recalcular_luzes(self):
        if self.luz_overlay is None:
            return
        from .luzes import luzes_acesas, poligonos_de_luz
        try:
            from .luzes import iluminar_objetos
            from . import luz_dinamica
            obst = self.obstaculos_visiveis()
            polys = poligonos_de_luz(luzes_acesas(self.itens_de_luz()), obst)
            polys = iluminar_objetos(polys, self.props_visiveis())
            self._polys_fixos, self._obst_luz = polys, obst   # (as passageiras usam — luz_dinamica)
            self.luz_overlay.definir(self.luz_ambiente, polys + luz_dinamica.poligonos(self))
        except RuntimeError:
            self.luz_overlay = None

    def definir_ambiente(self, chave: str):
        self.luz_ambiente = chave
        self.recalcular_luzes()
        self.marcar_modificada()

    def definir_previa_luz(self, mostrar: bool):
        self.previa_luz = mostrar
        if self.luz_overlay is not None:
            self.luz_overlay.setVisible(mostrar)

    def colocar_luz(self, pos: QPointF):
        from .luzes import LuzItem
        camada = self.camada_por_tipo("luzes")
        if not camada or camada.travada:
            return None
        luz = LuzItem(self.tipo_luz)
        if self.snap_ativo:   # no centro do quadrado
            pos = QPointF((math.floor(pos.x() / CELULA) + 0.5) * CELULA,
                          (math.floor(pos.y() / CELULA) + 0.5) * CELULA)
        luz.setParentItem(camada)
        luz.setPos(camada.mapFromScene(pos))
        luz.aplicar_trava(camada.travada)
        self.marcar_modificada()
        self.camadas_mudaram.emit()
        return luz

    def definir_nevoa(self, ativa: bool):
        self.nevoa_ativa = ativa
        self.marcar_modificada()

    def definir_mostrar_cones(self, mostrar: bool):
        self.mostrar_cones = mostrar
        if self.cones is not None:
            self.cones.setVisible(mostrar)
            if mostrar:
                self.cones.recalcular()

    # ============================================================ desfazer / refazer
    # Vale pra construção: terreno, paredes e portas. Cada ação concluída guarda
    # uma "foto" do estado; Ctrl+Z volta uma foto, Ctrl+Y avança.
    LIMITE_HISTORICO = 80

    def _foto_construcao(self) -> str:
        import json
        camada = self.camada_por_tipo("paredes")
        portas = [i.para_dict() for i in camada.itens()] if camada else []
        return json.dumps({
            "t": self.terreno.para_lista() if self.terreno else [],
            "p": self.paredes.para_lista() if self.paredes else [],
            "d": portas,
        }, separators=(",", ":"))

    def reiniciar_historico(self):
        self._historico = [self._foto_construcao()]
        self._posicao_hist = 0

    def registrar(self):
        """Chame depois de cada ação de construção concluída."""
        foto = self._foto_construcao()
        if self._historico and self._historico[self._posicao_hist] == foto:
            return
        del self._historico[self._posicao_hist + 1:]
        self._historico.append(foto)
        if len(self._historico) > self.LIMITE_HISTORICO:
            self._historico.pop(0)
        self._posicao_hist = len(self._historico) - 1

    def pode_desfazer(self) -> bool:
        return self._posicao_hist > 0

    def pode_refazer(self) -> bool:
        return self._posicao_hist < len(self._historico) - 1

    def desfazer(self):
        if self.pode_desfazer():
            self._posicao_hist -= 1
            self._aplicar_foto(self._historico[self._posicao_hist])

    def refazer(self):
        if self.pode_refazer():
            self._posicao_hist += 1
            self._aplicar_foto(self._historico[self._posicao_hist])

    def _aplicar_foto(self, foto: str):
        import json
        self.limpar_selecao_construcao()
        dados = json.loads(foto)
        if self.terreno:
            self.terreno.definir(TerrenoItem.de_lista(dados["t"]))
        if self.paredes:
            self.paredes.definir(ParedesItem.de_lista(dados["p"]))
        camada = self.camada_por_tipo("paredes")
        if camada:
            for porta in camada.itens():
                self.removeItem(porta)
            for d in dados["d"]:
                porta = PortaItem.de_dict(d)
                porta.setParentItem(camada)
                porta.aplicar_trava(camada.travada)
                porta.pular_animacao()
        self.marcar_modificada()
        self.camadas_mudaram.emit()

    # ============================================================ construção
    def definir_ferramenta(self, nome: str):
        self.ferramenta = nome
        self.ferramenta_mudou.emit(nome)

    def _pode_editar(self, tipo: str) -> bool:
        camada = self.camada_por_tipo(tipo)
        return camada is not None and not camada.travada and camada.isVisible()

    # --- terreno (tinta)
    def celulas_do_pincel(self, pos: QPointF):
        """Quadrados cobertos pelo pincel no modo grid (n×n centrado no quadrado do mouse)."""
        n = max(1, round(self.pincel))
        ci, cj = math.floor(pos.x() / CELULA), math.floor(pos.y() / CELULA)
        a = (n - 1) // 2
        return [(ci - a + di, cj - a + dj) for di in range(n) for dj in range(n)]

    def comecar_pincelada(self, pos: QPointF, apagar: bool = False) -> bool:
        if not (self.terreno and self._pode_editar("terreno")):
            return False
        material = None if apagar else self.material_chao
        if self.forma_pincel == "grid":
            self.terreno.iniciar_celulas(material, self.celulas_do_pincel(pos))
        else:
            self.terreno.iniciar_traco(material, self.raio_pincel(), pos)
        self._ultimo_ponto = pos
        return True

    def continuar_pincelada(self, pos: QPointF):
        if not self.terreno:
            return
        if self.forma_pincel == "grid":
            # Preenche o caminho todo, mesmo se o mouse correr
            a = getattr(self, "_ultimo_ponto", pos)
            passos = max(1, int(QLineF(a, pos).length() / (CELULA / 3)))
            celulas = []
            for k in range(passos + 1):
                p = a + (pos - a) * (k / passos)
                celulas += self.celulas_do_pincel(p)
            self.terreno.adicionar_celulas(celulas)
        else:
            self.terreno.estender_traco(pos)
        self._ultimo_ponto = pos

    def terminar_pincelada(self):
        self.marcar_modificada()
        self.registrar()

    def raio_pincel(self) -> float:
        return self.pincel * CELULA / 2  # pincel = diâmetro em metros

    def trocar_material_terreno(self, indice, material):
        if self.terreno and self._pode_editar("terreno"):
            self.terreno.trocar_material(indice, material)
            self.marcar_modificada()
            self.registrar()

    def remover_pincelada(self, indice):
        if self.terreno and self._pode_editar("terreno"):
            self.terreno.remover_operacao(indice)
            self.marcar_modificada()
            self.registrar()

    # --- borracha de paredes
    def apagar_paredes_em(self, pos: QPointF) -> bool:
        if self.paredes and self._pode_editar("paredes"):
            if self.paredes.apagar_no_circulo(pos, self.raio_pincel()):
                self.marcar_modificada()
                return True
        return False

    # --- paredes
    def adicionar_parede(self, a: QPointF, b: QPointF, material: str | None = None):
        if self.paredes and self._pode_editar("paredes"):
            if self.paredes.adicionar(a, b, material or self.material_parede):
                self.marcar_modificada()
                self.registrar()

    def remover_parede(self, uid):
        if self.paredes and self._pode_editar("paredes") and self.paredes.remover(uid):
            self.marcar_modificada()
            self.registrar()

    def trocar_material_parede(self, uid, material):
        if self.paredes and self._pode_editar("paredes"):
            self.paredes.trocar_material(uid, material)
            self.marcar_modificada()
            self.registrar()

    def parede_em(self, pos: QPointF):
        camada = self.camada_por_tipo("paredes")
        if self.paredes and camada and camada.isVisible():
            return self.paredes.segmento_em(pos)
        return None

    def criar_sala(self, a: QPointF, b: QPointF):
        """Chão no retângulo + quatro paredes em volta."""
        r = QRectF(a, b).normalized()
        if r.width() < 4 or r.height() < 4:
            return
        if self.terreno and self._pode_editar("terreno"):
            self.terreno.adicionar_retangulo(self.material_chao, r)
        if self.paredes and self._pode_editar("paredes"):
            cantos = [r.topLeft(), r.topRight(), r.bottomRight(), r.bottomLeft()]
            for k in range(4):
                self.paredes.adicionar(cantos[k], cantos[(k + 1) % 4], self.material_parede)
        self.marcar_modificada()
        self.registrar()

    # --- seleção de construção (arrastar com o mouse no modo Selecionar)
    def selecionar_construcao_em(self, area: QRectF, somar: bool = False):
        self.area_selecionada = QRectF(area)
        if not somar:
            self.limpar_selecao_construcao(avisar=False)
        camada_p = self.camada_por_tipo("paredes")
        if self.paredes and camada_p and camada_p.isVisible() and not camada_p.travada:
            for uid, seg in self.paredes.segmentos.items():
                if ParedesItem.caminho_segmento(seg).intersects(area):
                    self.paredes.selecionados.add(uid)
            self.paredes.update()
            # Portas: basta encostar na caixa
            for porta in camada_p.itens():
                if porta.isVisible() and \
                        porta.mapToScene(porta.shape()).intersects(area):
                    porta.setSelected(True)
        camada_t = self.camada_por_tipo("terreno")
        if self.terreno and camada_t and camada_t.isVisible() and not camada_t.travada:
            for i, (op, cam) in enumerate(zip(self.terreno.ops, self.terreno._caminhos)):
                if op["m"] is not None and cam.intersects(area):
                    self.terreno.selecionados.add(i)
            self.terreno.update()
        self._avisar_selecao()

    def limpar_selecao_construcao(self, avisar: bool = True):
        mudou = False
        if self.paredes and self.paredes.selecionados:
            self.paredes.selecionados.clear()
            self.paredes.update()
            mudou = True
        if self.terreno and self.terreno.selecionados:
            self.terreno.selecionados.clear()
            self.terreno.update()
            mudou = True
        if avisar and mudou:
            self._avisar_selecao()

    def tem_selecao_construcao(self) -> bool:
        return bool((self.paredes and self.paredes.selecionados) or
                    (self.terreno and self.terreno.selecionados))

    def contagem_selecao(self) -> tuple[int, int]:
        return (len(self.paredes.selecionados) if self.paredes else 0,
                len(self.terreno.selecionados) if self.terreno else 0)

    def _avisar_selecao(self):
        self.selecao_construcao_mudou.emit(*self.contagem_selecao())

    def apagar_selecao_construcao(self) -> bool:
        if not self.tem_selecao_construcao():
            return False
        if self.paredes:
            for uid in list(self.paredes.selecionados):
                self.paredes.segmentos.pop(uid, None)
            self.paredes.selecionados.clear()
            self.paredes._recalcular()
        if self.terreno and self.terreno.selecionados:
            for i in sorted(self.terreno.selecionados, reverse=True):
                if 0 <= i < len(self.terreno.ops):
                    self.terreno.remover_operacao(i)
            self.terreno.selecionados.clear()
        self.marcar_modificada()
        self.registrar()
        self._avisar_selecao()
        return True

    def apagar_terreno_na_area(self, area: QRectF):
        """Apaga só o pedaço de terreno dentro da área (como uma borracha retangular)."""
        if self.terreno and self._pode_editar("terreno"):
            self.terreno.adicionar_retangulo(None, area)
            self.terreno.selecionados.clear()
            self.marcar_modificada()
            self.registrar()
            self._avisar_selecao()

    # --- portas
    def encaixe_porta(self, pos: QPointF, largura_m: float):
        """
        Onde a porta gruda:
          1) numa parede perto do mouse (alinha no ângulo dela e abre o vão);
          2) senão, na linha do grid mais perto (um dos 4 lados do quadrado).
        Retorna (centro, angulo, uid_da_parede, t0, t1).
        """
        L = largura_m * CELULA
        uid = self.paredes.segmento_em(pos, ESPESSURA * 1.5) if self.paredes else None
        if uid:
            seg = self.paredes.segmentos[uid]
            a, b = QPointF(*seg["a"]), QPointF(*seg["b"])
            linha = QLineF(a, b)
            comp = max(1.0, linha.length())
            _, t = distancia_segmento(pos, a, b)
            passo = (CELULA / 2) / comp            # anda de meio em meio metro
            t = round(t / passo) * passo
            meio_vao = (L / 2) / comp
            t = max(meio_vao, min(1 - meio_vao, t)) if comp > L else 0.5
            return linha.pointAt(t), -linha.angle(), uid, t - meio_vao, t + meio_vao

        fx, fy = pos.x() / CELULA, pos.y() / CELULA
        horizontal = abs(fy - round(fy)) <= abs(fx - round(fx))
        ao_longo = fx if horizontal else fy
        # As pontas da porta caem nos cantos do grid (largura inteira) ou em meio metro
        if float(largura_m).is_integer():
            inicio = round(ao_longo - largura_m / 2)
        else:
            inicio = round((ao_longo - largura_m / 2) * 2) / 2
        meio = (inicio + largura_m / 2) * CELULA
        if horizontal:
            return QPointF(meio, round(fy) * CELULA), 0.0, None, 0, 0
        return QPointF(round(fx) * CELULA, meio), 90.0, None, 0, 0

    def colocar_porta(self, pos: QPointF) -> "PortaItem | None":
        """Coloca uma porta grudada numa parede ou num lado do quadrado do grid."""
        camada = self.camada_por_tipo("paredes")
        if not camada or not self._pode_editar("paredes"):
            return None
        porta = PortaItem(self.tipo_porta, self.largura_porta)
        centro, angulo, uid, t0, t1 = self.encaixe_porta(pos, self.largura_porta)
        self._abrir_vao(centro, angulo, self.largura_porta)
        porta.setRotation(angulo)
        porta.setParentItem(camada)
        porta.setPos(camada.mapFromScene(centro))
        zs = [i.zValue() for i in camada.itens() if i is not porta]
        porta.setZValue((max(zs) + 1) if zs else 0)
        porta.pular_animacao()
        self.marcar_modificada()
        self.camadas_mudaram.emit()
        self.registrar()
        return porta

    def _abrir_vao(self, centro: QPointF, angulo: float, largura_m: float):
        """Tira as paredes de baixo da porta (todas, mesmo se tiver parede dupla)."""
        if not self.paredes:
            return
        meio = largura_m * CELULA / 2
        a = math.radians(angulo)
        dx, dy = math.cos(a) * meio, math.sin(a) * meio
        self.paredes.cortar_ao_longo(QPointF(centro.x() - dx, centro.y() - dy),
                                     QPointF(centro.x() + dx, centro.y() + dy))

    def _fechar_vao(self, porta):
        """(v0.60.1) Porta apagada: a parede dos dois lados fecha o vão (mesmo material), virando uma
        parede só. Porta solta (sem parede do lado) não deixa parede nenhuma."""
        if not self.paredes:
            return
        try:
            p0, p1 = porta.pontas_cena()
        except RuntimeError:
            return
        comp = QLineF(p0, p1).length()
        if comp < 1:
            return
        ux, uy = (p1.x() - p0.x()) / comp, (p1.y() - p0.y()) / comp

        def vizinha(p):
            for uid, s in self.paredes.segmentos.items():
                a, b = QPointF(*s["a"]), QPointF(*s["b"])
                sl = QLineF(a, b).length()
                if sl < 1 or abs(((b.x() - a.x()) * uy - (b.y() - a.y()) * ux) / sl) > 0.05:
                    continue   # não está alinhada com a porta
                for ponta, outra in ((a, b), (b, a)):
                    if QLineF(ponta, p).length() < 3:
                        return uid, s, outra
            return None
        va, vb = vizinha(p0), vizinha(p1)
        if not va and not vb:
            return
        mat = (va or vb)[1]["m"]
        ini = va[2] if va and va[1]["m"] == mat else p0
        fim = vb[2] if vb and vb[1]["m"] == mat else p1
        for v in (va, vb):
            if v and v[1]["m"] == mat:
                self.paredes.segmentos.pop(v[0], None)
        self.paredes.adicionar(ini, fim, mat)

    def porta_perto(self, pos: QPointF, tolerancia: float | None = None):
        """(v0.60.1) A porta mais perto do clique (a porta é fininha e no 3D ela aparece mais "alta" que o
        chão: o botão direito errava ela)."""
        from .construcao import distancia_segmento
        tol = tolerancia if tolerancia is not None else CELULA * 0.6
        melhor, menor = None, tol
        camada = self.camada_por_tipo("paredes")
        if camada is None or not camada.isVisible():
            return None
        for porta in camada.itens():
            if not isinstance(porta, PortaItem) or not porta.isVisible():
                continue
            a, b = porta.pontas_cena()
            d, _ = distancia_segmento(pos, a, b)
            if d < menor:
                melhor, menor = porta, d
        return melhor

    def encaixar_porta_existente(self, porta):
        """Depois de arrastar uma porta: gruda de novo (e abre vão se caiu numa parede)."""
        centro, angulo, uid, t0, t1 = self.encaixe_porta(porta.scenePos(), porta.largura_m)
        self._abrir_vao(centro, angulo, porta.largura_m)
        porta.setRotation(angulo)
        porta.setPos(porta.parentItem().mapFromScene(centro))
        self.marcar_modificada()

    def porta_em(self, pos: QPointF):
        for item in self.items(pos):
            if isinstance(item, PortaItem) and item.isVisible():
                return item
        return None

    def marcar_modificada(self, valor: bool = True):
        if valor:
            self.mesa_mudou.emit()
        if self.modificada != valor:
            self.modificada = valor
            self.modificacao_mudou.emit(valor)
