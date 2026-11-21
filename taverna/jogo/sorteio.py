"""
Recompensa aleatória (Etapa 12): baú/objeto que sorteia o conteúdo quando alguém abre pela primeira vez.

O mestre configura (chance de vir vazio, moedas, quantos itens, tipos, raridade máxima)
e o primeiro jogador que abrir recebe o sorteio. Pode vir um pão, 3 PO, uma poção de cura,
uma espada +1… ou nada.

Itens: equipamentos e itens mágicos do SRD 5.1 (CC-BY, já embutidos no compêndio) +
uma listinha de comidas e bugigangas do próprio Taverna.
"""

import random

from .dados import rolar

RARIDADES = ["comum", "incomum", "rara", "muito rara", "lendária"]
_RARIDADE_EN = {"Common": "comum", "Uncommon": "incomum", "Rare": "rara", "Very Rare": "muito rara",
                "Legendary": "lendária"}
_PESO_RARIDADE = {"comum": 10, "incomum": 5, "rara": 2, "muito rara": 0.6, "lendária": 0.15}

MOEDAS = {
    "nenhuma": "Sem moedas",
    "poucas": "Poucas (trocados)",
    "medias": "Médias (bolsa de viajante)",
    "muitas": "Muitas (cofre de mercador)",
    "tesouro": "Tesouro (covil de monstro)",
    "personalizado": "Personalizado (você escolhe os dados)",
}

TIPOS = {
    "comida": ("🍞 Comida e bebida", 25),
    "bugigangas": ("🪶 Bugigangas", 18),
    "equipamento": ("🎒 Equipamento de aventura", 18),
    "armas": ("⚔ Armas", 10),
    "armaduras": ("🛡 Armaduras", 5),
    "pocoes": ("🧪 Poções", 14),
    "magicos": ("✨ Itens mágicos", 8),
    "proprios": ("📝 Meus itens (lista abaixo)", 20),
}

# Do próprio Taverna (não vem de livro nenhum)
COMIDAS = [
    ("Pão", "Um pão meio duro, mas ainda dá pra comer."), ("Pão preto", "Pesado e escuro, de centeio."),
    ("Queijo curado", "Um pedaço embrulhado em pano."), ("Maçã", "Vermelha, sem bichos (por enquanto)."),
    ("Carne seca", "Salgada demais. Dá sede."), ("Odre de vinho", "Vinho barato, mas é vinho."),
    ("Cantil de água", "Água fresca."), ("Biscoitos de viagem", "Duros como pedra, duram meses."),
    ("Pote de mel", "Fechado com cera."), ("Cogumelos secos", "Parecem comestíveis… parecem."),
    ("Garrafa de hidromel", "Doce e forte."), ("Peixe defumado", "O cheiro chega antes de você abrir."),
    ("Ração de viagem (1 dia)", "Comida pra um dia de estrada."), ("Saquinho de nozes", "Um punhado de nozes."),
]
BUGIGANGAS = [
    ("Dado de osso", "Um dado viciado que sempre cai no 1?"), ("Anel de latão", "Sem valor, mas bonito."),
    ("Carta de amor rasgada", "A assinatura está ilegível."), ("Pena de corvo", "Preta e brilhante."),
    ("Chave enferrujada", "Não se sabe o que ela abre."), ("Moeda estrangeira", "De um reino que ninguém conhece."),
    ("Boneco de pano", "Falta um olho de botão."), ("Mapa borrado", "Mostra um X… mas onde?"),
    ("Dente de lobo", "Furado pra virar colar."), ("Pedra lisa de rio", "Agradável de segurar."),
    ("Vela pela metade", "Ainda acende."), ("Frasco vazio", "Tem um cheiro estranho."),
    ("Pedaço de giz", "Bom pra marcar paredes."), ("Medalhão sem foto", "Abre e fecha. Está vazio."),
    ("Gaita de madeira", "Toca uma nota só."), ("Livro de orações", "Faltam algumas páginas."),
]
_FRASES_VAZIO = ["Só poeira e teias de aranha.", "Vazio. Alguém chegou antes.", "Nada além de um cheiro de mofo.",
                 "Está vazio… ou será que tem fundo falso?"]


