"""
Sólidos dos dados. Cada dado: vértices (N×3, centrados na origem, "raio" ~1) e faces (listas de
índices, em ordem anti-horária vista de fora). Tudo numpy.
"""

import math

import numpy as np

PHI = (1 + 5 ** 0.5) / 2


def _normalizar_faces(v, faces):
    """Garante a ordem anti-horária vista de fora (normal apontando pra fora do centro)."""
    saida = []
    for f in faces:
        a, b, c = v[f[0]], v[f[1]], v[f[2]]
        n = np.cross(b - a, c - a)
        if np.dot(n, v[f].mean(axis=0)) < 0:
            f = list(reversed(f))
        saida.append(list(f))
    return saida


def _faces_por_plano(v, tol=1e-6):
    """Faces de um poliedro convexo (pelos planos de apoio dos vértices). Bom pros sólidos de Platão."""
    n = len(v)
    planos = {}
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                normal = np.cross(v[j] - v[i], v[k] - v[i])
                tam = np.linalg.norm(normal)
                if tam < tol:
                    continue
                normal /= tam
                d = np.dot(normal, v[i])
                if d < 0:
                    normal, d = -normal, -d
                lado = v @ normal - d
                if np.all(lado <= tol * 10):
                    chave = tuple(np.round(normal, 5))
                    if chave not in planos:
                        planos[chave] = (normal, np.where(np.abs(lado) <= tol * 10)[0])
    faces = []
    for normal, idx in planos.values():
        centro = v[idx].mean(axis=0)
        u = v[idx[0]] - centro
        u /= np.linalg.norm(u)
        w = np.cross(normal, u)
        ang = [math.atan2(np.dot(v[i] - centro, w), np.dot(v[i] - centro, u)) for i in idx]
        faces.append([int(i) for _, i in sorted(zip(ang, idx))])
    return faces


def _escala(v, raio=1.0):
    v = np.array(v, dtype=float)
    v -= v.mean(axis=0)
    return v * (raio / np.max(np.linalg.norm(v, axis=1)))


def tetraedro():
    v = _escala([(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)], 1.15)
    return v, _normalizar_faces(v, _faces_por_plano(v))


