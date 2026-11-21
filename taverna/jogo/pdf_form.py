"""
Formulários PDF genéricos (Etapa 14): qualquer ficha em PDF editável, de qualquer sistema.

O Taverna não precisa "entender" a ficha: ele acha os campos (caixas de texto, checkboxes,
botões de opção, listas), mostra na tela por cima da página e grava de volta no PDF.
"""

import io

from pypdf import PdfReader, PdfWriter
from pypdf.generic import BooleanObject, NameObject, TextStringObject

# bits do /Ff (flags do campo)
_SO_LEITURA = 1
_MULTILINHA = 1 << 12
_SENHA = 1 << 13
_SEM_DESMARCAR = 1 << 14
_RADIO = 1 << 15
_BOTAO = 1 << 16
_COMBO = 1 << 17


def _herdado(widget, chave):
    """Valor de uma chave no widget ou nos 'pais' dele (campos podem ser hierárquicos)."""
    obj = widget
    for _ in range(12):
        if obj is None:
            return None
        if chave in obj:
            return obj[chave]
        obj = obj.get("/Parent")
        obj = obj.get_object() if obj is not None else None
    return None


def _nome_completo(widget) -> str:
    partes = []
    obj = widget
    for _ in range(12):
        if obj is None:
            break
        t = obj.get("/T")
        if t is not None:
            partes.append(str(t))
        obj = obj.get("/Parent")
        obj = obj.get_object() if obj is not None else None
    return ".".join(reversed(partes))


def _estado_ligado(widget) -> str | None:
    ap = widget.get("/AP")
    ap = ap.get_object() if ap is not None else None
    normal = ap.get("/N") if ap is not None else None
    normal = normal.get_object() if normal is not None else None
    if normal is None or not hasattr(normal, "keys"):
        return None
    for k in normal.keys():
        if k != "/Off":
            return str(k)
    return None


def ler_formulario(dados_ou_caminho) -> dict:
    """
    Devolve {"paginas": [(largura_pt, altura_pt, x0, y0)], "campos": [...]}.
    Cada campo: nome, tipo ("texto"|"multilinha"|"caixa"|"radio"|"lista"|"combo"), pagina,
    rect (x1, y1, x2, y2 em pontos do PDF), valor, ligado (estado "on" de caixa/radio),
    opcoes, so_leitura, max_len, alinhar (0 esq · 1 centro · 2 dir), fonte (tamanho, 0 = automático).
    """
    leitor = PdfReader(io.BytesIO(dados_ou_caminho) if isinstance(dados_ou_caminho, bytes) else dados_ou_caminho)
    paginas, campos = [], []
    for i, pagina in enumerate(leitor.pages):
        caixa = pagina.cropbox
        x0, y0 = float(caixa.left), float(caixa.bottom)
        paginas.append((float(caixa.width), float(caixa.height), x0, y0, int(pagina.get("/Rotate", 0) or 0) % 360))
        for ref in pagina.get("/Annots") or []:
            w = ref.get_object()
            if w.get("/Subtype") != "/Widget":
                continue
            ft = _herdado(w, "/FT")
            if ft not in ("/Tx", "/Btn", "/Ch"):
                continue
            flags = int(_herdado(w, "/Ff") or 0)
            if ft == "/Btn" and flags & _BOTAO:
                continue   # botão de apertar (scripts) — não dá pra preencher
            r = [float(v) for v in w.get("/Rect", [0, 0, 0, 0])]
            rect = (min(r[0], r[2]), min(r[1], r[3]), max(r[0], r[2]), max(r[1], r[3]))
            if rect[2] - rect[0] < 2 or rect[3] - rect[1] < 2:
                continue
            valor = _herdado(w, "/V")
            c = {"nome": _nome_completo(w), "pagina": i, "rect": rect,
                 "so_leitura": bool(flags & _SO_LEITURA), "opcoes": [], "ligado": None,
                 "max_len": int(_herdado(w, "/MaxLen") or 0), "alinhar": int(_herdado(w, "/Q") or 0),
                 "fonte": 0}
            da = str(_herdado(w, "/DA") or "")
            try:   # "/Helv 10 Tf 0 g" -> 10
                partes = da.split()
                c["fonte"] = float(partes[partes.index("Tf") - 1])
            except (ValueError, IndexError):
                pass
            if ft == "/Tx":
                c["tipo"] = "multilinha" if flags & _MULTILINHA else "texto"
                c["valor"] = str(valor) if valor is not None else ""
            elif ft == "/Btn":
                c["tipo"] = "radio" if flags & _RADIO else "caixa"
                c["ligado"] = _estado_ligado(w) or "/Yes"
                c["valor"] = str(valor) if valor is not None else "/Off"
            else:
                c["tipo"] = "combo" if flags & _COMBO else "lista"
                for op in _herdado(w, "/Opt") or []:
                    op = op.get_object() if hasattr(op, "get_object") else op
                    c["opcoes"].append(str(op[1] if isinstance(op, list) and len(op) > 1 else
                                           (op[0] if isinstance(op, list) else op)))
                c["valor"] = str(valor) if valor is not None else ""
            campos.append(c)
    return {"paginas": paginas, "campos": campos}


def gravar_formulario(dados_ou_caminho, valores: dict) -> bytes:
    """Escreve os valores {nome: valor} no PDF e devolve o PDF novo (bytes)."""
    leitor = PdfReader(io.BytesIO(dados_ou_caminho) if isinstance(dados_ou_caminho, bytes) else dados_ou_caminho)
    escritor = PdfWriter(clone_from=leitor)
    textos = {}
    for pagina in escritor.pages:
        for ref in pagina.get("/Annots") or []:
            w = ref.get_object()
            if w.get("/Subtype") != "/Widget":
                continue
            nome = _nome_completo(w)
            if nome not in valores:
                continue
            ft = _herdado(w, "/FT")
            valor = valores[nome]
            if ft == "/Btn":
                ligado = _estado_ligado(w) or "/Yes"
                marcado = str(valor) == ligado
                w[NameObject("/AS")] = NameObject(ligado if marcado else "/Off")
                dono = w if "/T" in w else w.get("/Parent").get_object()
                if marcado or "/V" not in dono or str(dono.get("/V")) == ligado:
                    dono[NameObject("/V")] = NameObject(str(valor) if str(valor).startswith("/") else "/Off")
            else:
                textos.setdefault(id(pagina), (pagina, {}))[1][nome] = str(valor)
    for pagina, vals in textos.values():
        try:
            escritor.update_page_form_field_values(pagina, vals, auto_regenerate=False)
        except Exception:
            # campo esquisito: grava pelo menos o valor
            for ref in pagina.get("/Annots") or []:
                w = ref.get_object()
                n = _nome_completo(w)
                if n in vals:
                    dono = w if "/T" in w else w.get("/Parent").get_object()
                    dono[NameObject("/V")] = TextStringObject(vals[n])
    if "/AcroForm" in escritor._root_object:
        escritor._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)
    buf = io.BytesIO()
    escritor.write(buf)
    return buf.getvalue()
