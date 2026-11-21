"""(v0.65.1) Pedidos do Manel: no combate, o JOGADOR encerra o próprio turno (só na vez de um token dele), e a
iniciativa que ele rola só aparece na lista DEPOIS que o dado mostra o resultado."""
import os
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

app = QApplication(sys.argv)
from taverna.config import CELULA as C
from taverna.ui import painel_combate as PC
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
w = QTest.qWait


def esperar(cond, ms=5000):
    for _ in range(ms // 50):
        if cond():
            return True
        w(50)
    return cond()


s = socket.socket()
s.bind(("127.0.0.1", 0))
porta = s.getsockname()[1]
s.close()
M = JanelaMestre(); M.resize(1000, 700); M.show(); M.mostrar_mesa(); w(50)
c = M.cena
c.criar_sala(QPointF(-4 * C, -3 * C), QPointF(4 * C, 3 * C))
aelar = c.adicionar_token({"nome": "Aelar", "tipo": "jogador", "cor": "#3f6b4a", "tamanho": 1, "dono": "Manel"},
                          QPointF(-C, 0))
orc = c.adicionar_token({"nome": "Orc", "tipo": "criatura", "cor": "#6b3f3f", "tamanho": 1}, QPointF(2 * C, 0))
assert M.servidor.abrir(porta)
P = JanelaPlayer(); P.resize(1000, 700); P.show()
P.nome, P.ip, P.porta = "Manel", "127.0.0.1", porta
P._ja_entrou = False
P._primeiro_estado = True
P.cliente.conectar(P.ip, P.porta, P.nome)
assert esperar(lambda: P.cliente.dentro)
w(300)

print("== iniciativa: o número só aparece quando o dado parar")
srv = M.servidor
srv.combate.iniciar([aelar, orc])
srv.atualizar_combate()
srv.combate.definir_iniciativa(orc.uid, 8)
srv.atualizar_combate()
srv.transmitir_agora()
assert esperar(lambda: P.painel_combate._pendente == aelar.uid)
# simula o dado 3D rolando (nos testes não tem placa de vídeo): segura a revelação
segurados = []
P.dados3d.rolar = lambda r: (segurados.append(r), True)[1]
M.dados3d.rolar = lambda r: True
P.painel_combate.mod.setValue(3)
P.painel_combate._rolar()
assert esperar(lambda: segurados and srv.combate.participante(aelar.uid)["ini"] is not None)
w(400)
total = srv.combate.participante(aelar.uid)["ini"]
linha = next(P.painel_combate.lista.item(i).text() for i in range(P.painel_combate.lista.count())
             if "Aelar" in P.painel_combate.lista.item(i).text())
print("   enquanto rola:", repr(linha), "· total no mestre:", total)
assert "…" in linha and str(total) not in linha.split("Aelar")[0]
mestre_ini = next(M.painel_combate.tabela.item(k, 2).text() for k in range(M.painel_combate.tabela.rowCount())
                  if "Aelar" in M.painel_combate.tabela.item(k, 1).text())
assert mestre_ini == "…", mestre_ini                              # o mestre também espera o dado dele
P._mostrar_rolagem(segurados[0])                                   # o dado parou
linha = next(P.painel_combate.lista.item(i).text() for i in range(P.painel_combate.lista.count())
             if "Aelar" in P.painel_combate.lista.item(i).text())
print("   dado parou:", repr(linha))
assert str(total) in linha
M._mostrar_rolagem(dict(segurados[0], token=aelar.uid))
mestre_ini = next(M.painel_combate.tabela.item(k, 2).text() for k in range(M.painel_combate.tabela.rowCount())
                  if "Aelar" in M.painel_combate.tabela.item(k, 1).text())
assert mestre_ini == str(total)

print("== o jogador encerra o PRÓPRIO turno")
srv.combate.comecar()
while srv._tokens().get(srv.combate.vez) is not aelar:
    srv.proximo_turno()
srv.transmitir_agora()
assert esperar(lambda: not P.painel_combate.btn_encerrar.isHidden())
rodada_antes = srv.combate.rodada
P.painel_combate.btn_encerrar.click()
assert esperar(lambda: srv.combate.vez == orc.uid)
assert esperar(lambda: P.painel_combate.btn_encerrar.isHidden())   # não é mais a vez dele
print("   vez passou pro Orc; botão sumiu")
print("== fora da vez dele, a mensagem não passa nada")
P.cliente.enviar({"tipo": "encerrar_turno"})
w(500)
assert srv.combate.vez == orc.uid
print("FIM")
sys.stdout.flush()
os._exit(0)
