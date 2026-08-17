# core/__init__.py - CORRIGIDO PARA PYINSTALLER

import os
import sys

# Configuração de caminho para PyInstaller
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Adiciona os caminhos necessários
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Adiciona o diretório core
core_dir = os.path.join(BASE_DIR, 'core')
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

# Tenta importar de diferentes formas
SistemaLimpeza = None
ModoRapido = None

try:
    # Tenta importar diretamente (modo PyInstaller)
    from core.limpeza import SistemaLimpeza, ModoRapido
except ImportError:
    try:
        # Tenta importar relativo (modo desenvolvimento)
        from limpeza import SistemaLimpeza, ModoRapido
    except ImportError:
        try:
            # Tenta importar usando o caminho absoluto
            import importlib.util
            limpeza_path = os.path.join(core_dir, 'limpeza.py')
            if os.path.exists(limpeza_path):
                spec = importlib.util.spec_from_file_location("limpeza", limpeza_path)
                if spec and spec.loader:
                    limpeza_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(limpeza_module)
                    SistemaLimpeza = limpeza_module.SistemaLimpeza
                    ModoRapido = limpeza_module.ModoRapido
        except:
            pass

# Tenta importar base
try:
    from core.base import *
except ImportError:
    try:
        from base import *
    except ImportError:
        pass

# Tenta importar winget_updater
verificar_winget = None
executar_atualizacao = None

try:
    from core.winget_updater import verificar_winget, executar_atualizacao
except ImportError:
    try:
        from winget_updater import verificar_winget, executar_atualizacao
    except ImportError:
        pass

__all__ = [
    'SistemaLimpeza', 
    'ModoRapido',
    'verificar_winget',
    'executar_atualizacao'
]