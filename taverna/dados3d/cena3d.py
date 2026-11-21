"""
O que os dois desenhos (OpenGL e plano B) compartilham: câmera, material de cada tema,
a textura com os números de cada face e a preparação de uma rolagem.
"""

import math

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QPolygonF

from .fisica import QUADROS_POR_SEG, q_matriz, q_slerp, renumerar, simular
from .geometria import solido

CELULA = 128          # pixels de cada face na textura dos números
TAMANHO_DADO = 1.0
# A área onde os dados rolam é FIXA (igual em todos os PCs → mesmo quique pra todo mundo).
# Só a câmera se ajusta ao tamanho da janela de cada um. Menor = dados maiores na tela.
ARENA_L = 7.6          # metade da largura
ARENA_A = 4.4          # metade da altura

# material por tema: corpo, número, brilho (0–1), "gema" (translúcido/brilhante)
MATERIAIS = {
    "medieval":  ("#e8dcc0", "#3a2414", 0.35, False),   # osso
    "moderno":   ("#f2f2f0", "#1c1c1e", 0.55, False),   # plástico branco
    "futurista": ("#18b8e8", "#f4fdff", 0.9, True),     # vidro ciano
    "magico":    ("#6a3ab8", "#ffd86a", 0.85, True),    # ametista com ouro
    "terror":    ("#5e0a12", "#e8dcc0", 0.6, False),    # vermelho sangue, números de osso
    "steampunk": ("#a8823a", "#2a1c06", 0.9, False),    # latão envelhecido, número gravado fundo (v0.59)
    "posapoc":   ("#c8b278", "#f4f0e4", 0.0, False),   # plástico amarelo desbotado e fosco (v0.59)
    "claro":     ("#f4ecd8", "#6a3a10", 0.4, False),
    "escuro":    ("#2a2d33", "#7c9cff", 0.7, False),
}


def material(tema: str):
    corpo, numero, brilho, gema = MATERIAIS.get(tema, MATERIAIS["medieval"])
    return QColor(corpo), QColor(numero), brilho, gema


# (v0.59) DETALHE/DESGASTE por cima do corpo do dado, em TODOS os temas: uma textura que MULTIPLICA a cor
# (0,5 = igual; menos = escurece, mais = clareia). Cobre 4×4 faces e repete.
#   medieval: osso amarelado, poros e trincas finas · moderno: plástico com leve marmorizado
#   futurista: trilhas de circuito acesas dentro do vidro · mágico: veios e nuvens na ametista
#   terror: sangue seco respingado e arranhões · steampunk: pátina verde e riscos de polimento
#   pós-apocalíptico: desbotado, sujeira, arranhões e FITA ISOLANTE · claro/escuro: grão discreto
DESGASTE = {"medieval", "moderno", "futurista", "magico", "terror", "steampunk", "posapoc", "claro", "escuro",
            "pedra", "marmore", "madeira", "ferro", "polido"}   # (v0.74: + os materiais dos "Meus dados")
_DESGASTE_CACHE = {}


