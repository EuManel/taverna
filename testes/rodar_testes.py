"""Roda todos os testes do Taverna e mostra quais passaram.

Uso (na pasta do projeto):   python testes/rodar_testes.py
Um teste só:                 python testes/rodar_testes.py impactos

Os testes abrem as janelas do Mestre e do Player "invisíveis" (sem tela e
sem som), conectam um no outro pela rede local e conferem o resultado.
As capturas de tela ficam em testes/saida/.
"""
import os, subprocess, sys, glob, time

AQUI = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(AQUI, "saida"), exist_ok=True)
filtro = sys.argv[1:] 
arquivos = sorted(glob.glob(os.path.join(AQUI, "teste_*.py")))
if filtro:
    arquivos = [a for a in arquivos if any(f in os.path.basename(a) for f in filtro)]

amb = dict(os.environ, QT_QPA_PLATFORM="offscreen", TAVERNA_SEM_AUDIO="1", PYTHONIOENCODING="utf-8",
           TAVERNA_IDIOMA="pt")   # (v1.0) os testes conferem os textos em português, seja qual for o idioma salvo
falhas = []
for a in arquivos:
    nome = os.path.basename(a)
    t = time.time()
    try:
        r = subprocess.run([sys.executable, a], cwd=AQUI, env=amb, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=300)
        ok, saida = r.returncode == 0, (r.stdout + r.stderr)
    except subprocess.TimeoutExpired:
        ok, saida = False, "demorou mais de 5 minutos"
    print(f"{'OK    ' if ok else 'FALHOU'} {nome}  ({time.time()-t:.0f}s)", flush=True)
    if not ok:
        falhas.append(nome)
        print("    " + "\n    ".join(saida.strip().splitlines()[-12:]))

print(f"\n{len(arquivos)-len(falhas)} de {len(arquivos)} passaram.")
sys.exit(1 if falhas else 0)
