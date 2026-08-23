# CleanCrow - © 2024 Eduardo Dos Santos Ferreira
# Licenciado sob GNU GPL v3.0

import os
import sys
import time
import subprocess
import threading
from typing import List, Dict, Optional, Tuple

import qtawesome as qta
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
from PyQt5.QtGui import QFont, QIcon, QTextCursor, QColor, QTextCharFormat, QPixmap

# ============================================================================
# CONFIGURACAO DE CAMINHO
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


def is_admin() -> bool:
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


# ============================================================================
# IMPORTS DA ENGINE
# ============================================================================

ENGINE_AVAILABLE = False
formatar_tamanho = lambda x: f"{x} B"

try:
    from core.engine import CleanerEngine, create_engine
    from core.models import CleanerInfo, CleanerResult, ScanResult, RiskLevel, Category, formatar_tamanho
    from core.cleaners import (
        TempCleaner,
        WindowsTempCleaner,
        RecycleBinCleaner,
        ThumbnailCleaner,
        WERCleaner,
        WindowsUpdateCleaner,
        NvidiaCacheCleaner,
        AmdCacheCleaner,
        BrowsersCleaner,
        WebCacheCleaner,
        SystemCleaner,
    )
    ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"Engine nao disponivel: {e}")
    CleanerInfo = None
    CleanerResult = None
    ScanResult = None
    RiskLevel = None
    Category = None
    formatar_tamanho = lambda x: f"{x} B"


# ============================================================================
# WORKER THREAD
# ============================================================================

class HybridWorkerThread(QThread):
    progress_updated = pyqtSignal(int)
    operation_completed = pyqtSignal(bool, str)
    log_message = pyqtSignal(str, str)
    status_text_updated = pyqtSignal(str)
    total_freed = pyqtSignal(int)

    def __init__(self, modo: str = "normal", dry_run: bool = False, verbose: bool = True, parent=None):
        super().__init__(parent)
        self.modo = modo
        self.dry_run = dry_run
        self.verbose = verbose
        self.engine = None
        self._is_running = True
        self._was_canceled = False
        self._timeout_seconds = 3600  # 1 hora de timeout

    def stop(self):
        self._is_running = False
        self._was_canceled = True
        if self.engine:
            self.engine.request_interruption()

    def _emit_log(self, message: str, level: str = "info"):
        self.log_message.emit(message, level)

    def run(self):
        success = False
        message = "Operacao cancelada"

        try:
            if ENGINE_AVAILABLE:
                success, message = self._run_with_engine()
            else:
                success, message = self._run_fallback()
        except Exception as e:
            message = f"Erro: {str(e)}"
            self._emit_log(f"Erro: {message}", "error")
            import traceback
            self._emit_log(traceback.format_exc(), "error")

        if not self._was_canceled and self._is_running:
            self.operation_completed.emit(success, message)

    def _run_with_engine(self) -> Tuple[bool, str]:
        self._emit_log("INICIANDO SCAN DO SISTEMA", "system")
        self._emit_log("=" * 50, "system")
        
        self.engine = create_engine(dry_run=False, verbose=self.verbose)
        self.engine.set_log_callback(self._emit_log)

        all_cleaners = self.engine.get_cleaners()
        all_names = [c.name for c in all_cleaners]
        
        self._emit_log(f"{len(all_names)} categorias disponiveis", "info")
        
        cleaners_filtrados = self._filtrar_por_modo(all_names)
        
        if not cleaners_filtrados:
            return False, f"Nenhuma categoria disponivel no modo {self.modo.upper()}"
        
        self._emit_log(f"Modo {self.modo.upper()}: {len(cleaners_filtrados)} categorias", "info")

        self._emit_log("Analisando espaco a ser liberado...", "step")
        scan_results = self.engine.scan_all()
        total_antes = sum(r.size_bytes for r in scan_results.values())
        
        for name in cleaners_filtrados:
            if name in scan_results and scan_results[name].exists:
                size = scan_results[name].size_bytes
                if size > 0:
                    self._emit_log(f"  {name}: {formatar_tamanho(size)}", "detail")
        
        self._emit_log(f"Total detectado: {formatar_tamanho(total_antes)}", "info")

        self._emit_log("INICIANDO LIMPEZA", "system")
        self._emit_log("=" * 50, "system")
        
        success, message, results = self.engine.clean_selected(
            cleaners_filtrados,
            progress_callback=self.progress_updated.emit,
            status_callback=lambda s: self.status_text_updated.emit(s)
        )

        total_libertado = sum(r.bytes_freed for r in results)
        self.total_freed.emit(total_libertado)
        self.progress_updated.emit(100)
        
        return success, message

    def _filtrar_por_modo(self, selected: List[str]) -> List[str]:
        if self.modo == "seguro":
            nomes_seguros = [
                "Temporarios do Usuario",
                "Temporarios do Windows",
                "Lixeira",
                "Cache de Miniaturas",
                "Relatorios de Erro (WER)",
                "Navegadores",
            ]
            return [n for n in selected if n in nomes_seguros]
        elif self.modo == "rapido":
            nomes_rapidos = [
                "Temporarios do Usuario",
                "Temporarios do Windows",
                "Lixeira",
                "Cache de Miniaturas",
                "Navegadores",
                "Relatorios de Erro (WER)",
            ]
            return [n for n in selected if n in nomes_rapidos]
        else:
            return [n for n in selected if n != "WebCache"]

    def _run_fallback(self) -> Tuple[bool, str]:
        # Implementação de fallback simples (apenas limpeza básica)
        self._emit_log("Engine nao disponivel. Usando modo de limpeza basica.", "warning")
        return False, "Motor de limpeza nao disponivel."


