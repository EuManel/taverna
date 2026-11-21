"""(v0.63) 🌍 Mesa → Cidade → Mundo, etapa 2: marcador do grupo automático (um só com todos na mesma aba; um por
jogador, na cor do token, se separarem), VIAGEM (o mestre arrasta o marcador no mundo/cidade e vê a distância em
km/m; fica o rastro) e a régua (M) em cada nível na unidade dele."""
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
w = QTest.qWait
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")
pasta = tempfile.mkdtemp(prefix="taverna_viagem_")


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
esgoto = M._nova_cena_vazia("Esgoto")
M._registrar_cena(esgoto)
M.cenas.append(esgoto)
esgoto.criar_sala(QPointF(0, 0), QPointF(16 * C, 12 * C))
J = M.abrir_atlas()
cidade = J.importar("cidade", imagem("c.png", 1000, 800, "#6a7a50", [(QRectF(100, 100, 50, 40), "#8a5a3a")]), "Porto")
mundo = J.importar("mundo", imagem("m.png", 2000, 1000, "#2a4a6a", [(QRectF(500, 300, 40, 32), "#c0a060")]), "Norte")
J.atual = cidade
J._marcou(QRectF(100, 100, 50, 40), A.chave_da_cena(taverna))
J._marcou(QRectF(600, 500, 80, 60), A.chave_da_cena(esgoto))
J._tracou(QLineF(0, 0, 100, 0), 50)          # cidade: 100 px = 50 m
J.atual = mundo
J._marcou(QRectF(500, 300, 40, 32), cidade["id"])
J._tracou(QLineF(0, 0, 200, 0), 40)          # mundo: 200 px = 40 km
J.close()
camada = M.camada_atlas

print("== distâncias na unidade de cada nível")
assert A.Atlas.texto_distancia(mundo, 200) == "40 km", A.Atlas.texto_distancia(mundo, 200)
assert A.Atlas.texto_distancia(cidade, 60) == "30 m"
assert A.Atlas.texto_distancia(cidade, 3000) == "1,5 km"
assert "calibre" in A.Atlas.texto_distancia({"tipo": "cidade"}, 10)

print("== marcador do grupo")
aelar = taverna.adicionar_token({"nome": "Aelar", "tipo": "jogador", "cor": "#3f9b4a", "tamanho": 1, "dono": "Manel"},
                                QPointF(-2 * C, 0))
lyra = taverna.adicionar_token({"nome": "Lyra", "tipo": "jogador", "cor": "#8a3fbb", "tamanho": 1, "dono": "Bia"},
                               QPointF(2 * C, 0))
taverna.adicionar_token({"nome": "Orc", "tipo": "criatura", "cor": "#6b3f3f", "tamanho": 1}, QPointF(0, 2 * C))
camada.ir_para("cidade"); w(700)
ms = camada.marcadores()
print("  ", [(m["id"], m["nome"]) for m in ms])
assert len(ms) == 1 and ms[0]["id"] == "grupo"                       # criatura não conta
assert A.ret(cidade["lugares"][0]).contains(ms[0]["pos"])             # dentro da taverna, no mapa da cidade

print("== grupo separado: um marcador por jogador, na cor do token")
taverna.remover_itens([lyra])
lyra2 = esgoto.adicionar_token({"nome": "Lyra", "tipo": "jogador", "cor": "#8a3fbb", "tamanho": 1, "dono": "Bia"},
                               QPointF(8 * C, 6 * C))
ms = {m["id"]: m for m in camada.marcadores()}
print("  ", sorted(ms))
assert set(ms) == {"jog:Manel", "jog:Bia"} and ms["jog:Bia"]["cor"] == QColor("#8a3fbb")
assert A.ret(cidade["lugares"][1]).contains(ms["jog:Bia"]["pos"])
camada.ir_para("mundo"); w(700)
assert len(camada.marcadores()) == 2
assert all(A.ret(mundo["lugares"][0]).adjusted(-1, -1, 1, 1).contains(m["pos"]) for m in camada.marcadores())

print("== viagem: o mestre arrasta o grupo no mundo")
esgoto.remover_itens([lyra2])
taverna.adicionar_token({"nome": "Lyra", "tipo": "jogador", "cor": "#8a3fbb", "tamanho": 1, "dono": "Bia"},
                        QPointF(2 * C, 0))
camada.update(); w(50)
g = camada.marcadores()[0]
assert g["id"] == "grupo"
s = camada.M.map(g["pos"])
ini = QPoint(int(s.x()), int(s.y() - 16))
fim = ini + QPoint(150, 40)
QTest.mousePress(camada, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, ini)
for k in range(1, 11):
    QTest.mouseMove(camada, ini + (fim - ini) * (k / 10))
    w(10)
camada.grab().save(os.path.join(SAIDA, "atlas_viagem.png"))
QTest.mouseRelease(camada, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, fim)
g2 = camada.marcadores()[0]
andou = QLineF(g["pos"], g2["pos"]).length()
print("   andou", round(andou, 1), "px do mundo =", A.Atlas.texto_distancia(mundo, andou),
      "· rastro:", len(M.atlas.rastros[mundo["id"]]), "pontos")
assert andou > 20 and len(M.atlas.rastros[mundo["id"]]) >= 3
assert M.cena.modificada
assert M.atlas.posicao_viagem(mundo["id"], "grupo", g["base"]) is not None

print("== régua (M) no mundo")
camada.setFocus()
QTest.keyPress(camada, Qt.Key.Key_M)
QTest.mousePress(camada, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(300, 300))
QTest.mouseMove(camada, QPoint(500, 300))
assert camada._regua is not None
dist_px = QLineF(camada._regua[0], camada._regua[1]).length()
print("   régua:", A.Atlas.texto_distancia(mundo, dist_px))
assert abs(dist_px - 200 / camada.M.m11()) < 2
QTest.mouseRelease(camada, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(500, 300))
QTest.keyRelease(camada, Qt.Key.Key_M)
assert camada._regua is None

print("== o grupo muda de aba: volta pro automático")
taverna.remover_itens([i for i in taverna.itens_do_usuario() if getattr(i, "nome", "") == "Aelar"])
esgoto.adicionar_token({"nome": "Aelar", "tipo": "jogador", "cor": "#3f9b4a", "tamanho": 1, "dono": "Manel"},
                       QPointF(4 * C, 4 * C))
ms = camada.marcadores()
assert len(ms) == 2 and all(m["pos"] == m["auto"] for m in ms)

print("== salva a viagem e o rastro")
de_novo = A.Atlas(M.atlas.para_dict())
assert de_novo.rastros[mundo["id"]] == M.atlas.rastros[mundo["id"]] and "grupo" in de_novo.viagem[mundo["id"]]
M.atlas.voltar_pro_automatico(mundo["id"], "grupo")
assert "grupo" not in M.atlas.viagem[mundo["id"]]
print("FIM")
sys.stdout.flush()
os._exit(0)
