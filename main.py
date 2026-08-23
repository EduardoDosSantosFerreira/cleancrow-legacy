import os
import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox

# ============================================================================
# CONFIGURAÇÃO PARA PYINSTALLER
# ============================================================================

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def is_admin() -> bool:
    """Verifica se está rodando como administrador"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


def request_uac() -> bool:
    """
    Solicita elevação de privilégios via UAC.
    Se conseguir elevar, retorna True e o processo atual é encerrado.
    """
    if is_admin():
        return True
    
    try:
        import ctypes
        import sys
        
        script = os.path.abspath(sys.argv[0])
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:] if arg != "--no-admin"])
        
        result = ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas", 
            sys.executable, 
            f'"{script}" {params}', 
            None, 
            1
        )
        
        if result > 32:
            # Processo elevado iniciado, encerra o atual
            sys.exit(0)
            return True
    except:
        pass
    
    return False


def salvar_log_erro(mensagem):
    try:
        log_path = os.path.join(BASE_DIR, "cleanCrow_erro.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("="*50 + "\n")
            f.write(mensagem + "\n")
            f.write("="*50 + "\n\n")
    except:
        pass


def mostrar_erro(mensagem, detalhe_tecnico=""):
    msg_completa = mensagem
    if detalhe_tecnico:
        msg_completa += f"\n\nDetalhe Tecnico:\n{detalhe_tecnico}"
    
    salvar_log_erro(msg_completa)
    
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Erro - CleanCrow")
        msg.setText("Ocorreu um erro no CleanCrow")
        msg.setInformativeText(mensagem)
        msg.setDetailedText(detalhe_tecnico)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    except:
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, msg_completa, "Erro - CleanCrow", 0x10)
        except:
            print(msg_completa)


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal do CleanCrow"""
    
    success = False
    
    # Verifica SO
    if sys.platform != "win32":
        mostrar_erro("Este software e compativel apenas com Windows.")
        return success
    
    # ========================================================================
    # SOLICITA UAC ANTES DE QUALQUER COISA
    # ========================================================================
    
    # Verifica se já é admin
    if not is_admin():
        print("Solicitando privilegios de Administrador via UAC...")
        if request_uac():
            # Se conseguiu elevar, o processo foi reiniciado
            # O código abaixo só executa se o usuário cancelou o UAC
            print("Usuario cancelou a solicitacao de privilegios.")
            print("Algumas funcionalidades serao limitadas.")
            
            # Pergunta se quer continuar mesmo sem admin
            try:
                import ctypes
                resposta = ctypes.windll.user32.MessageBoxW(
                    0, 
                    "O CleanCrow precisa de privilegios de Administrador para funcionar corretamente.\n\nDeseja continuar mesmo sem privilegios? (Algumas limpezas falharao)", 
                    "CleanCrow - Aviso", 
                    0x00000004 | 0x00000030  # Yes/No + Warning
                )
                if resposta != 6:  # 6 = IDYES
                    print("Operacao cancelada pelo usuario.")
                    return success
            except:
                pass
        else:
            print("Nao foi possivel obter privilegios administrativos.")
            print("O programa continuara com funcionalidades limitadas.")
    
    try:
        # Verifica se a pasta core existe
        core_path = os.path.join(BASE_DIR, "core")
        if not os.path.isdir(core_path):
            raise ImportError(f"A pasta 'core' nao foi encontrada em: {BASE_DIR}")

        # Importa a interface
        try:
            from interface import CleanCrowUI
        except ImportError as ie:
            raise ImportError(f"Erro ao importar interface.py: {str(ie)}")

        # Cria a aplicacao
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        app.setStyle("Fusion")
        
        # Inicia a janela
        window = CleanCrowUI()
        window.show()
        
        success = True
        sys.exit(app.exec_())

    except ImportError as e:
        try:
            arquivos = "\n".join([f"  - {f}" for f in os.listdir(BASE_DIR) if os.path.isfile(os.path.join(BASE_DIR, f))])
            pastas = "\n".join([f"  {f}/" for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))])
        except:
            arquivos, pastas = "Nao foi possivel listar o diretorio."
        
        mensagem = "Erro ao importar modulos necessarios."
        detalhes = f"""
Diretorio atual: {BASE_DIR}

Arquivos:
{arquivos}

Pastas:
{pastas}

Erro original: {str(e)}
"""
        mostrar_erro(mensagem, detalhes)
        
    except Exception as e:
        detalhes = traceback.format_exc()
        mostrar_erro("Erro inesperado ao iniciar o CleanCrow.", detalhes)

    return success


if __name__ == "__main__":
    main()