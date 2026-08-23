# core/models.py
"""
CleanCrow - Modelos de Dados para Engine de Limpeza
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class RiskLevel(Enum):
    """Nível de risco da operação de limpeza"""
    SEGURO = "seguro"       # 🟢 - Sem risco
    AVANCADO = "avancado"   # 🟡 - Precisa de atenção
    ESPECIAL = "especial"   # 🟠 - Específico


class Category(Enum):
    """Categoria da limpeza"""
    TEMPORARIOS = "temporarios"
    SISTEMA = "sistema"
    NAVEGADORES = "navegadores"
    CACHES = "caches"
    LOGS = "logs"
    ATUALIZACOES = "atualizacoes"
    GRAFICOS = "graficos"
    REDE = "rede"
    LIXEIRA = "lixeira"


@dataclass
class CleanerResult:
    """Resultado de uma operação de limpeza"""
    cleaner_name: str
    success: bool
    files_removed: int = 0
    folders_removed: int = 0
    bytes_freed: int = 0
    errors: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    duration_ms: float = 0.0
    
    @property
    def size_formatted(self) -> str:
        return formatar_tamanho(self.bytes_freed)


@dataclass
class ScanResult:
    """Resultado de um scan"""
    cleaner_name: str
    exists: bool
    size_bytes: int = 0
    file_count: int = 0
    folder_count: int = 0
    error: Optional[str] = None
    
    @property
    def size_formatted(self) -> str:
        return formatar_tamanho(self.size_bytes)


@dataclass
class CleanerInfo:
    """Informações de um cleaner"""
    name: str
    description: str
    category: Category
    risk_level: RiskLevel
    requires_admin: bool = False
    enabled: bool = True
    icon: str = "📋"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "risk_level": self.risk_level.value,
            "requires_admin": self.requires_admin,
            "enabled": self.enabled,
            "icon": self.icon,
        }


def formatar_tamanho(bytes_val: int) -> str:
    """Formata bytes para exibição amigável"""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"