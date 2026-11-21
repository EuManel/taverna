"""
📚 Livros entre mestre e jogadores (v0.43) — pedido do Manel.

- O MESTRE escolhe, na Biblioteca → PDFs, quais livros cada jogador pode ver ("Liberar pros jogadores").
  O PDF VAI PELA REDE pro jogador (em partes, sem travar a mesa) e aparece na aba "📗 Do mestre".
  Se o mestre tirar a liberação, a cópia do jogador é apagada.
- O mestre VÊ a biblioteca de cada jogador (a lista dos PDFs dele, aba "👥 Dos jogadores") e pode
  pegar uma cópia de um livro personalizado. O jogador é avisado quando isso acontece.
- Responsabilidade: só compartilhe o que você tem direito de compartilhar (aviso na tela).

Mensagens (rede):
  mestre → jogador: livros {lista} · livro_ini {id,titulo,tamanho} · livro_parte {id,dados} · livro_fim {id}
                    · livro_pedido_mestre {id}
  jogador → mestre: livro_pedir {id} · minha_biblioteca {livros} · livro_up_ini/livro_up_parte/livro_up_fim
"""

import base64
import hashlib
import json
import os
import re

from PyQt6.QtCore import QObject, QSettings, QStandardPaths, QTimer, pyqtSignal

PARTE = 384 * 1024            # bytes por mensagem
LIMITE = 400 * 1024 * 1024    # maior livro que dá pra mandar (400 MB)
TIPOS = {"livros", "livro_ini", "livro_parte", "livro_fim", "livro_pedido_mestre",
         "livro_pedir", "minha_biblioteca", "livro_up_ini", "livro_up_parte", "livro_up_fim"}
AVISO = ("Só compartilhe livros que você tem direito de compartilhar (os seus, os de licença livre, os que "
         "o autor permite). A responsabilidade pelo que é enviado é de quem envia.")


def _docs() -> str:
    return QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation) \
        or os.path.expanduser("~")


def _nome_arquivo(titulo: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", titulo).strip().rstrip(".")[:120] or "Livro"


def id_do_caminho(caminho: str) -> str:
    """Id estável de um PDF (caminho + tamanho + data), sem precisar ler o arquivo inteiro."""
    try:
        st = os.stat(caminho)
        base = f"{os.path.normcase(os.path.abspath(caminho))}|{st.st_size}|{int(st.st_mtime)}"
    except OSError:
        base = os.path.normcase(os.path.abspath(caminho))
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:20]


def pdfs_da_biblioteca(app_nome: str) -> list[str]:
    """Todos os PDFs da aba 📕 PDFs (arquivos avulsos + os das pastas)."""
    config = QSettings("Taverna", app_nome)
    saida = []
    for chave in ("meus_pdfs",):
        try:
            saida += [c for c in json.loads(config.value(chave, "[]")) if os.path.isfile(c)]
        except (TypeError, ValueError):
            pass
    try:
        pastas = json.loads(config.value("pastas_pdf", "[]"))
    except (TypeError, ValueError):
        pastas = []
    for pasta in pastas:
        if os.path.isdir(pasta):
            for raiz, _, arquivos in os.walk(pasta):
                saida += [os.path.join(raiz, a) for a in arquivos if a.lower().endswith(".pdf")]
    vistos, unicos = set(), []
    for c in saida:
        k = os.path.normcase(os.path.abspath(c))
        if k not in vistos:
            vistos.add(k)
            unicos.append(c)
    return unicos


class _Envio:
    """Manda um arquivo em partes, uma por 'tique' (não trava a mesa nem a rede)."""

    def __init__(self, caminho, ident, titulo, mandar, prefixo):
        self.f = open(caminho, "rb")
        self.ident, self.titulo, self.mandar, self.prefixo = ident, titulo, mandar, prefixo
        self.tamanho = os.path.getsize(caminho)
        self.mandar({"tipo": f"{prefixo}_ini", "id": ident, "titulo": titulo, "tamanho": self.tamanho})

    def passo(self) -> bool:
        """Manda mais uma parte. False = acabou."""
        dados = self.f.read(PARTE)
        if not dados:
            self.f.close()
            self.mandar({"tipo": f"{self.prefixo}_fim", "id": self.ident})
            return False
        self.mandar({"tipo": f"{self.prefixo}_parte", "id": self.ident,
                     "dados": base64.b64encode(dados).decode("ascii")})
        return True

    def cancelar(self):
        try:
            self.f.close()
        except OSError:
            pass


