import os
import subprocess
from pathlib import Path
from typing import List

from core.cleaners.base import BaseCleaner
from core.models import CleanerInfo, RiskLevel, Category, CleanerResult


class BrowsersCleaner(BaseCleaner):
    """Limpa cache de navegadores (Chrome, Edge, Firefox, Brave, Opera)"""
    
    BROWSER_CONFIG = {
        'Chrome': 'Google/Chrome/User Data',
        'Edge': 'Microsoft/Edge/User Data',
        'Brave': 'BraveSoftware/Brave-Browser/User Data',
        'Opera': 'Opera Software/Opera Stable',
    }
    
    CACHE_DIRS = ['Cache', 'Code Cache', 'GPUCache', 'Service Worker']
    
    @property
    def info(self) -> CleanerInfo:
        return CleanerInfo(
            name="Navegadores",
            description="Remove cache de navegadores (Chrome, Edge, Firefox, etc)",
            category=Category.NAVEGADORES,
            risk_level=RiskLevel.SEGURO,
            requires_admin=False,
            icon="🌐"
        )
    
    def _get_targets(self) -> List[Path]:
        targets = []
        local_appdata = Path(os.environ.get('LOCALAPPDATA', ''))
        
        if not local_appdata.exists():
            return targets
        
        for browser, path_rel in self.BROWSER_CONFIG.items():
            browser_path = local_appdata / path_rel
            if browser_path.exists():
                # Perfis: Default, Profile*, etc
                for profile in browser_path.iterdir():
                    if profile.is_dir() and (profile.name == 'Default' or profile.name.startswith('Profile')):
                        for cache_dir in self.CACHE_DIRS:
                            cache_path = profile / cache_dir
                            if cache_path.exists():
                                targets.append(cache_path)
        
        # Firefox (usa perfis com cache2)
        firefox = local_appdata / 'Mozilla/Firefox/Profiles'
        if firefox.exists():
            for profile in firefox.iterdir():
                if profile.is_dir():
                    for cache_dir in ['cache2', 'cache']:
                        cache_path = profile / cache_dir
                        if cache_path.exists():
                            targets.append(cache_path)
        
        return targets
    
    def _can_clean(self, path: Path) -> bool:
        return path.is_dir()
    
    def detect(self) -> bool:
        """
        Detecção realista: só retorna True se os navegadores NÃO estiverem rodando.
        Se o navegador estiver aberto, o cache não pode ser limpo, então não reportamos.
        """
        browser_processes = ['chrome.exe', 'msedge.exe', 'firefox.exe', 'brave.exe', 'opera.exe']
        try:
            result = subprocess.run(
                ['tasklist', '/fi', 'imagename eq chrome.exe'],
                capture_output=True,
                text=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for proc in browser_processes:
                if proc.lower() in result.stdout.lower():
                    self._log(f"Navegador {proc} esta rodando. Cache nao pode ser limpo.", "warning")
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
            # Fecha navegadores antes de limpar (se estiverem rodando)
            browser_processes = ['chrome.exe', 'msedge.exe', 'firefox.exe', 'brave.exe', 'opera.exe']
            for proc in browser_processes:
                try:
                    subprocess.run(
                        ['taskkill', '/f', '/im', proc],
                        capture_output=True,
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                except:
                    pass
            
            # Chama a limpeza base
            result = super().clean()
            
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            self._log(f"Erro: {e}", "error")
        
        return result