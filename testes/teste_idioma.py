"""(v1.0) Idiomas: português (o original) e inglês, trocados pelas bandeirinhas da tela inicial.
Confere: o dicionário carrega; frases inteiras, modelos ("Rodada 3"), HTML, emoji e maiúsculas traduzem; o que não
está no dicionário (nome de token) fica igual; a tela inicial troca de idioma e volta; a janela do Mestre em
inglês não tem texto em português; o compêndio vem em inglês; em português nada muda."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
os.environ["TAVERNA_SEM_DICAS"] = "1"
os.environ["TAVERNA_IDIOMA"] = "en"
from PyQt6.QtWidgets import QAbstractButton, QApplication, QComboBox, QLabel, QMessageBox, QWidget
from PyQt6.QtGui import QAction
from PyQt6.QtTest import QTest

app = QApplication(sys.argv)
from taverna import seguranca
erros = []
seguranca.registrar_erro = lambda t: erros.append(t)
from PyQt6.QtCore import QSettings
_ORIGINAL = QSettings("Taverna", "Geral").value("idioma", "pt", type=str)   # (devolvido no fim)
from taverna import idioma
idioma.instalar(app)

# ---- o tradutor
t = idioma.t
assert idioma.atual() == "en"
assert t("🍺  Abrir taverna") == "🍺  Open tavern", t("🍺  Abrir taverna")
assert t("Rodada 3") == "Round 3", t("Rodada 3")
assert t("<b>Mestre</b>") == "<b>Game Master</b>", t("<b>Mestre</b>")
assert t("Aelar, o Ladino") == "Aelar, o Ladino"            # (não está no dicionário: fica igual)
assert t("NOVA SESSÃO") == "NEW SESSION", t("NOVA SESSÃO")
assert t("Abrir a pasta do banco") == "Open the bank folder", t("Abrir a pasta do banco")   # (sem o emoji)
assert t("Gelo  ·  Cristal de gelo") == "Ice  ·  Ice crystal", t("Gelo  ·  Cristal de gelo")

# ---- os pontos do Qt
lb = QLabel("Jogador")
lb.show(); QTest.qWait(10)
assert lb.text() == "Player", lb.text()
lb.setText("Rodada 7")
assert lb.text() == "Round 7", lb.text()
cb = QComboBox(); cb.addItems(["Alto", "Baixo"])
assert [cb.itemText(k) for k in range(2)] == ["High", "Low"]

# ---- a tela inicial: inglês → português → inglês
from taverna.ui.lancador import JanelaLancador, bandeira
from PyQt6.QtQuickWidgets import QQuickWidget
for c in ("pt", "en"):
    img = bandeira(c, 2.0)
    assert img.width() == 60 and img.height() == 40 and img.pixelColor(30, 20).alpha() == 255
L = JanelaLancador(); L.resize(1280, 800); L.show(); QTest.qWait(300)
assert L.quick.status() == QQuickWidget.Status.Ready
assert L.ponte.idioma == "en"
assert any(n["nome"] == "High" for n in L.ponte.niveis), L.ponte.niveis
pasta = idioma.pasta_qml(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                      "taverna", "ui", "qml"))
qml = open(os.path.join(pasta, "Lancador.qml"), encoding="utf-8").read()
assert '"New session"' in qml and '"Nova sessão"' not in qml and '"mestre_nova"' in qml
L.ponte.definirIdioma("pt"); QTest.qWait(300)
assert idioma.atual() == "pt" and L.quick.status() == QQuickWidget.Status.Ready
assert t("Rodada 3") == "Rodada 3"
lb2 = QLabel(); lb2.setText("Jogador")
assert lb2.text() == "Jogador"                               # português: nada muda
assert any(n["nome"] == "Alto" for n in L.ponte.niveis)
L.ponte.definirIdioma("en"); QTest.qWait(300)
assert idioma.atual() == "en" and L.quick.status() == QQuickWidget.Status.Ready
L.grab().save(os.path.join("saida", "idioma_lancador_en.png"))

# ---- a janela do Mestre em inglês
from taverna.ui.janela_mestre import JanelaMestre
M = JanelaMestre(); M.resize(1500, 900); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); QTest.qWait(300)
assert "Untitled adventure" in M.windowTitle() and "Scene 1" in M.windowTitle(), M.windowTitle()
menus = [a.text() for a in M.menuBar().actions()]
assert "&File" in menus and "&Session" in menus, menus
PT = re.compile(r"[ãõçáéíóúâêô]|\b(de|do|da|para|pra|com|não|sem|você|aqui|mesa|jogador|mestre|abrir|fechar|salvar)\b",
                re.I)
sobrou = set()
for w in M.findChildren(QWidget):
    textos = [w.toolTip()]
    if isinstance(w, (QLabel, QAbstractButton)):
        textos.append(w.text())
    if isinstance(w, QComboBox):
        textos += [w.itemText(k) for k in range(w.count())]
    sobrou |= {x for x in textos if x and PT.search(x)}
for a in M.findChildren(QAction):
    sobrou |= {x for x in (a.text(), a.toolTip()) if x and PT.search(x)}
# (as rolagens salvas são do usuário: "Dano da espada" etc. não contam)
sobrou = {x for x in sobrou if not any(p in x for p in ("espada", "Espada"))}
assert not sobrou, sobrou
M.grab().save(os.path.join("saida", "idioma_mestre_en.png"))

# ---- caixa de aviso (função estática)
from PyQt6.QtCore import QTimer
vistos = []


def _fechar():
    for w in app.topLevelWidgets():
        if isinstance(w, QMessageBox) and w.isVisible():
            vistos.append((w.windowTitle(), w.text()))
            w.accept()


QTimer.singleShot(200, _fechar)
QMessageBox.information(M, "Sessão", "Abrir taverna")
assert vistos and vistos[0] == ("Session", "Open tavern"), vistos

# ---- o compêndio (SRD) em inglês
from taverna.compendio.compendio import compendio
c = compendio()
nomes = {e["nome"] for e in c.entradas["classes"]}
assert "Wizard" in nomes, sorted(nomes)[:5]

QSettings("Taverna", "Geral").setValue("idioma", _ORIGINAL)
QSettings("Taverna", "Geral").sync()
assert not erros, erros[:3]
print("OK — idiomas")
os._exit(0)
