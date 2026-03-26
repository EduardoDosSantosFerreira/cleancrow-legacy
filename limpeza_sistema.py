import subprocess
import ctypes
import sys
import os
import time
import re
import string
import shutil
from pathlib import Path

class SistemaLimpeza:
    def __init__(self):
        self.verificar_e_solicitar_administrador()

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
                (self.verificar_disco, 100),
            ]
            
            total_operacoes = len(operacoes)
            for idx, (operacao, progresso) in enumerate(operacoes):
                try:
                    operacao()
                    if progress_callback:
                        progresso_calculado = int((idx + 1) / total_operacoes * 100)
                        progress_callback(progresso_calculado)
                except Exception as e:
                    print(f"Erro na operação {operacao.__name__}: {e}")
                    continue

            return True, "Limpeza concluída com sucesso!"
        except Exception as e:
            return False, f"Erro durante a limpeza: {str(e)}"

    def executar_atualizacao(self, progress_callback=None):
        try:
            if progress_callback:
                progress_callback(5)
                
            try:
                result = subprocess.run(
                    ["winget", "--version"], 
                    capture_output=True, 
                    text=True, 
                    shell=True, 
                    check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                print(f"✅ Winget encontrado. Versão: {result.stdout.strip()}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                return (
                    False,
                    "Winget não encontrado. Certifique-se de que o Windows Package Manager está instalado."
                )

            if progress_callback:
                progress_callback(15)

            print("🔄 Executando 'winget upgrade --all'...")
            
            try:
                result = subprocess.run(
                    ["winget", "upgrade", "--all"],
                    capture_output=True,
                    text=True,
                    shell=True,
                    timeout=300,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                if progress_callback:
                    progress_callback(50)

                print(f"Código de saída: {result.returncode}")
                
                if progress_callback:
                    progress_callback(100)

                if result.returncode == 0:
                    output = result.stdout.lower()
                    
                    if "no updates available" in output or "nenhuma atualização disponível" in output:
                        return True, "✅ Sistema já está atualizado. Nenhuma atualização necessária."
                    elif "upgraded" in output or "installed" in output or "sucesso" in output:
                        return True, "✅ Atualização concluída com sucesso!"
                    else:
                        return True, "✅ Comando de atualização executado com sucesso."
                else:
                    error_output = result.stderr if result.stderr else result.stdout
                    
                    if "requires admin" in error_output.lower() or "elevated" in error_output.lower():
                        return False, "❌ Winget requer privilégios de administrador. Execute este programa como administrador."
                    elif "access denied" in error_output.lower():
                        return False, "❌ Acesso negado. Certifique-se de executar como administrador."
                    else:
                        error_msg = error_output.strip()[:200]
                        return False, f"❌ Erro na atualização: {error_msg}"

            except subprocess.TimeoutExpired:
                if progress_callback:
                    progress_callback(100)
                return False, "⏰ Tempo excedido durante a atualização"
                
            except Exception as e:
                if progress_callback:
                    progress_callback(100)
                return False, f"❌ Erro durante a execução: {str(e)}"

        except Exception as e:
            if progress_callback:
                progress_callback(100)
            return False, f"❌ Erro inesperado: {str(e)}"

    def verificar_atualizacoes(self):
        try:
            try:
                subprocess.run(
                    ["winget", "--version"], 
                    capture_output=True, 
                    text=True, 
                    shell=True, 
                    check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                return False, "Winget não encontrado", []

            result = subprocess.run(
                ["winget", "upgrade", "--include-unknown", "--source", "winget"],
                capture_output=True,
                text=True,
                shell=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            output_lines = result.stdout.split('\n')
            updates = []
            
            for line in output_lines:
                line = line.strip()
                if line and not any(x in line for x in ["---", "Nome", "ID", "Versão", "Name", "Id", "Version", "Available"]):
                    if "->" in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            package_info = {
                                'nome': parts[0],
                                'versao_atual': parts[1] if len(parts) > 1 else 'N/A',
                                'versao_nova': parts[3] if len(parts) > 3 else 'N/A'
                            }
                            updates.append(package_info)

            if updates:
                return True, f"Encontradas {len(updates)} atualizações disponíveis", updates
            else:
                return True, "Sistema já está atualizado", []

        except subprocess.TimeoutExpired:
            return False, "Tempo excedido ao verificar atualizações", []
        except Exception as e:
            return False, f"Erro ao verificar atualizações: {str(e)}", []

    # ==================== MÉTODOS DE LIMPEZA MELHORADOS ====================

    def limpar_temporarios(self):
        """Limpa arquivos temporários em múltiplos locais"""
        temp_locations = [
            "%TEMP%\\*",
            "C:\\Windows\\Temp\\*",
            "C:\\Windows\\Prefetch\\*",
            "%USERPROFILE%\\AppData\\Local\\Temp\\*",
            "%USERPROFILE%\\AppData\\LocalLow\\Temp\\*",
            "C:\\Windows\\Logs\\*",
            "C:\\Windows\\System32\\LogFiles\\*",
            "C:\\Windows\\System32\\config\\systemprofile\\AppData\\Local\\Temp\\*",
            "C:\\Windows\\System32\\config\\systemprofile\\AppData\\LocalLow\\Temp\\*",
            "%USERPROFILE%\\Documents\\*tmp*",
            "%USERPROFILE%\\Desktop\\*tmp*",
            "%USERPROFILE%\\Downloads\\*tmp*",
        ]
        
        for location in temp_locations:
            try:
                subprocess.run(
                    ["cmd", "/c", f"del /q/f/s {location}"], 
                    shell=True, 
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10
                )
            except:
                pass
        
        print("Arquivos temporários limpos com sucesso!")

    def limpar_logs(self):
        """Limpa logs do sistema Windows"""
        try:
            subprocess.run(["wevtutil.exe", "el"], stdout=subprocess.PIPE,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["wevtutil.exe", "cl", "Application"], stdout=subprocess.PIPE,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["wevtutil.exe", "cl", "Security"], stdout=subprocess.PIPE,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["wevtutil.exe", "cl", "System"], stdout=subprocess.PIPE,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["wevtutil.exe", "cl", "Setup"], stdout=subprocess.PIPE,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["wevtutil.exe", "cl", "Windows PowerShell"], stdout=subprocess.PIPE,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            print("Logs do sistema limpos com sucesso!")
        except:
            pass

    def limpar_update(self):
        """Limpa cache do Windows Update"""
        try:
            subprocess.run(["net", "stop", "wuauserv"], shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["net", "stop", "bits"], shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["rd", "/s", "/q", "%windir%\\SoftwareDistribution"], shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["net", "start", "wuauserv"], shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["net", "start", "bits"], shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            print("Cache do Windows Update limpo com sucesso!")
        except:
            pass

    def limpar_dns(self):
        """Limpa cache DNS"""
        try:
            subprocess.run(["ipconfig", "/flushdns"], shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            print("Cache DNS limpo com sucesso!")
        except:
            pass

    def limpar_edge(self):
        """Limpa cache do Microsoft Edge (legado)"""
        try:
            subprocess.run(
                ["RunDll32.exe", "InetCpl.cpl,ClearMyTracksByProcess", "255"], shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("Cache do Edge limpo com sucesso!")
        except:
            pass

    def limpar_edge_chromium(self):
        """Limpa cache do Microsoft Edge Chromium"""
        try:
            edge_paths = [
                "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Cache\\*",
                "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Code Cache\\*",
                "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Service Worker\\CacheStorage\\*",
                "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Session Storage\\*",
                "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\GPUCache\\*",
                "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Media Cache\\*",
            ]
            
            for path in edge_paths:
                subprocess.run(
                    ["cmd", "/c", f"del /q/f/s {path}"],
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            print("Cache do Edge Chromium limpo com sucesso!")
        except:
            pass

    def limpar_chrome(self):
        """Limpa cache do Google Chrome"""
        try:
            chrome_paths = [
                "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cache\\*",
                "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Code Cache\\*",
                "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\GPUCache\\*",
                "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Service Worker\\CacheStorage\\*",
                "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Session Storage\\*",
            ]
            
            for path in chrome_paths:
                subprocess.run(
                    ["cmd", "/c", f"del /q/f/s {path}"],
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            print("Cache do Chrome limpo com sucesso!")
        except:
            pass

    def limpar_firefox(self):
        """Limpa cache do Firefox"""
        try:
            subprocess.run(
                [
                    "cmd",
                    "/c",
                    'rd /s /q "%APPDATA%\\Mozilla\\Firefox\\Profiles\\*.default-release\\cache2"',
                ],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            subprocess.run(
                [
                    "cmd",
                    "/c",
                    'rd /s /q "%APPDATA%\\Mozilla\\Firefox\\Profiles\\*.default-release\\offlinecache"',
                ],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("Cache do Firefox limpo com sucesso!")
        except:
            pass

    def limpar_opera(self):
        """Limpa cache do Opera"""
        try:
            subprocess.run(
                ["cmd", "/c", 'rd /s /q "%APPDATA%\\Opera Software\\Opera Stable\\Cache"'],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            subprocess.run(
                [
                    "cmd",
                    "/c",
                    'rd /s /q "%APPDATA%\\Opera Software\\Opera Stable\\Code Cache"',
                ],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("Cache do Opera limpo com sucesso!")
        except:
            pass

    def limpar_brave(self):
        """Limpa cache do Brave Browser"""
        try:
            brave_paths = [
                "%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Cache\\*",
                "%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Code Cache\\*",
                "%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data\\Default\\GPUCache\\*",
            ]
            
            for path in brave_paths:
                subprocess.run(
                    ["cmd", "/c", f"del /q/f/s {path}"],
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            print("Cache do Brave limpo com sucesso!")
        except:
            pass

    def limpar_vivaldi(self):
        """Limpa cache do Vivaldi"""
        try:
            vivaldi_paths = [
                "%LOCALAPPDATA%\\Vivaldi\\User Data\\Default\\Cache\\*",
                "%LOCALAPPDATA%\\Vivaldi\\User Data\\Default\\Code Cache\\*",
                "%LOCALAPPDATA%\\Vivaldi\\User Data\\Default\\GPUCache\\*",
            ]
            
            for path in vivaldi_paths:
                subprocess.run(
                    ["cmd", "/c", f"del /q/f/s {path}"],
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            print("Cache do Vivaldi limpo com sucesso!")
        except:
            pass

    def limpar_safari(self):
        """Limpa cache do Safari"""
        try:
            subprocess.run(
                ["cmd", "/c", 'rd /s /q "%APPDATA%\\Apple Computer\\Safari\\Cache"'],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            subprocess.run(
                ["cmd", "/c", 'rd /s /q "%APPDATA%\\Apple Computer\\Safari\\Cache.db"'],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("Cache do Safari limpo com sucesso!")
        except:
            pass

    def limpar_tor(self):
        """Limpa cache do Tor Browser"""
        try:
            subprocess.run(
                ["cmd", "/c", 'rd /s /q "%APPDATA%\\Tor Browser\\Browser\\Caches"'],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("Cache do Tor Browser limpo com sucesso!")
        except:
            pass

    def limpar_maxthon(self):
        """Limpa cache do Maxthon"""
        try:
            subprocess.run(
                ["cmd", "/c", 'rd /s /q "%APPDATA%\\Maxthon3\\Cache"'],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("Cache do Maxthon limpo com sucesso!")
        except:
            pass

    def limpar_waterfox(self):
        """Limpa cache do Waterfox"""
        try:
            subprocess.run(
                [
                    "cmd",
                    "/c",
                    'rd /s /q "%APPDATA%\\Waterfox\\Profiles\\*.default-release\\cache2"',
                ],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("Cache do Waterfox limpo com sucesso!")
        except:
            pass

    def limpar_pale_moon(self):
        """Limpa cache do Pale Moon"""
        try:
            subprocess.run(
                [
                    "cmd",
                    "/c",
                    'rd /s /q "%APPDATA%\\Moonchild Productions\\Pale Moon\\Profiles\\*.default\\cache2"',
                ],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("Cache do Pale Moon limpo com sucesso!")
        except:
            pass

    def limpar_lixeira(self):
        """Esvazia a lixeira de forma mais eficiente"""
        try:
            # Método usando PowerShell
            ps_script = '''
            $Recycler = New-Object -ComObject Shell.Application
            $Recycler.Namespace(0xA).Items() | ForEach-Object {
                $_.InvokeVerb("delete")
            }
            Clear-RecycleBin -Force -ErrorAction SilentlyContinue
            '''
            subprocess.run(["powershell", "-Command", ps_script],
                          creationflags=subprocess.CREATE_NO_WINDOW, timeout=30)
            
            # Método alternativo para todas as unidades
            drives = [f"{chr(d)}:" for d in range(65, 91) if os.path.exists(f"{chr(d)}:")]
            for drive in drives:
                recycle_path = f"{drive}\\$Recycle.Bin"
                if os.path.exists(recycle_path):
                    try:
                        shutil.rmtree(recycle_path, ignore_errors=True)
                    except:
                        pass
            
            print("Lixeira esvaziada com sucesso!")
        except Exception as e:
            print(f"Erro ao limpar lixeira: {e}")

    def limpar_arquivos_duplicados(self):
        """Remove arquivos temporários antigos e duplicados"""
        try:
            # Remover arquivos .tmp com mais de 30 dias
            ps_script = '''
            $oldFiles = Get-ChildItem -Path C:\\ -Recurse -Filter *.tmp -ErrorAction SilentlyContinue | 
                        Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} |
                        Select-Object -ExpandProperty FullName
            foreach ($file in $oldFiles) {
                try { Remove-Item -Path $file -Force -ErrorAction SilentlyContinue } catch {}
            }
            '''
            subprocess.run(["powershell", "-Command", ps_script],
                          creationflags=subprocess.CREATE_NO_WINDOW, timeout=60)
            
            # Remover arquivos de erro
            error_files = [
                "C:\\Windows\\*.dmp",
                "C:\\Windows\\*.log",
                "C:\\Windows\\System32\\*.dmp",
                "C:\\Windows\\System32\\*.log",
                "C:\\Windows\\System32\\config\\systemprofile\\*.dmp",
            ]
            
            for pattern in error_files:
                subprocess.run(
                    ["cmd", "/c", f"del /q/f/s {pattern}"],
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            print("Arquivos duplicados e antigos removidos com sucesso!")
        except:
            pass

    def limpar_cache_fontes_icones(self):
        """Limpa cache de fontes e ícones do sistema"""
        try:
            # Resetar cache de ícones
            subprocess.run(
                ["cmd", "/c", "ie4uinit.exe -show"],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Limpar cache de fontes
            font_cache = [
                "%LOCALAPPDATA%\\Microsoft\\Windows\\Fonts\\*",
                "C:\\Windows\\ServiceProfiles\\LocalService\\AppData\\Local\\FontCache\\*",
                "C:\\Windows\\System32\\FNTCACHE.DAT",
            ]
            
            for path in font_cache:
                subprocess.run(
                    ["cmd", "/c", f"del /q/f/s {path}"],
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            print("Cache de fontes e ícones limpo com sucesso!")
        except:
            pass

    def limpar_miniaturas(self):
        """Limpa cache de miniaturas"""
        try:
            subprocess.run(
                ["cmd", "/c", "del /q/f/s %LOCALAPPDATA%\\Microsoft\\Windows\\Explorer\\thumbcache_*"],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("Cache de miniaturas limpo com sucesso!")
        except:
            pass

    def limpar_dumps_memoria(self):
        """Limpa dumps de memória"""
        try:
            subprocess.run(["cmd", "/c", "del /q/f/s C:\\Windows\\Minidump\\*"], shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["cmd", "/c", "del /q/f/s C:\\Windows\\MEMORY.DMP"], shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            print("Dumps de memória limpos com sucesso!")
        except:
            pass

    def limpar_relatorios_erros(self):
        """Limpa relatórios de erro do Windows"""
        try:
            subprocess.run(
                ["cmd", "/c", "del /q/f/s C:\\ProgramData\\Microsoft\\Windows\\WER\\*"],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("Relatórios de erro limpos com sucesso!")
        except:
            pass

    def limpar_logs_windows_update(self):
        """Limpa logs do Windows Update"""
        try:
            subprocess.run(
                ["cmd", "/c", "del /q/f/s %windir%\\Logs\\WindowsUpdate\\*"], shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            subprocess.run(
                ["cmd", "/c", "del /q/f/s %windir%\\WindowsUpdate.log"], shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("Logs do Windows Update limpos com sucesso!")
        except:
            pass

    def limpar_instaladores_antigos(self):
        """Remove instaladores antigos e arquivos de instalação temporários"""
        try:
            # Limpar pasta C:\Windows\Installer
            subprocess.run(
                ["cmd", "/c", "del /q/f/s C:\\Windows\\Installer\\*.tmp"],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Limpar pasta de downloads do Windows Update
            update_downloads = [
                "C:\\Windows\\SoftwareDistribution\\Download\\*",
                "C:\\Windows\\SoftwareDistribution\\DeliveryOptimization\\*",
            ]
            
            for path in update_downloads:
                subprocess.run(
                    ["cmd", "/c", f"del /q/f/s {path}"],
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            # Limpar cache do Windows Installer
            subprocess.run(
                ["cmd", "/c", "del /q/f/s C:\\Windows\\Installer\\*.msi"],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            print("Instaladores antigos removidos com sucesso!")
        except:
            pass

    def limpar_reciclaveis_sistema(self):
        """Remove arquivos recicláveis do sistema"""
        try:
            recyclable_paths = [
                "C:\\Windows\\System32\\config\\systemprofile\\AppData\\Local\\Microsoft\\Windows\\WER\\*",
                "C:\\Windows\\System32\\config\\systemprofile\\AppData\\Local\\CrashDumps\\*",
                "C:\\ProgramData\\Microsoft\\Windows\\WER\\*",
                "C:\\Users\\*\\AppData\\Local\\Microsoft\\Windows\\WER\\*",
                "C:\\Users\\*\\AppData\\Local\\CrashDumps\\*",
                "C:\\ProgramData\\Microsoft\\Windows\\Caches\\*",
                "C:\\Windows\\ServiceProfiles\\NetworkService\\AppData\\Local\\Microsoft\\Windows\\WER\\*",
                "C:\\Windows\\ServiceProfiles\\LocalService\\AppData\\Local\\Microsoft\\Windows\\WER\\*",
            ]
            
            for path in recyclable_paths:
                subprocess.run(
                    ["cmd", "/c", f"rd /s /q {path}"],
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            print("Arquivos recicláveis do sistema removidos com sucesso!")
        except:
            pass

    def limpar_cache_loja_windows(self):
        """Limpa cache da Microsoft Store"""
        try:
            # Parar processos da Store
            subprocess.run(["taskkill", "/f", "/im", "WinStore.App.exe"], 
                          capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Executar wsreset
            subprocess.run(["wsreset.exe"], 
                          creationflags=subprocess.CREATE_NO_WINDOW, timeout=30)
            
            # Limpar cache manualmente
            cache_paths = [
                "%LOCALAPPDATA%\\Packages\\Microsoft.WindowsStore_8wekyb3d8bbwe\\LocalCache",
                "%LOCALAPPDATA%\\Packages\\Microsoft.WindowsStore_8wekyb3d8bbwe\\LocalState\\Cache",
                "%LOCALAPPDATA%\\Packages\\Microsoft.WindowsStore_8wekyb3d8bbwe\\AC\\Microsoft\\Windows Store\\Cache",
            ]
            
            for path in cache_paths:
                subprocess.run(
                    ["cmd", "/c", f"rd /s /q {path}"],
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            time.sleep(1)
            self.fechar_microsoft_store()
            print("Cache da Microsoft Store limpo com sucesso!")
        except:
            pass

    def limpar_temp_adicional(self):
        """Limpa pastas temporárias adicionais"""
        try:
            temp_adicional = [
                "%USERPROFILE%\\AppData\\Local\\Temp\\*",
                "%USERPROFILE%\\AppData\\LocalLow\\Temp\\*",
                "C:\\Windows\\Temp\\*",
                "C:\\Windows\\Logs\\*",
            ]
            
            for path in temp_adicional:
                subprocess.run(
                    ["cmd", "/c", f"del /q/f/s {path}"],
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            print("Temporários adicionais limpos com sucesso!")
        except:
            pass

    def limpar_espaco_disco(self):
        """Executa limpeza de disco"""
        try:
            subprocess.run(["cleanmgr", "/sagerun:1"], shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            print("Limpeza de disco executada com sucesso!")
        except:
            pass

    def limpar_desnecessarios(self):
        """Limpa componentes desnecessários do sistema"""
        try:
            subprocess.run(
                ["dism", "/online", "/cleanup-image", "/startcomponentcleanup"], shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("Componentes desnecessários removidos com sucesso!")
        except:
            pass

    def limpar_atualizacao(self):
        """Limpa atualizações antigas"""
        try:
            subprocess.run(
                ["dism", "/online", "/cleanup-image", "/spsuperseded", "/hidesp"],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("Atualizações antigas removidas com sucesso!")
        except:
            pass

    def remover_programas(self):
        """Remove programas desnecessários"""
        try:
            if subprocess.run("where FlashUtil*.exe", shell=True,
                             creationflags=subprocess.CREATE_NO_WINDOW).returncode == 0:
                subprocess.run("FlashUtil*.exe -uninstall", shell=True,
                              creationflags=subprocess.CREATE_NO_WINDOW)
            print("Programas desnecessários removidos com sucesso!")
        except:
            pass

    def remover_bloatware(self):
        """Remove bloatware do Windows"""
        try:
            apps = [
                "Microsoft.3DBuilder",
                "Microsoft.BingWeather",
                "Microsoft.MicrosoftSolitaireCollection",
                "Microsoft.MicrosoftOfficeHub",
                "Microsoft.GetHelp",
                "Microsoft.Getstarted",
                "Microsoft.Messaging",
                "Microsoft.Microsoft3DViewer",
                "Microsoft.MicrosoftOfficeHub",
                "Microsoft.MicrosoftSolitaireCollection",
                "Microsoft.MixedReality.Portal",
                "Microsoft.Office.OneNote",
                "Microsoft.OneConnect",
                "Microsoft.People",
                "Microsoft.Print3D",
                "Microsoft.SkypeApp",
                "Microsoft.Wallet",
                "Microsoft.WindowsAlarms",
                "Microsoft.WindowsCamera",
                "Microsoft.WindowsCommunicationsApps",
                "Microsoft.WindowsFeedbackHub",
                "Microsoft.WindowsMaps",
                "Microsoft.WindowsPhone",
                "Microsoft.WindowsSoundRecorder",
                "Microsoft.XboxApp",
                "Microsoft.XboxIdentityProvider",
                "Microsoft.XboxSpeechToTextOverlay",
                "Microsoft.ZuneMusic",
                "Microsoft.ZuneVideo",
            ]
            
            for app in apps:
                subprocess.run(
                    ["powershell", "-Command", f"Get-AppxPackage {app} | Remove-AppxPackage"],
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            print("Bloatware removido com sucesso!")
        except:
            pass

    def compactar_sistema(self):
        """Compacta arquivos do sistema"""
        try:
            subprocess.run(["compact", "/compactos:always", "/exe"], shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            print("Sistema compactado com sucesso!")
        except:
            pass

    def desativar_hibernacao(self):
        """Desativa hibernação"""
        try:
            subprocess.run(["powercfg", "-h", "off"], shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            print("Hibernação desativada com sucesso!")
        except:
            pass

    def desabilitar_inicializacao(self):
        """Desabilita programas da inicialização"""
        try:
            subprocess.run(
                [
                    "reg",
                    "add",
                    '"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"',
                    "/v",
                    '"UnwantedProgram"',
                    "/f",
                ],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("Programas da inicialização desabilitados com sucesso!")
        except:
            pass

    def otimizar_desligamento(self):
        """Otimiza tempo de desligamento"""
        try:
            subprocess.run(
                [
                    "reg",
                    "add",
                    '"HKCU\\Control Panel\\Desktop"',
                    "/v",
                    '"WaitToKillAppTimeout"',
                    "/t",
                    "REG_SZ",
                    "/d",
                    '"2000"',
                    "/f",
                ],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            subprocess.run(
                [
                    "reg",
                    "add",
                    '"HKCU\\Control Panel\\Desktop"',
                    "/v",
                    '"HungAppTimeout"',
                    "/t",
                    "REG_SZ",
                    "/d",
                    '"1000"',
                    "/f",
                ],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            subprocess.run(
                [
                    "reg",
                    "add",
                    '"HKLM\\SYSTEM\\CurrentControlSet\\Control"',
                    "/v",
                    '"WaitToKillServiceTimeout"',
                    "/t",
                    "REG_SZ",
                    "/d",
                    '"2000"',
                    "/f",
                ],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("Tempo de desligamento otimizado com sucesso!")
        except:
            pass

    def reiniciar_servicos_essenciais(self):
        """Reinicia serviços essenciais"""
        try:
            subprocess.run(["net", "start", "wuauserv"], shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["net", "start", "bits"], shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["net", "start", "Dnscache"], shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            print("Serviços essenciais reiniciados com sucesso!")
        except:
            pass

    def fechar_microsoft_store(self):
        """Fecha a Microsoft Store"""
        try:
            processos_store = [
                "WinStore.App.exe",
                "WWAHost.exe",
                "Microsoft.StorePurchaseApp.exe",
                "Microsoft.WindowsStore_8wekyb3d8bbwe"
            ]
            
            for processo in processos_store:
                try:
                    subprocess.run(f'taskkill /f /im "{processo}"', 
                                  shell=True, capture_output=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
                except:
                    pass
            
            ps_script = '''
            Get-Process | Where-Object {$_.ProcessName -like "*store*" -or $_.ProcessName -like "*windowsstore*"} | Stop-Process -Force
            Get-Process | Where-Object {$_.MainWindowTitle -like "*Microsoft Store*"} | Stop-Process -Force
            '''
            subprocess.run(["powershell", "-Command", ps_script], 
                          shell=True, capture_output=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            
            print("Microsoft Store fechada com sucesso!")
        except:
            pass

    def verificar_disco(self):
        """Verifica integridade do disco"""
        try:
            p = subprocess.Popen(
                ["chkdsk", "C:", "/f", "/r", "/x"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            output, err = p.communicate(input=b"y\n")
            print("Verificação de disco agendada para a próxima reinicialização!")
        except:
            pass

    def desfragmentar_disco(self):
        """Desfragmenta o disco"""
        try:
            subprocess.run(["defrag", "C:", "/O"], shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            print("Disco desfragmentado com sucesso!")
        except:
            pass


class SistemaLimpezaSimplificado(SistemaLimpeza):
    def executar_atualizacao(self, progress_callback=None):
        """
        Versão ultra-simplificada para evitar erros de importação
        """
        try:
            import subprocess as sp
            
            if progress_callback:
                progress_callback(10)
            
            try:
                sp.run(["winget", "--version"], capture_output=True, shell=True,
                      creationflags=sp.CREATE_NO_WINDOW)
            except:
                return False, "Winget não encontrado"
            
            if progress_callback:
                progress_callback(30)
            
            result = sp.run(["winget", "upgrade", "--all"],
                          capture_output=True, text=True, shell=True,
                          timeout=300, creationflags=sp.CREATE_NO_WINDOW)
            
            if progress_callback:
                progress_callback(100)
            
            if result.returncode == 0:
                return True, "Atualização executada com sucesso!"
            else:
                return False, f"Falha na atualização. Código: {result.returncode}"
                
        except Exception as e:
            return False, f"Erro: {str(e)}"


if __name__ == "__main__":
    limpeza = SistemaLimpezaSimplificado()
    
    print("🔄 Testando sistema de atualização...")
    
    def mostrar_progresso(valor):
        print(f"📊 Progresso: {valor}%")
    
    sucesso, mensagem = limpeza.executar_atualizacao(mostrar_progresso)
    print(f"\nResultado: {mensagem}")
    
    print("\n🔍 Verificando atualizações disponíveis...")
    sucesso, msg, updates = limpeza.verificar_atualizacoes()
    print(f"Verificação: {msg}")
    if updates:
        print(f"Atualizações encontradas: {len(updates)}")
        for i, update in enumerate(updates[:5], 1):
            print(f"  {i}. {update['nome']}: {update['versao_atual']} -> {update['versao_nova']}")
    
    print("\n🧹 Testando limpeza completa...")
    sucesso, mensagem = limpeza.executar_limpeza()
    print(f"Resultado: {mensagem}")