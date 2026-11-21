"""
Onde tem CENÁRIO (v0.45): chão pintado (terreno) + mapas importados.

"Se tá fora do mapa é porque não tá no cenário": áreas de efeito, marcas, gás e líquidos só existem
aqui dentro (o que cai no vazio é cortado). Tokens e objetos podem ficar fora (o mestre "estaciona").
Cena sem chão nenhum (mesa em branco) → None = não corta nada.
"""

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPainterPath


def caminho_do_chao(cena, terreno, mapas) -> QPainterPath | None:
    """Guardado na cena; só refaz quando o terreno ou os mapas mudam."""
    ops = list(getattr(terreno, "ops", []) or []) if terreno is not None else []
    chave_t = tuple((op.get("t"), op.get("m") is None, len(op.get("p", []) or []), len(op.get("c", []) or []),
                     op.get("x"), op.get("y"), op.get("w"), op.get("h"),
                     tuple(op["p"][-1]) if op.get("p") and op.get("t") != "marca" else None)
                    for op in ops if op.get("t") != "marca")
    retas = []
    for m in mapas:
        try:
            if m.isVisible():
                r = m.mapToScene(QRectF(0, 0, m.w, m.h)).boundingRect()
                retas.append((round(r.x()), round(r.y()), round(r.width()), round(r.height())))
        except (RuntimeError, AttributeError):
            continue
    chave = (chave_t, tuple(retas))
    if getattr(cena, "_chao_chave", None) == chave:
        return cena._chao_cam
    cam = QPainterPath()
    cam.setFillRule(Qt.FillRule.WindingFill)
    borracha = QPainterPath()
    borracha.setFillRule(Qt.FillRule.WindingFill)
    caminhos = list(getattr(terreno, "_caminhos", []) or []) if terreno is not None else []
    for op, c in zip(ops, caminhos):
        if op.get("t") == "marca":
            continue
        (borracha if op.get("m") is None else cam).addPath(c)
    for x, y, w, h in retas:
        cam.addRect(QRectF(x, y, w, h))
    if cam.isEmpty():
        final = None
    else:
        final = cam.simplified()
        if not borracha.isEmpty():
            final = final.subtracted(borracha.simplified())
    cena._chao_chave = chave
    cena._chao_cam = final
    cena._chao_versao = getattr(cena, "_chao_versao", 0) + 1
    return final
