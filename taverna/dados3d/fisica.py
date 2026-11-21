"""
Física dos dados (numpy). Determinística: mesma semente + mesmos dados = mesmo movimento em
todos os PCs, então todo mundo vê o MESMO quique.

Mesa: plano z = 0, paredes em x = ±L e y = ±A (o tamanho da área visível). Cada dado é um corpo
rígido; o contato é pelos vértices (quinas) com o chão e as paredes, e dado com dado por esfera.
No fim, cada dado é assentado na face de cima (ou no vértice, no d4) com um ajuste suave.
"""

import math

import numpy as np

from .geometria import solido

GRAVIDADE = 42.0
PASSO = 1 / 240          # física a 240 Hz
QUADROS_POR_SEG = 60     # o que vai pra tela
TEMPO_MAX = 4.5
RESTITUICAO = 0.32       # quanto quica no chão
ATRITO = 0.45
RESTITUICAO_PAREDE = 0.55


# ---------------------------------------------------------------- quatérnios (w, x, y, z)
def q_mult(a, b):
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return np.array([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
                     w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                     w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2])


def q_matriz(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def q_eixo(eixo, ang):
    eixo = np.asarray(eixo, dtype=float)
    n = np.linalg.norm(eixo)
    if n < 1e-9:
        return np.array([1.0, 0, 0, 0])
    eixo = eixo / n
    s = math.sin(ang / 2)
    return np.array([math.cos(ang / 2), eixo[0] * s, eixo[1] * s, eixo[2] * s])


def q_alinhar(de, para):
    """Rotação mínima que leva o vetor `de` até `para`."""
    de = de / np.linalg.norm(de)
    para = para / np.linalg.norm(para)
    c = float(np.clip(np.dot(de, para), -1, 1))
    if c > 1 - 1e-9:
        return np.array([1.0, 0, 0, 0])
    if c < -1 + 1e-9:
        orto = np.cross(de, [1, 0, 0]) if abs(de[0]) < 0.9 else np.cross(de, [0, 1, 0])
        return q_eixo(orto, math.pi)
    return q_eixo(np.cross(de, para), math.acos(c))


def q_slerp(a, b, t):
    d = float(np.dot(a, b))
    if d < 0:
        b, d = -b, -d
    if d > 0.9995:
        r = a + t * (b - a)
        return r / np.linalg.norm(r)
    th = math.acos(d)
    return (math.sin((1 - t) * th) * a + math.sin(t * th) * b) / math.sin(th)


# ---------------------------------------------------------------- dado
class _Corpo:
    def __init__(self, lados, tamanho):
        v, faces, normais, _ = solido(lados)
        self.lados = lados
        self.local = v * tamanho
        self.normais = normais
        self.raio = float(np.max(np.linalg.norm(self.local, axis=1)))
        self.inercia = 0.4 * self.raio ** 2       # esfera cheia, massa 1 (simples e estável)
        self.p = np.zeros(3)
        self.q = np.array([1.0, 0, 0, 0])
        self.v = np.zeros(3)
        self.w = np.zeros(3)
        self.parado = False
        self.quieto = 0.0

    def mundo(self):
        return self.local @ q_matriz(self.q).T + self.p

    def impulso(self, ponto, normal, e, mu):
        r = ponto - self.p
        vc = self.v + np.cross(self.w, r)
        vn = float(np.dot(vc, normal))
        if vn >= 0:
            return
        rn = np.cross(r, normal)
        denom = 1.0 + float(np.dot(rn, rn)) / self.inercia
        j = -(1 + e) * vn / denom
        self.v += j * normal
        self.w += np.cross(r, j * normal) / self.inercia
        # atrito
        vc = self.v + np.cross(self.w, r)
        vt = vc - np.dot(vc, normal) * normal
        tam = float(np.linalg.norm(vt))
        if tam > 1e-6:
            t = vt / tam
            rt = np.cross(r, t)
            jt = -tam / (1.0 + float(np.dot(rt, rt)) / self.inercia)
            jt = max(jt, -mu * j)
            self.v += jt * t
            self.w += np.cross(r, jt * t) / self.inercia


def face_de_cima(lados, q):
    """Índice da face pra cima (no d4: índice do VÉRTICE de cima)."""
    v, faces, normais, _ = solido(lados)
    m = q_matriz(q)
    if lados == 4:
        return int(np.argmax((v @ m.T)[:, 2]))
    return int(np.argmax((normais @ m.T)[:, 2]))


def simular(lados_lista, semente: int, largura: float, altura: float, tamanho: float = 1.0):
    """
    Joga os dados. Devolve (quadros, finais):
      quadros: lista de quadros; cada quadro = lista de (posição xyz, quatérnio wxyz) por dado
      finais:  índice da face (ou vértice, no d4) que ficou pra cima, por dado
    largura/altura = metade do tamanho da área (as paredes).
    """
    rng = np.random.default_rng(int(semente) & 0x7FFFFFFF)
    corpos = [_Corpo(l, tamanho) for l in lados_lista]
    n = len(corpos)
    # lançados de um lado da tela (sorteado), em direção ao meio, girando
    lado = rng.integers(4)
    for k, c in enumerate(corpos):
        espalhar = (k - (n - 1) / 2) * tamanho * 2.3
        if lado in (0, 1):
            sx = -1 if lado == 0 else 1
            c.p = np.array([sx * (largura - tamanho * 1.5), espalhar * 0.6 + rng.uniform(-1, 1) * altura * 0.25,
                            rng.uniform(2.5, 4.5) * tamanho])
        else:
            sy = -1 if lado == 2 else 1
            c.p = np.array([espalhar * 0.6 + rng.uniform(-1, 1) * largura * 0.25, sy * (altura - tamanho * 1.5),
                            rng.uniform(2.5, 4.5) * tamanho])
        # mira um ponto perto do meio da mesa (cada dado o seu, pra não empilhar)
        alvo = np.array([rng.uniform(-0.3, 0.3) * largura + espalhar * 0.5, rng.uniform(-0.3, 0.3) * altura, 0])
        rumo = alvo[:2] - c.p[:2]
        c.v = np.array([*(rumo * rng.uniform(1.9, 2.3)), rng.uniform(-2, 3)])
        c.q = q_eixo(rng.normal(size=3), rng.uniform(0, 2 * math.pi))
        c.w = rng.normal(size=3) * rng.uniform(10, 22)
    quadros = []
    passos_por_quadro = int(round(1 / (PASSO * QUADROS_POR_SEG)))
    passo = 0
    max_passos = int(TEMPO_MAX / PASSO)
    paredes = ((np.array([1.0, 0, 0]), -largura), (np.array([-1.0, 0, 0]), -largura),
               (np.array([0, 1.0, 0]), -altura), (np.array([0, -1.0, 0]), -altura))
    while passo < max_passos:
        for c in corpos:
            if c.parado:
                continue
            c.v[2] -= GRAVIDADE * PASSO
            c.v *= 0.9993
            c.w *= 0.996
            c.p = c.p + c.v * PASSO
            dq = q_mult(np.array([0.0, *c.w]), c.q) * (0.5 * PASSO)
            c.q = c.q + dq
            c.q /= np.linalg.norm(c.q)
            pts = c.mundo()
            # chão
            fundo = pts[:, 2]
            dentro = np.where(fundo < 0)[0]
            if len(dentro):
                c.p[2] -= float(fundo.min()) * 0.8          # desfaz a afundada
                for i in dentro:
                    c.impulso(pts[i], np.array([0.0, 0, 1]), RESTITUICAO, ATRITO)
            # paredes
            for normal, d in paredes:
                dist = pts @ normal - d
                fora = np.where(dist < 0)[0]
                if len(fora):
                    c.p -= normal * float(dist.min()) * 0.8
                    for i in fora:
                        c.impulso(pts[i], normal, RESTITUICAO_PAREDE, 0.2)
        # dado com dado (esferas um pouco menores que o dado)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = corpos[i], corpos[j]
                d = b.p - a.p
                dist = float(np.linalg.norm(d))
                minimo = (a.raio + b.raio) * 0.78
                if 1e-6 < dist < minimo:
                    nrm = d / dist
                    corr = (minimo - dist) / 2
                    a.p -= nrm * corr
                    b.p += nrm * corr
                    rel = float(np.dot(b.v - a.v, nrm))
                    if rel < 0:
                        jj = -(1 + 0.4) * rel / 2
                        a.v -= jj * nrm
                        b.v += jj * nrm
                        a.parado = b.parado = False
        # parou?
        for c in corpos:
            if c.parado:
                continue
            no_chao = float(c.mundo()[:, 2].min()) < 0.02 * c.raio
            if no_chao and np.linalg.norm(c.v) < 0.25 and np.linalg.norm(c.w) < 0.5:
                c.quieto += PASSO
                if c.quieto > 0.18:
                    c.parado = True
                    c.v[:] = 0
                    c.w[:] = 0
            else:
                c.quieto = 0.0
        if passo % passos_por_quadro == 0:
            quadros.append([(c.p.copy(), c.q.copy()) for c in corpos])
        passo += 1
        if all(c.parado for c in corpos):
            break
    # assentar: gira cada dado o mínimo pra face de cima ficar reta (dado em pé na quina não existe)
    finais = []
    alvos = []
    for c in corpos:
        idx = face_de_cima(c.lados, c.q)
        finais.append(idx)
        m = q_matriz(c.q)
        if c.lados == 4:   # d4: a face de baixo (oposta ao vértice de cima) fica reta no chão
            v, faces, normais, _ = solido(4)
            baixo = next(k for k, f in enumerate(faces) if idx not in f)
            q_corr = q_alinhar(m @ normais[baixo], np.array([0, 0, -1.0]))
        else:
            q_corr = q_alinhar(m @ c.normais[idx], np.array([0, 0, 1.0]))
        q_alvo = q_mult(q_corr, c.q)
        q_alvo /= np.linalg.norm(q_alvo)
        pts = c.local @ q_matriz(q_alvo).T
        p_alvo = np.array([c.p[0], c.p[1], -float(pts[:, 2].min())])
        alvos.append((p_alvo, q_alvo))
    inicio = [(c.p.copy(), c.q.copy()) for c in corpos]
    for k in range(1, 9):
        t = k / 8
        t = t * t * (3 - 2 * t)
        quadros.append([(pi + (pa - pi) * t, q_slerp(qi, qa, t)) for (pi, qi), (pa, qa) in zip(inicio, alvos)])
    return quadros, finais


def renumerar(lados, valor_desejado, indice_de_cima):
    """
    Números das faces (ou vértices, no d4) DESTE dado pra que a de cima mostre `valor_desejado`.
    Gira a numeração padrão (soma das opostas continua valendo na maioria das faces).
    d10: valores 1–10 (10 mostra '0').
    """
    _, _, _, nums = solido(lados)
    nums = list(nums)
    if lados == 10:
        alvo = valor_desejado % 10
        atual = nums[indice_de_cima]
        delta = (alvo - atual) % 10
        return [(x + delta) % 10 for x in nums]
    atual = nums[indice_de_cima]
    delta = (valor_desejado - atual) % lados
    return [((x - 1 + delta) % lados) + 1 for x in nums]
