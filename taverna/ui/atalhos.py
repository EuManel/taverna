"""
⌨ Tela de atalhos (F1) — v0.58, pedido do Manel.

Mostra TODOS os atalhos do papel de quem abriu (mestre vê os do mestre, jogador os do jogador), em grupos,
com busca. Também lista os comandos do mouse. Abre pelo F1 e pelo menu Ajuda.

A lista fica aqui num lugar só. Quando um atalho mudar no código, mude aqui também: o `teste_atalhos.py`
confere que cada tecla marcada como "da janela" existe mesmo na janela (e avisa se faltar).
Decisão do Manel (v0.58): teclas que fazem uma coisa no mestre e outra no jogador (Ctrl+P, E, Ctrl+I,
Ctrl+T) ficam como estão — ninguém é os dois ao mesmo tempo.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem,
                             QVBoxLayout)

# (tecla, o que faz, da_janela)
# da_janela=True: é um atalho registrado na própria janela (QAction/QShortcut) — o teste confere.
# da_janela=False: é tecla tratada na mesa, em outra janela (biblioteca, ficha) ou é o mouse.
MESTRE = [
    ("Arquivo", [
        ("Ctrl+N", "Nova sessão", True),
        ("Ctrl+O", "Abrir sessão", True),
        ("Ctrl+S", "Salvar", True),
        ("Ctrl+Shift+S", "Salvar como", True),
        ("Ctrl+I", "Importar mapa (imagem)", True),
        ("Ctrl+W", "Fechar a sessão e voltar pro início", True),
        ("Ctrl+Q", "Sair", True),
    ]),
    ("Edição", [
        ("Ctrl+Z", "Desfazer", True),
        ("Ctrl+Y", "Refazer (também Ctrl+Shift+Z)", True),
        ("Delete", "Remover os selecionados", True),
        ("Ctrl+A", "Selecionar tudo", True),
    ]),
    ("Construção", [
        ("V", "Selecionar", True),
        ("B", "Pincel de terreno (chão)", True),
        ("E", "Borracha de terreno", True),
        ("W", "Parede", True),
        ("Shift+E", "Borracha de parede", True),
        ("R", "Sala (arraste um retângulo)", True),
        ("D", "Porta", True),
        ("L", "Luz", True),
        ("[", "Pincel menor", True),
        ("]", "Pincel maior", True),
        ("Esc", "Soltar a ferramenta / cancelar", True),
    ]),
    ("Mesa e câmera", [
        ("T", "Tokens (biblioteca de tokens)", True),
        ("S", "Snap no grid (liga/desliga)", True),
        ("Home", "Enquadrar a mesa toda", True),
        ("Ctrl+0", "Zoom 100%", True),
        ("M (segurar)", "Régua: segure M e arraste pra medir", False),
        ("P", "Ping: marca o ponto do mouse pra todos", False),
        ("Shift+P", "📣 Levar a câmera de todos até o mouse", False),
        ("Espaço (segurar)", "Arrastar a mesa com o mouse", False),
    ]),
    ("Tokens e visão", [
        (",", "Girar os selecionados pra esquerda", True),
        (".", "Girar os selecionados pra direita", True),
        ("F", "Os selecionados olham pro mouse", True),
    ]),
    ("Combate", [
        ("N", "Próximo turno", True),
        ("Ctrl+K", "Painel de combate", True),
    ]),
    ("Painéis", [
        ("Ctrl+D", "Dados", True),
        ("Ctrl+E", "Chat", True),
        ("Ctrl+H", "Histórico (só você vê)", True),
        ("Ctrl+J", "Objetos e banco de imagens", True),
        ("Ctrl+T", "Atmosfera (clima, áreas, sons, música)", True),
        ("Ctrl+P", "Projetor", True),
        ("Ctrl+B", "Biblioteca", True),
        ("Ctrl+Shift+D", "Diário da campanha", True),
    ]),
    ("Biblioteca (com ela aberta)", [
        ("PgUp / PgDown", "Página anterior / próxima", False),
        ("Ctrl+F", "Buscar no PDF", False),
        ("F3 / Shift+F3", "Próximo / anterior resultado", False),
    ]),
    ("Mouse", [
        ("Roda", "Zoom", False),
        ("Botão do meio + arrastar", "Arrastar a mesa", False),
        ("Alt + arrastar", "Câmera livre: girar (pro lado) e inclinar (pra cima/baixo) — solte o cadeado da bússola", False),
        ("Bússola (canto da mesa)", "Clique duplo: volta pro reto de cima · rodinha: inclina · ◀ ▶: giram", False),
        ("Botão direito no token → Ver pelos olhos", "Câmera por cima do ombro, acompanhando o token (Esc sai)", False),
        ("Botão direito", "Menu do que está embaixo do mouse", False),
        ("Duplo clique", "Abrir porta, baú, objeto…", False),
    ]),
    ("Ajuda", [
        ("F1", "Esta tela de atalhos", True),
    ]),
]

JOGADOR = [
    ("Mesa e câmera", [
        ("C", "Centralizar no seu token", True),
        ("Home", "Ver a mesa toda", True),
        ("M (segurar)", "Régua: segure M e arraste pra medir", False),
        ("P", "Ping: marca o ponto do mouse pra todos", False),
        ("Espaço (segurar)", "Arrastar a mesa com o mouse", False),
    ]),
    ("Seu personagem", [
        ("Q", "Girar pra esquerda (se o mestre liberar)", True),
        ("E", "Girar pra direita (se o mestre liberar)", True),
        ("F", "Olhar pro mouse", True),
        ("I", "Inventário", True),
        ("Ctrl+P", "Sua ficha", True),
    ]),
    ("Painéis", [
        ("Ctrl+K", "Combate", True),
        ("Ctrl+D", "Dados", True),
        ("Ctrl+E", "Chat", True),
        ("Ctrl+I", "Informações", True),
        ("Ctrl+T", "Templates e lápis", True),
        ("Ctrl+M", "Som e música", True),
        ("Ctrl+B", "Biblioteca", True),
        ("Ctrl+Shift+D", "Diário da campanha", True),
    ]),
    ("Biblioteca (com ela aberta)", [
        ("PgUp / PgDown", "Página anterior / próxima", False),
        ("Ctrl+F", "Buscar no PDF", False),
        ("F3 / Shift+F3", "Próximo / anterior resultado", False),
    ]),
    ("Ficha em PDF (com ela aberta)", [
        ("Ctrl+S", "Salvar a ficha", False),
        ("Ctrl++ / Ctrl+-", "Zoom", False),
    ]),
    ("Mouse", [
        ("Roda", "Zoom", False),
        ("Botão do meio + arrastar", "Arrastar a mesa", False),
        ("Alt + arrastar", "Câmera livre: girar (pro lado) e inclinar (pra cima/baixo) — solte o cadeado da bússola", False),
        ("Bússola (canto da mesa)", "Clique duplo: volta pro reto de cima · rodinha: inclina · ◀ ▶: giram", False),
        ("Botão direito no token → Ver pelos olhos", "Câmera por cima do ombro, acompanhando o token (Esc sai)", False),
        ("Botão direito", "Menu rápido (usar magia, item…)", False),
        ("Duplo clique", "Abrir porta, baú, pegar item…", False),
    ]),
    ("Ajuda", [
        ("F1", "Esta tela de atalhos", True),
    ]),
]


def lista(papel: str):
    return MESTRE if papel == "mestre" else JOGADOR


class JanelaAtalhos(QDialog):
    def __init__(self, papel: str, parent=None):
        super().__init__(parent)
        self.papel = papel
        self.setWindowTitle("⌨  Atalhos — " + ("Mestre" if papel == "mestre" else "Jogador"))
        self.resize(620, 660)
        lay = QVBoxLayout(self)
        topo = QHBoxLayout()
        dica = QLabel("Os atalhos do " + ("mestre" if papel == "mestre" else "jogador") + ". Digite pra procurar:")
        topo.addWidget(dica)
        lay.addLayout(topo)
        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Procurar… (ex.: régua, porta, Ctrl+D)")
        self.busca.setClearButtonEnabled(True)
        self.busca.textChanged.connect(self.filtrar)
        lay.addWidget(self.busca)
        self.arvore = QTreeWidget()
        self.arvore.setColumnCount(2)
        self.arvore.setHeaderLabels(["Tecla", "O que faz"])
        self.arvore.setRootIsDecorated(False)
        self.arvore.setUniformRowHeights(True)
        self.arvore.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)
        self.arvore.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        fonte_grupo = self.arvore.font()
        fonte_grupo.setBold(True)
        for grupo, linhas in lista(papel):
            g = QTreeWidgetItem([grupo, ""])
            g.setFirstColumnSpanned(False)
            g.setFont(0, fonte_grupo)
            self.arvore.addTopLevelItem(g)
            for tecla, texto, _ in linhas:
                f = QTreeWidgetItem(g, [tecla, texto])
                f.setFont(0, fonte_grupo)
            g.setExpanded(True)
            g.setFirstColumnSpanned(True)
        self.arvore.setColumnWidth(0, 210)
        lay.addWidget(self.arvore, 1)
        baixo = QHBoxLayout()
        baixo.addWidget(QLabel("F1 abre esta tela de qualquer lugar da mesa."))
        baixo.addStretch(1)
        fechar = QPushButton("Fechar")
        fechar.clicked.connect(self.close)
        baixo.addWidget(fechar)
        lay.addLayout(baixo)
        from .acabamento import iconizar
        iconizar(self)
        self.busca.setFocus()

    def filtrar(self, texto: str):
        t = texto.strip().lower()
        for i in range(self.arvore.topLevelItemCount()):
            g = self.arvore.topLevelItem(i)
            algum = False
            for k in range(g.childCount()):
                f = g.child(k)
                ok = not t or t in f.text(0).lower() or t in f.text(1).lower() or t in g.text(0).lower()
                f.setHidden(not ok)
                algum = algum or ok
            g.setHidden(not algum)

    def visiveis(self):
        """(pros testes) as linhas que estão aparecendo."""
        out = []
        for i in range(self.arvore.topLevelItemCount()):
            g = self.arvore.topLevelItem(i)
            for k in range(g.childCount()):
                if not g.child(k).isHidden() and not g.isHidden():
                    out.append((g.child(k).text(0), g.child(k).text(1)))
        return out


def abrir(janela, papel: str):
    """Abre (ou traz pra frente) a tela de atalhos da janela."""
    atual = getattr(janela, "_janela_atalhos", None)
    if atual is None:
        atual = janela._janela_atalhos = JanelaAtalhos(papel, janela)
    atual.show()
    atual.raise_()
    atual.activateWindow()
    return atual
