"""
(v0.69) HUD com METAL DE VERDADE — a interface da mesa (botões, barra de ferramentas, títulos e molduras dos
painéis, abas, menus, sliders, caixinhas de marcar, barras de rolagem) com as mesmas peças de metal da tela
inicial (`estilizado.metal`: reflexo de verdade, não degradê de plástico).

Cada peça é uma imagem pequena (feita uma vez e guardada no disco) usada pelo QSS como `border-image`
(9 fatias: as quinas ficam do tamanho certo, o meio estica ou repete). As imagens saem no DOBRO (nítidas em
tela com zoom do Windows); a fatia em pixels de imagem = 2 × a borda em pixels de tela.

O exagero segue os Gráficos (decisão do Manel):
  Baixo = o QSS liso de sempre · Médio = moldura de metal fina · Alto = metal mais grosso, ornamentos
  (losangos, gemas, rebites, cantoneiras) e brilho ao passar o mouse.
Claro e Escuro são os temas "de programa" (neutros): ficam lisos.
Cada tema tem o seu jeito: forma do canto (ponta/chanfro/redondo, a mesma dos botões da tela inicial),
ferrugem (Terror, Pós-apocalíptico), linha de neon (Futurista), gemas acesas (Mágico), rebites (Steampunk).
"""

import os

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QBrush, QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen,
                         QRadialGradient)

from . import estilizado as E

VERSAO = "1"           # suba quando mudar um desenho (as imagens guardadas são refeitas)
K = 2                  # as imagens saem no dobro
NEUTROS = ("claro", "escuro")

# forma do canto · ornamento (Alto) · acabamento
JEITO = {
    "medieval": ("ponta", "losango", None),
    "terror": ("ponta", "prego", "ferrugem"),
    "futurista": ("chanfro", "neon", None),
    "moderno": ("redondo", "parafuso", None),
    "magico": ("ponta", "gema", None),
    "steampunk": ("redondo", "rebite", None),
    "posapoc": ("chanfro", "prego", "ferrugem"),
}


# ====================================================================== utilidades
def _pasta():
    from PyQt6.QtCore import QStandardPaths
    docs = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    pasta = os.path.join(docs or os.path.expanduser("~"), "Taverna", "cache", f"hud_v{VERSAO}")
    try:
        os.makedirs(pasta, exist_ok=True)
    except OSError:
        return None
    return pasta


def _cor(h, alfa=None):
    c = QColor(h)
    if alfa is not None:
        c.setAlphaF(alfa)
    return c


def _mix(a, b, f):
    ca, cb = QColor(a), QColor(b)
    return QColor(int(ca.red() + (cb.red() - ca.red()) * f), int(ca.green() + (cb.green() - ca.green()) * f),
                  int(ca.blue() + (cb.blue() - ca.blue()) * f))


def _contorno(forma, r: QRectF, c):
    """Caminho da peça: c = tamanho do canto (px de imagem)."""
    x0, y0, x1, y1 = r.left(), r.top(), r.right(), r.bottom()
    cam = QPainterPath()
    if forma == "chanfro":
        cam.moveTo(x0 + c, y0)
        cam.lineTo(x1 - c * 0.35, y0)
        cam.lineTo(x1, y0 + c * 0.35)
        cam.lineTo(x1, y1 - c)
        cam.lineTo(x1 - c, y1)
        cam.lineTo(x0 + c * 0.35, y1)
        cam.lineTo(x0, y1 - c * 0.35)
        cam.lineTo(x0, y0 + c)
        cam.closeSubpath()
    elif forma == "redondo":
        cam.addRoundedRect(r, c, c)
    else:   # "ponta": cantos levemente cortados (as pontas de losango ficam pros ornamentos)
        k = c * 0.45
        cam.moveTo(x0 + k, y0)
        cam.lineTo(x1 - k, y0)
        cam.lineTo(x1, y0 + k)
        cam.lineTo(x1, y1 - k)
        cam.lineTo(x1 - k, y1)
        cam.lineTo(x0 + k, y1)
        cam.lineTo(x0, y1 - k)
        cam.lineTo(x0, y0 + k)
        cam.closeSubpath()
    return cam


def _ferrugem(camada, tema, forca=0.55):
    """Manchas de ferrugem/sujeira no metal (Terror, Pós-apocalíptico)."""
    H, W = camada.shape[:2]
    import zlib
    rng = np.random.default_rng(zlib.crc32(f"{tema}{H}x{W}".encode()))
    n = E._caixa_borrar(rng.random((H, W)).astype(np.float32), 2)
    n = (n - n.min()) / max(1e-6, n.max() - n.min())
    mancha = np.clip((n - 0.45) * 3.0, 0, 1) * forca
    ferr = np.array([0.36, 0.16, 0.06], np.float32)
    a = camada[..., 3:4]
    camada[..., :3] = camada[..., :3] * (1 - mancha[..., None]) + ferr * a * mancha[..., None]
    return camada


