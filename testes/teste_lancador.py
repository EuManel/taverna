"""v0.49: launcher único — a tela em QML abre nos 3 níveis de gráficos, o mestre entra e volta,
o jogador conecta e entra na mesa."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"; os.environ["TAVERNA_SEM_AUDIO"] = "1"
os.environ.setdefault("QT_QUICK_BACKEND", "software")   # sem placa de vídeo nos testes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
app = QApplication(sys.argv); app.setStyle("Fusion")
from taverna.graficos import graficos
from taverna.ui.lancador import JanelaLancador
w = QTest.qWait
saida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")
os.makedirs(saida, exist_ok=True)


def esperar(cond, ms=5000):
    for _ in range(ms // 50):
        if cond():
            return True
        w(50)
    return cond()


nivel_antes = graficos().atual
print("== (v0.51) a luvinha vale em qualquer janela do Taverna")
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton
from taverna.ui.cursor_global import instalar as instalar_luva, definir_cor
instalar_luva(app)
b = QPushButton("teste"); b.show(); b.setCursor(Qt.CursorShape.PointingHandCursor); w(50)
assert b.cursor().shape() == Qt.CursorShape.BitmapCursor, b.cursor().shape()   # virou luva
from PyQt6.QtWidgets import QLineEdit
campo = QLineEdit(); campo.show(); campo.setCursor(Qt.CursorShape.IBeamCursor); w(50)
assert campo.cursor().shape() == Qt.CursorShape.IBeamCursor   # onde digita, fica o de texto
definir_cor("#c03030")
assert b.cursor().shape() == Qt.CursorShape.BitmapCursor
b.close(); campo.close()
print("ok")
L = JanelaLancador(); L.resize(1280, 800); L.show(); w(300)
raiz = L.quick.rootObject()
assert raiz is not None, [e.toString() for e in L.quick.errors()]
print("== a tela abre nos 3 níveis e em todos os temas")
for chave in ("baixo", "medio", "alto"):
    L.ponte.definirNivel(chave); w(250)
    L.quick.grab().save(os.path.join(saida, f"lancador_{chave}.png"))
for t in ("futurista", "magico", "claro"):
    L.ponte.definirTema(t); w(250)
    L.quick.grab().save(os.path.join(saida, f"lancador_alto_{t}.png"))
L.ponte.definirTema("medieval")
print("capturas em testes/saida/lancador_*.png")

print("== (v0.81) janelinha de pai escondido abre em cima da tela inicial, não no monitor principal")
M = L._janela_mestre()
from taverna.ui.dialogos import DialogoNovaAventura
L.move(160, 90); w(100)
dlg = DialogoNovaAventura(M, os.path.join(saida, "aventuras"), lambda nome: False)
dlg.show(); w(100)
d = dlg.frameGeometry().center() - L.frameGeometry().center()
assert abs(d.x()) <= 2 and abs(d.y()) <= 2, (dlg.frameGeometry(), L.frameGeometry())
dlg.close()
print("ok")

print("== Mestre → nova sessão → mesa; fechar a sessão volta pro launcher")
M.nova_cena = lambda: True   # (sem a janelinha de nome/tema)
L.ponte.escolher("mestre_nova"); w(300)
assert M.isVisible() and not L.isVisible() and M.pilha.currentWidget() is M.area_mesa
assert L.ponte.papel == "mestre"
M._pode_descartar = lambda: True
M.fechar_sessao(); w(300)
assert L.isVisible() and not M.isVisible()
print("ok")

print("== Jogador → conecta no mestre → a mesa dele aparece")
M.mostrar_mesa(); M.show()
assert M.servidor.abrir(7803)
P = L._janela_player()
P.pedir_conexao = lambda erro="": (setattr(P, "nome", "Bia"), setattr(P, "ip", "127.0.0.1"), setattr(P, "porta", 7803),
                                  P.cliente.conectar("127.0.0.1", 7803, "Bia"), True)[-1]
L.show(); L.ponte.escolher("jogador_entrar")
assert esperar(lambda: P.isVisible() and not L.isVisible())
assert L.ponte.papel == "jogador"
print("ok")
graficos().definir(nivel_antes)
print("FIM")
