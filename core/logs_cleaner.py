"""
Limpeza de logs do sistema (CBS, Panther, Minidump)
Remove apenas arquivos antigos para segurança
"""

from pathlib import Path
from typing import Tuple
import time
import os
import stat


class LogsCleaner:
    """Limpeza especializada para logs do sistema"""
    
    # Logs que podem ser removidos com segurança
    LOG_PATHS = [
        ("C:/Windows/Logs", 7),           # 7 dias
        ("C:/Windows/Logs/CBS", 7),       # 7 dias
        ("C:/Windows/Logs/DISM", 3),      # 3 dias
        ("C:/Windows/Logs/WindowsUpdate", 3),  # 3 dias
        ("C:/Windows/Panther", 30),       # 30 dias
        ("C:/Windows/Panther/UnattendGC", 7),
        ("C:/Windows/debug", 7),
        ("C:/Windows/System32/LogFiles", 7),
        ("C:/Windows/System32/winevt/Logs", 30),  # Event logs (30 dias)
    ]
    
    # Crash dumps
    DUMP_PATHS = [
        ("C:/Windows/Minidump", 0),       # Todos
        ("C:/Windows/MEMORY.DMP", 0),     # Único arquivo
    ]
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def _log(self, msg: str):
        if self.verbose:
            print(f"  {msg}")
    
    def _remove_readonly(self, func, path, excinfo):
        """Remove atributo readonly"""
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except:
            pass
    
    def _is_old_file(self, filepath: Path, days: int) -> bool:
        """Verifica se arquivo é mais antigo que 'days' dias"""
        if days <= 0:
            return True
        
        try:
            mtime = filepath.stat().st_mtime
            age_days = (time.time() - mtime) / 86400
            return age_days >= days
        except:
            return False
    
    def _limpar_arquivo(self, filepath: Path) -> Tuple[bool, int]:
        """Tenta remover arquivo"""
        try:
            size = filepath.stat().st_size
            os.chmod(filepath, stat.S_IWRITE)
            filepath.unlink()
            return True, size
        except:
            return False, 0
    
    def _limpar_pasta_logs(self, path: Path, days: int) -> Tuple[int, int]:
        """Limpa arquivos de log antigos de uma pasta"""
        files = 0
        bytes_freed = 0
        
        if not path.exists():
            return 0, 0
        
        try:
            for item in path.iterdir():
                try:
                    if item.is_file():
                        if self._is_old_file(item, days):
                            success, size = self._limpar_arquivo(item)
                            if success:
                                files += 1
                                bytes_freed += size
                except:
                    pass
        except:
            pass
        
        return files, bytes_freed
    
    def _limpar_dump(self, path: Path) -> Tuple[int, int]:
        """Limpa crash dumps"""
        files = 0
        bytes_freed = 0
        
        if not path.exists():
            return 0, 0
        
        if path.is_file():  # MEMORY.DMP
            if self._is_old_file(path, 0):
                success, size = self._limpar_arquivo(path)
                if success:
                    files = 1
                    bytes_freed = size
        elif path.is_dir():  # Minidump
            files, bytes_freed = self._limpar_pasta_logs(path, 0)
        
        return files, bytes_freed
    
    def limpar(self) -> Tuple[int, int]:
        """
        Limpa logs antigos do sistema
        
        Returns:
            Tuple[int, int]: (arquivos_removidos, bytes_liberados)
        """
        total_files = 0
        total_bytes = 0
        
        # Logs normais
        for path_str, days in self.LOG_PATHS:
            path = Path(path_str)
            if path.exists():
                self._log(f"Limpando logs antigos: {path} (> {days} dias)")
                files, bytes_freed = self._limpar_pasta_logs(path, days)
                total_files += files
                total_bytes += bytes_freed
                if bytes_freed > 0:
                    self._log(f"  Liberado: {bytes_freed // (1024*1024)} MB")
        
        # Crash dumps
        for path_str, days in self.DUMP_PATHS:
            path = Path(path_str)
            if path.exists():
                self._log(f"Limpando dumps: {path}")
                files, bytes_freed = self._limpar_dump(path)
                total_files += files
                total_bytes += bytes_freed
        
        return total_files, total_bytes
    
    def estimar_espaco(self) -> int:
        """Estima espaço que pode ser liberado"""
        total = 0
        
        for path_str, days in self.LOG_PATHS:
            path = Path(path_str)
            if path.exists():
                try:
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            filepath = Path(root) / file
                            if self._is_old_file(filepath, days):
                                try:
                                    total += filepath.stat().st_size
                                except:
                                    pass
                except:
                    pass
        
        return total