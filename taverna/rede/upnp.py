"""
🌐 Entrar sem Radmin (v0.65 — item 10 dos PEDIDOS_v0.58).

Ao abrir a taverna, o Taverna pede pro ROTEADOR abrir a porta sozinho (UPnP), feito à mão com `socket` e `urllib`
(sem pacote: o Python 3.15 ficou sem vários):
  1. SSDP: grita na rede local "tem roteador aí?" (M-SEARCH em 239.255.255.250:1900) e lê o endereço da descrição;
  2. lê a descrição (XML) e acha o serviço WANIPConnection (ou WANPPPConnection);
  3. SOAP: GetExternalIPAddress (o IP de fora), AddPortMapping (abre), DeletePortMapping (fecha ao sair).
Se o IP de fora que o roteador diz for PRIVADO ou 100.64.x (CGNAT, comum nas operadoras do Brasil), abrir a porta
não adianta: a internet da pessoa não recebe conexões → avisa pra usar o Radmin VPN (que continua funcionando).

CÓDIGO DE SALA: o IP de fora + a porta codificados em 10 letras/números ("TAV-7K3PQ-X2M9A"), pra o jogador colar
no "Entrar na sessão" (ele também aceita IP e "IP:porta").

⚠ Só dá pra conferir de verdade com um amigo FORA da rede (os testes conferem o protocolo com um roteador falso).
"""

import ipaddress
import re
import socket
import threading
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

SSDP = ("239.255.255.250", 1900)
SERVICOS = ("urn:schemas-upnp-org:service:WANIPConnection:2", "urn:schemas-upnp-org:service:WANIPConnection:1",
            "urn:schemas-upnp-org:service:WANPPPConnection:1")
ALFABETO = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"   # Crockford: sem I, L, O, U (não confunde)
DESCRICAO = "Taverna (VTT)"


class ErroUPnP(Exception):
    pass


# ====================================================================== código de sala
def codigo_de_sala(ip: str, porta: int) -> str:
    n = int(ipaddress.IPv4Address(ip)) << 16 | (int(porta) & 0xFFFF)
    letras = []
    for _ in range(10):
        letras.append(ALFABETO[n & 31])
        n >>= 5
    s = "".join(reversed(letras))
    return f"TAV-{s[:5]}-{s[5:]}"


def ler_codigo(codigo: str) -> tuple[str, int] | None:
    s = re.sub(r"[\s\-]", "", codigo.upper())
    if s.startswith("TAV"):
        s = s[3:]
    s = s.replace("O", "0").replace("I", "1").replace("L", "1")
    if len(s) != 10 or any(c not in ALFABETO for c in s):
        return None
    n = 0
    for c in s:
        n = n * 32 + ALFABETO.index(c)
    return str(ipaddress.IPv4Address(n >> 16)), n & 0xFFFF


def ler_endereco(texto: str, porta_padrao: int) -> tuple[str, int]:
    """O que o jogador digitou → (ip, porta). Aceita código de sala, "ip:porta" e só o ip."""
    t = (texto or "").strip()
    if t.upper().startswith("TAV"):
        r = ler_codigo(t)
        if r:
            return r
    m = re.fullmatch(r"\[?([^\]\s]+?)\]?:(\d{2,5})", t)
    if m and "." in m.group(1):
        return m.group(1), int(m.group(2))
    return t, porta_padrao


# ====================================================================== rede
def ip_problematico(ip: str) -> str | None:
    """Por que esse IP "de fora" não recebe conexões (None = parece público, dá certo)."""
    try:
        a = ipaddress.IPv4Address(ip)
    except ValueError:
        return "o roteador não informou o IP de fora"
    if a in ipaddress.IPv4Network("100.64.0.0/10"):
        return "CGNAT"
    if a.is_private or a.is_loopback or a.is_link_local or a.is_unspecified:
        return "IP privado (tem outro roteador ou a operadora usa CGNAT)"
    return None


def descobrir(timeout: float = 2.5, destino=SSDP) -> list[str]:
    """Endereços (LOCATION) das descrições dos roteadores que responderam."""
    achados = []
    for st in ("urn:schemas-upnp-org:device:InternetGatewayDevice:1", SERVICOS[1], "upnp:rootdevice"):
        msg = ("M-SEARCH * HTTP/1.1\r\n"
               f"HOST: {destino[0]}:{destino[1]}\r\n"
               'MAN: "ssdp:discover"\r\n'
               "MX: 2\r\n"
               f"ST: {st}\r\n\r\n").encode()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            s.settimeout(timeout)
            s.sendto(msg, destino)
            while True:
                try:
                    dados, _ = s.recvfrom(4096)
                except socket.timeout:
                    break
                m = re.search(rb"(?im)^location:\s*(\S+)", dados)
                if m:
                    url = m.group(1).decode(errors="ignore")
                    if url not in achados:
                        achados.append(url)
        except OSError:
            pass
        finally:
            s.close()
        if achados:
            break
    return achados


def _sem_ns(tag: str) -> str:
    return tag.split("}", 1)[-1]


