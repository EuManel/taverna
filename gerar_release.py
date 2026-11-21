"""Gera a versão de release pra Windows (v1.0): uma PASTA com o Taverna.exe (sem console, com ícone, não precisa de
Python), + README.txt e HOW_TO_CONNECT.txt (inglês primeiro, depois português) e LICENCAS.md, compactada em release/Taverna-v<versão>-windows.zip.

Uso (na pasta do projeto):   python gerar_release.py
Precisa: pip install -r requirements.txt pyinstaller PyQt6-WebEngine
"""
import os
import shutil
import subprocess
import sys
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from taverna.config import APP_VERSAO  # noqa: E402

CURTA = ".".join(APP_VERSAO.split(".")[:2]) if APP_VERSAO.endswith(".0") else APP_VERSAO   # 1.0.0 -> 1.0
SAIDA = os.path.join(AQUI, "release")
TRABALHO = os.path.join(SAIDA, "_build")
DADOS = ["taverna/compendio/dados", "taverna/fontes", "taverna/ui/qml", "taverna/ui/materiais", "taverna/idiomas"]


def main():
    os.chdir(AQUI)
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--windowed",
           "--name", "Taverna", "--icon", os.path.join(AQUI, "assets", "taverna.ico"),
           "--distpath", os.path.join(TRABALHO, "dist"), "--workpath", os.path.join(TRABALHO, "work"),
           "--specpath", TRABALHO,
           "--collect-all", "pypdfium2", "--collect-all", "pypdfium2_raw",
           "--hidden-import", "pypdf", "--hidden-import", "PyQt6.QtQuick", "--hidden-import", "PyQt6.QtQuickWidgets",
           "--hidden-import", "PyQt6.QtQml", "--hidden-import", "PyQt6.QtQuick3D",
           "--hidden-import", "PyQt6.QtWebEngineWidgets", "--hidden-import", "PyQt6.QtWebEngineCore",
           "--hidden-import", "PyQt6.QtMultimedia", "--hidden-import", "PyQt6.QtOpenGL",
           "--hidden-import", "PyQt6.QtOpenGLWidgets",
           "--exclude-module", "tkinter", "--exclude-module", "reportlab"]
    for d in DADOS:
        cmd += ["--add-data", f"{os.path.join(AQUI, d)}{os.pathsep}{d}"]
    cmd.append(os.path.join(AQUI, "taverna.py"))
    print("PyInstaller…", flush=True)
    subprocess.run(cmd, check=True)

    pasta = os.path.join(TRABALHO, "dist", "Taverna")
    # (os .txt com BOM e quebra de linha do Windows: o Bloco de Notas abre certinho, acento e tudo)
    for n in ("README.txt", "HOW_TO_CONNECT.txt"):
        with open(os.path.join(AQUI, n), encoding="utf-8") as f:
            texto = f.read().replace("{VERSAO}", "v" + CURTA)
        with open(os.path.join(pasta, n), "w", encoding="utf-8-sig", newline="\r\n") as f:
            f.write(texto)
    # licenças: LICENSE = GPL v3 (Taverna e PyQt6), LGPL v3 (Qt) e os créditos
    for n in ("LICENCAS.md", "LICENSE", "LICENSE-LGPL-3.0.txt"):
        shutil.copy2(os.path.join(AQUI, n), os.path.join(pasta, n))

    os.makedirs(SAIDA, exist_ok=True)
    zip_ = os.path.join(SAIDA, f"Taverna-v{CURTA}-windows.zip")
    if os.path.exists(zip_):
        os.remove(zip_)
    print("Compactando…", flush=True)
    with zipfile.ZipFile(zip_, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for raiz, _d, arqs in os.walk(pasta):
            for a in arqs:
                c = os.path.join(raiz, a)
                z.write(c, os.path.join("Taverna", os.path.relpath(c, pasta)))
    print(f"Pronto: {zip_}  ({os.path.getsize(zip_) / 1e6:.0f} MB)")
    print(f"Pasta pra testar: {pasta}")


if __name__ == "__main__":
    main()
