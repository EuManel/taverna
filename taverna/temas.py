"""
Temas do Taverna. Cada tema muda:
  - as cores da interface (mestre e players);
  - a cor de fundo da mesa e do grid;
  - quais materiais de chão e parede aparecem primeiro no painel Construção.
"""

TEMAS = {
    "medieval": {
        "nome": "Medieval",
        "descricao": "Madeira, pedra e luz de vela.",
        "fundo": "#16120f", "painel": "#1e1914", "painel2": "#272019", "borda": "#3b2f24",
        "texto": "#e8dcc4", "fraco": "#9c8d76", "destaque": "#c9a24a", "selecao": "#3a2c17",
        "mesa": "#0f0d0b", "grid": "#e8dcc4", "fonte_titulo": "MedievalSharp, Georgia, serif",
        "chao": ["pedra", "paralelepipedo", "terra", "grama", "areia", "madeira",
                 "tabuas_velhas", "tapete", "cascalho", "lama", "pantano", "agua",
                 "neve", "gelo", "rocha_caverna", "lava", "ouro"],
        "paredes": ["pedra", "tijolo", "madeira", "ferro", "rocha", "palicada", "sebe",
                    "gelo", "osso"],
    },
    "moderno": {
        "nome": "Moderno",
        "descricao": "Concreto, asfalto e luz fria.",
        "fundo": "#15171a", "painel": "#1c1f23", "painel2": "#252930", "borda": "#343a42",
        "texto": "#e4e7eb", "fraco": "#8b939c", "destaque": "#4fb3a9", "selecao": "#1f3b38",
        "mesa": "#0e1012", "grid": "#d6dde4", "fonte_titulo": "'Bebas Neue', 'Segoe UI Semibold', 'Segoe UI', sans-serif",
        "chao": ["concreto", "asfalto", "ceramica", "xadrez", "carpete", "madeira",
                 "tabuas_velhas", "metal_enferrujado", "grama", "terra", "lama", "agua",
                 "neve", "sangue"],
        "paredes": ["concreto", "tijolo", "vidro", "gesso", "enferrujado", "madeira", "sebe"],
    },
    "futurista": {
        "nome": "Futurista",
        "descricao": "Metal, neon e estações espaciais.",
        "fundo": "#0a0e17", "painel": "#0f1522", "painel2": "#16203a", "borda": "#1e3354",
        "texto": "#d8f3ff", "fraco": "#6f8fa8", "destaque": "#38e1ff", "selecao": "#0f3348",
        "mesa": "#05080e", "grid": "#7fdcff", "fonte_titulo": "Orbitron, Bahnschrift, 'Segoe UI', sans-serif",
        "chao": ["placa_metal", "hexagono", "grade", "painel_neon", "vidro_piso",
                 "metal_enferrujado", "acido", "gelo", "rocha_caverna", "agua", "lava"],
        "paredes": ["metal", "energia", "vidro", "concreto", "enferrujado", "obsidiana"],
    },
    "magico": {
        "nome": "Mágico",
        "descricao": "Cristais, runas e brilho arcano.",
        "fundo": "#140f1e", "painel": "#1b1428", "painel2": "#251b37", "borda": "#3a2b52",
        "texto": "#ece2ff", "fraco": "#9a8bb5", "destaque": "#b48cff", "selecao": "#2f2148",
        "mesa": "#0c0814", "grid": "#d9c8ff", "fonte_titulo": "'Cinzel Decorative', 'Palatino Linotype', Georgia, serif",
        "chao": ["cristal", "marmore_arcano", "marmore_branco", "runas", "musgo_luminoso",
                 "obsidiana", "grama", "pantano", "agua", "gelo", "lava", "acido", "ouro"],
        "paredes": ["cristal", "pedra_runica", "obsidiana", "madeira", "pedra", "gelo",
                    "osso", "sebe"],
    },
    "terror": {
        "nome": "Terror",
        "descricao": "Névoa, sangue seco e luz que falha.",
        "fundo": "#0b0a0b", "painel": "#121012", "painel2": "#1b1719", "borda": "#3a2226",
        "texto": "#d9d2c9", "fraco": "#84787a", "destaque": "#b3202c", "selecao": "#2b0f13",
        "mesa": "#060506", "grid": "#b9aeb0", "fonte_titulo": "'Pirata One', Constantia, Georgia, serif",
        "chao": ["tabuas_velhas", "terra", "lama", "pantano", "sangue", "pedra", "paralelepipedo",
                 "concreto", "ceramica", "xadrez", "metal_enferrujado", "carpete", "grama", "agua",
                 "rocha_caverna", "neve"],
        "paredes": ["madeira", "tijolo", "pedra", "enferrujado", "gesso", "osso", "palicada", "ferro",
                    "concreto", "sebe"],
    },
    "steampunk": {
        "nome": "Steampunk",
        "descricao": "Latão, cobre, vapor e engrenagens (v0.59).",
        "fundo": "#1c140e", "painel": "#241a12", "painel2": "#2e2117", "borda": "#4a3a28",
        "texto": "#ecdcb8", "fraco": "#a8957a", "destaque": "#c9a24a", "selecao": "#3a2a14",
        "mesa": "#120d09", "grid": "#ecdcb8", "fonte_titulo": "'IM FELL English SC', Georgia, serif",
        "chao": ["tabuas_velhas", "madeira", "placa_metal", "metal_enferrujado", "paralelepipedo", "tapete",
                 "grade", "pedra", "ceramica", "xadrez", "cascalho", "agua", "lama"],
        "paredes": ["tijolo", "ferro", "madeira", "metal", "enferrujado", "pedra", "vidro", "gesso"],
    },
    "posapoc": {
        "nome": "Pós-apocalíptico",
        "descricao": "Ferrugem, concreto rachado e mato tomando conta (v0.59).",
        "fundo": "#1a1a14", "painel": "#212118", "painel2": "#2a2a1e", "borda": "#3e3c2a",
        "texto": "#e0d8c0", "fraco": "#9a947c", "destaque": "#d0702a", "selecao": "#3a2a16",
        "mesa": "#10100c", "grid": "#e0d8c0", "fonte_titulo": "'Black Ops One', Impact, sans-serif",
        "chao": ["asfalto", "concreto", "terra", "grama", "lama", "metal_enferrujado", "tabuas_velhas",
                 "cascalho", "areia", "agua", "acido", "sangue", "pantano", "carpete"],
        "paredes": ["concreto", "tijolo", "enferrujado", "madeira", "palicada", "sebe", "vidro", "gesso"],
    },
    "claro": {
        "nome": "Claro",
        "descricao": "Neutro e limpo, como um programa de edição (v0.52).",
        "fundo": "#eef0f3", "painel": "#ffffff", "painel2": "#f3f5f8", "borda": "#cfd4db",
        "texto": "#1d1f24", "fraco": "#6b717b", "destaque": "#3a6df0", "selecao": "#dbe5ff",
        "mesa": "#e4e7eb", "grid": "#3a3f48", "fonte_titulo": "'Segoe UI Semibold', 'Segoe UI', sans-serif",
        "chao": ["pedra", "paralelepipedo", "madeira", "grama", "terra", "areia", "tapete",
                 "marmore_branco", "ceramica", "cascalho", "agua", "neve", "concreto", "lama"],
        "paredes": ["pedra", "tijolo", "madeira", "gesso", "sebe", "vidro", "ferro", "concreto"],
    },
    "escuro": {
        "nome": "Escuro",
        "descricao": "Neutro e discreto, pra qualquer sistema.",
        "fundo": "#101113", "painel": "#17181b", "painel2": "#1f2125", "borda": "#2e3138",
        "texto": "#e6e7ea", "fraco": "#8a8e97", "destaque": "#7c9cff", "selecao": "#1d2740",
        "mesa": "#0a0b0c", "grid": "#cfd3da", "fonte_titulo": "'Segoe UI Semibold', 'Segoe UI', sans-serif",
        "chao": ["pedra", "madeira", "concreto", "grama", "terra", "areia", "asfalto", "ceramica",
                 "placa_metal", "agua", "neve", "lama", "rocha_caverna", "tapete"],
        "paredes": ["pedra", "tijolo", "madeira", "concreto", "metal", "vidro", "ferro", "sebe"],
    },
}

