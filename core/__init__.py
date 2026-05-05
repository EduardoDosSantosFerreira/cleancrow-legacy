"""
CleanCrow Core Module
Sistema de limpeza ultra efetivo para Windows
"""

# Importações seguras com fallback
try:
    from core.limpeza import SistemaLimpeza
except ImportError:
    from limpeza import SistemaLimpeza

# Diagnosticar espaço é opcional - pode não existir
try:
    from core.limpeza import diagnosticar_espaco
except (ImportError, AttributeError):
    # Função não disponível - criar fallback
    def diagnosticar_espaco():
        return {
            "windows_update_mb": 0,
            "temp_mb": 0,
            "logs_mb": 0,
            "recycle_mb": 0,
            "total_mb": 0,
            "total_gb": 0,
        }

__all__ = ['SistemaLimpeza', 'diagnosticar_espaco']