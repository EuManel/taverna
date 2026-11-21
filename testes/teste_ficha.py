import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.environ["QT_QPA_PLATFORM"]="offscreen"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
from taverna.config import CELULA
from taverna.mesa.token import TokenItem
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
QMessageBox.information=staticmethod(lambda *a,**k: None)
M=JanelaMestre(); M.resize(1400,850); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
c=M.cena
aelar=c.adicionar_token(dict(nome="Aelar",tipo="jogador",cor="#3f6b4a",tamanho=1,imagem=None,dono="Manel"), QPointF(0,0))
lyra=c.adicionar_token(dict(nome="Lyra",tipo="jogador",cor="#5a3f6b",tamanho=1,imagem=None,dono="Bia"), QPointF(2*CELULA,0))
lyra.ficha={"nome":"Lyra","classe":"Mago","nivel":3,"historia":"segredo da Bia"}
aelar.definir_info("inventario",[{"id":"i1","nome":"Espada Lendária","qtd":1,"desc":"do baú","img":None,"origem":"Baú"}])
assert M.servidor.abrir(7793)
def player(n):
    P=JanelaPlayer(); P.resize(1200,800); P.show(); P.nome,P.ip,P.porta=n,"127.0.0.1",7793
    P._ja_entrou=False; P._primeiro_estado=True; P.cliente.conectar(P.ip,P.porta,P.nome); return P
P1=player("Manel"); P2=player("Bia"); w(900)
def tok(P,n): return next(i for i in P.cena.itens.values() if isinstance(i,TokenItem) and i.nome==n)
print("Manel recebeu ficha da Lyra?", tok(P1,"Lyra").ficha is not None, "| Bia recebeu a dela:", (tok(P2,"Lyra").ficha or {}).get("historia"))

print("== PLAYER importa PDF e salva")
P1.abrir_minha_ficha(); F1=P1._fichas[aelar.uid]; w(100)
print("inventário na ficha:", [F1.inv.item(r,0).text() for r in range(F1.inv.rowCount())])
QFileDialog.getOpenFileName=staticmethod(lambda *a,**k: (os.path.abspath("ficha_teste_preenchida.pdf"),""))
F1._importar_pdf(); w(50)
print("importou:", F1.nome.text(), F1.classe.currentText(), F1.nivel.value(), "| FOR mod", F1.atrib_mod["for"].text(),
      "| atletismo", F1.per_val["atletismo"].text(), "| inventário:", [F1.inv.item(r,0).text() for r in range(F1.inv.rowCount())])
F1.grab().save("ficha_principal.png")
F1._salvar(); w(600)
print("mestre recebeu: PV", aelar.info["pv"]["v"], "desl", aelar.deslocamento, "raça", aelar.info["raca"]["v"], "classe", aelar.info["classe"]["v"])
print("ficha no token do mestre:", aelar.ficha["nome"], aelar.ficha["atributos"]["for"], "| inventário:", [i["nome"] for i in aelar.info["inventario"]["v"]])
print("Bia vê inventário do Aelar?", tok(P2,"Aelar").info.get("inventario",{}).get("v"), "| ficha?", tok(P2,"Aelar").ficha)

print("== MESTRE abre e dá dano; ficha atualiza")
M.abrir_ficha(aelar); FM=M._fichas[aelar.uid]; w(100)
c.clearSelection(); aelar.setSelected(True); M.painel_info.atualizar(); M.painel_info.pv.setValue(12); w(300)
FM.atualizar_de_fora(); print("ficha do mestre PV:", FM.pv.value(), "/", FM.pv_max.value())
w(400); F1.atualizar_de_fora(); print("ficha do player PV:", F1.pv.value(), "/", F1.pv_max.value())
FM.nivel.setValue(9); FM._salvar(); w(400)
print("nível 9 -> prof", FM.lbl_prof.text(), "| classe no INFORMAÇÕES:", aelar.info["classe"]["v"])
print("--- histórico:", M.painel_historico.texto.toPlainText().splitlines()[-1])

print("== PDFs")
pasta=tempfile.mkdtemp()
QFileDialog.getSaveFileName=staticmethod(lambda *a,**k: (os.path.join(pasta,"aelar.pdf"),""))
FM._exportar_pdf(); print("PDF Taverna:", os.path.getsize(os.path.join(pasta,"aelar.pdf")), "bytes")
import pypdfium2 as pdfium
pg=pdfium.PdfDocument(os.path.join(pasta,"aelar.pdf"))[0]; bm=pg.render(scale=1.2)
from PyQt6.QtGui import QImage
QImage(bm.buffer, bm.width, bm.height, bm.stride, QImage.Format.Format_BGR888).copy().save("ficha_pdf.png")
QFileDialog.getOpenFileName=staticmethod(lambda *a,**k: (os.path.abspath("ficha_teste_fillable.pdf"),""))
QFileDialog.getSaveFileName=staticmethod(lambda *a,**k: (os.path.join(pasta,"oficial.pdf"),""))
FM._preencher_oficial()
from taverna.jogo.ficha import ler_campos_pdf
print("oficial preenchida:", {k:v for k,v in ler_campos_pdf(os.path.join(pasta,"oficial.pdf")).items() if k in ("CharacterName","ClassLevel","ProfBonus","Equipment","HPCurrent")})

print("== SALVAR/ABRIR aventura")
M.caminho_cena=os.path.join(pasta,"f.taverna"); M.salvar()
M2=JanelaMestre(); M2.abrir_cena(M.caminho_cena)
a2=next(t for t in M2.cena.itens_do_usuario() if isinstance(t,TokenItem) and t.nome=="Aelar")
print("reaberto:", a2.ficha["nome"], a2.ficha["nivel"], len(a2.ficha["ataques"]), "ataques")
M2.close(); FM.sujo=False; F1.sujo=False
print("FIM")
