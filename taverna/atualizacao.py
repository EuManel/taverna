"""
🔔 Aviso de versão nova (v1.0.1).

Ao abrir, a tela inicial pergunta ao GitHub qual é a última Release do Taverna. Se for mais nova que esta, aparece
um aviso no rodapé com link pro itch.io. Regras (combinadas com o Manel):
  - SÓ AVISA: nunca baixa nem instala nada sozinho;
  - sem internet / GitHub fora / resposta estranha: não aparece nada e o programa segue normal;
  - no máximo UMA consulta por dia (o resultado fica guardado nas preferências);
  - a consulta não leva nenhum dado da pessoa (só um nome genérico de programa no User-Agent);
  - a tag da Release tem que ser "vX.Y" ou "vX.Y.Z" (ver COMO_LANCAR_VERSAO.md);
  - TAVERNA_SEM_ATUALIZACAO=1 desliga (os testes usam).
"""

import json
import os
import re
import threading
import time
import urllib.request

from PyQt6.QtCore import QObject, QSettings, pyqtSignal

from .config import APP_VERSAO

URL_API = "https://api.github.com/repos/EuManel/taverna/releases/latest"
PAGINA = "https://omanel.itch.io/taverna"
INTERVALO = 24 * 3600          # segundos entre consultas
TEMPO_LIMITE = 5               # segundos esperando o GitHub


def versao_tupla(texto):
    """'v1.2' -> (1, 2, 0) · '1.0.0' -> (1, 0, 0) · lixo -> None."""
    numeros = re.findall(r"\d+", texto or "")
    if not numeros or not re.match(r"^\s*v?\d", texto or ""):
        return None
    return tuple(int(n) for n in (numeros + ["0", "0"])[:3])


def e_mais_nova(tag, atual=APP_VERSAO):
    a, b = versao_tupla(tag), versao_tupla(atual)
    return a is not None and b is not None and a > b


def ler_release(dados):
    """A tag da última Release, de uma resposta da API do GitHub (bytes ou str). Rascunho/pré-lançamento: None."""
    try:
        info = json.loads(dados)
    except (ValueError, TypeError):
        return None
    if not isinstance(info, dict) or info.get("draft") or info.get("prerelease"):
        return None
    tag = info.get("tag_name")
    return tag if isinstance(tag, str) and versao_tupla(tag) else None


def _baixar_info():
    pedido = urllib.request.Request(URL_API, headers={"Accept": "application/vnd.github+json",
                                                      "User-Agent": "Taverna-VTT"})
    with urllib.request.urlopen(pedido, timeout=TEMPO_LIMITE) as r:
        return r.read(200_000)


class Verificador(QObject):
    """Faz a consulta numa thread e avisa (no Qt) com `novaVersao("v1.1")` quando há versão mais nova."""
    novaVersao = pyqtSignal(str)
    _resultado = pyqtSignal(str)

    def __init__(self, parent=None, baixar=None):
        super().__init__(parent)
        self._baixar = baixar or _baixar_info
        self._thread = None
        self._resultado.connect(self._resposta)        # (chega da thread; o Qt entrega na thread da tela)

    def iniciar(self):
        if os.environ.get("TAVERNA_SEM_ATUALIZACAO"):
            return
        cfg = QSettings("Taverna", "Geral")
        if time.time() - cfg.value("atualizacao/quando", 0.0, type=float) < INTERVALO:
            self._avisar(cfg.value("atualizacao/tag", "", type=str))   # consultou há pouco: usa o que já sabe
            return
        self._thread = threading.Thread(target=self._consultar, name="taverna-atualizacao", daemon=True)
        self._thread.start()

    def _consultar(self):
        try:
            tag = ler_release(self._baixar()) or ""
        except Exception:                               # sem internet, GitHub fora, demorou…: fica quieto
            return
        try:
            self._resultado.emit(tag)
        except RuntimeError:                            # (a janela já fechou)
            pass

    def _resposta(self, tag):
        """O GitHub respondeu: guarda (pra não perguntar de novo hoje) e avisa se for mais nova."""
        cfg = QSettings("Taverna", "Geral")
        cfg.setValue("atualizacao/tag", tag)
        cfg.setValue("atualizacao/quando", time.time())
        self._avisar(tag)

    def _avisar(self, tag):
        if e_mais_nova(tag):
            self.novaVersao.emit(tag)
