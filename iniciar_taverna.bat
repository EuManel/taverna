@echo off
title Taverna
cd /d "%~dp0"
python -c "import PyQt6, pypdfium2, pypdf, numpy" 2>nul || (
  echo Instalando o que falta - primeira vez, aguarde...
  python -m pip install -r requirements.txt
)
python taverna.py
if errorlevel 1 pause
