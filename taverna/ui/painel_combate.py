"""
Combate por turnos.

Mestre: inicia o combate (com os selecionados, com quem está na mesma área ou com todos),
edita iniciativas, rola pras criaturas e passa a vez. Fora do combate, decide se os
jogadores podem mover/girar os tokens.

Player: vê a ordem de iniciativa, rola a própria iniciativa quando o mestre pede
e é avisado quando é a vez dele.
"""

import html

from PyQt6.QtCore import QSettings, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import (QAbstractItemView, QCheckBox, QHBoxLayout, QHeaderView, QLabel,
                             QListWidget, QListWidgetItem, QMenu, QPushButton, QSpinBox,
                             QTableWidget, QTableWidgetItem, QToolButton, QVBoxLayout, QWidget)

from ..config import CELULA
from ..mesa.token import TokenItem

ICONE_TIPO = {"jogador": "escudo", "criatura": "monstro", "npc": "pessoa"}   # desenhos de ui/icones.py


def _icone_tipo(tipo):
    # cor fixa do texto em todos os modos (a célula da tabela não é "editável" e o Qt apagaria o ícone)
    from PyQt6.QtGui import QIcon
    from .icones import pixmap_cache
    from .tema import tema_atual
    return QIcon(pixmap_cache(ICONE_TIPO.get(tipo, "token"), tema_atual()["texto"], 32))


# (v0.65.1) iniciativas cujo dado AINDA está rolando na tela: a lista mostra "…" até ele parar (o número
# não aparece antes do dado). Quem rola marca (ini_rolando) e quem revela solta (ini_revelada).
INI_ROLANDO: set = set()


def ini_rolando(uid: str):
    INI_ROLANDO.add(uid)


def ini_revelada(uid: str):
    INI_ROLANDO.discard(uid)


def _texto_ini(p) -> str:
    if p["ini"] is None:
        return ""
    return "…" if p["id"] in INI_ROLANDO else str(p["ini"])