def _ornamento(q, tipo, cx, cy, s):
    """Desenha (na máscara do metal, branco) um ornamento pequeno centrado em (cx, cy)."""
    q.setPen(Qt.PenStyle.NoPen)
    q.setBrush(QColor(255, 255, 255))
    if tipo in ("losango", "gema"):
        p = QPainterPath()
        p.moveTo(cx, cy - s)
        p.lineTo(cx + s * 0.8, cy)
        p.lineTo(cx, cy + s)
        p.lineTo(cx - s * 0.8, cy)
        p.closeSubpath()
        q.drawPath(p)
    elif tipo in ("rebite", "prego", "parafuso"):
        q.drawEllipse(QPointF(cx, cy), s * 0.62, s * 0.62)


def _gema(p, cx, cy, s, cor, nivel):
    """Gema acesa (Mágico) / LED (Futurista) por cima do metal."""
    if nivel == 2:
        g = QRadialGradient(QPointF(cx, cy), s * 2.4)
        c0 = _cor(cor, 0.55)
        c1 = _cor(cor, 0.0)
        g.setColorAt(0, c0)
        g.setColorAt(1, c1)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), s * 2.4, s * 2.4)
    g = QRadialGradient(QPointF(cx - s * 0.25, cy - s * 0.3), s)
    g.setColorAt(0, QColor(255, 255, 255))
    g.setColorAt(0.35, _cor(cor))
    g.setColorAt(1, _mix(cor, "#000000", 0.55))
    p.setBrush(QBrush(g))
    p.drawEllipse(QPointF(cx, cy), s * 0.55, s * 0.55)


def _salvar(img: QImage, nome: str) -> str:
    pasta = _pasta()
    if not pasta:
        return ""
    arq = os.path.join(pasta, nome + ".png")
    img.save(arq)
    return arq.replace("\\", "/")


def _caminho(nome):
    pasta = _pasta()
    if not pasta:
        return None
    arq = os.path.join(pasta, nome + ".png")
    return arq.replace("\\", "/") if os.path.exists(arq) else None


def _metal_sobre(img: QImage, desenhar, tema, perfil, brilho=1.0, acab=None):
    W, H = img.width(), img.height()
    m = E._mascara(W, H, desenhar)
    if m.max() <= 0:
        return img
    camada = E.metal(m, tema, K * 0.5, perfil=perfil)
    if brilho != 1.0:
        camada[..., :3] = np.clip(camada[..., :3] * brilho, 0, camada[..., 3:4])
    if acab == "ferrugem":
        camada = _ferrugem(camada, tema)
    return E._compor(img, camada)


