@echo off
echo ========================================
echo   CLEANCROW - GERANDO EXECUTAVEL
echo ========================================
echo.

echo Verificando se o PyInstaller esta instalado...
pip show pyinstaller > nul 2>&1
if errorlevel 1 (
    echo Instalando PyInstaller...
    pip install pyinstaller
)

echo.
echo Limpando builds anteriores...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q *.spec 2>nul

echo.
echo Gerando executavel...
echo Isso pode levar alguns minutos...

pyinstaller --onefile --windowed --name "CleanCrow" --icon "assets/img/profile_icons/crowico.ico" --add-data "assets;assets" --hidden-import PyQt5 --hidden-import PyQt5.QtCore --hidden-import PyQt5.QtGui --hidden-import PyQt5.QtWidgets --hidden-import core.limpeza --hidden-import core.base --hidden-import core.modo_normal --hidden-import core.modo_rapido --hidden-import core.modo_seguro --exclude-module matplotlib --exclude-module numpy --exclude-module pandas main.py

if errorlevel 1 (
    echo.
    echo ERRO ao gerar executavel!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   EXECUTAVEL GERADO COM SUCESSO!
echo ========================================
echo.
echo Local: dist\CleanCrow.exe
echo.
echo Testando executavel...
if exist "dist\CleanCrow.exe" (
    echo OK - Executavel criado com sucesso!
    echo Tamanho: 
    dir dist\CleanCrow.exe | find "CleanCrow.exe"
) else (
    echo ERRO - Executavel nao encontrado!
)

echo.
pause