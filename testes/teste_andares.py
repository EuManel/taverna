"""v0.46: andares — cada jogador vê só o andar do token dele; escada leva o token pro outro andar."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.config import CELULA as C
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
from taverna.mesa.token import TokenItem
from taverna.mesa.props import PropItem
app = QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w = QTest.qWait


def esperar(cond, ms=5000):
    for _ in range(ms // 50):
        if cond():
            return True
        w(50)
    return cond()


M = JanelaMestre(); M.resize(1300, 850); M.show(); M.mostrar_mesa(); w(50)
terreo = M.cena
terreo.criar_sala(QPointF(-8 * C, -5 * C), QPointF(8 * C, 5 * C))
aelar = terreo.adicionar_token({"nome": "Aelar", "tipo": "jogador", "cor": "#3f6b4a", "tamanho": 1, "dono": "Manel"},
                               QPointF(-4 * C, 0))
lyra = terreo.adicionar_token({"nome": "Lyra", "tipo": "jogador", "cor": "#5a3f6b", "tamanho": 1, "dono": "Bia"},
                              QPointF(-2 * C, 0))
escada = terreo.colocar_prop("escada", QPointF(4 * C, 0))

print("== o mestre cria o 1º andar e liga a escada")
M.ligar_escada(escada, +1)          # cria o andar de cima (não existia) e a escada de lá
assert escada.ligacao and escada.ligacao["andar"] == 1
primeiro = next(c for c in M.cenas if c is not terreo)
assert primeiro.predio == terreo.predio and primeiro.andar == 1
outra = primeiro.item_por_id(escada.ligacao["id"])
assert isinstance(outra, PropItem) and outra.ligacao["id"] == escada.uid
print("== (v0.46.2) o andar novo clona SÓ paredes e chão; a escada não é baú")
n_par, n_chao = len(terreo.paredes.para_lista()), len(terreo.terreno.para_lista())
print("paredes:", n_par, "->", len(primeiro.paredes.para_lista()), "| chão:", n_chao, "->", len(primeiro.terreno.para_lista()))
assert n_par > 0 and len(primeiro.paredes.para_lista()) == n_par
assert len(primeiro.terreno.para_lista()) == n_chao
assert not any(isinstance(t, TokenItem) for t in primeiro.itens_do_usuario())   # tokens não vêm
assert not escada.interativo and not outra.interativo and escada.itens == []
primeiro.criar_sala(QPointF(-8 * C, -5 * C), QPointF(8 * C, 5 * C))
primeiro.colocar_prop("barril", QPointF(-5 * C, 3 * C))
M.trocar_aba(M.cenas.index(terreo))
print("abas:", [M.abas.tabText(i) for i in range(M.abas.count())])
assert M.servidor.e_ao_vivo(terreo) and M.servidor.e_ao_vivo(primeiro)   # o prédio inteiro ao vivo

assert M.servidor.abrir(7793)
P1 = JanelaPlayer(); P1.show(); P1.nome, P1.ip, P1.porta = "Manel", "127.0.0.1", 7793
P2 = JanelaPlayer(); P2.show(); P2.nome, P2.ip, P2.porta = "Bia", "127.0.0.1", 7793
for P in (P1, P2):
    P._ja_entrou = False; P._primeiro_estado = True
    P.cliente.conectar(P.ip, P.porta, P.nome)
assert esperar(lambda: len(M.servidor.nomes()) == 2)


def nomes(P):
    return sorted(i.nome for i in P.cena.itens.values() if isinstance(i, TokenItem))


def tipos_props(P):
    return sorted(i.tipo for i in P.cena.itens.values() if isinstance(i, PropItem))


assert esperar(lambda: "Aelar" in nomes(P1) and "Lyra" in nomes(P2))
print("P1 vê:", nomes(P1), getattr(P1.cena, "andar_atual", ""), "| P2 vê:", nomes(P2), getattr(P2.cena, "andar_atual", ""))
assert P1.cena.andar_atual == "Térreo" and P2.cena.andar_atual == "Térreo"

print("== o mestre leva a Lyra pro 1º andar: a Bia passa a ver só o 1º andar")
M.levar_token_pro_andar(lyra, primeiro)
assert esperar(lambda: P2.cena.andar_atual == "1º andar")
w(300)
print("P1 vê:", nomes(P1), tipos_props(P1), "| P2 vê:", nomes(P2), tipos_props(P2))
assert "Lyra" not in nomes(P1) and "Aelar" not in nomes(P2)
assert "barril" in tipos_props(P2) and "barril" not in tipos_props(P1)   # cada um vê o próprio andar

print("== o Manel sobe a escada (duplo clique perto dela)")
aelar = next(t for t in terreo.itens_do_usuario() if isinstance(t, TokenItem) and t.nome == "Aelar")
aelar.setPos(aelar.pos() + QPointF(7.5 * C, 0))   # chega perto da escada
w(200)
print("== escada bloqueada pelo mestre: não sobe")
M.liberar_escada(escada, False)
assert escada.trancado and outra.trancado   # vale pras duas pontas
P1.cliente.enviar({"tipo": "interagir", "id": escada.uid})
w(800)
assert P1.cena.andar_atual == "Térreo"
M.liberar_escada(escada, True)
P1.cliente.enviar({"tipo": "interagir", "id": escada.uid})
assert esperar(lambda: P1.cena.andar_atual == "1º andar")
w(300)
print("P1 vê:", nomes(P1), "| no térreo sobrou:", [t.nome for t in terreo.itens_do_usuario() if isinstance(t, TokenItem)])
assert sorted(nomes(P1)) == ["Aelar", "Lyra"]
assert not any(isinstance(t, TokenItem) for t in terreo.itens_do_usuario())
aelar2 = next(t for t in primeiro.itens_do_usuario() if isinstance(t, TokenItem) and t.nome == "Aelar")
d_esc = (aelar2.centro_cena() - outra.centro_cena())
assert (d_esc.x() ** 2 + d_esc.y() ** 2) ** 0.5 < 2 * C   # chegou na escada de cima

print("== (v0.48) escada ligada a OUTRO cenário (aba que já existia), pela janela da escada")
M._nova_aba = getattr(M, "_nova_aba", None)
porao = M._nova_cena_vazia("Porão")
M._registrar_cena(porao)
M.cenas.append(porao)
solta = porao.colocar_prop("escada", QPointF(2 * C, 2 * C))   # o mestre já tinha posto uma escada lá
esc2 = terreo.colocar_prop("escada", QPointF(-6 * C, -3 * C))
from taverna.ui.dialogo_prop import DialogoProp
dlg = DialogoProp(esc2, M)
rotulos = [dlg.cb_leva.itemText(i) for i in range(dlg.cb_leva.count())]
print("leva para:", rotulos)
assert any("Porão" in r for r in rotulos)
dlg.cb_leva.setCurrentIndex(next(i for i, r in enumerate(rotulos) if "Porão" in r))
dlg._ok()
assert esc2.ligacao and esc2.ligacao["id"] == solta.uid and solta.ligacao["id"] == esc2.uid   # usou a solta
assert porao.predio == terreo.predio and porao.andar not in (0, 1)
assert M.servidor.e_ao_vivo(porao)   # entrou no prédio que está no ar
M.desligar_escada(esc2)
assert esc2.ligacao is None and solta.ligacao is None

print("== salvar e abrir: o prédio volta igual")
from taverna.mesa.arquivo import dados_da_cena
d1, d2 = dados_da_cena(terreo), dados_da_cena(primeiro)
assert d1["predio"] == d2["predio"] and (d1["andar"], d2["andar"]) == (0, 1)
esc_d = next(i for c in d1["camadas"] for i in c.get("itens", []) if i.get("tipo") == "escada")
assert esc_d.get("ligacao", {}).get("andar") == 1
print("FIM")
