"""
🌍 Mapa em 3 níveis: Mesa → Cidade → Mundo (v0.62, item 9 dos PEDIDOS_v0.58 — etapa 1: montagem e navegação).

O mestre importa uma IMAGEM pronta pra cada cidade e pro mundo, e marca com retângulos:
  - no mapa da CIDADE, onde fica cada aba ("lugar": taverna, castelo, esgoto…). As abas de um prédio (andares)
    são um lugar só (alvo = "predio:<id>");
  - no MUNDO, onde fica cada cidade (alvo = id da cidade).
Escala própria por nível (cidade em metros, mundo em km): o mestre traça uma linha e diz a distância.

Navegação: o retângulo do lugar é ENCAIXADO no chão da aba (o cenário inteiro), e o da cidade no mapa da
cidade inteiro. Assim o zoom out é contínuo: o cenário encolhe e a cidade aparece em volta. As contas ficam aqui
(transformações), o desenho e o zoom em `ui/atlas_visao.py`.

Formato (vai no .taverna em "atlas" e no pacote do item 8):
  {"mundo": nivel | None, "cidades": [nivel, ...]}
  nivel = {"classe": "nivel", "id", "tipo": "cidade"|"mundo", "nome", "imagem": base64, "escala": unidade/px | None,
           "lugares": [{"id", "nome", "alvo", "x", "y", "w", "h"}]}   (x, y, w, h em pixels da imagem)
"""

import base64
import math
import uuid

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPixmap, QTransform

UNIDADE = {"cidade": "m", "mundo": "km"}
TROCA = 1 / 3          # o nível de cima termina de aparecer quando o de baixo ocupa 1/3 da tela
COMECA = 0.5           # …e começa quando ele ocupa metade (o "enquadrar tudo" da mesa deixa a sala em ~57% da
                       # tela por causa da folga do 3D: começando em "cabe na tela", a cidade já aparecia no uso normal)
FOLGA = 1.12           # histerese: pra voltar precisa passar um pouco do ponto (sem pisca-pisca)


def novo_nivel(tipo: str, nome: str, imagem: bytes) -> dict:
    if tipo not in UNIDADE:
        raise ValueError(tipo)
    pm = QPixmap()
    if not pm.loadFromData(imagem):
        raise ValueError("Não consegui ler essa imagem.")
    return {"classe": "nivel", "id": uuid.uuid4().hex[:12], "tipo": tipo, "nome": nome or tipo.title(),
            "imagem": base64.b64encode(imagem).decode("ascii"), "escala": None, "lugares": []}


def chave_da_cena(cena) -> str:
    """O que um lugar da cidade aponta: o prédio inteiro (andares) ou a aba sozinha."""
    predio = getattr(cena, "predio", None)
    return f"predio:{predio}" if predio else str(getattr(cena, "uid", ""))


def ret(lugar: dict) -> QRectF:
    return QRectF(float(lugar["x"]), float(lugar["y"]), float(lugar["w"]), float(lugar["h"]))


def encaixe(fora: QRectF, dentro: QRectF) -> QTransform:
    """Transformação que leva as coordenadas do nível de CIMA pras do nível de BAIXO, fazendo o retângulo
    `fora` (no nível de cima) coincidir com `dentro` (o tamanho todo do nível de baixo). Escala única (sem
    esticar): a média geométrica das duas direções."""
    if fora.width() <= 0 or fora.height() <= 0 or dentro.width() <= 0 or dentro.height() <= 0:
        return QTransform()
    k = math.sqrt((dentro.width() * dentro.height()) / (fora.width() * fora.height()))
    t = QTransform()
    t.translate(dentro.center().x(), dentro.center().y())
    t.scale(k, k)
    t.translate(-fora.center().x(), -fora.center().y())
    return t


def tamanho_na_tela(r: QRectF, para_tela: QTransform, w: float, h: float) -> float:
    """Quanto da tela o retângulo ocupa (1 = cabe exato; 1/3 = um terço)."""
    t = para_tela.mapRect(r)
    return max(t.width() / max(1.0, w), t.height() / max(1.0, h))


