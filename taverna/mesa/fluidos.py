"""
🏞 Gás e líquidos de CENÁRIO (v0.45) — pedido do Manel.

"Num calabouço tem uma sala com uma estátua soltando gás tóxico. O gás sai da boca da estátua e se
espalha pelo ambiente." Diferente da ÁREA DE EFEITO (gás mágico: não se espalha nem some), aqui é
gás/líquido de verdade:

  - FONTE: solta sem parar ou por um tempo (ex.: 60 s); liga/desliga. Fica onde o mestre pôs (a boca da
    estátua, um cano…). Só o mestre vê o marcador.
  - GÁS (tóxico, fumaça): espalha (difusão) pela sala, contorna as coisas, NÃO atravessa parede, porta
    fechada nem objeto que bloqueia; abriu a porta, flui. Sem fonte, quanto mais espalha, mais ralo — até
    sumir sozinho.
  - LÍQUIDO (água, lava, ácido): escorre pelo chão do mais fundo pro mais raso até virar uma película e
    para (não some sozinho). Lava escorre devagar, água rápido.
  - Só existe onde tem CENÁRIO (chão pintado ou mapa importado): o que vai pro vazio some.
  - Reações: água + lava → vapor (fumaça) e a lava vira rocha (marca no chão); gás tóxico concentrado +
    fogo/raio/lava (área ou líquido, bola de fogo chegando) → EXPLOSÃO em cadeia na nuvem toda que encosta;
    água alagando uma área de fogo → apaga ali.

Quem calcula é o MESTRE (10×/s); os jogadores recebem o "retrato" (até 4×/s) e só desenham.
Grade de 0,5 m (16 px de cena por… CELULA/2), crescendo conforme precisa (até ~200 m de lado).
"""

import base64
import math
import uuid
import zlib

import numpy as np
from PyQt6.QtCore import QObject, QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPolygonF

from ..config import CELULA

G = CELULA / 2                 # lado da célula (0,5 m)
MAX_CELULAS = 400              # lado máximo da grade (200 m)
PELICULA = 0.06                # líquido: abaixo disso não escorre mais (m) — a poça para com ~6 cm
# chave: (nome, "gas"/"liquido", cor, efeito parecido (desenho/reação), velocidade de espalhar)
TIPOS = {
    "gas_toxico": ("☠ Gás tóxico", "gas", "#7cc040", "veneno", 0.20),
    "fumaca": ("💨 Fumaça", "gas", "#9a9aa2", "fumaca", 0.22),
    "agua": ("💧 Água", "liquido", "#3d8fd0", "agua", 0.20),
    "lava": ("🌋 Lava", "liquido", "#ff6a10", "lava", 0.05),
    "acido": ("🧪 Ácido", "liquido", "#9be02e", "acido", 0.14),
}
VAZOES = {"fraca": 0.5, "media": 1.2, "forte": 2.6}     # (nomes; o valor de verdade é por classe abaixo)
VAZAO_GAS = {"fraca": 2.0, "media": 5.0, "forte": 10.0}        # concentração por segundo
VAZAO_LIQUIDO = {"fraca": 0.06, "media": 0.15, "forte": 0.35}   # altura (m) por segundo, na célula da fonte
QUANTIZAR = {"gas": 2.0, "liquido": 0.5}               # máximo representado na rede/arquivo (0–255)


def _uint8(campo, maximo):
    return np.clip(campo / maximo * 255.0, 0, 255).astype(np.uint8)


