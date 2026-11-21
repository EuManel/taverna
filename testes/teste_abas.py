import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication, QInputDialog, QMessageBox
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
from taverna.config import CELULA
from taverna.mesa.token import TokenItem
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
nomes=iter(["Floresta","Castelo"])
QInputDialog.getText=staticmethod(lambda *a, **k: (next(nomes), True))
QMessageBox.question=staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
M=JanelaMestre(); M.resize(1400,860); M.show()
c=M.cena; c.criar_camadas_padrao(); c.nome_aventura="Cromocópia"; c.nome_aba="Caverna"; M._recarregar_abas()
M.caminho_cena=os.path.abspath("abas.taverna"); M.mostrar_mesa(); w(50)
c.material_chao="rocha_caverna"; c.criar_sala(QPointF(0,0),QPointF(5*CELULA,4*CELULA))
c.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Bia"), QPointF(2*CELULA,2*CELULA))
M.nova_aba(); f=M.cena
print("abas:", [x.nome_aba for x in M.cenas], "atual:", M.cena.nome_aba, "painel camadas cena ok:", M.painel_camadas.cena is f, M.barra_construcao.cena is f)
f.material_chao="grama"; f.pincel=5; f.comecar_pincelada(QPointF(0,0)); f.continuar_pincelada(QPointF(400,100)); f.terminar_pincelada()
f.adicionar_token(dict(nome="Lobo",tipo="criatura",cor="#555555",tamanho=1,imagem=None), QPointF(200,60))
M.nova_aba(); print("abas:", [x.nome_aba for x in M.cenas])
assert M.servidor.abrir(7786)
P=JanelaPlayer(); P.resize(900,600); P.show(); P.nome,P.ip,P.porta="Bia","127.0.0.1",7786; P.cliente.conectar("127.0.0.1",7786,"Bia"); w(700)
def vejo(): return sorted(getattr(i,"nome","?") for i in P.cena.itens.values()), len(P.cena.terreno.ops)
print("ao vivo:", M.indice_ao_vivo, "player vê:", vejo())
M.trocar_aba(1); M.mostrar_aba_pros_players(1); w(400)
print("após mostrar Floresta -> player vê:", vejo(), "| abas:", [M.abas.tabText(i) for i in range(M.abas.count())])
# player token from Caverna can't be moved now (not on live) - and mestre edits Caverna without leaking
M.trocar_aba(0); M.cena.adicionar_token(dict(nome="Surpresa",tipo="criatura",cor="#900",tamanho=1,imagem=None), QPointF(64,64)); w(300)
print("mestre edita Caverna (não ao vivo) -> player vê:", vejo())
M.grab().save("abas_mestre.png"); P.grab().save("abas_player.png")
# rename, duplicate, move, delete
M.duplicar_aba(0); print("duplicou:", [x.nome_aba for x in M.cenas], "ao vivo idx", M.indice_ao_vivo, M.cenas[M.indice_ao_vivo].nome_aba)
M._aba_movida(3,0); print("moveu:", [x.nome_aba for x in M.cenas], "ao vivo:", M.cenas[M.indice_ao_vivo].nome_aba)
M.excluir_aba(M.cenas.index([x for x in M.cenas if x.nome_aba=="Floresta"][0])); w(300)
print("excluiu a ao vivo:", [x.nome_aba for x in M.cenas], "ao vivo:", M.cenas[M.indice_ao_vivo].nome_aba, "player vê:", vejo())
M.salvar(); print("salvo:", M.windowTitle())
M.abrir_cena(M.caminho_cena); w(200)
print("reaberto:", [x.nome_aba for x in M.cenas], "atual", M.cena.nome_aba, "ao vivo", M.cenas[M.indice_ao_vivo].nome_aba, "player vê:", vejo())
# old v3 file
M.abrir_cena(os.path.abspath("tinta.taverna")); w(100)
print("v3:", [x.nome_aba for x in M.cenas], len(M.cena.terreno.ops))
for x in M.cenas: x.marcar_modificada(False)
print("FIM")
