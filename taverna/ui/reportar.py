"""
🐞 Reportar problema (v0.58, pacote do Manel) — menu Ajuda, no mestre e no jogador.

Monta um .zip com o erros.log, a versão, o protocolo, o Windows, a placa de vídeo / OpenGL, as opções de
Gráficos e um texto "o que aconteceu". NÃO manda nada pela internet: salva na Área de Trabalho e abre a pasta;
a pessoa manda o arquivo pro Manel. Caixinha opcional (desligada) "incluir a aventura aberta". Nunca entram
PDFs nem fichas em PDF.
"""

import os
import platform
import sys
import time
import zipfile

from PyQt6.QtCore import QStandardPaths, Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QLabel, QMessageBox, QPlainTextEdit,
                             QVBoxLayout)

LIMITE_LOG = 2 * 1024 * 1024    # (só o fim do erros.log, se ele estiver enorme)


def info_placa() -> str:
    """Nome da placa de vídeo e versão do OpenGL (se não der, diz por quê — nunca derruba)."""
    try:
        from PyQt6.QtGui import QOffscreenSurface, QOpenGLContext
        from PyQt6.QtOpenGL import QOpenGLVersionFunctionsFactory, QOpenGLVersionProfile
        ctx = QOpenGLContext()
        if not ctx.create():
            return "OpenGL: não consegui abrir um contexto"
        sup = QOffscreenSurface()
        sup.setFormat(ctx.format())
        sup.create()
        if not ctx.makeCurrent(sup):
            return "OpenGL: não consegui ativar o contexto"
        try:
            perfil = QOpenGLVersionProfile()
            perfil.setVersion(2, 1)
            gl = QOpenGLVersionFunctionsFactory.get(perfil, ctx)
            gl.initializeOpenGLFunctions()
            vendedor, placa, versao = (gl.glGetString(c) for c in (0x1F00, 0x1F01, 0x1F02))
            return f"Placa de vídeo: {placa} ({vendedor})\nOpenGL: {versao}"
        finally:
            ctx.doneCurrent()
    except Exception as erro:   # (sem placa, sem driver, modo sem tela…)
        return f"OpenGL: não deu pra ler ({erro!r})"


def resumo_sistema(papel: str) -> str:
    from PyQt6.QtCore import PYQT_VERSION_STR, QT_VERSION_STR
    from ..config import APP_VERSAO
    from ..graficos import NIVEIS, graficos
    from ..rede.protocolo import VERSAO_PROTOCOLO
    g = graficos()
    linhas = [
        f"Taverna {APP_VERSAO} · protocolo {VERSAO_PROTOCOLO} · {papel}",
        f"Data: {time.strftime('%d/%m/%Y %H:%M:%S')}",
        f"Windows: {platform.platform()} ({platform.machine()})",
        f"Python {platform.python_version()} · PyQt {PYQT_VERSION_STR} · Qt {QT_VERSION_STR}",
        info_placa(),
        f"Gráficos: {NIVEIS.get(g.atual, g.atual)}",
        "Mesa em 3D: " + ("ligada" if g.mesa3d else "desligada")
        + " · Dados 3D: " + ("ligados" if g.dados3d else "desligados")
        + " · Tela tremer: " + ("sim" if g.tremor else "não") + " · Tela clarear: " + ("sim" if g.clarao else "não"),
    ]
    return "\n".join(linhas)


def pasta_padrao() -> str:
    return QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DesktopLocation) or os.path.expanduser("~")


def gerar_pacote(descricao: str, papel: str, aventura: str | None = None, pasta: str | None = None) -> str:
    """Cria o .zip e devolve o caminho. `aventura` = caminho do .taverna aberto (só se a pessoa marcou)."""
    from ..seguranca import caminho_log
    pasta = pasta or pasta_padrao()
    os.makedirs(pasta, exist_ok=True)
    nome = time.strftime("Taverna_problema_%Y-%m-%d_%H%M%S.zip")
    caminho = os.path.join(pasta, nome)
    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("o_que_aconteceu.txt", (descricao.strip() or "(a pessoa não escreveu nada)") + "\n")
        z.writestr("sistema.txt", resumo_sistema(papel) + "\n")
        log = caminho_log()
        if os.path.isfile(log):
            with open(log, "rb") as f:
                f.seek(max(0, os.path.getsize(log) - LIMITE_LOG))
                z.writestr("erros.log", f.read())
        else:
            z.writestr("erros.log", "(nenhum erro anotado)\n")
        if aventura and os.path.isfile(aventura) and aventura.lower().endswith(".taverna"):
            z.write(aventura, "aventura/" + os.path.basename(aventura))   # (só o .taverna: nada de PDF/ficha)
    return caminho


