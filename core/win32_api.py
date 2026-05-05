"""
Win32 API para operações nativas do Windows
Usado para lixeira, thumbnails e operações privilegiadas
"""

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import sys


# ============================================================================
# CONSTANTES WIN32
# ============================================================================

SHERB_NOCONFIRMATION = 0x00000001
SHERB_NOPROGRESSUI = 0x00000002
SHERB_NOSOUND = 0x00000004

CSIDL_LOCAL_APPDATA = 0x001c


# ============================================================================
# ESTRUTURAS WIN32
# ============================================================================

class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64),
    ]


# ============================================================================
# FUNÇÕES WIN32
# ============================================================================

def esvaziar_lixeira_win32() -> bool:
    """
    Esvazia lixeira usando API nativa do Windows
    Mais confiável que deletar manualmente $Recycle.Bin
    
    Returns:
        True se sucesso, False caso contrário
    """
    try:
        shell32 = ctypes.windll.shell32
        result = shell32.SHEmptyRecycleBinW(None, None, SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND)
        return result == 0
    except Exception:
        return False


def obter_tamanho_lixeira() -> int:
    """
    Obtém tamanho total da lixeira em bytes
    
    Returns:
        Tamanho em bytes
    """
    try:
        shell32 = ctypes.windll.shell32
        rbi = SHQUERYRBINFO()
        rbi.cbSize = ctypes.sizeof(SHQUERYRBINFO)
        
        if shell32.SHQueryRecycleBinW(None, ctypes.byref(rbi)):
            return 0
        
        return rbi.i64Size
    except Exception:
        return 0


def obter_caminho_local_appdata() -> Path:
    """
    Obtém caminho do Local AppData via API do Windows
    
    Returns:
        Path do Local AppData
    """
    try:
        shell32 = ctypes.windll.shell32
        buf = ctypes.create_unicode_buffer(260)
        shell32.SHGetFolderPathW(None, CSIDL_LOCAL_APPDATA, None, 0, buf)
        return Path(buf.value)
    except Exception:
        return Path(os.environ.get('LOCALAPPDATA', ''))


def limpar_thumbnails() -> int:
    """
    Limpa cache de thumbnails do Windows Explorer
    
    Returns:
        Bytes liberados
    """
    bytes_freed = 0
    local_appdata = obter_caminho_local_appdata()
    explorer_path = local_appdata / "Microsoft" / "Windows" / "Explorer"
    
    if not explorer_path.exists():
        return 0
    
    try:
        for file in explorer_path.glob("thumbcache_*.db"):
            try:
                size = file.stat().st_size
                file.unlink()
                bytes_freed += size
            except:
                pass
        
        for file in explorer_path.glob("iconcache_*.db"):
            try:
                size = file.stat().st_size
                file.unlink()
                bytes_freed += size
            except:
                pass
    except:
        pass
    
    return bytes_freed


def limpar_iconcache() -> int:
    """
    Limpa cache de ícones do Windows
    
    Returns:
        Bytes liberados
    """
    bytes_freed = 0
    local_appdata = obter_caminho_local_appdata()
    explorer_path = local_appdata / "Microsoft" / "Windows" / "Explorer"
    
    if not explorer_path.exists():
        return 0
    
    try:
        for file in explorer_path.glob("iconcache*"):
            try:
                size = file.stat().st_size
                file.unlink()
                bytes_freed += size
            except:
                pass
    except:
        pass
    
    return bytes_freed