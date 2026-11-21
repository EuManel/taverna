"""
Opção de GRÁFICOS (cada pessoa escolhe a sua, fica salva no PC):

  baixo — efeitos simples, sem animação pesada (PC fraco / notebook na bateria)
  medio — o equilíbrio (padrão)
  alto  — tudo ligado: partículas, brilho, animações completas

Quem desenha pergunta `nivel()` (0, 1, 2) ou usa os atalhos `escolha(baixo, medio, alto)`.
"""

from PyQt6.QtCore import QObject, QSettings, pyqtSignal

NIVEIS = {"baixo": "Baixo — leve (PC fraco)", "medio": "Médio — equilibrado", "alto": "Alto — tudo ligado"}
_ORDEM = ["baixo", "medio", "alto"]


class _Graficos(QObject):
    mudou = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        cfg = QSettings("Taverna", "Geral")
        v = cfg.value("graficos", "medio")
        self.atual = v if v in NIVEIS else "medio"
        self.tremor = cfg.value("tremor_tela", "1") != "0"     # tela tremer (explosão…)
        self.clarao = cfg.value("clarao_tela", "1") != "0"     # tela clarear (raio…)
        self.dados3d = cfg.value("dados3d_tela", "1") != "0"   # dados 3D rolando na mesa
        self.mesa3d = cfg.value("mesa3d_tela", "1") != "0"     # mesa em 3D (paredes com altura…)

    def definir(self, chave: str):
        if chave in NIVEIS and chave != self.atual:
            self.atual = chave
            QSettings("Taverna", "Geral").setValue("graficos", chave)
            self.mudou.emit(chave)

    def definir_opcao(self, nome: str, ligado: bool):
        setattr(self, nome, bool(ligado))
        QSettings("Taverna", "Geral").setValue(f"{nome}_tela", "1" if ligado else "0")


_G = None


def graficos() -> _Graficos:
    global _G
    if _G is None:
        _G = _Graficos()
    return _G


def nivel() -> int:
    """0 = baixo · 1 = médio · 2 = alto"""
    return _ORDEM.index(graficos().atual)


def escolha(baixo, medio, alto):
    return (baixo, medio, alto)[nivel()]


def menu_graficos(menu, pai):
    """Monta o submenu 'Gráficos' (usado no Mestre e no Player)."""
    from PyQt6.QtGui import QAction, QActionGroup
    g = graficos()
    grupo = QActionGroup(pai)
    for chave, nome in NIVEIS.items():
        a = QAction(nome, pai)
        a.setCheckable(True)
        a.setChecked(g.atual == chave)
        a.setData(chave)
        a.triggered.connect(lambda _=False, k=chave: g.definir(k))
        grupo.addAction(a)
        menu.addAction(a)
    g.mudou.connect(lambda k: [a.setChecked(a.data() == k) for a in grupo.actions()])
    menu.addSeparator()
    for nome, texto in (("tremor", "Tela tremer (explosões, terremotos)"), ("clarao", "Tela clarear (raios, clarões)"),
                        ("dados3d", "Dados 3D rolando na mesa"),
                        ("mesa3d", "Mesa em 3D (paredes e portas com altura)")):
        a = QAction(texto, pai)
        a.setCheckable(True)
        a.setChecked(getattr(g, nome))
        a.toggled.connect(lambda v, n=nome: g.definir_opcao(n, v))
        if nome == "mesa3d":   # redesenha a mesa na hora
            a.toggled.connect(lambda _v: g.mudou.emit(g.atual))
        menu.addAction(a)
    return grupo
