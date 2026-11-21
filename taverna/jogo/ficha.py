"""
Ficha de personagem D&D 5e.

A ficha mora no token (token.ficha). Alguns campos são os MESMOS do painel de informações
(token.info) — PV, deslocamento, raça, classe e inventário — então o que o mestre muda lá
(dano, item pego do baú...) aparece na ficha, e vice-versa.

PDF:
- importar_pdf(): lê uma ficha preenchível (a oficial do D&D 5e ou parecida) pelos nomes dos campos.
- preencher_pdf_oficial(): escreve a ficha num PDF preenchível que a pessoa já tem.
- O PDF "do Taverna" (layout próprio) é gerado na interface (ui/janela_ficha.py).
"""

import copy
import re

ATRIBUTOS = [("for", "Força", "FOR"), ("des", "Destreza", "DES"), ("con", "Constituição", "CON"),
             ("int", "Inteligência", "INT"), ("sab", "Sabedoria", "SAB"), ("car", "Carisma", "CAR")]

PERICIAS = [  # chave, nome, atributo
    ("acrobacia", "Acrobacia", "des"), ("adestrar", "Adestrar Animais", "sab"),
    ("arcanismo", "Arcanismo", "int"), ("atletismo", "Atletismo", "for"),
    ("atuacao", "Atuação", "car"), ("enganacao", "Enganação", "car"),
    ("furtividade", "Furtividade", "des"), ("historia", "História", "int"),
    ("intimidacao", "Intimidação", "car"), ("intuicao", "Intuição", "sab"),
    ("investigacao", "Investigação", "int"), ("medicina", "Medicina", "sab"),
    ("natureza", "Natureza", "int"), ("percepcao", "Percepção", "sab"),
    ("persuasao", "Persuasão", "car"), ("prestidigitacao", "Prestidigitação", "des"),
    ("religiao", "Religião", "int"), ("sobrevivencia", "Sobrevivência", "sab"),
]

# atributo de conjuração por classe (SRD)
CONJURACAO = {"bardo": "car", "bruxo": "car", "feiticeiro": "car", "paladino": "car",
              "clérigo": "sab", "clerigo": "sab", "druida": "sab", "patrulheiro": "sab",
              "mago": "int"}
DADO_VIDA = {"bárbaro": 12, "barbaro": 12, "guerreiro": 10, "paladino": 10, "patrulheiro": 10,
             "bardo": 8, "clérigo": 8, "clerigo": 8, "druida": 8, "monge": 8, "ladino": 8, "bruxo": 8,
             "feiticeiro": 6, "mago": 6}


def ficha_vazia() -> dict:
    return {
        "nome": "", "jogador": "", "classe": "", "nivel": 1, "subclasse": "", "raca": "",
        "antecedente": "", "tendencia": "", "xp": 0, "inspiracao": False,
        "atributos": {k: 10 for k, _, _ in ATRIBUTOS},
        "salvaguardas": [], "pericias": [], "especialista": [],
        "ca": 10, "pv_temp": 0, "dados_vida": "", "morte_sucessos": 0, "morte_falhas": 0,
        "ataques": [],              # {"nome", "bonus", "dano"}
        "conjuracao_atrib": "", "magias": [],     # {"nome", "nivel", "preparada"}
        "espacos": {str(n): [0, 0] for n in range(1, 10)},   # nível: [usados, total]
        "moedas": {"pc": 0, "pp": 0, "pe": 0, "po": 0, "pl": 0},
        "idiomas_prof": "", "caracteristicas": "",
        "personalidade": "", "ideais": "", "vinculos": "", "defeitos": "",
        "aparencia": "", "historia": "", "notas": "",
    }


def completar(ficha: dict | None) -> dict:
    """Garante todos os campos (fichas antigas / importadas)."""
    base = ficha_vazia()
    if not ficha:
        return base
    for k, v in ficha.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k].update(v)
        else:
            base[k] = v
    return base


# ====================================================================== cálculos
def mod(valor) -> int:
    try:
        return (int(valor) - 10) // 2
    except (TypeError, ValueError):
        return 0