class PainelCombateMestre(QWidget):
    centralizar_token = pyqtSignal(object)
    girar_todos = pyqtSignal(bool)

    def __init__(self, servidor, parent=None):
        super().__init__(parent)
        self.servidor = servidor
        self._preenchendo = False

        self.btn_iniciar = QToolButton()
        self.btn_iniciar.setText("⚔  Iniciar combate")
        self.btn_iniciar.setObjectName("primario")
        self.btn_iniciar.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btn_iniciar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        menu = QMenu(self)
        for texto, modo, dica in (
                ("Com os tokens selecionados", "selecionados", ""),
                ("Selecionados + quem está na mesma área", "area",
                 "Inclui quem está à vista dos selecionados (paredes e portas fechadas separam)"),
                ("Com todos os tokens visíveis da mesa", "todos", "")):
            a = QAction(texto, menu)
            a.setToolTip(dica)
            a.triggered.connect(lambda _=False, m=modo: self.iniciar(m))
            menu.addAction(a)
        self.btn_iniciar.setMenu(menu)
        self.btn_encerrar = QPushButton("✖  Encerrar")
        self.btn_encerrar.clicked.connect(self.encerrar)
        topo = QHBoxLayout()
        topo.addWidget(self.btn_iniciar, 1)
        topo.addWidget(self.btn_encerrar)

        self.status = QLabel()
        self.status.setStyleSheet("font-size: 11pt; font-weight: bold; color: palette(highlight);")
        self.status.setWordWrap(True)

        self.tabela = QTableWidget(0, 5)
        self.tabela.setHorizontalHeaderLabels(["", "Nome", "Inic.", "Mod", "Desl."])
        cab = self.tabela.horizontalHeader()
        cab.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        cab.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.tabela.verticalHeader().hide()
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabela.setToolTip("Clique duas vezes na iniciativa, modificador ou deslocamento pra editar.\n"
                               "Desl. = metros por turno (ex.: ferido → 4,5). Clique no nome pra achar o token.")
        self.tabela.itemChanged.connect(self._editou)
        self.tabela.cellClicked.connect(self._clicou)

        self.btn_criaturas = QPushButton("🎲 Rolar pras criaturas")
        self.btn_criaturas.setToolTip("Rola 1d20 + modificador pra quem não é jogador e ainda não tem iniciativa")
        self.btn_criaturas.clicked.connect(self.rolar_criaturas)
        self.criaturas_privado = QCheckBox("🔒 escondido")
        self.criaturas_privado.setChecked(True)
        self.criaturas_privado.setToolTip("Os jogadores não veem os dados das criaturas")
        linha_rolar = QHBoxLayout()
        linha_rolar.addWidget(self.btn_criaturas, 1)
        linha_rolar.addWidget(self.criaturas_privado)

        self.btn_add = QPushButton("＋ Selecionados")
        self.btn_add.setToolTip("Coloca no combate os tokens selecionados na mesa")
        self.btn_add.clicked.connect(self.adicionar_selecionados)
        self.btn_tirar = QPushButton("－ Tirar")
        self.btn_tirar.setToolTip("Tira do combate quem está marcado na lista")
        self.btn_tirar.clicked.connect(self.tirar)

        self.btn_anterior = QPushButton("◀")
        self.btn_anterior.setToolTip("Voltar a vez")
        self.btn_anterior.clicked.connect(self.anterior)
        self.btn_proximo = QPushButton("Próximo turno  ▶")
        self.btn_proximo.setObjectName("primario")
        self.btn_proximo.setToolTip("Passa a vez (atalho: N)")
        self.btn_proximo.clicked.connect(self.proximo)
        linha_turno = QHBoxLayout()
        linha_turno.addWidget(self.btn_anterior)
        linha_turno.addWidget(self.btn_proximo, 1)

        self.chk_limitar = QCheckBox("Limitar o movimento ao deslocamento")
        self.chk_limitar.setChecked(True)
        self.chk_limitar.setToolTip("No turno, o jogador só anda até o deslocamento dele\n"
                                    "(a partir de onde começou o turno). Você não tem limite.")
        self.chk_limitar.toggled.connect(self._limitar)
        self.btn_disparada = QPushButton("🏃 Disparada")
        self.btn_disparada.setToolTip("Dobra o deslocamento de quem está na vez, só neste turno")
        self.btn_disparada.clicked.connect(self.disparada)
        linha_add = QHBoxLayout()
        linha_add.addWidget(self.btn_add, 1)
        linha_add.addWidget(self.btn_tirar)
        linha_add.addWidget(self.btn_disparada)
        self.chk_movem = QCheckBox("Fora do combate, jogadores podem mover")
        self.chk_movem.setChecked(True)
        self.chk_movem.toggled.connect(self.servidor.definir_players_movem)
        self.chk_giram = QCheckBox("Jogadores podem girar a visão")
        self.chk_giram.setChecked(True)
        self.chk_giram.toggled.connect(self.girar_todos)
        dica = QLabel("No combate, só o token da vez se mexe.\nVocê sempre pode mexer em tudo.")
        dica.setObjectName("dica")

        # Arranjo (v0.29): passar a vez em cima, a ordem no meio, ações logo abaixo da lista
        # e as regras de movimento numa seção que fecha.
        from .acabamento import Secao
        self.secao_regras = Secao("combate/regras", "🏃 Regras de movimento", aberta=False)
        for w in (self.chk_limitar, self.chk_movem, self.chk_giram, dica):
            self.secao_regras.lay.addWidget(w)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addLayout(topo)
        layout.addWidget(self.status)
        layout.addLayout(linha_turno)
        layout.addWidget(self.tabela, 1)
        layout.addLayout(linha_rolar)
        layout.addLayout(linha_add)
        layout.addWidget(self.secao_regras)
        self.servidor.combate_mudou.connect(self.atualizar)
        self.atualizar()
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def changeEvent(self, ev):
        # tema mudou: refaz a tabela (ícones e cores vêm do tema)
        from PyQt6.QtCore import QEvent, QTimer
        if ev.type() == QEvent.Type.StyleChange and not getattr(self, "_refazendo", False):
            self._refazendo = True
            QTimer.singleShot(0, self._refazer_tema)
        super().changeEvent(ev)

    def _refazer_tema(self):
        self._refazendo = False
        self.atualizar()

    @property
    def combate(self):
        return self.servidor.combate

    def _tokens(self):
        return {t.uid: t for t in self.servidor.cena.itens_do_usuario() if isinstance(t, TokenItem)}

    # ------------------------------------------------------------ iniciar / encerrar
    def iniciar(self, modo):
        cena = self.servidor.cena
        visiveis = [t for t in self._tokens().values()
                    if t.isVisible() and t.parentItem() and t.parentItem().isVisible()]
        selecionados = [t for t in cena.selectedItems() if isinstance(t, TokenItem)]
        if modo == "todos":
            escolhidos = visiveis
        else:
            escolhidos = list(selecionados)
            if modo == "area" and selecionados:
                escolhidos = self._mesma_area(selecionados, visiveis)
        if not escolhidos:
            self.status.setText("Selecione os tokens na mesa primeiro\n(ou escolha “todos os visíveis”).")
            return
        self.combate.iniciar(escolhidos)
        self.servidor.atualizar_combate()

    @staticmethod
    def _mesma_area(selecionados, candidatos):
        from ..mesa.linha_de_visao import poligono
        cena = selecionados[0].scene()
        obst = cena.obstaculos_visiveis()
        escolhidos = list(selecionados)
        for s in selecionados:
            c = s.centro_cena()
            area = poligono(c.x(), c.y(), 0, 360, 60, obst)
            for t in candidatos:
                if t not in escolhidos and area.containsPoint(t.centro_cena(), Qt.FillRule.OddEvenFill):
                    escolhidos.append(t)
        return escolhidos

    def encerrar(self):
        self.combate.encerrar()
        self.servidor.atualizar_combate()

    def adicionar_selecionados(self):
        if not self.combate.ativo:
            self.iniciar("selecionados")
            return
        for t in self.servidor.cena.selectedItems():
            if isinstance(t, TokenItem):
                self.combate.adicionar(t)
        self.servidor.atualizar_combate()

    def tirar(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            return
        uid = self.tabela.item(linha, 1).data(Qt.ItemDataRole.UserRole)
        self.combate.remover(uid)
        self.servidor.atualizar_combate()

    # ------------------------------------------------------------ turnos
    def proximo(self):
        if not self.combate.ativo:
            return
        self.servidor.proximo_turno()
        t = self._tokens().get(self.combate.vez)
        if t is not None:
            self.centralizar_token.emit(t)

    def anterior(self):
        if self.combate.ativo:
            self.combate.anterior()
            self.servidor.atualizar_combate()

    def _limitar(self, ligado):
        self.combate.limitar = ligado
        self.servidor.atualizar_combate()

    def disparada(self):
        p = self.combate.participante(self.combate.vez) if self.combate.ativo else None
        t = self._tokens().get(self.combate.vez) if p else None
        if p is None or t is None:
            return
        p["extra"] = p.get("extra", 0.0) + t.deslocamento
        self.servidor.registrar("Mestre", f"deu Disparada pra {t.nome}", "🏃")
        self.servidor.atualizar_combate()

    def rolar_criaturas(self):
        for p in self.combate.participantes:
            if p["ini"] is None and p["tipo"] != "jogador":
                expr = f"1d20{p['mod']:+d}" if p["mod"] else "1d20"
                r = self.servidor.rolar_mestre(expr, privada=self.criaturas_privado.isChecked(),
                                               motivo=f"iniciativa de {p['nome']}")
                p["ini"] = r["total"]
        self.servidor.atualizar_combate()

    # ------------------------------------------------------------ tabela
    def atualizar(self):
        c = self.combate
        self.btn_encerrar.setEnabled(c.ativo)
        for b in (self.btn_proximo, self.btn_anterior, self.btn_criaturas, self.btn_tirar,
                  self.btn_disparada):
            b.setEnabled(c.ativo)
        from .acabamento import com_icone
        com_icone(self.btn_add, "＋ Selecionados" if c.ativo else "＋ Selecionados (inicia)")
        if not c.ativo:
            self.status.setText("Fora de combate.")
        else:
            faltam = c.faltando()
            if c.vez is None:
                txt = "Rolando iniciativa…"
                if faltam:
                    txt += f"\nFaltam: {', '.join(p['nome'] for p in faltam)}"
                txt += "\nQuando estiver pronto, aperte “Próximo turno”."
            else:
                atual = c.participante(c.vez)
                txt = f"Rodada {c.rodada} · vez de {atual['nome'] if atual else '?'}"
            self.status.setText(txt)
            self.btn_proximo.setText("Começar  ▶" if c.vez is None else "Próximo turno  ▶")

        self._preenchendo = True
        ordem = c.ordem() if c.ativo else []
        self.tabela.setRowCount(len(ordem))
        for linha, p in enumerate(ordem):
            vez = p["id"] == c.vez
            marca = QTableWidgetItem("▶" if vez else "")
            if not vez:
                marca.setIcon(_icone_tipo(p["tipo"]))
            nome = QTableWidgetItem(p["nome"] + (f"  ({p['dono']})" if p["dono"] else ""))
            nome.setData(Qt.ItemDataRole.UserRole, p["id"])
            ini = QTableWidgetItem(_texto_ini(p))
            ini.setToolTip("Sem iniciativa ainda" if p["ini"] is None else "")
            mod = QTableWidgetItem(f"{p['mod']:+d}")
            tok = self._tokens().get(p["id"])
            base = tok.deslocamento if tok else 0
            extra = p.get("extra", 0.0) if vez else 0.0
            desl = QTableWidgetItem(f"{base:g}".replace(".", ",") + (f" +{extra:g}" if extra else ""))
            desl.setToolTip("metros por turno" + (" (com Disparada)" if extra else ""))
            for k, item in enumerate((marca, nome, ini, mod, desl)):
                if k < 2:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if vez:
                    item.setBackground(QColor(107, 74, 31))
                elif p["ini"] is None:
                    item.setForeground(QColor(150, 130, 100))
                self.tabela.setItem(linha, k, item)
        self._preenchendo = False

    def _editou(self, item):
        if self._preenchendo or item.column() not in (2, 3, 4):
            return
        uid = self.tabela.item(item.row(), 1).data(Qt.ItemDataRole.UserRole)
        p = self.combate.participante(uid)
        if p is None:
            return
        if item.column() == 4:
            tok = self._tokens().get(uid)
            try:
                valor = float(item.text().split("+")[0].strip().replace(",", ".").replace("m", ""))
            except ValueError:
                valor = tok.deslocamento if tok else 0
            if tok is not None:
                tok.definir_info("desl", max(0.0, valor))
            self.servidor.atualizar_combate()
            return
        texto = item.text().strip().replace("+", "")
        try:
            valor = int(texto) if texto else None
        except ValueError:
            valor = p["ini"] if item.column() == 2 else p["mod"]
        if item.column() == 2:
            p["ini"] = valor
        else:
            p["mod"] = valor or 0
        self.servidor.atualizar_combate()

    def _clicou(self, linha, coluna):
        if coluna != 1:
            return
        uid = self.tabela.item(linha, 1).data(Qt.ItemDataRole.UserRole)
        t = self._tokens().get(uid)
        if t is not None:
            self.centralizar_token.emit(t)


class PainelCombatePlayer(QWidget):
    rolar_iniciativa = pyqtSignal(str, str)   # expressão, uid do token
    encerrar_turno = pyqtSignal()             # (v0.65.1) o jogador passa a vez dele

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = QSettings("Taverna", "Player")
        self.status = QLabel("Fora de combate.")
        self.status.setStyleSheet("font-size: 11pt; font-weight: bold; color: palette(highlight);")
        self.status.setWordWrap(True)
        self.lista = QListWidget()
        self.caixa = QWidget()
        lc = QVBoxLayout(self.caixa)
        lc.setContentsMargins(0, 0, 0, 0)
        self.pedido = QLabel()
        self.pedido.setWordWrap(True)
        self.mod = QSpinBox()
        self.mod.setRange(-10, 20)
        self.mod.setPrefix("mod. ")
        self.mod.setToolTip("Seu bônus de iniciativa (normalmente o modificador de Destreza)")
        self.btn = QPushButton("🎲 Rolar iniciativa")
        self.btn.setObjectName("primario")
        self.btn.clicked.connect(self._rolar)
        linha = QHBoxLayout()
        linha.addWidget(self.mod)
        linha.addWidget(self.btn, 1)
        lc.addWidget(self.pedido)
        lc.addLayout(linha)
        self.caixa.hide()
        self._pendente = None
        # (v0.65.1, pedido do Manel) na minha vez, eu mesmo encerro o meu turno
        self.btn_encerrar = QPushButton("Encerrar meu turno  ▶")
        self.btn_encerrar.setObjectName("primario")
        self.btn_encerrar.setToolTip("Passa a vez pro próximo (o mestre também pode passar)")
        self.btn_encerrar.clicked.connect(self._encerrar)
        self.btn_encerrar.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(self.status)
        layout.addWidget(self.btn_encerrar)
        layout.addWidget(self.caixa)
        layout.addWidget(self.lista, 1)
        from .acabamento import iconizar
        iconizar(self)   # emoji → ícone do tema

    def atualizar(self, combate: dict, meus_tokens) -> str | None:
        """Retorna o nome do meu token se acabou de virar a minha vez."""
        self._ultimo = (combate, meus_tokens)
        from ..rede.protocolo import mesmo_nome  # noqa
        self.lista.clear()
        meus_ids = {t.uid: t for t in meus_tokens}
        if not combate or not combate.get("ativo"):
            self.status.setText("Fora de combate.")
            self.caixa.hide()
            self.btn_encerrar.hide()
            self._vez_anterior = None
            return None
        vez = combate.get("vez")
        ordem = combate.get("ordem", [])
        self.btn_encerrar.setVisible(vez is not None and vez in meus_ids)
        self.btn_encerrar.setEnabled(True)
        if vez is None:
            self.status.setText("Combate! Rolando iniciativa…")
        else:
            atual = next((p for p in ordem if p["id"] == vez), None)
            nome = atual["nome"] if atual else "???"
            self.status.setText(f"Rodada {combate.get('rodada')} · vez de {nome}"
                                + ("  — SUA VEZ!" if vez in meus_ids else ""))
        for p in ordem:
            ini = _texto_ini(p) or "—"
            texto = f"{'▶ ' if p['id'] == vez else '   '}{ini:>3}   {p['nome']}"
            item = QListWidgetItem(_icone_tipo(p["tipo"]), texto)
            if p["id"] == vez:
                from .tema import tema_atual
                item.setBackground(QColor(tema_atual()["selecao"]))
            if p["id"] in meus_ids:
                f = item.font()
                f.setBold(True)
                item.setFont(f)
            self.lista.addItem(item)
        # Pedido de iniciativa: meus tokens que ainda não rolaram
        faltando = [p for p in ordem if p["id"] in meus_ids and p["ini"] is None]
        if faltando:
            p = faltando[0]
            self._pendente = p["id"]
            self._pendente_nome = p["nome"]
            self.pedido.setText(f"<b>Role a iniciativa de {html.escape(p['nome'])}!</b>")
            self.mod.setValue(int(self.config.value(f"mod_ini/{p['nome']}", 0)))
            self.caixa.show()
        else:
            self._pendente = None
            self.caixa.hide()
        anterior = getattr(self, "_vez_anterior", None)
        self._vez_anterior = vez
        if vez in meus_ids and vez != anterior:
            return meus_ids[vez].nome
        return None

    def redesenhar(self):
        """De novo com o último estado (o dado de iniciativa parou: o número aparece)."""
        ultimo = getattr(self, "_ultimo", None)
        if ultimo is not None:
            vez = getattr(self, "_vez_anterior", None)
            self.atualizar(*ultimo)
            self._vez_anterior = vez   # (não avisa "sua vez" de novo)

    def _encerrar(self):
        self.btn_encerrar.setEnabled(False)   # (não manda duas vezes; volta quando o estado chegar)
        self.encerrar_turno.emit()

    def _rolar(self):
        if not self._pendente:
            return
        mod = self.mod.value()
        self.config.setValue(f"mod_ini/{self._pendente_nome}", mod)
        self.rolar_iniciativa.emit(f"1d20{mod:+d}" if mod else "1d20", self._pendente)
        self.btn.setEnabled(False)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self.btn.setEnabled(True))
