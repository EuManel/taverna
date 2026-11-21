"""
Salvar e abrir aventuras (.taverna).

O arquivo é um JSON com tudo dentro, inclusive as imagens (em base64),
então dá pra mandar um único arquivo pra outra pessoa e abrir igualzinho.

Versão 4: a aventura tem várias ABAS (cenários: caverna, floresta, castelo...).
          Uma delas é a "ao vivo" (a que os players veem).
Versão 3: terreno como tinta, paredes em qualquer ângulo, portas livres.
Arquivos antigos abrem normalmente (viram uma aventura de uma aba só).
"""

import base64
import json
import uuid

from ..config import APP_NOME, VERSAO_ARQUIVO
from ..temas import TEMA_PADRAO, TEMAS
from .construcao import ParedesItem, TerrenoItem
from .luzes import LuzItem
from .mapa import MapaItem
from .portas import PortaItem
from .token import TokenItem

from .gatilho_area import AreaGatilhoItem
from .props import PropItem
from .efeitos import EfeitoItem

CLASSES = {"mapa": MapaItem, "token": TokenItem, "porta": PortaItem, "luz": LuzItem, "prop": PropItem,
           "gatilho": AreaGatilhoItem, "efeito": EfeitoItem}


# ====================================================================== uma aba
def dados_da_cena(cena) -> dict:
    """Uma aba (cenário) vira um dicionário."""
    camadas = []
    for c in cena.camadas:  # de baixo pra cima
        info = {"nome": c.nome, "tipo": c.tipo, "visivel": c.isVisible(),
                "travada": c.travada, "itens": [i.para_dict() for i in c.itens()]}
        if c.tipo == "terreno" and cena.terreno:
            info["pinceladas"] = cena.terreno.para_lista()
        elif c.tipo == "paredes" and cena.paredes:
            info["segmentos"] = cena.paredes.para_lista()
        camadas.append(info)
    return {
        "id": cena.uid,
        "nome": cena.nome_aba,
        "snap": cena.snap_ativo,
        "opacidade_grid": cena.opacidade_grid,
        "nevoa": cena.nevoa_ativa,
        "ambiente": cena.luz_ambiente,
        "clima": dict(cena.clima),
        "desenhos": [t for t in cena.tracos if not t.get("temp")],
        "camadas": camadas,
        "fluidos": cena.fluidos.para_dict() if getattr(cena, "fluidos", None) is not None else None,
        "predio": getattr(cena, "predio", None),   # 🏢 andares (v0.46)
        "andar": getattr(cena, "andar", 0),
    }


def carregar_dados_na_cena(cena, aba: dict, tema: str = TEMA_PADRAO, aventura: str = ""):
    cena.opacidade_grid = aba.get("opacidade_grid", 0.35)
    cena.tema = tema if tema in TEMAS else TEMA_PADRAO
    cena.nome_aventura = aventura
    cena.nome_aba = aba.get("nome") or "Cenário"
    cena.uid = aba.get("id") or uuid.uuid4().hex

    cena.clima = dict(aba.get("clima") or {"tipo": "nenhum", "forca": 2})
    cena.tracos = list(aba.get("desenhos") or [])
    cena.clear()
    cena.camadas = []
    if hasattr(cena, "limpar_restos"):
        cena.limpar_restos()   # (nada da sessão anterior pendurado: gás, luzes passageiras…)
    cena.predio = aba.get("predio") or None   # 🏢 andares (v0.46)
    try:
        cena.andar = int(aba.get("andar") or 0)
    except (TypeError, ValueError):
        cena.andar = 0
    for info in aba["camadas"]:
        tipo = info.get("tipo", "livre")
        camada = cena.criar_camada(tipo, info.get("nome"))
        itens = list(info.get("itens", []))
        if tipo == "terreno":
            if "pinceladas" in info:
                cena.terreno.definir(TerrenoItem.de_lista(info["pinceladas"]))
            elif "celulas" in info:  # versão 2
                celulas = {(int(i), int(j)): m for i, j, m in info["celulas"]}
                cena.terreno.definir(TerrenoItem.converter_celulas(celulas))
        elif tipo == "paredes":
            if "segmentos" in info:
                from .construcao import sem_sobreposicao   # (v0.60.1) conserta salas encostadas antigas
                cena.paredes.definir(sem_sobreposicao(ParedesItem.de_lista(info["segmentos"])))
            elif "paredes" in info:  # versão 2
                segmentos, portas = ParedesItem.converter_arestas(info["paredes"])
                cena.paredes.definir(segmentos)
                itens += portas
        for d in itens:
            classe = CLASSES.get(d.get("classe"))
            if classe:
                classe.de_dict(d).setParentItem(camada)
        camada.setVisible(info.get("visivel", True))
        camada.definir_travada(info.get("travada", False))

    cena.garantir_camadas_especiais()
    cena._renumerar_camadas()
    cena.nevoa_ativa = bool(aba.get("nevoa", False))
    cena.luz_ambiente = aba.get("ambiente", "dia")
    cena.adicionar_extras()
    cena.camada_ativa = cena.camadas[-1]
    cena.definir_snap(aba.get("snap", False))
    cena.definir_escala(cena.escala_visao)
    cena.definir_tema(cena.tema)
    # gás e líquidos de cenário (v0.45): fontes + o que estava espalhado
    f = getattr(cena, "fluidos", None)
    if f is not None:
        f.limpar(fontes=True)
    if aba.get("fluidos"):
        from . import fluidos
        fluidos.de_cena(cena).de_dict(aba["fluidos"])
    elif f is not None:
        from . import fluidos
        fluidos.de_cena(cena)   # (a cena foi limpa: os itens de desenho voltam)
    cena.marcar_modificada(False)
    cena.reiniciar_historico()
    cena.camadas_mudaram.emit()
    cena.mesa_mudou.emit()


