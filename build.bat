@echo off
cd /d A:\WorkStation\cleancrow
echo ========================================
echo Construindo CleanCrow
echo ========================================
echo.

REM Verificar se o UPX existe
if not exist "upx-5.1.0-win64\upx.exe" (
    echo [AVISO] UPX não encontrado em upx-5.1.0-win64
    echo Continuando sem UPX...
    set UPX_PARAM=
) else (
    echo [OK] UPX encontrado
    set UPX_PARAM=--upx-dir=upx-5.1.0-win64
)

REM Verificar se o ícone existe
if not exist "crowico.ico" (
    echo [ERRO] Arquivo crowico.ico não encontrado!
    echo Certifique-se de que o arquivo está em: A:\WorkStation\cleancrow\crowico.ico
    pause
    exit /b 1
) else (
    echo [OK] Ícone encontrado: crowico.ico
)

echo.
echo Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo.
echo Executando PyInstaller...
echo.

pyinstaller --onefile --noconsole %UPX_PARAM% ^
    --add-data "crowico.ico;." ^
    --icon=crowico.ico ^
    --name CleanCrow ^
    main.py

echo.
if %errorlevel% equ 0 (
    echo ========================================
    echo [SUCESSO] Build concluído!
    echo Executável criado em: A:\WorkStation\cleancrow\dist\CleanCrow.exe
    echo ========================================
) else (
    echo ========================================
    echo [ERRO] Falha no build. Código: %errorlevel%
    echo ========================================
)

echo.
pause