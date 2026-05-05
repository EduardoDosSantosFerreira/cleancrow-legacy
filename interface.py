# CleanCrow - © 2024 Eduardo Dos Santos Ferreira
# Licenciado sob GNU GPL v3.0

import os
import sys
import time
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
    QMenuBar,
    QMenu,
    QAction,
    QButtonGroup,
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon, QTextCursor, QColor, QTextCharFormat

# Import da fachada unificada
from core.limpeza import SistemaLimpeza


# ============================================================================
# FUNÇÃO PARA RECURSOS (SUPORTE A PYINSTALLER)
# ============================================================================

def resource_path(relative_path: str) -> str:
    """Obtém o caminho correto para recursos"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ============================================================================
# WORKER THREAD
# ============================================================================

class WorkerThread(QThread):
    progress_updated = pyqtSignal(int)
    operation_completed = pyqtSignal(bool, str)
    log_message = pyqtSignal(str, str)
    operation_started = pyqtSignal(str)

    def __init__(self, operation: str, modo: str = "normal", parent=None):
        super().__init__(parent)
        self.operation = operation
        self.modo = modo
        self.sistema = None
        self._is_running = True
        self.max_execution_time = 1800

    def stop(self):
        self._is_running = False
        if self.sistema:
            self.sistema.request_interruption()

    def run(self):
        try:
            # Injetar flag de modo para o sistema
            if self.modo == "rapido":
                sys.argv.append("--modo-rapido")
            elif self.modo == "seguro":
                sys.argv.append("--modo-seguro")
            
            self.sistema = SistemaLimpeza(dry_run=False, verbose=True, quiet=False)
            
            if self.operation == "limpeza":
                success, message = self.sistema.executar_limpeza(self.update_progress)
            else:
                success, message = self.sistema.executar_atualizacao(self.update_progress)
            
            if self._is_running:
                self.operation_completed.emit(success, message)
                
        except Exception as e:
            if self._is_running:
                self.operation_completed.emit(False, f"Erro interno: {str(e)}")

    def update_progress(self, progress: int):
        if self._is_running:
            self.progress_updated.emit(progress)


# ============================================================================
# CLASSE PRINCIPAL DA INTERFACE
# ============================================================================

class CleanCrowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CleanCrow - Otimizador de Sistema")
        self.setMinimumSize(800, 600)
        self.setMaximumSize(1100, 900)
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

        # Ícone
        icone = self.obter_caminho_icone("crowico.png")
        if icone:
            self.setWindowIcon(QIcon(icone))

        self.modo_atual = "normal"  # normal, rapido, seguro
        self.worker_thread = None
        
        self.setup_ui()
        self.setup_menu()
        self.setup_modo_selector()

    def obter_caminho_icone(self, nome_arquivo: str) -> str:
        caminhos = [
            resource_path(os.path.join("assets", "img", "profile_icons", nome_arquivo)),
            os.path.join(os.path.dirname(__file__), "assets", "img", "profile_icons", nome_arquivo),
            os.path.join(os.path.dirname(__file__), nome_arquivo),
        ]
        for caminho in caminhos:
            if caminho and os.path.exists(caminho):
                return caminho
        return None

    def setup_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #1a1a1a;
                color: #ffffff;
                border-bottom: 1px solid #333333;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #333333;
            }
            QMenu {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #333333;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #3498db;
            }
        """)
        
        ajuda_menu = menubar.addMenu("Ajuda")
        sobre_action = QAction("Sobre", self)
        sobre_action.triggered.connect(self.mostrar_sobre)
        ajuda_menu.addAction(sobre_action)

    def setup_modo_selector(self):
        """Painel de seleção de modo"""
        modo_frame = QFrame()
        modo_frame.setStyleSheet("""
            background-color: #1a1a1a;
            border-radius: 8px;
            border: 1px solid #333333;
            margin-top: 5px;
        """)
        modo_layout = QHBoxLayout(modo_frame)
        modo_layout.setSpacing(10)
        modo_layout.setContentsMargins(10, 8, 10, 8)
        
        # Label de modo
        label_modo = QLabel("Selecione o modo:")
        label_modo.setStyleSheet("color: #95a5a6; font-weight: bold;")
        modo_layout.addWidget(label_modo)
        
        self.btn_normal = self.criar_botao_modo("🚀 NORMAL", "#e74c3c", self.set_modo_normal)
        self.btn_rapido = self.criar_botao_modo("⚡ RÁPIDO", "#3498db", self.set_modo_rapido)
        self.btn_seguro = self.criar_botao_modo("🔒 SEGURO", "#27ae60", self.set_modo_seguro)
        
        # Estilo do botão normal como ativo (padrão)
        self.btn_normal.setStyleSheet(self._estilo_botao_modo("#e74c3c", True))
        
        modo_layout.addWidget(self.btn_normal)
        modo_layout.addWidget(self.btn_rapido)
        modo_layout.addWidget(self.btn_seguro)
        modo_layout.addStretch()
        
        # Descrição do modo
        self.modo_descricao = QLabel("Completo: limpeza em todos os discos + DISM + CleanMgr")
        self.modo_descricao.setStyleSheet("color: #e74c3c; font-size: 11px; padding: 4px;")
        modo_layout.addWidget(self.modo_descricao)
        
        self.main_layout.insertWidget(1, modo_frame)

    def criar_botao_modo(self, texto: str, cor: str, callback):
        btn = QPushButton(texto)
        btn.setStyleSheet(self._estilo_botao_modo(cor, False))
        btn.clicked.connect(callback)
        btn.setMinimumWidth(120)
        return btn

    def _estilo_botao_modo(self, cor: str, ativo: bool) -> str:
        if ativo:
            return f"""
                QPushButton {{
                    background-color: {cor};
                    color: white;
                    font-weight: bold;
                    border: 2px solid white;
                    padding: 6px 12px;
                    border-radius: 6px;
                    font-size: 12px;
                    min-width: 100px;
                }}
            """
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {cor};
                font-weight: bold;
                border: 2px solid {cor};
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 12px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {cor};
                color: white;
            }}
        """

    def set_modo_normal(self):
        self.modo_atual = "normal"
        self.atualizar_botoes_modo("#e74c3c", self.btn_normal)
        self.modo_descricao.setText("Completo: limpeza em todos os discos + DISM + CleanMgr")
        self.modo_descricao.setStyleSheet("color: #e74c3c; font-size: 11px; padding: 4px;")
        self.add_log_message("📌 Modo NORMAL selecionado - Limpeza completa em todos os discos", "info")

    def set_modo_rapido(self):
        self.modo_atual = "rapido"
        self.atualizar_botoes_modo("#3498db", self.btn_rapido)
        self.modo_descricao.setText("Rápido: apenas caches leves e arquivos temporários")
        self.modo_descricao.setStyleSheet("color: #3498db; font-size: 11px; padding: 4px;")
        self.add_log_message("⚡ Modo RÁPIDO selecionado - Apenas caches leves", "info")

    def set_modo_seguro(self):
        self.modo_atual = "seguro"
        self.atualizar_botoes_modo("#27ae60", self.btn_seguro)
        self.modo_descricao.setText("Seguro: não mexe em arquivos do sistema")
        self.modo_descricao.setStyleSheet("color: #27ae60; font-size: 11px; padding: 4px;")
        self.add_log_message("🔒 Modo SEGURO selecionado - Não mexe em arquivos do sistema", "info")

    def atualizar_botoes_modo(self, cor_ativa, botao_ativo):
        self.btn_normal.setStyleSheet(self._estilo_botao_modo("#e74c3c", False))
        self.btn_rapido.setStyleSheet(self._estilo_botao_modo("#3498db", False))
        self.btn_seguro.setStyleSheet(self._estilo_botao_modo("#27ae60", False))
        botao_ativo.setStyleSheet(self._estilo_botao_modo(cor_ativa, True))

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)
        self.central_widget.setLayout(self.main_layout)

        self.setup_header()
        self.setup_action_buttons()
        self.setup_progress_panel()
        self.setup_log_panel()

    def setup_header(self):
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        logo_path = self.obter_caminho_icone("crowico.png")
        if logo_path:
            logo_label = QLabel()
            logo_label.setPixmap(QIcon(logo_path).pixmap(QSize(60, 60)))
            header_layout.addWidget(logo_label)

        title_label = QLabel("CLEANCROW")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #e74c3c;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

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

    def setup_action_buttons(self):
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(15)
        
        self.limpar_button = QPushButton("🧹 Limpar Sistema")
        self.limpar_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                min-width: 180px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #5d6d7e;
            }
        """)
        self.limpar_button.clicked.connect(self.iniciar_limpeza)
        
        self.atualizar_button = QPushButton("🔄 Atualizar Sistema")
        self.atualizar_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                min-width: 180px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #5d6d7e;
            }
        """)
        self.atualizar_button.clicked.connect(self.iniciar_atualizacao)
        
        self.clear_logs_button = QPushButton("🗑️ Limpar Logs")
        self.clear_logs_button.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                font-weight: bold;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                min-width: 180px;
            }
            QPushButton:hover {
                background-color: #616a6b;
            }
            QPushButton:disabled {
                background-color: #5d6d7e;
            }
        """)
        self.clear_logs_button.clicked.connect(self.limpar_logs)
        
        button_layout.addWidget(self.limpar_button)
        button_layout.addWidget(self.atualizar_button)
        button_layout.addWidget(self.clear_logs_button)
        button_layout.addStretch()
        
        self.main_layout.addWidget(button_container)

    def setup_progress_panel(self):
        progress_frame = QFrame()
        progress_frame.setStyleSheet("background-color: #1a1a1a; border-radius: 6px; border: 1px solid #333333; padding: 10px;")
        progress_layout = QVBoxLayout(progress_frame)
        
        self.progress_label = QLabel("Aguardando início da operação")
        self.progress_label.setStyleSheet("font-size: 12px; color: #ecf0f1;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333333;
                border-radius: 4px;
                height: 16px;
                background-color: #222222;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
                border-radius: 3px;
            }
        """)
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        self.main_layout.addWidget(progress_frame)

    def setup_log_panel(self):
        log_title = QLabel("📝 Log de Operações")
        log_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #3498db; padding: 4px;")
        self.main_layout.addWidget(log_title)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.main_layout.addWidget(self.log_text)

    def add_log_message(self, message: str, msg_type: str = "info"):
        timestamp = time.strftime("%H:%M:%S")
        colors = {"info": "#3498db", "success": "#27ae60", "warning": "#f39c12", "error": "#e74c3c", "system": "#9b59b6"}
        color = colors.get(msg_type, "#ffffff")
        
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        fmt_time = QTextCharFormat()
        fmt_time.setForeground(QColor("#95a5a6"))
        cursor.setCharFormat(fmt_time)
        cursor.insertText(f"[{timestamp}] ")
        
        fmt_msg = QTextCharFormat()
        fmt_msg.setForeground(QColor(color))
        cursor.setCharFormat(fmt_msg)
        cursor.insertText(f"{message}\n")
        
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()

    def show_message(self, title: str, message: str, icon):
        """Exibe caixa de diálogo estilizada"""
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
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        msg_box.exec_()

    def iniciar_limpeza(self):
        self.limpar_button.setEnabled(False)
        self.atualizar_button.setEnabled(False)
        self.clear_logs_button.setEnabled(False)
        
        self.progress_bar.setValue(0)
        self.status_indicator.setText("🟡 Executando")
        self.status_indicator.setStyleSheet("""
            font-size: 11px;
            padding: 4px 8px;
            background-color: #f39c12;
            border-radius: 8px;
            color: white;
            font-weight: bold;
        """)
        
        self.log_text.clear()
        self.add_log_message("🚀 Iniciando limpeza do sistema...", "system")
        self.add_log_message(f"📌 Modo selecionado: {self.modo_atual.upper()}", "info")
        
        self.worker_thread = WorkerThread("limpeza", self.modo_atual)
        self.worker_thread.progress_updated.connect(self.atualizar_progresso)
        self.worker_thread.operation_completed.connect(self.operacao_concluida)
        self.worker_thread.log_message.connect(self.add_log_message)
        self.worker_thread.start()

    def iniciar_atualizacao(self):
        self.limpar_button.setEnabled(False)
        self.atualizar_button.setEnabled(False)
        self.clear_logs_button.setEnabled(False)
        
        self.progress_bar.setValue(0)
        self.progress_label.setText("Iniciando atualização do sistema...")
        self.status_indicator.setText("🟡 Executando")
        self.status_indicator.setStyleSheet("""
            font-size: 11px;
            padding: 4px 8px;
            background-color: #f39c12;
            border-radius: 8px;
            color: white;
            font-weight: bold;
        """)
        
        self.log_text.clear()
        self.add_log_message("🔄 Iniciando atualização do sistema...", "system")
        
        self.worker_thread = WorkerThread("atualizacao", self.modo_atual)
        self.worker_thread.progress_updated.connect(self.atualizar_progresso)
        self.worker_thread.operation_completed.connect(self.operacao_concluida)
        self.worker_thread.log_message.connect(self.add_log_message)
        self.worker_thread.start()

    def atualizar_progresso(self, valor: int):
        self.progress_bar.setValue(valor)
        self.progress_label.setText(f"Progresso: {valor}%")

    def operacao_concluida(self, success: bool, message: str):
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
            self.progress_label.setText("Operação concluída com sucesso!")
            self.add_log_message(f"✅ {message}", "success")
            QTimer.singleShot(500, lambda: self.show_message("Sucesso", message, QMessageBox.Information))
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
            self.add_log_message(f"❌ {message}", "error")
            QTimer.singleShot(500, lambda: self.show_message("Erro", message, QMessageBox.Critical))

        self.limpar_button.setEnabled(True)
        self.atualizar_button.setEnabled(True)
        self.clear_logs_button.setEnabled(True)
        self.worker_thread = None

    def limpar_logs(self):
        self.log_text.clear()
        self.add_log_message("🗑️ Logs limpos com sucesso!", "info")

    def mostrar_sobre(self):
        QMessageBox.about(self, "Sobre o CleanCrow",
            "CleanCrow - Otimizador de Sistema\n\n"
            "Versão: 3.0.0\n"
            "© 2024 Eduardo Dos Santos Ferreira\n\n"
            "Modos de limpeza:\n"
            "• NORMAL: Limpeza completa em todos os discos + DISM + CleanMgr\n"
            "• RÁPIDO: Apenas caches leves e temporários\n"
            "• SEGURO: Não mexe em arquivos do sistema\n\n"
            "Licenciado sob GNU GPL v3.0")

    def closeEvent(self, event):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.quit()
            self.worker_thread.wait(3000)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = CleanCrowUI()
    window.show()
    sys.exit(app.exec_())