"""
CleanCrow - Sistema de Limpeza Rápida
Unificado: ModoRápido + Fachada em um único arquivo
Tempo de execução: < 2 minutos
"""

import os
import sys
import time
from pathlib import Path
from typing import Tuple, Dict, Optional

from core.base import (
    ModoTipo, is_admin, formatar_tamanho, remover_pasta, remover_arquivos_antigos,
    limpar_cache_navegadores, esvaziar_lixeira_api
)


class ModoRapido:
    """
    Modo RÁPIDO - Limpeza leve e rápida
    - Arquivos temporários
    - Cache de navegadores
    - Thumbnails
    - Lixeira
    """
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.stats = {
            "total_arquivos": 0,
            "total_bytes": 0,
            "erros": 0,
            "tempo_total": 0,
        }
    
    def log(self, mensagem: str, nivel: str = "info"):
        if self.verbose:
            prefixos = {"info": "📋", "success": "✅", "warning": "⚠️", "error": "❌", "step": "⚡"}
            print(f"  {prefixos.get(nivel, '📋')} {mensagem}")
    
    def limpar_temporarios(self) -> Tuple[int, int]:
        """Limpa diretórios temporários"""
        total_arquivos = 0
        total_bytes = 0
        
        temp_dirs = [
            Path(os.environ.get('TEMP', '')),
            Path(os.environ.get('TMP', '')),
            Path("C:/Windows/Temp"),
            Path(os.environ.get('LOCALAPPDATA', '')) / "Temp",
        ]
        
        for dir_path in temp_dirs:
            if dir_path and dir_path.exists():
                if self.dry_run:
                    for item in dir_path.iterdir():
                        try:
                            if item.is_file():
                                total_arquivos += 1
                                total_bytes += item.stat().st_size
                        except:
                            pass
                else:
                    arquivos, bytes_liberados = remover_pasta(dir_path)
                    total_arquivos += arquivos
                    total_bytes += bytes_liberados
        
        return total_arquivos, total_bytes
    
    def limpar_cache_usuarios_rapido(self) -> Tuple[int, int]:
        """Limpa cache rápido de usuários (apenas Temp e Thumbnails)"""
        total_arquivos = 0
        total_bytes = 0
        
        users_path = Path("C:/Users")
        if not users_path.exists():
            return 0, 0
        
        for user_dir in users_path.iterdir():
            if not user_dir.is_dir():
                continue
            
            # Apenas Temp
            temp_path = user_dir / "AppData/Local/Temp"
            if temp_path.exists():
                if self.dry_run:
                    for item in temp_path.iterdir():
                        try:
                            if item.is_file():
                                total_arquivos += 1
                                total_bytes += item.stat().st_size
                        except:
                            pass
                else:
                    arquivos, bytes_liberados = remover_arquivos_antigos(temp_path, 1)
                    total_arquivos += arquivos
                    total_bytes += bytes_liberados
            
            # Thumbnails
            explorer_path = user_dir / "AppData/Local/Microsoft/Windows/Explorer"
            if explorer_path.exists():
                for pattern in ["thumbcache_*.db", "iconcache_*.db"]:
                    for file in explorer_path.glob(pattern):
                        if self.dry_run:
                            try:
                                total_arquivos += 1
                                total_bytes += file.stat().st_size
                            except:
                                pass
                        else:
                            success, size = self._remover_arquivo_simples(file)
                            if success:
                                total_arquivos += 1
                                total_bytes += size
        
        return total_arquivos, total_bytes
    
    def _remover_arquivo_simples(self, filepath: Path) -> Tuple[bool, int]:
        """Remove arquivo simplesmente"""
        try:
            if not filepath.exists():
                return False, 0
            size = filepath.stat().st_size
            filepath.unlink()
            return True, size
        except:
            return False, 0
    
    def limpar_cache_navegadores_rapido(self) -> Tuple[int, int]:
        """Limpa cache de navegadores"""
        local_appdata = Path(os.environ.get('LOCALAPPDATA', ''))
        if not local_appdata.exists():
            return 0, 0
        
        return limpar_cache_navegadores(local_appdata, self.verbose)
    
    def limpar_lixeira(self) -> Tuple[int, int]:
        """Esvazia lixeira"""
        if self.dry_run:
            return 1, 0
        
        success = esvaziar_lixeira_api()
        return (1, 0) if success else (0, 0)
    
    def executar(self, progress_callback=None) -> Tuple[bool, str]:
        """Executa limpeza no modo rápido"""
        self.log("\n⚡ MODO RÁPIDO - Limpeza leve", "step")
        self.log("Arquivos temporários + Cache navegadores + Thumbnails + Lixeira\n", "info")
        
        inicio = time.time()
        
        tarefas = [
            ("Arquivos Temporários", self.limpar_temporarios, 30),
            ("Cache Navegadores", self.limpar_cache_navegadores_rapido, 25),
            ("Cache Usuários", self.limpar_cache_usuarios_rapido, 25),
            ("Lixeira", self.limpar_lixeira, 20),
        ]
        
        for i, (nome, func, peso) in enumerate(tarefas):
            if progress_callback:
                progress_callback(i * 25)
            
            self.log(f"🔹 {nome}...", "step")
            
            try:
                arquivos, bytes_liberados = func()
                self.stats["total_arquivos"] += arquivos
                self.stats["total_bytes"] += bytes_liberados
                
                if arquivos > 0:
                    self.log(f"  {formatar_tamanho(bytes_liberados)} liberados", "success")
            except Exception as e:
                self.stats["erros"] += 1
                self.log(f"  Erro: {e}", "error")
        
        self.stats["tempo_total"] = time.time() - inicio # type: ignore
        
        # Resumo
        print(f"\n  ✅ Total: {self.stats['total_arquivos']:,} arquivos, {formatar_tamanho(self.stats['total_bytes'])}")
        print(f"  ⏱️  Tempo: {self.stats['tempo_total']:.1f} segundos")
        
        if progress_callback:
            progress_callback(100)
        
        mensagem = f"{self.stats['total_arquivos']} arquivos, {formatar_tamanho(self.stats['total_bytes'])}"
        return True, mensagem


class SistemaLimpeza:
    """
    Fachada principal - apenas modo rápido
    Interface unificada para o sistema de limpeza
    """
    
    def __init__(self, dry_run: bool = False, verbose: bool = False, quiet: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.quiet = quiet
        self.modo = ModoTipo.RAPIDO
        self._impl = ModoRapido(dry_run=dry_run, verbose=verbose)
    
    def request_interruption(self):
        """Solicita interrupção (placeholder)"""
        pass
    
    def executar_limpeza(self, progress_callback=None) -> Tuple[bool, str]:
        """
        Executa limpeza no modo rápido
        """
        print("\n" + "="*60)
        print("⚡ CLEANCROW - MODO RÁPIDO")
        print("="*60)
        
        if self.dry_run:
            print("🔍 MODO SIMULAÇÃO - Nenhum arquivo será deletado")
        
        print("="*60 + "\n")
        
        return self._impl.executar(progress_callback)
    
    def executar_atualizacao(self, progress_callback=None) -> Tuple[bool, str]:
        """Placeholder para compatibilidade"""
        if progress_callback:
            progress_callback(100)
        return True, "Sistema atualizado"