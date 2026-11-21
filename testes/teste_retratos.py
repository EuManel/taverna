import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"; os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QBuffer, QIODevice, QPointF, Qt
from PyQt6.QtGui import QColor, QImage, QPainter
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
from taverna.config import CELULA
app = QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w = QTest.qWait


def imagem_teste(cor):
    img = QImage(120, 160, QImage.Format.Format_ARGB32)
    img.fill(QColor(cor))
    p = QPainter(img); p.setBrush(QColor("#f0d0a0")); p.drawEllipse(30, 20, 60, 70); p.end()
    buf = QBuffer(); buf.open(QIODevice.OpenModeFlag.WriteOnly); img.save(buf, "PNG")
    return bytes(buf.data())


M = JanelaMestre(); M.resize(1500, 900); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
c = M.cena
aelar = c.adicionar_token(dict(nome="Aelar", tipo="jogador", cor="#3f6b4a", tamanho=1, imagem=None, dono="Manel"),
                          QPointF(-6 * CELULA, 0))
lyra = c.adicionar_token(dict(nome="Lyra", tipo="jogador", cor="#5a3f6b", tamanho=1, imagem=None, dono="Bia"),
                         QPointF(6 * CELULA, 0))
ogro = c.adicionar_token(dict(nome="Ogro", tipo="criatura", cor="#6e2a2f", tamanho=2, imagem=None), QPointF(0, 8 * CELULA))
aelar.definir_retrato(imagem_teste("#2a4a6a"))
aelar.definir_info("pv", [12, 24])                                  # oculto: só o dono (e o mestre)
aelar.definir_info("condicoes", ["envenenado", "cego"], vis="todos")
lyra.definir_info("pv", [20, 20], vis="todos")
assert M.servidor.abrir(7791)


def player(nome):
    P = JanelaPlayer(); P.resize(1300, 800); P.show()
    P.nome, P.ip, P.porta = nome, "127.0.0.1", 7791
    P._ja_entrou = False; P._primeiro_estado = True
    P.cliente.conectar(P.ip, P.porta, P.nome); return P


P1 = player("Manel"); P2 = player("Bia"); w(900)


def ret(P, nome):
    return next(r for r in P._grupo if r["nome"] == nome)


print("== GRUPO")
print("Bia recebe:", [r["nome"] for r in P2._grupo])
assert [r["nome"] for r in P2._grupo] == ["Lyra", "Aelar"] or {r["nome"] for r in P2._grupo} == {"Aelar", "Lyra"}
print("Bia vê PV de Aelar? ", ret(P2, "Aelar")["pv"], "| condições:", ret(P2, "Aelar")["cond"])
assert ret(P2, "Aelar")["pv"] is None and ret(P2, "Aelar")["cond"] == ["envenenado", "cego"]
print("Manel (dono) vê PV de Aelar:", ret(P1, "Aelar")["pv"])
assert ret(P1, "Aelar")["pv"] == [12, 24]
print("Bia vê PV de Lyra (dela):", ret(P2, "Lyra")["pv"])
assert ret(P2, "Lyra")["pv"] == [20, 20]
print("retrato chegou no Bia:", ret(P2, "Aelar")["img"] in P2.cliente.imagens)
assert ret(P2, "Aelar")["img"] in P2.cliente.imagens
print("retratos na tela: mestre", len(M.painel_grupo.cartoes), "| Bia", len(P2.painel_grupo.cartoes),
      "| visíveis:", M.painel_grupo.isVisible(), P2.painel_grupo.isVisible())
assert len(P2.painel_grupo.cartoes) == 2

print("== NÉVOA: companheiro fora da visão continua no grupo")
c.definir_nevoa(True); c.definir_ambiente("escuro"); M.servidor.enviar_estado() if hasattr(M.servidor, "enviar_estado") else None
w(700)
from taverna.mesa.token import TokenItem
ve_aelar = any(isinstance(i, TokenItem) and i.nome == "Aelar" for i in P2.cena.itens.values())
print("Bia vê o token de Aelar na mesa?", ve_aelar, "| Aelar no grupo dela?", any(r["nome"] == "Aelar" for r in P2._grupo))
assert any(r["nome"] == "Aelar" for r in P2._grupo)

print("== COMBATE: retratos na ordem")
c.clearSelection()
for t in (aelar, lyra, ogro):
    t.setSelected(True)
M.painel_combate.iniciar("selecionados"); w(600)
nomes_p2 = [k.dados.get("nome") for k in P2.faixa_turnos.cartoes]
nomes_m = [k.dados.get("nome") for k in M.faixa_turnos.cartoes]
print("faixa mestre:", nomes_m, "| faixa Bia:", nomes_p2)
assert len(nomes_m) == 3 and "Ogro" in nomes_m
assert "Aelar" in nomes_p2 and "???" in nomes_p2   # companheiro sempre aparece; o ogro no escuro não

print("== ESTADO: caído aparece no retrato")
aelar.definir_estado("caido"); w(600)
print("Aelar caído no retrato da Bia:", ret(P2, "Aelar")["estado"])
assert ret(P2, "Aelar")["estado"] == "caido"

print("== DESLIGAR os retratos (preferência)")
P2._alternar_retratos(False); print("escondeu:", not P2.painel_grupo.isVisible()); P2._alternar_retratos(True)

c.definir_ambiente("dia"); w(500)
M.grab().save("saida/shot_retratos_mestre.png")
P2.grab().save("saida/shot_retratos_bia.png")
M.servidor.fechar() if hasattr(M.servidor, "fechar") else None
print("FIM")
