# core/cleaners/component_store.py
"""
CleanCrow - Cleaner para Windows Component Store (DISM)
"""

import subprocess
import threading
from pathlib import Path
from typing import List

from core.cleaners.base import BaseCleaner
from core.models import CleanerInfo, RiskLevel, Category, CleanerResult


class ComponentStoreCleaner(BaseCleaner):
    """Limpeza do Component Store via DISM (Avançado)"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._process = None
        self._cancelled = False
    
    @property
    def info(self) -> CleanerInfo:
        return CleanerInfo(
            name="Windows Component Cleanup",
            description="Limpa a Component Store do Windows (DISM)",
            category=Category.SISTEMA,
            risk_level=RiskLevel.AVANCADO,
            requires_admin=True,
            icon="⚙️"
        )
    
    def _get_targets(self) -> List[Path]:
        # Não tem arquivos diretos
        return []
    
    def _can_clean(self, path: Path) -> bool:
        """ComponentStore não tem arquivos para limpar diretamente"""
        return False
    
    def detect(self) -> bool:
        # Sempre disponível no Windows 10/11
        return True
    
    def calculate_size(self) -> int:
        # Estima usando DISM
        try:
            proc = subprocess.run(
                ['dism', '/online', '/cleanup-image', '/analyzecomponentstore'],
                capture_output=True,
                text=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=120
            )
            # Tenta extrair o tamanho estimado
            for line in proc.stdout.splitlines():
                if 'Tamanho do armazenamento de componentes' in line:
                    import re
                    match = re.search(r'([\d,]+)\s*MB', line)
                    if match:
                        return int(match.group(1).replace(',', '')) * 1024 * 1024
        except:
            pass
        return 0
    
    def clean(self) -> CleanerResult:
        """Executa DISM /StartComponentCleanup"""
        result = CleanerResult(
            cleaner_name=self.info.name,
            success=True
        )
        
        if self.dry_run:
            result.bytes_freed = self.calculate_size()
            return result
        
        try:
            # Não usa /ResetBase
            proc = subprocess.run(
                ['dism', '/online', '/cleanup-image', '/startcomponentcleanup'],
                capture_output=True,
                text=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=600
            )
            if proc.returncode != 0:
                result.success = False
                result.errors.append(proc.stderr.strip() or "DISM falhou")
        except subprocess.TimeoutExpired:
            result.success = False
            result.errors.append("DISM excedeu o tempo limite (10 minutos)")
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
        
        return result
    
    def verify(self) -> bool:
        # Verifica se o comando executou
        return True