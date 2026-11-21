"""
Reações entre áreas de efeito (v0.40; física na v0.41) — "água em cima do fogo, o fogo apaga".

Quando uma área encosta em outra (≥ 8% da menor), e o par está na tabela, o MESTRE recebe um aviso
("Água + Fogo: … Aplicar?") e só acontece se ele aceitar. Nada disso dá dano: decisão do mestre.

Física (pedido do Manel): reação de CONTATO só onde as áreas se encostam; reação em CADEIA, a área toda.
  💧 Água + 🔥 Fogo     → apaga só o pedaço coberto pela água, sobe vapor ali             (contato)
  💧 Água + 🌋 Lava     → ali a lava vira rocha (marca), onda de vapor, a água evapora   (contato)
  🔥 Fogo + ☠ Gás       → a nuvem TODA explode; o chão fica queimado                    (cadeia)
  ⚡ Raio + ☠ Gás       → a faísca acende a nuvem toda: EXPLODE                         (cadeia)
  🔥 Fogo + 🧪 Ácido    → o ácido ferve onde o fogo pega: estalo + vapor tóxico ali      (contato)
  🔥 Fogo + ❄ Gelo      → derrete onde o fogo encosta: vira água ali                    (contato)
  💧 Água + ❄ Gelo      → a água que encosta congela                                    (contato)
  ⚡ Raio + 💧 Água     → a poça TODA fica eletrificada                                  (cadeia)
  🔥 Fogo + 🌿 Vinhas / 🕸 Teia → o fogo se espalha por elas todas                       (cadeia)
  ✨ Luz / ☀ Radiante + 🌑 Escuridão → dissipa onde a luz chega                          (contato)
"""

from PyQt6.QtCore import QTimer

from ..config import CELULA

SOBREPOSICAO = 0.08   # fração da menor área que precisa estar coberta (encostar de leve não conta)

# par → (título, o que acontece)
REACOES = {
    frozenset(("agua", "fogo")): ("💧 Água + 🔥 Fogo", "O fogo apaga onde a água cobre, e sobe vapor ali."),
    frozenset(("agua", "lava")): ("💧 Água + 🌋 Lava", "Onde se encostam, a lava esfria e vira rocha, com uma explosão de vapor. Essa água evapora."),
    frozenset(("fogo", "veneno")): ("🔥 Fogo + ☠ Gás", "Reação em cadeia: a nuvem TODA pega fogo e EXPLODE. O chão fica queimado."),
    frozenset(("eletrico", "veneno")): ("⚡ Raio + ☠ Gás", "Reação em cadeia: a faísca acende a nuvem toda e ela EXPLODE."),
    frozenset(("fogo", "acido")): ("🔥 Fogo + 🧪 Ácido", "O ácido ferve onde o fogo pega: estala e solta vapor tóxico ali."),
    frozenset(("fogo", "gelo")): ("🔥 Fogo + ❄ Gelo", "O gelo derrete onde o fogo encosta e vira água ali."),
    frozenset(("agua", "gelo")): ("💧 Água + ❄ Gelo", "A água que encosta no gelo congela."),
    frozenset(("eletrico", "agua")): ("⚡ Raio + 💧 Água", "Reação em cadeia: a poça TODA fica eletrificada."),
    frozenset(("fogo", "planta")): ("🔥 Fogo + 🌿 Vinhas", "Reação em cadeia: o fogo se espalha pelas vinhas todas."),
    frozenset(("fogo", "teia")): ("🔥 Fogo + 🕸 Teia", "Reação em cadeia: a teia toda pega fogo."),
    frozenset(("luz", "trevas")): ("✨ Luz + 🌑 Escuridão", "A luz dissipa a escuridão onde ela chega."),
    frozenset(("sagrado", "trevas")): ("☀ Radiante + 🌑 Escuridão", "A luz radiante dissipa a escuridão onde ela chega."),
}


# ====================================================================== geometria
def _area_caminho(caminho) -> float:
    total = 0.0
    for pol in caminho.toFillPolygons():
        n = pol.count()
        s = 0.0
        for i in range(n):
            a, b = pol.at(i), pol.at((i + 1) % n)
            s += a.x() * b.y() - b.x() * a.y()
        total += abs(s) / 2
    return total


