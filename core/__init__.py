# core/__init__.py - VERSÃO CORRIGIDA (sem imports circulares)
"""
CleanCrow Core Module
Sistema de limpeza ultra efetivo para Windows
"""

# Importações seguras - evitar circular imports
try:
    from core.limpeza import SistemaLimpeza
except ImportError:
    try:
        from limpeza import SistemaLimpeza
    except ImportError:
        SistemaLimpeza = None

# Função de diagnóstico (fallback)
def diagnosticar_espaco():
    """Diagnostica espaço que pode ser liberado"""
    try:
        from core.base import obter_tamanho_lixeira, formatar_tamanho
    except:
        pass
    
    return {
        "windows_update_mb": 0,
        "temp_mb": 0,
        "logs_mb": 0,
        "recycle_mb": 0,
        "total_mb": 0,
        "total_gb": 0,
    }

__all__ = ['SistemaLimpeza', 'diagnosticar_espaco']