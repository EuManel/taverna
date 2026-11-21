import sys, os, tempfile, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.environ["QT_QPA_PLATFORM"]="offscreen"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
from taverna.config import CELULA
from taverna.mesa.token import TokenItem
from taverna.mesa.props import PropItem
from taverna.mesa.portas import PortaItem
from taverna.mesa.luzes import LuzItem
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
M=JanelaMestre(); M.resize(1500,880); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
c=M.cena
c.criar_sala(QPointF(-5*CELULA,-4*CELULA), QPointF(6*CELULA,4*CELULA))
porta=c.colocar_porta(QPointF(6*CELULA, 0)) or next(i for i in c.itens_do_usuario() if isinstance(i,PortaItem))
porta.alternar(); w(50)   # porta aberta
luz=c.colocar_luz(QPointF(0,0))
aelar=c.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Manel"), QPointF(-4*CELULA,-3*CELULA))
aelar.definir_info("pv",[20,20])
gob=c.adicionar_token(dict(nome="Goblin",tipo="criatura",cor="#6e2a2f",tamanho=1,imagem=None), QPointF(4*CELULA,2*CELULA))
c.definir_item_visivel(gob, False)
# baú com armadilha
M._colocar_prop("bau", QPointF(-2.5*CELULA,-2.5*CELULA)); bau=c.selectedItems()[0]
bau.itens=[{"id":"b1","nome":"Bilhete amassado","qtd":1,"desc":"","img":None,"doc":{"texto":"# Aviso\nNão confie no **taverneiro**.","img":None}}]
bau.gatilho={"nome":"Agulha envenenada","ativo":True,"uma_vez":True,"disparado":False,"quando":"abrir",
             "acoes":[{"tipo":"mensagem","texto":"Uma agulha espeta seu dedo!","para":"quem"},
                      {"tipo":"dano","expr":"1d4+1","condicao":"envenenado","rodadas":3},
                      {"tipo":"revelar","ids":[gob.uid]}]}
# área no chão
area=c.criar_area_gatilho(QPointF(1*CELULA,-2*CELULA))
area.gatilho.update(nome="Placa de pressão", acoes=[{"tipo":"porta","ids":[porta.uid],"estado":"fechar"},
     {"tipo":"luz","ids":"todas","estado":"apagar"},{"tipo":"ambiente","valor":"escuro"},
     {"tipo":"mensagem","texto":"CLIQUE. A porta bate atrás de vocês e tudo escurece!","para":"todos"}])
# pergaminho solto
M._colocar_prop("pergaminho", QPointF(-4*CELULA, 2*CELULA)); perg=c.selectedItems()[0]
perg.itens[0]["doc"]["texto"]="O tesouro está **sob a estátua**."
assert M.servidor.abrir(7795)
P=JanelaPlayer(); P.resize(1200,800); P.show(); P.nome,P.ip,P.porta="Manel","127.0.0.1",7795
P._ja_entrou=False; P._primeiro_estado=True; P.cliente.conectar(P.ip,P.porta,P.nome); w(900)
avisos=[]; P.cliente.aviso_recebido.connect(avisos.append)
estado=M.servidor._estado_completo()[0]
txt=json.dumps(estado)
print("vazou armadilha pro player?", "Agulha" in txt or "Placa de press" in txt or "gatilho" in txt)
def prop_p(n): return next(i for i in P.cena.itens.values() if isinstance(i,PropItem) and i.nome==n)
print("player vê goblin?", any(isinstance(i,TokenItem) and i.nome=="Goblin" for i in P.cena.itens.values()))

print("== BAÚ COM ARMADILHA")
P.cena.prop_duplo_clique(prop_p("Baú")); w(500)
print("mensagem:", [a.lstrip("​") for a in avisos][-1:], "| PV:", aelar.info["pv"]["v"], "| cond:", aelar.info["condicoes"]["v"], aelar.info["condicoes"].get("dur"))
print("goblin apareceu:", gob.isVisible(), "| player vê goblin:", any(isinstance(i,TokenItem) and i.nome=="Goblin" for i in P.cena.itens.values()))
print("janela do baú:", P.janela_conteudo.isVisible(), "| armadilha gasta:", bau.gatilho["disparado"])
P.janela_conteudo._ler(bau.itens[0], False); w(100); P.janela_conteudo._leitura.grab().save("leitura_bilhete.png"); P.janela_conteudo._leitura.close()
P.janela_conteudo.hide()
P.cena.prop_duplo_clique(prop_p("Baú")); w(400); print("abriu de novo, PV:", aelar.info["pv"]["v"], "(não disparou de novo)")
P.janela_conteudo.hide()

print("== PERGAMINHO NO CHÃO")
aelar.setPos(-4*CELULA, 1*CELULA); w(400)
P.cena.prop_duplo_clique(prop_p("Pergaminho")); w(400)
leit=P.janela_conteudo._leitura
print("abriu direto pra ler:", leit.isVisible(), "| janela de lista:", P.janela_conteudo.isVisible())
leit.grab().save("leitura_pergaminho.png")
leit.pegar.emit(); w(500)
print("pergaminho sumiu do chão:", not perg.isVisible(), "| inventário:", [i["nome"] for i in aelar.info["inventario"]["v"]])

print("== ÁREA NO CHÃO")
P.cliente.mover(aelar.uid, 1*CELULA, -2*CELULA); w(900)
print("porta aberta?", porta.aberta, "| luz acesa?", luz.acesa, "| ambiente:", c.luz_ambiente, "| msg:", avisos[-1].lstrip("​"))
print("--- HISTÓRICO ---"); print("\n".join(l for l in M.painel_historico.texto.toPlainText().splitlines() if "⚡" in l or "📦" in l or "🎒" in l))

print("== SALVAR/ABRIR")
pasta=tempfile.mkdtemp(); M.caminho_cena=os.path.join(pasta,"a.taverna"); M.salvar()
M2=JanelaMestre(); M2.abrir_cena(M.caminho_cena)
from taverna.mesa.gatilho_area import AreaGatilhoItem
areas=[i for i in M2.cena.itens_do_usuario() if isinstance(i,AreaGatilhoItem)]
b2=next(i for i in M2.cena.itens_do_usuario() if isinstance(i,PropItem) and i.nome=="Baú")
print("reaberto: áreas", len(areas), areas[0].nome, "| baú gatilho:", b2.gatilho["nome"], "disparado:", b2.gatilho["disparado"])
M2.close()
c.definir_ambiente("dia"); M.visao.centerOn(QPointF(0,0)); c.clearSelection(); w(200); M.grab().save("armadilha_mestre.png")
print("FIM")
