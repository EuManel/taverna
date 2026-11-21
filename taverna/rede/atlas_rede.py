"""
🌍 Cidade e mundo pela rede (v0.64 — item 9, etapa 3). Lado do MESTRE.

Cada jogador recebe só o que é DELE:
  - a cidade onde fica a aba do token dele (e o mundo, se a cidade estiver marcada nele);
  - o retângulo do lugar dele (pra subir da mesa pra cidade no ponto certo) e o chão da aba (o encaixe fica
    igual ao do mestre);
  - os marcadores do grupo que estão em parte REVELADA;
  - a IMAGEM em pedaços de 256 px: só os pedaços que têm alguma parte revelada, já com a parte coberta
    APAGADA (transparente). O que está na névoa nunca sai do PC do mestre. Quando a névoa muda, só vão os
    pedaços que mudaram (e "pedaço vazio" pra apagar o que voltou a ser coberto).

Mensagens:
  {"tipo": "atlas", "chao": [x, y, w, h] | None, "cidade": {...} | None, "mundo": {...} | None,
   "marcadores": {"cidade": [...], "mundo": [...]}}
  {"tipo": "atlas_pedaco", "nivel": id, "x": px, "y": px, "dados": base64 PNG | ""}
"""

import hashlib
import math

import numpy as np
from PyQt6.QtCore import QBuffer, QIODevice, QObject, Qt, QTimer
from PyQt6.QtGui import QImage

from ..mesa import atlas as A
from .protocolo import b64, codificar

PEDACO = 256
LIMIAR = 12          # menos que isso de "revelado" conta como coberto (nada vaza pela borda)


def _array(img: QImage, canais: int):
    bits = img.constBits()
    bits.setsize(img.sizeInBytes())
    a = np.frombuffer(bits, np.uint8).reshape(img.height(), img.bytesPerLine())
    if canais == 1:
        return a[:, :img.width()]
    return a[:, :img.width() * 4].reshape(img.height(), img.width(), 4)


