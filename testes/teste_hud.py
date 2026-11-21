"""(v0.69) HUD de METAL: barras, botões, títulos e molduras dos painéis, abas, menus, sliders e caixinhas com as
peças de metal da tela inicial. Baixo = liso como antes; Claro/Escuro (neutros) = lisos; Médio/Alto = metal.
Trocar o nível de Gráficos refaz o visual na hora."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["TAVERNA_SEM_AUDIO"] = "1"
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

QSettings.setDefaultFormat(QSettings.Format.IniFormat)          # preferências num lugar de teste
QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, tempfile.mkdtemp())
app = QApplication(sys.argv[:1])
app.setStyle("Fusion")
from taverna import seguranca
erros = []
seguranca.registrar_erro = lambda t: erros.append(t)
from taverna.graficos import graficos
from taverna.temas import TEMAS
from taverna.ui import hud, tema
from taverna.ui.tema import gerar_qss

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")

print("== cada tema e nível")
for chave in TEMAS:
    for niv in ("baixo", "medio", "alto"):
        graficos().definir(niv)
        q = gerar_qss(chave)
        tem = "HUD de metal" in q
        esperado = niv != "baixo" and chave not in hud.NEUTROS
        assert tem == esperado, (chave, niv, tem)
        if tem:   # todas as imagens citadas existem
            import re
            urls = re.findall(r"url\(([^)]+)\)", q)
            assert len(urls) > 20 and all(os.path.exists(u) for u in urls), (chave, niv)
print("   ok:", len(TEMAS), "temas")
assert not erros, erros[:2]

print("== peças com a forma certa")
t = TEMAS["medieval"]
img = hud.peca_caixa("medieval", t, 2, "sobre")
assert img.width() == 48 * hud.K and img.pixelColor(img.width() // 2, 1).alpha() > 0           # aro em cima
assert hud.peca_caixa("medieval", t, 2, "normal", "ferramenta").pixelColor(40, 30).alpha() == 0   # barra parada: vazio
assert hud.peca_redonda("futurista", TEMAS["futurista"], 2, "caixa", True).width() == 18 * hud.K

print("== janela de verdade + troca de Gráficos na hora")
graficos().definir("alto")
app.setStyleSheet(gerar_qss("terror"))
from taverna.ui.janela_mestre import JanelaMestre
M = JanelaMestre(); M.resize(1400, 850); M.show(); M.mostrar_mesa(); QTest.qWait(150)
app.setStyleSheet(gerar_qss("terror"))
QTest.qWait(100)
assert "HUD de metal" in app.styleSheet()
assert hud.pixmap("titulo") is not None
M.grab().save(os.path.join(SAIDA, "hud_terror_alto.png"))
graficos().definir("baixo")
QTest.qWait(50)
assert "HUD de metal" not in app.styleSheet()          # o Baixo volta pro liso sem reabrir nada
assert hud.pixmap("titulo") is None
graficos().definir("medio")
QTest.qWait(50)
assert "HUD de metal" in app.styleSheet()
M.grab().save(os.path.join(SAIDA, "hud_terror_medio.png"))
print("   erros:", erros[:2])
assert not erros, erros
print("FIM")
sys.stdout.flush()
os._exit(0)
