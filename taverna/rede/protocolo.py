"""
Protocolo de rede do Taverna (mensagens JSON via WebSocket).

Player -> Mestre
  {"tipo": "ola", "nome": "Manel", "versao": 2}     primeira mensagem
  {"tipo": "mover", "id": "<uid>", "x": 128, "y": 64} mover token próprio
  {"tipo": "rolar", "expr": "1d20+3", "motivo": "iniciativa"|"", "token": "<uid>"}
      quem rola é o MESTRE (o player só pede): ninguém trapaceia

Mestre -> Player
  {"tipo": "bem_vindo", "nome": "Manel"}
  {"tipo": "recusado", "motivo": "..."}             e a conexão é fechada
  {"tipo": "asset", "id": "<sha1>", "dados": "<base64>"}  imagem (enviada 1x)
  {"tipo": "rolagem", "quem", "expr", "total", "detalhes", "d20", "motivo"}
  {"tipo": "olhar_aqui", "x", "y", "escala", "travar": s}   (v0.58) 📣 câmera vai até o ponto (trava s segundos)
  {"tipo": "atlas", "chao", "cidade", "mundo", "marcadores"}   (v0.64) 🌍 cidade/mundo DESSE jogador (rede/atlas_rede.py)
  {"tipo": "atlas_pedaco", "nivel", "x", "y", "dados"}         pedaço de 256 px da imagem, só a parte revelada ("" = cobriu)
  {"tipo": "estado", ...}                           a mesa inteira (sem imagens)
      cada token leva só as informações (PV, condições...) que ESSE jogador pode ver;
      "combate" traz a ordem de iniciativa e de quem é a vez; "regras" diz se pode mover.
      "construcao" (terreno + paredes) só vem quando mudou desde o último envio.

O "estado" só leva o que está VISÍVEL na mesa do mestre. Camada ou item
escondido nunca sai do PC do mestre.
"""

import base64
import json

VERSAO_PROTOCOLO = 21   # 21 = v0.82+ (mensagem grande vai comprimida: binária "Z" + zlib); 20 = v0.78+ (token com "se": escala do standee); 19 = v0.77+ (token com "sb": standee sem bordas); 18 = v0.74+ (rolar/rolagem com "dv": a cara dos dados de quem rolou); 17 = v0.73+ (token com "es": ficha/standee); 16 = v0.65.1+ ("encerrar_turno": o jogador passa a própria vez) · 15 = v0.64.1+ ("criar_token": o jogador cria o PRÓPRIO token, um só) · 14 = v0.64+ ("atlas", "atlas_pedaco": cidade e mundo, só o revelado) · 13 = v0.58+ ("olhar_aqui": 📣 o mestre leva a câmera de todos) · 12 = v0.48+ ("editar_token" do jogador, "pegar_chao") · 11 = v0.46+ (andares: "andar" no estado, escada com "ligacao") · 10 = v0.45+ · 10 = v0.45+ (gás/líquido de cenário: "fluidos") · 9 = v0.43+ · 9 = v0.43+ (livros: "livros", "livro_*", "minha_biblioteca") · 8 = v0.41+ (áreas com "pontos"/"recortes"; "lancar"/"lancamento") · 7 = v0.39+ (marcas de efeito no terreno: {"t": "marca"}) · 6 = v0.31+ (retratos do grupo: "grupo" no estado) · 6 = v0.31+ (retratos do grupo: "grupo" no estado) · 5 = v0.25+ (impactos, lava)
PORTA_PADRAO = 7777


def codificar(msg: dict) -> str:
    return json.dumps(msg, ensure_ascii=False, separators=(",", ":"))


COMPRIMIR_A_PARTIR = 2048   # bytes: mensagem menor vai como texto mesmo


def enviar_grande(socket, texto: str):
    """(v0.82) Mensagem grande (a mesa, o histórico do chat…) vai COMPRIMIDA (zlib, binária, começa com "Z"): o JSON
    da mesa tem muita repetição e encolhe ~5–10×. Medido com 5 jogadores arrastando um goblin: ~3,5 Mbps de upload
    do mestre sem isso. Mensagem pequena continua texto."""
    if len(texto) < COMPRIMIR_A_PARTIR:
        socket.sendTextMessage(texto)
        return
    import zlib
    from PyQt6.QtCore import QByteArray
    socket.sendBinaryMessage(QByteArray(b"Z" + zlib.compress(texto.encode("utf-8"), 6)))


def abrir_binaria(dados) -> str | None:
    """O contrário do enviar_grande (com limite: nada de 'bomba' de 64 MB+)."""
    import zlib
    dados = bytes(dados)
    if not dados.startswith(b"Z"):
        return None
    try:
        d = zlib.decompressobj()
        bruto = d.decompress(dados[1:], 64 * 1024 * 1024)
        if d.unconsumed_tail:
            return None
        return bruto.decode("utf-8")
    except (zlib.error, UnicodeDecodeError):
        return None