class JanelaReportar(QDialog):
    def __init__(self, papel: str, aventura: str | None = None, parent=None):
        super().__init__(parent)
        self.papel = papel
        self.aventura = aventura
        self.caminho = ""
        self.setWindowTitle("🐞  Reportar problema")
        self.resize(560, 470)
        lay = QVBoxLayout(self)
        topo = QLabel("<b>Deu algum problema?</b> Conta o que aconteceu e o Taverna monta um arquivo .zip na "
                      "sua <b>Área de Trabalho</b>.<br><br>"
                      "<b>Nada é enviado pela internet.</b> Depois é só mandar o arquivo pro Manel "
                      "(WhatsApp, Discord, e-mail…).")
        topo.setWordWrap(True)
        lay.addWidget(topo)
        self.texto = QPlainTextEdit()
        self.texto.setPlaceholderText("O que aconteceu? O que você estava fazendo na hora? Aconteceu mais de uma vez?")
        lay.addWidget(self.texto, 1)
        self.incluir = QCheckBox("Incluir a aventura aberta (o arquivo .taverna)")
        self.incluir.setChecked(False)
        tem = bool(aventura) and os.path.isfile(aventura or "")
        self.incluir.setEnabled(tem)
        self.incluir.setVisible(papel == "mestre")
        self.incluir.setToolTip("Ajuda a achar problema de mapa/objeto. Só o .taverna vai — nunca PDFs nem fichas."
                                if tem else "Salve a aventura primeiro pra poder incluir.")
        lay.addWidget(self.incluir)
        vai = QLabel("Vai no arquivo: o registro de erros (erros.log), a versão do Taverna, o Windows, a placa de "
                     "vídeo e as opções de Gráficos. <b>Nunca</b> vão PDFs nem fichas.")
        vai.setWordWrap(True)
        vai.setStyleSheet("color: gray;")
        lay.addWidget(vai)
        botoes = QDialogButtonBox()
        self.btn_gerar = botoes.addButton("Gerar o arquivo", QDialogButtonBox.ButtonRole.AcceptRole)
        botoes.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        botoes.accepted.connect(self.gerar)
        botoes.rejected.connect(self.reject)
        lay.addWidget(botoes)
        from .acabamento import iconizar
        iconizar(self)

    def gerar(self, pasta: str | None = None, abrir_pasta: bool = True):
        try:
            self.caminho = gerar_pacote(self.texto.toPlainText(), self.papel,
                                        self.aventura if self.incluir.isChecked() else None, pasta)
        except OSError as erro:
            QMessageBox.warning(self, "Reportar problema", f"Não consegui criar o arquivo:\n{erro}")
            return ""
        if abrir_pasta:
            QMessageBox.information(self, "Reportar problema",
                                    f"Pronto! O arquivo ficou na sua Área de Trabalho:\n\n{os.path.basename(self.caminho)}"
                                    "\n\nAgora é só mandar ele pro Manel.")
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(self.caminho)))
        self.accept()
        return self.caminho


def abrir(janela, papel: str):
    aventura = getattr(janela, "caminho_cena", None) if papel == "mestre" else None
    d = JanelaReportar(papel, aventura, janela)
    d.setWindowModality(Qt.WindowModality.ApplicationModal)
    d.show()
    return d


if __name__ == "__main__":   # (rodar sozinho: só mostra o resumo)
    from PyQt6.QtWidgets import QApplication
    _a = QApplication(sys.argv)
    print(resumo_sistema("teste"))
