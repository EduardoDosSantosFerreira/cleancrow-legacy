# core/win32_api.py
"""
CleanCrow - APIs do Windows (Low-level)
"""

import ctypes
import ctypes.wintypes
from typing import Optional, Tuple


# ============================================================================
# LIXEIRA - SHEmptyRecycleBin
# ============================================================================

def esvaziar_lixeira_api() -> bool:
    """Esvazia a Lixeira usando a API do Windows"""
    try:
        SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
        return SHEmptyRecycleBin(0, None, 0x0001) == 0
    except:
        return False


def obter_tamanho_lixeira() -> int:
    """
    Obtém o tamanho total dos itens na Lixeira.
    
    Usa SHQueryRecycleBin para cada unidade.
    """
    total = 0
    
    try:
        SHQueryRecycleBin = ctypes.windll.shell32.SHQueryRecycleBinW
        
        # Estrutura para receber informações
        class SHQUERYRBINFO(ctypes.Structure):
            _fields_ = [
                ('cbSize', ctypes.wintypes.DWORD),
                ('i64Size', ctypes.wintypes.LONGLONG),
                ('i64NumItems', ctypes.wintypes.LONGLONG),
            ]
        
        # Verifica todas as unidades
        for drive in ['C:', 'D:', 'E:', 'F:', 'G:']:
            try:
                info = SHQUERYRBINFO()
                info.cbSize = ctypes.sizeof(SHQUERYRBINFO)
                if SHQueryRecycleBin(drive, ctypes.byref(info)) == 0:
                    total += info.i64Size
            except:
                pass
    except:
        pass
    
    return total


# ============================================================================
# DISCO - GetDiskFreeSpace
# ============================================================================

def obter_espaco_livre(drive: str = "C:") -> Tuple[Optional[int], Optional[int]]:
    """
    Obtém espaço livre e total de uma unidade.
    
    Returns:
        (free_bytes, total_bytes) ou (None, None) em erro
    """
    try:
        free = ctypes.c_ulonglong(0)
        total = ctypes.c_ulonglong(0)
        GetDiskFreeSpaceEx = ctypes.windll.kernel32.GetDiskFreeSpaceExW
        if GetDiskFreeSpaceEx(f"{drive}\\", ctypes.byref(free), ctypes.byref(total), None):
            return free.value, total.value
    except:
        pass
    return None, None


# ============================================================================
# PERMISSÕES - Administrador
# ============================================================================

def is_admin() -> bool:
    """Verifica se o processo atual é administrador"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


def elevar_processo() -> bool:
    """
    Eleva o processo atual via UAC.
    
    Returns:
        True se o processo foi reiniciado com elevação
    """
    import sys
    import os
    
    if is_admin():
        return True
    
    try:
        script = os.path.abspath(sys.argv[0])
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:] if arg != "--no-admin"])
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
        if result > 32:
            # Processo elevado iniciado, podemos encerrar este
            import sys
            sys.exit(0)
    except:
        pass
    return False