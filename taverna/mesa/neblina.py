"""
Neblina VOLUMÉTRICA rasteira (v0.44) — pedido do Manel: "não deixa como uns PNG de fumaça flutuando".

Clima → Neblina, com a Mesa 3D ligada:
  - é uma CAMADA de neblina de verdade, do chão até ~1,5 m (a força muda a altura e a densidade);
  - na placa de vídeo, cada pixel atravessa essa camada em FATIAS de altura (com a perspectiva da câmera)
    somando a densidade de um ruído 3D que se mexe — por isso tem volume: ao arrastar o mapa, o alto
    da neblina anda mais que o pé, e ela fica mais grossa embaixo;
  - REAGE aos objetos: objeto, token e parede "abrem caminho" (a neblina contorna, desvia e fica rala
    em volta deles) — o token andando passa pela neblina abrindo espaço;
  - as luzes da cena acendem a neblina em volta delas (halo da tocha).
Paredes (2 m) ficam por cima: saem da neblina. Luz/escuro e névoa de guerra continuam por cima de tudo.

Plano B (sem placa de vídeo): camadas de ruído em alturas diferentes, com os mesmos buracos em volta
das coisas. Com a Mesa 3D desligada ou Gráficos Baixo, fica a neblina de antes (na tela).
"""

import math
import time

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QColor, QImage, QMatrix4x4, QOpenGLContext, QPainter, QPainterPath, QPaintEngine,
                         QPen, QPixmap, QVector2D, QVector3D, QVector4D)
from PyQt6.QtWidgets import QGraphicsItem

from ..config import CELULA, LIMITE_CENA

Z_NEBLINA = 690_000          # por cima de tokens e objetos, por baixo das paredes altas (700.000)
ALTURA = 1.5 * CELULA        # neblina rasteira
MAX_LUZES = 12

VERT = """
#version 120
attribute vec2 pos;
uniform mat4 mvp;
varying vec2 vP;
void main() {
    vP = pos;
    gl_Position = mvp * vec4(pos, 0.0, 1.0);
}
"""

FRAG = """
#version 120
uniform sampler2D masc;
uniform vec4 ret;          // retângulo da máscara (cena)
uniform vec2 centro;       // ponto da cena no centro da tela
uniform float H;           // altura da câmera (pixels)
uniform float escala;      // pixels por unidade da cena
uniform float t;
uniform float alt;         // altura da neblina (cena)
uniform float forca;       // 0.6 / 1.0 / 1.4
uniform int passos;
uniform int nLuzes;
uniform vec4 luz[12];      // x, y, alcance, força
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
float ocupado(vec2 q) {   // 1 = tem objeto/token/parede ali (a neblina abre caminho)
    vec2 uv = (q - ret.xy) / ret.zw;
    if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) return 0.0;
    return texture2D(masc, uv).r;
}

void main() {
    vec3 acum = vec3(0.0);
    float T = 1.0;
    float dz = alt / float(passos);
    for (int i = 0; i < 12; i++) {
        if (i >= passos) break;
        float z = alt - (float(i) + 0.5) * dz;               // de cima pra baixo
        // (v0.70) o raio de visão: do chão (vP) até a câmera (centro = pé da câmera, H = altura dela em px)
        vec2 q = vP + (centro - vP) * min(0.95, z * escala / H);                  // o ponto da cena nessa altura, sob este pixel
        float m = ocupado(q);
        float e = 28.0;
        vec2 g = vec2(ocupado(q + vec2(e, 0.0)) - ocupado(q - vec2(e, 0.0)),
                      ocupado(q + vec2(0.0, e)) - ocupado(q - vec2(0.0, e)));
        // o fluxo desvia em volta das coisas (contorna)
        vec3 pn = vec3(q / 110.0 - g * 1.8 + vec2(t * 0.045, t * 0.018), z / 70.0 + t * 0.025);
        float n = fbm3(pn);
        float perfil = 1.0 - smoothstep(alt * 0.2, alt, z);   // mais grossa embaixo
        float dens = max(0.0, n - 0.40) * 3.0 * perfil * (1.0 - smoothstep(0.1, 0.7, m)) * forca;
        // sombreamento: onde tem menos neblina por cima, é mais claro (o topo dos "rolos" pega luz)
        float acima = fbm3(pn + vec3(0.0, 0.0, 0.35));
        float ilum = clamp(1.05 - (acima - 0.35) * 1.4, 0.55, 1.15);
        vec3 L = vec3(0.0);
        for (int k = 0; k < 12; k++) {
            if (k >= nLuzes) break;
            float d = length(luz[k].xy - q);
            float att = clamp(1.0 - d / luz[k].z, 0.0, 1.0);
            L += corLuz[k] * att * att * luz[k].w;
        }
        vec3 cor = vec3(0.72, 0.76, 0.82) * ilum + L * 0.85;
        float a = 1.0 - exp(-dens * dz * 0.016);
        acum += T * a * cor;
        T *= (1.0 - a);
    }
    float alfa = 1.0 - T;
    if (alfa < 0.003) discard;
    gl_FragColor = vec4(clamp(acum / alfa, 0.0, 1.0), clamp(alfa, 0.0, 0.92));
}
"""

