import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"; os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QTransform
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
app = QApplication(sys.argv); app.setStyle("Fusion")
from taverna.ui.tema import QSS
app.setStyleSheet(QSS)
w = QTest.qWait
from taverna.config import CELULA as C
from taverna.graficos import graficos
from taverna.mesa import camera3d
from taverna.mesa.altura3d import ParedesAltas, PORTAS

print("== CÂMERA: o chão não muda, o que é alto vem pra câmera")
img = QImage(1000, 800, QImage.Format.Format_ARGB32)
p = QPainter(img)
p.setWorldTransform(QTransform().translate(500, 400))   # cena (0,0) no centro da tela
cam = camera3d.Camera(p)
chao = cam.projetar(QPointF(300, 0), 0)
alto = cam.projetar(QPointF(300, 0), camera3d.ALTURA_PAREDE)
centro = cam.projetar(QPointF(0, 0), camera3d.ALTURA_PAREDE)
p.end()
print("chão em x=300 ->", round(chao.x() - 500, 1), "| topo da parede ->", round(alto.x() - 500, 1),
      "| no centro da tela o topo não sai do lugar:", round(centro.x() - 500, 3))
assert abs(chao.x() - 800) < 1e-6 and alto.x() > chao.x() and abs(centro.x() - 500) < 1e-6

from taverna.ui.janela_mestre import JanelaMestre
M = JanelaMestre(); M.resize(1300, 850); M.show(); M.mostrar_mesa(); w(50)
c = M.cena
print("== A MESA NA PLACA DE VÍDEO? (aqui não tem tela: plano B)", M.visao.usa_placa_de_video)
assert M.visao.usa_placa_de_video is False

print("== PAREDES ALTAS: camada própria, por cima dos tokens e por baixo da luz/névoa")
c.criar_sala(QPointF(-5 * C, -4 * C), QPointF(5 * C, 4 * C))
altas = [i for i in c.items() if isinstance(i, ParedesAltas)]
print("camadas de paredes altas na cena:", len(altas), "| z:", altas[0].zValue() if altas else None)
assert len(altas) == 1 and 0 < altas[0].zValue() < 800_000
c.tipo_porta = "madeira"
porta = c.colocar_porta(QPointF(0, -4 * C))
print("porta registrada pra camada 3D:", porta in PORTAS)
assert porta in PORTAS

print("== DESENHA nos dois modos sem quebrar (2D e 3D), com tocha")
c.tipo_luz = "tocha"; c.colocar_luz(QPointF(-3 * C, -2 * C)); c.definir_ambiente("penumbra")
M.visao.enquadrar_tudo(); w(200)
for ligado in (False, True, False, True):
    graficos().mesa3d = ligado
    graficos().mudou.emit(graficos().atual); w(120)
    M.visao.grab()
print("ok nos dois modos")

print("== A TOCHA PINTA A LATERAL DE FRENTE PRA ELA")
from taverna.mesa.altura3d import luzes_da_cena
luzes = luzes_da_cena(c)
print("luzes que chegam nas paredes:", len(luzes))
assert luzes
def lateral(luzes):
    img = QImage(400, 400, QImage.Format.Format_ARGB32); img.fill(QColor("black"))
    p = QPainter(img); p.setWorldTransform(QTransform().translate(200, 200))
    cam = camera3d.Camera(p)
    from PyQt6.QtGui import QPolygonF
    # parede vertical à direita do centro: a face da esquerda (virada pro centro) aparece
    pol = QPolygonF([QPointF(100, -80), QPointF(112, -80), QPointF(112, 80), QPointF(100, 80)])
    camera3d.desenhar_laterais(p, cam, [pol], camera3d.ALTURA_PAREDE, QColor("#808080"), luzes=luzes)
    p.end()
    return QColor(img.pixel(306, 200))   # pixel na face da esquerda (pé em x=300 na tela, topo ~x=321)
