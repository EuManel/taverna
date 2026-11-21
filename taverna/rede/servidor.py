"""
Servidor do Mestre ("Abrir a taverna").

- Aceita conexões dos players (WebSocket, porta 7777 por padrão).
- Sempre que a mesa muda, manda o estado novo pra todo mundo
  (agrupando mudanças rápidas, tipo arrastar um token, em pacotes de ~60 ms).
- Imagens vão uma vez só por player; depois só o "nome" (hash) delas.
- Quando um player pede pra mover um token, confere se o token é dele.
"""

from PyQt6.QtCore import QObject, QPointF, Qt, QTimer, pyqtSignal
from PyQt6.QtNetwork import QHostAddress, QNetworkInterface, QAbstractSocket
from PyQt6.QtWebSockets import QWebSocketServer

from ..mesa.token import TokenItem
from ..mesa.vida import Limitador
from ..jogo.combate import Combate
from ..jogo.dados import ErroDados, rolar
from ..config import APP_VERSAO
from .protocolo import (VERSAO_PROTOCOLO, b64, codificar, decodificar, enviar_grande, filtrar_info,
                        filtrar_pela_visao, mesmo_nome, montar_estado)


class Conexao:
    def __init__(self, socket):
        self.socket = socket
        self.nome: str | None = None       # None até mandar o "ola"
        self.imagens_enviadas: set[str] = set()
        self.ultima_construcao: str | None = None
        self.fichas_enviadas: dict[str, str] = {}   # só manda a ficha quando ela muda
        self.sons_enviados: set[str] = set()        # arquivos de som que ele já tem
        self.ambientes: set[str] = set()            # sons de ambiente tocando pra ele


