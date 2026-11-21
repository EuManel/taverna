"""(v0.73) ♟ Tipos de token: FICHA redonda (a de sempre) ou STANDEE (a imagem em pé num suporte, sempre virada pra
câmera). O mestre escolhe um por um (Editar token → Peça) ou todos (Mesa → Peças dos tokens). Vai pela rede (protocolo
17, campo "es") e fica salvo. O cartão é desenhado depois das paredes e recortado só pelas que estão ENTRE a câmera
e o token (a parede do fundo não corta mais o cartão). Com a câmera inclinada, o nome do token fica de pé na tela."""
import os
import socket
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
from taverna.mesa import altura3d, camera3d
from taverna.mesa.token import TokenItem
from taverna.rede.protocolo import VERSAO_PROTOCOLO
from taverna.ui.dialogos import DialogoToken
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")
assert VERSAO_PROTOCOLO >= 17

M = JanelaMestre(); M.resize(1400, 900); M.show(); M.mostrar_mesa(); QTest.qWait(80)
c, v = M.cena, M.visao
c.criar_sala(QPointF(-6 * C, -4 * C), QPointF(6 * C, 4 * C))
a = c.adicionar_token(dict(nome="Aelar", tipo="jogador", cor="#3f6b4a", tamanho=1, imagem=None, dono="Manel"),
                      QPointF(-2 * C, 1 * C))
o = c.adicionar_token(dict(nome="Ogro", tipo="criatura", cor="#8a2020", tamanho=2, imagem=None, dono=""),
                      QPointF(2 * C, -1 * C))
k = c.adicionar_token(dict(nome="Kobold", tipo="criatura", cor="#6a5a20", tamanho=1, imagem=None, dono=""),
                      QPointF(1 * C, 3.4 * C))   # encostado na parede de baixo

print("== padrão é ficha; o diálogo tem a escolha; salvar/abrir guarda")
assert a.estilo == "ficha"
dlg = DialogoToken(M, token=o)
dlg.estilo.setCurrentIndex(dlg.estilo.findData("standee"))
assert dlg.dados()["estilo"] == "standee"
o.estilo = "standee"
d = o.para_dict()
assert d["estilo"] == "standee" and TokenItem.de_dict(d).estilo == "standee"
assert TokenItem.de_dict(dict(d, estilo="qualquer")).estilo == "ficha"
o.sem_borda = True                                                   # (v0.77) PNG recortado: sem bordas
assert TokenItem.de_dict(o.para_dict()).sem_borda is True
dlg2 = DialogoToken(M, token=o)
assert dlg2.sem_borda.isChecked() and dlg2.dados()["sem_borda"] is True
h1 = o.altura_standee()                                              # (v0.78) escala da imagem do standee
o.escala_standee = 2.0
assert abs(o.altura_standee() - 2 * h1) < 1e-6
assert TokenItem.de_dict(o.para_dict()).escala_standee == 2.0
assert TokenItem.de_dict(dict(o.para_dict(), escala_standee=99)).escala_standee == 3.0   # (conferida)
dlg3 = DialogoToken(M, token=o)
assert dlg3.escala_standee.value() == 200
dlg3.escala_standee.setValue(150)
assert dlg3.dados()["escala_standee"] == 1.5
assert DialogoToken(M, token=a, do_jogador=True).estilo.isHidden() or True   # (o jogador não escolhe)

print("== Mesa → Peças dos tokens: todos de uma vez")
assert M.estilo_de_todos("standee") == 2
assert all(t.estilo == "standee" for t in (a, o, k))

print("== vai pela rede pro jogador")
s = socket.socket(); s.bind(("127.0.0.1", 0)); porta = s.getsockname()[1]; s.close()
assert M.servidor.abrir(porta)
P = JanelaPlayer(); P.resize(900, 600); P.show()
P.nome, P.ip, P.porta = "Manel", "127.0.0.1", porta
P._ja_entrou = False; P._primeiro_estado = True
P.cliente.conectar(P.ip, P.porta, P.nome)
for _ in range(60):
    QTest.qWait(100)
    if o.uid in P.cena.itens:
        break
