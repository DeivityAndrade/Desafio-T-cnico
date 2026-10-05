@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto usar_python
py -3 main.py
goto finalizar
:usar_python
python main.py
:finalizar
if errorlevel 1 echo Verifique se o Python 3.10 ou superior esta instalado.
pause
