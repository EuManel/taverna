"""(v0.58) 🐞 Reportar problema: o .zip sai com o que aconteceu, o sistema e o erros.log; a aventura só entra se
marcada (e só o .taverna); nunca PDF. O menu Ajuda tem a opção no mestre e no jogador."""
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
from taverna.ui import reportar

app = QApplication(sys.argv)
app.setStyle("Fusion")
app.setStyleSheet(QSS)
pasta = tempfile.mkdtemp()

M = JanelaMestre()
M.resize(1200, 800)
M.show()
M.cena.criar_camadas_padrao()
M.mostrar_mesa()
QTest.qWait(50)
assert M.a_reportar.isEnabled()
# aventura salva + um PDF "da biblioteca" do lado: o PDF nunca pode ir
M.caminho_cena = os.path.join(pasta, "Minha aventura.taverna")
M.salvar()
open(os.path.join(pasta, "livro.pdf"), "wb").write(b"%PDF-1.4 fake")
d = reportar.abrir(M, "mestre")
QTest.qWait(50)
assert d.incluir.isVisible() and d.incluir.isEnabled() and not d.incluir.isChecked(), "a caixinha começa desligada"
d.texto.setPlainText("O token sumiu quando abri a porta.")
saida = os.path.join(pasta, "saida")
cam = d.gerar(pasta=saida, abrir_pasta=False)
nomes = zipfile.ZipFile(cam).namelist()
print("sem a aventura:", os.path.basename(cam), nomes)
assert set(nomes) == {"o_que_aconteceu.txt", "sistema.txt", "erros.log"}
z = zipfile.ZipFile(cam)
assert "O token sumiu" in z.read("o_que_aconteceu.txt").decode()
sis = z.read("sistema.txt").decode()
print(sis)
from taverna.config import APP_VERSAO
for chave in (f"Taverna {APP_VERSAO}", "protocolo", "Windows", "Gráficos", "Mesa em 3D", "OpenGL"):
    assert chave in sis, chave
# com a aventura marcada
d2 = reportar.abrir(M, "mestre")
d2.incluir.setChecked(True)
cam2 = d2.gerar(pasta=os.path.join(pasta, "saida2"), abrir_pasta=False)
nomes2 = zipfile.ZipFile(cam2).namelist()
print("com a aventura:", nomes2)
assert "aventura/Minha aventura.taverna" in nomes2 and not any(n.lower().endswith(".pdf") for n in nomes2)
# texto vazio também funciona
cam3 = reportar.gerar_pacote("", "mestre", None, os.path.join(pasta, "saida3"))
assert "não escreveu" in zipfile.ZipFile(cam3).read("o_que_aconteceu.txt").decode()

# jogador: tem a opção no menu Ajuda e NÃO tem a caixinha da aventura
P = JanelaPlayer()
P.show()
QTest.qWait(50)
assert P.a_reportar in P._menu_ajuda.actions()
dp = reportar.abrir(P, "jogador")
assert not dp.incluir.isVisible()
camp = dp.gerar(pasta=os.path.join(pasta, "saida4"), abrir_pasta=False)
assert "jogador" in zipfile.ZipFile(camp).read("sistema.txt").decode()
print("FIM")
sys.stdout.flush()
os._exit(0)
