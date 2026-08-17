# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

# Define o diretório base do projeto explicitamente
project_dir = r"H:\projetos\cleancrow-legacy"

datas = [
    (os.path.join(project_dir, 'interface.py'), '.'),
    (os.path.join(project_dir, 'core'), 'core'),
    (os.path.join(project_dir, 'crowico.ico'), '.'),
    (os.path.join(project_dir, 'crowico.png'), '.'),
]
binaries = []
hiddenimports = ['interface', 'core', 'core.limpeza', 'core.base', 'core.winget_updater']

tmp_ret = collect_all('qtawesome')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
    [os.path.join(project_dir, 'main.py')],
    pathex=[project_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Correção compatível com PyInstaller v6+ (removido o .zipped obsoleto)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CLEANCROW',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_window_traceback=False,
    argv_emulation=False,
    target_arch=None,
    icon=[os.path.join(project_dir, 'crowico.ico')],
)