"""(v0.60.1) Pedidos do Manel sobre paredes e portas:
- sala encostada em sala não faz parede repetida (era isso que sumia no 3D);
- parede que encosta no meio de outra (T) para no eixo dela (não abre frestinha no canto);
- porta fica PRESA (arrastar não move); botão direito acha a porta mesmo errando um pouquinho;
- excluir a porta fecha a parede de novo (uma parede só, do mesmo material)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtWidgets import QApplication, QGraphicsItem
from PyQt6.QtTest import QTest

app = QApplication(sys.argv)
from taverna.config import CELULA as C
from taverna.mesa.construcao import pedacos_livres, sem_sobreposicao
from taverna.mesa.portas import PortaItem
from taverna.ui.janela_mestre import JanelaMestre
w = QTest.qWait


def sobreposicoes(segs):
    """Quantos pares de paredes estão uma em cima da outra (mesma linha, trecho em comum > 2 px)."""
    lista = list(segs.values())
    n = 0
    for i, s in enumerate(lista):
        outros = lista[:i] + lista[i + 1:]
        livres = pedacos_livres(s["a"], s["b"], outros)
        comp = ((s["b"][0] - s["a"][0]) ** 2 + (s["b"][1] - s["a"][1]) ** 2) ** 0.5
        livre = sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 for a, b in livres)
        if comp - livre > 2:
            n += 1
    return n


M = JanelaMestre(); M.resize(1100, 800); M.show(); M.mostrar_mesa(); w(50)
c = M.cena
print("== salas encostadas")
c.criar_sala(QPointF(-6 * C, -4 * C), QPointF(0, 0))
c.criar_sala(QPointF(0, -4 * C), QPointF(6 * C, 0))
c.criar_sala(QPointF(-6 * C, 0), QPointF(6 * C, 4 * C))
print("paredes:", len(c.paredes.segmentos), "· sobrepostas:", sobreposicoes(c.paredes.segmentos))
assert sobreposicoes(c.paredes.segmentos) == 0
assert c.paredes.adicionar(QPointF(-6 * C, 0), QPointF(0, 0), "pedra") is None   # já tem parede ali

print("== aventura antiga com parede repetida é consertada ao abrir")
velhas = {"x1": {"a": [0, 0], "b": [4 * C, 0], "m": "pedra"}, "x2": {"a": [2 * C, 0], "b": [6 * C, 0], "m": "pedra"},
          "x3": {"a": [4 * C, 0], "b": [0, 0], "m": "pedra"}}
limpas = sem_sobreposicao(velhas)
print(" ", len(velhas), "->", len(limpas), "·", [(s["a"], s["b"]) for s in limpas.values()])
assert len(limpas) == 2 and sobreposicoes(limpas) == 0

print("== encontro em T")
uid_t = c.paredes.adicionar(QPointF(2 * C, 0), QPointF(2 * C, 4 * C), "pedra")
pontas = c.paredes._caps[uid_t]
print("  pontas da parede do meio:", pontas)
assert pontas == (False, False)                       # as duas pontas encostam no meio de outra parede
canto = next(u for u, s in c.paredes.segmentos.items() if s["a"] == [-6 * C, -4 * C] or s["b"] == [-6 * C, -4 * C])
assert c.paredes._caps[canto] != (False, False)       # canto de verdade continua fechado

print("== porta presa")
n_antes = len(c.paredes.segmentos)
porta = c.colocar_porta(QPointF(-3 * C, 4 * C))
assert isinstance(porta, PortaItem)
assert not (porta.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
c.camada_por_tipo("paredes").travada = False
porta.aplicar_trava(False)
assert not (porta.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
M.visao.centerOn(porta.scenePos()); w(100)
antes = QPointF(porta.scenePos())
p_tela = M.visao.mapFromScene(porta.scenePos())
QTest.mousePress(M.visao.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p_tela)
QTest.mouseMove(M.visao.viewport(), p_tela + QPoint(80, 60))
QTest.mouseRelease(M.visao.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p_tela + QPoint(80, 60))
w(100)
print("  arrastou: porta foi de", antes, "para", porta.scenePos())
assert porta.scenePos() == antes
print("== botão direito acha a porta perto")
assert c.porta_perto(QPointF(-3 * C, 4 * C - 0.4 * C)) is porta
assert c.porta_perto(QPointF(-3 * C, 4 * C - 1.5 * C)) is None
print("== excluir a porta fecha a parede")
assert c.parede_em(porta.scenePos()) is None           # tinha vão
n_com_porta = len(c.paredes.segmentos)
c.remover_itens([porta])
print("  paredes:", n_antes, "-> com porta", n_com_porta, "-> sem porta", len(c.paredes.segmentos))
assert c.parede_em(QPointF(-3 * C, 4 * C)) is not None   # fechou
assert len(c.paredes.segmentos) == n_antes               # virou uma parede só de novo
assert sobreposicoes(c.paredes.segmentos) == 0
c.desfazer()                                               # Ctrl+Z traz a porta (e o vão) de volta
assert any(isinstance(i, PortaItem) for i in c.camada_por_tipo("paredes").itens())
c.clearSelection(); M.visao.centerOn(QPointF(0, 0)); w(200)
M.visao.grab().save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida", "paredes_portas.png"))
print("FIM")
sys.stdout.flush()
os._exit(0)
