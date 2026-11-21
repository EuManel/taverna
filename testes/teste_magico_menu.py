"""(v0.58) Mágico, círculo: o menu escrito com luz na pedra. Confere as texturas novas (fendas com relevo, runas
soltas), a cor de destaque (dourado/ciano) e que as cenas 3D do Mágico compilam sem erro de QML."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtCore import QUrl
from PyQt6.QtQml import QQmlComponent, QQmlEngine
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)
from taverna.ui import magico_cenas as M
from taverna.ui.lancador import PASTA_QML, Ponte

# fendas: as 3 texturas (cor, luz, relevo) do mesmo tamanho (pra baterem certinho)
cor, luz, rel = M.textura("pedra_rachada"), M.textura("fendas_luz"), M.textura("fendas_normal")
print("fendas:", cor.size(), luz.size(), rel.size())
assert cor.size() == luz.size() == rel.size() and cor.width() == 1024
for k in range(16):
    assert not M.textura(f"runa_{k}").isNull()

# cor de destaque: dourado por padrão, ciano pela variável (pra comparar)
p = Ponte()
os.environ.pop("TAVERNA_DESTAQUE", None)
assert p.destaqueMagico == "#f2c454"
os.environ["TAVERNA_DESTAQUE"] = "ciano"
assert p.destaqueMagico == "#4ee8f0"
os.environ.pop("TAVERNA_DESTAQUE", None)

# as cenas compilam (o QML é lido e checado; desenhar o 3D precisa da placa de vídeo)
eng = QQmlEngine()
eng.rootContext().setContextProperty("ponte", p)
for nome in ("MagicoCirculo.qml", "MagicoTorre.qml"):
    comp = QQmlComponent(eng, QUrl.fromLocalFile(os.path.join(PASTA_QML, nome)))
    erros = [e.toString() for e in comp.errors()]
    print(nome, "->", "ok" if not erros else erros)
    assert not erros, erros
texto = open(os.path.join(PASTA_QML, "MagicoCirculo.qml"), encoding="utf-8").read()
for chave in ("menuProprio: true", "tituloProprio: true", "ritual", "pedra_rachada", "fendas_normal"):
    assert chave in texto, chave
print("FIM")
sys.stdout.flush()
os._exit(0)
