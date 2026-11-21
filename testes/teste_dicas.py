"""(v0.66) 💡 Dicas de primeiro acesso (mestre e jogador): uma vez só, destacando a coisa explicada, com
Anterior/Próxima/Pular (Esc pula), e o menu Ajuda reabre. Usa preferências TEMPORÁRIAS (não marca nada no
Taverna de verdade)."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

app = QApplication(sys.argv)
from taverna.ui import dicas
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")
pasta = tempfile.mkdtemp(prefix="taverna_dicas_")

print("== mestre")
M = JanelaMestre(); M.resize(1300, 820); M.show()
M.config = QSettings(os.path.join(pasta, "mestre.ini"), QSettings.Format.IniFormat)
M.mostrar_mesa(); QTest.qWait(1200)
assert getattr(M, "_tour_dicas", None) is None                     # nos testes não abre sozinho
t = dicas.mostrar(M, "mestre", forcar=True)
assert t is not None and t.i == 0 and t.alvo() is None
QTest.keyClick(t, Qt.Key.Key_Right)
assert t.i == 1 and t.alvo() is not None                            # a barra de ferramentas destacada
M.grab().save(os.path.join(SAIDA, "dicas_mestre_barra.png"))
QTest.keyClick(t, Qt.Key.Key_Right)
QTest.keyClick(t, Qt.Key.Key_Left)
assert t.i == 1
for _ in range(4):
    t.b_ir.click()
assert t.i == 5
print("   passo 6:", t.titulo.text(), "· destaque:", t.alvo())
M.grab().save(os.path.join(SAIDA, "dicas_mestre_taverna.png"))
QTest.keyClick(t, Qt.Key.Key_Escape)
QTest.qWait(50)
assert M._tour_dicas is None and dicas.ja_viu(M.config)
assert dicas.mostrar(M, "mestre") is None                           # já viu: não abre de novo sozinho
t2 = dicas.mostrar(M, "mestre", forcar=True)                         # (menu Ajuda) reabre
assert t2 is not None
while t2.i < len(t2.passos) - 1:
    t2.b_ir.click()
assert t2.b_ir.text() == "Entendi!" and not t2.b_pular.isVisibleTo(t2)
t2.b_ir.click()
assert M._tour_dicas is None

print("== jogador")
P = JanelaPlayer(); P.resize(1200, 780); P.show()
P.config = QSettings(os.path.join(pasta, "jogador.ini"), QSettings.Format.IniFormat)
P.mostrar_mesa(); QTest.qWait(300)
tj = dicas.mostrar(P, "jogador", forcar=True)
tj.b_ir.click()
print("   passo 2:", tj.titulo.text(), "· destaque:", tj.alvo())
assert tj.titulo.text() == "O seu token" and tj.alvo() is not None   # o botão ✏ Criar meu token
P.grab().save(os.path.join(SAIDA, "dicas_jogador_token.png"))
tj.terminar()
assert dicas.ja_viu(P.config)
print("FIM")
sys.stdout.flush()
os._exit(0)