class AtlasServidor(QObject):
    def __init__(self, servidor, janela):
        super().__init__(janela)
        self.servidor = servidor
        self.janela = janela
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(300)
        self._timer.timeout.connect(self.enviar_todos)
        self._alfas: dict = {}   # nivel id -> (versão da névoa, alfa no tamanho da imagem)

    @property
    def atlas(self):
        return self.janela.atlas

    def agendar(self):
        if self.servidor.aberto and not self._timer.isActive():
            self._timer.start()

    def enviar_todos(self):
        for c in list(self.servidor.conexoes):
            if c.nome:
                try:
                    self.enviar(c)
                except RuntimeError:
                    continue

    # ------------------------------------------------------------ o que esse jogador pode ver
    def dados_do_jogador(self, nome: str) -> tuple[dict, list]:
        """(mensagem "atlas", [níveis cujos pedaços ele recebe])."""
        cena = self.servidor._cena_do_nome(nome)
        info = {"tipo": "atlas", "chao": None, "cidade": None, "mundo": None, "marcadores": {"cidade": [], "mundo": []}}
        cidade, lugar = self.atlas.lugar_da_cena(cena)
        if cidade is None:
            return info, []
        camada = getattr(self.janela, "camada_atlas", None)
        chao = camada._chao(cena) if camada is not None else None
        if chao is not None:
            info["chao"] = [chao.x(), chao.y(), chao.width(), chao.height()]
        niveis = [cidade]
        a = self.atlas.area(cidade)
        info["cidade"] = {"id": cidade["id"], "nome": cidade.get("nome", ""), "w": a.width(), "h": a.height(),
                          "escala": cidade.get("escala"), "nevoa": self.atlas.nevoa_ligada(cidade),
                          "lugar": {k: lugar[k] for k in ("x", "y", "w", "h")}}
        lc = self.atlas.lugar_da_cidade(cidade)
        if lc is not None and self.atlas.mundo is not None:
            m = self.atlas.mundo
            am = self.atlas.area(m)
            info["mundo"] = {"id": m["id"], "nome": m.get("nome", ""), "w": am.width(), "h": am.height(),
                             "escala": m.get("escala"), "nevoa": self.atlas.nevoa_ligada(m),
                             "lugar_cidade": {k: lc[k] for k in ("x", "y", "w", "h")}}
            niveis.append(m)
        if camada is not None:
            for quadro, nivel in (("cidade", cidade), ("mundo", self.atlas.mundo if info["mundo"] else None)):
                if nivel is None:
                    continue
                for mk in camada.marcadores(quadro, cidade):
                    if self.atlas.revelado(nivel, mk["pos"]) < 128:
                        continue   # marcador escondido na névoa: o jogador não sabe dele
                    info["marcadores"][quadro].append({"id": mk["id"], "x": round(mk["pos"].x(), 1),
                                                       "y": round(mk["pos"].y(), 1), "cor": mk["cor"].name(),
                                                       "nome": mk["nome"]})
        return info, niveis

    def enviar(self, conexao):
        info, niveis = self.dados_do_jogador(conexao.nome)
        texto = codificar(info)
        if texto != getattr(conexao, "atlas_ultimo", None):
            from .protocolo import enviar_grande
            enviar_grande(conexao.socket, texto)   # (v0.82) comprimida se for grande
            conexao.atlas_ultimo = texto
        for nivel in niveis:
            self._pedacos(conexao, nivel)

    # ------------------------------------------------------------ os pedaços da imagem
    def _alfa(self, nivel) -> np.ndarray | None:
        """A névoa no tamanho da imagem (0 = coberto). None = névoa desligada (tudo aberto)."""
        if not self.atlas.nevoa_ligada(nivel):
            return None
        versao = self.atlas.versao_nevoa.get(nivel["id"], 0)
        guardado = self._alfas.get(nivel["id"])
        if guardado and guardado[0] == versao:
            return guardado[1]
        img = self.atlas.imagem(nivel)
        m = self.atlas.mascara(nivel).scaled(img.width(), img.height(), Qt.AspectRatioMode.IgnoreAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
        alfa = _array(m.convertToFormat(QImage.Format.Format_Grayscale8), 1).copy()
        alfa[alfa < LIMIAR] = 0
        self._alfas[nivel["id"]] = (versao, alfa)
        return alfa

    def _pedacos(self, conexao, nivel):
        versao = (nivel["id"], len(nivel["imagem"]), self.atlas.versao_nevoa.get(nivel["id"], 0),
                  self.atlas.nevoa_ligada(nivel))
        vistas = conexao.__dict__.setdefault("atlas_versoes", {})
        if vistas.get(nivel["id"]) == versao:
            return   # nada mudou nesse mapa desde o último envio
        vistas[nivel["id"]] = versao
        enviados = conexao.__dict__.setdefault("atlas_pedacos", {})
        img = self.atlas.imagem(nivel)
        cor = _array(img, 4)
        alfa = self._alfa(nivel)
        w, h = img.width(), img.height()
        for y0 in range(0, h, PEDACO):
            for x0 in range(0, w, PEDACO):
                x1, y1 = min(w, x0 + PEDACO), min(h, y0 + PEDACO)
                chave = (nivel["id"], x0, y0)
                if alfa is None:
                    marca = "aberto:" + str(len(nivel["imagem"]))
                    a = None
                else:
                    a = alfa[y0:y1, x0:x1]
                    marca = "vazio" if not a.any() else hashlib.sha1(a.tobytes()).hexdigest()
                marca += ":" + str(len(nivel["imagem"]))
                if enviados.get(chave) == marca or (chave not in enviados and marca.startswith("vazio")):
                    continue
                enviados[chave] = marca
                dados = ""
                if not marca.startswith("vazio"):
                    pedaco = cor[y0:y1, x0:x1].copy()
                    if a is not None:   # pré-multiplica: a parte coberta vira transparente E preta
                        f = a.astype(np.float32) / 255.0
                        for i in range(3):
                            pedaco[..., i] = (pedaco[..., i] * f).astype(np.uint8)
                        pedaco[..., 3] = (pedaco[..., 3] * f).astype(np.uint8)
                    q = QImage(pedaco.tobytes(), x1 - x0, y1 - y0, (x1 - x0) * 4,
                               QImage.Format.Format_ARGB32_Premultiplied)
                    buf = QBuffer()
                    buf.open(QIODevice.OpenModeFlag.WriteOnly)
                    q.save(buf, "PNG")
                    dados = b64(bytes(buf.data()))
                conexao.socket.sendTextMessage(codificar({"tipo": "atlas_pedaco", "nivel": nivel["id"],
                                                          "x": x0, "y": y0, "dados": dados}))
