"""
Desenho dos dados em OpenGL (placa de vídeo): luz com reflexo, borda brilhante nos temas "gema",
sombra macia no chão e números gravados (textura). Fundo transparente, por cima da mesa.

Se qualquer coisa falhar (driver, shader), emite `falhou` e o painel volta pro plano B (render_2d).
"""

import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMatrix4x4, QPainter, QSurfaceFormat, QVector2D, QVector3D
from PyQt6.QtOpenGL import (QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram, QOpenGLTexture,
                            QOpenGLVersionFunctionsFactory, QOpenGLVersionProfile)
from PyQt6.QtOpenGLWidgets import QOpenGLWidget

from .cena3d import camera, material, textura_desgaste
from .geometria import malha_chanfrada, solido

# constantes do OpenGL (o PyQt6 não exporta)
GL_COLOR_BUFFER_BIT = 0x4000
GL_DEPTH_BUFFER_BIT = 0x0100
GL_DEPTH_TEST = 0x0B71
GL_BLEND = 0x0BE2
GL_SRC_ALPHA = 0x0302
GL_ONE_MINUS_SRC_ALPHA = 0x0303
GL_TRIANGLES = 0x0004
GL_FLOAT = 0x1406
GL_MULTISAMPLE = 0x809D

VERT_DADO = """
#version 120
attribute vec3 pos;
attribute vec3 nrm;
attribute vec2 uv;
uniform mat4 mvp;
uniform mat4 modelo;
varying vec3 vN;
varying vec3 vP;
varying vec2 vUV;
void main() {
    vec4 w = modelo * vec4(pos, 1.0);
    vP = w.xyz;
    vN = normalize(mat3(modelo) * nrm);
    vUV = uv;
    gl_Position = mvp * vec4(pos, 1.0);
}
"""

FRAG_DADO = """
#version 120
uniform sampler2D tex;
uniform vec3 corpo;
uniform vec3 corNum;
uniform vec3 olho;
uniform float brilho;
uniform float gema;
uniform float metal;
uniform float apagado;
uniform sampler2D desg;
uniform float usaDesg;
uniform vec2 repDesg;
varying vec3 vN;
varying vec3 vP;
varying vec2 vUV;
void main() {
    vec3 N = normalize(vN);
    vec3 L = normalize(vec3(-0.35, 0.45, 0.82));
    vec3 L2 = normalize(vec3(0.6, -0.3, 0.5));
    vec3 V = normalize(olho - vP);
    vec3 H = normalize(L + V);
    float dif = max(dot(N, L), 0.0) + 0.25 * max(dot(N, L2), 0.0);
    float spec = pow(max(dot(N, H), 0.0), mix(24.0, 70.0, brilho)) * (0.25 + brilho);
    // UV negativo = chanfro (aresta/quina arredondada): sem número
    float temNum = vUV.x < 0.0 ? 0.0 : 1.0;
    float a = texture2D(tex, max(vUV, vec2(0.0))).a * temNum;
    // número gravado: um pouco mais escuro em volta (dá a sensação de baixo-relevo)
    float aura = texture2D(tex, max(vUV, vec2(0.0)) + vec2(0.0015, 0.0015)).a * temNum;
    // (v0.59) desgaste do tema (pátina, arranhões, fita): multiplica a cor do corpo (0,5 = igual)
    vec3 dz = texture2D(desg, abs(vUV) * repDesg).rgb * 2.0;
    vec3 corpoD = corpo * mix(vec3(1.0), dz, usaDesg);
    vec3 base = mix(corpoD, corpoD * 0.55, clamp(aura - a, 0.0, 1.0));
    base = mix(base, corNum, a * 0.96);
    // (v0.74) metal: o brilho tem a cor do metal (ouro brilha dourado) e o corpo reflete menos luz "difusa"
    vec3 specC = mix(vec3(1.0), corpo * 1.5 + 0.15, metal);
    vec3 cor = base * (0.36 + mix(0.72, 0.5, metal) * dif) + specC * spec * (1.0 + metal * 0.8) * (1.0 - a * 0.6);
    float rim = pow(1.0 - max(dot(N, V), 0.0), 2.2) * gema;
    cor += corpo * rim * 0.9 + corNum * a * gema * 0.35;
    cor *= apagado;
    gl_FragColor = vec4(cor, gema > 0.5 ? 0.84 : 1.0);   // (v0.74: translúcido mais de verdade)
}
"""

VERT_SOMBRA = """
#version 120
attribute vec3 pos;
uniform mat4 mvp;
varying vec2 vQ;
void main() {
    vQ = pos.xy;
    gl_Position = mvp * vec4(pos, 1.0);
}
"""

FRAG_SOMBRA = """
#version 120
uniform float forca;
varying vec2 vQ;
void main() {
    float d = length(vQ);
    float a = clamp(1.0 - d, 0.0, 1.0);
    gl_FragColor = vec4(0.0, 0.0, 0.0, a * a * forca);
}
"""


