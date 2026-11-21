"""
💡 Iluminação dinâmica (v0.45) — "quando lançar a bola de fogo, ela ilumina em volta… o mais fiel possível".

Luzes PASSAGEIRAS: a bola de fogo voando (a luz vai junto), o estouro no alvo (clarão que vai apagando),
o jato de fogo (a luz anda com as labaredas), o raio (flash que pisca), explosão / clarão arcano.
Cada uma PARA NA PAREDE (sombra de verdade: o polígono de luz é recalculado enquanto ela se move) e
ilumina tudo que as luzes normais iluminam: chão com relevo, faces das paredes, tokens, neblina e gás.

Só as luzes que se mexem são recalculadas (as fixas ficam guardadas): no máx. ~30×/s.
"""

from PyQt6.QtCore import QTimer


def definir(cena, ident: str, d: dict | None):
    """Liga/atualiza (d) ou apaga (None) uma luz passageira. d: x, y, fraco (m), cor, brilho (0–1)."""
    if cena is None:
        return
    temp = cena.__dict__.setdefault("_luzes_temp", {})
    if d is None:
        if temp.pop(ident, None) is None:
            return
    else:
        temp[ident] = {"classe": "luz", "id": ident, "x": float(d["x"]), "y": float(d["y"]),
                       "fraco": max(0.5, float(d["fraco"])), "forte": max(0.2, float(d["fraco"]) * 0.35),
                       "cor": d.get("cor", "#ffb060"), "tremula": False, "acesa": True, "visivel": True,
                       "brilho": max(0.0, min(1.0, float(d.get("brilho", 1.0))))}
    timer = cena.__dict__.get("_timer_luz_temp")
    if timer is None:
        timer = cena._timer_luz_temp = QTimer(cena)
        timer.setSingleShot(True)
        timer.setInterval(33)
        timer.timeout.connect(lambda c=cena: aplicar(c))
    if not timer.isActive():
        timer.start()


def poligonos(cena) -> list:
    """[(dict, polígono)] das luzes passageiras (paredes bloqueiam)."""
    temp = cena.__dict__.get("_luzes_temp") or {}
    if not temp:
        return []
    from .linha_de_visao import poligono
    obst = cena.__dict__.get("_obst_luz") or []
    return [(d, poligono(d["x"], d["y"], 0, 360, d["fraco"], obst)) for d in temp.values() if d["brilho"] > 0.02]


def aplicar(cena):
    """Junta as luzes fixas (guardadas) com as passageiras e manda pro overlay de luz."""
    overlay = getattr(cena, "luz_overlay", None)
    if overlay is None:
        return
    try:
        fixas = cena.__dict__.get("_polys_fixos")
        if fixas is None:   # ainda não calculou as fixas: calcula tudo
            if hasattr(cena, "recalcular_luzes"):
                cena.recalcular_luzes()
            elif hasattr(cena, "recalcular_nevoa"):
                cena.recalcular_nevoa()
            return
        overlay.definir(getattr(cena, "luz_ambiente", "dia"), list(fixas) + poligonos(cena))
        terreno = getattr(cena, "terreno", None)   # o relevo do chão também reage
        if terreno is not None:
            terreno.update()
        paredes = getattr(cena, "paredes", None)
        alta = getattr(paredes, "_alta", None) if paredes is not None else None
        if alta is not None:
            alta.update()
    except RuntimeError:
        pass