# ====================================================================== as peças
def peca_caixa(tema, t, nivel, estado="normal", tipo="botao"):
    """Botão / botão da barra / aba / campo: fundo do tema + aro de metal (9 fatias).
    estado: normal · sobre · apertado · marcado · desligado. tipo: botao · primario · ferramenta · aba."""
    forma, orn, acab = JEITO.get(tema, JEITO["medieval"])
    W, H = 48 * K, 32 * K
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    aro = (1.6 if nivel == 1 else 2.4) * K * (1.3 if tipo == "primario" else 1.0)
    r = QRectF(aro / 2 + 0.5, aro / 2 + 0.5, W - aro - 1, H - aro - 1)
    if tipo == "aba":   # aba: sem aro embaixo (encosta no painel)
        r.setBottom(H + aro * 2)
    c = 7 * K
    cam = _contorno(forma, r, c)
    destaque = t["destaque"]
    # ---- fundo
    if tipo == "ferramenta" and estado == "normal":
        p.end()
        return img   # botão da barra parado: transparente
    alto = _mix(t["painel2"], "#ffffff", 0.07)
    baixo = _mix(t["painel2"], "#000000", 0.28)
    if tipo == "primario" or estado == "marcado":
        alto, baixo = _mix(t["selecao"], destaque, 0.28), _mix(t["selecao"], "#000000", 0.2)
    if estado == "apertado":
        alto, baixo = baixo, alto
    if estado == "desligado":
        alto, baixo = _mix(t["painel"], "#000000", 0.05), _mix(t["painel"], "#000000", 0.2)
    g = QLinearGradient(QPointF(0, r.top()), QPointF(0, r.bottom()))
    g.setColorAt(0, alto)
    g.setColorAt(1, baixo)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(g))
    p.drawPath(cam)
    if estado in ("sobre", "marcado") and nivel == 2:   # véu de luz por dentro
        v = QRadialGradient(QPointF(W / 2, r.bottom()), W * 0.7)
        v.setColorAt(0, _cor(destaque, 0.32 if estado == "sobre" else 0.22))
        v.setColorAt(1, _cor(destaque, 0.0))
        p.setBrush(QBrush(v))
        p.drawPath(cam)
    # brilhozinho de vidro em cima (dá volume)
    vidro = QLinearGradient(QPointF(0, r.top()), QPointF(0, r.top() + H * 0.45))
    vidro.setColorAt(0, QColor(255, 255, 255, 26 if nivel == 2 else 16))
    vidro.setColorAt(1, QColor(255, 255, 255, 0))
    p.setBrush(QBrush(vidro))
    p.drawPath(cam)
    p.end()
    if estado == "desligado":
        brilho = 0.55
    else:
        brilho = {"sobre": 1.22, "marcado": 1.12, "apertado": 0.85}.get(estado, 1.0)

    def desenhar(q):
        q.setBrush(Qt.BrushStyle.NoBrush)
        q.setPen(QPen(QColor(255, 255, 255), aro))
        q.drawPath(cam)
        if nivel == 2 and tipo in ("primario",):
            q.setPen(QPen(QColor(255, 255, 255), 0.9 * K))
            q.drawPath(_contorno(forma, r.adjusted(3.2 * K, 3.2 * K, -3.2 * K, -3.2 * K), c * 0.7))
        if nivel == 2 and orn in ("rebite", "prego", "parafuso") and tipo != "aba":
            for cx in (r.left() + 4.6 * K, r.right() - 4.6 * K):
                for cy in (r.top() + 4.6 * K, r.bottom() - 4.6 * K):
                    _ornamento(q, orn, cx, cy, 1.9 * K)
        if nivel == 2 and orn in ("losango", "gema") and tipo in ("primario", "botao"):
            for cx in (r.left(), r.right()):
                _ornamento(q, "losango", cx, r.center().y(), 3.2 * K)
    img = _metal_sobre(img, desenhar, tema, 1.4 if nivel == 1 else 2.0, brilho, acab)
    if orn in ("neon", "gema") and estado != "desligado" and (nivel == 2 or estado in ("sobre", "marcado")):
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if orn == "neon":   # linha de luz embaixo, por dentro do aro
            forte = estado in ("sobre", "marcado") or tipo == "primario"
            for larg, a in ((5 * K, 0.10), (2.6 * K, 0.22), (1.0 * K, 0.95 if forte else 0.45)):
                p.setPen(QPen(_cor(destaque, a), larg, cap=Qt.PenCapStyle.RoundCap))
                y = r.bottom() - aro - 1.6 * K
                p.drawLine(QPointF(r.left() + c, y), QPointF(r.right() - c, y))
        elif tipo in ("primario", "botao") and nivel == 2:
            for cx in (r.left(), r.right()):
                _gema(p, cx, r.center().y(), 2.4 * K, destaque, nivel)
        p.end()
    return img


def peca_barra(tema, t, nivel, lado="baixo"):
    """Barra de ferramentas / menu / status: placa escura com trilho de metal (com rebites no Alto).
    A imagem REPETE na horizontal, então os rebites ficam espaçados certinho."""
    forma, orn, acab = JEITO.get(tema, JEITO["medieval"])
    W, H = 64 * K, 24 * K
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    g = QLinearGradient(QPointF(0, 0), QPointF(0, H))
    topo, fundo = _mix(t["painel"], "#ffffff", 0.05), _mix(t["painel"], "#000000", 0.25)
    if lado == "cima":
        topo, fundo = fundo, topo
    g.setColorAt(0, topo)
    g.setColorAt(1, fundo)
    p.fillRect(img.rect(), QBrush(g))
    p.end()
    trilho = (2.2 if nivel == 1 else 3.6) * K
    y = H - trilho / 2 - 0.5 if lado == "baixo" else trilho / 2 + 0.5

    def desenhar(q):
        q.setPen(QPen(QColor(255, 255, 255), trilho, cap=Qt.PenCapStyle.FlatCap))
        q.drawLine(QPointF(-4, y), QPointF(W + 4, y))
        if nivel == 2:
            q.setPen(QPen(QColor(255, 255, 255), 0.8 * K, cap=Qt.PenCapStyle.FlatCap))
            y2 = y - (trilho + 2.2 * K) * (1 if lado == "baixo" else -1)
            q.drawLine(QPointF(-4, y2), QPointF(W + 4, y2))
            if orn in ("rebite", "prego", "parafuso", "losango", "gema"):
                _ornamento(q, "losango" if orn in ("losango", "gema") else orn, W / 2, y, trilho * 0.85)
    img = _metal_sobre(img, desenhar, tema, 1.2 if nivel == 1 else 1.8, 1.0, acab)
    if orn == "neon":
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        yy = y - (trilho / 2 + 1.4 * K) * (1 if lado == "baixo" else -1)
        for larg, a in ((4 * K, 0.10), (1.0 * K, 0.7)):
            p.setPen(QPen(_cor(t["destaque"], a), larg))
            p.drawLine(QPointF(0, yy), QPointF(W, yy))
        p.end()
    return img


