"""(v0.81) Documento de conexão: o HOW_TO_CONNECT.txt (era COMO_CONECTAR.txt; v1.0: inglês e português) existe, explica UPnP (código TAV-) → Radmin (IP 26.), vai junto
no gerar_exe.bat, e o botão "❓ Como conectar" do Abrir taverna / Entrar na sessão abre ele."""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtWidgets import QApplication, QPushButton

app = QApplication(sys.argv[:1])
from PyQt6.QtGui import QDesktopServices
from taverna.ui import dialogos

print("== o documento")
arq = dialogos.caminho_como_conectar()
assert arq and os.path.basename(arq) == "HOW_TO_CONNECT.txt", arq
txt = open(arq, encoding="utf-8").read()
for trecho in ("UPnP", "TAV-", "Radmin", "26.", "7777", "CGNAT", "Firewall", "Privada", "Jogador", "Private", "Player"):
    assert trecho in txt, trecho
assert txt.index("[ ENGLISH ]") < txt.index("[ PORTUGUÊS ]")       # (v1.0) inglês primeiro
for parte in txt.split("[ PORTUGUÊS ]"):
    assert parte.index("UPnP") < parte.index("radmin-vpn.com")      # primeiro tenta a internet, depois o Radmin
leia = open(os.path.join(RAIZ, "README.txt"), encoding="utf-8").read()
assert leia.index("[ ENGLISH ]") < leia.index("[ PORTUGUÊS ]") and "HOW_TO_CONNECT.txt" in leia
bat = open(os.path.join(RAIZ, "gerar_exe.bat"), encoding="utf-8", errors="replace").read()
assert "gerar_release.py" in bat                                    # (v1.0) o .bat chama o script de release
rel = open(os.path.join(RAIZ, "gerar_release.py"), encoding="utf-8").read()
assert '"HOW_TO_CONNECT.txt"' in rel and '"README.txt"' in rel       # vão do lado do Taverna.exe

print("== o botão abre o documento (nas duas janelas)")
abertos = []
QDesktopServices.openUrl = staticmethod(lambda url: abertos.append(url.toLocalFile()) or True)
for dlg in (dialogos.DialogoAbrirTaverna(None, [("26.1.2.3", "Radmin VPN")], 7777),
            dialogos.DialogoConectar(None, "Ana", "", 7777)):
    b = [x for x in dlg.findChildren(QPushButton) if "Como conectar" in x.text()]
    assert len(b) == 1, [x.text() for x in dlg.findChildren(QPushButton)]
    assert not b[0].autoDefault()                                  # Enter continua sendo "Abrir"/"Entrar"
    b[0].click()
assert len(abertos) == 2 and all(os.path.samefile(a, arq) for a in abertos), abertos
print("FIM")
sys.stdout.flush()
os._exit(0)
