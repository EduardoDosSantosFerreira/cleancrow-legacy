# core/engine.py
"""
CleanCrow - Engine de Limpeza (Orquestrador)
"""

import os
import sys
import time
import threading
import subprocess
from typing import List, Dict, Optional, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.models import CleanerResult, ScanResult, CleanerInfo, formatar_tamanho

try:
    from core.cleaners import (
        BaseCleaner,
        TempCleaner,
        WindowsTempCleaner,
        RecycleBinCleaner,
        ThumbnailCleaner,
        WERCleaner,
        WindowsUpdateCleaner,
        NvidiaCacheCleaner,
        AmdCacheCleaner,
        BrowsersCleaner,
        WebCacheCleaner,
        SystemCleaner,
    )
except ImportError as e:
    raise ImportError(f"Erro crítico ao importar cleaners: {e}")


class CleanerEngine:
    
    def __init__(
        self,
        dry_run: bool = False,
        verbose: bool = False,
        max_workers: int = 4,
        timeout_seconds: int = 1800,
    ):
        self.dry_run = dry_run
        self.verbose = verbose
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds
        self._cancel_event = threading.Event()
        self._log_callback: Optional[Callable[[str, str], None]] = None
        
        self._is_admin = self._check_admin()
        self._cleaners: List[BaseCleaner] = self._register_cleaners()
        self._scan_cache: Dict[str, ScanResult] = {}
        self._last_results: Dict[str, CleanerResult] = {}
    
    def _check_admin(self) -> bool:
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    def _elevate_admin(self) -> bool:
        if self._is_admin:
            return True
        
        try:
            import ctypes
            
            script = os.path.abspath(sys.argv[0])
            params = " ".join([f'"{arg}"' for arg in sys.argv[1:] if arg != "--no-admin"])
            
            result = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script}" {params}', None, 1
            )
            
            if result > 32:
                sys.exit(0)  # Encerra o processo atual para que o elevado assuma
                return True
        except:
            pass
        
        return False
    
    def _register_cleaners(self) -> List[BaseCleaner]:
        # Não registramos o SystemCleaner aqui para não executar DISM sem permissão em clean_all
        return [
            TempCleaner(dry_run=self.dry_run, verbose=self.verbose),
            WindowsTempCleaner(dry_run=self.dry_run, verbose=self.verbose),
            RecycleBinCleaner(dry_run=self.dry_run, verbose=self.verbose),
            ThumbnailCleaner(dry_run=self.dry_run, verbose=self.verbose),
            WERCleaner(dry_run=self.dry_run, verbose=self.verbose),
            WindowsUpdateCleaner(dry_run=self.dry_run, verbose=self.verbose),
            NvidiaCacheCleaner(dry_run=self.dry_run, verbose=self.verbose),
            AmdCacheCleaner(dry_run=self.dry_run, verbose=self.verbose),
            BrowsersCleaner(dry_run=self.dry_run, verbose=self.verbose),
            WebCacheCleaner(dry_run=self.dry_run, verbose=self.verbose),
            SystemCleaner(dry_run=self.dry_run, verbose=self.verbose),
        ]
    
    def set_log_callback(self, callback: Callable[[str, str], None]):
        self._log_callback = callback
    
    def _log(self, message: str, level: str = "info"):
        if self._log_callback:
            self._log_callback(message, level)
        elif self.verbose:
            print(f"[{level.upper()}] {message}")
    
    def request_interruption(self):
        self._cancel_event.set()
    
    def is_canceled(self) -> bool:
        return self._cancel_event.is_set()
    
    def get_cleaners(self) -> List[CleanerInfo]:
        return [c.info for c in self._cleaners]
    
    def get_cleaner(self, name: str) -> Optional[BaseCleaner]:
        for c in self._cleaners:
            if c.info.name == name:
                return c
        return None
    
    def scan_all(self, progress_callback: Optional[Callable[[int], None]] = None) -> Dict[str, ScanResult]:
        self._log("INICIANDO SCAN DO SISTEMA", "system")
        self._scan_cache = {}
        
        total = len(self._cleaners)
        self._log(f"{total} categorias a analisar", "info")
        
        if not self._is_admin:
            self._log("Execute como Administrador para scan completo", "warning")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for cleaner in self._cleaners:
                if self.is_canceled():
                    break
                future = executor.submit(self._scan_single, cleaner)
                futures[future] = cleaner
            
            completed = 0
            for future in as_completed(futures):
                if self.is_canceled():
                    break
                cleaner = futures[future]
                try:
                    result = future.result(timeout=30)
                    self._scan_cache[cleaner.info.name] = result
                except Exception as e:
                    self._scan_cache[cleaner.info.name] = ScanResult(
                        cleaner_name=cleaner.info.name,
                        exists=False,
                        error=str(e)
                    )
                
                completed += 1
                if progress_callback:
                    progress_callback(int(completed / total * 100))
                
                if result.exists and result.size_bytes > 0:
                    self._log(f"{cleaner.info.name}: {result.size_formatted}", "detail")
                else:
                    self._log(f"{cleaner.info.name}: Nao encontrado", "detail")
        
        total_bytes = sum(r.size_bytes for r in self._scan_cache.values())
        self._log(f"SCAN CONCLUIDO - Total recuperavel: {formatar_tamanho(total_bytes)}", "success")
        
        return self._scan_cache
    
    def _scan_single(self, cleaner: BaseCleaner) -> ScanResult:
        try:
            exists = cleaner.detect()
            size = cleaner.calculate_size() if exists else 0
            return ScanResult(
                cleaner_name=cleaner.info.name,
                exists=exists,
                size_bytes=size
            )
        except Exception as e:
            return ScanResult(
                cleaner_name=cleaner.info.name,
                exists=False,
                error=str(e)
            )
    
    def clean_selected(
        self,
        selected_names: List[str],
        progress_callback: Optional[Callable[[int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str, List[CleanerResult]]:
        
        self._last_results = {}
        
        if not selected_names:
            return False, "Nenhuma categoria selecionada", []
        
        if not self._is_admin:
            self._log("Programa nao esta como Administrador", "warning")
            self._log("Tentando elevar privilegios...", "step")
            
            if self._elevate_admin():
                self._log("Processo elevado com sucesso", "success")
                return True, "Reiniciando como Administrador...", []
            else:
                self._log("Nao foi possivel elevar. Algumas limpezas falharao.", "error")
        
        cleaners = [c for c in self._cleaners if c.info.name in selected_names]
        if not cleaners:
            return False, "Nenhum cleaner valido encontrado", []
        
        self._log(f"INICIANDO LIMPEZA - {len(cleaners)} categorias", "system")
        self._log("=" * 50, "system")
        
        results = []
        total_bytes_freed = 0
        total_files_removed = 0
        total_folders_removed = 0
        total_errors = 0
        
        for i, cleaner in enumerate(cleaners):
            if self.is_canceled():
                self._log("LIMPEZA CANCELADA PELO USUARIO", "error")
                break
            
            base_progress = 10 + int((i / len(cleaners)) * 80)
            if progress_callback:
                progress_callback(base_progress)
            
            if status_callback:
                status_callback(f"Limpando: {cleaner.info.name}...")
            
            self._log(f"[{i+1}/{len(cleaners)}] {cleaner.info.name}...", "step")
            
            try:
                result = cleaner.clean()
                self._last_results[cleaner.info.name] = result
                results.append(result)
                
                total_bytes_freed += result.bytes_freed
                total_files_removed += result.files_removed
                total_folders_removed += result.folders_removed
                total_errors += len(result.errors)
                
                if result.success:
                    if result.bytes_freed > 0:
                        self._log(f"{formatar_tamanho(result.bytes_freed)} liberados", "success")
                    else:
                        self._log(f"Nada a limpar", "info")
                    if result.errors:
                        self._log(f"{len(result.errors)} erro(s)", "warning")
                else:
                    self._log(f"Falha na limpeza", "error")
                    
            except Exception as e:
                self._log(f"Erro: {e}", "error")
                results.append(CleanerResult(
                    cleaner_name=cleaner.info.name,
                    success=False,
                    errors=[str(e)]
                ))
                total_errors += 1
        
        self._log("=" * 50, "system")
        self._log("RESUMO DA LIMPEZA", "system")
        self._log(f"Arquivos removidos: {total_files_removed:,}", "info")
        self._log(f"Pastas removidas: {total_folders_removed:,}", "info")
        self._log(f"Bytes liberados: {formatar_tamanho(total_bytes_freed)}", "success")
        if total_errors > 0:
            self._log(f"Erros: {total_errors}", "warning")
        
        if progress_callback:
            progress_callback(100)
        
        success = total_errors == 0 and not self.is_canceled()
        message = f"{formatar_tamanho(total_bytes_freed)} liberados, {total_files_removed} arquivos"
        
        return success, message, results
    
    def clean_all(self, **kwargs) -> Tuple[bool, str, List[CleanerResult]]:
        all_names = [c.info.name for c in self._cleaners]
        return self.clean_selected(all_names, **kwargs)
    
    def get_scan_summary(self) -> Dict[str, Dict]:
        summary = {}
        for name, result in self._scan_cache.items():
            if result.exists and result.size_bytes > 0:
                summary[name] = {
                    "size_bytes": result.size_bytes,
                    "size_formatted": result.size_formatted,
                    "file_count": result.file_count,
                }
        return summary
    
    def get_total_scan_size(self) -> int:
        return sum(r.size_bytes for r in self._scan_cache.values())


def create_engine(dry_run: bool = False, verbose: bool = False) -> CleanerEngine:
    return CleanerEngine(dry_run=dry_run, verbose=verbose)