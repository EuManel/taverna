"""
Painel de camadas, estilo Photoshop.

  ▸ Jogadores          <- clique na setinha pra ver o que tem dentro
      ⬤ Aelar
  ▸ Criaturas e NPCs
      ⬤ Ogro
      ⬤ Taverneiro
  ▸ Grid
  ▸ Mapa
      🗺 masmorra

- A de cima na lista é a que fica por cima na mesa (vale pra camadas e itens).
- Caixinha = visível (na camada inteira ou só num item).
- Clicar num item seleciona ele na mesa, e vice-versa.
- Duplo clique: camada = renomear · token = editar · mapa = centralizar a câmera.
- ▲▼ movem a camada OU o item selecionado (dentro da camada dele).
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from .tema import eh_claro as _eh_claro
from PyQt6.QtWidgets import (QAbstractItemView, QHBoxLayout, QInputDialog,
                             QPushButton, QTreeWidget, QTreeWidgetItem,
                             QVBoxLayout, QWidget)

from ..config import TIPOS_TOKEN
from ..mesa.camadas import Camada
from ..mesa.mapa import MapaItem
from ..mesa.luzes import LuzItem
from ..mesa.portas import PortaItem
from ..mesa.token import TokenItem

from .acabamento import item_com_icone
from .icones import icone_tema

# ícone desenhado (icones.py) de cada tipo de camada
ICONES_TIPO = {"mapa": "mapa", "terreno": "terreno", "paredes": "parede", "grid": "snap", "luzes": "luz",
               "criaturas": "monstro", "jogadores": "escudo", "livre": "camadas"}
PAPEL = Qt.ItemDataRole.UserRole


class PainelCamadas(QWidget):
    def __init__(self, cena, ao_duplo_clique_item=None, parent=None):
        super().__init__(parent)
        self.cena = cena
        self.ao_duplo_clique_item = ao_duplo_clique_item
        self._atualizando = False
        self._fechadas = set()  # camadas que o mestre recolheu (o resto fica aberto)

        self.arvore = QTreeWidget()
        self.arvore.setHeaderHidden(True)
        self.arvore.setIndentation(18)
        self.arvore.setAnimated(True)
        self.arvore.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.arvore.itemSelectionChanged.connect(self._selecao_da_arvore)
        self.arvore.itemChanged.connect(self._marcacao_mudou)
        self.arvore.itemDoubleClicked.connect(self._duplo_clique)
        self.arvore.itemCollapsed.connect(
            lambda i: self._fechadas.add(id(i.data(0, PAPEL))))
        self.arvore.itemExpanded.connect(
            lambda i: self._fechadas.discard(id(i.data(0, PAPEL))))

        def botao(texto, dica, funcao):
            b = QPushButton(texto)
            b.setToolTip(dica)
            b.setFixedHeight(30)
            b.clicked.connect(funcao)
            return b

        self.b_subir = botao("▲", "Subir (camada ou item selecionado)", lambda: self._mover(+1))
        self.b_descer = botao("▼", "Descer (camada ou item selecionado)", lambda: self._mover(-1))
        self.b_trava = botao("🔒", "Travar / destravar camada", self._alternar_trava)
        self.b_nova = botao("＋", "Nova camada", self._nova)
        self.b_remover = botao("🗑", "Apagar o que está selecionado", self._remover)

        botoes = QHBoxLayout()
        botoes.setSpacing(4)
        for b in (self.b_subir, self.b_descer, self.b_trava, self.b_nova, self.b_remover):
            botoes.addWidget(b)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.arvore)
        layout.addLayout(botoes)

        self.cena = None
        self.definir_cena(cena)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def definir_cena(self, cena):
        """Troca de aba: o painel passa a mostrar as camadas da outra cena."""
        if self.cena is not None:
            for sinal, slot in ((self.cena.camadas_mudaram, self.recarregar),
                                (self.cena.selectionChanged, self._selecao_da_mesa)):
                try:
                    sinal.disconnect(slot)
                except (TypeError, RuntimeError):
                    pass
        self.cena = cena
        cena.camadas_mudaram.connect(self.recarregar)
        cena.selectionChanged.connect(self._selecao_da_mesa)
        self._fechadas = set()
        self.recarregar()

    # ================================================================ montar
    def _texto_item(self, item) -> str:
        if isinstance(item, TokenItem):
            tipo = TIPOS_TOKEN.get(item.tipo, ("?",))[0]
            extra = f" · {item.tamanho}×{item.tamanho}" if item.tamanho > 1 else ""
            dono = f" ({item.dono})" if item.tipo == "jogador" and item.dono else ""
            return f"⬤  {item.nome}{dono}   — {tipo}{extra}"
        if isinstance(item, MapaItem):
            return f"🗺  {item.nome}"
        if isinstance(item, PortaItem):
            return f"🚪  {item.nome}"
        if isinstance(item, LuzItem):
            return f"{'🔥' if item.acesa else '💡'}  {item.nome}" + ("" if item.acesa else "   (apagada)")
        if hasattr(item, "efeito_area"):
            return f"✨  {item.nome or item.descricao()}" + (f"   — de {item.dono}" if item.dono else "")
        if hasattr(item, "retangulo_cena"):   # área de armadilha
            return f"⚡  {item.nome}   — área (só você vê)"
        if hasattr(item, "luz_dict"):   # objeto (prop)
            escada = getattr(item, "tipo", "") == "escada"
            marcas = [m for m, sim in (("interativo", item.interativo),
                                       ("bloqueada" if escada else "trancado", item.trancado),
                                       ("armadilha", item.gatilho)) if sim]
            return f"📦  {item.nome}" + (f"   · {', '.join(marcas)}" if marcas else "")
        return "?"

    def recarregar(self):
        self._atualizando = True
        self.arvore.clear()
        for camada in reversed(self.cena.camadas):
            texto = camada.nome + ("   (travada)" if camada.travada else "")
            no = QTreeWidgetItem([texto])
            no.setIcon(0, icone_tema(ICONES_TIPO.get(camada.tipo, "camadas")))
            no.setData(0, PAPEL, camada)
            no.setFlags(no.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            no.setCheckState(0, Qt.CheckState.Checked if camada.isVisible()
                             else Qt.CheckState.Unchecked)
            fonte = no.font(0)
            fonte.setBold(True)
            no.setFont(0, fonte)
            no.setToolTip(0, "Duplo clique para renomear")
            self.arvore.addTopLevelItem(no)

            itens = sorted(camada.itens(), key=lambda i: i.zValue(), reverse=True)
            for item in itens:
                filho = item_com_icone(QTreeWidgetItem(), self._texto_item(item), 0)
                filho.setData(0, PAPEL, item)
                filho.setFlags(filho.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                filho.setCheckState(0, Qt.CheckState.Checked if item.isVisible()
                                    else Qt.CheckState.Unchecked)
                if isinstance(item, TokenItem):
                    filho.setForeground(0, QColor(TIPOS_TOKEN[item.tipo][1]).darker(150)
                                        if _eh_claro() else QColor(TIPOS_TOKEN[item.tipo][1]).lighter(130))
                    filho.setToolTip(0, "Duplo clique para editar")
                else:
                    filho.setToolTip(0, "Duplo clique para centralizar a câmera")
                if not camada.isVisible() or not item.isVisible():
                    filho.setForeground(0, QColor("#6b5f50"))
                no.addChild(filho)
                filho.setSelected(item.isSelected())

            if camada.tipo in ("grid", "terreno"):
                no.setChildIndicatorPolicy(
                    QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)
            no.setExpanded(id(camada) not in self._fechadas)
        self._atualizando = False
        self._atualizar_botoes()

    # ================================================================ seleção
    def _selecionados(self):
        return [n.data(0, PAPEL) for n in self.arvore.selectedItems()]

    def _selecao_da_arvore(self):
        if self._atualizando:
            return
        objetos = self._selecionados()
        camadas = [o for o in objetos if isinstance(o, Camada)]
        itens = [o for o in objetos if not isinstance(o, Camada)]
        if camadas:
            self.cena.camada_ativa = camadas[0]
        elif itens:
            self.cena.camada_ativa = itens[0].parentItem()
        # Espelha na mesa
        self._atualizando = True
        try:
            self.cena.clearSelection()
            for item in itens:
                if item.isVisible() and item.parentItem().isVisible():
                    item.setSelected(True)
        except RuntimeError:
            pass
        self._atualizando = False
        self._atualizar_botoes()

    def _selecao_da_mesa(self):
        if self._atualizando:
            return
        self._atualizando = True
        try:
            for i in range(self.arvore.topLevelItemCount()):
                no = self.arvore.topLevelItem(i)
                for j in range(no.childCount()):
                    filho = no.child(j)
                    item = filho.data(0, PAPEL)
                    selecionado = item.isSelected()
                    filho.setSelected(selecionado)
                    if selecionado:
                        no.setExpanded(True)
                        self.arvore.scrollToItem(filho)
                no.setSelected(False)
        except RuntimeError:
            pass
        self._atualizando = False
        self._atualizar_botoes()

    def _atualizar_botoes(self):
        objetos = self._selecionados()
        alvo = objetos[0] if len(objetos) == 1 else None
        camada = alvo if isinstance(alvo, Camada) else None
        self.b_subir.setEnabled(alvo is not None)
        self.b_descer.setEnabled(alvo is not None)
        self.b_trava.setEnabled(bool(camada) and camada.tipo != "grid")
        if camada and camada.tipo in ("terreno", "paredes"):
            self.b_trava.setToolTip("Travar: as ferramentas de construção não mexem nesta camada")
        else:
            self.b_trava.setToolTip("Travar / destravar camada")
        tem_itens = any(not isinstance(o, Camada) for o in objetos)
        self.b_remover.setEnabled(tem_itens or (bool(camada) and not camada.fixa))

    # ================================================================ ações
    def _marcacao_mudou(self, no, coluna):
        if self._atualizando:
            return
        obj = no.data(0, PAPEL)
        visivel = no.checkState(0) == Qt.CheckState.Checked
        if obj.isVisible() == visivel:
            return
        if isinstance(obj, Camada):
            self.cena.definir_visivel(obj, visivel)
        else:
            self.cena.definir_item_visivel(obj, visivel)

    def _duplo_clique(self, no, coluna):
        obj = no.data(0, PAPEL)
        if isinstance(obj, Camada):
            nome, ok = QInputDialog.getText(self, "Renomear camada", "Nome:", text=obj.nome)
            if ok and nome.strip():
                self.cena.renomear_camada(obj, nome.strip())
        elif self.ao_duplo_clique_item:
            self.ao_duplo_clique_item(obj)

    def _mover(self, delta):
        objetos = self._selecionados()
        if len(objetos) != 1:
            return
        obj = objetos[0]
        if isinstance(obj, Camada):
            self.cena.camada_ativa = obj
            self.cena.mover_camada(obj, delta)
            self._reselecionar(obj)
        else:
            self.cena.mover_item_na_camada(obj, delta)
            obj.setSelected(True)
            self._selecao_da_mesa()

    def _reselecionar(self, obj):
        for i in range(self.arvore.topLevelItemCount()):
            no = self.arvore.topLevelItem(i)
            if no.data(0, PAPEL) is obj:
                self.arvore.setCurrentItem(no)
                return

    def _alternar_trava(self):
        objetos = self._selecionados()
        if len(objetos) == 1 and isinstance(objetos[0], Camada):
            camada = objetos[0]
            self.cena.definir_travada(camada, not camada.travada)
            self._reselecionar(camada)

    def _nova(self):
        nome, ok = QInputDialog.getText(self, "Nova camada", "Nome da camada:",
                                        text=f"Camada {len(self.cena.camadas) + 1}")
        if ok and nome.strip():
            camada = self.cena.nova_camada(nome.strip())
            self._reselecionar(camada)

    def _remover(self):
        objetos = self._selecionados()
        itens = [o for o in objetos if not isinstance(o, Camada)]
        if itens:
            self.cena.remover_itens(itens)
            return
        for obj in objetos:
            if isinstance(obj, Camada) and not obj.fixa:
                self.cena.remover_camada(obj)
