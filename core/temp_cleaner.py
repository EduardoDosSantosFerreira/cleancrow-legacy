"""
Limpeza agressiva de arquivos temporários
Sem filtros idiotas - limpa TUDO que não está em uso
"""

import os
import shutil
import stat
from pathlib import Path
from typing import Tuple, List, Set
import time


class TempCleaner:
    """Limpeza especializada para arquivos temporários"""
    
    TEMP_DIRS = [
        "%TEMP%",
        "%TMP%",
        "C:/Windows/Temp",
        "C:/Windows/ServiceProfiles/LocalService/AppData/Local/Temp",
        "C:/Windows/ServiceProfiles/NetworkService/AppData/Local/Temp",
    ]
    
    # Pastas adicionais que acumulam lixo
    ADDITIONAL_PATHS = [
        "%LOCALAPPDATA%/Temp",
        "%LOCALAPPDATA%/Microsoft/Windows/INetCache",
        "%LOCALAPPDATA%/Microsoft/Windows/INetCookies",
        "%LOCALAPPDATA%/Microsoft/Windows/History",
        "%APPDATA%/Microsoft/Windows/Recent",
    ]
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._processed_dirs: Set[Path] = set()
    
    def _log(self, msg: str):
        if self.verbose:
            print(f"  {msg}")
    
    def _expand_path(self, path_str: str) -> Path:
        """Expande variáveis de ambiente"""
        expanded = os.path.expandvars(path_str)
        return Path(expanded)
    
    def _remove_readonly(self, func, path, excinfo):
        """Remove atributo readonly"""
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except:
            pass
    
    def _limpar_arquivo(self, filepath: Path) -> Tuple[bool, int]:
        """Tenta remover um arquivo"""
        try:
            size = filepath.stat().st_size
            os.chmod(filepath, stat.S_IWRITE)
            filepath.unlink()
            return True, size
        except (OSError, PermissionError):
            return False, 0
    
    def _limpar_pasta(self, path: Path, recursivo: bool = True) -> Tuple[int, int]:
        """Limpa pasta recursivamente"""
        files = 0
        bytes_freed = 0
        
        if not path.exists():
            return 0, 0
        
        # Evitar processar mesma pasta múltiplas vezes
        if path in self._processed_dirs:
            return 0, 0
        self._processed_dirs.add(path)
        
        try:
            # Processar arquivos primeiro
            try:
                for item in path.iterdir():
                    try:
                        if item.is_file():
                            success, size = self._limpar_arquivo(item)
                            if success:
                                files += 1
                                bytes_freed += size
                    except (OSError, PermissionError):
                        pass
            except:
                pass
            
            # Depois, limpar subpastas (se recursivo)
            if recursivo:
                try:
                    for item in path.iterdir():
                        if item.is_dir():
                            sub_files, sub_bytes = self._limpar_pasta(item, recursivo)
                            files += sub_files
                            bytes_freed += sub_bytes
                except:
                    pass
            
            # Tentar remover pasta se vazia
            try:
                if path.exists() and not any(path.iterdir()):
                    path.rmdir()
            except:
                pass
                
        except Exception:
            pass
        
        return files, bytes_freed
    
    def limpar(self) -> Tuple[int, int]:
        """
        Limpa TODOS os arquivos temporários
        
        Returns:
            Tuple[int, int]: (arquivos_removidos, bytes_liberados)
        """
        total_files = 0
        total_bytes = 0
        
        # Temp dirs principais
        for path_str in self.TEMP_DIRS:
            path = self._expand_path(path_str)
            if path.exists():
                self._log(f"Limpando: {path}")
                files, bytes_freed = self._limpar_pasta(path, recursivo=True)
                total_files += files
                total_bytes += bytes_freed
                if bytes_freed > 0:
                    self._log(f"  Liberado: {bytes_freed // (1024*1024)} MB")
        
        # Pastas adicionais
        for path_str in self.ADDITIONAL_PATHS:
            path = self._expand_path(path_str)
            if path.exists() and path not in self._processed_dirs:
                self._log(f"Limpando: {path}")
                files, bytes_freed = self._limpar_pasta(path, recursivo=False)
                total_files += files
                total_bytes += bytes_freed
        
        return total_files, total_bytes
    
    def estimar_espaco(self) -> int:
        """Estima espaço que pode ser liberado"""
        total = 0
        
        for path_str in self.TEMP_DIRS:
            path = self._expand_path(path_str)
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