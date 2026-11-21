"""
Piso com relevo que reage à luz (Mesa 3D, parte 2 — v0.34).

Quando a mesa está na placa de vídeo (viewport OpenGL), o terreno é desenhado por um shader:
  - a textura de sempre (os azulejos/tiles do TerrenoItem);
  - um MAPA DE RELEVO calculado a partir dela (claro = mais alto: pedras saltam, juntas afundam);
  - as luzes da cena (posição, alcance, cor).
Pra cada pixel, o shader vê se aquela saliência está virada pra luz ou contra ela: a tocha passando
"revela" os sulcos do chão. Sem luz por perto, o chão fica igualzinho ao de sempre.

Plano B: se qualquer coisa falhar, anota no erros.log e o terreno volta a ser desenhado pelo QPainter.
"""

import numpy as np
from PyQt6.QtGui import (QColor, QImage, QMatrix4x4, QOpenGLContext, QPaintEngine, QPainter, QVector3D,
                         QVector4D)
from PyQt6.QtOpenGL import (QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram, QOpenGLTexture,
                            QOpenGLVersionFunctionsFactory, QOpenGLVersionProfile)

from ..config import CELULA

MAX_LUZES = 12
MAX_TEXTURAS = 140
GL_BLEND = 0x0BE2
GL_DEPTH_TEST = 0x0B71
GL_SCISSOR_TEST = 0x0C11
GL_STENCIL_TEST = 0x0B90
GL_SRC_ALPHA = 0x0302
GL_ONE_MINUS_SRC_ALPHA = 0x0303
GL_TRIANGLES = 0x0004
GL_FLOAT = 0x1406

VERT = """
#version 120
attribute vec2 pos;
attribute vec2 uv;
uniform mat4 mvp;
varying vec2 vUV;
varying vec2 vP;
void main() {
    vUV = uv;
    vP = pos;
    gl_Position = mvp * vec4(pos, 0.0, 1.0);
}
"""

FRAG = """
#version 120
uniform sampler2D tex;
uniform sampler2D nrm;
uniform int nLuzes;
uniform vec4 luz[12];      // x, y, alcance, força
uniform vec3 corLuz[12];
uniform float relevo;      // 0 = liso … 1 = relevo forte
uniform float alturaLuz;   // altura das luzes (unidades da cena)
varying vec2 vUV;
varying vec2 vP;
void main() {
    vec4 c = texture2D(tex, vUV);
    if (c.a < 0.004) discard;
    vec4 m = texture2D(nrm, vUV);
    vec2 nxy = m.rg * 2.0 - 1.0;
    vec3 N = vec3(nxy, sqrt(max(0.0, 1.0 - dot(nxy, nxy))));
    float cavidade = m.b;
    // sujeira/sombra nas juntas e rachaduras (pedra de verdade junta poeira nos vãos)
    vec3 base = c.rgb * (1.0 - cavidade * 0.42 * relevo);
    float soma = 0.0;
    for (int i = 0; i < 12; i++) {
        if (i >= nLuzes) break;
        vec2 d = luz[i].xy - vP;
        float dist = length(d);
        float att = clamp(1.0 - dist / luz[i].z, 0.0, 1.0);
        att *= att;
        vec3 L = normalize(vec3(d, alturaLuz));
        // fosco (Lambert puro): só a diferença pro chão liso; nada de reflexo — era o que dava cara
        // de plástico. As juntas recebem menos luz ainda (a borda da lajota faz sombra nelas).
        float dif = max(dot(N, L), 0.0) - L.z;
        // dentro do vão a luz quase não chega (e nunca "brilha" — senão a junta parece saliente)
        float fator = dif > 0.0 ? (1.0 - cavidade) * (1.0 - cavidade) : 1.0;
        soma += dif * att * luz[i].w * fator;
    }
    vec3 cor = base * (1.0 + relevo * soma * 2.8);
    gl_FragColor = vec4(clamp(cor, 0.0, 1.0), c.a);
}
"""

_falhou = False
_por_contexto = {}


def ativo(painter: QPainter) -> bool:
    """Dá pra desenhar o piso pelo shader agora? (mesa na placa de vídeo, 3D ligado, Médio/Alto)"""
    if _falhou:
        return False
    motor = painter.paintEngine()
    if motor is None or motor.type() != QPaintEngine.Type.OpenGL2:
        return False
    from . import camera3d
    return camera3d.ligada()


