import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.environ["QT_QPA_PLATFORM"]="offscreen"; os.environ["TAVERNA_SEM_AUDIO"]="1"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.dialogo_prop import DialogoProp
from taverna.ui.tema import QSS
from taverna.config import CELULA
from taverna.jogo.sorteio import sortear, config_padrao, itens_proprios
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
print("lista própria:", itens_proprios("Amuleto do culto\nFlecha de prata ×5\nCarta do barão | Selada com cera\n\n"))
cfg=dict(config_padrao(), vazio=0, moedas="personalizado", moedas_dados={"PO":"2d6","PC":"","PP":"3","PL":""},
         itens_min=3, itens_max=3, tipos={"proprios":True}, proprios="Amuleto do culto\nFlecha de prata ×5")
print("personalizado:", sortear(cfg, random.Random(1))[1])
print("100% vazio:", sortear(dict(config_padrao(), vazio=100))[1])
M=JanelaMestre(); M.resize(1400,850); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
aelar=M.cena.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Manel"), QPointF(0,0))
M._colocar_prop("bau", QPointF(1.5*CELULA, 0.5*CELULA)); bau=M.cena.selectedItems()[0]
d=DialogoProp(bau, M); d.caixa_sorteio.setChecked(True); d.s_min.setValue(2); d.s_max.setValue(3)
d.s_moedas.setCurrentIndex(d.s_moedas.findData("medias")); d.s_vazio.setValue(0)
d.s_tipos["magicos"].setChecked(True); d.s_raridade.setCurrentIndex(d.s_raridade.findData("rara"))
d._testar_sorteio(); print("teste no diálogo:", d.s_status.text())
d.show(); w(200); d.grab().save("saida/shot_sorteio_dialogo.png"); d._ok()
print("config salva no baú:", {k: bau.sorteio[k] for k in ("vazio","moedas","itens_min","itens_max","raridade_max")}, "| itens antes:", bau.itens)
assert M.servidor.abrir(7795)
P=JanelaPlayer(); P.resize(1100,750); P.show(); P.nome,P.ip,P.porta="Manel","127.0.0.1",7795
P._ja_entrou=False; P._primeiro_estado=True; P.cliente.conectar(P.ip,P.porta,P.nome); w(900)
for _ in range(100):   # (espera o baú chegar no jogador: com o PC carregado 0,9 s às vezes não bastava)
    if bau.uid in P.cena.itens: break
    w(50)
P.cena.prop_duplo_clique(P.cena.itens[bau.uid]); w(500)
print("jogador abriu e viu:", [ (i["nome"], i["qtd"]) for i in P.janela_conteudo._itens] if hasattr(P.janela_conteudo,"_itens") else P.janela_conteudo.isVisible())
print("baú agora:", [i["nome"] for i in bau.itens], "| sorteado:", bau.sorteio["sorteado"])
antes=[i["nome"] for i in bau.itens]
P.janela_conteudo.hide(); P.cena.prop_duplo_clique(P.cena.itens[bau.uid]); w(400)
print("segunda abertura não sorteia de novo:", [i["nome"] for i in bau.itens]==antes)
print("histórico:", [l for l in M.painel_historico.texto.toPlainText().splitlines() if "🎲" in l])
M.grab().save("saida/shot_sorteio_mestre.png")
print("FIM")