def textura_desgaste(tema: str):
    """QImage 512×512 (RGB = multiplicador/2) ou None se o tema não tem desgaste."""
    if tema not in DESGASTE:
        return None
    if tema in _DESGASTE_CACHE:
        return _DESGASTE_CACHE[tema]
    import zlib
    from PyQt6.QtGui import QPen
    n = 512
    rng = np.random.default_rng(zlib.crc32(tema.encode()))

    def ruido(escala):
        base = rng.random((n // escala + 2, n // escala + 2)).astype(np.float32)
        r = np.kron(base, np.ones((escala, escala), np.float32))[:n, :n]
        k = np.ones(escala, np.float32) / escala   # (suaviza)
        r = np.apply_along_axis(lambda v: np.convolve(v, k, "same"), 0, r)
        return np.apply_along_axis(lambda v: np.convolve(v, k, "same"), 1, r)

    def mancha(escala, corte, forca):
        return np.clip((ruido(escala) - corte) * 4, 0, 1) * forca

    mult = np.ones((n, n, 3), np.float32)
    if tema == "steampunk":
        m = mancha(24, 0.63, 0.7)
        mult = mult * (1 - m[..., None]) + np.array([0.62, 0.86, 0.80], np.float32) * m[..., None]
        mult *= (0.9 + 0.2 * ruido(6))[..., None]
    elif tema == "posapoc":
        mult *= (0.8 + 0.3 * ruido(10))[..., None]
        mult *= (1 - 0.45 * mancha(20, 0.6, 1))[..., None]
    elif tema == "medieval":
        m = mancha(30, 0.5, 0.6)                                            # amarelado do osso velho
        mult = mult * (1 - m[..., None]) + np.array([1.0, 0.9, 0.7], np.float32) * m[..., None]
        mult *= (0.92 + 0.1 * ruido(4))[..., None]
    elif tema == "moderno":
        mult *= (0.94 + 0.08 * np.sin(ruido(40) * 18))[..., None]          # marmorizado leve
    elif tema == "futurista":
        mult *= (0.85 + 0.2 * ruido(30))[..., None]
    elif tema == "magico":
        m = mancha(36, 0.45, 0.5)                                           # nuvens dentro da pedra
        mult = mult * (1 - m[..., None]) + np.array([1.35, 1.2, 1.5], np.float32) * m[..., None]
        mult *= (0.85 + 0.25 * ruido(12))[..., None]
    elif tema == "terror":
        mult *= (0.85 + 0.2 * ruido(14))[..., None]
    elif tema == "pedra":                                                   # grão de pedra + manchas
        mult *= (0.82 + 0.3 * ruido(3))[..., None]
        mult *= (0.9 + 0.2 * ruido(28))[..., None]
    elif tema == "marmore":                                                 # veios escuros ondulando
        veio = np.abs(np.sin(ruido(48) * 22 + ruido(12) * 4))
        mult *= (0.72 + 0.3 * np.clip(veio * 1.6, 0, 1))[..., None]
    elif tema == "madeira":                                                 # anéis/veio da madeira
        xs = np.arange(n, dtype=np.float32)[None, :]
        veio = np.sin(xs * 0.12 + ruido(40) * 9 + ruido(8) * 1.5) * 0.5 + 0.5
        mult *= (0.78 + 0.32 * veio)[..., None]
        mult *= (0.92 + 0.1 * ruido(3))[..., None]
    elif tema == "ferro":                                                   # ferrugem em manchas
        m = mancha(18, 0.58, 0.7)
        mult = mult * (1 - m[..., None]) + np.array([1.3, 0.88, 0.58], np.float32) * m[..., None]
        mult *= (0.86 + 0.2 * ruido(5))[..., None]
    elif tema == "polido":                                                  # ouro/prata: quase liso
        mult *= (0.97 + 0.05 * ruido(20))[..., None]
    else:                                                                   # claro / escuro
        mult *= (0.95 + 0.08 * ruido(5))[..., None]
    arr = np.clip(mult * 0.5 * 255, 0, 255).astype(np.uint8)
    rgba = np.dstack([arr, np.full((n, n), 255, np.uint8)])
    img = QImage(rgba.tobytes(), n, n, n * 4, QImage.Format.Format_RGBA8888).copy()
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    def riscos(qtd, cor, larg=(0.6, 1.4), comp=(8, 40)):
        for _ in range(qtd):
            x, y = rng.uniform(0, n), rng.uniform(0, n)
            a = rng.uniform(0, math.pi)
            c = rng.uniform(*comp)
            p.setPen(QPen(QColor(*cor, int(rng.uniform(60, 150))), rng.uniform(*larg)))
            p.drawLine(QPointF(x, y), QPointF(x + math.cos(a) * c, y + math.sin(a) * c))

    def trinca(qtd, cor):
        for _ in range(qtd):
            x, y = rng.uniform(0, n), rng.uniform(0, n)
            a = rng.uniform(0, 2 * math.pi)
            p.setPen(QPen(QColor(*cor), rng.uniform(0.6, 1.2)))
            for _k in range(int(rng.uniform(4, 10))):
                a += rng.uniform(-0.8, 0.8)
                nx, ny = x + math.cos(a) * rng.uniform(4, 10), y + math.sin(a) * rng.uniform(4, 10)
                p.drawLine(QPointF(x, y), QPointF(nx, ny))
                x, y = nx, ny

    if tema in ("steampunk", "posapoc", "terror", "ferro", "polido"):
        riscos({"posapoc": 70, "ferro": 90, "polido": 30}.get(tema, 40), (200, 200, 200))
    if tema == "pedra":                                                     # pontinhos e trincas
        p.setPen(Qt.PenStyle.NoPen)
        for _ in range(500):
            claro = rng.random() < 0.5
            p.setBrush(QColor(235, 230, 220, 120) if claro else QColor(30, 28, 26, 130))
            p.drawEllipse(QPointF(rng.uniform(0, n), rng.uniform(0, n)), rng.uniform(0.6, 1.8), rng.uniform(0.6, 1.8))
        trinca(10, (40, 38, 34, 150))
    if tema == "medieval":
        p.setPen(Qt.PenStyle.NoPen)
        for _ in range(300):                                                # poros do osso
            p.setBrush(QColor(70, 60, 50, int(rng.uniform(60, 140))))
            p.drawEllipse(QPointF(rng.uniform(0, n), rng.uniform(0, n)), rng.uniform(0.6, 1.6), rng.uniform(0.6, 1.6))
        trinca(14, (60, 50, 40, 150))
    if tema == "futurista":                                                 # trilhas de circuito acesas
        p.setPen(QPen(QColor(240, 255, 255, 235), 2.6))
        for _ in range(26):
            x, y = rng.uniform(0, n), rng.uniform(0, n)
            for _k in range(4):
                if rng.random() < 0.5:
                    nx, ny = x + rng.choice([-1, 1]) * rng.uniform(10, 40), y
                else:
                    nx, ny = x, y + rng.choice([-1, 1]) * rng.uniform(10, 40)
                p.drawLine(QPointF(x, y), QPointF(nx, ny))
                x, y = nx, ny
            p.setBrush(QColor(240, 255, 255, 200))
            p.drawEllipse(QPointF(x, y), 3.4, 3.4)
    if tema == "magico":                                                    # veios claros
        trinca(18, (230, 210, 255, 140))
    if tema == "terror":                                                    # sangue seco respingado
        p.setPen(Qt.PenStyle.NoPen)
        for _ in range(16):
            cx, cy = rng.uniform(0, n), rng.uniform(0, n)
            for _k in range(int(rng.uniform(3, 9))):
                p.setBrush(QColor(30, 6, 6, int(rng.uniform(120, 200))))
                r = rng.uniform(1, 6)
                p.drawEllipse(QPointF(cx + rng.normal(0, 8), cy + rng.normal(0, 8)), r, r)
    if tema == "posapoc":                                                   # fita isolante em umas faces
        for cx, cy in ((0, 1), (2, 3), (3, 0), (1, 2), (0, 0)):
            p.save()
            p.translate(cx * 128 + 64, cy * 128 + 64)
            p.rotate(rng.uniform(-35, 35))
            p.fillRect(QRectF(-80, 22, 160, 40), QColor(14, 14, 16))
            p.setPen(QPen(QColor(70, 70, 76), 1))
            p.drawLine(QPointF(-80, 31), QPointF(80, 31))
            p.restore()
    p.end()
    _DESGASTE_CACHE[tema] = img
    return img

# ---------------------------------------------------------------- câmera
_CAMERAS = {}


def camera(largura_px: int, altura_px: int):
    """Igual a _camera, mas guarda o resultado (é chamada a cada quadro)."""
    chave = (int(largura_px), int(altura_px))
    if chave not in _CAMERAS:
        if len(_CAMERAS) > 16:
            _CAMERAS.clear()
        _CAMERAS[chave] = _camera(*chave)
    return _CAMERAS[chave]


def _camera(largura_px: int, altura_px: int):
    """(visão, projeção, metade_largura, metade_altura da arena, posição do olho)."""
    aspecto = max(0.3, largura_px / max(1, altura_px))
    inclinacao = math.radians(28)            # olhando de cima, um pouco inclinado (dá o 3D)
    fov = math.radians(38)
    # afasta a câmera o bastante pra arena caber inteira (pela altura ou pela largura)
    meia_altura_visivel = max(ARENA_A * 1.18, ARENA_L * 1.08 / aspecto)
    dist = meia_altura_visivel / math.tan(fov / 2) + 2
    olho = np.array([0.0, -dist * math.sin(inclinacao), dist * math.cos(inclinacao)])
    alvo = np.array([0.0, 0.0, 0.0])
    cima = np.array([0.0, 1.0, 0.0])
    f = alvo - olho
    f /= np.linalg.norm(f)
    s = np.cross(f, cima)
    s /= np.linalg.norm(s)
    u = np.cross(s, f)
    visao = np.identity(4)
    visao[0, :3], visao[1, :3], visao[2, :3] = s, u, -f
    visao[:3, 3] = -visao[:3, :3] @ olho
    perto, longe = 1.0, dist * 3
    t = 1 / math.tan(fov / 2)
    proj = np.zeros((4, 4))
    proj[0, 0] = t / aspecto
    proj[1, 1] = t
    proj[2, 2] = (longe + perto) / (perto - longe)
    proj[2, 3] = 2 * longe * perto / (perto - longe)
    proj[3, 2] = -1
    return visao, proj, ARENA_L, ARENA_A, olho


def projetar(pts, visao, proj, w, h):
    """Pontos 3D → pixels (x, y) e profundidade."""
    p4 = np.c_[pts, np.ones(len(pts))] @ (proj @ visao).T
    p4 = p4[:, :3] / p4[:, 3:4]
    x = (p4[:, 0] * 0.5 + 0.5) * w
    y = (1 - (p4[:, 1] * 0.5 + 0.5)) * h
    return np.c_[x, y], p4[:, 2]


# ---------------------------------------------------------------- textura dos números
def _uv_da_face(v, face):
    """Coordenadas 2D (no plano da face) de cada vértice, normalizadas pra caber numa célula (0–1)."""
    p = v[face]
    c = p.mean(axis=0)
    n = np.cross(p[1] - p[0], p[2] - p[0])
    n /= np.linalg.norm(n)
    eixo_u = p[0] - c
    eixo_u /= np.linalg.norm(eixo_u)
    eixo_v = np.cross(n, eixo_u)
    # (na imagem o y cresce pra baixo: o eixo "v" da face vai invertido, senão o número sai espelhado)
    uv = np.c_[(p - c) @ eixo_u, -((p - c) @ eixo_v)]
    # gira pra "ponta" ficar pra cima (número em pé dentro da face)
    raio = np.max(np.linalg.norm(uv, axis=1))
    uv = uv / (raio * 2.0) + 0.5
    return uv


def textura_numeros(dados, tema: str, fonte: str):
    """
    Uma QImage com os números de todas as faces de todos os dados desta rolagem.
    `dados`: lista de dicts com "lados", "nums" (número por face/vértice) e "rotulo" (d100: dezenas).
    Devolve (imagem, uv_por_dado) onde uv_por_dado[i][j] = coordenadas UV (no atlas) dos vértices da face j.
    """
    total = sum(len(solido(d["lados"])[1]) for d in dados)
    colunas = max(1, math.ceil(math.sqrt(total)))
    linhas = math.ceil(total / colunas)
    img = QImage(colunas * CELULA, linhas * CELULA, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    p.setPen(QColor(255, 255, 255))
    uv_por_dado = []
    k = 0
    for d in dados:
        v, faces, _, _ = solido(d["lados"])
        uvs = []
        for j, face in enumerate(faces):
            cx, cy = (k % colunas) * CELULA, (k // colunas) * CELULA
            uv = _uv_da_face(v, face)
            pts = [QPointF(cx + a * CELULA, cy + b * CELULA) for a, b in uv]
            centro = QPointF(cx + CELULA / 2, cy + CELULA / 2)
            if d["lados"] == 4:   # d4: o número de cada vértice, perto da quina
                f = QFont(fonte)
                f.setPixelSize(int(CELULA * 0.2))
                f.setBold(True)
                p.setFont(f)
                for vi, pt in zip(face, pts):
                    alvo = centro + (pt - centro) * 0.62
                    p.save()
                    p.translate(alvo)
                    ang = math.degrees(math.atan2(pt.y() - centro.y(), pt.x() - centro.x())) + 90
                    p.rotate(ang)
                    p.drawText(QRectF(-CELULA * 0.15, -CELULA * 0.12, CELULA * 0.3, CELULA * 0.24),
                               Qt.AlignmentFlag.AlignCenter, str(d["nums"][vi]))
                    p.restore()
            else:
                texto = _texto_face(d, j)
                f = QFont(fonte)
                lados = d["lados"]
                f.setPixelSize(int(CELULA * {6: 0.42, 8: 0.32, 10: 0.26, 12: 0.3, 20: 0.24}.get(lados, 0.3)
                                   * (0.8 if len(texto) > 2 else 1)))
                f.setBold(True)
                p.setFont(f)
                desloc = QPointF(0, CELULA * 0.06) if lados == 10 else QPointF(0, 0)
                ret = QRectF(centro.x() - CELULA * 0.3, centro.y() - CELULA * 0.2, CELULA * 0.6, CELULA * 0.4)
                p.drawText(ret.translated(desloc), Qt.AlignmentFlag.AlignCenter, texto)
                if texto in ("6", "9") and lados > 6:   # risquinho pra não confundir 6 e 9
                    m = p.fontMetrics()
                    larg = m.horizontalAdvance(texto)
                    y = centro.y() + m.ascent() * 0.55 + desloc.y()
                    p.fillRect(QRectF(centro.x() - larg / 2, y, larg, max(2, CELULA * 0.022)), QColor(255, 255, 255))
            uvs.append([((cx + a * CELULA) / img.width(), (cy + b * CELULA) / img.height()) for a, b in uv])
            k += 1
        uv_por_dado.append(uvs)
    p.end()
    return img, uv_por_dado


def _texto_face(d, j):
    n = d["nums"][j]
    if d.get("dezena"):     # d100: o dado das dezenas mostra 00, 10, … 90
        return f"{n}0" if n else "00"
    return str(n)


# ---------------------------------------------------------------- uma rolagem
class Rolagem:
    """Tudo que precisa pra mostrar uma rolagem: dados, quadros da física, números e textura."""

    def __init__(self, r: dict, largura_px: int, altura_px: int, tema: str, fonte: str):
        self.r = r
        self.tema = tema
        from .visual import resolver   # (v0.74) os dados de quem ROLOU (cor/material que ele escolheu)
        self.corpo, self.cor_num, self.brilho, self.gema, self.desgaste, self.metal = resolver(r.get("dv"), tema)
        _, _, L, A, _ = camera(largura_px, altura_px)
        self.dados = []
        for f in r.get("fisicos") or []:
            lados, valor = int(f.get("lados", 0)), int(f.get("valor", 0))
            if lados == 100:   # d%: dois d10 (dezenas e unidades); 100 = "00" + "0"
                self.dados.append({"lados": 10, "valor": (valor // 10) % 10 or 10, "dezena": True, "fora": f.get("fora")})
                self.dados.append({"lados": 10, "valor": valor % 10 or 10, "fora": f.get("fora")})
            elif lados in (4, 6, 8, 10, 12, 20):
                self.dados.append({"lados": lados, "valor": valor, "fora": f.get("fora")})
            if len(self.dados) >= 10:
                break
        self.dados = self.dados[:10]
        self.quadros, finais = simular([d["lados"] for d in self.dados], int(r.get("semente") or 1), L, A,
                                       TAMANHO_DADO)
        for d, fim in zip(self.dados, finais):
            d["nums"] = renumerar(d["lados"], d["valor"], fim)
        self.imagem, self.uvs = textura_numeros(self.dados, tema, fonte)
        self.duracao = len(self.quadros) / QUADROS_POR_SEG
        # v0.45.2: o d20 que VALEU deu 20 ou 1 natural? (o descartado na vantagem não conta)
        self.critico = None   # (índice do dado, 20 ou 1)
        natural = r.get("d20")
        if natural in (1, 20):
            for i, d in enumerate(self.dados):
                if d["lados"] == 20 and d["valor"] == natural and not d.get("fora"):
                    self.critico = (i, natural)
                    break

    def quadro(self, t: float):
        """Posições/rotações no tempo t (s), INTERPOLADAS entre os quadros da física (animação lisa
        em qualquer taxa do monitor). Depois do fim, fica no último quadro (e o d20 crítico dá um
        pulinho; o da falha treme)."""
        if not self.quadros:
            return []
        x = max(0.0, t * QUADROS_POR_SEG)
        i = int(x)
        if i >= len(self.quadros) - 1:
            final = self.quadros[-1]
            if self.critico is None:
                return final
            k, valor = self.critico
            dt = t - self.duracao
            p, q = final[k]
            if valor == 20 and 0.0 <= dt < 0.45:     # pulinho de alegria
                s = dt / 0.45
                p = p + np.array([0.0, 0.0, 4 * s * (1 - s) * TAMANHO_DADO * 0.9])
            elif valor == 1 and 0.0 <= dt < 0.7:     # treme de vergonha
                amort = 1 - dt / 0.7
                p = p + np.array([math.sin(dt * 70) * 0.09 * amort, math.cos(dt * 53) * 0.04 * amort, 0.0])
            else:
                return final
            final = list(final)
            final[k] = (p, q)
            return final
        f = x - i
        a, b = self.quadros[i], self.quadros[i + 1]
        return [(pa + (pb - pa) * f, q_slerp(qa, qb, f)) for (pa, qa), (pb, qb) in zip(a, b)]

    def matriz_modelo(self, p, q):
        m = np.identity(4)
        m[:3, :3] = q_matriz(q) * TAMANHO_DADO
        m[:3, 3] = p
        return m
