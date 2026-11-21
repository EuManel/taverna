import sys, os, random, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"; os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
app = QApplication(sys.argv); app.setStyle("Fusion")
from taverna.ui.tema import QSS, carregar_fontes
app.setStyleSheet(QSS); carregar_fontes()
w = QTest.qWait

print("== O RESULTADO DA FACE DE CIMA É SEMPRE O SORTEADO")
from taverna.jogo.dados import rolar
from taverna.dados3d.cena3d import Rolagem
from taverna.dados3d.fisica import face_de_cima
from taverna.dados3d.geometria import solido
rng = random.Random(3)
conferidos = 0
for k in range(60):
    expr = rng.choice(["1d20", "2d6", "1d4", "1d8+1d10", "1d12", "4d6kh3", "2d20kl1", "1d%", "3d4+1d20"])
    r = rolar(expr, rng)
    rol = Rolagem(r, 1200, 700, "medieval", "MedievalSharp")
    for d, (pos, q) in zip(rol.dados, rol.quadros[-1]):
        idx = face_de_cima(d["lados"], q)
        mostrado = d["nums"][idx]
        esperado = d["valor"] % 10 if d["lados"] == 10 else d["valor"]
        assert mostrado == esperado, (expr, d, mostrado)
        v = solido(d["lados"])[0]
        conferidos += 1
print("dados conferidos:", conferidos, "· todos mostram o valor sorteado")

print("== MESMA SEMENTE = MESMO QUIQUE")
r = rolar("1d20+1d6", random.Random(9))
a = Rolagem(r, 1200, 700, "magico", "Cinzel Decorative")
c = Rolagem(dict(r), 800, 900, "terror", "Pirata One")   # outra janela, outro tema: o quique é o mesmo
igual = len(a.quadros) == len(c.quadros) and all(
    (pa == pc).all() and (qa == qc).all() for fa, fc in zip(a.quadros, c.quadros) for (pa, qa), (pc, qc) in zip(fa, fc))
print("outra janela e outro tema -> mesmo movimento:", igual, "| duração %.1fs" % a.duracao)
assert igual

print("== NA MESA (mestre + jogador, pela rede)")
from taverna.ui.janela_mestre import JanelaMestre
from taverna.ui.janela_player import JanelaPlayer
from taverna.config import CELULA
M = JanelaMestre(); M.resize(1400, 850); M.show(); M.cena.criar_camadas_padrao(); M.mostrar_mesa(); w(50)
M.cena.adicionar_token(dict(nome="Aelar", tipo="jogador", cor="#3f6b4a", tamanho=1, imagem=None, dono="Manel"),
                       QPointF(0, 0))
assert M.servidor.abrir(7793)
P = JanelaPlayer(); P.resize(1400, 850); P.show()
P.nome, P.ip, P.porta = "Manel", "127.0.0.1", 7793
P._ja_entrou = False; P._primeiro_estado = True
P.cliente.conectar(P.ip, P.porta, P.nome); w(900)
print("OpenGL nesta máquina de teste?", M.dados3d.usando_gl, "(sem tela: usa o desenho simples)")
P.painel_dados.pedir_rolagem.emit("1d20+5", False); w(150)
t0 = time.time()
while (M.dados3d.rolagem is None or P.dados3d.rolagem is None) and time.time() - t0 < 5:
    w(50)
assert M.dados3d.rolagem is not None and P.dados3d.rolagem is not None, "a animação não começou"
rm, rp = M.dados3d.rolagem, P.dados3d.rolagem
print("rolagem:", rp.r["expr"], "=", rp.r["total"], "| d20 natural:", rp.r["d20"], "| semente igual:", rm.r["semente"] == rp.r["semente"])
assert rm.r["semente"] == rp.r["semente"] and rm.r["total"] == rp.r["total"]
mesmo = all((pa == pb).all() for (pa, _), (pb, _) in zip(rm.quadros[-1], rp.quadros[-1]))
print("mestre e jogador: dados param no mesmo lugar:", mesmo)
assert mesmo
w(int(rp.duracao * 450)); P.grab().save("saida/shot_dados3d_rolando.png")
w(int(rp.duracao * 650) + 300); P.grab().save("saida/shot_dados3d_placar.png"); M.grab().save("saida/shot_dados3d_mestre.png")

