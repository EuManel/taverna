"""(v0.74) 🎨 Meus dados: cada pessoa escolhe material e cores dos SEUS dados 3D; a escolha vai junto com a rolagem
(campo "dv", protocolo 18) e todo mundo vê os dados de quem rolou do jeito dele. Sem escolha = do tema."""
import os
import socket
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

app = QApplication(sys.argv[:1])
_INI = os.path.join(tempfile.mkdtemp(), "geral.ini")   # preferências num ARQUIVO de teste (nunca nas reais do PC)
from taverna import seguranca
erros = []
seguranca.registrar_erro = lambda t: erros.append(t)
from taverna.dados3d import visual
visual._config = lambda: QSettings(_INI, QSettings.Format.IniFormat)
from taverna.dados3d.cena3d import Rolagem
from taverna.rede.protocolo import VERSAO_PROTOCOLO

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")
assert VERSAO_PROTOCOLO >= 18

print("== limpar: o que chega da rede é conferido")
assert visual.limpar(None) is None and visual.limpar({"m": "tema"}) is None
assert visual.limpar({"m": "lava-de-hacker"}) is None
v = visual.limpar({"m": "gema", "c": "#1e8a3a", "n": "nada"})
assert (v["m"], v["c"], v["n"], v["t"]) == ("gema", "#1e8a3a", visual.MATERIAIS["gema"][5], True), v
x = visual.limpar({"m": "pedra", "t": True, "b": 7})          # translúcido em qualquer material; brilho 0–1
assert x["t"] is True and x["b"] == 1.0
assert visual.limpar({"m": "ouro"})["t"] is False and visual.limpar({"m": "ouro"})["b"] == 1.0

print("== resolver: com escolha usa a do jogador; sem, a do tema")
corpo, num, brilho, gema, desg, metal = visual.resolver(v, "medieval")
assert corpo.name() == "#1e8a3a" and gema is True and desg == "magico" and not metal
assert visual.resolver({"m": "ouro"}, "medieval")[5] is True        # metal: brilho colorido
from taverna.dados3d.cena3d import textura_desgaste
for m in ("pedra", "marmore", "madeira", "ferro", "ouro"):          # cada material com a sua textura
    d = visual.MATERIAIS[m][3]
    assert d and textura_desgaste(d) is not None, m
corpo_t, *_r = visual.resolver(None, "futurista")
assert corpo_t.name() == "#18b8e8"
rol = Rolagem({"fisicos": [{"lados": 20, "valor": 7}], "semente": 3, "dv": v}, 800, 500, "medieval", "Georgia")
assert rol.corpo.name() == "#1e8a3a" and rol.desgaste == "magico"

print("== guardar/ler (preferência deste PC)")
assert visual.meus_dados() is None
visual.guardar({"m": "metal", "c": "#b8b8c0"})
assert visual.meus_dados()["c"] == "#b8b8c0" and visual.meus_dados()["m"] == "metal"

print("== janela Meus dados: prévia e OK")
from taverna.ui.dialogo_meus_dados import DialogoMeusDados, previa
img = previa(v, "medieval", "Georgia")
assert not img.isNull() and img.width() > 100
d = DialogoMeusDados()
d.material.setCurrentIndex(d.material.findData("vidro"))
assert d.visual()["m"] == "vidro" and d.visual()["c"] == visual.MATERIAIS["vidro"][4] and d.translucido.isChecked()
d.material.setCurrentIndex(d.material.findData("madeira"))
assert not d.translucido.isChecked() and d.brilho.value() == 25
d.translucido.setChecked(True)
assert d.visual()["t"] is True and d.visual()["m"] == "madeira"
d.material.setCurrentIndex(d.material.findData("vidro"))
d.grab().save(os.path.join(SAIDA, "meus_dados.png"))
d._ok()
assert visual.meus_dados()["m"] == "vidro"

print("== pela rede: o jogador rola com os dados dele, o mestre recebe o visual")
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
s = socket.socket(); s.bind(("127.0.0.1", 0)); porta = s.getsockname()[1]; s.close()
M = JanelaMestre(); M.resize(900, 600); M.show(); M.mostrar_mesa(); QTest.qWait(80)
recebidas = []
M.servidor.rolagem.connect(recebidas.append)
assert M.servidor.abrir(porta)
P = JanelaPlayer(); P.resize(900, 600); P.show()
P.nome, P.ip, P.porta = "Lia", "127.0.0.1", porta
P._ja_entrou = False; P._primeiro_estado = True
P.cliente.conectar(P.ip, P.porta, P.nome)
QTest.qWait(1200)
visual.guardar({"m": "gema", "c": "#aa2244"})
P.cliente.rolar("1d20")
for _ in range(40):
    QTest.qWait(100)
    if recebidas:
        break
assert recebidas and recebidas[-1]["dv"]["m"] == "gema" and recebidas[-1]["dv"]["c"] == "#aa2244", recebidas
r_m = M.servidor.rolar_mestre("1d6")
assert r_m["dv"]["m"] == "gema"           # (mesmo PC no teste: a mesma preferência)
print("   erros:", erros[:2])
assert not erros, erros
print("FIM")
sys.stdout.flush()
os._exit(0)