def config_padrao() -> dict:
    return {"ativo": True, "vazio": 15, "moedas": "poucas", "itens_min": 0, "itens_max": 2,
            "tipos": {k: k not in ("magicos", "proprios") for k in TIPOS}, "raridade_max": "incomum",
            "moedas_dados": {"PC": "", "PP": "", "PO": "1d6", "PL": ""},
            "proprios": "",   # um por linha: "Nome", "Nome ×3" ou "Nome | descrição"
            "tabela": None,   # tabela personalizada (cópia) — no lugar dos itens do D&D
            "sorteado": False, "resultado": ""}


_NOMES_MOEDA = {"PC": "Moedas de cobre (PC)", "PP": "Moedas de prata (PP)", "PO": "Moedas de ouro (PO)",
                "PL": "Moedas de platina (PL)"}


def itens_proprios(texto: str) -> list[tuple]:
    """Lê a lista do mestre: 'Amuleto do culto', 'Flecha ×10', 'Carta | Selada com cera'."""
    import re
    saida = []
    for linha in (texto or "").splitlines():
        linha = linha.strip()
        if not linha:
            continue
        nome, _, desc = linha.partition("|")
        qtd = 1
        m = re.search(r"\s*[x×]\s*(\d+)\s*$", nome.strip(), re.IGNORECASE)
        if m:
            qtd = int(m.group(1))
            nome = nome.strip()[:m.start()]
        if nome.strip():
            saida.append((nome.strip(), desc.strip(), qtd))
    return saida


# ------------------------------------------------------------------ dados do SRD (carrega uma vez)
_SRD = None


def _srd():
    global _SRD
    if _SRD is not None:
        return _SRD
    from ..compendio.compendio import _ler
    equip = _ler("Equipment")
    magicos = _ler("Magic-Items")
    porcat = {"equipamento": [], "armas": [], "armaduras": []}
    for e in equip:
        cat = e.get("equipment_category", {}).get("name")
        if cat == "Adventuring Gear":
            porcat["equipamento"].append(e)
        elif cat == "Weapon":
            porcat["armas"].append(e)
        elif cat == "Armor":
            porcat["armaduras"].append(e)
    pocoes, outros = [], []
    for m in magicos:
        rar = _RARIDADE_EN.get(m.get("rarity", {}).get("name"))
        if not rar:   # "Varies" (tem as variantes separadas) e artefatos ficam de fora
            continue
        (pocoes if m.get("equipment_category", {}).get("name") == "Potion" else outros).append((m, rar))
    _SRD = {"porcat": porcat, "pocoes": pocoes, "magicos": outros}
    return _SRD


def _custo(e) -> str:
    c = e.get("cost") or {}
    unidade = {"cp": "PC", "sp": "PP", "ep": "PE", "gp": "PO", "pp": "PL"}.get(c.get("unit"), "")
    return f"{c.get('quantity')} {unidade}" if c.get("quantity") is not None and unidade else ""


def _desc_equip(e) -> str:
    partes = []
    if e.get("damage"):
        d = e["damage"]
        partes.append(f"{d.get('damage_dice', '')} de dano")
    if e.get("armor_class"):
        partes.append(f"CA {e['armor_class'].get('base')}" + (" + Des" if e["armor_class"].get("dex_bonus") else ""))
    custo = _custo(e)
    if custo:
        partes.append(f"vale {custo}")
    return " · ".join(partes)


def _item(nome, desc="", qtd=1, srd=None) -> dict:
    from ..mesa.props import novo_id_item
    d = {"id": novo_id_item(), "nome": nome, "qtd": int(qtd), "desc": desc, "img": None}
    if srd:
        d["srd"] = srd
    return d


