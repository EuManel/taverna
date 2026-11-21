"""(v0.60) Importar mapa Universal VTT (.dd2vtt/.uvtt/.df2vtt): imagem na escala certa (1 quadrado = 1,5 m
padrão), paredes de pedra, portas (abrem o vão na parede; aberta/fechada como no arquivo) e luzes.
O arquivo de exemplo é gerado aqui mesmo (nada de mapa de terceiros)."""
import base64
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QBuffer, QIODevice, QPointF
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

app = QApplication(sys.argv)
from taverna.config import CELULA as C
from taverna.mesa import uvtt
from taverna.mesa.luzes import LuzItem
from taverna.mesa.mapa import MapaItem
from taverna.mesa.portas import PortaItem
from taverna.ui.janela_mestre import JanelaMestre

# ---- o arquivo de exemplo: 10 x 8 quadrados, 50 px por quadrado, uma sala com 2 portas e 1 luz
img = QImage(500, 400, QImage.Format.Format_RGB32)
img.fill(QColor("#6a5a48"))
buf = QBuffer()
buf.open(QIODevice.OpenModeFlag.WriteOnly)
img.save(buf, "PNG")
P = lambda x, y: {"x": x, "y": y}
dd = {
    "format": 0.3,
    "resolution": {"map_origin": P(0, 0), "map_size": P(10, 8), "pixels_per_grid": 50},
    # a sala: a parede passa por cima das portas (o importador abre o vão)
    "line_of_sight": [[P(2, 2), P(8, 2), P(8, 6), P(2, 6), P(2, 2)]],
    "objects_line_of_sight": [[P(5, 3.5), P(5.5, 3.5)]],
    "portals": [{"position": P(4.5, 2), "bounds": [P(4, 2), P(5, 2)], "rotation": 0, "closed": True, "freestanding": False},
                {"position": P(4.5, 6), "bounds": [P(4, 6), P(5, 6)], "rotation": 0, "closed": False, "freestanding": False}],
    "lights": [{"position": P(5, 4), "range": 4, "intensity": 1, "color": "ffff8800", "shadows": True}],
    "environment": {"baked_lighting": True, "ambient_light": "ffffffff"},
    "image": base64.b64encode(bytes(buf.data())).decode("ascii"),
}
pasta = tempfile.mkdtemp(prefix="taverna_uvtt_")
caminho = os.path.join(pasta, "Cripta de teste.dd2vtt")
with open(caminho, "w", encoding="utf-8") as f:
    json.dump(dd, f)

# ---- leitura (em quadrados, origem descontada)
d = uvtt.ler(caminho)
assert d["tamanho"] == (10, 8) and len(d["paredes"]) == 5 and len(d["portas"]) == 2 and len(d["luzes"]) == 1
assert d["luzes"][0]["cor"] == "#ff8800"
d2 = uvtt.ler(dict(dd, resolution={"map_origin": P(-3, 1), "map_size": P(10, 8), "pixels_per_grid": 50}))
assert d2["paredes"][0][0] == (5, 1)                         # (2,2) com origem (-3,1) → (5,1)
try:
    uvtt.ler(b'{"ola": 1}')
    raise AssertionError("devia recusar")
except uvtt.ErroUVTT:
    pass
print("leitura ok")

# ---- importar na janela do mestre (aba nova, 1,5 m, pedra)
M = JanelaMestre(); M.resize(1200, 800); M.show(); M.mostrar_mesa(); QTest.qWait(50)
abas_antes = len(M.cenas)
r = M.importar_uvtt(caminho, {"metros": 1.5, "material": "pedra", "aba_nova": True})
assert r and len(M.cenas) == abas_antes + 1 and M.cena.nome_aba == "Cripta de teste"
cena = M.cena
mapas = [i for i in cena.itens_do_usuario() if isinstance(i, MapaItem)]
assert len(mapas) == 1 and abs(mapas[0].largura_m - 15) < 1e-6 and abs(mapas[0].altura_m - 12) < 1e-6
x0, y0 = mapas[0].scenePos().x(), mapas[0].scenePos().y()
assert x0 % C == 0 and y0 % C == 0                           # gruda no grid do Taverna
segs = cena.paredes.segmentos
assert all(s["m"] == "pedra" for s in segs.values())
# 4 lados + o objeto; os lados de cima e de baixo foram cortados pelas portas → 7 trechos
print("paredes:", len(segs))
assert len(segs) == 7, len(segs)
k = 1.5 * C
cantos = {tuple(s["a"]) for s in segs.values()} | {tuple(s["b"]) for s in segs.values()}
assert (round(x0 + 2 * k, 1), round(y0 + 2 * k, 1)) in cantos
portas = [i for i in cena.camada_por_tipo("paredes").itens() if isinstance(i, PortaItem)]
assert len(portas) == 2 and all(abs(p.largura_m - 1.5) < 0.01 for p in portas)
assert sorted(p.aberta for p in portas) == [False, True]
# nenhum trecho de parede passa por dentro do vão da porta fechada
pf = next(p for p in portas if not p.aberta)
for s in segs.values():
    if abs(s["a"][1] - pf.scenePos().y()) < 1 and abs(s["b"][1] - pf.scenePos().y()) < 1:
        lo, hi = sorted((s["a"][0], s["b"][0]))
        assert not (lo < pf.scenePos().x() < hi), "parede atravessando a porta"
luzes = [i for i in cena.camada_por_tipo("luzes").itens() if isinstance(i, LuzItem)]
assert len(luzes) == 1 and abs(luzes[0].raio_fraco - 6) < 1e-6 and luzes[0].cor.name() == "#ff8800"
assert abs(luzes[0].scenePos().x() - (x0 + 5 * k)) < 0.5
print(f"importado: {r['paredes']} paredes, {r['portas']} portas, {r['luzes']} luzes")

# ---- 1 m por quadrado, na aba atual, outro material
r2 = M.importar_uvtt(caminho, {"metros": 1.0, "material": "tijolo", "aba_nova": False})
assert len(M.cenas) == abas_antes + 1
assert abs(r2["mapa"].largura_m - 10) < 1e-6
assert sum(1 for s in M.cena.paredes.segmentos.values() if s["m"] == "tijolo") == 7

# ---- salva e abre de novo (vai no arquivo .taverna como qualquer mapa)
from taverna.mesa.arquivo import dados_da_cena
dados = dados_da_cena(cena)
assert any(i.get("classe") == "porta" for c in dados["camadas"] for i in c.get("itens", []))

# ---- o diálogo abre
from taverna.ui.dialogo_uvtt import DialogoUVTT
dlg = DialogoUVTT(M, "Cripta de teste", d)
assert dlg.metros() == 1.5 and dlg.material.currentData() == "pedra" and dlg.aba_nova.isChecked()
dlg.escala.setCurrentIndex(2)
dlg.outro.setValue(2.5)
assert dlg.metros() == 2.5
M.visao.grab().save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida", "uvtt_importado.png"))
print("FIM")
sys.stdout.flush()
os._exit(0)
