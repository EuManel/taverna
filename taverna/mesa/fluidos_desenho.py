"""
Desenho do gás e dos líquidos de cenário (v0.45) — ver mesa/fluidos.py.

  GasItem       — gás VOLUMÉTRICO (o mesmo jeito da neblina: fatias de altura na placa de vídeo), na cor
                  do gás e mais grosso onde está concentrado; o tóxico fica rasteiro, a fumaça sobe mais.
                  Plano B: imagem da concentração em duas alturas.
  LiquidosItem  — água/lava/ácido no chão (por baixo de tokens e objetos), com o shader animado das áreas
                  (água com cáusticas, lava escorrendo, ácido borbulhando) na forma exata do alagamento.
                  Plano B: o desenho 2D das áreas de efeito, no contorno do alagamento.
  FontesItem    — os marcadores das fontes (só o mestre vê).
"""

import math
import time

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QColor, QImage, QMatrix4x4, QOpenGLContext, QPainter, QPainterPath, QPaintEngine, QPen,
                         QVector2D, QVector3D, QVector4D)
from PyQt6.QtWidgets import QGraphicsItem

from ..config import CELULA, LIMITE_CENA
from .fluidos import PELICULA, QUANTIZAR, TIPOS

Z_GAS = 689_500       # logo abaixo da neblina
Z_LIQUIDO = 3.5       # depois do chão, do grid e das paredes (3); antes de objetos (4) e tokens
Z_FONTES = 960_000

FRAG_GAS = """
#version 120
uniform sampler2D conc;     // R = gás tóxico, G = fumaça (0–1 = 0–2 de concentração)
uniform vec4 ret;
uniform vec2 centro;
uniform float H;
uniform float escala;
uniform float t;
uniform float alt;
uniform int passos;
uniform vec3 cor1;
uniform vec3 cor2;
uniform int nLuzes;
uniform vec4 luz[12];
uniform vec3 corLuz[12];
varying vec2 vP;

float hash3(vec3 p) {
    p = fract(p * 0.3183099 + vec3(0.1, 0.2, 0.3));
    p *= 17.0;
    return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}
float ruido3(vec3 x) {
    vec3 i = floor(x), f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(mix(hash3(i), hash3(i + vec3(1, 0, 0)), f.x),
                   mix(hash3(i + vec3(0, 1, 0)), hash3(i + vec3(1, 1, 0)), f.x), f.y),
               mix(mix(hash3(i + vec3(0, 0, 1)), hash3(i + vec3(1, 0, 1)), f.x),
                   mix(hash3(i + vec3(0, 1, 1)), hash3(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}
float fbm3(vec3 p) {
    float s = 0.0, a = 0.55;
    for (int i = 0; i < 4; i++) { s += a * ruido3(p); p = p * 2.07 + vec3(3.1, 1.7, 5.3); a *= 0.5; }
    return s;
}
vec2 amostra(vec2 q) {
    vec2 uv = (q - ret.xy) / ret.zw;
    if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) return vec2(0.0);
    return texture2D(conc, uv).rg * 2.0;
}
void main() {
    vec3 acum = vec3(0.0);
    float T = 1.0;
    float dz = alt / float(passos);
    for (int i = 0; i < 12; i++) {
        if (i >= passos) break;
        float z = alt - (float(i) + 0.5) * dz;
        // (v0.70) o raio de visão: do chão (vP) até a câmera (centro = pé da câmera, H = altura dela em px)
        vec2 q = vP + (centro - vP) * min(0.95, z * escala / H);
        vec2 c = amostra(q);
        if (c.x + c.y < 0.003) continue;
        float n = fbm3(vec3(q / 90.0 + vec2(t * 0.06, t * 0.025), z / 60.0 + t * 0.04));
        float d1 = c.x * (0.45 + 0.9 * n) * (1.0 - smoothstep(alt * 0.12, alt * 0.7, z));   // tóxico: rasteiro
        float d2 = c.y * (0.45 + 0.9 * n) * (1.0 - smoothstep(alt * 0.35, alt, z));        // fumaça: sobe
        float dens = d1 + d2;
        float acima = fbm3(vec3(q / 90.0 + vec2(t * 0.06, t * 0.025), z / 60.0 + t * 0.04 + 0.35));
        float ilum = clamp(1.05 - (acima - 0.35) * 1.3, 0.55, 1.15);
        vec3 L = vec3(0.0);
        for (int k = 0; k < 12; k++) {
            if (k >= nLuzes) break;
            float dd = length(luz[k].xy - q);
            float att = clamp(1.0 - dd / luz[k].z, 0.0, 1.0);
            L += corLuz[k] * att * att * luz[k].w;
        }
        vec3 cor = (cor1 * d1 + cor2 * d2) / max(dens, 1e-4) * ilum + L * 0.7;
        float a = 1.0 - exp(-dens * dz * 0.07);
        acum += T * a * cor;
        T *= (1.0 - a);
    }
    float alfa = 1.0 - T;
    if (alfa < 0.004) discard;
    gl_FragColor = vec4(clamp(acum / alfa, 0.0, 1.0), clamp(alfa, 0.0, 0.95));
}
"""

