"""(v0.64.1) Pedido do Manel: o JOGADOR cria o próprio token (só um, sempre dele — nunca de outro tipo nem de
outra pessoa) e edita o dele (duplo clique no token ou o botão ✏, sem precisar acertar o token)."""
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
from taverna.mesa.token import TokenItem
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
w = QTest.qWait


def porta_livre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def esperar(cond, ms=5000):
    for _ in range(ms // 50):
        if cond():
            return True
        w(50)
    return cond()


M = JanelaMestre(); M.resize(1000, 700); M.show(); M.mostrar_mesa(); w(50)
c = M.cena
c.criar_sala(QPointF(-4 * C, -3 * C), QPointF(4 * C, 3 * C))
porta = porta_livre()
assert M.servidor.abrir(porta)
P = JanelaPlayer(); P.resize(1000, 700); P.show()
P.nome, P.ip, P.porta = "Bia", "127.0.0.1", porta
P._ja_entrou = False
P._primeiro_estado = True
P.cliente.conectar(P.ip, P.porta, P.nome)
assert esperar(lambda: P.cliente.dentro)
w(300)
assert P.a_meu_token.text().endswith("Criar meu token")


def tokens_da_bia():
    return [t for t in c.itens_do_usuario() if isinstance(t, TokenItem) and t.dono == "Bia"]


print("== o jogador cria o próprio token")
P.visao.centerOn(QPointF(50 * C, 50 * C))                     # olhando pra fora do cenário: nasce dentro dele
assert P.criar_meu_token({"nome": "Lyra", "cor": "#8a3fbb"})
assert esperar(lambda: len(tokens_da_bia()) == 1)
t = tokens_da_bia()[0]
print("  ", t.nome, t.tipo, t.dono, t.cor.name(), t.tamanho, "em", t.centro_cena())
assert t.nome == "Lyra" and t.tipo == "jogador" and t.cor.name() == "#8a3fbb"
assert c.chao_caminho().contains(t.centro_cena())
assert esperar(lambda: P.cena.meus_tokens())
assert P.a_meu_token.text().endswith("Editar meu token")

print("== não cria um segundo (nem forçando a mensagem)")
assert P.criar_meu_token({"nome": "Outro"}) is False
P.cliente.enviar({"tipo": "criar_token", "nome": "Clone", "cor": "#ffffff", "x": 0, "y": 0})
P.cliente.enviar({"tipo": "criar_token", "nome": "Dragão", "tipo_token": "criatura", "dono": "Manel", "x": 0, "y": 0})
w(800)
assert len(tokens_da_bia()) == 1
assert not any(isinstance(x, TokenItem) and x.nome in ("Clone", "Dragão") for x in c.itens_do_usuario())

print("== edita o dele (duplo clique abre a edição)")
aberto = []
P.cena.ao_editar_meu = lambda tok: aberto.append(tok)
P.cena.token_duplo_clique(P.cena.meus_tokens()[0])
assert aberto and aberto[0].uid == t.uid
P.cliente.enviar({"tipo": "editar_token", "id": t.uid, "nome": "Lyra, a Sábia", "cor": "#aa7722"})
assert esperar(lambda: t.nome == "Lyra, a Sábia" and t.cor.name() == "#aa7722")

print("== o token que o mestre criou pra ele (noutro andar) também edita")
from taverna.mesa.andares import garantir_predio
garantir_predio(c)
cima = M._nova_cena_vazia("1º andar")
M._registrar_cena(cima)
M.cenas.append(cima)
cima.predio, cima.andar = c.predio, 1
M.servidor.definir_andares([c, cima])
c.remover_itens([t])
t2 = cima.adicionar_token({"nome": "Lyra", "tipo": "jogador", "cor": "#8a3fbb", "tamanho": 1, "dono": "Bia"},
                          QPointF(C, C))
w(500)
P.cliente.enviar({"tipo": "editar_token", "id": t2.uid, "nome": "Lyra lá em cima", "cor": "#8a3fbb"})
assert esperar(lambda: t2.nome == "Lyra lá em cima")

print("== e quem não é dono não edita")
orc = c.adicionar_token({"nome": "Orc", "tipo": "criatura", "cor": "#6b3f3f", "tamanho": 1}, QPointF(0, 0))
P.cliente.enviar({"tipo": "editar_token", "id": orc.uid, "nome": "Orc bonzinho"})
w(500)
assert orc.nome == "Orc"
print("FIM")
sys.stdout.flush()
os._exit(0)
