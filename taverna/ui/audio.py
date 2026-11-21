"""
Efeitos sonoros (mesa de som).

- O mestre importa arquivos de som DELE (mp3, ogg, wav… — ex.: Pixabay, Freesound, MyInstants).
  A lista fica guardada no PC dele (QSettings), igual aos "Meus PDFs".
- Quando ele toca "pra todos", o arquivo vai UMA vez pra cada jogador (guardado numa pasta
  temporária) e depois só o comando "toca" / "para".
- Sons em "ambiente" repetem até o mestre parar (chuva, taverna cheia, masmorra...).
"""

import hashlib
import os
import tempfile

from PyQt6.QtCore import QObject, QSettings, QUrl

try:
    from PyQt6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer
    TEM_AUDIO = not os.environ.get("TAVERNA_SEM_AUDIO")   # (os testes desligam o som de verdade)
except Exception:   # sem o módulo de multimídia: o resto do programa continua funcionando
    TEM_AUDIO = False

_tem_saida = None


def tem_saida_de_som() -> bool:
    """Tem caixa de som/fone? (sem nenhuma, nem tenta tocar)"""
    global _tem_saida
    if _tem_saida is None:
        try:
            _tem_saida = TEM_AUDIO and bool(QMediaDevices.audioOutputs())
        except Exception:
            _tem_saida = False
    return _tem_saida

EXTENSOES = ("mp3", "ogg", "wav", "flac", "m4a", "aac", "opus", "webm")
LIMITE_MB = 25


def id_do_arquivo(dados: bytes) -> str:
    return hashlib.sha1(dados).hexdigest()[:20]


def pasta_cache() -> str:
    pasta = os.path.join(tempfile.gettempdir(), "taverna_sons")
    os.makedirs(pasta, exist_ok=True)
    return pasta


# ---------------------------------------------------------------- biblioteca do mestre
class BibliotecaSons:
    """Lista de sons do mestre: [{nome, caminho, ambiente(bool), vol(0-100)}]."""

    def __init__(self, app_nome="Mestre"):
        self._cfg = QSettings("Taverna", app_nome)

    def lista(self) -> list[dict]:
        v = self._cfg.value("sons", []) or []
        return [dict(x) for x in v if isinstance(x, dict) and x.get("caminho")]

    def salvar(self, lista: list[dict]):
        self._cfg.setValue("sons", lista)

    def adicionar(self, caminhos: list[str]) -> int:
        lista = self.lista()
        ja = {os.path.normcase(s["caminho"]) for s in lista}
        n = 0
        for c in caminhos:
            if os.path.normcase(c) in ja or not os.path.isfile(c):
                continue
            nome = os.path.splitext(os.path.basename(c))[0].replace("_", " ").replace("-", " ")
            lista.append({"nome": nome[:60], "caminho": c, "ambiente": False, "vol": 80})
            n += 1
        self.salvar(lista)
        return n


# ---------------------------------------------------------------- quem toca
class TocadorSons(QObject):
    """Toca vários sons ao mesmo tempo. Cada som tem um id (hash do arquivo)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.volume_geral = 0.8           # 0..1 (cada pessoa ajusta o seu)
        self.mudo = False
        self.arquivos: dict[str, str] = {}   # id -> caminho no disco
        self._tocando: list[tuple] = []      # (id, player, saida, vol_som, ambiente)

    def tem(self, sid: str) -> bool:
        c = self.arquivos.get(sid)
        return bool(c and os.path.isfile(c))

    def registrar_arquivo(self, sid: str, caminho: str):
        self.arquivos[sid] = caminho

    def guardar(self, sid: str, ext: str, dados: bytes) -> str:
        ext = ext if ext in EXTENSOES else "mp3"
        caminho = os.path.join(pasta_cache(), f"{sid}.{ext}")
        if not os.path.isfile(caminho):
            with open(caminho, "wb") as f:
                f.write(dados)
        self.arquivos[sid] = caminho
        return caminho

    def tocar(self, sid: str, vol: float = 0.8, ambiente: bool = False) -> bool:
        if not self.tem(sid) or not tem_saida_de_som():
            return False
        if ambiente:
            self.parar(sid)   # ambiente: um só de cada
        self._limpar()
        player = QMediaPlayer(self)
        saida = QAudioOutput(self)
        player.setAudioOutput(saida)
        saida.setVolume(0.0 if self.mudo else max(0.0, min(1.0, vol * self.volume_geral)))
        player.setSource(QUrl.fromLocalFile(self.arquivos[sid]))
        if ambiente:
            player.setLoops(QMediaPlayer.Loops.Infinite)
        player.play()
        self._tocando.append((sid, player, saida, vol, ambiente))
        return True

    def parar(self, sid: str | None = None):
        restam = []
        for item in self._tocando:
            if sid is None or item[0] == sid:
                item[1].stop()
                item[1].deleteLater()
                item[2].deleteLater()
            else:
                restam.append(item)
        self._tocando = restam

    def definir_volume(self, geral: float | None = None, mudo: bool | None = None):
        if geral is not None:
            self.volume_geral = max(0.0, min(1.0, geral))
        if mudo is not None:
            self.mudo = mudo
        for sid, player, saida, vol, amb in self._tocando:
            saida.setVolume(0.0 if self.mudo else vol * self.volume_geral)

    def ambientes(self) -> list[str]:
        self._limpar()
        return [i[0] for i in self._tocando if i[4]]

    def _limpar(self):
        vivos = []
        for item in self._tocando:
            if not item[4] and item[1].playbackState() == QMediaPlayer.PlaybackState.StoppedState \
                    and item[1].mediaStatus() in (QMediaPlayer.MediaStatus.EndOfMedia,
                                                  QMediaPlayer.MediaStatus.InvalidMedia):
                item[1].deleteLater()
                item[2].deleteLater()
            else:
                vivos.append(item)
        self._tocando = vivos