_falhou_gas = False
_por_contexto = {}


def _vivo(f):
    try:
        return f is not None and f.cena is not None
    except RuntimeError:
        return False


# ====================================================================== gás
class GasItem(QGraphicsItem):
    def __init__(self, fluidos):
        super().__init__()
        self.f = fluidos
        self.setZValue(Z_GAS)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._img = None
        from .efeitos import animacao
        animacao().registrar(self)

    def boundingRect(self):
        L = LIMITE_CENA
        from .camera3d import limitar
        return limitar(self, QRectF(-L, -L, 2 * L, 2 * L))   # (v0.70) câmera inclinada: só o chão visível

    def shape(self):
        return QPainterPath()

    def animado(self) -> bool:
        return any(float(self.f.campos[n].max()) > 0.004 for n in ("gas_toxico", "fumaca")
                   if n in self.f.campos and self.f.campos[n].size)

    def _imagem(self) -> QImage:
        """R = gás tóxico, G = fumaça (0–255 = 0–2 de concentração)."""
        f = self.f
        a1, a2 = f.campos["gas_toxico"], f.campos["fumaca"]
        saida = np.zeros((f.ny, f.nx, 4), np.uint8)
        saida[..., 0] = np.clip(a1 / 2.0 * 255, 0, 255)
        saida[..., 1] = np.clip(a2 / 2.0 * 255, 0, 255)
        saida[..., 3] = 255
        return QImage(saida.tobytes(), f.nx, f.ny, f.nx * 4, QImage.Format.Format_RGBA8888).copy()

    def paint(self, painter, option, widget=None):
        global _falhou_gas
        if not self.f.nx or not self.animado():
            return
        try:
            img = self._imagem()
            r = self.f.ret_cena()
            from . import camera3d
            motor = painter.paintEngine()
            if (not _falhou_gas and camera3d.ligada() and motor is not None
                    and motor.type() == QPaintEngine.Type.OpenGL2):
                painter.beginNativePainting()
                try:
                    _shader_gas(painter, self.scene(), img, r)
                    return
                except Exception as erro:
                    _falhou_gas = True
                    from ..seguranca import registrar_erro
                    registrar_erro(f"Gás volumétrico (OpenGL) desligado: {erro!r}")
                finally:
                    painter.endNativePainting()
            self._plano_b(painter, r)
        except Exception as erro:   # (erro dentro de paint() fecha o programa)
            from ..seguranca import registrar_erro
            registrar_erro(f"Gás do cenário não desenhou: {erro!r}")

    def _plano_b(self, painter, r):
        f = self.f
        cor1, cor2 = QColor(TIPOS["gas_toxico"][2]), QColor(TIPOS["fumaca"][2])
        a1 = np.clip(f.campos["gas_toxico"] / 1.0, 0, 1)
        a2 = np.clip(f.campos["fumaca"] / 1.0, 0, 1)
        alfa = np.clip(a1 + a2, 0, 1)
        peso = np.where(alfa > 0, a1 / np.maximum(a1 + a2, 1e-4), 0)
        saida = np.zeros((f.ny, f.nx, 4), np.uint8)
        for k, (c1, c2) in enumerate(((cor1.red(), cor2.red()), (cor1.green(), cor2.green()), (cor1.blue(), cor2.blue()))):
            saida[..., k] = (c1 * peso + c2 * (1 - peso)).astype(np.uint8)
        saida[..., 3] = (alfa * 170).astype(np.uint8)
        img = QImage(saida.tobytes(), f.nx, f.ny, f.nx * 4, QImage.Format.Format_RGBA8888).copy()
        from . import camera3d
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if camera3d.ligada():   # duas alturas (com a perspectiva = volume)
            cam = camera3d.Camera(painter)
            for z, op in ((0.3 * CELULA, 0.7), (0.9 * CELULA, 0.45)):
                painter.setWorldTransform(cam.transformacao_topo(z))
                painter.setOpacity(op)
                painter.drawImage(r, img)
        else:
            painter.drawImage(r, img)
        painter.restore()


