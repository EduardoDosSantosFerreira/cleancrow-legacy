import os
import subprocess
import time
from pathlib import Path
from typing import List

from core.cleaners.base import BaseCleaner
from core.models import CleanerInfo, RiskLevel, Category, CleanerResult, formatar_tamanho  # Import adicionado


class WebCacheCleaner(BaseCleaner):
    
    @property
    def info(self) -> CleanerInfo:
        return CleanerInfo(
            name="WebCache",
            description="Remove cache de aplicacoes web do Windows",
            category=Category.CACHES,
            risk_level=RiskLevel.ESPECIAL,
            requires_admin=False,
            icon=""
        )
    
    def _get_targets(self) -> List[Path]:
        targets = []
        local_appdata = Path(os.environ.get('LOCALAPPDATA', ''))
        if local_appdata.exists():
            webcache = local_appdata / 'Microsoft/Windows/WebCache'
            if webcache.exists():
                targets.append(webcache)
        return targets
    
    def _can_clean(self, path: Path) -> bool:
        return path.is_dir()
    
    def clean(self) -> CleanerResult:
        result = CleanerResult(
            cleaner_name=self.info.name,
            success=True
        )
        
        if self.dry_run:
            result.bytes_freed = self.calculate_size()
            return result
        
        try:
            self._log("Fechando processos que usam WebCache...", "info")
            processos_fechados = 0
            for proc in ['SearchApp.exe', 'SearchIndexer.exe', 'Microsoft.Photos.exe']:
                try:
                    result_proc = subprocess.run(
                        ['taskkill', '/f', '/im', proc],
                        capture_output=True,
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    if result_proc.returncode == 0:
                        processos_fechados += 1
                        self._log(f"  {proc}: fechado", "detail")
                except:
                    pass
            
            if processos_fechados > 0:
                self._log(f"  {processos_fechados} processo(s) fechado(s)", "info")
                time.sleep(1)
            
            for path in self._get_targets():
                if path.exists():
                    self._log(f"Removendo {path.name}...", "info")
                    size_before = self._calculate_dir_size(path)
                    self._log(f"  Tamanho detectado: {formatar_tamanho(size_before)}", "detail")
                    
                    files, folders, bytes_freed = self._remove_folder(path)
                    result.files_removed += files
                    result.folders_removed += folders
                    result.bytes_freed += bytes_freed
                    
                    if not path.exists():
                        path.mkdir(parents=True, exist_ok=True)
                    
                    if bytes_freed > 0:
                        self._log(f"  Removido: {formatar_tamanho(bytes_freed)}", "success")
                    else:
                        self._log("  Nenhum arquivo para remover", "info")
        
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            self._log(f"Erro: {e}", "error")
        
        return result