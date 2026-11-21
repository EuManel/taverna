"""
🍺 Launcher do Taverna (v0.49, pedido do Manel): UM programa só pra mestre e jogador.

A tela inicial é feita em Qt Quick (QML: `ui/qml/Lancador.qml`), com o cenário animado de cada tema por
trás e dois painéis: MESTRE (nova sessão, continuar, abrir) e JOGADOR (entrar na sessão). O detalhe da
interface segue o nível de Gráficos: Baixo = simples · Médio = equilibrado · Alto = exagerado.

Quem escolhe, abre a janela de sempre (JanelaMestre / JanelaPlayer). Quando a pessoa sai da mesa, volta pra
cá (as janelas chamam `voltar`).
"""

import os

from PyQt6.QtCore import QObject, QSettings, QSize, Qt, QTimer, QUrl, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtQuick import QQuickImageProvider, QQuickPaintedItem
from PyQt6.QtWidgets import QApplication, QMainWindow

from ..config import APP_NOME, APP_VERSAO
from ..graficos import NIVEIS, graficos, nivel
from ..temas import TEMAS, TEMA_PADRAO, tema as dados_tema

PASTA_QML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qml")


# ====================================================================== imagens pro QML
_PASTA_CACHE = None


def _arquivo_cache(ident):
    """Arquivo onde fica guardada a imagem `ident`. A "assinatura" (versão + data dos arquivos de desenho) muda
    quando um desenho muda, aí tudo é refeito sozinho."""
    global _PASTA_CACHE
    # (v0.58) sem tela (os testes): as fontes do Windows não aparecem e o desenho sai com a fonte errada —
    # NÃO pode ir pro cache, senão o programa de verdade reaproveita o desenho errado
    if os.environ.get("QT_QPA_PLATFORM", "") in ("offscreen", "minimal"):
        return ""
    try:
        if _PASTA_CACHE is None:
            import hashlib
            from PyQt6.QtCore import QStandardPaths
            base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation) or ""
            aqui = os.path.dirname(os.path.abspath(__file__))
            marcas = [APP_VERSAO] + [str(int(os.path.getmtime(os.path.join(aqui, n)))) for n in
                                     ("estilizado.py", "terror_cenas.py", "medieval_cenas.py", "relevo_ui.py",
                                      "materiais_ui.py") if os.path.isfile(os.path.join(aqui, n))]
            assinatura = hashlib.sha1("|".join(marcas).encode()).hexdigest()[:10]
            _PASTA_CACHE = os.path.join(base, "imagens", assinatura) if base else ""
            if _PASTA_CACHE:
                os.makedirs(_PASTA_CACHE, exist_ok=True)
                pai = os.path.dirname(_PASTA_CACHE)        # apaga as pastas de versões velhas
                for velha in os.listdir(pai):
                    if velha != assinatura:
                        import shutil
                        shutil.rmtree(os.path.join(pai, velha), ignore_errors=True)
        if not _PASTA_CACHE:
            return ""
        import hashlib
        from ..idioma import atual
        return os.path.join(_PASTA_CACHE, hashlib.sha1((ident + "|" + atual()).encode()).hexdigest() + ".png")
    except Exception:
        return ""


def bandeira(codigo, dpr=1.0):
    """(v1.0) Bandeirinha desenhada (sem imagem de fora): pt = Brasil, en = Estados Unidos. 30×20 (× dpr)."""
    from PyQt6.QtCore import QPointF, QRectF
    from PyQt6.QtGui import QBrush, QColor, QPainterPath, QPen, QPolygonF
    w, h = 30.0, 20.0
    img = QImage(max(1, round(w * dpr)), max(1, round(h * dpr)), QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(0)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(dpr, dpr)
    borda = QPainterPath()
    borda.addRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 2.5, 2.5)
    p.setClipPath(borda)
    if codigo == "en":
        for i in range(13):
            p.fillRect(QRectF(0, i * h / 13, w, h / 13 + 0.05), QColor("#b22234" if i % 2 == 0 else "#ffffff"))
        p.fillRect(QRectF(0, 0, w * 0.42, h * 7 / 13), QColor("#3c3b6e"))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#ffffff"))
        for lin in range(4):
            for col in range(5 if lin % 2 == 0 else 4):
                x = 1.6 + col * 2.4 + (1.2 if lin % 2 else 0)
                p.drawEllipse(QPointF(x, 1.5 + lin * 2.3), 0.45, 0.45)
    else:
        p.fillRect(QRectF(0, 0, w, h), QColor("#009c3b"))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#ffdf00"))
        p.drawPolygon(QPolygonF([QPointF(w / 2, 2.2), QPointF(w - 2.6, h / 2), QPointF(w / 2, h - 2.2),
                                 QPointF(2.6, h / 2)]))
        p.setBrush(QColor("#002776"))
        p.drawEllipse(QPointF(w / 2, h / 2), 4.6, 4.6)
        p.setPen(QPen(QColor("#ffffff"), 0.9))
        p.setBrush(QBrush())
        p.drawArc(QRectF(w / 2 - 6.2, h / 2 - 2.2, 12.4, 9.0), 35 * 16, 110 * 16)
    p.setClipping(False)
    p.setPen(QPen(QColor(0, 0, 0, 110), 1.0))
    p.setBrush(QBrush())
    p.drawPath(borda)
    p.end()
    return img