print("== DUAS ROLAGENS SEGUIDAS: a nova cancela a anterior (v0.45.3)")
P.painel_dados.pedir_rolagem.emit("2d6", False); w(30)
P.painel_dados.pedir_rolagem.emit("1d8", False)
for _ in range(60):   # (até 3 s pra voltar do servidor e a física ficar pronta)
    w(50)
    atual = P.dados3d.rolagem.r.get("expr") if P.dados3d.rolagem is not None else None
    if atual == "1d8":
        break
print("na fila do jogador:", len(P.dados3d.fila), "| rolando agora:", atual)
assert not P.dados3d.fila and atual == "1d8"

print("== PRIVADA DO MESTRE: só na tela dele")
while P.dados3d.rolagem is not None or P.dados3d.fila or P.dados3d._calculando:
    w(100)
M.servidor.rolar_mestre("1d20", privada=True); w(600)
print("mestre anima:", M.dados3d.rolagem is not None or M.dados3d._calculando, "| jogador anima:", P.dados3d.rolagem is not None)
assert P.dados3d.rolagem is None

print("== DESLIGADO em Gráficos: volta pro aviso de sempre")
from taverna.graficos import graficos
graficos().dados3d = False
while P.dados3d.rolagem is not None or P.dados3d.fila or P.dados3d._calculando:
    w(100)
P.painel_dados.pedir_rolagem.emit("1d6", False); w(500)
print("animou?", P.dados3d.rolagem is not None, "| aviso no canto:", P.aviso_rolagem.isVisible())
assert P.dados3d.rolagem is None
graficos().dados3d = True

print("== 20 E 1 NATURAL: ANIMAÇÃO NO d20 (v0.45.2)")
from taverna.dados3d.cena3d import Rolagem
from taverna.dados3d import render_2d
from PyQt6.QtGui import QImage, QPainter, QColor
painel = P.dados3d
for nat in (20, 1):
    r = {"fisicos": [{"lados": 20, "valor": nat}], "semente": 3, "d20": nat, "total": nat, "quem": "Teste"}
    rol = Rolagem(r, 640, 400, "medieval", "Georgia")
    assert rol.critico == (0, nat)
    antes = rol.quadro(rol.duracao)[0][0].copy()
    mexeu = rol.quadro(rol.duracao + 0.2)[0][0]
    assert abs(mexeu - antes).max() > 1e-3, "o d20 crítico pula / o da falha treme"
    painel.rolagem = rol
    for dt in (0.05, 0.3, 0.8, 1.6, 2.4):
        painel.t = rol.duracao + dt
        im = QImage(640, 400, QImage.Format.Format_ARGB32_Premultiplied); im.fill(QColor(40, 34, 30))
        pp = QPainter(im)
        render_2d.desenhar(pp, rol, painel.t, 640, 400)
        painel.desenhar_placar(pp, 640, 400)
        pp.end()
    assert rol.critico is not None   # (None = a animação deu erro e foi desligada)
painel.rolagem = None
# vantagem: o d20 descartado (fora) NÃO anima, só o que valeu
r = {"fisicos": [{"lados": 20, "valor": 1, "fora": True}, {"lados": 20, "valor": 17}], "semente": 4, "d20": 17}
assert Rolagem(r, 640, 400, "medieval", "Georgia").critico is None
r = {"fisicos": [{"lados": 20, "valor": 20}, {"lados": 20, "valor": 6, "fora": True}], "semente": 4, "d20": 20}
assert Rolagem(r, 640, 400, "medieval", "Georgia").critico == (0, 20)
print("crítico e falha: ok (só o d20 que valeu)")
print("FIM")