def peca_titulo(tema, t, nivel):
    """Título do painel: placa com trilho de metal embaixo e uma ponta ornamentada à esquerda.
    Fatias: esquerda 22 px (ornamento), direita 6, o meio repete."""
    forma, orn, acab = JEITO.get(tema, JEITO["medieval"])
    W, H = 96 * K, 30 * K
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    g = QLinearGradient(QPointF(0, 0), QPointF(0, H))
    g.setColorAt(0, _mix(t["painel2"], "#ffffff", 0.06))
    g.setColorAt(1, _mix(t["painel"], "#000000", 0.2))
    p.fillRect(img.rect(), QBrush(g))
    # um véu da cor do tema saindo da ponta (Alto)
    if nivel == 2:
        v = QLinearGradient(QPointF(0, 0), QPointF(W * 0.6, 0))
        v.setColorAt(0, _cor(t["destaque"], 0.16))
        v.setColorAt(1, _cor(t["destaque"], 0.0))
        p.fillRect(img.rect(), QBrush(v))
    p.end()
    trilho = (2.0 if nivel == 1 else 3.0) * K
    yb = H - trilho / 2 - 0.5
    cx, cy = 11 * K, H / 2

    def desenhar(q):
        q.setPen(QPen(QColor(255, 255, 255), trilho, cap=Qt.PenCapStyle.FlatCap))
        q.drawLine(QPointF(0, yb), QPointF(W + 4, yb))
        q.setPen(QPen(QColor(255, 255, 255), trilho * 0.9, cap=Qt.PenCapStyle.FlatCap))
        q.drawLine(QPointF(1 + trilho * 0.45, 0), QPointF(1 + trilho * 0.45, H))   # filete em pé na ponta
        if nivel == 2:
            q.setPen(QPen(QColor(255, 255, 255), 0.8 * K))
            q.drawLine(QPointF(cx + 8 * K, yb - trilho - 1.6 * K), QPointF(W + 4, yb - trilho - 1.6 * K))
        tipo = {"neon": "losango", "gema": "losango"}.get(orn, orn if nivel == 2 else "losango")
        _ornamento(q, tipo, cx, cy, (5.5 if nivel == 2 else 4.2) * K)
    img = _metal_sobre(img, desenhar, tema, 1.3 if nivel == 1 else 1.9, 1.0, acab)
    if orn in ("gema", "neon"):
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        _gema(p, cx, cy, 3.0 * K, t["destaque"], nivel)
        p.end()
    return img


