import sys, os, shutil, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.environ["QT_QPA_PLATFORM"]="offscreen"; os.environ["TAVERNA_SEM_AUDIO"]="1"
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, HexColor
c=canvas.Canvas(os.path.join(tempfile.gettempdir(),"op_ficha.pdf"), pagesize=(595,842))
c.setFillColor(HexColor("#1b1b1b")); c.rect(0,780,595,62,fill=1,stroke=0)
c.setFillColor(HexColor("#e8e8e8")); c.setFont("Helvetica-Bold",20); c.drawString(30,805,"FICHA DE AGENTE (exemplo)")
c.setFillColor(black); c.setFont("Helvetica",10)
f=c.acroForm
c.drawString(30,745,"Nome do agente"); f.textfield(name="nome", x=30, y=720, width=300, height=20, borderWidth=0.5)
c.drawString(350,745,"NEX %"); f.textfield(name="nex", x=350, y=720, width=60, height=20, borderWidth=0.5)
c.drawString(30,700,"Classe"); f.radio(name="classe", value="Combatente", x=30, y=680, size=12, selected=False)
c.drawString(48,682,"Combatente"); f.radio(name="classe", value="Especialista", x=130, y=680, size=12, selected=True)
c.drawString(148,682,"Especialista"); f.radio(name="classe", value="Ocultista", x=240, y=680, size=12, selected=False); c.drawString(258,682,"Ocultista")
c.drawString(30,655,"Origem"); f.choice(name="origem", value="Acadêmico", options=["Acadêmico","Policial","Religioso","Militar"], x=30, y=630, width=200, height=20)
f.checkbox(name="ferido", x=30, y=600, size=14, checked=False); c.drawString(50,603,"Machucado")
f.checkbox(name="sanidade_baixa", x=150, y=600, size=14, checked=False); c.drawString(170,603,"Enlouquecendo")
c.drawString(30,575,"Inventário"); f.textfield(name="inventario", x=30, y=430, width=530, height=140, borderWidth=0.5, fieldFlags="multiline")
c.showPage()
c.drawString(30,780,"Página 2 — Rituais"); f.textfield(name="nome_p2", x=30, y=750, width=300, height=20, borderWidth=0.5)
f.textfield(name="rituais", x=30, y=500, width=530, height=230, borderWidth=0.5, fieldFlags="multiline")
c.save()
from taverna.jogo.pdf_form import ler_formulario, gravar_formulario
form=ler_formulario(os.path.join(tempfile.gettempdir(),"op_ficha.pdf"))
print("campos:", [(x["nome"], x["tipo"], x["valor"], x["ligado"]) for x in form["campos"]])
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt
from taverna.ui.tema import QSS
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w=QTest.qWait
from taverna.ui import fichas_pdf as F
for a in os.listdir(F.pasta_fichas()): os.remove(os.path.join(F.pasta_fichas(), a))
dst=os.path.join(F.pasta_fichas(),"Agente Lúcia.pdf"); shutil.copy(os.path.join(tempfile.gettempdir(),"op_ficha.pdf"), dst)
ed=F.EditorFichaPDF(dst); ed.show(); w(300)
nome=ed.widgets["nome"][0]; nome.setFocus(); QTest.keyClicks(nome, "Lucia Andrade"); w(50)
QTest.keyClicks(ed.widgets["nex"][0], "35")
radios=ed.widgets["classe"]; print("radios:", [(r.ligado, r.isChecked()) for r in radios])
radios[2].click(); w(50); print("depois de clicar Ocultista:", [(r.ligado, r.isChecked()) for r in radios])
ed.widgets["ferido"][0].click(); ed.widgets["origem"][0].setCurrentText("Religioso")
ed.widgets["inventario"][0].setPlainText("Revólver (12 balas)\nLanterna\nAmuleto de sangue")
print("nome igual na página 2? (campos diferentes, não sincroniza):", ed.widgets["nome_p2"][0].text()=="")
print("modificado:", ed.modificado, "|", ed.status.text())
ed.rolagem.verticalScrollBar().setValue(0); w(100); ed.grab().save("saida/shot_fichapdf.png")
ed.close(); w(100)
v=ler_formulario(dst)
print("relido do arquivo:", {x["nome"]: x["valor"] for x in v["campos"] if x["nome"] in ("nome","nex","classe","origem","ferido","sanidade_baixa")})
print("inventário:", repr([x["valor"] for x in v["campos"] if x["nome"]=="inventario"][0]))
# reabrir mostra o que foi salvo
ed2=F.EditorFichaPDF(dst); print("reabriu com:", ed2.widgets["nome"][0].text(), ed2.widgets["ferido"][0].isChecked(), [r.isChecked() for r in ed2.widgets["classe"]]); ed2.close()
# o PDF preenchido abre certo em outro leitor (pdfium com formulários)
import pypdfium2 as pdfium
doc=pdfium.PdfDocument(dst); doc.init_forms(); bm=doc[0].render(scale=1, may_draw_forms=True)
from PyQt6.QtGui import QImage
QImage(bm.buffer,bm.width,bm.height,bm.stride,QImage.Format.Format_BGR888).copy().save("saida/shot_fichapdf_outro_leitor.png")
bm.close(); doc.close()  # no Windows o PDF aberto não deixa apagar o arquivo no fim
# PDF sem campos
ed3=F.EditorFichaPDF("teste.pdf"); print("sem campos:", ed3.status.text()); ed3.close()
# ficha antiga de teste (D&D)
if os.path.exists("ficha_teste_fillable.pdf"):
    print("ficha D&D de teste:", len(ler_formulario("ficha_teste_fillable.pdf")["campos"]), "campos")
J=F.JanelaFichasPDF(); print("lista:", [J.lista.item(i).text() for i in range(J.lista.count())])
os.remove(dst)
print("FIM")