_falhou = False
_por_contexto = {}
GL_BLEND, GL_DEPTH_TEST, GL_SCISSOR_TEST, GL_STENCIL_TEST = 0x0BE2, 0x0B71, 0x0C11, 0x0B90
GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_TRIANGLES, GL_FLOAT = 0x0302, 0x0303, 0x0004, 0x1406


def ligada(cena) -> bool:
    clima = getattr(cena, "clima", None) or {}
    from . import camera3d
    return clima.get("tipo") == "neblina" and camera3d.ligada()


def forca_de(cena) -> int:
    try:
        return max(1, min(3, int((getattr(cena, "clima", None) or {}).get("forca", 2))))
    except (TypeError, ValueError):
        return 2


# ====================================================================== o que "abre caminho"
def mascara(cena, r: QRectF) -> QImage:
    """Imagem (vermelho = ocupado) do que a neblina contorna: objetos, tokens, paredes."""
    from .props import PropItem
    from .token import TokenItem
    lado = max(r.width(), r.height())
    s = min(1 / 4, 640 / max(1.0, lado))   # pixels por unidade da cena
    W, Hh = max(8, int(r.width() * s)), max(8, int(r.height() * s))
    img = QImage(W, Hh, QImage.Format.Format_RGBA8888)
    img.fill(QColor(0, 0, 0, 255))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(s, s)
    p.translate(-r.x(), -r.y())
    p.setPen(Qt.PenStyle.NoPen)
    for item in cena.items():
        try:
            if not item.isVisible():
                continue
            if isinstance(item, PropItem):
                if item.altura_3d <= 0:
                    continue
                from PyQt6.QtGui import QPolygonF
                p.setBrush(QColor(255, 0, 0))
                p.drawPolygon(QPolygonF(item.cantos_cena()))
            elif isinstance(item, TokenItem):
                c = item.centro_cena()
                raio = item.diametro / 2 * 1.25
                p.setBrush(QColor(215, 0, 0))   # o token abre bastante, mas não tudo
                p.drawEllipse(c, raio, raio)
        except RuntimeError:
            continue
    paredes = getattr(cena, "paredes", None)
    if paredes is not None and paredes.isVisible():
        p.setPen(QPen(QColor(255, 0, 0), 0.3 * CELULA, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for seg in list(getattr(paredes, "segmentos", {}).values()):
            try:
                (x1, y1), (x2, y2) = seg["a"], seg["b"]
                p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            except (KeyError, TypeError, ValueError):
                continue
    p.end()
    # borra (a neblina vai rareando perto das coisas, sem borda dura)
    pequeno = img.scaled(max(2, W // 4), max(2, Hh // 4), Qt.AspectRatioMode.IgnoreAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)
    return pequeno.scaled(W, Hh, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)


def _visivel_na_tela(painter) -> QRectF:
    dev = painter.device()
    w, h = (dev.width(), dev.height()) if dev is not None else (1000, 800)
    inv, ok = painter.worldTransform().inverted()
    if not ok:
        return QRectF()
    r = inv.mapRect(QRectF(0, 0, w, h))
    g = CELULA * 2   # arredonda (a máscara não muda a cada pixel arrastado)
    return QRectF(math.floor(r.left() / g) * g - g, math.floor(r.top() / g) * g - g,
                  (math.ceil(r.width() / g) + 2) * g, (math.ceil(r.height() / g) + 2) * g)


def _luzes(cena):
    saida = []
    overlay = getattr(cena, "luz_overlay", None)
    for d, _pol in (getattr(overlay, "luzes", None) or []):
        try:
            saida.append((float(d["x"]), float(d["y"]), float(d["fraco"]) * CELULA, QColor(d["cor"])))
        except (KeyError, TypeError, ValueError):
            continue
    return saida[:MAX_LUZES]


# ====================================================================== shader
class _Desenhista:
    def __init__(self, ctx):
        from PyQt6.QtOpenGL import (QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram,
                                    QOpenGLVersionFunctionsFactory, QOpenGLVersionProfile)
        perfil = QOpenGLVersionProfile()
        perfil.setVersion(2, 1)
        self.gl = QOpenGLVersionFunctionsFactory.get(perfil, ctx)
        if self.gl is None:
            raise RuntimeError("OpenGL 2.1 indisponível")
        self.gl.initializeOpenGLFunctions()
        self.prog = QOpenGLShaderProgram()
        if not (self.prog.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, VERT)
                and self.prog.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, FRAG)
                and self.prog.link()):
            raise RuntimeError("shader da neblina: " + self.prog.log())
        self.buf = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        self.buf.create()
        self.tex = None
        self.chave_tex = None

    def desenhar(self, painter, cena, r, masc_img, chave, forca, qual):
        from PyQt6.QtOpenGL import QOpenGLTexture
        from . import camera3d
        f = self.gl
        dev = painter.device()
        w, h = max(1, dev.width()), max(1, dev.height())
        dpr = dev.devicePixelRatioF() if hasattr(dev, "devicePixelRatioF") else 1.0
        tr = painter.combinedTransform()
        mvp = camera3d.mvp(tr, w, h)
        cam = camera3d.Camera(painter)
        # (v0.70) pé da câmera (inclinada fica mais pra trás) e a ALTURA dela (D·cos θ): o raio de cada pixel
        centro = cam.pe_cena()   # (nas coordenadas do painter, como o vP)
        H_cam = cam.H * math.cos(cam.teta)
        if self.chave_tex != chave or self.tex is None:
            if self.tex is not None:
                self.tex.destroy()
            self.tex = QOpenGLTexture(masc_img)
            self.tex.setMinificationFilter(QOpenGLTexture.Filter.Linear)
            self.tex.setMagnificationFilter(QOpenGLTexture.Filter.Linear)
            self.tex.setWrapMode(QOpenGLTexture.WrapMode.ClampToEdge)
            self.chave_tex = chave
        x0, y0, x1, y1 = r.left(), r.top(), r.right(), r.bottom()
        arr = np.array([x0, y0, x1, y0, x1, y1, x0, y0, x1, y1, x0, y1], np.float32)
        f.glViewport(0, 0, int(w * dpr), int(h * dpr))
        f.glDisable(GL_DEPTH_TEST)
        f.glDisable(GL_SCISSOR_TEST)
        f.glDisable(GL_STENCIL_TEST)
        f.glEnable(GL_BLEND)
        f.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        p = self.prog
        p.bind()
        self.buf.bind()
        self.buf.allocate(arr.tobytes(), arr.nbytes)
        lp = p.attributeLocation("pos")
        p.enableAttributeArray(lp)
        p.setAttributeBuffer(lp, GL_FLOAT, 0, 2, 8)
        p.setUniformValue("mvp", mvp)
        p.setUniformValue("masc", 0)
        p.setUniformValue("ret", QVector4D(r.x(), r.y(), r.width(), r.height()))
        p.setUniformValue("centro", QVector2D(centro.x(), centro.y()))
        p.setUniformValue("H", float(H_cam))
        p.setUniformValue("escala", float(cam.escala))
        p.setUniformValue("t", float(time.monotonic() % 10000.0))
        p.setUniformValue("alt", float(ALTURA * (0.75 + 0.25 * forca)))
        p.setUniformValue("forca", float((0.6, 1.0, 1.4)[forca - 1]))
        p.setUniformValue("passos", int(10 if qual == 2 else 6))
        luzes = _luzes(cena)
        p.setUniformValue("nLuzes", len(luzes))
        for i, (lx, ly, alcance, cor) in enumerate(luzes):
            p.setUniformValue(f"luz[{i}]", QVector4D(lx, ly, alcance, 1.0))
            p.setUniformValue(f"corLuz[{i}]", QVector3D(cor.redF(), cor.greenF(), cor.blueF()))
        self.tex.bind(0)
        f.glDrawArrays(GL_TRIANGLES, 0, 6)
        p.disableAttributeArray(lp)
        self.buf.release()
        p.release()


# ====================================================================== o item na cena
class NeblinaItem(QGraphicsItem):
    def __init__(self):
        super().__init__()
        self.setZValue(Z_NEBLINA)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._masc = None   # (chave, imagem)
        self._camadas = {}  # plano B: texturas de ruído
        self._buracos_cache = (None, None)
        from .efeitos import animacao
        animacao().registrar(self)

    def boundingRect(self) -> QRectF:
        L = LIMITE_CENA
        from .camera3d import limitar
        return limitar(self, QRectF(-L, -L, 2 * L, 2 * L))   # (v0.70) câmera inclinada: só o chão visível

    def shape(self) -> QPainterPath:
        return QPainterPath()

    def animado(self) -> bool:
        cena = self.scene()
        return cena is not None and ligada(cena)

    def _mascara(self, cena, r):
        from .props import PropItem
        from .token import TokenItem
        sinal = []
        for item in cena.items():
            if isinstance(item, (PropItem, TokenItem)) and item.isVisible():
                p = item.scenePos()
                sinal.append((round(p.x() / 8), round(p.y() / 8), round(item.rotation())))
        paredes = getattr(cena, "paredes", None)
        chave = (round(r.x()), round(r.y()), round(r.width()), round(r.height()), hash(tuple(sinal)),
                 len(getattr(paredes, "segmentos", {}) or {}))
        if self._masc is None or self._masc[0] != chave:
            self._masc = (chave, mascara(cena, r))
        return self._masc

    def paint(self, painter, option, widget=None):
        global _falhou
        cena = self.scene()
        if cena is None or not ligada(cena):
            return
        try:
            r = _visivel_na_tela(painter)
            if r.isEmpty():
                return
            from ..graficos import nivel
            forca = forca_de(cena)
            chave, masc = self._mascara(cena, r)
            motor = painter.paintEngine()
            if not _falhou and motor is not None and motor.type() == QPaintEngine.Type.OpenGL2:
                painter.beginNativePainting()
                try:
                    ctx = QOpenGLContext.currentContext()
                    if ctx is None:
                        raise RuntimeError("sem contexto OpenGL")
                    from .gl_contexto import do_contexto
                    des = do_contexto(ctx, "neblina", lambda: _Desenhista(ctx))
                    des.desenhar(painter, cena, r, masc, chave, forca, nivel())
                    return
                except Exception as erro:
                    _falhou = True
                    from ..seguranca import registrar_erro
                    registrar_erro(f"Neblina volumétrica (OpenGL) desligada: {erro!r}")
                finally:
                    painter.endNativePainting()
            self._plano_b(painter, cena, r, masc, forca, nivel())
        except Exception as erro:   # (erro dentro de paint() fecha o programa)
            from ..seguranca import registrar_erro
            registrar_erro(f"Neblina não desenhou: {erro!r}")

    # --- plano B (QPainter): camadas de ruído em alturas diferentes, com buracos em volta das coisas
    def _camada(self, k):
        if k not in self._camadas:
            from . import texturas as T
            rng = np.random.default_rng(91 + k * 7)
            n = T.fbm(256, 256, rng, [(64, 1.0), (32, 0.6), (12, 0.3)])
            a = np.clip((n - 0.32) * 1.9, 0, 1)
            saida = np.zeros((256, 256, 4), np.uint8)
            saida[..., 0], saida[..., 1], saida[..., 2] = 182, 190, 202
            saida[..., 3] = (a * 120).astype(np.uint8)
            img = QImage(saida.tobytes(), 256, 256, 1024, QImage.Format.Format_RGBA8888).copy()
            self._camadas[k] = QPixmap.fromImage(img)
        return self._camadas[k]

    def _buracos(self, masc: QImage) -> QImage:
        """A máscara (vermelho) virando transparência: é o que se recorta da neblina."""
        chave = masc.cacheKey()
        if getattr(self, "_buracos_cache", (None,))[0] != chave:
            img = masc.convertToFormat(QImage.Format.Format_RGBA8888)
            w, h = img.width(), img.height()
            ptr = img.constBits()
            ptr.setsize(img.sizeInBytes())
            arr = np.frombuffer(ptr, np.uint8).reshape(h, img.bytesPerLine() // 4, 4)[:, :w, :]
            saida = np.zeros((h, w, 4), np.uint8)
            saida[..., 3] = np.clip(arr[..., 0].astype(np.int32) * 1.2, 0, 255).astype(np.uint8)
            self._buracos_cache = (chave, QImage(saida.tobytes(), w, h, w * 4, QImage.Format.Format_RGBA8888).copy())
        return self._buracos_cache[1]

    def _plano_b(self, painter, cena, r, masc, forca, qual):
        from PyQt6.QtGui import QBrush, QTransform
        from . import camera3d
        cam = camera3d.Camera(painter)
        t = time.monotonic()
        dev = painter.device()
        w, h = max(1, dev.width()), max(1, dev.height())
        tela = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        tela.fill(Qt.GlobalColor.transparent)
        p = QPainter(tela)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        n_camadas = 4 if qual == 2 else 3
        for k in range(n_camadas):   # camadas em alturas diferentes (com a perspectiva = volume)
            z = ALTURA * (k + 0.5) / n_camadas
            p.setWorldTransform(cam.transformacao_topo(z))
            escala = 6 * CELULA / 256   # textura de 256 px cobrindo ~6 m, andando com o tempo
            pincel = QBrush(self._camada(k))
            pincel.setTransform(QTransform().scale(escala, escala).translate(t * (6 + k * 3) % 256, t * 2 % 256))
            p.setOpacity((0.55, 0.8, 1.0)[forca - 1] * (1.0 - 0.18 * k))
            p.fillRect(r, pincel)
        # a neblina abre caminho em volta de objetos, tokens e paredes
        p.setOpacity(1.0)
        p.setWorldTransform(painter.worldTransform())
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
        p.drawImage(r, self._buracos(masc))
        p.end()
        painter.save()
        painter.resetTransform()
        painter.drawImage(0, 0, tela)
        painter.restore()


def garantir(cena):
    """Põe a camada de neblina na cena (uma só). Chamado quando o clima muda/aba abre."""
    if cena is None:
        return None
    item = getattr(cena, "_neblina_item", None)
    try:
        if item is not None and item.scene() is cena:
            item.update()
            return item
    except RuntimeError:
        pass
    item = NeblinaItem()
    cena.addItem(item)
    cena._neblina_item = item
    return item
