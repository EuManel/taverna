"""
Compêndio do Taverna: regras, monstros, magias, itens... do SRD 5.1 de D&D 5e.

O SRD (System Reference Document) é a parte das regras que a Wizards of the Coast
liberou pra uso livre (Creative Commons BY 4.0). Os dados vêm do projeto 5e-database
(licença MIT). Onde existe tradução pt-BR no projeto, ela é usada; o resto vem em inglês,
com os rótulos traduzidos e as distâncias convertidas pra metros (5 pés = 1,5 m).

ATRIBUIÇÃO (obrigatória pela licença):
Este trabalho inclui material do System Reference Document 5.1 ("SRD 5.1") da
Wizards of the Coast LLC, disponível em https://dnd.wizards.com/resources/systems-reference-document.
O SRD 5.1 é licenciado sob a Creative Commons Attribution 4.0 International License,
disponível em https://creativecommons.org/licenses/by/4.0/legalcode.
"""

import html
import json
import os
import re
import unicodedata

from .traducoes import (ANCESTRALIDADE_DRACONICA, CATEGORIAS_EQUIP, CONDICOES, ESCOLAS,
                         PROPRIEDADES, SUBRACAS, SUBTIPOS, TENDENCIAS_EXTRA, TIPO_CA, TRACOS,
                         dano, idiomas, proficiencia, tempo)

PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")

ATRIBUICAO = (
    'Este programa inclui material do <b>System Reference Document 5.1 ("SRD 5.1")</b> da '
    'Wizards of the Coast LLC, disponível em '
    '<a href="https://dnd.wizards.com/resources/systems-reference-document">'
    'dnd.wizards.com/resources/systems-reference-document</a>. O SRD 5.1 é licenciado sob a '
    '<a href="https://creativecommons.org/licenses/by/4.0/legalcode">Creative Commons '
    'Attribution 4.0 International</a>. Dados organizados pelo projeto 5e-database (MIT). '
    'Dungeons &amp; Dragons é marca da Wizards of the Coast; o Taverna não é afiliado a ela.'
)

# ====================================================================== traduções
TAMANHOS = {"Tiny": "Miúdo", "Small": "Pequeno", "Medium": "Médio", "Large": "Grande",
            "Huge": "Enorme", "Gargantuan": "Imenso"}
QUADRADOS_TAMANHO = {"Tiny": 1, "Small": 1, "Medium": 1, "Large": 2, "Huge": 3, "Gargantuan": 4}
TIPOS_CRIATURA = {
    "aberration": "aberração", "beast": "besta", "celestial": "celestial",
    "construct": "constructo", "dragon": "dragão", "elemental": "elemental", "fey": "fada",
    "fiend": "corruptor", "giant": "gigante", "humanoid": "humanoide",
    "monstrosity": "monstruosidade", "ooze": "limo", "plant": "planta", "undead": "morto-vivo",
    "swarm of Tiny beasts": "enxame de bestas miúdas",
}
ATRIBUTOS = [("strength", "FOR"), ("dexterity", "DES"), ("constitution", "CON"),
             ("intelligence", "INT"), ("wisdom", "SAB"), ("charisma", "CAR")]
DESLOCAMENTO = {"walk": "", "fly": "voo", "swim": "natação", "climb": "escalada",
                "burrow": "escavação", "hover": "flutuar"}
SENTIDOS = {"darkvision": "visão no escuro", "blindsight": "percepção às cegas",
            "tremorsense": "sentido sísmico", "truesight": "visão verdadeira",
            "passive_perception": "Percepção passiva"}
RARIDADE = {"Common": "comum", "Uncommon": "incomum", "Rare": "raro", "Very Rare": "muito raro",
            "Legendary": "lendário", "Artifact": "artefato", "Varies": "variável"}
MOEDA = {"cp": "PC", "sp": "PP", "ep": "PE", "gp": "PO", "pp": "PL"}

