import sys, os, shutil, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.environ["QT_QPA_PLATFORM"]="offscreen"; os.environ["TAVERNA_SEM_AUDIO"]="1"
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QImage, QPainter, QColor
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.ui.tema import QSS
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
import numpy as np
from taverna.ui import remover_fundo as R
# imagem de teste: fundo branco levemente ruidoso + espada (marrom/cinza) + "ilha" branca no meio da guarda
img=QImage(600,400,QImage.Format.Format_RGB32); img.fill(QColor(250,250,248))
p=QPainter(img); p.setRenderHint(QPainter.RenderHint.Antialiasing)
p.setBrush(QColor("#8a8f99")); p.setPen(Qt.PenStyle.NoPen); p.drawRect(100,180,380,40)
p.setBrush(QColor("#6b4a2a")); p.drawRect(60,150,50,100)
p.setBrush(QColor(250,250,248)); p.drawEllipse(QPointF(85,200),10,10)
p.setBrush(QColor("#2e7d32")); p.drawEllipse(QPointF(520,200),60,60); p.end()
arr=R._para_array(img)
t=time.time(); auto=R.remover_automatico(arr, 40, True); dt=time.time()-t
print(f"automático: {dt*1000:.0f} ms | transparente: {(auto[:,:,3]==0).mean()*100:.0f}% | ilha branca no meio continua? {auto[200,85,3]>0} | espada inteira? {auto[200,300,3]==255 and auto[200,80,3]==255}")
masc=R._parecidos(auto, auto[200,85], 40); ilha=R.preencher(masc,[(200,85)])
print("clicar na ilha apaga só ela:", int(ilha.sum()), "px")
grande=QImage(2000,2000,QImage.Format.Format_RGB32); grande.fill(QColor("white"))
pp=QPainter(grande); pp.setBrush(QColor("red")); pp.drawEllipse(500,500,1000,1000); pp.end()
t=time.time(); R.remover_automatico(R._para_array(grande)); print(f"2000×2000: {(time.time()-t)*1000:.0f} ms")
from PyQt6.QtCore import QBuffer, QIODevice
b=QBuffer(); b.open(QIODevice.OpenModeFlag.WriteOnly); img.save(b,"PNG"); dados=bytes(b.data())
d=R.DialogoRemoverFundo(dados,"Espada"); d.show(); w(100); d._automatico(); w(100); d.grab().save("saida/shot_fundo.png")
out=QImage.fromData(d.resultado()); print("resultado cortado:", out.width(), "x", out.height(), "| tem alfa:", out.hasAlphaChannel())
d._desfazer(); print("desfazer volta ao original:", (d.arr[:,:,3]==255).all())
d.close()
# banco
from taverna.ui import banco_imagens as B
raiz=B.pasta_banco(); print("pastas:", sorted(os.listdir(raiz)))
tmp=tempfile.mkdtemp(); f1=os.path.join(tmp,"espada longa.png"); img.save(f1); f2=os.path.join(tmp,"goblin.png"); img.save(f2)
from taverna.ui.janela_mestre import JanelaMestre
M=JanelaMestre(); M.resize(1400,850); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
pb=M.painel_banco; M.abrir_banco(); w(50)
pb.cb_pasta.setCurrentIndex(pb.cb_pasta.findData("Objetos")); n=pb.importar([f1, f1]); print("importou:", n, "| na pasta:", [pb.grade.item(i).text() for i in range(pb.grade.count())])
pb.cb_pasta.setCurrentIndex(pb.cb_pasta.findData("Tokens")); pb.importar([f2])
c_obj=os.path.join(raiz,"Objetos","espada longa.png")
M._usar_do_banco("objeto", c_obj, QPointF(0,0)); M._usar_do_banco("token", os.path.join(raiz,"Tokens","goblin.png"), QPointF(150,0))
M._usar_do_banco("projetor", c_obj, None)
from taverna.mesa.props import PropItem
from taverna.mesa.token import TokenItem
props=[i for i in M.cena.itens_do_usuario() if isinstance(i,PropItem)]; toks=[i for i in M.cena.itens_do_usuario() if isinstance(i,TokenItem)]
print("na mesa:", [p.nome for p in props], [t.nome for t in toks], "| projetor:", [g["titulo"] for g in M.painel_projetor.galeria])
# arrastar do banco pra mesa (simula o drop)
M.visao.banco_solto.emit("mapa", c_obj, QPointF(-500,0)); w(50)
from taverna.mesa.mapa import MapaItem
print("drop como mapa:", [m.nome for m in M.cena.itens_do_usuario() if isinstance(m,MapaItem)])
M.dock_objetos.show(); M.abas_objetos.setCurrentWidget(pb); w(100); M.grab().save("saida/shot_banco.png")
for p_ in ("Objetos","Tokens","Projetor","Mapas"):
    for a in os.listdir(os.path.join(raiz,p_)): os.remove(os.path.join(raiz,p_,a))
print("FIM")
