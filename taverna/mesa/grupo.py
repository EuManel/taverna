"""
Retratos do grupo (estilo Baldur's Gate) — os dados.

O grupo são os tokens de JOGADOR da aba ao vivo. Vai numa lista separada da mesa, então o retrato
de um companheiro não some quando ele sai da visão de quem está olhando (névoa de guerra).

PV e condições respeitam o cadeado "quem vê" do INFORMAÇÕES, igual ao que aparece em cima do token:
o dono vê tudo do próprio; dos outros, só o que o mestre liberou. O mestre vê tudo.

Formato de cada retrato:
  {"id", "nome", "cor", "dono", "estado", "img": hash da imagem (retrato ou token) ou None,
   "pv": [atual, máx] ou None, "cond": [chaves], "dur": {chave: rodadas},
   "pv_oculto": bool, "cond_oculto": bool, "escondido": bool}   (os 3 últimos só pro mestre)
"""


def _tokens_de_jogador(cena, so_visiveis: bool):
    from .token import TokenItem
    tokens = []
    for camada in cena.camadas:
        for item in camada.itens():
            if not isinstance(item, TokenItem) or item.tipo != "jogador":
                continue
            visivel = item.isVisible() and camada.isVisible()
            if so_visiveis and not visivel:
                continue
            tokens.append((item, visivel))
    # ordem estável: pelo dono, depois pelo nome (cada um acha o seu no mesmo lugar sempre)
    tokens.sort(key=lambda tv: ((tv[0].dono or "~").casefold(), tv[0].nome.casefold()))
    return tokens


def montar_grupo(cena, mestre: bool = False) -> tuple[list[dict], dict]:
    """Retratos com tudo (pro mestre, ou pro servidor filtrar depois). Devolve (lista, imagens {hash: bytes})."""
    imagens = {}
    grupo = []
    for t, visivel in _tokens_de_jogador(cena, so_visiveis=not mestre):
        dados, chave = t.imagem_retrato()
        if dados:
            imagens[chave] = dados
        pv = t.info.get("pv") or {}
        cond = t.info.get("condicoes") or {}
        grupo.append({
            "id": t.uid, "nome": t.nome, "cor": t.cor.name(), "dono": t.dono, "estado": t.estado,
            "img": chave if dados else None,
            "pv": pv.get("v"), "cond": list(cond.get("v") or []), "dur": dict(cond.get("dur") or {}),
            "_vis_pv": pv.get("vis", "oculto"), "_vis_cond": cond.get("vis", "oculto"),
            "pv_oculto": pv.get("vis", "oculto") == "oculto",
            "cond_oculto": cond.get("vis", "oculto") == "oculto",
            "escondido": not visivel,
        })
    return grupo, imagens


def cartao_do_token(t) -> tuple[dict, dict]:
    """Retrato de um token qualquer (criatura no combate, por exemplo), com o que este lado da rede sabe dele.
    Devolve (cartão, imagens {hash: bytes})."""
    dados, chave = t.imagem_retrato()
    pv = t.info.get("pv") or {}
    cond = t.info.get("condicoes") or {}
    cartao = {"id": t.uid, "nome": t.nome, "cor": t.cor.name(), "dono": t.dono, "estado": t.estado,
              "img": chave if dados else None, "pv": pv.get("v"), "cond": list(cond.get("v") or []),
              "dur": dict(cond.get("dur") or {}), "tipo": t.tipo,
              "pv_oculto": pv.get("vis") == "oculto", "cond_oculto": cond.get("vis") == "oculto",
              "escondido": not t.isVisible()}
    return cartao, ({chave: dados} if dados else {})


def filtrar_grupo(grupo: list[dict], nome_jogador: str) -> list[dict]:
    """O que ESTE jogador pode ver de cada retrato (o resto vai vazio)."""
    from ..jogo.condicoes import pode_ver
    saida = []
    for r in grupo:
        d = {k: v for k, v in r.items() if not k.startswith("_") and k not in ("pv_oculto", "cond_oculto", "escondido")}
        if not pode_ver({"vis": r["_vis_pv"]}, nome_jogador, r["dono"]):
            d["pv"] = None
        if not pode_ver({"vis": r["_vis_cond"]}, nome_jogador, r["dono"]):
            d["cond"], d["dur"] = [], {}
        saida.append(d)
    return saida
