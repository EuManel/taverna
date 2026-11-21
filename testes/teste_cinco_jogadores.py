"""(v0.82) Ensaio do teste com os amigos: o mestre e CINCO jogadores pela rede local, numa mesa "de verdade" (mapa,
salas com paredes e porta, 30 criaturas, névoa, combate). Confere que todo mundo vê o que deve (cada um move o seu, o
mestre move os monstros, ninguém mexe no dos outros) e MEDE quanto custa pro mestre mandar a mesa pros 5."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
os.environ["TAVERNA_SEM_DICAS"] = "1"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

app = QApplication(sys.argv[:1])
from taverna import seguranca
erros = []
seguranca.registrar_erro = lambda t: erros.append(t)
from taverna.config import CELULA as C
from taverna.mesa.token import TokenItem
from taverna.rede import servidor as mod_servidor
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer

PORTA = 7791
NOMES = ["Ana", "Beto", "Caio", "Duda", "Eli"]
AQUI = os.path.dirname(os.path.abspath(__file__))

# mede cada envio da mesa (montar + filtrar + mandar pra todo mundo) — antes de criar o mestre (o timer liga o método)
tempos = []
orig = mod_servidor.ServidorMestre._transmitir


def medir(self):
    t0 = time.perf_counter()
    orig(self)
    tempos.append((time.perf_counter() - t0) * 1000)


mod_servidor.ServidorMestre._transmitir = medir
bytes_enviados = []
orig_estado = mod_servidor.ServidorMestre._enviar_estado


pedacos = {}


def contar(self, conexao, estado, imagens):
    from taverna.rede.protocolo import codificar
    bytes_enviados.append(len(codificar(estado)))
    if os.environ.get("TAVERNA_PEDACOS"):
        for k, v in estado.items():
            pedacos[k] = len(codificar({k: v}))
    orig_estado(self, conexao, estado, imagens)


mod_servidor.ServidorMestre._enviar_estado = contar

from PyQt6.QtWebSockets import QWebSocket
saida_rede = []   # (tipo, bytes) de tudo que sai de verdade pela rede
_orig_send = QWebSocket.sendTextMessage


def _send(self, texto):
    saida_rede.append((texto[:40], len(texto.encode("utf-8"))))
    return _orig_send(self, texto)


QWebSocket.sendTextMessage = _send
_orig_bin = QWebSocket.sendBinaryMessage


def _send_bin(self, dados):
    from taverna.rede.protocolo import abrir_binaria
    texto = abrir_binaria(dados) or ""
    saida_rede.append((texto[:40], len(bytes(dados))))
    return _orig_bin(self, dados)


QWebSocket.sendBinaryMessage = _send_bin

M = JanelaMestre(); M.resize(1200, 800); M.show(); M.mostrar_mesa(); QTest.qWait(80)
c = M.cena
mapa = os.path.join(AQUI, "..", "mapa_teste.png")
if os.path.isfile(mapa):
    M._carregar_imagem(mapa, QPointF(0, 0))
c.criar_sala(QPointF(-10 * C, -6 * C), QPointF(0, 6 * C))
c.criar_sala(QPointF(0, -6 * C), QPointF(10 * C, 6 * C))
herois = {}
for i, n in enumerate(NOMES):
    herois[n] = c.adicionar_token(dict(nome=f"Herói {n}", tipo="jogador", cor="#3f6b4a", tamanho=1, imagem=None,
                                       dono=n), QPointF((-8 + i) * C, 0))
monstros = [c.adicionar_token(dict(nome=f"Goblin {k}", tipo="criatura", cor="#6e2a2f", tamanho=1, imagem=None),
                              QPointF((2 + k % 6) * C, (-4 + k // 6) * C)) for k in range(30)]
c.clearSelection()
assert M.servidor.abrir(PORTA)

print("== 5 jogadores entram")
P = {}
for n in NOMES:
    j = JanelaPlayer(); j.resize(900, 600); j.show()
    j.nome, j.ip, j.porta = n, "127.0.0.1", PORTA
    j._ja_entrou = False; j._primeiro_estado = True
    j.cliente.conectar("127.0.0.1", PORTA, n)
    P[n] = j


def esperar(cond, ms=8000):
    t0 = time.monotonic()
    while time.monotonic() - t0 < ms / 1000:
        QTest.qWait(50)
        if cond():
            return True
    return cond()


assert esperar(lambda: sorted(M.servidor.nomes()) == sorted(NOMES)), M.servidor.nomes()
assert esperar(lambda: all(len(j.cena.meus_tokens()) == 1 for j in P.values()))
print("   conectados:", sorted(M.servidor.nomes()))


def token_em(j, nome):
    return next(x for x in j.cena.itens.values() if isinstance(x, TokenItem) and x.nome == nome)


print("== cada um move o seu, ao mesmo tempo")
tempos.clear(); bytes_enviados.clear()
for passo in range(1, 4):
    for i, n in enumerate(NOMES):
        P[n].cliente.mover(herois[n].uid, (-8 + i) * C, passo * C)
    QTest.qWait(120)
alvo_y = 3 * C


def todos_veem():
    for j in P.values():
        for n in NOMES:
            try:
                if abs(token_em(j, f"Herói {n}").scenePos().y() - alvo_y) > 1:
                    return False
            except StopIteration:
                return False
    return True


assert esperar(todos_veem), {n: [round(token_em(j, f"Herói {m}").scenePos().y()) for m in NOMES] for n, j in P.items()}
assert all(abs(herois[n].scenePos().y() - alvo_y) < 1 for n in NOMES)
print("   todo mundo vê os 5 no lugar novo")

print("== ninguém mexe no dos outros")
P["Ana"].cliente.mover(herois["Beto"].uid, 0, 0)
P["Ana"].cliente.mover(monstros[0].uid, 0, 0)
QTest.qWait(400)
assert abs(herois["Beto"].scenePos().y() - alvo_y) < 1 and monstros[0].scenePos() != QPointF(0, 0)

print("== o mestre ARRASTA um goblin por 2 s (o pior caso de rede)")
QTest.qWait(500)
saida_rede.clear()
t0 = time.monotonic()
k = 0
while time.monotonic() - t0 < 2.0:
    k += 1
    monstros[5].setPos(monstros[5].pos() + QPointF(3, 0))
    QTest.qWait(16)
QTest.qWait(200)
seg = time.monotonic() - t0
do_mestre = sum(b for _t, b in saida_rede if '"tipo": "estado"' in _t or '"tipo":"estado"' in _t)
total = sum(b for _t, b in saida_rede)
kbps = total * 8 / 1000 / seg
print(f"   saiu do mestre: {total / 1024:.0f} KB em {seg:.1f} s = {kbps / 1000:.2f} Mbps (pros 5)")
print("   mensagens:", sorted({t.split(",")[0] for t, _b in saida_rede})[:6])
assert kbps / 1000 < 1.5, kbps   # (v0.82: a mesa vai comprimida; sem isso eram ~3,5 Mbps aqui)

print("== o mestre move 10 goblins de uma vez")
for k in range(10):
    monstros[k].setPos(monstros[k].pos() + QPointF(0, 2 * C))
n_antes = len(tempos)
assert esperar(lambda: len(tempos) > n_antes)        # (o goblin só aparece pra quem o vê; aqui basta a mesa ir)
QTest.qWait(400)

n_env = len(tempos)
medio = sum(tempos) / max(1, n_env)
pior = max(tempos) if tempos else 0
kb = (sum(bytes_enviados) / max(1, len(bytes_enviados))) / 1024
print(f"   envios da mesa: {n_env} · médio {medio:.1f} ms · pior {pior:.1f} ms (pros 5)")
print(f"   tamanho da mesa por jogador: {kb:.1f} KB")
if pedacos:
    print("   pedaços:", sorted(((v, k) for k, v in pedacos.items()), reverse=True)[:8])
M.grab().save(os.path.join(AQUI, "saida", "cinco_mestre.png"))
P["Caio"].grab().save(os.path.join(AQUI, "saida", "cinco_jogador.png"))
assert medio < 250, medio   # (sem placa de vídeo, 6 janelas no mesmo processo; no PC de verdade é bem menos)
print("   erros:", erros[:2])
assert not erros, erros
print("FIM")
sys.stdout.flush()
os._exit(0)