def placa_titulo(tema, t, nivel, w, h):
    """(v0.77) Título do painel como uma PLACA inteira, no tamanho exato (w×h px de tela): moldura de metal em volta,
    MEDALHÃO de metal à esquerda (o ícone vai dentro), divisória antes do botão de fechar, rebites/losangos no Alto.
    Devolve (imagem, centro do medalhão, x onde o texto começa, x da divisória) — em px de tela."""
    forma, orn, acab = JEITO.get(tema, JEITO["medieval"])
    W, H = max(8, int(w * K)), max(8, int(h * K))
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    m = 1.2 * K
    r = QRectF(m, m, W - 2 * m, H - 2 * m)
    cam = _contorno(forma, r, 5.5 * K)
    g = QLinearGradient(QPointF(0, r.top()), QPointF(0, r.bottom()))
    g.setColorAt(0, _mix(t["painel2"], "#ffffff", 0.08))
    g.setColorAt(0.5, _mix(t["painel2"], "#000000", 0.05))
    g.setColorAt(1, _mix(t["painel"], "#000000", 0.3))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(g))
    p.drawPath(cam)
    if nivel == 2:   # véu da cor do tema saindo do medalhão
        v = QLinearGradient(QPointF(0, 0), QPointF(W * 0.55, 0))
        v.setColorAt(0, _cor(t["destaque"], 0.2))
        v.setColorAt(1, _cor(t["destaque"], 0.0))
        p.setBrush(QBrush(v))
        p.drawPath(cam)
    # medalhão: fundo escuro afundado (o ícone vai por cima)
    R = H * 0.36
    mc = QPointF(r.left() + H * 0.5, H / 2)
    rg = QRadialGradient(mc - QPointF(R * 0.3, R * 0.3), R * 1.2)
    rg.setColorAt(0, _mix(t["painel"], "#000000", 0.05))
    rg.setColorAt(1, _mix(t["fundo"], "#000000", 0.45))
    p.setBrush(QBrush(rg))
    p.drawEllipse(mc, R, R)
    p.end()
    div_x = W - H * 1.05   # divisória antes do botão de fechar
    aro = (1.5 if nivel == 1 else 2.2) * K

    def desenhar(q):
        q.setBrush(Qt.BrushStyle.NoBrush)
        q.setPen(QPen(QColor(255, 255, 255), aro))
        q.drawPath(cam)
        if nivel == 2:   # filete por dentro da moldura
            q.setPen(QPen(QColor(255, 255, 255), 0.7 * K))
            q.drawPath(_contorno(forma, r.adjusted(2.6 * K, 2.6 * K, -2.6 * K, -2.6 * K), 4 * K))
        q.setPen(QPen(QColor(255, 255, 255), aro * 1.15))
        q.drawEllipse(mc, R, R)                                     # aro do medalhão
        q.setPen(QPen(QColor(255, 255, 255), aro * 0.9, cap=Qt.PenCapStyle.FlatCap))
        q.drawLine(QPointF(div_x, r.top() + 3 * K), QPointF(div_x, r.bottom() - 3 * K))
        if nivel == 2:
            o = orn if orn in ("rebite", "prego", "parafuso") else "losango"
            for cx in (mc.x() + R + 7 * K, div_x - 6 * K):
                for cy in (r.top() + 3.2 * K, r.bottom() - 3.2 * K):
                    _ornamento(q, o, cx, cy, 1.5 * K)
            for cy in (mc.y() - R, mc.y() + R):                     # pontinhas no medalhão
                _ornamento(q, "losango", mc.x(), cy, 2.2 * K)
    img = _metal_sobre(img, desenhar, tema, 1.4 if nivel == 1 else 1.9, 1.0, acab)
    if orn in ("gema", "neon") and nivel == 2:
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for cy in (mc.y() - R, mc.y() + R):
            _gema(p, mc.x(), cy, 1.8 * K, t["destaque"], nivel)
        p.end()
    return img, QPointF(mc.x() / K, mc.y() / K), (mc.x() + R) / K + 7, div_x / K


def peca_moldura(tema, t, nivel, fundo=None, borda=5):
    """Moldura de painel/menu: aro de metal fino com cantoneiras (Alto). Fatias = borda×K; o meio estica."""
    forma, orn, acab = JEITO.get(tema, JEITO["medieval"])
    b = borda * K
    W = H = 64 * K
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    aro = (1.4 if nivel == 1 else 2.0) * K
    r = QRectF(aro / 2 + 0.5, aro / 2 + 0.5, W - aro - 1, H - aro - 1)
    cam = _contorno(forma, r, b * 0.9)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(_cor(fundo or t["painel"]))
    p.drawPath(cam)
    # sombra por dentro do aro (o painel fica "afundado" na moldura)
    for i in range(4):
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(0, 0, 0, 40 - i * 9), K))
        p.drawPath(_contorno(forma, r.adjusted(aro + i * K, aro + i * K, -aro - i * K, -aro - i * K), b * 0.8))
    p.end()

    def desenhar(q):
        q.setBrush(Qt.BrushStyle.NoBrush)
        q.setPen(QPen(QColor(255, 255, 255), aro))
        q.drawPath(cam)
        if nivel == 2:   # cantoneiras em L nos 4 cantos
            s = b * 1.0
            q.setPen(QPen(QColor(255, 255, 255), aro * 1.25, cap=Qt.PenCapStyle.SquareCap))
            for (x, y, dx, dy) in ((r.left(), r.top(), 1, 1), (r.right(), r.top(), -1, 1),
                                   (r.left(), r.bottom(), 1, -1), (r.right(), r.bottom(), -1, -1)):
                x2, y2 = x + dx * aro * 1.2, y + dy * aro * 1.2
                q.drawLine(QPointF(x2, y2), QPointF(x2 + dx * s, y2))
                q.drawLine(QPointF(x2, y2), QPointF(x2, y2 + dy * s))
    return _metal_sobre(img, desenhar, tema, 1.2 if nivel == 1 else 1.6, 1.0, acab)


