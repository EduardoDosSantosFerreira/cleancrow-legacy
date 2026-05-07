"""
CleanCrow - Winget Updater
Atualiza todos os programas via winget upgrade --all
"""

import subprocess
import sys
import os
from typing import Tuple


def verificar_winget() -> Tuple[bool, str]:
    """
    Verifica se winget está instalado
    
    Returns:
        (True, versão) se instalado, (False, erro) caso contrário
    """
    try:
        # Executar winget --version
        result = subprocess.run(
            ["winget", "--version"],
            capture_output=True,
            text=True,
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        if result.returncode == 0:
            versao = result.stdout.strip()
            return True, versao
        else:
            return False, "Winget não encontrado"
            
    except FileNotFoundError:
        return False, "Winget não está instalado. Instale o 'App Installer' da Microsoft Store."
    except Exception as e:
        return False, f"Erro: {str(e)}"


def executar_atualizacao(progress_callback=None) -> Tuple[bool, str]:
    """
    Executa winget upgrade --all
    
    Returns:
        (sucesso, mensagem)
    """
    # Verificar se winget existe
    tem_winget, msg = verificar_winget()
    
    if not tem_winget:
        return False, msg
    
    # Atualizar fonts/sources
    if progress_callback:
        progress_callback(10)
    
    # Executar winget upgrade --all
    try:
        # Comando completo
        cmd = [
            "winget", "upgrade", "--all",
            "--silent",
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--disable-interactivity"
        ]
        
        # Para debug, pode usar sem silent
        # cmd = ["winget", "upgrade", "--all"]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        # Simular progresso enquanto executa
        for i in range(20, 101, 10):
            if progress_callback:
                progress_callback(i)
        
        # Aguardar conclusão (timeout 10 minutos)
        stdout, stderr = process.communicate(timeout=600)
        
        if progress_callback:
            progress_callback(100)
        
        # Verificar resultado
        if process.returncode == 0:
            return True, "Atualização concluída com sucesso!"
        elif "No available upgrade" in stdout or "No installed package" in stdout:
            return True, "Nenhuma atualização disponível"
        else:
            erro = stderr if stderr else stdout[:200]
            return False, f"Erro na atualização: {erro}"
            
    except subprocess.TimeoutExpired:
        process.kill()
        return False, "Timeout: Atualização demorou demais"
    except Exception as e:
        return False, f"Erro: {str(e)}"


def listar_atualizacoes() -> Tuple[list, str]:
    """
    Lista programas que têm atualização disponível
    
    Returns:
        (lista_de_programas, mensagem)
    """
    tem_winget, msg = verificar_winget()
    
    if not tem_winget:
        return [], msg
    
    try:
        result = subprocess.run(
            ["winget", "upgrade"],
            capture_output=True,
            text=True,
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
            timeout=60
        )
        
        output = result.stdout
        
        if "No installed package" in output or "No available" in output:
            return [], "Nenhuma atualização disponível"
        
        # Parse simples para extrair nomes
        programas = []
        linhas = output.split('\n')
        in_table = False
        
        for linha in linhas:
            if 'Name' in linha and 'Id' in linha and 'Version' in linha:
                in_table = True
                continue
            if in_table and linha.strip() and '---' not in linha:
                # Pega o nome (primeira coluna)
                partes = linha.split()
                if partes:
                    # O nome pode ter múltiplas palavras, mas o ID geralmente é o penúltimo
                    # Simplificando: pega tudo antes do ID
                    nome = ' '.join(partes[:-3]) if len(partes) > 3 else partes[0]
                    programas.append(nome)
        
        return programas, f"{len(programas)} programa(s) com atualização"
        
    except Exception as e:
        return [], f"Erro: {str(e)}"


# Para teste direto
if __name__ == "__main__":
    print("=" * 50)
    print("Teste do Winget Updater")
    print("=" * 50)
    
    # Verificar winget
    tem, msg = verificar_winget()
    print(f"Winget: {msg}")
    
    if tem:
        print("\nListando atualizações disponíveis...")
        programas, msg2 = listar_atualizacoes()
        print(f"Resultado: {msg2}")
        
        if programas:
            print("\nProgramas para atualizar:")
            for p in programas[:10]:
                print(f"  - {p}")
            if len(programas) > 10:
                print(f"  ... e mais {len(programas) - 10}")
        
        print("\nDeseja executar a atualização? (s/n)")
        resposta = input().lower()
        if resposta == 's':
            print("\nExecutando atualização...")
            success, result = executar_atualizacao()
            print(f"Resultado: {result}")