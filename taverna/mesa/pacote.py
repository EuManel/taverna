"""
📦 Pacote de aventura (.tavernapack) — v0.61, item 8 dos PEDIDOS_v0.58.

Um .zip com:
  manifesto.json   nome, versão do Taverna, contagens, o aviso de direitos
  aventura.json    a aventura (igual ao .taverna), mas com as imagens trocadas por "@pacote:imagens/…"
  imagens/<Pasta>/<hash>.<ext>   mapas, tokens, objetos, projetor (cada imagem uma vez só)
  tabelas/<nome>.json            tabelas de sorteio usadas nos baús
  LEIA-ME.txt

NÃO vão: PDFs, fichas dos jogadores (tokens de jogador vão sem ficha), o diário da campanha (só se o mestre
marcar). Música do YouTube não é salva na aventura. Importar: a aventura vai pra pasta de aventuras, as imagens
pro banco de imagens e as tabelas pras tabelas de sorteio — SEM sobrescrever nada (renomeia se repetir; o que
já existe igualzinho não é copiado de novo).
"""

import base64
import copy
import hashlib
import json
import os
import re
import zipfile

from ..config import APP_NOME, APP_VERSAO, EXTENSAO_CENA

EXTENSAO = ".tavernapack"
FILTRO = "Pacote de aventura do Taverna (*.tavernapack)"
AVISO = ("Só compartilhe o que você tem direito de compartilhar: mapas, imagens e textos de outras pessoas "
         "ou de livros podem ter direitos autorais.")
FORMATO = 1
PREFIXO = "@pacote:"
LIMITE_ARQUIVO = 200 * 1024 * 1024   # (não abre "bomba de zip": nenhum arquivo de dentro passa disso)
_CATEGORIA = {"mapa": "Mapas", "token": "Tokens", "prop": "Objetos"}


class ErroPacote(ValueError):
    pass


def _seguro(nome: str, padrao: str = "Aventura") -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", str(nome or "")).strip().rstrip(".")[:80] or padrao


def _extensao(dados: bytes) -> str:
    if dados.startswith(b"\x89PNG"):
        return ".png"
    if dados.startswith(b"\xff\xd8"):
        return ".jpg"
    if dados[:4] == b"RIFF" and dados[8:12] == b"WEBP":
        return ".webp"
    if dados.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if dados.startswith(b"BM"):
        return ".bmp"
    return ".bin"


# ====================================================================== exportar
def _tirar_imagens(obj, arquivos: dict, nomes: dict, categoria: str = "Outros", nome: str = ""):
    """Troca cada imagem em base64 por uma referência e guarda os bytes (cada imagem uma vez só)."""
    if isinstance(obj, list):
        for x in obj:
            _tirar_imagens(x, arquivos, nomes, categoria, nome)
        return
    if not isinstance(obj, dict):
        return
    classe = obj.get("classe")
    if isinstance(classe, str):
        categoria = _CATEGORIA.get(classe, categoria)
    rotulo = obj.get("nome") or obj.get("titulo")
    if isinstance(rotulo, str) and rotulo:
        nome = rotulo
    for chave in list(obj):
        valor = obj[chave]
        if chave in ("imagem", "img") and isinstance(valor, str) and len(valor) > 64 \
                and not valor.startswith(PREFIXO):
            try:
                dados = base64.b64decode(valor, validate=True)
            except (ValueError, TypeError):
                continue
            h = hashlib.sha1(dados).hexdigest()[:20]
            caminho = f"imagens/{categoria}/{h}{_extensao(dados)}"
            if not any(c.endswith(h + _extensao(dados)) for c in arquivos):
                arquivos[caminho] = dados
                nomes[caminho] = nome or h
            else:
                caminho = next(c for c in arquivos if c.endswith(h + _extensao(dados)))
            obj[chave] = PREFIXO + caminho
        else:
            _tirar_imagens(valor, arquivos, nomes, categoria, nome)


def _tabelas_usadas(obj, achadas: dict):
    if isinstance(obj, list):
        for x in obj:
            _tabelas_usadas(x, achadas)
    elif isinstance(obj, dict):
        sorteio = obj.get("sorteio")
        if isinstance(sorteio, dict) and isinstance(sorteio.get("tabela"), dict) and sorteio["tabela"].get("nome"):
            t = sorteio["tabela"]
            achadas.setdefault(json.dumps(t, sort_keys=True, ensure_ascii=False), t)
        for v in obj.values():
            _tabelas_usadas(v, achadas)


