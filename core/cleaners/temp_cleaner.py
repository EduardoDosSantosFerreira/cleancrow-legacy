import os
import time
import subprocess
import ctypes
from pathlib import Path
from typing import List

from core.cleaners.base import BaseCleaner
from core.models import CleanerInfo, RiskLevel, Category, CleanerResult, formatar_tamanho


class TempCleaner(BaseCleaner):
    
    @property
    def info(self) -> CleanerInfo:
        return CleanerInfo(
            name="Temporarios do Usuario",
            description="Remove arquivos temporarios do usuario atual (e de todos os usuarios se admin)",
            category=Category.TEMPORARIOS,
            risk_level=RiskLevel.SEGURO,
            requires_admin=False,
            icon=""
        )
    
    def _get_targets(self) -> List[Path]:
        targets = []
        
        # Pasta temporária do usuário atual
        temp = os.environ.get('TEMP', '')
        if temp:
            targets.append(Path(temp))
        
        # Pasta Temp do LocalAppData
        local_appdata = os.environ.get('LOCALAPPDATA', '')
        if local_appdata:
            targets.append(Path(local_appdata) / 'Temp')
        
        # Se for admin, tenta limpar a pasta Temp de todos os usuários
        try:
            import ctypes
            if ctypes.windll.shell32.IsUserAnAdmin() != 0:
                users_base = Path('C:/Users')
                if users_base.exists():
                    for user_dir in users_base.iterdir():
                        if user_dir.is_dir() and user_dir.name not in ['Public', 'Default', 'Default User', 'All Users']:
                            user_temp = user_dir / 'AppData/Local/Temp'
                            if user_temp.exists() and user_temp != Path(temp):
                                targets.append(user_temp)
        except:
            pass
        
        return targets
    
    def _can_clean(self, path: Path) -> bool:
        return path.is_dir()
    
    def detect(self) -> bool:
        """
        Detecção realista: só retorna True se houver arquivos com mais de 1 hora de existência.
        Arquivos muito recentes geralmente estão em uso e não podem ser limpos.
        """
        for path in self._get_targets():
            if not path.exists():
                continue
            try:
                # Verifica se há arquivos com mais de 1 hora
                for item in path.iterdir():
                    try:
                        if item.is_file() and (time.time() - item.stat().st_mtime) > 3600:
                            return True
                    except:
                        pass
            except:
                pass
        return False
    
    def _agendar_exclusao(self, path: Path):
        """
        Agenda a exclusão de um arquivo para o próximo reinício.
        Usa a API do Windows MoveFileEx com MOVEFILE_DELAY_UNTIL_REBOOT.
        """
        try:
            # Constantes da API
            MOVEFILE_DELAY_UNTIL_REBOOT = 0x00000004
            MOVEFILE_REPLACE_EXISTING = 0x00000001
            
            # Converte o caminho para string
            file_path = str(path)
            
            # Chama a API
            result = ctypes.windll.kernel32.MoveFileExW(
                file_path,
                None,  # NULL significa deletar
                MOVEFILE_DELAY_UNTIL_REBOOT | MOVEFILE_REPLACE_EXISTING
            )
            
            return result != 0
        except:
            return False
    
    def clean(self) -> CleanerResult:
        start_time = time.time()
        result = CleanerResult(
            cleaner_name=self.info.name,
            success=True
        )
        
        # Tenta matar processos que usam a pasta TEMP (EXCETO o próprio Python!)
        try:
            for proc in ['chrome.exe', 'msedge.exe', 'firefox.exe']:
                try:
                    subprocess.run(
                        ['taskkill', '/f', '/im', proc],
                        capture_output=True,
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                except:
                    pass
        except:
            pass
        
        for path in self._get_targets():
            if not path.exists():
                continue
            
            if path.is_dir():
                self._log(f"Removendo arquivos de {path.name}...", "info")
                size_before = self._calculate_dir_size(path)
                self._log(f"  Tamanho detectado: {formatar_tamanho(size_before)}", "detail")
                
                files, folders, bytes_freed = self._remove_folder(path)
                result.files_removed += files
                result.folders_removed += folders
                result.bytes_freed += bytes_freed
                
                # Agenda exclusão dos arquivos que não puderam ser removidos (em uso)
                if bytes_freed < size_before:
                    self._log("  Alguns arquivos estao em uso. Agendando exclusao no proximo reinicio...", "warning")
                    try:
                        for item in path.rglob('*'):
                            if item.is_file():
                                try:
                                    # Tenta abrir para verificar se está bloqueado
                                    with open(item, 'r'):
                                        pass
                                except PermissionError:
                                    # Arquivo bloqueado, agenda exclusão
                                    if self._agendar_exclusao(item):
                                        # Não contabiliza como removido agora, mas será no reboot
                                        pass
                    except:
                        pass
                
                if not path.exists():
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                    except:
                        pass
                
                if bytes_freed > 0:
                    self._log(f"  Removido: {formatar_tamanho(bytes_freed)}", "success")
                else:
                    self._log("  Nenhum arquivo para remover", "info")
        
        result.duration_ms = (time.time() - start_time) * 1000
        self._last_result = result
        return result