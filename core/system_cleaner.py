"""
Limpeza avançada do sistema
DISM, CleanMgr, Component Store
"""

import subprocess
from pathlib import Path
from typing import Tuple
import time


class SystemCleaner:
    """Limpeza profunda do sistema usando ferramentas nativas"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def _log(self, msg: str):
        if self.verbose:
            print(f"  {msg}")
    
    def _run_command(self, cmd: str, timeout: int = 300) -> Tuple[int, str]:
        """Executa comando do sistema"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            output = result.stdout.decode('utf-8', errors='ignore')
            return result.returncode, output
        except subprocess.TimeoutExpired:
            self._log(f"Timeout: {cmd}")
            return -1, "Timeout"
        except Exception as e:
            return -2, str(e)
    
    def dism_cleanup(self) -> Tuple[bool, str, int]:
        """
        Executa DISM /StartComponentCleanup
        
        Returns:
            Tuple[bool, str, int]: (sucesso, mensagem, bytes_liberados_estimados)
        """
        self._log("Executando DISM /StartComponentCleanup...")
        
        returncode, output = self._run_command(
            "dism /online /cleanup-image /StartComponentCleanup /quiet",
            timeout=600
        )
        
        if returncode == 0:
            self._log("DISM concluído com sucesso")
            return True, "DISM executado com sucesso", 300 * 1024 * 1024
        else:
            self._log(f"DISM falhou: {output[:200]}")
            return False, f"DISM falhou: {output[:100]}", 0
    
    def dism_spsuperseded(self) -> Tuple[bool, str, int]:
        """
        Remove Service Pack e atualizações superseded
        
        Returns:
            Tuple[bool, str, int]: (sucesso, mensagem, bytes_liberados_estimados)
        """
        self._log("Executando DISM /SPSuperseded...")
        
        returncode, output = self._run_command(
            "dism /online /cleanup-image /SPSuperseded /quiet",
            timeout=600
        )
        
        if returncode == 0:
            self._log("SPSuperseded concluído")
            return True, "SPs antigos removidos", 100 * 1024 * 1024
        else:
            return False, "", 0
    
    def cleanmgr_aggressive(self) -> Tuple[bool, str]:
        """
        Executa CleanMgr no modo mais agressivo
        
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        self._log("Executando CleanMgr (modo agressivo)...")
        
        returncode, output = self._run_command("cleanmgr /verylowdisk", timeout=600)
        
        if returncode == 0 or returncode == 1:
            self._log("CleanMgr concluído")
            return True, "CleanMgr executado com sucesso"
        else:
            self._log("Tentando método alternativo...")
            self._run_command("cleanmgr /sageset:1", timeout=60)
            time.sleep(2)
            returncode2, _ = self._run_command("cleanmgr /sagerun:1", timeout=600)
            
            if returncode2 == 0 or returncode2 == 1:
                return True, "CleanMgr executado via sageset"
        
        return False, "CleanMgr falhou"
    
    def otimizar_volume_c(self) -> Tuple[bool, str]:
        """
        Otimiza volume C: (defrag/trim)
        """
        self._log("Otimizando volume C:...")
        
        returncode, output = self._run_command("defrag C: /O", timeout=1800)
        
        if returncode == 0:
            self._log("Otimização concluída")
            return True, "Volume C: otimizado"
        else:
            return False, "Otimização falhou"
    
    def limpeza_profunda(self) -> Tuple[int, int]:
        """
        Executa limpeza profunda do sistema (todas as ferramentas)
        
        Returns:
            Tuple[int, int]: (arquivos_removidos_estimados, bytes_liberados_estimados)
        """
        total_files_est = 0
        total_bytes_est = 0
        
        success, msg, bytes_freed = self.dism_cleanup()
        if success:
            total_bytes_est += bytes_freed
            total_files_est += 50
        
        success, msg, bytes_freed = self.dism_spsuperseded()
        if success:
            total_bytes_est += bytes_freed
        
        self.cleanmgr_aggressive()
        total_bytes_est += 200 * 1024 * 1024
        total_files_est += 200
        
        return total_files_est, total_bytes_est