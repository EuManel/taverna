"""(v0.58) Moderno com 2 telas (celular / terraço): sorteio 50/50 (e de novo ao escolher o tema), texturas,
grade de LED, notificações inventadas e as cenas 3D compilam sem erro de QML."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtCore import QUrl
from PyQt6.QtQml import QQmlComponent, QQmlEngine
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)
from taverna.ui import moderno_cenas as M
from taverna.ui.lancador import PASTA_QML, Ponte, ProvedorTaverna

for n in ("mesa_moderna", "documento", "couro_preto", "ceu_cidade", "concreto", "asfalto", "papel_outdoor",
          "fachada0", "fachada0_luz", "fachada1", "fachada2_luz"):
    assert not M.textura(n).isNull(), n
img, _ = ProvedorTaverna().requestImage("led/grade", None)
print("grade de LED:", img.size())
assert img.width() == 8 and img.hasAlphaChannel()
# (v0.58) fachada única por prédio: cor e luz do mesmo tamanho, e sementes diferentes = prédios diferentes
a, b = M.textura("predio_7_10_20"), M.textura("predio_7_10_20_luz")
assert a.size() == b.size() and not a.isNull()
assert M.textura("predio_8_10_20") != a
from taverna.ui.geometria3d import malha
assert len(malha("tentaculo|1|0.6|0.22|0.07|0.012")["idx"]) > 1000   # (o Cthulhu 3D)

from taverna.ui.tema import guardar_tema_preferido, tema_preferido
tema_antes = tema_preferido()   # (o teste troca o tema salvo; no fim devolve)
p = Ponte()
os.environ.pop("TAVERNA_CENA_MODERNO", None)
vistas = set()
for _ in range(40):                      # sorteia de novo a cada vez que escolhe o tema
    p.definirTema("medieval")
    p.definirTema("moderno")
    vistas.add(p.cenaModerno)
print("cenas sorteadas:", vistas)
assert vistas == {"celular", "terraco"}
os.environ["TAVERNA_CENA_MODERNO"] = "terraco"
p.definirTema("medieval")
p.definirTema("moderno")
assert p.cenaModerno == "terraco"
os.environ.pop("TAVERNA_CENA_MODERNO", None)
assert len(p.notificacoes) >= 5 and all(len(n) == 2 for n in p.notificacoes)

eng = QQmlEngine()
eng.rootContext().setContextProperty("ponte", p)
for nome in ("ModernoCelular.qml", "ModernoTerraco.qml"):
    comp = QQmlComponent(eng, QUrl.fromLocalFile(os.path.join(PASTA_QML, nome)))
    erros = [e.toString() for e in comp.errors()]
    print(nome, "->", "ok" if not erros else erros)
    assert not erros, erros
cel = open(os.path.join(PASTA_QML, "ModernoCelular.qml"), encoding="utf-8").read()
ter = open(os.path.join(PASTA_QML, "ModernoTerraco.qml"), encoding="utf-8").read()
assert "function vibrar()" in cel and "property rect tela" in cel
assert "menuProprio: true" in ter and "component Refletor" in ter and "alvoEsq" in ter   # (v0.58: outdoor de papel + refletores)
guardar_tema_preferido(tema_antes)
print("FIM")
sys.stdout.flush()
os._exit(0)