def _shader_gas(painter, cena, img, r):
    from PyQt6.QtOpenGL import (QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram, QOpenGLTexture,
                                QOpenGLVersionFunctionsFactory, QOpenGLVersionProfile)
    from . import camera3d
    from .neblina import VERT, _luzes
    ctx = QOpenGLContext.currentContext()
    if ctx is None:
        raise RuntimeError("sem contexto OpenGL")
    from .gl_contexto import do_contexto

    def _criar():
        perfil = QOpenGLVersionProfile()
        perfil.setVersion(2, 1)
        gl = QOpenGLVersionFunctionsFactory.get(perfil, ctx)
        gl.initializeOpenGLFunctions()
        prog = QOpenGLShaderProgram()
        if not (prog.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, VERT)
                and prog.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, FRAG_GAS) and prog.link()):
            raise RuntimeError("shader do gás: " + prog.log())
        buf = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        buf.create()
        return {"gl": gl, "prog": prog, "buf": buf, "tex": None}
    d = do_contexto(ctx, "gas", _criar)
    gl, p, buf = d["gl"], d["prog"], d["buf"]
    dev = painter.device()
    w, h = max(1, dev.width()), max(1, dev.height())
    dpr = dev.devicePixelRatioF() if hasattr(dev, "devicePixelRatioF") else 1.0
    tr = painter.combinedTransform()
    mvp = camera3d.mvp(tr, w, h)
    cam = camera3d.Camera(painter)
    import math
    # (v0.70) pé da câmera e a altura dela (inclinada: mais pra trás e mais baixa)
    centro = cam.pe_cena()   # (nas coordenadas do painter, como o vP)
    H_cam = cam.H * math.cos(cam.teta)
    if d["tex"] is not None:
        d["tex"].destroy()
    tex = d["tex"] = QOpenGLTexture(img)
    tex.setMinificationFilter(QOpenGLTexture.Filter.Linear)
    tex.setMagnificationFilter(QOpenGLTexture.Filter.Linear)
    tex.setWrapMode(QOpenGLTexture.WrapMode.ClampToEdge)
    x0, y0, x1, y1 = r.left(), r.top(), r.right(), r.bottom()
    arr = np.array([x0, y0, x1, y0, x1, y1, x0, y0, x1, y1, x0, y1], np.float32)
    gl.glViewport(0, 0, int(w * dpr), int(h * dpr))
    for c in (0x0B71, 0x0C11, 0x0B90):
        gl.glDisable(c)
    gl.glEnable(0x0BE2)
    gl.glBlendFunc(0x0302, 0x0303)
    p.bind()
    buf.bind()
    buf.allocate(arr.tobytes(), arr.nbytes)
    lp = p.attributeLocation("pos")
    p.enableAttributeArray(lp)
    p.setAttributeBuffer(lp, 0x1406, 0, 2, 8)
    from ..graficos import nivel
    c1, c2 = QColor(TIPOS["gas_toxico"][2]), QColor(TIPOS["fumaca"][2])
    p.setUniformValue("mvp", mvp)
    p.setUniformValue("conc", 0)
    p.setUniformValue("ret", QVector4D(r.x(), r.y(), r.width(), r.height()))
    p.setUniformValue("centro", QVector2D(centro.x(), centro.y()))
    p.setUniformValue("H", float(H_cam))
    p.setUniformValue("escala", float(cam.escala))
    p.setUniformValue("t", float(time.monotonic() % 10000.0))
    p.setUniformValue("alt", float(1.6 * CELULA))
    p.setUniformValue("passos", int(10 if nivel() == 2 else 6))
    p.setUniformValue("cor1", QVector3D(c1.redF(), c1.greenF(), c1.blueF()))
    p.setUniformValue("cor2", QVector3D(c2.redF(), c2.greenF(), c2.blueF()))
    luzes = _luzes(cena)
    p.setUniformValue("nLuzes", len(luzes))
    for i, (lx, ly, alcance, cor) in enumerate(luzes):
        p.setUniformValue(f"luz[{i}]", QVector4D(lx, ly, alcance, 1.0))
        p.setUniformValue(f"corLuz[{i}]", QVector3D(cor.redF(), cor.greenF(), cor.blueF()))
    tex.bind(0)
    gl.glDrawArrays(0x0004, 0, 6)
    p.disableAttributeArray(lp)
    buf.release()
    p.release()


