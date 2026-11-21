import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.environ["QT_QPA_PLATFORM"]="offscreen"; os.environ["TAVERNA_SEM_AUDIO"]="1"
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.graficos import graficos
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
from taverna.config import CELULA
from taverna.mesa.impactos import ImpactoItem, IMPACTOS
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
graficos().definir("alto"); graficos().definir_opcao("tremor", True); graficos().definir_opcao("clarao", True)
M=JanelaMestre(); M.resize(1400,850); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
c=M.cena; c.criar_sala(QPointF(-7*CELULA,-5*CELULA), QPointF(7*CELULA,5*CELULA))
c.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Manel"), QPointF(-5*CELULA,0))
assert M.servidor.abrir(7792)
P=JanelaPlayer(); P.resize(1280,800); P.show(); P.nome,P.ip,P.porta="Manel","127.0.0.1",7792
P._ja_entrou=False; P._primeiro_estado=True; P.cliente.conectar(P.ip,P.porta,P.nome); w(900)
M.dock_atmosfera.show(); w(100)
centro_antes=M.visao.centro_da_visao()
# arma a explosão e clica no mapa
M.painel_atmosfera.botoes_impacto["explosao"].click(); w(50)
print("ferramenta:", c.ferramenta, c.impacto_atual)
v=M.visao; QTest.mouseClick(v.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, v.mapFromScene(QPointF(0,0))); w(120)
imp=lambda cena:[i for i in cena.items() if isinstance(i, ImpactoItem)]
print("explosão no mestre:", len(imp(c)), "| no player:", len(imp(P.cena)), "| tremendo:", M.visao._tremor_timer.isActive(), P.visao._tremor_timer.isActive(), "| clarão player:", P.clima_overlay._flash>0)
w(130); M.visao.grab().save("saida/imp_explosao1.png"); w(350); M.visao.grab().save("saida/imp_explosao2.png")
w(1700); print("sumiu sozinha:", len(imp(c))==0 and len(imp(P.cena))==0, "| câmera voltou:", (M.visao.centro_da_visao()-centro_antes).manhattanLength()<1.5)
QTest.keyClick(v.viewport(), Qt.Key.Key_Escape); w(50); print("Esc:", c.ferramenta, M.painel_atmosfera.botoes_impacto["explosao"].isChecked())
for k, espera in (("raio",90),("arcano",350),("desabamento",700),("onda",250)):
    M.servidor.impacto(k, 0, 0, 3.0); w(espera); M.visao.grab().save(f"saida/imp_{k}.png"); w(int(IMPACTOS[k][2]*1000)+200)
M.painel_atmosfera.botoes_impacto["apagao"].click(); w(400); print("apagão no player:", P.clima_overlay._apagao is not None, P.clima_overlay.isVisible()); w(1700)
M.painel_atmosfera.botoes_impacto["tremor"].click(); w(100); print("tremor no player:", P.visao._tremor_timer.isActive()); w(2400)
graficos().definir_opcao("tremor", False); M.servidor.impacto("explosao",0,0,3); w(100); print("tremor desligado respeitado:", not M.visao._tremor_timer.isActive()); graficos().definir_opcao("tremor", True)
# armadilha com explosão
from taverna.jogo.gatilhos import executar, descrever_acao
g={"nome":"Runa explosiva","ativo":True,"uma_vez":True,"disparado":False,"quando":"entrar","acoes":[{"tipo":"impacto","efeito":"explosao","tam":4.5}]}
print("ação:", descrever_acao(g["acoes"][0]), "->", executar(M.servidor, g, "Manel", None, (100,100)))
w(200); print("armadilha explodiu no player:", len(imp(P.cena))>=1)
M._clima_mudou("tempestade", 3); w(600); M.visao.grab().save("saida/clima_tempestade.png")
print("FIM")
