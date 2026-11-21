import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.environ["QT_QPA_PLATFORM"]="offscreen"; os.environ["TAVERNA_SEM_AUDIO"]="1"
from PyQt6.QtCore import QPointF, QBuffer, QIODevice, Qt
from PyQt6.QtGui import QImage, QPainter, QColor, QFont, QLinearGradient
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
def imagem(texto, cor, tam=(2600,1600)):
    img=QImage(*tam, QImage.Format.Format_RGB32); p=QPainter(img)
    g=QLinearGradient(0,0,tam[0],tam[1]); g.setColorAt(0,QColor(cor)); g.setColorAt(1,QColor("#1a1410")); p.fillRect(img.rect(), g)
    f=QFont("Georgia"); f.setPixelSize(tam[1]//8); p.setFont(f); p.setPen(QColor("#f0e0c0"))
    p.drawText(img.rect(), Qt.AlignmentFlag.AlignCenter, texto); p.end()
    b=QBuffer(); b.open(QIODevice.OpenModeFlag.WriteOnly); img.save(b,"PNG"); return bytes(b.data())
M=JanelaMestre(); M.resize(1400,850); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
M.cena.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Manel"), QPointF(0,0))
duq=M.cena.adicionar_token(dict(nome="Duquesa Velmora",tipo="npc",cor="#5a3a6a",tamanho=1,imagem=imagem("Duquesa","#6a3a7a",(600,600)),dono=""), QPointF(200,0))
pp=M.painel_projetor
grande=imagem("Mapa do tesouro","#8a5a2a")
i=pp.adicionar(grande, "Mapa do tesouro")
print("galeria:", [x["titulo"] for x in pp.galeria], "| reduzida:", len(grande)//1024, "KB ->", len(pp.galeria[0]["dados"])//1024, "KB")
assert M.servidor.abrir(7796)
def entrar(nome):
    P=JanelaPlayer(); P.resize(1100,750); P.show(); P.nome,P.ip,P.porta=nome,"127.0.0.1",7796
    P._ja_entrou=False; P._primeiro_estado=True; P.cliente.conectar(P.ip,P.porta,P.nome); return P
P=entrar("Manel"); B=entrar("Bia"); w(1000)
print("jogadores no painel:", [pp.lista_jog.item(k).text() for k in range(pp.lista_jog.count())])
M.dock_projetor.show(); pp.lista.setCurrentRow(0); pp.btn_projetar.click(); w(600)
print("Manel vê:", P.projecao.isVisible(), P.projecao.titulo.text(), "| Bia vê:", B.projecao.isVisible())
P.grab().save("saida/shot_proj_player.png")
P.projecao.hide(); w(400); print("Manel fechou e não reabre sozinho:", not P.projecao.isVisible())
# só pra Bia
pp.ck_todos.setChecked(False)
for k in range(pp.lista_jog.count()):
    it=pp.lista_jog.item(k); it.setCheckState(Qt.CheckState.Checked if it.text()=="Bia" else Qt.CheckState.Unchecked)
i2=pp.adicionar(imagem("Carta selada","#2a4a6a",(900,1200)), "Carta pra Bia"); pp.btn_projetar.click(); w(600)
print("só Bia:", "Bia", B.projecao.isVisible(), B.projecao.titulo.text(), "| Manel", P.projecao.isVisible())
pp.btn_recolher.click(); w(500); print("recolheu -> Bia:", B.projecao.isVisible())
# retrato de token pelo botão direito
M.projetar_imagem(duq.imagem, duq.nome); w(600)
print("retrato pra todos:", P.projecao.isVisible(), B.projecao.isVisible(), "| galeria:", [x["titulo"] for x in pp.galeria])
print("imagens recebidas Manel:", [x["titulo"] for x in P.imagens_recebidas], "| Bia:", [x["titulo"] for x in B.imagens_recebidas])
print("histórico:", M.painel_historico.texto.toPlainText().splitlines()[-1])
pasta=tempfile.mkdtemp(); M.caminho_cena=os.path.join(pasta,"p.taverna"); M.salvar()
M2=JanelaMestre(); M2.abrir_cena(M.caminho_cena); print("reaberto, galeria:", [x["titulo"] for x in M2.painel_projetor.galeria])
M.grab().save("saida/shot_proj_mestre.png")
print("barra mestre:", M.barra.sizeHint().width())
print("FIM")
