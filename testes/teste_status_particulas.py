"""(v0.79) Status do token com PARTÍCULAS (Mesa 3D): "em chamas", "envenenado", "sangrando", "congelado"… soltam as
partículas das áreas em volta do token (além do simbolozinho). Vale o efeito em cima do token e as condições da ficha;
o token fica animando enquanto tiver status; no Baixo não tem partícula."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

app = QApplication(sys.argv[:1])
from taverna import seguranca
erros = []
seguranca.registrar_erro = lambda t: erros.append(t)
from taverna.graficos import graficos
graficos().definir("alto")
from taverna.config import CELULA as C
from taverna.mesa import efeitos3d
from taverna.ui.janela_mestre import JanelaMestre

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")
M = JanelaMestre(); M.resize(1400, 900); M.show(); M.mostrar_mesa(); QTest.qWait(80)
c, v = M.cena, M.visao
c.criar_sala(QPointF(-6 * C, -4 * C), QPointF(6 * C, 4 * C))
fogo = c.adicionar_token(dict(nome="Fogo", tipo="criatura", cor="#6a5a40", tamanho=1, imagem=None, dono=""),
                         QPointF(-3 * C, 0))
sangra = c.adicionar_token(dict(nome="Sangra", tipo="criatura", cor="#6a5a40", tamanho=2, imagem=None, dono=""),
                           QPointF(1 * C, 0))
nada = c.adicionar_token(dict(nome="Nada", tipo="criatura", cor="#6a5a40", tamanho=1, imagem=None, dono=""),
                         QPointF(4 * C, 0))
fogo.definir_efeito("fogo")
sangra.definir_info("condicoes", ["sangrando", "envenenado"], "todos")
c.clearSelection()

print("== quais partículas cada um solta")
assert efeitos3d.status_do_token(fogo) == ["fogo"]
assert efeitos3d.status_do_token(sangra) == ["sangue", "veneno"]
assert efeitos3d.status_do_token(nada) == []
assert sangra.animado() and fogo.animado() and not nada.animado()   # (fica animando por causa da condição)

print("== desenhadas junto com o token, inclinada e de cima")
vistos = []
orig = efeitos3d.desenhar_status


def contar(painter, cam, tok, t, n):
    vistos.append(tok.nome)
    orig(painter, cam, tok, t, n)


efeitos3d.desenhar_status = contar
v.definir_zoom(1.0)
v.centerOn(QPointF(0, 0))
v.definir_camera(0, 45, livre=True)
QTest.qWait(400)
print("   tokens com partículas:", sorted(set(vistos)))
assert {"Fogo", "Sangra"} <= set(vistos) and "Nada" not in vistos
v.grab().save(os.path.join(SAIDA, "status_particulas.png"))
pts = efeitos3d._pontos_token(sangra, 20)
centro = sangra.centro_cena()
assert all(((x - centro.x()) ** 2 + (y - centro.y()) ** 2) ** 0.5 <= sangra.diametro * 0.5 for x, y, _a, _b in pts)

print("== no Baixo, nada de partícula")
vistos.clear()
graficos().definir("baixo")
v.viewport().update()
QTest.qWait(300)
assert not vistos
efeitos3d.desenhar_status = orig
graficos().definir("alto")
print("   erros:", erros[:2])
assert not erros, erros
print("FIM")
sys.stdout.flush()
os._exit(0)
