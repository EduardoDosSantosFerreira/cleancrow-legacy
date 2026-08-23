# core/__init__.py
"""
CleanCrow - Core Module
Exporta os componentes principais da engine de limpeza
"""

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

core_dir = os.path.join(BASE_DIR, 'core')
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

# ============================================================================
# IMPORTS DA ENGINE MODULAR
# ============================================================================

# Models
try:
    from core.models import CleanerInfo, CleanerResult, ScanResult, RiskLevel, Category, formatar_tamanho
except ImportError:
    try:
        from models import CleanerInfo, CleanerResult, ScanResult, RiskLevel, Category, formatar_tamanho
    except ImportError:
        CleanerInfo = None
        CleanerResult = None
        ScanResult = None
        RiskLevel = None
        Category = None
        formatar_tamanho = lambda x: f"{x} B"

# Engine
try:
    from core.engine import CleanerEngine, create_engine
except ImportError:
    try:
        from engine import CleanerEngine, create_engine
    except ImportError:
        CleanerEngine = None
        create_engine = None

# Logger
try:
    from core.logger import CleanerLogger, LogEntry
except ImportError:
    try:
        from logger import CleanerLogger, LogEntry
    except ImportError:
        CleanerLogger = None
        LogEntry = None

# Win32 API
try:
    from core.win32_api import is_admin, elevar_processo, esvaziar_lixeira_api, obter_tamanho_lixeira
except ImportError:
    try:
        from win32_api import is_admin, elevar_processo, esvaziar_lixeira_api, obter_tamanho_lixeira
    except ImportError:
        is_admin = lambda: False
        elevar_processo = lambda: False
        esvaziar_lixeira_api = lambda: False
        obter_tamanho_lixeira = lambda: 0

# Winget Updater
try:
    from core.winget_updater import WingetUpdater, verificar_winget, executar_atualizacao
except ImportError:
    try:
        from winget_updater import WingetUpdater, verificar_winget, executar_atualizacao
    except ImportError:
        WingetUpdater = None
        verificar_winget = None
        executar_atualizacao = None

# ============================================================================
# CLEANERS
# ============================================================================

try:
    from core.cleaners import (
        BaseCleaner,
        TempCleaner,
        WindowsTempCleaner,
        RecycleBinCleaner,
        ThumbnailCleaner,
        WERCleaner,
        WindowsUpdateCleaner,
        NvidiaCacheCleaner,
        AmdCacheCleaner,
        BrowsersCleaner,
        WebCacheCleaner,
        SystemCleaner,
    )
    CLEANERS_LOADED = True
except ImportError:
    try:
        from core.cleaners.base import BaseCleaner
        from core.cleaners.temp_cleaner import TempCleaner
        from core.cleaners.windows_temp import WindowsTempCleaner
        from core.cleaners.recycle_bin import RecycleBinCleaner
        from core.cleaners.thumbnail_cleaner import ThumbnailCleaner
        from core.cleaners.wer_cleaner import WERCleaner
        from core.cleaners.windows_update import WindowsUpdateCleaner
        from core.cleaners.nvidia_cache import NvidiaCacheCleaner
        from core.cleaners.amd_cache import AmdCacheCleaner
        from core.cleaners.browsers import BrowsersCleaner
        from core.cleaners.web_cache import WebCacheCleaner
        from core.cleaners.system_cleaner import SystemCleaner
        CLEANERS_LOADED = True
    except ImportError as e:
        CLEANERS_LOADED = False
        print(f"⚠️ Erro ao carregar cleaners: {e}")
        BaseCleaner = TempCleaner = WindowsTempCleaner = RecycleBinCleaner = None
        ThumbnailCleaner = WERCleaner = WindowsUpdateCleaner = NvidiaCacheCleaner = None
        AmdCacheCleaner = BrowsersCleaner = WebCacheCleaner = SystemCleaner = None

# ============================================================================
# EXPORTAÇÕES
# ============================================================================

__all__ = [
    'CleanerInfo', 'CleanerResult', 'ScanResult', 'RiskLevel', 'Category', 'formatar_tamanho',
    'CleanerEngine', 'create_engine',
    'CleanerLogger', 'LogEntry',
    'is_admin', 'elevar_processo', 'esvaziar_lixeira_api', 'obter_tamanho_lixeira',
    'WingetUpdater', 'verificar_winget', 'executar_atualizacao',
    'BaseCleaner', 'TempCleaner', 'WindowsTempCleaner', 'RecycleBinCleaner',
    'ThumbnailCleaner', 'WERCleaner', 'WindowsUpdateCleaner', 'NvidiaCacheCleaner',
    'AmdCacheCleaner', 'BrowsersCleaner', 'WebCacheCleaner', 'SystemCleaner',
    'CLEANERS_LOADED',
]