import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.environ["QT_QPA_PLATFORM"]="offscreen"
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
from taverna.config import CELULA
from taverna.mesa.token import TokenItem
from taverna.mesa.props import PropItem
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
M=JanelaMestre(); M.resize(1500,880); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
c=M.cena
print("camadas:", [cam.tipo for cam in c.camadas])
c.criar_sala(QPointF(-5*CELULA,-4*CELULA), QPointF(7*CELULA,5*CELULA))
aelar=c.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Manel"), QPointF(-4*CELULA,-3*CELULA))
M._colocar_prop("bau", QPointF(4.5*CELULA, 3.5*CELULA)); bau=c.selectedItems()[0]
bau.itens=[{"id":"x1","nome":"Espada Lendária","qtd":1,"desc":"Brilha com luz azulada.","img":None},
           {"id":"x2","nome":"Moedas de ouro","qtd":50,"desc":"","img":None}]
M._colocar_prop("pilar", QPointF(0.5*CELULA, 0.5*CELULA)); pilar=c.selectedItems()[0]
M._colocar_prop("lareira", QPointF(-2*CELULA, -3.5*CELULA))
M._colocar_prop("mesa", QPointF(2*CELULA, -2*CELULA))
M._colocar_prop("cama_casal", QPointF(5*CELULA, -2.5*CELULA))
M._colocar_prop("tapete", QPointF(-2*CELULA, 2*CELULA))
print("obstáculos (paredes + pilar):", len(c.obstaculos_visiveis()))
print("luzes extras:", [d.get("tipo") if isinstance(d, dict) else type(d).__name__ for d in c.itens_de_luz()])
aelar.luz="tocha"; c.marcar_modificada()
print("com tocha:", [d.get("tipo") if isinstance(d, dict) else "?" for d in c.itens_de_luz()])
assert M.servidor.abrir(7789)
P=JanelaPlayer(); P.resize(1200,800); P.show(); P.nome,P.ip,P.porta="Manel","127.0.0.1",7789
P._ja_entrou=False; P._primeiro_estado=True; P.cliente.conectar(P.ip,P.porta,P.nome); w(900)
props_p=[i for i in P.cena.itens.values() if isinstance(i,PropItem)]
print("player vê props:", sorted(p.nome for p in props_p), "| conteúdo vazou?", any(p.itens for p in props_p))
bau_p=next(p for p in props_p if p.nome=="Baú")
avisos=[]; P.cliente.aviso_recebido.connect(avisos.append)
P.cena.prop_duplo_clique(bau_p); w(400)
print("longe:", avisos[-1] if avisos else None, "| janela aberta?", P.janela_conteudo.isVisible())
aelar.setPos(3*CELULA, 3*CELULA); w(400)
P.cena.prop_duplo_clique(bau_p); w(400)
print("perto -> janela:", P.janela_conteudo.isVisible(), P.janela_conteudo.titulo.text())
P.janela_conteudo.grab().save("props_janela.png")
P.janela_conteudo.pegar.emit(bau.uid, "x1"); w(500)
print("baú agora:", [i["nome"] for i in bau.itens], "| inventário:", [i["nome"] for i in aelar.info["inventario"]["v"]])
print("player vê inventário dele:", [i["nome"] for i in P.cena.meus_tokens()[0].info["inventario"]["v"]])
bau.trancado=True; P.cena.prop_duplo_clique(bau_p); w(400); print("trancado:", avisos[-1])
bau.trancado=False
P.janela_conteudo.hide(); M.servidor.mostrar_conteudo(bau, None, False); w(400)
print("mestre mostrou:", P.janela_conteudo.isVisible(), P.janela_conteudo.subtitulo.text())
print("--- HISTÓRICO ---"); print(M.painel_historico.texto.toPlainText())
# salvar/abrir
pasta=tempfile.mkdtemp(); M.caminho_cena=os.path.join(pasta,"props.taverna"); M.salvar()
M2=JanelaMestre(); M2.abrir_cena(M.caminho_cena)
props2=[i for i in M2.cena.itens_do_usuario() if isinstance(i,PropItem)]
b2=next(p for p in props2 if p.nome=="Baú")
print("reaberto:", len(props2), "props | baú itens:", [i["nome"] for i in b2.itens], "| tocha:", next(t for t in M2.cena.itens_do_usuario() if isinstance(t,TokenItem)).luz)
M2.close()
# telas
c.definir_ambiente("penumbra") if hasattr(c,"definir_ambiente") else None
M.dock_objetos.show(); c.clearSelection(); bau.setSelected(True); w(200)
M.visao.centerOn(QPointF(CELULA,0)); w(100); M.grab().save("props_mestre.png")
P.janela_conteudo.hide(); P.visao.centerOn(QPointF(CELULA,0)); w(300); P.grab().save("props_player.png")
print("FIM")