def sinal(n: int) -> str:
    return f"+{n}" if n >= 0 else str(n)


def bonus_prof(nivel) -> int:
    try:
        n = max(1, min(20, int(nivel)))
    except (TypeError, ValueError):
        n = 1
    return 2 + (n - 1) // 4


def bonus_pericia(f: dict, chave: str) -> int:
    atrib = next(a for k, _, a in PERICIAS if k == chave)
    b = mod(f["atributos"].get(atrib, 10))
    if chave in f.get("pericias", []):
        b += bonus_prof(f.get("nivel", 1)) * (2 if chave in f.get("especialista", []) else 1)
    return b


def bonus_salvaguarda(f: dict, atrib: str) -> int:
    b = mod(f["atributos"].get(atrib, 10))
    if atrib in f.get("salvaguardas", []):
        b += bonus_prof(f.get("nivel", 1))
    return b


def iniciativa(f: dict) -> int:
    return mod(f["atributos"].get("des", 10))


def percepcao_passiva(f: dict) -> int:
    return 10 + bonus_pericia(f, "percepcao")


def atributo_conjuracao(f: dict) -> str:
    if f.get("conjuracao_atrib"):
        return f["conjuracao_atrib"]
    return CONJURACAO.get((f.get("classe") or "").strip().lower(), "")


def cd_magia(f: dict) -> int | None:
    a = atributo_conjuracao(f)
    return 8 + bonus_prof(f.get("nivel", 1)) + mod(f["atributos"].get(a, 10)) if a else None


def ataque_magia(f: dict) -> int | None:
    a = atributo_conjuracao(f)
    return bonus_prof(f.get("nivel", 1)) + mod(f["atributos"].get(a, 10)) if a else None


# ====================================================================== PDF
def _norm(nome: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (nome or "").lower())


# nome do campo na ficha oficial (normalizado) -> caminho na nossa ficha
CAMPOS_PDF = {
    "charactername": "nome", "playername": "jogador", "background": "antecedente",
    "race": "@raca", "alignment": "tendencia", "xp": "xp", "ac": "ca",
    "speed": "@desl", "hpmax": "@pv_max", "hpcurrent": "@pv", "hptemp": "pv_temp",
    "hdtotal": "dados_vida", "str": "atributos.for", "dex": "atributos.des", "con": "atributos.con",
    "int": "atributos.int", "wis": "atributos.sab", "cha": "atributos.car",
    "personalitytraits": "personalidade", "ideals": "ideais", "bonds": "vinculos", "flaws": "defeitos",
    "proficiencieslang": "idiomas_prof", "featuresandtraits": "caracteristicas",
    "equipment": "@equipamento", "cp": "moedas.pc", "sp": "moedas.pp", "ep": "moedas.pe",
    "gp": "moedas.po", "pp": "moedas.pl", "backstory": "historia", "feattraits": "caracteristicas",
    "spellcastingability2": "@conj", "classlevel": "@classe_nivel",
}
# perícias na ficha oficial
PERICIAS_PDF = {"acrobatics": "acrobacia", "animal": "adestrar", "arcana": "arcanismo",
                "athletics": "atletismo", "performance": "atuacao", "deception": "enganacao",
                "stealth": "furtividade", "history": "historia", "intimidation": "intimidacao",
                "insight": "intuicao", "investigation": "investigacao", "medicine": "medicina",
                "nature": "natureza", "perception": "percepcao", "persuasion": "persuasao",
                "sleightofhand": "prestidigitacao", "religion": "religiao", "survival": "sobrevivencia"}
SALV_PDF = {"ststrength": "for", "stdexterity": "des", "stconstitution": "con",
            "stintelligence": "int", "stwisdom": "sab", "stcharisma": "car"}
CLASSES_EN = {"barbarian": "Bárbaro", "bard": "Bardo", "cleric": "Clérigo", "druid": "Druida",
              "fighter": "Guerreiro", "monk": "Monge", "paladin": "Paladino", "ranger": "Patrulheiro",
              "rogue": "Ladino", "sorcerer": "Feiticeiro", "warlock": "Bruxo", "wizard": "Mago"}


