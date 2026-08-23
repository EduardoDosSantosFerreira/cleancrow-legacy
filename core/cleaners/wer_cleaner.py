# core/cleaners/wer_cleaner.py
"""
CleanCrow - Cleaner para Windows Error Reporting - LIMPEZA REAL
"""

import os
from pathlib import Path
from typing import List

from core.cleaners.base import BaseCleaner
from core.models import CleanerInfo, RiskLevel, Category


class WERCleaner(BaseCleaner):
    """Limpa relatórios do Windows Error Reporting - REMOVE ARQUIVOS DE VERDADE!"""
    
    @property
    def info(self) -> CleanerInfo:
        return CleanerInfo(
            name="Relatórios de Erro (WER)",
            description="Remove relatórios antigos do Windows Error Reporting",
            category=Category.LOGS,
            risk_level=RiskLevel.SEGURO,
            requires_admin=False,
            icon="📋"
        )
    
    def _get_targets(self) -> List[Path]:
        targets = []
        
        # System-wide WER
        targets.append(Path('C:/ProgramData/Microsoft/Windows/WER/ReportArchive'))
        targets.append(Path('C:/ProgramData/Microsoft/Windows/WER/ReportQueue'))
        
        # User WER
        local_appdata = Path(os.environ.get('LOCALAPPDATA', ''))
        if local_appdata.exists():
            targets.append(local_appdata / 'Microsoft/Windows/WER/ReportArchive')
            targets.append(local_appdata / 'Microsoft/Windows/WER/ReportQueue')
        
        return targets
    
    def _can_clean(self, path: Path) -> bool:
        return path.is_dir()