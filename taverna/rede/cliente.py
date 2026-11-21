"""
Conexão do Player com o Mestre.
"""

from PyQt6.QtCore import QObject, QUrl, pyqtSignal
from PyQt6.QtWebSockets import QWebSocket

from .protocolo import VERSAO_PROTOCOLO, codificar, de_b64, decodificar


class ClienteRede(QObject):
    conectado = pyqtSignal(str)        # nome confirmado pelo mestre
    recusado = pyqtSignal(str)         # motivo
    desconectado = pyqtSignal(str)     # motivo/erro (pode ser vazio)
    estado_recebido = pyqtSignal(dict)
    cursor_recebido = pyqtSignal(str, object, object)   # nome, x, y (None = saiu)
    rolagem_recebida = pyqtSignal(dict)
    erro_dados = pyqtSignal(str)
    ping_recebido = pyqtSignal(str, float, float)
    conteudo_recebido = pyqtSignal(dict)
    aviso_recebido = pyqtSignal(str)
    outra_mensagem = pyqtSignal(dict)   # relâmpago, som, música... (quem quiser escuta)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.socket = QWebSocket()
        self.socket.setParent(self)
        self.socket.connected.connect(self._abriu)
        self.socket.disconnected.connect(self._fechou)
        self.socket.textMessageReceived.connect(self._mensagem)
        self.socket.binaryMessageReceived.connect(self._binaria)   # (v0.82) a mesa vem comprimida
        self.socket.errorOccurred.connect(self._erro)
        self.imagens: dict[str, bytes] = {}
        self.nome = ""
        self.dentro = False
        self._ultimo_erro = ""
        self._foi_recusado = False

    def conectar(self, ip: str, porta: int, nome: str):
        self.nome = nome
        self._ultimo_erro = ""
        self._foi_recusado = False
        self.socket.abort()
        self.socket.open(QUrl(f"ws://{ip.strip()}:{porta}"))

    def desconectar(self):
        self._foi_recusado = True  # saída voluntária: não tenta reconectar
        self.socket.close()

    def enviar(self, msg: dict):
        if self.dentro:
            self.socket.sendTextMessage(codificar(msg))

    def cursor(self, x, y):
        self.enviar({"tipo": "cursor", "x": None if x is None else round(x, 1),
                     "y": None if y is None else round(y, 1)})

    def girar(self, uid: str, direcao: float):
        self.enviar({"tipo": "girar", "id": uid, "direcao": round(direcao % 360, 1)})

    def porta(self, uid: str):
        self.enviar({"tipo": "porta", "id": uid})

    def interagir(self, uid: str):
        self.enviar({"tipo": "interagir", "id": uid})

    def salvar_ficha(self, uid: str, pacote: dict):
        self.enviar({"tipo": "ficha", "id": uid, "pacote": pacote})

    def mover_prop(self, uid: str, x: float, y: float):
        self.enviar({"tipo": "mover_prop", "id": uid, "x": round(x, 1), "y": round(y, 1)})

    def pegar(self, uid: str, item_id: str):
        self.enviar({"tipo": "pegar", "id": uid, "item": item_id})

    def ping(self, x: float, y: float):
        self.enviar({"tipo": "ping", "x": round(x, 1), "y": round(y, 1)})

    def rolar(self, expr: str, motivo: str = "", token: str = ""):
        from ..dados3d.visual import meus_dados   # (v0.74) a cara dos MEUS dados vai junto
        self.enviar({"tipo": "rolar", "expr": expr, "motivo": motivo, "token": token, "dv": meus_dados()})

    def mover(self, uid: str, x: float, y: float):
        self.enviar({"tipo": "mover", "id": uid, "x": round(x, 2), "y": round(y, 2)})

    # ------------------------------------------------------------
    def _abriu(self):
        self.socket.sendTextMessage(codificar(
            {"tipo": "ola", "nome": self.nome, "versao": VERSAO_PROTOCOLO}))

    def _fechou(self):
        estava = self.dentro
        self.dentro = False
        if not self._foi_recusado:
            self.desconectado.emit(self._ultimo_erro or
                                   ("O mestre fechou a taverna." if estava else
                                    "Não consegui falar com o mestre."))

    def _erro(self, _codigo):
        self._ultimo_erro = self.socket.errorString()

    def _binaria(self, dados):
        from .protocolo import abrir_binaria
        texto = abrir_binaria(dados)
        if texto is not None:
            self._mensagem(texto)

    def _mensagem(self, texto: str):
        msg = decodificar(texto)
        if msg is None:
            return
        tipo = msg["tipo"]
        if tipo == "bem_vindo":
            self.dentro = True
            self.nome = msg.get("nome", self.nome)
            self.conectado.emit(self.nome)
        elif tipo == "recusado":
            self._foi_recusado = True
            self.recusado.emit(msg.get("motivo", "O mestre recusou a conexão."))
        elif tipo == "asset":
            try:
                self.imagens[msg["id"]] = de_b64(msg["dados"])
            except (KeyError, ValueError):
                pass
        elif tipo == "estado":
            self.estado_recebido.emit(msg)
        elif tipo == "cursor":
            self.cursor_recebido.emit(str(msg.get("nome", "?")), msg.get("x"), msg.get("y"))
        elif tipo == "rolagem":
            self.rolagem_recebida.emit(msg)
        elif tipo == "conteudo":
            self.conteudo_recebido.emit(msg)
        elif tipo == "aviso":
            texto = str(msg.get("texto", ""))
            self.aviso_recebido.emit(("\u200b" if msg.get("longo") else "") + texto)
        elif tipo == "ping":
            try:
                self.ping_recebido.emit(str(msg.get("nome", "?")), float(msg["x"]), float(msg["y"]))
            except (KeyError, TypeError, ValueError):
                pass
        elif tipo == "erro_dados":
            self.erro_dados.emit(str(msg.get("motivo", "")))
        elif tipo == "cursor_sai":
            self.cursor_recebido.emit(str(msg.get("nome", "?")), None, None)
        else:
            self.outra_mensagem.emit(msg)
