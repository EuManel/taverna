import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.environ["QT_QPA_PLATFORM"]="offscreen"
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
from taverna.config import CELULA
from taverna.mesa.efeitos import EfeitoItem
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
M=JanelaMestre(); M.resize(1400,850); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
c=M.cena
c.criar_sala(QPointF(-6*CELULA,-4*CELULA), QPointF(6*CELULA,4*CELULA))
aelar=c.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Manel"), QPointF(-5*CELULA,0))
gob=c.adicionar_token(dict(nome="Goblin",tipo="criatura",cor="#7a3a3a",tamanho=1,imagem=None,dono=""), QPointF(4*CELULA,0))
# mestre: escuridão no meio, via o sinal da visão
M.dock_atmosfera.show()
M._efeito_pedido({"efeito":"trevas","forma":"circulo","tamanho":2,"x":0,"y":0.5*CELULA,"angulo":0})
M._clima_mudou("chuva", 2)
assert M.servidor.abrir(7798)
P=JanelaPlayer(); P.resize(1100,750); P.show(); P.nome,P.ip,P.porta="Manel","127.0.0.1",7798
P._ja_entrou=False; P._primeiro_estado=True; P.cliente.conectar(P.ip,P.porta,P.nome); w(900)
c.nevoa_ativa=True; c.mesa_mudou.emit(); w(400)
from taverna.mesa.efeitos import EfeitoItem as E
print("efeito chegou no player:", [ (e.efeito, e.forma) for e in P.cena.itens.values() if isinstance(e,E)])
print("player vê o goblin atrás da escuridão?", gob.uid in P.cena.itens)
print("clima no player:", P.clima_overlay.tipo, P.clima_overlay.isVisible())
# tira a escuridão -> vê
esc=[e for e in c.efeitos_visiveis()][0]; esc.aplicar(efeito="fogo"); w(500)
print("virou fogo -> vê o goblin?", gob.uid in P.cena.itens, "| luz de fogo no mestre:", any(l.get("id","").endswith(":luz") for l in [x if isinstance(x,dict) else {} for x in c.itens_de_luz()]))
# token em chamas
gob.definir_efeito("fogo"); w(400)
print("goblin em chamas no player:", P.cena.itens[gob.uid].efeito)
# player coloca template (cone) arrastando
P.painel_atmosfera.btn_colocar.setChecked(True)
from taverna.mesa.efeitos import EFEITOS
for b in P.painel_atmosfera.grupo_efeito.buttons():
    if b.property("chave")=="gelo": b.click()
P.painel_atmosfera.cb_forma.setCurrentIndex(P.painel_atmosfera.cb_forma.findData("cone"))
v=P.visao
a=v.mapFromScene(QPointF(-4.5*CELULA, 0.5*CELULA)); b=v.mapFromScene(QPointF(-0.5*CELULA, 0.5*CELULA))
QTest.mousePress(v.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, a)
QTest.mouseMove(v.viewport(), b); QTest.mouseRelease(v.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, b); w(500)
tpl=[e for e in c.efeitos_visiveis() if e.dono]
print("template do player no mestre:", [(e.dono, e.descricao(), round(e.angulo)) for e in tpl])
# lápis do player (fixo)
P.painel_atmosfera.ck_temp.setChecked(False)
P.painel_atmosfera.btn_lapis.setChecked(True)
pts=[QPointF(-3*CELULA,-3*CELULA),QPointF(-1*CELULA,-2*CELULA),QPointF(1*CELULA,-3*CELULA)]
QTest.mousePress(v.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, v.mapFromScene(pts[0]))
for p in pts[1:]: QTest.mouseMove(v.viewport(), v.mapFromScene(p)); w(20)
QTest.mouseRelease(v.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, v.mapFromScene(pts[-1])); w(500)
print("rabisco no mestre:", [(t["autor"], len(t["pts"]), t["temp"]) for t in c.tracos])
QTest.keyClick(v.viewport(), Qt.Key.Key_Escape); w(100)
print("Esc saiu da ferramenta:", P.cena.ferramenta, P.painel_atmosfera.btn_lapis.isChecked())
# mestre rabisco temporário
c.adicionar_traco({"id":"t1","pts":[[0,0],[100,100]],"cor":"#ffd166","esp":3,"autor":"Mestre","temp":True}); w(300)
print("player vê 2 traços:", len(P.cena.desenhos_item.tracos))
M.servidor.relampago(); w(100); print("relâmpago no player:", P.clima_overlay._flash>0)
M.ck_templates.setChecked(False); w(300); print("templates bloqueados no player:", not P.painel_atmosfera.btn_colocar.isEnabled())
P.cliente.enviar({"tipo":"apagar_efeitos"}); w(400); print("apagou os meus:", len([e for e in c.efeitos_visiveis() if e.dono]))
print("--- histórico:"); print("\n".join(M.painel_historico.texto.toPlainText().splitlines()[-3:]))
pasta=tempfile.mkdtemp(); M.caminho_cena=os.path.join(pasta,"a.taverna"); M.salvar()
M2=JanelaMestre(); M2.abrir_cena(M.caminho_cena)
print("reaberto: clima", M2.cena.clima, "| efeitos", [e.descricao() for e in M2.cena.efeitos_visiveis()], "| traços fixos", len(M2.cena.tracos),
      "| goblin", [t.efeito for t in M2.cena.itens_do_usuario() if getattr(t,"nome","")=="Goblin"])
M.grab().save("saida/shot_atm_mestre.png"); P.grab().save("saida/shot_atm_player.png")
print("FIM")
