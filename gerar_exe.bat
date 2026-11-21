@echo off
title Taverna - Gerar release
cd /d "%~dp0"
echo Instalando o PyInstaller (so na primeira vez)...
python -m pip install -r requirements.txt pyinstaller PyQt6-WebEngine
echo.
echo Gerando a pasta do Taverna (Taverna.exe) e o .zip de release...
python gerar_release.py
echo.
echo Pronto! O .zip esta na pasta "release".
explorer release
pause