CATEGORIAS = [
    # chave, nome exibido, só mestre?
    ("monstros", "👹 Monstros", True),
    ("magias", "✨ Magias", False),
    ("condicoes", "🩸 Condições", False),
    ("racas", "🧝 Raças", False),
    ("classes", "⚔ Classes", False),
    ("habilidades", "📜 Habilidades de classe", False),
    ("antecedentes", "📖 Antecedentes", False),
    ("talentos", "🎖 Talentos", False),
    ("equipamento", "🛡 Equipamento", False),
    ("itens_magicos", "💎 Itens mágicos", False),
    ("regras", "📚 Regras", False),
    ("pericias", "🎯 Perícias", False),
    ("atributos", "💪 Atributos", False),
    ("idiomas", "🗣 Idiomas", False),
    ("tipos_dano", "💥 Tipos de dano", False),
    ("escolas", "🔮 Escolas de magia", False),
    ("tendencias", "⚖ Tendências", False),
]


_NOMES = None


def _nomes():
    global _NOMES
    if _NOMES is None:
        caminho = os.path.join(PASTA, "pt-taverna", "nomes.json")
        _NOMES = json.load(open(caminho, encoding="utf-8")) if os.path.exists(caminho) else {}
    return _NOMES


def _traduzir_ref(ref, arquivo):
    """Troca o nome de uma referência {"index","name"} pelo nome traduzido."""
    if isinstance(ref, dict) and "index" in ref:
        pt = _nomes().get(arquivo, {}).get(ref["index"])
        if pt:
            return dict(ref, name=pt)
    return ref


def _em_ingles() -> bool:
    try:
        from ..idioma import ingles
        return ingles()
    except Exception:
        return False


def _ler(nome, idioma="en"):
    caminho = os.path.join(PASTA, idioma, f"5e-SRD-{nome}.json")
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    if idioma != "en" or _em_ingles():   # (v1.0) Taverna em inglês: o SRD original, sem tradução
        return dados
    # tradução do Taverna: nomes + (quando houver) textos completos
    nomes = _nomes().get(nome, {})
    textos = {}
    caminho_pt = os.path.join(PASTA, "pt-taverna", f"{nome}.json")
    if os.path.exists(caminho_pt):
        with open(caminho_pt, encoding="utf-8") as f:
            textos = json.load(f)
    for d in dados:
        i = d.get("index")
        if i in nomes:
            d["name_en"] = d["name"]
            d["name"] = nomes[i]
        for campo, valor in textos.get(i, {}).items():
            d[campo] = valor
        d["_texto_pt"] = i in textos
        # referências a outras coisas (classes de uma magia, classe de uma habilidade...)
        if isinstance(d.get("classes"), list):
            d["classes"] = [_traduzir_ref(c, "Classes") for c in d["classes"]]
        if isinstance(d.get("class"), dict):
            d["class"] = _traduzir_ref(d["class"], "Classes")
        if isinstance(d.get("subclass"), dict):
            d["subclass"] = _traduzir_ref(d["subclass"], "Subclasses")
    return dados


def _original(d) -> str:
    """Mostra o nome em inglês, pra quem usa material em inglês, e avisa se o texto ainda não foi traduzido."""
    if not (d.get("name_en") and d["name_en"] != d["name"]):
        return ""
    aviso = ("" if d.get("_texto_pt") or not (d.get("desc") or d.get("actions"))
             else " · <span style='color:#b0703a'>descrição ainda em inglês (tradução em andamento)</span>")
    return f"<p class='orig'><i>Original: {html.escape(d['name_en'])}</i>{aviso}</p>"


def _preferir_pt(nome):
    """Usa a versão pt-BR quando existe (pelo 'index'), senão a inglesa."""
    en = _ler(nome, "en")
    if _em_ingles() and en:
        return en
    pt = {d["index"]: d for d in _ler(nome, "pt-BR")}
    return [pt.get(d["index"], d) for d in en] or list(pt.values())


def sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower())
                   if unicodedata.category(c) != "Mn")


def metros(texto) -> str:
    """'30 ft.' -> '9 m' · '120 feet' -> '36 m' (5 pés = 1,5 m)."""
    if not isinstance(texto, str):
        return str(texto)

    def conv(pes_txt):
        valor = float(pes_txt.replace(",", "")) / 5 * 1.5
        return f"{valor:g}".replace(".", ",")

    # alcance duplo: "80/320 ft." -> "24/96 m"
    texto = re.sub(r"(\d[\d,]*)/(\d[\d,]*)[ -](?:ft\.?|feet|foot)",
                   lambda m: f"{conv(m.group(1))}/{conv(m.group(2))} m", texto)
    return re.sub(r"(\d[\d,]*)[ -](?:ft\.?|feet|foot)", lambda m: conv(m.group(1)) + " m", texto)


def _e(t) -> str:
    return html.escape(str(t))


def _paragrafos(desc) -> str:
    if isinstance(desc, list):
        return "".join(_md(metros(p)) for p in desc)
    return _md(metros(desc or ""))


def _md(texto: str) -> str:
    """Markdown bem simples -> HTML (títulos, negrito, itálico, tabelas, listas)."""
    linhas = texto.split("\n")
    saida, tabela = [], []

    def fecha_tabela():
        if tabela:
            linhas_t = [l for l in tabela if not re.match(r"^\s*\|?\s*:?-{2,}", l)]
            h = "<table cellspacing='0' cellpadding='4' class='tab'>"
            for k, l in enumerate(linhas_t):
                cel = [c.strip() for c in l.strip().strip("|").split("|")]
                tag = "th" if k == 0 else "td"
                h += "<tr>" + "".join(f"<{tag}>{_inline(c)}</{tag}>" for c in cel) + "</tr>"
            saida.append(h + "</table>")
            tabela.clear()

    for l in linhas:
        if l.strip().startswith("|"):
            tabela.append(l)
            continue
        fecha_tabela()
        m = re.match(r"^(#{1,6})\s*(.*)", l)
        if m:
            n = min(4, len(m.group(1)) + 1)
            saida.append(f"<h{n}>{_inline(m.group(2))}</h{n}>")
        elif l.strip().startswith(("- ", "* ", "• ")):
            saida.append(f"<p style='margin-left:12px'>• {_inline(l.strip()[2:])}</p>")
        elif l.strip():
            saida.append(f"<p>{_inline(l)}</p>")
    fecha_tabela()
    return "".join(saida)


def _inline(t: str) -> str:
    t = _e(t)
    t = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*(?!\s)(.+?)\*", r"<i>\1</i>", t)
    return t


def _mod(valor: int) -> str:
    m = (valor - 10) // 2
    return f"+{m}" if m >= 0 else str(m)


def _cr(cr) -> str:
    return {0.125: "1/8", 0.25: "1/4", 0.5: "1/2"}.get(cr, f"{cr:g}")


# ====================================================================== formatadores
_TENDENCIAS = None


def tendencia(texto: str) -> str:
    global _TENDENCIAS
    if _em_ingles():
        return texto or ""
    if _TENDENCIAS is None:
        _TENDENCIAS = {d["index"]: d["name"] for d in _ler("Alignments", "pt-BR")}
        _TENDENCIAS.update({"unaligned": "sem tendência", "any-alignment": "qualquer tendência",
                            "any-evil-alignment": "qualquer tendência maligna"})
    if (texto or "").lower() in TENDENCIAS_EXTRA:
        return TENDENCIAS_EXTRA[texto.lower()]
    chave = (texto or "").lower().replace(" ", "-")
    return _TENDENCIAS.get(chave, texto or "")