def decodificar(texto: str) -> dict | None:
    try:
        msg = json.loads(texto)
        return msg if isinstance(msg, dict) and "tipo" in msg else None
    except (ValueError, TypeError):
        return None


def b64(dados: bytes) -> str:
    return base64.b64encode(dados).decode("ascii")


def de_b64(texto: str) -> bytes:
    return base64.b64decode(texto)


def montar_estado(cena) -> tuple[dict, dict]:
    """
    Tira uma "foto" do que os players podem ver.
    Retorna (estado, imagens) onde imagens = {hash: bytes}.
    """
    from ..mesa.mapa import MapaItem
    from ..mesa.luzes import LuzItem
    from ..mesa.portas import PortaItem
    from ..mesa.props import PropItem
    from ..mesa.token import TokenItem
    from ..mesa.efeitos import EfeitoItem

    imagens = {}
    camadas = []
    construcao = {"terreno": [], "paredes": []}
    for camada in cena.camadas:  # de baixo pra cima
        if camada.tipo == "grid":
            camadas.append({"grid": True, "visivel": camada.isVisible(), "itens": []})
            continue
        especial = camada.tipo if camada.tipo in ("terreno", "paredes", "luzes") else None
        if especial and camada.isVisible():
            if especial == "terreno" and cena.terreno:
                construcao["terreno"] = cena.terreno.para_lista()
            elif especial == "paredes" and cena.paredes:
                construcao["paredes"] = cena.paredes.para_lista()
        if not camada.isVisible():
            if especial:
                camadas.append({"especial": especial, "itens": []})
            continue
        itens = []
        for item in sorted(camada.itens(), key=lambda i: i.zValue()):
            if not item.isVisible():
                continue
            p = item.scenePos()
            if isinstance(item, MapaItem):
                imagens[item.hash_imagem] = item.dados
                itens.append({"classe": "mapa", "id": item.uid, "x": p.x(), "y": p.y(),
                              "w": item.w, "h": item.h, "img": item.hash_imagem})
            elif isinstance(item, TokenItem):
                if item.imagem:
                    imagens[item.hash_imagem] = item.imagem
                itens.append({"classe": "token", "id": item.uid, "x": p.x(), "y": p.y(),
                              "nome": item.nome, "tipo": item.tipo, "cor": item.cor.name(),
                              "tamanho": item.tamanho, "dono": item.dono,
                              "img": item.hash_imagem,
                              "va": item.visao_alcance, "vb": item.visao_abertura,
                              "dir": item.direcao, "giro": item.pode_girar,
                              "ve": item.visao_escuro, "_info": item.info, "luz": item.luz,
                              "estado": item.estado, "_ficha": item.ficha, "efeito": item.efeito,
                              "es": item.estilo, "sb": item.sem_borda, "se": item.escala_standee})
            elif isinstance(item, PropItem):
                # sem o conteúdo! (o que tem dentro só vai quando alguém abre)
                d = item.para_dict(com_itens=False)
                d["x"], d["y"] = p.x(), p.y()
                if item.imagem:
                    imagens[item.hash_imagem] = item.imagem
                d["img"] = item.hash_imagem
                itens.append(d)
            elif isinstance(item, PortaItem):
                d = item.para_dict()
                for segredo in ("trancada", "chave", "gasta_chave"):
                    d.pop(segredo, None)   # o jogador só descobre tentando
                d["x"], d["y"] = p.x(), p.y()
                itens.append(d)
            elif isinstance(item, LuzItem):
                d = item.para_dict()
                d["x"], d["y"] = p.x(), p.y()
                itens.append(d)
            elif isinstance(item, EfeitoItem):
                d = item.para_dict()
                d["x"], d["y"] = p.x(), p.y()
                itens.append(d)
        camadas.append({"grid": False, "especial": especial, "itens": itens})

    estado = {
        "tipo": "estado",
        "aventura": getattr(cena, "nome_aventura", ""),
        "cenario": getattr(cena, "uid", ""),
        "cenario_nome": getattr(cena, "nome_aba", ""),
        "tema": getattr(cena, "tema", "medieval"),
        "construcao": construcao,
        "snap": cena.snap_ativo,
        "nevoa": getattr(cena, "nevoa_ativa", False),
        "ambiente": getattr(cena, "luz_ambiente", "dia"),
        "opacidade_grid": cena.opacidade_grid,
        "clima": dict(getattr(cena, "clima", {}) or {}),
        "desenhos": [{k: v for k, v in t.items() if k != "ate"} for t in getattr(cena, "tracos", [])],
        "camadas": camadas,
    }
    return estado, imagens


