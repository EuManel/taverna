import sys, os, tempfile, wave, struct, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.environ["QT_QPA_PLATFORM"]="offscreen"; os.environ["TAVERNA_SEM_AUDIO"]="1"
from PyQt6.QtCore import QPointF, QSettings
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
QSettings("Taverna","Mestre").remove("sons")
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
from taverna.config import CELULA
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
pasta=tempfile.mkdtemp()
def wav(nome, seg=0.4):
    c=os.path.join(pasta,nome)
    with wave.open(c,"wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(22050)
        f.writeframes(b"".join(struct.pack("<h", int(8000*math.sin(i*0.1))) for i in range(int(22050*seg))))
    return c
porta_rangendo=wav("porta_rangendo.wav"); chuva=wav("chuva-forte.wav", 1.0)
M=JanelaMestre(); M.resize(1400,850); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
M.cena.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Manel"), QPointF(0,0))
ps=M.painel_som
ps.biblioteca.adicionar([porta_rangendo, chuva]); ps.recarregar_sons()
print("lista:", [ps.lista_sons.item(i).text() for i in range(ps.lista_sons.count())])
assert M.servidor.abrir(7797)
P=JanelaPlayer(); P.resize(1100,750); P.show(); P.nome,P.ip,P.porta="Manel","127.0.0.1",7797
P._ja_entrou=False; P._primeiro_estado=True; P.cliente.conectar(P.ip,P.porta,P.nome); w(900)
tocados=[]; orig=P.tocador.tocar
P.tocador.tocar=lambda sid,vol=0.8,amb=False: (tocados.append((sid,round(vol,2),amb)), orig(sid,vol,amb))[1]
ps.lista_sons.setCurrentRow(0); ps.btn_todos.click(); w(500)
print("player recebeu e tocou:", tocados, "| arquivo no cache:", os.path.isfile(P.tocador.arquivos.get(tocados[0][0],"")) if tocados else None)
ps.lista_sons.setCurrentRow(1); ps.ck_ambiente.setChecked(True); ps.btn_todos.click(); w(500)
print("ambiente:", tocados[-1], "| servidor guarda:", list(M.servidor.ambientes))
# alguém entra depois: recebe o ambiente
P2=JanelaPlayer(); P2.nome,P2.ip,P2.porta="Bia","127.0.0.1",7797
P2._ja_entrou=False; P2._primeiro_estado=True
t2=[]; o2=P2.tocador.tocar; P2.tocador.tocar=lambda sid,vol=0.8,amb=False:(t2.append((sid,amb)),o2(sid,vol,amb))[1]
P2.cliente.conectar(P2.ip,P2.porta,P2.nome); w(900)
print("quem entrou depois ouviu o ambiente:", t2)
paradas=[]; op=P.tocador.parar; P.tocador.parar=lambda sid=None:(paradas.append(sid),op(sid))[1]
ps.btn_parar_sons.click(); w(400); print("parar tudo chegou:", paradas)
# música
ps.ed_link.setText("https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=xyz"); ps._adicionar_link()
ps.ed_link.setText("https://youtu.be/abcdefghijk"); ps._adicionar_link()
ps.ed_link.setText("isso não é link"); ps._adicionar_link()
print("fila:", [f["id"] for f in ps.fila])
ps.btn_play.click(); w(500); P.grab().save("saida/shot_mini.png")
print("player música:", P.seguidor_musica.atual, P.seguidor_musica.tocando, "| mini player visível:", P.mini_player.isVisible(), "|", P.lbl_musica.text())
ps.btn_play.click(); w(400); print("pausou:", P.seguidor_musica.tocando, P.lbl_musica.text())
ps.btn_prox.click(); w(400); print("próxima:", P.seguidor_musica.atual)
ps.btn_parar.click(); w(400); print("parou:", P.seguidor_musica.atual, P.lbl_musica.text())
M.abas_atmosfera.setCurrentIndex(1); M.dock_atmosfera.show(); w(200)
M.grab().save("saida/shot_som_mestre.png"); P.grab().save("saida/shot_som_player.png")
print("FIM")
