@echo off
title CleanCrow - Build Executavel
echo ========================================
echo    CLEANCROW - BUILD EXECUTAVEL
echo ========================================
echo.

echo [1/4] Verificando ambiente...
if not exist "interface.py" (
    echo ERRO: Arquivo interface.py nao encontrado!
    pause
    exit /b 1
)
if not exist "crowico.png" (
    echo AVISO: Arquivo crowico.png nao encontrado
)
if not exist "core" (
    echo ERRO: Pasta core nao encontrada!
    pause
    exit /b 1
)
echo OK!

echo.
echo [2/4] Limpando builds anteriores...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec" del /q *.spec 2>nul
echo OK!

echo.
echo [3/4] Gerando arquivo .spec...
echo Gerando cleancrow.spec...
(
echo # -*- mode: python ; coding: utf-8 -*-
echo.
echo import os
echo.
echo a = Analysis^(
echo     ['interface.py'],
echo     pathex=[os.getcwd()],
echo     binaries=[],
echo     datas=[
echo         ('crowico.png', '.'),
echo         ('core', 'core'),
echo     ],
echo     hiddenimports=[
echo         'ctypes',
echo         'ctypes.windll',
echo         'ctypes.wintypes',
echo         'string',
echo         'enum',
echo         'dataclasses',
echo         'pathlib',
echo         'stat',
echo         'subprocess',
echo         'threading',
echo         'time',
echo         'os',
echo         'sys',
echo         'queue',
echo         'PyQt5',
echo         'PyQt5.sip',
echo         'PyQt5.QtCore',
echo         'PyQt5.QtGui',
echo         'PyQt5.QtWidgets',
echo         'core.base',
echo         'core.limpeza',
echo         'core.modo_rapido',
echo         'core.modo_normal',
echo         'core.modo_seguro',
echo     ],
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=[
echo         'tkinter',
echo         'numpy',
echo         'pandas',
echo         'matplotlib',
echo         'PIL',
echo         'curses',
echo         'test',
echo         'unittest',
echo     ],
echo     noarchive=False,
echo ^)
echo.
echo pyz = PYZ(a.pure)
echo.
echo exe = EXE^(
echo     pyz,
echo     a.scripts,
echo     a.binaries,
echo     a.datas,
echo     [],
echo     name='cleancrow',
echo     debug=False,
echo     bootloader_ignore_signals=False,
echo     strip=False,
echo     upx=True,
echo     upx_exclude=[],
echo     runtime_tmpdir=None,
echo     console=False,
echo     disable_windowed_traceback=False,
echo     argv_emulation=False,
echo     target_arch=None,
echo     codesign_identity=None,
echo     entitlements_file=None,
echo     icon='crowico.png',
echo     uac_admin=True,
echo ^)
) > cleancrow.spec
echo OK!

echo.
echo [4/4] Compilando executavel...
echo Isso pode levar alguns minutos...
echo.
pyinstaller cleancrow.spec --clean

if errorlevel 1 (
    echo.
    echo ========================================
    echo    ERRO NA COMPILACAO!
    echo ========================================
    echo Verifique as mensagens acima.
) else (
    echo.
    echo ========================================
    echo    BUILD CONCLUIDO COM SUCESSO!
    echo ========================================
    echo.
    echo Executavel gerado em:
    echo   %CD%\dist\cleancrow.exe
    echo.
    echo Para testar, execute:
    echo   dist\cleancrow.exe
    echo.
    echo ========================================
)

echo.
pause