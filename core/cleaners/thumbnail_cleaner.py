# core/cleaners/thumbnail_cleaner.py

import subprocess
from pathlib import Path
from typing import List

from core.cleaners.base import BaseCleaner
from core.models import CleanerInfo, RiskLevel, Category


class ThumbnailCleaner(BaseCleaner):
    
    @property
    def info(self) -> CleanerInfo:
        return CleanerInfo(
            name="Cache de Miniaturas",
            description="Remove o cache de miniaturas do Windows Explorer",
            category=Category.CACHES,
            risk_level=RiskLevel.SEGURO,
            requires_admin=False,
            icon=""
        )
    
    def _get_targets(self) -> List[Path]:
        targets = []
        users_path = Path('C:/Users')
        if users_path.exists():
            for user in users_path.iterdir():
                if user.is_dir():
                    explorer = user / 'AppData/Local/Microsoft/Windows/Explorer'
                    if explorer.exists():
                        targets.append(explorer)
        return targets
    
    def _can_clean(self, path: Path) -> bool:
        return path.is_dir()
    
    def clean(self):
        result = super().clean()
        
        if not self.dry_run and result.files_removed > 0:
            try:
                subprocess.run(['taskkill', '/f', '/im', 'explorer.exe'], 
                             capture_output=True, shell=True)
                subprocess.Popen(['start', 'explorer.exe'], shell=True)
            except:
                pass
        
        return result