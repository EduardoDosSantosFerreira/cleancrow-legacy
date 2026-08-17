import os
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox

# ============================================================================
# CONFIGURAÇÃO PARA PYINSTALLER - CORREÇÃO COMPLETA
# ============================================================================

def resource_path(relative_path):
    """Obtém o caminho correto para recursos quando compilado com PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Configuração de caminhos
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Adiciona os caminhos necessários
sys.path.insert(0, BASE_DIR)

# Adiciona também o diretório atual
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

# ============================================================================
# FUNÇÃO PARA MOSTRAR ERRO
# ============================================================================

def mostrar_erro(mensagem):
    """Mostra erro em uma janela"""
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Erro - CleanCrow")
        msg.setText("Erro ao iniciar o CleanCrow")
        msg.setInformativeText(mensagem)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    except:
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, mensagem, "Erro - CleanCrow", 0x10)
        except:
            print(mensagem)

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal do CleanCrow"""
    
    if sys.platform != "win32":
        mostrar_erro("Este software é compatível apenas com Windows.")
        return
    
    try:
        # Tenta importar a interface
        from interface import CleanCrowUI
        
        # Cria a aplicação
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        
        window = CleanCrowUI()
        window.show()
        
        sys.exit(app.exec_())
        
    except ImportError as e:
        # Mostra os arquivos disponíveis para debug
        arquivos = "\n".join([f"  - {f}" for f in os.listdir(BASE_DIR) if os.path.isfile(os.path.join(BASE_DIR, f))])
        pastas = "\n".join([f"  📁 {f}/" for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))])
        
        mensagem = f"""
Erro ao importar interface.py

Detalhes: {str(e)}

Diretório: {BASE_DIR}

Arquivos encontrados:
{arquivos}

Pastas encontradas:
{pastas}
"""
        mostrar_erro(mensagem)
        
    except Exception as e:
        mostrar_erro(f"Erro inesperado:\n\n{str(e)}")

if __name__ == "__main__":
    main()