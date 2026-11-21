"""
🏙 Cenários do tema Moderno (v0.58, pacote do Manel). Sorteia um cada vez que escolhe o tema (50/50):

  CELULAR — vista de cima de uma mesa à noite: chuva na janela do lado, café soltando fumaça, chaves, carteira,
            papéis. O MENU É A TELA DO CELULAR (como um app); a luz da tela ilumina a mesa. Mouse num botão =
            o celular vibra de leve; notificações inventadas descendo de vez em quando.
  TERRAÇO — noite no alto de um prédio: a cidade lá embaixo (janelas acesas, carros passando), um helicóptero
            com holofote cruzando de vez em quando. O MENU APARECE NUM OUTDOOR DE LED no prédio da frente
            (pixels visíveis, brilho no ar úmido).

Tudo desenhado aqui (nada de marca ou app de verdade).
"""

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPen

from .estilizado import _c, _caixa_borrar, _rgb_img, _rng, _ruido, _suave
from .terror_cenas import _guardado, _pintar, _pixelar, _rgba

NOTIFICACOES = [
    ("Grupo da mesa", "alguém leva os dados extras?"),
    ("Lembrete", "sessão sábado, 19h — não esquece a ficha"),
    ("Bardo", "compus uma música sobre o dragão 🎵"),
    ("Mestre", "preparei uma surpresa pra hoje 😈"),
    ("Clima", "chuva forte a noite toda"),
    ("Grupo da mesa", "quem tá com a poção de cura?"),
    ("Ladino", "não fui eu que peguei o ouro"),
]


def textura(nome):
    if nome.startswith("predio_"):                                  # predio_<semente>_<colunas>_<andares>[_luz]
        partes = nome.split("_")
        try:
            semente, cols, lins = int(partes[1]), int(partes[2]), int(partes[3])
        except (IndexError, ValueError):
            return None
        luz = nome.endswith("_luz")
        return _guardado(("moderno", nome), lambda: _predio(semente, cols, lins)[1 if luz else 0])
    if nome.startswith("fachada") and nome[7:8].isdigit():
        k = int(nome[7])
        luz = nome.endswith("_luz")
        return _guardado(("moderno", nome), lambda: _fachada(k)[1 if luz else 0])
    f = {"mesa_moderna": _mesa_moderna, "documento": _documento, "couro_preto": _couro_preto,
         "ceu_cidade": _ceu_cidade, "concreto": _concreto, "asfalto": _asfalto,
         "papel_outdoor": _papel_outdoor}.get(nome)
    return _guardado(("moderno", nome), f) if f else None


def grade_led(lado=8):
    """A grade do outdoor de LED: cada "pixel" é um quadradinho, separado por uma linha escura."""
    def gerar():
        a = np.zeros((lado, lado), np.float32)
        a[:, -2:] = 0.85
        a[-2:, :] = 0.85
        rgb = np.zeros((lado, lado, 3), np.float32)
        return _rgba(rgb, a)
    return _guardado(("led",), gerar)


# ---------------------------------------------------------------------- mesa (celular)
def _mesa_moderna(lado=1024):
    """Tampo de madeira escura fosca (tábuas largas, veio suave)."""
    rng = _rng("mesa-moderna")
    ys, xs = np.mgrid[0:lado, 0:lado].astype(np.float32)
    larg = lado / 4
    tab = np.floor(ys / larg)
    lu = ys - tab * larg
    fibra = _caixa_borrar(rng.random((lado, lado)).astype(np.float32), 1)
    fibra = _caixa_borrar(fibra, 16)
    fibra = (fibra - fibra.min()) / max(1e-6, float(np.ptp(fibra)))
    ra = _ruido(lado, lado, 30, rng)
    veio = 0.5 + 0.5 * np.sin(ys * 0.06 + ra * 9 + tab * 2.1)
    tons = _rng("tons-mesa-moderna").random(8).astype(np.float32)
    cor = _c("#3a2a20") * (0.8 + 0.3 * tons[tab.astype(int) % 8])[..., None]
    cor *= (0.75 + 0.3 * fibra[..., None]) * (0.9 + 0.12 * veio[..., None])
    cor *= (0.55 + 0.45 * _suave(np.minimum(lu, larg - lu) / 2))[..., None]
    return _rgb_img(cor)