def filtrar_pela_visao(estado: dict, nome_jogador: str) -> dict:
    """
    Névoa de guerra: tira do estado os tokens que esse jogador NÃO consegue ver.
    (Assim nem chega no PC dele — não tem como "espiar".)
    """
    if not estado.get("nevoa"):
        return estado
    from PyQt6.QtCore import QPointF
    from ..config import CELULA
    from ..mesa.linha_de_visao import caminho_da_visao, obstaculos, poligono, ponto_visivel

    from PyQt6.QtCore import Qt
    from ..mesa.luzes import luzes_acesas, poligonos_de_luz
    tokens = [d for c in estado["camadas"] for d in c["itens"] if d["classe"] == "token"]
    from ..mesa.luzes import luzes_extras
    portas = [d for c in estado["camadas"] for d in c["itens"] if d["classe"] in ("porta", "prop", "efeito")]
    luzes = [d for c in estado["camadas"] for d in c["itens"] if d["classe"] == "luz"]
    luzes += luzes_extras([d for c in estado["camadas"] for d in c["itens"]
                           if d["classe"] in ("prop", "token", "efeito")])
    obst = obstaculos(estado["construcao"]["paredes"], portas)
    escuro_total = estado.get("ambiente") == "escuro"
    polys_luz = poligonos_de_luz(luzes_acesas(luzes), obst) if escuro_total else []
    visoes = []   # (cone, visão no escuro)
    for d in tokens:
        if d["tipo"] == "jogador" and mesmo_nome(d["dono"], nome_jogador):
            meio = d["tamanho"] * CELULA / 2
            cx, cy = d["x"] + meio, d["y"] + meio
            cone = poligono(cx, cy, d["dir"], d["vb"], d["va"], obst)
            ve = min(float(d.get("ve", 0)), float(d["va"]))
            escuro = poligono(cx, cy, 0, 360, ve, obst) if ve > 0 and escuro_total else None
            visoes.append((cone, escuro))

    def ve_ponto(x, y):
        ponto = QPointF(x, y)
        for cone, escuro in visoes:
            if not cone.containsPoint(ponto, Qt.FillRule.OddEvenFill):
                continue
            if not escuro_total:
                return True
            if escuro is not None and escuro.containsPoint(ponto, Qt.FillRule.OddEvenFill):
                return True
            if any(pol.containsPoint(ponto, Qt.FillRule.OddEvenFill) for _, pol in polys_luz):
                return True
        return False

    def pode_ver(d):
        if d["classe"] != "token":
            return True   # mapas, portas e luzes sempre vão (a névoa cobre na tela)
        if d["tipo"] == "jogador" and mesmo_nome(d["dono"], nome_jogador):
            return True
        meio = d["tamanho"] * CELULA / 2
        cx, cy = d["x"] + meio, d["y"] + meio
        r = meio * 0.8
        return any(ve_ponto(cx + dx, cy + dy)
                   for dx, dy in ((0, 0), (r, 0), (-r, 0), (0, r), (0, -r)))

    novo = dict(estado)
    novo["camadas"] = [dict(c, itens=[d for d in c["itens"] if pode_ver(d)])
                       for c in estado["camadas"]]
    return novo


def mesmo_nome(a: str, b: str) -> bool:
    return a.strip().casefold() == b.strip().casefold() and a.strip() != ""


def filtrar_info(estado: dict, nome_jogador: str) -> dict:
    # Painel de informações: cada token leva só os campos que esse jogador pode ver
    # (o dono vê tudo do próprio token; o resto depende do que o mestre revelou).
    # No combate, criaturas que ele não está vendo aparecem como "???".
    from ..jogo.condicoes import pode_ver
    visiveis = set()
    camadas = []
    for c in estado["camadas"]:
        itens = []
        for d in c["itens"]:
            if d.get("classe") == "token":
                d = dict(d)
                info = d.pop("_info", {}) or {}
                ficha = d.pop("_ficha", None)
                if ficha and mesmo_nome(d.get("dono", ""), nome_jogador):
                    d["ficha"] = ficha     # a ficha só vai pro dono
                d["info"] = {k: dict({"v": campo.get("v"), "vis": "todos"},
                                     **({"dur": campo["dur"]} if campo.get("dur") else {}))
                             for k, campo in info.items()
                             if pode_ver(campo, nome_jogador, d.get("dono", ""))}
                visiveis.add(d["id"])
            itens.append(d)
        camadas.append(dict(c, itens=itens))
    novo = dict(estado, camadas=camadas)
    combate = estado.get("combate")
    if combate and combate.get("ativo"):
        # companheiro de grupo (token de jogador) nunca vira "???": os retratos do grupo já mostram ele
        conhecidos = visiveis | {p["id"] for p in combate["ordem"] if p.get("tipo") == "jogador"}
        ordem = []
        for p in combate["ordem"]:
            p = dict(p)
            if p["id"] not in conhecidos:
                p["nome"] = "???"
            ordem.append(p)
        vez = combate["vez"]
        novo["combate"] = dict(combate, ordem=ordem,
                               vez=vez if vez is None or vez in conhecidos else "?")
    return novo