class ProvedorTaverna(QQuickImageProvider):
    """image://taverna/tex/<tema> · image://taverna/canto/<tema>"""

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)

    # (v0.56, otimização) desenhos caros ficam guardados em arquivo: a tela abre bem mais rápido da 2ª vez
    _GUARDAR = ("ornado", "logo", "suporte", "peca", "tex", "canto", "terror", "farol", "tv", "quadro")

    def requestImage(self, ident, tamanho):
        tipo = (ident or "").split("/")[0]
        if tipo not in self._GUARDAR:
            return self._gerar(ident, tamanho)
        caminho = _arquivo_cache(ident)
        if caminho and os.path.isfile(caminho):
            img = QImage(caminho)
            if not img.isNull():
                return img, img.size()
        img, tam = self._gerar(ident, tamanho)
        if caminho and img.width() > 1:
            try:
                img.save(caminho)
            except Exception:
                pass
        return img, tam

    def _gerar(self, ident, tamanho):
        """tex/<tema> · canto/<tema> · peca/<tema>/<placa|botao|principal>/<w>/<h>/<estado>/<nivel>/<raio>/<dpr>"""
        from .materiais_ui import cantoneira, textura
        partes = (ident or "").split("/")
        tipo, tema = (partes + ["", ""])[:2]
        if tipo not in ("sprite", "suporte", "vinheta", "grao", "terror", "varredura", "mesa3d", "tv", "farol", "led"):
            tema = tema if tema in TEMAS else TEMA_PADRAO
        try:
            from . import estilizado as E
            if tipo == "led":        # (v0.58) led/grade: a grade de pixels do outdoor (Moderno)
                from .moderno_cenas import grade_led
                img = grade_led()
                return img, img.size()
            if tipo in ("tv", "farol"):  # (v0.55) cenas do Terror: tv/<chiado|rosto|teia|hera>, farol/<peça>/...
                from .terror_cenas import imagem
                img = imagem(partes)
                return img, img.size()
            if tipo == "ornado":       # ornado/<tema>/<w>/<h>/<estado>/<nivel>/<dpr>[/<texto>]
                from urllib.parse import unquote
                w, h, estado, niv, dpr = partes[2:7]
                texto = unquote(partes[7]) if len(partes) > 7 else ""
                img = E.botao_tema(tema, int(float(w)), int(float(h)), estado, float(dpr), int(niv), texto)
                return img, img.size()
            if tipo == "grao":
                img = E.grao(256)
                return img, img.size()
            if tipo == "bandeira":     # bandeira/<pt|en>/<dpr>: a bandeirinha do seletor de idioma
                img = bandeira(partes[1], float(partes[2]) if len(partes) > 2 else 1.0)
                return img, img.size()
            if tipo == "mesa3d":       # mesa3d/<tampo|tampo_normal|caneca|d20|ambiente>
                img = E.textura_3d(partes[1])
                return img, img.size()
            if tipo == "varredura":
                img = E.varredura()
                return img, img.size()
            if tipo == "terror":       # terror/<ceu|lua|arvore|nevoa|morros>/...
                peca = partes[1]
                if peca == "ceu":       # ceu/<w>/<h>/<x da lua>/<y da lua>/<vermelha>
                    img = E.ceu_terror(int(float(partes[2])), int(float(partes[3])),
                                       (float(partes[4]), float(partes[5])), partes[6] == "1")
                elif peca == "lua":     # lua/<fase>/<vermelha>
                    img = E.lua(320, float(partes[2]), partes[3] == "1")
                elif peca == "arvore":
                    img = E.arvore_morta(int(partes[2]), float(partes[3]))
                elif peca == "nevoa":
                    img = E.faixa_nevoa(int(partes[2]))
                else:
                    img = E.morros_terror(int(float(partes[2])), int(float(partes[3])))
                return img, img.size()
            if tipo == "logo":         # logo/<tema>/<nivel>/<dpr>
                niv, dpr = partes[2:4]
                familia = dados_tema(tema)["fonte_titulo"].split(",")[0].strip().strip("'\"")
                img = E.logo_tema(tema, familia, float(dpr), int(niv))
                return img, img.size()
            if tipo == "suporte":      # suporte/<dpr>
                img = E.suporte_tocha(float(partes[1]))
                return img, img.size()
            if tipo == "sprite":       # sprite/<chama|faisca|fumaca>
                img = E.sprite_fogo(64, partes[1])
                return img, img.size()
            if tipo == "vinheta":      # vinheta/<w>/<h>
                img = E.vinheta(max(8, int(float(partes[1]) / 4)), max(8, int(float(partes[2]) / 4)))
                return img, img.size()
            if tipo == "peca":
                from .relevo_ui import esculpir
                peca, w, h, estado, niv, raio, dpr = partes[2:9]
                img = esculpir(tema, peca, int(float(w)), int(float(h)), estado, int(niv), float(raio), float(dpr))
            elif tipo == "tex":
                img = textura(tema)
            elif tipo == "canto":
                img = cantoneira(tema, 128)
            else:
                img = QImage(1, 1, QImage.Format.Format_ARGB32)
        except Exception as erro:   # (imagem com problema não pode derrubar a tela)
            from ..seguranca import registrar_erro
            registrar_erro(f"Imagem da interface '{ident}': {erro!r}")
            img = QImage(1, 1, QImage.Format.Format_ARGB32)
            img.fill(0)
        return img, img.size()