def _html_monstro(m) -> str:
    tam = TAMANHOS.get(m.get("size"), m.get("size"))
    tipo = TIPOS_CRIATURA.get(m.get("type"), m.get("type"))
    if m.get("subtype"):
        tipo += f" ({SUBTIPOS.get(m['subtype'], m['subtype'])})"
    ca = ", ".join(f"{a['value']}" + (f" ({TIPO_CA.get(a['type'], a['type'])})"
                                      if TIPO_CA.get(a.get("type"), "") else "")
                   for a in m.get("armor_class", []))
    desl = ", ".join((f"{DESLOCAMENTO.get(k, k)} " if DESLOCAMENTO.get(k, k) else "") + metros(v)
                     for k, v in m.get("speed", {}).items() if isinstance(v, str))
    atrib = "".join(f"<td align='center'><b>{ab}</b><br>{m.get(chave, 10)} ({_mod(m.get(chave, 10))})</td>"
                    for chave, ab in ATRIBUTOS)
    prof = ", ".join(f"{proficiencia(p['proficiency']['name'])} +{p['value']}"
                     for p in m.get("proficiencies", []))
    sentidos = ", ".join(f"{SENTIDOS.get(k, k)} {metros(v)}" for k, v in m.get("senses", {}).items())
    linhas = [
        f"<h2>{_e(m['name'])}</h2>{_original(m)}",
        f"<p><i>{tam} · {tipo} · {_e(tendencia(m.get('alignment', '')))}</i></p><hr>",
        f"<p><b>Classe de Armadura</b> {ca}<br>"
        f"<b>Pontos de Vida</b> {m.get('hit_points')} ({m.get('hit_points_roll', m.get('hit_dice'))})<br>"
        f"<b>Deslocamento</b> {desl}</p><hr>",
        f"<table width='100%'><tr>{atrib}</tr></table><hr>",
    ]
    extras = []
    if prof:
        extras.append(f"<b>Testes e perícias</b> {_e(prof)}")
    for chave, nome in (("damage_vulnerabilities", "Vulnerável a"),
                        ("damage_resistances", "Resistente a"),
                        ("damage_immunities", "Imune a dano")):
        if m.get(chave):
            extras.append(f"<b>{nome}</b> {_e('; '.join(dano(x) for x in m[chave]))}")
    if m.get("condition_immunities"):
        extras.append("<b>Imune a condições</b> " +
                      _e(", ".join(CONDICOES.get(c["index"], c["name"]) for c in m["condition_immunities"])))
    extras.append(f"<b>Sentidos</b> {_e(sentidos)}")
    extras.append(f"<b>Idiomas</b> {_e(idiomas(metros(m.get('languages') or '')))}")
    extras.append(f"<b>Nível de Desafio</b> {_cr(m.get('challenge_rating', 0))} "
                  f"({m.get('xp', 0)} XP) · <b>Proficiência</b> +{m.get('proficiency_bonus', 2)}")
    linhas.append("<p>" + "<br>".join(extras) + "</p><hr>")
    for titulo, chave in (("", "special_abilities"), ("Ações", "actions"),
                          ("Reações", "reactions"), ("Ações lendárias", "legendary_actions")):
        lista = m.get(chave) or []
        if not lista:
            continue
        if titulo:
            linhas.append(f"<h3>{titulo}</h3>")
        for a in lista:
            linhas.append(f"<p><b><i>{_e(a['name'])}.</i></b> {_inline(metros(a.get('desc', '')))}</p>")
    return "".join(linhas)