def sobreposicao(a, b) -> float:
    """Quanto da MENOR das duas áreas está coberto pela outra (0–1)."""
    ca, cb = a.caminho_cena(), b.caminho_cena()
    if not ca.boundingRect().intersects(cb.boundingRect()):
        return 0.0
    menor = min(_area_caminho(ca), _area_caminho(cb))
    if menor <= 0:
        return 0.0
    return _area_caminho(ca.intersected(cb)) / menor


def assinatura(a, b) -> tuple:
    """Posição/tamanho das duas (o mestre recusou: só pergunta de novo se alguma mudar)."""
    def s(x):
        p = x.scenePos()
        return (x.efeito, round(p.x()), round(p.y()), round(x.tamanho, 2), round(x.largura, 2), round(x.angulo))
    return tuple(sorted((s(a), s(b))))


def procurar(cena, mudadas) -> list:
    """[(par, a, b)] — reações possíveis envolvendo as áreas que mudaram."""
    from .efeitos import EfeitoItem
    todas = [i for i in cena.items() if isinstance(i, EfeitoItem) and i.isVisible()]
    vistas, saida = set(), []
    for a in mudadas:
        if a not in todas:
            continue
        for b in todas:
            if b is a:
                continue
            par = frozenset((a.efeito, b.efeito))
            uids = frozenset((a.uid, b.uid))
            if par not in REACOES or uids in vistas:
                continue
            vistas.add(uids)
            if uids in cena._reagidos or cena._recusados.get(uids) == assinatura(a, b):
                continue
            if sobreposicao(a, b) >= SOBREPOSICAO:
                saida.append((par, a, b))
    return saida


# ====================================================================== aplicar
# Física: reação de CONTATO acontece só onde as áreas se encostam (a água apaga só o pedaço do fogo
# que ela cobre); reação em CADEIA pega a área inteira (o gás todo explode, a poça toda fica
# eletrificada, a vinha toda pega fogo).
EM_CADEIA = {frozenset(("fogo", "veneno")), frozenset(("eletrico", "veneno")), frozenset(("eletrico", "agua")),
             frozenset(("fogo", "planta")), frozenset(("fogo", "teia"))}


def _raio_m_caminho(caminho) -> float:
    r = caminho.boundingRect()
    return max(r.width(), r.height()) / CELULA / 2


def _vapor(cena, caminho, fator, segundos, nome="Vapor"):
    """Nuvem de vapor (área de fumaça que some sozinha) em cima do pedaço que reagiu."""
    c = caminho.boundingRect().center()
    v = cena.criar_efeito({"efeito": "fumaca", "forma": "circulo",
                           "tamanho": max(0.75, _raio_m_caminho(caminho) * fator),
                           "x": c.x(), "y": c.y(), "nome": nome})
    if v is None:   # (no vazio não tem vapor)
        return None
    uid = v.uid
    QTimer.singleShot(int(segundos * 1000), lambda: _sumir(cena, uid))
    return v


def _sumir(cena, uid):
    try:
        cena.remover_efeitos(ids={uid})
    except RuntimeError:   # a cena já foi fechada
        pass


def _tirar(cena, area):
    cena.remover_efeitos(ids={area.uid})


def _cortar(cena, area, caminho):
    """Tira o pedaço da área; se não sobrar quase nada, a área some."""
    if not area.recortar(caminho):
        _tirar(cena, area)


def _pedaco(cena, efeito, caminho, nome, cor=""):
    """Área nova com a forma exata do pedaço que reagiu (ex.: o gelo que derreteu vira água ali)."""
    c = caminho.boundingRect().center()
    pols = []
    for pol in caminho.toFillPolygons():
        pts = [[round(pol.at(i).x() - c.x(), 1), round(pol.at(i).y() - c.y(), 1)] for i in range(pol.count())]
        if len(pts) >= 3:
            pols.append(pts)
    if not pols:
        return None
    return cena.criar_efeito({"efeito": efeito, "forma": "livre", "tamanho": 1, "x": c.x(), "y": c.y(),
                              "pontos": pols, "nome": nome, "cor": cor})