def peca_redonda(tema, t, nivel, tipo="botao_slider", ligado=False):
    """Peças pequenas de tamanho fixo: botão do slider (16), caixinha de marcar (16), bolinha de rádio (16)."""
    forma, orn, acab = JEITO.get(tema, JEITO["medieval"])
    L = 18 * K
    img = QImage(L, L, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    destaque = t["destaque"]
    if tipo == "caixa":
        r = QRectF(1.5 * K, 1.5 * K, L - 3 * K, L - 3 * K)
        cam = _contorno(forma, r, 4.5 * K)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_cor(_mix(t["fundo"], "#000000", 0.2).name()))
        p.drawPath(cam)
        p.end()

        def desenhar(q):
            q.setBrush(Qt.BrushStyle.NoBrush)
            q.setPen(QPen(QColor(255, 255, 255), 1.6 * K))
            q.drawPath(cam)
            if ligado:   # o "visto" é uma peça de metal
                q.setPen(QPen(QColor(255, 255, 255), 2.4 * K, cap=Qt.PenCapStyle.RoundCap,
                              join=Qt.PenJoinStyle.RoundJoin))
                v = QPainterPath()
                v.moveTo(5.2 * K, 9.4 * K)
                v.lineTo(8 * K, 12.4 * K)
                v.lineTo(13 * K, 5.8 * K)
                q.drawPath(v)
        img = _metal_sobre(img, desenhar, tema, 1.3, 1.1 if ligado else 1.0, acab)
        if ligado and nivel == 2:
            p = QPainter(img)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            v = QRadialGradient(QPointF(L / 2, L / 2), L * 0.5)
            v.setColorAt(0, _cor(destaque, 0.35))
            v.setColorAt(1, _cor(destaque, 0.0))
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOver)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(v))
            p.drawEllipse(QRectF(0, 0, L, L))
            p.end()
        return img
    # botão do slider: um "pino" de metal com a cor do tema no meio
    p.end()
    c = QPointF(L / 2, L / 2)

    def desenhar(q):
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QColor(255, 255, 255))
        if forma == "chanfro" or orn == "losango":
            _ornamento(q, "losango", c.x(), c.y(), L * 0.46)
        else:
            q.drawEllipse(c, L * 0.42, L * 0.42)
    img = _metal_sobre(img, desenhar, tema, 2.6, 1.15 if ligado else 1.0, acab)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    _gema(p, c.x(), c.y(), 3.2 * K, destaque, 1)
    p.end()
    return img


def peca_rolagem(tema, t, nivel, horizontal=False):
    """Alça da barra de rolagem: um bastão de metal (fatias 5×K nas pontas, o meio estica)."""
    forma, orn, acab = JEITO.get(tema, JEITO["medieval"])
    W, H = (40 * K, 10 * K) if horizontal else (10 * K, 40 * K)
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    r = QRectF(1.5 * K, 1.5 * K, W - 3 * K, H - 3 * K)

    def desenhar(q):
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QColor(255, 255, 255))
        q.drawRoundedRect(r, 3 * K, 3 * K)
    return _metal_sobre(img, desenhar, tema, 2.4, 0.8, acab)


# ====================================================================== QSS
def _arq(tema, t, nivel, nome, fazer):
    nome = f"{tema}_{nivel}_{nome}"
    caminho = _caminho(nome)
    if caminho:
        return caminho
    return _salvar(fazer(), nome)


def qss(tema: str, t: dict, nivel: int) -> str:
    """O QSS extra do HUD (vazio no Baixo, nos temas neutros ou se algo falhar)."""
    if nivel < 1 or tema in NEUTROS or tema not in JEITO:
        return ""
    try:
        from PyQt6.QtGui import QGuiApplication
        if QGuiApplication.instance() is None:
            return ""
        return _qss(tema, t, nivel)
    except Exception as erro:   # sem o HUD de metal, fica o liso — nunca quebra a janela
        try:
            from ..seguranca import registrar_erro
            registrar_erro(f"HUD de metal não montou ({tema}): {erro!r}")
        except Exception:
            pass
        return ""