def _numero(texto, padrao=0):
    m = re.search(r"-?\d+", str(texto or ""))
    return int(m.group()) if m else padrao


def ler_campos_pdf(caminho: str) -> dict:
    from pypdf import PdfReader
    leitor = PdfReader(caminho)
    campos = leitor.get_fields() or {}
    saida = {}
    for nome, campo in campos.items():
        valor = campo.get("/V") if isinstance(campo, dict) else None
        if valor is None:
            continue
        saida[nome] = str(valor)
    return saida


def de_campos(campos: dict) -> tuple[dict, dict]:
    """
    Converte os campos de um PDF (nome -> valor) numa ficha.
    Retorna (ficha, extras) onde extras tem o que vai pro token: pv, pv_max, desl (m), raca,
    classe, equipamento (texto).
    """
    f = ficha_vazia()
    extras = {}
    norm = {_norm(k): v for k, v in campos.items()}
    for chave, destino in CAMPOS_PDF.items():
        if chave not in norm or norm[chave] in ("", "/Off", "Off"):
            continue
        valor = norm[chave].strip()
        if destino.startswith("@"):
            extras[destino[1:]] = valor
        elif "." in destino:
            a, b = destino.split(".")
            f[a][b] = _numero(valor, f[a][b])
        elif destino in ("xp", "ca", "pv_temp"):
            f[destino] = _numero(valor, f[destino])
        else:
            f[destino] = valor
    # classe e nível ("Fighter 3", "Mago 5", "Guerreiro nível 2")
    cn = extras.pop("classe_nivel", "")
    if cn:
        m = re.match(r"\s*([^\d/]+?)\s*(?:n[ií]vel\s*)?(\d+)?\s*$", cn, re.IGNORECASE)
        nome = (m.group(1) if m else cn).strip()
        f["classe"] = CLASSES_EN.get(nome.lower(), nome)
        f["nivel"] = int(m.group(2)) if m and m.group(2) else 1
    # perícias e salvaguardas: proficiente se o valor passa do modificador do atributo
    pb = bonus_prof(f["nivel"])
    for chave, nossa in PERICIAS_PDF.items():
        if chave in norm and norm[chave].strip():
            atrib = next(a for k, _, a in PERICIAS if k == nossa)
            valor = _numero(norm[chave], None)
            if valor is None:
                continue
            extra = valor - mod(f["atributos"][atrib])
            if extra >= pb * 2:
                f["pericias"].append(nossa)
                f["especialista"].append(nossa)
            elif extra >= pb:
                f["pericias"].append(nossa)
    for chave, atrib in SALV_PDF.items():
        if chave in norm and norm[chave].strip():
            valor = _numero(norm[chave], None)
            if valor is not None and valor - mod(f["atributos"][atrib]) >= pb:
                f["salvaguardas"].append(atrib)
    # ataques (Wpn Name / Wpn1 AtkBonus / Wpn1 Damage)
    for k, sufixo in enumerate(("", "2", "3"), start=1):
        nome = norm.get(f"wpnname{sufixo}", "").strip()
        if nome:
            f["ataques"].append({"nome": nome, "bonus": norm.get(f"wpn{k}atkbonus", "").strip(),
                                 "dano": norm.get(f"wpn{k}damage", "").strip()})
    # deslocamento: "30" (pés) ou "9 m"
    if "desl" in extras:
        texto = extras["desl"].lower()
        n = _numero(texto, 30)
        extras["desl"] = float(n) if "m" in texto and "ft" not in texto else n / 5 * 1.5
    for k in ("pv", "pv_max"):
        if k in extras:
            extras[k] = _numero(extras[k], 0)
    if "conj" in extras:
        mapa = {"str": "for", "dex": "des", "con": "con", "int": "int", "wis": "sab", "cha": "car",
                "for": "for", "des": "des", "sab": "sab", "car": "car"}
        f["conjuracao_atrib"] = mapa.get(extras.pop("conj").strip().lower()[:3], "")
    return f, extras


