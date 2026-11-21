"""
Tabelas de sorteio personalizadas (pra qualquer sistema: Ordem Paranormal, Cyberpunk, Tormenta...).

Cada tabela é um arquivo .json em Documentos/Taverna/Tabelas de sorteio — vale pra todas as aventuras
e dá pra mandar pros amigos. Quando o mestre escolhe uma tabela num baú, uma CÓPIA dela vai junto
com o baú (assim a aventura abre igual em outro PC, mesmo sem o arquivo da tabela).

Tabela: {"nome", "moeda": "Créditos", "moeda_dados": "2d10", "linhas": [{"nome", "qtd", "chance", "desc"}]}
  qtd: "1", "3" ou dados ("2d10")
  chance: "comum" | "incomum" | "raro" | "muito raro"
"""

import json
import os
import re

CHANCES = {"comum": 10, "incomum": 5, "raro": 2, "muito raro": 0.6}
_SINONIMOS = {"rara": "raro", "muito rara": "muito raro", "comuns": "comum"}


def pasta_tabelas() -> str:
    from PyQt6.QtCore import QStandardPaths
    docs = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation) \
        or os.path.expanduser("~")
    pasta = os.path.join(docs, "Taverna", "Tabelas de sorteio")
    os.makedirs(pasta, exist_ok=True)
    return pasta


def _arquivo(nome: str) -> str:
    seguro = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", nome).strip().rstrip(".") or "Tabela"
    return os.path.join(pasta_tabelas(), seguro + ".json")


def tabela_vazia(nome: str = "Nova tabela") -> dict:
    return {"nome": nome, "moeda": "", "moeda_dados": "", "linhas": []}


def listar() -> list[dict]:
    tabelas = []
    for arq in sorted(os.listdir(pasta_tabelas())):
        if arq.lower().endswith(".json"):
            try:
                with open(os.path.join(pasta_tabelas(), arq), encoding="utf-8") as f:
                    t = json.load(f)
                if isinstance(t, dict) and t.get("nome"):
                    t.setdefault("linhas", [])
                    tabelas.append(t)
            except (OSError, ValueError):
                pass
    return tabelas


def salvar(tabela: dict, nome_antigo: str | None = None):
    if nome_antigo and nome_antigo != tabela["nome"]:
        apagar(nome_antigo)
    with open(_arquivo(tabela["nome"]), "w", encoding="utf-8") as f:
        json.dump(tabela, f, ensure_ascii=False, indent=1)


def apagar(nome: str):
    try:
        os.remove(_arquivo(nome))
    except OSError:
        pass


def ler_texto(texto: str) -> list[dict]:
    """
    Lista colada (um item por linha), ex.:
        Pistola
        Fuzil de assalto [raro]
        Munição ×2d10 [comum]
        Kit médico | Recupera 2d8 PV
    """
    linhas = []
    for bruta in (texto or "").splitlines():
        linha = bruta.strip().lstrip("•-*·").strip()
        if not linha:
            continue
        nome, _, desc = linha.partition("|")
        chance = "comum"
        m = re.search(r"\[([^\]]+)\]", nome)
        if m:
            c = m.group(1).strip().lower()
            c = _SINONIMOS.get(c, c)
            if c in CHANCES:
                chance = c
            nome = (nome[:m.start()] + nome[m.end():]).strip()
        qtd = "1"
        m = re.search(r"\s*[x×]\s*(\d+(?:d\d+)?(?:[+-]\d+)?)\s*$", nome.strip(), re.IGNORECASE)
        if m:
            qtd = m.group(1)
            nome = nome.strip()[:m.start()]
        if nome.strip():
            linhas.append({"nome": nome.strip(), "qtd": qtd, "chance": chance, "desc": desc.strip()})
    return linhas


def para_texto(linhas: list[dict]) -> str:
    saida = []
    for l in linhas:
        t = l["nome"]
        if str(l.get("qtd", "1")) not in ("", "1"):
            t += f" ×{l['qtd']}"
        if l.get("chance", "comum") != "comum":
            t += f" [{l['chance']}]"
        if l.get("desc"):
            t += f" | {l['desc']}"
        saida.append(t)
    return "\n".join(saida)