def _qss(tema, t, nivel):
    a = lambda nome, fazer: _arq(tema, t, nivel, nome, fazer)   # noqa: E731
    cx = {e: a(f"botao_{e}", lambda e=e: peca_caixa(tema, t, nivel, e))
          for e in ("normal", "sobre", "apertado", "marcado", "desligado")}
    pr = {e: a(f"primario_{e}", lambda e=e: peca_caixa(tema, t, nivel, e, "primario"))
          for e in ("normal", "sobre", "apertado")}
    fe = {e: a(f"ferr_{e}", lambda e=e: peca_caixa(tema, t, nivel, e, "ferramenta"))
          for e in ("sobre", "apertado", "marcado")}
    ab = {e: a(f"aba_{e}", lambda e=e: peca_caixa(tema, t, nivel, e, "aba")) for e in ("normal", "marcado")}
    barra = a("barra", lambda: peca_barra(tema, t, nivel, "baixo"))
    barra_cima = a("barra_cima", lambda: peca_barra(tema, t, nivel, "cima"))
    from PyQt6.QtGui import QTransform
    lado_esq = a("barra_esq", lambda: peca_barra(tema, t, nivel, "baixo").transformed(QTransform().rotate(-90)))
    lado_dir = a("barra_dir", lambda: peca_barra(tema, t, nivel, "baixo").transformed(QTransform().rotate(90)))
    titulo = a("titulo", lambda: peca_titulo(tema, t, nivel))
    moldura = a("moldura", lambda: peca_moldura(tema, t, nivel))
    menu = a("menu", lambda: peca_moldura(tema, t, nivel, t["painel"], 6))
    pino = a("pino", lambda: peca_redonda(tema, t, nivel))
    pino_sobre = a("pino_sobre", lambda: peca_redonda(tema, t, nivel, ligado=True))
    caixa = a("caixa", lambda: peca_redonda(tema, t, nivel, "caixa"))
    caixa_ok = a("caixa_ok", lambda: peca_redonda(tema, t, nivel, "caixa", True))
    rol_v = a("rol_v", lambda: peca_rolagem(tema, t, nivel))
    rol_h = a("rol_h", lambda: peca_rolagem(tema, t, nivel, True))
    B = 5            # borda dos botões em px de tela (fatia = B×K na imagem)
    s = B * K
    dest, texto = t["destaque"], t["texto"]
    fonte_painel = t.get("fonte_painel", t["fonte_titulo"])   # (v0.77) o menu na fonte dos títulos do tema
    espaco_menu = max(0.5, min(2.0, float(t.get("espaco_painel", 1)) * 0.5))

    def bi(url, f, fd=None, rep="stretch stretch"):
        """border-image com fatias f (px de imagem); borda na tela = f/K."""
        fd = fd or (f, f, f, f)
        return (f"border-image: url({url}) {fd[0]} {fd[1]} {fd[2]} {fd[3]} {rep}; "
                f"border-width: {fd[0] // K}px {fd[1] // K}px {fd[2] // K}px {fd[3] // K}px;")

    return f"""
/* ===== HUD de metal (v0.69) ===== */
QToolBar {{ {bi(barra, 0, (0, 0, 8 * K, 0), "repeat stretch")} background: transparent; }}
QToolBar:left {{ {bi(lado_esq, 0, (0, 8 * K, 0, 0), "stretch repeat")} }}
QToolBar:right {{ {bi(lado_dir, 0, (0, 0, 0, 8 * K), "stretch repeat")} }}
QToolBar:bottom {{ {bi(barra_cima, 0, (8 * K, 0, 0, 0), "repeat stretch")} }}
QMenuBar {{ {bi(barra, 0, (0, 0, 6 * K, 0), "repeat stretch")} background: transparent; padding: 1px 6px 0px 6px; }}
QMenuBar::item {{ {bi(cx["normal"], s)} padding: 0px 7px; margin: 2px 2px 3px 2px; background: transparent;
    font-family: {fonte_painel}; letter-spacing: {espaco_menu}px; color: {texto}; }}
QMenuBar::item:selected {{ {bi(fe["sobre"], s)} color: {dest}; }}
QMenuBar::item:pressed {{ {bi(fe["marcado"], s)} color: {dest}; }}
QStatusBar {{ {bi(barra_cima, 0, (6 * K, 0, 0, 0), "repeat stretch")} background: transparent; }}
QDockWidget::title {{ {bi(titulo, 0, (0, 6 * K, 6 * K, 22 * K), "repeat stretch")}
    padding: 2px 6px 1px 4px; background: transparent; }}
QDockWidget > QWidget {{ {bi(moldura, 5 * K)} background: transparent; }}

QPushButton {{ {bi(cx["normal"], s)} padding: 1px 8px; background: transparent; }}
QPushButton:hover {{ border-image: url({cx["sobre"]}) {s} {s} {s} {s} stretch stretch; color: {dest}; }}
QPushButton:pressed {{ border-image: url({cx["apertado"]}) {s} {s} {s} {s} stretch stretch; }}
QPushButton:checked {{ border-image: url({cx["marcado"]}) {s} {s} {s} {s} stretch stretch; color: {dest}; }}
QPushButton:disabled {{ border-image: url({cx["desligado"]}) {s} {s} {s} {s} stretch stretch; }}
QPushButton#primario {{ border-image: url({pr["normal"]}) {s} {s} {s} {s} stretch stretch; color: {texto}; }}
QPushButton#primario:hover {{ border-image: url({pr["sobre"]}) {s} {s} {s} {s} stretch stretch; color: #ffffff; }}
QPushButton#primario:pressed {{ border-image: url({pr["apertado"]}) {s} {s} {s} {s} stretch stretch; }}

QToolBar QToolButton {{ border: {B}px solid transparent; background: transparent; padding: 0px 2px; }}
QToolBar QToolButton:hover {{ {bi(fe["sobre"], s)} color: {dest}; }}
QToolBar QToolButton:pressed {{ {bi(fe["apertado"], s)} }}
QToolBar QToolButton:checked {{ {bi(fe["marcado"], s)} color: {dest}; }}
QToolBar#barra_ferramentas QToolButton {{ padding: 0px 2px; }}
QToolBar#barra_ferramentas QToolButton#primario {{ {bi(pr["normal"], s)} padding: 0px 7px; color: {texto}; }}
QToolBar#barra_ferramentas QToolButton#primario:hover {{ {bi(pr["sobre"], s)} color: #ffffff; }}
QToolButton#primario {{ {bi(pr["normal"], s)} padding: 1px 5px; color: {texto}; }}
QToolButton#primario:hover {{ {bi(pr["sobre"], s)} color: #ffffff; }}

QTabBar::tab {{ {bi(ab["normal"], s, (s, s, 0, s))} padding: 1px 10px 4px 10px; margin-right: 2px;
    background: transparent; }}
QTabBar::tab:selected {{ {bi(ab["marcado"], s, (s, s, 0, s))} color: {dest}; }}

QMenu {{ {bi(menu, 6 * K)} padding: 2px; background: transparent; }}
QComboBox QAbstractItemView {{ {bi(menu, 6 * K)} }}

QSlider::handle:horizontal {{ image: url({pino}); background: transparent; width: 18px; height: 18px;
    margin: -7px 0; border: none; }}
QSlider::handle:horizontal:hover {{ image: url({pino_sobre}); background: transparent; }}
QCheckBox::indicator, QGroupBox::indicator {{ image: url({caixa}); background: transparent; border: none;
    width: 17px; height: 17px; }}
QTreeView::indicator, QListView::indicator {{ image: url({caixa}); background: transparent; border: none;
    width: 15px; height: 15px; }}
QTreeView::indicator:checked, QListView::indicator:checked {{ image: url({caixa_ok}); }}
QCheckBox::indicator:checked, QGroupBox::indicator:checked {{ image: url({caixa_ok}); background: transparent; }}
QScrollBar::handle:vertical {{ {bi(rol_v, 5 * K)} background: transparent; min-height: 28px; }}
QScrollBar::handle:horizontal {{ {bi(rol_h, 5 * K)} background: transparent; min-width: 28px; }}
"""