# ====================================================================== o cenário animado (o mesmo da tela antiga)
class FundoTema(QQuickPaintedItem):
    temaMudou = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        import random
        self._tema = TEMA_PADRAO
        self._fundo = None
        self._t = 0.0
        self._rnd = random.Random()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._passo)
        graficos().mudou.connect(lambda _c: self._ligar())
        self._ligar()

    def _get_tema(self):
        return self._tema

    def _set_tema(self, v):
        if v != self._tema:
            self._tema = v if v in TEMAS else TEMA_PADRAO
            self._fundo = None
            self.temaMudou.emit()
            self._ligar()

    tema = pyqtProperty(str, _get_tema, _set_tema, notify=temaMudou)

    # (v0.56, otimização) quando uma cena 3D cobre a tela inteira, não pinta nada caro por baixo dela
    cobertoMudou = pyqtSignal()

    def _get_coberto(self):
        return getattr(self, "_coberto", False)

    def _set_coberto(self, v):
        if bool(v) != self._get_coberto():
            self._coberto = bool(v)
            self.cobertoMudou.emit()
            self.update()

    coberto = pyqtProperty(bool, _get_coberto, _set_coberto, notify=cobertoMudou)

    def _paint_parede(self, p, w, h):
        """Desenha o muro no tamanho certo; se a janela mudou, estica o velho e refaz depois (sem travar)."""
        from PyQt6.QtCore import QRectF
        from .estilizado import mesa_taverna
        pronto = getattr(self, "_parede", None)
        if pronto is None or (pronto.width(), pronto.height()) != (w, h):
            if pronto is None:
                pronto = self._parede = mesa_taverna(w, h)   # (v0.53) a mesa da taverna
            else:
                if not hasattr(self, "_refazer"):
                    self._refazer = QTimer(self)
                    self._refazer.setSingleShot(True)
                    self._refazer.timeout.connect(self._refazer_parede)
                self._refazer.start(350)
        p.drawImage(QRectF(0, 0, w, h), pronto)

    def _refazer_parede(self):
        from .estilizado import mesa_taverna
        self._parede = mesa_taverna(max(1, int(self.width())), max(1, int(self.height())))
        self.update()

    def _ligar(self):
        n = nivel()
        from .estilizado import NEUTROS
        if self._tema in ("medieval", "terror") or self._tema in NEUTROS:   # parado (o movimento é do QML)
            self._timer.stop()
            self.update()
            return
        if n == 0:
            self._timer.stop()
        else:
            self._timer.start(70 if n == 1 else 33)
        self.update()

    def _passo(self):
        if not self.isVisible():
            return
        self._t += self._timer.interval() / 1000
        self.update()

    def paint(self, p: QPainter):
        try:
            from .tela_inicial import ANIMACOES, _anim_medieval, desenhar_fundo
            w, h = max(1, int(self.width())), max(1, int(self.height()))
            from .estilizado import NEUTROS
            if self._get_coberto():
                from PyQt6.QtGui import QColor
                p.fillRect(0, 0, w, h, QColor("#0b0907"))
                return
            if self._tema == "terror":   # (v0.52.1) o cenário do Terror é todo do QML (lua, árvores, névoa)
                from PyQt6.QtGui import QColor
                p.fillRect(0, 0, w, h, QColor("#0b0c10"))
                return
            if self._tema in NEUTROS:   # neutro: fundo liso, como um programa de edição
                from PyQt6.QtGui import QColor
                p.fillRect(0, 0, w, h, QColor("#1e1f22" if self._tema == "escuro" else "#eef0f3"))
                return
            if self._tema == "medieval":
                # (v0.52) muro de pedra 3D iluminado pelas tochas; o fogo/faísca é do QML (placa de vídeo)
                self._paint_parede(p, w, h)
                return
            if self._fundo is None or self._fundo.width() != w or self._fundo.height() != h:
                self._fundo = desenhar_fundo(self._tema, w, h)
            p.drawPixmap(0, 0, self._fundo)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            ANIMACOES.get(self._tema, _anim_medieval)(p, w, h, self._t if nivel() else 2.0, nivel(), self._rnd)
        except Exception as erro:   # (erro dentro de paint() fecha o programa)
            from ..seguranca import registrar_erro
            registrar_erro(f"Fundo da tela inicial: {erro!r}")


