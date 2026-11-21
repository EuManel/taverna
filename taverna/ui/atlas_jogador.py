"""
🌍 Cidade e mundo no JOGADOR (v0.64 — item 9, etapa 3).

O jogador não recebe o atlas do mestre: recebe (rede/atlas_rede.py) só a cidade da aba dele, o mundo (se a cidade
estiver nele), o lugar dele, o chão da aba e os marcadores revelados — e a imagem em pedaços já sem a parte coberta
pela névoa. Aqui a gente junta os pedaços numa tela e entrega pra mesma camada do mestre (ui/atlas_visao.py) em
modo "só olhar" (não arrasta marcador, não pinta névoa, não troca de aba).
"""

import base64

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap

from ..mesa.atlas import Atlas


class AtlasJogador(Atlas):
    def __init__(self):
        super().__init__()
        self.chao: QRectF | None = None
        self._telas: dict = {}      # nivel id -> QImage (os pedaços revelados juntados)
        self._versao: dict = {}
        self._marcadores = {"cidade": [], "mundo": []}

    # ------------------------------------------------------------ o que chega do mestre
    def receber(self, msg: dict):
        c = msg.get("chao")
        self.chao = QRectF(*c) if c else None
        cid, mun = msg.get("cidade"), msg.get("mundo")
        self.cidades = []
        self.mundo = None
        if cid:
            self.cidades = [{"classe": "nivel", "id": cid["id"], "tipo": "cidade", "nome": cid.get("nome", ""),
                             "escala": cid.get("escala"), "imagem": "", "_w": cid["w"], "_h": cid["h"],
                             "lugares": [dict(cid["lugar"], id="minha", alvo="__minha__", nome="")]}]
        if mun and cid:
            self.mundo = {"classe": "nivel", "id": mun["id"], "tipo": "mundo", "nome": mun.get("nome", ""),
                          "escala": mun.get("escala"), "imagem": "", "_w": mun["w"], "_h": mun["h"],
                          "lugares": [dict(mun["lugar_cidade"], id="cidade", alvo=cid["id"], nome="")]}
        vivos = {n["id"] for n in self.niveis()}
        for ident in list(self._telas):
            if ident not in vivos:
                del self._telas[ident]
        self._marcadores = {q: [{"id": m["id"], "pos": QPointF(m["x"], m["y"]), "auto": QPointF(m["x"], m["y"]),
                                 "cor": QColor(m.get("cor", "#e8c25a")), "nome": m.get("nome", ""), "base": ""}
                                for m in (msg.get("marcadores") or {}).get(q, [])]
                            for q in ("cidade", "mundo")}

    def pedaco(self, msg: dict):
        nivel = self.nivel(msg.get("nivel", ""))
        if nivel is None:
            return
        tela = self._tela(nivel)
        x, y = int(msg.get("x", 0)), int(msg.get("y", 0))
        p = QPainter(tela)
        if msg.get("dados"):
            img = QImage()
            img.loadFromData(base64.b64decode(msg["dados"]))
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            p.drawImage(x, y, img)
        else:   # voltou a ficar coberto
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            p.fillRect(x, y, 256, 256, QColor(0, 0, 0, 0))
        p.end()
        self._versao[nivel["id"]] = self._versao.get(nivel["id"], 0) + 1

    def _tela(self, nivel) -> QImage:
        t = self._telas.get(nivel["id"])
        w, h = int(nivel["_w"]), int(nivel["_h"])
        if t is None or (t.width(), t.height()) != (w, h):
            t = QImage(max(1, w), max(1, h), QImage.Format.Format_ARGB32_Premultiplied)
            t.fill(0)
            self._telas[nivel["id"]] = t
        return t

    # ------------------------------------------------------------ o que a camada pergunta
    def vazio(self) -> bool:
        return not self.cidades

    def pixmap(self, nivel) -> QPixmap:
        chave = (nivel["id"], self._versao.get(nivel["id"], 0))
        pm = self._pixmaps.get(nivel["id"])
        if pm is None or pm[0] != chave:
            pm = (chave, QPixmap.fromImage(self._tela(nivel)))
            self._pixmaps[nivel["id"]] = pm
        return pm[1]

    def area(self, nivel) -> QRectF:
        return QRectF(0, 0, float(nivel["_w"]), float(nivel["_h"]))

    def lugar_da_cena(self, cena):
        if not self.cidades:
            return None, None
        c = self.cidades[0]
        return c, c["lugares"][0]

    def cidade_para_mesa(self, cena, chao):
        return super().cidade_para_mesa(cena, self.chao)

    @staticmethod
    def nevoa_ligada(nivel) -> bool:
        return False   # (a imagem já chega sem a parte coberta: não tem névoa pra desenhar por cima)

    def marcadores_de(self, quadro: str) -> list:
        return list(self._marcadores.get(quadro, []))


class _Ponte:
    """O que a camada do atlas espera de "janela", pro lado do jogador."""

    def __init__(self, janela):
        self._janela = janela
        self.atlas = AtlasJogador()

    @property
    def cena(self):
        return self._janela.cena

    @property
    def cenas(self):
        return [self._janela.cena]

    def trocar_aba(self, *_a, **_k):
        pass

    def atlas_editado(self):
        pass

    def abrir_atlas(self):
        pass


def ligar(janela):
    """Põe a camada da cidade/mundo na mesa do jogador. Devolve a ponte (com .atlas e .camada)."""
    from .atlas_visao import CamadaAtlas
    ponte = _Ponte(janela)
    ponte.camada = CamadaAtlas(janela.visao, ponte, mestre=False)
    return ponte


def mensagem(ponte, msg: dict) -> bool:
    """Trata "atlas"/"atlas_pedaco". Devolve True se era dela."""
    tipo = msg.get("tipo")
    if tipo == "atlas":
        ponte.atlas.receber(msg)
        ponte.camada.atlas_mudou()
        ponte.camada.update()
        return True
    if tipo == "atlas_pedaco":
        ponte.atlas.pedaco(msg)
        ponte.camada.update()
        return True
    return False
