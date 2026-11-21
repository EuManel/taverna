"""
Áreas de efeito desenhadas pela PLACA DE VÍDEO (Mesa 3D — v0.39).

Um shader por pixel, animado, no lugar do desenho 2D de sempre:
  lava    — correnteza de lava (ruído "torcido" que escorre), crosta de rocha escura boiando e
            rachaduras incandescentes entre as placas
  fogo    — chão em brasa com labaredas tremendo (dá pra ver o chão queimado embaixo)
  gelo    — placa de gelo rachada em células, azulada, com brilhinhos que piscam
  ácido   — poça verde com ondinhas e bolhas que crescem e estouram
  veneno / fumaça — gás que se enrola devagar
  água    — poça com cáusticas (a luz dançando no fundo)
  raio    — arcos elétricos que trocam de lugar ~10× por segundo
  escuridão — breu que se mexe, com a cor escolhida nas bordas
  luz / radiante / magia — brilho, raios de luz girando, espiral de energia (na cor escolhida)
A borda é irregular (ruído), então a área "se mistura" com o chão em vez de ser um disco recortado.
Teia e vinhas continuam com o desenho de sempre (são "coisas", não superfícies).

Plano B: sem placa de vídeo, Mesa 3D desligada, Baixo, ou qualquer erro → o desenho 2D de sempre
(o erro vai pro erros.log e o shader não é tentado de novo).
"""

import numpy as np
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QMatrix4x4, QOpenGLContext, QPaintEngine, QPainter, QVector2D, QVector3D, QVector4D
from PyQt6.QtOpenGL import (QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram, QOpenGLTexture,
                            QOpenGLVersionFunctionsFactory, QOpenGLVersionProfile)

from ..config import CELULA

TIPOS = {"fogo": 0, "lava": 1, "gelo": 2, "veneno": 3, "acido": 4, "agua": 5, "eletrico": 6,
         "trevas": 7, "fumaca": 8, "luz": 9, "sagrado": 10, "magia": 11}
GL_BLEND = 0x0BE2
GL_DEPTH_TEST = 0x0B71
GL_SCISSOR_TEST = 0x0C11
GL_STENCIL_TEST = 0x0B90
GL_SRC_ALPHA = 0x0302
GL_ONE_MINUS_SRC_ALPHA = 0x0303
GL_ONE = 0x0001
GL_TRIANGLES = 0x0004
GL_FLOAT = 0x1406
ESCALA_MASCARA = 0.25   # px da máscara por unidade da cena (a borda é macia mesmo)

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
uniform int tipo;
uniform float t;
uniform vec3 cor;
uniform float semente;
uniform vec4 ret;       // retângulo da máscara (coordenadas locais)
uniform vec2 centro;    // centro da área (coordenadas locais)
uniform float qual;     // 1 = Alto, 0.6 = Médio
varying vec2 vP;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float ruido(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
               mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}
float fbm(vec2 p) {
    float s = 0.0, a = 0.5;
    for (int i = 0; i < 5; i++) { s += a * ruido(p); p = p * 2.03 + vec2(1.7, 9.2); a *= 0.5; }
    return s / 0.97;
}
vec2 voronoi(vec2 x) {   // (distância à 1ª e à 2ª célula)
    vec2 n = floor(x), f = fract(x);
    float d1 = 8.0, d2 = 8.0;
    for (int j = -1; j <= 1; j++)
    for (int i = -1; i <= 1; i++) {
        vec2 g = vec2(float(i), float(j));
        vec2 o = vec2(hash(n + g), hash(n + g + 19.19));
        vec2 r = g + o - f;
        float d = dot(r, r);
        if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) { d2 = d; }
    }
    return vec2(sqrt(d1), sqrt(d2));
}

