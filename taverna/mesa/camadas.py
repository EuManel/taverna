"""
Camadas da mesa, estilo Photoshop.

Cada camada é um item "invisível" da cena que serve de pai para os itens
que moram nela (mapas, tokens...). Isso dá três coisas de graça:
  - ordem: a camada com Z maior fica por cima de todas as de Z menor;
  - visibilidade: esconder a camada esconde todos os filhos;
  - trava: a camada avisa os filhos para não se mexerem.
"""

from PyQt6.QtCore import QRectF
from PyQt6.QtWidgets import QGraphicsItem

# Tipos especiais de camada. "livre" é qualquer camada criada pelo mestre.
TIPOS_CAMADA = ("mapa", "terreno", "grid", "paredes", "luzes", "criaturas", "jogadores", "livre")

# Camadas que não podem ser apagadas
CAMADAS_FIXAS = ("mapa", "terreno", "grid", "paredes", "luzes", "criaturas", "jogadores")


class Camada(QGraphicsItem):
    def __init__(self, nome: str, tipo: str = "livre"):
        super().__init__()
        self.nome = nome
        self.tipo = tipo
        self.travada = False
        # A camada não desenha nada, só agrupa
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemHasNoContents, True)

    def boundingRect(self) -> QRectF:
        return QRectF()

    def paint(self, painter, option, widget=None):
        pass

    @property
    def fixa(self) -> bool:
        return self.tipo in CAMADAS_FIXAS

    def itens(self):
        """Itens do usuário que moram nesta camada (mapas, tokens...)."""
        return [i for i in self.childItems() if hasattr(i, "para_dict")]

    def definir_travada(self, travada: bool):
        self.travada = travada
        for item in self.itens():
            item.aplicar_trava(travada)
