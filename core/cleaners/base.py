# core/cleaners/base.py

import os
import time
import shutil
import subprocess
import stat
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, List, Optional

from core.models import CleanerResult, CleanerInfo, formatar_tamanho


class BaseCleaner(ABC):
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self._last_result: Optional[CleanerResult] = None
        
    @property
    @abstractmethod
    def info(self) -> CleanerInfo:
        pass
    
    @abstractmethod
    def _get_targets(self) -> List[Path]:
        pass
    
    @abstractmethod
    def _can_clean(self, path: Path) -> bool:
        pass
    
    def _log(self, message: str, level: str = "info"):
        if self.verbose:
            print(f"[{self.info.name}] {message}")
    
    def detect(self) -> bool:
        for path in self._get_targets():
            if path.exists():
                return True
        return False
    
    def calculate_size(self) -> int:
        total = 0
        for path in self._get_targets():
            if not path.exists():
                continue
            if path.is_file():
                try:
                    total += path.stat().st_size
                except:
                    pass
            elif path.is_dir():
                total += self._calculate_dir_size(path)
        return total
    
    def _calculate_dir_size(self, path: Path) -> int:
        total = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    try:
                        total += item.stat().st_size
                    except:
                        pass
        except (PermissionError, OSError):
            pass
        return total
    
    def _is_cleanmgr_running(self) -> bool:
        """Verifica se o cleanmgr ja esta em execucao"""
        try:
            result = subprocess.run(
                ['tasklist', '/fi', 'imagename eq cleanmgr.exe'],
                capture_output=True,
                text=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return 'cleanmgr.exe' in result.stdout
        except:
            return False
    
    def clean(self) -> CleanerResult:
        start_time = time.time()
        result = CleanerResult(
            cleaner_name=self.info.name,
            success=True
        )
        
        for path in self._get_targets():
            if not path.exists():
                continue
            
            if self._can_clean(path):
                files, folders, bytes_freed = self._remove_path(path)
                result.files_removed += files
                result.folders_removed += folders
                result.bytes_freed += bytes_freed
        
        result.duration_ms = (time.time() - start_time) * 1000
        self._last_result = result
        return result
    
    def _remove_path(self, path: Path) -> Tuple[int, int, int]:
        files = 0
        folders = 0
        bytes_freed = 0
        
        if self.dry_run:
            if path.is_dir():
                bytes_freed = self._calculate_dir_size(path)
            elif path.is_file():
                try:
                    bytes_freed = path.stat().st_size
                except:
                    pass
            return 0, 0, bytes_freed
        
        try:
            if path.is_file():
                try:
                    tamanho = path.stat().st_size
                except:
                    tamanho = 0
                
                if self._remove_file(path):
                    files += 1
                    bytes_freed += tamanho
                    
            elif path.is_dir():
                f, d, b = self._remove_folder(path)
                files += f
                folders += d
                bytes_freed += b
        except (PermissionError, OSError) as e:
            if self.verbose:
                print(f"  Erro ao remover {path}: {e}")
        
        return files, folders, bytes_freed
    
    def _remove_file(self, path: Path) -> bool:
        if self.dry_run:
            return True
        
        try:
            if os.name == 'nt':
                os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
            path.unlink()
            return True
        except:
            pass
        
        try:
            subprocess.run(
                ['cmd', '/c', 'del', '/f', '/q', '/a', str(path)],
                capture_output=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if not path.exists():
                return True
        except:
            pass
        
        try:
            os.remove(str(path))
            return True
        except:
            pass
        
        return False
    
    def _remove_folder(self, path: Path) -> Tuple[int, int, int]:
        files = 0
        folders = 0
        bytes_freed = 0
        
        if self.dry_run:
            bytes_freed = self._calculate_dir_size(path)
            return 0, 0, bytes_freed
        
        try:
            subprocess.run(
                ['cmd', '/c', 'attrib', '-h', '-s', '-r', f'{path}\\*.*', '/s', '/d'],
                capture_output=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except:
            pass
        
        try:
            subprocess.run(
                ['cmd', '/c', 'takeown', '/f', str(path), '/r', '/d', 'y'],
                capture_output=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except:
            pass
        
        try:
            subprocess.run(
                ['cmd', '/c', 'icacls', str(path), '/grant', 'Administradores:F', '/t'],
                capture_output=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except:
            pass
        
        try:
            for item in list(path.iterdir()):
                try:
                    if item.is_file():
                        try:
                            tamanho = item.stat().st_size
                        except:
                            tamanho = 0
                        
                        if self._remove_file(item):
                            files += 1
                            bytes_freed += tamanho
                    elif item.is_dir():
                        f, d, b = self._remove_folder(item)
                        files += f
                        folders += d
                        bytes_freed += b
                except (PermissionError, OSError):
                    pass
        except (PermissionError, OSError):
            pass
        
        try:
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)
                if not path.exists():
                    folders += 1
                    return files, folders, bytes_freed
        except:
            pass
        
        try:
            subprocess.run(
                ['cmd', '/c', 'rmdir', '/s', '/q', str(path)],
                capture_output=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if not path.exists():
                folders += 1
                return files, folders, bytes_freed
        except:
            pass
        
        try:
            os.rmdir(str(path))
            if not path.exists():
                folders += 1
        except:
            pass
        
        return files, folders, bytes_freed
    
    def verify(self) -> bool:
        for path in self._get_targets():
            if path.exists():
                if path.is_dir():
                    try:
                        if any(path.iterdir()):
                            return False
                    except:
                        pass
                else:
                    return False
        return True
    
    def get_info(self) -> CleanerInfo:
        return self.info