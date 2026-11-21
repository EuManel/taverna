"""
🧊 Formas 3D próprias pra mesa da taverna (v0.53) — pedido do Manel: "eu sei que você consegue fazer as
moedas em 3D, a caneca em 3D, com a cerveja borbulhando, a vela…".

O Qt Quick 3D só traz cubo, esfera, cilindro, cone e plano. As outras formas são calculadas aqui (numpy) e
entregues pro QML, que monta com `ProceduralMesh` (QtQuick3D.Helpers). (Registrar uma classe de geometria
feita em Python no QML derrubava o programa — por isso a malha vai como listas de pontos.)

  torno|<perfil>|<ondula> : sólido de revolução (caneca, castiçal, vela com cera torta). Perfil "r,y; r,y; …"
  toro|<R>|<r>|<arco>      : argola (aros de ferro, asa da caneca)
  icosaedro                : o d20, faces chapadas (arestas vivas)
  espuma                   : calota de espuma cheia de bolotas
"""

import math

import numpy as np
from PyQt6.QtGui import QVector2D, QVector3D

_CACHE = {}


def _normais_suaves(pos, idx):
    n = np.zeros_like(pos)
    a, b, c = pos[idx[:, 0]], pos[idx[:, 1]], pos[idx[:, 2]]
    fn = np.cross(b - a, c - a)
    for k in range(3):
        np.add.at(n, idx[:, k], fn)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    return n


def _grade(L, nlin, ncol, inverter=False):
    idx = []
    for i in range(nlin):
        for j in range(ncol):
            a, b, c, d = i * L + j, i * L + j + 1, (i + 1) * L + j, (i + 1) * L + j + 1
            idx += [(a, b, c), (b, d, c)] if inverter else [(a, c, b), (b, c, d)]
    return np.array(idx, np.int64)


def torno(perfil: str, ondula: float = 0.0, lados: int = 48):
    pts = [tuple(float(t) for t in par.split(",")) for par in perfil.split(";") if par.strip()]
    P = np.array(pts, np.float32)
    ang = np.linspace(0, 2 * math.pi, lados + 1, dtype=np.float32)
    rr = P[:, 0][:, None] * np.ones((1, lados + 1), np.float32)
    if ondula:
        rng = np.random.default_rng(3)
        fase = rng.uniform(0, 6.28, 3)
        ond = sum(np.sin(ang * (k + 3) + fase[k]) for k in range(3)) / 3
        rr = rr * (1 + ondula * ond[None, :] * np.linspace(0, 1, len(P))[:, None] ** 2)
    x, z = rr * np.cos(ang)[None, :], rr * np.sin(ang)[None, :]
    y = P[:, 1][:, None] * np.ones((1, lados + 1), np.float32)
    pos = np.stack([x, y, z], -1).reshape(-1, 3)
    comp = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    comp = comp / max(1e-6, comp[-1])
    u = np.broadcast_to(ang[None, :] / (2 * math.pi), (len(P), lados + 1))
    v = np.broadcast_to(comp[:, None], (len(P), lados + 1))
    uv = np.stack([u, v], -1).reshape(-1, 2)
    idx = _grade(lados + 1, len(P) - 1, lados)
    return pos, _normais_suaves(pos, idx), uv, idx


def toro(R: float, r: float, arco: float = 1.0, nu: int = 48, nv: int = 16):
    u = np.linspace(0, 2 * math.pi * arco, nu + 1, dtype=np.float32)
    v = np.linspace(0, 2 * math.pi, nv + 1, dtype=np.float32)
    U, V = np.meshgrid(u, v, indexing="ij")
    cx, cz = R * np.cos(U), R * np.sin(U)
    x, z = (R + r * np.cos(V)) * np.cos(U), (R + r * np.cos(V)) * np.sin(U)
    y = r * np.sin(V)
    pos = np.stack([x, y, z], -1).reshape(-1, 3)
    nor = np.stack([x - cx, y, z - cz], -1).reshape(-1, 3)
    nor /= np.maximum(np.linalg.norm(nor, axis=1, keepdims=True), 1e-9)
    uv = np.stack([U / (2 * math.pi), V / (2 * math.pi)], -1).reshape(-1, 2)
    return pos, nor, uv, _grade(nv + 1, nu, nv, inverter=True)