# ====================================================================== ponte Python ↔ QML
class Ponte(QObject):
    mudou = pyqtSignal()
    escolhido = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        from .tema import tema_preferido
        self._tema = tema_preferido()
        self._info = ""
        self._ultima = ""
        self._servidor = ""
        self._papel = QSettings("Taverna", "Launcher").value("papel", "", type=str)
        graficos().mudou.connect(lambda _c: self.mudou.emit())

    # ---- propriedades lidas pelo QML
    @pyqtProperty(str, notify=mudou)
    def tema(self):
        return self._tema

    @pyqtProperty(int, notify=mudou)
    def nivel(self):
        return nivel()

    @pyqtProperty(str, notify=mudou)
    def nivelChave(self):
        return graficos().atual

    @pyqtProperty("QVariantMap", notify=mudou)
    def cores(self):
        t = dados_tema(self._tema)
        from .tela_inicial import CORES_TELA
        tit, sub, *_r = CORES_TELA.get(self._tema, CORES_TELA["medieval"])
        fonte = t["fonte_titulo"].split(",")[0].strip().strip("'\"")
        return {"fundo": t["fundo"], "painel": t["painel"], "painel2": t["painel2"], "borda": t["borda"],
                "texto": t["texto"], "fraco": t["fraco"], "destaque": t["destaque"], "destaque2": t["destaque2"],
                "claro": t["claro"], "raio": t["raio"], "fonte": fonte, "titulo": tit, "sub": sub,
                "perigo": t["perigo"]}

    @pyqtProperty("QVariantList", notify=mudou)
    def temas(self):
        from ..idioma import t as tr
        return [{"chave": k, "nome": tr(t["nome"])} for k, t in TEMAS.items()]

    @pyqtProperty("QVariantList", notify=mudou)
    def niveis(self):
        from ..idioma import t as tr
        return [{"chave": k, "nome": tr(n.split(" — ")[0])} for k, n in NIVEIS.items()]

    @pyqtProperty(str, notify=mudou)
    def idioma(self):
        from ..idioma import atual
        return atual()

    @pyqtProperty("QVariantList", constant=True)
    def idiomas(self):
        from ..idioma import IDIOMAS
        return [{"chave": k, "nome": n} for k, n in IDIOMAS]

    @pyqtProperty(str, notify=mudou)
    def info(self):
        return self._info

    @pyqtProperty(str, notify=mudou)
    def ultimaAventura(self):
        return self._ultima

    @pyqtProperty(bool, notify=mudou)
    def temUltima(self):
        return bool(self._ultima)

    @pyqtProperty(str, notify=mudou)
    def servidor(self):
        return self._servidor

    @pyqtProperty(str, notify=mudou)
    def papel(self):
        return self._papel

    @pyqtProperty(str, constant=True)
    def versao(self):
        return APP_VERSAO

    @pyqtProperty("QVariantMap", constant=True)
    def luaTerror(self):
        """(v0.53, ideia do Manel) A lua do Terror muda TODA VEZ que o programa abre: lugar no céu, fase
        (cheia, crescente, minguante, nova…) e, de vez em quando, lua de SANGUE."""
        if not hasattr(self, "_lua"):
            import random
            rnd = random.Random()
            fase = rnd.choice([0.5, 0.5, 0.42, 0.58, 0.3, 0.7, 0.2, 0.8, 0.06])
            lado_x = rnd.uniform(0.09, 0.2) if rnd.random() < 0.5 else rnd.uniform(0.8, 0.91)   # (fora do título)
            self._lua = {"x": round(lado_x, 3), "y": round(rnd.uniform(0.13, 0.32), 3),
                         "fase": fase, "vermelha": rnd.random() < 0.15,
                         "tamanho": round(rnd.uniform(0.2, 0.3), 3)}
        return self._lua

    @pyqtProperty(str, notify=mudou)
    def cenaTerror(self):
        """(v0.55, pedido do Manel) O Terror tem duas telas e sorteia uma cada vez que o programa abre:
        "tv" (sala com a TV velha, menu dentro da tela) ou "farol" (tempestade no mar)."""
        if not hasattr(self, "_cena_terror"):
            import os
            import random
            pedida = os.environ.get("TAVERNA_CENA_TERROR", "")
            self._cena_terror = pedida if pedida in ("tv", "farol") else random.choice(["tv", "farol"])
        return self._cena_terror

    @pyqtProperty(str, notify=mudou)
    def cenaMedieval(self):
        """(v0.56, pedido do Manel) O Medieval sorteia: "mesa" (mesa da taverna com o contrato) ou "quadro"
        (quadro de missões)."""
        if not hasattr(self, "_cena_medieval"):
            import os
            import random
            pedida = os.environ.get("TAVERNA_CENA_MEDIEVAL", "")
            self._cena_medieval = pedida if pedida in ("mesa", "quadro") else random.choice(["mesa", "quadro"])
        return self._cena_medieval

    @pyqtProperty(str, notify=mudou)
    def cenaMagico(self):
        """(v0.57, pedido do Manel) O Mágico sorteia: "circulo" (círculo mágico) ou "torre" (torre de mago)."""
        if not hasattr(self, "_cena_magico"):
            import os
            import random
            pedida = os.environ.get("TAVERNA_CENA_MAGICO", "")
            self._cena_magico = pedida if pedida in ("circulo", "torre") else random.choice(["circulo", "torre"])
        return self._cena_magico

    @pyqtProperty(str, notify=mudou)
    def cenaModerno(self):
        """(v0.58) O Moderno sorteia: "celular" (celular na mesa à noite) ou "terraco" (outdoor de LED)."""
        if not hasattr(self, "_cena_moderno"):
            import os
            import random
            pedida = os.environ.get("TAVERNA_CENA_MODERNO", "")
            self._cena_moderno = pedida if pedida in ("celular", "terraco") else random.choice(["celular", "terraco"])
        return self._cena_moderno

    @pyqtProperty(str, notify=mudou)
    def cenaFuturista(self):
        """(v0.58) O Futurista sorteia: "beco" (beco de neon) ou "nave" (cabine de nave)."""
        if not hasattr(self, "_cena_futurista"):
            import os
            import random
            pedida = os.environ.get("TAVERNA_CENA_FUTURISTA", "")
            self._cena_futurista = pedida if pedida in ("beco", "nave") else random.choice(["beco", "nave"])
        return self._cena_futurista

    @pyqtProperty(str, notify=mudou)
    def cenaSteampunk(self):
        """(v0.59) O Steampunk sorteia: "oficina" (oficina do inventor) ou "dirigivel" (ponte de comando)."""
        if not hasattr(self, "_cena_steampunk"):
            import os
            import random
            pedida = os.environ.get("TAVERNA_CENA_STEAMPUNK", "")
            self._cena_steampunk = pedida if pedida in ("oficina", "dirigivel") else random.choice(["oficina", "dirigivel"])
        return self._cena_steampunk

    @pyqtProperty(str, notify=mudou)
    def cenaPosApocaliptico(self):
        """(v0.59) O Pós-apocalíptico sorteia: "cidade" (cidade tomada pelas plantas) ou "abrigo" (abrigo à noite)."""
        if not hasattr(self, "_cena_posapoc"):
            import os
            import random
            pedida = os.environ.get("TAVERNA_CENA_POSAPOC", "")
            self._cena_posapoc = pedida if pedida in ("cidade", "abrigo") else random.choice(["cidade", "abrigo"])
        return self._cena_posapoc

    @pyqtProperty("QVariantList", constant=True)
    def frasesRadio(self):
        """(v0.59) As frases picotadas do rádio do abrigo (inventadas)."""
        from ..idioma import tl
        from .posapoc_cenas import FRASES_RADIO
        return tl(list(FRASES_RADIO))

    @pyqtProperty("QVariantList", constant=True)
    def letreiros(self):
        """(v0.58) Palavras inventadas dos letreiros do beco (nada de marca de verdade)."""
        from .futurista_cenas import LETREIROS
        return list(LETREIROS)

    @pyqtProperty("QVariantList", constant=True)
    def notificacoes(self):
        """(v0.58) As notificações inventadas do celular do Moderno: [[título, texto], …]."""
        from ..idioma import tl
        from .moderno_cenas import NOTIFICACOES
        return [tl(list(n)) for n in NOTIFICACOES]

    @pyqtProperty(str, constant=True)
    def destaqueMagico(self):
        """(v0.58) Cor de destaque do círculo mágico (só no hover e no título). Dourado ou ciano — o Manel escolhe;
        dá pra forçar com TAVERNA_DESTAQUE=dourado|ciano pra comparar."""
        import os
        cores = {"dourado": "#f2c454", "ciano": "#4ee8f0"}
        return cores.get(os.environ.get("TAVERNA_DESTAQUE", ""), cores["dourado"])

    @pyqtProperty("QVariantMap", constant=True)
    def farolLampada(self):
        """Onde fica a lâmpada do farol na imagem do penhasco (fração), pro brilho e o feixe."""
        from .terror_cenas import farol_lampada
        x, y = farol_lampada()
        return {"x": x, "y": y}

    @pyqtProperty(bool, notify=mudou)
    def textoNaImagem(self):
        """Terror: a letra do botão é desenhada gasta no Python (o QML não mostra o texto dele)."""
        from .estilizado import TEXTO_NA_IMAGEM
        return self._tema in TEXTO_NA_IMAGEM

    @pyqtProperty(bool, notify=mudou)
    def neutro(self):
        """Claro/Escuro: temas NEUTROS, "de programa" (tipo editor de imagem): sem cenário nem enfeite."""
        from .estilizado import NEUTROS
        return self._tema in NEUTROS

    @pyqtProperty("QVariantList", notify=mudou)
    def tochas(self):
        """Tochas com fogo de verdade (partículas) — por enquanto, no Medieval."""
        from .estilizado import VELA
        # (v0.53) Medieval: a vela da mesa da taverna (só a chama; o castiçal está na imagem da mesa)
        return [{"x": VELA[0], "y": VELA[1], "vela": True}] if self._tema == "medieval" else []

    # ---- o QML chama
    @pyqtSlot(str, result="QVariantMap")
    def malha(self, pedido):
        """Forma 3D (pontos, normais, uv, triângulos) pro ProceduralMesh da mesa da taverna."""
        try:
            from .geometria3d import malha
            return malha(pedido)
        except Exception as erro:   # forma com problema: some (não derruba a tela)
            from ..seguranca import registrar_erro
            registrar_erro(f"Forma 3D '{pedido}': {erro!r}")
            return {"pos": [], "nor": [], "uv": [], "idx": []}

    @pyqtSlot(str, result=str)
    def textura(self, nome):
        """URL de arquivo de uma textura da mesa 3D (o Qt Quick 3D não lê do provedor de imagens)."""
        try:
            from .estilizado import caminho_textura_3d
            return QUrl.fromLocalFile(caminho_textura_3d(nome)).toString()
        except Exception as erro:
            from ..seguranca import registrar_erro
            registrar_erro(f"Textura 3D '{nome}': {erro!r}")
            return ""

    @pyqtSlot()
    def plim(self):
        """(v0.59) A campainha "plim-plim" do telégrafo do dirigível (som sintetizado aqui mesmo, sem arquivo de
        fora). Sem caixa de som, ou nos testes, não faz nada."""
        try:
            from .audio import TocadorSons, tem_saida_de_som
            if not tem_saida_de_som():
                return
            import os
            import tempfile
            import wave
            import numpy as np
            caminho = os.path.join(tempfile.gettempdir(), "taverna_plim_v1.wav")
            if not os.path.isfile(caminho):
                taxa = 44100
                t = np.arange(int(taxa * 1.1)) / taxa
                som = np.zeros_like(t)
                for inicio in (0.0, 0.22):                                   # dois toques
                    tt = np.clip(t - inicio, 0, None)
                    env = np.where(t >= inicio, np.exp(-tt * 5.5), 0)
                    som += env * (np.sin(2 * np.pi * 1760 * tt) + 0.5 * np.sin(2 * np.pi * 2637 * tt)
                                  + 0.25 * np.sin(2 * np.pi * 4186 * tt))
                som = (som / np.abs(som).max() * 0.6 * 32767).astype(np.int16)
                with wave.open(caminho, "wb") as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(taxa)
                    w.writeframes(som.tobytes())
            if not hasattr(self, "_tocador"):
                self._tocador = TocadorSons(self)
            self._tocador.registrar_arquivo("plim", caminho)
            self._tocador.tocar("plim", 0.7)
        except Exception as erro:
            from ..seguranca import registrar_erro
            registrar_erro(f"Campainha do telégrafo: {erro!r}")

    @pyqtSlot(str)
    def escolher(self, chave):
        self.escolhido.emit(chave)

    @pyqtSlot(str)
    def definirTema(self, chave):
        if chave in TEMAS and chave != self._tema:
            from .tema import guardar_tema_preferido
            self._tema = chave
            guardar_tema_preferido(chave)
            # (v0.57, o Manel reparou) sorteia a tela de novo TODA VEZ que escolhe o tema (50/50), não só ao abrir
            for attr in ("_cena_terror", "_cena_medieval", "_cena_magico", "_cena_moderno", "_cena_futurista",
                         "_cena_steampunk", "_cena_posapoc"):
                if hasattr(self, attr):
                    delattr(self, attr)
            self.aplicar_estilo()
            self.mudou.emit()

    @pyqtSlot(str)
    def definirNivel(self, chave):
        if chave in NIVEIS:
            graficos().definir(chave)

    idiomaTrocado = pyqtSignal()

    @pyqtSlot(str)
    def definirIdioma(self, codigo):
        """(v1.0) As bandeirinhas: troca o idioma e a tela inicial é recarregada (fora do clique do QML)."""
        from .. import idioma
        if codigo != idioma.atual() and codigo in dict(idioma.IDIOMAS):
            idioma.definir(codigo)
            QTimer.singleShot(0, self.idiomaTrocado.emit)

    # ---- o Python usa
    def aplicar_estilo(self):
        from PyQt6.QtWidgets import QApplication
        from .tema import gerar_qss
        QApplication.instance().setStyleSheet(gerar_qss(self._tema))   # diálogos (nova aventura, conectar…)

    def definir(self, info=None, ultima=None, servidor=None, papel=None):
        if info is not None:
            from ..idioma import t as tr
            self._info = tr(info)
        if ultima is not None:
            self._ultima = ultima
        if servidor is not None:
            self._servidor = servidor
        if papel is not None:
            self._papel = papel
            QSettings("Taverna", "Launcher").setValue("papel", papel)
        self.mudou.emit()