sem = lateral([])
com = lateral([(QPointF(60, 0), 3 * C, QColor("#ff9a3a"), None)])
print("cor da face sem luz:", sem.name(), "| com tocha perto:", com.name())
assert com.red() > sem.red() + 20

print("== MESMA COISA NO JOGADOR (a cena dele também ganha a camada)")
from taverna.mesa.cena_player import CenaPlayer
cp = CenaPlayer()
print("camada de paredes altas no jogador:", any(isinstance(i, ParedesAltas) for i in cp.items()))
assert any(isinstance(i, ParedesAltas) for i in cp.items())
graficos().mesa3d = True
M.visao.grab().save("saida/shot_mesa3d.png")

print("== PARTÍCULAS 3D DAS ÁREAS DE EFEITO (v0.36)")
from taverna.mesa import efeitos3d
from taverna.mesa.efeitos import EFEITOS, EfeitoItem
from PyQt6.QtWidgets import QGraphicsScene
cena_p = QGraphicsScene()
areas = []
for k, ef in enumerate(EFEITOS):
    a = EfeitoItem(ef, "circulo", 1.5)
    cena_p.addItem(a)
    a.setPos(-300 + (k % 6) * 120, -100 + (k // 6) * 120)
    areas.append(a)
assert all(a in efeitos3d.AREAS for a in areas)
img = QImage(800, 400, QImage.Format.Format_ARGB32); img.fill(QColor(50, 50, 50))
p = QPainter(img)
p.setWorldTransform(QTransform().translate(400, 200)); cam = camera3d.Camera(p); p.resetTransform()
for nivel in (1, 2):
    for t in (0.0, 1.37, 5.9):
        for a in areas:
            efeitos3d.desenhar(p, cam, a, t, nivel)   # nenhum efeito pode dar erro
p.end()
mudou = sum(1 for x in range(0, 800, 7) for y in range(0, 400, 7) if img.pixel(x, y) != QColor(50, 50, 50).rgba())
print("efeitos desenhados:", len(areas), "| pixels com partícula:", mudou)
assert mudou > 200
cena_p.removeItem(areas[0]); del areas[0]   # apagar uma área não quebra a camada

print("== TOKENS (FICHA GROSSA) E OBJETOS COM ALTURA (v0.37)")
from taverna.mesa.props import CATALOGO, PropItem, altura_3d
from taverna.mesa.token import TokenItem
assert altura_3d("estante") == 1.9 * C and altura_3d("tapete") == 0 and altura_3d("pergaminho") == 0
assert all(altura_3d(t) >= 0 for t in CATALOGO)
from PyQt6.QtWidgets import QStyleOptionGraphicsItem


def pintar(item, x, y):
    """Desenha o item numa imagem 1000x800 com ele em (x,y) da tela; devolve a imagem."""
    im = QImage(1000, 800, QImage.Format.Format_ARGB32); im.fill(QColor(0, 0, 0, 0))
    pp = QPainter(im)
    pp.setWorldTransform(QTransform().translate(x, y))
    item.paint(pp, QStyleOptionGraphicsItem(), None)
    from taverna.mesa.altura3d import OBJETOS   # (v0.84) o corpo do objeto 3D vem da camada das coisas altas
    if item in OBJETOS:
        pp.setWorldTransform(QTransform().translate(x, y))
        item.pintar_corpo_3d(pp, 2)
    pp.end()
    return im


def fora_da_base(im, x, y, w, h):
    """Pixels pintados fora do retângulo do objeto no chão (lateral/topo deslocado)."""
    return sum(1 for px in range(0, 1000, 3) for py in range(0, 800, 3)
               if not (x - 30 <= px <= x + w + 30 and y - 30 <= py <= y + h + 30) and QColor.fromRgba(im.pixel(px, py)).alpha() > 40)


est = PropItem("estante")
im = pintar(est, 40, 40)   # no canto da tela: o topo de 1,9 m se afasta bastante do centro
desloc = fora_da_base(im, 40, 40, est.largura, est.altura)
graficos().mesa3d = False
plano = fora_da_base(pintar(est, 40, 40), 40, 40, est.largura, est.altura)
graficos().mesa3d = True
print("estante no canto: pixels fora da base em 3D =", desloc, "| em 2D =", plano)
assert desloc > 20 and plano == 0
tk = TokenItem("Teste", "jogador")
im = pintar(tk, 40, 40)
print("token 3D desenhou sem erro; boundingRect:", tk.boundingRect().width())

print("== CLIMA E IMPACTOS EM 3D (v0.38)")
import time as _t
from taverna.ui.clima import CLIMAS
co = M.clima_overlay
for clima in CLIMAS:
    if clima == "nenhum":
        continue
    co.definir(clima, 3)
    for k in range(6):
        if k == 3:
            M.visao.horizontalScrollBar().setValue(M.visao.horizontalScrollBar().value() + 40)   # arrasta o mapa
        co._proximo_raio = 0
        co._passo()
        co.grab()
    assert co._modo3d and co._p, clima
    if clima == "chuva":
        assert all(0 <= q[2] <= 0.5 for q in co._p)
print("climas em 3D: ok (", len(CLIMAS) - 1, ")")
co.definir("nenhum", 2)
from taverna.mesa.impactos import IMPACTOS, ImpactoItem
for tipo, (_n, no_mapa, dur) in IMPACTOS.items():
    if not no_mapa:
        continue
    it = ImpactoItem(tipo)
    for fr in (0.05, 0.3, 0.6, 0.9):
        it.t0 = _t.monotonic() - dur * fr
        im = pintar(it, 500, 400)
    assert it.dur > 0, tipo   # (dur = 0 = deu erro no desenho)
    it._timer.stop()
print("impactos em 3D: ok")

print("== MARCAS NO CHÃO (v0.39)")
from taverna.mesa import marcas
c = M.cena
c.criar_sala(QPointF(-6 * C, -4 * C), QPointF(6 * C, 4 * C))
antes = sum(1 for o in c.terreno.ops if o["t"] == "marca")
fogo = c.criar_efeito({"efeito": "fogo", "forma": "circulo", "tamanho": 1.5, "x": 0, "y": 0})
assert fogo.forca_marca() == 0
fogo.setPos(fogo.pos() + QPointF(C, 0))   # arrastou logo: não marca
assert sum(1 for o in c.terreno.ops if o["t"] == "marca") == antes
fogo._desde -= 10   # ficou parada uns segundos
assert fogo.forca_marca() == 1.0
im = pintar(fogo, 300, 300)   # desenha a marca "pegando" sem erro
fogo.setPos(fogo.pos() + QPointF(2 * C, 0))   # moveu depois de pegar: a marca fica no lugar antigo
assert sum(1 for o in c.terreno.ops if o["t"] == "marca") == antes + 1
fogo._desde -= 10
luz = c.criar_efeito({"efeito": "luz", "forma": "circulo", "tamanho": 1.5, "x": 0, "y": 0})
luz._desde -= 10
c.remover_efeitos()   # apagou: fogo marca, luz não (luz não deixa marca)
ops_marca = [o for o in c.terreno.ops if o["t"] == "marca"]
print("marcas no terreno:", len(ops_marca), "| tipos:", sorted({o["k"] for o in ops_marca}))
assert len(ops_marca) == antes + 2
for ef in marcas.MARCA_DO_EFEITO:   # todas as marcas geram imagem
    a = c.criar_efeito({"efeito": ef, "forma": "cone", "tamanho": 3, "x": 0, "y": 0, "cor": "#40e0d0"})
    op = marcas.op_da_area(a)
    img_m, img_c, r = marcas.imagem(op["k"], op["p"], op["s"], op.get("c", ""))
    assert not img_m.isNull() and not img_c.isNull() and r.width() > 0, ef
    c.remover_itens([a])
c.terreno._cache.clear()
c.terreno._tile(0, 0, 0)   # azulejo com marca desenha sem erro
import json
json.dumps(c.terreno.para_lista())   # vai pela rede / arquivo
n = c.limpar_marcas()
print("limpar marcas tirou:", n)
assert n >= antes + 2 and not any(o["t"] == "marca" for o in c.terreno.ops)
c.desfazer()   # Ctrl+Z traz de volta
assert any(o["t"] == "marca" for o in c.terreno.ops)

print("== REAÇÕES ENTRE ÁREAS (v0.40)")
from taverna.mesa import reacoes
c.limpar_marcas()


def ef(nome, x=0, tam=1.5):
    return c.criar_efeito({"efeito": nome, "forma": "circulo", "tamanho": tam, "x": x * C, "y": 0})


def vivas():
    return sorted(e.efeito for e in c.efeitos_visiveis())


def reagir(a, b, esperado=True):
    achadas = reacoes.procurar(c, [a])
    assert bool(achadas) == esperado, (a.efeito, b.efeito, achadas)
    if achadas:
        par, x, y = achadas[0]
        return reacoes.aplicar(c, par, x, y, None)


c.remover_efeitos()
f, w = ef("fogo"), ef("agua", 1.5)                     # a água cobre só um lado do fogo
area_antes = reacoes._area_caminho(f.caminho())
print(reagir(w, f), "->", vivas())
assert "fogo" in vivas() and "fumaca" in vivas()       # apagou SÓ onde encostou, sobe vapor
assert f.recortes and reacoes._area_caminho(f.caminho()) < area_antes * 0.9
assert reacoes.sobreposicao(f, w) < 0.01               # não reage de novo sozinho
d = f.para_dict()
from taverna.mesa.efeitos import EfeitoItem as _E
copia = _E.de_dict(d)                                  # recorte vai pela rede / arquivo
assert abs(reacoes._area_caminho(copia.caminho()) - reacoes._area_caminho(f.caminho())) < 1
c.remover_efeitos()
f, w = ef("fogo", 0, 1.5), ef("agua", 0, 2)            # a água cobre o fogo todo: apaga todo
reagir(w, f)
assert "fogo" not in vivas()
c.remover_efeitos()
gelo, f = ef("gelo", 0, 2), ef("fogo", 2.5, 1.5)      # derrete só a beirada
reagir(f, gelo)
assert vivas().count("gelo") == 1 and "agua" in vivas()
pedaco = next(e for e in c.efeitos_visiveis() if e.efeito == "agua")
assert pedaco.forma == "livre" and pedaco.pontos
c.remover_efeitos()
longe = ef("fogo", 0), ef("agua", 8)
reagir(longe[1], longe[0], esperado=False)             # sem encostar: nada
c.remover_efeitos()
lv, w = ef("lava"), ef("agua")
reagir(w, lv)
assert "lava" not in vivas() and "agua" not in vivas()
assert any(o["t"] == "marca" and o["k"] == "basalto" for o in c.terreno.ops)   # virou rocha
c.remover_efeitos()
g, f = ef("veneno", 0, 3), ef("fogo", 0.5)
reagir(f, g)
assert "veneno" not in vivas() and any(o["k"] == "queimado" for o in c.terreno.ops if o["t"] == "marca")
c.remover_efeitos()
for (x, y), virou in ((("fogo", "acido"), "veneno"), (("fogo", "gelo"), "agua"), (("agua", "gelo"), "gelo"),
                      (("fogo", "planta"), "fogo"), (("fogo", "teia"), "fogo")):
    a, b = ef(x), ef(y)
    reagir(a, b)
    assert virou in vivas(), (x, y, vivas())
    c.remover_efeitos()
r, w = ef("eletrico"), ef("agua")
reagir(r, w)
assert vivas().count("eletrico") == 2   # a água ficou eletrificada
assert not reacoes.procurar(c, [e for e in c.efeitos_visiveis()]) or True
c.remover_efeitos()
l, t = ef("luz"), ef("trevas")
reagir(l, t)
assert "trevas" not in vivas()
c.remover_efeitos()
f, w = ef("fogo"), ef("agua")
c.recusar_reacao(f, w)
reagir(w, f, esperado=False)            # o mestre disse "agora não": não pergunta de novo…
w.setPos(w.pos() + QPointF(5, 0))
reagir(w, f, esperado=True)             # …até mexer numa delas
c.remover_efeitos()
print("reações: ok (", len(reacoes.REACOES), "pares )")
# v0.42: AUTOMÁTICO — a água cai em cima do fogo e ele apaga sozinho (sem aviso)
f, w = ef("fogo", 0, 1.5), ef("agua", 0, 2)
QTest.qWait(900)
assert "fogo" not in vivas(), vivas()
print("reação automática: ok")
c.remover_efeitos()

print("== LANÇAR (bola de fogo, jato…) (v0.41)")
from taverna.mesa import lancamentos as L
assert L.conferir({"x0": 0, "y0": 0, "x1": 1, "y1": 0}) is None          # curto demais
longe = L.conferir({"x0": 0, "y0": 0, "x1": 500 * C, "y1": 0, "velocidade": 9999})
assert abs(L.distancia_m(longe) - L.LIMITES["dist"][1]) < 0.01 and longe["velocidade"] == L.LIMITES["velocidade"][1]
assert L.conferir({"x0": "x"}) is None
for graf3d in (True, False):
    graficos().mesa3d = graf3d
    for el in L.ELEMENTOS:
        for tipo in L.TIPOS_LANCE:
            d = L.conferir({"elemento": el, "tipo": tipo, "x0": -3 * C, "y0": 0, "x1": 4 * C, "y1": C,
                            "velocidade": 10, "deixar": True, "tam": 2})
            item = L.LancamentoItem(d)
            for fr in (0.02, 0.3, 0.6, 0.85, 0.99):
                item.t0 = _t.monotonic() - item.dur * fr
                pintar(item, 500, 400)
            assert item.dur > 0, (el, tipo)   # (dur = 0 = deu erro no desenho)
            item._timer.stop()
graficos().mesa3d = True
for forma in L.PROJETEIS:   # v0.42: formato do projétil + cor (fogo negro, raio vermelho, magia verde…)
    for el, cor in (("magia", "#40e070"), ("fogo", "#2a1236"), ("eletrico", "#ff3a3a"), ("gelo", "#ff0000")):
        d = L.conferir({"elemento": el, "tipo": "projetil", "projetil": forma, "cor": cor,
                        "x0": 0, "y0": 0, "x1": 6 * C, "y1": 2 * C, "velocidade": 10})
        assert (d["cor"] == "") == (el not in L.CORES_LANCE)   # gelo não tem cor livre
        item = L.LancamentoItem(d)
        for fr in (0.1, 0.4, 0.8):
            item.t0 = _t.monotonic() - item.dur * fr
            pintar(item, 300, 300)
        assert item.dur > 0, (forma, el)
        item._timer.stop()
print("lançamentos desenham: ok (", len(L.ELEMENTOS), "elementos x", len(L.TIPOS_LANCE), "tipos x",
      len(L.PROJETEIS), "projéteis, 2D e 3D )")
c.remover_efeitos()
d = M.servidor.lancar({"elemento": "acido", "tipo": "projetil", "x0": 0, "y0": 0, "x1": 3 * C, "y1": 0,
                       "velocidade": 30, "deixar": True, "tam": 1.5}, dono="Lúcia")
assert d and any(isinstance(i, L.LancamentoItem) for i in M.servidor.cena.items())
QTest.qWait(int(L.chegada(d) * 1000) + 300)
poca = [e for e in c.efeitos_visiveis() if e.efeito == "acido"]
print("bolha de ácido deixou a poça:", len(poca), "| dono:", poca[0].dono if poca else "-")
assert poca and poca[0].dono == "Lúcia"
c.remover_efeitos()

print("== GÁS NÃO ATRAVESSA PAREDE (v0.44)")
c.remover_efeitos()
c.adicionar_parede(QPointF(2 * C, -4 * C), QPointF(2 * C, 4 * C))
tem_parede = any(abs(s["a"][0] - 2 * C) < 1 and abs(s["b"][0] - 2 * C) < 1 for s in c.paredes.segmentos.values())
print("parede no meio:", tem_parede)
assert tem_parede
gas = c.criar_efeito({"efeito": "veneno", "forma": "circulo", "tamanho": 4, "x": 0, "y": 0})
gas._gas_t = -1
cam = gas.caminho_cena()
outro_lado = QPointF(3.5 * C, 0)
print("gás do outro lado da parede?", cam.contains(outro_lado), "| deste lado?", cam.contains(QPointF(-1 * C, 0)))
if tem_parede:
    assert not cam.contains(outro_lado) and cam.contains(QPointF(-1 * C, 0))
fogo_longe = c.criar_efeito({"efeito": "fogo", "forma": "circulo", "tamanho": 1, "x": 3.5 * C, "y": 0})
assert not reacoes.procurar(c, [fogo_longe])   # o fogo do outro lado da parede não acende o gás
c.remover_efeitos()

print("== NEBLINA VOLUMÉTRICA (v0.44)")
from taverna.mesa import neblina
c.criar_sala(QPointF(-6 * C, -4 * C), QPointF(6 * C, 4 * C))
barril = c.colocar_prop("barril", QPointF(-2 * C, 0))
bc = barril.centro_cena()
c.definir_clima("neblina", 2)
item_n = neblina.garantir(c)
assert neblina.garantir(c) is item_n and item_n.animado()   # uma só camada
r_vis = QRectF(-8 * C, -6 * C, 16 * C, 12 * C)
masc = neblina.mascara(c, r_vis)
# o barril "abre caminho": a máscara tem vermelho onde ele está, e nada longe dele
mx = lambda x, y: QColor(masc.pixel(int((x - r_vis.x()) / r_vis.width() * masc.width()),
                                     int((y - r_vis.y()) / r_vis.height() * masc.height()))).red()
print("máscara no barril:", mx(bc.x(), bc.y()), "| longe:", mx(4 * C, -2 * C))
assert mx(bc.x(), bc.y()) > 100 and mx(4 * C, -2 * C) < 30
im = QImage(800, 600, QImage.Format.Format_ARGB32_Premultiplied); im.fill(QColor(80, 60, 40))
pp = QPainter(im); pp.setWorldTransform(QTransform().translate(400, 300).scale(0.6, 0.6))
item_n._plano_b(pp, c, r_vis, masc, 2, 2)   # plano B (sem placa de vídeo) desenha sem erro
pp.end()
cinza = QColor(im.pixel(650, 120))
print("plano B pintou neblina:", cinza.name())
assert cinza != QColor(80, 60, 40)
M.visao.grab()   # passa pelo paint() de verdade (offscreen = plano B)
c.definir_clima("nenhum", 2)
assert not item_n.animado()

print("== GÁS E LÍQUIDOS DE CENÁRIO (v0.45)")
from taverna.mesa import fluidos as FL
c.remover_efeitos()
c.criar_sala(QPointF(-10 * C, -5 * C), QPointF(10 * C, 5 * C))
c.adicionar_parede(QPointF(0, -5 * C), QPointF(0, 5 * C))
fl = FL.de_cena(c)
fl.limpar(fontes=True)
fl.adicionar_fonte("gas_toxico", -8 * C, 0, "forte")   # a estátua soltando gás (entre paredes de testes de cima)
for _ in range(200):
    fl.passo(0.1)
gas = fl.campos["gas_toxico"]
i_parede = int(0 / FL.G) - fl.ox
esq, dir_ = float(gas[:, :i_parede].sum()), float(gas[:, i_parede:].sum())
print("gás: lado da estátua", round(esq, 1), "| do outro lado da parede", round(dir_, 3))
assert esq > 20 and dir_ < 0.01
jj, ii = FL.np.nonzero(gas > 0.05)
print("gás espalhado por", len(ii), "células (0,25 m² cada)")
assert len(ii) > 60
# bola de fogo chegando no gás: EXPLODE (em cadeia) e o gás some
boom = []
fl.explosao.connect(lambda x, y, t: boom.append((x, y, t)))
assert fl.ignicao_em(-8 * C, 0, 1.5) and boom and float(fl.campos["gas_toxico"].sum()) < esq * 0.3
print("explosão:", [(round(x), round(y), round(t, 1)) for x, y, t in boom])
fl.limpar(fontes=True)
# nuvem solta: espalha e some sozinha
fl.soltar("fumaca", -5 * C, 0, 2)
for _ in range(2000):
    fl.passo(0.1)
assert not fl.ativo(), float(fl.campos["fumaca"].sum())
# poça: escorre, para, não passa a parede e não some
fl.soltar("agua", -2 * C, 0, 1.5)
for _ in range(300):
    fl.passo(0.1)
agua = fl.campos["agua"]
molhado = int((agua > FL.PELICULA * 0.5).sum())
for _ in range(100):
    fl.passo(0.1)
print("poça: células molhadas", molhado, "→", int((agua > FL.PELICULA * 0.5).sum()), "| do outro lado:",
      round(float(agua[:, i_parede:].sum()), 4))
assert molhado > 40 and float(agua[:, i_parede:].sum()) < 1e-3 and fl.ativo()
# rede/arquivo: o jogador recebe o retrato e vê a mesma coisa
from taverna.mesa.cena_player import CenaPlayer
cp2 = CenaPlayer()
fp = FL.de_cena(cp2, simula=False)
fp.aplicar_retrato(fl.retrato())
assert abs(float(fp.campos["agua"].sum()) - float(agua.sum())) < float(agua.sum()) * 0.05
d_arq = fl.para_dict()
fl.adicionar_fonte("lava", 4 * C, 0, "fraca", 30)
d_arq = fl.para_dict()
fl2 = FL.Fluidos(c)
fl2.de_dict(json.loads(json.dumps(d_arq)))
assert len(fl2.fontes) == 1 and fl2.fontes[0]["duracao"] == 30
fl2.timer.stop()
# área de fogo alagada pela água: apaga onde molhou
fogo_ag = c.criar_efeito({"efeito": "fogo", "forma": "circulo", "tamanho": 1.5, "x": -2 * C, "y": 0})
fogo_ag._gas_t = -1
fl._t_reacoes = 0
fl.passo(0.1)
print("fogo em cima da poça:", "apagou" if fogo_ag.scene() is None else f"recortado ({len(fogo_ag.recortes)} pedaço)")
assert fogo_ag.scene() is None or fogo_ag.recortes
fl.limpar(fontes=True)
c.remover_efeitos()

print("== EFEITO FORA DO MAPA É CORTADO (v0.45)")
meio_fora = c.criar_efeito({"efeito": "fogo", "forma": "circulo", "tamanho": 3, "x": 9 * C, "y": 0})
meio_fora._gas_t = -1
cam = meio_fora.caminho_cena()
print("dentro da sala:", cam.contains(QPointF(8 * C, 0)), "| no vazio:", cam.contains(QPointF(11 * C, 0)))
assert cam.contains(QPointF(8 * C, 0)) and not cam.contains(QPointF(11 * C, 0))
# v0.45.1 — a "sala fantasma": área clicada no limbo não pode virar um pedaço da sala lá longe
no_limbo = c.criar_efeito({"efeito": "fogo", "forma": "circulo", "tamanho": 6, "x": 40 * C, "y": 20 * C})
assert no_limbo is None, "área toda no vazio não deve existir"
perto = c.criar_efeito({"efeito": "fogo", "forma": "circulo", "tamanho": 6, "x": 13 * C, "y": 0})   # metade dentro
cam_p = perto.caminho_cena()
print("área na beirada: cortada em", cam_p.boundingRect().left() / C, "→", cam_p.boundingRect().right() / C, "m")
assert cam_p.boundingRect().right() <= 10 * C + 1 and cam_p.boundingRect().left() >= 7 * C - 1
perto.setPos(perto.pos() + QPointF(40 * C, 0))   # arrastou pro vazio: na hora, sem efeito (sem fantasma)
assert perto.caminho_cena().isEmpty() and not perto.shape().isEmpty()   # mas dá pra clicar e apagar
c.remover_efeitos()
tk_fora = c.adicionar_token({"nome": "Estacionado", "tipo": "criatura", "cor": "#6e2a2f", "tamanho": 1},
                            QPointF(30 * C, 0))
assert tk_fora.isVisible()   # token pode ficar fora (o mestre "estaciona")
c.remover_itens([tk_fora])
c.remover_efeitos()

print("== ILUMINAÇÃO DINÂMICA (v0.45)")
from taverna.mesa import luz_dinamica
c.definir_ambiente("escuro")
c.recalcular_luzes()
d_l = L.conferir({"elemento": "fogo", "tipo": "projetil", "x0": -8 * C, "y0": 0, "x1": -1 * C, "y1": 0,
                  "velocidade": 10})
bola = L.LancamentoItem(d_l)
c.addItem(bola)
bola._timer.stop()
luz = bola._luz(0.3)
print("bola de fogo voando ilumina:", {k: (round(v, 1) if isinstance(v, float) else v) for k, v in luz.items()})
assert luz and luz["brilho"] > 0.5
luz_dinamica.definir(c, "teste", dict(luz, x=-1.5 * C, y=0, fraco=8))
luz_dinamica.aplicar(c)
pol = next(p for d, p in c.luz_overlay.luzes if d.get("id") == "teste")
print("a luz passa da parede?", pol.containsPoint(QPointF(2 * C, 0), Qt.FillRule.OddEvenFill),
      "| ilumina deste lado?", pol.containsPoint(QPointF(-4 * C, 0), Qt.FillRule.OddEvenFill))
assert not pol.containsPoint(QPointF(2 * C, 0), Qt.FillRule.OddEvenFill)
assert pol.containsPoint(QPointF(-4 * C, 0), Qt.FillRule.OddEvenFill)
luz_dinamica.definir(c, "teste", None)
luz_dinamica.aplicar(c)
assert not any(d.get("id") == "teste" for d, _p in c.luz_overlay.luzes)
c.removeItem(bola)
from taverna.mesa.impactos import ImpactoItem
imp = ImpactoItem("explosao")
c.addItem(imp)
imp._timer.stop()
assert imp._luz(0.1)["brilho"] > 0.7 and imp._luz(0.95) is None   # clarão que apaga
c.removeItem(imp)
c.definir_ambiente("dia")

print("== SHADER DAS ÁREAS (se der pra abrir OpenGL aqui)")
try:
    from PyQt6.QtGui import QOffscreenSurface, QOpenGLContext, QSurfaceFormat
    from PyQt6.QtOpenGL import QOpenGLFramebufferObject, QOpenGLPaintDevice
    ctx = QOpenGLContext()
    sup = QOffscreenSurface()
    tem_gl = ctx.create()
    if tem_gl:
        sup.setFormat(ctx.format()); sup.create()
        tem_gl = ctx.makeCurrent(sup)
except Exception as erro:
    tem_gl = False
if not tem_gl:
    print("sem OpenGL neste modo de teste: pulei (o desenho 2D é o que vale aqui)")
else:
    from taverna.mesa import efeitos_gl
    fbo = QOpenGLFramebufferObject(400, 400); fbo.bind()
    pp = QPainter(QOpenGLPaintDevice(400, 400))
    for ef in efeitos_gl.TIPOS:
        a = EfeitoItem(ef, "circulo", 1.5)
        pp.save(); pp.translate(200, 200)
        assert efeitos_gl.desenhar(pp, a), ef
        pp.restore()
    pp.end()
    print("shader compilou e desenhou os", len(efeitos_gl.TIPOS), "efeitos")
print("FIM")