class Fluidos(QObject):
    mudou = pyqtSignal()            # o desenho precisa atualizar
    para_rede = pyqtSignal(dict)    # (mestre) retrato novo pros jogadores
    explosao = pyqtSignal(float, float, float)   # x, y, tamanho (m) — a janela mostra pra todo mundo

    def __init__(self, cena, simula: bool = True):
        super().__init__(cena)
        self.cena = cena
        self.simula = simula                 # mestre: calcula · jogador: só recebe
        self.ox = self.oy = 0                # origem da grade (em células)
        self.nx = self.ny = 0
        self.campos: dict[str, np.ndarray] = {}
        self.aberto_x = self.aberto_y = None   # dá pra passar entre a célula e a vizinha?
        self.chao = None
        self.fontes: list[dict] = []
        self.rocha_nova = None               # células onde a lava virou rocha (vira marca no chão)
        self._chave_obst = None
        self._t_rede = 0.0
        self._t_reacoes = 0.0
        self._ultimo = None
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._tique)
        self.itens = None                    # (gás, líquidos, marcadores)

    # ================================================================== grade
    def _garantir(self, x0, y0, x1, y1):
        """A grade cobre esse retângulo da cena (com folga)? Senão, cresce."""
        cx0, cy0 = math.floor(x0 / G) - 8, math.floor(y0 / G) - 8
        cx1, cy1 = math.ceil(x1 / G) + 8, math.ceil(y1 / G) + 8
        if self.nx and cx0 >= self.ox and cy0 >= self.oy and cx1 <= self.ox + self.nx and cy1 <= self.oy + self.ny:
            return
        if self.nx:
            cx0, cy0 = min(cx0, self.ox), min(cy0, self.oy)
            cx1, cy1 = max(cx1, self.ox + self.nx), max(cy1, self.oy + self.ny)
        nx, ny = min(MAX_CELULAS, cx1 - cx0), min(MAX_CELULAS, cy1 - cy0)
        novos = {}
        for nome in TIPOS:
            a = np.zeros((ny, nx), np.float32)
            velho = self.campos.get(nome)
            if velho is not None and self.nx:
                dx, dy = self.ox - cx0, self.oy - cy0
                h, w = min(velho.shape[0], ny - dy), min(velho.shape[1], nx - dx)
                if h > 0 and w > 0 and dx >= 0 and dy >= 0:
                    a[dy:dy + h, dx:dx + w] = velho[:h, :w]
            novos[nome] = a
        self.campos = novos
        self.ox, self.oy, self.nx, self.ny = cx0, cy0, nx, ny
        self.rocha_nova = np.zeros((ny, nx), bool)
        self._chave_obst = None   # recalcula paredes e chão

    def celula(self, x, y):
        return int(math.floor(x / G)) - self.ox, int(math.floor(y / G)) - self.oy

    def ret_cena(self) -> QRectF:
        return QRectF(self.ox * G, self.oy * G, self.nx * G, self.ny * G)

    def _obstaculos(self):
        """Paredes/portas/objetos → arestas fechadas entre células; e onde tem chão."""
        if not self.nx:
            return
        try:
            obst = self.cena.obstaculos_gas() if hasattr(self.cena, "obstaculos_gas") else []
            chao_cam = self.cena.chao_caminho() if hasattr(self.cena, "chao_caminho") else None
        except RuntimeError:
            return
        chave = (self.ox, self.oy, self.nx, self.ny, hash(tuple(obst)), id(chao_cam) if chao_cam is not None else 0,
                 getattr(self.cena, "_chao_versao", 0))
        if chave == self._chave_obst:
            return
        self._chave_obst = chave
        ax = np.ones((self.ny, self.nx - 1), bool)
        ay = np.ones((self.ny - 1, self.nx), bool)
        for x1, y1, x2, y2 in obst:   # cada parede fecha as passagens que ela cruza
            cx0, cx1 = sorted((x1 / G - self.ox, x2 / G - self.ox))
            cy0, cy1 = sorted((y1 / G - self.oy, y2 / G - self.oy))
            i0, i1 = max(0, int(cx0) - 1), min(self.nx - 1, int(cx1) + 1)
            j0, j1 = max(0, int(cy0) - 1), min(self.ny - 1, int(cy1) + 1)
            if i1 < i0 or j1 < j0:
                continue
            # centros das células (em unidades de célula)
            jj, ii = np.mgrid[j0:j1 + 1, i0:i1 + 1].astype(np.float32)
            px, py = ii + 0.5, jj + 0.5
            ax0, ay0 = x1 / G - self.ox, y1 / G - self.oy
            ex, ey = x2 / G - self.ox - ax0, y2 / G - self.oy - ay0

            def cruza(qx, qy, dx, dy):   # segmento (q, q+d) cruza a parede?
                den = dx * ey - dy * ex
                with np.errstate(divide="ignore", invalid="ignore"):
                    t = ((ax0 - qx) * ey - (ay0 - qy) * ex) / den
                    u = ((ax0 - qx) * dy - (ay0 - qy) * dx) / den
                return (np.abs(den) > 1e-9) & (t >= 0) & (t <= 1) & (u >= -0.02) & (u <= 1.02)
            if i1 > i0:
                c = cruza(px[:, :-1], py[:, :-1], 1.0, 0.0)
                ax[j0:j1 + 1, i0:i1] &= ~c
            if j1 > j0:
                c = cruza(px[:-1, :], py[:-1, :], 0.0, 1.0)
                ay[j0:j1, i0:i1 + 1] &= ~c
        self.aberto_x, self.aberto_y = ax, ay
        # chão: onde tem cenário (sem nenhum chão na cena, vale tudo)
        if chao_cam is None:
            self.chao = np.ones((self.ny, self.nx), bool)
        else:
            img = QImage(self.nx, self.ny, QImage.Format.Format_Grayscale8)
            img.fill(0)
            p = QPainter(img)
            p.scale(1 / G, 1 / G)
            p.translate(-self.ox * G, -self.oy * G)
            p.fillPath(chao_cam, QColor(255, 255, 255))
            p.end()
            ptr = img.constBits()
            ptr.setsize(img.sizeInBytes())
            self.chao = np.frombuffer(ptr, np.uint8).reshape(self.ny, img.bytesPerLine())[:, :self.nx] > 127

    # ================================================================== ações do mestre
    def adicionar_fonte(self, tipo, x, y, vazao="media", duracao=0.0) -> dict:
        f = {"id": uuid.uuid4().hex[:10], "tipo": tipo if tipo in TIPOS else "gas_toxico", "x": float(x),
             "y": float(y), "vazao": vazao if vazao in VAZOES else "media", "duracao": max(0.0, float(duracao)),
             "decorrido": 0.0, "ligada": True}
        self.fontes.append(f)
        self._acordar()
        self.mudou.emit()
        return f

    def remover_fonte(self, ident):
        self.fontes = [f for f in self.fontes if f["id"] != ident]
        self.mudou.emit()

    def soltar(self, tipo, x, y, raio_m=2.0):
        """Nuvem solta (gás) ou poça derramada (líquido), sem fonte."""
        tipo = tipo if tipo in TIPOS else "gas_toxico"
        r = max(0.5, float(raio_m)) * CELULA
        self._garantir(x - r, y - r, x + r, y + r)
        self._cobrir_cenario()
        i, j = self.celula(x, y)
        n = max(1, int(r / G))
        jj, ii = np.ogrid[-n:n + 1, -n:n + 1]
        disco = (ii * ii + jj * jj) <= n * n
        i0, j0 = i - n, j - n
        a = self.campos[tipo]
        sl = (slice(max(0, j0), min(self.ny, j0 + 2 * n + 1)), slice(max(0, i0), min(self.nx, i0 + 2 * n + 1)))
        d = disco[sl[0].start - j0:sl[0].stop - j0, sl[1].start - i0:sl[1].stop - i0]
        valor = 1.2 if TIPOS[tipo][1] == "gas" else 0.14   # (líquido: espalha até ~1,5× o tamanho escolhido)
        a[sl][d] = np.maximum(a[sl][d], valor)
        self._obstaculos()
        if self.chao is not None:
            a *= self.chao
        self._acordar()
        self.mudou.emit()

    def limpar(self, fontes=False):
        for a in self.campos.values():
            a[:] = 0
        if fontes:
            self.fontes = []
        try:
            self.luzes_da_lava()   # (sem lava, as luzes dela apagam)
        except RuntimeError:
            pass
        self.mudou.emit()
        self._mandar_rede(forcar=True)

    def _acordar(self):
        if self.simula and not self.timer.isActive():
            import time
            self._ultimo = time.monotonic()
            self.timer.start()

    def ativo(self) -> bool:
        return bool(self.fontes) or any(float(a.max()) > 0.004 for a in self.campos.values() if a.size)

    # ================================================================== simulação
    def _tique(self):
        import time
        agora = time.monotonic()
        dt = min(0.25, agora - (self._ultimo or agora)) or 0.1
        self._ultimo = agora
        try:
            self.passo(dt)
        except RuntimeError:   # cena fechada
            self.timer.stop()
            return
        if not self.ativo():
            self.timer.stop()
            self.mudou.emit()
            self._mandar_rede(forcar=True)

    def _cobrir_cenario(self):
        """A grade cobre o cenário inteiro (até o limite); sem chão, cresce quando o fluido chega na borda."""
        try:
            chao = self.cena.chao_caminho() if hasattr(self.cena, "chao_caminho") else None
        except RuntimeError:
            chao = None
        if chao is not None:
            r = chao.boundingRect()
            self._garantir(r.left(), r.top(), r.right(), r.bottom())
        elif self.nx:
            borda = any(a[:2, :].any() or a[-2:, :].any() or a[:, :2].any() or a[:, -2:].any()
                        for a in self.campos.values())
            if borda:
                r = self.ret_cena()
                self._garantir(r.left() - 16 * G, r.top() - 16 * G, r.right() + 16 * G, r.bottom() + 16 * G)

    def passo(self, dt=0.1):
        # a grade acompanha as fontes e o cenário
        for f in self.fontes:
            self._garantir(f["x"] - G, f["y"] - G, f["x"] + G, f["y"] + G)
        self._cobrir_cenario()
        if not self.nx:
            return
        self._obstaculos()
        sub = max(1, int(round(dt / 0.1)))
        for _ in range(sub):
            self._sub_passo(dt / sub)
        import time
        agora = time.monotonic()
        if agora - self._t_reacoes > 0.5:
            self._t_reacoes = agora
            self._reacoes_com_areas()
            self._rocha_vira_marca()
            self.luzes_da_lava()
        self.mudou.emit()
        self._mandar_rede()

    def _sub_passo(self, dt):
        ax, ay = self.aberto_x, self.aberto_y
        for f in self.fontes:   # fontes soltando
            if not f["ligada"]:
                continue
            if f["duracao"] > 0:
                f["decorrido"] += dt
                if f["decorrido"] >= f["duracao"]:
                    f["ligada"] = False
                    continue
            i, j = self.celula(f["x"], f["y"])
            if 0 <= i < self.nx and 0 <= j < self.ny:
                tabela = VAZAO_GAS if TIPOS[f["tipo"]][1] == "gas" else VAZAO_LIQUIDO
                self.campos[f["tipo"]][j, i] += tabela[f["vazao"]] * dt
        for nome, (_n, classe, _c, _e, vel) in TIPOS.items():
            a = self.campos[nome]
            if not a.any():
                continue
            k = vel * dt / 0.1
            repete = 4 if classe == "gas" else 2   # gás espalha rápido (enche a sala em ~meio minuto)
            for _r in range(repete):
                if classe == "gas":
                    fx = (a[:, 1:] - a[:, :-1]) * ax
                    fy = (a[1:, :] - a[:-1, :]) * ay
                    kk = min(0.24, k)
                else:   # líquido: só escorre do lado que ainda está acima da película
                    dx = a[:, 1:] - a[:, :-1]
                    dy = a[1:, :] - a[:-1, :]
                    alto_x = np.maximum(a[:, 1:], a[:, :-1]) > PELICULA
                    alto_y = np.maximum(a[1:, :], a[:-1, :]) > PELICULA
                    fx = dx * ax * alto_x
                    fy = dy * ay * alto_y
                    kk = min(0.22, k)
                delta = np.zeros_like(a)
                delta[:, :-1] += fx
                delta[:, 1:] -= fx
                delta[:-1, :] += fy
                delta[1:, :] -= fy
                a += kk * delta
            if classe == "gas":   # gás se dilui e some (o fiapo ralo some primeiro)
                a *= (1.0 - 0.0025 * dt / 0.1)
                a -= 0.0005 * dt / 0.1
            np.maximum(a, 0, out=a)
            if self.chao is not None:
                a *= self.chao   # no vazio, some
        # água + lava → vapor e rocha
        agua, lava = self.campos["agua"], self.campos["lava"]
        junto = np.minimum(agua, lava)
        if junto.max() > 0.002:
            agua -= junto
            lava -= junto * 0.8
            self.campos["fumaca"] += junto * 6.0
            self.rocha_nova |= (junto > 0.004)

    # ================================================================== reações com o resto da mesa
    def _mascara_de(self, caminho_cena: QPainterPath) -> np.ndarray:
        img = QImage(self.nx, self.ny, QImage.Format.Format_Grayscale8)
        img.fill(0)
        p = QPainter(img)
        p.scale(1 / G, 1 / G)
        p.translate(-self.ox * G, -self.oy * G)
        p.fillPath(caminho_cena, QColor(255, 255, 255))
        p.end()
        ptr = img.constBits()
        ptr.setsize(img.sizeInBytes())
        return np.frombuffer(ptr, np.uint8).reshape(self.ny, img.bytesPerLine())[:, :self.nx] > 127

    def caminho_de(self, mascara: np.ndarray) -> QPainterPath:
        """Células marcadas → contorno na cena (pra recorte e marcas)."""
        cam = QPainterPath()
        cam.setFillRule(Qt.FillRule.WindingFill)
        h, w = mascara.shape
        for j in range(h):   # cada linha: as faixas seguidas de células marcadas viram retângulos
            linha = mascara[j]
            if not linha.any():
                continue
            d = np.diff(np.concatenate(([0], linha.astype(np.int8), [0])))
            for i0, i1 in zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]):
                cam.addRect(QRectF((self.ox + i0) * G, (self.oy + j) * G, (i1 - i0) * G, G))
        return cam.simplified()

    def ignicao(self, mascara: np.ndarray) -> bool:
        """Fogo/faísca encostou: o gás tóxico concentrado que encosta ali EXPLODE (em cadeia)."""
        gas = self.campos.get("gas_toxico")
        if gas is None or not gas.size:
            return False
        semente = mascara & (gas > 0.3)
        if not semente.any():
            return False
        regiao = semente.copy()
        alvo = gas > 0.12
        ax, ay = self.aberto_x, self.aberto_y
        while True:   # espalha a explosão pelas células ligadas (sem passar parede)
            nova = regiao.copy()
            nova[:, 1:] |= regiao[:, :-1] & ax
            nova[:, :-1] |= regiao[:, 1:] & ax
            nova[1:, :] |= regiao[:-1, :] & ay
            nova[:-1, :] |= regiao[1:, :] & ay
            nova &= alvo
            if (nova == regiao).all():
                break
            regiao = nova
        jj, ii = np.nonzero(regiao)
        cx = (ii.mean() + 0.5 + self.ox) * G
        cy = (jj.mean() + 0.5 + self.oy) * G
        tam = max(1.5, math.sqrt(len(ii) * 0.25 / math.pi) * 1.3)
        gas[regiao] = 0
        self.campos["fumaca"][regiao] += 0.6
        self.explosao.emit(cx, cy, tam)
        return True

    def ignicao_em(self, x, y, raio_m=1.5) -> bool:
        """Bola de fogo (ou faísca) chegando nesse ponto."""
        if not self.nx:
            return False
        cam = QPainterPath()
        cam.addEllipse(QPointF(x, y), raio_m * CELULA, raio_m * CELULA)
        return self.ignicao(self._mascara_de(cam))

    def _reacoes_com_areas(self):
        cena = self.cena
        if not hasattr(cena, "efeitos_visiveis"):
            return
        lava = self.campos["lava"] > 0.01
        if lava.any():
            self.ignicao(lava)
        for area in list(cena.efeitos_visiveis()):
            try:
                if area.efeito in ("fogo", "eletrico", "lava"):
                    m = self._mascara_de(area.caminho_cena())
                    self.ignicao(m)
                    if area.efeito == "fogo":
                        molhado = m & (self.campos["agua"] > PELICULA * 0.8)
                        if molhado.sum() >= 2:   # a água alagou o fogo: apaga ali
                            if not area.recortar(self.caminho_de(molhado)):
                                cena.remover_efeitos(ids={area.uid})
                            self.campos["fumaca"][molhado] += 0.5
            except RuntimeError:
                continue

    def _rocha_vira_marca(self):
        if self.rocha_nova is None or not self.rocha_nova.any():
            return
        terreno = getattr(self.cena, "terreno", None)
        if terreno is None or not hasattr(terreno, "adicionar_marca"):
            self.rocha_nova[:] = False
            return
        cam = self.caminho_de(self.rocha_nova)
        self.rocha_nova[:] = False
        for k, pol in enumerate(cam.toFillPolygons()):
            pts = [[round(pol.at(i).x(), 1), round(pol.at(i).y(), 1)] for i in range(pol.count())]
            if len(pts) > 96:
                passo = len(pts) / 96
                pts = [pts[int(i * passo)] for i in range(96)]
            if len(pts) >= 3:
                terreno.adicionar_marca({"t": "marca", "m": "marca", "k": "basalto", "p": pts, "s": 31 + k})
        if hasattr(self.cena, "registrar"):
            self.cena.registrar()

    def luzes_da_lava(self):
        """Lava de cenário BRILHA: uma luz laranja (com sombra) em cada pedaço de ~3 m que tem lava."""
        from . import luz_dinamica
        antigas = [k for k in (self.cena.__dict__.get("_luzes_temp") or {}) if k.startswith("lava_cenario:")]
        lava = self.campos.get("lava")
        novas = {}
        if lava is not None and lava.size and lava.max() > 0.01:
            B = 6   # blocos de 6 células = 3 m
            h, w = lava.shape
            hb, wb = (h + B - 1) // B, (w + B - 1) // B
            pad = np.zeros((hb * B, wb * B), np.float32)
            pad[:h, :w] = lava > 0.01
            blocos = pad.reshape(hb, B, wb, B).sum(axis=(1, 3))
            for jb, ib in sorted(zip(*np.nonzero(blocos >= 3)), key=lambda t: -blocos[t])[:8]:
                cx = (self.ox + ib * B + B / 2) * G
                cy = (self.oy + jb * B + B / 2) * G
                novas[f"lava_cenario:{jb}:{ib}"] = {"x": cx, "y": cy, "fraco": 4.5, "cor": "#ff6a10",
                                                    "brilho": min(1.0, 0.45 + blocos[jb, ib] / (B * B))}
        for k in antigas:
            if k not in novas:
                luz_dinamica.definir(self.cena, k, None)
        for k, d in novas.items():
            luz_dinamica.definir(self.cena, k, d)

    # ================================================================== rede / arquivo
    def retrato(self) -> dict:
        """Só a parte que tem alguma coisa, em bytes (0–255) comprimidos."""
        campos = {}
        for nome, a in self.campos.items():
            if not a.size or a.max() <= 0.004:
                continue
            jj, ii = np.nonzero(a > 0.004)
            j0, j1, i0, i1 = int(jj.min()), int(jj.max()) + 1, int(ii.min()), int(ii.max()) + 1
            q = _uint8(a[j0:j1, i0:i1], QUANTIZAR[TIPOS[nome][1]])
            campos[nome] = {"i": self.ox + i0, "j": self.oy + j0, "w": i1 - i0, "h": j1 - j0,
                            "d": base64.b64encode(zlib.compress(q.tobytes(), 6)).decode("ascii")}
        return {"campos": campos}

    def aplicar_retrato(self, d: dict):
        """Jogador (ou arquivo): põe o retrato recebido."""
        for a in self.campos.values():
            a[:] = 0
        for nome, c in (d.get("campos") or {}).items():
            if nome not in TIPOS:
                continue
            try:
                i, j, w, h = int(c["i"]), int(c["j"]), int(c["w"]), int(c["h"])
                if w <= 0 or h <= 0 or w > MAX_CELULAS or h > MAX_CELULAS:
                    continue
                q = np.frombuffer(zlib.decompress(base64.b64decode(c["d"])), np.uint8).reshape(h, w)
            except (KeyError, TypeError, ValueError, zlib.error):
                continue
            self._garantir(i * G, j * G, (i + w) * G, (j + h) * G)
            a = self.campos[nome]
            di, dj = i - self.ox, j - self.oy
            a[dj:dj + h, di:di + w] = q.astype(np.float32) / 255.0 * QUANTIZAR[TIPOS[nome][1]]
        try:
            self.luzes_da_lava()   # (no jogador também: a lava brilha)
        except RuntimeError:
            pass
        self.mudou.emit()

    def _mandar_rede(self, forcar=False):
        import time
        agora = time.monotonic()
        if forcar or agora - self._t_rede > 0.25:
            self._t_rede = agora
            self.para_rede.emit(self.retrato())

    def para_dict(self) -> dict:
        d = self.retrato()
        d["fontes"] = [dict(f) for f in self.fontes]
        return d

    def de_dict(self, d: dict):
        self.fontes = []
        for f in d.get("fontes") or []:
            try:
                self.fontes.append({"id": str(f.get("id") or uuid.uuid4().hex[:10]),
                                    "tipo": f.get("tipo") if f.get("tipo") in TIPOS else "gas_toxico",
                                    "x": float(f["x"]), "y": float(f["y"]),
                                    "vazao": f.get("vazao") if f.get("vazao") in VAZOES else "media",
                                    "duracao": float(f.get("duracao", 0)), "decorrido": float(f.get("decorrido", 0)),
                                    "ligada": bool(f.get("ligada", True))})
            except (KeyError, TypeError, ValueError):
                continue
        self.aplicar_retrato(d)
        if self.ativo():
            self._acordar()


def de_cena(cena, simula=True) -> Fluidos:
    """O gás/líquido da cena (cria na primeira vez) + os itens que desenham."""
    f = getattr(cena, "fluidos", None)
    if f is None:
        f = cena.fluidos = Fluidos(cena, simula)
    from . import fluidos_desenho
    fluidos_desenho.garantir_itens(cena, f)
    return f
