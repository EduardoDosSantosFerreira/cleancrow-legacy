import subprocess
import ctypes
import sys
import os
import time
import re
import string

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
                (self.limpar_chrome, 12),
                (self.limpar_firefox, 14),
                (self.limpar_opera, 16),
                (self.limpar_brave, 18),
                (self.limpar_vivaldi, 20),
                (self.limpar_safari, 22),
                (self.limpar_tor, 24),
                (self.limpar_maxthon, 26),
                (self.limpar_waterfox, 28),
                (self.limpar_pale_moon, 30),
                (self.limpar_lixeira, 33),
                (self.remover_programas, 36),
                (self.limpar_espaco_disco, 39),
                (self.verificar_disco, 42),
                (self.desfragmentar_disco, 45),
                (self.limpar_desnecessarios, 48),
                (self.limpar_atualizacao, 51),
                (self.compactar_sistema, 54),
                (self.desativar_hibernacao, 57),
                (self.limpar_temp_adicional, 60),
                (self.desabilitar_inicializacao, 63),
                (self.otimizar_desligamento, 66),
                (self.limpar_miniaturas, 69),
                (self.limpar_dumps_memoria, 72),
                (self.limpar_relatorios_erros, 75),
                (self.limpar_logs_windows_update, 78),
                (self.reiniciar_servicos_essenciais, 81),
                (self.limpar_cache_loja_windows, 84),
                (self.remover_bloatware, 87),
                (self.fechar_microsoft_store, 100),
            ]

            for operacao, progresso in operacoes:
                operacao()
                if progress_callback:
                    progress_callback(progresso)

            return True, "Limpeza concluída com sucesso!"
        except Exception as e:
            return False, f"Erro durante a limpeza: {str(e)}"

    def executar_atualizacao(self, progress_callback=None):
        """
        Executa a atualização do sistema usando winget de forma simplificada.
        Apenas executa 'winget upgrade --all' e retorna o resultado.
        """
        try:
            # Verificar se winget está disponível
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

            # Executar o comando simples de atualização
            print("🔄 Executando 'winget upgrade --all'...")
            
            try:
                # Executar o comando básico sem opções complexas
                result = subprocess.run(
                    ["winget", "upgrade", "--all"],
                    capture_output=True,
                    text=True,
                    shell=True,
                    timeout=300,  # 5 minutos timeout
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                if progress_callback:
                    progress_callback(50)

                # Verificar se o comando foi executado
                print(f"Código de saída: {result.returncode}")
                
                if progress_callback:
                    progress_callback(100)

                # Analisar resultado
                if result.returncode == 0:
                    # Verificar se há mensagens específicas na saída
                    output = result.stdout.lower()
                    
                    if "no updates available" in output or "nenhuma atualização disponível" in output:
                        return True, "✅ Sistema já está atualizado. Nenhuma atualização necessária."
                    elif "upgraded" in output or "installed" in output or "sucesso" in output:
                        return True, "✅ Atualização concluída com sucesso!"
                    else:
                        # Se não encontrou padrões específicos, retorna mensagem genérica de sucesso
                        return True, "✅ Comando de atualização executado com sucesso."
                else:
                    # Se houve erro, tentar extrair mensagem de erro útil
                    error_output = result.stderr if result.stderr else result.stdout
                    
                    if "requires admin" in error_output.lower() or "elevated" in error_output.lower():
                        return False, "❌ Winget requer privilégios de administrador. Execute este programa como administrador."
                    elif "access denied" in error_output.lower():
                        return False, "❌ Acesso negado. Certifique-se de executar como administrador."
                    else:
                        # Limitar o tamanho da mensagem de erro
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
        """
        Verifica apenas as atualizações disponíveis sem instalá-las
        Retorna: (sucesso, mensagem, lista_de_atualizacoes)
        """
        try:
            # Verificar se winget está disponível
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

            # Verificar atualizações disponíveis
            result = subprocess.run(
                ["winget", "upgrade", "--include-unknown", "--source", "winget"],
                capture_output=True,
                text=True,
                shell=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # Analisar saída
            output_lines = result.stdout.split('\n')
            updates = []
            
            for line in output_lines:
                line = line.strip()
                if line and not any(x in line for x in ["---", "Nome", "ID", "Versão", "Name", "Id", "Version", "Available"]):
                    if "->" in line:  # Indica que há atualização disponível
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

    # NOVO MÉTODO: Limpar a Lixeira
    def limpar_lixeira(self):
        try:
            # Método 1: Usando PowerShell (mais confiável)
            powershell_script = '''
            $shell = New-Object -ComObject Shell.Application
            $recycleBin = $shell.Namespace(0xA)
            $recycleBin.Items() | ForEach-Object { 
                $_.InvokeVerb("Delete") 
            }
            '''
            subprocess.run(["powershell", "-Command", powershell_script], 
                          shell=True, capture_output=True, text=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Método 2: Usando cmd.exe como fallback
            subprocess.run(["cmd", "/c", "rd /s /q C:\\$Recycle.Bin"], 
                          shell=True, capture_output=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["cmd", "/c", "rd /s /q %systemdrive%\\$Recycle.Bin"], 
                          shell=True, capture_output=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Método 3: Para todas as unidades
            drives = [f"{d}:" for d in string.ascii_uppercase if os.path.exists(f"{d}:")]
            for drive in drives:
                recycle_path = f"{drive}\\$Recycle.Bin"
                if os.path.exists(recycle_path):
                    subprocess.run(["cmd", "/c", f"rd /s /q {recycle_path}"], 
                                  shell=True, capture_output=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            
            print("Lixeira limpa com sucesso!")
        except Exception as e:
            print(f"Erro ao limpar lixeira: {e}")

    # NOVO MÉTODO: Fechar Microsoft Store
    def fechar_microsoft_store(self):
        try:
            # Método 1: Fechar processos relacionados à Microsoft Store
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
            
            # Método 2: Usando PowerShell para fechar apps da Store
            ps_script = '''
            Get-Process | Where-Object {$_.ProcessName -like "*store*" -or $_.ProcessName -like "*windowsstore*"} | Stop-Process -Force
            Get-Process | Where-Object {$_.MainWindowTitle -like "*Microsoft Store*"} | Stop-Process -Force
            '''
            subprocess.run(["powershell", "-Command", ps_script], 
                          shell=True, capture_output=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Método 3: Resetar a cache da Store pode abrir a aplicação,
            # então fazemos isso antes e depois fechamos
            time.sleep(1)  # Pequena pausa
            
            # Fechar novamente após possíveis abertos
            subprocess.run('taskkill /f /im "WinStore.App.exe"', 
                          shell=True, capture_output=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            
            print("Microsoft Store fechada com sucesso!")
        except Exception as e:
            print(f"Erro ao fechar Microsoft Store: {e}")

    # Métodos de limpeza existentes (mantidos do seu código original)
    def limpar_temporarios(self):
        subprocess.run(["cmd", "/c", "del /q/f/s %TEMP%\\*"], shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(["cmd", "/c", "del /q/f/s C:\\Windows\\Temp\\*"], shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(["cmd", "/c", "del /q/f/s C:\\Windows\\Prefetch\\*"], shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)

    def limpar_logs(self):
        subprocess.run(["wevtutil.exe", "el"], stdout=subprocess.PIPE,
                      creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(["wevtutil.exe", "cl", "Application"], stdout=subprocess.PIPE,
                      creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(["wevtutil.exe", "cl", "Security"], stdout=subprocess.PIPE,
                      creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(["wevtutil.exe", "cl", "System"], stdout=subprocess.PIPE,
                      creationflags=subprocess.CREATE_NO_WINDOW)

    def limpar_update(self):
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

    def limpar_dns(self):
        subprocess.run(["ipconfig", "/flushdns"], shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)

    def limpar_edge(self):
        subprocess.run(
            ["RunDll32.exe", "InetCpl.cpl,ClearMyTracksByProcess", "255"], shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def limpar_chrome(self):
        subprocess.run(
            [
                "cmd",
                "/c",
                'rd /s /q "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cache"',
            ],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        subprocess.run(
            [
                "cmd",
                "/c",
                'rd /s /q "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cookies"',
            ],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def limpar_firefox(self):
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
                'rd /s /q "%APPDATA%\\Mozilla\\Firefox\\Profiles\\*.default-release\\cookies.sqlite"',
            ],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def limpar_opera(self):
        subprocess.run(
            ["cmd", "/c", 'rd /s /q "%APPDATA%\\Opera Software\\Opera Stable\\Cache"'],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        subprocess.run(
            [
                "cmd",
                "/c",
                'rd /s /q "%APPDATA%\\Opera Software\\Opera Stable\\Cookies"',
            ],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def limpar_brave(self):
        subprocess.run(
            [
                "cmd",
                "/c",
                'rd /s /q "%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Cache"',
            ],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        subprocess.run(
            [
                "cmd",
                "/c",
                'rd /s /q "%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Cookies"',
            ],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def limpar_vivaldi(self):
        subprocess.run(
            [
                "cmd",
                "/c",
                'rd /s /q "%LOCALAPPDATA%\\Vivaldi\\User Data\\Default\\Cache"',
            ],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        subprocess.run(
            [
                "cmd",
                "/c",
                'rd /s /q "%LOCALAPPDATA%\\Vivaldi\\User Data\\Default\\Cookies"',
            ],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def limpar_safari(self):
        subprocess.run(
            ["cmd", "/c", 'rd /s /q "%APPDATA%\\Apple Computer\\Safari\\Cache"'],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        subprocess.run(
            ["cmd", "/c", 'rd /s /q "%APPDATA%\\Apple Computer\\Safari\\Cookies"'],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def limpar_tor(self):
        subprocess.run(
            ["cmd", "/c", 'rd /s /q "%APPDATA%\\Tor Browser\\Browser\\Caches"'],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        subprocess.run(
            ["cmd", "/c", 'rd /s /q "%APPDATA%\\Tor Browser\\Browser\\Cookies"'],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def limpar_maxthon(self):
        subprocess.run(
            ["cmd", "/c", 'rd /s /q "%APPDATA%\\Maxthon3\\Cache"'],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        subprocess.run(
            ["cmd", "/c", 'rd /s /q "%APPDATA%\\Maxthon3\\Cookies"'],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def limpar_waterfox(self):
        subprocess.run(
            [
                "cmd",
                "/c",
                'rd /s /q "%APPDATA%\\Waterfox\\Profiles\\*.default-release\\cache2"',
            ],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        subprocess.run(
            [
                "cmd",
                "/c",
                'rd /s /q "%APPDATA%\\Waterfox\\Profiles\\*.default-release\\cookies.sqlite"',
            ],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def limpar_pale_moon(self):
        subprocess.run(
            [
                "cmd",
                "/c",
                'rd /s /q "%APPDATA%\\Moonchild Productions\\Pale Moon\\Profiles\\*.default\\cache2"',
            ],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        subprocess.run(
            [
                "cmd",
                "/c",
                'rd /s /q "%APPDATA%\\Moonchild Productions\\Pale Moon\\Profiles\\*.default\\cookies.sqlite"',
            ],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def remover_programas(self):
        if subprocess.run("where FlashUtil*.exe", shell=True,
                         creationflags=subprocess.CREATE_NO_WINDOW).returncode == 0:
            subprocess.run("FlashUtil*.exe -uninstall", shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)

    def limpar_espaco_disco(self):
        subprocess.run(["cleanmgr", "/sagerun:1"], shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)

    def verificar_disco(self):
        p = subprocess.Popen(
            ["chkdsk", "C:", "/f", "/r", "/x"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        output, err = p.communicate(input=b"y\n")

    def desfragmentar_disco(self):
        subprocess.run(["defrag", "C:", "/O"], shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)

    def limpar_desnecessarios(self):
        subprocess.run(
            ["dism", "/online", "/cleanup-image", "/startcomponentcleanup"], shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def limpar_atualizacao(self):
        subprocess.run(
            ["dism", "/online", "/cleanup-image", "/spsuperseded", "/hidesp"],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def compactar_sistema(self):
        subprocess.run(["compact", "/compactos:always", "/exe"], shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)

    def desativar_hibernacao(self):
        subprocess.run(["powercfg", "-h", "off"], shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)

    def limpar_temp_adicional(self):
        subprocess.run(
            ["cmd", "/c", "del /q/f/s %USERPROFILE%\\AppData\\Local\\Temp\\*"],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        subprocess.run(
            ["cmd", "/c", "del /q/f/s %USERPROFILE%\\AppData\\LocalLow\\Temp\\*"],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def limpar_miniaturas(self):
        subprocess.run(
            ["cmd", "/c", "del /q/f/s %LOCALAPPDATA%\\Microsoft\\Windows\\Explorer\\thumbcache_*"],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def limpar_dumps_memoria(self):
        subprocess.run(["cmd", "/c", "del /q/f/s C:\\Windows\\Minidump\\*"], shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(["cmd", "/c", "del /q/f/s C:\\Windows\\MEMORY.DMP"], shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)

    def limpar_relatorios_erros(self):
        subprocess.run(
            ["cmd", "/c", "del /q/f/s C:\\ProgramData\\Microsoft\\Windows\\WER\\*"],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def limpar_logs_windows_update(self):
        subprocess.run(
            ["cmd", "/c", "del /q/f/s %windir%\\Logs\\WindowsUpdate\\*"], shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def reiniciar_servicos_essenciais(self):
        subprocess.run(["net", "start", "wuauserv"], shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(["net", "start", "bits"], shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(["net", "start", "Dnscache"], shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)

    def limpar_cache_loja_windows(self):
        # Esta função pode abrir a Microsoft Store, por isso adicionamos o fechamento depois
        subprocess.run(["wsreset.exe"], shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)

    def remover_bloatware(self):
        apps = [
            "Microsoft.3DBuilder",
            "Microsoft.BingWeather",
            "Microsoft.MicrosoftSolitaireCollection",
        ]
        for app in apps:
            subprocess.run(
                ["powershell", "-Command", f"Get-AppxPackage {app} | Remove-AppxPackage"],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

    def desabilitar_inicializacao(self):
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

    def otimizar_desligamento(self):
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


# Versão SUPER simplificada se ainda houver problemas
class SistemaLimpezaSimplificado(SistemaLimpeza):
    def executar_atualizacao(self, progress_callback=None):
        """
        Versão ultra-simplificada para evitar erros de importação
        """
        try:
            # Importar subprocess localmente para garantir que está disponível
            import subprocess as sp
            
            if progress_callback:
                progress_callback(10)
            
            # Verificar winget
            try:
                sp.run(["winget", "--version"], capture_output=True, shell=True,
                      creationflags=sp.CREATE_NO_WINDOW)
            except:
                return False, "Winget não encontrado"
            
            if progress_callback:
                progress_callback(30)
            
            # Executar comando simples
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


# Exemplo de uso
if __name__ == "__main__":
    # Use a classe simplificada se houver problemas
    limpeza = SistemaLimpezaSimplificado()
    
    # Testar sistema de atualização
    print("🔄 Testando sistema de atualização...")
    
    def mostrar_progresso(valor):
        print(f"📊 Progresso: {valor}%")
    
    sucesso, mensagem = limpeza.executar_atualizacao(mostrar_progresso)
    print(f"\nResultado: {mensagem}")
    
    # Testar verificação de atualizações
    print("\n🔍 Verificando atualizações disponíveis...")
    sucesso, msg, updates = limpeza.verificar_atualizacoes()
    print(f"Verificação: {msg}")
    if updates:
        print(f"Atualizações encontradas: {len(updates)}")
        for i, update in enumerate(updates[:5], 1):
            print(f"  {i}. {update['nome']}: {update['versao_atual']} -> {update['versao_nova']}")
    
    # Testar limpeza completa
    print("\n🧹 Testando limpeza completa...")
    sucesso, mensagem = limpeza.executar_limpeza()
    print(f"Resultado: {mensagem}")