def cubo():
    v = _escala([(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], 0.95)
    return v, _normalizar_faces(v, _faces_por_plano(v))


def octaedro():
    v = _escala([(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)], 1.05)
    return v, _normalizar_faces(v, _faces_por_plano(v))


def dodecaedro():
    pts = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    for a in (-1, 1):
        for b in (-1, 1):
            pts += [(0, a / PHI, b * PHI), (a / PHI, b * PHI, 0), (a * PHI, 0, b / PHI)]
    v = _escala(pts, 1.05)
    return v, _normalizar_faces(v, _faces_por_plano(v))


def icosaedro():
    pts = []
    for a in (-1, 1):
        for b in (-1, 1):
            pts += [(0, a, b * PHI), (a, b * PHI, 0), (a * PHI, 0, b)]
    v = _escala(pts, 1.08)
    return v, _normalizar_faces(v, _faces_por_plano(v))


def trapezoedro():
    """d10: 10 faces em pipa. Topo/base nos polos, dois anéis de 5 desencontrados (36°)."""
    a = 0.105   # altura dos anéis (o polo é calculado pras pipas ficarem planas)

    def pontos(b):
        cima = [(math.cos(math.radians(k * 72)), math.sin(math.radians(k * 72)), a) for k in range(5)]
        baixo = [(math.cos(math.radians(k * 72 + 36)), math.sin(math.radians(k * 72 + 36)), -a) for k in range(5)]
        return np.array([(0, 0, b), (0, 0, -b)] + cima + baixo, dtype=float)

    def torcao(b):   # quão fora do plano fica o 4º ponto da pipa
        v = pontos(b)
        p0, p1, p2, p3 = v[0], v[2], v[7], v[3]
        n = np.cross(p1 - p0, p2 - p0)
        return np.dot(n / np.linalg.norm(n), p3 - p0)

    lo, hi = 0.2, 3.0
    for _ in range(80):   # bisseção: acha o polo que deixa a pipa plana
        meio = (lo + hi) / 2
        if torcao(lo) * torcao(meio) <= 0:
            hi = meio
        else:
            lo = meio
    v = pontos((lo + hi) / 2)
    faces = []
    for k in range(5):
        faces.append([0, 2 + k, 7 + k, 2 + (k + 1) % 5])          # pipas de cima
        faces.append([1, 7 + k, 2 + (k + 1) % 5, 7 + (k + 1) % 5])  # pipas de baixo
    v = _escala(v, 1.05)
    return v, _normalizar_faces(v, faces)


SOLIDOS = {4: tetraedro, 6: cubo, 8: octaedro, 10: trapezoedro, 12: dodecaedro, 20: icosaedro}
_CACHE = {}


def normais(v, faces):
    out = []
    for f in faces:
        c = v[f].mean(axis=0)
        n = np.cross(v[f[1]] - v[f[0]], v[f[2]] - v[f[0]])
        n /= np.linalg.norm(n)
        out.append(n if np.dot(n, c) > 0 else -n)
    return np.array(out)


def numeracao(lados, v, faces):
    """Número de cada face (ou de cada VÉRTICE, no d4). Faces opostas somam lados+1 (d10: 0–9, opostas somam 9)."""
    if lados == 4:
        return list(range(1, 5))   # d4: um número por vértice; vale o vértice de cima
    ns = normais(v, faces)
    livres = list(range(len(faces)))
    nums = [0] * len(faces)
    proximo = 1
    while livres:
        i = livres.pop(0)
        oposta = min(livres, key=lambda j: np.dot(ns[i], ns[j])) if livres else None
        if lados == 10:
            nums[i] = proximo - 1
            if oposta is not None:
                nums[oposta] = 9 - (proximo - 1)
        else:
            nums[i] = proximo
            if oposta is not None:
                nums[oposta] = lados + 1 - proximo
        if oposta is not None:
            livres.remove(oposta)
        proximo += 1
    return nums


def solido(lados: int):
    """(vértices, faces, normais das faces, números) de um dado. lados ∈ SOLIDOS."""
    if lados not in _CACHE:
        v, f = SOLIDOS[lados]()
        _CACHE[lados] = (v, f, normais(v, f), numeracao(lados, v, f))
    return _CACHE[lados]


_MALHAS = {}


def malha_chanfrada(lados: int, k: float = 0.11):
    """
    Malha pra desenhar com as quinas e arestas ARREDONDADAS (dado de verdade não tem quina viva).
    Cada face encolhe um pouco pro centro (fração k); entre duas faces entra uma tira cuja normal vai
    de uma face à outra (a luz "rola" na aresta) e em cada vértice uma tampinha.
    A física continua usando o sólido original.

    Devolve uma lista de triângulos; cada vértice = (posição, normal, (face, vértice_original) ou None).
    O terceiro campo diz de onde tirar o UV do número (None = chanfro, sem número).
    """
    if (lados, k) in _MALHAS:
        return _MALHAS[(lados, k)]
    v, faces, normais, _ = solido(lados)
    copia = {}
    for j, f in enumerate(faces):
        c = v[f].mean(axis=0)
        for i in f:
            copia[(j, i)] = v[i] + (c - v[i]) * k
    tris = []
    # faces (encolhidas), em leque
    for j, f in enumerate(faces):
        for t in range(1, len(f) - 1):
            tris.append([(copia[(j, f[x])], normais[j], (j, f[x])) for x in (0, t, t + 1)])
    # arestas: tira entre as duas faces vizinhas, com a normal passando de uma pra outra
    arestas = {}
    for j, f in enumerate(faces):
        for t in range(len(f)):
            a, b = f[t], f[(t + 1) % len(f)]
            arestas.setdefault(frozenset((a, b)), []).append((j, a, b))
    for lista in arestas.values():
        if len(lista) != 2:
            continue
        (j1, a, b), (j2, _, _) = lista
        n1, n2 = normais[j1], normais[j2]
        pa1, pb1, pa2, pb2 = copia[(j1, a)], copia[(j1, b)], copia[(j2, a)], copia[(j2, b)]
        tris.append([(pa1, n1, None), (pb1, n1, None), (pb2, n2, None)])
        tris.append([(pa1, n1, None), (pb2, n2, None), (pa2, n2, None)])
    # quinas: as cópias do vértice em cada face, em volta dele
    for i in range(len(v)):
        js = [j for j, f in enumerate(faces) if i in f]
        if len(js) < 3:
            continue
        eixo = v[i] / np.linalg.norm(v[i])
        u = np.cross(eixo, [0.0, 0.0, 1.0] if abs(eixo[2]) < 0.9 else [1.0, 0.0, 0.0])
        u /= np.linalg.norm(u)
        w = np.cross(eixo, u)
        js.sort(key=lambda j: math.atan2(np.dot(copia[(j, i)] - v[i], w), np.dot(copia[(j, i)] - v[i], u)))
        for t in range(1, len(js) - 1):
            tris.append([(copia[(js[x], i)], normais[js[x]], None) for x in (0, t, t + 1)])
    _MALHAS[(lados, k)] = tris
    return tris


def suportado(lados: int) -> bool:
    return lados in SOLIDOS or lados == 100
