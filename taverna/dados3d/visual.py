"""
(v0.74) 🎨 MEUS DADOS — cada pessoa escolhe a cara dos SEUS dados 3D (fica salvo no PC dela):

  material: do tema (o de sempre) · osso · plástico · fosco · pedra · mármore · madeira · ferro · latão · ouro ·
            prata · vidro · cristal · gema · obsidiana — cada um com a sua textura por cima (veios, grão, ferrugem…)
  cor do corpo e cor dos números · translúcido (sim/não, pra qualquer material) · brilho (fosco ↔ polido)

A escolha vai JUNTO com cada rolagem (campo "dv"), então todo mundo vê os seus dados do seu jeito — e os dos
outros do jeito deles. Sem escolha (ou "do tema"), os dados seguem o tema da mesa de quem está olhando.
"""

import json

from PyQt6.QtGui import QColor

# chave: (nome, brilho 0–1, translúcido, desgaste (textura por cima), corpo, número, metal (brilho colorido))
MATERIAIS = {
    "tema": ("Do tema da mesa", None, None, None, None, None, False),
    "osso": ("Osso", 0.35, False, "medieval", "#e8dcc0", "#3a2414", False),
    "plastico": ("Plástico", 0.55, False, "moderno", "#f2f2f0", "#1c1c1e", False),
    "fosco": ("Fosco (borracha)", 0.05, False, "claro", "#3a4a5c", "#f4f0e4", False),
    "pedra": ("Pedra", 0.12, False, "pedra", "#8a8780", "#f2eee2", False),
    "marmore": ("Mármore", 0.6, False, "marmore", "#ece8e0", "#2e2e34", False),
    "madeira": ("Madeira", 0.25, False, "madeira", "#8a5a30", "#f4e6c4", False),
    "ferro": ("Ferro (com ferrugem)", 0.55, False, "ferro", "#4a4c52", "#e8e0d0", True),
    "metal": ("Latão", 0.95, False, "steampunk", "#a8823a", "#2a1c06", True),
    "ouro": ("Ouro", 1.0, False, "polido", "#d4a838", "#3a2406", True),
    "prata": ("Prata", 1.0, False, "polido", "#c8ccd4", "#1c2030", True),
    "vidro": ("Vidro", 0.9, True, "claro", "#18b8e8", "#f4fdff", False),
    "cristal": ("Cristal", 0.95, True, None, "#d8eeff", "#2a4a90", False),
    "gema": ("Gema", 0.85, True, "magico", "#6a3ab8", "#ffd86a", False),
    "obsidiana": ("Obsidiana", 0.9, False, "claro", "#1c1620", "#e8c060", False),
}
CHAVE = "dados_visual"


def _config():
    """As preferências (os testes trocam por um arquivo temporário)."""
    from PyQt6.QtCore import QSettings
    return QSettings("Taverna", "Geral")


def _cor(v, padrao):
    c = QColor(str(v)) if isinstance(v, str) and v.startswith("#") and len(v) in (4, 7) else QColor()
    return c.name() if c.isValid() else padrao


def limpar(d) -> dict | None:
    """O que chegou (da rede ou das preferências) virado num visual válido; None = do tema."""
    if not isinstance(d, dict):
        return None
    m = d.get("m")
    if m not in MATERIAIS or m == "tema":
        return None
    _n, brilho, transl, _d, corpo, numero, _metal = MATERIAIS[m]
    try:
        b = max(0.0, min(1.0, float(d.get("b", brilho))))
    except (TypeError, ValueError):
        b = brilho
    t = d.get("t", transl)
    return {"m": m, "c": _cor(d.get("c"), corpo), "n": _cor(d.get("n"), numero),
            "t": bool(t) if isinstance(t, (bool, int)) else transl, "b": round(b, 2)}


def meus_dados() -> dict | None:
    """O visual dos dados desta pessoa (preferência do PC)."""
    try:
        return limpar(json.loads(str(_config().value(CHAVE, "") or "{}")))
    except (ValueError, TypeError):
        return None


def guardar(d: dict | None):
    _config().setValue(CHAVE, json.dumps(limpar(d) or {"m": "tema"}))


def resolver(visual, tema: str):
    """(corpo QColor, número QColor, brilho, translúcido, tema do desgaste, metal) pra desenhar."""
    v = limpar(visual)
    if v is None:
        from .cena3d import DESGASTE, material
        corpo, numero, brilho, gema = material(tema)
        return corpo, numero, brilho, gema, (tema if tema in DESGASTE else None), tema == "steampunk"
    _n, _b, _t, desg, _c, _nn, metal = MATERIAIS[v["m"]]
    return QColor(v["c"]), QColor(v["n"]), v["b"], v["t"], desg, metal
