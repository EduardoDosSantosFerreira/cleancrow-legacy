# core/logger.py
"""
CleanCrow - Sistema de Logs Estruturado
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class LogEntry:
    """Uma entrada de log"""
    timestamp: str
    level: str  # info, success, warning, error, step, system, detail
    message: str
    category: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class CleanerLogger:
    """Sistema de logs para a engine de limpeza"""
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path(os.environ.get('LOCALAPPDATA', '')) / 'CleanCrow/Logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self._entries: List[LogEntry] = []
        self._callbacks: List[callable] = []
        
        # Cria arquivo de log da sessão
        self._session_file = self.log_dir / f'session_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    def add(self, message: str, level: str = "info", category: str = None, **details):
        """Adiciona uma entrada de log"""
        entry = LogEntry(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            level=level,
            message=message,
            category=category,
            details=details
        )
        self._entries.append(entry)
        
        # Notifica callbacks
        for callback in self._callbacks:
            try:
                callback(entry)
            except:
                pass
        
        # Salva no arquivo
        self._write_entry(entry)
    
    def _write_entry(self, entry: LogEntry):
        """Escreve entrada no arquivo de log"""
        try:
            with open(self._session_file, 'a', encoding='utf-8') as f:
                # Formato legível
                f.write(f"[{entry.timestamp}] {entry.level.upper()}: {entry.message}\n")
                if entry.details:
                    f.write(f"  {json.dumps(entry.details, ensure_ascii=False)}\n")
        except:
            pass
    
    def add_callback(self, callback: callable):
        """Adiciona callback para logs em tempo real"""
        self._callbacks.append(callback)
    
    def get_entries(self, level: Optional[str] = None) -> List[LogEntry]:
        """Retorna entradas de log, opcionalmente filtradas por nível"""
        if level:
            return [e for e in self._entries if e.level == level]
        return self._entries.copy()
    
    def get_summary(self) -> Dict[str, int]:
        """Retorna resumo do log"""
        summary = {
            "total": len(self._entries),
            "info": 0,
            "success": 0,
            "warning": 0,
            "error": 0,
            "step": 0,
            "system": 0,
            "detail": 0,
        }
        for entry in self._entries:
            if entry.level in summary:
                summary[entry.level] += 1
        return summary
    
    def clear(self):
        """Limpa entradas em memória"""
        self._entries.clear()
    
    def export_json(self, path: Optional[Path] = None) -> Path:
        """Exporta logs para JSON"""
        path = path or self.log_dir / f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        data = [asdict(e) for e in self._entries]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path