# ====================================================================== líquidos
class LiquidosItem(QGraphicsItem):
    def __init__(self, fluidos):
        super().__init__()
        self.f = fluidos
        self.setZValue(Z_LIQUIDO)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._cache = {}
        self._2d = {}
        from .efeitos import animacao
        animacao().registrar(self)

    def boundingRect(self):
        L = LIMITE_CENA
        from .camera3d import limitar
        return limitar(self, QRectF(-L, -L, 2 * L, 2 * L))   # (v0.70) câmera inclinada: só o chão visível

    def shape(self):
        return QPainterPath()

    def animado(self) -> bool:
        return any(float(self.f.campos[n].max()) > 0.004 for n in ("agua", "lava", "acido")
                   if n in self.f.campos and self.f.campos[n].size)

    def paint(self, painter, option, widget=None):
        if not self.f.nx:
            return
        try:
            from . import efeitos_gl
            from .efeitos import agora, desenhar_efeito
            r = self.f.ret_cena()
            gl = efeitos_gl.ativo(painter)
            for nome in ("agua", "acido", "lava"):
                a = self.f.campos.get(nome)
                if a is None or not a.size or a.max() <= 0.004:
                    continue
                efeito = TIPOS[nome][3]
                if gl:
                    m = np.clip((a - 0.01) / (PELICULA * 0.9), 0, 1)
                    saida = np.zeros((self.f.ny, self.f.nx, 4), np.uint8)
                    saida[..., 0] = (m * 255).astype(np.uint8)
                    saida[..., 3] = 255
                    img = QImage(saida.tobytes(), self.f.nx, self.f.ny, self.f.nx * 4,
                                 QImage.Format.Format_RGBA8888).copy()
                    if efeitos_gl.desenhar_campo(painter, img, r, efeito, semente=hash(nome) % 997):
                        continue
                # plano B: o contorno do alagamento com o desenho 2D das áreas
                chave = (nome, hash(a.tobytes()[::97]))
                if self._2d.get(nome, (None,))[0] != chave:
                    self._2d[nome] = (chave, self.f.caminho_de(a > PELICULA * 0.5))
                cam = self._2d[nome][1]
                if not cam.isEmpty():
                    desenhar_efeito(painter, cam, efeito, agora(), hash(nome) % 997, self._cache.setdefault(nome, {}))
        except Exception as erro:   # (erro dentro de paint() fecha o programa)
            from ..seguranca import registrar_erro
            registrar_erro(f"Líquido do cenário não desenhou: {erro!r}")


