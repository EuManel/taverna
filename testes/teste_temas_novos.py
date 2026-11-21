"""(v0.59) Temas STEAMPUNK e PÓS-APOCALÍPTICO: o tema completo (paleta, fonte OFL carregada, estilo, botões,
metal), os dados com desgaste em TODOS os temas, as 2 telas de cada (sorteio 50/50 + compilam sem erro), o
plano B 2D, as texturas e os ~10 objetos de cenário de cada no filtro "Tema:"."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QFontDatabase, QPainter
from PyQt6.QtQml import QQmlComponent, QQmlEngine
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)
from taverna.ui.tema import carregar_fontes, gerar_qss
carregar_fontes()
from taverna.temas import TEMAS

NOVOS = ("steampunk", "posapoc")
for k in NOVOS:
    t = TEMAS[k]
    for campo in ("fundo", "painel", "texto", "destaque", "destaque2", "fonte_titulo", "chao", "paredes"):
        assert t.get(campo), (k, campo)
    familia = t["fonte_titulo"].split(",")[0].strip("'\" ")
    assert familia in QFontDatabase.families(), (k, familia)   # a fonte OFL veio junto
    assert "QDockWidget" in gerar_qss(k)
assert "Sedgwick Ave Display" in QFontDatabase.families()
print("temas:", [TEMAS[k]["nome"] for k in NOVOS], "· fontes ok")
licencas = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "LICENCAS.md"), encoding="utf-8").read()
for nome in ("IM FELL English SC", "Black Ops One", "Sedgwick Ave Display"):
    assert nome in licencas, nome

# o estilo próprio de cada um (não cai no do Medieval)
from taverna.ui import estilizado as E
from taverna.ui import materiais_ui, relevo_ui
from taverna.ui.tela_inicial import ANIMACOES, CORES_TELA, FUNDOS, desenhar_fundo
for k in NOVOS:
    for tabela in (E.PALETAS, E.METAL_TITULO, E.CORES_METAL, E.ESTILO_BOTAO, CORES_TELA, FUNDOS, ANIMACOES, relevo_ui.KITS):
        assert k in tabela, (k, tabela is E.PALETAS)
    pm = desenhar_fundo(k, 320, 200)          # plano B 2D (sem placa de vídeo)
    p = QPainter(pm)
    import random
    ANIMACOES[k](p, 320, 200, 2.0, 2, random.Random(1))
    p.end()
    assert not E.botao_tema(k, 240, 48).isNull() and not materiais_ui.textura(k).isNull()

# dados: material de cada tema + o desgaste em TODOS os temas
from taverna.dados3d.cena3d import MATERIAIS, textura_desgaste
for k in TEMAS:
    assert k in MATERIAIS, k
    img = textura_desgaste(k)
    assert img is not None and img.width() == 512, k
print("dados: material e desgaste nos", len(TEMAS), "temas")

# texturas das cenas
from taverna.ui import posapoc_cenas, steampunk_cenas
for n in ("latao", "cobre", "parede_oficina", "mostrador", "telegrafo", "ceu_nuvens", "cidade_chamines", "nuvem"):
    assert not steampunk_cenas.textura(n).isNull(), n
for n in ("ferrugem", "madeira_placa", "cerca_arame", "mapa_marcado", "pa_ceu", "pa_lateral", "pa_frente", "pa_teto",
          "pa_folhas", "pa_capim", "pa_hera", "pa_asfalto", "pa_calcada", "pa_predio0", "pa_predio3", "pa_loja0", "pa_loja5"):
    assert not posapoc_cenas.textura(n).isNull(), n
assert len(posapoc_cenas.FRASES_RADIO) >= 4

# as duas telas de cada: sorteio 50/50, forçar pela variável, QML compila
from taverna.ui.lancador import PASTA_QML, Ponte
from taverna.ui.tema import guardar_tema_preferido, tema_preferido
tema_antes = tema_preferido()
p = Ponte()
for tema, prop, var, telas in (("steampunk", "cenaSteampunk", "TAVERNA_CENA_STEAMPUNK", {"oficina", "dirigivel"}),
                               ("posapoc", "cenaPosApocaliptico", "TAVERNA_CENA_POSAPOC", {"cidade", "abrigo"})):
    os.environ.pop(var, None)
    vistas = set()
    for _ in range(40):
        p.definirTema("medieval")
        p.definirTema(tema)
        vistas.add(getattr(p, prop))
    assert vistas == telas, (tema, vistas)
    forcada = sorted(telas)[0]
    os.environ[var] = forcada
    p.definirTema("medieval")
    p.definirTema(tema)
    assert getattr(p, prop) == forcada
    os.environ.pop(var, None)
p.plim()   # (sem som nos testes: não pode dar erro)
eng = QQmlEngine()
eng.rootContext().setContextProperty("ponte", p)
for nome in ("SteampunkOficina.qml", "SteampunkDirigivel.qml", "PosApocCidade.qml", "PosApocAbrigo.qml"):
    comp = QQmlComponent(eng, QUrl.fromLocalFile(os.path.join(PASTA_QML, nome)))
    erros = [e.toString() for e in comp.errors()]
    print(nome, "->", "ok" if not erros else erros)
    assert not erros, erros
    src = open(os.path.join(PASTA_QML, nome), encoding="utf-8").read()
    assert "menuProprio: true" in src and "tituloProprio: true" in src
lanc = open(os.path.join(PASTA_QML, "Lancador.qml"), encoding="utf-8").read()
assert "SteampunkDirigivel.qml" in lanc and "PosApocAbrigo.qml" in lanc
guardar_tema_preferido(tema_antes)

# objetos de cenário: ~10 de cada no filtro do tema, com desenho e altura na Mesa 3D
from taverna.mesa.props import ALTURA_3D, CATALOGO, desenhar_miniatura
from taverna.mesa.props_temas import TEMAS_PROP
from taverna.ui.painel_objetos import AMBIENTACOES
for k in NOVOS:
    assert k in AMBIENTACOES
    meus = [c for c, v in TEMAS_PROP.items() if k in v]
    assert len(meus) >= 10, (k, meus)
    for c in meus:
        assert c in CATALOGO and not desenhar_miniatura(c, 48).isNull(), c
        assert c in ALTURA_3D or CATALOGO[c][1], c
    print(k, "objetos:", len(meus))
assert CATALOGO["tambor_fogo"][5].get("luz") and CATALOGO["caldeira"][5].get("luz")
assert CATALOGO["zumbi_caido"][5].get("interativo")   # dá pra revistar
print("FIM")
sys.stdout.flush()
os._exit(0)
