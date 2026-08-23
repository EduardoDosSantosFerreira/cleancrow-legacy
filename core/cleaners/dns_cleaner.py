# core/cleaners/dns_cleaner.py
"""
CleanCrow - Cleaner para DNS Cache
"""

import subprocess
from pathlib import Path
from typing import List

from core.cleaners.base import BaseCleaner
from core.models import CleanerInfo, RiskLevel, Category, CleanerResult


class DNSCleaner(BaseCleaner):
    """Limpa cache DNS (ipconfig /flushdns)"""
    
    @property
    def info(self) -> CleanerInfo:
        return CleanerInfo(
            name="Cache DNS",
            description="Limpa o cache de resolução DNS",
            category=Category.REDE,
            risk_level=RiskLevel.SEGURO,
            requires_admin=True,
            icon="🌐"
        )
    
    def _get_targets(self) -> List[Path]:
        # Não tem arquivos, mas precisa retornar algo para detect()
        return []
    
    def _can_clean(self, path: Path) -> bool:
        """DNS Cleaner não tem arquivos para limpar"""
        return False
    
    def detect(self) -> bool:
        # Sempre disponível no Windows
        return True
    
    def calculate_size(self) -> int:
        # DNS cache não ocupa espaço em disco
        return 0
    
    def clean(self) -> CleanerResult:
        """Executa ipconfig /flushdns"""
        result = CleanerResult(
            cleaner_name=self.info.name,
            success=True
        )
        
        if self.dry_run:
            return result
        
        try:
            proc = subprocess.run(
                ['ipconfig', '/flushdns'],
                capture_output=True,
                text=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if proc.returncode != 0:
                result.success = False
                result.errors.append(proc.stderr.strip() or "Comando falhou")
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
        
        return result
    
    def verify(self) -> bool:
        # Não há como verificar facilmente
        return True