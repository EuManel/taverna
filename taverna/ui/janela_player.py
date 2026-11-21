"""
Janela do Player.

Mostra a mesa do mestre em tempo real. O player só arrasta o(s) token(s)
que o mestre vinculou ao nome dele. Se a conexão cair, tenta voltar sozinho.
"""

from PyQt6.QtCore import QSettings, Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from ..config import APP_NOME, APP_VERSAO
from ..mesa.cena_player import CenaPlayer
from ..mesa.visao import MesaVisao
from ..rede.cliente import ClienteRede
from ..rede.protocolo import PORTA_PADRAO
from .dialogos import DialogoConectar
from .tela_inicial import TelaInicial
from .tema import gerar_qss, guardar_tema_preferido, tema_preferido
from ..temas import tema as dados_tema
from .tema import icone_app


class JanelaPlayer(QMainWindow):
    def __init__(self, lancador=None):
        super().__init__()
        self.lancador = lancador   # (v0.49) aberto pelo launcher: "voltar pro início" volta pra ele
        self.setWindowIcon(icone_app())
        self.setWindowTitle(f"{APP_NOME} Player")
        self.resize(1280, 800)
        self.config = QSettings("Taverna", "Player")

        self.cena = CenaPlayer(self)
        self.cena.ao_mudar_tema = self._tema_mudou
        self.visao = MesaVisao(self.cena)
        self.visao.setAcceptDrops(False)

        self.tela_inicial = TelaInicial("Player", [
            ("Ingressar na sessão", "entrar"),
            ("Sair", "sair"),
        ], tema_inicial=tema_preferido())
        self.tela_inicial.tema_escolhido.connect(self._tema_da_tela_inicial)
        self.tela_inicial.escolhido.connect(self._escolha_inicial)
        self.pilha = QStackedWidget()
        self.pilha.addWidget(self.tela_inicial)
        self.pilha.addWidget(self.visao)
        self.setCentralWidget(self.pilha)

        self.cliente = ClienteRede(self)
        from ..rede.livros import LivrosPlayer
        self.livros = LivrosPlayer(self.cliente, self)   # livros que o mestre libera (v0.43)
        self.livros.aviso.connect(lambda t: self.statusBar().showMessage(t, 10000))
        self.cena.ao_mover = self.cliente.mover
        self.cliente.conectado.connect(self._conectou)
        self.cliente.recusado.connect(self._recusado)
        self.cliente.desconectado.connect(self._caiu)
        self.cliente.estado_recebido.connect(self._estado)
        self.cliente.cursor_recebido.connect(self.cena.cursores.atualizar)
        self._criar_paineis()
        from ..mesa.vida import Limitador
        self._enviar_cursor = Limitador(0.05, self.cliente.cursor)

        self.ip = ""
        self.porta = PORTA_PADRAO
        self.nome = ""
        self._ja_entrou = False
        self._primeiro_estado = True
        self._reconectar = QTimer(self)
        self._reconectar.setInterval(3000)
        self._reconectar.timeout.connect(
            lambda: self.cliente.conectar(self.ip, self.porta, self.nome))

        # Faixa de aviso por cima da mesa
        self.faixa = QLabel(self.visao)
        self.faixa.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.faixa.setStyleSheet(
            "background: rgba(20,16,12,225); color: #e8dcc4; border: 1px solid #c9a24a;"
            "border-radius: 8px; padding: 10px 18px; font-size: 11pt;")
        self.faixa.hide()

        from .acabamento import Icones, enfeitar_dock, espacador, estilo_barra
        barra = self.addToolBar("Ferramentas")
        self.barra = barra
        estilo_barra(barra)
        self.icones = Icones()
        barra.setMovable(False)
        a_meu = QAction("🎯  Meu token", self)
        a_meu.setShortcut(QKeySequence("C"))
        a_meu.setToolTip("Centralizar a câmera no seu token (C)\n"
                         "Q / E giram pra onde ele olha · F olha pro mouse\n"
                         "P marca um ponto no mapa pra todos · segure M e arraste pra medir")
        a_meu.triggered.connect(self.centralizar_meu_token)
        a_tudo = QAction("🗺  Ver mesa toda", self)
        a_tudo.setShortcut(QKeySequence("Home"))
        a_tudo.triggered.connect(self.visao.enquadrar_tudo)
        a_cursores = QAction("👆  Mouse dos outros", self)
        a_cursores.setCheckable(True)
        a_cursores.setChecked(True)
        a_cursores.setToolTip("Mostrar/esconder a setinha dos outros jogadores e do mestre")
        a_cursores.toggled.connect(self.cena.cursores.definir_visiveis)
        # Girar pra onde olha (se o mestre liberar)
        for atalho, graus in (("Q", -15), ("E", 15)):
            a = QAction(f"girar {atalho}", self)
            a.setShortcut(QKeySequence(atalho))
            a.triggered.connect(lambda _=False, g=graus: self.girar(g))
            self.addAction(a)
        a_olhar = QAction("olhar", self)
        a_olhar.setShortcut(QKeySequence("F"))
        a_olhar.triggered.connect(lambda: self.girar(olhar_mouse=True))
        self.addAction(a_olhar)
        a_bib = QAction("📚  Biblioteca", self)
        a_bib.setShortcut(QKeySequence("Ctrl+B"))
        a_bib.setToolTip("Regras, magias, raças, classes, itens (SRD) e os seus PDFs")
        a_bib.triggered.connect(self.abrir_biblioteca)
        self._a_bib = a_bib
        a_ficha = QAction("📜  Minha ficha", self)
        a_ficha.setShortcut(QKeySequence("Ctrl+P"))
        a_ficha.setToolTip("A ficha do seu personagem (Ctrl+P). Só você e o mestre veem.\n"
                           "Dá pra importar a ficha em PDF preenchível.")
        a_ficha.triggered.connect(self.abrir_minha_ficha)
        a_pdf = QAction("📄  Ficha em PDF (qualquer sistema)", self)
        a_pdf.setIconText("📄 Ficha PDF")
        a_pdf.setToolTip("Importar e preencher a ficha do seu sistema (PDF editável)")
        a_pdf.triggered.connect(self.abrir_fichas_pdf)
        from PyQt6.QtWidgets import QMenu as _Menu, QToolButton as _TB
        from ..graficos import menu_graficos
        self._menu_graficos = _Menu(self)
        self._grupo_graficos = menu_graficos(self._menu_graficos, self)
        self._menu_graficos.addSeparator()
        a_ret = self._menu_graficos.addAction("Retratos do grupo (na esquerda da mesa)")
        a_ret.setCheckable(True)
        a_ret.setChecked(self.config.value("retratos_grupo", True, type=bool))
        a_ret.toggled.connect(lambda v: self._alternar_retratos(v))
        self.btn_graficos = _TB()
        self.btn_graficos.setText("Gráficos")
        self.btn_graficos.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.icones.ligar(self.btn_graficos.setIcon, "engrenagem")
        self.btn_graficos.setToolTip("Gráficos: Baixo / Médio / Alto, tela tremer e clarear")
        self.btn_graficos.setMenu(self._menu_graficos)
        self.btn_graficos.setPopupMode(_TB.ToolButtonPopupMode.InstantPopup)
        a_sair = QAction("🚪  Sair da mesa", self)
        a_sair.triggered.connect(self.sair_da_mesa)
        for acao, curto, nome_icone in ((a_meu, "Meu token", "alvo"), (a_tudo, "Mesa toda", "enquadrar"),
                                        (a_cursores, "Mouses", "cursor"), (a_ficha, "Ficha", "ficha"),
                                        (a_pdf, "Ficha PDF", "pdf"), (a_bib, "Biblioteca", "biblioteca"),
                                        (a_sair, "Sair", "sair")):
            acao.setIconText(curto)
            self.icones.ligar(acao.setIcon, nome_icone)
        for acao, (curto, nome_icone) in zip(self.acoes_paineis, (("Combate", "combate"), ("Dados", "dados"),
                                                                   ("Chat", "chat"), ("Info", "info"),
                                                                   ("Magia", "magia"), ("Som", "som"),
                                                                   ("Imagens", "imagens"))):
            acao.setIconText(curto)
            self.icones.ligar(acao.setIcon, nome_icone)
        for dock, nome_icone in zip(self.docks, ("combate", "dados", "chat", "info", "magia", "som")):
            enfeitar_dock(dock, nome_icone)
        barra.addAction(a_meu)
        # (v0.64.1) ✏ criar o próprio token (se ainda não tem) ou editar o dele — sem precisar acertar o token
        self.a_meu_token = QAction("✏  Criar meu token", self)
        self.a_meu_token.setToolTip("Criar o seu token (só um, o seu) — ou, se já tem, mudar nome, cor e imagem.\n"
                                    "Duplo clique no seu token também edita.")
        self.a_meu_token.triggered.connect(self.meu_token)
        self.a_meu_token.setIconText("Criar token")
        self.icones.ligar(self.a_meu_token.setIcon, "token")
        barra.addAction(self.a_meu_token)
        barra.addAction(a_tudo)
        barra.addAction(a_cursores)
        # 📜 Ficha: clique = ficha D&D · setinha = ficha em PDF de qualquer sistema
        from PyQt6.QtWidgets import QMenu, QToolButton
        menu_ficha = QMenu(self)
        menu_ficha.addAction(a_ficha)
        a_inv = QAction("🎒  Meu inventário", self)   # (v0.48)
        a_inv.setShortcut(QKeySequence("I"))
        a_inv.setToolTip("O que o seu personagem carrega (I). O que você pega no chão ou nos baús vai pra cá.")
        a_inv.triggered.connect(lambda: self.abrir_minha_ficha(None, "inventario"))
        self.addAction(a_inv)
        menu_ficha.addAction(a_inv)
        menu_ficha.addAction(a_pdf)
        self.btn_ficha = QToolButton()
        self.btn_ficha.setDefaultAction(a_ficha)
        self.btn_ficha.setMenu(menu_ficha)
        self.btn_ficha.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.btn_ficha.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        barra.addWidget(self.btn_ficha)
        a_diario = QAction("📓  Diário da campanha", self)
        a_diario.setIconText("Diário")
        self.icones.ligar(a_diario.setIcon, "diario")
        a_diario.setShortcut(QKeySequence("Ctrl+Shift+D"))
        a_diario.setToolTip("O que o mestre compartilhou + suas anotações (Ctrl+Shift+D)")
        a_diario.triggered.connect(self.abrir_diario)
        self.a_diario = a_diario
        barra.addAction(a_diario)
        barra.addAction(a_bib)
        barra.addSeparator()
        for a in self.acoes_paineis:
            barra.addAction(a)
        barra.addWidget(espacador())
        # (v0.58) ❓ Ajuda: tela de atalhos (F1)
        from .atalhos import abrir as abrir_atalhos
        self.a_atalhos = QAction("⌨  Atalhos", self)
        self.a_atalhos.setShortcut(QKeySequence("F1"))
        self.a_atalhos.setToolTip("Todos os atalhos do jogador (F1)")
        self.a_atalhos.triggered.connect(lambda: abrir_atalhos(self, "jogador"))
        self.addAction(self.a_atalhos)
        self._menu_ajuda = _Menu(self)
        self._menu_ajuda.addAction(self.a_atalhos)
        from .dicas import mostrar as mostrar_dicas
        self._menu_ajuda.addAction("💡  Dicas de primeiro acesso", lambda: mostrar_dicas(self, "jogador", forcar=True))
        self._menu_ajuda.addSeparator()
        from .reportar import abrir as abrir_reportar
        self.a_reportar = self._menu_ajuda.addAction("🐞  Reportar problema…", lambda: abrir_reportar(self, "jogador"))
        self.btn_ajuda = _TB()
        self.btn_ajuda.setText("Ajuda")
        self.btn_ajuda.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.icones.ligar(self.btn_ajuda.setIcon, "info")
        self.btn_ajuda.setToolTip("Ajuda: atalhos (F1)")
        self.btn_ajuda.setMenu(self._menu_ajuda)
        self.btn_ajuda.setPopupMode(_TB.ToolButtonPopupMode.InstantPopup)
        barra.addWidget(self.btn_ajuda)
        barra.addWidget(self.btn_graficos)
        barra.addAction(a_sair)

        self.lbl_status = QLabel("Desconectado")
        self.lbl_zoom = QLabel("Zoom 100%")
        self.statusBar().addPermanentWidget(self.lbl_status)
        self.statusBar().addPermanentWidget(self.lbl_zoom)
        self.visao.zoom_mudou.connect(lambda z: self.lbl_zoom.setText(f"Zoom {z * 100:.0f}%"))
        self.visao.cursor_moveu.connect(lambda p: self._enviar_cursor(p.x(), p.y()))
        self.visao.cursor_saiu.connect(lambda: self._enviar_cursor(None, None))
        self.mostrar_inicio()
        from .acabamento import iconizar
        iconizar(self)   # emojis dos painéis, botões e menus → ícones do tema

    def _aplicar_tema(self, chave):
        from PyQt6.QtWidgets import QApplication
        from .acabamento import ICONES_GLOBAIS
        QApplication.instance().setStyleSheet(gerar_qss(chave))
        if hasattr(self, "icones"):
            self.icones.atualizar()
        ICONES_GLOBAIS.atualizar()

    def _tema_mudou(self, chave):
        from PyQt6.QtWidgets import QApplication
        if self.pilha.currentWidget() is not self.tela_inicial:
            self._aplicar_tema(chave)
        self.visao.definir_fundo(dados_tema(chave)["mesa"])

    def _tema_da_tela_inicial(self, chave):
        from PyQt6.QtWidgets import QApplication
        guardar_tema_preferido(chave)
        self._aplicar_tema(chave)

    # ------------------------------------------------------------ telas
    def mostrar_inicio(self, aviso: str = ""):
        self.barra.hide()
        self.statusBar().hide()
        self.faixa.hide()
        self._paineis_visiveis(False)
        self.tela_inicial.info.setText(aviso)
        self.pilha.setCurrentWidget(self.tela_inicial)
        from PyQt6.QtWidgets import QApplication
        self._aplicar_tema(self.tela_inicial.tema)
        self.setWindowTitle(f"{APP_NOME} Player")
        if self.lancador is not None:
            self.lancador.voltar(self, aviso)

    def mostrar_mesa(self):
        self.barra.show()
        self.statusBar().show()
        self._paineis_visiveis(True)
        self.pilha.setCurrentWidget(self.visao)
        from PyQt6.QtWidgets import QApplication
        self._aplicar_tema(self.cena.tema)
        from .dicas import agendar_primeira_vez
        agendar_primeira_vez(self, "jogador")   # 💡 (v0.66) dicas de primeiro acesso, uma vez só
        self.visao.setFocus()

    def _escolha_inicial(self, chave):
        if chave == "entrar":
            self.pedir_conexao()
        elif chave == "sair":
            self.close()

    # ------------------------------------------------------------ faixa
    def _mostrar_faixa(self, texto):
        self.faixa.setText(texto)
        self.faixa.adjustSize()
        self.faixa.move((self.visao.width() - self.faixa.width()) // 2, self._topo_faixa())
        self.faixa.show()
        self.faixa.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.faixa.isVisible():
            self.faixa.move((self.visao.width() - self.faixa.width()) // 2, self._topo_faixa())

    def _topo_faixa(self):
        # se a faixa de turnos estiver aparecendo, o aviso vem logo abaixo dela
        turnos = getattr(self, "faixa_turnos", None)
        if turnos is not None and turnos.isVisible():
            return turnos.y() + turnos.height() + 10
        return 16

    # ------------------------------------------------------------ conexão
    def pedir_conexao(self, erro="") -> bool:
        dialogo = DialogoConectar(
            self, self.config.value("nome", ""), self.config.value("ip", ""),
            int(self.config.value("porta", PORTA_PADRAO)), erro)
        if not dialogo.exec():
            return False
        self.nome = dialogo.nome.text().strip()
        # (v0.65) aceita o CÓDIGO DA SALA (TAV-XXXXX-XXXXX), "IP:porta" ou só o IP
        from ..rede.upnp import ler_endereco
        self.ip, self.porta = ler_endereco(dialogo.ip.text(), dialogo.porta.value())
        self.config.setValue("nome", self.nome)
        self.config.setValue("ip", self.ip)
        self.config.setValue("porta", self.porta)
        self._ja_entrou = False
        self._primeiro_estado = True
        self.lbl_status.setText(f"Conectando em {self.ip}:{self.porta}…")
        self.tela_inicial.info.setText("Batendo na porta da taverna…")
        self.cliente.conectar(self.ip, self.porta, self.nome)
        return True

    def _conectou(self, nome):
        self._reconectar.stop()
        self._ja_entrou = True
        self.livros.ao_conectar()   # o mestre fica sabendo dos PDFs da minha biblioteca
        self.nome = nome
        self.cena.meu_nome = nome
        self.faixa.hide()
        self.tela_inicial.info.setText("")
        self.mostrar_mesa()
        if self.lancador is not None:
            self.lancador.entrou(self)
        self.lbl_status.setText(f"Conectado: {nome} · {self.ip}:{self.porta}")
        self.setWindowTitle(f"{nome} — {APP_NOME} Player {APP_VERSAO}")

    def _recusado(self, motivo):
        self._reconectar.stop()
        self.cena.limpar()
        self.mostrar_inicio()
        self.pedir_conexao(motivo)

    def _caiu(self, motivo):
        if self._ja_entrou:
            # Já estava jogando: tenta voltar sozinho
            self.lbl_status.setText("Conexão perdida")
            self._mostrar_faixa("A conexão com o mestre caiu. Tentando voltar…")
            if not self._reconectar.isActive():
                self._reconectar.start()
        elif not self._reconectar.isActive():
            self.mostrar_inicio()
            self.pedir_conexao(f"Não deu pra entrar: {motivo}\n"
                               "Confira o IP, a porta e se o Radmin está ligado.")

    def _estado(self, estado):
        self.cena.aplicar_estado(estado, self.cliente.imagens)
        self._atualizar_botao_token()
        andar = estado.get("andar") or ""   # 🏢 andares (v0.46): o andar onde está o meu token
        if andar != getattr(self, "_andar", ""):
            self._andar = andar
            if andar:
                self.statusBar().showMessage(f"🏢 Você está no {andar}. (Duplo clique numa escada, "
                                             "perto dela, pra subir/descer.)", 8000)
        self.cena.andar_atual = andar
        aventura = self.cena.nome_aventura
        self.setWindowTitle(f"{self.nome}{' · ' + aventura if aventura else ''}"
                            f" — {APP_NOME} Player {APP_VERSAO}")
        cenario = estado.get("cenario", "")
        if self._primeiro_estado:
            self._primeiro_estado = False
            self._cenario = cenario
            QTimer.singleShot(0, self._enquadrar_inicial)
        elif cenario != getattr(self, "_cenario", cenario):
            # O mestre trocou o cenário (aba): enquadra o lugar novo
            self._cenario = cenario
            QTimer.singleShot(0, self._enquadrar_inicial)
            nome = estado.get("cenario_nome", "")
            self._mostrar_faixa(f"Novo cenário: {nome}" if nome else "O mestre mudou o cenário")
            QTimer.singleShot(2500, self.faixa.hide)
        self._atualizar_paineis(estado)
        meus = self.cena.meus_tokens()
        if not meus and self._ja_entrou:
            self.statusBar().showMessage(
                f"Você ainda não tem token. Peça pro mestre vincular um a “{self.nome}”.")
        elif meus:
            self.statusBar().clearMessage()
        from PyQt6.QtGui import QColor
        from ..mesa.vida import cor_do_nome
        self.visao.definir_cor_cursor(QColor(meus[0].cor) if meus else cor_do_nome(self.nome))   # 🧤

    # ------------------------------------------------------------ etapa 6
    def _criar_paineis(self):
        from PyQt6.QtWidgets import QDockWidget
        from .painel_combate import PainelCombatePlayer
        from .painel_dados import PainelDados
        from .painel_info import PainelInfoPlayer
        recursos = (QDockWidget.DockWidgetFeature.DockWidgetMovable
                    | QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.painel_combate = PainelCombatePlayer()
        self.painel_combate.rolar_iniciativa.connect(
            lambda expr, uid: self.cliente.rolar(expr, "iniciativa", uid))
        self.painel_combate.encerrar_turno.connect(lambda: self.cliente.enviar({"tipo": "encerrar_turno"}))
        self.painel_dados = PainelDados(mestre=False)
        self.painel_dados.pedir_rolagem.connect(lambda expr, _p: self.cliente.rolar(expr))
        self.painel_dados.pedir_pronta.connect(lambda expr, motivo, _p: self.cliente.rolar(expr, motivo))
        # 💬 chat (painel próprio, separado dos dados — v0.31.1)
        from .painel_chat import PainelChat
        self.painel_chat = PainelChat(mestre=False)
        self.painel_chat.enviar.connect(
            lambda texto, para, _como: self.cliente.enviar({"tipo": "chat", "texto": texto, "para": para}))
        self.painel_chat.nova_mensagem.connect(self._aviso_chat)
        self.diario = []   # (v0.46.1) a rolagem só entra no histórico/chat quando o dado PARA
        self.cliente.erro_dados.connect(self.painel_dados.mostrar_erro)
        self.painel_info = PainelInfoPlayer()
        from .painel_atmosfera import PainelAtmosfera
        self.painel_atmosfera = PainelAtmosfera(mestre=False)
        self.docks = []
        # ordem: 0 combate · 1 dados · 2 chat · 3 informações · 4 atmosfera (· 5 som, criado depois)
        for titulo, widget, nome in (("COMBATE", self.painel_combate, "dock_combate"),
                                     ("DADOS", self.painel_dados, "dock_dados"),
                                     ("CHAT", self.painel_chat, "dock_chat"),
                                     ("INFORMAÇÕES", self.painel_info, "dock_info"),
                                     ("ATMOSFERA", self.painel_atmosfera, "dock_atmosfera")):
            dock = QDockWidget(titulo, self)
            dock.setObjectName(nome)
            from .tema import rolavel
            dock.setWidget(widget if widget in (self.painel_atmosfera, self.painel_chat) else rolavel(widget))
            dock.setFeatures(recursos)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            dock.hide()
            self.docks.append(dock)
        self.dock_dados, self.dock_chat = self.docks[1], self.docks[2]
        self.resizeDocks(self.docks[:1], [300], Qt.Orientation.Horizontal)
        self.resizeDocks(self.docks, [220, 260, 300, 220, 300], Qt.Orientation.Vertical)
        self.tabifyDockWidget(self.docks[3], self.docks[4])
        # Botões na barra pra abrir/fechar (começam fechados)
        self.acoes_paineis = []
        for dock, texto, atalho in ((self.docks[0], "⚔  Combate", "Ctrl+K"),
                                    (self.docks[1], "🎲  Dados", "Ctrl+D"),
                                    (self.docks[2], "💬  Chat", "Ctrl+E"),
                                    (self.docks[3], "📋  Informações", "Ctrl+I"),
                                    (self.docks[4], "✨  Templates e lápis", "Ctrl+T")):
            a = dock.toggleViewAction()
            a.setText(texto)
            a.setShortcut(QKeySequence(atalho))
            a.setToolTip(f"Abrir/fechar o painel ({atalho})")
            self.acoes_paineis.append(a)
        self._abertos = []
        from .sobreposicoes import AvisoRolagem, FaixaTurnos
        self.faixa_turnos = FaixaTurnos(self.visao, mestre=False)
        self.faixa_turnos.abrir_painel.connect(lambda: (self.docks[0].show(), self.docks[0].raise_()))
        self.faixa_turnos.resolver = self._cartao_do_id
        self.faixa_turnos.centralizar.connect(self._centralizar_uid)
        # Retratos do grupo (estilo Baldur's Gate), na esquerda da mesa
        from .retratos import PainelGrupo
        self._grupo = []
        self.painel_grupo = PainelGrupo(self.visao)
        self.painel_grupo.centralizar.connect(self._centralizar_uid)
        self.painel_grupo.abrir_ficha.connect(self._ficha_do_retrato)
        self.painel_grupo.definir_ligado(self.config.value("retratos_grupo", True, type=bool))
        self.aviso_rolagem = AvisoRolagem(self.visao)
        from ..mesa.ping import pingar
        from .painel_dados import cor_do_nome

        def meu_ping(pos):
            pingar(self.cena, pos.x(), pos.y(), self.nome, cor_do_nome(self.nome))
            self.cliente.ping(pos.x(), pos.y())
        self.visao.ping_pedido.connect(meu_ping)
        self.cliente.ping_recebido.connect(
            lambda nome, x, y: pingar(self.cena, x, y, nome, cor_do_nome(nome)))
        # Baús e outros objetos interativos
        from .janela_conteudo import JanelaConteudo
        self.janela_conteudo = JanelaConteudo(self)
        self.janela_conteudo.pegar.connect(self.cliente.pegar)
        self.cena.ao_interagir = self.cliente.interagir
        self.cena.ao_editar_meu = self.editar_meu_token   # (v0.64.1) duplo clique no próprio token
        self.cena.ao_mover_prop = self.cliente.mover_prop
        self.cena.ao_abrir_porta = self.cliente.porta
        self.cliente.conteudo_recebido.connect(self.janela_conteudo.mostrar)

        def aviso(texto):
            longo = texto.startswith("\u200b")   # mensagem de armadilha/mestre: fica mais tempo
            self._mostrar_faixa(texto.lstrip("\u200b"))
            QTimer.singleShot(7000 if longo else 2500, self.faixa.hide)
        self.cliente.aviso_recebido.connect(aviso)
        # Dados 3D rolando na mesa (o resultado veio do mestre; aqui só a animação)
        from ..dados3d.overlay import PainelDados3D
        self.dados3d = PainelDados3D(self.visao)
        self.cliente.rolagem_recebida.connect(self._rolagem_na_mesa)
        self.dados3d.revelar.connect(self._mostrar_rolagem)
        self._criar_atmosfera()
        self.visao.menu_pedido.connect(self._menu_contexto)   # (v0.48) botão direito = acesso rápido

    # ------------------------------------------------------------ (v0.48) botão direito do jogador
    def _menu_contexto(self, item, pos_tela, pos_cena):
        from PyQt6.QtWidgets import QMenu
        from ..mesa.props import PropItem
        from ..mesa.token import TokenItem
        from ..rede.protocolo import mesmo_nome
        from .acabamento import iconizar_menu
        menu = QMenu(self)
        meu = isinstance(item, TokenItem) and bool(item.dono) and mesmo_nome(item.dono, self.nome)
        if meu:
            menu.addSection(item.nome)
            menu.addAction("✨ Usar magia", lambda t=item: self.abrir_minha_ficha(t, "magias"))
            menu.addAction("🎒 Inventário", lambda t=item: self.abrir_minha_ficha(t, "inventario"))
            menu.addAction("📜 Ficha", lambda t=item: self.abrir_minha_ficha(t))
            menu.addAction("🎲 Rolar d20", lambda t=item: self.cliente.rolar("1d20", "", t.uid))
            if self.visao.pelos_olhos() is item:   # (v0.75) 👁 câmera por cima do ombro
                menu.addAction("👁 Sair do pelos olhos", self.visao.sair_dos_olhos)
            else:
                menu.addAction("👁 Ver pelos olhos", lambda t=item: self.visao.ver_pelos_olhos(t))
            if self.painel_atmosfera.btn_lancar.isEnabled():
                menu.addAction("🎯 Lançar daqui (bola de fogo, jato…)",
                               lambda: self.painel_atmosfera.btn_lancar.setChecked(True))
            menu.addSeparator()
            menu.addAction("✏ Editar meu token (nome, cor, imagem)…", lambda t=item: self.editar_meu_token(t))
        elif isinstance(item, PropItem):
            menu.addSection(item.nome)
            if item.tipo == "escada":
                menu.addAction("🏢 Subir / descer a escada", lambda u=item.uid: self.cliente.interagir(u))
            elif getattr(item, "coletavel", False) or getattr(item, "solto", False):
                menu.addAction("✋ Pegar", lambda u=item.uid: self.cliente.interagir(u))
            elif item.interativo:
                menu.addAction("✋ Abrir / mexer", lambda u=item.uid: self.cliente.interagir(u))
        elif isinstance(item, TokenItem) and getattr(item, "estado", ""):
            menu.addSection(item.nome)
            menu.addAction("🔍 Revistar", lambda u=item.uid: self.cliente.interagir(u))
        if self.visao.pelos_olhos() is not None and not meu:
            menu.addAction("👁 Sair do pelos olhos", self.visao.sair_dos_olhos)
        if not menu.isEmpty():
            menu.addSeparator()
        menu.addAction("📍 Marcar este ponto pra todos", lambda p=pos_cena: self.visao.ping_pedido.emit(p))
        if not meu and self.cena.meus_tokens():
            menu.addAction("🎯 Ir pro meu token", self.centralizar_meu_token)
            menu.addAction("🎒 Meu inventário", lambda: self.abrir_minha_ficha(None, "inventario"))
        iconizar_menu(menu).exec(pos_tela)

    def meu_token(self):
        """Botão ✏: edita o token dele (se já tem) ou cria."""
        meus = self.cena.meus_tokens()
        if meus:
            self.editar_meu_token(meus[0])
        else:
            self.criar_meu_token()

    def criar_meu_token(self, dados: dict | None = None):
        """(v0.64.1) O jogador cria o PRÓPRIO token: só um, sempre dele (o mestre confere e recusa se já tiver).
        dados (testes) pula o diálogo."""
        import base64
        from .dialogos import DialogoToken, reduzir_imagem
        if self.cena.meus_tokens():
            self.statusBar().showMessage("Você já tem um token — use ✏ pra editar.", 5000)
            return False
        if dados is None:
            d = DialogoToken(self, do_jogador=True, tipo_inicial="jogador")
            d.setWindowTitle("Criar meu token")
            if not d.exec():
                return False
            dados = d.dados()
        centro = self.visao.centro_da_visao()
        msg = {"tipo": "criar_token", "nome": dados.get("nome") or self.nome, "cor": dados.get("cor", "#3f6b4a"),
               "x": centro.x(), "y": centro.y()}
        for campo, lado in (("imagem", 512), ("retrato", 768)):
            bruto = dados.get(campo)
            msg[campo] = base64.b64encode(reduzir_imagem(bruto, lado)).decode() if bruto else None
        self.cliente.enviar(msg)
        from PyQt6.QtGui import QColor
        self.visao.definir_cor_cursor(QColor(msg["cor"]))
        self.statusBar().showMessage("🧙 Token criado (o mestre recebe na hora).", 5000)
        return True

    def _atualizar_botao_token(self):
        a = getattr(self, "a_meu_token", None)
        if a is not None:
            tem = bool(self.cena.meus_tokens())
            a.setText("✏  Editar meu token" if tem else "✏  Criar meu token")
            a.setIconText("Editar token" if tem else "Criar token")   # (o que aparece embaixo do ícone)

    def editar_meu_token(self, token):
        """O jogador muda nome, cor, imagem e retrato do PRÓPRIO token (o mestre recebe e confere o dono)."""
        import base64
        from .dialogos import DialogoToken, reduzir_imagem
        d = DialogoToken(self, token=token, do_jogador=True)
        if not d.exec():
            return
        dados = d.dados()
        msg = {"tipo": "editar_token", "id": token.uid, "nome": dados["nome"], "cor": dados["cor"]}
        for campo, lado in (("imagem", 512), ("retrato", 768)):
            bruto = dados.get(campo)
            msg[campo] = base64.b64encode(reduzir_imagem(bruto, lado)).decode() if bruto else None
        self.cliente.enviar(msg)
        from PyQt6.QtGui import QColor
        self.visao.definir_cor_cursor(QColor(dados["cor"]))
        self.statusBar().showMessage("✏ Token atualizado (o mestre recebe na hora).", 4000)

    # ------------------------------------------------------------ etapa 10
    def _criar_atmosfera(self):
        from .clima import ClimaOverlay
        self.clima_overlay = ClimaOverlay(self.visao.viewport())
        p = self.painel_atmosfera
        p.definir_cena(self.cena)
        p.ferramenta.connect(self._definir_ferramenta)
        p.mostrar_clima.connect(self.clima_overlay.definir_ligado)
        p.apagar_templates.connect(lambda: self.cliente.enviar({"tipo": "apagar_efeitos"}))
        p.apagar_desenhos.connect(lambda: self.cliente.enviar({"tipo": "apagar_tracos"}))
        self.cena.ao_mudar_clima = self._clima_mudou
        self.visao.efeito_pedido.connect(lambda d: self.cliente.enviar(dict(d, tipo="efeito")))
        self.visao.lancar_pedido.connect(lambda d: self.cliente.enviar(dict(d, tipo="lancar")))
        self.visao.traco_pedido.connect(lambda t: self.cliente.enviar(dict(t, tipo="traco")))
        self.visao.ferramenta_saiu.connect(lambda: self._definir_ferramenta("selecionar"))
        self.cliente.outra_mensagem.connect(self._outra_mensagem)
        # som e música
        from .audio import TocadorSons
        from .musica import PlayerYouTube, SeguidorDeMusica
        self.tocador = TocadorSons(self)
        self.player_musica = PlayerYouTube()
        self.seguidor_musica = SeguidorDeMusica(self.player_musica)
        caixa = QWidget()
        lay = QVBoxLayout(caixa)
        lay.setContentsMargins(8, 6, 8, 8)
        self.lbl_musica = QLabel("Nada tocando.")
        self.lbl_musica.setWordWrap(True)
        lay.addWidget(self.lbl_musica)
        # o vídeo fica num mini player no canto da mesa (não ocupa a lateral)
        from .sobreposicoes import MiniPlayer
        self.mini_player = MiniPlayer(self.visao, self.player_musica)
        from PyQt6.QtWidgets import QSlider, QCheckBox
        for texto, valor, funcao in (("🎵 Música", 70, self.player_musica.volume),
                                     ("🔊 Efeitos", 80, lambda v: self.tocador.definir_volume(v / 100))):
            linha = QHBoxLayout()
            linha.addWidget(QLabel(texto))
            s = QSlider(Qt.Orientation.Horizontal)
            s.setRange(0, 100)
            s.setValue(valor)
            s.valueChanged.connect(funcao)
            linha.addWidget(s, 1)
            lay.addLayout(linha)
        self.player_musica.volume(70)
        self.ck_mudo = QCheckBox("🔇 Silenciar tudo")
        self.ck_mudo.toggled.connect(self._mudo)
        lay.addWidget(self.ck_mudo)
        lay.addStretch(1)
        from PyQt6.QtWidgets import QDockWidget
        self.dock_musica = QDockWidget("SOM E MÚSICA", self)
        self.dock_musica.setObjectName("dock_musica")
        self.dock_musica.setWidget(caixa)
        self.dock_musica.setFeatures(self.docks[0].features())
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_musica)
        self.dock_musica.hide()
        a = self.dock_musica.toggleViewAction()
        a.setText("🎵  Som e música")
        a.setIconText("🎵 Som")
        a.setShortcut(QKeySequence("Ctrl+M"))
        a.setToolTip("Volumes da música e dos efeitos (Ctrl+M)")
        self.a_musica = a
        self.acoes_paineis.append(a)
        self.docks.append(self.dock_musica)

        # projetor
        from .projetor import ProjecaoOverlay
        self.projecao = ProjecaoOverlay(self.visao)
        self._seq_projecao = None
        self.imagens_recebidas = []
        a = QAction("📽  Imagens do mestre", self)
        a.setIconText("📽 Imagens")
        a.setToolTip("Tudo que o mestre já mostrou nesta sessão")
        a.triggered.connect(self._galeria_recebidas)
        self.acoes_paineis.append(a)

    def abrir_fichas_pdf(self):
        from .fichas_pdf import JanelaFichasPDF
        JanelaFichasPDF(self).exec()

    def _galeria_recebidas(self):
        from .projetor import GaleriaRecebidas
        GaleriaRecebidas(self.imagens_recebidas, self).exec()

    def _projecao(self, p):
        if not p:
            if self._seq_projecao is not None:
                self.projecao.hide()   # o mestre recolheu
            self._seq_projecao = None
            return
        if p.get("seq") == self._seq_projecao:
            return
        dados = self.cliente.imagens.get(p.get("id"))
        if not dados:
            return
        self._seq_projecao = p.get("seq")
        titulo = p.get("titulo", "")
        if not any(i["dados"] is dados or i["dados"] == dados for i in self.imagens_recebidas):
            self.imagens_recebidas.append({"titulo": titulo, "dados": dados})
        self.projecao.mostrar(dados, titulo)

    def _mudo(self, mudo):
        self.tocador.definir_volume(mudo=mudo)
        self.player_musica.volume(0 if mudo else 70)

    def _musica(self, m):
        nova = self.seguidor_musica.aplicar(m)
        m = m or {}
        if m.get("id"):
            texto = ("▶ " if m.get("tocando") else "⏸ ") + (m.get("titulo") or "Música do mestre")
            self.lbl_musica.setText(texto)
            self.mini_player.definir_titulo(texto)
            if not self.mini_player.isVisible():   # o player do YouTube precisa ficar à vista
                self.mini_player.posicionar()
                self.mini_player.show()
        else:
            self.lbl_musica.setText("Nada tocando.")
            self.mini_player.hide()

    def _clima_mudou(self, c):
        self.clima_overlay.definir(c.get("tipo", "nenhum"), c.get("forca", 2))
        from ..mesa import neblina
        neblina.garantir(self.cena)   # neblina volumétrica dentro da mesa (Mesa 3D)

    def _definir_ferramenta(self, nome):
        self.cena.ferramenta = nome
        self.visao.atualizar_modo()
        self.painel_atmosfera.ferramenta_atual(nome)
        if nome == "efeito":
            self.statusBar().showMessage("Template: clique no mapa (ou clique e arraste pra apontar). Esc sai.", 8000)
        elif nome == "lapis":
            self.statusBar().showMessage("Lápis: segure e arraste pra rabiscar. Esc sai.", 8000)
        elif nome == "lancar":
            self.statusBar().showMessage("Lançar: arraste do seu token até o alvo. Esc sai.", 8000)

    # ------------------------------------------------------------ chat e diário
    def _aviso_chat(self, m):
        if m.get("de", "").casefold() == self.nome.casefold():
            return
        if self.dock_chat.isVisible():
            return
        import html as _h
        quem = m.get("como") or m.get("de", "")
        sussurro = "🤫 " if m.get("para") else ""
        self.aviso_rolagem.mostrar_texto(f"💬 {sussurro}<b>{_h.escape(quem)}</b>: "
                                         f"{_h.escape(m.get('texto', ''))[:120]}", 6)

    def abrir_diario(self):
        from .diario import JanelaDiarioPlayer
        if getattr(self, "janela_diario", None) is None:
            self.janela_diario = JanelaDiarioPlayer(self.diario, self.cena.nome_aventura, self)
            self.janela_diario.finished.connect(lambda _r: setattr(self, "janela_diario", None))
        self.janela_diario.show()
        self.janela_diario.raise_()

    def _outra_mensagem(self, msg):
        tipo = msg.get("tipo")
        if tipo in ("atlas", "atlas_pedaco"):   # 🌍 cidade e mundo (v0.64): só o que o mestre já revelou
            from . import atlas_jogador
            if getattr(self, "atlas_ponte", None) is None:
                self.atlas_ponte = atlas_jogador.ligar(self)
            atlas_jogador.mensagem(self.atlas_ponte, msg)
            return
        from ..rede.livros import TIPOS as TIPOS_LIVROS
        if tipo in TIPOS_LIVROS:
            novo = tipo == "livro_fim"
            self.livros.mensagem(msg)
            if novo:
                self.statusBar().showMessage("📗 O mestre liberou um livro pra você (Biblioteca → Do mestre).", 8000)
            return
        if tipo == "chat":
            self.painel_chat.adicionar(msg)
            return
        if tipo == "chat_hist":
            self.painel_chat.log.clear()
            for m in msg.get("mensagens") or []:
                self.painel_chat.adicionar(m, avisar=False)
            return
        if tipo == "diario":
            novo = list(msg.get("entradas") or [])
            mudou = bool(self.diario) and novo != self.diario and len(novo) >= len(self.diario)
            self.diario = novo
            if getattr(self, "janela_diario", None) is not None:
                self.janela_diario.atualizar(novo)
            if mudou:
                self.aviso_rolagem.mostrar_texto("📓 O mestre atualizou o <b>diário da campanha</b> (Ctrl+Shift+D)", 6)
            return
        if tipo == "impacto":
            from ..mesa.impactos import tocar
            try:
                tocar(self.cena, self.visao, self.clima_overlay, str(msg.get("efeito")), float(msg.get("x", 0)),
                      float(msg.get("y", 0)), float(msg.get("tam", 3.0)))
            except (TypeError, ValueError):
                pass
            return
        if tipo == "fluidos":   # gás/líquido de cenário (o mestre calcula, aqui só desenha)
            from ..mesa import fluidos
            fluidos.de_cena(self.cena, simula=False).aplicar_retrato(msg)
            return
        if tipo == "lancamento":   # bola de fogo, jato… (de qualquer um)
            from ..mesa.lancamentos import conferir, tocar
            d = conferir(msg)
            if d is not None:
                tocar(self.cena, d)
            return
        if tipo == "olhar_aqui":   # (v0.58) 📣 o mestre chamou a atenção de todos pra um ponto
            self.olhar_aqui(msg)
            return
        if tipo == "relampago":
            self.clima_overlay.relampago()
        elif tipo == "som_arquivo":
            from ..rede.protocolo import de_b64
            try:
                self.tocador.guardar(str(msg["id"]), str(msg.get("ext", "mp3")), de_b64(msg["dados"]))
            except (KeyError, ValueError, OSError):
                pass
        elif tipo == "som":
            if msg.get("acao") == "tocar":
                self.tocador.tocar(str(msg.get("id")), float(msg.get("vol", 0.8)), bool(msg.get("ambiente")))
            elif msg.get("acao") == "parar":
                self.tocador.parar(msg.get("id"))

    def olhar_aqui(self, msg):
        """(v0.58) 📣 A câmera desliza até onde o mestre chamou (a névoa continua valendo: só vê o que já veria)."""
        from PyQt6.QtCore import QPointF
        try:
            x, y = float(msg["x"]), float(msg["y"])
            escala = float(msg.get("escala") or self.visao.escala)
            travar = max(0, min(30, int(msg.get("travar") or 0)))
        except (KeyError, TypeError, ValueError):
            return
        self.visao.voar_para(QPointF(x, y), escala)
        from ..mesa.ping import pingar
        from .painel_dados import cor_do_nome
        pingar(self.cena, x, y, "Mestre", cor_do_nome("Mestre"))
        if travar:
            self.visao.travar_camera(travar + 0.9)   # (+ o tempo da câmera chegar)
        self.aviso_rolagem.mostrar_texto("📣 O mestre chamou a atenção de todos pra cá"
                                         + (f" <i>(câmera travada por {travar} s)</i>" if travar else ""), 5)

    def _paineis_visiveis(self, visiveis: bool):
        docks = getattr(self, "docks", [])
        if visiveis:
            for dock in getattr(self, "_abertos", []):
                dock.show()
        else:
            self._abertos = [d for d in docks if d.isVisible()]
            for dock in docks:
                dock.hide()
            if hasattr(self, "faixa_turnos"):
                self.faixa_turnos.hide()
            if hasattr(self, "painel_grupo"):
                self.painel_grupo.hide()

    def _atualizar_paineis(self, estado):
        from ..mesa.token import TokenItem
        tokens = [i for i in self.cena.itens.values() if isinstance(i, TokenItem)]
        meus = self.cena.meus_tokens()
        minha_vez = self.painel_combate.atualizar(estado.get("combate") or {}, meus)
        if hasattr(self, "seguidor_musica"):
            self._musica(estado.get("musica"))
        if hasattr(self, "projecao"):
            self._projecao(estado.get("projecao"))
        if hasattr(self, "painel_chat"):
            from ..mesa.token import TokenItem as _T
            donos = sorted({t.dono for t in self.cena.itens.values() if isinstance(_T, type)
                            and isinstance(t, _T) and t.tipo == "jogador" and t.dono})
            self.painel_chat.meu_nome = self.nome
            if donos != getattr(self, "_donos_chat", None):
                self._donos_chat = donos
                self.painel_chat.definir_destinos(donos)
        regras = estado.get("regras") or {}
        self.painel_atmosfera.permitir(bool(regras.get("templates", True)), bool(regras.get("lapis", True)))
        self._grupo = estado.get("grupo") or []
        combate = estado.get("combate") or {}
        self.painel_grupo.atualizar(self._grupo, self.cliente.imagens,
                                    vez=combate.get("vez") if combate.get("ativo") else None,
                                    meus={t.uid for t in meus})
        self.faixa_turnos.atualizar(combate, {t.uid for t in meus},
                                    falta_rolar=self.painel_combate._pendente is not None)
        if minha_vez:
            self._mostrar_faixa(f"Sua vez, {minha_vez}!")
            QTimer.singleShot(2500, self.faixa.hide)
        self.painel_info.atualizar(tokens, self.nome)

    def _enquadrar_inicial(self):
        if self.cena.meus_tokens():
            self.visao.zoom_100()
            self.centralizar_meu_token()
        else:
            self.visao.enquadrar_tudo()

    def girar(self, graus: float = 0, olhar_mouse: bool = False):
        import math
        meus = [t for t in self.cena.meus_tokens() if t.tem_visao]
        selecionados = [t for t in meus if t.isSelected()]
        alvos = selecionados or meus
        if not alvos:
            return
        mouse = self.visao.mapToScene(self.visao.mapFromGlobal(self.cursor().pos()))
        travados = False
        for t in alvos:
            if not t.pode_girar:
                travados = True
                continue
            if olhar_mouse:
                c = t.centro_cena()
                nova = math.degrees(math.atan2(mouse.y() - c.y(), mouse.x() - c.x()))
            else:
                nova = t.direcao + graus
            import time
            t.direcao = nova % 360
            t._giro_local_ate = time.monotonic() + 0.4
            t.update()
            self.cliente.girar(t.uid, t.direcao)
        self.cena.recalcular_nevoa()
        if travados:
            self.statusBar().showMessage("O mestre travou o giro do seu token agora.", 3000)

    def abrir_minha_ficha(self, token=None, aba: str = ""):
        """aba (v0.48): "magias" ou "inventario" abre a ficha já lá (atalhos do botão direito)."""
        from PyQt6.QtWidgets import QInputDialog, QMessageBox
        from .janela_ficha import JanelaFicha, pacote_do_token
        meus = self.cena.meus_tokens()
        if not meus:
            QMessageBox.information(self, "Ficha", f"Você ainda não tem token na mesa.\n"
                                                   f"Peça pro mestre vincular um a “{self.nome}”.")
            return
        if token is not None and token in meus:
            meus = [token]
        token = meus[0]
        if len(meus) > 1:
            nome, ok = QInputDialog.getItem(self, "Ficha", "De qual personagem?", [t.nome for t in meus], 0, False)
            if not ok:
                return
            token = next(t for t in meus if t.nome == nome)
        if not hasattr(self, "_fichas"):
            self._fichas = {}
        janela = self._fichas.get(token.uid)
        if janela is None:
            uid = token.uid

            def fonte():
                t = self.cena.itens.get(uid)
                return pacote_do_token(t) if t is not None else janela.ler()
            janela = JanelaFicha(pacote_do_token(token), token.nome, None, fonte=fonte, app_nome="Player")
            janela.salvar.connect(lambda pacote: self.cliente.salvar_ficha(uid, pacote))
            self._fichas[uid] = janela
        if aba:
            janela.ir_para(aba)
        janela.show()
        janela.raise_()
        janela.activateWindow()

    def abrir_biblioteca(self):
        if getattr(self, "_biblioteca", None) is None:
            from .biblioteca import JanelaBiblioteca
            self._biblioteca = JanelaBiblioteca(mestre=False, livros=self.livros)
        self._biblioteca.show()
        self._biblioteca.raise_()

    def _rolagem_na_mesa(self, r):
        from ..graficos import graficos
        from .painel_combate import ini_rolando
        if graficos().dados3d and self.pilha.currentWidget() is self.visao and self.dados3d.rolar(r):
            if r.get("token") and r.get("motivo") == "iniciativa":
                ini_rolando(r["token"])   # (v0.65.1) a lista só mostra o número quando o dado parar
                self.painel_combate.redesenhar()
            return   # o histórico/chat recebe quando o dado parar (dados3d.revelar)
        self._mostrar_rolagem(r)
        if not (self.dock_dados.isVisible() or self.dock_chat.isVisible()):
            self.aviso_rolagem.mostrar(r)

    def _mostrar_rolagem(self, r):
        """O resultado vai pro histórico dos dados e pro chat (depois da animação, se tiver)."""
        self.painel_chat.adicionar_rolagem(r)
        self.painel_dados.adicionar(r)
        if r.get("token"):
            from .painel_combate import ini_revelada
            ini_revelada(r["token"])
            self.painel_combate.redesenhar()
            ultimo = getattr(self.painel_combate, "_ultimo", None)
            if ultimo is not None:
                self.faixa_turnos.atualizar(ultimo[0], {t.uid for t in ultimo[1]},
                                            falta_rolar=self.painel_combate._pendente is not None)

    # ------------------------------------------------------------ retratos (grupo e combate)
    def _cartao_do_id(self, uid):
        """Retrato de quem está no combate: do grupo (vem sempre) ou de um token que estou vendo."""
        for r in self._grupo:
            if r.get("id") == uid:
                return r, self.cliente.imagens
        from ..mesa.grupo import cartao_do_token
        from ..mesa.token import TokenItem
        t = self.cena.itens.get(uid)
        if isinstance(t, TokenItem):
            cartao, _ = cartao_do_token(t)
            return dict(cartao, escondido=False), self.cliente.imagens
        return None

    def _centralizar_uid(self, uid):
        t = self.cena.itens.get(uid)
        if t is not None and t.isVisible() and not self.visao.camera_travada():
            self.visao.centerOn(t)

    def _ficha_do_retrato(self, uid):
        if any(t.uid == uid for t in self.cena.meus_tokens()):
            self.abrir_minha_ficha()
        else:
            self._centralizar_uid(uid)

    def _alternar_retratos(self, v):
        self.config.setValue("retratos_grupo", bool(v))
        self.painel_grupo.definir_ligado(v)

    def centralizar_meu_token(self):
        meus = self.cena.meus_tokens()
        if meus and not self.visao.camera_travada():
            self.visao.centerOn(meus[0])

    def sair_da_mesa(self):
        self._reconectar.stop()
        self.cliente.desconectar()
        self.cena.limpar()
        self.lbl_status.setText("Desconectado")
        self._ja_entrou = False
        self.cena.tema = ""  # força reaplicar o tema na próxima sessão
        self.mostrar_inicio()

    def closeEvent(self, event):
        self._reconectar.stop()
        self.cliente.desconectar()
        event.accept()