def _documento():
    rng = _rng("documento")

    def d(p, W, H):
        p.fillRect(0, 0, W, H, QColor("#ecebe6"))
        p.fillRect(QRectF(40, 40, W * 0.35, 26), QColor("#3a4a6a"))
        p.setPen(QPen(QColor(60, 60, 70, 140), 5))
        y = 110
        while y < H - 120:
            x0 = 40
            comp = rng.uniform(0.55, 0.92) * (W - 80)
            p.drawLine(QPointF(x0, y), QPointF(x0 + comp, y))
            y += rng.choice([22, 22, 22, 40])
        p.setPen(QPen(QColor(40, 60, 140, 200), 4))          # rabisco de assinatura
        cx, cy = W * 0.7, H - 70
        pts = [QPointF(cx + k * 9, cy + math.sin(k * 1.3) * 12) for k in range(14)]
        for a, b in zip(pts, pts[1:]):
            p.drawLine(a, b)
        p.fillRect(QRectF(0, 0, W, H), QColor(120, 100, 60, 18))
    return _pintar(512, 680, d)


def _couro_preto(lado=256):
    rng = _rng("couro-preto")
    n = _ruido(lado, lado, 2, rng) * 0.5 + _ruido(lado, lado, 8, rng) * 0.5
    cor = _c("#26201c") * (0.7 + 0.5 * n[..., None])
    cor[:, :6] *= 0.6
    cor[:, -6:] *= 0.6
    return _rgb_img(cor)


# ---------------------------------------------------------------------- cidade (terraço)
def _fachada(k, W=512, H=1024):
    """Fachada de prédio: grade de janelas; algumas acesas (quentes ou frias). Volta (cor, só-a-luz)."""
    rng = _rng("fachada", k)
    cor = np.zeros((H, W, 3), np.float32)
    luz = np.zeros((H, W, 3), np.float32)
    base = _c(["#2a2e36", "#34302c", "#22282e"][k % 3])
    n = _ruido(H, W, 12, rng)
    cor[:] = base * (0.75 + 0.35 * n[..., None])
    cols, lins = [8, 6, 10][k % 3], [20, 16, 24][k % 3]
    cw, ch = W / cols, H / lins
    for i in range(cols):
        for j in range(lins):
            x0, y0 = int(i * cw + cw * 0.18), int(j * ch + ch * 0.22)
            x1, y1 = int((i + 1) * cw - cw * 0.18), int((j + 1) * ch - ch * 0.2)
            acesa = rng.random() < 0.38
            if acesa:
                tom = _c(rng.choice(["#ffd27a", "#ffe4a8", "#ffb45a", "#bfe0ff", "#d8f0ff"]))
                v = rng.uniform(0.55, 1.0)
                cor[y0:y1, x0:x1] = tom * v
                luz[y0:y1, x0:x1] = tom * v
                if rng.random() < 0.3:                          # persiana / alguém na janela
                    yy = int(y0 + (y1 - y0) * rng.uniform(0.2, 0.6))
                    cor[yy:y1, x0:x1] *= 0.55
                    luz[yy:y1, x0:x1] *= 0.55
            else:
                cor[y0:y1, x0:x1] = _c("#0e1218") * rng.uniform(0.8, 1.4)
    return _rgb_img(np.clip(cor, 0, 1)), _rgb_img(np.clip(luz, 0, 1))


