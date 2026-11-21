"""(v0.75) 👁 "Pelos olhos de…": botão direito no token → a câmera vai pra trás dele (por cima do ombro), baixa e
bem deitada, virada pra onde ele olha, e ACOMPANHA (anda/gira junto). O horizonte entra na tela: céu em cima e névoa
ao longe; o chão "visível" corta no horizonte. CORTE: pedaço de parede entre a câmera e o token não é desenhado.
Esc, arrastar a visão ou o clique duplo na bússola saem — e a câmera volta como estava."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

app = QApplication(sys.argv[:1])
from taverna import seguranca
erros = []
seguranca.registrar_erro = lambda t: erros.append(t)
from taverna.graficos import graficos
graficos().definir("alto")
from taverna.config import CELULA as C
from taverna.mesa import camera3d
from taverna.ui.janela_mestre import JanelaMestre

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")
M = JanelaMestre(); M.resize(1400, 900); M.show(); M.mostrar_mesa(); QTest.qWait(80)
c, v = M.cena, M.visao
c.criar_sala(QPointF(-8 * C, -6 * C), QPointF(0, 6 * C))
c.tipo_porta = "madeira"
c.colocar_porta(QPointF(0, 0))
heroi = c.adicionar_token(dict(nome="Aelar", tipo="jogador", cor="#3f6b4a", tamanho=1, imagem=None, dono="Manel"),
                          QPointF(-6 * C, 0))
heroi.direcao = 0.0
c.clearSelection()
v.definir_zoom(0.9)
v.definir_camera(20, 30, livre=True)
antes = (v.camera_livre, v._cam_giro, v._cam_incl, v._cam_escala)

print("== entra: atrás do token, virada pra onde ele olha, horizonte na tela")
v.ver_pelos_olhos(heroi)
assert v._cam_incl < camera3d.INCLINACAO_OLHOS - 5                  # (v0.80) entra deslizando, não pula
for _ in range(40):
    QTest.qWait(100)
    if v._cam_incl == camera3d.INCLINACAO_OLHOS:
        break
assert v.pelos_olhos() is heroi and v._cam_incl == camera3d.INCLINACAO_OLHOS
assert abs(((v._cam_giro - 270) + 180) % 360 - 180) < 1          # olhando pro leste = leste pra cima na tela
assert camera3d.altura_telas() == camera3d.ALTURA_OLHOS_TELAS
assert 0 < v._horizonte < v.viewport().height() * 0.4, v._horizonte
t = v.mapFromScene(heroi.centro_cena())
assert t.y() > v.viewport().height() * 0.55                        # o token fica embaixo (a câmera atrás dele)
porta = v.mapFromScene(QPointF(0, 0))
assert porta.y() < t.y()                                          # a porta, na frente dele, fica mais pra cima
v.grab().save(os.path.join(SAIDA, "pelos_olhos.png"))

print("== a parede de trás (entre a câmera e o token) é cortada")
from PyQt6.QtGui import QImage, QPainter
img = QImage(v.viewport().size(), QImage.Format.Format_ARGB32)
p = QPainter(img)
p.setWorldTransform(v.viewportTransform())
cam = camera3d.Camera(p)
p.end()
corte = camera3d._ESTADO.get("corte_y")
assert corte is not None
assert cam.projetar(QPointF(-8 * C, 0), 0).y() > corte             # a parede oeste (atrás) fica abaixo do corte
assert cam.projetar(QPointF(0, 2 * C), 0).y() < corte              # a parede da porta (na frente) fica acima

print("== acompanha: o token gira, a câmera gira junto")
heroi.direcao = 90.0   # olhando pro sul
for _ in range(60):    # (gira suave; sem placa de vídeo cada quadro demora mais)
    QTest.qWait(100)
    if abs(((v._cam_giro - 180) + 180) % 360 - 180) < 3:
        break
assert abs(((v._cam_giro - 180) + 180) % 360 - 180) < 3, v._cam_giro

print("== Esc sai e a câmera volta como estava")
QTest.keyClick(v, Qt.Key.Key_Escape)
QTest.qWait(100)
assert v.pelos_olhos() is None
assert (v.camera_livre, round(v._cam_giro), round(v._cam_incl)) == (antes[0], round(antes[1]), round(antes[2]))
assert camera3d.altura_telas() == camera3d.CAMERA_ALTURA_TELAS and camera3d._ESTADO.get("corte_y") is None

print("== o token sumiu da mesa: sai sozinho")
v.ver_pelos_olhos(heroi)
QTest.qWait(100)
c.remover_itens([heroi])
QTest.qWait(200)
assert v.pelos_olhos() is None
print("   erros:", erros[:2])
assert not erros, erros
print("FIM")
sys.stdout.flush()
os._exit(0)
