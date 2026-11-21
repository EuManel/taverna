@echo off
title Taverna - Instalar a musica do YouTube
cd /d "%~dp0"
echo Instalando o componente da musica do YouTube (PyQt6-WebEngine)...
echo Pode demorar um pouco (uns 100 MB). So precisa fazer uma vez.
python -m pip install --upgrade PyQt6 PyQt6-WebEngine
echo.
echo Pronto! Abra o Taverna de novo.
pause