class _Fila(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.envios = []
        self.timer = QTimer(self)
        self.timer.setInterval(15)
        self.timer.timeout.connect(self._tique)

    def por(self, envio):
        self.envios.append(envio)
        self.timer.start()

    def cancelar(self, teste):
        for e in [e for e in self.envios if teste(e)]:
            e.cancelar()
            self.envios.remove(e)

    def _tique(self):
        if not self.envios:
            self.timer.stop()
            return
        e = self.envios[0]
        try:
            continua = e.passo()
        except (OSError, RuntimeError):
            continua = False
        if not continua:
            self.envios.pop(0)
        elif len(self.envios) > 1:   # reveza entre os envios
            self.envios.append(self.envios.pop(0))


class _Recebimento:
    def __init__(self, destino, tamanho, titulo):
        self.destino, self.tamanho, self.titulo = destino, int(tamanho), titulo
        self.temp = destino + ".parcial"
        self.f = open(self.temp, "wb")
        self.recebido = 0

    def parte(self, dados_b64):
        dados = base64.b64decode(dados_b64)
        self.recebido += len(dados)
        if self.recebido > min(self.tamanho, LIMITE):
            raise ValueError("maior que o anunciado")
        self.f.write(dados)

    def fim(self) -> bool:
        self.f.close()
        if self.recebido != self.tamanho:
            os.remove(self.temp)
            return False
        if os.path.exists(self.destino):
            os.remove(self.destino)
        os.replace(self.temp, self.destino)
        return True

    def cancelar(self):
        try:
            self.f.close()
            os.remove(self.temp)
        except OSError:
            pass


# ====================================================================== lado do MESTRE
class LivrosMestre(QObject):
    mudou = pyqtSignal()                      # liberações mudaram
    biblioteca_jogador = pyqtSignal(str)      # a lista de algum jogador chegou/mudou
    copia_recebida = pyqtSignal(str, str)     # nome do jogador, caminho do arquivo

    def __init__(self, servidor):
        super().__init__(servidor)
        self.servidor = servidor
        self.config = QSettings("Taverna", "Mestre")
        self.fila = _Fila(self)
        self.dos_jogadores: dict[str, list] = {}    # nome → [{id, titulo, tamanho}]
        self._subindo: dict[tuple, _Recebimento] = {}

    # --- liberações: {caminho: {"titulo", "jogadores": [nomes] ou ["*"]}}
    def liberados(self) -> dict:
        try:
            return json.loads(self.config.value("livros_liberados", "{}"))
        except (TypeError, ValueError):
            return {}

    def liberar(self, caminho: str, jogadores: list[str], titulo: str | None = None):
        lib = self.liberados()
        if jogadores:
            lib[caminho] = {"titulo": titulo or os.path.splitext(os.path.basename(caminho))[0],
                            "jogadores": list(jogadores)}
        else:
            lib.pop(caminho, None)
        self.config.setValue("livros_liberados", json.dumps(lib, ensure_ascii=False))
        self.mudou.emit()
        for c in self.servidor.conexoes:
            if c.nome:
                self.enviar_lista(c)

    def para(self, nome: str) -> list[dict]:
        saida = []
        for caminho, info in self.liberados().items():
            quem = info.get("jogadores", [])
            if ("*" in quem or any(n.casefold() == nome.casefold() for n in quem)) and os.path.isfile(caminho):
                tamanho = os.path.getsize(caminho)
                if tamanho <= LIMITE:
                    saida.append({"id": id_do_caminho(caminho), "titulo": info.get("titulo", "Livro"),
                                  "tamanho": tamanho, "_caminho": caminho})
        return saida

    def _mandar(self, conexao, msg):
        from .protocolo import codificar
        try:
            conexao.socket.sendTextMessage(codificar(msg))
        except RuntimeError:
            pass

    def enviar_lista(self, conexao):
        lista = [{k: v for k, v in d.items() if k != "_caminho"} for d in self.para(conexao.nome)]
        ids = {d["id"] for d in lista}
        self.fila.cancelar(lambda e: e.mandar.__self__ is conexao and e.ident not in ids)
        self._mandar(conexao, {"tipo": "livros", "lista": lista})

    def ao_entrar(self, conexao):
        self.enviar_lista(conexao)

    def ao_sair(self, conexao):
        self.fila.cancelar(lambda e: getattr(e.mandar, "__self__", None) is conexao)
        self.dos_jogadores.pop(conexao.nome or "", None)
        for chave in [k for k in self._subindo if k[0] == conexao.nome]:
            self._subindo.pop(chave).cancelar()
        self.biblioteca_jogador.emit(conexao.nome or "")

    def pedir_copia(self, nome: str, ident: str) -> bool:
        c = next((c for c in self.servidor.conexoes if c.nome and c.nome.casefold() == nome.casefold()), None)
        if c is None:
            return False
        self._mandar(c, {"tipo": "livro_pedido_mestre", "id": ident})
        return True

    def pasta_copias(self, nome: str) -> str:
        pasta = os.path.join(_docs(), "Taverna", "Livros dos jogadores", _nome_arquivo(nome))
        os.makedirs(pasta, exist_ok=True)
        return pasta

    def mensagem(self, conexao, msg):
        tipo = msg.get("tipo")
        nome = conexao.nome
        if tipo == "livro_pedir":   # o jogador quer um livro liberado pra ele
            alvo = next((d for d in self.para(nome) if d["id"] == msg.get("id")), None)
            if alvo:
                envio = _Envio(alvo["_caminho"], alvo["id"], alvo["titulo"],
                               _MandarPara(self, conexao), "livro")
                self.fila.por(envio)
        elif tipo == "minha_biblioteca":
            livros = []
            for d in (msg.get("livros") or [])[:2000]:
                try:
                    livros.append({"id": str(d["id"])[:40], "titulo": str(d["titulo"])[:160],
                                   "tamanho": int(d.get("tamanho", 0))})
                except (KeyError, TypeError, ValueError):
                    continue
            self.dos_jogadores[nome] = livros
            self.biblioteca_jogador.emit(nome)
        elif tipo == "livro_up_ini":
            try:
                tamanho = int(msg["tamanho"])
                titulo = str(msg.get("titulo", "Livro"))[:160]
            except (KeyError, TypeError, ValueError):
                return
            if tamanho > LIMITE:
                return
            destino = os.path.join(self.pasta_copias(nome), _nome_arquivo(titulo) + ".pdf")
            velho = self._subindo.pop((nome, msg.get("id")), None)
            if velho:
                velho.cancelar()
            self._subindo[(nome, msg.get("id"))] = _Recebimento(destino, tamanho, titulo)
        elif tipo == "livro_up_parte":
            r = self._subindo.get((nome, msg.get("id")))
            if r:
                try:
                    r.parte(msg.get("dados", ""))
                except (ValueError, OSError):
                    self._subindo.pop((nome, msg.get("id"))).cancelar()
        elif tipo == "livro_up_fim":
            r = self._subindo.pop((nome, msg.get("id")), None)
            if r and r.fim():
                self.copia_recebida.emit(nome, r.destino)


class _MandarPara:
    """'função' que manda pra uma conexão (guarda quem é, pra cancelar o envio se ela sair)."""

    def __init__(self, livros, conexao):
        self.livros, self.__self__ = livros, conexao

    def __call__(self, msg):
        self.livros._mandar(self.__self__, msg)


# ====================================================================== lado do JOGADOR
class LivrosPlayer(QObject):
    mudou = pyqtSignal()               # chegou/saiu livro do mestre (ou progresso)
    aviso = pyqtSignal(str)            # "o mestre pegou uma cópia de …"

    def __init__(self, cliente, parent=None):
        super().__init__(parent)
        self.cliente = cliente
        self.fila = _Fila(self)
        self.lista: list[dict] = []          # o que o mestre liberou
        self._baixando: dict[str, _Recebimento] = {}
        self._meus: dict[str, str] = {}      # id → caminho (os PDFs do próprio jogador)

    def pasta(self) -> str:
        pasta = os.path.join(_docs(), "Taverna", "Livros do mestre")
        os.makedirs(pasta, exist_ok=True)
        return pasta

    def _indice_caminho(self):
        return os.path.join(self.pasta(), "indice.json")

    def indice(self) -> dict:
        try:
            with open(self._indice_caminho(), encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def _gravar_indice(self, ind):
        with open(self._indice_caminho(), "w", encoding="utf-8") as f:
            json.dump(ind, f, ensure_ascii=False)

    def livros(self) -> list[dict]:
        """Pra aba 📗 Do mestre: [{id, titulo, caminho|None, progresso}]."""
        ind = self.indice()
        saida = []
        for d in self.lista:
            r = self._baixando.get(d["id"])
            caminho = ind.get(d["id"], {}).get("arquivo")
            saida.append({"id": d["id"], "titulo": d["titulo"],
                          "caminho": caminho if caminho and os.path.isfile(caminho) and not r else None,
                          "progresso": (r.recebido / max(1, r.tamanho)) if r else None})
        return saida

    def ao_conectar(self):
        self.enviar_minha_biblioteca()

    def enviar_minha_biblioteca(self):
        self._meus = {}
        livros = []
        for c in pdfs_da_biblioteca("Player"):
            ident = id_do_caminho(c)
            self._meus[ident] = c
            try:
                tamanho = os.path.getsize(c)
            except OSError:
                continue
            livros.append({"id": ident, "titulo": os.path.splitext(os.path.basename(c))[0], "tamanho": tamanho})
        self.cliente.enviar({"tipo": "minha_biblioteca", "livros": livros})

    def mensagem(self, msg):
        tipo = msg.get("tipo")
        if tipo == "livros":
            self.lista = []
            for d in msg.get("lista") or []:
                try:
                    self.lista.append({"id": str(d["id"])[:40], "titulo": str(d["titulo"])[:160],
                                       "tamanho": int(d["tamanho"])})
                except (KeyError, TypeError, ValueError):
                    continue
            ind = self.indice()
            ids = {d["id"] for d in self.lista}
            for ident in [i for i in ind if i not in ids]:   # o mestre tirou a liberação: apaga a cópia
                try:
                    os.remove(ind[ident]["arquivo"])
                except (OSError, KeyError):
                    pass
                ind.pop(ident)
            self._gravar_indice(ind)
            for d in self.lista:   # pede o que ainda não tem
                arq = ind.get(d["id"], {}).get("arquivo")
                if not (arq and os.path.isfile(arq) and os.path.getsize(arq) == d["tamanho"]):
                    self.cliente.enviar({"tipo": "livro_pedir", "id": d["id"]})
            self.mudou.emit()
        elif tipo == "livro_ini":
            ident = str(msg.get("id", ""))[:40]
            d = next((x for x in self.lista if x["id"] == ident), None)
            if not d or int(msg.get("tamanho", 0)) > LIMITE:
                return
            destino = os.path.join(self.pasta(), _nome_arquivo(d["titulo"]) + f" [{ident[:6]}].pdf")
            self._baixando[ident] = _Recebimento(destino, msg.get("tamanho", 0), d["titulo"])
            self.mudou.emit()
        elif tipo == "livro_parte":
            r = self._baixando.get(msg.get("id"))
            if r:
                try:
                    r.parte(msg.get("dados", ""))
                except (ValueError, OSError):
                    self._baixando.pop(msg.get("id")).cancelar()
                self.mudou.emit()
        elif tipo == "livro_fim":
            ident = msg.get("id")
            r = self._baixando.pop(ident, None)
            if r and r.fim():
                ind = self.indice()
                ind[ident] = {"titulo": r.titulo, "arquivo": r.destino}
                self._gravar_indice(ind)
            self.mudou.emit()
        elif tipo == "livro_pedido_mestre":   # o mestre quer uma cópia de um livro meu
            ident = str(msg.get("id", ""))
            if not self._meus:
                self.enviar_minha_biblioteca()
            caminho = self._meus.get(ident)
            if caminho and os.path.isfile(caminho) and os.path.getsize(caminho) <= LIMITE:
                titulo = os.path.splitext(os.path.basename(caminho))[0]
                self.fila.por(_Envio(caminho, ident, titulo, self.cliente.enviar, "livro_up"))
                self.aviso.emit(f"📚 O mestre pegou uma cópia de “{titulo}” da sua biblioteca.")
