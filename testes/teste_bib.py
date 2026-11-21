import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PyQt6.QtWidgets import QApplication, QFileDialog, QInputDialog
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.biblioteca import JanelaBiblioteca, LeitorPdf
from taverna.ui.tema import QSS
from taverna.mesa.token import TokenItem
app=QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
M=JanelaMestre(); M.resize(1400,860); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); QTest.qWait(50)
M.abrir_biblioteca(); B=M._biblioteca; QTest.qWait(100)

print("== v0.42: sem o compêndio de D&D")
abas = [B.abas.tabText(i) for i in range(B.abas.count())]
print("abas do mestre:", abas)
assert not any("Compêndio" in a or "SRD" in a for a in abas) and len(abas) == 4   # PDFs, Fichas, Tokens, Dos jogadores
P = JanelaBiblioteca(mestre=False)
print("abas do jogador (sem rede):", [P.abas.tabText(i) for i in range(P.abas.count())])
assert P.tokens is None and P.abas.count() == 2

print("== tokens: salvar na biblioteca e colocar na mesa")
from taverna.ui import biblioteca_tokens as BT
ident = BT.salvar({"nome": "Goblin de teste", "tipo": "criatura", "cor": "#6e2a2f", "tamanho": 1, "pv": 7, "desl": 9})
B.tokens.recarregar()
achou = [B.tokens.lista.item(i) for i in range(B.tokens.lista.count())
         if B.tokens.lista.item(i).text() == "Goblin de teste"]
assert achou
B.tokens.lista.setCurrentItem(achou[0])
antes = len([t for t in M.cena.itens_do_usuario() if isinstance(t, TokenItem)])
B.tokens._colocar(); B.tokens._colocar()   # spawna 2× (como objeto)
goblins = [t for t in M.cena.itens_do_usuario() if isinstance(t, TokenItem) and t.nome == "Goblin de teste"]
print("goblins na mesa:", len(goblins), "| PV:", goblins[0].info["pv"]["v"], "| desl:", goblins[0].deslocamento)
assert len(goblins) == 2 and goblins[0].info["pv"]["v"] == [7, 7] and goblins[0].deslocamento == 9
M.salvar_token_na_biblioteca(goblins[0])   # botão direito → salvar na biblioteca
assert sum(1 for d in BT.listar() if d["nome"] == "Goblin de teste") == 2
for d in BT.listar():
    if d["nome"] == "Goblin de teste":
        BT.apagar(d["id"])
B.mostrar_tokens(); QTest.qWait(30); B.grab().save("bib_tokens.png")
# o diálogo do token novo tem os 3 botões
from taverna.ui.dialogos import DialogoToken
dlg = DialogoToken(M)
textos = [b.text() for b in dlg.findChildren(type(dlg.findChildren(__import__("PyQt6.QtWidgets", fromlist=["QPushButton"]).QPushButton)[0]))]
print("botões do novo token:", [t for t in textos if t in ("Cancelar",) or "biblioteca" in t or "mesa" in t])
assert any("biblioteca" in t for t in textos) and any("mesa" in t for t in textos)

print("== fichas: modelo → nova ficha")
from taverna.ui.fichas_pdf import pasta_fichas
fich = B.fichas
QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: (os.path.abspath("teste.pdf"), ""))
fich._importar_modelo()
fich.modelos.setCurrentRow(0)
QInputDialog.getText = staticmethod(lambda *a, **k: ("Personagem de teste", True))
fich.fichas.abrir = lambda: None   # (não abre o editor no teste)
fich._nova()
criada = os.path.join(pasta_fichas(), "Personagem de teste.pdf")
print("ficha criada do modelo:", os.path.exists(criada))
assert os.path.exists(criada)
os.remove(criada)
for a in os.listdir(fich._pasta_modelos()):
    if a.startswith("teste"):
        os.remove(os.path.join(fich._pasta_modelos(), a))

print("== meus PDFs (continua igual)")
aba = B.pdfs
QFileDialog.getOpenFileNames=staticmethod(lambda *a,**k: ([os.path.abspath("teste.pdf")], ""))
aba._importar(); print("meus pdfs:", aba.arvore.topLevelItem(0).child(0).text(0))
L=LeitorPdf(os.path.abspath("teste.pdf")); L.show(); QTest.qWait(50)
L.busca.setText("goblin"); L.buscar(); print("busca ->", L.status.text(), "pagina", L.pagina+1)
L.grab().save("leitor_pdf.png")
aba._salvar("meus_pdfs", [])
print("FIM")
