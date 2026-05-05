"""
CleanCrow - Fachada Unificada
Redireciona para o modo correto baseado nas configurações
"""

import sys
from typing import Tuple

from core.base import ModoTipo, elevar_privilegios, is_admin
from core.modo_rapido import ModoRapido
from core.modo_normal import ModoNormal  # Agora é o ULTRA
from core.modo_seguro import ModoSeguro


class SistemaLimpeza:
    """
    Fachada principal do sistema de limpeza
    Redireciona para o modo apropriado
    """
    
    def __init__(self, dry_run: bool = False, verbose: bool = False, quiet: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.quiet = quiet
        
        # Determinar modo baseado em flags
        self.modo = ModoTipo.NORMAL  # padrão é NORMAL ULTRA
        
        if "--modo-rapido" in sys.argv or "--fast" in sys.argv:
            self.modo = ModoTipo.RAPIDO
        elif "--modo-seguro" in sys.argv or "--safe" in sys.argv:
            self.modo = ModoTipo.SEGURO
        
        # Instanciar o modo correto
        if self.modo == ModoTipo.RAPIDO:
            self._impl = ModoRapido(dry_run=dry_run, verbose=verbose)
        elif self.modo == ModoTipo.SEGURO:
            self._impl = ModoSeguro(dry_run=dry_run, verbose=verbose)
        else:
            self._impl = ModoNormal(dry_run=dry_run, verbose=verbose)  # ULTRA
    
    def request_interruption(self):
        """Solicita interrupção (placeholder)"""
        pass
    
    def executar_limpeza(self, progress_callback=None) -> Tuple[bool, str]:
        """
        Executa limpeza no modo selecionado
        """
        # Elevar privilégios apenas no modo normal (ULTRA)
        if self.modo == ModoTipo.NORMAL:
            elevar_privilegios()
        
        print("\n" + "="*60)
        if self.modo == ModoTipo.RAPIDO:
            print("⚡ CLEANCROW - MODO RÁPIDO")
        elif self.modo == ModoTipo.SEGURO:
            print("🔒 CLEANCROW - MODO SEGURO")
        else:
            print("🚀 CLEANCROW - MODO NORMAL ULTRA")
        print("="*60)
        
        if not is_admin() and self.modo == ModoTipo.NORMAL:
            print("⚠️ Atenção: Algumas limpezas requerem administrador")
        
        if self.dry_run:
            print("🔍 MODO SIMULAÇÃO - Nenhum arquivo será deletado")
        
        print("="*60 + "\n")
        
        return self._impl.executar(progress_callback)
    
    def executar_atualizacao(self, progress_callback=None) -> Tuple[bool, str]:
        """Placeholder para compatibilidade"""
        if progress_callback:
            progress_callback(100)
        return True, "Sistema atualizado"