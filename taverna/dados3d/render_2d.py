"""
Plano B sem OpenGL: desenha os mesmos dados (mesma física, mesmos números) com QPainter.
Usado se o OpenGL falhar no PC, se a pessoa desligar o OpenGL, e nos testes automáticos (sem tela).
"""

import numpy as np
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QBrush, QColor, QImage, QPainter, QPainterPath, QPen, QPolygonF, QRadialGradient, QTransform

from .cena3d import camera, material, projetar
from .geometria import solido

LUZ = np.array([-0.35, 0.45, 0.82])
LUZ = LUZ / np.linalg.norm(LUZ)


def _atlas_colorido(rolagem, cor: QColor) -> QImage:
    """A textura dos números (branca) pintada na cor dos números do tema. Guardada na rolagem."""
    chave = ("_atlas2d", cor.name())
    if getattr(rolagem, "_cache2d", None) and rolagem._cache2d[0] == chave:
        return rolagem._cache2d[1]
    img = QImage(rolagem.imagem.size(), QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(cor)
    p = QPainter(img)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
    p.drawImage(0, 0, rolagem.imagem)
    p.end()
    rolagem._cache2d = (chave, img)
    return img


def _afim(src, dst):
    """QTransform que leva 3 pontos (src, em pixels do atlas) nos 3 pontos da tela (dst)."""
    a = np.array([[s[0], s[1], 1.0] for s in src])
    try:
        mx = np.linalg.solve(a, np.array([d[0] for d in dst]))
        my = np.linalg.solve(a, np.array([d[1] for d in dst]))
    except np.linalg.LinAlgError:
        return None
    return QTransform(mx[0], my[0], mx[1], my[1], mx[2], my[2])


def desenhar(p: QPainter, rolagem, t: float, w: int, h: int):
    visao, proj, _, _, olho = camera(w, h)
    corpo, cor_num, brilho, gema = rolagem.corpo, rolagem.cor_num, rolagem.brilho, rolagem.gema   # (v0.74)
    atlas = _atlas_colorido(rolagem, cor_num)
    desg = None   # (v0.74) a textura do material (veio, grão, ferrugem…) também no desenho simples
    if getattr(rolagem, "desgaste", None):
        from .cena3d import textura_desgaste
        img_d = textura_desgaste(rolagem.desgaste)
        desg = QBrush(img_d) if img_d is not None else None
    quadro = rolagem.quadro(t)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    # sombras no chão
    for d, (pos, q) in zip(rolagem.dados, quadro):
        altura = max(0.0, float(pos[2]))
        c2d, _ = projetar(np.array([[pos[0], pos[1], 0.0]]), visao, proj, w, h)
        borda, _ = projetar(np.array([[pos[0] + 1.1, pos[1], 0.0]]), visao, proj, w, h)
        raio = float(np.linalg.norm(borda[0] - c2d[0])) * (1 + altura * 0.12)
        alfa = int(max(0, 120 - altura * 22))
        g = QRadialGradient(QPointF(*c2d[0]), raio)
        g.setColorAt(0, QColor(0, 0, 0, alfa))
        g.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(*c2d[0]), raio, raio * 0.75)
    # dados, do mais longe pro mais perto
    ordem = sorted(range(len(quadro)), key=lambda i: -float(np.linalg.norm(quadro[i][0] - olho)))
    for i in ordem:
        d = rolagem.dados[i]
        pos, q = quadro[i]
        m = rolagem.matriz_modelo(pos, q)
        v, faces, normais, _ = solido(d["lados"])
        mundo = v @ m[:3, :3].T + m[:3, 3]
        nmundo = normais @ (m[:3, :3] / np.linalg.norm(m[:3, 0])).T
        tela, prof = projetar(mundo, visao, proj, w, h)
        caras = []
        for j, face in enumerate(faces):
            centro = mundo[face].mean(axis=0)
            if np.dot(nmundo[j], olho - centro) <= 0:
                continue   # de costas pra câmera
            caras.append((float(np.linalg.norm(olho - centro)), j, face))
        caras.sort(reverse=True)
        base = QColor(corpo)
        if d.get("fora"):   # descartado (vantagem/desvantagem): mais apagado
            base = base.darker(160)
        for _, j, face in caras:
            luz = max(0.0, float(np.dot(nmundo[j], LUZ)))
            fator = 0.45 + 0.65 * luz
            cor = QColor(min(255, int(base.red() * fator)), min(255, int(base.green() * fator)),
                         min(255, int(base.blue() * fator)), 200 if gema else 255)
            poli = QPolygonF([QPointF(*tela[k]) for k in face])
            p.setPen(QPen(base.darker(190), 1.1))
            p.setBrush(cor)
            p.drawPolygon(poli)
            uv = rolagem.uvs[i][j]
            src = [(uv[k][0] * atlas.width(), uv[k][1] * atlas.height()) for k in range(3)]
            dst = [tuple(tela[face[k]]) for k in range(3)]
            tr = _afim(src, dst)
            if desg is not None and tr is not None:   # textura: 50% = igual (luz dura: cinza do meio não muda nada)
                caminho_d = QPainterPath()
                caminho_d.addPolygon(poli)
                p.save()
                p.setClipPath(caminho_d)
                p.setTransform(tr, True)
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_HardLight)
                p.setOpacity(0.85)
                p.fillRect(0, 0, atlas.width(), atlas.height(), desg)
                p.restore()
            # brilho (reflexo da luz) nas faces viradas pra ela
            if luz > 0.75 and brilho > 0.3:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(255, 255, 255, int(70 * brilho * (luz - 0.75) * 4)))
                p.drawPolygon(poli)
            # número: a célula da textura, levada pra face (aproximação afim, boa o bastante)
            if tr is not None:
                caminho = QPainterPath()
                caminho.addPolygon(poli)
                p.save()
                p.setClipPath(caminho)
                p.setTransform(tr, True)
                p.setOpacity(0.92)
                p.drawImage(0, 0, atlas)
                p.restore()
