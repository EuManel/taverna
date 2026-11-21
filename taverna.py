"""
Taverna — o programa ÚNICO (v0.49): na tela inicial a pessoa escolhe Mestre ou Jogador.

Rodar:  python taverna.py
(mestre.py e player.py continuam funcionando, abrindo direto cada um.)
"""

import sys

from PyQt6.QtCore import QLocale
from PyQt6.QtWidgets import QApplication

from taverna.config import APP_NOME
from taverna.ui.tema import icone_app, preparar_icone_windows


def main():
    preparar_icone_windows("Taverna.App")
    # Números no padrão brasileiro (16,5 m)
    QLocale.setDefault(QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil))
    # A música do YouTube usa um navegador embutido (PyQt6-WebEngine, opcional),
    # que precisa ser carregado ANTES de criar o app.
    from PyQt6.QtCore import QCoreApplication, Qt
    try:
        import PyQt6.QtWebEngineWidgets  # noqa: F401
    except Exception:
        pass
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    # (v0.56, otimização) a tela inicial em 3D desenha com OpenGL (o mesmo da mesa): o driver da placa guarda os
    # shaders já compilados, e da 2ª vez em diante o 3D aparece bem mais rápido (no Direct3D eles eram refeitos
    # toda vez que o programa abria).
    import os
    if not os.environ.get("QT_QUICK_BACKEND") and not os.environ.get("QSG_RHI_BACKEND"):
        from PyQt6.QtQuick import QQuickWindow, QSGRendererInterface
        QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.OpenGL)
    app = QApplication(sys.argv)
    from taverna import idioma
    idioma.instalar(app)   # 🇧🇷/🇺🇸 os textos saem no idioma escolhido na tela inicial
    app.setApplicationName(APP_NOME)
    app.setWindowIcon(icone_app())
    app.setStyle("Fusion")
    from taverna.ui.tema import gerar_qss, tema_preferido
    app.setStyleSheet(gerar_qss(tema_preferido()))

    from taverna.ui.cursor_global import instalar as instalar_luva
    instalar_luva(app)   # 🧤 a luvinha em todas as janelas do Taverna
    from taverna.ui.lancador import JanelaLancador
    lancador = JanelaLancador()
    from taverna.seguranca import instalar

    def janela_ativa():
        for j in (lancador.mestre, lancador.player):
            if j is not None and j.isVisible():
                return j
        return lancador
    instalar(janela_ativa)
    lancador.show()
    codigo = app.exec()
    # (v0.50) Sai direto: as janelas já fecharam (e salvaram). Deixar o Python ir apagando os objetos do Qt
    # um por um às vezes derrubava o programa NA SAÍDA (erro 0xC0000409 do Windows).
    import os
    for saida in (sys.stdout, sys.stderr):   # (v0.65.1) no .exe sem console elas não existem (None)
        if saida is not None:
            try:
                saida.flush()
            except (OSError, ValueError):
                pass
    os._exit(codigo)


if __name__ == "__main__":
    main()
