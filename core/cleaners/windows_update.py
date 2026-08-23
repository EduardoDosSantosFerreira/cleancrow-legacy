import subprocess
import time
from pathlib import Path
from typing import List

from core.cleaners.base import BaseCleaner
from core.models import CleanerInfo, RiskLevel, Category, CleanerResult, formatar_tamanho


class WindowsUpdateCleaner(BaseCleaner):
    
    @property
    def info(self) -> CleanerInfo:
        return CleanerInfo(
            name="Cache do Windows Update",
            description="Remove arquivos baixados das atualizacoes do Windows",
            category=Category.ATUALIZACOES,
            risk_level=RiskLevel.AVANCADO,
            requires_admin=True,
            icon=""
        )
    
    def _get_targets(self) -> List[Path]:
        return [Path('C:/Windows/SoftwareDistribution/Download')]
    
    def _can_clean(self, path: Path) -> bool:
        return path.is_dir()
    
    def detect(self) -> bool:
        """
        Detecção realista: o cache do Windows Update só pode ser limpo se o serviço estiver parado.
        Se o serviço estiver rodando, não reportamos (pois não vai conseguir limpar).
        """
        try:
            result = subprocess.run(
                ['sc', 'query', 'wuauserv'],
                capture_output=True,
                text=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if 'RUNNING' in result.stdout.upper() or 'STATE' not in result.stdout.upper():
                return False
        except:
            pass
        
        return super().detect()
    
    def clean(self) -> CleanerResult:
        result = CleanerResult(
            cleaner_name=self.info.name,
            success=True
        )
        
        if self.dry_run:
            result.bytes_freed = self.calculate_size()
            return result
        
        try:
            self._log("Parando servicos de atualizacao...", "info")
            
            # Para servicos com forca
            for service in ['wuauserv', 'bits', 'cryptsvc']:
                proc = subprocess.run(
                    ['net', 'stop', service, '/y'],
                    capture_output=True,
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if proc.returncode == 0:
                    self._log(f"  {service}: parado", "detail")
                else:
                    self._log(f"  {service}: erro ao parar (pode ja estar parado)", "detail")
            
            # Espera mais tempo para garantir que os arquivos sejam liberados
            time.sleep(5)
            
            path = Path('C:/Windows/SoftwareDistribution/Download')
            if path.exists():
                self._log("Removendo cache de atualizacoes...", "info")
                size_before = self._calculate_dir_size(path)
                self._log(f"  Tamanho detectado: {formatar_tamanho(size_before)}", "detail")
                
                # Remove arquivos
                cmd = f'del /f /s /q "{path}\\*.*" 2>nul & rmdir /s /q "{path}" 2>nul'
                subprocess.run(
                    ['cmd', '/c', cmd],
                    capture_output=True,
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=180
                )
                
                # Recria a pasta se foi removida
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                    result.bytes_freed = size_before
                else:
                    size_after = self._calculate_dir_size(path)
                    result.bytes_freed = size_before - size_after
                
                if result.bytes_freed > 0:
                    self._log(f"  Removido: {formatar_tamanho(result.bytes_freed)}", "success")
                else:
                    self._log("  Nenhum arquivo para remover", "info")
            else:
                self._log("  Pasta nao encontrada", "info")
            
            self._log("Reiniciando servicos...", "info")
            for service in ['cryptsvc', 'bits', 'wuauserv']:
                proc = subprocess.run(
                    ['net', 'start', service],
                    capture_output=True,
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if proc.returncode == 0:
                    self._log(f"  {service}: iniciado", "detail")
                else:
                    self._log(f"  {service}: erro ao iniciar", "detail")
            
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            self._log(f"Erro: {e}", "error")
        
        return result