def _magico(lista, raridade_max, rnd):
    limite = RARIDADES.index(raridade_max) if raridade_max in RARIDADES else 1
    validos = [(m, r) for m, r in lista if RARIDADES.index(r) <= limite]
    if not validos:
        return None
    m, rar = rnd.choices(validos, weights=[_PESO_RARIDADE[r] for _, r in validos])[0]
    nome = m.get("name", "?")
    # "Arma +1" / "Armadura +2": vira uma arma/armadura de verdade do SRD
    idx = m.get("index", "")
    srd = _srd()["porcat"]
    if idx.startswith("weapon-") and srd["armas"]:
        base = rnd.choice(srd["armas"])
        nome = f"{base['name']} +{idx.split('-')[-1]}"
    elif idx.startswith("armor-") and srd["armaduras"]:
        base = rnd.choice(srd["armaduras"])
        nome = f"{base['name']} +{idx.split('-')[-1]}"
    return _item(nome, f"Item mágico ({rar}). Detalhes no compêndio.", 1, ["Magic-Items", idx])


def _moedas(nivel, rnd) -> list[dict]:
    tabela = {
        "poucas": [("1d8", "Moedas de cobre (PC)", 0.6), ("1d4", "Moedas de prata (PP)", 0.35),
                   ("1d3", "Moedas de ouro (PO)", 0.2)],
        "medias": [("2d6", "Moedas de prata (PP)", 0.7), ("1d6+1", "Moedas de ouro (PO)", 0.7),
                   ("3d6", "Moedas de cobre (PC)", 0.4)],
        "muitas": [("3d6", "Moedas de ouro (PO)", 1.0), ("4d6", "Moedas de prata (PP)", 0.8),
                   ("1d4", "Moedas de platina (PL)", 0.15)],
        "tesouro": [("4d6*10", "Moedas de ouro (PO)", 1.0), ("2d6*10", "Moedas de prata (PP)", 0.9),
                    ("1d6", "Moedas de platina (PL)", 0.5)],
    }.get(nivel, [])
    saida = []
    for expr, nome, chance in tabela:
        if rnd.random() < chance:
            mult = 1
            if "*" in expr:
                expr, m = expr.split("*")
                mult = int(m)
            qtd = rolar(expr, rnd)["total"] * mult
            if qtd > 0:
                saida.append(_item(nome, "", qtd))
    return saida


def _qtd(expr, rnd) -> int:
    expr = str(expr or "1").strip()
    try:
        return max(0, int(expr))
    except ValueError:
        try:
            return max(0, rolar(expr, rnd)["total"])
        except Exception:
            return 1


def _juntar(itens, rnd):
    juntos = []
    for it in itens:
        igual = next((j for j in juntos if j["nome"] == it["nome"] and j.get("desc") == it.get("desc")), None)
        if igual:
            igual["qtd"] += it["qtd"]
        else:
            juntos.append(it)
    if not juntos:
        return [], rnd.choice(_FRASES_VAZIO)
    return juntos, ", ".join(f"{i['nome']}" + (f" ×{i['qtd']}" if i["qtd"] > 1 else "") for i in juntos)


def _sortear_tabela(cfg, tabela, rnd):
    """Sorteio com a tabela personalizada do mestre (qualquer sistema)."""
    from .tabelas import CHANCES
    itens = []
    moeda = (tabela.get("moeda") or "").strip()
    if moeda and (tabela.get("moeda_dados") or "").strip():
        q = _qtd(tabela["moeda_dados"], rnd)
        if q > 0:
            itens.append(_item(moeda, "", q))
    linhas = [l for l in tabela.get("linhas") or [] if l.get("nome")]
    linhas += [{"nome": n, "desc": d, "qtd": str(q), "chance": "comum"}
               for n, d, q in itens_proprios(cfg.get("proprios", ""))]
    lo, hi = int(cfg.get("itens_min", 0)), int(cfg.get("itens_max", 2))
    n = rnd.randint(min(lo, hi), max(lo, hi)) if linhas else 0
    for _ in range(n):
        l = rnd.choices(linhas, weights=[CHANCES.get(x.get("chance", "comum"), 10) for x in linhas])[0]
        q = _qtd(l.get("qtd", "1"), rnd)
        if q > 0:
            itens.append(_item(l["nome"], l.get("desc", ""), q))
    return _juntar(itens, rnd)


