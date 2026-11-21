"""v0.50: 👁 Visão dos jogadores — o mestre vê a mesa como o jogador vê (com a névoa e tudo)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"; os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
app = QApplication(sys.argv); app.setStyle("Fusion")
from taverna.config import CELULA as C
from taverna.ui.janela_mestre import JanelaMestre
from taverna.mesa.token import TokenItem
w = QTest.qWait

M = JanelaMestre(); M.resize(1300, 820); M.show(); M.mostrar_mesa(); w(50)
c = M.cena
c.criar_sala(QPointF(0, 0), QPointF(6 * C, 5 * C))
c.criar_sala(QPointF(6 * C, 0), QPointF(12 * C, 5 * C))   # outra sala, atrás da parede
heroi = c.adicionar_token({"nome": "Aelar", "tipo": "jogador", "cor": "#3f6b4a", "tamanho": 1, "dono": "Bia"},
                          QPointF(2 * C, 2.5 * C))
c.adicionar_token({"nome": "Goblin", "tipo": "criatura", "cor": "#4a6e2f", "tamanho": 1}, QPointF(4 * C, 2.5 * C))
c.adicionar_token({"nome": "Ogro", "tipo": "criatura", "cor": "#6e2a2f", "tamanho": 2}, QPointF(9 * C, 2.5 * C))
M.a_nevoa.setChecked(True); w(100)

print("== o mestre liga a 👁 Visão dos jogadores (a Bia nem entrou ainda)")
M.btn_visao_jogador.setChecked(True); w(500)
pv = M.painel_visao_jogador
assert M.pilha_mesa.currentWidget() is pv and pv.nome() == "Bia"
vejo = sorted(i.nome for i in pv.cena.itens.values() if isinstance(i, TokenItem))
print("a Bia vê:", vejo, "|", pv.info.text())
assert "Aelar" in vejo and "Goblin" in vejo and "Ogro" not in vejo   # o ogro está atrás da parede
print("== o mestre move o ogro pra frente dela: aparece na visão dela")
ogro = next(t for t in c.itens_do_usuario() if isinstance(t, TokenItem) and t.nome == "Ogro")
ogro.setPos(ogro.parentItem().mapFromScene(QPointF(4.5 * C, 3.5 * C)))
w(800)
vejo = sorted(i.nome for i in pv.cena.itens.values() if isinstance(i, TokenItem))
print("agora:", vejo)
assert "Ogro" in vejo
pv.grab().save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida", "visao_jogador.png"))
M.btn_visao_jogador.setChecked(False); w(100)
assert M.pilha_mesa.currentWidget() is M.visao and not pv.timer.isActive()
print("FIM")