def _html_magia(s) -> str:
    nivel = "Truque" if s.get("level") == 0 else f"{s.get('level')}º nível"
    escola = ESCOLAS.get(s.get("school", {}).get("name", ""), s.get("school", {}).get("name", ""))
    comp = ", ".join(s.get("components", []))
    if s.get("material"):
        comp += f" ({s['material']})"
    linhas = [
        f"<h2>{_e(s['name'])}</h2>{_original(s)}",
        f"<p><i>{nivel} · {_e(escola)}{' · ritual' if s.get('ritual') else ''}</i></p><hr>",
        f"<p><b>Tempo de conjuração</b> {_e(tempo(s.get('casting_time', '')))}<br>"
        f"<b>Alcance</b> {_e(tempo(metros(s.get('range', ''))))}<br>"
        f"<b>Componentes</b> {_e(comp)}<br>"
        f"<b>Duração</b> {'Concentração, ' if s.get('concentration') else ''}"
        f"{_e(tempo(s.get('duration', '')))}<br>"
        f"<b>Classes</b> {_e(', '.join(c['name'] for c in s.get('classes', [])))}</p><hr>",
        _paragrafos(s.get("desc", [])),
    ]
    if s.get("higher_level"):
        linhas.append("<p><b><i>Em níveis superiores.</i></b></p>" + _paragrafos(s["higher_level"]))
    return "".join(linhas)


def _html_generico(d, extra="") -> str:
    return f"<h2>{_e(d['name'])}</h2>{_original(d)}{extra}" + _paragrafos(d.get("desc", ""))


def _html_traco(indice, traits) -> str:
    if indice in TRACOS:
        nome, desc = TRACOS[indice]
    elif indice in traits:
        nome, desc = traits[indice]["name"], traits[indice].get("desc", [])
    else:
        return ""
    corpo = _paragrafos(desc)
    if indice == "draconic-ancestry":
        corpo += ("<table cellspacing='0' cellpadding='4' class='tab'>"
                  "<tr><th>Dragão</th><th>Tipo de dano</th><th>Arma de sopro</th></tr>"
                  + "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>"
                            for a, b, c in ANCESTRALIDADE_DRACONICA) + "</table>")
    return f"<h4>{_e(nome)}</h4>{corpo}"


def _html_raca(r, traits, subracas) -> str:
    bonus = ", ".join(f"{b['ability_score']['name']} +{b['bonus']}" for b in r.get("ability_bonuses", []))
    opc = r.get("ability_bonus_options")
    if opc:
        bonus += f" e +1 em {opc.get('choose', 2)} outros à sua escolha"
    vel = r.get("speed")
    # o arquivo pt-BR já vem em metros; o inglês vem em pés
    desl = (f"{vel:g} m".replace(".", ",") if isinstance(vel, (int, float)) and vel < 20
            else metros(f"{vel} ft."))
    tracos = "".join(_html_traco(t["index"], traits) for t in r.get("traits", []))
    subs = ""
    for sr in r.get("subraces", []):
        if sr["index"] in SUBRACAS:
            nome, desc, sb = SUBRACAS[sr["index"]]
        else:
            d = subracas.get(sr["index"], {})
            nome, desc, sb = sr.get("name", ""), d.get("desc", ""), ""
        tr = "".join(_html_traco(t["index"], traits)
                     for t in subracas.get(sr["index"], {}).get("racial_traits", []))
        subs += (f"<h3>Sub-raça: {_e(nome)}</h3><p>{_e(desc)}</p>"
                 + (f"<p><b>Atributos</b> {_e(sb)}</p>" if sb else "") + tr)
    return (f"<h2>{_e(r['name'])}</h2>"
            f"<p><b>Atributos</b> {_e(bonus)}<br><b>Deslocamento</b> {desl}"
            f"<br><b>Tamanho</b> {_e(TAMANHOS.get(r.get('size'), r.get('size')))}</p>"
            f"<p><b>Idade.</b> {_e(metros(r.get('age', '')))}</p>"
            f"<p><b>Tendência.</b> {_e(r.get('alignment', ''))}</p>"
            f"<p><b>Tamanho.</b> {_e(metros(r.get('size_description', '')))}</p>"
            f"<p><b>Idiomas.</b> {_e(r.get('language_desc', ''))}</p>"
            + (f"<h3>Traços</h3>{tracos}" if tracos else "") + subs)