def _predio(semente, cols, lins, W=1024, H=2048):
    """(v0.58, pedido do Manel) Fachada INTEIRA de um prédio (a textura cobre o prédio todo: nada se repete).
    Janelas GRANDES, cada uma do seu jeito: acesa quente/fria ou apagada, com cortina, persiana, gente, planta,
    TV piscando azul… Faixas de laje entre os andares. Volta (cor, só-a-luz)."""
    from PyQt6.QtGui import QImage, QPainter, QLinearGradient, QBrush
    rng = _rng("predio", semente, cols, lins)
    paleta = ["#3a3a40", "#4a4038", "#32383e", "#463a3a", "#3c4038"]
    base = QColor(paleta[semente % len(paleta)])
    cor = QImage(W, H, QImage.Format.Format_RGB32)
    luz = QImage(W, H, QImage.Format.Format_RGB32)
    cor.fill(base)
    luz.fill(QColor(0, 0, 0))
    pc, pl = QPainter(cor), QPainter(luz)
    for p in (pc, pl):
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # textura da parede (manchas) e as lajes entre andares
    for _ in range(int(W * H / 2500)):
        pc.setPen(Qt.PenStyle.NoPen)
        pc.setBrush(QColor(0, 0, 0, int(rng.uniform(6, 26))) if rng.random() < 0.6 else QColor(255, 255, 255, int(rng.uniform(4, 14))))
        r = rng.uniform(4, 30)
        pc.drawEllipse(QPointF(rng.uniform(0, W), rng.uniform(0, H)), r, r * rng.uniform(0.4, 1))
    cw, ch = W / cols, H / lins
    for j in range(lins + 1):
        pc.fillRect(QRectF(0, j * ch - 5, W, 10), base.darker(135))
    quentes = ["#ffd27a", "#ffe2a8", "#ffbe6a", "#fff0cc"]
    frias = ["#bfe0ff", "#d8ecff", "#a8c8ff"]
    for i in range(cols):
        for j in range(lins):
            m = 0.17 + rng.uniform(-0.02, 0.03)
            x0, y0 = i * cw + cw * m, j * ch + ch * 0.2
            w, h = cw * (1 - 2 * m), ch * 0.62
            jan = QRectF(x0, y0, w, h)
            pc.fillRect(jan.adjusted(-6, -6, 6, 10), base.darker(160))      # moldura + peitoril
            pc.fillRect(QRectF(x0 - 10, y0 + h + 4, w + 20, 8), base.lighter(125))
            sorte = rng.random()
            if sorte < 0.42:                                                  # ACESA
                tom = QColor(rng.choice(quentes if rng.random() < 0.75 else frias))
                g = QLinearGradient(x0, y0, x0, y0 + h)
                g.setColorAt(0, tom.darker(rng.integers(115, 150)))
                g.setColorAt(1, tom)
                for p in (pc, pl):
                    p.fillRect(jan, QBrush(g))
                extra = rng.random()
                if extra < 0.3:                                               # cortina meio fechada
                    lado = rng.random() < 0.5
                    larg = w * rng.uniform(0.25, 0.45)
                    cort = QRectF(x0 if lado else x0 + w - larg, y0, larg, h)
                    cc = QColor(rng.choice(["#a0503a", "#3a5a8a", "#8a7a5a", "#6a3a5a"]))
                    for p, f in ((pc, 1.0), (pl, 0.45)):
                        c2 = QColor(cc)
                        c2.setRgb(int(cc.red() * f), int(cc.green() * f), int(cc.blue() * f))
                        p.fillRect(cort, c2)
                elif extra < 0.5:                                             # persiana (listras)
                    for k in range(int(h / 12)):
                        for p in (pc, pl):
                            p.fillRect(QRectF(x0, y0 + k * 12, w, 5), QColor(0, 0, 0, 120))
                elif extra < 0.65:                                            # alguém na janela (silhueta)
                    pose = int(rng.integers(0, 5))
                    for p in (pc, pl):
                        p.save()
                        p.setClipRect(jan)
                        _pessoa(p, jan, pose, rng.uniform(0.3, 0.7), tom)
                        p.restore()
                    rng.random()
                elif extra < 0.75:                                            # luminária pendurada
                    for p in (pc, pl):
                        p.setPen(QPen(QColor(30, 24, 18), 3))
                        p.drawLine(QPointF(x0 + w / 2, y0), QPointF(x0 + w / 2, y0 + h * 0.3))
            elif sorte < 0.52:                                                # TV ligada (azul) no escuro
                tv = QColor("#5a80d8")
                for p in (pc, pl):
                    p.fillRect(jan, QColor("#0e1420"))
                    g = QLinearGradient(x0, y0 + h, x0, y0)
                    g.setColorAt(0, tv)
                    g.setColorAt(1, QColor(0, 0, 0, 0))
                    p.fillRect(QRectF(x0, y0 + h * 0.4, w, h * 0.6), QBrush(g))
            else:                                                             # APAGADA (vidro escuro com reflexo)
                pc.fillRect(jan, QColor("#10141c"))
                g = QLinearGradient(x0, y0, x0 + w, y0 + h)
                g.setColorAt(0, QColor(120, 140, 170, 40))
                g.setColorAt(0.5, QColor(0, 0, 0, 0))
                pc.fillRect(jan, QBrush(g))
            # divisão da janela (caixilho)
            pc.setPen(QPen(base.darker(170), 5))
            pc.drawLine(QPointF(x0 + w / 2, y0), QPointF(x0 + w / 2, y0 + h))
            pl.setPen(QPen(QColor(0, 0, 0), 5))
            pl.drawLine(QPointF(x0 + w / 2, y0), QPointF(x0 + w / 2, y0 + h))
    pc.end()
    pl.end()
    return cor, luz


