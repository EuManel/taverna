"""(v0.62) 🌍 Mesa → Cidade → Mundo, etapa 1 (mestre): montar (imagens, lugares, escala), zoom contínuo com mistura
entre os níveis, descer pra outra aba pelo zoom, botões Mesa · Cidade · Mundo, salvar na aventura e no pacote."""
import json
import math
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QLineF, QPointF, QRectF
from PyQt6.QtGui import QColor, QImage, QPainter
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

app = QApplication(sys.argv)
from taverna.config import CELULA as C
from taverna.mesa import atlas as A
from taverna.ui.janela_mestre import JanelaMestre
w = QTest.qWait
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")

print("== contas")
T = A.encaixe(QRectF(100, 100, 50, 40), QRectF(-320, -256, 640, 512))
assert (T.map(QPointF(125, 120)) - QPointF(0, 0)).manhattanLength() < 1e-6     # centro no centro
assert abs(T.m11() - 12.8) < 1e-6
assert A.mistura(1.2) == 0 and A.mistura(0.6) == 0 and A.mistura(0.3) == 1 and 0 < A.mistura(0.42) < 1

pasta = tempfile.mkdtemp(prefix="taverna_atlas_")


def imagem(caminho, w_, h_, cor, marcas=()):
    img = QImage(w_, h_, QImage.Format.Format_RGB32)
    img.fill(QColor(cor))
    p = QPainter(img)
    for r, c in marcas:
        p.fillRect(r, QColor(c))
    p.end()
    img.save(caminho)
    return caminho


cid_png = imagem(os.path.join(pasta, "cidade.png"), 1000, 800, "#6a7a50",
                 [(QRectF(100, 100, 50, 40), "#8a5a3a"), (QRectF(600, 500, 80, 60), "#3a3a4a")])
mun_png = imagem(os.path.join(pasta, "mundo.png"), 2000, 1000, "#2a4a6a", [(QRectF(500, 300, 40, 32), "#c0a060")])

M = JanelaMestre(); M.resize(1200, 800); M.show(); M.mostrar_mesa(); w(50)
taverna = M.cena
taverna.nome_aba = "Taverna"
taverna.criar_sala(QPointF(-5 * C, -4 * C), QPointF(5 * C, 4 * C))
esgoto = M._nova_cena_vazia("Esgoto")
M._registrar_cena(esgoto)
M.cenas.append(esgoto)
esgoto.criar_sala(QPointF(0, 0), QPointF(16 * C, 12 * C))

print("== montar")
J = M.abrir_atlas()
cidade = J.importar("cidade", cid_png, "Porto Velho")
mundo = J.importar("mundo", mun_png, "Terras do Norte")
J.atual = cidade
assert [o[0] for o in J.opcoes_de_alvo()] == ["Taverna", "Esgoto"]
J._marcou(QRectF(100, 100, 50, 40), A.chave_da_cena(taverna))
J._marcou(QRectF(600, 500, 80, 60), A.chave_da_cena(esgoto))
J._tracou(QLineF(0, 0, 100, 0), 50)                       # 100 px = 50 m
J.atual = mundo
J._marcou(QRectF(500, 300, 40, 32), cidade["id"])
J._tracou(QLineF(0, 0, 200, 0), 40)                       # 200 px = 40 km
assert abs(A.Atlas.distancia(cidade, 10) - 5) < 1e-9 and abs(A.Atlas.distancia(mundo, 10) - 2) < 1e-9
assert M.atlas.lugar_da_cena(taverna)[0] is cidade and M.atlas.lugar_da_cidade(cidade) is not None
J.atual = cidade
J.recarregar(manter=cidade["id"])
w(100)
J.grab().save(os.path.join(SAIDA, "atlas_montagem.png"))
J.close()

camada = M.camada_atlas
V = M.visao
w(100)
centro = QPointF(V.viewport().width() / 2, V.viewport().height() / 2)

