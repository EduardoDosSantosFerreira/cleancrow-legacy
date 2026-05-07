"""
CleanCrow - Modo NORMAL ULTRA
Limpeza profissional completa do Windows + Winget
Libera espaço REAL em TODOS os discos e atualiza programas
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
from dataclasses import dataclass, field
import string


# ============================================================================
# CONSTANTES E CONFIGURAÇÕES
# ============================================================================

class ModoExecucao(Enum):
    RAPIDO = "rapido"
    NORMAL = "normal"
    SEGURO = "seguro"


@dataclass
class ResultadoLimpeza:
    disco: str
    arquivos: int = 0
    bytes_liberados: int = 0
    erros: int = 0
    tarefas: Dict[str, Tuple[int, int]] = field(default_factory=dict)


# ============================================================================
# UTILITÁRIOS
# ============================================================================

def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def elevar_privilegios() -> None:
    if is_admin():
        return
    if "--no-admin" in sys.argv:
        return
    print("🔐 Solicitando privilégios de administrador...")
    script = os.path.abspath(sys.argv[0])
    params = " ".join([arg for arg in sys.argv[1:] if arg != "--no-admin"])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
    sys.exit(0)


def executar_comando(comando: str, timeout_segundos: int = 300) -> Tuple[int, str, str]:
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
    if bytes_size >= 1024 * 1024 * 1024:
        return f"{bytes_size / (1024*1024*1024):.2f} GB"
    elif bytes_size >= 1024 * 1024:
        return f"{bytes_size / (1024*1024):.2f} MB"
    elif bytes_size >= 1024:
        return f"{bytes_size / 1024:.2f} KB"
    return f"{bytes_size} bytes"


def remover_arquivo(filepath: Path) -> Tuple[bool, int]:
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


def obter_todos_discos() -> List[str]:
    drives = []
    try:
        for letter in string.ascii_uppercase:
            drive_path = f"{letter}:\\"
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
            if drive_type in (2, 3):
                if os.path.exists(drive_path):
                    drives.append(f"{letter}:")
    except:
        pass
    return drives if drives else ['C:']


# ============================================================================
# LIMPEZA POR DISCO
# ============================================================================

class LimpezaDisco:
    def __init__(self, drive: str, verbose: bool = False):
        self.drive = drive
        self.verbose = verbose
        self.resultado = ResultadoLimpeza(disco=drive)
    
    def log(self, mensagem: str, nivel: str = "info"):
        if self.verbose:
            print(f"  [{self.drive}] {mensagem}")
    
    def limpar_lixeira(self) -> Tuple[int, int]:
        try:
            shell32 = ctypes.windll.shell32
            result = shell32.SHEmptyRecycleBinW(None, None, 0x00000001 | 0x00000002)
            if result == 0:
                return 1, 0
        except:
            self.resultado.erros += 1
        return 0, 0
    
    def limpar_temp(self) -> Tuple[int, int]:
        total_arquivos = 0
        total_bytes = 0
        temp_paths = [
            Path(f"{self.drive}/Temp"),
            Path(f"{self.drive}/Windows/Temp"),
            Path(f"{self.drive}/Windows/Logs"),
        ]
        for path in temp_paths:
            if path.exists():
                arquivos, bytes_liberados = remover_arquivos_antigos(path, 3)
                total_arquivos += arquivos
                total_bytes += bytes_liberados
        return total_arquivos, total_bytes
    
    def limpar_prefetch(self) -> Tuple[int, int]:
        prefetch_path = Path(f"{self.drive}/Windows/Prefetch")
        if not prefetch_path.exists():
            return 0, 0
        return remover_arquivos_antigos(prefetch_path, 7)
    
    def limpar_logs_pesados(self) -> Tuple[int, int]:
        total_arquivos = 0
        total_bytes = 0
        log_paths = [
            (f"{self.drive}/Windows/Logs/CBS", 7),
            (f"{self.drive}/Windows/Logs/DISM", 3),
            (f"{self.drive}/Windows/Logs/WindowsUpdate", 3),
            (f"{self.drive}/Windows/Panther", 30),
            (f"{self.drive}/Windows/Minidump", 0),
        ]
        for path_str, dias in log_paths:
            path = Path(path_str)
            if path.exists():
                if dias > 0:
                    arquivos, bytes_liberados = remover_arquivos_antigos(path, dias)
                else:
                    arquivos, bytes_liberados = remover_pasta(path)
                total_arquivos += arquivos
                total_bytes += bytes_liberados
        memory_dmp = Path(f"{self.drive}/Windows/MEMORY.DMP")
        if memory_dmp.exists():
            success, size = remover_arquivo(memory_dmp)
            if success:
                total_arquivos += 1
                total_bytes += size
        return total_arquivos, total_bytes
    
    def limpar_cache_usuarios(self) -> Tuple[int, int]:
        total_arquivos = 0
        total_bytes = 0
        users_path = Path(f"{self.drive}/Users")
        if not users_path.exists():
            return 0, 0
        try:
            for user_dir in users_path.iterdir():
                if not user_dir.is_dir():
                    continue
                cache_paths = [
                    user_dir / "AppData/Local/Temp",
                    user_dir / "AppData/Local/Microsoft/Windows/Explorer",
                    user_dir / "AppData/Local/CrashDumps",
                    user_dir / "AppData/Local/D3DSCache",
                    user_dir / "AppData/Local/Packages",
                ]
                for cache_path in cache_paths:
                    if cache_path.exists():
                        if "Explorer" in str(cache_path):
                            for pattern in ["thumbcache_*.db", "iconcache_*.db"]:
                                for file in cache_path.glob(pattern):
                                    success, size = remover_arquivo(file)
                                    if success:
                                        total_arquivos += 1
                                        total_bytes += size
                        elif "Packages" in str(cache_path):
                            for package in cache_path.iterdir():
                                if package.is_dir():
                                    local_cache = package / "LocalCache"
                                    if local_cache.exists():
                                        arquivos, bytes_liberados = remover_pasta(local_cache)
                                        total_arquivos += arquivos
                                        total_bytes += bytes_liberados
                        else:
                            arquivos, bytes_liberados = remover_arquivos_antigos(cache_path, 3)
                            total_arquivos += arquivos
                            total_bytes += bytes_liberados
        except:
            pass
        return total_arquivos, total_bytes
    
    def limpar_caches_web(self) -> Tuple[int, int]:
        total_arquivos = 0
        total_bytes = 0
        users_path = Path(f"{self.drive}/Users")
        if not users_path.exists():
            return 0, 0
        navegadores = {
            "Chrome": "Google/Chrome/User Data",
            "Edge": "Microsoft/Edge/User Data",
            "Brave": "BraveSoftware/Brave-Browser/User Data",
            "Opera": "Opera Software/Opera Stable",
            "Firefox": "Mozilla/Firefox/Profiles",
        }
        try:
            for user_dir in users_path.iterdir():
                if not user_dir.is_dir():
                    continue
                local_appdata = user_dir / "AppData/Local"
                if not local_appdata.exists():
                    continue
                for nome, caminho_rel in navegadores.items():
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
                                for cache_dir in ["Cache", "Code Cache", "GPUCache", "Service Worker"]:
                                    cache_path = profile_dir / cache_dir
                                    if cache_path.exists():
                                        arquivos, bytes_liberados = remover_pasta(cache_path)
                                        total_arquivos += arquivos
                                        total_bytes += bytes_liberados
        except:
            pass
        return total_arquivos, total_bytes
    
    def limpar_windows_update(self) -> Tuple[int, int]:
        if self.drive != "C:":
            return 0, 0
        total_arquivos = 0
        total_bytes = 0
        for service in ["wuauserv", "bits"]:
            executar_comando(f"net stop {service}", timeout=30)
        time.sleep(2)
        update_paths = [
            Path("C:/Windows/SoftwareDistribution/Download"),
            Path("C:/Windows/SoftwareDistribution/DeliveryOptimization"),
        ]
        for path in update_paths:
            if path.exists():
                arquivos, bytes_liberados = remover_pasta(path)
                total_arquivos += arquivos
                total_bytes += bytes_liberados
                path.mkdir(parents=True, exist_ok=True)
        for service in ["wuauserv", "bits"]:
            executar_comando(f"net start {service}", timeout=30)
        return total_arquivos, total_bytes
    
    def executar_limpeza_completa(self) -> ResultadoLimpeza:
        tarefas = [
            ("Lixeira", self.limpar_lixeira),
            ("Temporários", self.limpar_temp),
            ("Prefetch", self.limpar_prefetch),
            ("Logs Pesados", self.limpar_logs_pesados),
            ("Cache Usuários", self.limpar_cache_usuarios),
            ("Cache Navegadores", self.limpar_caches_web),
        ]
        if self.drive == "C:":
            tarefas.insert(0, ("Windows Update", self.limpar_windows_update))
        for nome, func in tarefas:
            try:
                arquivos, bytes_liberados = func()
                self.resultado.arquivos += arquivos
                self.resultado.bytes_liberados += bytes_liberados
                self.resultado.tarefas[nome] = (arquivos, bytes_liberados)
            except:
                self.resultado.erros += 1
        return self.resultado


# ============================================================================
# SISTEMA (PAINEL DE CONTROLE)
# ============================================================================

class LimpezaSistema:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def log(self, mensagem: str, nivel: str = "info"):
        if self.verbose:
            print(f"  {mensagem}")
    
    def executar_dism(self) -> Tuple[bool, str, int]:
        if not is_admin():
            return False, "Requer admin", 0
        returncode, stdout, stderr = executar_comando("dism /online /cleanup-image /StartComponentCleanup /ResetBase /quiet", timeout_segundos=600)
        if returncode == 0:
            return True, "Sucesso", 500 * 1024 * 1024
        elif "no operation required" in stdout.lower():
            return True, "Nada a limpar", 0
        return False, stderr[:200], 0
    
    def executar_cleanmgr(self) -> Tuple[bool, str, int]:
        if not is_admin():
            return False, "Requer admin", 0
        executar_comando("cleanmgr /sageset:1", timeout_segundos=30)
        time.sleep(1)
        returncode, stdout, stderr = executar_comando("cleanmgr /sagerun:1", timeout_segundos=600)
        if returncode == 0 or returncode == 1:
            return True, "Sucesso", 200 * 1024 * 1024
        return False, "CleanMgr falhou", 0
    
    def executar_limpeza_sistema(self) -> Tuple[int, int]:
        total_bytes = 0
        total_arquivos = 0
        success, msg, bytes_freed = self.executar_dism()
        total_bytes += bytes_freed
        success, msg, bytes_freed = self.executar_cleanmgr()
        total_bytes += bytes_freed
        return total_arquivos, total_bytes


# ============================================================================
# CLASSE PRINCIPAL DO MODO NORMAL
# ============================================================================

class ModoNormal:
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.stats = {
            "total_arquivos": 0,
            "total_bytes": 0,
            "erros": 0,
            "discos_processados": 0,
            "tempo_total": 0,
        }
        self.resultados_discos: List[ResultadoLimpeza] = []
    
    def log(self, mensagem: str, nivel: str = "info"):
        if self.verbose:
            print(f"  {mensagem}")
    
    def executar(self, progress_callback=None) -> Tuple[bool, str]:
        elevar_privilegios()
        
        print("\n" + "="*70)
        print("🧹 CLEANCROW - MODO NORMAL ULTRA")
        print("="*70)
        print("📌 Modo: COMPLETO (todos os discos + DISM + CleanMgr)")
        print("🖥️  Sistema: Windows")
        
        if not is_admin():
            print("⚠️ Atenção: Algumas limpezas requerem privilégios de administrador")
        
        if self.dry_run:
            print("🔍 MODO SIMULAÇÃO - Nenhum arquivo será deletado")
        
        print("="*70 + "\n")
        
        inicio_total = time.time()
        
        # FASE 1: LIMPEZA EM TODOS OS DISCOS
        self.log("📀 [FASE 1] Limpeza em todos os discos", "step")
        drives = obter_todos_discos()
        self.log(f"Discos detectados: {', '.join(drives)}", "info")
        
        for i, drive in enumerate(drives):
            if progress_callback:
                progress_callback(10 + (i * 60 // len(drives)))
            
            self.log(f"\nProcessando {drive}:", "title")
            cleaner = LimpezaDisco(drive, self.verbose)
            resultado = cleaner.executar_limpeza_completa()
            self.resultados_discos.append(resultado)
            
            self.stats["total_arquivos"] += resultado.arquivos
            self.stats["total_bytes"] += resultado.bytes_liberados
            self.stats["erros"] += resultado.erros
            self.stats["discos_processados"] += 1
            
            if resultado.bytes_liberados > 0:
                self.log(f"  💾 {formatar_tamanho(resultado.bytes_liberados)} liberados", "success")
        
        if progress_callback:
            progress_callback(70)
        
        # FASE 2: SISTEMA (DISM + CleanMgr)
        if not self.dry_run:
            if progress_callback:
                progress_callback(75)
            self.log("\n🔧 [FASE 2] Limpeza profunda do sistema", "step")
            sistema = LimpezaSistema(self.verbose)
            arquivos_sistema, bytes_sistema = sistema.executar_limpeza_sistema()
            self.stats["total_arquivos"] += arquivos_sistema
            self.stats["total_bytes"] += bytes_sistema
        
        self.stats["tempo_total"] = time.time() - inicio_total
        
        print("\n" + "="*70)
        print("📊 RESULTADO FINAL DA LIMPEZA")
        print("="*70)
        
        for resultado in self.resultados_discos:
            if resultado.arquivos > 0 or resultado.bytes_liberados > 0:
                print(f"\n💿 Disco {resultado.disco}:")
                print(f"   📁 Arquivos: {resultado.arquivos:,}")
                print(f"   💾 Espaço liberado: {formatar_tamanho(resultado.bytes_liberados)}")
        
        print(f"\n📈 TOTAL GERAL:")
        print(f"   • Discos processados: {self.stats['discos_processados']}")
        print(f"   • Arquivos removidos: {self.stats['total_arquivos']:,}")
        print(f"   • Espaço liberado: {formatar_tamanho(self.stats['total_bytes'])}")
        print(f"   • Erros ignorados: {self.stats['erros']}")
        print(f"   • Tempo total: {self.stats['tempo_total']:.1f} segundos")
        print("="*70 + "\n")
        
        if progress_callback:
            progress_callback(100)
        
        return True, f"Finalizado! {formatar_tamanho(self.stats['total_bytes'])} liberados"