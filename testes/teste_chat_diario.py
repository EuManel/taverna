import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.environ["QT_QPA_PLATFORM"]="offscreen"; os.environ["TAVERNA_SEM_AUDIO"]="1"
from PyQt6.QtCore import QPointF, QSettings
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
QSettings("Taverna","Player").remove("rolagens_prontas")
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
M=JanelaMestre(); M.resize(1400,850); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
for n,d,x in (("Aelar","Manel",0),("Bruna","Bia",100),("Caio","Cadu",200)):
    M.cena.adicionar_token(dict(nome=n,tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono=d), QPointF(x,0))
M.cena.adicionar_token(dict(nome="Duquesa Velmora",tipo="npc",cor="#5a3a6a",tamanho=1,imagem=None,dono=""), QPointF(300,0))
assert M.servidor.abrir(7793)
def entrar(nome):
    P=JanelaPlayer(); P.resize(1280,800); P.show(); P.nome,P.ip,P.porta=nome,"127.0.0.1",7793
    P._ja_entrou=False; P._primeiro_estado=True; P.cliente.conectar(P.ip,P.porta,P.nome); return P
P=entrar("Manel"); B=entrar("Bia"); w(1000)
def txt(x): return x.painel_chat.log.toPlainText()
P.painel_chat.campo.setText("Alguém viu a porta trancada?"); P.painel_chat._enviar(); w(300)
print("Bia viu msg pública:", "porta trancada" in txt(B), "| mestre viu:", "porta trancada" in txt(M))
# sussurro Manel -> Bia
i=P.painel_chat.para.findData("Bia"); print("Manel pode sussurrar pra:", [P.painel_chat.para.itemText(k) for k in range(P.painel_chat.para.count())])
P.painel_chat.para.setCurrentIndex(i); P.painel_chat.campo.setText("Acho que o mordomo mente"); P.painel_chat._enviar(); w(300)
C=entrar("Cadu"); w(900)
print("sussurro: Bia vê", "mordomo" in txt(B), "| mestre vê", "mordomo" in txt(M), "| Cadu (entrou depois) NÃO vê:", "mordomo" not in txt(C), "| Cadu vê a pública antiga:", "porta trancada" in txt(C))
# mestre fala como NPC
M.dock_chat.show(); w(100); M._npcs_do_chat()
print("NPCs no 'como':", [M.painel_chat.como.itemText(k) for k in range(M.painel_chat.como.count())])
M.painel_chat.como.setCurrentText("Duquesa Velmora"); M.painel_chat.campo.setText("Saiam da minha casa!"); M.painel_chat._enviar(); w(300)
print("Manel vê fala da Duquesa:", "Duquesa Velmora (Mestre): Saiam" in txt(P))
# mestre sussurra pro Manel
M.painel_chat.como.setCurrentText("Mestre"); M.painel_chat.para.setCurrentIndex(M.painel_chat.para.findData("Manel"))
M.painel_chat.campo.setText("Você sente um arrepio."); M.painel_chat._enviar(); w(300)
print("sussurro do mestre: Manel", "arrepio" in txt(P), "| Bia não:", "arrepio" not in txt(B))
# /r no chat
P.painel_chat.para.setCurrentIndex(0); P.painel_chat.campo.setText("/r 1d20+3"); P.painel_chat._enviar(); w(400)
print("rolagem via chat aparece pra Bia:", "Manel: " in txt(B) and "(1d20+3)" in txt(B))
# aviso quando o chat está fechado
B.dock_chat.hide(); B.dock_dados.hide(); avisos=[]; o=B.aviso_rolagem.mostrar_texto; B.aviso_rolagem.mostrar_texto=lambda t,s=5:(avisos.append(t),o(t,s))
P.painel_chat.campo.setText("Bia, cuidado!"); P.painel_chat._enviar(); w(300); print("aviso com chat fechado:", avisos[-1][:60] if avisos else None)
# rolagens prontas
pd=P.painel_dados
pd._salvar_prontas([{"nome":"Ataque com espada","expr":"1d20+5"},{"nome":"Dano da espada","expr":"1d8+3"}])
botoes=[pd.grade_prontas.itemAt(k).widget() for k in range(pd.grade_prontas.count())]
print("botões prontos:", [b.text() for b in botoes])
roladas=[]; M.servidor.rolagem.connect(roladas.append)
botoes[0].click(); w(400)
print("rolou pronta:", roladas[-1]["expr"], roladas[-1]["motivo"], "=", roladas[-1]["total"], "| no chat da Bia:", "Ataque com espada" in txt(B))
print("guardada no PC:", [p["nome"] for p in pd.prontas()])
# diário
from taverna.ui.diario import nova_entrada
M.abrir_diario(); jd=M.janela_diario
jd.cb_novo.setCurrentIndex(jd.cb_novo.findData("sessao")); jd._nova(); jd.compartilhar.setChecked(True)
jd.texto.setPlainText("## O que aconteceu\nO grupo chegou à **mansão Velmora**.\n- achou uma chave\n- ouviu sussurros"); w(50)
jd.cb_novo.setCurrentIndex(jd.cb_novo.findData("npc")); jd._nova(); jd.titulo.setText("Duquesa Velmora"); jd._editou()
jd.texto.setPlainText("**Segredo:** é uma vampira."); w(1000)
print("diário do mestre:", [(e["tipo"], e["titulo"], e["compartilhado"]) for e in M.diario])
print("Manel recebeu só a compartilhada:", [e["titulo"] for e in P.diario])
P.abrir_diario(); w(200); print("Manel lê:", P.janela_diario.leitor.toPlainText()[:80].replace("\n"," | "))
P.janela_diario.notas.setPlainText("Desconfiar da Duquesa."); P.janela_diario.close()
jd.show(); jd.grab().save("saida/shot_diario.png")
M.dock_chat.show(); M.dock_dados.show(); w(100); M.grab().save("saida/shot_chat_mestre.png")
P.dock_chat.show(); P.dock_dados.show(); w(100); P.grab().save("saida/shot_chat_player.png")
print("barra do jogador:", P.barra.sizeHint().width(), "| mestre:", M.barra.sizeHint().width())
pasta=tempfile.mkdtemp(); M.caminho_cena=os.path.join(pasta,"d.taverna"); M.salvar()
M2=JanelaMestre(); M2.abrir_cena(M.caminho_cena); print("reaberto, diário:", [e["titulo"] for e in M2.diario])
print("FIM")