print("== zoom out na mesa: a cidade vai aparecendo")
V.enquadrar_tudo(); w(50)
print("   enquadrado: t =", round(camada.t, 3))
assert camada.quadro == "mesa" and camada.t == 0           # "enquadrar tudo": nada da cidade ainda
ts = []
for _ in range(200):
    V._escalar_em(V.escala / 1.08, centro)
    ts.append(round(camada.t, 2))
    if 0.45 < camada.t < 0.6 and not os.path.exists(os.path.join(SAIDA, "atlas_mistura.png")):
        M.visao.grab().save(os.path.join(SAIDA, "atlas_mistura.png"))
    if camada.quadro != "mesa":
        break
print("   t:", ts[:3], "…", ts[-4:])
assert camada.quadro == "cidade" and any(0 < t < 1 for t in ts)
assert camada.cidade is cidade
M.visao.grab().save(os.path.join(SAIDA, "atlas_cidade.png"))

print("== mais zoom out: o mundo")
for _ in range(200):
    camada._escalar(1 / 1.1, centro)
    if camada.quadro == "mundo":
        break
assert camada.quadro == "mundo"
for _ in range(100):
    camada._escalar(1 / 1.1, centro)                       # para quando o mundo inteiro cabe
a = M.atlas.area(mundo)
fr = A.tamanho_na_tela(a, camada.M, camada.width(), camada.height())
assert abs(fr - 1) < 0.02, fr
r_mundo = camada.M.mapRect(a)
assert abs(r_mundo.center().x() - camada.width() / 2) < 2 and abs(r_mundo.center().y() - camada.height() / 2) < 2
M.visao.grab().save(os.path.join(SAIDA, "atlas_mundo.png"))

print("== zoom in na cidade (no mundo) → cidade; no esgoto → aba Esgoto")
alvo_w = camada.M.map(A.ret(mundo["lugares"][0]).center())
for _ in range(200):
    camada._escalar(1.1, alvo_w)
    alvo_w = camada.M.map(A.ret(mundo["lugares"][0]).center())
    if camada.quadro == "cidade":
        break
assert camada.quadro == "cidade" and camada.cidade is cidade
lugar_esg = next(l for l in cidade["lugares"] if l["alvo"] == A.chave_da_cena(esgoto))
for _ in range(300):
    p = camada.M.map(A.ret(lugar_esg).center())
    camada._escalar(1.1, p)
    if camada.quadro == "mesa":
        break
assert camada.quadro == "mesa" and M.cena is esgoto, (camada.quadro, M.cena.nome_aba)
print("   desceu na aba:", M.cena.nome_aba, "· mistura", round(camada.t, 2))
assert 0 < camada.t < 1                                    # chegou no meio da mistura (contínuo)
chao = esgoto.chao_caminho().boundingRect()
tela = V.viewportTransform().mapRect(chao)
assert tela.contains(centro) or tela.intersects(QRectF(centro.x() - 50, centro.y() - 50, 100, 100))

print("== botões Mesa · Cidade · Mundo")
camada.ir_para("cidade"); w(700)
assert camada.quadro == "cidade" and camada.botoes.botoes["cidade"].isChecked()
camada.ir_para("mundo"); w(700)
assert camada.quadro == "mundo"
camada.ir_para("mesa"); w(1200)
assert camada.quadro == "mesa" and M.cena is esgoto
print("   voltou pra mesa; t =", round(camada.t, 2))

print("== salva na aventura e vai no pacote")
from taverna.mesa.arquivo import dados_aventura
dados = dados_aventura(M.cenas, "Teste", "medieval", 0, 0, [], [], M.atlas.para_dict())
assert dados["atlas"]["mundo"]["nome"] == "Terras do Norte" and len(dados["atlas"]["cidades"]) == 1
from taverna.mesa import pacote
arq = os.path.join(pasta, "a.tavernapack")
r = pacote.exportar(arq, dados)
with zipfile.ZipFile(arq) as z:
    av = json.loads(z.read("aventura.json"))
    assert av["atlas"]["mundo"]["imagem"].startswith(pacote.PREFIXO)
    assert sum(1 for n in z.namelist() if n.startswith("imagens/Mapas/")) == 2
lido = pacote.ler(arq)
assert A.Atlas(lido["aventura"]["atlas"]).pixmap(A.Atlas(lido["aventura"]["atlas"]).mundo).width() == 2000
M._definir_atlas({})
assert camada.quadro == "mesa" and not camada.botoes.isVisible()
print("FIM")
sys.stdout.flush()
os._exit(0)
