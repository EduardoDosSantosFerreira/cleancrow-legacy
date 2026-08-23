import os
import time
from pathlib import Path
from typing import List

from core.cleaners.base import BaseCleaner
from core.models import CleanerInfo, RiskLevel, Category, CleanerResult, formatar_tamanho  # Import adicionado


class WindowsTempCleaner(BaseCleaner):
    
    @property
    def info(self) -> CleanerInfo:
        return CleanerInfo(
            name="Temporarios do Windows",
            description="Remove arquivos temporarios do sistema Windows",
            category=Category.SISTEMA,
            risk_level=RiskLevel.SEGURO,
            requires_admin=True,
            icon=""
        )
    
    def _get_targets(self) -> List[Path]:
        return [Path('C:/Windows/Temp')]
    
    def _can_clean(self, path: Path) -> bool:
        return path.is_dir()
    
    def clean(self) -> CleanerResult:
        start_time = time.time()
        result = CleanerResult(
            cleaner_name=self.info.name,
            success=True
        )
        
        for path in self._get_targets():
            if not path.exists():
                continue
            
            if path.is_dir():
                self._log(f"Removendo arquivos de {path.name}...", "info")
                size_before = self._calculate_dir_size(path)
                self._log(f"  Tamanho detectado: {formatar_tamanho(size_before)}", "detail")
                
                files, folders, bytes_freed = self._remove_folder(path)
                result.files_removed += files
                result.folders_removed += folders
                result.bytes_freed += bytes_freed
                
                if not path.exists():
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                    except:
                        pass
                
                if bytes_freed > 0:
                    self._log(f"  Removido: {formatar_tamanho(bytes_freed)}", "success")
                else:
                    self._log("  Nenhum arquivo para remover", "info")
        
        result.duration_ms = (time.time() - start_time) * 1000
        self._last_result = result
        return result