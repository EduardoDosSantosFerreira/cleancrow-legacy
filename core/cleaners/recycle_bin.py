# core/cleaners/recycle_bin.py
"""
CleanCrow - Cleaner para Lixeira
"""

import ctypes
from pathlib import Path
from typing import List

from core.cleaners.base import BaseCleaner
from core.models import CleanerInfo, RiskLevel, Category


class RecycleBinCleaner(BaseCleaner):
    """Limpa a Lixeira (Recycle Bin)"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._api_result = False
    
    @property
    def info(self) -> CleanerInfo:
        return CleanerInfo(
            name="Lixeira",
            description="Esvazia a Lixeira do Windows",
            category=Category.LIXEIRA,
            risk_level=RiskLevel.SEGURO,
            requires_admin=False,
            icon="♻️"
        )
    
    def _get_targets(self) -> List[Path]:
        # Retorna caminhos da lixeira por unidade
        targets = []
        for drive in ['C:', 'D:', 'E:', 'F:', 'G:']:
            recycle = Path(f'{drive}/$Recycle.Bin')
            if recycle.exists():
                targets.append(recycle)
        return targets
    
    def _can_clean(self, path: Path) -> bool:
        return path.is_dir()
    
    def clean(self):
        """Sobrescreve para usar API do Windows também"""
        result = super().clean()
        
        # Tenta usar API do Windows
        if not self.dry_run:
            try:
                SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
                if SHEmptyRecycleBin(0, None, 0x0001) == 0:
                    self._api_result = True
            except:
                pass
        
        return result
    
    def calculate_size(self) -> int:
        """Calcula tamanho da lixeira via API quando possível"""
        try:
            # Tenta usar API para tamanho
            from core.win32_api import obter_tamanho_lixeira
            return obter_tamanho_lixeira()
        except:
            return super().calculate_size()