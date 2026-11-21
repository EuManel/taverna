"""v0.48: o jogador edita o PRÓPRIO token (nome/cor/imagem), pega item do chão direto pro inventário,
não vê o ponto de luz (só a luz), a luvinha segue a cor do token; Atmosfera desmarca o efeito."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"; os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
app = QApplication(sys.argv); app.setStyle("Fusion")
from taverna.config import CELULA as C
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.mesa.luzes import LuzItem
w = QTest.qWait


def esperar(cond, ms=4000):
    for _ in range(ms // 50):
        if cond():
            return True
        w(50)
    return cond()


M = JanelaMestre(); M.resize(1200, 800); M.show(); M.mostrar_mesa(); w(50)
c = M.cena
c.criar_sala(QPointF(-6 * C, -4 * C), QPointF(6 * C, 4 * C))
meu = c.adicionar_token({"nome": "Aelar", "tipo": "jogador", "cor": "#3f6b4a", "tamanho": 1, "dono": "Manel"},
                        QPointF(-2 * C, 0))
outro = c.adicionar_token({"nome": "Lyra", "tipo": "jogador", "cor": "#5a3f6b", "tamanho": 1, "dono": "Bia"},
                          QPointF(2 * C, 0))
espada = c.colocar_prop("espada", QPointF(-1 * C, 0))
c.colocar_luz(QPointF(0, -2 * C))
assert M.servidor.abrir(7801)
P = JanelaPlayer(); P.resize(1000, 700); P.show(); P.nome, P.ip, P.porta = "Manel", "127.0.0.1", 7801
P._ja_entrou = False; P._primeiro_estado = True
P.cliente.conectar(P.ip, P.porta, P.nome)
assert esperar(lambda: meu.uid in P.cena.itens)

print("== o jogador edita o PRÓPRIO token (nome e cor); o dos outros, não")
P.cliente.enviar({"tipo": "editar_token", "id": meu.uid, "nome": "Aelar, o Ruivo", "cor": "#c03030"})
P.cliente.enviar({"tipo": "editar_token", "id": outro.uid, "nome": "Hackeado", "cor": "#000000"})
assert esperar(lambda: meu.nome == "Aelar, o Ruivo")
w(300)
print("meu:", meu.nome, meu.cor.name(), "| da Bia:", outro.nome, outro.cor.name())
assert meu.cor.name() == "#c03030" and outro.nome == "Lyra"
assert esperar(lambda: P.cena.itens[meu.uid].cor.name() == "#c03030")
from taverna.mesa.luva import cursor_luva
assert esperar(lambda: P.visao.cursor_padrao is cursor_luva(QColor("#c03030")))
print("luvinha do jogador na cor do token: ok")

print("== item do chão: duplo clique (de perto) → direto pro inventário")
P.cena.prop_duplo_clique(P.cena.itens[espada.uid])
assert esperar(lambda: not espada.isVisible())
inv = [i["nome"] for i in meu.info["inventario"]["v"]]
print("inventário:", inv)
assert "Espada" in inv

print("== o ponto de luz: o mestre vê o desenho, o jogador só a luz")
luz_p = next(i for i in P.cena.itens.values() if isinstance(i, LuzItem))
assert luz_p.icone_oculto
luz_m = next(i for i in c.items() if isinstance(i, LuzItem))
assert not luz_m.icone_oculto

print("== Atmosfera: clicou no efeito = arma o 'Colocar'; clicou de novo = desmarca")
pa = M.painel_atmosfera
fogo = next(b for b in pa.grupo_efeito.buttons() if b.property("chave") == "fogo")
fogo.click(); w(50)
assert fogo.isChecked() and pa.btn_colocar.isChecked() and M.cena.ferramenta == "efeito"
fogo.click(); w(50)
assert not fogo.isChecked() and not pa.btn_colocar.isChecked() and M.cena.ferramenta == "selecionar"
gelo = next(b for b in pa.grupo_efeito.buttons() if b.property("chave") == "gelo")
fogo.click(); gelo.click(); w(50)
assert gelo.isChecked() and not fogo.isChecked() and M.cena.efeito_atual["efeito"] == "gelo"
print("ok")

print("== tocha de parede no catálogo, com luz")
from taverna.mesa.props import CATALOGO
t = c.colocar_prop("tocha_parede", QPointF(0, -3.5 * C))
assert t.luz == "tocha" and CATALOGO["tocha_parede"][1] == "Luzes"
print("FIM")
