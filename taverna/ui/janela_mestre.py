"""
Janela principal do Mestre.

Layout estilo Photoshop:
  - Menus no topo (Arquivo, Editar, Mesa, Exibir)
  - Barra de ferramentas logo abaixo
  - A mesa no centro
  - Painéis de Camadas e Propriedades à direita
  - Barra de status embaixo (posição em metros, zoom, snap)
"""

import os
import re

from PyQt6.QtCore import QPointF, Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtCore import QSettings, QStandardPaths
from PyQt6.QtGui import QActionGroup
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import (QDockWidget, QFileDialog, QHBoxLayout, QInputDialog,
                             QLabel, QListWidget, QListWidgetItem, QMainWindow, QMenu,
                             QMessageBox, QPushButton, QSlider, QStackedWidget, QTabBar,
                             QToolButton, QVBoxLayout, QWidget)

from ..config import APP_NOME, APP_VERSAO, CELULA, EXTENSAO_CENA, fmt_m
from ..mesa.arquivo import (carregar_dados_na_cena, dados_da_cena, ler_aventura,
                            ler_cabecalho, salvar_aventura)
from ..temas import TEMAS, tema as dados_tema
from ..mesa.cena import MesaCena
from ..mesa import materiais
from ..mesa.mapa import MapaItem
from ..mesa.luzes import LuzItem
from ..mesa.portas import TIPOS_PORTA, PortaItem
from ..mesa.token import TokenItem
from ..mesa.visao import MesaVisao
from ..rede.protocolo import PORTA_PADRAO, mesmo_nome
from ..rede.servidor import ServidorMestre
from .dialogos import DialogoAbrirTaverna, DialogoNovaAventura, DialogoToken
from .painel_construcao import BarraConstrucao
from .painel_camadas import PainelCamadas
from .painel_propriedades import PainelPropriedades
from .tela_inicial import TelaInicial
from .icones import icone, pixmap_icone
from .acabamento import ICONES_GLOBAIS, com_icone, iconizar, iconizar_menu, item_com_icone
from .tema import guardar_tema_preferido, tema_preferido, rolavel, gerar_qss, icone_app

FILTRO_CENA = f"Aventura do Taverna (*{EXTENSAO_CENA})"
FILTRO_IMAGEM = "Imagens (*.png *.jpg *.jpeg *.webp *.bmp *.gif)"


