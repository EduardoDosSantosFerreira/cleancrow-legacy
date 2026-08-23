# core/cleaners/__init__.py

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

__all__ = [
    'BaseCleaner',
    'TempCleaner',
    'WindowsTempCleaner',
    'RecycleBinCleaner',
    'ThumbnailCleaner',
    'WERCleaner',
    'WindowsUpdateCleaner',
    'NvidiaCacheCleaner',
    'AmdCacheCleaner',
    'BrowsersCleaner',
    'WebCacheCleaner',
    'SystemCleaner',
]