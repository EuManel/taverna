"""
Gatilhos e armadilhas.

Um gatilho mora num OBJETO (dispara quando um jogador abre/mexe nele) ou numa ÁREA no chão
(dispara quando o token de um jogador entra nela). A área é invisível pros jogadores.

gatilho = {
  "nome": "Armadilha de agulha", "ativo": True, "uma_vez": True, "disparado": False,
  "quando": "abrir" | "mover" | "entrar",
  "acoes": [ {"tipo": ...}, ... ]
}

Ações:
  porta     {"ids": [...], "estado": "abrir" | "fechar" | "alternar"}
  luz       {"ids": [...] ou "todas", "estado": "apagar" | "acender" | "alternar"}
  revelar   {"ids": [...]}                       tokens/objetos escondidos aparecem
  esconder  {"ids": [...]}
  mensagem  {"texto": "...", "para": "quem" | "todos"}
  dano      {"expr": "2d6", "condicao": "" , "rodadas": 0}   no token de quem disparou
  ping      {}                                    sinal no lugar pra todo mundo
  ambiente  {"valor": "dia" | "penumbra" | "escuro"}
"""

import copy

TIPOS_ACAO = {
    "mensagem": "💬 Mostrar mensagem",
    "dano": "🩸 Dano / condição em quem disparou",
    "porta": "🚪 Abrir/fechar portas",
    "luz": "💡 Apagar/acender luzes",
    "revelar": "👁 Fazer aparecer (monstros, objetos escondidos)",
    "esconder": "🙈 Esconder coisas",
    "ambiente": "🌑 Mudar a luz ambiente",
    "ping": "📍 Sinal no lugar (ping)",
    "impacto": "💥 Efeito de impacto (explosão, raio, tremor…)",
}
QUANDO = {"abrir": "quando um jogador ABRIR/mexer nele",
          "mover": "quando um jogador MOVER o objeto",
          "entrar": "quando um jogador ENTRAR na área"}


def gatilho_novo(origem: str = "prop") -> dict:
    return {"nome": "Armadilha" if origem == "prop" else "Área de armadilha", "ativo": True,
            "uma_vez": True, "disparado": False, "quando": "abrir" if origem == "prop" else "entrar",
            "acoes": [], "so_jogadores": True}


def descrever_acao(a: dict, nomes: dict | None = None) -> str:
    nomes = nomes or {}
    t = a.get("tipo")

    def lista(ids):
        if ids == "todas":
            return "todas"
        return ", ".join(nomes.get(i, "?") for i in (ids or [])) or "nenhuma"
    if t == "mensagem":
        return f"💬 “{(a.get('texto') or '')[:40]}” ({'todos' if a.get('para') == 'todos' else 'quem disparou'})"
    if t == "dano":
        extra = f" + {a['condicao']}" if a.get("condicao") else ""
        dur = f" ({a['rodadas']} rod.)" if a.get("rodadas") else ""
        return f"🩸 {a.get('expr') or '0'} de dano{extra}{dur}"
    if t == "porta":
        return f"🚪 {a.get('estado', 'fechar')}: {lista(a.get('ids'))}"
    if t == "luz":
        return f"💡 {a.get('estado', 'apagar')}: {lista(a.get('ids'))}"
    if t == "revelar":
        return f"👁 aparecer: {lista(a.get('ids'))}"
    if t == "esconder":
        return f"🙈 esconder: {lista(a.get('ids'))}"
    if t == "ambiente":
        return f"🌑 luz ambiente: {a.get('valor', 'escuro')}"
    if t == "impacto":
        from ..mesa.impactos import IMPACTOS
        return f"{IMPACTOS.get(a.get('efeito', 'explosao'), ('💥',))[0]} no lugar"
    if t == "ping":
        return "📍 ping no lugar"
    return t or "?"


def pode_disparar(g: dict | None) -> bool:
    return bool(g) and g.get("ativo", True) and not (g.get("uma_vez", True) and g.get("disparado"))