def _pessoa(p, jan, pose, onde, luz):
    """(v0.58, o Manel pediu mais caprichado) Silhueta de gente na janela acesa, com contorno de luz.
    poses: 0 em pé de frente · 1 de lado tomando café · 2 sentado no notebook · 3 duas pessoas conversando ·
    4 de lado olhando o celular."""
    from PyQt6.QtGui import QPainterPath
    escuro = QColor(18, 14, 12)
    borda = QColor(luz).lighter(115)
    borda.setAlpha(150)
    x0, y0, w, h = jan.x(), jan.y(), jan.width(), jan.height()
    u = h / 100.0                                       # tudo em "centésimos" da altura da janela

    def corpo(cx, chao, lado=1, olha=0.0, braco=None):
        """Uma pessoa de pé: cabeça com cabelo, pescoço, ombros arredondados e tronco."""
        c = QPainterPath()
        cab_y = chao - 62 * u
        c.addEllipse(QPointF(cx + olha * 2 * u, cab_y), 8.5 * u, 10 * u)                   # cabeça
        cab = QPainterPath()                                                               # cabelo (volume em cima)
        cab.addEllipse(QPointF(cx - lado * 1.5 * u, cab_y - 4 * u), 9.5 * u, 8 * u)
        c = c.united(cab)
        if olha:                                                                           # nariz (de perfil)
            nariz = QPainterPath(QPointF(cx + olha * 8 * u, cab_y - 1 * u))
            nariz.lineTo(QPointF(cx + olha * 11.5 * u, cab_y + 3 * u))
            nariz.lineTo(QPointF(cx + olha * 8 * u, cab_y + 4 * u))
            c = c.united(nariz)
        c.addRect(QRectF(cx - 3.5 * u, cab_y + 8 * u, 7 * u, 6 * u))                       # pescoço
        tronco = QPainterPath(QPointF(cx - 17 * u, chao + 5 * u))
        tronco.lineTo(QPointF(cx - 17 * u, cab_y + 22 * u))
        tronco.quadTo(QPointF(cx - 17 * u, cab_y + 13 * u), QPointF(cx - 7 * u, cab_y + 13 * u))
        tronco.lineTo(QPointF(cx + 7 * u, cab_y + 13 * u))
        tronco.quadTo(QPointF(cx + 17 * u, cab_y + 13 * u), QPointF(cx + 17 * u, cab_y + 22 * u))
        tronco.lineTo(QPointF(cx + 17 * u, chao + 5 * u))
        tronco.closeSubpath()
        c = c.united(tronco)
        def braco_grosso(*pts):
            from PyQt6.QtGui import QPainterPathStroker
            lin = QPainterPath(QPointF(*pts[0]))
            for q in pts[1:]:
                lin.lineTo(QPointF(*q))
            st = QPainterPathStroker()
            st.setWidth(7 * u)
            st.setCapStyle(Qt.PenCapStyle.RoundCap)
            st.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            return st.createStroke(lin)
        ombro = (cx + olha * 11 * u, cab_y + 19 * u)
        if braco == "cafe":                                                                # caneca na boca
            c = c.united(braco_grosso(ombro, (cx + olha * 19 * u, cab_y + 38 * u), (cx + olha * 13 * u, cab_y + 8 * u)))
            c.addRoundedRect(QRectF(cx + olha * 13 * u - 5 * u, cab_y - 1 * u, 10 * u, 11 * u), 2 * u, 2 * u)
        elif braco == "celular":                                                           # celular na frente do rosto
            c = c.united(braco_grosso(ombro, (cx + olha * 17 * u, cab_y + 40 * u), (cx + olha * 19 * u, cab_y + 14 * u)))
        return c
    figuras = []
    chao = y0 + h + 4 * u
    cx = x0 + w * onde
    if pose == 0:
        figuras.append(corpo(cx, chao))
    elif pose == 1:
        figuras.append(corpo(cx, chao, 1, olha=1, braco="cafe"))
    elif pose == 2:                                                                        # sentado no notebook
        figuras.append(corpo(cx, chao + 18 * u))
        p.fillRect(QRectF(x0, y0 + h * 0.82, w, h * 0.2), escuro)                         # mesa
        tela = QRectF(cx + 8 * u, y0 + h * 0.68, 22 * u, 14 * u)
        p.fillRect(tela, QColor(170, 200, 255))                                            # brilho do notebook
    elif pose == 3:                                                                        # duas pessoas conversando
        figuras.append(corpo(x0 + w * 0.24, chao, 1, olha=1))
        figuras.append(corpo(x0 + w * 0.78, chao + 4 * u, -1, olha=-1, braco="cafe"))
    else:
        figuras.append(corpo(cx, chao, -1, olha=-1, braco="celular"))
        p.fillRect(QRectF(cx - 22 * u, chao - 52 * u, 6 * u, 9 * u), QColor(150, 190, 255))  # tela do celular
    for f in figuras:
        p.setPen(QPen(borda, max(1.0, 1.2 * u)))                                          # contorno de luz
        p.setBrush(escuro)
        p.drawPath(f)


