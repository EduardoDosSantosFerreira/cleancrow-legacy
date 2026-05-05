"""
CleanCrow - Modo SEGURO
Não mexe em arquivos críticos do sistema
Ideal para uso em servidores ou PCs corporativos
"""

import os
import time
from pathlib import Path
from typing import Tuple

from core.base import (
    ModoTipo, is_admin, formatar_tamanho, remover_pasta, remover_arquivos_antigos,
    limpar_cache_navegadores, esvaziar_lixeira_api
)


class ModoSeguro:
    """
    Modo SEGURO - Não mexe em system files
    - Apenas arquivos temporários do usuário
    - Cache de navegadores
    - Thumbnails
    - Lixeira
    - NÃO mexe em Windows, System32, Program Files
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
            prefixos = {"info": "📋", "success": "✅", "warning": "⚠️", "error": "❌", "step": "🔒"}
            print(f"  {prefixos.get(nivel, '📋')} {mensagem}")
    
    def limpar_temp_usuario(self) -> Tuple[int, int]:
        """Limpa apenas temp do usuário (não do sistema)"""
        total_arquivos = 0
        total_bytes = 0
        
        temp_dirs = [
            Path(os.environ.get('TEMP', '')),
            Path(os.environ.get('TMP', '')),
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
                    arquivos, bytes_liberados = remover_arquivos_antigos(dir_path, 1)
                    total_arquivos += arquivos
                    total_bytes += bytes_liberados
        
        return total_arquivos, total_bytes
    
    def limpar_thumbnails_seguro(self) -> Tuple[int, int]:
        """Limpa thumbnails do usuário atual"""
        total_arquivos = 0
        total_bytes = 0
        
        explorer_path = Path(os.environ.get('LOCALAPPDATA', '')) / "Microsoft/Windows/Explorer"
        
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
                        try:
                            size = file.stat().st_size
                            file.unlink()
                            total_arquivos += 1
                            total_bytes += size
                        except:
                            pass
        
        return total_arquivos, total_bytes
    
    def limpar_cache_navegadores_seguro(self) -> Tuple[int, int]:
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
    
    def limpar_cache_recente(self) -> Tuple[int, int]:
        """Limpa lista de arquivos recentes"""
        total_arquivos = 0
        total_bytes = 0
        
        recent_path = Path(os.environ.get('APPDATA', '')) / "Microsoft/Windows/Recent"
        
        if recent_path.exists():
            for item in recent_path.iterdir():
                try:
                    if item.is_file():
                        if self.dry_run:
                            total_arquivos += 1
                            try:
                                total_bytes += item.stat().st_size
                            except:
                                pass
                        else:
                            success, size = self._remover_arquivo_simples(item)
                            if success:
                                total_arquivos += 1
                                total_bytes += size
                except:
                    pass
        
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
    
    def executar(self, progress_callback=None) -> Tuple[bool, str]:
        """Executa limpeza no modo seguro"""
        self.log("\n🔒 MODO SEGURO - Protegido", "step")
        self.log("Apenas arquivos do usuário - NÃO mexe em system files\n", "info")
        
        inicio = time.time()
        
        tarefas = [
            ("Temp do Usuário", self.limpar_temp_usuario, 25),
            ("Cache Navegadores", self.limpar_cache_navegadores_seguro, 25),
            ("Thumbnails", self.limpar_thumbnails_seguro, 20),
            ("Arquivos Recentes", self.limpar_cache_recente, 15),
            ("Lixeira", self.limpar_lixeira, 15),
        ]
        
        for i, (nome, func, peso) in enumerate(tarefas):
            if progress_callback:
                progress_callback(i * 20)
            
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
        
        self.stats["tempo_total"] = time.time() - inicio
        
        # Resumo
        print(f"\n  ✅ Total: {self.stats['total_arquivos']:,} arquivos, {formatar_tamanho(self.stats['total_bytes'])}")
        print(f"  ⏱️  Tempo: {self.stats['tempo_total']:.1f} segundos")
        print(f"  🔒 Modo seguro: sem alterações em arquivos do sistema")
        
        if progress_callback:
            progress_callback(100)
        
        mensagem = f"{self.stats['total_arquivos']} arquivos, {formatar_tamanho(self.stats['total_bytes'])}"
        return True, mensagem