def para_campos(f: dict, extras: dict) -> dict:
    """O contrário: nossa ficha -> campos da ficha oficial (pra preencher o PDF)."""
    pb = bonus_prof(f.get("nivel", 1))
    valores = {
        "charactername": f.get("nome", ""), "charactername2": f.get("nome", ""),
        "playername": f.get("jogador", ""), "background": f.get("antecedente", ""),
        "race": extras.get("raca", ""), "alignment": f.get("tendencia", ""), "xp": str(f.get("xp", "")),
        "classlevel": f"{f.get('classe', '')} {f.get('nivel', 1)}".strip(),
        "ac": str(f.get("ca", "")), "initiative": sinal(iniciativa(f)),
        "speed": f"{extras.get('desl', 9):g} m".replace(".", ","),
        "hpmax": str(extras.get("pv_max", "")), "hpcurrent": str(extras.get("pv", "")),
        "hptemp": str(f.get("pv_temp", "") or ""), "hdtotal": f.get("dados_vida", ""),
        "profbonus": sinal(pb), "passive": str(percepcao_passiva(f)),
        "personalitytraits": f.get("personalidade", ""), "ideals": f.get("ideais", ""),
        "bonds": f.get("vinculos", ""), "flaws": f.get("defeitos", ""),
        "proficiencieslang": f.get("idiomas_prof", ""), "featuresandtraits": f.get("caracteristicas", ""),
        "equipment": extras.get("equipamento", ""), "backstory": f.get("historia", ""),
    }
    for chave, nome_pdf in (("for", "str"), ("des", "dex"), ("con", "con"),
                            ("int", "int"), ("sab", "wis"), ("car", "cha")):
        valores[nome_pdf] = str(f["atributos"].get(chave, 10))
        valores[nome_pdf + "mod"] = sinal(mod(f["atributos"].get(chave, 10)))
    for chave, atrib in SALV_PDF.items():
        valores[chave] = sinal(bonus_salvaguarda(f, atrib))
    for chave, nossa in PERICIAS_PDF.items():
        valores[chave] = sinal(bonus_pericia(f, nossa))
    for nome, chave in (("cp", "pc"), ("sp", "pp"), ("ep", "pe"), ("gp", "po"), ("pp", "pl")):
        valores[nome] = str(f["moedas"].get(chave, 0) or "")
    for k, sufixo in enumerate(("", "2", "3"), start=1):
        if k <= len(f.get("ataques", [])):
            a = f["ataques"][k - 1]
            valores[f"wpnname{sufixo}"] = a.get("nome", "")
            valores[f"wpn{k}atkbonus"] = a.get("bonus", "")
            valores[f"wpn{k}damage"] = a.get("dano", "")
    if f.get("magias"):
        valores["attacksspellcasting"] = "Magias: " + ", ".join(m.get("nome", "") for m in f["magias"])
    return valores


def preencher_pdf_oficial(modelo: str, destino: str, f: dict, extras: dict) -> int:
    """Escreve a ficha num PDF preenchível. Retorna quantos campos foram preenchidos."""
    dados, n = preencher_pdf_bytes(modelo, f, extras)
    with open(destino, "wb") as arq:
        arq.write(dados)
    return n


def preencher_pdf_bytes(modelo: str, f: dict, extras: dict) -> tuple[bytes, int]:
    """Mesmo que preencher_pdf_oficial, mas devolve o PDF na memória (pra mostrar na tela)."""
    import io
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import BooleanObject, NameObject
    leitor = PdfReader(modelo)
    escritor = PdfWriter(clone_from=leitor)
    valores = para_campos(f, extras)
    campos = leitor.get_fields() or {}
    por_norma = {}
    for nome in campos:
        por_norma.setdefault(_norm(nome), nome)
    preencher = {por_norma[k]: v for k, v in valores.items() if k in por_norma}
    for pagina in escritor.pages:
        try:
            escritor.update_page_form_field_values(pagina, preencher, auto_regenerate=False)
        except Exception:
            pass
    if "/AcroForm" in escritor._root_object:
        escritor._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)
    buf = io.BytesIO()
    escritor.write(buf)
    return buf.getvalue(), len(preencher)


def copia(f: dict) -> dict:
    return copy.deepcopy(f)
