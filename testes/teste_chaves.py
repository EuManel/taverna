import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.environ["QT_QPA_PLATFORM"]="offscreen"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication, QInputDialog
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
from taverna.config import CELULA
from taverna.mesa.props import PropItem
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
M=JanelaMestre(); M.resize(1400,850); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
c=M.cena
c.criar_sala(QPointF(-4*CELULA,-3*CELULA), QPointF(4*CELULA,3*CELULA))
porta=c.colocar_porta(QPointF(4*CELULA,0)); porta.alternar(); w(50)
porta.nome_proprio="Porta armadilha"
aelar=c.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Manel"), QPointF(-3*CELULA,-2*CELULA))
M._colocar_prop("bau", QPointF(-2.5*CELULA,-1.5*CELULA)); bau=c.selectedItems()[0]
bau.gatilho={"nome":"Baú armadilha","ativo":True,"uma_vez":True,"disparado":False,"quando":"abrir",
  "acoes":[{"tipo":"porta","ids":[porta.uid],"estado":"trancar"},{"tipo":"mensagem","texto":"A porta bate e tranca!","para":"todos"}]}
QInputDialog.getText=staticmethod(lambda *a,**k: ("Chave armadilha", True))
M._criar_chave(porta)
chave=next(i for i in c.itens_do_usuario() if isinstance(i,PropItem) and i.tipo=="chave")
chave.setPos(chave.parentItem().mapFromScene(QPointF(2*CELULA, 2*CELULA)))   # o mestre esconde
porta.trancada=False; porta.alternar(); porta.mudou()   # (pro exemplo: começa aberta e destrancada)
print("porta:", porta.nome, "| chave:", porta.chave, "| item no chão:", chave.nome, chave.itens[0]["nome"])
assert M.servidor.abrir(7799)
P=JanelaPlayer(); P.resize(1100,750); P.show(); P.nome,P.ip,P.porta="Manel","127.0.0.1",7799
P._ja_entrou=False; P._primeiro_estado=True; P.cliente.conectar(P.ip,P.porta,P.nome); w(900)
avisos=[]; P.cliente.aviso_recebido.connect(avisos.append)
print("chave vaza pro player?", "Chave armadilha" in str([d for cam in M.servidor._estado_completo()[0]["camadas"] for d in cam["itens"] if d["classe"]=="porta"]))
P.cena.prop_duplo_clique(P.cena.itens[bau.uid]); w(500); P.janela_conteudo.hide()
print("abriu o baú -> porta aberta?", porta.aberta, "trancada?", porta.trancada, "|", avisos[-1].lstrip("​"))
aelar.setPos(3*CELULA, -0.5*CELULA); w(400)
P.cena.porta_duplo_clique(P.cena.itens[porta.uid]); w(400); print("sem chave:", porta.aberta, avisos[-1])
aelar.setPos(1.5*CELULA, 1.5*CELULA); w(400)
P.cena.prop_duplo_clique(P.cena.itens[chave.uid]); w(600)   # (v0.48) coletável: direto pro inventário
print("chave sumiu do chão:", not chave.isVisible(), "| inventário:", [i["nome"] for i in aelar.info["inventario"]["v"]],
      "|", avisos[-1])
assert not chave.isVisible() and "Chave armadilha" in [i["nome"] for i in aelar.info["inventario"]["v"]]
aelar.setPos(3*CELULA, -0.5*CELULA); w(400)
P.cena.porta_duplo_clique(P.cena.itens[porta.uid]); w(500)
print("com a chave:", "aberta" if porta.aberta else "fechada", "| trancada:", porta.trancada, "|", avisos[-1])
print("--- histórico:"); print("\n".join(M.painel_historico.texto.toPlainText().splitlines()[-6:]))
# baú com chave que some
M._colocar_prop("cofre", QPointF(-1*CELULA, 1*CELULA)); cofre=c.selectedItems()[0]
cofre.trancado=True; cofre.chave="chave armadilha"; cofre.gasta_chave=True
aelar.setPos(-2*CELULA, 1*CELULA); w(400)
P.cena.prop_duplo_clique(P.cena.itens[cofre.uid]); w(500)
print("cofre (chave que some, nome com minúscula):", "abriu" if P.janela_conteudo.isVisible() else "não abriu", "| inventário:", [i["nome"] for i in aelar.info["inventario"]["v"]])
pasta=tempfile.mkdtemp(); M.caminho_cena=os.path.join(pasta,"k.taverna"); M.salvar()
M2=JanelaMestre(); M2.abrir_cena(M.caminho_cena)
from taverna.mesa.portas import PortaItem
p2=next(i for i in M2.cena.itens_do_usuario() if isinstance(i,PortaItem))
print("reaberto:", p2.nome, "| chave:", p2.chave); M2.close()
print("FIM")