def icosaedro():
    t = (1 + math.sqrt(5)) / 2
    v = np.array([(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t),
                  (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)], np.float32)
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    f = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2),
         (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5),
         (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    pos, nor, uv = [], [], []
    for k, (a, b, c) in enumerate(f):
        tri = v[[a, b, c]]
        n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
        n /= np.linalg.norm(n)
        if np.dot(n, tri.mean(axis=0)) < 0:
            tri, n = tri[[0, 2, 1]], -n
        pos += list(tri)
        nor += [n, n, n]
        cu, cv = (k % 5) / 5, (k // 5) / 4       # cada face pega uma casa da textura de números (5×4)
        uv += [(cu + 0.1, cv + 0.2), (cu + 0.18, cv + 0.05), (cu + 0.02, cv + 0.05)]
    pos, nor, uv = np.array(pos), np.array(nor), np.array(uv)
    return pos, nor, uv, np.arange(len(pos)).reshape(-1, 3)


def espuma(nu: int = 64, nv: int = 24):
    rng = np.random.default_rng(11)
    bolhas = rng.normal(size=(70, 3))
    bolhas /= np.linalg.norm(bolhas, axis=1, keepdims=True)
    tam = rng.uniform(0.12, 0.3, 70)
    u = np.linspace(0, 2 * math.pi, nu + 1, dtype=np.float32)
    v = np.linspace(0, math.pi / 2 + 0.35, nv + 1, dtype=np.float32)
    U, V = np.meshgrid(u, v, indexing="ij")
    d = np.stack([np.cos(U) * np.sin(V), np.cos(V), np.sin(U) * np.sin(V)], -1)
    r = np.ones(U.shape, np.float32)
    for b, s in zip(bolhas, tam):
        ang = np.arccos(np.clip(d @ b, -1, 1))
        r += np.clip(1 - ang / s, 0, 1) ** 2 * s * 0.45
    pos = d * r[..., None]
    pos[..., 1] *= 0.45
    pos = pos.reshape(-1, 3)
    uv = np.stack([U / (2 * math.pi), V / math.pi], -1).reshape(-1, 2)
    idx = _grade(nv + 1, nu, nv, inverter=True)
    return pos, _normais_suaves(pos, idx), uv, idx


def achatar(pos, nor, uv, idx):
    """Low-poly: cada triângulo com a SUA normal (faces chapadas, cara de jogo facetado)."""
    p = pos[idx.reshape(-1)]
    t = uv[idx.reshape(-1)]
    tri = p.reshape(-1, 3, 3)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    # garante que a normal aponte pra fora (mesmo lado da normal suave original)
    suave = nor[idx.reshape(-1)].reshape(-1, 3, 3).mean(axis=1)
    sinal = np.sign((n * suave).sum(axis=1, keepdims=True))
    sinal[sinal == 0] = 1
    n = n * sinal
    return p, np.repeat(n, 3, axis=0), t, np.arange(len(p)).reshape(-1, 3)


def moeda(lados=14):
    """Moeda: cilindro baixo, facetado, com a tampa de cima mapeada de chapado (o brasão aparece)."""
    ang = np.linspace(0, 2 * math.pi, lados, endpoint=False)
    R, h = 1.0, 0.16
    pos, nor, uv, idx = [], [], [], []

    def add(p, n, t):
        pos.append(p)
        nor.append(n)
        uv.append(t)
        return len(pos) - 1
    c = add((0, h, 0), (0, 1, 0), (0.5, 0.5))
    anel = [add((R * math.cos(a), h, R * math.sin(a)), (0, 1, 0), (0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)))
            for a in ang]
    for k in range(lados):
        idx.append((c, anel[(k + 1) % lados], anel[k]))
    for k in range(lados):                       # borda (cada lado chapado)
        a0, a1 = ang[k], ang[(k + 1) % lados]
        am = (a0 + a1) / 2 if k < lados - 1 else (a0 + a1 + 2 * math.pi) / 2
        n = (math.cos(am), 0, math.sin(am))
        q = [add((R * math.cos(a0), h, R * math.sin(a0)), n, (0.9, 0.5)),
             add((R * math.cos(a1), h, R * math.sin(a1)), n, (0.9, 0.5)),
             add((R * math.cos(a0), 0, R * math.sin(a0)), n, (0.95, 0.5)),
             add((R * math.cos(a1), 0, R * math.sin(a1)), n, (0.95, 0.5))]
        idx += [(q[0], q[1], q[2]), (q[1], q[3], q[2])]
    return np.array(pos, np.float32), np.array(nor, np.float32), np.array(uv, np.float32), np.array(idx, np.int64)


def folha(cols=3, lins=2, amp=0.06, ruga=0.0, semente=1):
    """Papel/pano: grade com as DOBRAS levantadas (mapa dobrado) e rugas (pano). Tamanho 1×1, em XZ."""
    n = 40
    rng = np.random.default_rng(semente)
    u = np.linspace(0, 1, n + 1, dtype=np.float32)
    U, V = np.meshgrid(u, u, indexing="ij")
    y = np.zeros_like(U)
    for k in range(1, cols):                      # vinco: sobe e desce em zigue-zague
        y += amp * (1 if k % 2 else -0.6) * np.clip(1 - np.abs(U - k / cols) * cols * 1.6, 0, 1)
    for k in range(1, lins):
        y += amp * 0.6 * np.clip(1 - np.abs(V - k / lins) * lins * 1.6, 0, 1)
    if ruga:
        for _ in range(5):
            ang, fr, fs = rng.uniform(0, math.pi), rng.uniform(4, 9), rng.uniform(0, 6)
            y += ruga * np.sin((U * math.cos(ang) + V * math.sin(ang)) * fr + fs) * rng.uniform(0.4, 1)
    y -= y.min()
    pos = np.stack([U - 0.5, y, V - 0.5], -1).reshape(-1, 3)
    uv = np.stack([U, 1 - V], -1).reshape(-1, 2)
    idx = _grade(n + 1, n, n, inverter=True)
    return pos, _normais_suaves(pos, idx), uv, idx


def dado(chanfro=0.12):
    """d6 low-poly: cubo de lado 2 com as quinas chanfradas; cada face pega uma casa da textura 'dados' (3×2)."""
    pos, nor, uv, idx = [], [], [], []
    c = 1 - chanfro
    faces = [((0, 1, 0), (1, 0, 0), (0, 0, 1)), ((0, -1, 0), (1, 0, 0), (0, 0, -1)),
             ((1, 0, 0), (0, 0, -1), (0, 1, 0)), ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
             ((0, 0, 1), (1, 0, 0), (0, 1, 0)), ((0, 0, -1), (-1, 0, 0), (0, 1, 0))]
    for k, (n, eu, ev) in enumerate(faces):
        n, eu, ev = np.array(n, float), np.array(eu, float), np.array(ev, float)
        cu, cv = (k % 3) / 3, (k // 3) / 2
        base = len(pos)
        for (a, b) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            p = n + eu * a * c + ev * b * c
            pos.append(p)
            nor.append(n)
            uv.append((cu + (a * 0.5 + 0.5) / 3, cv + (b * 0.5 + 0.5) / 2))
        if np.dot(np.cross(eu, ev), n) > 0:      # triângulos de frente pra fora
            idx += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
        else:
            idx += [(base, base + 2, base + 1), (base, base + 3, base + 2)]
    pos, nor, uv = [list(map(float, p)) for p in pos], [list(map(float, n)) for n in nor], [list(t) for t in uv]
    # chanfros: liga cada par de faces vizinhas por uma tira, e as quinas por um triângulo (cor da borda)
    P = np.array(pos)
    tris = []
    # (jeito simples e robusto: casco convexo dos 24 pontos)
    from itertools import combinations
    for a, b, c3 in combinations(range(len(P)), 3):
        n = np.cross(P[b] - P[a], P[c3] - P[a])
        ln = np.linalg.norm(n)
        if ln < 1e-6:
            continue
        n /= ln
        d = (P - P[a]) @ n
        if (d <= 1e-6).all() or (d >= -1e-6).all():
            if (d >= -1e-6).all():
                n = -n
            # pula as faces grandes (já feitas): normal alinhada a um eixo
            if np.max(np.abs(n)) > 0.999:
                continue
            tris.append((a, b, c3, n))
    vistos = set()
    for a, b, c3, n in tris:
        chave = tuple(sorted((a, b, c3)))
        if chave in vistos:
            continue
        vistos.add(chave)
        base = len(pos)
        ordem = (a, b, c3) if np.dot(np.cross(P[b] - P[a], P[c3] - P[a]), n) > 0 else (a, c3, b)
        for v in ordem:
            pos.append(list(map(float, P[v])))
            nor.append(list(map(float, n)))
            uv.append((0.999, 0.999))          # canto da textura = cor da borda do dado
        idx.append((base, base + 1, base + 2))
    return np.array(pos, np.float32), np.array(nor, np.float32), np.array(uv, np.float32), np.array(idx, np.int64)


def tela(bojo=0.06, n=24):
    """Tela de TV de tubo: retângulo 1×1 em XY, estufado pra frente (+z) no meio."""
    u = np.linspace(-0.5, 0.5, n + 1, dtype=np.float32)
    X, Y = np.meshgrid(u, u, indexing="ij")
    Z = bojo * (1 - (2 * X) ** 2) * (1 - (2 * Y) ** 2)
    pos = np.stack([X, Y, Z], -1).reshape(-1, 3)
    uv = np.stack([X + 0.5, Y + 0.5], -1).reshape(-1, 2)
    idx = _grade(n + 1, n, n, inverter=True)
    return pos, _normais_suaves(pos, idx), uv, idx


def grade(n=120):
    """Plano 1×1 (XZ) bem dividido — o mar (as ondas são feitas no shader)."""
    u = np.linspace(-0.5, 0.5, n + 1, dtype=np.float32)
    X, Z = np.meshgrid(u, u, indexing="ij")
    pos = np.stack([X, np.zeros_like(X), Z], -1).reshape(-1, 3)
    nor = np.tile(np.array([0, 1, 0], np.float32), (len(pos), 1))
    uv = np.stack([X + 0.5, Z + 0.5], -1).reshape(-1, 2)
    return pos, nor, uv, _grade(n + 1, n, n, inverter=True)


def casco(n=14):
    """Casco de barco low-poly: seções em "U" ao longo do comprimento (x), afinando até a proa (x=+1).
    Vai de x=-1 (popa cortada) a x=+1 (proa), largura 2·0.35, altura 0.4 (borda em y=0)."""
    secoes = []
    xs = np.linspace(-1, 1, n)
    for x in xs:
        larg = 0.35 * (1 - max(0, x) ** 1.8)               # afina na proa
        fundo = -0.4 * (1 - max(0, x) ** 3 * 0.6)
        pts = [(-larg, 0), (-larg * 0.92, fundo * 0.55), (-larg * 0.5, fundo * 0.95), (0, fundo),
               (larg * 0.5, fundo * 0.95), (larg * 0.92, fundo * 0.55), (larg, 0)]
        secoes.append([(x + 0.06 * max(0, x) ** 2, y, z) for (z, y) in pts])   # proa um pouco "puxada" pra frente
    P = np.array(secoes, np.float32).reshape(-1, 3)
    L = 7
    idx = _grade(L, n - 1, L - 1)
    uv = np.stack([np.repeat((xs + 1) / 2, L), np.tile(np.linspace(0, 1, L), n)], -1).astype(np.float32)
    return P, _normais_suaves(P, idx), uv, idx


def helice(R=40.0, r=7.0, voltas=4.0, altura=200.0, nu=160, nv=8):
    """Tubo em espiral (a serpentina do alambique). Eixo y, de y=0 a y=altura."""
    t = np.linspace(0, 1, nu + 1, dtype=np.float32)
    a = t * voltas * 2 * math.pi
    c = np.stack([R * np.cos(a), altura * t, R * np.sin(a)], -1)
    tg = np.gradient(c, axis=0)
    tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    n1 = np.stack([np.cos(a), np.zeros_like(a), np.sin(a)], -1)          # aponta pra fora da espiral
    n1 -= (n1 * tg).sum(1, keepdims=True) * tg
    n1 /= np.linalg.norm(n1, axis=1, keepdims=True)
    n2 = np.cross(tg, n1)
    v = np.linspace(0, 2 * math.pi, nv + 1, dtype=np.float32)
    nor = np.cos(v)[None, :, None] * n1[:, None, :] + np.sin(v)[None, :, None] * n2[:, None, :]
    pos = (c[:, None, :] + r * nor).reshape(-1, 3)
    nor = nor.reshape(-1, 3)
    uv = np.stack(np.meshgrid(t, v / (2 * math.pi), indexing="ij"), -1).reshape(-1, 2)
    return pos, nor, uv, _grade(nv + 1, nu, nv, inverter=True)


def tentaculo(alto=1.0, largo=0.5, enrola=0.25, r0=0.08, r1=0.012, giro=1.0, voltas=1.8, laco=0.0, passos=90, nv=10):
    """(v0.58) Tentáculo de polvo: tubo que sai da água (y=0) e sobe em ARCO pro lado (+x), afinando de r0 a r1.
    giro = +1 a ponta enrola pra dentro/cima, -1 enrola pra fora/baixo · voltas = quanto a ponta enrola (0 = solta)
    · laco = 1: em vez de subir, faz um ARCO que volta pra dentro d'água (aparece só a "corcova")."""
    pts = []
    if laco:
        for k in range(passos):
            u = k / (passos - 1)
            pts.append((largo * u, alto * math.sin(u * math.pi) * (1 - 0.15 * u)))
    else:
        corpo = int(passos * (0.72 if voltas > 0.05 else 1.0))
        for k in range(corpo):
            u = k / (corpo - 1)
            pts.append((largo * math.sin(u * math.pi * 0.82), alto * (1 - (1 - u) ** 1.8)))
        if corpo < passos:
            bx, by = pts[-1]
            ax, ay = pts[-2]
            ang0 = math.atan2(by - ay, bx - ax)
            passo = math.hypot(bx - ax, by - ay)
            for k in range(1, passos - corpo + 1):
                u = k / (passos - corpo)
                ang = ang0 + giro * u * math.pi * voltas
                r = (1 - u * 0.75)
                bx += math.cos(ang) * passo * r * (enrola * 6)
                by += math.sin(ang) * passo * r * (enrola * 6)
                pts.append((bx, by))
    c = np.array([(x, y, 0.0) for x, y in pts], np.float32)
    tg = np.gradient(c, axis=0)
    tg /= np.maximum(np.linalg.norm(tg, axis=1, keepdims=True), 1e-9)
    n1 = np.stack([-tg[:, 1], tg[:, 0], np.zeros(len(c))], -1)
    n2 = np.tile(np.array([0, 0, 1], np.float32), (len(c), 1))
    t = np.linspace(0, 1, len(c), dtype=np.float32)
    raio = r0 + (r1 - r0) * t ** 0.85
    v = np.linspace(0, 2 * math.pi, nv + 1, dtype=np.float32)
    nor = np.cos(v)[None, :, None] * n1[:, None, :] + np.sin(v)[None, :, None] * n2[:, None, :]
    pos = (c[:, None, :] + raio[:, None, None] * nor).reshape(-1, 3)
    uv = np.stack(np.meshgrid(t, v / (2 * math.pi), indexing="ij"), -1).reshape(-1, 2)
    return pos, nor.reshape(-1, 3), uv, _grade(nv + 1, len(c) - 1, nv, inverter=True)


def malha(pedido: str) -> dict:
    """pedido → {"pos": [QVector3D], "nor": [QVector3D], "uv": [QVector2D], "idx": [int]} pro ProceduralMesh."""
    if pedido in _CACHE:
        return _CACHE[pedido]
    partes = pedido.split("|")
    tipo = partes[0]
    plano = partes[-1] == "plano"               # "...|plano" no fim = low-poly (faces chapadas)
    if plano:
        partes = partes[:-1]
    if tipo == "torno":                         # torno|perfil|ondula|lados
        pos, nor, uv, idx = torno(partes[1], float(partes[2]) if len(partes) > 2 else 0.0,
                                  int(partes[3]) if len(partes) > 3 else 48)
    elif tipo == "toro":                        # toro|R|r|arco|lados_volta|lados_tubo
        pos, nor, uv, idx = toro(float(partes[1]), float(partes[2]), float(partes[3]) if len(partes) > 3 else 1.0,
                                 int(partes[4]) if len(partes) > 4 else 48, int(partes[5]) if len(partes) > 5 else 16)
    elif tipo == "icosaedro":
        pos, nor, uv, idx = icosaedro()
    elif tipo == "moeda":
        pos, nor, uv, idx = moeda(int(partes[1]) if len(partes) > 1 else 14)
    elif tipo == "tela":                        # tela|bojo
        pos, nor, uv, idx = tela(float(partes[1]) if len(partes) > 1 else 0.06)
    elif tipo == "grade":                       # grade|n
        pos, nor, uv, idx = grade(int(partes[1]) if len(partes) > 1 else 120)
    elif tipo == "tentaculo":                   # tentaculo|alto|largo|enrola|r0|r1[|giro|voltas|laco]
        pos, nor, uv, idx = tentaculo(*[float(x) for x in partes[1:9]])
    elif tipo == "helice":                      # helice|R|r|voltas|altura
        pos, nor, uv, idx = helice(*[float(x) for x in partes[1:5]])
    elif tipo == "casco":
        pos, nor, uv, idx = casco()
    elif tipo == "conves":                      # o convés: a tampa de cima do casco
        P = casco()[0].reshape(14, 7, 3)
        borda = list(P[:, 0]) + list(P[::-1, 6])
        pos = np.array(borda, np.float32)
        nor = np.tile(np.array([0, 1, 0], np.float32), (len(pos), 1))
        uv = np.stack([(pos[:, 0] + 1) * 2, (pos[:, 2] + 0.4) * 2], -1).astype(np.float32)
        n = len(P)
        tri = []
        for k in range(n - 1):                  # tiras entre o lado esquerdo e o direito
            a, b = k, k + 1
            c, d = 2 * n - 1 - k, 2 * n - 2 - k
            tri += [(a, c, b), (b, c, d)]
        idx = np.array(tri, np.int64)
    elif tipo == "dado":
        pos, nor, uv, idx = dado()
    elif tipo == "folha":                       # folha|cols|lins|amp|ruga|semente
        pos, nor, uv, idx = folha(int(partes[1]), int(partes[2]), float(partes[3]), float(partes[4]), int(partes[5]))
    else:                                       # espuma|nu|nv
        pos, nor, uv, idx = espuma(int(partes[1]) if len(partes) > 1 else 64, int(partes[2]) if len(partes) > 2 else 24)
    if plano:
        pos, nor, uv, idx = achatar(pos, nor, uv, idx)
    m = {"pos": [QVector3D(*p) for p in np.asarray(pos, np.float64).tolist()],
         "nor": [QVector3D(*n) for n in np.asarray(nor, np.float64).tolist()],
         "uv": [QVector2D(*t) for t in np.asarray(uv, np.float64).tolist()], "idx": np.asarray(idx).reshape(-1).tolist()}
    _CACHE[pedido] = m
    return m
