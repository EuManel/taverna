"""(v0.64) 🌍 Mesa → Cidade → Mundo, etapa 3: NÉVOA da cidade e do mundo (o grupo revela em volta de onde está e por
onde viaja; o mestre revela/cobre com pincel) e os JOGADORES vendo pela rede — só os pedaços revelados da imagem
saem do PC do mestre; o jogador sobe da aba dele dando zoom out e só olha (não arrasta, não pinta)."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QLineF, QPoint, QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QPainter
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

app = QApplication(sys.argv)
from taverna.config import CELULA as C
from taverna.mesa import atlas as A
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
w = QTest.qWait
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")
pasta = tempfile.mkdtemp(prefix="taverna_atlas_rede_")


def esperar(cond, ms=6000):
    for _ in range(ms // 50):
        if cond():
            return True
        w(50)
    return cond()


def imagem(nome, w_, h_, cor, marcas=()):
    img = QImage(w_, h_, QImage.Format.Format_RGB32)
    img.fill(QColor(cor))
    p = QPainter(img)
    for r, c in marcas:
        p.fillRect(r, QColor(c))
    p.end()
    caminho = os.path.join(pasta, nome)
    img.save(caminho)
    return caminho


M = JanelaMestre(); M.resize(1200, 800); M.show(); M.mostrar_mesa(); w(50)
taverna = M.cena
taverna.nome_aba = "Taverna"
taverna.criar_sala(QPointF(-5 * C, -4 * C), QPointF(5 * C, 4 * C))
J = M.abrir_atlas()
cidade = J.importar("cidade", imagem("c.png", 1000, 800, "#6a7a50", [(QRectF(100, 100, 50, 40), "#8a5a3a"),
                                                                       (QRectF(850, 650, 100, 100), "#d02020")]), "Porto")
mundo = J.importar("mundo", imagem("m.png", 2000, 1000, "#2a4a6a", [(QRectF(500, 300, 40, 32), "#c0a060")]), "Norte")
J.atual = cidade
J._marcou(QRectF(100, 100, 50, 40), A.chave_da_cena(taverna))
J._tracou(QLineF(0, 0, 100, 0), 50)
J.atual = mundo
J._marcou(QRectF(500, 300, 40, 32), cidade["id"])
J.close()
camada = M.camada_atlas
atlas = M.atlas

print("== névoa começa cobrindo tudo; o grupo revela em volta dele")
assert atlas.nevoa_ligada(cidade) and atlas.revelado(cidade, QPointF(125, 120)) == 0
taverna.adicionar_token({"nome": "Aelar", "tipo": "jogador", "cor": "#3f9b4a", "tamanho": 1, "dono": "Manel"},
                        QPointF(0, 0))
assert esperar(lambda: atlas.revelado(cidade, QPointF(125, 120)) > 200, 3000)
assert atlas.revelado(cidade, QPointF(900, 700)) == 0                  # longe do grupo: coberto
assert atlas.revelado(mundo, QPointF(520, 316)) > 200                  # no mundo, em volta da cidade
assert atlas.revelado(mundo, QPointF(1800, 900)) == 0

print("== o jogador conecta")
assert M.servidor.abrir(7851)
P = JanelaPlayer(); P.resize(1100, 750); P.show()
P.nome, P.ip, P.porta = "Manel", "127.0.0.1", 7851
P._ja_entrou = False
P._primeiro_estado = True
P.cliente.conectar(P.ip, P.porta, P.nome)
assert esperar(lambda: getattr(P, "atlas_ponte", None) is not None and P.atlas_ponte.atlas.cidades)
ponte = P.atlas_ponte
pa = ponte.atlas
assert pa.cidades[0]["id"] == cidade["id"] and pa.mundo["id"] == mundo["id"]
assert pa.chao == taverna.chao_caminho().boundingRect()
assert esperar(lambda: pa.marcadores_de("cidade") and pa._telas.get(cidade["id"]) is not None)
assert pa.marcadores_de("cidade")[0]["nome"] == "Grupo"


def pixel(nivel_id, x, y):
    t = pa._telas.get(nivel_id)
    return t.pixelColor(x, y) if t is not None else QColor(0, 0, 0, 0)


assert esperar(lambda: pixel(cidade["id"], 125, 120).alpha() > 200)
c = pixel(cidade["id"], 125, 120)
print("   revelado no jogador:", c.name(), c.alpha(), "· coberto:", pixel(cidade["id"], 900, 700).alpha())
assert abs(c.red() - 0x8a) < 6 and abs(c.green() - 0x5a) < 6
assert pixel(cidade["id"], 900, 700).alpha() == 0                    # a névoa NÃO saiu do mestre
con = next(x for x in M.servidor.conexoes if x.nome == "Manel")
assert (cidade["id"], 768, 512) not in con.atlas_pedacos               # o pedaço coberto nem foi mandado
total = len(range(0, 1000, 256)) * len(range(0, 800, 256))
mandados = sum(1 for k, v in con.atlas_pedacos.items() if k[0] == cidade["id"] and not v.startswith("vazio"))
print(f"   pedaços da cidade mandados: {mandados} de {total}")
assert 0 < mandados < total

print("== o mestre revela tudo / cobre tudo")
atlas.revelar_tudo(cidade, True)
M.atlas_editado()
assert esperar(lambda: pixel(cidade["id"], 900, 700).alpha() > 200)
assert pixel(cidade["id"], 900, 700).red() > 180                       # o quadrado vermelho apareceu
atlas.revelar_tudo(cidade, False)
M.atlas_editado()
assert esperar(lambda: pixel(cidade["id"], 900, 700).alpha() == 0)   # cobriu (o pedaço some no jogador)
assert esperar(lambda: pixel(cidade["id"], 125, 120).alpha() > 200)  # …mas onde o grupo ESTÁ revela de novo
# marcador dentro da névoa não vai pro jogador
atlas.mover_marcador(cidade["id"], "grupo", A.chave_da_cena(taverna), QPointF(900, 700))
assert not M.atlas_rede.dados_do_jogador("Manel")[0]["marcadores"]["cidade"]
atlas.voltar_pro_automatico(cidade["id"], "grupo")
assert M.atlas_rede.dados_do_jogador("Manel")[0]["marcadores"]["cidade"]

print("== pincel do mestre")
camada.ir_para("cidade"); w(700)
camada._definir_pincel("revelar")
alvo = camada.M.map(QPointF(500, 400))
QTest.mousePress(camada, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, alvo.toPoint())
QTest.mouseMove(camada, (alvo + QPointF(30, 0)).toPoint())
QTest.mouseRelease(camada, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, (alvo + QPointF(30, 0)).toPoint())
assert atlas.revelado(cidade, QPointF(500, 400)) > 200
camada.grab().save(os.path.join(SAIDA, "atlas_nevoa_mestre.png"))
camada._definir_pincel(None)
camada.ir_para("mesa"); w(1200)
assert esperar(lambda: pixel(cidade["id"], 500, 400).alpha() > 200)

print("== o jogador sobe dando zoom out (e só olha)")
pc = ponte.camada
V = P.visao
P.mostrar_mesa() if hasattr(P, "mostrar_mesa") else None
w(200)
centro = QPointF(V.viewport().width() / 2, V.viewport().height() / 2)
V.enquadrar_tudo(); w(50)
for _ in range(200):
    V._escalar_em(V.escala / 1.08, centro)
    if pc.quadro != "mesa":
        break
print("   jogador está em:", pc.quadro)
assert pc.quadro == "cidade"
pc.ir_para("mundo"); w(700)
assert pc.quadro == "mundo"
pc.ir_para("cidade"); w(700)
foto = pc.grab()
foto.save(os.path.join(SAIDA, "atlas_nevoa_jogador.png"))
# (v0.83) o coberto não é mais o escuro liso: tem a névoa desenhada do tema (aqui no Alto/Médio)
from taverna.config import COR_FUNDO_MESA
from taverna.graficos import nivel as nivel_graficos
coberto = pc.M.map(QPointF(900, 700)).toPoint()
if nivel_graficos() >= 1:
    assert foto.toImage().pixelColor(coberto).name() != QColor(COR_FUNDO_MESA).name()
antes = dict(atlas.viagem)
m = pc.marcadores()[0]
s = pc.M.map(m["pos"])
QTest.mousePress(pc, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(int(s.x()), int(s.y() - 16)))
QTest.mouseMove(pc, QPoint(int(s.x()) + 120, int(s.y())))
QTest.mouseRelease(pc, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(int(s.x()) + 120, int(s.y())))
assert atlas.viagem == antes and pc._pincel is None                     # jogador não viaja nem pinta
pc.ir_para("mesa"); w(1200)
assert pc.quadro == "mesa"

print("== a névoa fica salva")
de_novo = A.Atlas(atlas.para_dict())
assert de_novo.revelado(de_novo.nivel(cidade["id"]), QPointF(500, 400)) > 200
assert de_novo.revelado(de_novo.nivel(cidade["id"]), QPointF(950, 50)) == 0
print("FIM")
sys.stdout.flush()
os._exit(0)
