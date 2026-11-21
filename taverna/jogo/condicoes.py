"""Condições que aparecem no painel de informações e como ícone no token."""

# chave: (nome, ícone)
CONDICOES = {
    "envenenado": ("Envenenado", "🤢"),
    "sangrando": ("Sangrando", "🩸"),
    "ferido": ("Ferido", "🩹"),
    "inconsciente": ("Inconsciente", "💤"),
    "caido": ("Caído", "⬇"),
    "agarrado": ("Agarrado", "✊"),
    "impedido": ("Impedido", "⛓"),
    "atordoado": ("Atordoado", "💫"),
    "paralisado": ("Paralisado", "⚡"),
    "incapacitado": ("Incapacitado", "🚫"),
    "petrificado": ("Petrificado", "🗿"),
    "amedrontado": ("Amedrontado", "😱"),
    "enfeiticado": ("Enfeitiçado", "💘"),
    "cego": ("Cego", "🙈"),
    "surdo": ("Surdo", "🙉"),
    "invisivel": ("Invisível", "👻"),
    "exaustao": ("Exaustão", "😩"),
    "queimando": ("Queimando", "🔥"),
    "molhado": ("Molhado", "💧"),
    "congelado": ("Congelado", "❄"),
    "concentrando": ("Concentrando", "🧠"),
    "abencoado": ("Abençoado", "✨"),
}

# Campos do painel de informações (ordem de exibição)
CAMPOS = [("pv", "Pontos de vida"), ("desl", "Deslocamento"), ("condicoes", "Condições"), ("raca", "Raça"),
          ("classe", "Classe"), ("notas", "Anotações"), ("inventario", "Inventário")]


def info_vazia() -> dict:
    return {
        "pv": {"v": None, "vis": "oculto"},          # [atual, máximo] ou None
        "desl": {"v": 9.0, "vis": "oculto"},         # deslocamento em metros (limite no combate)
        "condicoes": {"v": [], "vis": "oculto"},
        "raca": {"v": "", "vis": "oculto"},
        "classe": {"v": "", "vis": "oculto"},
        "notas": {"v": "", "vis": "oculto"},
        "inventario": {"v": [], "vis": "oculto"},    # itens pegos (baús etc.)
        "segredo": {"v": "", "vis": "mestre"},       # notas secretas: NUNCA saem do mestre
    }


def pode_ver(campo: dict, jogador: str, dono: str) -> bool:
    """vis: "oculto" (só mestre e dono), "todos", ou lista de nomes."""
    from ..rede.protocolo import mesmo_nome
    if campo.get("vis") == "mestre":
        return False   # notas secretas do mestre: nem o dono vê
    if dono and mesmo_nome(dono, jogador):
        return True
    vis = campo.get("vis", "oculto")
    if vis == "todos":
        return True
    if isinstance(vis, list):
        return any(mesmo_nome(n, jogador) for n in vis)
    return False


def tem_valor(chave: str, valor) -> bool:
    if chave == "pv":
        return bool(valor)
    return bool(valor)
