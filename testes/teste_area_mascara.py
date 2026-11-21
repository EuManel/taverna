"""(v0.69.1) Bug do Manel: área de fogo dentro da sala aparecia vazando PRA FORA (só na placa de vídeo).
A máscara do shader era guardada só por forma/tamanho: duas áreas iguais (ou uma apagada e outra nova) pegavam
a máscara uma da outra, com o recorte de outro lugar. Agora a máscara é de CADA área, no lugar onde ela está."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv[:1])
from taverna.config import CELULA as C
from taverna.mesa import efeitos_gl
from taverna.mesa.cena import MesaCena

cena = MesaCena()
cena.criar_camadas_padrao()
cena.criar_sala(QPointF(-20 * C, -20 * C), QPointF(0, 0))       # salão grande
cena.criar_sala(QPointF(10 * C, 10 * C), QPointF(16 * C, 16 * C))  # quartinho

print("== área no canto do salão (cortada só de um lado) e área igual no quartinho (cortada toda)")
a = cena.criar_efeito(dict(efeito="fogo", forma="circulo", tamanho=5, x=-19 * C, y=-10 * C))
b = cena.criar_efeito(dict(efeito="fogo", forma="circulo", tamanho=5, x=13 * C, y=13 * C))
ra = a.caminho_cena().boundingRect()
rb = b.caminho_cena().boundingRect()
print("   salão:", ra.width() / C, "· quartinho:", rb.width() / C)
assert rb.height() < ra.height() - C                                # o do quartinho foi cortado
ma, reta = efeitos_gl.mascara(a)
mb, retb = efeitos_gl.mascara(b)
print("   máscaras:", reta.height() / C, retb.height() / C)
assert retb.height() < reta.height() - C, "o quartinho pegou a máscara do salão"
assert b.mapToScene(retb).boundingRect().adjusted(-1, -1, 1, 1).contains(rb)

print("== apagou e pôs outra igual no quartinho: máscara certa")
cena.removeItem(b)
c = cena.criar_efeito(dict(efeito="fogo", forma="circulo", tamanho=5, x=13 * C, y=13 * C))
mc, retc = efeitos_gl.mascara(c)
assert retc.height() < reta.height() - C

print("== mudou de lugar: máscara nova")
c.setPos(c.pos() + QPointF(-23 * C, -23 * C))   # foi pro meio do salão: cabe inteira de novo
c.caminho()
md, retd = efeitos_gl.mascara(c)
print("   depois de mover:", retd.width() / C)
assert retd.height() > retc.height() + C
print("FIM")
sys.stdout.flush()
os._exit(0)