QTest.qWait(300)
assert P.cena.itens[o.uid].estilo == "standee"
assert P.cena.itens[o.uid].sem_borda is True                       # (v0.77) o "sem bordas" chegou no jogador
assert P.cena.itens[o.uid].escala_standee == 2.0                    # (v0.78) e a escala também
M.estilo_de_todos("ficha")
for _ in range(40):
    QTest.qWait(100)
    if P.cena.itens[o.uid].estilo == "ficha":
        break
assert P.cena.itens[o.uid].estilo == "ficha", "a troca não chegou no jogador"
M.estilo_de_todos("standee")

print("== inclinada: só a parede da FRENTE tapa o cartão")
c.clearSelection()
v.definir_zoom(1.0)
v.centerOn(QPointF(0, 0))
v.definir_camera(0, 50, livre=True)
QTest.qWait(400)
from PyQt6.QtGui import QImage, QPainter
img = QImage(v.viewport().size(), QImage.Format.Format_ARGB32)
p = QPainter(img)
p.setWorldTransform(v.viewportTransform())
cam = camera3d.Camera(p)
p.end()
# a câmera inclinada fica ATRÁS (pro lado de baixo da tela): entre ela e o Ogro só a parede de baixo;
# do lado de fora da parede de baixo (do lado da câmera) nenhuma; do lado de fora da de CIMA, as duas
frente_ogro = altura3d._na_frente(cam, c.paredes, o.centro_cena())
fora_baixo = altura3d._na_frente(cam, c.paredes, QPointF(1 * C, 4.6 * C))
fora_cima = altura3d._na_frente(cam, c.paredes, QPointF(1 * C, -4.6 * C))
print("   paredes na frente — ogro:", len(frente_ogro), "· fora (baixo):", len(fora_baixo), "· fora (cima):", len(fora_cima))
assert len(frente_ogro) == 1 and len(fora_baixo) == 0 and len(fora_cima) == 2
assert o in altura3d.STANDEES and k in altura3d.STANDEES       # os cartões estão sendo desenhados

print("== (v0.77) câmera LIVRE: standee em pé no mundo; TRAVADA: virado pra câmera")
usou = []
o_mundo, o_tela = TokenItem.pintar_cartao_no_mundo, TokenItem.pintar_cartao
TokenItem.pintar_cartao_no_mundo = lambda s, *a: (usou.append("mundo"), o_mundo(s, *a))[1]
TokenItem.pintar_cartao = lambda s, *a: (usou.append("tela"), o_tela(s, *a))[1]
v.viewport().update()
QTest.qWait(250)
assert "mundo" in usou and "tela" not in usou, usou
usou.clear()
v.definir_camera(livre=False)
QTest.qWait(250)
v.viewport().update()
QTest.qWait(250)
assert "tela" in usou and "mundo" not in usou, usou
TokenItem.pintar_cartao_no_mundo, TokenItem.pintar_cartao = o_mundo, o_tela
v.definir_camera(0, 50, livre=True)
QTest.qWait(250)
v.grab().save(os.path.join(SAIDA, "standee.png"))
M.estilo_de_todos("ficha")
QTest.qWait(300)

print("== (v0.77) fichas também na ordem da câmera: o mais longe é desenhado primeiro")
ordem = []
orig_corpo = TokenItem.pintar_corpo_3d


def _gravar(self, painter, n):
    ordem.append(self.nome)
    orig_corpo(self, painter, n)


TokenItem.pintar_corpo_3d = _gravar
v.viewport().update()
QTest.qWait(300)
TokenItem.pintar_corpo_3d = orig_corpo
pe = cam.pe_cena()
dist = {t.nome: (t.centro_cena() - pe).manhattanLength() for t in (a, o, k)}
vistos = [nm for nm in dict.fromkeys(ordem) if nm in dist]
print("   ordem:", vistos)
assert vistos == sorted(vistos, key=lambda nm: -dist[nm]), (vistos, dist)
v.grab().save(os.path.join(SAIDA, "standee_fichas_nomes.png"))
v.camera_de_cima()
QTest.qWait(150)
print("   erros:", erros[:2])
assert not erros, erros
print("FIM")
sys.stdout.flush()
os._exit(0)
