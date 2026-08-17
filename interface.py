# CleanCrow - © 2024 Eduardo Dos Santos Ferreira
# Licenciado sob GNU GPL v3.0

import os
import sys
import time
import subprocess
import threading
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
    QTextEdit,
    QMenu,
    QAction,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon, QTextCursor, QColor, QTextCharFormat, QPainter, QPixmap

# ============================================================================
# CONFIGURAÇÃO DE CAMINHO PARA RECURSOS
# ============================================================================

def resource_path(relative_path):
    """Obtém o caminho correto para recursos quando compilado com PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Configuração para importar o core
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

# Import da fachada unificada
try:
    from core.limpeza import SistemaLimpeza
except ImportError:
    try:
        from limpeza import SistemaLimpeza
    except ImportError:
        SistemaLimpeza = None

# ============================================================================
# WORKER THREAD
# ============================================================================

class WorkerThread(QThread):
    progress_updated = pyqtSignal(int)
    operation_completed = pyqtSignal(bool, str)
    log_message = pyqtSignal(str, str)
    operation_started = pyqtSignal(str)
    step_updated = pyqtSignal(int, int)
    status_text_updated = pyqtSignal(str)

    def __init__(self, operation: str, modo: str = "normal", parent=None):
        super().__init__(parent)
        self.operation = operation
        self.modo = modo
        self.sistema = None
        self._is_running = True
        self.max_execution_time = 1800
        self.process = None

    def stop(self):
        self._is_running = False
        if self.sistema:
            self.sistema.request_interruption()
        if self.process:
            try:
                self.process.kill()
            except:
                pass

    def run(self):
        try:
            if self.operation == "limpeza":
                if self.modo == "rapido":
                    sys.argv.append("--modo-rapido")
                elif self.modo == "seguro":
                    sys.argv.append("--modo-seguro")

                self.sistema = SistemaLimpeza(dry_run=False, verbose=True, quiet=False)
                success, message = self.sistema.executar_limpeza(self.update_progress)

            else:
                success, message = self.executar_winget_atualizacao()

            if self._is_running:
                self.operation_completed.emit(success, message)

        except Exception as e:
            if self._is_running:
                self.operation_completed.emit(False, f"Erro interno: {str(e)}")

    def update_progress(self, progress: int):
        if self._is_running:
            self.progress_updated.emit(progress)

    def executar_winget_atualizacao(self):
        """Executa winget upgrade --all com log em tempo real"""
        try:
            self.log_message.emit("🔍 Verificando winget...", "info")

            result = subprocess.run(
                ["winget", "--version"],
                capture_output=True,
                text=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if result.returncode != 0:
                return False, "Winget não encontrado. Instale o 'App Installer' da Microsoft Store."

            versao = result.stdout.strip()
            self.log_message.emit(f"✅ Winget encontrado (versão: {versao})", "success")

            self.log_message.emit("📦 Atualizando fontes...", "step")
            self.update_progress(5)

            subprocess.run(
                ["winget", "source", "update", "--quiet"],
                capture_output=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=120
            )

            self.update_progress(10)

            self.log_message.emit("🔍 Verificando atualizações disponíveis...", "step")

            result = subprocess.run(
                ["winget", "upgrade"],
                capture_output=True,
                text=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=120
            )

            output = result.stdout

            if "No installed package" in output or "No available" in output:
                self.log_message.emit("ℹ️ Nenhuma atualização disponível", "info")
                self.update_progress(100)
                return True, "Nenhuma atualização disponível"

            self.log_message.emit("📋 Programas que serão atualizados:", "system")

            linhas = output.split('\n')
            programas_para_atualizar = []
            in_table = False

            for linha in linhas:
                if 'Name' in linha and 'Id' in linha and 'Version' in linha:
                    in_table = True
                    continue
                if in_table and linha.strip() and '---' not in linha:
                    partes = linha.split()
                    if len(partes) >= 3:
                        nome = ' '.join(partes[:-3]) if len(partes) > 3 else partes[0]
                        versao_atual = partes[-2] if len(partes) >= 2 else "?"
                        nova_versao = partes[-1] if len(partes) >= 1 else "?"
                        programas_para_atualizar.append((nome, versao_atual, nova_versao))
                        self.log_message.emit(f"  📦 {nome} ({versao_atual} → {nova_versao})", "info")

            if not programas_para_atualizar:
                for linha in linhas:
                    if '->' in linha:
                        partes = linha.split('->')
                        if len(partes) >= 2:
                            nome = partes[0].strip()
                            versoes = partes[1].strip().split()
                            versao_atual = versoes[0] if versoes else "?"
                            nova_versao = versoes[-1] if versoes else "?"
                            programas_para_atualizar.append((nome, versao_atual, nova_versao))
                            self.log_message.emit(f"  📦 {nome} ({versao_atual} → {nova_versao})", "info")

            count = len(programas_para_atualizar)
            self.log_message.emit(f"\n📊 Total: {count} programa(s) para atualizar\n", "success")
            self.step_updated.emit(0, count)

            if count == 0:
                self.update_progress(100)
                return True, "Nenhuma atualização disponível"

            self.log_message.emit("🚀 Iniciando atualização dos programas...", "step")
            self.log_message.emit("⏱️ Aguarde... cada programa será baixado e instalado", "warning")
            self.log_message.emit("=" * 50, "system")

            self.update_progress(20)

            comando = [
                "winget", "upgrade", "--all",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--disable-interactivity"
            ]

            self.process = subprocess.Popen(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                bufsize=1
            )

            programa_atual = ""
            programa_index = 0

            def monitor_output():
                nonlocal programa_atual, programa_index
                for line in iter(self.process.stdout.readline, ''):
                    if not self._is_running:
                        break

                    line = line.strip()
                    if not line:
                        continue

                    if len(line) > 300:
                        line = line[:300] + "..."

                    line_lower = line.lower()

                    if line.startswith('█') or line.startswith('■') or line.startswith('['):
                        pass
                    elif 'baixando' in line_lower or 'downloading' in line_lower:
                        self.log_message.emit(f"  📥 {line}", "info")
                    elif 'instalando' in line_lower or 'installing' in line_lower:
                        self.log_message.emit(f"  ⚙️ {line}", "step")
                    elif 'sucesso' in line_lower or 'success' in line_lower or 'concluído' in line_lower:
                        self.log_message.emit(f"  ✅ {line}", "success")
                    elif 'erro' in line_lower or 'error' in line_lower or 'falha' in line_lower:
                        self.log_message.emit(f"  ❌ {line}", "error")
                    elif 'atualizado' in line_lower or 'upgraded' in line_lower:
                        self.log_message.emit(f"  ✨ {line}", "success")
                    elif 'já instalado' in line_lower or 'already installed' in line_lower:
                        self.log_message.emit(f"  ℹ️ {line}", "info")
                    elif 'ignorando' in line_lower or 'skipping' in line_lower:
                        self.log_message.emit(f"  ⏭️ {line}", "warning")
                    elif 'encontrado' in line_lower or 'found' in line_lower:
                        programa_atual = line
                        programa_index += 1
                        self.log_message.emit(f"\n📌 [{programa_index}/{count}] {line}", "system")
                        self.step_updated.emit(programa_index, count)
                        self.status_text_updated.emit(f"Atualizando pacote {programa_index} de {count}...")
                    else:
                        if line and not line.startswith(' ' * 10):
                            self.log_message.emit(f"  {line}", "info")

            monitor_thread = threading.Thread(target=monitor_output, daemon=True)
            monitor_thread.start()

            progress = 20
            incremento = 70 / max(count, 1)

            while self.process.poll() is None:
                if not self._is_running:
                    self.process.kill()
                    return False, "Atualização cancelada pelo usuário"

                if self.process.poll() is None and programa_index > 0:
                    novo_progresso = min(20 + (programa_index * incremento), 90)
                    if novo_progresso > progress:
                        progress = novo_progresso
                        self.update_progress(int(progress))

                time.sleep(1)

            returncode = self.process.returncode
            self.update_progress(100)

            self.log_message.emit("\n" + "=" * 50, "system")

            if returncode == 0:
                self.log_message.emit("✅ Todas as atualizações foram concluídas!", "success")
                return True, f"{count} programa(s) atualizado(s) com sucesso!"
            elif returncode == -1 or returncode == 1:
                self.log_message.emit("⚠️ Atualização concluída (alguns programas podem ter sido ignorados)", "warning")
                return True, f"Processo finalizado. {count} programa(s) processado(s)"
            else:
                self.log_message.emit(f"⚠️ Winget retornou código {returncode}", "warning")
                return True, f"Processo finalizado. Verifique os logs acima."

        except subprocess.TimeoutExpired:
            if self.process:
                self.process.kill()
            return False, "Timeout: A atualização demorou demais. Tente novamente."
        except Exception as e:
            return False, f"Erro: {str(e)}"
        finally:
            self.process = None


# ============================================================================
# BARRA DE TÍTULO PERSONALIZADA
# ============================================================================

class TitleBar(QWidget):
    def __init__(self, main_window, on_about=None):
        super().__init__()
        self.main_window = main_window
        self.on_about = on_about
        self._drag_offset = None

        self.setFixedHeight(38)
        self.setStyleSheet("""
            background-color: #111111;
            border-top-left-radius: 14px;
            border-top-right-radius: 14px;
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 12, 0)
        layout.setSpacing(8)

        layout.addWidget(self._dot("#ff5f57", self.main_window.close))
        layout.addWidget(self._dot("#febc2e", self.main_window.showMinimized))
        layout.addWidget(self._dot("#28c840", self._toggle_maximize))

        layout.addSpacing(10)

        icon_label = QLabel()
        icon_path = self.main_window.obter_caminho_icone("crowico.png")
        if icon_path and os.path.exists(icon_path):
            icon_label.setPixmap(QPixmap(icon_path).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            icon_label.setText("🐦")
        layout.addWidget(icon_label)

        titulo = QLabel("<span style='color:#e74c3c;font-weight:bold;'>CleanCrow</span> - Painel de Controle")
        titulo.setStyleSheet("""
            color: #8a8f98;
            font-size: 12px;
            font-family: 'Consolas', 'Courier New', monospace;
        """)
        layout.addWidget(titulo)
        layout.addStretch()

        self.status_label = QLabel("● Pronto")
        self.status_label.setStyleSheet("color: #27ae60; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.status_label)

        layout.addSpacing(10)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(18, 18)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFlat(True)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #262626;
                color: #8a8f98;
                border-radius: 9px;
                font-weight: bold;
                font-size: 12px;
                border: none;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #e74c3c;
                color: #ffffff;
            }
        """)
        close_btn.clicked.connect(self.main_window.close)
        layout.addWidget(close_btn)

    def _dot(self, cor, callback):
        btn = QPushButton()
        btn.setFixedSize(13, 13)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFlat(True)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {cor};
                border-radius: 6px;
                border: none;
                padding: 0px;
            }}
        """)
        btn.clicked.connect(callback)
        return btn

    def _toggle_maximize(self):
        if self.main_window.isMaximized():
            self.main_window.showNormal()
        else:
            self.main_window.showMaximized()

    def set_status(self, texto: str, cor: str):
        self.status_label.setText(f"● {texto}")
        self.status_label.setStyleSheet(f"color: {cor}; font-size: 11px; font-weight: bold;")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPos() - self.main_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.main_window.move(event.globalPos() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_offset = None

    def mouseDoubleClickEvent(self, event):
        self._toggle_maximize()


# ============================================================================
# CLASSE PRINCIPAL DA INTERFACE
# ============================================================================

class CleanCrowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CleanCrow - Otimizador de Sistema")
        self.setMinimumSize(800, 600)
        self.setMaximumSize(1100, 900)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setStyleSheet("""
            QMainWindow { background: transparent; }
            QLabel { color: #ffffff; }
            QTextEdit {
                background-color: #0d0d0d;
                color: #ffffff;
                border: 1px solid #262626;
                border-radius: 10px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
            }
            QScrollBar:vertical {
                border: none;
                background: #1a1a1a;
                width: 10px;
                margin: 2px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #e74c3c;
                min-height: 24px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ff6b5b;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        icone = self.obter_caminho_icone("crowico.png")
        if icone:
            self.setWindowIcon(QIcon(icone))

        self.modo_atual = "normal"
        self.worker_thread = None

        self.setup_ui()

    def obter_caminho_icone(self, nome_arquivo: str) -> str:
        caminhos = [
            resource_path(os.path.join("assets", "img", "profile_icons", nome_arquivo)),
            resource_path(nome_arquivo),
            os.path.join(os.path.dirname(__file__), "assets", "img", "profile_icons", nome_arquivo),
            os.path.join(os.path.dirname(__file__), nome_arquivo),
        ]
        for caminho in caminhos:
            if caminho and os.path.exists(caminho):
                return caminho
        return None

    def setup_ui(self):
        self.central_widget = QWidget()
        self.central_widget.setObjectName("centralCard")
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("""
            QWidget#centralCard {
                background-color: #111111;
                border-radius: 14px;
                border: 1px solid rgba(231, 76, 60, 100);
            }
        """)

        sombra = QGraphicsDropShadowEffect(self.central_widget)
        sombra.setBlurRadius(40)
        sombra.setOffset(0, 0)
        sombra.setColor(QColor(231, 76, 60, 110))
        self.central_widget.setGraphicsEffect(sombra)

        outer_layout = QVBoxLayout(self.central_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.title_bar = TitleBar(self, on_about=self.mostrar_sobre)
        outer_layout.addWidget(self.title_bar)

        content = QWidget()
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setContentsMargins(18, 16, 18, 18)
        self.main_layout.setSpacing(14)
        outer_layout.addWidget(content)

        self.setup_action_buttons()
        self.setup_progress_panel()
        self.setup_log_panel()

    def setup_action_buttons(self):
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(14)

        self.limpar_button = self._criar_botao_acao("🧹", "LIMPAR", "SISTEMA", "#e74c3c", "#c0392b")
        self.limpar_button.clicked.connect(self.iniciar_limpeza)
        self.limpar_button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.limpar_button.customContextMenuRequested.connect(self.mostrar_menu_modo)
        self.limpar_button.setToolTip("Clique para limpar · botão direito para escolher o modo (atual: Normal)")

        self.atualizar_button = self._criar_botao_acao("🔄", "ATUALIZAR", "SISTEMA", "#3498db", "#2980b9")
        self.atualizar_button.clicked.connect(self.iniciar_atualizacao)

        self.clear_logs_button = self._criar_botao_acao("🗑️", "LIMPAR", "LOGS", "#3d3d3d", "#4a4a4a")
        self.clear_logs_button.clicked.connect(self.limpar_logs)

        button_layout.addWidget(self.limpar_button)
        button_layout.addWidget(self.atualizar_button)
        button_layout.addWidget(self.clear_logs_button)

        self.main_layout.addWidget(button_container)

    def _criar_botao_acao(self, emoji: str, linha1: str, linha2: str, cor: str, cor_hover: str) -> QPushButton:
        btn = QPushButton(f"{linha1}\n{linha2}")
        btn.setIcon(self._emoji_para_icone(emoji))
        btn.setIconSize(QSize(28, 28))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(64)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {cor};
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 12px;
                padding: 10px 16px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {cor_hover};
            }}
            QPushButton:disabled {{
                background-color: #4a4a4a;
                color: #8a8a8a;
            }}
        """)
        return btn

    def _emoji_para_icone(self, emoji: str, tamanho: int = 32) -> QIcon:
        pixmap = QPixmap(tamanho, tamanho)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        fonte = QFont()
        fonte.setPointSize(int(tamanho * 0.6))
        painter.setFont(fonte)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, emoji)
        painter.end()
        return QIcon(pixmap)

    def setup_progress_panel(self):
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)

        status_row = QWidget()
        status_layout = QHBoxLayout(status_row)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(10)

        self.progress_label = QLabel("Aguardando início da operação")
        self.progress_label.setStyleSheet("font-size: 12px; color: #ecf0f1;")
        status_layout.addWidget(self.progress_label)
        status_layout.addStretch()

        self.percent_label = QLabel("0%")
        self.percent_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #5dade2;")
        status_layout.addWidget(self.percent_label)

        self.fraction_badge = QLabel("")
        self.fraction_badge.setStyleSheet("""
            background-color: #262626;
            color: #b0b0b0;
            font-size: 11px;
            font-weight: bold;
            padding: 3px 10px;
            border-radius: 9px;
        """)
        self.fraction_badge.setVisible(False)
        status_layout.addWidget(self.fraction_badge)

        progress_layout.addWidget(status_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 5px;
                background-color: #1f1f1f;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
                border-radius: 5px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        self.main_layout.addWidget(progress_container)

    def setup_log_panel(self):
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(8)

        log_header = QWidget()
        log_header_layout = QHBoxLayout(log_header)
        log_header_layout.setContentsMargins(0, 0, 0, 0)
        log_header_layout.setSpacing(8)

        prompt_icon = QLabel(">_")
        prompt_icon.setStyleSheet("""
            color: #e74c3c;
            font-weight: bold;
            font-size: 14px;
            font-family: 'Consolas', 'Courier New', monospace;
        """)
        log_header_layout.addWidget(prompt_icon)

        log_title = QLabel("Log de Operações")
        log_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #ffffff;")
        log_header_layout.addWidget(log_title)
        log_header_layout.addStretch()

        log_layout.addWidget(log_header)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(230)
        log_layout.addWidget(self.log_text)

        self.main_layout.addWidget(log_container)

    def mostrar_menu_modo(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #e74c3c;
            }
        """)
        modos = [
            ("normal", "🚀 Normal — limpeza completa"),
            ("rapido", "⚡ Rápido — apenas caches"),
            ("seguro", "🔒 Seguro — não mexe no sistema"),
        ]
        for chave, label in modos:
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(self.modo_atual == chave)
            action.triggered.connect(lambda checked, m=chave: self.selecionar_modo(m))
            menu.addAction(action)
        menu.exec_(self.limpar_button.mapToGlobal(pos))

    def selecionar_modo(self, modo: str):
        self.modo_atual = modo
        nomes = {"normal": "Normal", "rapido": "Rápido", "seguro": "Seguro"}
        self.limpar_button.setToolTip(
            f"Clique para limpar · botão direito para escolher o modo (atual: {nomes[modo]})"
        )
        self.add_log_message(f"📌 Modo alterado para {nomes[modo].upper()}", "info")

    def add_log_message(self, message: str, msg_type: str = "info"):
        timestamp = time.strftime("%H:%M:%S")
        colors = {
            "info": "#5dade2",
            "success": "#2dd4bf",
            "warning": "#f5b041",
            "error": "#ec7063",
            "system": "#bb8fce",
            "step": "#f0a860",
        }
        color = colors.get(msg_type, "#ffffff")

        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)

        fmt_time = QTextCharFormat()
        fmt_time.setForeground(QColor("#6b7280"))
        cursor.setCharFormat(fmt_time)
        cursor.insertText(f"[{timestamp}] ")

        fmt_msg = QTextCharFormat()
        fmt_msg.setForeground(QColor(color))
        cursor.setCharFormat(fmt_msg)
        cursor.insertText(f"{message}\n")

        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()

        QApplication.processEvents()

    def show_message(self, title: str, message: str, icon):
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
        self.percent_label.setText("0%")
        self.fraction_badge.setVisible(False)
        self.fraction_badge.setText("")
        self.progress_label.setText("Executando: Limpeza do sistema...")
        self.title_bar.set_status("Executando", "#f39c12")

        self.log_text.clear()
        self.add_log_message("🚀 Iniciando limpeza do sistema...", "system")
        self.add_log_message(f"📌 Modo selecionado: {self.modo_atual.upper()}", "info")

        self.worker_thread = WorkerThread("limpeza", self.modo_atual)
        self.worker_thread.progress_updated.connect(self.atualizar_progresso)
        self.worker_thread.operation_completed.connect(self.operacao_concluida)
        self.worker_thread.log_message.connect(self.add_log_message)
        self.worker_thread.step_updated.connect(self.atualizar_passo)
        self.worker_thread.status_text_updated.connect(self._atualizar_texto_status)
        self.worker_thread.start()

    def iniciar_atualizacao(self):
        self.limpar_button.setEnabled(False)
        self.atualizar_button.setEnabled(False)
        self.clear_logs_button.setEnabled(False)

        self.progress_bar.setValue(0)
        self.percent_label.setText("0%")
        self.fraction_badge.setVisible(False)
        self.fraction_badge.setText("")
        self.progress_label.setText("Executando: Atualização do sistema...")
        self.title_bar.set_status("Executando", "#f39c12")

        self.log_text.clear()
        self.add_log_message("🔄 Iniciando atualização do sistema via Winget...", "system")
        self.add_log_message("📦 Vou atualizar todos os programas instalados", "info")
        self.add_log_message("⏰ O processo pode levar vários minutos. Aguarde...", "warning")

        self.worker_thread = WorkerThread("atualizacao", self.modo_atual)
        self.worker_thread.progress_updated.connect(self.atualizar_progresso)
        self.worker_thread.operation_completed.connect(self.operacao_concluida)
        self.worker_thread.log_message.connect(self.add_log_message)
        self.worker_thread.step_updated.connect(self.atualizar_passo)
        self.worker_thread.status_text_updated.connect(self._atualizar_texto_status)
        self.worker_thread.start()

    def atualizar_progresso(self, valor: int):
        self.progress_bar.setValue(valor)
        self.percent_label.setText(f"{valor}%")

    def atualizar_passo(self, atual: int, total: int):
        if total > 0:
            self.fraction_badge.setText(f"{atual}/{total}")
            self.fraction_badge.setVisible(True)

    def _atualizar_texto_status(self, texto: str):
        self.progress_label.setText(f"Executando: {texto}")

    def operacao_concluida(self, success: bool, message: str):
        if success:
            self.title_bar.set_status("Concluído", "#27ae60")
            self.progress_bar.setValue(100)
            self.percent_label.setText("100%")
            self.progress_label.setText("Operação concluída com sucesso!")
            self.add_log_message(f"✅ {message}", "success")
            QTimer.singleShot(500, lambda: self.show_message("Sucesso", message, QMessageBox.Information))
        else:
            self.title_bar.set_status("Erro", "#e74c3c")
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
            "Versão: 3.1.0\n"
            "© 2024 Eduardo Dos Santos Ferreira\n\n"
            "Funcionalidades:\n"
            "• Limpeza de sistema (3 modos)\n"
            "• Atualização de programas via Winget\n\n"
            "Modos de limpeza (botão direito em 'Limpar Sistema'):\n"
            "• NORMAL: Limpeza completa em todos os discos + DISM + CleanMgr\n"
            "• RÁPIDO: Apenas caches leves e temporários\n"
            "• SEGURO: Não mexe em arquivos do sistema\n\n"
            "Licenciado sob GNU GPL v3.0")

    def closeEvent(self, event):
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(self, 'Confirmar',
                'Uma operação está em andamento. Deseja cancelar e sair?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.worker_thread.stop()
                self.worker_thread.quit()
                self.worker_thread.wait(5000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = CleanCrowUI()
    window.show()
    sys.exit(app.exec_())