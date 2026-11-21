"""(v0.65) 🌐 Entrar sem Radmin: UPnP feito à mão (SSDP + SOAP) contra um ROTEADOR FALSO aqui mesmo (127.0.0.1),
código da sala (IP de fora + porta), aviso de CGNAT, e a porta fechada ao fechar a taverna. ⚠ O teste de verdade
só com um amigo fora da rede."""
import os
import re
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

app = QApplication(sys.argv)
from taverna.rede import upnp

print("== código da sala")
for ip, porta in (("177.10.20.30", 7777), ("8.8.4.4", 65535), ("200.1.2.3", 1024)):
    cod = upnp.codigo_de_sala(ip, porta)
    assert re.fullmatch(r"TAV-[0-9A-Z]{5}-[0-9A-Z]{5}", cod), cod
    assert upnp.ler_codigo(cod) == (ip, porta)
    assert upnp.ler_codigo(cod.lower().replace("-", " ")) == (ip, porta)   # digitado de qualquer jeito
print("  ", upnp.codigo_de_sala("177.10.20.30", 7777))
assert upnp.ler_endereco(upnp.codigo_de_sala("177.10.20.30", 7777), 1) == ("177.10.20.30", 7777)
assert upnp.ler_endereco("26.12.34.56", 7777) == ("26.12.34.56", 7777)
assert upnp.ler_endereco(" 26.12.34.56:8000 ", 7777) == ("26.12.34.56", 8000)
assert upnp.ler_codigo("TAV-ABC") is None
assert upnp.ip_problematico("100.70.1.2") == "CGNAT"
assert upnp.ip_problematico("192.168.0.5") and upnp.ip_problematico("10.0.0.1")
assert upnp.ip_problematico("177.10.20.30") is None

# ---------------------------------------------------------------- o roteador falso
estado = {"ip": "177.10.20.30", "mapas": {}, "acoes": []}
DESC = """<?xml version="1.0"?><root xmlns="urn:schemas-upnp-org:device-1-0"><device>
<deviceType>urn:schemas-upnp-org:device:InternetGatewayDevice:1</deviceType><deviceList><device><deviceList><device>
<serviceList><service><serviceType>urn:schemas-upnp-org:service:WANIPConnection:1</serviceType>
<controlURL>/ctl/IPConn</controlURL></service></serviceList></device></deviceList></device></deviceList>
</device></root>"""


class Http(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(DESC.encode())

    def do_POST(self):
        corpo = self.rfile.read(int(self.headers["Content-Length"])).decode()
        acao = self.headers["SOAPAction"].strip('"').split("#")[1]
        estado["acoes"].append(acao)
        campo = lambda n: (re.search(f"<{n}>(.*?)</{n}>", corpo) or [None, None])[1]
        resp = ""
        if acao == "GetExternalIPAddress":
            resp = f"<NewExternalIPAddress>{estado['ip']}</NewExternalIPAddress>"
        elif acao == "AddPortMapping":
            estado["mapas"][campo("NewExternalPort")] = (campo("NewInternalClient"), campo("NewPortMappingDescription"))
        elif acao == "DeletePortMapping":
            estado["mapas"].pop(campo("NewExternalPort"), None)
        xml = (f'<?xml version="1.0"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body>'
               f'<u:{acao}Response xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">{resp}'
               f'</u:{acao}Response></s:Body></s:Envelope>')
        self.send_response(200)
        self.end_headers()
        self.wfile.write(xml.encode())


http = HTTPServer(("127.0.0.1", 0), Http)
threading.Thread(target=http.serve_forever, daemon=True).start()
ssdp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ssdp.bind(("127.0.0.1", 0))


def responder():
    while True:
        try:
            dados, quem = ssdp.recvfrom(2048)
        except OSError:
            return
        if b"M-SEARCH" in dados:
            ssdp.sendto(("HTTP/1.1 200 OK\r\nST: upnp:rootdevice\r\n"
                         f"LOCATION: http://127.0.0.1:{http.server_port}/desc.xml\r\n\r\n").encode(), quem)


threading.Thread(target=responder, daemon=True).start()
DEST = ("127.0.0.1", ssdp.getsockname()[1])

print("== abre a porta no roteador")
r = upnp.abrir_porta(7777, timeout=1.0, destino=DEST)
print("  ", {k: v for k, v in r.items() if k != "roteador"})
assert r["ok"] and r["ip_externo"] == "177.10.20.30" and upnp.ler_codigo(r["codigo"]) == ("177.10.20.30", 7777)
assert estado["mapas"]["7777"] == ("127.0.0.1", upnp.DESCRICAO)
r["roteador"].fechar(7777)
assert "7777" not in estado["mapas"]

print("== CGNAT: não abre e avisa")
estado["ip"] = "100.70.1.2"
r = upnp.abrir_porta(7777, timeout=1.0, destino=DEST)
assert not r["ok"] and r["cgnat"] and "7777" not in estado["mapas"]
estado["ip"] = "177.10.20.30"

print("== sem roteador: avisa (sem travar)")
mudo = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mudo.bind(("127.0.0.1", 0))
r = upnp.abrir_porta(7777, timeout=0.5, destino=("127.0.0.1", mudo.getsockname()[1]))
assert not r["ok"] and "roteador" in r["motivo"]

print("== no mestre: abre ao abrir a taverna, mostra o código, fecha ao fechar")
from taverna.ui.janela_mestre import JanelaMestre
M = JanelaMestre(); M.resize(1000, 700); M.show(); M.mostrar_mesa(); QTest.qWait(50)
s = socket.socket()
s.bind(("127.0.0.1", 0))
porta = s.getsockname()[1]
s.close()
assert M.servidor.abrir(porta)
M.abrir_pela_internet(porta, destino=DEST)
for _ in range(100):
    QTest.qWait(50)
    if M._upnp:
        break
print("   barra:", M.btn_internet.text())
assert M._upnp["ok"] and M.btn_internet.text().startswith("Aberta pela internet")
assert upnp.ler_codigo(M._upnp["codigo"]) == ("177.10.20.30", porta)
assert str(porta) in estado["mapas"]
M._fechar_internet()
M.servidor.fechar()
for _ in range(60):
    QTest.qWait(50)
    if str(porta) not in estado["mapas"]:
        break
assert str(porta) not in estado["mapas"] and not M.btn_internet.isVisible()
print("FIM")
sys.stdout.flush()
os._exit(0)
