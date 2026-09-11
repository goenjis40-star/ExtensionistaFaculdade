@echo off
REM ============================================================
REM  EcoMetric 2.0 - Script de Build para Windows
REM  Gera o executavel em dist/EcoMetric/EcoMetric.exe
REM ============================================================

echo.
echo [1/4] Verificando ambiente virtual...
if not exist "venv\Scripts\activate.bat" (
    echo Criando ambiente virtual...
    python -m venv venv
)

echo.
echo [2/4] Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo.
echo [3/4] Instalando dependencias...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [4/4] Gerando executavel com PyInstaller...
pyinstaller EcoMetric.spec --clean --noconfirm

echo.
echo ============================================================
echo  Build concluido!
echo  Executavel gerado em: dist\EcoMetric\EcoMetric.exe
echo ============================================================
pause