_REGISTRADO = False


def _registrar_tipos():
    global _REGISTRADO
    if not _REGISTRADO:
        from PyQt6.QtQml import qmlRegisterType
        qmlRegisterType(FundoTema, "Taverna", 1, 0, "FundoTema")
        _REGISTRADO = True


class _CentrarDialogos(QObject):
    """(v0.81) Janelinha cujo pai ainda está ESCONDIDO (ex.: "Nova sessão" e "Entrar na sessão" são da janela do
    Mestre/Jogador, que só aparece depois) nascia no monitor principal, longe da tela inicial: centraliza na janela
    do Taverna que está aparecendo."""

    def __init__(self, lancador):
        super().__init__(lancador)
        self.lancador = lancador

    def eventFilter(self, obj, ev):
        from PyQt6.QtCore import QEvent
        from PyQt6.QtWidgets import QDialog
        if ev.type() == QEvent.Type.Show and isinstance(obj, QDialog):
            try:
                pai = obj.parentWidget()
                if pai is None or not pai.window().isVisible():
                    base = next((j for j in (self.lancador.mestre, self.lancador.player, self.lancador)
                                 if j is not None and j.isVisible()), None)
                    if base is not None:
                        r = obj.frameGeometry()
                        r.moveCenter(base.frameGeometry().center())
                        obj.move(r.topLeft())
            except RuntimeError:   # (objeto do Qt já apagado)
                pass
        return False