class ServidorMestre(QObject):
    jogadores_mudaram = pyqtSignal(list)   # lista de nomes conectados
    aviso = pyqtSignal(str)                # mensagens pra barra de status
    rolagem = pyqtSignal(dict)             # toda rolagem (do mestre ou dos players)
    combate_mudou = pyqtSignal()
    ping = pyqtSignal(str, float, float)   # alguém pingou o mapa
    historico = pyqtSignal(dict)           # ações dos jogadores (só o mestre vê)
    conteudo_mudou = pyqtSignal(object)    # alguém pegou um item de um prop
    ficha_mudou = pyqtSignal(object)       # um jogador salvou a ficha (token)
    gatilho_disparou = pyqtSignal(str)     # aviso pro mestre
    efeito_colocado = pyqtSignal(object)   # um jogador pôs um template
    chat = pyqtSignal(dict)                # mensagem de chat (o mestre vê todas, até os sussurros)
    impacto_local = pyqtSignal(str, float, float, float)   # o mestre também vê o impacto
    lancamento_local = pyqtSignal(dict)                    # o mestre também vê a bola de fogo voando

    def __init__(self, cena, parent=None):
        super().__init__(parent)
        self.cena = cena
        self.servidor = QWebSocketServer("Taverna", QWebSocketServer.SslMode.NonSecureMode, self)
        self.servidor.newConnection.connect(self._nova_conexao)
        self.conexoes: list[Conexao] = []

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(60)
        self._timer.timeout.connect(self._transmitir)
        cena.mesa_mudou.connect(self._agendar)
        self.cursor_mestre = Limitador(0.05, self._enviar_cursor_mestre)
        self.mostrar_meu_cursor = True   # o mestre pode esconder o mouse dele
        self.combate = Combate()
        self.players_movem = True         # fora do combate, os players podem mover os tokens?
        self.players_templates = True     # jogadores podem colocar template de magia?
        self.players_lapis = True         # jogadores podem rabiscar no mapa?
        # Som (Etapa 10)
        self.sons: dict[str, tuple] = {}            # id -> (nome, ext, bytes)
        self.ambientes: dict[str, float] = {}       # id -> volume (sons que repetem)
        self.musica = {"id": None, "tocando": False, "pos": 0.0, "quando": 0.0, "titulo": ""}
        self.projecao = None   # {"seq", "id", "titulo", "para": None|[nomes], "dados"} (Etapa 11)
        self.chat_hist: list[dict] = []   # últimas mensagens (quem entra depois vê as que podia ver)
        self.diario: list[dict] = []      # entradas do diário que o mestre compartilhou
        self._seq_projecao = 0
        self._vez_marcada = None          # pra saber quando a vez mudou (marca o início do turno)
        # Histórico: movimentos são juntados (um arrasto = uma linha só)
        self._movendo: dict[str, dict] = {}
        self._timer_mov = QTimer(self)
        self._timer_mov.setInterval(400)
        self._timer_mov.timeout.connect(self._fechar_movimentos)
        self._avisos_recusa: dict[str, float] = {}
        self._dentro_de: set[tuple] = set()   # (área, token) — pra disparar só ao ENTRAR
        from .livros import LivrosMestre
        self.livros = LivrosMestre(self)      # livros liberados pros jogadores / biblioteca deles (v0.43)
        self.andares = [cena]                 # 🏢 o prédio ao vivo (v0.46): cada jogador vê o andar do token dele
        self._ligadas = {cena}

    # ------------------------------------------------------------ trocar a aba ao vivo
    def definir_cena(self, cena):
        """O mestre escolheu outra aba pra mostrar: todo mundo passa a ver ela."""
        if cena is self.cena:
            return
        self.cena.cursores.limpar()
        self.cena = cena
        self.definir_andares([cena])
        for c in self.conexoes:
            c.ultima_construcao = None  # manda terreno/paredes da aba nova
        if self.aberto:
            self._transmitir()
            for c in self.conexoes:
                if c.nome:
                    self._fluidos_pra(c)   # o gás/líquido da aba nova (ou nada)

    # ------------------------------------------------------------ 🏢 andares (v0.46)
    def definir_andares(self, cenas: list):
        """O prédio ao vivo (os andares da aba ao vivo). Mudança em qualquer andar vai pra quem está nele."""
        cenas = [c for c in cenas if c is not None] or [self.cena]
        if self.cena not in cenas:
            cenas = [self.cena] + cenas
        for c in list(self._ligadas):
            if c not in cenas:
                try:
                    c.mesa_mudou.disconnect(self._agendar)
                except (TypeError, RuntimeError):
                    pass
                self._ligadas.discard(c)
        for c in cenas:
            if c not in self._ligadas:
                c.mesa_mudou.connect(self._agendar)
                self._ligadas.add(c)
        self.andares = cenas
        if self.aberto:
            self._transmitir()

    def e_ao_vivo(self, cena) -> bool:
        return cena in self.andares

    def _cena_de(self, conexao):
        """O andar onde está o token desse jogador (sem token: o andar que o mestre pôs ao vivo)."""
        return self._cena_do_nome(conexao.nome)

    def _cena_do_nome(self, nome):
        if len(self.andares) > 1 and nome:
            for c in self.andares:
                try:
                    if any(isinstance(t, TokenItem) and mesmo_nome(t.dono, nome)
                           for t in c.itens_do_usuario()):
                        return c
                except RuntimeError:
                    continue
        return self.cena

    def estado_do_jogador(self, nome: str):
        """(v0.50) O estado EXATAMENTE como esse jogador recebe (andar dele, névoa, o que ele pode ver/ler) —
        pro mestre usar o botão "👁 Visão dos jogadores"."""
        from ..mesa.grupo import filtrar_grupo
        estado, imagens = self._estado_completo(self._cena_do_nome(nome))
        estado = filtrar_info(filtrar_pela_visao(estado, nome), nome)
        estado = dict(estado)
        estado["grupo"] = filtrar_grupo(estado.pop("_grupo", []), nome)
        return estado, imagens

    def nomes_dos_jogadores(self) -> list:
        """Conectados + donos de token (dá pra ver a visão de quem ainda não entrou)."""
        nomes = list(self.nomes())
        for c in (self.andares or [self.cena]):
            try:
                for t in c.itens_do_usuario():
                    if isinstance(t, TokenItem) and t.dono and not any(mesmo_nome(t.dono, n) for n in nomes):
                        nomes.append(t.dono)
            except RuntimeError:
                continue
        return nomes

    def _para_andar(self, cena, msg: dict):
        """Manda só pra quem está nesse andar."""
        texto = codificar(msg)
        for c in self.conexoes:
            if c.nome and self._cena_de(c) is cena:
                c.socket.sendTextMessage(texto)

    def mover_token_de_andar(self, token, destino, pos=None):
        """Leva o token pra outro andar (mesmo id, ficha, informações…). pos = centro onde ele aparece."""
        from ..config import TIPOS_TOKEN
        origem = token.scene()
        d = token.para_dict()
        centro = pos if pos is not None else token.centro_cena()
        if origem is not None:
            origem.removeItem(token)
            origem.marcar_modificada()
            origem.camadas_mudaram.emit()
        novo = TokenItem.de_dict(d)
        camada = destino.camada_por_tipo(TIPOS_TOKEN.get(novo.tipo, TIPOS_TOKEN["criatura"])[2]) or destino.camadas[-1]
        novo.setParentItem(camada)
        meio = novo.diametro / 2
        novo.setPos(camada.mapFromScene(QPointF(centro.x() - meio, centro.y() - meio)))
        novo.definir_retrato(getattr(token, "retrato", None))
        destino.marcar_modificada()
        destino.camadas_mudaram.emit()
        destino.mesa_mudou.emit()
        self._transmitir()
        return novo

    def _usar_escada(self, conexao, escada, token) -> bool:
        """O jogador deu duplo clique numa escada ligada: o token dele vai pro outro andar."""
        from ..config import CELULA
        from ..mesa.andares import nome_andar
        lig = escada.ligacao or {}
        destino = next((c for c in self.andares if c.andar == lig.get("andar")
                        and getattr(c, "predio", None) == getattr(self.cena, "predio", None)), None)
        if destino is None or token is None:
            conexao.socket.sendTextMessage(codificar({"tipo": "aviso", "texto": "Essa escada não leva a lugar nenhum."}))
            return True
        if escada.trancado:   # o mestre não liberou
            conexao.socket.sendTextMessage(codificar({"tipo": "aviso", "texto": "🚫 O mestre não liberou essa escada."}))
            self.registrar(conexao.nome, f"tentou usar a escada com {token.nome} (bloqueada)", "⚠")
            return True
        if self._distancia(token, escada) > 1.5:
            conexao.socket.sendTextMessage(codificar({"tipo": "aviso", "texto": "Chegue perto da escada pra usar."}))
            return True
        outra = destino.item_por_id(str(lig.get("id", "")))
        pos = outra.centro_cena() + QPointF(0, CELULA) if outra is not None else token.centro_cena()
        sobe = lig.get("andar", 0) > getattr(self.cena, "andar", 0)
        self.mover_token_de_andar(token, destino, pos)
        self.registrar(conexao.nome, f"{'subiu' if sobe else 'desceu'} a escada com {token.nome} "
                                     f"→ {nome_andar(destino.andar)}", "🏢")
        self.aviso.emit(f"{token.nome} {'subiu' if sobe else 'desceu'} pro {nome_andar(destino.andar)}.")
        return True

    # ------------------------------------------------------------ ligar/desligar
    @property
    def aberto(self) -> bool:
        return self.servidor.isListening()

    @property
    def porta(self) -> int:
        return self.servidor.serverPort()

    def abrir(self, porta: int) -> bool:
        if self.aberto:
            return True
        ok = self.servidor.listen(QHostAddress(QHostAddress.SpecialAddress.AnyIPv4), porta)
        if not ok:
            self.aviso.emit(f"Não consegui abrir a porta {porta}: {self.servidor.errorString()}")
        return ok

    def fechar(self):
        for c in list(self.conexoes):
            c.socket.close()
        self.conexoes.clear()
        self.servidor.close()
        self.jogadores_mudaram.emit([])

    def nomes(self) -> list[str]:
        return [c.nome for c in self.conexoes if c.nome]

    @staticmethod
    def enderecos_locais() -> list[tuple[str, str]]:
        """[(ip, descrição)] — o IP do Radmin começa com 26."""
        lista = []
        for interface in QNetworkInterface.allInterfaces():
            for entrada in interface.addressEntries():
                ip = entrada.ip()
                if ip.protocol() != QAbstractSocket.NetworkLayerProtocol.IPv4Protocol:
                    continue
                if ip.isLoopback():
                    continue
                texto = ip.toString()
                nome = interface.humanReadableName()
                if texto.startswith("26."):
                    nome = "Radmin VPN  ← passe ESTE pros amigos"
                lista.append((texto, nome))
        lista.sort(key=lambda t: not t[0].startswith("26."))
        return lista

    # ------------------------------------------------------------ conexões
    def _nova_conexao(self):
        while self.servidor.hasPendingConnections():
            socket = self.servidor.nextPendingConnection()
            conexao = Conexao(socket)
            self.conexoes.append(conexao)
            socket.textMessageReceived.connect(
                lambda texto, c=conexao: self._mensagem(c, texto))
            socket.disconnected.connect(lambda c=conexao: self._saiu(c))

    def _saiu(self, conexao: Conexao):
        try:
            self._remover_conexao(conexao)
        except RuntimeError:
            pass  # programa fechando

    def _remover_conexao(self, conexao: Conexao):
        if conexao in self.conexoes:
            self.conexoes.remove(conexao)
            self.livros.ao_sair(conexao)
            if conexao.nome:
                self.aviso.emit(f"{conexao.nome} saiu da taverna.")
                self.registrar(conexao.nome, "saiu da taverna", "⚪")
                self.cena.cursores.remover(conexao.nome)
                self._para_todos({"tipo": "cursor_sai", "nome": conexao.nome}, exceto=conexao)
            self.jogadores_mudaram.emit(self.nomes())
        conexao.socket.deleteLater()

    def _recusar(self, conexao: Conexao, motivo: str):
        conexao.socket.sendTextMessage(codificar({"tipo": "recusado", "motivo": motivo}))
        conexao.socket.flush()
        QTimer.singleShot(200, conexao.socket.close)

    def _mensagem(self, conexao: Conexao, texto: str):
        msg = decodificar(texto)
        if msg is None:
            return
        tipo = msg["tipo"]

        if conexao.nome is None:
            if tipo != "ola":
                return
            nome = str(msg.get("nome", "")).strip()[:30]
            if msg.get("versao") != VERSAO_PROTOCOLO:
                self._recusar(conexao, f"Seu Taverna é de outra versão. Peça pro mestre o Taverna Player "
                                       f"{APP_VERSAO} (o .exe novo) e abra de novo.")
            elif not nome:
                self._recusar(conexao, "Escolha um nome.")
            elif any(mesmo_nome(nome, n) for n in self.nomes()):
                self._recusar(conexao, f"Já tem alguém chamado “{nome}” na mesa.")
            else:
                conexao.nome = nome
                conexao.socket.sendTextMessage(codificar({"tipo": "bem_vindo", "nome": nome}))
                cena_jog = self._cena_de(conexao)
                conexao.cena_vista = cena_jog
                self._enviar_estado(conexao, *self._estado_completo(cena_jog))
                visiveis = [m for m in self.chat_hist if self._pode_ver_chat(m, nome)]
                enviar_grande(conexao.socket, codificar({"tipo": "chat_hist", "mensagens": visiveis[-80:]}))
                enviar_grande(conexao.socket, codificar({"tipo": "diario", "entradas": self.diario}))
                self.livros.ao_entrar(conexao)   # os livros que o mestre liberou pra ele
                self._fluidos_pra(conexao)       # gás/líquido de cenário que já está na mesa
                if getattr(self, "atlas_rede", None) is not None:
                    self.atlas_rede.agendar()    # 🌍 a cidade/mundo dele (só o revelado)
                self.aviso.emit(f"{nome} entrou na taverna!")
                self.registrar(nome, "entrou na taverna", "🟢")
                self.jogadores_mudaram.emit(self.nomes())
            return

        # 🏢 tudo que o jogador faz acontece no ANDAR onde está o token dele
        cena_jog = self._cena_de(conexao)
        if cena_jog is not self.cena:
            antiga = self.cena
            self.cena = cena_jog
            try:
                return self._mensagem_jogo(conexao, msg, tipo)
            finally:
                self.cena = antiga
        return self._mensagem_jogo(conexao, msg, tipo)

    def _mensagem_jogo(self, conexao, msg, tipo):
        from .livros import TIPOS as TIPOS_LIVROS
        if tipo in TIPOS_LIVROS:
            self.livros.mensagem(conexao, msg)
        elif tipo == "rolar":
            self._rolar_player(conexao, msg)
        elif tipo == "ping":
            try:
                x, y = float(msg["x"]), float(msg["y"])
            except (KeyError, TypeError, ValueError):
                return
            self.ping.emit(conexao.nome, x, y)
            self.registrar(conexao.nome, "marcou um ponto no mapa", "📍", (x, y))
            self._para_todos({"tipo": "ping", "nome": conexao.nome, "x": x, "y": y}, exceto=conexao)
        elif tipo == "interagir":
            self._interagir(conexao, msg)
        elif tipo == "pegar":
            self._pegar(conexao, msg)
        elif tipo == "mover_prop":
            self._mover_prop(conexao, msg)
        elif tipo == "ficha":
            self._ficha_do_player(conexao, msg)
        elif tipo == "porta":
            self._porta_do_player(conexao, msg)
        elif tipo == "chat":
            self._chat_do_player(conexao, msg)
        elif tipo == "efeito":
            self._efeito_do_player(conexao, msg)
        elif tipo == "lancar":   # o jogador lançou (bola de fogo, jato…)
            if not self.players_templates:
                conexao.socket.sendTextMessage(codificar({"tipo": "aviso", "texto": "O mestre desligou os templates."}))
            else:
                d = self.lancar(msg, dono=conexao.nome)
                if d:
                    from ..mesa.lancamentos import ELEMENTOS, TIPOS_LANCE
                    self.registrar(conexao.nome, f"lançou: {ELEMENTOS[d['elemento']][0]} "
                                                 f"({TIPOS_LANCE[d['tipo']].split(' ', 1)[1].split(' (')[0]})",
                                   "🎯", (d["x1"], d["y1"]))
        elif tipo == "apagar_efeitos":
            n = self.cena.remover_efeitos(dono=conexao.nome)
            if n:
                self.registrar(conexao.nome, f"apagou {n} template(s)", "✨")
        elif tipo == "traco":
            self._traco_do_player(conexao, msg)
        elif tipo == "apagar_tracos":
            self.cena.apagar_tracos(autor=conexao.nome)
        elif tipo == "editar_token":   # (v0.48) o jogador mudou o PRÓPRIO token: nome, cor, imagem, retrato
            self._editar_token_do_player(conexao, msg)
        elif tipo == "criar_token":    # (v0.64.1) o jogador cria o PRÓPRIO token (só um, só o dele)
            self._criar_token_do_player(conexao, msg)
        elif tipo == "encerrar_turno":  # (v0.65.1) o jogador passa a vez — só se a vez for de um token DELE
            vez = self._tokens().get(self.combate.vez) if self.combate.ativo else None
            if vez is not None and vez.dono and mesmo_nome(vez.dono, conexao.nome):
                self.registrar(conexao.nome, f"encerrou o turno de {vez.nome}", "⏭")
                self.proximo_turno()
                self._transmitir()
        elif tipo == "mover":
            self._mover(conexao, msg)
        elif tipo == "girar":
            self._girar(conexao, msg)
        elif tipo == "cursor":
            x, y = msg.get("x"), msg.get("y")
            if x is not None:
                try:
                    x, y = float(x), float(y)
                except (TypeError, ValueError):
                    return
            self.cena.cursores.atualizar(conexao.nome, x, y)
            self._para_todos({"tipo": "cursor", "nome": conexao.nome, "x": x, "y": y},
                             exceto=conexao)

    def _editar_token_do_player(self, conexao: Conexao, msg: dict):
        """Só o dono edita, e só nome, cor, imagem e retrato (tipo, tamanho e dono são do mestre)."""
        import base64
        from PyQt6.QtGui import QColor
        item = None
        for c in self._todas_as_abas():   # (v0.64.1) o token pode estar em qualquer andar/aba
            try:
                item = c.item_por_id(str(msg.get("id", "")))
            except RuntimeError:
                continue
            if item is not None:
                break
        if not isinstance(item, TokenItem) or not item.dono or not mesmo_nome(item.dono, conexao.nome):
            return
        mudou = []
        nome = str(msg.get("nome") or "").strip()[:40]
        if nome and nome != item.nome:
            mudou.append(f"nome “{nome}”")
            item.nome = nome
        cor = QColor(str(msg.get("cor") or ""))
        if cor.isValid() and cor.name() != item.cor.name():
            item.cor = cor
            mudou.append("cor")
        for campo, definir, lado in (("imagem", item.definir_imagem, 512), ("retrato", item.definir_retrato, 768)):
            if campo not in msg:
                continue
            bruto = msg.get(campo)
            try:
                dados = base64.b64decode(bruto) if bruto else None
            except (ValueError, TypeError):
                continue
            if dados and len(dados) > 4_000_000:   # grande demais pra rede
                continue
            if dados:
                from ..ui.dialogos import reduzir_imagem
                dados = reduzir_imagem(dados, lado)
            atual = item.imagem if campo == "imagem" else getattr(item, "retrato", None)
            if dados != atual:
                definir(dados)
                mudou.append(campo)
        if not mudou:
            return
        item.prepareGeometryChange()
        item.update()
        item._avisar_modificacao()
        self.registrar(conexao.nome, f"editou o token {item.nome} ({', '.join(mudou)})", "✏")
        self._transmitir()

    def _todas_as_abas(self) -> list:
        cenas = list(getattr(self.parent(), "cenas", None) or [])
        for c in self.andares + [self.cena]:
            if c not in cenas:
                cenas.append(c)
        return cenas

    def tokens_do_jogador(self, nome: str) -> list:
        """Os tokens desse jogador em TODAS as abas da aventura."""
        saida = []
        for c in self._todas_as_abas():
            try:
                saida += [t for t in c.itens_do_usuario() if isinstance(t, TokenItem) and t.dono
                          and mesmo_nome(t.dono, nome)]
            except RuntimeError:
                continue
        return saida

    def _criar_token_do_player(self, conexao: Conexao, msg: dict):
        """(v0.64.1, pedido do Manel) O jogador cria o PRÓPRIO token — um só: se já tem token dele em qualquer aba,
        não cria. Sempre tipo jogador, tamanho 1, dono = ele. Nasce onde ele estava olhando (dentro do cenário)."""
        import base64
        from PyQt6.QtCore import QPointF
        from PyQt6.QtGui import QColor
        if self.tokens_do_jogador(conexao.nome):
            conexao.socket.sendTextMessage(codificar({"tipo": "aviso", "texto": "Você já tem um token — use "
                                                      "“Editar meu token” pra mudar nome, cor ou imagem."}))
            return
        nome = str(msg.get("nome") or "").strip()[:40] or conexao.nome
        cor = QColor(str(msg.get("cor") or ""))
        imagem = None
        if msg.get("imagem"):
            try:
                imagem = base64.b64decode(msg["imagem"])
            except (ValueError, TypeError):
                imagem = None
            if imagem and len(imagem) > 4_000_000:
                imagem = None
            if imagem:
                from ..ui.dialogos import reduzir_imagem
                imagem = reduzir_imagem(imagem, 512)
        cena = self._cena_de(conexao)
        try:
            pos = QPointF(float(msg.get("x", 0)), float(msg.get("y", 0)))
        except (TypeError, ValueError):
            pos = QPointF(0, 0)
        chao = cena.chao_caminho() if hasattr(cena, "chao_caminho") else None
        if chao is not None and not chao.isEmpty() and not chao.contains(pos):
            pos = chao.boundingRect().center()
        token = cena.adicionar_token({"nome": nome, "tipo": "jogador", "cor": cor.name() if cor.isValid() else "#3f6b4a",
                                      "tamanho": 1, "imagem": imagem, "dono": conexao.nome}, pos)
        if msg.get("retrato"):
            try:
                from ..ui.dialogos import reduzir_imagem
                token.definir_retrato(reduzir_imagem(base64.b64decode(msg["retrato"]), 768))
            except (ValueError, TypeError):
                pass
        self.registrar(conexao.nome, f"criou o próprio token “{nome}”", "🧙")
        self.aviso.emit(f"{conexao.nome} criou o token “{nome}”.")
        self._transmitir()

    def _mover(self, conexao: Conexao, msg: dict):
        item = self.cena.item_por_id(str(msg.get("id", "")))
        if not isinstance(item, TokenItem):
            return
        # Só o dono move, e só se o token estiver visível pra ele
        if not mesmo_nome(item.dono, conexao.nome):
            return
        if not self.pode_mover(item):
            self._recusa(conexao.nome, item, "tentou mover {t} fora da vez" if self.combate.ativo
                         else "tentou mover {t} (movimento travado)")
            self.transmitir_agora()   # devolve o token pro lugar certo na tela dele
            return
        if not item.isVisible() or not item.parentItem().isVisible():
            return
        try:
            x, y = float(msg["x"]), float(msg["y"])
        except (KeyError, TypeError, ValueError):
            return
        x, y, limitou = self._aplicar_limite(item, x, y)
        if limitou:
            self._recusa(conexao.nome, item, "tentou passar do deslocamento com {t}")
            QTimer.singleShot(150, self.transmitir_agora)
        self._anotar_movimento(conexao.nome, item, x, y)
        self._checar_areas(conexao, item, x, y)
        # Desliza até lá (fica suave na tela do mestre e dos outros players)
        self.cena.suavizador.mover(item, item.parentItem().mapFromScene(QPointF(x, y)))

    def _girar(self, conexao: Conexao, msg: dict):
        item = self.cena.item_por_id(str(msg.get("id", "")))
        if not isinstance(item, TokenItem) or not mesmo_nome(item.dono, conexao.nome):
            return
        if not item.pode_girar:
            return  # o mestre travou
        if self.combate.ativo and self.combate.vez != item.uid:
            return  # no combate só gira na sua vez
        try:
            item.definir_visao(direcao=float(msg["direcao"]))
        except (KeyError, TypeError, ValueError):
            pass

    # ------------------------------------------------------------ regras de movimento
    def pode_mover(self, token) -> bool:
        if self.combate.ativo:
            return self.combate.vez == token.uid
        return self.players_movem

    def limite_do_turno(self, token) -> float | None:
        # metros que o token da vez pode andar neste turno (None = sem limite)
        if not (self.combate.ativo and self.combate.limitar and token.uid == self.combate.vez):
            return None
        p = self.combate.participante(token.uid)
        return max(0.0, token.deslocamento + (p.get("extra", 0.0) if p else 0.0))

    def _aplicar_limite(self, token, x, y):
        from ..config import CELULA
        limite = self.limite_do_turno(token)
        origem = getattr(token, "origem_turno", None)
        if limite is None or origem is None:
            return x, y, False
        meio = token.diametro / 2
        cx, cy = x + meio, y + meio
        dx, dy = cx - origem.x(), cy - origem.y()
        dist = (dx * dx + dy * dy) ** 0.5
        raio = limite * CELULA
        if dist <= raio + 0.5:
            return x, y, False
        f = raio / dist if dist > 0 else 0
        return origem.x() + dx * f - meio, origem.y() + dy * f - meio, True

    # ------------------------------------------------------------ histórico (só o mestre vê)
    def registrar(self, quem: str, texto: str, icone: str = "•", pos=None):
        import time
        self.historico.emit({"hora": time.strftime("%H:%M:%S"), "quem": quem, "texto": texto,
                             "icone": icone, "pos": pos})

    def _recusa(self, quem, token, modelo):
        import time
        chave = f"{quem}|{token.uid}|{modelo}"
        agora = time.monotonic()
        if agora - self._avisos_recusa.get(chave, 0) < 4:
            return   # não enche o histórico com o mesmo aviso
        self._avisos_recusa[chave] = agora
        self.registrar(quem, modelo.format(t=token.nome), "⚠", None)

    def _anotar_movimento(self, quem, token, x, y):
        import time
        from ..config import CELULA
        mov = self._movendo.get(token.uid)
        meio = token.diametro / 2
        if mov is None:
            inicio = token.scenePos()
            mov = {"quem": quem, "token": token, "inicio": (inicio.x() + meio, inicio.y() + meio)}
            self._movendo[token.uid] = mov
        mov["fim"] = (x + meio, y + meio)
        mov["ultimo"] = time.monotonic()
        if not self._timer_mov.isActive():
            self._timer_mov.start()

    def _fechar_movimentos(self):
        import time
        from ..config import CELULA, fmt_m
        agora = time.monotonic()
        for uid, mov in list(self._movendo.items()):
            if agora - mov["ultimo"] < 0.9:
                continue
            del self._movendo[uid]
            (ax, ay), (bx, by) = mov["inicio"], mov["fim"]
            dist = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5 / CELULA
            if dist < 0.1:
                continue
            extra = ""
            limite = self.limite_do_turno(mov["token"])
            if limite is not None and getattr(mov["token"], "origem_turno", None) is not None:
                o = mov["token"].origem_turno
                andou = ((bx - o.x()) ** 2 + (by - o.y()) ** 2) ** 0.5 / CELULA
                extra = f" (no turno: {fmt_m(andou)} de {fmt_m(limite)} m)"
            self.registrar(mov["quem"], f"moveu {mov['token'].nome} {fmt_m(dist)} m{extra}", "👣", (bx, by))
        if not self._movendo:
            self._timer_mov.stop()

    def definir_players_movem(self, pode: bool):
        self.players_movem = pode
        self.transmitir_agora()

    def definir_regras_atmosfera(self, templates: bool, lapis: bool):
        self.players_templates, self.players_lapis = bool(templates), bool(lapis)
        self.transmitir_agora()

    # ------------------------------------------------------------ atmosfera
    def _efeito_do_player(self, conexao, msg):
        from ..mesa.efeitos import EFEITOS, FORMAS, cor_valida
        if not self.players_templates:
            conexao.socket.sendTextMessage(codificar({"tipo": "aviso", "texto": "O mestre desligou os templates."}))
            return
        try:
            d = {"x": float(msg["x"]), "y": float(msg["y"]),
                 "efeito": msg.get("efeito") if msg.get("efeito") in EFEITOS else "magia",
                 "forma": msg.get("forma") if msg.get("forma") in FORMAS else "circulo",
                 "tamanho": max(0.5, min(60.0, float(msg.get("tamanho", 3)))),
                 "largura": max(0.5, min(12.0, float(msg.get("largura", 1.5)))),
                 "angulo": float(msg.get("angulo", 0)) % 360,
                 "cor": cor_valida(msg.get("cor", ""))}   # cor da magia do jogador (validada)
        except (KeyError, TypeError, ValueError):
            return
        meus = [e for e in self.cena.efeitos_visiveis() if e.dono.casefold() == conexao.nome.casefold()]
        if len(meus) >= 12:   # não deixa entupir a mesa
            self.cena.remover_efeitos(ids={meus[0].uid})
        item = self.cena.criar_efeito(d, dono=conexao.nome)
        if item is None:   # todo fora do mapa
            conexao.socket.sendTextMessage(codificar({"tipo": "aviso",
                                                      "texto": "Fora do mapa: o efeito só existe onde tem chão."}))
            return
        self.registrar(conexao.nome, f"colocou um template: {item.descricao()}", "✨", (d["x"], d["y"]))
        self.efeito_colocado.emit(item)

    def _traco_do_player(self, conexao, msg):
        if not self.players_lapis:
            return
        try:
            pts = [[float(x), float(y)] for x, y in (msg.get("pts") or [])[:3000]]
        except (TypeError, ValueError):
            return
        if not pts:
            return
        from ..mesa.desenhos import traco_novo
        cor = str(msg.get("cor", "#4cc9f0"))[:9]
        traco = traco_novo([tuple(p) for p in pts], cor if cor.startswith("#") else "#4cc9f0",
                           max(1.0, min(12.0, float(msg.get("esp", 3) or 3))), conexao.nome,
                           bool(msg.get("temp", True)))
        traco["id"] = str(msg.get("id") or traco["id"])[:16]
        self.cena.adicionar_traco(traco)
        if not traco.get("temp"):
            self.registrar(conexao.nome, "rabiscou no mapa", "✏", tuple(pts[0]))

    # ------------------------------------------------------------ chat
    @staticmethod
    def _pode_ver_chat(m: dict, nome: str) -> bool:
        if not m.get("para"):
            return True
        return mesmo_nome(m.get("de", ""), nome) or mesmo_nome(m.get("para", ""), nome)

    def _espalhar_chat(self, m: dict):
        import time
        m.setdefault("hora", time.strftime("%H:%M"))
        self.chat_hist.append(m)
        del self.chat_hist[:-200]
        self.chat.emit(m)   # o mestre vê tudo (inclusive sussurro entre jogadores)
        texto = codificar(dict(m, tipo="chat"))
        for c in self.conexoes:
            if c.nome and self._pode_ver_chat(m, c.nome):
                c.socket.sendTextMessage(texto)

    def _chat_do_player(self, conexao, msg):
        texto = str(msg.get("texto", "")).strip()[:1000]
        if not texto:
            return
        if texto.lower().startswith(("/r ", "/rolar ")):   # atalho: rolar pelo chat
            self._rolar_player(conexao, {"expr": texto.split(" ", 1)[1], "motivo": ""})
            return
        para = str(msg.get("para") or "").strip()[:30] or None
        if para and para != "Mestre" and not any(mesmo_nome(para, n) for n in self.nomes()):
            conexao.socket.sendTextMessage(codificar({"tipo": "aviso", "texto": f"{para} não está na mesa."}))
            return
        self._espalhar_chat({"de": conexao.nome, "texto": texto, "para": para})

    def chat_mestre(self, texto: str, para: str | None = None, como: str = ""):
        texto = texto.strip()[:1000]
        if texto:
            self._espalhar_chat({"de": "Mestre", "texto": texto, "para": para or None, "como": como or ""})

    # ------------------------------------------------------------ diário (entradas compartilhadas)
    def definir_diario(self, entradas: list[dict]):
        compartilhadas = [{k: e.get(k) for k in ("id", "titulo", "texto", "tipo", "criado")}
                          for e in entradas if e.get("compartilhado")]
        if compartilhadas == self.diario:
            return
        self.diario = compartilhadas
        self._para_todos({"tipo": "diario", "entradas": compartilhadas})

    def impacto(self, tipo: str, x: float = 0.0, y: float = 0.0, tam: float = 3.0, cena=None):
        """Efeito de impacto (explosão, raio…) no andar onde aconteceu; os de tela (tremor, apagão…), pra todos."""
        from ..mesa.impactos import IMPACTOS
        msg = {"tipo": "impacto", "efeito": tipo, "x": round(x, 1), "y": round(y, 1), "tam": tam}
        self.cena_do_impacto = cena or self.cena
        if IMPACTOS.get(tipo, ("", False))[1]:
            self._para_andar(self.cena_do_impacto, msg)
        else:
            self._para_todos(msg)
        self.impacto_local.emit(tipo, float(x), float(y), float(tam))

    # ------------------------------------------------------------ gás e líquidos de cenário (v0.45)
    def enviar_fluidos(self, cena, retrato: dict):
        """O retrato do gás/líquido de um andar ao vivo vai pra quem está nele."""
        if cena in self.andares:
            self._para_andar(cena, dict(retrato, tipo="fluidos"))

    def _fluidos_pra(self, conexao):
        f = getattr(self._cena_de(conexao), "fluidos", None)
        enviar_grande(conexao.socket, codificar(dict(f.retrato() if f else {"campos": {}}, tipo="fluidos")))

    def lancar(self, d: dict, dono: str = "", cena=None) -> dict | None:
        """Bola de fogo, jato… voando na tela de quem está no andar; se 'deixar', a área aparece quando chega."""
        from ..mesa.lancamentos import chegada, conferir
        d = conferir(dict(d, dono=dono))
        if d is None:
            return None
        cena_l = cena or self.cena
        self._para_andar(cena_l, dict(d, tipo="lancamento"))
        self.lancamento_local.emit(dict(d, _cena=id(cena_l)))
        if d["elemento"] in ("fogo", "lava", "eletrico"):   # chegou num gás tóxico? explode

            def acender(cena_l=cena_l, d=d):
                f = getattr(cena_l, "fluidos", None)
                if f is not None:
                    try:
                        f.ignicao_em(d["x1"], d["y1"], max(1.0, d["tam"] if d["tipo"] == "projetil" else 1.5))
                    except RuntimeError:
                        pass
            QTimer.singleShot(int(chegada(d) * 1000), acender)
        if d["deixar"]:
            QTimer.singleShot(int(chegada(d) * 1000), lambda: self._deixar_area(cena_l, d))
        return d

    def _deixar_area(self, cena, d):
        from ..mesa.efeitos import cor_valida
        from ..mesa.lancamentos import area_deixada
        try:
            area = area_deixada(d)
            area["cor"] = cor_valida(area.get("cor", ""))
            if d["dono"]:   # do jogador: entra como template dele (até 12)
                meus = [e for e in cena.efeitos_visiveis() if e.dono.casefold() == d["dono"].casefold()]
                if len(meus) >= 12:
                    cena.remover_efeitos(ids={meus[0].uid})
            cena.criar_efeito(area, dono=d["dono"])
        except RuntimeError:   # a cena foi fechada nesse meio-tempo
            pass

    def relampago(self):
        self._para_todos({"tipo": "relampago"})

    # ------------------------------------------------------------ som
    def preparar_som(self, caminho: str) -> str | None:
        """Lê o arquivo do mestre (uma vez) e devolve o id dele."""
        import os
        from ..ui.audio import LIMITE_MB, id_do_arquivo
        try:
            if os.path.getsize(caminho) > LIMITE_MB * 1024 * 1024:
                self.aviso.emit(f"Som grande demais (máx. {LIMITE_MB} MB): {os.path.basename(caminho)}")
                return None
            with open(caminho, "rb") as f:
                dados = f.read()
        except OSError:
            self.aviso.emit(f"Não consegui abrir o som: {caminho}")
            return None
        sid = id_do_arquivo(dados)
        ext = os.path.splitext(caminho)[1].lstrip(".").lower() or "mp3"
        self.sons[sid] = (os.path.basename(caminho), ext, dados)
        return sid

    def _mandar_arquivo_som(self, conexao, sid):
        if sid in conexao.sons_enviados or sid not in self.sons:
            return
        nome, ext, dados = self.sons[sid]
        conexao.socket.sendTextMessage(codificar({"tipo": "som_arquivo", "id": sid, "nome": nome,
                                                  "ext": ext, "dados": b64(dados)}))
        conexao.sons_enviados.add(sid)

    def tocar_som(self, sid: str, vol: float = 0.8, ambiente: bool = False):
        if sid not in self.sons:
            return
        if ambiente:
            self.ambientes[sid] = vol
        for c in self.conexoes:
            if not c.nome:
                continue
            self._mandar_arquivo_som(c, sid)
            c.socket.sendTextMessage(codificar({"tipo": "som", "acao": "tocar", "id": sid,
                                                "vol": vol, "ambiente": ambiente}))
            if ambiente:
                c.ambientes.add(sid)

    def parar_som(self, sid: str | None = None):
        if sid is None:
            self.ambientes.clear()
        else:
            self.ambientes.pop(sid, None)
        for c in self.conexoes:
            if sid is None:
                c.ambientes.clear()
            else:
                c.ambientes.discard(sid)
        self._para_todos({"tipo": "som", "acao": "parar", "id": sid})

    def _sons_atrasados(self, conexao):
        # quem entrou depois: recebe os sons de ambiente que já estão tocando
        for sid, vol in self.ambientes.items():
            if sid not in conexao.ambientes:
                self._mandar_arquivo_som(conexao, sid)
                conexao.socket.sendTextMessage(codificar({"tipo": "som", "acao": "tocar", "id": sid,
                                                          "vol": vol, "ambiente": True}))
                conexao.ambientes.add(sid)

    # ------------------------------------------------------------ projetor
    def projetar(self, dados: bytes, titulo: str = "", para=None):
        from ..ui.projetor import id_imagem
        self._seq_projecao += 1
        self.projecao = {"seq": self._seq_projecao, "id": "proj_" + id_imagem(dados), "titulo": titulo,
                         "para": list(para) if para else None, "dados": dados}
        self.transmitir_agora()

    def recolher_projecao(self):
        self.projecao = None
        self.transmitir_agora()

    def _projecao_pra(self, conexao) -> dict | None:
        p = self.projecao
        if not p or not conexao.nome:
            return None
        if p["para"] is not None and not any(mesmo_nome(n, conexao.nome) for n in p["para"]):
            return None
        if p["id"] not in conexao.imagens_enviadas:
            conexao.socket.sendTextMessage(codificar({"tipo": "asset", "id": p["id"], "dados": b64(p["dados"])}))
            conexao.imagens_enviadas.add(p["id"])
        return {"seq": p["seq"], "id": p["id"], "titulo": p["titulo"]}

    # ------------------------------------------------------------ música (YouTube)
    def definir_musica(self, **mudancas):
        import time
        m = self.musica
        if "pos" in mudancas or mudancas.get("tocando") is not None or "id" in mudancas:
            m["quando"] = time.time()
        m.update({k: v for k, v in mudancas.items() if k in ("id", "tocando", "pos", "titulo")})
        if not m.get("id"):
            m.update({"tocando": False, "pos": 0.0, "titulo": ""})
        self.transmitir_agora()

    def musica_agora(self) -> dict:
        import time
        m = self.musica
        pos = float(m.get("pos", 0))
        if m.get("tocando"):
            pos += max(0.0, time.time() - float(m.get("quando", time.time())))
        return {"id": m.get("id"), "tocando": bool(m.get("tocando")), "pos": round(pos, 2),
                "titulo": m.get("titulo", "")}

    # ------------------------------------------------------------ dados
    def rolar_mestre(self, expr: str, privada: bool = False, motivo: str = "") -> dict:
        r = rolar(expr)   # pode levantar ErroDados
        from ..dados3d.visual import meus_dados   # (v0.74) os dados do mestre do jeito dele
        r.update({"tipo": "rolagem", "quem": "Mestre", "motivo": motivo, "privada": privada, "dv": meus_dados()})
        self.rolagem.emit(r)
        if not privada:
            self._para_todos(r)
        return r

    def _rolar_player(self, conexao: Conexao, msg: dict):
        expr = str(msg.get("expr", ""))[:60]
        motivo = str(msg.get("motivo", ""))[:40]
        try:
            r = rolar(expr)
        except ErroDados as erro:
            conexao.socket.sendTextMessage(codificar({"tipo": "erro_dados", "motivo": str(erro)}))
            return
        from ..dados3d.visual import limpar   # (v0.74) a cara dos dados de quem rolou (conferida)
        r.update({"tipo": "rolagem", "quem": conexao.nome, "motivo": motivo, "privada": False,
                  "dv": limpar(msg.get("dv"))})
        if motivo == "iniciativa":
            uid = str(msg.get("token", ""))
            item = self.cena.item_por_id(uid)
            p = self.combate.participante(uid)
            if (not isinstance(item, TokenItem) or not mesmo_nome(item.dono, conexao.nome)
                    or p is None or p["ini"] is not None):
                return
            p["ini"] = r["total"]
            r["token_nome"] = item.nome
            r["token"] = uid
        # (v0.65.1) a ROLAGEM sai antes do estado novo do combate: cada um esconde a iniciativa até o dado parar
        self.rolagem.emit(r)
        self._para_todos(r)   # rolagem de player é sempre pública
        if r.get("token"):
            self.combate_mudou.emit()
            self.transmitir_agora()
        motivo_txt = f" ({motivo}{' de ' + r['token_nome'] if r.get('token_nome') else ''})" if motivo else ""
        d20 = " ✨20 natural" if r.get("d20") == 20 else (" 💀1 natural" if r.get("d20") == 1 else "")
        self.registrar(conexao.nome, f"rolou {r['expr']}{motivo_txt} = {r['total']}{d20}", "🎲")

    # ------------------------------------------------------------ baús, criaturas caídas, objetos
    def _alvo_e_token(self, conexao, uid):
        """(alvo, meu token mais perto). Alvo = objeto interativo ou token de outra criatura."""
        from ..mesa.props import PropItem
        alvo = self.cena.item_por_id(str(uid))
        if isinstance(alvo, PropItem):
            if not alvo.isVisible() or not alvo.parentItem().isVisible():
                return None, None
        elif isinstance(alvo, TokenItem):
            if mesmo_nome(alvo.dono, conexao.nome) or not alvo.isVisible():
                return None, None
        else:
            return None, None
        meus = [t for t in self.cena.itens_do_usuario()
                if isinstance(t, TokenItem) and mesmo_nome(t.dono, conexao.nome) and t.isVisible()]
        if not meus:
            return alvo, None
        return alvo, min(meus, key=lambda t: self._distancia(t, alvo))

    @staticmethod
    def _distancia(token, alvo) -> float:
        """Distância (metros) entre as bordas do token e do alvo (objeto ou outro token)."""
        from ..config import CELULA
        from PyQt6.QtGui import QPolygonF
        c = token.centro_cena()
        if isinstance(alvo, TokenItem):
            o = alvo.centro_cena()
            d = ((c.x() - o.x()) ** 2 + (c.y() - o.y()) ** 2) ** 0.5
            return max(0.0, (d - token.diametro / 2 - alvo.diametro / 2) / CELULA)
        cantos = alvo.cantos_cena()
        if QPolygonF(cantos).containsPoint(c, Qt.FillRule.OddEvenFill):
            return 0.0
        melhor = float("inf")
        for k in range(4):
            a, b = cantos[k], cantos[(k + 1) % 4]
            ab = b - a
            tam = ab.x() ** 2 + ab.y() ** 2 or 1
            t = max(0.0, min(1.0, ((c.x() - a.x()) * ab.x() + (c.y() - a.y()) * ab.y()) / tam))
            q = a + ab * t
            melhor = min(melhor, ((c.x() - q.x()) ** 2 + (c.y() - q.y()) ** 2) ** 0.5)
        return max(0.0, (melhor - token.diametro / 2) / CELULA)

    _distancia_ao_prop = _distancia   # nome antigo

    @staticmethod
    def _itens_de(alvo) -> list:
        if isinstance(alvo, TokenItem):
            return list(alvo.info.get("inventario", {}).get("v") or [])
        return alvo.itens

    @staticmethod
    def _guardar_itens(alvo, itens):
        if isinstance(alvo, TokenItem):
            alvo.definir_info("inventario", itens)
        else:
            alvo.itens = itens
            alvo._mudou()

    def _pode_abrir(self, conexao, alvo, token) -> str | None:
        # None = pode; senão o motivo
        if token is None:
            return "Você precisa de um token na mesa pra mexer nisso."
        if isinstance(alvo, TokenItem):
            if alvo.estado not in ("morto", "caido") and not getattr(alvo, "saqueavel", False):
                return "Só dá pra revistar quem está caído ou morto."
            if self._distancia(token, alvo) > 1.5:
                return "Chegue mais perto pra revistar."
            return None
        if not alvo.interativo:
            return "Não dá pra abrir isso."
        if alvo.perto and self._distancia(token, alvo) > 1.5:
            return "Chegue mais perto pra abrir."
        if alvo.trancado:
            return "🔒 Está trancado."
        return None

    def _interagir(self, conexao, msg):
        alvo, token = self._alvo_e_token(conexao, msg.get("id"))
        if alvo is None:
            return
        if getattr(alvo, "tipo", "") == "escada" and not isinstance(alvo, TokenItem):   # 🏢 subir/descer
            self._usar_escada(conexao, alvo, token)
            return
        verbo = "revistar" if isinstance(alvo, TokenItem) else "abrir"
        motivo = self._pode_abrir(conexao, alvo, token)
        if motivo == "🔒 Está trancado." and self._usar_chave(conexao, token, alvo, "o " + alvo.nome.lower()):
            alvo._mudou()
            motivo = None
        perto = token is not None and "perto" not in (motivo or "")
        if perto and not isinstance(alvo, TokenItem) and (alvo.gatilho or {}).get("quando") == "abrir":
            c = alvo.centro_cena()
            self.disparar(alvo.gatilho, conexao.nome, token, (c.x(), c.y()), conexao)
        if motivo:
            conexao.socket.sendTextMessage(codificar({"tipo": "aviso", "texto": motivo}))
            self.registrar(conexao.nome, f"tentou {verbo} {alvo.nome} "
                                         f"({motivo.replace('🔒 ', '').rstrip('.').lower()})", "⚠")
            return
        if (not isinstance(alvo, TokenItem) and getattr(alvo, "solto", False)
                and not getattr(alvo, "documento", False)):
            self._coletar(conexao, alvo, token)   # (v0.48) item do chão: direto pro inventário
            return
        pode_pegar = True if isinstance(alvo, TokenItem) else alvo.pode_pegar
        sorteio = None if isinstance(alvo, TokenItem) else getattr(alvo, "sorteio", None)
        if sorteio and sorteio.get("ativo") and not sorteio.get("sorteado"):
            # primeira vez que alguém abre: sorteia o que tem dentro
            from ..jogo.sorteio import sortear
            itens, resumo = sortear(sorteio)
            alvo.itens = itens
            sorteio["sorteado"], sorteio["resultado"] = True, resumo
            alvo._mudou()
            c = alvo.centro_cena()
            self.registrar(conexao.nome, f"abriu {alvo.nome} 🎲 sorteio: {resumo}", "🎲", (c.x(), c.y()))
            self.conteudo_mudou.emit(alvo)
            if not itens:
                conexao.socket.sendTextMessage(codificar({"tipo": "aviso", "texto": resumo}))
        self._enviar_conteudo(conexao, alvo, pode_pegar)
        n = len(self._itens_de(alvo))
        c = alvo.centro_cena()
        if getattr(alvo, "documento", False):
            self.registrar(conexao.nome, f"leu {alvo.nome}", "📜", (c.x(), c.y()))
        elif getattr(alvo, "solto", False):
            self.registrar(conexao.nome, f"achou {alvo.nome} no chão", "✨", (c.x(), c.y()))
        else:
            self.registrar(conexao.nome, f"{'revistou' if verbo == 'revistar' else 'abriu'} {alvo.nome}"
                                         + (f" ({n} itens)" if n else " (vazio)"), "📦", (c.x(), c.y()))

    def _coletar(self, conexao, alvo, token):
        """(v0.48) Item coletável (chave, poção, espada…): tudo o que ele tem vai pro inventário do
        personagem e o objeto some do chão. Sem janela no meio."""
        if token is None:
            return
        itens = list(self._itens_de(alvo))
        if not itens:
            from ..mesa.props import novo_id_item
            itens = [{"id": novo_id_item(), "nome": alvo.nome, "qtd": 1, "desc": "", "img": None}]
        inv = token.info.setdefault("inventario", {"v": [], "vis": "oculto"})
        lista = list(inv.get("v") or [])
        for item in itens:
            lista.append(dict(item, origem="chão"))
        token.definir_info("inventario", lista)
        self._guardar_itens(alvo, [])
        self.cena.definir_item_visivel(alvo, False)
        nomes = ", ".join(f"{i.get('nome', '?')}" + (f" (x{i.get('qtd')})" if i.get("qtd", 1) not in (1, None) else "")
                          for i in itens)
        conexao.socket.sendTextMessage(codificar({"tipo": "aviso", "texto": f"🎒 {token.nome} pegou: {nomes}"}))
        c = alvo.centro_cena()
        self.registrar(conexao.nome, f"pegou {nomes} do chão → {token.nome}", "🎒", (c.x(), c.y()))
        self.conteudo_mudou.emit(alvo)
        self._transmitir()

    def _enviar_conteudo(self, conexao, alvo, pode_pegar, do_mestre=False):
        conexao.socket.sendTextMessage(codificar({
            "tipo": "conteudo", "id": alvo.uid, "nome": alvo.nome, "itens": self._itens_de(alvo),
            "pode_pegar": bool(pode_pegar), "do_mestre": do_mestre,
            "criatura": isinstance(alvo, TokenItem), "documento": bool(getattr(alvo, "documento", False)),
            "solto": bool(getattr(alvo, "solto", False))}))

    def _pegar(self, conexao, msg):
        alvo, token = self._alvo_e_token(conexao, msg.get("id"))
        if alvo is None or token is None:
            return
        if self._pode_abrir(conexao, alvo, token):
            return
        if not isinstance(alvo, TokenItem) and not alvo.pode_pegar:
            return
        itens = self._itens_de(alvo)
        item = next((i for i in itens if i.get("id") == msg.get("item")), None)
        if item is None:
            return
        itens = [i for i in itens if i is not item]
        self._guardar_itens(alvo, itens)
        inv = token.info.setdefault("inventario", {"v": [], "vis": "oculto"})
        lista = list(inv.get("v") or [])
        lista.append(dict(item, origem=alvo.nome))
        token.definir_info("inventario", lista)
        qtd = item.get("qtd", 1)
        origem = "do chão" if getattr(alvo, "solto", False) else f"de {alvo.nome}"
        self.registrar(conexao.nome, f"pegou {item.get('nome', '?')}{f' (x{qtd})' if qtd and qtd != 1 else ''} "
                                     f"{origem} → {token.nome}", "🎒")
        if getattr(alvo, "solto", False) and not itens:
            self.cena.definir_item_visivel(alvo, False)   # o papel/chave saiu do chão
        else:
            self._enviar_conteudo(conexao, alvo, True if isinstance(alvo, TokenItem) else alvo.pode_pegar)
        self.conteudo_mudou.emit(alvo)

    def _mover_prop(self, conexao, msg):
        # Jogador empurrando/levando um objeto (cama pra bloquear a porta, caixote...)
        from ..config import CELULA, fmt_m
        from ..mesa.props import PropItem
        prop, token = self._alvo_e_token(conexao, msg.get("id"))
        if not isinstance(prop, PropItem):
            return
        try:
            x, y = float(msg["x"]), float(msg["y"])
        except (KeyError, TypeError, ValueError):
            return
        motivo = None
        if not prop.movel:
            motivo = "Isso não dá pra mover."
        elif token is None:
            motivo = "Você precisa de um token na mesa."
        elif self.combate.ativo and self.combate.vez != token.uid:
            motivo = "Espere a sua vez."
        elif self._distancia(token, prop) > 1.5:
            motivo = "Chegue mais perto pra mover."
        if motivo:
            conexao.socket.sendTextMessage(codificar({"tipo": "aviso", "texto": motivo}))
            self._recusa(conexao.nome, prop, "tentou mover {t} (" + motivo.rstrip(".").lower() + ")")
            self.transmitir_agora()
            return
        # o objeto só vai até onde o personagem alcança (encostado nele, ~1,5 m da borda)
        antes = prop.centro_cena()
        camada = prop.parentItem()
        nova = camada.mapFromScene(QPointF(x, y))
        prop.setPos(nova)
        # Regra: se continuar ao alcance do personagem, vai pra onde ele quiser;
        # senão, cada empurrão leva o objeto no máximo 1,5 m.
        c = token.centro_cena()
        centro = prop.centro_cena()
        alcance = token.diametro / 2 + 1.5 * CELULA + max(prop.largura, prop.altura) / 2
        d = ((centro.x() - c.x()) ** 2 + (centro.y() - c.y()) ** 2) ** 0.5
        mov = centro - antes
        passo = (mov.x() ** 2 + mov.y() ** 2) ** 0.5
        if d > alcance and passo > 1.5 * CELULA:
            alvo_centro = antes + mov * (1.5 * CELULA / passo)
            prop.setPos(prop.pos() + camada.mapFromScene(alvo_centro) - camada.mapFromScene(centro))
            QTimer.singleShot(150, self.transmitir_agora)
        depois = prop.centro_cena()
        dist = ((depois.x() - antes.x()) ** 2 + (depois.y() - antes.y()) ** 2) ** 0.5 / CELULA
        if dist >= 0.1:
            self.registrar(conexao.nome, f"moveu {prop.nome} {fmt_m(dist)} m", "✋", (depois.x(), depois.y()))
            if (prop.gatilho or {}).get("quando") == "mover":
                self.disparar(prop.gatilho, conexao.nome, token, (depois.x(), depois.y()), conexao)

    @staticmethod
    def _chave_no_inventario(token, nome_chave: str):
        # procura um item com o nome da chave no inventário do personagem
        from ..compendio.compendio import sem_acento
        if not token or not nome_chave:
            return None
        alvo = sem_acento(nome_chave.strip())
        for item in token.info.get("inventario", {}).get("v") or []:
            if sem_acento(str(item.get("nome", "")).strip()) == alvo:
                return item
        return None

    def _usar_chave(self, conexao, token, alvo, coisa) -> bool:
        # tem a chave? destranca (e gasta, se for o caso). True = destrancou
        item = self._chave_no_inventario(token, getattr(alvo, "chave", ""))
        if item is None:
            return False
        if hasattr(alvo, "trancado"):
            alvo.trancado = False
        if hasattr(alvo, "trancada"):
            alvo.trancada = False
        if alvo.gasta_chave:
            lista = [i for i in token.info.get("inventario", {}).get("v") or [] if i is not item]
            token.definir_info("inventario", lista)
        conexao.socket.sendTextMessage(codificar(
            {"tipo": "aviso", "texto": f"🗝 Você destrancou {coisa} com {item.get('nome')}."
                                       + (" (a chave ficou presa na fechadura)" if alvo.gasta_chave else "")}))
        self.registrar(conexao.nome, f"usou {item.get('nome')} e destrancou {alvo.nome}", "🗝")
        return True

    def _porta_do_player(self, conexao, msg):
        from ..config import CELULA
        from ..mesa.portas import JANELAS, PortaItem
        porta = self.cena.item_por_id(str(msg.get("id", "")))
        if not isinstance(porta, PortaItem) or not porta.isVisible() or not porta.parentItem().isVisible():
            return
        coisa = "a janela" if porta.tipo in JANELAS else "a porta"
        meus = [t for t in self.cena.itens_do_usuario()
                if isinstance(t, TokenItem) and mesmo_nome(t.dono, conexao.nome) and t.isVisible()]

        def dist(t):
            a, b = porta.pontas_cena()
            c = t.centro_cena()
            ab = b - a
            tam = ab.x() ** 2 + ab.y() ** 2 or 1
            k = max(0.0, min(1.0, ((c.x() - a.x()) * ab.x() + (c.y() - a.y()) * ab.y()) / tam))
            q = a + ab * k
            return max(0.0, (((c.x() - q.x()) ** 2 + (c.y() - q.y()) ** 2) ** 0.5 - t.diametro / 2) / CELULA)
        token = min(meus, key=dist) if meus else None
        motivo = None
        if not porta.jogadores_abrem:
            motivo = "Não dá pra abrir isso."
        elif token is None:
            motivo = "Você precisa de um token na mesa."
        elif dist(token) > 1.5:
            motivo = "Chegue mais perto."
        elif self.combate.ativo and self.combate.vez != token.uid:
            motivo = "Espere a sua vez."
        elif porta.trancada and not porta.aberta and not self._usar_chave(conexao, token, porta, coisa):
            motivo = "🔒 Está trancada."
        if motivo:
            conexao.socket.sendTextMessage(codificar({"tipo": "aviso", "texto": motivo}))
            self._recusa(conexao.nome, porta, f"tentou abrir {porta.nome} (" +
                         motivo.replace("🔒 ", "").rstrip(".").lower() + ")")
            return
        porta.alternar()
        c = porta.scenePos()
        self.registrar(conexao.nome, f"{'abriu' if porta.aberta else 'fechou'} {coisa} ({porta.nome})", "🚪",
                       (c.x(), c.y()))

    def _ficha_do_player(self, conexao, msg):
        # o jogador salvou a ficha dele
        from ..ui.janela_ficha import aplicar_pacote
        token = self.cena.item_por_id(str(msg.get("id", "")))
        pacote = msg.get("pacote")
        if not isinstance(token, TokenItem) or not mesmo_nome(token.dono, conexao.nome):
            return
        if not isinstance(pacote, dict) or not isinstance(pacote.get("ficha"), dict):
            return
        if len(codificar(pacote)) > 400_000:
            return   # grande demais
        aplicar_pacote(token, pacote)
        self.ficha_mudou.emit(token)
        self.registrar(conexao.nome, f"salvou a ficha de {token.nome}", "📜")

    # ------------------------------------------------------------ gatilhos / armadilhas
    def _checar_areas(self, conexao, token, x, y):
        meio = token.diametro / 2
        centro = QPointF(x + meio, y + meio)
        for area in self.cena.areas_gatilho():
            chave = (area.uid, token.uid)
            dentro = area.contem(centro)
            if dentro and chave not in self._dentro_de:
                self._dentro_de.add(chave)
                self.disparar(area.gatilho, conexao.nome, token, (centro.x(), centro.y()), conexao)
                area.update()
            elif not dentro:
                self._dentro_de.discard(chave)

    def disparar(self, gatilho, quem, token, pos, conexao=None, manual=False):
        from ..jogo.gatilhos import executar, pode_disparar
        if not manual and not pode_disparar(gatilho):
            return False
        feito = executar(self, gatilho, quem, token, pos, conexao)
        nome = gatilho.get("nome", "Armadilha")
        resumo = f"⚡ {nome} disparou" + (f" ({quem})" if quem and not manual else " (você disparou)") + \
                 (": " + "; ".join(feito) if feito else "")
        self.registrar(quem if not manual else "Mestre", f"disparou {nome}" + (": " + "; ".join(feito) if feito else ""),
                       "⚡", pos)
        self.gatilho_disparou.emit(resumo)
        self.cena.marcar_modificada()
        self.transmitir_agora()
        return True

    def mostrar_conteudo(self, prop, nomes=None, pode_pegar=False):
        # o mestre mostra o que tem dentro (pra todos ou pra alguns)
        alvos = [c for c in self.conexoes if c.nome and (nomes is None or
                 any(mesmo_nome(c.nome, n) for n in nomes))]
        for c in alvos:
            self._enviar_conteudo(c, prop, pode_pegar, do_mestre=True)
        quem = "todos" if nomes is None else ", ".join(nomes)
        self.registrar("Mestre", f"mostrou o conteúdo de {prop.nome} para {quem}", "👁")

    # ------------------------------------------------------------ ping
    def ping_mestre(self, x, y):
        self._para_todos({"tipo": "ping", "nome": "Mestre", "x": x, "y": y})

    def olhar_aqui(self, cena, x, y, escala, travar=0) -> int:
        """(v0.58) 📣 "Todos olhem pra cá": manda a câmera de cada jogador que está NESTE andar até (x, y).
        Quem está em outro andar recebe só um aviso. Volta quantos jogadores foram levados."""
        from ..mesa.andares import nome_andar
        if getattr(cena, "predio", None):
            onde = nome_andar(getattr(cena, "andar", 0))
        else:
            onde = getattr(cena, "nome_aba", "") or "outro lugar"
        travar = max(0, min(30, int(travar or 0)))
        n = 0
        for c in self.conexoes:
            if not c.nome:
                continue
            if self._cena_de(c) is cena:
                c.socket.sendTextMessage(codificar({"tipo": "olhar_aqui", "x": round(x, 1), "y": round(y, 1),
                                                    "escala": round(float(escala), 3), "travar": travar}))
                n += 1
            else:
                c.socket.sendTextMessage(codificar({"tipo": "aviso",
                                                    "texto": f"📣 O mestre chamou a atenção pro {onde}."}))
        self.registrar("Mestre", "chamou a atenção de todos pra cá" + (f" (câmera travada {travar} s)" if travar else ""),
                       "📣", (x, y))
        return n

    # ------------------------------------------------------------ combate
    def _tokens(self):
        """Os tokens de todos os andares ao vivo (o combate pode ter gente em andares diferentes)."""
        saida = {}
        for c in dict.fromkeys(self.andares + [self.cena]):
            try:
                saida.update({t.uid: t for t in c.itens_do_usuario() if isinstance(t, TokenItem)})
            except RuntimeError:
                continue
        return saida

    def proximo_turno(self):
        # Acaba o turno de quem estava jogando: as condições com duração perdem 1 rodada
        if not self.combate.ativo:
            return
        token = self._tokens().get(self.combate.vez)
        if token is not None:
            self._contar_duracoes(token)
        self.combate.proximo()
        tokens = self._tokens()
        for _ in range(len(self.combate.participantes)):
            t = tokens.get(self.combate.vez)
            if t is None or t.estado != "morto":
                break
            self.combate.proximo()   # morto não joga
        self.atualizar_combate()

    def _contar_duracoes(self, token):
        from ..jogo.condicoes import CONDICOES
        campo = token.info.get("condicoes") or {}
        dur = dict(campo.get("dur") or {})
        if not dur:
            return
        lista = list(campo.get("v") or [])
        acabaram = []
        for chave in list(dur):
            dur[chave] -= 1
            if dur[chave] <= 0:
                del dur[chave]
                if chave in lista:
                    lista.remove(chave)
                acabaram.append(CONDICOES.get(chave, (chave, ""))[0])
        campo["dur"] = dur
        token.definir_info("condicoes", lista)
        if acabaram:
            self.aviso.emit(f"{token.nome}: acabou {', '.join(acabaram)}.")

    def atualizar_combate(self):
        # chamado pelo painel do mestre quando ele mexe no combate
        tokens = self._tokens()
        self.combate.atualizar_nomes(tokens)
        vez = self.combate.vez if self.combate.ativo else None
        if vez != self._vez_marcada:
            # começou o turno de alguém: marca de onde ele saiu (pra mostrar quanto andou)
            self._vez_marcada = vez
            p = self.combate.participante(vez) if vez else None
            if p is not None:
                p["extra"] = 0.0
            for t in tokens.values():
                t.origem_turno = t.centro_cena() if t.uid == vez else None
        for t in tokens.values():
            t.definir_vez(self.combate.ativo and t.uid == self.combate.vez)
            t.limite_turno = self.limite_do_turno(t)
            t.update()
        self.combate_mudou.emit()
        self.transmitir_agora()

    def transmitir_agora(self):
        if self.aberto:
            self._transmitir()

    # ------------------------------------------------------------ cursores
    def _para_todos(self, msg: dict, exceto=None):
        texto = codificar(msg)
        for c in self.conexoes:
            if c.nome and c is not exceto:
                c.socket.sendTextMessage(texto)

    def _enviar_cursor_mestre(self, x, y):
        if not self.aberto:
            return
        if not self.mostrar_meu_cursor:
            x = y = None  # escondido: os players só recebem "sumiu"
        self._para_todos({"tipo": "cursor", "nome": "Mestre", "x": x, "y": y})

    def definir_mostrar_meu_cursor(self, mostrar: bool):
        self.mostrar_meu_cursor = mostrar
        if not mostrar:
            self._enviar_cursor_mestre(None, None)

    # ------------------------------------------------------------ transmissão
    def _agendar(self):
        if self.aberto and self.conexoes and not self._timer.isActive():
            self._timer.start()

    def _transmitir(self):
        prontos = [c for c in self.conexoes if c.nome]
        if not prontos:
            return
        por_andar = {}   # 🏢 um estado por andar (cada jogador recebe o andar do token dele)
        for conexao in prontos:
            cena = self._cena_de(conexao)
            if id(cena) not in por_andar:
                por_andar[id(cena)] = self._estado_completo(cena)
            estado, imagens = por_andar[id(cena)]
            mudou_de_andar = getattr(conexao, "cena_vista", None) is not cena
            conexao.cena_vista = cena
            self._enviar_estado(conexao, estado, imagens)
            if mudou_de_andar:
                self._fluidos_pra(conexao)   # o gás/líquido do andar novo
        atlas_rede = getattr(self, "atlas_rede", None)
        if atlas_rede is not None:
            atlas_rede.agendar()   # 🌍 cidade/mundo (só o revelado), marcadores (v0.64)

    def _estado_completo(self, cena=None):
        cena = cena or self.cena
        estado, imagens = montar_estado(cena)
        estado["combate"] = self.combate.para_dict()
        vez = self._tokens().get(self.combate.vez) if self.combate.ativo else None
        origem = getattr(vez, "origem_turno", None) if vez is not None else None
        estado["combate"]["origem"] = [origem.x(), origem.y()] if origem is not None else None
        estado["combate"]["limite"] = self.limite_do_turno(vez) if vez is not None else None
        estado["regras"] = {"movem": self.players_movem, "templates": self.players_templates,
                            "lapis": self.players_lapis}
        estado["musica"] = self.musica_agora()
        # retratos do grupo (lista à parte: não some quando o companheiro sai da visão)
        from ..mesa.grupo import montar_grupo
        estado["_grupo"], imgs_grupo = montar_grupo(cena)
        from ..mesa.andares import nome_andar
        estado["andar"] = nome_andar(getattr(cena, "andar", 0)) if getattr(cena, "predio", None) else ""
        imagens.update(imgs_grupo)
        return estado, imagens

    def _enviar_estado(self, conexao: Conexao, estado, imagens):
        estado = filtrar_pela_visao(estado, conexao.nome or "")
        estado = filtrar_info(estado, conexao.nome or "")
        from ..mesa.grupo import filtrar_grupo
        estado = dict(estado)
        estado["grupo"] = filtrar_grupo(estado.pop("_grupo", []), conexao.nome or "")
        for camada in estado["camadas"]:
            for d in camada["itens"]:
                if "ficha" in d:
                    marca = codificar(d["ficha"])
                    if conexao.fichas_enviadas.get(d["id"]) == marca:
                        del d["ficha"]
                    else:
                        conexao.fichas_enviadas[d["id"]] = marca
        for chave, dados in imagens.items():
            if chave not in conexao.imagens_enviadas:
                conexao.socket.sendTextMessage(
                    codificar({"tipo": "asset", "id": chave, "dados": b64(dados)}))
                conexao.imagens_enviadas.add(chave)
        # Terreno e paredes podem ser grandes: só manda quando mudou
        construcao = codificar(estado["construcao"])
        if construcao == conexao.ultima_construcao:
            estado = {k: v for k, v in estado.items() if k != "construcao"}
        else:
            conexao.ultima_construcao = construcao
        estado = dict(estado, projecao=self._projecao_pra(conexao))
        enviar_grande(conexao.socket, codificar(estado))   # (v0.82) comprimida
        if self.ambientes:
            self._sons_atrasados(conexao)