# ====================================================================== fontes (só o mestre)
class FontesItem(QGraphicsItem):
    def __init__(self, fluidos):
        super().__init__()
        self.f = fluidos
        self.setZValue(Z_FONTES)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    def boundingRect(self):
        L = LIMITE_CENA
        from .camera3d import limitar
        return limitar(self, QRectF(-L, -L, 2 * L, 2 * L))   # (v0.70) câmera inclinada: só o chão visível

    def shape(self):
        return QPainterPath()

    def fonte_em(self, pos: QPointF, raio=None):
        raio = raio or CELULA * 0.5
        for f in self.f.fontes:
            if math.hypot(f["x"] - pos.x(), f["y"] - pos.y()) <= raio:
                return f
        return None

    def paint(self, painter, option, widget=None):
        if not self.f.fontes:
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        fonte = painter.font()
        fonte.setPixelSize(11)
        fonte.setBold(True)
        painter.setFont(fonte)
        for f in self.f.fontes:
            cor = QColor(TIPOS[f["tipo"]][2])
            c = QPointF(f["x"], f["y"])
            r = CELULA * 0.28
            painter.setPen(QPen(QColor(15, 12, 10), 2))
            painter.setBrush(cor if f["ligada"] else QColor(90, 90, 90))
            painter.drawEllipse(c, r, r)
            painter.setPen(QPen(QColor(255, 255, 255, 220), 1.6))
            for k in range(3):   # "jorrando"
                ang = k * 2.094 + time.monotonic() * (2 if f["ligada"] else 0)
                painter.drawLine(c + QPointF(math.cos(ang) * r * 0.4, math.sin(ang) * r * 0.4),
                                 c + QPointF(math.cos(ang) * r * 0.9, math.sin(ang) * r * 0.9))
            resto = ""
            if f["duracao"] > 0:
                resto = f"  {max(0, int(f['duracao'] - f['decorrido']))} s" if f["ligada"] else "  (acabou)"
            elif not f["ligada"]:
                resto = "  (desligada)"
            painter.setPen(QColor(240, 230, 210))
            painter.drawText(QRectF(c.x() - 80, c.y() + r + 2, 160, 16), Qt.AlignmentFlag.AlignCenter,
                             TIPOS[f["tipo"]][0].split(" ", 1)[1] + resto)


def garantir_itens(cena, f):
    """Os itens de desenho estão na cena? (a cena é limpa ao abrir uma aventura)"""
    itens = getattr(cena, "_fluidos_itens", None)
    try:
        if itens and all(i.scene() is cena for i in itens):
            return itens
    except RuntimeError:
        pass
    itens = [GasItem(f), LiquidosItem(f)]
    if f.simula:
        itens.append(FontesItem(f))
    for i in itens:
        cena.addItem(i)
    cena._fluidos_itens = itens

    def atualizar(itens=itens):
        for i in itens:
            try:
                i.update()
            except RuntimeError:
                pass
    if not getattr(f, "_ligado_desenho", False):
        f.mudou.connect(lambda: [x.update() for x in getattr(cena, "_fluidos_itens", []) if _ok(x)])
        f._ligado_desenho = True
    atualizar()
    return itens


def _ok(item):
    try:
        return item.scene() is not None
    except RuntimeError:
        return False