def _html_classe(c, subclasses) -> str:
    prof = ", ".join(p["name"] for p in c.get("proficiencies", []))
    salv = ", ".join(s["name"] for s in c.get("saving_throws", []))
    escolhas = "".join(f"<p>{_e(p.get('desc', ''))}</p>" for p in c.get("proficiency_choices", []))
    subs = "".join(f"<h3>{_e(s['name'])}</h3>{_paragrafos(s.get('desc', []))}"
                   for s in subclasses if s.get("class", {}).get("index") == c["index"])
    equip = ", ".join(f"{e['quantity']}× {e['equipment']['name']}" for e in c.get("starting_equipment", []))
    return (f"<h2>{_e(c['name'])}</h2>{_original(c)}"
            f"<p><b>Dado de vida</b> d{c.get('hit_die')}<br><b>Testes de resistência</b> {_e(salv)}"
            f"<br><b>Proficiências</b> {_e(prof)}</p>{escolhas}"
            f"<p><b>Equipamento inicial</b> {_e(equip or '—')}</p>"
            f"<h3>Subclasses (SRD)</h3>{subs or '<p>—</p>'}")


def _html_equipamento(e) -> str:
    custo = e.get("cost") or {}
    preco = f"{custo.get('quantity', '')} {MOEDA.get(custo.get('unit'), custo.get('unit', ''))}"
    linhas = [f"<h2>{_e(e['name'])}</h2>{_original(e)}",
              f"<p><i>{_e(CATEGORIAS_EQUIP.get(e.get('equipment_category', {}).get('name', ''), e.get('equipment_category', {}).get('name', '')))}</i></p>",
              f"<p><b>Preço</b> {_e(preco)} · <b>Peso</b> "
              + (f"{e['weight'] * 0.45:.1f} kg".replace(".", ",") if e.get("weight") else "—") + "</p>"]
    if e.get("damage"):
        linhas.append(f"<p><b>Dano</b> {_e(e['damage'].get('damage_dice', ''))} "
                      f"{_e(dano(e['damage'].get('damage_type', {}).get('index', '')))}</p>")
    if e.get("armor_class"):
        ac = e["armor_class"]
        linhas.append(f"<p><b>CA</b> {ac.get('base')}"
                      f"{' + mod. Des' if ac.get('dex_bonus') else ''}"
                      + (f" (máx. {ac.get('max_bonus')})" if ac.get("max_bonus") else "")
                      + "</p>")
    if e.get("range") and isinstance(e["range"], dict):
        r = e["range"]
        linhas.append(f"<p><b>Alcance</b> {metros(str(r.get('normal', '')) + ' ft.')}"
                      + (f" / {metros(str(r['long']) + ' ft.')}" if r.get("long") else "") + "</p>")
    if e.get("properties"):
        linhas.append("<p><b>Propriedades</b> " + _e(", ".join(PROPRIEDADES.get(p["name"], p["name"])
                                                               for p in e["properties"])) + "</p>")
    linhas.append(_paragrafos(e.get("desc", [])))
    return "".join(linhas)


