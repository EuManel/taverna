import sys, os, tempfile, wave, struct, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.environ["QT_QPA_PLATFORM"]="offscreen"; os.environ["TAVERNA_SEM_AUDIO"]="1"
from PyQt6.QtCore import QPointF, QSettings
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
QSettings("Taverna","Mestre").remove("sons"); QSettings("Taverna","Mestre").remove("sons_impactos")
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.sons_efeitos import DialogoSonsEfeitos, sons_dos_efeitos
from taverna.ui.tema import QSS
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
pasta=tempfile.mkdtemp()
def wav(nome):
    c=os.path.join(pasta,nome)
    with wave.open(c,"wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(22050)
        f.writeframes(b"".join(struct.pack("<h", int(8000*math.sin(i*0.1))) for i in range(6000)))
    return c
boom=wav("explosao_grande.wav"); trovao=wav("trovao.wav")
M=JanelaMestre(); M.resize(1400,850); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
M.painel_som.biblioteca.adicionar([boom, trovao])
d=DialogoSonsEfeitos(M)
cb,vol=d.linhas["explosao"]; print("opções:", [cb.itemText(i) for i in range(cb.count())])
cb.setCurrentIndex(cb.findData(boom)); vol.setValue(60)
cb2,_=d.linhas["raio"]; cb2.setCurrentIndex(cb2.findData(trovao))
d.show(); w(100); d.grab().save("saida/shot_sons_efeitos.png"); d._ok()
print("salvo:", {k:(os.path.basename(v["caminho"]), v["vol"]) for k,v in sons_dos_efeitos().items()})
assert M.servidor.abrir(7791)
P=JanelaPlayer(); P.resize(1280,800); P.show(); P.nome,P.ip,P.porta="Manel","127.0.0.1",7791
P._ja_entrou=False; P._primeiro_estado=True; P.cliente.conectar(P.ip,P.porta,P.nome); w(900)
tocados=[]; o=P.tocador.tocar; P.tocador.tocar=lambda sid,vol=0.8,amb=False:(tocados.append((M.servidor.sons[sid][0], round(vol,2))), o(sid,vol,amb))[1]
M.servidor.impacto("explosao", 0, 0, 3); w(400); print("explosão ->", tocados)
M.servidor.impacto("raio", 0, 0, 3); w(400); print("raio ->", tocados[-1])
n=len(tocados); M.servidor.impacto("onda", 0, 0, 3); w(300); print("onda (sem som) não toca nada:", len(tocados)==n)
from taverna.jogo.gatilhos import executar
executar(M.servidor, {"acoes":[{"tipo":"impacto","efeito":"explosao","tam":3}]}, "Manel", None, (0,0)); w(400)
print("armadilha com explosão também toca:", len(tocados)==n+1)
print("FIM")
