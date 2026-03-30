# CleanCrow - © 2024 Eduardo Dos Santos Ferreira
# Licenciado sob GNU GPL v3.0 - https://www.gnu.org/licenses/gpl-3.0.html

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QProgressBar,
    QMessageBox,
    QFrame,
    QTextEdit,
    QSplitter,
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon, QTextCursor, QColor, QTextCharFormat
import os
import sys
import time
import subprocess

# Adicione esta linha para importar sua classe de limpeza
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from limpeza_sistema import SistemaLimpeza


class WorkerThread(QThread):
    progress_updated = pyqtSignal(int)
    operation_completed = pyqtSignal(bool, str)
    log_message = pyqtSignal(str, str)  # (mensagem, tipo)
    operation_started = pyqtSignal(str)  # Nome da operação

    def __init__(self, operation, parent=None):
        super().__init__(parent)
        self.operation = operation
        self.sistema = SistemaLimpeza()
        self.operation_names = {
            "limpar_temporarios": "Limpando arquivos temporários...",
            "limpar_logs": "Limpando logs do sistema...",
            "limpar_update": "Limpando cache do Windows Update...",
            "limpar_dns": "Limpando cache DNS...",
            "limpar_edge": "Limpando cache do Microsoft Edge...",
            "limpar_chrome": "Limpando cache do Google Chrome...",
            "limpar_firefox": "Limpando cache do Firefox...",
            "limpar_opera": "Limpando cache do Opera...",
            "limpar_brave": "Limpando cache do Brave...",
            "limpar_vivaldi": "Limpando cache do Vivaldi...",
            "limpar_safari": "Limpando cache do Safari...",
            "limpar_tor": "Limpando cache do Tor Browser...",
            "limpar_maxthon": "Limpando cache do Maxthon...",
            "limpar_waterfox": "Limpando cache do Waterfox...",
            "limpar_pale_moon": "Limpando cache do Pale Moon...",
            "limpar_lixeira": "Esvaziando lixeira...",
            "remover_programas": "Removendo programas desnecessários...",
            "limpar_espaco_disco": "Limpando espaço em disco...",
            "verificar_disco": "Verificando disco...",
            "desfragmentar_disco": "Desfragmentando disco...",
            "limpar_desnecessarios": "Limpando componentes desnecessários...",
            "limpar_atualizacao": "Limpando atualizações antigas...",
            "compactar_sistema": "Compactando sistema...",
            "desativar_hibernacao": "Desativando hibernação...",
            "limpar_temp_adicional": "Limpando temporários adicionais...",
            "desabilitar_inicializacao": "Desabilitando programas da inicialização...",
            "otimizar_desligamento": "Otimizando tempo de desligamento...",
            "limpar_miniaturas": "Limpando cache de miniaturas...",
            "limpar_dumps_memoria": "Limpando dumps de memória...",
            "limpar_relatorios_erros": "Limpando relatórios de erro...",
            "limpar_logs_windows_update": "Limpando logs do Windows Update...",
            "reiniciar_servicos_essenciais": "Reiniciando serviços essenciais...",
            "limpar_cache_loja_windows": "Resetando cache da Microsoft Store...",
            "remover_bloatware": "Removendo bloatware...",
            "fechar_microsoft_store": "Fechando Microsoft Store...",
            "limpar_cache_windows_update": "Limpando cache de atualizações do Windows...",
            "limpar_defender_antivirus": "Limpando arquivos do Microsoft Defender...",
            "limpar_arquivos_otimizacao": "Limpando arquivos de otimização de entrega...",
            "limpar_temp_internet": "Limpando arquivos temporários da internet...",
            "limpar_arquivos_windows": "Limpando arquivos extras do Windows...",
        }

    def run(self):
        if self.operation == "limpeza":
            success, message = self.sistema.executar_limpeza(self.update_progress_with_logs)
        else:
            success, message = self.executar_atualizacao_com_logs()
        self.operation_completed.emit(success, message)

    def update_progress_with_logs(self, progress):
        # Emitir atualização de progresso
        self.progress_updated.emit(progress)
        
        # Determinar qual operação está sendo executada baseada no progresso
        for operation_name, display_name in self.operation_names.items():
            if progress == self.get_progress_for_operation(operation_name):
                self.operation_started.emit(display_name)
                self.log_message.emit(f"▶️ Iniciando: {display_name}", "info")
                break

    def get_progress_for_operation(self, operation_name):
        # Mapeia operações para valores de progresso (ajuste conforme seu sistema)
        progress_map = {
            "limpar_temporarios": 2,
            "limpar_logs": 4,
            "limpar_update": 6,
            "limpar_dns": 8,
            "limpar_edge": 10,
            "limpar_chrome": 12,
            "limpar_firefox": 14,
            "limpar_opera": 16,
            "limpar_brave": 18,
            "limpar_vivaldi": 20,
            "limpar_safari": 22,
            "limpar_tor": 24,
            "limpar_maxthon": 26,
            "limpar_waterfox": 28,
            "limpar_pale_moon": 30,
            "limpar_lixeira": 33,
            "remover_programas": 36,
            "limpar_espaco_disco": 39,
            "verificar_disco": 42,
            "desfragmentar_disco": 45,
            "limpar_desnecessarios": 48,
            "limpar_atualizacao": 51,
            "compactar_sistema": 54,
            "desativar_hibernacao": 57,
            "limpar_temp_adicional": 60,
            "desabilitar_inicializacao": 63,
            "otimizar_desligamento": 66,
            "limpar_miniaturas": 69,
            "limpar_dumps_memoria": 72,
            "limpar_relatorios_erros": 75,
            "limpar_logs_windows_update": 78,
            "reiniciar_servicos_essenciais": 81,
            "limpar_cache_loja_windows": 84,
            "remover_bloatware": 87,
            "fechar_microsoft_store": 90,
            "limpar_cache_windows_update": 93,
            "limpar_defender_antivirus": 95,
            "limpar_arquivos_otimizacao": 97,
            "limpar_temp_internet": 98,
            "limpar_arquivos_windows": 100,
        }
        return progress_map.get(operation_name, 0)

    def executar_atualizacao_com_logs(self):
        """
        Método simplificado que usa diretamente a classe SistemaLimpeza
        """
        try:
            self.log_message.emit("🔍 Verificando atualizações disponíveis...", "info")
            
            # Usar o método da classe SistemaLimpeza em vez de chamar subprocess diretamente
            success, message = self.sistema.executar_atualizacao(self.update_progress_for_atualizacao)
            
            if success:
                self.log_message.emit(f"✅ {message}", "success")
                return True, message
            else:
                self.log_message.emit(f"❌ {message}", "error")
                return False, message
                
        except Exception as e:
            self.log_message.emit(f"❌ Erro inesperado: {str(e)}", "error")
            return False, f"Erro durante a atualização: {str(e)}"

    def update_progress_for_atualizacao(self, progress):
        """
        Callback para atualizar o progresso durante a atualização
        """
        self.progress_updated.emit(progress)
        
        # Mapear progresso para mensagens descritivas
        if progress <= 15:
            self.operation_started.emit("Verificando se winget está disponível...")
            self.log_message.emit("🔍 Verificando se winget está disponível...", "info")
        elif progress <= 30:
            self.operation_started.emit("Verificando atualizações disponíveis...")
            self.log_message.emit("📋 Verificando atualizações disponíveis...", "info")
        elif progress <= 60:
            self.operation_started.emit("Executando atualizações...")
            self.log_message.emit("🚀 Executando atualizações...", "info")
        elif progress < 100:
            self.operation_started.emit("Concluindo atualização...")
            self.log_message.emit("⚡ Concluindo atualização...", "info")


class CleanCrowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CleanCrow - Otimizador de Sistema")
        self.setMinimumSize(800, 600)
        self.setMaximumSize(1100, 900)

        # Definir ícone da janela
        icone_janela = self.obter_caminho_icone("crowico.png")
        if icone_janela:
            self.setWindowIcon(QIcon(icone_janela))

        self.setup_ui()
        self.current_operation = None

    def obter_caminho_icone(self, nome_arquivo):
        caminhos_possiveis = [
            os.path.join(os.path.dirname(__file__), "assets", "img", "profile_icons", nome_arquivo),
            os.path.join(os.path.dirname(__file__), "src", "assets", "img", "profile_icons", nome_arquivo),
            os.path.join(os.path.dirname(__file__), nome_arquivo),
            os.path.join(os.path.dirname(__file__), "..", "assets", "img", "profile_icons", nome_arquivo),
        ]
        for caminho in caminhos_possiveis:
            if os.path.exists(caminho):
                return caminho
        return None

    def setup_ui(self):
        # Configuração principal da janela
        self.setStyleSheet("""
            QMainWindow {
                background-color: #111111;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QTextEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 5px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
            QScrollBar:vertical {
                border: none;
                background: #222222;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #444444;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #555555;
            }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Reduzindo as margens e espaçamentos
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)
        self.central_widget.setLayout(self.main_layout)

        # Cabeçalho
        self.setup_header()

        # Área principal dividida
        splitter = QSplitter(Qt.Vertical)
        self.main_layout.addWidget(splitter, 1)

        # Painel superior - Controles
        top_panel = QWidget()
        top_layout = QVBoxLayout(top_panel)
        top_layout.setSpacing(10)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Botões de ação
        self.setup_action_buttons(top_layout)
        
        # Painel de progresso
        self.setup_progress_panel(top_layout)
        
        splitter.addWidget(top_panel)

        # Painel inferior - Logs
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(5)
        
        # Título da área de logs
        log_title = QLabel("📝 Log de Operações")
        log_title.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
            color: #3498db;
            padding: 5px;
            background-color: #222222;
            border-radius: 5px;
        """)
        bottom_layout.addWidget(log_title)
        
        # Área de logs - reduzindo altura máxima
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        bottom_layout.addWidget(self.log_text)
        
        splitter.addWidget(bottom_panel)
        
        # Definir proporções iniciais
        splitter.setSizes([400, 200])

        self.worker_thread = None

    def setup_header(self):
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        # Logo
        logo_path = self.obter_caminho_icone("crowico.png")
        if logo_path:
            logo_label = QLabel()
            logo_label.setPixmap(QIcon(logo_path).pixmap(QSize(100, 100)))
            header_layout.addWidget(logo_label)

        # Título
        title_label = QLabel("CLEANCROW")
        title_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #e74c3c;
            padding: 0;
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Indicador de status
        self.status_indicator = QLabel("🟢 Pronto")
        self.status_indicator.setStyleSheet("""
            font-size: 11px;
            padding: 4px 8px;
            background-color: #27ae60;
            border-radius: 8px;
            color: white;
            font-weight: bold;
        """)
        header_layout.addWidget(self.status_indicator)

        self.main_layout.addWidget(header_widget)

    def setup_action_buttons(self, layout):
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Botão Limpar
        self.limpar_button = self.create_action_button(
            " Limpar Sistema", 
            "broom.png", 
            "#e74c3c", 
            "#c0392b",
            self.iniciar_limpeza
        )
        button_layout.addWidget(self.limpar_button)
        
        # Botão Atualizar
        self.atualizar_button = self.create_action_button(
            " Atualizar Sistema", 
            "refresh.png", 
            "#3498db", 
            "#2980b9",
            self.iniciar_atualizacao
        )
        button_layout.addWidget(self.atualizar_button)
        
        # Botão Limpar Logs
        self.clear_logs_button = self.create_action_button(
            " Limpar Logs", 
            "trash.png", 
            "#7f8c8d", 
            "#616a6b",
            self.limpar_logs
        )
        button_layout.addWidget(self.clear_logs_button)
        
        layout.addWidget(button_container)

    def create_action_button(self, text, icon_name, color, hover_color, callback):
        button = QPushButton(text)
        
        icon_path = self.obter_caminho_icone(icon_name)
        if icon_path:
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(20, 20))
        
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-weight: bold;
                border: none;
                padding: 10px 16px;
                border-radius: 5px;
                font-size: 13px;
                min-width: 160px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:disabled {{
                background-color: #5d6d7e;
                color: #bdc3c7;
            }}
        """)
        
        button.clicked.connect(callback)
        return button

    def setup_progress_panel(self, layout):
        progress_frame = QFrame()
        progress_frame.setStyleSheet("""
            background-color: #1a1a1a;
            border-radius: 6px;
            border: 1px solid #333333;
            padding: 12px;
        """)
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setSpacing(8)
        
        # Informações de progresso
        progress_info = QHBoxLayout()
        progress_info.setSpacing(10)
        
        self.progress_label = QLabel("Aguardando início da operação")
        self.progress_label.setStyleSheet("""
            font-size: 13px;
            color: #ecf0f1;
            font-weight: bold;
        """)
        
        # Container para porcentagem e contador de operações
        status_container = QHBoxLayout()
        status_container.setSpacing(10)
        
        self.progress_percent = QLabel("0%")
        self.progress_percent.setStyleSheet("""
            font-size: 16px;
            color: #3498db;
            font-weight: bold;
            min-width: 45px;
        """)
        
        self.operations_counter = QLabel("0/45")
        self.operations_counter.setStyleSheet("""
            font-size: 13px;
            color: #95a5a6;
            font-weight: bold;
            padding: 2px 8px;
            background-color: #222222;
            border-radius: 8px;
        """)
        
        status_container.addWidget(self.progress_percent)
        status_container.addWidget(self.operations_counter)
        
        progress_info.addWidget(self.progress_label)
        progress_info.addStretch()
        progress_info.addLayout(status_container)
        
        progress_layout.addLayout(progress_info)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #333333;
                border-radius: 5px;
                height: 18px;
                background-color: #222222;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
                border-radius: 3px;
                border: 1px solid #c0392b;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_frame)

    def add_log_message(self, message, msg_type="info"):
        timestamp = time.strftime("%H:%M:%S")
        
        # Define cores baseadas no tipo de mensagem
        colors = {
            "info": "#3498db",
            "success": "#27ae60",
            "warning": "#f39c12",
            "error": "#e74c3c",
            "system": "#9b59b6",
        }
        
        color = colors.get(msg_type, "#ffffff")
        
        # Cria formatação para a mensagem
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Adiciona timestamp
        format_timestamp = QTextCharFormat()
        format_timestamp.setForeground(QColor("#95a5a6"))
        cursor.setCharFormat(format_timestamp)
        cursor.insertText(f"[{timestamp}] ")
        
        # Adiciona mensagem com cor
        format_message = QTextCharFormat()
        format_message.setForeground(QColor(color))
        cursor.setCharFormat(format_message)
        cursor.insertText(f"{message}\n")
        
        # Rola para a última linha
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()

    def iniciar_limpeza(self):
        self.limpar_button.setEnabled(False)
        self.atualizar_button.setEnabled(False)
        self.clear_logs_button.setEnabled(False)
        
        self.progress_bar.setValue(0)
        self.progress_percent.setText("0%")
        self.operations_counter.setText("0/45")
        self.status_indicator.setText("🟡 Executando")
        self.status_indicator.setStyleSheet("""
            font-size: 11px;
            padding: 4px 8px;
            background-color: #f39c12;
            border-radius: 8px;
            color: white;
            font-weight: bold;
        """)
        
        self.progress_label.setText("Preparando sistema para limpeza...")
        
        # Limpar logs anteriores
        self.log_text.clear()
        self.add_log_message("🚀 Iniciando limpeza completa do sistema...", "system")
        self.add_log_message("🔐 Verificando privilégios de administrador...", "info")
        
        # Atualizar estilo da barra de progresso
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #333333;
                border-radius: 5px;
                height: 18px;
                background-color: #222222;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
                border-radius: 3px;
                border: 1px solid #c0392b;
            }
        """)
        
        self.worker_thread = WorkerThread("limpeza")
        self.worker_thread.progress_updated.connect(self.atualizar_progresso)
        self.worker_thread.operation_completed.connect(self.operacao_concluida)
        self.worker_thread.log_message.connect(self.add_log_message)
        self.worker_thread.operation_started.connect(self.atualizar_operacao_atual)
        self.worker_thread.start()

    def iniciar_atualizacao(self):
        self.limpar_button.setEnabled(False)
        self.atualizar_button.setEnabled(False)
        self.clear_logs_button.setEnabled(False)
        
        self.progress_bar.setValue(0)
        self.progress_label.setText("Iniciando atualização do sistema...")
        self.progress_percent.setText("0%")
        self.operations_counter.setText("0%")
        self.status_indicator.setText("🟡 Executando")
        self.status_indicator.setStyleSheet("""
            font-size: 11px;
            padding: 4px 8px;
            background-color: #f39c12;
            border-radius: 8px;
            color: white;
            font-weight: bold;
        """)
        
        # Limpar logs anteriores
        self.log_text.clear()
        self.add_log_message("🔄 Iniciando atualização do sistema...", "system")
        
        # Atualizar estilo da barra de progresso para azul
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #333333;
                border-radius: 5px;
                height: 18px;
                background-color: #222222;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
                border: 1px solid #2980b9;
            }
        """)
        
        self.worker_thread = WorkerThread("atualizacao")
        self.worker_thread.progress_updated.connect(self.atualizar_progresso)
        self.worker_thread.operation_completed.connect(self.operacao_concluida)
        self.worker_thread.log_message.connect(self.add_log_message)
        self.worker_thread.operation_started.connect(self.atualizar_operacao_atual)
        self.worker_thread.start()

    def atualizar_progresso(self, valor):
        self.progress_bar.setValue(valor)
        self.progress_percent.setText(f"{valor}%")
        
        # Atualizar contador de operações
        if self.worker_thread and self.worker_thread.operation == "limpeza":
            completed = int(valor / 100 * 45)
            self.operations_counter.setText(f"{completed}/45")
        elif self.worker_thread and self.worker_thread.operation == "atualizacao":
            self.operations_counter.setText(f"{valor}%")

    def atualizar_operacao_atual(self, operacao):
        self.progress_label.setText(f"Executando: {operacao}")

    def operacao_concluida(self, success, message):
        if success:
            self.status_indicator.setText("🟢 Concluído")
            self.status_indicator.setStyleSheet("""
                font-size: 11px;
                padding: 4px 8px;
                background-color: #27ae60;
                border-radius: 8px;
                color: white;
                font-weight: bold;
            """)
            
            self.progress_bar.setValue(100)
            self.progress_percent.setText("100%")
            if self.worker_thread and self.worker_thread.operation == "limpeza":
                self.operations_counter.setText("45/45")
            else:
                self.operations_counter.setText("100%")
            self.progress_label.setText("Operação concluída com sucesso!")
            
            self.add_log_message("✅ " + message, "success")
            
            # Mostrar mensagem de sucesso
            QTimer.singleShot(500, lambda: self.show_message("Sucesso", message, QMessageBox.Information))
            
            # Atualizar estilo da barra para verde
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #333333;
                    border-radius: 5px;
                    height: 18px;
                    background-color: #222222;
                }
                QProgressBar::chunk {
                    background-color: #27ae60;
                    border-radius: 3px;
                    border: 1px solid #229954;
                }
            """)
        else:
            self.status_indicator.setText("🔴 Erro")
            self.status_indicator.setStyleSheet("""
                font-size: 11px;
                padding: 4px 8px;
                background-color: #e74c3c;
                border-radius: 8px;
                color: white;
                font-weight: bold;
            """)
            
            self.progress_label.setText("Operação falhou!")
            
            self.add_log_message("❌ " + message, "error")
            
            # Mostrar mensagem de erro
            QTimer.singleShot(500, lambda: self.show_message("Erro", message, QMessageBox.Critical))

        # Reabilitar botões
        self.limpar_button.setEnabled(True)
        self.atualizar_button.setEnabled(True)
        self.clear_logs_button.setEnabled(True)

    def show_message(self, title, message, icon):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #111111;
                color: white;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 6px 14px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        msg_box.exec_()

    def limpar_logs(self):
        self.log_text.clear()
        self.add_log_message("🗑️ Logs limpos com sucesso!", "info")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = CleanCrowUI()
    window.show()
    
    sys.exit(app.exec_())