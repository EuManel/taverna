"""
Configurações gerais do Taverna.

A regra de ouro da mesa: 1 quadrado do grid = 1 metro = CELULA pixels de cena.
O grid NUNCA muda de tamanho. Quem se adapta é a imagem do mapa.
"""

APP_NOME = "Taverna"
APP_VERSAO = "1.0.0"

# Tamanho de 1 quadrado (1 metro) em pixels de cena
CELULA = 64

# Até onde a mesa vai (em pixels de cena, pra cada lado a partir do centro)
LIMITE_CENA = 400 * CELULA

# Limites de zoom da câmera
ZOOM_MIN = 0.08
ZOOM_MAX = 6.0
ZOOM_PASSO = 1.15

# Tamanho mínimo de um mapa, em metros
MAPA_MIN_METROS = 0.5

# Largura padrão (em metros) de um mapa recém-importado
MAPA_LARGURA_PADRAO = 20

# Arquivo de cena
EXTENSAO_CENA = ".taverna"
VERSAO_ARQUIVO = 4

# Paleta da interface (tema "Taverna")
COR_FUNDO_MESA = "#0f0d0b"
COR_GRID = "#e8dcc4"
COR_DESTAQUE = "#c9a24a"   # dourado
COR_PERIGO = "#a8323e"     # carmim

# Tipos de token: chave -> (nome exibido, cor do anel, camada onde nasce)
TIPOS_TOKEN = {
    "jogador":  ("Jogador",  "#c9a24a", "jogadores"),
    "criatura": ("Criatura", "#a8323e", "criaturas"),
    "npc":      ("NPC",      "#5b8bb0", "criaturas"),
}

# Tamanhos de criatura: rótulo -> quantos quadrados de lado
TAMANHOS_TOKEN = {
    "Pequeno / Médio (1×1)": 1,
    "Grande (2×2)": 2,
    "Enorme (3×3)": 3,
    "Imenso (4×4)": 4,
}


def metros(px: float) -> float:
    """Converte pixels de cena em metros."""
    return px / CELULA


def px(metros_: float) -> float:
    """Converte metros em pixels de cena."""
    return metros_ * CELULA


def fmt_m(valor: float) -> str:
    """Formata metros no padrão brasileiro: 9,5 m"""
    return f"{valor:.1f}".replace(".", ",")