def sortear(config: dict, rnd: random.Random | None = None) -> tuple[list[dict], str]:
    """Devolve (itens, resumo). Lista vazia = não veio nada."""
    rnd = rnd or random.Random()
    cfg = dict(config_padrao(), **(config or {}))
    if rnd.random() * 100 < float(cfg.get("vazio", 0)):
        return [], rnd.choice(_FRASES_VAZIO)
    tabela = cfg.get("tabela")
    if tabela:
        return _sortear_tabela(cfg, tabela, rnd)
    if cfg.get("moedas") == "personalizado":
        itens = []
        for sigla, expr in (cfg.get("moedas_dados") or {}).items():
            expr = (expr or "").strip()
            if expr and sigla in _NOMES_MOEDA:
                try:
                    qtd = rolar(expr, rnd)["total"]
                except Exception:
                    continue
                if qtd > 0:
                    itens.append(_item(_NOMES_MOEDA[sigla], "", qtd))
    else:
        itens = _moedas(cfg.get("moedas", "nenhuma"), rnd)
    proprios = itens_proprios(cfg.get("proprios", ""))
    tipos = [k for k, ligado in (cfg.get("tipos") or {}).items() if ligado and k in TIPOS
             and (k != "proprios" or proprios)]
    lo, hi = int(cfg.get("itens_min", 0)), int(cfg.get("itens_max", 2))
    n = rnd.randint(min(lo, hi), max(lo, hi)) if tipos else 0
    srd = _srd()
    for _ in range(n):
        tipo = rnd.choices(tipos, weights=[TIPOS[t][1] for t in tipos])[0]
        if tipo == "comida":
            nome, desc = rnd.choice(COMIDAS)
            itens.append(_item(nome, desc, rnd.choice([1, 1, 1, 2, 3])))
        elif tipo == "bugigangas":
            nome, desc = rnd.choice(BUGIGANGAS)
            itens.append(_item(nome, desc))
        elif tipo in ("equipamento", "armas", "armaduras"):
            lista = srd["porcat"][tipo]
            if lista:
                e = rnd.choice(lista)
                qtd = rnd.randint(5, 20) if e.get("gear_category", {}).get("index") == "ammunition" else 1
                itens.append(_item(e["name"], _desc_equip(e), qtd, ["Equipment", e.get("index")]))
        elif tipo == "pocoes":
            it = _magico(srd["pocoes"], cfg.get("raridade_max", "incomum"), rnd)
            if it:
                itens.append(it)
        elif tipo == "proprios":
            nome, desc, qtd = rnd.choice(proprios)
            itens.append(_item(nome, desc, qtd))
        elif tipo == "magicos":
            it = _magico(srd["magicos"], cfg.get("raridade_max", "incomum"), rnd)
            if it:
                itens.append(it)
    # junta repetidos (2 pães = "Pão ×2")
    juntos = []
    for it in itens:
        igual = next((j for j in juntos if j["nome"] == it["nome"] and j.get("desc") == it.get("desc")), None)
        if igual:
            igual["qtd"] += it["qtd"]
        else:
            juntos.append(it)
    if not juntos:
        return [], rnd.choice(_FRASES_VAZIO)
    resumo = ", ".join(f"{i['nome']}" + (f" ×{i['qtd']}" if i["qtd"] > 1 else "") for i in juntos)
    return juntos, resumo
