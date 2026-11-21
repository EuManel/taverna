"""
Rolagem de dados: "2d6+3", "1d20+5-1d4", "d20", "4d6kh3" (fica com os 3 maiores),
"2d20kh1" (vantagem), "2d20kl1" (desvantagem), "d%" ou "d100".

As rolagens são feitas SEMPRE no computador do mestre (assim ninguém trapaceia).
"""

import random
import re

_TERMO = re.compile(r"([+-]?)\s*(?:(\d*)d(\d+|%)(?:(kh|kl)(\d+))?|(\d+))", re.IGNORECASE)
MAX_DADOS = 100
MAX_LADOS = 1000
MAX_FISICOS = 10   # dados 3D na mesa: no máximo 10 rolando (o total vale sempre pra todos)


class ErroDados(ValueError):
    pass


def rolar(expressao: str, rng=random) -> dict:
    """
    Retorna {"expr", "total", "detalhes", "d20": valor natural do d20 (se for 1 dado d20), "termos"}.
    """
    texto = (expressao or "").replace(" ", "").lower()
    if not texto:
        raise ErroDados("Digite uma rolagem, tipo 1d20+3.")
    if not texto[0] in "+-":
        texto = "+" + texto
    pos, total, partes, d20s = 0, 0, [], []
    fisicos = []   # cada dado rolado, pros dados 3D na mesa: {"lados", "valor", "fora": descartado (kh/kl)}
    for m in _TERMO.finditer(texto):
        if m.start() != pos:
            raise ErroDados(f"Não entendi “{expressao}”. Use algo como 2d6+3.")
        pos = m.end()
        sinal = -1 if m.group(1) == "-" else 1
        if m.group(6) is not None:  # número solto
            valor = int(m.group(6))
            total += sinal * valor
            partes.append(f"{'-' if sinal < 0 else '+'} {valor}")
            continue
        qtd = int(m.group(2) or 1)
        lados = 100 if m.group(3) == "%" else int(m.group(3))
        if not (1 <= qtd <= MAX_DADOS) or not (2 <= lados <= MAX_LADOS):
            raise ErroDados(f"Exagerou: até {MAX_DADOS} dados de até {MAX_LADOS} lados.")
        valores = [rng.randint(1, lados) for _ in range(qtd)]
        usados = list(range(qtd))
        if m.group(4):
            manter = max(1, min(qtd, int(m.group(5))))
            ordem = sorted(range(qtd), key=lambda k: valores[k], reverse=(m.group(4) == "kh"))
            usados = sorted(ordem[:manter])
        soma = sum(valores[k] for k in usados)
        fisicos.extend({"lados": lados, "valor": v, "fora": k not in usados} for k, v in enumerate(valores))
        total += sinal * soma
        if lados == 20 and (len(usados) == 1):
            d20s.append(valores[usados[0]])
        mostrados = ", ".join(str(v) if k in usados else f"~{v}~" for k, v in enumerate(valores))
        rotulo = f"{qtd}d{lados}" + (f"{m.group(4)}{m.group(5)}" if m.group(4) else "")
        partes.append(f"{'-' if sinal < 0 else '+'} {rotulo}[{mostrados}]")
    if pos != len(texto):
        raise ErroDados(f"Não entendi “{expressao}”. Use algo como 2d6+3.")
    detalhes = " ".join(partes).lstrip("+ ").strip()
    return {"expr": expressao.strip(), "total": total, "detalhes": detalhes,
            "d20": d20s[0] if len(d20s) == 1 else None,
            "fisicos": fisicos[:MAX_FISICOS],
            "semente": rng.randint(1, 2 ** 31 - 1)}   # mesma semente = mesmo dado quicando em todos os PCs


def modificador(valor: int) -> str:
    return f"+{valor}" if valor >= 0 else str(valor)