def servico(url_descricao: str, timeout: float = 4.0) -> tuple[str, str]:
    """(url de controle, tipo do serviço) do WANIPConnection/WANPPPConnection."""
    with urllib.request.urlopen(url_descricao, timeout=timeout) as r:
        raiz = ET.fromstring(r.read())
    base = url_descricao
    for el in raiz.iter():
        if _sem_ns(el.tag) == "URLBase" and (el.text or "").strip():
            base = el.text.strip()
    candidatos = {}
    for el in raiz.iter():
        if _sem_ns(el.tag) != "service":
            continue
        campos = {_sem_ns(c.tag): (c.text or "").strip() for c in el}
        if campos.get("serviceType") in SERVICOS and campos.get("controlURL"):
            candidatos[campos["serviceType"]] = urljoin(base, campos["controlURL"])
    for tipo in SERVICOS:
        if tipo in candidatos:
            return candidatos[tipo], tipo
    raise ErroUPnP("o roteador não tem o serviço de abrir portas (WANIPConnection)")


def soap(controle: str, tipo: str, acao: str, args: dict, timeout: float = 5.0) -> dict:
    corpo = "".join(f"<{k}>{v}</{k}>" for k, v in args.items())
    xml = ('<?xml version="1.0"?>'
           '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
           's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>'
           f'<u:{acao} xmlns:u="{tipo}">{corpo}</u:{acao}></s:Body></s:Envelope>').encode()
    req = urllib.request.Request(controle, data=xml, method="POST", headers={
        "Content-Type": 'text/xml; charset="utf-8"', "SOAPAction": f'"{tipo}#{acao}"'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raiz = ET.fromstring(r.read())
    except urllib.error.HTTPError as erro:
        texto = erro.read().decode(errors="ignore")
        m = re.search(r"<errorDescription>(.*?)</errorDescription>", texto)
        raise ErroUPnP(f"o roteador recusou ({acao}): {m.group(1) if m else erro.code}") from erro
    saida = {}
    for el in raiz.iter():
        if not list(el) and el.text is not None:
            saida[_sem_ns(el.tag)] = el.text.strip()
    return saida


def ip_local_para(host: str) -> str:
    """O IP DESTE PC na rede do roteador (o roteador manda as conexões de fora pra ele)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((host, 1900))
        return s.getsockname()[0]
    finally:
        s.close()


class Roteador:
    def __init__(self, controle: str, tipo: str):
        self.controle, self.tipo = controle, tipo

    @classmethod
    def achar(cls, timeout: float = 2.5, destino=SSDP) -> "Roteador":
        locais = descobrir(timeout, destino)
        if not locais:
            raise ErroUPnP("nenhum roteador respondeu (o UPnP pode estar desligado no roteador)")
        ultimo = None
        for url in locais:
            try:
                return cls(*servico(url))
            except (ErroUPnP, OSError, ET.ParseError) as erro:
                ultimo = erro
        raise ErroUPnP(str(ultimo or "não achei o serviço do roteador"))

    def ip_externo(self) -> str:
        return soap(self.controle, self.tipo, "GetExternalIPAddress", {}).get("NewExternalIPAddress", "")

    def abrir(self, porta: int, ip_local: str | None = None, horas: int = 12):
        from urllib.parse import urlparse
        ip_local = ip_local or ip_local_para(urlparse(self.controle).hostname)
        soap(self.controle, self.tipo, "AddPortMapping", {
            "NewRemoteHost": "", "NewExternalPort": int(porta), "NewProtocol": "TCP",
            "NewInternalPort": int(porta), "NewInternalClient": ip_local, "NewEnabled": 1,
            "NewPortMappingDescription": DESCRICAO, "NewLeaseDuration": int(horas) * 3600})
        return ip_local

    def fechar(self, porta: int):
        soap(self.controle, self.tipo, "DeletePortMapping",
             {"NewRemoteHost": "", "NewExternalPort": int(porta), "NewProtocol": "TCP"}, timeout=3.0)


def abrir_porta(porta: int, timeout: float = 2.5, destino=SSDP) -> dict:
    """Faz tudo. Devolve {"ok", "ip_externo", "codigo", "motivo", "roteador"} — nunca levanta erro."""
    try:
        rot = Roteador.achar(timeout, destino)
        ip = rot.ip_externo()
        problema = ip_problematico(ip)
        if problema:
            return {"ok": False, "ip_externo": ip, "codigo": "", "motivo": problema, "roteador": rot, "cgnat": True}
        rot.abrir(porta)
        return {"ok": True, "ip_externo": ip, "codigo": codigo_de_sala(ip, porta), "motivo": "", "roteador": rot,
                "cgnat": False}
    except (ErroUPnP, OSError, ET.ParseError, ValueError) as erro:
        return {"ok": False, "ip_externo": "", "codigo": "", "motivo": str(erro), "roteador": None, "cgnat": False}


def em_segundo_plano(funcao, ao_terminar):
    """Roda `funcao()` numa thread e chama ao_terminar(resultado) na thread da tela (Qt)."""
    from PyQt6.QtCore import QObject, pyqtSignal

    class _Aviso(QObject):
        pronto = pyqtSignal(object)
    aviso = _Aviso()
    aviso.pronto.connect(ao_terminar)

    def rodar():
        try:
            r = funcao()
        except Exception as erro:   # (nunca derruba o programa)
            r = {"ok": False, "motivo": str(erro)}
        aviso.pronto.emit(r)
    t = threading.Thread(target=rodar, daemon=True)
    t._aviso = aviso   # (guarda o objeto vivo até acabar)
    t.start()
    return t