def _borrar(a, raio):
    """Média numa caixa de (2·raio+1)² (com 'embrulho' nas bordas, a textura repete)."""
    s = a.copy()
    for eixo in (0, 1):
        acum = s.copy()
        for k in range(1, raio + 1):
            acum += np.roll(s, k, eixo) + np.roll(s, -k, eixo)
        s = acum / (2 * raio + 1)
    return s


def mapas(arr):
    """
    A partir da textura (array RGBA float 0–255), devolve (nx, ny, cavidade):
      - relevo em DUAS escalas: a forma (quina da lajota, junta) + o grão fino da pedra. Sem o grão,
        a pedra parecia plástico "acolchoado" (v0.34.1 → v0.34.2);
      - cavidade: o quanto o ponto está abaixo da vizinhança (junta, rachadura) — vira sujeira/sombra.
    """
    lum = (arr[..., 0] * 0.3 + arr[..., 1] * 0.59 + arr[..., 2] * 0.11) / 255.0
    forma = _borrar(lum, 1)
    dfx = np.roll(forma, -1, 1) - np.roll(forma, 1, 1)
    dfy = np.roll(forma, -1, 0) - np.roll(forma, 1, 0)
    grao = lum - forma                          # só o detalhe fininho
    dgx = np.roll(grao, -1, 1) - np.roll(grao, 1, 1)
    dgy = np.roll(grao, -1, 0) - np.roll(grao, 1, 0)
    nx = -(dfx * 2.6 + dgx * 2.8)   # (v0.35: menos "bisel" na borda, mais grão — pedra, não plástico)
    ny = -(dfy * 2.6 + dgy * 2.8)
    nz = np.ones_like(lum)
    tam = np.sqrt(nx * nx + ny * ny + nz * nz)
    vizinhanca = _borrar(lum, 4)
    cavidade = np.clip((vizinhanca - forma) * 4.0, 0.0, 1.0)
    return nx / tam, ny / tam, cavidade


