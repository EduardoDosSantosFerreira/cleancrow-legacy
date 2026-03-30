import subprocess
import ctypes
import sys
import os
import time
import shutil
import glob
from pathlib import Path

class SistemaLimpeza:
    def __init__(self):
        self.verificar_e_solicitar_administrador()
        self.winget_path = self.encontrar_winget()
        print(f"Caminho do winget encontrado: {self.winget_path}")

    def verificar_e_solicitar_administrador(self):
        if not ctypes.windll.shell32.IsUserAnAdmin():
            MessageBox = ctypes.windll.user32.MessageBoxW
            MessageBox(
                None,
                "Este programa requer privilégios de administrador. Por favor, execute como administrador.",
                "Erro de Privacidade",
                0x10,
            )
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit(0)

    def encontrar_winget(self):
        """Encontra o caminho completo do winget"""
        possiveis_caminhos = [
            r"C:\Program Files\WindowsApps\Microsoft.DesktopAppInstaller_*_x64__8wekyb3d8bbwe\winget.exe",
            r"C:\Program Files\WindowsApps\*winget.exe",
            r"C:\Users\%USERNAME%\AppData\Local\Microsoft\WindowsApps\winget.exe",
            r"%LOCALAPPDATA%\Microsoft\WindowsApps\winget.exe",
        ]
        
        for caminho in possiveis_caminhos:
            caminho_expandido = os.path.expandvars(caminho)
            if "*" in caminho_expandido:
                try:
                    arquivos = glob.glob(caminho_expandido)
                    if arquivos:
                        arquivos.sort(key=os.path.getmtime, reverse=True)
                        return arquivos[0]
                except:
                    continue
            elif os.path.exists(caminho_expandido):
                return caminho_expandido
        return None

    def verificar_winget(self):
        """Verifica se o winget está disponível"""
        try:
            if self.winget_path and os.path.exists(self.winget_path):
                result = subprocess.run(
                    [self.winget_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    return True, result.stdout.strip()
            return False, "Winget não encontrado"
        except:
            return False, "Winget não encontrado"

    def atualizar_winget(self):
        """Tenta atualizar o winget antes de usar"""
        try:
            print("🔄 Tentando atualizar o winget...")
            
            # Tentar atualizar via Microsoft Store
            ps_script = '''
            $appxPackage = Get-AppxPackage -Name "*DesktopAppInstaller*"
            if ($appxPackage) {
                Write-Host "Atualizando winget via Microsoft Store..."
                $appxPackage | Select-Object -ExpandProperty InstallLocation
            }
            '''
            subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=30
            )
            time.sleep(5)
            return True
        except:
            return False

    def executar_comando_winget(self, comando, timeout=600):
        """Executa comando do winget com tratamento de erro 2316632108"""
        try:
            if not self.winget_path or not os.path.exists(self.winget_path):
                return -1, "", "Winget não encontrado"
            
            # Tentar executar com o caminho completo
            cmd = [self.winget_path] + comando
            
            # Adicionar flags para evitar erro de autenticação
            if "upgrade" in comando:
                if "--accept-package-agreements" not in cmd:
                    cmd.append("--accept-package-agreements")
                if "--accept-source-agreements" not in cmd:
                    cmd.append("--accept-source-agreements")
                # Flag para ignorar assinatura
                if "--disable-interactivity" not in cmd:
                    cmd.append("--disable-interactivity")
            
            print(f"Executando comando: {' '.join(cmd)}")
            
            # Executar comando
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Se erro 2316632108, tentar método alternativo
            if result.returncode == 2316632108 or result.returncode == -2147024773:
                print("⚠️ Erro de autenticação. Tentando método alternativo...")
                
                # Método alternativo: usar PowerShell com bypass
                ps_script = f'''
                $wingetPath = "{self.winget_path}"
                $command = "upgrade --all --accept-package-agreements --accept-source-agreements --disable-interactivity"
                & $wingetPath $command
                '''
                
                result = subprocess.run(
                    ["powershell", "-Command", ps_script],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout"
        except Exception as e:
            return -3, "", str(e)

    def executar_atualizacao_alternativa(self, progress_callback=None):
        """Método alternativo para atualização usando PowerShell"""
        try:
            if progress_callback:
                progress_callback(10)
            
            # Script PowerShell para atualizar usando winget
            ps_script = '''
            $ErrorActionPreference = "Continue"
            
            Write-Host "🔍 Verificando atualizações disponíveis..."
            
            # Tentar encontrar o winget
            $wingetPaths = @(
                "C:\\Program Files\\WindowsApps\\Microsoft.DesktopAppInstaller_*_x64__8wekyb3d8bbwe\\winget.exe",
                "$env:LOCALAPPDATA\\Microsoft\\WindowsApps\\winget.exe"
            )
            
            $wingetExe = $null
            foreach ($path in $wingetPaths) {
                $found = Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($found) {
                    $wingetExe = $found.FullName
                    break
                }
            }
            
            if (-not $wingetExe) {
                Write-Host "❌ Winget não encontrado"
                exit 1
            }
            
            Write-Host "✅ Winget encontrado em: $wingetExe"
            
            # Listar atualizações disponíveis
            Write-Host "📋 Listando atualizações disponíveis..."
            & $wingetExe upgrade --accept-source-agreements --disable-interactivity 2>&1 | Out-String
            
            Write-Host "🔄 Executando atualizações..."
            & $wingetExe upgrade --all --accept-package-agreements --accept-source-agreements --disable-interactivity 2>&1
            
            exit 0
            '''
            
            if progress_callback:
                progress_callback(30)
            
            print("🔄 Executando atualização via PowerShell...")
            
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=600,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if progress_callback:
                progress_callback(80)
            
            # Analisar saída
            output = result.stdout if result.stdout else ""
            error = result.stderr if result.stderr else ""
            
            print(f"Saída: {output[:500]}")
            if error:
                print(f"Erro: {error[:500]}")
            
            if "no updates available" in output.lower() or "nenhuma atualização disponível" in output.lower():
                if progress_callback:
                    progress_callback(100)
                return True, "✅ Sistema já está atualizado. Nenhuma atualização necessária."
            elif "upgraded" in output.lower() or "installed" in output.lower() or "sucesso" in output.lower():
                if progress_callback:
                    progress_callback(100)
                return True, "✅ Atualização concluída com sucesso!"
            elif result.returncode == 0:
                if progress_callback:
                    progress_callback(100)
                return True, "✅ Atualização executada com sucesso."
            else:
                if progress_callback:
                    progress_callback(100)
                return False, f"❌ Erro durante a atualização. Verifique os logs para mais detalhes."
                
        except Exception as e:
            if progress_callback:
                progress_callback(100)
            return False, f"❌ Erro inesperado: {str(e)}"

    def executar_atualizacao(self, progress_callback=None):
        """Executa atualização do sistema via winget"""
        try:
            if progress_callback:
                progress_callback(5)
            
            # Verificar winget
            winget_disponivel, versao = self.verificar_winget()
            
            if not winget_disponivel:
                print("⚠️ Winget não encontrado.")
                if progress_callback:
                    progress_callback(100)
                return False, "Winget não encontrado. Por favor, instale o Windows Package Manager da Microsoft Store."
            
            print(f"✅ Winget encontrado. Versão: {versao}")
            
            if progress_callback:
                progress_callback(20)
            
            # Tentar método principal
            print("🔄 Executando atualização via winget...")
            returncode, stdout, stderr = self.executar_comando_winget(
                ["upgrade", "--all"],
                timeout=600
            )
            
            if progress_callback:
                progress_callback(60)
            
            # Se falhar com erro específico, tentar método alternativo
            if returncode == 2316632108 or returncode == -2147024773:
                print("⚠️ Método principal falhou. Tentando método alternativo...")
                return self.executar_atualizacao_alternativa(progress_callback)
            
            # Analisar resultado
            if returncode == 0:
                output = stdout.lower() if stdout else ""
                if "no updates available" in output or "nenhuma atualização disponível" in output:
                    if progress_callback:
                        progress_callback(100)
                    return True, "✅ Sistema já está atualizado. Nenhuma atualização necessária."
                else:
                    if progress_callback:
                        progress_callback(100)
                    return True, "✅ Atualização concluída com sucesso!"
            else:
                # Se o método principal falhou, tentar o alternativo
                print("⚠️ Método principal falhou. Tentando método alternativo...")
                return self.executar_atualizacao_alternativa(progress_callback)
                
        except Exception as e:
            if progress_callback:
                progress_callback(100)
            return False, f"❌ Erro inesperado: {str(e)}"

    # ==================== MÉTODOS DE LIMPEZA (MANTIDOS) ====================
    
    def executar_limpeza(self, progress_callback=None):
        try:
            operacoes = [
                (self.limpar_temporarios, 2),
                (self.limpar_logs, 4),
                (self.limpar_update, 6),
                (self.limpar_dns, 8),
                (self.limpar_edge, 10),
                (self.limpar_edge_chromium, 12),
                (self.limpar_chrome, 14),
                (self.limpar_firefox, 16),
                (self.limpar_opera, 18),
                (self.limpar_brave, 20),
                (self.limpar_vivaldi, 22),
                (self.limpar_safari, 24),
                (self.limpar_tor, 26),
                (self.limpar_maxthon, 28),
                (self.limpar_waterfox, 30),
                (self.limpar_pale_moon, 32),
                (self.limpar_lixeira, 35),
                (self.limpar_arquivos_duplicados, 38),
                (self.limpar_cache_fontes_icones, 41),
                (self.limpar_miniaturas, 44),
                (self.limpar_dumps_memoria, 47),
                (self.limpar_relatorios_erros, 50),
                (self.limpar_logs_windows_update, 53),
                (self.limpar_instaladores_antigos, 56),
                (self.limpar_reciclaveis_sistema, 59),
                (self.limpar_cache_loja_windows, 62),
                (self.limpar_temp_adicional, 65),
                (self.limpar_espaco_disco, 68),
                (self.limpar_desnecessarios, 71),
                (self.limpar_atualizacao, 74),
                (self.remover_programas, 77),
                (self.remover_bloatware, 80),
                (self.compactar_sistema, 83),
                (self.desativar_hibernacao, 86),
                (self.desabilitar_inicializacao, 89),
                (self.otimizar_desligamento, 92),
                (self.reiniciar_servicos_essenciais, 95),
                (self.fechar_microsoft_store, 98),
                (self.limpar_cache_windows_update, 99),
                (self.limpar_defender_antivirus, 100),
                (self.limpar_arquivos_otimizacao, 101),
                (self.limpar_temp_internet, 102),
                (self.limpar_arquivos_windows, 103),
                (self.verificar_disco, 105),
            ]
            
            total_operacoes = len(operacoes)
            for idx, (operacao, progresso) in enumerate(operacoes):
                try:
                    operacao()
                    if progress_callback:
                        progresso_calculado = int((idx + 1) / total_operacoes * 100)
                        progress_callback(progresso_calculado)
                except Exception as e:
                    print(f"Erro na operação: {e}")
                    continue

            return True, "Limpeza concluída com sucesso!"
        except Exception as e:
            return False, f"Erro durante a limpeza: {str(e)}"

    # ==================== MÉTODOS DE LIMPEZA (CONTINUAÇÃO) ====================
    
    def limpar_cache_windows_update(self):
        try:
            update_paths = [
                "C:\\Windows\\SoftwareDistribution\\Download\\*",
                "C:\\Windows\\SoftwareDistribution\\DeliveryOptimization\\*",
                "C:\\Windows\\Logs\\WindowsUpdate\\*"
            ]
            for path in update_paths:
                subprocess.run(["cmd", "/c", f"del /q/f/s {path}"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("Cache de atualizações do Windows limpo")
        except:
            pass

    def limpar_defender_antivirus(self):
        try:
            defender_paths = [
                "C:\\ProgramData\\Microsoft\\Windows Defender\\Scans\\History\\*",
                "C:\\ProgramData\\Microsoft\\Windows Defender\\Scans\\mpcache-*",
                "C:\\ProgramData\\Microsoft\\Windows Defender\\LocalCopy\\*"
            ]
            for path in defender_paths:
                subprocess.run(["cmd", "/c", f"del /q/f/s {path}"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("Arquivos do Defender limpos")
        except:
            pass

    def limpar_arquivos_otimizacao(self):
        try:
            delivery_paths = [
                "C:\\Windows\\ServiceProfiles\\NetworkService\\AppData\\Local\\Microsoft\\Windows\\DeliveryOptimization\\*",
                "C:\\Windows\\ServiceProfiles\\LocalService\\AppData\\Local\\Microsoft\\Windows\\DeliveryOptimization\\*"
            ]
            for path in delivery_paths:
                subprocess.run(["cmd", "/c", f"del /q/f/s {path}"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("Arquivos de otimização limpos")
        except:
            pass

    def limpar_temp_internet(self):
        try:
            internet_paths = [
                "%USERPROFILE%\\AppData\\Local\\Microsoft\\Windows\\INetCache\\*",
                "%USERPROFILE%\\AppData\\Local\\Microsoft\\Windows\\INetCookies\\*",
                "%USERPROFILE%\\AppData\\Local\\Microsoft\\Windows\\History\\*"
            ]
            for path in internet_paths:
                subprocess.run(["cmd", "/c", f"del /q/f/s {path}"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("Arquivos temporários da internet limpos")
        except:
            pass

    def limpar_arquivos_windows(self):
        try:
            windows_paths = [
                "C:\\Windows\\Prefetch\\*",
                "C:\\Windows\\System32\\config\\systemprofile\\AppData\\Local\\Temp\\*",
                "C:\\Windows\\System32\\config\\systemprofile\\AppData\\Local\\Microsoft\\Windows\\WER\\*",
                "C:\\Windows\\System32\\config\\systemprofile\\AppData\\Local\\CrashDumps\\*"
            ]
            for path in windows_paths:
                subprocess.run(["cmd", "/c", f"del /q/f/s {path}"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("Arquivos extras do Windows limpos")
        except:
            pass

    def limpar_temporarios(self):
        temp_locations = [
            "%TEMP%\\*", "C:\\Windows\\Temp\\*", "C:\\Windows\\Prefetch\\*",
            "%USERPROFILE%\\AppData\\Local\\Temp\\*", "%USERPROFILE%\\AppData\\LocalLow\\Temp\\*",
            "C:\\Windows\\Logs\\*", "C:\\Windows\\System32\\LogFiles\\*"
        ]
        for location in temp_locations:
            try:
                subprocess.run(["cmd", "/c", f"del /q/f/s {location}"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            except:
                pass
        print("Arquivos temporários limpos com sucesso!")

    def limpar_logs(self):
        try:
            logs = ["Application", "Security", "System", "Setup", "Windows PowerShell"]
            for log in logs:
                subprocess.run(["wevtutil.exe", "cl", log], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("Logs do sistema limpos com sucesso!")
        except:
            pass

    def limpar_update(self):
        try:
            subprocess.run(["net", "stop", "wuauserv"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["net", "stop", "bits"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["rd", "/s", "/q", "%windir%\\SoftwareDistribution"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["net", "start", "wuauserv"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["net", "start", "bits"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("Cache do Windows Update limpo com sucesso!")
        except:
            pass

    def limpar_dns(self):
        subprocess.run(["ipconfig", "/flushdns"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        print("Cache DNS limpo com sucesso!")

    def limpar_edge(self):
        subprocess.run(["RunDll32.exe", "InetCpl.cpl,ClearMyTracksByProcess", "255"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        print("Cache do Edge limpo com sucesso!")

    def limpar_edge_chromium(self):
        edge_paths = [
            "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Cache\\*",
            "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Code Cache\\*",
        ]
        for path in edge_paths:
            self._clean_path(path)
        print("Cache do Edge Chromium limpo com sucesso!")

    def _clean_path(self, path):
        try:
            subprocess.run(["cmd", "/c", f"del /q/f/s {path}"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass

    def limpar_chrome(self):
        chrome_paths = [
            "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cache\\*",
            "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Code Cache\\*",
        ]
        for path in chrome_paths:
            self._clean_path(path)
        print("Cache do Chrome limpo com sucesso!")

    def limpar_firefox(self):
        try:
            subprocess.run(["cmd", "/c", 'rd /s /q "%APPDATA%\\Mozilla\\Firefox\\Profiles\\*.default-release\\cache2"'], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("Cache do Firefox limpo com sucesso!")
        except:
            pass

    def limpar_opera(self):
        try:
            subprocess.run(["cmd", "/c", 'rd /s /q "%APPDATA%\\Opera Software\\Opera Stable\\Cache"'], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("Cache do Opera limpo com sucesso!")
        except:
            pass

    def limpar_brave(self):
        brave_paths = [
            "%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Cache\\*",
            "%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Code Cache\\*",
        ]
        for path in brave_paths:
            self._clean_path(path)
        print("Cache do Brave limpo com sucesso!")

    def limpar_vivaldi(self):
        self._clean_path("%LOCALAPPDATA%\\Vivaldi\\User Data\\Default\\Cache\\*")
        self._clean_path("%LOCALAPPDATA%\\Vivaldi\\User Data\\Default\\Code Cache\\*")
        print("Cache do Vivaldi limpo com sucesso!")

    def limpar_safari(self):
        try:
            subprocess.run(["cmd", "/c", 'rd /s /q "%APPDATA%\\Apple Computer\\Safari\\Cache"'], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("Cache do Safari limpo com sucesso!")
        except:
            pass

    def limpar_tor(self):
        try:
            subprocess.run(["cmd", "/c", 'rd /s /q "%APPDATA%\\Tor Browser\\Browser\\Caches"'], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("Cache do Tor Browser limpo com sucesso!")
        except:
            pass

    def limpar_maxthon(self):
        try:
            subprocess.run(["cmd", "/c", 'rd /s /q "%APPDATA%\\Maxthon3\\Cache"'], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("Cache do Maxthon limpo com sucesso!")
        except:
            pass

    def limpar_waterfox(self):
        try:
            subprocess.run(["cmd", "/c", 'rd /s /q "%APPDATA%\\Waterfox\\Profiles\\*.default-release\\cache2"'], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("Cache do Waterfox limpo com sucesso!")
        except:
            pass

    def limpar_pale_moon(self):
        try:
            subprocess.run(["cmd", "/c", 'rd /s /q "%APPDATA%\\Moonchild Productions\\Pale Moon\\Profiles\\*.default\\cache2"'], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("Cache do Pale Moon limpo com sucesso!")
        except:
            pass

    def limpar_lixeira(self):
        try:
            ps_script = '''
            $Recycler = New-Object -ComObject Shell.Application
            $Recycler.Namespace(0xA).Items() | ForEach-Object { $_.InvokeVerb("delete") }
            Clear-RecycleBin -Force -ErrorAction SilentlyContinue
            '''
            subprocess.run(["powershell", "-Command", ps_script], creationflags=subprocess.CREATE_NO_WINDOW, timeout=30)
            drives = [f"{chr(d)}:" for d in range(65, 91) if os.path.exists(f"{chr(d)}:")]
            for drive in drives:
                recycle_path = f"{drive}\\$Recycle.Bin"
                if os.path.exists(recycle_path):
                    shutil.rmtree(recycle_path, ignore_errors=True)
            print("Lixeira esvaziada com sucesso!")
        except:
            pass

    def limpar_arquivos_duplicados(self):
        try:
            ps_script = '''
            Get-ChildItem -Path C:\\ -Recurse -Filter *.tmp -ErrorAction SilentlyContinue | 
            Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | 
            Remove-Item -Force -ErrorAction SilentlyContinue
            '''
            subprocess.run(["powershell", "-Command", ps_script], creationflags=subprocess.CREATE_NO_WINDOW, timeout=60)
            print("Arquivos duplicados e antigos removidos com sucesso!")
        except:
            pass

    def limpar_cache_fontes_icones(self):
        subprocess.run(["cmd", "/c", "ie4uinit.exe -show"], creationflags=subprocess.CREATE_NO_WINDOW)
        self._clean_path("%LOCALAPPDATA%\\Microsoft\\Windows\\Fonts\\*")
        print("Cache de fontes e ícones limpo com sucesso!")

    def limpar_miniaturas(self):
        self._clean_path("%LOCALAPPDATA%\\Microsoft\\Windows\\Explorer\\thumbcache_*")
        print("Cache de miniaturas limpo com sucesso!")

    def limpar_dumps_memoria(self):
        self._clean_path("C:\\Windows\\Minidump\\*")
        self._clean_path("C:\\Windows\\MEMORY.DMP")
        print("Dumps de memória limpos com sucesso!")

    def limpar_relatorios_erros(self):
        self._clean_path("C:\\ProgramData\\Microsoft\\Windows\\WER\\*")
        print("Relatórios de erro limpos com sucesso!")

    def limpar_logs_windows_update(self):
        self._clean_path("%windir%\\Logs\\WindowsUpdate\\*")
        self._clean_path("%windir%\\WindowsUpdate.log")
        print("Logs do Windows Update limpos com sucesso!")

    def limpar_instaladores_antigos(self):
        self._clean_path("C:\\Windows\\Installer\\*.tmp")
        self._clean_path("C:\\Windows\\SoftwareDistribution\\Download\\*")
        print("Instaladores antigos removidos com sucesso!")

    def limpar_reciclaveis_sistema(self):
        recyclable_paths = [
            "C:\\Windows\\System32\\config\\systemprofile\\AppData\\Local\\Microsoft\\Windows\\WER\\*",
            "C:\\Windows\\System32\\config\\systemprofile\\AppData\\Local\\CrashDumps\\*",
            "C:\\ProgramData\\Microsoft\\Windows\\WER\\*",
        ]
        for path in recyclable_paths:
            self._clean_path(path)
        print("Arquivos recicláveis do sistema removidos com sucesso!")

    def limpar_cache_loja_windows(self):
        try:
            subprocess.run(["taskkill", "/f", "/im", "WinStore.App.exe"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            cache_paths = [
                "%LOCALAPPDATA%\\Packages\\Microsoft.WindowsStore_8wekyb3d8bbwe\\LocalCache",
                "%LOCALAPPDATA%\\Packages\\Microsoft.WindowsStore_8wekyb3d8bbwe\\LocalState\\Cache",
            ]
            for path in cache_paths:
                subprocess.run(["cmd", "/c", f"rd /s /q {path}"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("Cache da Microsoft Store limpo com sucesso!")
        except:
            pass

    def limpar_temp_adicional(self):
        self._clean_path("%USERPROFILE%\\AppData\\Local\\Temp\\*")
        self._clean_path("%USERPROFILE%\\AppData\\LocalLow\\Temp\\*")
        self._clean_path("C:\\Windows\\Temp\\*")
        print("Temporários adicionais limpos com sucesso!")

    def limpar_espaco_disco(self):
        try:
            subprocess.run(["cleanmgr", "/sagerun:1"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("Limpeza de disco executada com sucesso!")
        except:
            pass

    def limpar_desnecessarios(self):
        subprocess.run(["dism", "/online", "/cleanup-image", "/startcomponentcleanup"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        print("Componentes desnecessários removidos com sucesso!")

    def limpar_atualizacao(self):
        subprocess.run(["dism", "/online", "/cleanup-image", "/spsuperseded", "/hidesp"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        print("Atualizações antigas removidas com sucesso!")

    def remover_programas(self):
        try:
            subprocess.run("where FlashUtil*.exe", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run("FlashUtil*.exe -uninstall", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("Programas desnecessários removidos com sucesso!")
        except:
            pass

    def remover_bloatware(self):
        bloatware_list = [
            "Microsoft.3DBuilder", "Microsoft.BingWeather", "Microsoft.MicrosoftSolitaireCollection",
            "Microsoft.MicrosoftOfficeHub", "Microsoft.GetHelp", "Microsoft.Getstarted",
            "Microsoft.Microsoft3DViewer", "Microsoft.OneConnect", "Microsoft.People",
            "Microsoft.SkypeApp", "Microsoft.WindowsAlarms", "Microsoft.WindowsCamera",
            "Microsoft.WindowsMaps", "Microsoft.XboxApp", "Microsoft.XboxIdentityProvider"
        ]
        for app in bloatware_list:
            try:
                subprocess.run(["powershell", "-Command", f"Get-AppxPackage {app} | Remove-AppxPackage"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except:
                pass
        print("Bloatware removido com sucesso!")

    def compactar_sistema(self):
        subprocess.run(["compact", "/compactos:always", "/exe"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        print("Sistema compactado com sucesso!")

    def desativar_hibernacao(self):
        subprocess.run(["powercfg", "-h", "off"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        print("Hibernação desativada com sucesso!")

    def desabilitar_inicializacao(self):
        subprocess.run(["reg", "add", '"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"', "/v", '"UnwantedProgram"', "/f"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        print("Programas da inicialização desabilitados com sucesso!")

    def otimizar_desligamento(self):
        reg_settings = [
            ('"HKCU\\Control Panel\\Desktop"', '"WaitToKillAppTimeout"', "2000"),
            ('"HKCU\\Control Panel\\Desktop"', '"HungAppTimeout"', "1000"),
            ('"HKLM\\SYSTEM\\CurrentControlSet\\Control"', '"WaitToKillServiceTimeout"', "2000"),
        ]
        for path, key, value in reg_settings:
            subprocess.run(["reg", "add", path, "/v", key, "/t", "REG_SZ", "/d", f'"{value}"', "/f"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        print("Tempo de desligamento otimizado com sucesso!")

    def reiniciar_servicos_essenciais(self):
        services = ["wuauserv", "bits", "Dnscache"]
        for service in services:
            subprocess.run(["net", "start", service], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        print("Serviços essenciais reiniciados com sucesso!")

    def fechar_microsoft_store(self):
        store_processes = ["WinStore.App.exe", "WWAHost.exe", "Microsoft.StorePurchaseApp.exe"]
        for process in store_processes:
            subprocess.run(f'taskkill /f /im "{process}"', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        print("Microsoft Store fechada com sucesso!")

    def verificar_disco(self):
        try:
            p = subprocess.Popen(["chkdsk", "C:", "/f", "/r", "/x"], stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
            p.communicate(input=b"y\n", timeout=5)
            print("Verificação de disco agendada para a próxima reinicialização!")
        except:
            pass

    def desfragmentar_disco(self):
        subprocess.run(["defrag", "C:", "/O"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        print("Disco desfragmentado com sucesso!")


if __name__ == "__main__":
    limpeza = SistemaLimpeza()
    
    print("🔄 Testando sistema de atualização...")
    
    def mostrar_progresso(valor):
        print(f"📊 Progresso: {valor}%")
    
    sucesso, mensagem = limpeza.executar_atualizacao(mostrar_progresso)
    print(f"\nResultado: {mensagem}")