import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.environ["QT_QPA_PLATFORM"]="offscreen"; os.environ["TAVERNA_SEM_AUDIO"]="1"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.ui.tema import QSS
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
from taverna.jogo import tabelas as T
from taverna.jogo.sorteio import sortear, config_padrao
for t in T.listar(): T.apagar(t["nome"])
lista="""Pistola
Revólver [incomum]
Fuzil de assalto [raro]
• Munição ×2d10
Kit médico | Recupera 2d8 PV
Granada ×2 [incomum]
Componente ritualístico [muito rara]
"""
linhas=T.ler_texto(lista); print("lido:", [(l["nome"], l["qtd"], l["chance"], l["desc"]) for l in linhas])
print("de volta pra texto:\n" + T.para_texto(linhas))
tab={"nome":"Ordem Paranormal — Armas","moeda":"R$","moeda_dados":"3d6*10".replace("*10","")+"0" if False else "2d6+10","linhas":linhas}
T.salvar(tab); print("arquivos:", os.listdir(T.pasta_tabelas()))
cfg=dict(config_padrao(), vazio=0, itens_min=2, itens_max=3, tabela=T.listar()[0])
r=random.Random(5)
for _ in range(4): print("  sorteio:", sortear(cfg, r)[1])
from collections import Counter
c=Counter()
for _ in range(3000):
    for it in sortear(dict(cfg, itens_min=1, itens_max=1), r)[0]:
        if it["nome"]!="R$": c[it["nome"]]+=1
print("frequência (comum > raro):", c.most_common())
# diálogo de tabelas
from taverna.ui.dialogo_tabelas import DialogoTabelas
d=DialogoTabelas(None, "Ordem Paranormal — Armas"); d.show(); w(200)
d._testar(); print("teste no gerenciador:", d.resultado.text()[:120])
d.grab().save("saida/shot_tabelas.png"); d.accept()
# baú usando a tabela
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.dialogo_prop import DialogoProp
from taverna.config import CELULA
M=JanelaMestre(); M.resize(1400,850); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
M.cena.adicionar_token(dict(nome="Agente",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Manel"), QPointF(0,0))
M._colocar_prop("bau", QPointF(1.5*CELULA, 0.5*CELULA)); bau=M.cena.selectedItems()[0]
dp=DialogoProp(bau, M); dp.caixa_sorteio.setChecked(True); dp.s_vazio.setValue(0); dp.s_min.setValue(2); dp.s_max.setValue(2)
dp.s_tabela.setCurrentIndex(dp.s_tabela.findData("Ordem Paranormal — Armas"))
print("D&D escondido com tabela:", not dp.s_raridade.isVisible() if dp.isVisible() else dp.s_raridade.isHidden())
dp.show(); w(150); dp.grab().save("saida/shot_bau_tabela.png"); dp._ok()
print("baú guardou cópia da tabela:", bau.sorteio["tabela"]["nome"], len(bau.sorteio["tabela"]["linhas"]), "itens")
assert M.servidor.abrir(7794)
P=JanelaPlayer(); P.resize(1100,750); P.show(); P.nome,P.ip,P.porta="Manel","127.0.0.1",7794
P._ja_entrou=False; P._primeiro_estado=True; P.cliente.conectar(P.ip,P.porta,P.nome); w(900)
P.cena.prop_duplo_clique(P.cena.itens[bau.uid]); w(500)
print("jogador abriu:", [(i["nome"], i["qtd"]) for i in bau.itens])
for t in T.listar(): T.apagar(t["nome"])
print("FIM")
