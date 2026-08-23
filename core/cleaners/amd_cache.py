# core/cleaners/amd_cache.py
"""
CleanCrow - Cleaner para AMD Shader Cache
"""

import os  # <-- ADICIONAR ESTE IMPORT
from pathlib import Path
from typing import List

from core.cleaners.base import BaseCleaner
from core.models import CleanerInfo, RiskLevel, Category


class AmdCacheCleaner(BaseCleaner):
    """Limpa cache de shaders da AMD"""
    
    @property
    def info(self) -> CleanerInfo:
        return CleanerInfo(
            name="AMD Shader Cache",
            description="Remove caches de shaders da AMD",
            category=Category.GRAFICOS,
            risk_level=RiskLevel.AVANCADO,
            requires_admin=False,
            icon="🎮"
        )
    
    def _get_targets(self) -> List[Path]:
        targets = []
        local_appdata = Path(os.environ.get('LOCALAPPDATA', ''))
        
        if local_appdata.exists():
            amd = local_appdata / 'AMD'
            if amd.exists():
                dxcache = amd / 'DxCache'
                if dxcache.exists():
                    targets.append(dxcache)
        
        return targets
    
    def _can_clean(self, path: Path) -> bool:
        return path.is_dir()
    
    def detect(self) -> bool:
        # Verifica se existe placa AMD
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r'SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}')
            for i in range(0, winreg.QueryInfoKey(key)[0]):
                subkey = winreg.OpenKey(key, str(i))
                try:
                    provider = winreg.QueryValueEx(subkey, 'ProviderName')[0]
                    if 'AMD' in provider.upper():
                        return True
                except:
                    pass
        except:
            pass
        return super().detect()