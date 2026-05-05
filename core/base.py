"""
CleanCrow - Base e Utilitários Comuns
Compartilhado entre todos os modos de limpeza
"""

import os
import sys
import time
import ctypes
import subprocess
import stat
from pathlib import Path
from typing import Tuple, Dict, List, Optional
from enum import Enum


# ============================================================================
# CONSTANTES
# ============================================================================

class ModoTipo(Enum):
    RAPIDO = "rapido"
    NORMAL = "normal"
    SEGURO = "seguro"


# ============================================================================
# UTILITÁRIOS DE SISTEMA
# ============================================================================

def is_admin() -> bool:
    """Verifica se está rodando como administrador"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def elevar_privilegios() -> None:
    """Eleva privilégios via UAC automaticamente"""
    if is_admin():
        return
    
    if "--no-admin" in sys.argv:
        return
    
    print("🔐 Solicitando privilégios de administrador...")
    
    script = os.path.abspath(sys.argv[0])
    params = " ".join([arg for arg in sys.argv[1:] if arg != "--no-admin"])
    
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, f'"{script}" {params}', None, 1
    )
    
    sys.exit(0)


def executar_comando(comando: str, timeout_segundos: int = 300) -> Tuple[int, str, str]:
    """Executa comando do sistema com timeout"""
    try:
        process = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout_segundos)
            return process.returncode, stdout.decode('utf-8', errors='ignore'), stderr.decode('utf-8', errors='ignore')
        except subprocess.TimeoutExpired:
            process.kill()
            return -1, "", f"Timeout após {timeout_segundos} segundos"
            
    except Exception as e:
        return -2, "", str(e)


def formatar_tamanho(bytes_size: int) -> str:
    """Formata bytes para exibição"""
    if bytes_size >= 1024 * 1024 * 1024:
        return f"{bytes_size / (1024*1024*1024):.2f} GB"
    elif bytes_size >= 1024 * 1024:
        return f"{bytes_size / (1024*1024):.2f} MB"
    elif bytes_size >= 1024:
        return f"{bytes_size / 1024:.2f} KB"
    return f"{bytes_size} bytes"


# ============================================================================
# OPERAÇÕES DE ARQUIVO
# ============================================================================

def remover_arquivo(filepath: Path) -> Tuple[bool, int]:
    """Remove um arquivo com tratamento de erro"""
    try:
        if not filepath.exists():
            return False, 0
        tamanho = filepath.stat().st_size
        os.chmod(filepath, stat.S_IWRITE)
        filepath.unlink()
        return True, tamanho
    except:
        return False, 0


def remover_arquivos_antigos(path: Path, dias: int) -> Tuple[int, int]:
    """Remove arquivos mais antigos que X dias"""
    arquivos = 0
    bytes_liberados = 0
    
    if not path.exists():
        return 0, 0
    
    limite = time.time() - (dias * 86400)
    
    try:
        for item in path.iterdir():
            try:
                if item.is_file():
                    if item.stat().st_mtime < limite:
                        success, size = remover_arquivo(item)
                        if success:
                            arquivos += 1
                            bytes_liberados += size
            except:
                pass
    except:
        pass
    
    return arquivos, bytes_liberados


def remover_pasta(path: Path) -> Tuple[int, int]:
    """Remove uma pasta completamente"""
    arquivos = 0
    bytes_liberados = 0
    
    if not path.exists():
        return 0, 0
    
    try:
        for item in path.iterdir():
            try:
                if item.is_file():
                    success, size = remover_arquivo(item)
                    if success:
                        arquivos += 1
                        bytes_liberados += size
                elif item.is_dir():
                    sub_arquivos, sub_bytes = remover_pasta(item)
                    arquivos += sub_arquivos
                    bytes_liberados += sub_bytes
            except:
                pass
        
        try:
            path.rmdir()
        except:
            pass
    except:
        pass
    
    return arquivos, bytes_liberados


# ============================================================================
# DETECÇÃO DE DISCOS
# ============================================================================

def obter_todos_discos() -> List[str]:
    """Detecta TODOS os discos disponíveis no sistema"""
    drives = []
    
    try:
        if sys.platform == 'win32':
            import string
            for letter in string.ascii_uppercase:
                drive_path = f"{letter}:\\"
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
                if drive_type in (2, 3):  # REMOVABLE ou FIXED
                    if os.path.exists(drive_path):
                        drives.append(f"{letter}:")
    except:
        pass
    
    return drives if drives else ['C:']


# ============================================================================
# NAVEGADORES (COMUM)
# ============================================================================

NAVEGADORES_CONFIG = {
    "Chrome": "Google/Chrome/User Data",
    "Edge": "Microsoft/Edge/User Data", 
    "Brave": "BraveSoftware/Brave-Browser/User Data",
    "Opera": "Opera Software/Opera Stable",
    "Firefox": "Mozilla/Firefox/Profiles",
}

CACHE_DIRS = ["Cache", "Code Cache", "GPUCache", "Service Worker"]


def limpar_cache_navegadores(local_appdata: Path, verbose: bool = False) -> Tuple[int, int]:
    """Limpa cache de navegadores (comum para todos os modos)"""
    total_arquivos = 0
    total_bytes = 0
    
    for nome, caminho_rel in NAVEGADORES_CONFIG.items():
        browser_path = local_appdata / caminho_rel
        if not browser_path.exists():
            continue
        
        if nome == "Firefox":
            for profile in browser_path.iterdir():
                if profile.is_dir():
                    for cache_dir in ["cache2", "cache"]:
                        cache_path = profile / cache_dir
                        if cache_path.exists():
                            arquivos, bytes_liberados = remover_pasta(cache_path)
                            total_arquivos += arquivos
                            total_bytes += bytes_liberados
        else:
            for profile_dir in browser_path.iterdir():
                if profile_dir.is_dir() and (profile_dir.name == "Default" or profile_dir.name.startswith("Profile")):
                    for cache_dir in CACHE_DIRS:
                        cache_path = profile_dir / cache_dir
                        if cache_path.exists():
                            arquivos, bytes_liberados = remover_pasta(cache_path)
                            total_arquivos += arquivos
                            total_bytes += bytes_liberados
    
    return total_arquivos, total_bytes


# ============================================================================
# ESVAZIAR LIXEIRA
# ============================================================================

def esvaziar_lixeira_api() -> bool:
    """Esvazia lixeira via API nativa do Windows"""
    try:
        shell32 = ctypes.windll.shell32
        result = shell32.SHEmptyRecycleBinW(
            None, None, 
            0x00000001 | 0x00000002  # SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI
        )
        return result == 0
    except:
        return False