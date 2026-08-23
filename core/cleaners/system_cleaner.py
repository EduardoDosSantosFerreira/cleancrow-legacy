import os
import subprocess
import time
import winreg
import shutil
from pathlib import Path
from typing import List

from core.cleaners.base import BaseCleaner
from core.models import CleanerInfo, RiskLevel, Category, CleanerResult, formatar_tamanho  # Import adicionado


class SystemCleaner(BaseCleaner):
    
    @property
    def info(self) -> CleanerInfo:
        return CleanerInfo(
            name="Limpeza Avancada do Sistema",
            description="Remove arquivos do sistema usando cleanmgr e DISM",
            category=Category.SISTEMA,
            risk_level=RiskLevel.AVANCADO,
            requires_admin=True,
            icon=""
        )
    
    def _get_targets(self) -> List[Path]:
        return []
    
    def _can_clean(self, path: Path) -> bool:
        return False
    
    def detect(self) -> bool:
        return True
    
    def calculate_size(self) -> int:
        total = 0
        try:
            defender_path = Path('C:/ProgramData/Microsoft/Windows Defender/Scans/History/Service')
            if defender_path.exists():
                total += self._calculate_dir_size(defender_path)
        except:
            pass
        
        try:
            do_path = Path('C:/Windows/ServiceProfiles/NetworkService/AppData/Local/Microsoft/Windows/DeliveryOptimization/Cache')
            if do_path.exists():
                total += self._calculate_dir_size(do_path)
        except:
            pass
        
        try:
            dx_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'D3DSCache'
            if dx_path.exists():
                total += self._calculate_dir_size(dx_path)
        except:
            pass
        
        return total
    
    def _configure_cleanmgr(self) -> bool:
        try:
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches"
            
            categorias = [
                ("Active Setup Temp Folders", 2),
                ("Downloaded Program Files", 2),
                ("Internet Cache Files", 2),
                ("Memory Dumps", 2),
                ("Microsoft Defender", 2),
                ("Previous Installations", 2),
                ("Recycle Bin", 2),
                ("Setup Log Files", 2),
                ("System error memory dump files", 2),
                ("System error minidump files", 2),
                ("Temporary Files", 2),
                ("Temporary Setup Files", 2),
                ("Thumbnail Cache", 2),
                ("Update Cleanup", 2),
                ("Windows Defender", 2),
                ("Windows Error Reports", 2),
                ("Windows Upgrade Log Files", 2),
                ("Delivery Optimization Files", 2)
            ]
            
            configured = 0
            for cat, value in categorias:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, f"{key_path}\\{cat}", 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, "StateFlags0001", 0, winreg.REG_DWORD, value)
                    winreg.CloseKey(key)
                    configured += 1
                except:
                    try:
                        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, f"{key_path}\\{cat}")
                        winreg.SetValueEx(key, "StateFlags0001", 0, winreg.REG_DWORD, value)
                        winreg.CloseKey(key)
                        configured += 1
                    except:
                        pass
            
            self._log(f"  {configured} categorias configuradas", "detail")
            return True
        except Exception as e:
            self._log(f"  Erro ao configurar cleanmgr: {e}", "error")
            return False
    
    def clean(self) -> CleanerResult:
        result = CleanerResult(
            cleaner_name=self.info.name,
            success=True
        )
        
        if self.dry_run:
            result.bytes_freed = self.calculate_size()
            return result
        
        bytes_freed_total = 0
        
        self._log("=" * 50, "system")
        self._log("INICIANDO LIMPEZA AVANCADA DO SISTEMA", "system")
        self._log("=" * 50, "system")
        
        # Verifica permissoes
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            self._log(f"  Permissao: {'Administrador' if is_admin else 'Usuario comum'}", "info")
            if not is_admin:
                self._log("  ATENCAO: Execute como Administrador para melhores resultados!", "warning")
        except:
            self._log("  Nao foi possivel verificar permissoes", "warning")
        
        # CALCULA TAMANHO ANTES
        self._log("\n[1/6] Calculando espaco antes da limpeza...", "step")
        size_before = self.calculate_size()
        if size_before > 0:
            self._log(f"  Espaco detectado: {formatar_tamanho(size_before)}", "info")
        else:
            self._log("  Nenhum arquivo pendente para limpeza", "info")
        
        # ============================================================
        # CONFIGURAR CLEANMGR
        # ============================================================
        self._log("\n[2/6] Configurando Limpeza de Disco do Windows...", "step")
        self._log("  Registrando configuracoes no Windows...", "detail")
        try:
            self._configure_cleanmgr()
            self._log("  Limpeza de Disco configurada com sucesso", "success")
        except Exception as e:
            self._log(f"  Erro ao configurar: {e}", "error")
            self._log("  Continuando mesmo assim...", "warning")
        
        # ============================================================
        # EXECUTAR CLEANMGR
        # ============================================================
        MAX_WAIT_SECONDS = 600  # 10 minutos
        STUCK_THRESHOLD = 120   # 2 minutos sem progresso
        MIN_SIZE_TO_WATCH = 10 * 1024 * 1024  # 10 MB - se já estiver limpo, não monitora
        
        self._log("\n[3/6] Executando Limpeza de Disco do Windows...", "step")
        self._log(f"  Tempo maximo: {MAX_WAIT_SECONDS/60} minutos", "info")
        
        # Se já está limpo, avisa e continua
        if size_before < MIN_SIZE_TO_WATCH:
            self._log("  Sistema ja esta limpo. Pulando Limpeza de Disco.", "info")
        else:
            self._log("  ATENCAO: O Windows abrira uma janela do Limpeza de Disco.", "warning")
            self._log("  Isso e normal e nao requer acao do usuario.", "info")
            self._log("  Aguarde... a janela fechara automaticamente.", "info")
        
        cleanmgr_success = False
        cleanmgr_timeout = False
        cleanmgr_stuck = False
        cleanmgr_started = False
        
        # Só executa se houver algo para limpar
        if size_before >= MIN_SIZE_TO_WATCH:
            try:
                start_time = time.time()
                last_progress_time = start_time
                last_size = size_before
                
                self._log("  Iniciando processo...", "detail")
                
                # Executa o cleanmgr
                process = subprocess.Popen(
                    ['cleanmgr', '/sagerun:1'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self._log("  Processo iniciado. Aguardando conclusao...", "info")
                cleanmgr_started = True
                
                # Aguarda o cleanmgr terminar ou timeout
                while cleanmgr_started:
                    # Verifica se o processo ainda esta rodando
                    check = subprocess.run(
                        ['tasklist', '/fi', 'imagename eq cleanmgr.exe'],
                        capture_output=True,
                        text=True,
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    if 'cleanmgr.exe' not in check.stdout:
                        # Processo ja terminou
                        self._log("  Limpeza de Disco concluida", "success")
                        cleanmgr_success = True
                        break
                    
                    elapsed = time.time() - start_time
                    
                    # TIMEOUT
                    if elapsed > MAX_WAIT_SECONDS:
                        self._log(f"  ATENCAO: Limpeza excedeu {MAX_WAIT_SECONDS/60} minutos!", "warning")
                        self._log("  Finalizando processo forcadamente...", "warning")
                        subprocess.run(['taskkill', '/f', '/im', 'cleanmgr.exe'], 
                                     capture_output=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                        self._log("  Processo finalizado.", "warning")
                        cleanmgr_timeout = True
                        result.errors.append("cleanmgr: timeout (10 minutos)")
                        break
                    
                    # DETECCAO DE TRAVAMENTO - só monitora se ainda tem muito para limpar
                    current_size = self.calculate_size()
                    if current_size < last_size:
                        # Progresso detectado!
                        progress = last_size - current_size
                        last_progress_time = time.time()
                        last_size = current_size
                        self._log(f"  Progresso detectado: {formatar_tamanho(progress)} removidos", "detail")
                    elif current_size < MIN_SIZE_TO_WATCH:
                        # Já está limpo, pode terminar
                        self._log("  Sistema ja esta limpo. Finalizando...", "info")
                        subprocess.run(['taskkill', '/f', '/im', 'cleanmgr.exe'], 
                                     capture_output=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                        cleanmgr_success = True
                        break
                    elif (time.time() - last_progress_time) > STUCK_THRESHOLD:
                        # Travado! Mais de 2 minutos sem progresso
                        self._log(f"  ATENCAO: Processo parece travado (sem progresso ha {STUCK_THRESHOLD}s)", "warning")
                        self._log("  Finalizando processo para nao travar o programa...", "warning")
                        subprocess.run(['taskkill', '/f', '/im', 'cleanmgr.exe'], 
                                     capture_output=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                        self._log("  Processo finalizado.", "warning")
                        cleanmgr_stuck = True
                        result.errors.append("cleanmgr: travado")
                        break
                    
                    # MOSTRA TEMPO DECORRIDO
                    if elapsed > 30 and elapsed % 30 == 0:
                        self._log(f"  Aguardando... {elapsed:.0f} segundos decorridos", "detail")
                    
                    time.sleep(5)
                
                if cleanmgr_success:
                    self._log("  Limpeza de Disco concluida com sucesso!", "success")
                    
            except Exception as e:
                self._log(f"  ERRO ao executar Limpeza de Disco: {e}", "error")
                self._log("  Continuando com as proximas etapas...", "warning")
                result.errors.append(f"cleanmgr: {e}")
        else:
            self._log("  Pulando Limpeza de Disco (sistema ja esta limpo)", "info")
            cleanmgr_success = True
        
        # ============================================================
        # REMOVER DIRECTX SHADER CACHE
        # ============================================================
        self._log("\n[4/6] Removendo DirectX Shader Cache...", "step")
        try:
            dx_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'D3DSCache'
            if dx_path.exists():
                size_before_dx = self._calculate_dir_size(dx_path)
                self._log(f"  Tamanho detectado: {formatar_tamanho(size_before_dx)}", "detail")
                
                files, folders, bytes_freed = self._remove_folder(dx_path)
                result.files_removed += files
                result.folders_removed += folders
                
                if not dx_path.exists():
                    dx_path.mkdir(parents=True, exist_ok=True)
                
                if bytes_freed > 0:
                    self._log(f"  Removido: {formatar_tamanho(bytes_freed)}", "success")
                else:
                    self._log("  Nenhum arquivo para remover", "info")
            else:
                self._log("  Pasta nao encontrada", "info")
        except Exception as e:
            self._log(f"  Erro: {e}", "error")
            self._log("  Continuando...", "warning")
            result.errors.append(f"DirectX Shader: {e}")
        
        # ============================================================
        # CALCULAR O QUE FOI LIMPO
        # ============================================================
        self._log("\n[5/6] Calculando resultado da limpeza...", "step")
        size_after = self.calculate_size()
        bytes_freed_cleanmgr = size_before - size_after
        
        if bytes_freed_cleanmgr > 0:
            self._log(f"  Limpeza de Disco liberou: {formatar_tamanho(bytes_freed_cleanmgr)}", "success")
        else:
            if cleanmgr_timeout:
                self._log("  Limpeza de Disco foi interrompida por timeout.", "warning")
                self._log("  Tente executar novamente ou use o Limpeza de Disco manualmente.", "info")
            elif cleanmgr_stuck:
                self._log("  Limpeza de Disco foi interrompida por travamento.", "warning")
                self._log("  Isso pode indicar arquivos corrompidos no cache do sistema.", "info")
            else:
                self._log("  Limpeza de Disco: nenhum arquivo para remover", "info")
        
        # ============================================================
        # EXECUTAR DISM
        # ============================================================
        self._log("\n[6/6] Executando Windows Update Cleanup (DISM)...", "step")
        self._log("  Isso pode levar alguns minutos...", "info")
        
        try:
            start_time = time.time()
            
            process = subprocess.Popen(
                ['dism', '/online', '/cleanup-image', '/startcomponentcleanup'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            self._log("  Processo iniciado. Aguardando...", "detail")
            
            while process.poll() is None:
                elapsed = time.time() - start_time
                if elapsed > 30 and elapsed % 30 == 0:
                    self._log(f"  Aguardando DISM... {elapsed:.0f} segundos", "detail")
                time.sleep(5)
            
            stdout, stderr = process.communicate()
            elapsed = time.time() - start_time
            self._log(f"  DISM finalizado em {elapsed:.1f} segundos", "info")
            
            if process.returncode == 0:
                self._log("  DISM concluido com sucesso!", "success")
            else:
                self._log(f"  DISM retornou codigo {process.returncode}", "warning")
                if stderr:
                    self._log(f"  Detalhe: {stderr[:200]}", "detail")
                
        except subprocess.TimeoutExpired:
            self._log("  ATENCAO: DISM excedeu o tempo limite!", "warning")
            self._log("  Continuando mesmo assim...", "warning")
            result.errors.append("DISM timeout")
        except Exception as e:
            self._log(f"  Erro no DISM: {e}", "error")
            self._log("  Continuando...", "warning")
            result.errors.append(f"DISM: {e}")
        
        # ============================================================
        # RESUMO FINAL
        # ============================================================
        total_bytes_freed = bytes_freed_cleanmgr
        
        self._log("\n" + "=" * 50, "system")
        self._log("RESUMO DA LIMPEZA AVANCADA DO SISTEMA", "system")
        self._log("=" * 50, "system")
        self._log(f"  Limpeza de Disco: {formatar_tamanho(bytes_freed_cleanmgr)}", "info")
        self._log(f"  DirectX Shader: {formatar_tamanho(result.bytes_freed)}", "info")
        self._log(f"  Total liberado: {formatar_tamanho(total_bytes_freed)}", "success")
        
        if result.errors:
            self._log(f"  Avisos/Erros: {len(result.errors)}", "warning")
            for i, err in enumerate(result.errors, 1):
                self._log(f"    {i}. {err}", "detail")
        
        if cleanmgr_timeout:
            self._log("  OBS: A Limpeza de Disco foi interrompida por timeout.", "warning")
            self._log("  Execute novamente para tentar limpar o restante.", "info")
        elif cleanmgr_stuck:
            self._log("  OBS: A Limpeza de Disco travou e foi interrompida.", "warning")
            self._log("  Isso pode indicar arquivos corrompidos no cache do sistema.", "info")
        elif cleanmgr_success:
            self._log("  OBS: Limpeza de Disco concluida com sucesso.", "success")
        
        self._log("=" * 50, "system")
        
        result.bytes_freed = total_bytes_freed
        return result