"""v0.43: o mestre libera livros (o PDF vai pela rede) e vê a biblioteca do jogador."""
import sys, os, json, shutil, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.ui.tema import QSS
app = QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
w = QTest.qWait


def esperar(cond, ms=8000):
    for _ in range(ms // 50):
        if cond():
            return True
        w(50)
    return cond()


# as preferências reais: guarda e devolve no fim
cfg_m, cfg_p = QSettings("Taverna", "Mestre"), QSettings("Taverna", "Player")
antes_lib = cfg_m.value("livros_liberados", "{}")
antes_pdfs = cfg_p.value("meus_pdfs", "[]")
pasta = tempfile.mkdtemp(prefix="taverna_livros_")
livro = os.path.join(pasta, "Regras da casa.pdf")
dados = b"%PDF-1.4\n" + os.urandom(1_000_000) + b"\n%%EOF"   # ~1 MB: vai em várias partes
open(livro, "wb").write(dados)
meu = os.path.join(pasta, "Meu bestiário caseiro.pdf")
open(meu, "wb").write(b"%PDF-1.4\n" + os.urandom(300_000) + b"\n%%EOF")
try:
    M = JanelaMestre(); M.show()
    assert M.servidor.abrir(7791)
    cfg_p.setValue("meus_pdfs", json.dumps([meu]))
    P = JanelaPlayer(); P.show()
    P.nome, P.ip, P.porta = "Lúcia", "127.0.0.1", 7791
    P._ja_entrou = False; P._primeiro_estado = True
    P.cliente.conectar(P.ip, P.porta, P.nome)
    assert esperar(lambda: "Lúcia" in M.servidor.nomes())

    print("== o mestre libera um livro pra Lúcia")
    M.servidor.livros.liberar(livro, ["Lúcia"])
    assert esperar(lambda: any(d["caminho"] for d in P.livros.livros()))
    recebido = next(d["caminho"] for d in P.livros.livros() if d["caminho"])
    print("chegou:", os.path.basename(recebido), os.path.getsize(recebido), "bytes")
    assert open(recebido, "rb").read() == dados
    P.abrir_biblioteca(); w(100)
    abas = [P._biblioteca.abas.tabText(i) for i in range(P._biblioteca.abas.count())]
    print("abas do jogador:", abas)
    assert any("mestre" in a.lower() for a in abas)

    print("== o mestre tira a liberação: a cópia some")
    M.servidor.livros.liberar(livro, [])
    assert esperar(lambda: not os.path.exists(recebido))
    assert not P.livros.livros()

    print("== o mestre vê a biblioteca da Lúcia e pega uma cópia")
    assert esperar(lambda: M.servidor.livros.dos_jogadores.get("Lúcia"))
    lista = M.servidor.livros.dos_jogadores["Lúcia"]
    print("biblioteca da Lúcia:", [d["titulo"] for d in lista])
    assert any(d["titulo"] == "Meu bestiário caseiro" for d in lista)
    M.abrir_biblioteca(); w(100)
    assert M._biblioteca.dos_jogadores.arvore.topLevelItemCount() >= 1
    ident = next(d["id"] for d in lista if d["titulo"] == "Meu bestiário caseiro")
    assert M.servidor.livros.pedir_copia("Lúcia", ident)
    copia = os.path.join(M.servidor.livros.pasta_copias("Lúcia"), "Meu bestiário caseiro.pdf")
    assert esperar(lambda: os.path.exists(copia))
    print("cópia com o mestre:", os.path.getsize(copia), "bytes")
    assert open(copia, "rb").read() == open(meu, "rb").read()
    os.remove(copia)

    print("== 'Todos' vale pra quem entra depois")
    M.servidor.livros.liberar(livro, ["*"])
    assert esperar(lambda: any(d["caminho"] for d in P.livros.livros()))
    M.servidor.livros.liberar(livro, [])
    esperar(lambda: not any(d["caminho"] for d in P.livros.livros()))
    print("FIM")
finally:
    cfg_m.setValue("livros_liberados", antes_lib)
    cfg_p.setValue("meus_pdfs", antes_pdfs)
    shutil.rmtree(pasta, ignore_errors=True)
# sai como o taverna.py sai (v0.50): sem o Python desmontar o Qt peça por peça (às vezes caía na saída)
sys.stdout.flush()
os._exit(0)