class JanelaMestre(QMainWindow):
    def __init__(self, lancador=None):
        super().__init__()
        self.lancador = lancador   # (v0.49) aberto pelo launcher: "voltar pro início" volta pra ele
        self.caminho_cena: str | None = None
        self.setWindowIcon(icone_app())
        self.resize(1400, 860)

        self.cena = MesaCena(self)      # a aba que o mestre está vendo/editando
        self.cenas = [self.cena]        # todas as abas (cenários) da aventura
        self.indice_ao_vivo = 0         # a aba que os players estão vendo
        self.servidor = ServidorMestre(self.cena, self)
        self.config = QSettings("Taverna", "Mestre")
        self.visao = MesaVisao(self.cena)

        # Tela inicial (muro de pedra) e a mesa, empilhadas
        self.tela_inicial = TelaInicial("Mestre", [
            ("Nova sessão", "nova"),
            ("Continuar sessão", "continuar"),
            ("Abrir sessão…", "abrir"),
            ("Sair", "sair"),
        ], tema_inicial=tema_preferido())
        self.tela_inicial.tema_escolhido.connect(self._tema_da_tela_inicial)
        self.tela_inicial.escolhido.connect(self._escolha_inicial)
        self.pilha = QStackedWidget()
        self.pilha.addWidget(self.tela_inicial)
        self.area_mesa = self._criar_area_mesa()
        self.pilha.addWidget(self.area_mesa)
        self.setCentralWidget(self.pilha)

        self._criar_paineis()
        self._criar_acoes()
        self._criar_menus()
        self._criar_barra()
        self._criar_status()
        self._conectar()
        from .atlas_visao import CamadaAtlas
        self.camada_atlas = CamadaAtlas(self.visao, self)   # 🌍 cidade e mundo por cima da mesa (v0.62)
        from ..rede.atlas_rede import AtlasServidor
        self.atlas_rede = AtlasServidor(self.servidor, self)   # …e pros jogadores, só o revelado (v0.64)
        self.servidor.atlas_rede = self.atlas_rede
        self._registrar_cena(self.cena)
        self._ligar_cena(self.cena)
        self._recarregar_abas()
        self._atualizar_titulo()
        self.mostrar_inicio()
        iconizar(self)   # emojis dos painéis, botões e menus → ícones do tema
        # Salvamento automático (a cada 3 minutos, se mudou algo)
        self._timer_auto = QTimer(self)
        self._timer_auto.setInterval(3 * 60 * 1000)
        self._timer_auto.timeout.connect(self.salvar_automatico)
        self._timer_auto.start()

    # ================================================================ abas (cenários)
    def _criar_area_mesa(self):
        """Barra de abas em cima + a mesa embaixo."""
        area = QWidget()
        lay = QVBoxLayout(area)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        linha = QWidget()
        linha.setObjectName("linha_abas")
        h = QHBoxLayout(linha)
        h.setContentsMargins(6, 4, 6, 0)
        h.setSpacing(6)
        self.abas = QTabBar()
        self.abas.setMovable(True)
        self.abas.setExpanding(False)
        self.abas.setDocumentMode(True)
        self.abas.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.abas.currentChanged.connect(self._aba_clicada)
        self.abas.tabMoved.connect(self._aba_movida)
        self.abas.customContextMenuRequested.connect(self._menu_aba)
        self.abas.tabBarDoubleClicked.connect(self.renomear_aba)
        self.btn_nova_aba = QToolButton()
        self.btn_nova_aba.setText("＋ Cenário")
        self.btn_nova_aba.setToolTip("Criar uma aba nova (outro cenário: caverna, floresta...)")
        self.btn_nova_aba.clicked.connect(self.nova_aba)
        self.btn_ao_vivo = QPushButton()
        self.btn_ao_vivo.clicked.connect(lambda: self.mostrar_aba_pros_players(
            self.cenas.index(self.cena)))
        # (v0.50) 👁 ver a mesa como um jogador vê
        self.btn_visao_jogador = QPushButton("👁 Visão dos jogadores")
        self.btn_visao_jogador.setCheckable(True)
        self.btn_visao_jogador.setToolTip("Ver a mesa EXATAMENTE como está na tela de um jogador\n"
                                          "(névoa, andar dele, o que ele pode ver). Clique de novo pra voltar.")
        self.btn_visao_jogador.toggled.connect(self.alternar_visao_jogador)
        h.addWidget(self.abas, 1)
        h.addWidget(self.btn_nova_aba)
        h.addWidget(self.btn_visao_jogador)
        h.addWidget(self.btn_ao_vivo)
        lay.addWidget(linha)
        from PyQt6.QtWidgets import QStackedWidget
        self.pilha_mesa = QStackedWidget()
        self.pilha_mesa.addWidget(self.visao)
        self.painel_visao_jogador = None
        lay.addWidget(self.pilha_mesa, 1)
        return area

    def alternar_visao_jogador(self, ligar: bool):
        """👁 Liga/desliga a mesa vista como um jogador vê (só pra olhar)."""
        if ligar:
            if self.painel_visao_jogador is None:
                from .visao_jogador import PainelVisaoJogador
                self.painel_visao_jogador = PainelVisaoJogador(
                    self.servidor, lambda: self.btn_visao_jogador.setChecked(False), self)
                self.pilha_mesa.addWidget(self.painel_visao_jogador)
            self.painel_visao_jogador.ligar()
            self.pilha_mesa.setCurrentWidget(self.painel_visao_jogador)
            self.statusBar().showMessage("👁 Você está vendo a mesa como o jogador vê. Pra editar, volte pra sua mesa.", 6000)
        else:
            if self.painel_visao_jogador is not None:
                self.painel_visao_jogador.desligar()
            self.pilha_mesa.setCurrentWidget(self.visao)
            self.visao.setFocus()

    def _recarregar_abas(self):
        # A aba ao vivo é sempre a que o servidor está transmitindo
        if self.servidor.cena in self.cenas:
            self.indice_ao_vivo = self.cenas.index(self.servidor.cena)
        self.abas.blockSignals(True)
        while self.abas.count():
            self.abas.removeTab(0)
        from .tema import tema_atual
        vivo = QIcon(pixmap_icone("ao_vivo", tema_atual()["perigo"], 16))
        from ..mesa.andares import nome_andar
        for i, c in enumerate(self.cenas):
            no_ar = self.servidor.e_ao_vivo(c)   # (🏢 o prédio ao vivo: todos os andares dele)
            self.abas.addTab(c.nome_aba + (f" · {nome_andar(c.andar)}" if getattr(c, "predio", None) else ""))
            if no_ar:
                self.abas.setTabIcon(i, vivo)
            self.abas.setTabToolTip(i, ("AO VIVO: cada jogador vê o andar onde está o token dele"
                                        if getattr(c, "predio", None) else "AO VIVO: é o que os jogadores estão vendo")
                                    if no_ar else "Só você vê esta aba. Botão direito: opções")
        self.abas.setCurrentIndex(self.cenas.index(self.cena))
        self.abas.blockSignals(False)
        ao_vivo = self.servidor.e_ao_vivo(self.cena)
        com_icone(self.btn_ao_vivo, "🔴 Esta aba está ao vivo" if ao_vivo
                  else "📡 Mostrar esta aba pros jogadores")
        self.btn_ao_vivo.setEnabled(not ao_vivo)
        self.btn_ao_vivo.setObjectName("" if ao_vivo else "primario")
        self.btn_ao_vivo.style().unpolish(self.btn_ao_vivo)
        self.btn_ao_vivo.style().polish(self.btn_ao_vivo)

    def _nova_cena_vazia(self, nome: str):
        cena = MesaCena(self)
        cena.nome_aba = nome or "Cenário"
        cena.nome_aventura = self.cena.nome_aventura
        cena.definir_tema(self.cena.tema)
        cena.marcar_modificada(False)
        return cena

    def _ficar_so_com_a_cena_atual(self):
        """Antes de abrir/criar outra aventura: sobra só a aba que está na tela."""
        for c in self.cenas:
            if c is not self.cena:
                c.deleteLater()
        self.cenas = [self.cena]
        self.indice_ao_vivo = 0
        self.servidor.definir_cena(self.cena)

    def _aba_clicada(self, indice):
        if 0 <= indice < len(self.cenas):
            self.trocar_aba(indice)

    def trocar_aba(self, indice, manter_camera: bool = False):
        """manter_camera (v0.62): quem chamou já vai pôr a câmera (descendo da cidade pra uma aba)."""
        nova = self.cenas[indice]
        antiga = self.cena
        if nova is antiga:
            return
        antiga._camera = (self.visao.centro_da_visao(), self.visao.escala)
        antiga.clearSelection()
        antiga.limpar_selecao_construcao()
        self._desligar_cena(antiga)
        self.painel_props.definir_cena(nova)
        self.painel_camadas.definir_cena(nova)
        self.barra_construcao.definir_cena(nova)
        self.cena = nova
        self.visao.setScene(nova)
        self._ligar_cena(nova)
        self.visao.atualizar_modo()
        camera = getattr(nova, "_camera", None)
        if manter_camera:
            nova.definir_escala(self.visao.escala)
        elif camera:
            self.visao.definir_zoom(camera[1])
            self.visao.centerOn(camera[0])
        else:
            nova.definir_escala(self.visao.escala)
            QTimer.singleShot(0, self.visao.enquadrar_tudo)
        self.slider_grid.blockSignals(True)
        self.slider_grid.setValue(int(nova.opacidade_grid * 100))
        self.slider_grid.blockSignals(False)
        self._snap_mudou(nova.snap_ativo)
        self.a_nevoa.blockSignals(True)
        self.a_nevoa.setChecked(nova.nevoa_ativa)
        self.a_nevoa.blockSignals(False)
        self.acoes_ambiente.get(nova.luz_ambiente, self.acoes_ambiente["dia"]).setChecked(True)
        if nova is not self.servidor.cena:
            self.servidor.cursor_mestre(None, None)
        self._recarregar_abas()
        self._atualizar_titulo()
        if getattr(self, "camada_atlas", None) is not None:
            self.camada_atlas.aba_mudou()

    def nova_aba(self):
        nome, ok = QInputDialog.getText(self, "Novo cenário", "Nome do cenário (aba):",
                                        text=f"Cenário {len(self.cenas) + 1}")
        if not ok or not nome.strip():
            return
        cena = self._nova_cena_vazia(nome.strip())
        self._registrar_cena(cena)
        self.cenas.append(cena)
        cena.marcar_modificada()
        self.trocar_aba(len(self.cenas) - 1)

    def renomear_aba(self, indice):
        if not 0 <= indice < len(self.cenas):
            return
        cena = self.cenas[indice]
        nome, ok = QInputDialog.getText(self, "Renomear cenário", "Nome:", text=cena.nome_aba)
        if ok and nome.strip():
            cena.nome_aba = nome.strip()
            cena.marcar_modificada()
            cena.mesa_mudou.emit()
            self._recarregar_abas()
            self._atualizar_titulo()

    def duplicar_aba(self, indice):
        original = self.cenas[indice]
        dados = dados_da_cena(original)
        import uuid
        dados["id"] = uuid.uuid4().hex
        dados["nome"] = f"{original.nome_aba} (cópia)"
        for camada in dados["camadas"]:
            for item in camada.get("itens", []):
                item["id"] = uuid.uuid4().hex   # itens da cópia são outros itens
        cena = self._nova_cena_vazia(dados["nome"])
        carregar_dados_na_cena(cena, dados, self.cena.tema, self.cena.nome_aventura)
        self._registrar_cena(cena)
        self.cenas.insert(indice + 1, cena)
        cena.marcar_modificada()
        self.trocar_aba(indice + 1)

    def excluir_aba(self, indice):
        if len(self.cenas) <= 1:
            QMessageBox.information(self, "Excluir cenário", "A aventura precisa de pelo menos uma aba.")
            return
        cena = self.cenas[indice]
        r = QMessageBox.question(self, "Excluir cenário",
                                 f"Excluir a aba “{cena.nome_aba}” e tudo que tem nela?\n"
                                 "(Isso não dá pra desfazer.)")
        if r != QMessageBox.StandardButton.Yes:
            return
        ao_vivo = self.cenas[self.indice_ao_vivo]
        if cena is self.cena:
            self.trocar_aba(indice - 1 if indice > 0 else 1)
        self.cenas.remove(cena)
        if cena is ao_vivo:
            ao_vivo = self.cenas[0]
            self.servidor.definir_cena(ao_vivo)
        self.indice_ao_vivo = self.cenas.index(ao_vivo)
        self._atualizar_andares_ao_vivo()   # (se era um andar do prédio ao vivo, sai do ar)
        cena.deleteLater()
        self.cena.marcar_modificada()
        self._recarregar_abas()

    # ================================================================ 🏢 andares (v0.46)
    def _atualizar_andares_ao_vivo(self):
        """O prédio da aba ao vivo inteiro fica no ar (cada jogador vê o andar do token dele)."""
        from ..mesa.andares import do_predio
        self.servidor.definir_andares(do_predio(self.cenas, self.servidor.cena))

    def novo_andar(self, indice, delta):
        """Cria um andar acima (+1) ou abaixo (-1) do da aba, no mesmo prédio."""
        from ..mesa.andares import andar_vizinho, garantir_predio, nome_andar
        base = self.cenas[indice]
        garantir_predio(base)
        existente = andar_vizinho(self.cenas, base, delta)
        if existente is not None:
            self.trocar_aba(self.cenas.index(existente))
            return existente
        cena = self._nova_cena_vazia(base.nome_aba)
        cena.predio, cena.andar = base.predio, base.andar + delta
        cena.luz_ambiente = base.luz_ambiente
        cena.opacidade_grid = base.opacidade_grid
        cena.definir_snap(base.snap_ativo)
        self._copiar_estrutura(base, cena)   # (v0.46.2) o andar novo já vem com as paredes e o chão do de baixo
        self._registrar_cena(cena)
        self.cenas.insert(indice + 1 if delta > 0 else indice, cena)
        cena.marcar_modificada()
        base.marcar_modificada()
        self._atualizar_andares_ao_vivo()
        self.trocar_aba(self.cenas.index(cena))
        self.statusBar().showMessage(f"🏢 {nome_andar(cena.andar)} criado com as paredes e o chão do "
                                     f"{nome_andar(base.andar)}. Ligue os andares com uma ESCADA "
                                     "(Objetos → Escada; botão direito nela → Ligar ao andar…).", 9000)
        return cena

    @staticmethod
    def _copiar_estrutura(base, cena):
        """Clona SÓ o chão (terreno) e as paredes (com portas/janelas) de um andar pro outro, no mesmo lugar.
        Objetos, tokens, luzes, mapa, áreas… não vêm (pedido do Manel: "geralmente o andar de cima é igual")."""
        import uuid
        from ..mesa.arquivo import CLASSES
        from ..mesa.construcao import ParedesItem, TerrenoItem
        if base.terreno is not None and cena.terreno is not None:
            cena.terreno.definir(TerrenoItem.de_lista(base.terreno.para_lista()))
        if base.paredes is not None and cena.paredes is not None:
            cena.paredes.definir(ParedesItem.de_lista(base.paredes.para_lista()))
        cam_b, cam_n = base.camada_por_tipo("paredes"), cena.camada_por_tipo("paredes")
        if cam_b is None or cam_n is None:
            return
        for item in cam_b.itens():   # portas (e o que mais morar na camada de paredes)
            d = item.para_dict()
            classe = CLASSES.get(d.get("classe"))
            if classe is None:
                continue
            d["id"] = uuid.uuid4().hex
            classe.de_dict(d).setParentItem(cam_n)

    def ligar_escada(self, escada, delta):
        """Põe a escada correspondente no andar de cima/baixo (no mesmo lugar) e liga as duas."""
        from ..mesa.andares import andar_vizinho, garantir_predio, nome_andar
        base = escada.scene()
        if base is None:
            return
        garantir_predio(base)
        destino = andar_vizinho(self.cenas, base, delta) or self.novo_andar(self.cenas.index(base), delta)
        if destino is None:
            return
        self._ligar_escadas(escada, destino)

    # ---- (v0.48) a escada pode levar pra QUALQUER cenário (aba), não só pro andar de cima/baixo
    @staticmethod
    def _escadas_de(cena) -> list:
        from ..mesa.props import PropItem
        return [i for i in cena.items() if isinstance(i, PropItem) and i.tipo == "escada"]

    def _ponta_de(self, escada):
        """(cena, escada) do outro lado da ligação, ou (None, None)."""
        from ..mesa.andares import do_predio
        lig = escada.ligacao or {}
        base = escada.scene()
        if not lig or base is None:
            return None, None
        cena = next((c for c in do_predio(self.cenas, base) if c.andar == lig.get("andar")), None)
        return cena, (cena.item_por_id(str(lig.get("id", ""))) if cena is not None else None)

    def desligar_escada(self, escada):
        _cena, outra = self._ponta_de(escada)
        if outra is not None and (outra.ligacao or {}).get("id") == escada.uid:
            outra.ligacao = None
            outra._mudou()
        escada.ligacao = None
        escada._mudou()

    def destinos_escada(self, escada) -> list:
        """[(rótulo, destino)] pra janela/menu: destino = +1 / -1 (andar novo ou vizinho) ou uma cena."""
        from ..mesa.andares import nome_andar
        base = escada.scene()
        saida = [("⬆ Andar de cima", +1), ("⬇ Andar de baixo", -1)]
        for i, c in enumerate(self.cenas):
            if c is base:
                continue
            rot = getattr(c, "nome_aba", "") or f"Cenário {i + 1}"
            if getattr(c, "predio", None):
                rot += f"  ({nome_andar(c.andar)})"
            saida.append((f"🗺 {rot}", c))
        return saida

    def ligar_escada_cena(self, escada, destino):
        """Liga a escada a um cenário (aba) qualquer. O cenário entra no mesmo prédio (num andar livre),
        porque é o prédio que vai pro ar inteiro e manda cada jogador pro andar do token dele."""
        from ..mesa.andares import do_predio, garantir_predio
        base = escada.scene()
        if base is None or destino is None or destino is base:
            return
        garantir_predio(base)
        if getattr(destino, "predio", None) != base.predio:
            usados = {c.andar for c in do_predio(self.cenas, base)}
            n = base.andar + 1
            while n in usados:
                n += 1
            destino.predio, destino.andar = base.predio, n
        self._ligar_escadas(escada, destino)
        self._recarregar_abas()

    def _ligar_escadas(self, escada, destino):
        """Liga `escada` a uma escada do `destino`: uma solta que já esteja lá ou uma nova no mesmo lugar."""
        from ..mesa.andares import nome_andar
        base = escada.scene()
        self.desligar_escada(escada)
        outra = next((e for e in self._escadas_de(destino) if not e.ligacao), None)
        if outra is None:
            outra = destino.colocar_prop("escada", escada.centro_cena())
            outra.angulo = escada.angulo
            outra._atualizar_origem()
        outra.trancado = escada.trancado
        escada.ligacao = {"andar": destino.andar, "id": outra.uid}
        outra.ligacao = {"andar": base.andar, "id": escada.uid}
        for c in (base, destino):
            c.marcar_modificada()
            c.mesa_mudou.emit()
        self._atualizar_andares_ao_vivo()
        self.statusBar().showMessage(f"🏢 Escada ligada: {nome_andar(base.andar)} ↔ {nome_andar(destino.andar)}. "
                                     "O jogador dá duplo clique nela (perto) pra subir/descer.", 8000)

    def aplicar_destino_escada(self, escada, destino):
        if destino is None:
            self.desligar_escada(escada)
        elif destino in (+1, -1):
            self.ligar_escada(escada, destino)
        else:
            self.ligar_escada_cena(escada, destino)

    def liberar_escada(self, escada, liberar: bool):
        """Permissão do mestre: escada liberada (o jogador sobe/desce) ou bloqueada. Vale pras duas pontas."""
        from ..mesa.andares import do_predio
        pontas = [escada]
        lig = escada.ligacao or {}
        base = escada.scene()
        if base is not None and lig:
            outra_cena = next((c for c in do_predio(self.cenas, base) if c.andar == lig.get("andar")), None)
            outra = outra_cena.item_por_id(str(lig.get("id", ""))) if outra_cena is not None else None
            if outra is not None:
                pontas.append(outra)
        for e in pontas:
            e.trancado = not liberar
            e._mudou()
            e.update()
        self.painel_props.atualizar()
        self.painel_camadas.recarregar()
        self.statusBar().showMessage("✅ Escada liberada: os jogadores podem subir/descer." if liberar else
                                     "🚫 Escada bloqueada: os jogadores não conseguem usar.", 5000)

    def levar_token_pro_andar(self, token, destino):
        from ..mesa.andares import nome_andar
        novo = self.servidor.mover_token_de_andar(token, destino)
        self.statusBar().showMessage(f"🏢 {novo.nome} foi pro {nome_andar(destino.andar)}.", 5000)

    def mostrar_aba_pros_players(self, indice):
        self.indice_ao_vivo = indice
        self.servidor.definir_cena(self.cenas[indice])
        self._atualizar_andares_ao_vivo()
        self.cena.marcar_modificada()
        self._recarregar_abas()
        self._atualizar_jogadores()
        self.statusBar().showMessage(
            f"Os jogadores agora estão vendo: {self.cenas[indice].nome_aba}", 5000)

    def _aba_movida(self, de, para):
        cena = self.cenas.pop(de)
        self.cenas.insert(para, cena)
        ao_vivo = self.servidor.cena
        self.indice_ao_vivo = self.cenas.index(ao_vivo)
        self.cena.marcar_modificada()
        self._recarregar_abas()

    def _menu_aba(self, pos):
        indice = self.abas.tabAt(pos)
        menu = QMenu(self)
        if indice >= 0:
            if not self.servidor.e_ao_vivo(self.cenas[indice]):
                menu.addAction("📡  Mostrar pros jogadores",
                               lambda: self.mostrar_aba_pros_players(indice))
            menu.addAction("🏢  Novo andar acima", lambda: self.novo_andar(indice, +1))
            menu.addAction("🏢  Novo andar abaixo", lambda: self.novo_andar(indice, -1))
            menu.addSeparator()
            menu.addAction("Renomear…", lambda: self.renomear_aba(indice))
            menu.addAction("Duplicar", lambda: self.duplicar_aba(indice))
            menu.addSeparator()
            menu.addAction("Excluir…", lambda: self.excluir_aba(indice))
            menu.addSeparator()
        menu.addAction("＋  Novo cenário…", self.nova_aba)
        iconizar_menu(menu).exec(self.abas.mapToGlobal(pos))

    # ================================================================ tela inicial
    def _ultima_cena(self) -> str | None:
        caminho = self.config.value("ultima_cena", "")
        return caminho if caminho and os.path.isfile(caminho) else None

    def mostrar_inicio(self):
        if getattr(self, "btn_visao_jogador", None) is not None and self.btn_visao_jogador.isChecked():
            self.btn_visao_jogador.setChecked(False)
        ultima = self._ultima_cena()
        self.tela_inicial.botoes["continuar"].setEnabled(bool(ultima))
        texto = ""
        if ultima:
            try:
                cab = ler_cabecalho(ultima)
                nome = cab["aventura"] or os.path.splitext(os.path.basename(ultima))[0]
                texto = f"Última aventura: {nome}  ·  {dados_tema(cab['tema'])['nome']}"
            except (OSError, ValueError):
                texto = f"Última aventura: {os.path.basename(ultima)}"
        self.tela_inicial.info.setText(texto)
        for widget in self._widgets_da_mesa():
            widget.hide()
        # Painéis retráteis: lembra se estavam abertos e esconde
        retrateis = (self.dock_combate, self.dock_dados, self.dock_chat, self.dock_historico, self.dock_objetos)
        self._retrateis_abertos = [d for d in retrateis if d.isVisible()]
        for d in retrateis:
            d.hide()
        for acao in self.findChildren(QAction):
            acao.setEnabled(False)
        if getattr(self, "a_atalhos", None) is not None:   # (v0.58) o F1 funciona em qualquer tela
            self.a_atalhos.setEnabled(True)
        if getattr(self, "a_reportar", None) is not None:
            self.a_reportar.setEnabled(True)
        self.pilha.setCurrentWidget(self.tela_inicial)
        self._aplicar_tema(self.tela_inicial.tema)
        self.setWindowTitle(f"{APP_NOME} Mestre")
        if self.lancador is not None:
            self.lancador.voltar(self)

    def _aplicar_tema(self, chave):
        QApplication.instance().setStyleSheet(gerar_qss(chave))
        if hasattr(self, "icones"):
            self.icones.atualizar()
        ICONES_GLOBAIS.atualizar()
        if hasattr(self, "abas"):
            self._recarregar_abas()   # ícone "ao vivo" na cor do tema novo

    def _tema_da_tela_inicial(self, chave):
        guardar_tema_preferido(chave)
        self._aplicar_tema(chave)

    def mostrar_mesa(self):
        for acao in self.findChildren(QAction):
            acao.setEnabled(True)
        for widget in self._widgets_da_mesa():
            widget.show()
        for d in getattr(self, "_retrateis_abertos", []):
            d.show()
        self._aplicar_tema(self.cena.tema)
        if not getattr(self, "_docks_ajustados", False):
            # primeira vez que a mesa aparece: divide a coluna da direita num tamanho bom
            self._docks_ajustados = True
            QTimer.singleShot(0, lambda: self.resizeDocks(
                [self.dock_camadas, self.dock_props, self.dock_jogadores], [230, 380, 120],
                Qt.Orientation.Vertical))
        self.pilha.setCurrentWidget(self.area_mesa)
        self.visao.setFocus()
        self._atualizar_titulo()
        from .dicas import agendar_primeira_vez
        agendar_primeira_vez(self, "mestre")   # 💡 (v0.66) dicas de primeiro acesso, uma vez só

    def _widgets_da_mesa(self):
        return (self.menuBar(), self.barra, self.statusBar(), self.dock_camadas,
                self.dock_props, self.dock_jogadores, self.barra_construcao,
                self.dock_info)

    def _escolha_inicial(self, chave):
        if chave == "nova":
            if self.nova_cena():
                self.mostrar_mesa()
        elif chave == "continuar":
            if self.abrir_cena(self._ultima_cena()):
                self.mostrar_mesa()
        elif chave == "abrir":
            if self.abrir_cena():
                self.mostrar_mesa()
        elif chave == "sair":
            self.close()

    def fechar_sessao(self):
        if self.servidor.aberto and self.servidor.nomes():
            r = QMessageBox.question(self, "Fechar sessão",
                                     "Tem jogador conectado. A taverna vai fechar. Continuar?")
            if r != QMessageBox.StandardButton.Yes:
                return
        if not self._pode_descartar():
            return
        self._fechar_internet()
        self.servidor.fechar()
        self._atualizar_jogadores()
        self.painel_props.soltar_referencias()
        self._ficar_so_com_a_cena_atual()
        self.cena.criar_camadas_padrao()
        self.cena.nome_aba = "Cenário 1"
        self._recarregar_abas()
        self.cena.marcar_modificada(False)
        self.caminho_cena = None
        self.mostrar_inicio()

    # ================================================================ montagem
    def _criar_paineis(self):
        # Barra de construção vertical, à esquerda (estilo Photoshop)
        self.barra_construcao = BarraConstrucao(self.cena, self)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.barra_construcao)
        self.barra_construcao.dica.connect(
            lambda t: self.statusBar().showMessage(t, 8000) if t else None)

        self.painel_camadas = PainelCamadas(self.cena, self._editar_item_da_lista)
        self.dock_camadas = QDockWidget("CAMADAS", self)
        self.dock_camadas.setObjectName("dock_camadas")
        self.dock_camadas.setWidget(self.painel_camadas)
        self.dock_camadas.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable
                                      | QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_camadas)

        self.painel_props = PainelPropriedades(self.cena, self.editar_token)
        self.dock_props = QDockWidget("PROPRIEDADES", self)
        self.dock_props.setObjectName("dock_props")
        self.dock_props.setWidget(rolavel(self.painel_props))
        self.dock_props.setFeatures(self.dock_camadas.features())
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_props)
        self.lista_jogadores = QListWidget()
        self.lista_jogadores.setToolTip("Quem está conectado e qual token controla")
        self.dock_jogadores = QDockWidget("JOGADORES", self)
        self.dock_jogadores.setObjectName("dock_jogadores")
        self.dock_jogadores.setWidget(self.lista_jogadores)
        self.dock_jogadores.setFeatures(self.dock_camadas.features())
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_jogadores)
        # --- Etapa 6: informações, combate e dados
        from .painel_combate import PainelCombateMestre
        from .painel_dados import PainelDados
        from .painel_info import PainelInfoMestre
        self.painel_info = PainelInfoMestre(self.cena, self._nomes_pro_painel)
        self.dock_info = QDockWidget("INFORMAÇÕES", self)
        self.dock_info.setObjectName("dock_info")
        self.dock_info.setWidget(rolavel(self.painel_info))
        self.dock_info.setFeatures(self.dock_camadas.features())
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_info)
        self.tabifyDockWidget(self.dock_props, self.dock_info)
        self.dock_props.raise_()

        self.painel_combate = PainelCombateMestre(self.servidor)
        self.painel_combate.centralizar_token.connect(self._mostrar_token)
        self.painel_combate.girar_todos.connect(self._giro_todos)
        self.dock_combate = QDockWidget("COMBATE", self)
        self.dock_combate.setObjectName("dock_combate")
        self.dock_combate.setWidget(rolavel(self.painel_combate))
        self.dock_combate.setFeatures(self.dock_camadas.features())
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_combate)

        self.painel_dados = PainelDados(mestre=True)
        self.painel_dados.pedir_rolagem.connect(self._rolar_mestre)
        self.painel_dados.pedir_pronta.connect(lambda e, m, p: self._rolar_mestre(e, p, m))
        # (v0.46.1) a rolagem só entra no histórico/chat quando o dado PARA (ver _rolagem_na_mesa)
        # Dados e Chat em painéis separados (pedido do Manel, v0.31.1): cada um com seu botão na barra
        self.dock_dados = QDockWidget("DADOS", self)
        self.dock_dados.setObjectName("dock_dados")
        self.dock_dados.setWidget(rolavel(self.painel_dados))
        self.dock_dados.setFeatures(self.dock_camadas.features())
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_dados)
        from .painel_chat import PainelChat
        self.painel_chat = PainelChat(mestre=True, meu_nome="Mestre")
        self.painel_chat.enviar.connect(self._chat_mestre)
        self.servidor.chat.connect(self.painel_chat.adicionar)
        self.servidor.jogadores_mudaram.connect(self.painel_chat.definir_destinos)
        self.painel_chat.nova_mensagem.connect(self._aviso_chat)
        self.dock_chat = QDockWidget("CHAT", self)
        self.dock_chat.setObjectName("dock_chat")
        self.dock_chat.setWidget(self.painel_chat)
        self.dock_chat.visibilityChanged.connect(lambda _v: self._zerar_chat())
        self.dock_chat.setFeatures(self.dock_camadas.features())
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_chat)
        from .painel_historico import PainelHistorico
        self.painel_historico = PainelHistorico()
        self.servidor.historico.connect(self.painel_historico.adicionar)
        self.painel_historico.ir_para.connect(self._ir_para)
        self.dock_historico = QDockWidget("HISTÓRICO DOS JOGADORES", self)
        self.dock_historico.setObjectName("dock_historico")
        self.dock_historico.setWidget(self.painel_historico)
        self.dock_historico.setFeatures(self.dock_camadas.features())
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_historico)
        self.dock_historico.hide()
        self.painel_info.ao_mudar_desl = self.servidor.atualizar_combate

        # Biblioteca de objetos (props)
        from .painel_objetos import PainelObjetos
        self.painel_objetos = PainelObjetos()
        self.painel_objetos.colocar.connect(
            lambda tipo: self._colocar_prop(tipo, self.visao.centro_da_visao()))
        self.painel_objetos.importar_imagem.connect(self._importar_prop_imagem)
        self.visao.prop_solto.connect(self._colocar_prop)
        self.dock_objetos = QDockWidget("OBJETOS", self)
        self.dock_objetos.setObjectName("dock_objetos")
        from PyQt6.QtWidgets import QTabWidget
        from .banco_imagens import PainelBanco
        self.painel_banco = PainelBanco()
        self.painel_banco.usar.connect(lambda uso, c: self._usar_do_banco(uso, c, None))
        self.visao.banco_solto.connect(self._usar_do_banco)
        self.abas_objetos = QTabWidget()
        self.abas_objetos.addTab(rolavel(self.painel_objetos), "📦 Objetos")
        self.abas_objetos.addTab(self.painel_banco, "🖼 Banco de imagens")
        self.dock_objetos.setWidget(self.abas_objetos)
        self.dock_objetos.setFeatures(self.dock_camadas.features())
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_objetos)
        self.dock_objetos.hide()
        self.painel_props.ao_editar_prop = self.editar_prop
        self.painel_props.ao_mostrar_conteudo = self._menu_mostrar_conteudo
        self.servidor.conteudo_mudou.connect(lambda _p: self.painel_props.atualizar())
        self.servidor.ficha_mudou.connect(self._ficha_do_player)
        self.servidor.gatilho_disparou.connect(self._gatilho_disparou)
        self.painel_info.ao_abrir_ficha = self.abrir_ficha
        self.diario = []
        self.janela_diario = None
        from ..mesa.atlas import Atlas
        self.atlas = Atlas()   # 🌍 cidades e mundo (v0.62)
        self._criar_atmosfera()
        self._criar_projetor()
        self.resizeDocks([self.dock_combate], [290], Qt.Orientation.Horizontal)
        from PyQt6.QtGui import QShortcut
        QShortcut(QKeySequence("N"), self, self.painel_combate.proximo)
        # Retráteis: começam fechados; abrem pelos botões ⚔ / 🎲 da barra
        self.dock_combate.hide()
        self.dock_dados.hide()
        self.dock_chat.hide()
        from .sobreposicoes import AvisoRolagem, FaixaTurnos
        self.faixa_turnos = FaixaTurnos(self.visao, mestre=True)
        self.faixa_turnos.proximo.connect(self.painel_combate.proximo)
        self.faixa_turnos.anterior.connect(self.painel_combate.anterior)
        self.faixa_turnos.abrir_painel.connect(lambda: self._abrir_dock(self.dock_combate))
        self.faixa_turnos.resolver = self._cartao_do_id
        self.faixa_turnos.centralizar.connect(self._centralizar_uid)
        self.servidor.combate_mudou.connect(
            lambda: self.faixa_turnos.atualizar(self.servidor.combate.para_dict()))
        # Retratos do grupo (estilo Baldur's Gate), na esquerda da mesa
        from .retratos import PainelGrupo
        self.painel_grupo = PainelGrupo(self.visao)
        self.painel_grupo.centralizar.connect(self._centralizar_uid)
        self.painel_grupo.abrir_ficha.connect(
            lambda uid: (t := self._token_uid(uid)) is not None and self.abrir_ficha(t))
        self.painel_grupo.definir_ligado(self.config.value("retratos_grupo", True, type=bool))
        self._assinatura_grupo = None
        self._timer_grupo = QTimer(self)
        self._timer_grupo.setInterval(400)   # leve: compara antes de redesenhar
        self._timer_grupo.timeout.connect(self._atualizar_grupo)
        self._timer_grupo.start()
        self.aviso_rolagem = AvisoRolagem(self.visao)
        # Ping (tecla P): sinal no mapa pra todo mundo
        from ..mesa.ping import pingar
        from .painel_dados import cor_do_nome
        self.visao.ping_pedido.connect(self._ping)
        self.visao.olhar_pedido.connect(lambda pos: self.chamar_atencao(pos))   # (v0.58) Shift+P
        self.servidor.ping.connect(
            lambda nome, x, y: pingar(self.servidor.cena, x, y, nome, cor_do_nome(nome)))
        # Dados 3D rolando na mesa (inclusive as privadas do mestre: só na tela dele)
        from ..dados3d.overlay import PainelDados3D
        self.dados3d = PainelDados3D(self.visao)
        self.servidor.rolagem.connect(self._rolagem_na_mesa)
        self.dados3d.revelar.connect(self._mostrar_rolagem)

        self.resizeDocks([self.dock_camadas], [300], Qt.Orientation.Horizontal)
        self.resizeDocks([self.dock_camadas, self.dock_props, self.dock_jogadores],
                         [250, 340, 130], Qt.Orientation.Vertical)

    def _acao(self, texto, atalho=None, funcao=None, dica=None, marcavel=False):
        a = QAction(texto, self)
        if atalho:
            a.setShortcut(QKeySequence(atalho))
        if funcao:
            (a.toggled if marcavel else a.triggered).connect(funcao)
        if dica:
            a.setToolTip(dica)
            a.setStatusTip(dica)
        a.setCheckable(marcavel)
        return a

    def _criar_acoes(self):
        self.a_nova = self._acao("Nova sessão…", "Ctrl+N", self.nova_cena)
        self.a_abrir = self._acao("Abrir sessão…", "Ctrl+O", self.abrir_cena)

        # Ferramentas de construção (atalhos de uma tecla, estilo Photoshop)
        self.acoes_ferramenta = {}
        for chave, atalho in (("selecionar", "V"), ("terreno", "B"), ("borracha", "E"),
                              ("parede", "W"), ("borracha_parede", "Shift+E"),
                              ("sala", "R"), ("porta", "D"), ("luz", "L")):
            a = self._acao(chave, atalho, lambda _=False, k=chave: self.cena.definir_ferramenta(k))
            self.addAction(a)
            self.acoes_ferramenta[chave] = a
        a_esc = self._acao("esc", "Esc", self._esc)
        self.addAction(a_esc)
        for atalho, direcao in (("[", -1), ("]", +1)):
            a = self._acao(f"pincel{atalho}", atalho,
                           lambda _=False, d=direcao: self.barra_construcao.mudar_tamanho(d))
            self.addAction(a)

        # Temas
        self.grupo_temas = QActionGroup(self)
        self.acoes_tema = {}
        for chave, t in TEMAS.items():
            a = self._acao(t["nome"], None, lambda _=False, k=chave: self.cena.definir_tema(k))
            a.setCheckable(True)
            self.grupo_temas.addAction(a)
            self.acoes_tema[chave] = a
        self.a_salvar = self._acao("Salvar", "Ctrl+S", self.salvar)
        self.a_salvar_como = self._acao("Salvar como…", "Ctrl+Shift+S", self.salvar_como)
        self.a_fechar_sessao = self._acao("Fechar sessão (voltar ao início)", "Ctrl+W",
                                          self.fechar_sessao)
        self.a_importar = self._acao("🗺  Importar mapa…", "Ctrl+I", self.importar_mapa,
                                     "Abrir uma imagem para ser o mapa da mesa")
        self.a_importar_uvtt = self._acao("🗺  Importar mapa Universal VTT (.dd2vtt, .uvtt)…", None,
                                          self.importar_uvtt,
                                          "Mapa do Dungeondraft, DungeonFog e afins, já com paredes, portas e luzes")
        self.a_exportar_pacote = self._acao("📦  Exportar pacote de aventura…", None, self.exportar_pacote,
                                            "A aventura num arquivo só (.tavernapack) pra mandar pra alguém")
        self.a_importar_pacote = self._acao("📦  Importar pacote de aventura…", None, self.importar_pacote,
                                            "Abrir um .tavernapack (instala imagens e tabelas sem apagar nada)")
        self.a_sair = self._acao("Sair", "Ctrl+Q", self.close)

        self.a_desfazer = self._acao("Desfazer", "Ctrl+Z", self.desfazer,
                                     "Desfaz a última construção (terreno, parede, porta)")
        self.a_refazer = self._acao("Refazer", "Ctrl+Y", self.refazer)
        a_refazer2 = self._acao("refazer2", "Ctrl+Shift+Z", self.refazer)
        self.addAction(a_refazer2)
        self.a_cursores = self._acao("Mostrar o mouse dos jogadores", None,
                                     lambda v: [c.cursores.definir_visiveis(v)
                                                for c in self.cenas], marcavel=True)
        self.a_cursores.setChecked(True)
        self.a_meu_cursor = self._acao("Mostrar o meu mouse pros jogadores", None,
                                       self.servidor.definir_mostrar_meu_cursor, marcavel=True)
        self.a_meu_cursor.setChecked(True)
        self.a_remover = self._acao("Remover selecionados", "Delete", self.remover_selecionados)
        self.a_sel_tudo = self._acao("Selecionar tudo", "Ctrl+A", self.selecionar_tudo)

        self.a_token = self._acao("⬤  Tokens…", "T", lambda: self.abrir_tokens(),
                                  "Biblioteca de tokens: crie, salve e coloque jogadores, criaturas e NPCs na mesa")
        self.a_snap = self._acao("⌗  Snap no grid", "S", lambda v: self.cena.definir_snap(v),
                                 "Liga/desliga o encaixe dos tokens no centro dos quadrados (S)",
                                 marcavel=True)
        self.a_snap.setChecked(self.cena.snap_ativo)

        self.a_taverna = self._acao("🍺  Abrir taverna", None, self.alternar_taverna,
                                    "Abrir/fechar a mesa para os jogadores entrarem")

        # Visão / névoa
        self.a_nevoa = self._acao("🌫  Névoa de guerra (nesta aba)", None,
                                  lambda v: self.cena.definir_nevoa(v),
                                  "Os jogadores só veem o que os tokens deles enxergam",
                                  marcavel=True)
        self.a_cones = self._acao("Mostrar a visão dos jogadores", None,
                                  lambda v: [c.definir_mostrar_cones(v) for c in self.cenas],
                                  "Desenha na sua tela o que cada jogador está vendo",
                                  marcavel=True)
        from ..mesa.luzes import AMBIENTES
        self.grupo_ambiente = QActionGroup(self)
        self.acoes_ambiente = {}
        for chave, (nome, _) in AMBIENTES.items():
            a = self._acao(nome, None, lambda _=False, k=chave: self._ambiente(k))
            a.setCheckable(True)
            self.grupo_ambiente.addAction(a)
            self.acoes_ambiente[chave] = a
        self.acoes_ambiente["dia"].setChecked(True)
        self.a_previa_luz = self._acao("Prévia da iluminação na minha tela", None,
                                       lambda v: [c.definir_previa_luz(v) for c in self.cenas],
                                       "Escurece um pouco a sua tela pra você ver como está a luz",
                                       marcavel=True)
        self.a_previa_luz.setChecked(True)
        self.a_liberar_giro = self._acao("Liberar giro de todos os jogadores", None,
                                         lambda: self._giro_todos(True))
        self.a_travar_giro = self._acao("Travar giro de todos os jogadores", None,
                                        lambda: self._giro_todos(False))
        for atalho, graus in ((",", -15), (".", 15)):
            a = self._acao(f"girar{atalho}", atalho,
                           lambda _=False, g=graus: self._girar_selecionados(g))
            self.addAction(a)
        a_olhar = self._acao("olhar", "F", self._olhar_pro_mouse)
        self.addAction(a_olhar)

        self.a_biblioteca = self._acao("📚  Biblioteca", "Ctrl+B", self.abrir_biblioteca,
                                       "Compêndio do SRD (monstros, magias, regras…) e seus PDFs")

        self.a_enquadrar = self._acao("Enquadrar tudo", "Home", self.visao.enquadrar_tudo)
        self.a_zoom100 = self._acao("Zoom 100%", "Ctrl+0", self.visao.zoom_100)

    def _criar_menus(self):
        barra = self.menuBar()
        m = barra.addMenu("&Arquivo")
        m.addActions([self.a_nova, self.a_abrir])
        m.addSeparator()
        m.addActions([self.a_salvar, self.a_salvar_como])
        m.addSeparator()
        m.addAction(self.a_importar)
        m.addAction(self.a_importar_uvtt)
        m.addSeparator()
        m.addAction(self.a_exportar_pacote)
        m.addAction(self.a_importar_pacote)
        m.addSeparator()
        m.addAction(self.a_fechar_sessao)
        m.addAction(self.a_sair)

        m = barra.addMenu("&Editar")
        m.addActions([self.a_desfazer, self.a_refazer])
        m.addSeparator()
        m.addActions([self.a_remover, self.a_sel_tudo])

        m = barra.addMenu("&Mesa")
        m.addActions([self.a_token, self.a_snap])
        m.addSeparator()
        m.addAction("🗺  Cidade e mundo (montar)…", self.abrir_atlas)
        m.addSeparator()
        m.addAction(self.a_nevoa)
        luz = m.addMenu("💡  Luz ambiente (nesta aba)")
        luz.addActions(list(self.acoes_ambiente.values()))
        luz.addSeparator()
        luz.addAction(self.a_previa_luz)
        m.addAction(self.a_cones)
        m.addAction(self.a_liberar_giro)
        m.addAction(self.a_travar_giro)
        pecas = m.addMenu("Peças dos tokens (Mesa 3D)")   # (v0.73) todos de uma vez
        pecas.addAction("Todos como ficha redonda", lambda: self.estilo_de_todos("ficha"))
        pecas.addAction("Todos como standee (imagem em pé)", lambda: self.estilo_de_todos("standee"))
        m.addSeparator()
        sub = m.addMenu("Tema")
        sub.addActions(list(self.acoes_tema.values()))

        m = barra.addMenu("&Sessão")
        m.addAction(self.a_taverna)
        a = m.addAction("📓  Diário da campanha", self.abrir_diario)
        a.setShortcut(QKeySequence("Ctrl+Shift+D"))
        self.addAction(a)

        m = barra.addMenu("&Biblioteca")
        m.addAction(self.a_biblioteca)
        m.addAction("📄  Fichas em PDF (qualquer sistema)…", self.abrir_fichas_pdf)

        m = barra.addMenu("E&xibir")
        from ..graficos import menu_graficos
        self._grupo_graficos = menu_graficos(m.addMenu("✨ Gráficos"), self)
        m.addSeparator()
        m.addActions([self.a_enquadrar, self.a_zoom100])
        m.addSeparator()
        m.addAction(self.dock_camadas.toggleViewAction())
        m.addAction(self.dock_props.toggleViewAction())
        m.addAction(self.dock_jogadores.toggleViewAction())
        m.addAction(self.dock_info.toggleViewAction())
        m.addAction(self.dock_combate.toggleViewAction())
        m.addAction(self.dock_dados.toggleViewAction())
        m.addAction(self.dock_chat.toggleViewAction())
        m.addAction(self.dock_atmosfera.toggleViewAction())
        m.addAction(self.dock_projetor.toggleViewAction())
        m.addAction("🖼  Banco de imagens", self.abrir_banco)
        m.addAction(self.barra_construcao.toggleViewAction())
        m.addSeparator()
        m.addAction(self.a_cursores)
        m.addAction(self.a_meu_cursor)
        m.addSeparator()
        self.a_retratos = m.addAction("Retratos do grupo (na esquerda da mesa)")
        self.a_retratos.setCheckable(True)
        self.a_retratos.setChecked(self.config.value("retratos_grupo", True, type=bool))
        self.a_retratos.toggled.connect(lambda v: self._alternar_retratos(v))

        # (v0.58) ❓ Ajuda: tela de atalhos (F1)
        from .atalhos import abrir as abrir_atalhos
        m = barra.addMenu("Aj&uda")
        self.a_atalhos = self._acao("⌨  Atalhos", "F1", lambda: abrir_atalhos(self, "mestre"),
                                    "Todos os atalhos do mestre (F1)")
        m.addAction(self.a_atalhos)
        from .dicas import mostrar as mostrar_dicas
        m.addAction("💡  Dicas de primeiro acesso", lambda: mostrar_dicas(self, "mestre", forcar=True))
        m.addSeparator()
        from .reportar import abrir as abrir_reportar
        self.a_reportar = self._acao("🐞  Reportar problema…", None, lambda: abrir_reportar(self, "mestre"),
                                     "Monta um .zip com o registro de erros pra mandar pro Manel (nada vai pela internet)")
        m.addAction(self.a_reportar)

    def _criar_barra(self):
        from .acabamento import Icones, enfeitar_dock, espacador, estilo_barra
        barra = self.addToolBar("Ferramentas")
        self.barra = barra
        estilo_barra(barra)
        self.icones = Icones()
        barra.setMovable(False)
        barra.addAction(self.a_importar)
        barra.addAction(self.a_token)
        barra.addSeparator()
        barra.addAction(self.a_snap)
        barra.addSeparator()
        rot = QLabel("Grade")
        rot.setToolTip("Opacidade do grid")
        barra.addWidget(rot)
        self.slider_grid = QSlider(Qt.Orientation.Horizontal)
        self.slider_grid.setRange(0, 100)
        self.slider_grid.setFixedWidth(64)
        self.slider_grid.setValue(int(self.cena.opacidade_grid * 100))
        self.slider_grid.setToolTip("Opacidade do grid")
        self.slider_grid.valueChanged.connect(
            lambda v: self.cena.definir_opacidade_grid(v / 100))
        barra.addWidget(self.slider_grid)
        barra.addSeparator()
        barra.addAction(self.a_biblioteca)
        barra.addSeparator()
        self.a_combate = self.dock_combate.toggleViewAction()
        self.a_combate.setText("⚔  Combate")
        self.a_combate.setShortcut(QKeySequence("Ctrl+K"))
        self.a_combate.setToolTip("Abrir/fechar o painel de combate (Ctrl+K)\n"
                                  "Com combate rolando, a faixa de turnos fica em cima da mesa.")
        self.a_dados = self.dock_dados.toggleViewAction()
        self.a_dados.setText("🎲  Dados")
        self.a_dados.setShortcut(QKeySequence("Ctrl+D"))
        self.a_dados.setToolTip("Rolar dados e rolagens prontas (Ctrl+D)\n"
                                "Com Dados e Chat fechados, as rolagens aparecem num aviso no canto da mesa.")
        self.a_chat = self.dock_chat.toggleViewAction()
        self.a_chat.setText("💬  Chat")
        self.a_chat.setShortcut(QKeySequence("Ctrl+E"))
        self.a_chat.setToolTip("Chat da mesa (Ctrl+E)\n"
                               "Fechado, as mensagens aparecem num aviso no canto da mesa.")
        self.a_historico = self.dock_historico.toggleViewAction()
        self.a_historico.setText("📜  Histórico")
        self.a_historico.setShortcut(QKeySequence("Ctrl+H"))
        self.a_historico.setToolTip("O que os jogadores fizeram: movimentos, rolagens, pings,\n"
                                    "tentativas recusadas… (Ctrl+H). Só você vê.")
        self.a_objetos = self.dock_objetos.toggleViewAction()
        self.a_objetos.setText("📦  Objetos")
        self.a_objetos.setShortcut(QKeySequence("Ctrl+J"))
        self.a_objetos.setToolTip("Objetos (móveis, baús, luzes…) e o 🖼 Banco de imagens (Ctrl+J)")
        barra.insertAction(self.a_biblioteca, self.a_objetos)
        barra.addAction(self.a_combate)
        barra.addAction(self.a_dados)
        barra.addAction(self.a_chat)
        barra.addAction(self.a_historico)
        self.a_atmosfera = self.dock_atmosfera.toggleViewAction()
        self.a_atmosfera.setText("🌦  Atmosfera")
        self.a_atmosfera.setShortcut(QKeySequence("Ctrl+T"))
        self.a_atmosfera.setToolTip("Clima, áreas de efeito (fogo, gelo, escuridão…), lápis,\n"
                                    "efeitos sonoros e música do YouTube (Ctrl+T)")
        barra.addAction(self.a_atmosfera)
        self.a_projetor = self.dock_projetor.toggleViewAction()
        self.a_projetor.setText("📽  Projetor")
        self.a_projetor.setShortcut(QKeySequence("Ctrl+P"))
        self.a_projetor.setToolTip("Mostrar uma imagem na tela dos jogadores (Ctrl+P)")
        barra.addAction(self.a_projetor)
        barra.addSeparator()
        barra.addAction(self.a_nevoa)
        # Na barra: ícone do tema em cima, nome curto embaixo (o menu continua com o nome completo)
        for acao, curto, nome_icone in (
                (self.a_importar, "Mapa", "mapa"), (self.a_token, "Token", "token"), (self.a_snap, "Snap", "snap"),
                (self.a_objetos, "Objetos", "objetos"), (self.a_biblioteca, "Biblioteca", "biblioteca"),
                (self.a_combate, "Combate", "combate"), (self.a_dados, "Dados", "dados"),
                (self.a_chat, "Chat", "chat"),
                (self.a_historico, "Histórico", "historico"), (self.a_atmosfera, "Atmosfera", "atmosfera"),
                (self.a_projetor, "Projetor", "projetor"), (self.a_nevoa, "Névoa", "nevoa"),
                (self.a_taverna, "Abrir taverna", "taverna"), (self.a_meu_cursor, "Meu mouse", "olho")):
            acao.setIconText(curto)
            self.icones.ligar(acao.setIcon, nome_icone)
        barra.addWidget(espacador())
        barra.addAction(self.a_meu_cursor)
        barra.addAction(self.a_taverna)
        barra.widgetForAction(self.a_taverna).setObjectName("primario")
        self.a_meu_cursor.setToolTip("Os jogadores veem (ou não) a setinha do seu mouse")
        # cabeçalho enfeitado dos painéis + ícones das abas
        for dock, nome_icone in ((self.dock_camadas, "camadas"), (self.dock_props, "propriedades"),
                                 (self.dock_jogadores, "jogadores"), (self.dock_info, "info"),
                                 (self.dock_combate, "combate"), (self.dock_dados, "dados"),
                                 (self.dock_chat, "chat"),
                                 (self.dock_historico, "historico"), (self.dock_objetos, "objetos"),
                                 (self.dock_atmosfera, "atmosfera"), (self.dock_projetor, "projetor")):
            enfeitar_dock(dock, nome_icone)
        for abas, lista in ((self.abas_objetos, (("Objetos", "objetos"), ("Banco de imagens", "banco"))),
                            (self.abas_atmosfera, (("Efeitos e clima", "magia"), ("Som e música", "som")))):
            for k, (texto, nome_icone) in enumerate(lista):
                abas.setTabText(k, texto)
                self.icones.ligar(lambda ic, a=abas, k=k: a.setTabIcon(k, ic), nome_icone)

    def _criar_status(self):
        self.lbl_pos = QLabel("—")
        self.lbl_zoom = QLabel("Zoom 100%")
        self.lbl_snap = QLabel()
        self.lbl_taverna = QLabel("Taverna fechada")
        s = self.statusBar()
        from PyQt6.QtWidgets import QToolButton
        self.btn_internet = QToolButton()   # 🌐 (v0.65) "Aberta pela internet" / "Só rede local/Radmin"
        self.btn_internet.setAutoRaise(True)
        self.btn_internet.setVisible(False)
        self.btn_internet.clicked.connect(self._mostrar_internet)
        self._upnp = None
        s.addPermanentWidget(self.btn_internet)
        s.addPermanentWidget(self.lbl_taverna)
        s.addPermanentWidget(self.lbl_snap)
        s.addPermanentWidget(self.lbl_pos)
        s.addPermanentWidget(self.lbl_zoom)
        self._snap_mudou(self.cena.snap_ativo)
        s.showMessage("Roda do mouse = zoom · Botão do meio ou Espaço+arrastar = mover a visão "
                      "· Duplo clique no token = editar", 12000)

    def _conectar(self):
        self.visao.zoom_mudou.connect(lambda z: self.lbl_zoom.setText(f"Zoom {z * 100:.0f}%"))
        self.visao.cursor_moveu.connect(self._cursor_moveu)
        self.visao.cursor_moveu.connect(self._cursor_pro_servidor)
        self.visao.cursor_saiu.connect(lambda: self.servidor.cursor_mestre(None, None))
        self.visao.imagem_solta.connect(self._imagem_solta)
        self.visao.menu_pedido.connect(self._menu_contexto)
        self.servidor.jogadores_mudaram.connect(lambda _: self._atualizar_jogadores())
        self.servidor.aviso.connect(lambda t: self.statusBar().showMessage(t, 6000))
        self._atualizar_jogadores()

    def _registrar_cena(self, cena):
        """Ligações que valem pra TODAS as abas (mesmo as que o mestre não está vendo)."""
        self._ligar_fluidos(cena)
        cena.modificacao_mudou.connect(lambda _: self._atualizar_titulo())
        cena.mesa_mudou.connect(self._mesa_mudou_atlas)   # 🌍 marcadores do grupo seguem os tokens (e revelam)
        cena.camadas_mudaram.connect(self._atualizar_jogadores)
        cena.cursores.definir_visiveis(self.a_cursores.isChecked())
        cena.definir_mostrar_cones(self.a_cones.isChecked())
        cena.definir_previa_luz(self.a_previa_luz.isChecked())

    def _sinais_da_cena(self, cena):
        return ((cena.snap_mudou, self._snap_mudou),
                (cena.editar_token_pedido, self.editar_token),
                (cena.ferramenta_mudou, self.visao.atualizar_modo),
                (cena.selecao_construcao_mudou, self._selecao_construcao_mudou),
                (cena.tema_mudou, self._tema_mudou),
                (cena.editar_prop_pedido, self.editar_prop),
                (cena.editar_gatilho_pedido, self.editar_area_gatilho),
                (cena.editar_efeito_pedido, self.editar_efeito),
                (cena.reacoes_sugeridas, self._reacoes_sugeridas),
                (cena.ferramenta_mudou, self._ferramenta_atmosfera))

    def _ligar_cena(self, cena):
        """Ligações só da aba que está na tela."""
        for sinal, slot in self._sinais_da_cena(cena):
            sinal.connect(slot)
        if hasattr(self, "painel_info"):
            self.painel_info.definir_cena(cena)
        if hasattr(self, "painel_atmosfera"):
            self.painel_atmosfera.definir_cena(cena)
            clima = getattr(cena, "clima", {}) or {}
            self.clima_overlay.definir(clima.get("tipo", "nenhum"), clima.get("forca", 2))
            from ..mesa import neblina
            neblina.garantir(cena)
        self._tema_mudou(cena.tema)

    def _desligar_cena(self, cena):
        for sinal, slot in self._sinais_da_cena(cena):
            try:
                sinal.disconnect(slot)
            except (TypeError, RuntimeError):
                pass

    def _cursor_pro_servidor(self, p):
        # Só mostra o mouse do mestre se ele estiver olhando a mesma aba dos players
        if self.cena is self.servidor.cena:
            self.servidor.cursor_mestre(p.x(), p.y())
        else:
            self.servidor.cursor_mestre(None, None)

    # ================================================================ status
    def _cursor_moveu(self, p: QPointF):
        self.lbl_pos.setText(f"X {fmt_m(p.x() / CELULA)} m · Y {fmt_m(p.y() / CELULA)} m")

    def _snap_mudou(self, ativo):
        if self.a_snap.isChecked() != ativo:
            self.a_snap.setChecked(ativo)
        self.lbl_snap.setText("Snap: ligado" if ativo else "Snap: desligado")

    def _atualizar_titulo(self):
        nome = self.cena.nome_aventura or (
            os.path.basename(self.caminho_cena) if self.caminho_cena else "Aventura sem nome")
        nome += f" · {self.cena.nome_aba}"
        marca = " •" if any(c.modificada for c in getattr(self, "cenas", [self.cena])) else ""
        self.setWindowTitle(f"{nome}{marca} — {APP_NOME} Mestre {APP_VERSAO}")

    def _tema_mudou(self, chave):
        # O tema é da aventura inteira: aplica em todas as abas
        for c in getattr(self, "cenas", []):
            if c is not self.cena and c.tema != chave:
                c.definir_tema(chave)
        if self.pilha.currentWidget() is not self.tela_inicial:
            self._aplicar_tema(chave)
        self.visao.definir_fundo(dados_tema(chave)["mesa"])
        if hasattr(self, "painel_objetos"):
            self.painel_objetos.definir_tema(chave)   # Objetos abre nos do tema da aventura
        if hasattr(self, "painel_camadas"):
            QTimer.singleShot(0, self.painel_camadas.recarregar)   # cores da lista acompanham o tema
        acao = self.acoes_tema.get(chave)
        if acao and not acao.isChecked():
            acao.setChecked(True)

    # ================================================================ aventuras
    @staticmethod
    def pasta_aventuras() -> str:
        docs = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DocumentsLocation) or os.path.expanduser("~")
        pasta = os.path.join(docs, "Taverna", "Aventuras")
        os.makedirs(pasta, exist_ok=True)
        return pasta

    @classmethod
    def caminho_da_aventura(cls, nome: str) -> str:
        seguro = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", nome).strip().rstrip(".") or "Aventura"
        return os.path.join(cls.pasta_aventuras(), seguro + EXTENSAO_CENA)

    # ================================================================ mapa
    def importar_mapa(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Importar mapa", "", FILTRO_IMAGEM)
        if caminho:
            self._carregar_imagem(caminho, self.visao.centro_da_visao())

    def importar_uvtt(self, caminho: str | None = None, escolhas: dict | None = None):
        """🗺 Mapa Universal VTT: imagem na escala certa + paredes + portas + luzes (mesa/uvtt.py).
        escolhas (testes): {"metros": 1.5, "material": "pedra", "aba_nova": True} pula o diálogo."""
        from ..mesa import uvtt
        if not caminho:
            caminho, _ = QFileDialog.getOpenFileName(self, "Importar mapa Universal VTT", "", uvtt.FILTRO)
            if not caminho:
                return None
        nome = os.path.splitext(os.path.basename(caminho))[0]
        try:
            dados = uvtt.ler(caminho)
        except uvtt.ErroUVTT as erro:
            QMessageBox.warning(self, "Não deu", str(erro))
            return None
        if escolhas is None:
            from .dialogo_uvtt import DialogoUVTT
            dlg = DialogoUVTT(self, nome, dados)
            if not dlg.exec():
                return None
            escolhas = {"metros": dlg.metros(), "material": dlg.material.currentData(),
                        "aba_nova": dlg.aba_nova.isChecked()}
        if escolhas.get("aba_nova", True):
            cena = self._nova_cena_vazia(nome)
            self._registrar_cena(cena)
            self.cenas.append(cena)
            self.trocar_aba(len(self.cenas) - 1)
            centro = QPointF(0, 0)
        else:
            centro = self.visao.centro_da_visao()
        try:
            r = uvtt.aplicar(self.cena, dados, escolhas.get("metros", 1.5), escolhas.get("material", "pedra"),
                             centro, nome)
        except (ValueError, OSError) as erro:
            QMessageBox.warning(self, "Não deu", f"Não consegui montar o mapa:\n{erro}")
            return None
        self.visao.centerOn(r["centro"])
        self.statusBar().showMessage(
            f"Mapa “{nome}” importado: {fmt_m(r['largura_m'])} × {fmt_m(r['altura_m'])} m, {r['paredes']} paredes, "
            f"{r['portas']} portas, {r['luzes']} luzes.", 10000)
        return r

    # ================================================================ 📦 pacote de aventura (v0.61)
    def exportar_pacote(self, caminho: str | None = None, levar_diario: bool | None = None):
        """A aventura inteira num .tavernapack (mesa/pacote.py). caminho/levar_diario (testes) pulam as perguntas."""
        from ..mesa import pacote
        from ..mesa.arquivo import dados_aventura
        nome = self.cena.nome_aventura or "Aventura"
        if levar_diario is None:
            from PyQt6.QtWidgets import QCheckBox
            caixa = QMessageBox(self)
            caixa.setWindowTitle("Exportar pacote de aventura")
            caixa.setIcon(QMessageBox.Icon.Information)
            caixa.setText(f"<b>{nome}</b> vai num arquivo só (.tavernapack): todas as abas, mapas, tokens, objetos, "
                          "imagens do projetor e as tabelas de sorteio dos baús.<br><br>"
                          "Não vão: PDFs e as fichas dos jogadores.<br><br>⚠ " + pacote.AVISO)
            diario = QCheckBox("Levar o diário da campanha também")
            caixa.setCheckBox(diario)
            caixa.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            caixa.button(QMessageBox.StandardButton.Ok).setText("Exportar…")
            caixa.button(QMessageBox.StandardButton.Cancel).setText("Cancelar")
            if caixa.exec() != QMessageBox.StandardButton.Ok:
                return None
            levar_diario = diario.isChecked()
        if not caminho:
            sugestao = os.path.join(self.pasta_aventuras(), pacote._seguro(nome) + pacote.EXTENSAO)
            caminho, _ = QFileDialog.getSaveFileName(self, "Exportar pacote de aventura", sugestao, pacote.FILTRO)
            if not caminho:
                return None
            if not caminho.lower().endswith(pacote.EXTENSAO):
                caminho += pacote.EXTENSAO
        dados = dados_aventura(self.cenas, nome, self.cena.tema, self.indice_ao_vivo, self.cenas.index(self.cena),
                               self.painel_projetor.galeria, self.diario, self.atlas.para_dict())
        try:
            r = pacote.exportar(caminho, dados, levar_diario)
        except OSError as erro:
            QMessageBox.warning(self, "Não deu", f"Não consegui gravar o pacote:\n{erro}")
            return None
        mb = r["tamanho"] / (1024 * 1024)
        self.statusBar().showMessage(
            f"📦 Pacote “{os.path.basename(caminho)}” pronto: {r['abas']} aba(s), {r['imagens']} imagens, "
            f"{r['tabelas']} tabela(s), {fmt_m(round(mb, 1))} MB.", 10000)
        return r

    def importar_pacote(self, caminho: str | None = None, abrir: bool = True):
        """Instala um .tavernapack (aventura, imagens no banco, tabelas) sem sobrescrever nada, e abre."""
        from ..mesa import pacote
        if not caminho:
            caminho, _ = QFileDialog.getOpenFileName(self, "Importar pacote de aventura", "", pacote.FILTRO)
            if not caminho:
                return None
        from ..jogo.tabelas import pasta_tabelas
        from .banco_imagens import pasta_banco
        try:
            r = pacote.instalar(caminho, self.pasta_aventuras(), pasta_banco(), pasta_tabelas())
        except (pacote.ErroPacote, OSError) as erro:
            QMessageBox.warning(self, "Não deu", str(erro))
            return None
        if getattr(self, "painel_banco", None) is not None and hasattr(self.painel_banco, "recarregar"):
            self.painel_banco.recarregar()
        partes = [f"{r['imagens']} imagens novas no banco"]
        if r["imagens_repetidas"]:
            partes.append(f"{r['imagens_repetidas']} que você já tinha")
        partes.append(f"{r['tabelas']} tabela(s) de sorteio")
        if r["tabelas_renomeadas"]:
            partes.append(f"{r['tabelas_renomeadas']} renomeada(s) pra não apagar as suas")
        if abrir:
            self.abrir_cena(r["aventura"])
        self.statusBar().showMessage(f"📦 “{r['nome']}” importada: " + ", ".join(partes) + ".", 12000)
        return r

    def _imagem_solta(self, caminho, pos):
        self._carregar_imagem(caminho, pos)

    def _carregar_imagem(self, caminho, centro):
        try:
            with open(caminho, "rb") as f:
                dados = f.read()
            nome = os.path.splitext(os.path.basename(caminho))[0]
            mapa = self.cena.adicionar_mapa(dados, centro, nome)
        except (OSError, ValueError) as erro:
            QMessageBox.warning(self, "Não deu", f"Não consegui abrir a imagem:\n{erro}")
            return
        self.cena.clearSelection()
        mapa.setSelected(True)
        self.statusBar().showMessage(
            "Mapa importado. Arraste as alças douradas ou digite o tamanho em Propriedades.", 8000)

    # ================================================================ tokens
    def novo_token(self, tipo="criatura", centro=None):
        """Novo token: Salvar na biblioteca (fica pronto pra usar depois) ou Colocar na mesa."""
        dialogo = DialogoToken(self, tipo_inicial=tipo, jogadores=self.servidor.nomes())
        if not dialogo.exec():
            return
        if dialogo.acao == "salvar":
            from . import biblioteca_tokens
            biblioteca_tokens.salvar(dialogo.dados())
            if getattr(self, "_biblioteca", None) is not None:
                self._biblioteca.tokens.recarregar()
            self.statusBar().showMessage(f"“{dialogo.dados()['nome']}” salvo na Biblioteca → Tokens.", 5000)
            return
        self.token_da_biblioteca(dialogo.dados(), centro)

    def token_da_biblioteca(self, d, centro=None):
        """Põe na mesa um token pronto (da biblioteca ou recém-criado), já com PV e deslocamento."""
        token = self.cena.adicionar_token(d, centro or self.visao.centro_da_visao())
        token.definir_retrato(d.get("retrato"))
        if d.get("estilo") in ("ficha", "standee"):   # (v0.73) ficha redonda ou standee
            token.prepareGeometryChange()
            token.estilo = d["estilo"]
        token.sem_borda = bool(d.get("sem_borda", False))   # (v0.77)
        from ..mesa.token import escala_valida
        token.escala_standee = escala_valida(d.get("escala_standee", 1.0))   # (v0.78)
        if d.get("pv"):
            token.definir_info("pv", [int(d["pv"]), int(d["pv"])])
        if d.get("desl"):
            token.definir_info("desl", float(d["desl"]))
        self.cena.clearSelection()
        token.setSelected(True)
        self.statusBar().showMessage(f"{token.nome} colocado na mesa.", 4000)
        return token

    def salvar_token_na_biblioteca(self, token):
        """Botão direito num token da mesa → guardar como modelo na Biblioteca → Tokens."""
        from . import biblioteca_tokens
        pv = (token.info.get("pv") or {}).get("v")
        biblioteca_tokens.salvar({"nome": token.nome, "tipo": token.tipo, "cor": token.cor.name(),
                                  "tamanho": token.tamanho, "dono": token.dono, "imagem": token.imagem,
                                  "retrato": getattr(token, "retrato", None),
                                  "pv": int(pv[1]) if isinstance(pv, (list, tuple)) and len(pv) > 1 else 0,
                                  "desl": token.deslocamento, "estilo": token.estilo,
                                  "sem_borda": token.sem_borda, "escala_standee": token.escala_standee})
        if getattr(self, "_biblioteca", None) is not None:
            self._biblioteca.tokens.recarregar()
        self.statusBar().showMessage(f"“{token.nome}” salvo na Biblioteca → Tokens.", 5000)

    def estilo_de_todos(self, estilo: str):
        """(v0.73) Todos os tokens desta aba viram ficha redonda ou standee."""
        n = 0
        for t in self.cena.itens_do_usuario():
            if isinstance(t, TokenItem) and t.estilo != estilo:
                t.prepareGeometryChange()
                t.estilo = estilo
                t.update()
                n += 1
        if n:
            self.cena.marcar_modificada()
            self.cena.mesa_mudou.emit()
        nome = "standee" if estilo == "standee" else "ficha redonda"
        self.statusBar().showMessage(f"{n} token(s) agora como {nome}.", 4000)
        return n

    def editar_token(self, token: TokenItem):
        dialogo = DialogoToken(self, token=token, jogadores=self.servidor.nomes())
        if dialogo.exec():
            d = dialogo.dados()
            tipo_antigo = token.tipo
            token.definir_retrato(d.get("retrato"))   # (antes do atualizar: ele avisa que mudou)
            token.atualizar(d["nome"], d["tipo"], d["cor"], d["tamanho"], d["imagem"], d["dono"])
            from ..mesa.token import escala_valida
            esc = escala_valida(d.get("escala_standee", token.escala_standee))
            if (d.get("estilo") in ("ficha", "standee") and d["estilo"] != token.estilo) or \
                    bool(d.get("sem_borda")) != token.sem_borda or esc != token.escala_standee:   # (v0.73/77/78)
                token.prepareGeometryChange()
                token.estilo = d.get("estilo") or token.estilo
                token.sem_borda = bool(d.get("sem_borda"))
                token.escala_standee = esc
                token.update()
                self.cena.mesa_mudou.emit()
            # Se mudou de jogador pra criatura (ou vice-versa), muda de camada
            from ..config import TIPOS_TOKEN
            if TIPOS_TOKEN[tipo_antigo][2] != TIPOS_TOKEN[d["tipo"]][2]:
                destino = self.cena.camada_por_tipo(TIPOS_TOKEN[d["tipo"]][2])
                if destino:
                    self.cena.mover_item_para_camada(token, destino)
            self.cena.camadas_mudaram.emit()
            self.painel_props.atualizar()

    def _editar_item_da_lista(self, item):
        """Duplo clique num item no painel de camadas."""
        if isinstance(item, TokenItem):
            self.editar_token(item)
        else:
            self.visao.centerOn(item)

    def _esc(self):
        self.cena.definir_ferramenta("selecionar")
        self.cena.limpar_selecao_construcao()
        self.cena.clearSelection()

    def _selecao_construcao_mudou(self, paredes, pinceladas):
        itens = len([i for i in self.cena.selectedItems() if hasattr(i, "para_dict")])
        if paredes or pinceladas or itens:
            self.statusBar().showMessage(
                f"Selecionado: {itens} item(ns), {paredes} parede(s), {pinceladas} pincelada(s)"
                " · Delete apaga · Ctrl+arrastar soma", 6000)

    # ================================================================ visão
    # ================================================================ biblioteca
    def abrir_biblioteca(self):
        if getattr(self, "_biblioteca", None) is None:
            from .biblioteca import JanelaBiblioteca
            self._biblioteca = JanelaBiblioteca(mestre=True, livros=self.servidor.livros,
                                                jogadores=self.servidor.nomes)
            self._biblioteca.tokens.colocar.connect(lambda d: self.token_da_biblioteca(d))
            self._biblioteca.tokens.novo.connect(lambda: self.novo_token())
        self._biblioteca.show()
        self._biblioteca.raise_()
        self._biblioteca.activateWindow()

    def abrir_tokens(self):
        """Botão Token da barra: abre a Biblioteca já na aba Tokens."""
        self.abrir_biblioteca()
        self._biblioteca.mostrar_tokens()

    # ================================================================ etapa 6
    # ================================================================ objetos (props)
    def _colocar_prop(self, tipo, pos):
        prop = self.cena.colocar_prop(tipo, pos)
        if prop is not None:
            self.cena.clearSelection()
            prop.setSelected(True)
            self.statusBar().showMessage(
                f"{prop.nome} na mesa." + ("  Duplo clique pra colocar itens dentro." if prop.interativo else
                                           "  Botão direito → Ligar ao andar…" if prop.tipo == "escada" else ""), 5000)

    def _importar_prop_imagem(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Imagem do objeto", "",
                                                 "Imagens (*.png *.jpg *.jpeg *.webp)")
        if not caminho:
            return
        with open(caminho, "rb") as f:
            dados = f.read()
        self._prop_de_imagem(dados, os.path.splitext(os.path.basename(caminho))[0], self.visao.centro_da_visao())

    def _prop_de_imagem(self, dados, nome, pos):
        prop = self.cena.colocar_prop("imagem", pos, dados)
        if prop is None:
            return
        prop.nome = nome
        pm = prop._pixmap
        if pm is not None and pm.width() > 0:
            prop.definir_tamanho(2, max(0.5, round(2 * pm.height() / pm.width() * 2) / 2))
        self.cena.clearSelection()
        prop.setSelected(True)

    # ================================================================ banco de imagens (Etapa 13)
    def _usar_do_banco(self, uso, caminho, pos):
        try:
            with open(caminho, "rb") as f:
                dados = f.read()
        except OSError as erro:
            QMessageBox.warning(self, "Não deu", f"Não consegui abrir a imagem:\n{erro}")
            return
        nome = os.path.splitext(os.path.basename(caminho))[0]
        pos = pos or self.visao.centro_da_visao()
        if uso == "perguntar":
            uso = "objeto"
        if uso == "mapa":
            self._carregar_imagem(caminho, pos)
        elif uso == "token":
            token = self.cena.adicionar_token(dict(nome=nome, tipo="criatura", cor="#7a4b3a", tamanho=1,
                                                   imagem=dados, dono=""), pos)
            self.cena.clearSelection()
            token.setSelected(True)
            self.statusBar().showMessage(f"⬤ {nome} na mesa. Duplo clique pra editar (tipo, tamanho, dono…).", 6000)
        elif uso == "objeto":
            self._prop_de_imagem(dados, nome, pos)
        elif uso == "projetor":
            self.painel_projetor.adicionar(dados, nome)
            self.dock_projetor.show()
            self.dock_projetor.raise_()
            self.statusBar().showMessage(f"📽 {nome} está na galeria do projetor.", 5000)

    def abrir_fichas_pdf(self):
        from .fichas_pdf import JanelaFichasPDF
        JanelaFichasPDF(self).exec()

    def abrir_banco(self):
        self.dock_objetos.show()
        self.dock_objetos.raise_()
        self.abas_objetos.setCurrentWidget(self.painel_banco)

    def _guardar_no_banco(self, dados, nome, pasta):
        import os as _os
        from .banco_imagens import pasta_banco
        destino = self.painel_banco.guardar_bytes(dados, nome or "imagem", _os.path.join(pasta_banco(), pasta))
        self.statusBar().showMessage(f"🖼 Guardado no banco de imagens ({pasta}).", 5000)
        return destino

    def _remover_fundo_prop(self, prop):
        from .remover_fundo import DialogoRemoverFundo
        d = DialogoRemoverFundo(prop.imagem, prop.nome, self)
        if d.exec():
            from .remover_fundo import _para_qimage, imagem_png
            prop.definir_imagem(imagem_png(_para_qimage(d.arr)))   # sem cortar: mantém o tamanho
            prop.update()
            prop._mudou()
            self.painel_props.atualizar()

    def editar_prop(self, prop):
        from .dialogo_prop import DialogoProp
        if prop.solto and not prop.documento:   # (v0.48) item coletável: janela enxuta
            from .dialogo_coletavel import DialogoColetavel
            if DialogoColetavel(prop, self).exec():
                self.painel_props.atualizar()
                self.painel_camadas.recarregar()
            return
        if DialogoProp(prop, self).exec():
            self.painel_props.atualizar()
            self.painel_camadas.recarregar()

    def _menu_prop(self, menu, prop):
        menu.addAction("Editar escada…" if prop.tipo == "escada" else
                       ("🗝 Editar chave (o que ela abre)…" if prop.tipo == "chave" else "🎒 Editar item coletável…")
                       if prop.solto and not prop.documento else "Editar objeto e conteúdo…",
                       lambda: self.editar_prop(prop))
        menu.addAction("↻ Girar 90°", lambda: (prop.girar(90), self.painel_props.atualizar()))
        menu.addAction("↺ Girar -90°", lambda: (prop.girar(-90), self.painel_props.atualizar()))
        if prop.interativo and not prop.solto and prop.tipo != "escada":
            menu.addAction("🗝 Criar chave pra este objeto…", lambda: self._criar_chave(prop))
        if prop.interativo and not prop.solto:
            menu.addSeparator()
            menu.addAction("🔓 Destrancar" if prop.trancado else "🔒 Trancar",
                           lambda: (setattr(prop, "trancado", not prop.trancado), prop._mudou(),
                                    self.painel_props.atualizar(), self.painel_camadas.recarregar()))
            self._submenu_mostrar(menu.addMenu("👁 Mostrar conteúdo para…"), prop)
        menu.addSeparator()
        menu.addAction("⚡ Armadilha / gatilho…", lambda: self.editar_gatilho_prop(prop))
        if prop.gatilho:
            menu.addAction("⚡ Disparar agora", lambda: self._disparar_manual(prop.gatilho, prop.centro_cena()))
            menu.addAction("Tirar a armadilha", lambda: (setattr(prop, "gatilho", None), prop._mudou(),
                                                         self.painel_camadas.recarregar()))
        if prop.luz:
            menu.addAction("Apagar a luz" if prop.luz_acesa else "Acender a luz",
                           lambda: (setattr(prop, "luz_acesa", not prop.luz_acesa), prop._mudou(),
                                    self.painel_props.atualizar()))
        menu.addSeparator()
        menu.addAction("Remover objeto", lambda: self.cena.remover_itens([prop]))

    # ================================================================ atmosfera (Etapa 10)
    def _criar_atmosfera(self):
        from .clima import ClimaOverlay
        from .painel_atmosfera import PainelAtmosfera
        self.clima_overlay = ClimaOverlay(self.visao.viewport())
        self.painel_atmosfera = PainelAtmosfera(mestre=True)
        p = self.painel_atmosfera
        p.ferramenta.connect(lambda nome: self.cena.definir_ferramenta(nome))
        p.clima_mudou.connect(self._clima_mudou)
        p.relampago.connect(lambda: (self.clima_overlay.relampago(), self.servidor.relampago()))
        p.mostrar_clima.connect(self.clima_overlay.definir_ligado)
        p.apagar_templates.connect(self._apagar_templates_jogadores)
        p.limpar_marcas.connect(self._limpar_marcas)
        p.limpar_fluidos.connect(self._limpar_fluidos)
        self.visao.clique_ferramenta.connect(self._clique_ferramenta)
        p.impacto_tela.connect(lambda tipo: self.servidor.impacto(tipo))
        p.sons_efeitos.connect(self._abrir_sons_efeitos)
        self.visao.impacto_pedido.connect(self._impacto_no_mapa)
        self.servidor.impacto_local.connect(self._tocar_impacto)
        self.visao.lancar_pedido.connect(self._lancar)
        self.servidor.lancamento_local.connect(self._ver_lancamento)
        p.apagar_desenhos.connect(lambda: self.cena.apagar_tracos())
        # regras pros jogadores
        from PyQt6.QtWidgets import QCheckBox
        self.ck_templates = QCheckBox("Colocar templates de magia")
        self.ck_lapis = QCheckBox("Rabiscar no mapa (lápis)")
        for ck in (self.ck_templates, self.ck_lapis):
            ck.setChecked(True)
            ck.toggled.connect(lambda _v: self.servidor.definir_regras_atmosfera(
                self.ck_templates.isChecked(), self.ck_lapis.isChecked()))
        for w in (self.ck_templates, self.ck_lapis):   # seção "Jogadores podem…" do painel
            p.layout_extra.addWidget(w)
        # Som e música
        from PyQt6.QtWidgets import QTabWidget
        from .audio import TocadorSons
        from .painel_som import PainelSom
        self.tocador = TocadorSons(self)
        self.painel_som = PainelSom()
        self.painel_som.tocar_som.connect(self._tocar_som)
        self.painel_som.parar_sons.connect(lambda: (self.tocador.parar(), self.servidor.parar_som()))
        self.painel_som.volume_sons.connect(lambda v: self.tocador.definir_volume(v))
        self.painel_som.musica.connect(lambda d: self.servidor.definir_musica(**d))
        self.abas_atmosfera = QTabWidget()
        self.abas_atmosfera.addTab(p, "✨ Efeitos e clima")
        self.abas_atmosfera.addTab(self.painel_som, "🎵 Som e música")
        self.dock_atmosfera = QDockWidget("ATMOSFERA", self)
        self.dock_atmosfera.setObjectName("dock_atmosfera")
        self.dock_atmosfera.setWidget(self.abas_atmosfera)
        self.dock_atmosfera.setFeatures(self.dock_camadas.features())
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_atmosfera)
        self.dock_atmosfera.hide()
        self.visao.efeito_pedido.connect(self._efeito_pedido)
        self.visao.traco_pedido.connect(lambda t: self.cena.adicionar_traco(dict(t, autor="Mestre")))
        self.visao.ferramenta_saiu.connect(self._esc)
        self.servidor.efeito_colocado.connect(lambda _e: self.painel_camadas.recarregar())
        self.dock_chat.visibilityChanged.connect(lambda v: v and self._npcs_do_chat())

    def _tocar_som(self, caminho, vol, ambiente, pra_todos):
        sid = self.servidor.preparar_som(caminho)
        if not sid:
            return
        self.tocador.registrar_arquivo(sid, caminho)
        self.tocador.tocar(sid, vol, ambiente)
        if pra_todos:
            self.servidor.tocar_som(sid, vol, ambiente)
            self.statusBar().showMessage(f"🔊 Tocando pra todos: {self.servidor.sons[sid][0]}", 4000)

    # ================================================================ projetor (Etapa 11)
    def _criar_projetor(self):
        from .projetor import PainelProjetor
        self.painel_projetor = PainelProjetor()
        pp = self.painel_projetor
        pp.projetar.connect(self._projetar)
        pp.recolher.connect(lambda: (self.servidor.recolher_projecao(), pp.status.setText("Nada projetado."),
                                     self.statusBar().showMessage("📽 Projeção recolhida.", 3000)))
        pp.mudou.connect(lambda: self.cena.marcar_modificada())
        self.servidor.jogadores_mudaram.connect(pp.definir_jogadores)
        self.dock_projetor = QDockWidget("PROJETOR", self)
        self.dock_projetor.setObjectName("dock_projetor")
        self.dock_projetor.setWidget(rolavel(pp))
        self.dock_projetor.setFeatures(self.dock_camadas.features())
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_projetor)
        self.dock_projetor.hide()

    def _projetar(self, dados, titulo, para):
        if not self.servidor.aberto:
            self.painel_projetor.status.setText("Abra a taverna primeiro (menu Sessão) — ninguém está conectado.")
        self.servidor.projetar(dados, titulo, para)
        self.painel_projetor.mostrar_status(titulo, para)
        quem = "todos" if para is None else ", ".join(para)
        self.servidor.registrar("Mestre", f"projetou {titulo or 'uma imagem'} para {quem}", "📽")
        self.statusBar().showMessage(f"📽 Projetando pra {quem}.", 4000)

    def projetar_imagem(self, dados: bytes, titulo: str):
        """Do botão direito (token/documento): põe na galeria e já projeta pra todos."""
        i = self.painel_projetor.adicionar(dados, titulo)
        if i is None:
            return
        self.dock_projetor.show()
        self.dock_projetor.raise_()
        self.painel_projetor.ck_todos.setChecked(True)
        im = self.painel_projetor.galeria[i]
        self._projetar(im["dados"], im.get("titulo", ""), None)

    def _impacto_no_mapa(self, pos):
        d = getattr(self.cena, "impacto_atual", None) or {"tipo": "explosao", "tam": 3.0}
        self.impacto_de_reacao(self.cena, d["tipo"], pos.x(), pos.y(), d.get("tam", 3.0))

    def _abrir_sons_efeitos(self):
        from .sons_efeitos import DialogoSonsEfeitos
        d = DialogoSonsEfeitos(self)
        d.testar.connect(lambda caminho, vol: self._tocar_som(caminho, vol, False, False))
        if d.exec():
            self.painel_som.recarregar_sons()
            self.statusBar().showMessage("🔊 Sons dos efeitos salvos.", 4000)

    def _tocar_impacto(self, tipo, x, y, tam):
        from ..mesa.impactos import tocar
        from .sons_efeitos import som_do_efeito
        som = som_do_efeito(tipo)   # som atrelado: toca junto, pra todo mundo
        if som:
            self._tocar_som(som[0], som[1], False, True)
        # (se você estiver olhando outra aba/andar, só os jogadores de lá veem o desenho no mapa)
        cena = self.cena if self.cena is getattr(self.servidor, "cena_do_impacto", self.servidor.cena) else None
        tocar(cena, self.visao, self.clima_overlay, tipo, x, y, tam)

    def _submenu_impacto_aqui(self, menu, pos):
        from ..mesa.impactos import IMPACTOS
        sub = menu.addMenu("💥 Efeito rápido aqui")
        tam = self.painel_atmosfera.sp_impacto.value()
        for chave, (nome, no_mapa, _d) in IMPACTOS.items():
            if no_mapa:
                sub.addAction(nome, lambda k=chave: self.impacto_de_reacao(self.cena, k, pos.x(), pos.y(), tam))

    def _clima_mudou(self, tipo, forca):
        self.cena.definir_clima(tipo, forca)
        self.clima_overlay.definir(tipo, forca)
        from ..mesa import neblina
        neblina.garantir(self.cena)   # neblina volumétrica dentro da mesa (Mesa 3D)

    def _efeito_pedido(self, d):
        item = self.cena.criar_efeito(d)
        if item is None:
            self.statusBar().showMessage("Fora do mapa: área de efeito só existe onde tem chão ou mapa.", 5000)
            return
        self.painel_camadas.recarregar()
        self.statusBar().showMessage(f"✨ {item.descricao()} — duplo clique edita, botão direito apaga/gira. "
                                     f"Esc pra parar de colocar.", 6000)

    def _ferramenta_atmosfera(self, nome):
        self.painel_atmosfera.ferramenta_atual(nome)
        if nome in ("efeito", "lapis"):
            self.dock_atmosfera.show()
            self.abas_atmosfera.setCurrentIndex(0)

    def _apagar_templates_jogadores(self):
        ids = {e.uid for e in self.cena.efeitos_visiveis() if e.dono}
        n = self.cena.remover_efeitos(ids=ids) if ids else 0
        self.painel_camadas.recarregar()
        self.statusBar().showMessage(f"{n} template(s) dos jogadores apagado(s).", 4000)

    def _reacoes_sugeridas(self, feitas):
        """As áreas reagiram sozinhas (v0.42: automático): só avisa na barra de status."""
        self.painel_camadas.recarregar()
        self.statusBar().showMessage("Reação: " + " · ".join(feitas), 5000)

    def impacto_de_reacao(self, cena, tipo, x, y, tam):
        """Explosão/onda de uma reação: pra todo mundo se for a aba ao vivo; senão, só aqui."""
        if self.servidor.e_ao_vivo(cena):
            self.servidor.impacto(tipo, x, y, tam, cena=cena)   # quem está nesse andar vê (e o som toca)
        elif cena is self.cena:
            from ..mesa.impactos import tocar
            tocar(cena, self.visao, self.clima_overlay, tipo, x, y, tam)

    def _lancar(self, d):
        """O mestre arrastou um lançamento (bola de fogo, jato…)."""
        if self.servidor.e_ao_vivo(self.cena):
            self.servidor.lancar(d, cena=self.cena)   # quem está nesse andar vê; a área aparece quando chega
            return
        from ..mesa.lancamentos import area_deixada, chegada, conferir, tocar
        d = conferir(d)   # aba que não está ao vivo: só na tela do mestre
        if d is None:
            return
        tocar(self.cena, d)
        if d["deixar"]:
            cena = self.cena
            QTimer.singleShot(int(chegada(d) * 1000), lambda: cena.criar_efeito(area_deixada(d)))

    def _ver_lancamento(self, d):
        from ..mesa.lancamentos import tocar
        d = dict(d)
        onde = d.pop("_cena", None)
        if onde is None or onde == id(self.cena):   # o mestre só vê se estiver olhando esse andar
            tocar(self.cena if onde is not None else self.servidor.cena, d)

    def _limpar_marcas(self):
        n = self.cena.limpar_marcas()
        self.statusBar().showMessage(f"{n} marca(s) tirada(s) do chão." if n else "Não há marcas no chão.", 4000)

    def editar_efeito(self, item):
        from .dialogo_efeito import DialogoEfeito
        dlg = DialogoEfeito(item, self)
        if dlg.exec():
            dlg.aplicar()
            self.painel_camadas.recarregar()

    def _menu_efeito(self, menu, item):
        menu.addAction("✨ Editar efeito…", lambda: self.editar_efeito(item))
        sub = menu.addMenu("Trocar efeito")
        from ..mesa.efeitos import EFEITOS
        for chave, (nome, *_r) in EFEITOS.items():
            a = sub.addAction(nome, lambda k=chave: item.aplicar(efeito=k))
            a.setCheckable(True)
            a.setChecked(item.efeito == chave)
        if item.forma in ("cone", "linha", "quadrado"):
            menu.addAction("↻ Girar 45°", lambda: item.aplicar(angulo=item.angulo + 45))
            menu.addAction("↺ Girar -45°", lambda: item.aplicar(angulo=item.angulo - 45))
        menu.addSeparator()
        menu.addAction("Remover área de efeito", lambda: (self.cena.remover_itens([item]),
                                                         self.cena.mesa_mudou.emit()))

    def _submenu_efeito_objeto(self, menu, item):
        from ..mesa.efeitos import EFEITOS_OBJETO
        sub = menu.addMenu("✨ Efeito" + (f": {EFEITOS_OBJETO.get(item.efeito, '')}" if item.efeito else ""))
        a = sub.addAction("Nenhum", lambda: item.definir_efeito(""))
        a.setCheckable(True)
        a.setChecked(not item.efeito)
        for chave, nome in EFEITOS_OBJETO.items():
            a = sub.addAction(nome, lambda k=chave: item.definir_efeito(k))
            a.setCheckable(True)
            a.setChecked(item.efeito == chave)

    def _submenu_area_aqui(self, menu, pos):
        from ..mesa.efeitos import EFEITOS
        sub = menu.addMenu("✨ Área de efeito aqui")
        for chave, (nome, *_r) in EFEITOS.items():
            sub.addAction(nome, lambda k=chave: self._efeito_pedido(
                dict(self.cena.efeito_atual, efeito=k, x=pos.x(), y=pos.y(), angulo=0)))

    # ================================================================ chaves
    def _nomear_porta(self, porta):
        nome, ok = QInputDialog.getText(self, "Nome da porta", "Nome (ex.: Porta armadilha):",
                                        text=porta.nome_proprio)
        if ok:
            porta.nome_proprio = nome.strip()
            porta.mudou()
            self.painel_props.atualizar()

    def _criar_chave(self, alvo):
        # cria um item "chave" no chão, já ligado à porta/baú (e deixa trancado)
        from ..mesa.portas import PortaItem
        padrao = alvo.chave or f"Chave {'da' if isinstance(alvo, PortaItem) else 'do'} {alvo.nome}"
        nome, ok = QInputDialog.getText(self, "Criar chave", "Nome da chave (o item que vai abrir):", text=padrao)
        if not ok or not nome.strip():
            return
        alvo.chave = nome.strip()
        if isinstance(alvo, PortaItem):
            alvo.trancada = True
            if alvo.aberta:
                alvo.alternar()
            alvo.mudou()
            pos = alvo.scenePos()
        else:
            alvo.trancado = True
            alvo._mudou()
            pos = alvo.centro_cena()
        from ..config import CELULA
        chave = self.cena.colocar_prop("chave", QPointF(pos.x() + 1.5 * CELULA, pos.y() + 1.5 * CELULA))
        if chave is not None:
            chave.nome = alvo.chave
            chave.itens[0]["nome"] = alvo.chave
            chave.itens[0]["desc"] = f"Abre: {alvo.nome}"
            chave._mudou()
            self.cena.clearSelection()
            chave.setSelected(True)
        self.painel_props.atualizar()
        self.painel_camadas.recarregar()
        self.statusBar().showMessage(f"🗝 “{alvo.chave}” criada ao lado — arraste pra onde quiser esconder. "
                                     f"{alvo.nome} ficou trancado(a).", 10000)

    # ================================================================ armadilhas
    def editar_gatilho_prop(self, prop):
        from ..jogo.gatilhos import gatilho_novo
        from .dialogo_gatilho import DialogoGatilho
        d = DialogoGatilho(prop.gatilho or gatilho_novo("prop"), self.cena, "prop", self)
        if d.exec():
            prop.gatilho = d.resultado()
            prop._mudou()
            self.painel_camadas.recarregar()

    def _nova_area(self, pos):
        area = self.cena.criar_area_gatilho(pos)
        self.cena.clearSelection()
        area.setSelected(True)
        self.editar_area_gatilho(area)

    def editar_area_gatilho(self, area):
        from .dialogo_gatilho import DialogoGatilho
        d = DialogoGatilho(area.gatilho, self.cena, "area", self)
        if d.exec():
            area.gatilho = d.resultado()
            area.update()
            area._mudou()
            self.painel_camadas.recarregar()

    def _menu_area(self, menu, area):
        from ..jogo.gatilhos import pode_disparar
        menu.addAction("Editar armadilha…", lambda: self.editar_area_gatilho(area))
        menu.addAction("Tamanho…", lambda: self._tamanho_area(area))
        menu.addAction("⚡ Disparar agora", lambda: self._disparar_manual(area.gatilho, area.retangulo_cena().center()))
        if not pode_disparar(area.gatilho):
            menu.addAction("Rearmar", lambda: (area.gatilho.update(disparado=False, ativo=True), area.update(),
                                               area._mudou()))
        else:
            menu.addAction("Desarmar", lambda: (area.gatilho.update(ativo=False), area.update(), area._mudou()))
        menu.addSeparator()
        menu.addAction("Remover área", lambda: self.cena.remover_itens([area]))

    def _tamanho_area(self, area):
        texto, ok = QInputDialog.getText(self, "Tamanho da área", "Largura × altura em metros (ex.: 3 x 2):",
                                         text=f"{area.w:g} x {area.h:g}")
        if not ok:
            return
        import re
        nums = re.findall(r"\d+(?:[.,]\d+)?", texto)
        if len(nums) >= 2:
            area.definir_tamanho(float(nums[0].replace(",", ".")), float(nums[1].replace(",", ".")))

    def _disparar_manual(self, gatilho, pos):
        if self.cena is not self.servidor.cena:
            self.statusBar().showMessage("Só dá pra disparar no cenário que está ao vivo pros jogadores.", 6000)
            return
        self.servidor.disparar(gatilho, "Mestre", None, (pos.x(), pos.y()), manual=True)
        self.painel_camadas.recarregar()
        self.cena.update()

    def _gatilho_disparou(self, resumo):
        import html as _h
        self.statusBar().showMessage(resumo, 12000)
        self.aviso_rolagem.mostrar_texto(f"<b style='color:#ff7a5a'>{_h.escape(resumo)}</b>", 10)
        QApplication.alert(self, 3000)
        self.painel_camadas.recarregar()

    def _submenu_mostrar(self, sub, prop):
        nomes = self.servidor.nomes()
        if not nomes:
            a = sub.addAction("(nenhum jogador conectado)")
            a.setEnabled(False)
            return
        sub.addAction("Todos (só olhar)", lambda: self.servidor.mostrar_conteudo(prop, None, False))
        sub.addAction("Todos (podem pegar)", lambda: self.servidor.mostrar_conteudo(prop, None, prop.pode_pegar))
        sub.addSeparator()
        for n in nomes:
            sub.addAction(n, lambda n=n: self.servidor.mostrar_conteudo(prop, [n], prop.pode_pegar))

    def _menu_mostrar_conteudo(self, prop):
        menu = QMenu(self)
        self._submenu_mostrar(menu, prop)
        iconizar_menu(menu).exec(self.cursor().pos())

    def _ping(self, pos):
        from ..mesa.ping import pingar
        from .painel_dados import cor_do_nome
        pingar(self.cena, pos.x(), pos.y(), "Mestre", cor_do_nome("Mestre"))
        if self.cena is self.servidor.cena:
            self.servidor.ping_mestre(pos.x(), pos.y())

    def _ir_para(self, pos):
        if self.cena is not self.servidor.cena:
            self.trocar_aba(self.cenas.index(self.servidor.cena))
        self.visao.centerOn(pos)
        from ..mesa.ping import pingar
        pingar(self.cena, pos.x(), pos.y(), "", "#c9a24a")   # só pra você achar (não vai pra rede)

    # ================================================================ fichas
    # ================================================================ retratos (grupo e combate)
    def _token_uid(self, uid, cena=None):
        for c in ([cena] if cena else [self.cena, self.servidor.cena]):
            for item in c.itens_do_usuario():
                if isinstance(item, TokenItem) and item.uid == uid:
                    return item
        return None

    def _centralizar_uid(self, uid):
        t = self._token_uid(uid)
        if t is not None:
            self._mostrar_token(t)   # (só se o token estiver na aba que você está vendo)

    def _cartao_do_id(self, uid):
        """Faixa do combate: retrato de quem está no combate (aba ao vivo)."""
        from ..mesa.grupo import cartao_do_token
        t = self._token_uid(uid, self.servidor.cena)
        return cartao_do_token(t) if t is not None else None

    def _atualizar_grupo(self):
        if self.pilha.currentWidget() is self.tela_inicial:
            self.painel_grupo.hide()
            self._assinatura_grupo = None
            return
        from ..mesa.grupo import montar_grupo
        grupo, imagens = montar_grupo(self.cena, mestre=True)
        c = self.servidor.combate
        vez = c.vez if c.ativo and self.servidor.cena is self.cena else None
        assinatura = (repr(grupo), vez, self.painel_grupo.ligado)
        if assinatura != self._assinatura_grupo:
            self._assinatura_grupo = assinatura
            self.painel_grupo.atualizar(grupo, imagens, vez)
            if c.ativo:   # retratos pequenos da faixa também (caído, imagem nova…)
                self.faixa_turnos.atualizar(c.para_dict())

    def _alternar_retratos(self, v):
        self.config.setValue("retratos_grupo", bool(v))
        self.painel_grupo.definir_ligado(v)
        self._assinatura_grupo = None

    def abrir_ficha(self, token):
        from .janela_ficha import JanelaFicha, aplicar_pacote, pacote_do_token
        if not hasattr(self, "_fichas"):
            self._fichas = {}
        janela = self._fichas.get(token.uid)
        if janela is None:
            janela = JanelaFicha(pacote_do_token(token), token.nome, None,
                                 fonte=lambda t=token: pacote_do_token(t))

            def salvo(pacote, t=token):
                aplicar_pacote(t, pacote)
                self.painel_info.atualizar()
                self.painel_props.atualizar()
                self.servidor.atualizar_combate()
            janela.salvar.connect(salvo)
            self._fichas[token.uid] = janela
        janela.show()
        janela.raise_()
        janela.activateWindow()

    def _ficha_do_player(self, token):
        janela = getattr(self, "_fichas", {}).get(token.uid)
        if janela is not None:
            janela.atualizar_de_fora()
        self.painel_info.atualizar()

    def _abrir_dock(self, dock):
        dock.show()
        dock.raise_()

    def _nomes_pro_painel(self):
        nomes = list(self.servidor.nomes())
        for t in self.cena.itens_do_usuario():
            if isinstance(t, TokenItem) and t.dono and not any(
                    mesmo_nome(t.dono, n) for n in nomes):
                nomes.append(t.dono)
        return sorted(nomes, key=str.casefold)

    # ================================================================ chat e diário
    def _rolagem_na_mesa(self, r):
        from ..graficos import graficos
        if (graficos().dados3d and self.pilha.currentWidget() is not self.tela_inicial
                and self.dados3d.rolar(r)):
            if r.get("token") and r.get("motivo") == "iniciativa":
                from .painel_combate import ini_rolando
                ini_rolando(r["token"])   # (v0.65.1) a lista só mostra o número quando o dado parar
            return   # o histórico/chat recebe quando o dado parar (dados3d.revelar)
        self._mostrar_rolagem(r)
        if not (self.dock_dados.isVisible() or self.dock_chat.isVisible()):
            self.aviso_rolagem.mostrar(r)

    def _mostrar_rolagem(self, r):
        """O resultado vai pro histórico dos dados e pro chat (depois da animação, se tiver)."""
        self.painel_dados.adicionar(r)
        self.painel_chat.adicionar_rolagem(r)
        if r.get("token"):
            from .painel_combate import ini_revelada
            ini_revelada(r["token"])
            self.painel_combate.atualizar()
            self.faixa_turnos.atualizar(self.servidor.combate.para_dict())

    def _chat_mestre(self, texto, para, como):
        if texto.lower().startswith(("/r ", "/rolar ")):
            self._rolar_mestre(texto.split(" ", 1)[1], False)
            return
        self.servidor.chat_mestre(texto, para, como)

    def _aviso_chat(self, m):
        if m.get("de") == "Mestre":
            return
        if self.dock_chat.isVisible():
            return
        import html as _h
        self._nao_lidas = getattr(self, "_nao_lidas", 0) + 1
        self.a_chat.setIconText(f"Chat ({self._nao_lidas})")
        sussurro = "🤫 " if m.get("para") else ""
        self.aviso_rolagem.mostrar_texto(f"💬 {sussurro}<b>{_h.escape(m.get('de', ''))}</b>: "
                                         f"{_h.escape(m.get('texto', ''))[:120]}", 6)

    def _zerar_chat(self):
        if self.dock_chat.isVisible() and hasattr(self, "a_chat"):
            self._nao_lidas = 0
            self.a_chat.setIconText("Chat")

    def _npcs_do_chat(self):
        nomes = [t.nome for c in self.cenas for t in c.itens_do_usuario()
                 if isinstance(t, TokenItem) and t.tipo != "jogador" and t.nome]
        self.painel_chat.definir_npcs(nomes)

    def abrir_diario(self):
        from .diario import JanelaDiario
        if getattr(self, "janela_diario", None) is None:
            self.janela_diario = JanelaDiario(self.diario, self)
            self.janela_diario.mudou.connect(self._diario_mudou)
            self.janela_diario.finished.connect(lambda _r: setattr(self, "janela_diario", None))
        self.janela_diario.show()
        self.janela_diario.raise_()

    def _diario_mudou(self):
        self.servidor.definir_diario(self.diario)
        self.cena.marcar_modificada()

    def _dar_token(self, token, nome: str):
        """O token passa a ser desse jogador (ele move e edita)."""
        token.dono = nome
        token.update()
        token._avisar_modificacao()
        self.painel_props.atualizar()
        self.statusBar().showMessage(f"🧙 “{token.nome}” agora é de {nome}." if nome else
                                     f"“{token.nome}” agora é só do mestre.", 5000)

    def abrir_atlas(self):
        """🌍 Montar a cidade e o mundo (imagens, onde fica cada aba/cidade, escala)."""
        from .janela_atlas import JanelaAtlas
        if getattr(self, "janela_atlas", None) is None:
            self.janela_atlas = JanelaAtlas(self)
            self.janela_atlas.finished.connect(lambda _r: setattr(self, "janela_atlas", None))
        self.janela_atlas.show()
        self.janela_atlas.raise_()
        return self.janela_atlas

    def atlas_editado(self):
        """A montagem mudou: redesenha e marca a aventura como não salva."""
        if getattr(self, "camada_atlas", None) is not None:
            self.camada_atlas.atlas_mudou()
        self.cena.marcar_modificada()
        if getattr(self, "atlas_rede", None) is not None:
            self.atlas_rede.agendar()   # os jogadores recebem a névoa/marcadores novos

    def _mesa_mudou_atlas(self):
        camada = getattr(self, "camada_atlas", None)
        if camada is None or self.atlas.vazio():
            return
        if camada.quadro != "mesa":
            camada.update()
        camada.agendar_revelar()

    def _definir_atlas(self, dados: dict):
        from ..mesa.atlas import Atlas
        self.atlas = Atlas(dados)
        camada = getattr(self, "camada_atlas", None)
        if camada is not None:
            camada.atlas_mudou()

    def _definir_diario(self, entradas):
        self.diario = list(entradas or [])
        if getattr(self, "janela_diario", None) is not None:
            self.janela_diario.close()
            self.janela_diario = None
        self.servidor.definir_diario(self.diario)

    def _rolar_mestre(self, expr, privada, motivo=""):
        from ..jogo.dados import ErroDados
        try:
            self.servidor.rolar_mestre(expr, privada, motivo)
        except ErroDados as erro:
            self.painel_dados.mostrar_erro(str(erro))

    def _mostrar_token(self, token):
        if token.scene() is not self.cena:
            return
        self.cena.clearSelection()
        token.setSelected(True)
        self.visao.centerOn(token.centro_cena())

    def _ambiente(self, chave):
        self.cena.definir_ambiente(chave)
        from ..mesa.luzes import AMBIENTES
        self.statusBar().showMessage(f"Luz ambiente desta aba: {AMBIENTES[chave][0].strip()}", 4000)

    def _tokens_selecionados(self):
        return [i for i in self.cena.selectedItems() if isinstance(i, TokenItem)]

    def _girar_selecionados(self, graus):
        for t in self._tokens_selecionados():
            t.definir_visao(direcao=t.direcao + graus)
        self.painel_props.mostrar_token()

    def _olhar_pro_mouse(self):
        import math
        alvo = self.visao.mapToScene(self.visao.mapFromGlobal(self.cursor().pos()))
        for t in self._tokens_selecionados():
            c = t.centro_cena()
            t.definir_visao(direcao=math.degrees(math.atan2(alvo.y() - c.y(), alvo.x() - c.x())))
        self.painel_props.mostrar_token()

    def _giro_todos(self, liberar):
        for t in self.cena.tokens_com_visao():
            t.definir_visao(pode_girar=liberar)
        self.painel_props.mostrar_token()
        self.statusBar().showMessage("Giro liberado pra todos." if liberar
                                     else "Giro travado pra todos.", 4000)

    def desfazer(self):
        if self.cena.pode_desfazer():
            self.painel_props.soltar_referencias()
            self.cena.desfazer()
            self.statusBar().showMessage("Desfeito.", 2000)
        else:
            self.statusBar().showMessage("Nada pra desfazer.", 2000)

    def refazer(self):
        if self.cena.pode_refazer():
            self.painel_props.soltar_referencias()
            self.cena.refazer()
            self.statusBar().showMessage("Refeito.", 2000)
        else:
            self.statusBar().showMessage("Nada pra refazer.", 2000)

    # ================================================================ edição
    def remover_selecionados(self):
        itens = [i for i in self.cena.selectedItems() if hasattr(i, "para_dict")]
        paredes, pinceladas = self.cena.contagem_selecao()
        if itens:
            self.cena.remover_itens(itens)
        apagou = self.cena.apagar_selecao_construcao()
        if itens or apagou:
            partes = []
            if itens:
                partes.append(f"{len(itens)} item(ns)")
            if paredes:
                partes.append(f"{paredes} parede(s)")
            if pinceladas:
                partes.append(f"{pinceladas} pincelada(s)")
            self.statusBar().showMessage("Apagado: " + ", ".join(partes) + "  (Ctrl+Z desfaz)", 5000)

    def selecionar_tudo(self):
        for item in self.cena.itens_do_usuario():
            if item.isVisible() and item.parentItem().isVisible():
                item.setSelected(True)

    # ================================================================ gás e líquidos de cenário (v0.45)
    def _ligar_fluidos(self, cena):
        """Gás/líquido da aba: explosões pra todo mundo e o retrato pros jogadores (se for a aba ao vivo)."""
        from ..mesa import fluidos
        f = fluidos.de_cena(cena)
        if getattr(f, "_ligado_janela", False):
            return f
        f._ligado_janela = True
        f.explosao.connect(lambda x, y, tam, c=cena: self.impacto_de_reacao(c, "explosao", x, y, tam))
        f.para_rede.connect(lambda d, c=cena: self.servidor.enviar_fluidos(c, d))
        return f

    def _clique_ferramenta(self, nome, pos):
        d = dict(getattr(self.cena, "fluido_atual", None) or {"tipo": "gas_toxico", "vazao": "media",
                                                              "duracao": 0, "tam": 2})
        f = self._ligar_fluidos(self.cena)
        from ..mesa.fluidos import TIPOS
        if nome == "fonte_fluido":
            f.adicionar_fonte(d["tipo"], pos.x(), pos.y(), d.get("vazao", "media"), d.get("duracao", 0))
            self.statusBar().showMessage(f"Fonte de {TIPOS[d['tipo']][0]} colocada (botão direito nela: ligar/desligar, "
                                         "tirar).", 6000)
        elif nome == "soltar_fluido":
            f.soltar(d["tipo"], pos.x(), pos.y(), d.get("tam", 2))
        self.cena.marcar_modificada()

    def _limpar_fluidos(self, fontes):
        f = self._ligar_fluidos(self.cena)
        f.limpar(fontes=fontes)
        self.cena.marcar_modificada()
        self.statusBar().showMessage("Gás e líquidos limpos" + (" (e as fontes tiradas)." if fontes else "."), 4000)

    def _menu_fonte(self, menu, fonte):
        from ..mesa.fluidos import TIPOS
        f = self._ligar_fluidos(self.cena)
        menu.addSection(f"Fonte: {TIPOS[fonte['tipo']][0]}")

        def alternar():
            fonte["ligada"] = not fonte["ligada"]
            if fonte["ligada"] and fonte["duracao"] > 0 and fonte["decorrido"] >= fonte["duracao"]:
                fonte["decorrido"] = 0.0   # religou depois de acabar: começa de novo
            f._acordar()
            f.mudou.emit()
        menu.addAction("Desligar" if fonte["ligada"] else "Ligar", alternar)
        vaz = menu.addMenu("Vazão")
        for chave, nome in (("fraca", "Fraca"), ("media", "Média"), ("forte", "Forte")):
            a = vaz.addAction(nome, lambda c=chave: (fonte.__setitem__("vazao", c), f.mudou.emit()))
            a.setCheckable(True)
            a.setChecked(fonte["vazao"] == chave)
        menu.addAction("Tirar a fonte", lambda: f.remover_fonte(fonte["id"]))
        menu.addSeparator()

    def _menu_contexto(self, item, pos_tela, pos_cena):
        menu = QMenu(self)
        cena = self.cena
        itens_f = getattr(cena, "_fluidos_itens", None) or []
        fonte = next((i.fonte_em(pos_cena) for i in itens_f if hasattr(i, "fonte_em") and i.fonte_em(pos_cena)), None)
        if fonte is not None:
            self._menu_fonte(menu, fonte)
            iconizar_menu(menu).exec(pos_tela)   # (o import local daqui escondia o do topo: dava erro no menu todo)
            return
        if (item is None or isinstance(item, MapaItem)) and hasattr(cena, "porta_perto"):
            item = cena.porta_perto(pos_cena) or item   # (v0.60.1) a porta é fininha: acha a mais perto
        if item is not None and not item.isSelected():
            cena.clearSelection()
            item.setSelected(True)

        from ..mesa.gatilho_area import AreaGatilhoItem
        from ..mesa.props import PropItem
        from ..mesa.efeitos import EfeitoItem
        if isinstance(item, AreaGatilhoItem):
            self._menu_area(menu, item)
        elif isinstance(item, EfeitoItem):
            self._menu_efeito(menu, item)
        elif isinstance(item, PropItem):
            if item.tipo == "escada":   # 🏢 andares
                from ..mesa.andares import nome_andar
                if item.ligacao:
                    menu.addSection(f"Escada → {nome_andar(item.ligacao['andar'])}")
                menu.addAction("✅ Liberar pros jogadores" if item.trancado else "🚫 Bloquear pros jogadores",
                               lambda e=item: self.liberar_escada(e, e.trancado))
                leva = menu.addMenu("🏢 Esta escada leva para…")
                for rot, dest in self.destinos_escada(item):
                    leva.addAction(rot, lambda e=item, d=dest: self.aplicar_destino_escada(e, d))
                if item.ligacao:
                    leva.addSeparator()
                    leva.addAction("Desligar (não leva a lugar nenhum)", lambda e=item: self.desligar_escada(e))
                menu.addSeparator()
            self._submenu_efeito_objeto(menu, item)
            from ..mesa.fluidos import TIPOS as TIPOS_FLUIDO
            sub = menu.addMenu("🏞 Soltar gás/líquido daqui (fonte)")
            for chave, (nome, *_r) in TIPOS_FLUIDO.items():
                def fonte_aqui(c=chave, prop=item):
                    d = getattr(self.cena, "fluido_atual", None) or {}
                    p = prop.centro_cena()
                    self._ligar_fluidos(self.cena).adicionar_fonte(c, p.x(), p.y(), d.get("vazao", "media"),
                                                                    d.get("duracao", 0))
                    self.cena.marcar_modificada()
                sub.addAction(nome, fonte_aqui)
            for it_doc in item.itens:
                img_b64 = (it_doc.get("doc") or {}).get("img") or it_doc.get("img")
                if img_b64:
                    import base64
                    try:
                        dados_img = base64.b64decode(img_b64)
                    except (ValueError, TypeError):
                        continue
                    menu.addAction(f"📽 Projetar a imagem de “{it_doc.get('nome', 'documento')}”",
                                   lambda d=dados_img, n=it_doc.get("nome", ""): self.projetar_imagem(d, n))
            if item.imagem:
                menu.addAction("✂ Remover fundo da imagem…", lambda: self._remover_fundo_prop(item))
                menu.addAction("🖼 Guardar a imagem no banco",
                               lambda: self._guardar_no_banco(item.imagem, item.nome, "Objetos"))
            self._menu_prop(menu, item)
        elif isinstance(item, PortaItem):
            self._menu_porta(menu, item)
        elif isinstance(item, LuzItem):
            menu.addAction("Apagar" if item.acesa else "Acender", item.alternar)
            tipos = menu.addMenu("Tipo")
            from ..mesa.luzes import TIPOS_LUZ
            for chave, valores in TIPOS_LUZ.items():
                def trocar(k=chave, v=valores):
                    from PyQt6.QtGui import QColor
                    item.tipo = k
                    item.raio_forte, item.raio_fraco = float(v[1]), float(v[2])
                    item.cor, item.tremula = QColor(v[3]), v[4]
                    item.mudou()
                    self.painel_props.atualizar()
                tipos.addAction(icone("luz", valores[3]), valores[0], trocar)
            menu.addSeparator()
            menu.addAction("Remover luz", lambda: cena.remover_itens([item]))
        elif item is not None:
            if isinstance(item, TokenItem):
                menu.addAction("Editar token…", lambda: self.editar_token(item))
                if self.visao.pelos_olhos() is item:   # (v0.75) 👁 câmera por cima do ombro do token
                    menu.addAction("👁 Sair do pelos olhos", self.visao.sair_dos_olhos)
                else:
                    menu.addAction("👁 Ver pelos olhos", lambda t=item: self.visao.ver_pelos_olhos(t))
                if item.tipo == "jogador":   # (v0.64.1) de quem é: só o dono move e edita
                    from ..rede.protocolo import mesmo_nome as _mesmo
                    sub_d = menu.addMenu(f"🧙 Dar este token pra… (agora: {item.dono or 'ninguém'})")
                    for nome_j in list(self.servidor.nomes()) + ([item.dono] if item.dono and not any(
                            _mesmo(item.dono, n) for n in self.servidor.nomes()) else []):
                        a_d = sub_d.addAction(nome_j, lambda n=nome_j, t=item: self._dar_token(t, n))
                        a_d.setCheckable(True)
                        a_d.setChecked(bool(item.dono) and _mesmo(item.dono, nome_j))
                    sub_d.addSeparator()
                    sub_d.addAction("Ninguém (só o mestre)", lambda t=item: self._dar_token(t, ""))
                menu.addAction("📜 Ficha…", lambda: self.abrir_ficha(item))
                menu.addAction("💾 Salvar na biblioteca de tokens", lambda: self.salvar_token_na_biblioteca(item))
                from ..mesa.andares import do_predio, nome_andar
                outros = [c for c in do_predio(self.cenas, cena) if c is not cena]
                if outros:
                    sub_a = menu.addMenu("🏢 Levar pro andar")
                    for c_dest in outros:
                        sub_a.addAction(nome_andar(c_dest.andar),
                                        lambda c=c_dest, t=item: self.levar_token_pro_andar(t, c))
                est = menu.addMenu("Estado")
                for valor, texto in ((None, "Normal"), ("caido", "✚ Caído (pode ser ajudado)"),
                                     ("morto", "💀 Morto")):
                    a = est.addAction(texto, lambda v=valor: (item.definir_estado(v),
                                                              self.servidor.atualizar_combate(),
                                                              self.painel_info.atualizar()))
                    a.setCheckable(True)
                    a.setChecked(item.estado == valor)
                self._submenu_efeito_objeto(menu, item)
                if item.imagem:
                    menu.addAction("📽 Projetar o retrato pros jogadores",
                                   lambda: self.projetar_imagem(item.imagem, item.nome))
                    menu.addAction("🖼 Guardar a imagem no banco",
                                   lambda: self._guardar_no_banco(item.imagem, item.nome, "Tokens"))
                menu.addSeparator()
            from ..mesa.mapa import MapaItem
            if isinstance(item, MapaItem):
                menu.addAction("🖼 Guardar o mapa no banco de imagens",
                               lambda: self._guardar_no_banco(item.dados, getattr(item, "nome", "Mapa"), "Mapas"))
                menu.addSeparator()
            menu.addAction("Trazer para frente", lambda: cena.mover_item_na_camada(item, +1))
            menu.addAction("Enviar para trás", lambda: cena.mover_item_na_camada(item, -1))
            sub = menu.addMenu("Mover para camada")
            for camada in reversed(cena.camadas):
                if camada.tipo in ("grid", "terreno", "paredes"):
                    continue
                acao = sub.addAction(camada.nome,
                                     lambda c=camada: cena.mover_item_para_camada(item, c))
                acao.setEnabled(camada is not item.parentItem())
            menu.addSeparator()
            menu.addAction("Remover", lambda: cena.remover_itens([item]))
        else:
            if cena.tem_selecao_construcao():
                np, nt = cena.contagem_selecao()
                menu.addAction(f"Apagar seleção ({np} parede(s), {nt} pincelada(s))",
                               self.remover_selecionados)
                area = getattr(cena, "area_selecionada", None)
                if area is not None and nt:
                    menu.addAction("Apagar só o terreno DENTRO da área selecionada",
                                   lambda: cena.apagar_terreno_na_area(area))
                menu.addAction("Desmarcar", cena.limpar_selecao_construcao)
                menu.addSeparator()
            # Parede embaixo do mouse?
            parede = cena.parede_em(pos_cena)
            if parede:
                seg = cena.paredes.segmentos[parede]
                titulo = menu.addAction(f"Parede de {materiais.nome('parede', seg['m']).lower()}")
                titulo.setEnabled(False)
                sub = menu.addMenu("Trocar material")
                for chave in self._materiais_tema("paredes"):
                    sub.addAction(QIcon(materiais.amostra("parede", chave, 24)),
                                  materiais.nome("parede", chave),
                                  lambda k=chave: cena.trocar_material_parede(parede, k))
                menu.addAction("Remover este pedaço de parede",
                               lambda: cena.remover_parede(parede))
                menu.addAction("Colocar porta aqui", lambda: self._porta_aqui(pos_cena))
                menu.addSeparator()
            # Pincelada de terreno?
            camada_t = cena.camada_por_tipo("terreno")
            indice = cena.terreno.operacao_em(pos_cena) if cena.terreno and camada_t \
                and camada_t.isVisible() else None
            if indice is not None:
                mat = cena.terreno.ops[indice]["m"]
                titulo = menu.addAction(f"Terreno: {materiais.nome('chao', mat).lower()}")
                titulo.setEnabled(False)
                sub = menu.addMenu("Trocar material")
                for chave in self._materiais_tema("chao"):
                    sub.addAction(QIcon(materiais.amostra("chao", chave, 24)),
                                  materiais.nome("chao", chave),
                                  lambda k=chave: cena.trocar_material_terreno(indice, k))
                menu.addAction("Apagar esta pincelada", lambda: cena.remover_pincelada(indice))
                menu.addSeparator()
            self._submenu_area_aqui(menu, pos_cena)
            self._submenu_impacto_aqui(menu, pos_cena)
            menu.addAction("⚡ Criar área de armadilha aqui",
                           lambda: self._nova_area(pos_cena))
            menu.addAction("Adicionar criatura aqui…",
                           lambda: self.novo_token("criatura", pos_cena))
            menu.addAction("Adicionar jogador aqui…",
                           lambda: self.novo_token("jogador", pos_cena))
            menu.addAction("Adicionar NPC aqui…", lambda: self.novo_token("npc", pos_cena))
            menu.addAction("Colocar porta aqui", lambda: self._porta_aqui(pos_cena))
            menu.addSeparator()
            menu.addAction(self.a_importar)
        # (v0.58) 📣 "Todos olhem pra cá": leva a câmera de todos os jogadores até este ponto
        menu.addSeparator()
        pode, motivo = self._pode_chamar_atencao()
        for texto, travar in (("📣 Levar a câmera de todos aqui  (Shift+P)", 0),
                              ("📣 Levar a câmera de todos aqui e travar 5 s", 5)):
            a = menu.addAction(texto, lambda t=travar: self.chamar_atencao(pos_cena, t))
            a.setEnabled(pode)
            if not pode:
                a.setToolTip(motivo)
        menu.setToolTipsVisible(True)
        iconizar_menu(menu).exec(pos_tela)

    def _pode_chamar_atencao(self):
        if not self.servidor.aberto:
            return False, "Abra a taverna primeiro (os jogadores precisam estar conectados)."
        if not self.servidor.e_ao_vivo(self.cena):
            return False, "Esta aba não está ao vivo pros jogadores."
        return True, ""

    def chamar_atencao(self, pos, travar=0):
        """(v0.58) 📣 Leva a câmera de todos os jogadores até `pos` (no zoom do mestre). Quem está em outro andar
        só recebe um aviso. A névoa continua valendo (a câmera vai, mas o jogador só vê o que já veria)."""
        pode, motivo = self._pode_chamar_atencao()
        if not pode:
            self.statusBar().showMessage("📣 " + motivo, 5000)
            return
        from ..mesa.ping import pingar
        from .painel_dados import cor_do_nome
        pingar(self.cena, pos.x(), pos.y(), "Mestre", cor_do_nome("Mestre"))
        n = self.servidor.olhar_aqui(self.cena, pos.x(), pos.y(), self.visao.escala, travar)
        self.statusBar().showMessage(f"📣 Câmera de {n} jogador(es) levada até aqui"
                                     + (f" (travada por {travar} s)" if travar else "") + ".", 5000)

    def _materiais_tema(self, tipo):
        lista = dados_tema(self.cena.tema)[tipo]
        return lista

    def _porta_aqui(self, pos):
        porta = self.cena.colocar_porta(pos)
        if porta:
            self.cena.clearSelection()
            porta.setSelected(True)

    def _menu_porta(self, menu, porta):
        def mudar(**kw):
            for k, v in kw.items():
                setattr(porta, k, v)
            porta.mudou()
            self.painel_props.atualizar()

        menu.addSection(porta.nome)
        menu.addAction("Fechar porta" if porta.aberta else "Abrir porta", porta.alternar)
        menu.addAction("🗑 Excluir porta", lambda: self.cena.remover_itens([porta]))
        menu.addSeparator()
        menu.addAction("🔓 Destrancar" if porta.trancada else "🔒 Trancar",
                       lambda: mudar(trancada=not porta.trancada))
        menu.addAction("🗝 Criar chave pra esta porta…", lambda: self._criar_chave(porta))
        menu.addAction("Dar um nome…", lambda: self._nomear_porta(porta))
        a = menu.addAction("Jogadores podem abrir/fechar", lambda: mudar(jogadores_abrem=not porta.jogadores_abrem))
        a.setCheckable(True)
        a.setChecked(porta.jogadores_abrem)
        menu.addAction("Inverter abertura (dentro ↔ fora)", lambda: mudar(lado=-porta.lado))
        if not porta.dupla:
            menu.addAction("Trocar o lado da dobradiça",
                           lambda: mudar(dobradica=-porta.dobradica))
        menu.addAction("Desfazer porta dupla" if porta.dupla else "Transformar em porta dupla",
                       lambda: mudar(dupla=not porta.dupla))
        girar = menu.addMenu("Girar")
        for graus in (90, 45, 15, -15, -45, -90):
            girar.addAction(f"{graus:+d}°", lambda g=graus: (
                porta.setRotation((porta.rotation() + g) % 360), porta.mudou(),
                self.painel_props.atualizar()))
        tipo = menu.addMenu("Tipo")
        for chave, (nome, cor, _) in TIPOS_PORTA.items():
            a = tipo.addAction(icone("porta", cor), nome, lambda k=chave: mudar(tipo=k))
            a.setCheckable(True)
            a.setChecked(porta.tipo == chave)
        largura = menu.addMenu("Largura")
        for larg in (0.5, 1, 1.5, 2, 3, 4):
            a = largura.addAction(f"{larg:g} m".replace(".", ","),
                                  lambda l=larg: mudar(largura_m=l))
            a.setCheckable(True)
            a.setChecked(abs(porta.largura_m - larg) < 0.01)
        menu.addAction("Editar porta…", lambda: self.dock_props.raise_())

    # ================================================================ sessão
    def alternar_taverna(self):
        if self.servidor.aberto:
            if self.servidor.nomes():
                r = QMessageBox.question(self, "Fechar a taverna",
                                         "Tem jogador conectado. Fechar mesmo assim?")
                if r != QMessageBox.StandardButton.Yes:
                    return
            self._fechar_internet()
            self.servidor.fechar()
        else:
            porta = int(self.config.value("porta", PORTA_PADRAO))
            dialogo = DialogoAbrirTaverna(self, ServidorMestre.enderecos_locais(), porta)
            if not dialogo.exec():
                return
            porta = dialogo.porta.value()
            if not self.servidor.abrir(porta):
                QMessageBox.warning(self, "Não deu",
                                    f"Não consegui abrir a porta {porta}.\n"
                                    "Talvez outro programa esteja usando. Tente outra porta.")
                return
            self.config.setValue("porta", porta)
            self.abrir_pela_internet(porta)
        self._atualizar_jogadores()

    # ---------------------------------------------------------------- 🌐 entrar sem Radmin (v0.65)
    def abrir_pela_internet(self, porta: int, destino=None):
        """Pede pro roteador abrir a porta (UPnP), sem travar a tela. destino (testes): roteador falso."""
        from ..rede import upnp
        self.btn_internet.setVisible(True)
        self.btn_internet.setText("Abrindo pela internet…")
        self.btn_internet.setToolTip("Pedindo pro roteador abrir a porta (UPnP)…")
        args = {"destino": destino, "timeout": 1.0} if destino else {}
        self._upnp_thread = upnp.em_segundo_plano(lambda: upnp.abrir_porta(porta, **args), self._internet_pronta)

    def _internet_pronta(self, r: dict):
        self._upnp = dict(r, porta=self.servidor.porta)
        if not self.servidor.aberto:   # fechou a taverna enquanto o roteador respondia
            self._fechar_internet()
            return
        if r.get("ok"):
            self.btn_internet.setText(f"Aberta pela internet · {r['codigo']}")
            self.btn_internet.setToolTip("Clique pra copiar o código da sala e mandar pros amigos.")
        else:
            self.btn_internet.setText("Só pela rede local/Radmin (clique)")
            self.btn_internet.setToolTip("Clique pra ver por quê e o que fazer.")
        self.btn_internet.setVisible(True)

    def _fechar_internet(self):
        """Fecha no roteador a porta que a gente abriu (sem travar a tela)."""
        r, self._upnp = self._upnp, None
        self.btn_internet.setVisible(False)
        if r and r.get("ok") and r.get("roteador") is not None:
            from ..rede import upnp
            rot, porta = r["roteador"], r.get("porta")
            upnp.em_segundo_plano(lambda: rot.fechar(porta), lambda _r: None)

    def _mostrar_internet(self):
        r = self._upnp
        if r is None:
            return
        caixa = QMessageBox(self)
        caixa.setWindowTitle("Jogar pela internet")
        if r.get("ok"):
            caixa.setIcon(QMessageBox.Icon.Information)
            caixa.setText(f"<b>A taverna está aberta pela internet.</b><br><br>Mande este <b>código da sala</b> "
                          f"pros jogadores (eles colam no “Entrar na sessão”, no lugar do IP):"
                          f"<br><br><span style='font-size:18px'><b>{r['codigo']}</b></span><br><br>"
                          f"(É o seu IP de fora, {r['ip_externo']}, porta {r.get('porta')}.) Quem está no Radmin "
                          f"continua entrando pelo IP do Radmin, normalmente.")
            copiar = caixa.addButton("Copiar código", QMessageBox.ButtonRole.AcceptRole)
            caixa.addButton("Fechar", QMessageBox.ButtonRole.RejectRole)
            caixa.exec()
            if caixa.clickedButton() is copiar:
                QApplication.clipboard().setText(r["codigo"])
                self.statusBar().showMessage("Código da sala copiado.", 4000)
            return
        caixa.setIcon(QMessageBox.Icon.Warning)
        if r.get("cgnat"):
            motivo = ("<b>Sua internet não deixa receber conexões de fora</b> (a operadora usa CGNAT — é muito "
                      f"comum no Brasil; o roteador recebe o IP {r.get('ip_externo')}, que não é de verdade). "
                      "Abrir a porta não resolve.")
        else:
            motivo = (f"<b>O roteador não abriu a porta</b> ({r.get('motivo') or 'sem resposta'}). Às vezes o UPnP "
                      "está desligado nas configurações do roteador — dá pra ligar lá (procure “UPnP”), ou usar o "
                      "Radmin.")
        caixa.setText(motivo + "<br><br><b>Use o Radmin VPN</b> (de graça):<br>"
                      "1. Você e os jogadores instalam o Radmin VPN.<br>"
                      "2. Você cria uma rede (nome + senha) e manda pros amigos; eles entram nela.<br>"
                      "3. No “Abrir taverna”, o IP que começa com <b>26.</b> é o que vai pros jogadores.<br><br>"
                      "Quem está na mesma casa/rede entra pelo IP local, sem nada disso.")
        tentar = caixa.addButton("Tentar de novo", QMessageBox.ButtonRole.ActionRole)
        guia = caixa.addButton("Como conectar", QMessageBox.ButtonRole.HelpRole)   # (v0.81) o passo a passo
        caixa.addButton("Fechar", QMessageBox.ButtonRole.RejectRole)
        caixa.exec()
        if caixa.clickedButton() is guia:
            from .dialogos import abrir_como_conectar
            abrir_como_conectar(self)
        elif caixa.clickedButton() is tentar and self.servidor.aberto:
            self.abrir_pela_internet(self.servidor.porta)

    def _atualizar_jogadores(self):
        aberto = self.servidor.aberto
        self.a_taverna.setText("Fechar taverna" if aberto else "Abrir taverna")
        self.a_taverna.setIconText("Fechar taverna" if aberto else "Abrir taverna")
        nomes = self.servidor.nomes()
        if aberto:
            ips = ServidorMestre.enderecos_locais()
            ip = ips[0][0] if ips else "?"
            self.lbl_taverna.setText(f"Taverna aberta em {ip}:{self.servidor.porta} · "
                                     f"{len(nomes)} jogador(es)")
        else:
            self.lbl_taverna.setText("Taverna fechada")

        tokens = [t for t in self.servidor.cena.itens_do_usuario()
                  if isinstance(t, TokenItem) and t.dono]
        self.lista_jogadores.clear()
        if not aberto:
            self.lista_jogadores.addItem("Abra a taverna (menu Sessão)\npros jogadores entrarem.")
            return
        if not nomes:
            self.lista_jogadores.addItem("Esperando jogadores…")
        from .tema import tema_atual
        online = QIcon(pixmap_icone("circulo", "#3fbf5f", 16))
        offline = QIcon(pixmap_icone("circulo_vazio", tema_atual()["fraco"], 16))
        for nome in nomes:
            meus = [t.nome for t in tokens if mesmo_nome(t.dono, nome)]
            texto = f"{nome}   —   {', '.join(meus) if meus else 'sem token'}"
            self.lista_jogadores.addItem(QListWidgetItem(online, texto))
        # Tokens vinculados a alguém que ainda não entrou
        ausentes = sorted({t.dono for t in tokens
                           if not any(mesmo_nome(t.dono, n) for n in nomes)})
        for nome in ausentes:
            item = QListWidgetItem(offline, f"{nome}   —   offline")
            item.setForeground(Qt.GlobalColor.gray)
            self.lista_jogadores.addItem(item)

    # ================================================================ arquivo
    def _pode_descartar(self) -> bool:
        if not any(c.modificada for c in self.cenas):
            return True
        r = QMessageBox.question(
            self, "Alterações não salvas", "Quer salvar a cena antes?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel)
        if r == QMessageBox.StandardButton.Save:
            return self.salvar()
        return r == QMessageBox.StandardButton.Discard

    def nova_cena(self) -> bool:
        if not self._pode_descartar():
            return False
        dialogo = DialogoNovaAventura(self, self.pasta_aventuras(),
                                      lambda n: os.path.exists(self.caminho_da_aventura(n)))
        if not dialogo.exec():
            return False
        nome, tema = dialogo.dados()
        self.painel_props.soltar_referencias()
        self._ficar_so_com_a_cena_atual()
        self.cena.criar_camadas_padrao()
        self.painel_projetor.definir_galeria([])
        self._definir_diario([])
        self._definir_atlas({})
        self.servidor.recolher_projecao()
        self.cena.nome_aventura = nome
        self.cena.nome_aba = "Cenário 1"
        self.cena.definir_tema(tema)
        self.cena.definir_ferramenta("selecionar")
        self._recarregar_abas()
        self.caminho_cena = self.caminho_da_aventura(nome)
        self.salvar()  # já nasce salva, pro "Continuar" funcionar
        self.visao.centerOn(0, 0)
        self._atualizar_titulo()
        return True

    def abrir_cena(self, caminho=None) -> bool:
        if not self._pode_descartar():
            return False
        if not caminho:
            caminho, _ = QFileDialog.getOpenFileName(self, "Abrir sessão",
                                                     self.pasta_aventuras(), FILTRO_CENA)
        if not caminho:
            return False
        self.painel_props.soltar_referencias()
        try:
            dados = ler_aventura(caminho)
        except (OSError, ValueError, KeyError) as erro:
            QMessageBox.warning(self, "Não deu", f"Não consegui abrir a aventura:\n{erro}")
            return False
        self._ficar_so_com_a_cena_atual()
        abas = dados["abas"]
        atual = min(max(0, dados["aba_atual"]), len(abas) - 1)
        ao_vivo = min(max(0, dados["aba_ao_vivo"]), len(abas) - 1)
        try:
            cenas = []
            for i, aba in enumerate(abas):
                # a aba que vai ficar na tela reaproveita a cena atual (já ligada aos painéis)
                cena = self.cena if i == atual else self._nova_cena_vazia(aba.get("nome", ""))
                carregar_dados_na_cena(cena, aba, dados["tema"], dados["aventura"])
                cenas.append(cena)
        except (KeyError, ValueError, TypeError) as erro:
            QMessageBox.warning(self, "Não deu", f"Não consegui abrir a aventura:\n{erro}")
            self.cena.criar_camadas_padrao()
            return False
        for c in cenas:
            if c is not self.cena:
                self._registrar_cena(c)
        self.cenas = cenas
        self.indice_ao_vivo = ao_vivo
        self.painel_projetor.definir_galeria(dados.get("projetor", []))
        self._definir_diario(dados.get("diario", []))
        self._definir_atlas(dados.get("atlas") or {})
        self.servidor.recolher_projecao()
        self.servidor.definir_cena(self.cenas[ao_vivo])
        self._atualizar_andares_ao_vivo()
        self._recarregar_abas()
        self.caminho_cena = caminho
        self.config.setValue("ultima_cena", caminho)
        if not self.cena.nome_aventura:
            self.cena.nome_aventura = os.path.splitext(os.path.basename(caminho))[0]
        self.cena.definir_ferramenta("selecionar")
        self.slider_grid.blockSignals(True)
        self.slider_grid.setValue(int(self.cena.opacidade_grid * 100))
        self.slider_grid.blockSignals(False)
        QTimer.singleShot(0, self.visao.enquadrar_tudo)
        self._atualizar_titulo()
        return True

    @staticmethod
    def caminho_backup(caminho: str) -> str:
        base = caminho[:-len(EXTENSAO_CENA)] if caminho.lower().endswith(EXTENSAO_CENA) else caminho
        return f"{base} (cópia de segurança){EXTENSAO_CENA}"

    def _gravar(self, caminho: str):
        # Antes de sobrescrever, guarda a versão anterior como cópia de segurança
        import shutil
        if os.path.exists(caminho) and os.path.getsize(caminho) > 0:
            try:
                shutil.copy2(caminho, self.caminho_backup(caminho))
            except OSError:
                pass
        # grava num arquivo temporário e só depois troca (se a luz cair no meio, o antigo fica inteiro)
        temporario = caminho + ".salvando"
        salvar_aventura(temporario, self.cenas, self.cena.nome_aventura,
                        self.cena.tema, self.indice_ao_vivo, self.cenas.index(self.cena),
                        self.painel_projetor.galeria, self.diario, self.atlas.para_dict())
        os.replace(temporario, caminho)

    def salvar(self) -> bool:
        if not self.caminho_cena:
            return self.salvar_como()
        try:
            self._gravar(self.caminho_cena)
        except OSError as erro:
            QMessageBox.warning(self, "Não deu", f"Não consegui salvar:\n{erro}")
            return False
        self.config.setValue("ultima_cena", self.caminho_cena)
        self.statusBar().showMessage("Sessão salva.", 4000)
        self._atualizar_titulo()
        return True

    def salvar_automatico(self):
        if self.pilha.currentWidget() is not self.area_mesa:
            return
        if not any(c.modificada for c in self.cenas):
            return
        caminho = self.caminho_cena
        if not caminho:
            # ainda não foi salva: guarda na pasta de aventuras com um nome provisório
            nome = self.cena.nome_aventura or "Aventura sem nome"
            caminho = self.caminho_da_aventura(f"{nome} (automático)")
        try:
            self._gravar(caminho)
        except OSError as erro:
            self.statusBar().showMessage(f"⚠ Não consegui salvar automaticamente: {erro}", 8000)
            return
        # "Continuar sessão" abre esse arquivo se o PC desligar no meio
        self.config.setValue("ultima_cena", caminho)
        if not self.caminho_cena:
            for c in self.cenas:
                c.marcar_modificada(True)   # continua "não salvo" até ele escolher onde salvar
            self._ultimo_auto = caminho
        import time
        self.statusBar().showMessage(f"💾 Salvo automaticamente às {time.strftime('%H:%M')}.", 5000)
        self._atualizar_titulo()

    def salvar_como(self) -> bool:
        sugestao = self.caminho_da_aventura(self.cena.nome_aventura or "Minha aventura")
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar sessão", sugestao, FILTRO_CENA)
        if not caminho:
            return False
        if not caminho.lower().endswith(EXTENSAO_CENA):
            caminho += EXTENSAO_CENA
        self.caminho_cena = caminho
        return self.salvar()

    def closeEvent(self, event):
        if self._pode_descartar():
            r = getattr(self, "_upnp", None)
            if r and r.get("ok") and r.get("roteador") is not None:   # fecha a porta no roteador (rapidinho)
                try:
                    r["roteador"].fechar(r.get("porta"))
                except Exception:
                    pass
            self._upnp = None
            self.servidor.fechar()
            event.accept()
        else:
            event.ignore()