# Detalhes de estilo de cada tema (acabamento): cantos, fontes, segunda cor, perigo…
ESTILO = {
    #             raio  destaque2   perigo     claro  fonte do corpo                                   espaço título
    "medieval":  (4,  "#8a5a2b", "#b8433a", False, '"Segoe UI", "Noto Sans", sans-serif',              2),
    "moderno":   (8,  "#e0b34f", "#e05c5c", False, '"Segoe UI", "Noto Sans", sans-serif',              1),
    "futurista": (1,  "#ff3fa4", "#ff5470", False, 'Bahnschrift, "Segoe UI", "Noto Sans", sans-serif', 3),
    "magico":    (11, "#5fe0d0", "#ff6b9a", False, '"Segoe UI", "Noto Sans", sans-serif',              2),
    "terror":    (2,  "#6f7f5a", "#e0303c", False, '"Segoe UI", "Noto Sans", sans-serif',              4),
    "steampunk": (3,  "#b8653a", "#c0402a", False, '"Segoe UI", "Noto Sans", sans-serif',              2),
    "posapoc":   (2,  "#7a8a3a", "#d83a2a", False, '"Segoe UI", "Noto Sans", sans-serif',              2),
    "claro":     (5,  "#2f9a6a", "#d23a3a", True,  '"Segoe UI", "Noto Sans", sans-serif',              1),
    "escuro":    (8,  "#57d6a4", "#ff6b6b", False, '"Segoe UI", "Noto Sans", sans-serif',              1),
}

TEMA_PADRAO = "medieval"


for _k, (_r, _d2, _p, _c, _f, _e) in ESTILO.items():
    TEMAS[_k].update({"chave": _k, "raio": _r, "destaque2": _d2, "perigo": _p, "claro": _c,
                      "fonte_corpo": _f, "espaco_titulo": _e})
    # títulos pequenos (cabeçalho dos painéis, títulos de seção): por padrão a mesma fonte do título
    TEMAS[_k].setdefault("fonte_painel", TEMAS[_k]["fonte_titulo"])
    TEMAS[_k].setdefault("espaco_painel", _e)

# Terror: a gótica (Pirata One) fica só nos títulos grandes; nos pequenos ela embola (decisão do Manel)
TEMAS["terror"].update({"fonte_painel": "Constantia, Georgia, serif", "espaco_painel": 2})


def tema(chave: str) -> dict:
    return TEMAS.get(chave, TEMAS[TEMA_PADRAO])
