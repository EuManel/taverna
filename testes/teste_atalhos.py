"""(v0.58) Tela de atalhos (F1): a lista confere com os atalhos de verdade das janelas, abre pelo F1, a busca
filtra, e o mestre vê os do mestre / o jogador os do jogador."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
from taverna.ui import atalhos

app = QApplication(sys.argv)
app.setStyle("Fusion")
app.setStyleSheet(QSS)
saida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")
os.makedirs(saida, exist_ok=True)


def teclas_da_janela(j):
    """Todas as teclas registradas na janela (QAction e QShortcut)."""
    ks = set()
    for a in j.findChildren(QAction):
        for s in a.shortcuts():
            if not s.isEmpty():
                ks.add(s.toString())
    for s in j.findChildren(QShortcut):
        if not s.key().isEmpty():
            ks.add(s.key().toString())
    return ks


def conferir(j, papel):
    ks = teclas_da_janela(j)
    faltando = []
    total = 0
    for grupo, linhas in atalhos.lista(papel):
        for tecla, texto, da_janela in linhas:
            if da_janela:
                total += 1
                if QKeySequence(tecla).toString() not in ks:
                    faltando.append(f"{tecla} ({texto})")
    print(f"{papel}: {total} atalhos da janela conferidos; faltando: {faltando}")
    assert not faltando, faltando
    # nenhuma tecla repetida DENTRO do mesmo papel
    vistas = {}
    for grupo, linhas in atalhos.lista(papel):
        for tecla, texto, da_janela in linhas:
            if da_janela:
                assert tecla not in vistas, f"{papel}: {tecla} repetida ({vistas[tecla]} / {texto})"
                vistas[tecla] = texto


M = JanelaMestre()
M.resize(1300, 800)
M.show()
QTest.qWait(80)
conferir(M, "mestre")
M.a_atalhos.trigger()
QTest.qWait(80)
d = M._janela_atalhos
assert d.isVisible() and d.papel == "mestre"
n_tudo = len(d.visiveis())
d.busca.setText("régua")
QTest.qWait(30)
print("mestre — busca 'régua':", d.visiveis())
assert len(d.visiveis()) == 1 and "Régua" in d.visiveis()[0][1]
d.busca.setText("ctrl+d")
assert any(t == "Ctrl+D" for t, _ in d.visiveis())
d.busca.setText("xyzqualquercoisa")
assert d.visiveis() == []
d.busca.setText("")
assert len(d.visiveis()) == n_tudo
d.grab().save(os.path.join(saida, "atalhos_mestre.png"))
assert any("Projetor" in txt for _, txt in d.visiveis()) and not any("inventário" in txt.lower() for _, txt in d.visiveis())
d.close()

P = JanelaPlayer()
P.resize(1100, 750)
P.show()
QTest.qWait(80)
conferir(P, "jogador")
P.a_atalhos.trigger()
QTest.qWait(80)
dp = P._janela_atalhos
assert dp.isVisible() and dp.papel == "jogador"
assert any("Inventário" in txt for _, txt in dp.visiveis()) and not any("Projetor" in txt for _, txt in dp.visiveis())
dp.busca.setText("girar")
print("jogador — busca 'girar':", dp.visiveis())
assert {t for t, _ in dp.visiveis()} == {"Q", "E", "Alt + arrastar"}   # (v0.70) + câmera livre
dp.busca.setText("")
dp.grab().save(os.path.join(saida, "atalhos_jogador.png"))
# abrir de novo não cria outra janela
P.a_atalhos.trigger()
assert P._janela_atalhos is dp
dp.close()
print("FIM")
sys.stdout.flush()
os._exit(0)
