"""
Limpeza agressiva do Windows Update
Libera GBs removendo caches obsoletos
"""

import subprocess
import time
from pathlib import Path
from typing import Tuple
import shutil
import stat
import os


class WindowsUpdateCleaner:
    """Limpeza especializada para Windows Update"""
    
    SERVICES = ["wuauserv", "bits", "dosvc"]
    UPDATE_PATHS = [
        "C:/Windows/SoftwareDistribution/Download",
        "C:/Windows/SoftwareDistribution/DeliveryOptimization",
        "C:/Windows/SoftwareDistribution/DataStore",
    ]
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def _log(self, msg: str):
        if self.verbose:
            print(f"  {msg}")
    
    def _stop_services(self) -> bool:
        """Para serviços do Windows Update"""
        success = True
        for service in self.SERVICES:
            try:
                subprocess.run(
                    f"net stop {service}",
                    shell=True,
                    capture_output=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self._log(f"Serviço {service} parado")
            except:
                pass
        time.sleep(2)
        return success
    
    def _start_services(self) -> bool:
        """Reinicia serviços do Windows Update"""
        for service in self.SERVICES:
            try:
                subprocess.run(
                    f"net start {service}",
                    shell=True,
                    capture_output=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self._log(f"Serviço {service} iniciado")
            except:
                pass
        return True
    
    def _remove_readonly(self, func, path, excinfo):
        """Remove atributo readonly"""
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except:
            pass
    
    def _limpar_pasta(self, path: Path) -> Tuple[int, int]:
        """Limpa uma pasta completamente"""
        files = 0
        bytes_freed = 0
        
        if not path.exists():
            return 0, 0
        
        # Calcular tamanho antes
        try:
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    try:
                        filepath = Path(root) / filename
                        bytes_freed += filepath.stat().st_size
                        files += 1
                    except:
                        pass
        except:
            pass
        
        # Remover
        try:
            shutil.rmtree(path, ignore_errors=False, onerror=self._remove_readonly)
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._log(f"Erro ao limpar {path}: {e}")
            return 0, 0
        
        return files, bytes_freed
    
    def limpar(self) -> Tuple[int, int]:
        """
        Executa limpeza completa do Windows Update
        
        Returns:
            Tuple[int, int]: (arquivos_removidos, bytes_liberados)
        """
        total_files = 0
        total_bytes = 0
        
        # Parar serviços
        self._stop_services()
        
        # Limpar cada pasta
        for path_str in self.UPDATE_PATHS:
            path = Path(path_str)
            if path.exists():
                self._log(f"Limpando: {path}")
                files, bytes_freed = self._limpar_pasta(path)
                total_files += files
                total_bytes += bytes_freed
                if bytes_freed > 0:
                    self._log(f"  Liberado: {bytes_freed // (1024*1024)} MB")
        
        # Reiniciar serviços
        self._start_services()
        
        return total_files, total_bytes
    
    def estimar_espaco(self) -> int:
        """Estima espaço que pode ser liberado"""
        total = 0
        for path_str in self.UPDATE_PATHS:
            path = Path(path_str)
            if path.exists():
                try:
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            try:
                                total += (Path(root) / file).stat().st_size
                            except:
                                pass
                except:
                    pass
        return total