# ============================================================================
# BARRA DE TITULO
# ============================================================================

class TitleBar(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
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
            icon_label.setText("")
        layout.addWidget(icon_label)

        titulo = QLabel("CleanCrow - Painel de Controle")
        titulo.setStyleSheet("color: #e74c3c; font-size: 12px; font-family: 'Consolas', monospace; font-weight: bold;")
        layout.addWidget(titulo)
        
        # INDICADOR DE ADMIN
        self.admin_indicator = QLabel()
        if is_admin():
            self.admin_indicator.setText(" ADMIN ")
            self.admin_indicator.setStyleSheet("""
                background-color: #27ae60;
                color: #ffffff;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
            """)
            self.admin_indicator.setToolTip("Executando como Administrador")
        else:
            self.admin_indicator.setText(" ADMIN? ")
            self.admin_indicator.setStyleSheet("""
                background-color: #e74c3c;
                color: #ffffff;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
            """)
            self.admin_indicator.setToolTip("Nao esta como Administrador - algumas limpezas falharao")
        layout.addWidget(self.admin_indicator)
        
        layout.addStretch()

        self.status_label = QLabel("Pronto")
        self.status_label.setStyleSheet("color: #27ae60; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.status_label)

        layout.addSpacing(10)

        close_btn = QPushButton("X")
        close_btn.setFixedSize(18, 18)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFlat(True)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #262626;
                color: #8a8f98;
                border-radius: 9px;
                font-weight: bold;
                font-size: 11px;
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
        self.status_label.setText(texto)
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
# INTERFACE PRINCIPAL
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
                font-family: 'Consolas', monospace;
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
        QTimer.singleShot(300, self._scan_silencioso)

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

        self.title_bar = TitleBar(self)
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

        self.limpar_button = self._criar_botao_acao(
            'fa5s.broom', "LIMPAR", "SISTEMA", "#e74c3c", "#c0392b"
        )
        self.limpar_button.clicked.connect(self.iniciar_limpeza)
        self.limpar_button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.limpar_button.customContextMenuRequested.connect(self.mostrar_menu_modo)
        self.limpar_button.setToolTip("Clique para limpar | Botao direito para modo (atual: Normal)")

        self.atualizar_button = self._criar_botao_acao(
            'fa5s.sync-alt', "ATUALIZAR", "SISTEMA", "#3498db", "#2980b9"
        )
        self.atualizar_button.clicked.connect(self.iniciar_atualizacao)

        self.clear_logs_button = self._criar_botao_acao(
            'fa5s.trash-alt', "LIMPAR", "LOGS", "#3d3d3d", "#4a4a4a"
        )
        self.clear_logs_button.clicked.connect(self.limpar_logs)

        button_layout.addWidget(self.limpar_button)
        button_layout.addWidget(self.atualizar_button)
        button_layout.addWidget(self.clear_logs_button)

        self.main_layout.addWidget(button_container)

    def _criar_botao_acao(self, nome_icone: str, linha1: str, linha2: str, cor: str, cor_hover: str) -> QPushButton:
        btn = QPushButton(f"{linha1}\n{linha2}")
        icone = qta.icon(nome_icone, color='white')
        btn.setIcon(icone)
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
                text-align: center;
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

    def setup_progress_panel(self):
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)

        status_row = QWidget()
        status_layout = QHBoxLayout(status_row)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(10)

        self.progress_label = QLabel("Aguardando inicio da operacao")
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

        self.total_liberado_label = QLabel("Total: 0 B")
        self.total_liberado_label.setStyleSheet("""
            background-color: #1a2a1a;
            color: #2dd4bf;
            font-size: 11px;
            font-weight: bold;
            padding: 3px 12px;
            border-radius: 9px;
            border: 1px solid #2dd4bf;
        """)
        self.total_liberado_label.setVisible(False)
        status_layout.addWidget(self.total_liberado_label)

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
        prompt_icon.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 14px; font-family: 'Consolas', monospace;")
        log_header_layout.addWidget(prompt_icon)

        log_title = QLabel("Log de Operacoes")
        log_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #ffffff;")
        log_header_layout.addWidget(log_title)
        log_header_layout.addStretch()

        self.log_count_label = QLabel("0 linhas")
        self.log_count_label.setStyleSheet("color: #6b7280; font-size: 11px;")
        log_header_layout.addWidget(self.log_count_label)

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
            ("normal", "Normal - limpeza completa"),
            ("rapido", "Rapido - apenas caches"),
            ("seguro", "Seguro - apenas itens seguros"),
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
        nomes = {"normal": "Normal", "rapido": "Rapido", "seguro": "Seguro"}
        self.limpar_button.setToolTip(
            f"Clique para limpar | Botao direito para modo (atual: {nomes[modo]})"
        )
        self.add_log_message(f"Modo alterado para {nomes[modo].upper()}", "info")

    def _scan_silencioso(self):
        if not ENGINE_AVAILABLE:
            return
        try:
            engine = create_engine(dry_run=True, verbose=False)
            results = engine.scan_all()
            total = sum(r.size_bytes for r in results.values())
            if total > 0:
                self.add_log_message(f"Scan inicial: {formatar_tamanho(total)} recuperaveis", "info")
                self.total_liberado_label.setText(f"Total: {formatar_tamanho(total)}")
                self.total_liberado_label.setVisible(True)
        except Exception as e:
            print(f"Erro no scan inicial: {e}")

    def iniciar_limpeza(self):
        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.limpar_button.setEnabled(False)
        self.atualizar_button.setEnabled(False)
        self.clear_logs_button.setEnabled(False)

        self.progress_bar.setValue(0)
        self.percent_label.setText("0%")
        self.fraction_badge.setVisible(False)
        self.fraction_badge.setText("")
        self.total_liberado_label.setVisible(False)
        self.progress_label.setText("Executando: Limpeza do sistema...")
        self.title_bar.set_status("Executando", "#f39c12")

        self.log_text.clear()
        self.log_count_label.setText("0 linhas")
        
        self.add_log_message("INICIANDO LIMPEZA DO SISTEMA", "system")
        self.add_log_message("=" * 60, "system")
        self.add_log_message(f"Modo selecionado: {self.modo_atual.upper()}", "info")
        
        self.worker_thread = HybridWorkerThread(
            modo=self.modo_atual,
            dry_run=False,
            verbose=True,
            parent=self
        )
        
        self.worker_thread.progress_updated.connect(self.atualizar_progresso)
        self.worker_thread.operation_completed.connect(self.operacao_concluida)
        self.worker_thread.log_message.connect(self.add_log_message)
        self.worker_thread.status_text_updated.connect(self._atualizar_texto_status)
        self.worker_thread.total_freed.connect(self._on_total_freed)
        
        self.worker_thread.start()

    def iniciar_atualizacao(self):
        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.limpar_button.setEnabled(False)
        self.atualizar_button.setEnabled(False)
        self.clear_logs_button.setEnabled(False)

        self.progress_bar.setValue(0)
        self.percent_label.setText("0%")
        self.fraction_badge.setVisible(False)
        self.fraction_badge.setText("")
        self.total_liberado_label.setVisible(False)
        self.progress_label.setText("Executando: Atualizacao do sistema...")
        self.title_bar.set_status("Executando", "#f39c12")

        self.log_text.clear()
        self.log_count_label.setText("0 linhas")
        
        self.add_log_message("INICIANDO ATUALIZACAO DO SISTEMA", "system")
        self.add_log_message("=" * 60, "system")
        self.add_log_message("Atualizando todos os programas via Winget", "info")
        self.add_log_message("O processo pode levar varios minutos. Aguarde...", "warning")

        self._executar_winget_legado()

    def _executar_winget_legado(self):
        try:
            self.add_log_message("Verificando winget...", "info")
            
            result = subprocess.run(
                ["winget", "--version"],
                capture_output=True,
                text=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode != 0:
                self.operacao_concluida(False, "Winget nao encontrado. Instale o App Installer da Microsoft Store.")
                return
            
            versao = result.stdout.strip()
            self.add_log_message(f"Winget encontrado (versao: {versao})", "success")
            
            self.add_log_message("Atualizando fontes...", "step")
            subprocess.run(
                ["winget", "source", "update", "--quiet"],
                capture_output=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=120
            )
            
            self.add_log_message("Verificando atualizacoes disponiveis...", "step")
            self.add_log_message("Iniciando atualizacao...", "step")
            self.add_log_message("Aguarde...", "warning")
            
            proc = subprocess.Popen(
                ["winget", "upgrade", "--all", 
                 "--accept-package-agreements", 
                 "--accept-source-agreements"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                bufsize=1
            )
            
            for line in iter(proc.stdout.readline, ''):
                if line.strip():
                    self.add_log_message(f"  {line.strip()}", "info")
                self.atualizar_progresso(50)
            
            proc.wait()
            
            if proc.returncode == 0:
                self.add_log_message("Atualizacao concluida!", "success")
                self.operacao_concluida(True, "Atualizacao concluida com sucesso!")
            else:
                self.add_log_message(f"Winget retornou codigo {proc.returncode}", "warning")
                self.operacao_concluida(True, f"Atualizacao finalizada com codigo {proc.returncode}")
                
        except subprocess.TimeoutExpired:
            self.operacao_concluida(False, "Timeout: A atualizacao demorou demais. Tente novamente.")
        except Exception as e:
            self.operacao_concluida(False, f"Erro: {str(e)}")

    def _on_total_freed(self, total: int):
        if total > 0:
            self.total_liberado_label.setText(f"Total: {formatar_tamanho(total)}")
            self.total_liberado_label.setVisible(True)

    def _atualizar_texto_status(self, texto: str):
        self.progress_label.setText(f"Executando: {texto}")

    def atualizar_progresso(self, valor: int):
        self.progress_bar.setValue(valor)
        self.percent_label.setText(f"{valor}%")

    def operacao_concluida(self, success: bool, message: str):
        self.add_log_message("\n" + "=" * 60, "system")
        
        if success:
            self.title_bar.set_status("Concluido", "#27ae60")
            self.progress_bar.setValue(100)
            self.percent_label.setText("100%")
            self.progress_label.setText("Operacao concluida com sucesso!")
            self.add_log_message(f"SUCESSO: {message}", "success")
            
            if self.total_liberado_label.isVisible():
                self.add_log_message(f"Total liberado: {self.total_liberado_label.text()}", "success")
            
            QTimer.singleShot(500, lambda: self.show_message("Sucesso", message, QMessageBox.Information))
        else:
            self.title_bar.set_status("Erro", "#e74c3c")
            self.progress_label.setText("Operacao falhou!")
            self.add_log_message(f"FALHA: {message}", "error")
            QTimer.singleShot(500, lambda: self.show_message("Erro", message, QMessageBox.Critical))

        self.limpar_button.setEnabled(True)
        self.atualizar_button.setEnabled(True)
        self.clear_logs_button.setEnabled(True)
        
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait(5000)
        
        self.worker_thread = None

    def add_log_message(self, message: str, msg_type: str = "info"):
        timestamp = time.strftime("%H:%M:%S")
        colors = {
            "info": "#5dade2",
            "success": "#2dd4bf",
            "warning": "#f5b041",
            "error": "#ec7063",
            "system": "#bb8fce",
            "step": "#f0a860",
            "detail": "#8a8f98",
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

        line_count = self.log_text.document().blockCount()
        self.log_count_label.setText(f"{line_count} linhas")

        QApplication.processEvents()

    def limpar_logs(self):
        self.log_text.clear()
        self.log_count_label.setText("0 linhas")
        self.add_log_message("Logs limpos com sucesso!", "info")

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

    def closeEvent(self, event):
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(self, 'Confirmar',
                'Uma operacao esta em andamento. Deseja cancelar e sair?',
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


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = CleanCrowUI()
    window.show()
    sys.exit(app.exec_())