def _mapa_de_relevo(img: QImage) -> QImage:
    """R, G = normal (x, y) · B = cavidade (sujeira nas juntas) · A = o alfa da textura."""
    img = img.convertToFormat(QImage.Format.Format_RGBA8888)
    w, h = img.width(), img.height()
    ptr = img.constBits()
    ptr.setsize(img.sizeInBytes())
    arr = np.frombuffer(ptr, np.uint8).reshape(h, img.bytesPerLine() // 4, 4)[:, :w, :].astype(np.float32)
    nx, ny, cav = mapas(arr)
    saida = np.empty((h, w, 4), np.uint8)
    saida[..., 0] = np.clip((nx * 0.5 + 0.5) * 255, 0, 255)
    saida[..., 1] = np.clip((ny * 0.5 + 0.5) * 255, 0, 255)
    saida[..., 2] = np.clip(cav * 255, 0, 255)
    saida[..., 3] = arr[..., 3]
    return QImage(saida.tobytes(), w, h, w * 4, QImage.Format.Format_RGBA8888).copy()


class _Desenhista:
    """Shader + texturas, por contexto OpenGL."""

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
            raise RuntimeError("shader do piso: " + self.prog.log())
        self.buf = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        self.buf.create()
        self.texturas = {}   # chave -> (cor, relevo), em ordem de uso

    def _texturas(self, chave, pm):
        if chave in self.texturas:
            par = self.texturas.pop(chave)
            self.texturas[chave] = par
            return par
        img = pm.toImage()
        cor = QOpenGLTexture(img.convertToFormat(QImage.Format.Format_RGBA8888))
        rel = QOpenGLTexture(_mapa_de_relevo(img))
        for t in (cor, rel):
            t.setMinificationFilter(QOpenGLTexture.Filter.LinearMipMapLinear)
            t.setMagnificationFilter(QOpenGLTexture.Filter.Linear)
            t.setWrapMode(QOpenGLTexture.WrapMode.ClampToEdge)
        self.texturas[chave] = (cor, rel)
        while len(self.texturas) > MAX_TEXTURAS:
            velha = next(iter(self.texturas))
            for t in self.texturas.pop(velha):
                t.destroy()
        return cor, rel

    def desenhar(self, painter, azulejos, luzes, forca_relevo):
        f = self.gl
        dev = painter.device()
        w, h = max(1, dev.width()), max(1, dev.height())
        dpr = dev.devicePixelRatioF() if hasattr(dev, "devicePixelRatioF") else 1.0
        t = painter.combinedTransform()
        from .camera3d import mvp as _mvp
        mvp = _mvp(t, w, h)   # (v0.70) com perspectiva (câmera inclinada)
        f.glViewport(0, 0, int(w * dpr), int(h * dpr))
        f.glDisable(GL_DEPTH_TEST)
        f.glDisable(GL_SCISSOR_TEST)
        f.glDisable(GL_STENCIL_TEST)
        f.glEnable(GL_BLEND)
        f.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # um buffer com os quadrados de todos os azulejos visíveis
        dados = []
        for r, _pm, _chave in azulejos:
            x0, y0, x1, y1 = r.left(), r.top(), r.right(), r.bottom()
            dados += [x0, y0, 0, 0, x1, y0, 1, 0, x1, y1, 1, 1, x0, y0, 0, 0, x1, y1, 1, 1, x0, y1, 0, 1]
        arr = np.array(dados, dtype=np.float32)
        p = self.prog
        p.bind()
        self.buf.bind()
        self.buf.allocate(arr.tobytes(), arr.nbytes)
        lp, lu = p.attributeLocation("pos"), p.attributeLocation("uv")
        p.enableAttributeArray(lp)
        p.enableAttributeArray(lu)
        p.setAttributeBuffer(lp, GL_FLOAT, 0, 2, 16)
        p.setAttributeBuffer(lu, GL_FLOAT, 8, 2, 16)
        p.setUniformValue("mvp", mvp)
        p.setUniformValue("tex", 0)
        p.setUniformValue("nrm", 1)
        p.setUniformValue("relevo", float(forca_relevo))
        p.setUniformValue("alturaLuz", float(1.3 * CELULA))
        p.setUniformValue("nLuzes", len(luzes))
        for i, (cx, cy, alcance, forca, cor) in enumerate(luzes):
            p.setUniformValue(f"luz[{i}]", QVector4D(cx, cy, alcance, forca))
            p.setUniformValue(f"corLuz[{i}]", QVector3D(cor.redF(), cor.greenF(), cor.blueF()))
        for k, (_r, pm, chave) in enumerate(azulejos):
            cor, rel = self._texturas(chave, pm)
            cor.bind(0)
            rel.bind(1)
            f.glDrawArrays(GL_TRIANGLES, k * 6, 6)
        f.glActiveTexture(0x84C0)   # (v0.67) volta pra GL_TEXTURE0: senão o QPainter desenha imagem/degradê PRETO
        p.disableAttributeArray(lp)
        p.disableAttributeArray(lu)
        self.buf.release()
        p.release()


def desenhar(painter: QPainter, azulejos, cena) -> bool:
    """
    Desenha os azulejos do terreno pelo shader. azulejos = [(retângulo na cena, QPixmap, chave)].
    Devolve False se não deu (aí quem chamou desenha do jeito de sempre).
    """
    global _falhou
    from ..graficos import nivel
    luzes = []
    overlay = getattr(cena, "luz_overlay", None)
    for d, _pol in (getattr(overlay, "luzes", None) or []):   # (só vêm as luzes acesas)
        try:
            luzes.append((float(d["x"]), float(d["y"]), float(d["fraco"]) * CELULA, 1.0, QColor(d["cor"])))
        except (KeyError, TypeError, ValueError):
            continue
    luzes = luzes[:MAX_LUZES]
    painter.beginNativePainting()
    try:
        ctx = QOpenGLContext.currentContext()
        if ctx is None:
            raise RuntimeError("sem contexto OpenGL")
        from .gl_contexto import do_contexto
        des = do_contexto(ctx, "relevo_gl", lambda: _Desenhista(ctx))
        des.desenhar(painter, azulejos, luzes, 1.0 if nivel() == 2 else 0.6)
        return True
    except Exception as erro:
        _falhou = True   # daqui pra frente, o piso volta pro desenho de sempre
        from ..seguranca import registrar_erro
        registrar_erro(f"Piso com relevo (OpenGL) desligado: {erro!r}")
        return False
    finally:
        painter.endNativePainting()
