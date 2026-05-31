@echo off
REM ============================================================
REM  Gera o executavel "Controle de Horas.exe" via PyInstaller
REM ============================================================

setlocal

if not exist .venv (
    echo Criando ambiente virtual...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Instalando dependencias...
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo Gerando executavel...
set ICON_FLAG=
if exist app\assets\icon.ico set ICON_FLAG=--icon app\assets\icon.ico

pyinstaller --noconfirm --clean --windowed --onefile ^
    --name "Controle de Horas" %ICON_FLAG% ^
    --add-data "app\assets;app\assets" ^
    --hidden-import PySide6.QtSvg ^
    --collect-submodules PySide6.QtSvg ^
    --hidden-import win32com ^
    --hidden-import win32com.client ^
    --hidden-import pythoncom ^
    --hidden-import pywintypes ^
    main.py

echo.
echo ============================================================
echo  Build concluido. Executavel em: dist\Controle de Horas.exe
echo ============================================================

endlocal
pause