# ====================================================================== a janela
class JanelaLancador(QMainWindow):
    def __init__(self):
        super().__init__()
        from PyQt6.QtQuickWidgets import QQuickWidget
        from .tema import icone_app
        _registrar_tipos()
        self.setWindowTitle(APP_NOME)
        self.setWindowIcon(icone_app())
        self.resize(1280, 800)
        self.ponte = Ponte(self)
        self.ponte.escolhido.connect(self._escolhido)
        self.ponte.aplicar_estilo()
        self.quick = QQuickWidget(self)
        self.quick.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        self._provedor = ProvedorTaverna()   # (guardado: senão o Python apaga e as imagens somem)
        self.quick.engine().addImageProvider("taverna", self._provedor)
        self.quick.rootContext().setContextProperty("ponte", self.ponte)
        self.ponte.idiomaTrocado.connect(self._idioma_trocado)
        self._carregar_qml()
        if self.quick.status() == QQuickWidget.Status.Error:
            erros = "\n".join(e.toString() for e in self.quick.errors())
            from ..seguranca import registrar_erro
            registrar_erro(f"Tela inicial (QML) não abriu:\n{erros}")
            raise RuntimeError(erros)
        self.setCentralWidget(self.quick)
        self.mestre = None
        self.player = None
        self._centrar = _CentrarDialogos(self)   # (guardado numa variável)
        QApplication.instance().installEventFilter(self._centrar)
        self._atualizar_infos()

    # ------------------------------------------------------------ idioma
    def _carregar_qml(self):
        from ..idioma import pasta_qml
        self.quick.setSource(QUrl.fromLocalFile(os.path.join(pasta_qml(PASTA_QML), "Lancador.qml")))

    def _idioma_trocado(self):
        """(v1.0) A tela inicial é recarregada já no idioma novo. Janela de mesa que já foi aberta nesta
        execução só muda por inteiro quando o Taverna abre de novo."""
        from PyQt6.QtQuickWidgets import QQuickWidget
        self.quick.setSource(QUrl())
        self.quick.engine().clearComponentCache()
        self._carregar_qml()
        if self.quick.status() == QQuickWidget.Status.Error:   # (não deve acontecer) volta pro original
            from ..seguranca import registrar_erro
            registrar_erro("Tela inicial traduzida não abriu:\n" + "\n".join(e.toString() for e in self.quick.errors()))
            self.quick.setSource(QUrl.fromLocalFile(os.path.join(PASTA_QML, "Lancador.qml")))
        self.setWindowTitle(APP_NOME)
        aviso = ""
        if self.mestre is not None or self.player is not None:
            from ..idioma import ingles
            aviso = ("Some windows switch language only after reopening Taverna." if ingles() else
                     "Algumas janelas só trocam de idioma depois de reabrir o Taverna.")
        self._atualizar_infos(aviso)

    # ------------------------------------------------------------ infos
    def _atualizar_infos(self, aviso=""):
        from ..idioma import t as tr
        ultima = ""
        caminho = QSettings("Taverna", "Mestre").value("ultima_cena", "", type=str)
        if caminho and os.path.isfile(caminho):
            try:
                from ..mesa.arquivo import ler_cabecalho
                cab = ler_cabecalho(caminho)
                ultima = f"{cab['aventura'] or os.path.splitext(os.path.basename(caminho))[0]}  ·  " \
                         f"{tr(dados_tema(cab['tema'])['nome'])}"
            except (OSError, ValueError, KeyError):
                ultima = os.path.basename(caminho)
        cfg = QSettings("Taverna", "Player")
        nome, ip = cfg.value("nome", "", type=str), cfg.value("ip", "", type=str)
        servidor = f"{nome} · {ip}" if nome and ip else ""
        self.ponte.definir(info=aviso, ultima=ultima, servidor=servidor)

    # ------------------------------------------------------------ escolhas
    def _escolhido(self, chave):
        if chave.startswith("mestre_"):
            self._mestre(chave.split("_", 1)[1])
        elif chave == "jogador_entrar":
            self._jogador()
        elif chave == "sair":
            self.close()

    def _janela_mestre(self):
        if self.mestre is None:
            from .janela_mestre import JanelaMestre
            self.mestre = JanelaMestre(lancador=self)
        return self.mestre

    def _janela_player(self):
        if self.player is None:
            from .janela_player import JanelaPlayer
            self.player = JanelaPlayer(lancador=self)
        return self.player

    def _mestre(self, acao):
        j = self._janela_mestre()
        if acao == "nova":
            ok = j.nova_cena()
        elif acao == "continuar":
            ok = j.abrir_cena(j._ultima_cena())
        else:
            ok = j.abrir_cena()
        if ok:
            self.ponte.definir(papel="mestre")
            self._trocar_para(j)
            j.mostrar_mesa()

    def _jogador(self):
        p = self._janela_player()
        if p.pedir_conexao():
            self.ponte.definir(papel="jogador", info="Batendo na porta da taverna…")

    def entrou(self, janela):
        """O jogador conectou: a mesa dele aparece no lugar do launcher."""
        self.ponte.definir(info="")
        if janela.isVisible():   # reconectou depois de cair: já está na mesa
            self.hide()
            return
        self._trocar_para(janela)

    def _trocar_para(self, janela):
        if self.isMaximized():
            janela.showMaximized()
        else:
            janela.setGeometry(self.geometry())
            janela.show()
        janela.raise_()
        janela.activateWindow()
        self.hide()

    def voltar(self, janela, aviso: str = ""):
        """A janela (mestre ou jogador) saiu da mesa: volta pro launcher."""
        if janela.isVisible():
            if janela.isMaximized():
                self.showMaximized()
            else:
                self.setGeometry(janela.geometry())
                self.show()
            janela.hide()
        elif not self.isVisible():
            self.show()
        self.ponte.aplicar_estilo()
        self._atualizar_infos(aviso)
        self.raise_()
        self.activateWindow()


def abrir_launcher() -> JanelaLancador:
    return JanelaLancador()
