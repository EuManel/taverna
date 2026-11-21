"""(v1.0.1) Aviso de versão nova: compara versões, lê a resposta do GitHub, avisa só quando é mais nova, fica quieto
sem internet ou com resposta estranha, consulta no máximo uma vez por dia, e a tela inicial mostra o aviso (PT/EN).
Nada vai pra internet de verdade aqui: o "GitHub" é falso."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
os.environ["TAVERNA_SEM_DICAS"] = "1"
os.environ.pop("TAVERNA_SEM_ATUALIZACAO", None)
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

app = QApplication(sys.argv)
from taverna import seguranca
erros = []
seguranca.registrar_erro = lambda t: erros.append(t)
from taverna import atualizacao as A
from taverna.config import APP_VERSAO

cfg = QSettings("Taverna", "Geral")
guardado = {k: cfg.value(k) for k in ("atualizacao/tag", "atualizacao/quando")}   # (devolvido no fim)

print("== comparar versões")
assert A.versao_tupla("v1.2") == (1, 2, 0) and A.versao_tupla("1.0.0") == (1, 0, 0)
assert A.versao_tupla("v1.0.1") == (1, 0, 1) and A.versao_tupla("lixo") is None and A.versao_tupla("") is None
assert A.e_mais_nova("v99.0") and A.e_mais_nova("v1.1", "1.0.0") and A.e_mais_nova("v1.0.1", "1.0.0")
assert not A.e_mais_nova("v1.0", "1.0.0") and not A.e_mais_nova("v0.9", "1.0.0") and not A.e_mais_nova("x", "1.0")

print("== ler a resposta do GitHub")
assert A.ler_release(json.dumps({"tag_name": "v1.2", "draft": False, "prerelease": False})) == "v1.2"
assert A.ler_release(json.dumps({"tag_name": "v2.0", "prerelease": True})) is None
assert A.ler_release(json.dumps({"tag_name": "v2.0", "draft": True})) is None
assert A.ler_release(b"<html>rate limit</html>") is None and A.ler_release(b"[]") is None
assert A.ler_release(json.dumps({"message": "Not Found"})) is None


def rodar(baixar, esperar=True):
    avisos = []
    v = A.Verificador(None, baixar=baixar)
    v.novaVersao.connect(avisos.append)
    v.iniciar()
    if esperar and v._thread is not None:
        v._thread.join(5)
    QTest.qWait(50)
    return avisos


def limpar():
    cfg.remove("atualizacao/tag")
    cfg.remove("atualizacao/quando")


print("== versão nova: avisa e guarda")
limpar()
assert rodar(lambda: json.dumps({"tag_name": "v99.0"}).encode()) == ["v99.0"]
assert cfg.value("atualizacao/tag") == "v99.0" and time.time() - float(cfg.value("atualizacao/quando")) < 60

print("== no mesmo dia: não consulta de novo (usa o guardado)")
chamadas = []
assert rodar(lambda: chamadas.append(1) or b"{}") == ["v99.0"] and not chamadas

print("== mesma versão: não avisa")
limpar()
assert rodar(lambda: json.dumps({"tag_name": "v" + APP_VERSAO}).encode()) == []

print("== sem internet / resposta estranha: fica quieto, sem erro")


def sem_internet():
    raise OSError("sem rede")


limpar()
assert rodar(sem_internet) == [] and cfg.value("atualizacao/quando") is None   # (tenta de novo da próxima vez)
assert rodar(lambda: b"\x00\xff lixo") == []

print("== desligado nos testes (TAVERNA_SEM_ATUALIZACAO)")
limpar()
os.environ["TAVERNA_SEM_ATUALIZACAO"] = "1"
chamadas = []
assert rodar(lambda: chamadas.append(1) or b"{}") == [] and not chamadas
os.environ.pop("TAVERNA_SEM_ATUALIZACAO")

print("== a tela inicial mostra o aviso (e não baixa nada)")
os.environ["TAVERNA_SEM_ATUALIZACAO"] = "1"     # (a janela não consulta; o aviso é entregue na mão)
from taverna.ui.lancador import JanelaLancador
from PyQt6.QtQuickWidgets import QQuickWidget
L = JanelaLancador(); L.resize(1280, 800); L.show(); QTest.qWait(300)
assert L.quick.status() == QQuickWidget.Status.Ready
assert L.ponte.avisoVersao == ""
L.ponte.definir_nova_versao("v1.1"); QTest.qWait(100)
assert L.ponte.avisoVersao == "Nova versão v1.1 disponível — baixar", L.ponte.avisoVersao
abertos = []
from PyQt6.QtGui import QDesktopServices
QDesktopServices.openUrl = staticmethod(lambda url: abertos.append(url.toString()) or True)
L.ponte.abrirNovaVersao()
assert abertos == ["https://omanel.itch.io/taverna"], abertos
L.grab().save(os.path.join("saida", "atualizacao_aviso.png"))
from taverna import idioma
idioma.definir("en")
assert L.ponte.avisoVersao == "New version v1.1 available — download", L.ponte.avisoVersao
idioma.definir("pt")

for k, v in guardado.items():
    if v is None:
        cfg.remove(k)
    else:
        cfg.setValue(k, v)
cfg.sync()
assert not erros, erros[:3]
print("OK — atualização")
sys.stdout.flush()
os._exit(0)