# ====================================================================== aventura
def salvar_aventura(caminho: str, cenas: list, aventura: str, tema: str,
                    ao_vivo: int = 0, atual: int = 0, projetor: list | None = None,
                    diario: list | None = None, atlas: dict | None = None):
    dados = dados_aventura(cenas, aventura, tema, ao_vivo, atual, projetor, diario, atlas)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False)
    for c in cenas:
        c.marcar_modificada(False)


def dados_aventura(cenas: list, aventura: str, tema: str, ao_vivo: int = 0, atual: int = 0,
                   projetor: list | None = None, diario: list | None = None, atlas: dict | None = None) -> dict:
    """A aventura inteira como dicionário (o que vai no .taverna). Não mexe em nada."""
    return {
        "app": APP_NOME,
        "versao": VERSAO_ARQUIVO,
        "aventura": aventura,
        "tema": tema,
        "aba_ao_vivo": ao_vivo,
        "aba_atual": atual,
        "abas": [dados_da_cena(c) for c in cenas],
        # imagens do projetor (preparadas pelo mestre): [{"titulo", "imagem" base64}]
        "projetor": [{"titulo": p.get("titulo", ""), "imagem": base64.b64encode(p["dados"]).decode("ascii")}
                     for p in (projetor or []) if p.get("dados")],
        "diario": list(diario or []),   # 📓 diário da campanha (entradas do mestre)
        "atlas": atlas or {},           # 🌍 cidades e mundo (v0.62, mesa/atlas.py)
    }


def ler_aventura(caminho: str) -> dict:
    """Lê o arquivo e devolve sempre no formato novo (com 'abas')."""
    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)
    if dados.get("app") != APP_NOME:
        raise ValueError("Esse arquivo não parece ser uma aventura do Taverna.")
    if "abas" not in dados:  # versões 1 a 3: uma aba só
        dados["abas"] = [{
            "nome": "Cenário 1",
            "snap": dados.get("snap", False),
            "opacidade_grid": dados.get("opacidade_grid", 0.35),
            "camadas": dados["camadas"],
        }]
    dados.setdefault("aventura", "")
    dados.setdefault("tema", TEMA_PADRAO)
    dados.setdefault("aba_ao_vivo", 0)
    dados.setdefault("aba_atual", 0)
    dados.setdefault("atlas", {})
    projetor = []
    for p in dados.get("projetor") or []:
        try:
            projetor.append({"titulo": p.get("titulo", ""), "dados": base64.b64decode(p["imagem"])})
        except (KeyError, ValueError, TypeError):
            pass
    dados["projetor"] = projetor
    return dados


def ler_cabecalho(caminho: str) -> dict:
    """Lê só o nome, o tema e quantas abas (pra mostrar na tela inicial)."""
    dados = ler_aventura(caminho)
    return {"aventura": dados.get("aventura", ""), "tema": dados.get("tema", TEMA_PADRAO),
            "abas": len(dados["abas"])}


# ====================================================================== compatibilidade
def salvar_cena(cena, caminho: str):
    """Salva uma única cena como aventura de uma aba."""
    salvar_aventura(caminho, [cena], cena.nome_aventura, cena.tema)


def carregar_cena(cena, caminho: str):
    """Carrega a aba ao vivo do arquivo numa cena."""
    dados = ler_aventura(caminho)
    i = min(max(0, dados["aba_ao_vivo"]), len(dados["abas"]) - 1)
    carregar_dados_na_cena(cena, dados["abas"][i], dados["tema"], dados["aventura"])
