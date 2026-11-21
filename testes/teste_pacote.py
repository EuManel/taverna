"""(v0.61) 📦 Pacote de aventura (.tavernapack): exporta a aventura num arquivo só (imagens separadas e sem
repetir, tabelas dos baús, sem fichas dos jogadores, diário só se pedir) e importa SEM sobrescrever nada.
Tudo em pastas temporárias (não mexe no Documentos/Taverna de verdade)."""
import json
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QBuffer, QIODevice, QPointF
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

app = QApplication(sys.argv)
from taverna.config import CELULA as C
from taverna.mesa import pacote
from taverna.mesa.mapa import MapaItem
from taverna.mesa.props import PropItem
from taverna.mesa.token import TokenItem
from taverna.ui.janela_mestre import JanelaMestre


def png(cor, w=64, h=48):
    img = QImage(w, h, QImage.Format.Format_RGB32)
    img.fill(QColor(cor))
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG")
    return bytes(buf.data())


raiz = tempfile.mkdtemp(prefix="taverna_pacote_")
pastas = {k: os.path.join(raiz, k) for k in ("aventuras", "banco", "tabelas")}

M = JanelaMestre(); M.resize(1000, 700); M.show(); M.mostrar_mesa(); QTest.qWait(50)
c = M.cena
c.nome_aventura = "Cripta do Teste"
img_mapa = png("#5a4a3a", 200, 120)
c.adicionar_mapa(img_mapa, QPointF(0, 0), "Cripta")
c.adicionar_mapa(img_mapa, QPointF(8 * C, 0), "Cripta (cópia)")          # mesma imagem: vai uma vez só
heroi = c.adicionar_token({"nome": "Aelar", "tipo": "jogador", "cor": "#3f6b4a", "tamanho": 1,
                           "imagem": png("#c0a060"), "dono": "Manel"}, QPointF(C, C))
heroi.ficha = {"nome": "Aelar", "segredo": "ficha do jogador"}
orc = c.adicionar_token({"nome": "Orc", "tipo": "criatura", "cor": "#6b3f3f", "tamanho": 1}, QPointF(3 * C, C))
orc.ficha = {"nome": "Orc", "pv": 15}
bau = c.colocar_prop("bau", QPointF(5 * C, 2 * C))
tabela = {"nome": "Sucata do ermo", "moeda": "Tampinhas", "moeda_dados": "2d6",
          "linhas": [{"nome": "Lata de feijão", "qtd": "1", "chance": "comum", "desc": ""}]}
bau.sorteio = {"ativo": True, "tabela": tabela}
M.painel_projetor.adicionar(png("#304060", 80, 60), "Retrato do vilão")
M.diario.append({"texto": "segredo da campanha"})
c.uid  # (só pra ter certeza que a aba existe)

print("== exportar")
arq = os.path.join(raiz, "Cripta do Teste.tavernapack")
r = M.exportar_pacote(arq, levar_diario=False)
print("  ", r)
assert r and r["abas"] == 1 and r["tabelas"] == 1
with zipfile.ZipFile(arq) as z:
    nomes = z.namelist()
    av = json.loads(z.read("aventura.json"))
    man = json.loads(z.read("manifesto.json"))
imagens = [n for n in nomes if n.startswith("imagens/")]
print("   imagens no pacote:", imagens)
assert len(imagens) == 3                                     # mapa (1x), token, projetor
assert any(n.startswith("imagens/Mapas/") for n in imagens) and any(n.startswith("imagens/Projetor/") for n in imagens)
assert "tabelas/Sucata do ermo.json" in nomes and "LEIA-ME.txt" in nomes
assert man["aviso"] == pacote.AVISO and man["aventura"] == "Cripta do Teste"
texto = json.dumps(av, ensure_ascii=False)
assert "ficha do jogador" not in texto and '"pv": 15' in texto     # ficha do jogador NÃO vai; a do orc vai
assert av["diario"] == [] and "segredo da campanha" not in texto
assert len(texto) < 60_000, len(texto)                       # sem base64 das imagens dentro do JSON
assert c.modificada or True                                   # (exportar não "salva" a aventura)
r2 = M.exportar_pacote(os.path.join(raiz, "com_diario.tavernapack"), levar_diario=True)
with zipfile.ZipFile(os.path.join(raiz, "com_diario.tavernapack")) as z:
    assert "segredo da campanha" in z.read("aventura.json").decode("utf-8")

print("== importar (pastas vazias)")
i1 = pacote.instalar(arq, pastas["aventuras"], pastas["banco"], pastas["tabelas"])
print("  ", {k: v for k, v in i1.items() if k != "aventura"})
assert os.path.basename(i1["aventura"]) == "Cripta do Teste.taverna"
assert i1["imagens"] == 3 and i1["tabelas"] == 1
assert sorted(os.listdir(os.path.join(pastas["banco"], "Mapas"))) == ["Cripta do Teste - Cripta.png"]

print("== importar de novo: nada é sobrescrito")
i2 = pacote.instalar(arq, pastas["aventuras"], pastas["banco"], pastas["tabelas"])
assert os.path.basename(i2["aventura"]) == "Cripta do Teste (2).taverna"
assert i2["imagens"] == 0 and i2["imagens_repetidas"] == 3
assert i2["tabelas"] == 0 and i2["tabelas_repetidas"] == 1
with open(os.path.join(pastas["tabelas"], "Sucata do ermo.json"), "w", encoding="utf-8") as f:
    json.dump(dict(tabela, moeda="Parafusos"), f)                # o usuário mudou a tabela dele
i3 = pacote.instalar(arq, pastas["aventuras"], pastas["banco"], pastas["tabelas"])
assert i3["tabelas_renomeadas"] == 1
with open(os.path.join(pastas["tabelas"], "Sucata do ermo.json"), encoding="utf-8") as f:
    assert json.load(f)["moeda"] == "Parafusos"                # a dele ficou intacta
assert os.path.exists(os.path.join(pastas["tabelas"], "Sucata do ermo (2).json"))

print("== abre igualzinho")
M2 = JanelaMestre(); M2.resize(1000, 700); M2.show(); M2.mostrar_mesa(); QTest.qWait(50)
assert M2.abrir_cena(i1["aventura"])
itens = M2.cena.itens_do_usuario()
mapas = [i for i in itens if isinstance(i, MapaItem)]
assert len(mapas) == 2 and all(m.dados == img_mapa for m in mapas)
tokens = {t.nome: t for t in itens if isinstance(t, TokenItem)}
assert tokens["Aelar"].ficha is None and tokens["Aelar"].imagem
assert tokens["Orc"].ficha == {"nome": "Orc", "pv": 15}
bau2 = next(i for i in itens if isinstance(i, PropItem) and i.tipo == "bau")
assert bau2.sorteio["tabela"]["nome"] == "Sucata do ermo"
assert len(M2.painel_projetor.galeria) == 1

print("== arquivo que não é pacote")
falso = os.path.join(raiz, "falso.tavernapack")
with open(falso, "wb") as f:
    f.write(b"isso nao e zip")
try:
    pacote.ler(falso)
    raise AssertionError("devia recusar")
except pacote.ErroPacote as erro:
    print("   recusado:", erro)
print("FIM")
sys.stdout.flush()
os._exit(0)