def executar(servidor, g: dict, quem: str, token, pos, conexao=None) -> list[str]:
    """Faz as ações acontecerem na mesa ao vivo. Devolve um resumo (pro histórico)."""
    from ..jogo.dados import ErroDados
    from ..mesa.luzes import LuzItem
    from ..mesa.portas import PortaItem
    from ..mesa.props import PropItem
    from ..rede.protocolo import codificar
    cena = servidor.cena
    feito = []
    for a in g.get("acoes", []):
        t = a.get("tipo")
        ids = a.get("ids") or []
        itens = [cena.item_por_id(i) for i in ids] if isinstance(ids, list) else []
        itens = [i for i in itens if i is not None]
        if t == "mensagem" and a.get("texto"):
            msg = codificar({"tipo": "aviso", "texto": a["texto"], "longo": True})
            alvos = [c for c in servidor.conexoes if c.nome] if a.get("para") == "todos" else \
                [conexao] if conexao is not None else []
            for c in alvos:
                c.socket.sendTextMessage(msg)
            feito.append("mensagem")
        elif t == "dano" and token is not None:
            texto = []
            if a.get("expr"):
                try:
                    r = servidor.rolar_mestre(a["expr"], privada=False, motivo=f"armadilha em {token.nome}")
                    pv = token.info.get("pv", {}).get("v")
                    if pv:
                        novo = int(pv[0]) - max(0, int(r["total"]))
                        token.definir_info("pv", [novo, pv[1]])
                        if novo <= 0 and token.estado is None:
                            token.definir_estado("caido" if token.tipo == "jogador" else "morto")
                    texto.append(f"{r['total']} de dano")
                except ErroDados:
                    pass
            if a.get("condicao"):
                campo = token.info.setdefault("condicoes", {"v": [], "vis": "oculto"})
                lista = list(campo.get("v") or [])
                if a["condicao"] not in lista:
                    lista.append(a["condicao"])
                if a.get("rodadas"):
                    dur = dict(campo.get("dur") or {})
                    dur[a["condicao"]] = int(a["rodadas"])
                    campo["dur"] = dur
                token.definir_info("condicoes", lista)
                texto.append(a["condicao"])
            if texto:
                feito.append(f"{token.nome}: " + " + ".join(texto))
        elif t == "porta":
            for p in itens:
                if isinstance(p, PortaItem):
                    estado = a.get("estado", "fechar")
                    if estado == "trancar":
                        if p.aberta:
                            p.alternar()
                        p.trancada = True
                        p.mudou()
                        continue
                    if estado == "destrancar":
                        p.trancada = False
                        p.mudou()
                        continue
                    quer = (not p.aberta) if estado == "alternar" else (estado == "abrir")
                    if p.aberta != quer:
                        p.alternar()
            feito.append(f"portas: {a.get('estado', 'fechar')}")
        elif t == "luz":
            alvo = itens
            if ids == "todas":
                alvo = [i for i in cena.itens_do_usuario() if isinstance(i, LuzItem)] + \
                       [i for i in cena.itens_do_usuario() if isinstance(i, PropItem) and i.luz]
            for l in alvo:
                if isinstance(l, LuzItem):
                    quer = (not l.acesa) if a.get("estado") == "alternar" else (a.get("estado") == "acender")
                    if l.acesa != quer:
                        l.alternar()
                elif isinstance(l, PropItem):
                    quer = (not l.luz_acesa) if a.get("estado") == "alternar" else (a.get("estado") == "acender")
                    l.luz_acesa = quer
                    l._mudou()
            feito.append(f"luzes: {a.get('estado', 'apagar')}")
        elif t in ("revelar", "esconder"):
            for i in itens:
                cena.definir_item_visivel(i, t == "revelar")
            feito.append(f"{'apareceu' if t == 'revelar' else 'sumiu'}: {', '.join(getattr(i, 'nome', '?') for i in itens)}")
        elif t == "ambiente" and hasattr(cena, "definir_ambiente"):
            cena.definir_ambiente(a.get("valor", "escuro"))
            feito.append(f"luz ambiente: {a.get('valor')}")
        elif t == "impacto":
            x, y = pos if pos is not None else (0.0, 0.0)
            servidor.impacto(a.get("efeito", "explosao"), x, y, float(a.get("tam", 3.0)))
            feito.append(f"efeito: {a.get('efeito', 'explosao')}")
        elif t == "ping" and pos is not None:
            servidor.ping_mestre(pos[0], pos[1])
            servidor.ping.emit("⚡", pos[0], pos[1])
            feito.append("ping")
    g["disparado"] = True
    return feito


def copia(g):
    return copy.deepcopy(g)