# ====================================================================== pra quem desenha na mão (título do painel)
_PM = {}


def ativo():
    """(tema, t, nível) se o HUD de metal está valendo agora; senão None."""
    from ..graficos import nivel
    from . import tema as _t
    n = nivel()
    if n < 1 or _t._ATUAL in NEUTROS or _t._ATUAL not in JEITO:
        return None
    return _t._ATUAL, _t.tema_atual(), n


def pixmap(nome):
    """A peça do tema/nível atual como QPixmap (None se o HUD de metal estiver desligado)."""
    from PyQt6.QtGui import QPixmap
    a = ativo()
    if a is None:
        return None
    tema, t, n = a
    chave = (tema, n, nome)
    if chave not in _PM:
        fazer = {"titulo": lambda: peca_titulo(tema, t, n)}[nome]
        caminho = _arq(tema, t, n, nome, fazer)
        pm = QPixmap(caminho) if caminho else QPixmap.fromImage(fazer())
        _PM[chave] = pm if not pm.isNull() else None
    return _PM[chave]


def desenhar_faixa(p: QPainter, alvo: QRectF, pm, esq: int, dir_: int):
    """Desenha a peça esticando só na horizontal: ponta esquerda (esq px de tela), meio repetido, ponta direita.
    A imagem está no dobro (K)."""
    from PyQt6.QtCore import QRectF as R
    h = alvo.height()
    sy = pm.height() / h
    p.drawPixmap(R(alvo.left(), alvo.top(), esq, h), pm, R(0, 0, esq * K, pm.height()))
    p.drawPixmap(R(alvo.right() - dir_, alvo.top(), dir_, h), pm, R(pm.width() - dir_ * K, 0, dir_ * K, pm.height()))
    meio_src = R(esq * K, 0, pm.width() - (esq + dir_) * K, pm.height())
    passo = meio_src.width() / sy
    x = alvo.left() + esq
    fim = alvo.right() - dir_
    while x < fim:
        larg = min(passo, fim - x)
        p.drawPixmap(R(x, alvo.top(), larg, h), pm, R(meio_src.left(), 0, larg * sy, pm.height()))
        x += larg
