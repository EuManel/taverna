"""
Rede de segurança: se der um erro inesperado em alguma tela, o Taverna NÃO fecha.
O erro vai pra um arquivo (Documentos/Taverna/erros.log) e aparece um aviso discreto.
"""

import os
import sys
import time
import traceback


def caminho_log() -> str:
    try:
        from PyQt6.QtCore import QStandardPaths
        docs = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    except Exception:
        docs = ""
    pasta = os.path.join(docs or os.path.expanduser("~"), "Taverna")
    os.makedirs(pasta, exist_ok=True)
    return os.path.join(pasta, "erros.log")


def registrar_erro(texto: str):
    """Anota um problema no erros.log sem interromper nada (ex.: OpenGL não funcionou neste PC)."""
    try:
        with open(caminho_log(), "a", encoding="utf-8") as f:
            f.write(f"\n===== {time.strftime('%d/%m/%Y %H:%M:%S')} =====\n{texto}\n")
    except OSError:
        pass


def instalar(janela_de=None):
    """janela_de: função que devolve a janela principal (pra mostrar o aviso na barra de status)."""
    ultimo = {"quando": 0.0}

    def gancho(tipo, valor, tb):
        texto = "".join(traceback.format_exception(tipo, valor, tb))
        try:
            with open(caminho_log(), "a", encoding="utf-8") as f:
                f.write(f"\n===== {time.strftime('%d/%m/%Y %H:%M:%S')} =====\n{texto}")
        except OSError:
            pass
        if sys.stderr is not None:   # (no .exe sem console não existe stderr: era ele que derrubava o programa)
            try:
                sys.stderr.write(texto)
            except (OSError, ValueError):
                pass
        agora = time.monotonic()
        if agora - ultimo["quando"] > 3 and janela_de is not None:   # não entope de avisos
            ultimo["quando"] = agora
            try:
                j = janela_de()
                if j is not None:
                    j.statusBar().showMessage(
                        f"⚠ Deu um erro aqui ({tipo.__name__}), mas o Taverna continua aberto. "
                        f"Detalhes em Documentos/Taverna/erros.log — manda esse arquivo pro Claudio.", 15000)
            except Exception:
                pass

    sys.excepthook = gancho