def _qmat(m: np.ndarray) -> QMatrix4x4:
    return QMatrix4x4(*[float(x) for x in m.flatten()])   # QMatrix4x4 recebe por linhas


def formato_gl():
    f = QSurfaceFormat()
    f.setAlphaBufferSize(8)
    f.setDepthBufferSize(24)
    f.setSamples(8)        # antisserrilhado (borda lisa)
    f.setSwapInterval(1)   # sincroniza com o monitor (vsync): animação sem rasgos nem trancos
    return f


class DadosGL(QOpenGLWidget):
    falhou = pyqtSignal(str)

    def __init__(self, painel, parent=None):
        super().__init__(parent)
        self.painel = painel           # quem sabe a rolagem atual, o tempo e desenha o placar
        self.setFormat(formato_gl())
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.ok = False
        self._rolagem = None
        self._tex = None
        self._tex_desg = None
        self._buf = None
        self._faixas = []   # (início, quantidade) de vértices de cada dado no buffer

    # ------------------------------------------------------------ preparo
    def initializeGL(self):
        try:
            perfil = QOpenGLVersionProfile()
            perfil.setVersion(2, 1)
            self.gl = QOpenGLVersionFunctionsFactory.get(perfil, self.context())
            if self.gl is None:
                raise RuntimeError("OpenGL 2.1 indisponível neste PC")
            self.gl.initializeOpenGLFunctions()
            self.prog = QOpenGLShaderProgram(self)
            if not (self.prog.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, VERT_DADO)
                    and self.prog.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, FRAG_DADO)
                    and self.prog.link()):
                raise RuntimeError("shader dos dados: " + self.prog.log())
            self.prog_sombra = QOpenGLShaderProgram(self)
            if not (self.prog_sombra.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, VERT_SOMBRA)
                    and self.prog_sombra.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, FRAG_SOMBRA)
                    and self.prog_sombra.link()):
                raise RuntimeError("shader da sombra: " + self.prog_sombra.log())
            quad = np.array([[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, -1, 0], [1, 1, 0], [-1, 1, 0]], dtype=np.float32)
            self.buf_sombra = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
            self.buf_sombra.create()
            self.buf_sombra.bind()
            self.buf_sombra.allocate(quad.tobytes(), quad.nbytes)
            self.buf_sombra.release()
            self.ok = True
        except Exception as erro:   # sem OpenGL decente: volta pro plano B
            self.ok = False
            self.falhou.emit(str(erro))

    def _preparar(self, rolagem):
        """Monta o buffer de vértices e a textura dos números desta rolagem."""
        if self._tex is not None:
            self._tex.destroy()
        self._tex = QOpenGLTexture(rolagem.imagem)
        if self._tex_desg is not None:
            self._tex_desg.destroy()
            self._tex_desg = None
        desg = textura_desgaste(rolagem.desgaste) if rolagem.desgaste else None   # (v0.74)
        if desg is not None:
            self._tex_desg = QOpenGLTexture(desg)
            self._tex_desg.setWrapMode(QOpenGLTexture.WrapMode.Repeat)
            self._tex_desg.setMinificationFilter(QOpenGLTexture.Filter.LinearMipMapLinear)
            self._tex_desg.setMagnificationFilter(QOpenGLTexture.Filter.Linear)
        self._tex.setMinificationFilter(QOpenGLTexture.Filter.LinearMipMapLinear)
        self._tex.setMagnificationFilter(QOpenGLTexture.Filter.Linear)
        linhas = []
        self._faixas = []
        k = 0.11   # tamanho do chanfro (quinas e arestas arredondadas)
        for i, d in enumerate(rolagem.dados):
            v, faces, normais, _ = solido(d["lados"])
            inicio = len(linhas)
            # UV de cada vértice das faces (com o mesmo "encolhimento" da malha chanfrada)
            uv_de = {}
            for j, face in enumerate(faces):
                uv = np.array(rolagem.uvs[i][j])
                c = uv.mean(axis=0)
                for x, vi in enumerate(face):
                    uv_de[(j, vi)] = c + (uv[x] - c) * (1 - k)
            for tri in malha_chanfrada(d["lados"], k):
                for pos, nrm, origem in tri:
                    uv = uv_de[origem] if origem is not None else (-1.0, -1.0)   # chanfro: sem número
                    linhas.append([*pos, *nrm, *uv])
            self._faixas.append((inicio, len(linhas) - inicio))
        dados = np.array(linhas, dtype=np.float32)
        if self._buf is not None:
            self._buf.destroy()
        self._buf = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        self._buf.create()
        self._buf.bind()
        self._buf.allocate(dados.tobytes(), dados.nbytes)
        self._buf.release()
        self._rolagem = rolagem

    # ------------------------------------------------------------ desenho
    def paintGL(self):
        try:
            self._desenhar()
        except Exception as erro:
            self.ok = False
            self.falhou.emit(str(erro))

    def _desenhar(self):
        f = self.gl
        f.glEnable(GL_MULTISAMPLE)
        f.glClearColor(0, 0, 0, 0)
        f.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        rolagem, t = self.painel.rolagem, self.painel.t
        if not self.ok or rolagem is None:
            return
        if rolagem is not self._rolagem:
            self._preparar(rolagem)
        w, h = self.width(), self.height()
        dpr = self.devicePixelRatioF()
        f.glViewport(0, 0, int(w * dpr), int(h * dpr))
        visao, proj, _, _, olho = camera(w, h)
        vp = proj @ visao
        quadro = rolagem.quadro(t)
        f.glEnable(GL_BLEND)
        f.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # sombras (sem escrever profundidade)
        f.glDisable(GL_DEPTH_TEST)
        sp = self.prog_sombra
        sp.bind()
        self.buf_sombra.bind()
        loc = sp.attributeLocation("pos")
        sp.enableAttributeArray(loc)
        sp.setAttributeBuffer(loc, GL_FLOAT, 0, 3, 12)
        for pos, _q in quadro:
            altura = max(0.0, float(pos[2]))
            r = 1.25 * (1 + altura * 0.12)
            m = np.identity(4)
            m[0, 0], m[1, 1] = r, r * 0.82
            m[:3, 3] = [pos[0] + altura * 0.18, pos[1] - altura * 0.12, 0.002]
            sp.setUniformValue("mvp", _qmat(vp @ m))
            sp.setUniformValue("forca", float(max(0.0, 0.55 - altura * 0.08)))
            f.glDrawArrays(GL_TRIANGLES, 0, 6)
        sp.disableAttributeArray(loc)
        self.buf_sombra.release()
        sp.release()
        # dados
        f.glEnable(GL_DEPTH_TEST)
        corpo, cor_num, brilho, gema = rolagem.corpo, rolagem.cor_num, rolagem.brilho, rolagem.gema   # (v0.74)
        p = self.prog
        p.bind()
        self._buf.bind()
        self._tex.bind(0)
        stride = 8 * 4
        locs = [(p.attributeLocation("pos"), 0, 3), (p.attributeLocation("nrm"), 12, 3), (p.attributeLocation("uv"), 24, 2)]
        for loc, desloc, n in locs:
            p.enableAttributeArray(loc)
            p.setAttributeBuffer(loc, GL_FLOAT, desloc, n, stride)
        p.setUniformValue("tex", 0)   # (int = sampler na unidade 0)
        if self._tex_desg is not None:
            self._tex_desg.bind(1)
        p.setUniformValue("desg", 1)
        p.setUniformValue("usaDesg", 1.0 if self._tex_desg is not None else 0.0)
        p.setUniformValue("metal", 1.0 if getattr(rolagem, "metal", False) else 0.0)   # (v0.74)
        img = rolagem.imagem
        p.setUniformValue("repDesg", QVector2D(img.width() / 512.0, img.height() / 512.0))
        p.setUniformValue("corNum", QVector3D(cor_num.redF(), cor_num.greenF(), cor_num.blueF()))
        p.setUniformValue("olho", QVector3D(*[float(x) for x in olho]))
        p.setUniformValue("brilho", float(brilho))
        p.setUniformValue("gema", 1.0 if gema else 0.0)
        # gema translúcida: desenha do mais longe pro mais perto
        ordem = sorted(range(len(quadro)), key=lambda i: -float(np.linalg.norm(quadro[i][0] - olho)))
        for i in ordem:
            pos, q = quadro[i]
            d = rolagem.dados[i]
            m = rolagem.matriz_modelo(pos, q)
            p.setUniformValue("mvp", _qmat(vp @ m))
            p.setUniformValue("modelo", _qmat(m))
            p.setUniformValue("corpo", QVector3D(corpo.redF(), corpo.greenF(), corpo.blueF()))
            p.setUniformValue("apagado", 0.55 if d.get("fora") else 1.0)
            inicio, qtd = self._faixas[i]
            f.glDrawArrays(GL_TRIANGLES, inicio, qtd)
        for loc, _, _ in locs:
            p.disableAttributeArray(loc)
        self._tex.release(0)
        if self._tex_desg is not None:
            self._tex_desg.release(1)
        self._buf.release()
        p.release()
        f.glDisable(GL_DEPTH_TEST)
        # (v0.65.1) volta pra unidade de textura 0: o desgaste deixava a 1 ativa, e aí TODA imagem/degradê que o
        # QPainter desenhava depois saía PRETA (a "tela toda preta" na falha crítica)
        f.glActiveTexture(0x84C0)   # GL_TEXTURE0
        # placar (nome, total, 20 natural…) por cima, com QPainter
        pintor = QPainter(self)
        self.painel.desenhar_placar(pintor, w, h)
        pintor.end()
