"""
👁 Visão dos jogadores (v0.50, pedido do Manel): o mestre liga e vê a mesa EXATAMENTE como está na tela de
um jogador — mesmo filtro do servidor (névoa, andar do token, o que ele pode ver), desenhado pela mesma cena
do jogador (CenaPlayer). Só pra olhar: nada aqui mexe na mesa.
"""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class PainelVisaoJogador(QWidget):
    def __init__(self, servidor, ao_fechar, parent=None):
        super().__init__(parent)
        from ..mesa.cena_player import CenaPlayer
        from ..mesa.visao import MesaVisao
        self.servidor = servidor
        self.imagens = {}
        self.cena = CenaPlayer(self)
        self.visao = MesaVisao(self.cena)
        self.visao.setAcceptDrops(False)
        self.visao.setInteractive(False)   # só olhar
        self._primeiro = True

        barra = QWidget()
        barra.setObjectName("barra_visao_jogador")
        h = QHBoxLayout(barra)
        h.setContentsMargins(10, 6, 10, 6)
        self.titulo = QLabel("👁 <b>Visão dos jogadores</b> — vendo como:")
        self.cb = QComboBox()
        self.cb.setMinimumWidth(180)
        self.cb.currentIndexChanged.connect(lambda _i: self._trocou())
        self.info = QLabel("")
        self.info.setObjectName("dica")
        b_centro = QPushButton("🎯 Centralizar no token dele")
        b_centro.clicked.connect(self.centralizar)
        b_fechar = QPushButton("✖ Voltar pra minha mesa")
        b_fechar.setObjectName("primario")
        b_fechar.clicked.connect(ao_fechar)
        h.addWidget(self.titulo)
        h.addWidget(self.cb)
        h.addWidget(b_centro)
        h.addWidget(self.info, 1)
        h.addWidget(b_fechar)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(barra)
        lay.addWidget(self.visao, 1)

        self.timer = QTimer(self)
        self.timer.setInterval(300)   # acompanha a mesa ~3× por segundo
        self.timer.timeout.connect(self.atualizar)
        from .acabamento import iconizar
        iconizar(self)

    # ------------------------------------------------------------ ligar/desligar
    def ligar(self, nome: str = ""):
        self.recarregar_nomes(nome)
        self._primeiro = True
        self.atualizar()
        self.timer.start()

    def desligar(self):
        self.timer.stop()

    def recarregar_nomes(self, escolher: str = ""):
        atual = escolher or self.cb.currentText()
        self.cb.blockSignals(True)
        self.cb.clear()
        for n in self.servidor.nomes_dos_jogadores():
            self.cb.addItem(n)
        i = self.cb.findText(atual)
        self.cb.setCurrentIndex(i if i >= 0 else 0)
        self.cb.blockSignals(False)

    def _trocou(self):
        self._primeiro = True
        self.cena.nevoa.esquecer()   # outra pessoa: outra memória do que já foi visto
        self.atualizar()

    def nome(self) -> str:
        return self.cb.currentText()

    # ------------------------------------------------------------ desenhar
    def atualizar(self):
        nome = self.nome()
        if not nome:
            self.info.setText("Nenhum jogador ainda (vincule um token a um jogador).")
            return
        try:
            estado, imagens = self.servidor.estado_do_jogador(nome)
        except RuntimeError:
            return
        self.imagens.update(imagens)
        self.cena.meu_nome = nome
        self.cena.aplicar_estado(estado, self.imagens)
        online = any(n.casefold() == nome.casefold() for n in self.servidor.nomes())
        andar = estado.get("andar") or ""
        self.info.setText(("● conectado" if online else "○ ainda não entrou")
                          + (f" · {andar}" if andar else "")
                          + ("" if estado.get("nevoa") else " · névoa desligada (ele vê o mapa todo)"))
        if self._primeiro:
            self._primeiro = False
            QTimer.singleShot(0, self.centralizar)

    def centralizar(self):
        meus = self.cena.meus_tokens()
        if meus:
            self.visao.centerOn(meus[0].centro_cena())
        else:
            self.visao.enquadrar_tudo()