void main() {
    vec2 uv = (vP - ret.xy) / ret.zw;
    float m = texture2D(masc, uv).r;
    if (m < 0.004) discard;
    vec2 p = vP / 64.0 + vec2(semente * 0.0131, semente * 0.0071);   // em metros
    float borda = smoothstep(0.25, 0.7, m + (fbm(p * 1.1 + 3.1) - 0.5) * 0.6 + (ruido(p * 5.0) - 0.5) * 0.18);
    float dentro = smoothstep(0.5, 1.0, m);
    vec3 col = vec3(0.0);
    float a = 0.0;

    if (tipo == 1) {            // LAVA
        vec2 q = p * 0.8;
        vec2 w = vec2(fbm(q + vec2(0.0, t * 0.05)), fbm(q + vec2(5.2, 1.3) - t * 0.04));
        float f = fbm(q * 1.6 + w * 1.8 + vec2(t * 0.03, -t * 0.02));
        vec2 v = voronoi(p * 1.3 + w * 0.7);
        float racha = 1.0 - smoothstep(0.0, 0.1, v.y - v.x);
        float quente = smoothstep(0.3, 0.8, f);
        vec3 lava = mix(vec3(0.7, 0.1, 0.02), vec3(1.0, 0.62, 0.12), quente);
        lava = mix(lava, vec3(1.0, 0.93, 0.55), pow(quente, 4.0));
        float crosta = smoothstep(0.42, 0.58, fbm(p * 2.1 - w * 0.9 + t * 0.01)) * (1.0 - racha);
        vec3 rocha = vec3(0.1, 0.065, 0.05) * (0.6 + 0.7 * fbm(p * 9.0));
        col = mix(lava, rocha, crosta * 0.9);
        col += vec3(1.0, 0.45, 0.08) * racha * 0.7 * (1.0 - crosta);
        col *= mix(0.45, 1.0, dentro);              // a beira esfria
        a = borda;
    } else if (tipo == 0) {     // FOGO no chão
        float f1 = fbm(p * 2.2 + vec2(0.0, -t * 1.1));
        float f2 = fbm(p * 4.6 + vec2(t * 0.6, -t * 1.9));
        float chama = pow(clamp(f1 * 0.62 + f2 * 0.48, 0.0, 1.0), 2.0) * (0.6 + 0.5 * dentro);
        float treme = 0.86 + 0.14 * sin(t * 13.0 + f1 * 6.0);
        col = mix(vec3(0.55, 0.06, 0.0), vec3(1.0, 0.52, 0.08), smoothstep(0.12, 0.45, chama));
        col = mix(col, vec3(1.0, 0.93, 0.62), smoothstep(0.45, 0.8, chama));
        float brasa = smoothstep(0.78, 0.95, fbm(p * 7.0 + t * 0.2)) * (0.5 + 0.5 * sin(t * 5.0 + hash(floor(p * 7.0)) * 30.0));
        col += vec3(1.0, 0.4, 0.05) * brasa * 0.6;
        a = borda * clamp(smoothstep(0.06, 0.4, chama) * treme + brasa * 0.5, 0.0, 0.95);
    } else if (tipo == 2) {     // GELO
        vec2 v = voronoi(p * 1.7);
        float aresta = 1.0 - smoothstep(0.0, 0.05, v.y - v.x);
        float fino = 1.0 - smoothstep(0.0, 0.03, abs(fbm(p * 5.0) - 0.5));
        col = mix(vec3(0.6, 0.8, 0.94), vec3(0.9, 0.97, 1.0), fbm(p * 3.0));
        col += vec3(0.35) * aresta + vec3(0.2) * fino;
        float h = hash(floor(p * 36.0));
        float brilho = step(0.985, h) * pow(0.5 + 0.5 * sin(t * 3.0 + h * 60.0), 8.0) * qual;
        col += vec3(1.0) * brilho;
        a = borda * clamp(0.5 + 0.2 * fbm(p * 2.0) + aresta * 0.25 + brilho, 0.0, 0.92);
    } else if (tipo == 3 || tipo == 8) {   // VENENO / FUMAÇA (gás enrolando)
        vec2 q = p * 1.1;
        float f = fbm(q + vec2(t * 0.07, t * 0.05) + fbm(q * 0.8 - t * 0.05) * 1.6);
        if (tipo == 3) col = mix(vec3(0.22, 0.42, 0.08), vec3(0.62, 0.86, 0.26), f);
        else col = vec3(0.5, 0.5, 0.52) + 0.25 * f;
        a = borda * smoothstep(0.22, 0.78, f) * (tipo == 3 ? 0.7 : 0.8);
    } else if (tipo == 4) {     // ÁCIDO
        float f = fbm(p * 2.0 + vec2(t * 0.1, -t * 0.07));
        col = mix(vec3(0.4, 0.65, 0.04), vec3(0.78, 0.96, 0.22), f);
        vec2 g = floor(p * 2.6);
        vec2 fr = fract(p * 2.6) - 0.5 - (vec2(hash(g + 3.0), hash(g + 7.0)) - 0.5) * 0.4;
        float h = hash(g);
        float fase = fract(t * (0.35 + 0.3 * h) + h);
        float anel = (1.0 - smoothstep(0.0, 0.035, abs(length(fr) - (0.06 + 0.24 * fase)))) * (1.0 - fase) * step(0.45, h);
        col += vec3(0.85, 1.0, 0.5) * anel * 0.55;
        col += vec3(0.25) * pow(f, 6.0);          // reflexo
        a = borda * 0.84;
    } else if (tipo == 5) {     // ÁGUA
        float c1 = abs(sin(fbm(p * 1.8 + t * 0.12) * 11.0));
        float caus = pow(1.0 - c1, 5.0) * qual;
        col = mix(vec3(0.07, 0.24, 0.4), vec3(0.2, 0.48, 0.66), fbm(p * 1.4 - t * 0.05)) + vec3(0.55, 0.75, 0.85) * caus * 0.45;
        a = borda * 0.7;
    } else if (tipo == 6) {     // RAIO
        float salto = floor(t * 10.0);
        float r1 = 1.0 - abs(fbm(p * 2.2 + vec2(salto * 1.7, salto * 0.9)) * 2.0 - 1.0);
        float r2 = 1.0 - abs(fbm(p * 3.5 - vec2(salto * 2.3, 0.0)) * 2.0 - 1.0);
        float arco = pow(r1, 30.0) + pow(r2, 40.0) * 0.7;
        col = mix(vec3(0.35, 0.55, 1.0), vec3(1.0), clamp(arco * 1.4, 0.0, 1.0));
        a = borda * clamp(0.08 + arco * 1.2, 0.0, 1.0);
    } else if (tipo == 7) {     // ESCURIDÃO
        float f = fbm(p * 1.0 + vec2(t * 0.04, -t * 0.03) + fbm(p * 2.0 - t * 0.06));
        col = mix(vec3(0.0), cor * 0.35, smoothstep(0.55, 0.95, f) * (1.0 - dentro * 0.6));
        a = borda * (0.88 + 0.1 * f);
    } else if (tipo == 9) {     // LUZ (brilho + pontinhos de luz redondos que piscam)
        vec2 g = floor(p * 6.0);
        vec2 alvo = vec2(hash(g + 1.3), hash(g + 7.7));
        float h = hash(g);
        float ponto = 1.0 - smoothstep(0.0, 0.16, length(fract(p * 6.0) - alvo));
        float pisca = step(0.7, h) * ponto * (0.5 + 0.5 * sin(t * 3.0 + h * 40.0));
        col = mix(cor, vec3(1.0), 0.35 + 0.65 * pisca);
        a = borda * clamp(0.14 + 0.24 * m + pisca * 0.7, 0.0, 0.85) * (0.92 + 0.08 * sin(t * 2.0));
    } else if (tipo == 10) {    // RADIANTE (brilho do centro + feixes suaves girando)
        vec2 d = vP - centro;
        float ang = atan(d.y, d.x);
        float r = length(d) / 64.0;
        float raios = pow(0.5 + 0.5 * sin(ang * 9.0 + t * 0.35), 3.0) * (0.55 + 0.45 * fbm(vec2(r * 3.0 - t * 0.4, ang * 2.0)));
        col = mix(cor, vec3(1.0, 0.98, 0.9), 0.3 + 0.7 * raios * dentro);
        a = borda * (0.16 + 0.26 * dentro + raios * 0.14);
    } else {                    // MAGIA (espiral de energia; sem ângulo = sem emenda)
        vec2 d = (vP - centro) / 64.0;
        float r = length(d);
        float giro = r * 2.4 - t * 0.35;
        vec2 dd = mat2(cos(giro), -sin(giro), sin(giro), cos(giro)) * d;
        float s = fbm(dd * 2.2 + vec2(semente * 0.01, t * 0.05));
        float linhas = pow(1.0 - abs(s * 2.0 - 1.0), 7.0);
        col = mix(cor * 0.55, mix(cor, vec3(1.0), 0.55), linhas);
        a = borda * clamp(0.22 + linhas * 0.65, 0.0, 0.9);
    }
    gl_FragColor = vec4(clamp(col, 0.0, 1.0), clamp(a, 0.0, 1.0));
}
"""

_falhou = False
_por_contexto = {}
_MASCARAS = {}


def ativo(painter: QPainter) -> bool:
    if _falhou:
        return False
    motor = painter.paintEngine()
    if motor is None or motor.type() != QPaintEngine.Type.OpenGL2:
        return False
    from . import camera3d
    return camera3d.ligada()


def mascara(area) -> tuple[QImage, QRectF]:
    """Máscara macia da forma (coordenadas locais da área), guardada por forma/tamanho.
    (v0.69.1) A chave inclui QUAL área e ONDE ela está: o recorte (fora do chão, paredes do gás) depende do
    lugar. Antes, duas áreas do mesmo tamanho — ou uma apagada e outra nova — podiam pegar a máscara uma da
    outra, e o fogo aparecia fora da sala (só na placa de vídeo)."""
    p = area.scenePos()
    chave = (id(area), getattr(area, "uid", ""), round(p.x()), round(p.y()), round(area.rotation()),
             id(area.scene()), area.chave_forma())
    if chave in _MASCARAS:
        return _MASCARAS[chave]
    from . import texturas as T
    cam = area.caminho()
    r = cam.boundingRect().adjusted(-CELULA * 0.6, -CELULA * 0.6, CELULA * 0.6, CELULA * 0.6)
    W = max(8, min(1024, int(r.width() * ESCALA_MASCARA)))
    H = max(8, min(1024, int(r.height() * ESCALA_MASCARA)))
    img = QImage(W, H, QImage.Format.Format_Grayscale8)
    img.fill(0)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(W / r.width(), H / r.height())
    p.translate(-r.x(), -r.y())
    p.fillPath(cam, QColor(255, 255, 255))
    p.end()
    ptr = img.constBits()
    ptr.setsize(img.sizeInBytes())
    m = np.frombuffer(ptr, np.uint8).reshape(H, img.bytesPerLine())[:, :W].astype(np.float32) / 255.0
    m = T.borrar(m, 3)
    saida = np.zeros((H, W, 4), np.uint8)
    saida[..., 0] = np.clip(m * 255, 0, 255)
    saida[..., 3] = 255
    final = QImage(saida.tobytes(), W, H, W * 4, QImage.Format.Format_RGBA8888).copy()
    if len(_MASCARAS) > 64:
        _MASCARAS.clear()
    _MASCARAS[chave] = (final, r)
    return final, r


class _Desenhista:
    def __init__(self, ctx):
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
            raise RuntimeError("shader das áreas: " + self.prog.log())
        self.buf = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        self.buf.create()
        self.texturas = {}

    def _textura(self, img: QImage):
        chave = img.cacheKey()
        tex = self.texturas.get(chave)
        if tex is None:
            tex = QOpenGLTexture(img)
            tex.setMinificationFilter(QOpenGLTexture.Filter.Linear)
            tex.setMagnificationFilter(QOpenGLTexture.Filter.Linear)
            tex.setWrapMode(QOpenGLTexture.WrapMode.ClampToEdge)
            if len(self.texturas) > 64:
                for velha in self.texturas.values():
                    velha.destroy()
                self.texturas.clear()
            self.texturas[chave] = tex
        return tex

    def desenhar(self, painter, area, t, qual):
        img, r = mascara(area)
        self.desenhar_mascara(painter, img, r, TIPOS[area.efeito], QColor(area.cor_efetiva), area._semente % 997,
                              area.caminho().boundingRect().center(), t, qual)

    def desenhar_mascara(self, painter, img, r, tipo, cor, semente, centro, t, qual):
        """O shader numa máscara qualquer (área de efeito, ou poça/alagamento do cenário)."""
        f = self.gl
        dev = painter.device()
        w, h = max(1, dev.width()), max(1, dev.height())
        dpr = dev.devicePixelRatioF() if hasattr(dev, "devicePixelRatioF") else 1.0
        tr = painter.combinedTransform()
        from .camera3d import mvp as _mvp
        mvp = _mvp(tr, w, h)   # (v0.70) com perspectiva (câmera inclinada)
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
        p.setUniformValue("tipo", int(tipo))
        p.setUniformValue("t", float(t % 1000.0))
        p.setUniformValue("cor", QVector3D(cor.redF(), cor.greenF(), cor.blueF()))
        p.setUniformValue("semente", float(semente))
        p.setUniformValue("ret", QVector4D(r.x(), r.y(), r.width(), r.height()))
        p.setUniformValue("centro", QVector2D(centro.x(), centro.y()))
        p.setUniformValue("qual", float(qual))
        self._textura(img).bind(0)
        f.glDrawArrays(GL_TRIANGLES, 0, 6)
        p.disableAttributeArray(lp)
        self.buf.release()
        p.release()


def desenhar(painter: QPainter, area) -> bool:
    """Desenha a área pelo shader. False = não deu (quem chamou usa o desenho de sempre)."""
    global _falhou
    if area.efeito not in TIPOS:
        return False
    from ..graficos import nivel
    from .efeitos import agora
    painter.beginNativePainting()
    try:
        ctx = QOpenGLContext.currentContext()
        if ctx is None:
            raise RuntimeError("sem contexto OpenGL")
        from .gl_contexto import do_contexto
        des = do_contexto(ctx, "efeitos_gl", lambda: _Desenhista(ctx))
        des.desenhar(painter, area, agora(), 1.0 if nivel() == 2 else 0.6)
        return True
    except Exception as erro:
        _falhou = True
        from ..seguranca import registrar_erro
        registrar_erro(f"Áreas de efeito pela placa de vídeo desligadas: {erro!r}")
        return False
    finally:
        painter.endNativePainting()


def desenhar_campo(painter: QPainter, img: QImage, r: QRectF, efeito: str, cor: str = "", semente: int = 7) -> bool:
    """Poça/alagamento do cenário (mesa/fluidos.py): o mesmo shader, numa máscara pronta (vermelho = tem)."""
    global _falhou
    if efeito not in TIPOS or _falhou:
        return False
    from ..graficos import nivel
    from .efeitos import EFEITOS, agora
    painter.beginNativePainting()
    try:
        ctx = QOpenGLContext.currentContext()
        if ctx is None:
            raise RuntimeError("sem contexto OpenGL")
        from .gl_contexto import do_contexto
        des = do_contexto(ctx, "efeitos_gl", lambda: _Desenhista(ctx))
        des.desenhar_mascara(painter, img, r, TIPOS[efeito], QColor(cor or EFEITOS[efeito][1]), semente % 997,
                             r.center(), agora(), 1.0 if nivel() == 2 else 0.6)
        return True
    except Exception as erro:
        _falhou = True
        from ..seguranca import registrar_erro
        registrar_erro(f"Líquidos do cenário pela placa de vídeo desligados: {erro!r}")
        return False
    finally:
        painter.endNativePainting()
