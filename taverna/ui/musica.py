"""
Música pelo YouTube — com o PLAYER OFICIAL do YouTube, visível (não baixa nem extrai o áudio).

O mestre cola links numa fila e controla (tocar, pausar, próxima). Cada jogador tem o mesmo
player oficial na tela dele, que segue o do mestre. Cada um ajusta o próprio volume.

Precisa do componente PyQt6-WebEngine (um navegador embutido). Sem ele, o programa funciona
normal e só mostra um aviso com o link pra abrir no navegador.
"""

import json
import re

from PyQt6.QtCore import QTimer, QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

try:
    from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    TEM_WEB = True

    class _PaginaQuieta(QWebEnginePage):
        # O player do YouTube escreve um monte de avisos internos no console
        # ("web-share", "postMessage", "WebGPU"...). Não são erros do Taverna: ignora.
        def javaScriptConsoleMessage(self, nivel, mensagem, linha, origem):
            pass
except Exception:
    TEM_WEB = False

TAMANHO_MINIMO = 220   # o YouTube pede o player com pelo menos 200×200 visível

_PADRAO_ID = re.compile(r"(?:v=|youtu\.be/|/shorts/|/embed/|/live/|/v/)([A-Za-z0-9_-]{11})")


def extrair_id(texto: str) -> str | None:
    texto = (texto or "").strip()
    m = _PADRAO_ID.search(texto)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", texto):
        return texto
    return None


def link_do_video(vid: str) -> str:
    return f"https://www.youtube.com/watch?v={vid}"


HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>html,body{margin:0;height:100%;background:#000;overflow:hidden}#p{width:100%;height:100%}</style>
</head><body><div id="p"></div>
<script>
var player=null, pronto=false, pend=null, erro=null, vol=80;
var tag=document.createElement('script'); tag.src="https://www.youtube.com/iframe_api";
document.head.appendChild(tag);
function onYouTubeIframeAPIReady(){
  player=new YT.Player('p',{width:'100%',height:'100%',
    playerVars:{autoplay:1,controls:1,rel:0,playsinline:1,modestbranding:1,origin:'http://localhost'},
    events:{onReady:function(){pronto=true;player.setVolume(vol);if(pend){carregar(pend[0],pend[1],pend[2]);pend=null;}},
            onError:function(e){erro=e.data;}}});
}
function carregar(id,t,tocar){
  erro=null;
  if(!pronto){pend=[id,t,tocar];return;}
  if(tocar){player.loadVideoById({videoId:id,startSeconds:t});}else{player.cueVideoById({videoId:id,startSeconds:t});}
}
function tocar(){if(pronto)player.playVideo();}
function pausar(){if(pronto)player.pauseVideo();}
function parar(){pend=null;if(pronto)player.stopVideo();}
function ir(t){if(pronto)player.seekTo(t,true);}
function volume(v){vol=v;if(pronto){player.setVolume(v);if(v<=0)player.mute();else player.unMute();}}
function info(){
  if(!pronto)return JSON.stringify({pronto:false,erro:erro});
  var d={};try{d=player.getVideoData()||{};}catch(e){}
  return JSON.stringify({pronto:true,estado:player.getPlayerState(),t:player.getCurrentTime()||0,
                         dur:player.getDuration()||0,titulo:d.title||"",id:d.video_id||"",erro:erro});
}
</script></body></html>"""


class PlayerYouTube(QWidget):
    """O player oficial embutido. info_mudou(dict) a cada segundo (estado, tempo, título)."""
    info_mudou = pyqtSignal(dict)
    acabou = pyqtSignal()

    # estados do YouTube: -1 não começou · 0 acabou · 1 tocando · 2 pausado · 3 carregando · 5 pronto
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vid = None
        self.info = {}
        self._estado_antes = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        if TEM_WEB:
            self.web = QWebEngineView()
            self.web.setPage(_PaginaQuieta(self.web))
            s = self.web.settings()
            s.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
            s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            self.web.setMinimumSize(TAMANHO_MINIMO, int(TAMANHO_MINIMO * 9 / 16) + 4)
            self.web.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.web.setHtml(HTML, QUrl("http://localhost/"))
            lay.addWidget(self.web)
            self._timer = QTimer(self)
            self._timer.setInterval(1000)
            self._timer.timeout.connect(self._perguntar)
            self._timer.start()
        else:
            self.web = None
            aviso = QLabel("🎵 Pra ouvir a música do YouTube aqui dentro, falta o componente "
                           "<b>PyQt6-WebEngine</b>.<br>Feche o Taverna e rode "
                           "<b>instalar_musica.bat</b> (uma vez só).")
            aviso.setWordWrap(True)
            aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)
            aviso.setTextFormat(Qt.TextFormat.RichText)
            lay.addWidget(aviso)
            self.btn_navegador = QPushButton("Abrir a música no navegador")
            self.btn_navegador.setEnabled(False)
            self.btn_navegador.clicked.connect(
                lambda: self.vid and QDesktopServices.openUrl(QUrl(link_do_video(self.vid))))
            lay.addWidget(self.btn_navegador)

    @property
    def disponivel(self) -> bool:
        return self.web is not None

    def _js(self, codigo, depois=None):
        if self.web is None:
            return
        if depois is None:
            self.web.page().runJavaScript(codigo)
        else:
            self.web.page().runJavaScript(codigo, depois)

    # --- comandos
    def carregar(self, vid: str, t: float = 0.0, tocar: bool = True):
        self.vid = vid
        if self.web is None:
            self.btn_navegador.setEnabled(bool(vid))
            return
        self._js(f"carregar({json.dumps(vid)}, {float(t):.2f}, {'true' if tocar else 'false'})")

    def tocar(self):
        self._js("tocar()")

    def pausar(self):
        self._js("pausar()")

    def parar(self):
        self.vid = None
        self._js("parar()")

    def ir(self, t: float):
        self._js(f"ir({float(t):.2f})")

    def volume(self, v: int):
        self._js(f"volume({int(v)})")

    # --- acompanhamento
    def _perguntar(self):
        self._js("info()", self._resposta)

    def _resposta(self, texto):
        try:
            info = json.loads(texto) if texto else {}
        except (TypeError, ValueError):
            return
        self.info = info
        estado = info.get("estado")
        if estado == 0 and self._estado_antes not in (0, None):
            self.acabou.emit()
        self._estado_antes = estado
        self.info_mudou.emit(info)


class SeguidorDeMusica:
    """Player: acompanha o que o mestre mandou (estado["musica"])."""

    def __init__(self, player: PlayerYouTube):
        self.player = player
        self.atual = None          # id que eu carreguei
        self.tocando = False

    def aplicar(self, m: dict | None) -> bool:
        """Devolve True quando começou uma música nova (pra janela mostrar o player)."""
        m = m or {}
        vid = m.get("id")
        tocando = bool(m.get("tocando"))
        pos = float(m.get("pos", 0) or 0)
        nova = False
        if not vid:
            if self.atual:
                self.player.parar()
            self.atual, self.tocando = None, False
            return False
        if vid != self.atual:
            self.player.carregar(vid, pos, tocando)
            self.atual, self.tocando = vid, tocando
            return True
        if tocando != self.tocando:
            if tocando:
                self.player.ir(pos)
                self.player.tocar()
            else:
                self.player.pausar()
            self.tocando = tocando
        elif tocando:
            t = float(self.player.info.get("t", pos) or 0)
            if self.player.info.get("pronto") and abs(t - pos) > 4:
                self.player.ir(pos)
            if self.player.info.get("estado") == 2:   # o jogador pausou sem querer: volta
                self.player.tocar()
        return nova