def _marca(cena, caminho, tipo, semente=1):
    """Marca no chão com o contorno do pedaço (lava que virou rocha, gás que queimou o chão)."""
    if cena.terreno is None:
        return
    for k, pol in enumerate(caminho.toFillPolygons()):
        pts = [[round(pol.at(i).x(), 1), round(pol.at(i).y(), 1)] for i in range(pol.count())]
        if len(pts) > 96:
            passo = len(pts) / 96
            pts = [pts[int(i * passo)] for i in range(96)]
        if len(pts) >= 3:
            cena.terreno.adicionar_marca({"t": "marca", "m": "marca", "k": tipo, "p": pts, "s": int(semente) + k})
    cena.registrar()


def aplicar(cena, par, a, b, impacto=None) -> str:
    """Faz a reação. impacto(tipo, x, y, tam) mostra explosão/onda pra todo mundo. Devolve o resumo."""
    por = {a.efeito: a, b.efeito: b}
    titulo = REACOES[par][0]
    encosta = a.caminho_cena().intersected(b.caminho_cena())   # o pedaço onde as duas se encostam

    def bum(tipo, caminho, tam):
        c = caminho.boundingRect().center()
        if impacto is not None:
            impacto(tipo, c.x(), c.y(), tam)

    if par == frozenset(("agua", "fogo")):            # contato: apaga só onde a água cobre
        _vapor(cena, encosta, 1.0, 8)
        _cortar(cena, por["fogo"], encosta)
    elif par == frozenset(("agua", "lava")):          # contato: ali a lava vira rocha e a água evapora
        lava, agua = por["lava"], por["agua"]
        bum("onda", encosta, max(1.0, _raio_m_caminho(encosta)))
        _vapor(cena, encosta, 1.4, 12)
        _marca(cena, encosta, "basalto", lava._semente)
        _cortar(cena, lava, encosta)
        _cortar(cena, agua, encosta)
    elif par in (frozenset(("fogo", "veneno")), frozenset(("eletrico", "veneno"))):   # cadeia: o gás TODO
        gas = por["veneno"]
        nuvem = gas.caminho_cena()
        bum("explosao", nuvem, max(1.5, _raio_m_caminho(nuvem)))
        _marca(cena, nuvem, "queimado", gas._semente)
        _tirar(cena, gas)
    elif par == frozenset(("fogo", "acido")):         # contato: o ácido ferve onde o fogo pega
        acido = por["acido"]
        bum("explosao", encosta, max(0.75, _raio_m_caminho(encosta) * 0.6))
        _pedaco(cena, "veneno", encosta, "Vapor ácido")
        _cortar(cena, acido, encosta)
    elif par == frozenset(("fogo", "gelo")):          # contato: derrete só onde o fogo encosta
        gelo, fogo = por["gelo"], por["fogo"]
        _vapor(cena, encosta, 0.7, 5)
        agua = _pedaco(cena, "agua", encosta, "Gelo derretido")
        if agua is not None:
            cena._reagidos.add(frozenset((agua.uid, fogo.uid)))   # (a água nova não apaga esse fogo sozinha)
        _cortar(cena, gelo, encosta)
    elif par == frozenset(("agua", "gelo")):          # contato: a água que encosta congela (vira parte do gelo)
        _cortar(cena, por["agua"], encosta)
    elif par == frozenset(("eletrico", "agua")):      # cadeia: a poça TODA conduz
        agua = por["agua"]
        p = agua.scenePos()
        novo = cena.criar_efeito({"efeito": "eletrico", "forma": agua.forma, "tamanho": agua.tamanho,
                                  "largura": agua.largura, "angulo": agua.angulo, "x": p.x(), "y": p.y(),
                                  "pontos": agua.pontos, "recortes": agua.recortes,
                                  "nome": "Água eletrificada"})
        if novo is not None:
            cena._reagidos.add(frozenset((novo.uid, agua.uid)))
    elif par in (frozenset(("fogo", "planta")), frozenset(("fogo", "teia"))):   # cadeia: o fogo se espalha
        alvo = por.get("planta") or por.get("teia")
        alvo.aplicar(efeito="fogo", nome="Vinhas em chamas" if alvo.efeito == "planta" else "Teia em chamas")
    elif "trevas" in par:                             # contato: a luz dissipa só onde ilumina
        trevas = por["trevas"]
        bum("onda", encosta, max(0.75, _raio_m_caminho(encosta) * 0.7))
        _cortar(cena, trevas, encosta)
    cena.marcar_modificada()
    return titulo