def mistura(fracao: float) -> float:
    """0 = só o nível de baixo; 1 = só o de cima. Entre 'metade da tela' (COMECA) e 'um terço' (TROCA)."""
    if fracao >= COMECA:
        return 0.0
    if fracao <= TROCA:
        return 1.0
    x = (COMECA - fracao) / (COMECA - TROCA)
    return x * x * (3 - 2 * x)


class Atlas:
    def __init__(self, dados: dict | None = None):
        self.mundo: dict | None = None
        self.cidades: list[dict] = []
        # (etapa 2) VIAGEM: onde o mestre arrastou cada marcador, por mapa: {nivel_id: {marcador: {"x","y","base"}}}
        # ("base" = de onde os tokens estavam quando ele arrastou; se o grupo mudar de aba, volta pro automático)
        self.viagem: dict = {}
        # RASTRO: por onde os marcadores passaram, por mapa: {nivel_id: [[x, y], ...]} (a névoa usa — etapa 3)
        self.rastros: dict = {}
        self._pixmaps: dict = {}
        self._imagens: dict = {}
        # (etapa 3) NÉVOA: uma máscara por mapa (0 = coberto, 255 = revelado), em resolução menor que a imagem
        self._mascaras: dict = {}
        self._mascara_suja: set = set()
        self.versao_nevoa: dict = {}
        if dados:
            self.mundo = dados.get("mundo") or None
            self.cidades = [c for c in (dados.get("cidades") or []) if isinstance(c, dict) and c.get("imagem")]
            if self.mundo is not None and not self.mundo.get("imagem"):
                self.mundo = None
            self.viagem = {k: dict(v) for k, v in (dados.get("viagem") or {}).items() if isinstance(v, dict)}
            self.rastros = {k: [list(p) for p in v] for k, v in (dados.get("rastros") or {}).items()
                            if isinstance(v, list)}

    def para_dict(self) -> dict:
        for n in self.niveis():   # a névoa pintada vai pro arquivo (PNG cinza pequeno)
            if n["id"] in self._mascara_suja and n["id"] in self._mascaras:
                from PyQt6.QtCore import QBuffer, QIODevice
                buf = QBuffer()
                buf.open(QIODevice.OpenModeFlag.WriteOnly)
                self._mascaras[n["id"]].save(buf, "PNG")
                n.setdefault("nevoa", {})["mascara"] = base64.b64encode(bytes(buf.data())).decode("ascii")
        self._mascara_suja.clear()
        return {"mundo": self.mundo, "cidades": list(self.cidades), "viagem": self.viagem, "rastros": self.rastros}

    # ------------------------------------------------------------ névoa (etapa 3)
    NEVOA_MAX = 1024   # lado maior da máscara (a imagem pode ser bem maior; a borda da névoa é macia mesmo)

    @staticmethod
    def nevoa_ligada(nivel: dict) -> bool:
        return bool((nivel.get("nevoa") or {}).get("ligada", True))

    def ligar_nevoa(self, nivel: dict, ligada: bool):
        nivel.setdefault("nevoa", {})["ligada"] = bool(ligada)
        self._mexeu_na_nevoa(nivel)

    def mascara(self, nivel: dict):
        """QImage em tons de cinza (0 = coberto, 255 = revelado)."""
        from PyQt6.QtGui import QImage
        m = self._mascaras.get(nivel["id"])
        if m is None:
            a = self.area(nivel)
            k = min(1.0, self.NEVOA_MAX / max(1.0, a.width(), a.height()))
            tam = (max(1, math.ceil(a.width() * k)), max(1, math.ceil(a.height() * k)))
            m = QImage()
            dados = (nivel.get("nevoa") or {}).get("mascara")
            if dados:
                try:
                    m.loadFromData(base64.b64decode(dados))
                except (ValueError, TypeError):
                    m = QImage()
            if m.isNull() or (m.width(), m.height()) != tam:
                m = QImage(tam[0], tam[1], QImage.Format.Format_Grayscale8)
                m.fill(0)
            else:
                m = m.convertToFormat(QImage.Format.Format_Grayscale8)
            self._mascaras[nivel["id"]] = m
        return m

    def fator_mascara(self, nivel: dict) -> float:
        """pixels da máscara por pixel da imagem."""
        return self.mascara(nivel).width() / max(1.0, self.area(nivel).width())

    def raio_revela(self, nivel: dict) -> float:
        """Quanto o grupo revela em volta de onde passa (pixels da imagem)."""
        r = (nivel.get("nevoa") or {}).get("raio")
        if r:
            return float(r)
        a = self.area(nivel)
        return 0.06 * max(a.width(), a.height())

    def definir_raio(self, nivel: dict, raio_px: float):
        nivel.setdefault("nevoa", {})["raio"] = max(1.0, float(raio_px))

    def pintar_nevoa(self, nivel: dict, p: QPointF, raio: float, revelar: bool = True):
        """Revela (ou cobre) um círculo de borda macia em volta de p (pixels da imagem)."""
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QColor, QPainter, QRadialGradient
        m = self.mascara(nivel)
        k = self.fator_mascara(nivel)
        c, r = QPointF(p.x() * k, p.y() * k), max(1.0, raio * k)
        g = QRadialGradient(c, r)
        v = 255 if revelar else 0
        g.setColorAt(0, QColor(v, v, v, 255))
        g.setColorAt(0.7, QColor(v, v, v, 255))
        g.setColorAt(1, QColor(v, v, v, 0))
        pin = QPainter(m)
        pin.setRenderHint(QPainter.RenderHint.Antialiasing)
        pin.setPen(Qt.PenStyle.NoPen)
        pin.setBrush(g)
        pin.drawEllipse(c, r, r)
        pin.end()
        self._mexeu_na_nevoa(nivel)

    def revelar_tudo(self, nivel: dict, revelar: bool = True):
        self.mascara(nivel).fill(255 if revelar else 0)
        self._mexeu_na_nevoa(nivel)

    def revelado(self, nivel: dict, p: QPointF) -> int:
        """0 (coberto) … 255 (revelado) no ponto p da imagem. Névoa desligada: tudo revelado."""
        if not self.nevoa_ligada(nivel):
            return 255
        m = self.mascara(nivel)
        k = self.fator_mascara(nivel)
        x, y = int(p.x() * k), int(p.y() * k)
        if not (0 <= x < m.width() and 0 <= y < m.height()):
            return 0
        return m.pixelColor(x, y).red()

    def _mexeu_na_nevoa(self, nivel: dict):
        self._mascara_suja.add(nivel["id"])
        self.versao_nevoa[nivel["id"]] = self.versao_nevoa.get(nivel["id"], 0) + 1

    def imagem(self, nivel: dict):
        """A imagem do mapa como QImage (pra cortar os pedaços que vão pros jogadores)."""
        chave = (nivel["id"], len(nivel["imagem"]))
        img = self._imagens.get(chave)
        if img is None:
            from PyQt6.QtGui import QImage
            img = self.pixmap(nivel).toImage().convertToFormat(QImage.Format.Format_ARGB32)
            self._imagens[chave] = img
        return img

    # ------------------------------------------------------------ viagem (etapa 2)
    def posicao_viagem(self, nivel_id: str, marcador: str, base: str):
        """Onde o mestre deixou esse marcador neste mapa (se os tokens ainda estão onde estavam), senão None."""
        v = (self.viagem.get(nivel_id) or {}).get(marcador)
        if v and v.get("base") == base:
            return QPointF(float(v["x"]), float(v["y"]))
        return None

    def mover_marcador(self, nivel_id: str, marcador: str, base: str, p: QPointF):
        self.viagem.setdefault(nivel_id, {})[marcador] = {"x": round(p.x(), 1), "y": round(p.y(), 1), "base": base}
        rastro = self.rastros.setdefault(nivel_id, [])
        if not rastro or math.hypot(rastro[-1][0] - p.x(), rastro[-1][1] - p.y()) > 2:
            rastro.append([round(p.x(), 1), round(p.y(), 1)])

    def voltar_pro_automatico(self, nivel_id: str, marcador: str):
        (self.viagem.get(nivel_id) or {}).pop(marcador, None)

    def vazio(self) -> bool:
        return self.mundo is None and not self.cidades

    def niveis(self) -> list[dict]:
        return ([self.mundo] if self.mundo else []) + list(self.cidades)

    def nivel(self, ident: str) -> dict | None:
        return next((n for n in self.niveis() if n["id"] == ident), None)

    # ------------------------------------------------------------ imagem
    def pixmap(self, nivel: dict) -> QPixmap:
        chave = (nivel["id"], len(nivel["imagem"]))
        pm = self._pixmaps.get(chave)
        if pm is None:
            pm = QPixmap()
            pm.loadFromData(base64.b64decode(nivel["imagem"]))
            self._pixmaps[chave] = pm
        return pm

    def area(self, nivel: dict) -> QRectF:
        pm = self.pixmap(nivel)
        return QRectF(0, 0, pm.width(), pm.height())

    # ------------------------------------------------------------ lugares
    def ligar(self, nivel: dict, r: QRectF, alvo: str, nome: str = "") -> dict:
        """Marca um lugar. Um alvo só pode estar num lugar: se já estava em outro (até em outra cidade), muda."""
        for n in self.niveis():
            if n["tipo"] == nivel["tipo"]:
                n["lugares"] = [l for l in n["lugares"] if l["alvo"] != alvo]
        r = r.normalized()
        lugar = {"id": uuid.uuid4().hex[:12], "nome": nome, "alvo": alvo,
                 "x": round(r.x(), 1), "y": round(r.y(), 1), "w": round(r.width(), 1), "h": round(r.height(), 1)}
        nivel["lugares"].append(lugar)
        return lugar

    def remover_lugar(self, nivel: dict, lugar_id: str):
        nivel["lugares"] = [l for l in nivel["lugares"] if l["id"] != lugar_id]

    def remover_nivel(self, ident: str):
        if self.mundo and self.mundo["id"] == ident:
            self.mundo = None
            return
        self.cidades = [c for c in self.cidades if c["id"] != ident]
        self.viagem.pop(ident, None)
        self.rastros.pop(ident, None)
        if self.mundo:
            self.mundo["lugares"] = [l for l in self.mundo["lugares"] if l["alvo"] != ident]

    def lugar_da_cena(self, cena):
        """(cidade, lugar) onde a aba está marcada, ou (None, None)."""
        chave = chave_da_cena(cena)
        for c in self.cidades:
            for l in c["lugares"]:
                if l["alvo"] == chave:
                    return c, l
        return None, None

    def lugar_da_cidade(self, cidade: dict):
        if not self.mundo:
            return None
        return next((l for l in self.mundo["lugares"] if l["alvo"] == cidade["id"]), None)

    # ------------------------------------------------------------ escala (régua)
    @staticmethod
    def calibrar(nivel: dict, comprimento_px: float, distancia: float):
        """O mestre traçou uma linha de `comprimento_px` e disse que ela mede `distancia` (m na cidade, km no
        mundo)."""
        if comprimento_px > 0 and distancia > 0:
            nivel["escala"] = float(distancia) / float(comprimento_px)

    @staticmethod
    def distancia(nivel: dict, comprimento_px: float) -> float | None:
        e = nivel.get("escala")
        return comprimento_px * e if e else None

    @staticmethod
    def texto_distancia(nivel: dict, comprimento_px: float) -> str:
        """"350 m", "12,5 km"… — ou o aviso de que falta calibrar a escala."""
        d = Atlas.distancia(nivel, comprimento_px)
        if d is None:
            return "sem escala (calibre na montagem)"
        un = UNIDADE.get(nivel.get("tipo"), "m")
        if un == "m" and d >= 1000:
            d, un = d / 1000, "km"
        casas = 0 if d >= 100 else (1 if d >= 10 else 2)
        texto = f"{d:.{casas}f}".rstrip("0").rstrip(".") if casas else f"{d:.0f}"
        return texto.replace(".", ",") + " " + un

    # ------------------------------------------------------------ encaixes
    def cidade_para_mesa(self, cena, chao: QRectF | None):
        """Transformação pixels da cidade → coordenadas da mesa da aba (ou None se a aba não está numa cidade)."""
        cidade, lugar = self.lugar_da_cena(cena)
        if cidade is None or chao is None or chao.isEmpty():
            return None, None
        return cidade, encaixe(ret(lugar), chao)

    def mundo_para_cidade(self, cidade: dict) -> QTransform | None:
        lugar = self.lugar_da_cidade(cidade)
        if lugar is None:
            return None
        return encaixe(ret(lugar), self.area(cidade))