def janelas_predio(semente, cols, lins):
    """Quais janelas desse prédio estão ACESAS (mesmo sorteio da textura) — pra pôr jardineiras/ar-condicionado."""
    rng = _rng("predio", semente, cols, lins)
    return rng   # (o QML usa a própria regra; deixado aqui pra referência)


def _ceu_cidade(W=2048, H=1024):
    """Noite na cidade: azul-escuro em cima, o laranja da luz da cidade embaixo, nuvens baixas."""
    rng = _rng("ceu-cidade")
    h2, w2 = H // 2, W // 2
    v = np.linspace(0, 1, h2, dtype=np.float32)[:, None, None]
    cor = _c("#050a18")[None, None] * (1 - v) + _c("#1a1830")[None, None] * v
    cor = cor * np.ones((1, w2, 1), np.float32)
    cor += _c("#c8602a")[None, None] * (np.exp(-((1 - v) / 0.18) ** 2) * 0.45)
    nuv = _suave((_ruido(h2, w2, 26, rng) - 0.5) * 3) * (v[..., 0] > 0.35)
    cor = cor * (1 - nuv[..., None] * 0.4) + _c("#3a2a3a")[None, None] * nuv[..., None] * 0.4
    cor = np.repeat(np.repeat(cor, 2, axis=0), 2, axis=1)
    return _rgb_img(np.clip(cor, 0, 1))


def _papel_outdoor(W=1650, H=1050):
    """Por cima do cartaz do outdoor (fundo transparente): as EMENDAS das folhas coladas, rugas, manchas de cola,
    sujeira de chuva escorrendo e um canto rasgado mostrando o papel de baixo."""
    rng = _rng("papel-outdoor")
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    a = np.zeros((H, W), np.float32)
    cor = np.zeros((H, W, 3), np.float32)
    # emendas (4 folhas na horizontal, 2 na vertical): linha escura + borda clara levantada
    for k in range(1, 4):
        x = W * k / 4 + rng.uniform(-6, 6)
        d = np.abs(xs - x)
        a = np.maximum(a, np.exp(-(d / 1.6) ** 2) * 0.55)
        cor += (np.exp(-((xs - x - 4) / 2.5) ** 2) * 0.35)[..., None]
    y = H / 2 + rng.uniform(-8, 8)
    a = np.maximum(a, np.exp(-((ys - y) / 1.6) ** 2) * 0.5)
    # rugas (bolhas de cola) e manchas
    rug = _ruido(H, W, 22, rng)
    rug2 = _suave((np.abs(rug - 0.5) < 0.012).astype(np.float32))
    a = np.maximum(a, _caixa_borrar(rug2, 2) * 0.35)
    mancha = _suave((_ruido(H, W, 60, rng) - 0.62) * 4)
    a = np.maximum(a, mancha * 0.22)
    # sujeira escorrendo de cima (chuva)
    escorre = _caixa_borrar(rng.random((H, W)).astype(np.float32), 1)
    escorre = _caixa_borrar(escorre.T, 30).T
    escorre = (escorre - escorre.min()) / max(1e-6, float(np.ptp(escorre)))
    suja = _suave((escorre - 0.6) * 4) * (1 - ys / H) ** 1.5
    a = np.maximum(a, suja * 0.3)
    # canto rasgado (embaixo à direita): mostra o papel branco velho de baixo
    rasgo = ((xs - W) ** 2 / (W * 0.16) ** 2 + (ys - H) ** 2 / (H * 0.22) ** 2) < 1 + 0.25 * np.sin(xs * 0.05) * np.cos(ys * 0.07)
    a[rasgo] = 1
    cor[rasgo] = _c("#d8d2c0") * (0.8 + 0.2 * _ruido(H, W, 4, rng)[rasgo][:, None])
    cor[~rasgo] = cor[~rasgo] * 0.4 + np.array([0.05, 0.04, 0.03])
    return _rgba(np.clip(cor, 0, 1), np.clip(a, 0, 1))


def _concreto(lado=256):
    rng = _rng("concreto")
    n = _ruido(lado, lado, 3, rng) * 0.5 + _ruido(lado, lado, 14, rng) * 0.5
    return _rgb_img(_c("#4a4c50") * (0.7 + 0.45 * n[..., None]))


def _asfalto(lado=256):
    rng = _rng("asfalto")
    n = _ruido(lado, lado, 2, rng)
    cor = _c("#1a1c20") * (0.7 + 0.5 * n[..., None])
    cor[lado // 2 - 3:lado // 2 + 3, :] = _c("#8a8060") * 0.6        # faixa no meio
    return _rgb_img(cor)