def preparar(dados: dict, levar_diario: bool = False) -> tuple[dict, dict, dict, list]:
    """(aventura sem imagens, {caminho: bytes}, {caminho: nome}, [tabelas]) — não mexe no original."""
    d = copy.deepcopy(dados)
    if not levar_diario:
        d["diario"] = []
    for aba in d.get("abas", []):          # fichas dos JOGADORES não vão (as das criaturas do mestre vão)
        for camada in aba.get("camadas", []):
            for item in camada.get("itens", []):
                if item.get("classe") == "token" and item.get("tipo") == "jogador":
                    item["ficha"] = None
    achadas: dict = {}
    _tabelas_usadas(d, achadas)
    arquivos, nomes = {}, {}
    _tirar_imagens(d.get("abas", []), arquivos, nomes)
    _tirar_imagens(d.get("projetor", []), arquivos, nomes, "Projetor")
    _tirar_imagens(d.get("atlas", {}), arquivos, nomes, "Mapas")    # cidades e mundo (v0.62)
    return d, arquivos, nomes, list(achadas.values())


def exportar(caminho: str, dados: dict, levar_diario: bool = False) -> dict:
    """Grava o .tavernapack. Devolve o resumo (imagens, tabelas, abas, tamanho)."""
    d, arquivos, nomes, tabelas = preparar(dados, levar_diario)
    manifesto = {"formato": FORMATO, "app": APP_NOME, "versao_app": APP_VERSAO, "aventura": d.get("aventura", ""),
                 "abas": len(d.get("abas", [])), "imagens": len(arquivos), "tabelas": len(tabelas),
                 "nomes": nomes, "aviso": AVISO}
    temporario = caminho + ".salvando"
    with zipfile.ZipFile(temporario, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifesto.json", json.dumps(manifesto, ensure_ascii=False, indent=1))
        z.writestr("aventura.json", json.dumps(d, ensure_ascii=False))
        for arq, dados_img in arquivos.items():
            z.writestr(arq, dados_img, compress_type=zipfile.ZIP_STORED)   # (imagem já vem comprimida)
        usados = set()
        for t in tabelas:
            base = _seguro(t["nome"], "Tabela")
            nome_arq, k = base, 2
            while nome_arq in usados:
                nome_arq, k = f"{base} ({k})", k + 1
            usados.add(nome_arq)
            z.writestr(f"tabelas/{nome_arq}.json", json.dumps(t, ensure_ascii=False, indent=1))
        z.writestr("LEIA-ME.txt",
                   f"Pacote de aventura do {APP_NOME}: “{d.get('aventura', '')}”.\r\n"
                   f"Abra no {APP_NOME}: Arquivo → Importar pacote de aventura.\r\n\r\n{AVISO}\r\n")
    os.replace(temporario, caminho)
    return {"imagens": len(arquivos), "tabelas": len(tabelas), "abas": manifesto["abas"],
            "tamanho": os.path.getsize(caminho)}


# ====================================================================== importar
def _ler_bytes(z: zipfile.ZipFile, nome: str) -> bytes:
    info = z.getinfo(nome)
    if info.file_size > LIMITE_ARQUIVO:
        raise ErroPacote(f"Arquivo grande demais dentro do pacote: {nome}")
    return z.read(nome)


def _por_imagens(obj, z: zipfile.ZipFile, cache: dict):
    if isinstance(obj, list):
        for x in obj:
            _por_imagens(x, z, cache)
    elif isinstance(obj, dict):
        for chave, valor in list(obj.items()):
            if isinstance(valor, str) and valor.startswith(PREFIXO):
                arq = valor[len(PREFIXO):]
                if arq not in cache:
                    try:
                        cache[arq] = base64.b64encode(_ler_bytes(z, arq)).decode("ascii")
                    except KeyError:
                        cache[arq] = None   # imagem faltando: o item abre sem ela
                obj[chave] = cache[arq]
            else:
                _por_imagens(valor, z, cache)


def ler(caminho: str) -> dict:
    """Abre o pacote: {"manifesto", "aventura" (com as imagens de volta em base64), "imagens": [(pasta, nome,
    bytes)], "tabelas": [dict]}."""
    try:
        z = zipfile.ZipFile(caminho)
    except (OSError, zipfile.BadZipFile) as erro:
        raise ErroPacote(f"Não consegui abrir o pacote: {erro}") from erro
    with z:
        nomes = set(z.namelist())
        if "aventura.json" not in nomes or "manifesto.json" not in nomes:
            raise ErroPacote("Esse arquivo não é um pacote de aventura do Taverna.")
        try:
            manifesto = json.loads(_ler_bytes(z, "manifesto.json").decode("utf-8"))
            aventura = json.loads(_ler_bytes(z, "aventura.json").decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as erro:
            raise ErroPacote(f"O pacote está estragado: {erro}") from erro
        if manifesto.get("app") != APP_NOME or aventura.get("app") != APP_NOME:
            raise ErroPacote("Esse arquivo não é um pacote de aventura do Taverna.")
        if int(manifesto.get("formato", 0)) > FORMATO:
            raise ErroPacote("Esse pacote foi feito numa versão mais nova do Taverna. Atualize o programa.")
        _por_imagens(aventura, z, {})
        rotulos = manifesto.get("nomes") or {}
        imagens = []
        for arq in sorted(nomes):
            partes = arq.split("/")
            if len(partes) == 3 and partes[0] == "imagens" and not arq.endswith("/"):
                imagens.append((_seguro(partes[1], "Outros"), str(rotulos.get(arq) or partes[2]), _ler_bytes(z, arq),
                                os.path.splitext(partes[2])[1].lower()))
        tabelas = []
        for arq in sorted(nomes):
            if arq.startswith("tabelas/") and arq.endswith(".json"):
                try:
                    t = json.loads(_ler_bytes(z, arq).decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    continue
                if isinstance(t, dict) and t.get("nome"):
                    t.setdefault("linhas", [])
                    tabelas.append(t)
    return {"manifesto": manifesto, "aventura": aventura, "imagens": imagens, "tabelas": tabelas}


def _livre(pasta: str, base: str, ext: str) -> str:
    caminho = os.path.join(pasta, base + ext)
    k = 2
    while os.path.exists(caminho):
        caminho = os.path.join(pasta, f"{base} ({k}){ext}")
        k += 1
    return caminho


def _hashes(pasta: str) -> set:
    saida = set()
    try:
        for arq in os.listdir(pasta):
            p = os.path.join(pasta, arq)
            if os.path.isfile(p):
                with open(p, "rb") as f:
                    saida.add(hashlib.sha1(f.read()).hexdigest())
    except OSError:
        pass
    return saida


def instalar(caminho: str, pasta_aventuras: str, pasta_banco: str | None, pasta_tabelas: str | None) -> dict:
    """Extrai o pacote SEM sobrescrever nada. Devolve {"aventura": caminho do .taverna, "nome", "imagens",
    "imagens_repetidas", "tabelas", "tabelas_repetidas", "tabelas_renomeadas"}."""
    p = ler(caminho)
    av = p["aventura"]
    nome = av.get("aventura") or os.path.splitext(os.path.basename(caminho))[0]
    os.makedirs(pasta_aventuras, exist_ok=True)
    destino = _livre(pasta_aventuras, _seguro(nome), EXTENSAO_CENA)
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(av, f, ensure_ascii=False)
    res = {"aventura": destino, "nome": nome, "imagens": 0, "imagens_repetidas": 0, "tabelas": 0,
           "tabelas_repetidas": 0, "tabelas_renomeadas": 0}
    if pasta_banco:
        conhecidas: dict = {}
        for pasta_nome, rotulo, dados, ext in p["imagens"]:
            if ext == ".bin":
                continue
            pasta = os.path.join(pasta_banco, pasta_nome)
            os.makedirs(pasta, exist_ok=True)
            if pasta not in conhecidas:
                conhecidas[pasta] = _hashes(pasta)
            h = hashlib.sha1(dados).hexdigest()
            if h in conhecidas[pasta]:
                res["imagens_repetidas"] += 1
                continue
            alvo = _livre(pasta, _seguro(f"{nome} - {rotulo}", "imagem"), ext)
            with open(alvo, "wb") as f:
                f.write(dados)
            conhecidas[pasta].add(h)
            res["imagens"] += 1
    if pasta_tabelas:
        os.makedirs(pasta_tabelas, exist_ok=True)
        for t in p["tabelas"]:
            base = _seguro(t["nome"], "Tabela")
            atual = os.path.join(pasta_tabelas, base + ".json")
            if os.path.exists(atual):
                try:
                    with open(atual, encoding="utf-8") as f:
                        if json.load(f) == t:
                            res["tabelas_repetidas"] += 1
                            continue
                except (OSError, ValueError):
                    pass
                t = dict(t)
                k = 2
                while os.path.exists(os.path.join(pasta_tabelas, _seguro(f"{t['nome']} ({k})") + ".json")):
                    k += 1
                t["nome"] = f"{t['nome']} ({k})"
                res["tabelas_renomeadas"] += 1
            with open(os.path.join(pasta_tabelas, _seguro(t["nome"], "Tabela") + ".json"), "w", encoding="utf-8") as f:
                json.dump(t, f, ensure_ascii=False, indent=1)
            res["tabelas"] += 1
    return res
