"""
Coisas de OpenGL guardadas POR CONTEXTO (v0.47).

Antes cada módulo guardava o seu desenhista em `{id(ctx): ...}`. O problema: o `id()` do objeto Python
do contexto pode ser reaproveitado pra OUTRO contexto (outra janela) quando o Python apaga o antigo —
aí um shader/buffer/textura de uma janela era usado na outra e o programa caía (access violation),
o que aparecia com o Mestre e Players abertos ao mesmo tempo.
Agora o próprio objeto do contexto fica guardado junto (o id não muda mais de dono) e a entrada sai
quando o contexto é destruído.
"""

_dados = {}   # id(ctx) -> (ctx, {nome: objeto})


def do_contexto(ctx, nome: str, criar):
    """O objeto `nome` deste contexto; `criar()` na primeira vez."""
    k = id(ctx)
    ent = _dados.get(k)
    if ent is None or ent[0] is not ctx:
        ent = _dados[k] = (ctx, {})
        try:
            ctx.aboutToBeDestroyed.connect(lambda k=k: _dados.pop(k, None))
        except (AttributeError, RuntimeError, TypeError):
            pass
    d = ent[1]
    obj = d.get(nome)
    if obj is None:
        obj = d[nome] = criar()
    return obj