# ====================================================================== índice
class Compendio:
    """Carrega tudo uma vez e oferece busca por categoria."""

    def __init__(self):
        self.entradas: dict[str, list[dict]] = {c: [] for c, _, _ in CATEGORIAS}
        self._carregar()

    def _add(self, cat, nome, html_fn, extra_busca="", dados=None):
        if dados and dados.get("name_en"):
            extra_busca += " " + dados["name_en"]
        self.entradas[cat].append({
            "nome": nome, "html": html_fn, "busca": sem_acento(nome + " " + extra_busca),
            "dados": dados,
        })

    def _carregar(self):
        for m in _ler("Monsters"):
            tipo = TIPOS_CRIATURA.get(m.get("type"), m.get("type", ""))
            self._add("monstros", m["name"], lambda m=m: _html_monstro(m),
                      f"{tipo} nd {_cr(m.get('challenge_rating', 0))}", dados=m)
        for s in _ler("Spells"):
            self._add("magias", s["name"], lambda s=s: _html_magia(s),
                      f"{s.get('school', {}).get('name', '')} nivel {s.get('level')}", dados=s)
        for c in _preferir_pt("Conditions"):
            self._add("condicoes", c["name"], lambda c=c: _html_generico(c))
        traits = {t["index"]: t for t in _ler("Traits")}
        subracas = {x["index"]: x for x in _ler("Subraces")}
        for r in _preferir_pt("Races"):
            extra = " ".join(SUBRACAS.get(x["index"], ("",))[0] for x in r.get("subraces", []))
            self._add("racas", r["name"], lambda r=r: _html_raca(r, traits, subracas), extra)
        subclasses = _ler("Subclasses")
        for c in _ler("Classes"):
            self._add("classes", c["name"], lambda c=c: _html_classe(c, subclasses), dados=c)
        for f in _ler("Features"):
            classe = f.get("class", {}).get("name", "")
            nivel = f.get("level", "")
            self._add("habilidades", f"{f['name']} ({classe} {nivel})",
                      lambda f=f: _html_generico(f, f"<p><i>{_e(f.get('class', {}).get('name', ''))}"
                                                    f", nível {f.get('level', '')}</i></p>"), dados=f)
        for b in _preferir_pt("Backgrounds"):
            self._add("antecedentes", b["name"],
                      lambda b=b: _html_generico(b, _paragrafos(
                          [f"**{x.get('name', '')}.** " + " ".join(x.get("desc", []))
                           for x in [b.get("feature", {})] if x])))
        for t in _preferir_pt("Feats"):
            self._add("talentos", t["name"], lambda t=t: _html_generico(t))
        for e in _ler("Equipment"):
            self._add("equipamento", e["name"], lambda e=e: _html_equipamento(e),
                      e.get("equipment_category", {}).get("name", ""), dados=e)
        for i in _ler("Magic-Items"):
            rar = RARIDADE.get(i.get("rarity", {}).get("name"), "")
            self._add("itens_magicos", i["name"],
                      lambda i=i, rar=rar: _html_generico(i, f"<p><i>{_e(rar)}</i></p>"), rar, dados=i)
        for r in _ler("Rule-Sections"):
            self._add("regras", r["name"], lambda r=r: _original(r) + _md(metros(r.get("desc", ""))),
                      r.get("name_en", ""))
        for chave, arquivo in (("pericias", "Skills"), ("atributos", "Ability-Scores"),
                               ("idiomas", "Languages"), ("tipos_dano", "Damage-Types"),
                               ("escolas", "Magic-Schools"), ("tendencias", "Alignments")):
            for d in _preferir_pt(arquivo):
                nome = d.get("full_name") or d["name"]
                self._add(chave, nome, lambda d=d, nome=nome: _html_generico(dict(d, name=nome)))
        for lista in self.entradas.values():
            lista.sort(key=lambda e: sem_acento(e["nome"]))

    def categorias(self, mestre: bool):
        return [(c, n) for c, n, so_mestre in CATEGORIAS if mestre or not so_mestre]

    def buscar(self, categoria: str, texto: str = ""):
        termo = sem_acento(texto.strip())
        lista = self.entradas.get(categoria, [])
        if not termo:
            return lista
        return [e for e in lista if termo in e["busca"]]


_unico = None


def compendio() -> Compendio:
    """Carrega uma vez só (é rápido, mas não precisa repetir)."""
    global _unico
    lingua = "en" if _em_ingles() else "pt"
    if _unico is None or getattr(_unico, "_lingua", None) != lingua:   # (v1.0) trocou o idioma: recarrega
        _unico = Compendio()
        _unico._lingua = lingua
    return _unico
