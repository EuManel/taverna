"""(v0.58.9) Futurista com 2 telas (beco de neon / cabine de nave): sorteio 50/50 (e de novo ao escolher o tema),
texturas, letreiros inventados e as cenas 3D compilam sem erro de QML."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtCore import QUrl
from PyQt6.QtQml import QQmlComponent, QQmlEngine
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)
from taverna.ui import futurista_cenas as F
from taverna.ui.lancador import PASTA_QML, Ponte

for n in ("parede_beco", "chao_beco", "planeta", "painel_nave", "linhas_holo", "estrelas_nave"):
    assert not F.textura(n).isNull(), n
assert F.textura("nao_existe") is None

from taverna.ui.tema import guardar_tema_preferido, tema_preferido
tema_antes = tema_preferido()   # (o teste troca o tema salvo; no fim devolve)
p = Ponte()
os.environ.pop("TAVERNA_CENA_FUTURISTA", None)
vistas = set()
for _ in range(40):
    p.definirTema("medieval")
    p.definirTema("futurista")
    vistas.add(p.cenaFuturista)
print("cenas sorteadas:", vistas)
assert vistas == {"beco", "nave"}
os.environ["TAVERNA_CENA_FUTURISTA"] = "nave"
p.definirTema("medieval")
p.definirTema("futurista")
assert p.cenaFuturista == "nave"
os.environ.pop("TAVERNA_CENA_FUTURISTA", None)
assert len(p.letreiros) >= 6   # (palavras inventadas, nada de marca)

eng = QQmlEngine()
eng.rootContext().setContextProperty("ponte", p)
for nome in ("FuturistaBeco.qml", "FuturistaNave.qml"):
    comp = QQmlComponent(eng, QUrl.fromLocalFile(os.path.join(PASTA_QML, nome)))
    erros = [e.toString() for e in comp.errors()]
    print(nome, "->", "ok" if not erros else erros)
    assert not erros, erros
beco = open(os.path.join(PASTA_QML, "FuturistaBeco.qml"), encoding="utf-8").read()
nave = open(os.path.join(PASTA_QML, "FuturistaNave.qml"), encoding="utf-8").read()
assert "menuProprio: true" in beco and "component Placa" in beco and "espelho: true" in beco
assert beco.count("fonte:") >= 10 and "moldura:" in beco and "forma:" in beco   # (cada placa diferente)
assert "menuProprio: true" in nave and "component Holo" in nave and "estacao" in nave
guardar_tema_preferido(tema_antes)
print("FIM")
sys.stdout.flush()
os._exit(0)
