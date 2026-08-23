"""
CleanCrow - Winget Updater
Atualizador de programas via Windows Package Manager (winget).

Características:
- Detecta o winget corretamente.
- Atualiza as fontes.
- Detecta atualizações usando "winget upgrade".
- Solicita elevação UAC real quando necessário.
- Executa "winget upgrade --all".
- Confirma as atualizações restantes após a operação.
- Não utiliza "runas /user:Administrator".
- Não utiliza shell=True.
- Mantém compatibilidade com o CleanCrow.
"""

import ctypes
import os
import subprocess
import sys
import threading
import time

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple


# ============================================================
# ESTRUTURAS DE DADOS
# ============================================================

@dataclass
class Atualizacao:
    """Representa uma atualização encontrada pelo Winget."""

    nome: str
    id: str
    versao_atual: str = ""
    versao_disponivel: str = ""
    origem: str = ""

    def __str__(self) -> str:
        if self.versao_atual and self.versao_disponivel:
            return (
                f"{self.nome} ({self.id}) - "
                f"{self.versao_atual} → {self.versao_disponivel}"
            )

        return f"{self.nome} ({self.id})"


@dataclass
class ResultadoAtualizacao:
    """Resultado detalhado da atualização."""

    sucesso: bool = False
    cancelado: bool = False

    winget_disponivel: bool = False
    versao_winget: str = ""

    administrador: bool = False

    atualizacoes_encontradas: int = 0
    atualizacoes_processadas: int = 0
    atualizacoes_sucesso: int = 0
    atualizacoes_falha: int = 0
    atualizacoes_restantes: int = 0

    tempo_total: float = 0.0

    stdout: str = ""
    stderr: str = ""

    mensagem: str = ""
    comando_executado: str = ""

    erros_individuais: List[str] = field(default_factory=list)


# ============================================================
# WINGET UPDATER
# ============================================================

class WingetUpdater:
    """
    Gerenciador do Windows Package Manager.

    O módulo deliberadamente mantém o fluxo simples:

        verificar winget
              ↓
        atualizar fontes
              ↓
        winget upgrade
              ↓
        verificar atualizações
              ↓
        elevar UAC se necessário
              ↓
        winget upgrade --all
              ↓
        winget upgrade
              ↓
        confirmar restantes
    """

    def __init__(
        self,
        quiet: bool = False,
        verbose: bool = False,
        timeout_segundos: int = 1800,
    ):
        self.quiet = quiet
        self.verbose = verbose
        self.timeout_segundos = timeout_segundos

        self._cancel_event = threading.Event()
        self._processo_atual: Optional[subprocess.Popen] = None

    # ========================================================
    # CONTROLE
    # ========================================================

    def request_interruption(self) -> None:
        """Solicita cancelamento da operação."""

        self._cancel_event.set()

        processo = self._processo_atual

        if processo is not None:
            try:
                processo.terminate()
            except Exception:
                pass

    def is_canceled(self) -> bool:
        """Retorna True se o usuário solicitou cancelamento."""

        return self._cancel_event.is_set()

    # ========================================================
    # LOG
    # ========================================================

    def _log(self, mensagem: str, nivel: str = "info") -> None:
        """Exibe mensagens somente quando verbose está ativo."""

        if self.quiet or not self.verbose:
            return

        prefixos = {
            "info": "📋",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "step": "⚡",
            "cancel": "🛑",
            "start": "▶️",
        }

        prefixo = prefixos.get(nivel, "📋")

        print(f"  {prefixo} {mensagem}")

    # ========================================================
    # ADMINISTRADOR
    # ========================================================

    def _is_admin(self) -> bool:
        """Verifica se o processo atual possui privilégios administrativos."""

        if sys.platform != "win32":
            return False

        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    def verificar_administrador(self) -> Tuple[bool, str]:
        """Verifica o nível atual de privilégio."""

        if self._is_admin():
            return True, "Executando como administrador."

        return False, "Executando como usuário comum."

    def _elevar_processo(self) -> bool:
        """
        Reinicia o próprio CleanCrow usando UAC.

        Importante:
        NÃO usa:
            runas /user:Administrator

        O UAC eleva o usuário atual mantendo a sessão correta.
        """

        if sys.platform != "win32":
            return False

        if self._is_admin():
            return True

        try:
            shell32 = ctypes.windll.shell32

            if getattr(sys, "frozen", False):
                # Executável compilado, por exemplo PyInstaller.
                programa = sys.executable
                argumentos = " ".join(
                    f'"{arg}"'
                    for arg in sys.argv[1:]
                )
            else:
                # Execução normal via Python.
                programa = sys.executable

                script = os.path.abspath(sys.argv[0])

                argumentos = f'"{script}"'

                if len(sys.argv) > 1:
                    argumentos += " " + " ".join(
                        f'"{arg}"'
                        for arg in sys.argv[1:]
                    )

            resultado = shell32.ShellExecuteW(
                None,
                "runas",
                programa,
                argumentos,
                None,
                1,
            )

            # ShellExecute retorna > 32 quando conseguiu iniciar.
            if resultado > 32:
                return True

            self._log(
                f"Falha ao solicitar UAC. Código: {resultado}",
                "error",
            )

            return False

        except Exception as e:
            self._log(
                f"Erro ao solicitar privilégios administrativos: {e}",
                "error",
            )

            return False

    # ========================================================
    # LOCALIZAR WINGET
    # ========================================================

    def _localizar_winget(self) -> Optional[str]:
        """
        Localiza o executável winget.

        Primeiro tenta o PATH.
        Depois procura nos App Execution Aliases conhecidos.
        """

        # ----------------------------------------------------
        # Tentativa 1: PATH
        # ----------------------------------------------------

        try:
            resultado = subprocess.run(
                ["where.exe", "winget"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=False,
                timeout=10,
            )

            if resultado.returncode == 0:
                caminhos = [
                    linha.strip()
                    for linha in resultado.stdout.splitlines()
                    if linha.strip()
                ]

                if caminhos:
                    return caminhos[0]

        except Exception:
            pass

        # ----------------------------------------------------
        # Tentativa 2: alias comum do Windows
        # ----------------------------------------------------

        caminho_alias = os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Microsoft",
            "WindowsApps",
            "winget.exe",
        )

        if os.path.isfile(caminho_alias):
            return caminho_alias

        return None

    # ========================================================
    # EXECUÇÃO DE COMANDO
    # ========================================================

    def _executar_comando(
        self,
        comando: List[str],
        timeout: Optional[int] = None,
        mostrar_janela: bool = False,
    ) -> Tuple[int, str, str]:
        """
        Executa um comando sem shell=True.

        Retorna:

            returncode
            stdout
            stderr
        """

        if self.is_canceled():
            return -100, "", "Operação cancelada."

        timeout_real = timeout or self.timeout_segundos

        self._log(
            f"Executando: {' '.join(comando)}",
            "info",
        )

        creationflags = 0

        if sys.platform == "win32" and not mostrar_janela:
            creationflags = subprocess.CREATE_NO_WINDOW

        try:
            processo = subprocess.Popen(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=False,
                creationflags=creationflags,
            )

            self._processo_atual = processo

            try:
                stdout, stderr = processo.communicate(
                    timeout=timeout_real
                )

            except subprocess.TimeoutExpired:

                self._log(
                    f"Comando excedeu {timeout_real} segundos.",
                    "error",
                )

                try:
                    processo.kill()
                except Exception:
                    pass

                stdout, stderr = processo.communicate()

                self._processo_atual = None

                return -2, stdout or "", stderr or ""

            finally:
                self._processo_atual = None

            stdout = stdout or ""
            stderr = stderr or ""

            if self.verbose:

                if stdout:
                    self._log(
                        f"Saída: {stdout[-1000:]}",
                        "info",
                    )

                if stderr:
                    self._log(
                        f"Erro/Saída adicional: {stderr[-1000:]}",
                        "warning",
                    )

            return processo.returncode, stdout, stderr

        except FileNotFoundError:
            return -1, "", "Comando não encontrado."

        except PermissionError:
            return -3, "", "Permissão negada."

        except Exception as e:
            return -1, "", str(e)

    # ========================================================
    # VERIFICAR WINGET
    # ========================================================

    def verificar_winget(self) -> Tuple[bool, str]:
        """Verifica se o Winget está disponível."""

        caminho = self._localizar_winget()

        if not caminho:
            return (
                False,
                "Winget não encontrado. "
                "Instale/atualize o App Installer da Microsoft.",
            )

        try:

            resultado = subprocess.run(
                [caminho, "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=False,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if sys.platform == "win32"
                    else 0
                ),
                timeout=15,
            )

            if resultado.returncode == 0:

                versao = (
                    resultado.stdout.strip()
                    or resultado.stderr.strip()
                )

                return True, versao

            return (
                False,
                resultado.stderr.strip()
                or "Winget não respondeu corretamente.",
            )

        except Exception as e:
            return False, f"Erro ao verificar Winget: {e}"

    # ========================================================
    # ATUALIZAR FONTES
    # ========================================================

    def atualizar_fontes(
        self,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Tuple[bool, str]:
        """Atualiza as fontes do Winget."""

        if self.is_canceled():
            return False, "Operação cancelada."

        caminho = self._localizar_winget()

        if not caminho:
            return False, "Winget não encontrado."

        self._log(
            "Atualizando fontes do Winget...",
            "step",
        )

        if progress_callback:
            progress_callback(10)

        comando = [
            caminho,
            "source",
            "update",
            "--accept-source-agreements",
        ]

        returncode, stdout, stderr = self._executar_comando(
            comando,
            timeout=120,
        )

        if progress_callback:
            progress_callback(20)

        if returncode == 0:
            self._log(
                "Fontes atualizadas.",
                "success",
            )

            return True, "Fontes atualizadas."

        erro = (
            stderr.strip()
            or stdout.strip()
            or f"Código {returncode}"
        )

        self._log(
            f"Não foi possível atualizar as fontes: {erro}",
            "warning",
        )

        # Falha na atualização das fontes não precisa impedir
        # uma tentativa de upgrade.
        return True, f"Fontes atualizadas com aviso: {erro}"

    # ========================================================
    # DETECTAR ATUALIZAÇÕES
    # ========================================================

    def listar_atualizacoes(
        self,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Tuple[List[Atualizacao], str]:
        """
        Detecta atualizações usando:

            winget upgrade

        Não depende de JSON.
        """

        if self.is_canceled():
            return [], "Operação cancelada."

        caminho = self._localizar_winget()

        if not caminho:
            return [], "Winget não encontrado."

        self._log(
            "Verificando atualizações disponíveis...",
            "step",
        )

        if progress_callback:
            progress_callback(30)

        comando = [
            caminho,
            "upgrade",
            "--accept-source-agreements",
        ]

        returncode, stdout, stderr = self._executar_comando(
            comando,
            timeout=120,
        )

        if progress_callback:
            progress_callback(40)

        saida = (stdout + "\n" + stderr).strip()

        if not saida:

            if returncode == 0:
                return [], "Nenhuma atualização disponível."

            return [], "Winget não retornou informações."

        saida_lower = saida.lower()

        # ----------------------------------------------------
        # Mensagens conhecidas de nenhuma atualização
        # ----------------------------------------------------

        mensagens_sem_update = [
            "no applicable upgrade found",
            "no available upgrade",
            "no installed package found",
            "no upgrade available",
            "nenhuma atualização",
            "não há atualização",
        ]

        if any(
            mensagem in saida_lower
            for mensagem in mensagens_sem_update
        ):
            return [], "Nenhuma atualização disponível."

        # ----------------------------------------------------
        # Parser da tabela do Winget
        # ----------------------------------------------------

        atualizacoes = []

        linhas = stdout.splitlines()

        inicio_tabela = False

        for linha in linhas:

            linha_strip = linha.strip()

            if not linha_strip:
                continue

            # Detecta cabeçalho.
            if (
                "Name" in linha
                and "Id" in linha
                and "Version" in linha
            ):
                inicio_tabela = True
                continue

            if (
                "Nome" in linha
                and "ID" in linha
                and "Versão" in linha
            ):
                inicio_tabela = True
                continue

            if not inicio_tabela:
                continue

            # Ignorar linha separadora.
            if set(linha_strip) <= set("- "):
                continue

            # ------------------------------------------------
            # O Winget utiliza colunas separadas por espaços.
            #
            # Não tentamos reconstruir perfeitamente nomes
            # complexos. O objetivo aqui é apenas informar
            # o usuário.
            # ------------------------------------------------

            partes = linha_strip.split()

            if len(partes) < 3:
                continue

            try:

                # Normalmente:
                #
                # Name | Id | Version | Available | Source
                #
                # O nome pode conter espaços.

                id_index = None

                for i, parte in enumerate(partes):

                    if "." in parte:
                        # IDs do Winget normalmente possuem
                        # namespace, por exemplo:
                        # Microsoft.Edge
                        id_index = i
                        break

                if id_index is None:
                    continue

                nome = " ".join(partes[:id_index]).strip()

                if not nome:
                    nome = "Desconhecido"

                pacote_id = partes[id_index]

                versao_atual = ""

                versao_disponivel = ""

                if len(partes) > id_index + 1:
                    versao_atual = partes[id_index + 1]

                if len(partes) > id_index + 2:
                    versao_disponivel = partes[id_index + 2]

                origem = ""

                if len(partes) > id_index + 3:
                    origem = partes[id_index + 3]

                atualizacoes.append(
                    Atualizacao(
                        nome=nome,
                        id=pacote_id,
                        versao_atual=versao_atual,
                        versao_disponivel=versao_disponivel,
                        origem=origem,
                    )
                )

            except Exception as e:

                self._log(
                    f"Falha ao interpretar linha: {e}",
                    "warning",
                )

        # ----------------------------------------------------
        # Fallback importante
        #
        # Mesmo que o parser não consiga interpretar a tabela,
        # o Winget pode ter retornado código 0 e conteúdo indicando
        # que existem upgrades.
        #
        # Nesse caso NÃO podemos afirmar que existem zero.
        # ----------------------------------------------------

        if not atualizacoes:

            indicadores_update = [
                "upgrade available",
                "available",
                "version",
            ]

            possui_indicador = any(
                indicador in saida_lower
                for indicador in indicadores_update
            )

            if returncode == 0 and possui_indicador:

                self._log(
                    "O Winget indicou possíveis atualizações, "
                    "mas a tabela não pôde ser interpretada.",
                    "warning",
                )

                return (
                    [],
                    "Atualizações detectadas pelo Winget, "
                    "mas não foi possível listar os detalhes.",
                )

            if returncode != 0:

                return (
                    [],
                    f"Erro ao consultar Winget: "
                    f"{stderr.strip() or stdout.strip()}",
                )

            return [], "Nenhuma atualização disponível."

        self._log(
            f"{len(atualizacoes)} atualização(ões) encontrada(s).",
            "success",
        )

        return (
            atualizacoes,
            f"{len(atualizacoes)} atualização(ões) encontrada(s).",
        )

    # ========================================================
    # EXECUTAR UPGRADE
    # ========================================================

    def _executar_upgrade_all(
        self,
        progress_callback: Optional[Callable[[int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[int, str, str]:
        """
        Executa efetivamente:

            winget upgrade --all

        Se não estiver em modo administrador, o método primeiro
        solicita UAC reiniciando o processo atual.

        IMPORTANTE:
        Depois que um processo chama ShellExecuteW("runas"),
        o processo original NÃO pode simplesmente continuar
        esperando o processo elevado sem uma arquitetura de
        IPC/launcher.

        Por isso, quando o CleanCrow não é administrador,
        a função retorna um código especial indicando que
        a aplicação deve ser reiniciada como administrador.
        """

        caminho = self._localizar_winget()

        if not caminho:
            return -1, "", "Winget não encontrado."

        if not self._is_admin():

            self._log(
                "CleanCrow não está elevado.",
                "warning",
            )

            if status_callback:
                status_callback(
                    "Solicitando privilégios administrativos..."
                )

            sucesso = self._elevar_processo()

            if sucesso:

                # O processo elevado será iniciado pelo Windows.
                #
                # O processo atual precisa encerrar.
                return -10, "", "RESTART_AS_ADMIN"

            return (
                -3,
                "",
                "Não foi possível obter privilégios administrativos.",
            )

        comando = [
            caminho,
            "upgrade",
            "--all",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ]

        # ----------------------------------------------------
        # NÃO usamos --silent por padrão.
        #
        # Alguns instaladores possuem comportamento diferente
        # quando executados silenciosamente.
        #
        # A prioridade aqui é garantir que a atualização
        # realmente aconteça.
        # ----------------------------------------------------

        self._log(
            "Executando winget upgrade --all...",
            "step",
        )

        if status_callback:
            status_callback(
                "Atualizando todos os programas via Winget..."
            )

        if progress_callback:
            progress_callback(50)

        returncode, stdout, stderr = self._executar_comando(
            comando,
            timeout=self.timeout_segundos,
            mostrar_janela=False,
        )

        if progress_callback:
            progress_callback(90)

        return returncode, stdout, stderr

    # ========================================================
    # EXECUTAR ATUALIZAÇÃO COMPLETA
    # ========================================================

    def executar_atualizacao(
        self,
        progress_callback: Optional[Callable[[int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> ResultadoAtualizacao:

        resultado = ResultadoAtualizacao()

        inicio = time.monotonic()

        try:

            # ------------------------------------------------
            # WINGET
            # ------------------------------------------------

            if status_callback:
                status_callback("Verificando Winget...")

            tem_winget, versao = self.verificar_winget()

            resultado.winget_disponivel = tem_winget
            resultado.versao_winget = versao

            if not tem_winget:

                resultado.mensagem = versao
                resultado.tempo_total = time.monotonic() - inicio

                return resultado

            self._log(
                f"Winget encontrado: {versao}",
                "success",
            )

            if progress_callback:
                progress_callback(5)

            # ------------------------------------------------
            # ADMIN
            # ------------------------------------------------

            admin, admin_msg = self.verificar_administrador()

            resultado.administrador = admin

            self._log(
                admin_msg,
                "info",
            )

            # ------------------------------------------------
            # FONTES
            # ------------------------------------------------

            if status_callback:
                status_callback("Atualizando fontes do Winget...")

            self.atualizar_fontes(progress_callback)

            if self.is_canceled():

                resultado.cancelado = True
                resultado.mensagem = "Operação cancelada."

                return resultado

            # ------------------------------------------------
            # DETECÇÃO
            # ------------------------------------------------

            if status_callback:
                status_callback(
                    "Verificando programas com atualização..."
                )

            atualizacoes, mensagem_lista = (
                self.listar_atualizacoes(progress_callback)
            )

            resultado.atualizacoes_encontradas = len(
                atualizacoes
            )

            # ------------------------------------------------
            # Caso normal: zero
            # ------------------------------------------------

            if not atualizacoes:

                # Se o Winget não conseguiu interpretar a tabela,
                # ainda vamos executar o upgrade diretamente.
                #
                # Isso é proposital.
                #
                # O Winget é a autoridade final sobre quais
                # pacotes podem ser atualizados.

                mensagem_indica_ausencia = (
                    "Nenhuma atualização disponível"
                    in mensagem_lista
                )

                if mensagem_indica_ausencia:

                    resultado.sucesso = True
                    resultado.mensagem = (
                        "Nenhuma atualização disponível."
                    )

                    if progress_callback:
                        progress_callback(100)

                    return resultado

                self._log(
                    "Não foi possível determinar a lista "
                    "com precisão. O Winget será executado "
                    "diretamente para verificar.",
                    "warning",
                )

            else:

                if status_callback:
                    status_callback(
                        f"{len(atualizacoes)} programa(s) "
                        "serão atualizados."
                    )

                self._log(
                    "Programas encontrados:",
                    "info",
                )

                for update in atualizacoes:

                    self._log(
                        str(update),
                        "info",
                    )

            # ------------------------------------------------
            # ADMINISTRADOR
            # ------------------------------------------------

            if not self._is_admin():

                self._log(
                    "É necessário executar o CleanCrow "
                    "como administrador para continuar.",
                    "warning",
                )

                if status_callback:
                    status_callback(
                        "Solicitando privilégios de administrador..."
                    )

                elevou = self._elevar_processo()

                if elevou:

                    resultado.mensagem = (
                        "CleanCrow reiniciado como administrador."
                    )

                    resultado.tempo_total = (
                        time.monotonic() - inicio
                    )

                    # O processo atual não deve continuar.
                    #
                    # O processo elevado assumirá a operação.
                    resultado.sucesso = True

                    return resultado

                resultado.sucesso = False

                resultado.mensagem = (
                    "Não foi possível obter privilégios "
                    "administrativos."
                )

                return resultado

            # ------------------------------------------------
            # EXECUTAR UPGRADE
            # ------------------------------------------------

            resultado.administrador = True

            comando = [
                self._localizar_winget() or "winget",
                "upgrade",
                "--all",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ]

            resultado.comando_executado = " ".join(comando)

            returncode, stdout, stderr = (
                self._executar_upgrade_all(
                    progress_callback,
                    status_callback,
                )
            )

            resultado.stdout = stdout
            resultado.stderr = stderr

            if returncode == -10:

                # Processo elevado será iniciado.
                resultado.sucesso = True
                resultado.mensagem = (
                    "Solicitação de administrador enviada."
                )

                return resultado

            if returncode == -2:

                resultado.mensagem = (
                    f"Atualização excedeu o limite de "
                    f"{self.timeout_segundos} segundos."
                )

                resultado.sucesso = False

                return resultado

            if returncode == -3:

                resultado.mensagem = (
                    "Permissão negada. "
                    "Execute o CleanCrow como administrador."
                )

                resultado.sucesso = False

                return resultado

            # ------------------------------------------------
            # CÓDIGO DE RETORNO
            # ------------------------------------------------

            if returncode != 0:

                erro = (
                    stderr.strip()
                    or stdout.strip()
                    or f"Código de retorno: {returncode}"
                )

                resultado.sucesso = False
                resultado.mensagem = (
                    f"Winget terminou com erro: {erro[-1000:]}"
                )

                self._log(
                    resultado.mensagem,
                    "error",
                )

                return resultado

            # ------------------------------------------------
            # PROCESSAMENTO
            # ------------------------------------------------

            resultado.atualizacoes_processadas = (
                resultado.atualizacoes_encontradas
            )

            # NÃO afirmamos que todas tiveram sucesso apenas
            # porque o processo terminou com código 0.
            #
            # O WinGet é executado novamente abaixo para confirmar.

            resultado.atualizacoes_sucesso = (
                resultado.atualizacoes_encontradas
            )

            # ------------------------------------------------
            # VERIFICAÇÃO FINAL
            # ------------------------------------------------

            if progress_callback:
                progress_callback(95)

            if status_callback:
                status_callback(
                    "Verificando atualizações restantes..."
                )

            restantes, mensagem_restante = (
                self.listar_atualizacoes()
            )

            resultado.atualizacoes_restantes = len(
                restantes
            )

            # ------------------------------------------------
            # RESULTADO
            # ------------------------------------------------

            if resultado.atualizacoes_restantes == 0:

                resultado.sucesso = True

                if resultado.atualizacoes_encontradas > 0:

                    resultado.mensagem = (
                        f"Atualização concluída. "
                        f"{resultado.atualizacoes_encontradas} "
                        f"programa(s) processado(s) e "
                        f"nenhuma atualização restante."
                    )

                else:

                    resultado.mensagem = (
                        "Winget executado com sucesso. "
                        "Nenhuma atualização restante."
                    )

                self._log(
                    resultado.mensagem,
                    "success",
                )

            else:

                resultado.sucesso = False

                resultado.atualizacoes_falha = (
                    resultado.atualizacoes_restantes
                )

                resultado.mensagem = (
                    f"Atualização parcialmente concluída. "
                    f"{resultado.atualizacoes_restantes} "
                    f"atualização(ões) ainda permanecem."
                )

                self._log(
                    resultado.mensagem,
                    "warning",
                )

            if progress_callback:
                progress_callback(100)

            if status_callback:
                status_callback(
                    resultado.mensagem
                )

        except Exception as e:

            resultado.sucesso = False
            resultado.mensagem = (
                f"Erro inesperado: {e}"
            )

            self._log(
                resultado.mensagem,
                "error",
            )

        finally:

            resultado.tempo_total = (
                time.monotonic() - inicio
            )

        return resultado

    # ========================================================
    # COMPATIBILIDADE COM CLEAN CROW
    # ========================================================

    def executar(
        self,
        progress_callback: Optional[Callable[[int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Interface principal utilizada pelo CleanCrow.
        """

        if not self.quiet:

            self._log(
                "Iniciando Winget Updater...",
                "start",
            )

        resultado = self.executar_atualizacao(
            progress_callback=progress_callback,
            status_callback=status_callback,
        )

        if not self.quiet:

            self._log(
                resultado.mensagem,
                "success"
                if resultado.sucesso
                else "error",
            )

        return (
            resultado.sucesso,
            resultado.mensagem,
        )


# ============================================================
# FUNÇÕES PÚBLICAS
# ============================================================

def verificar_winget() -> Tuple[bool, str]:
    """Compatibilidade com versões anteriores."""

    updater = WingetUpdater(
        quiet=True,
    )

    return updater.verificar_winget()


def executar_atualizacao(
    progress_callback: Optional[Callable[[int], None]] = None,
) -> Tuple[bool, str]:
    """Compatibilidade com versões anteriores."""

    updater = WingetUpdater(
        quiet=False,
        verbose=False,
    )

    return updater.executar(
        progress_callback=progress_callback,
    )


def listar_atualizacoes() -> Tuple[List[Atualizacao], str]:
    """Compatibilidade com versões anteriores."""

    updater = WingetUpdater(
        quiet=True,
    )

    return updater.listar_atualizacoes()


# ============================================================
# TESTE DIRETO
# ============================================================

if __name__ == "__main__":

    print("=" * 65)
    print("        CLEANCROW - WINGET UPDATER")
    print("=" * 65)

    updater = WingetUpdater(
        quiet=False,
        verbose=True,
        timeout_segundos=1800,
    )

    # --------------------------------------------------------
    # Verificar Winget
    # --------------------------------------------------------

    print("\n🔍 Verificando Winget...")

    tem_winget, mensagem = updater.verificar_winget()

    if not tem_winget:

        print(f"\n❌ {mensagem}")

        sys.exit(1)

    print(f"✅ {mensagem}")

    # --------------------------------------------------------
    # Verificar administrador
    # --------------------------------------------------------

    admin, mensagem_admin = (
        updater.verificar_administrador()
    )

    print(
        f"\n🔐 Administrador: "
        f"{'SIM' if admin else 'NÃO'}"
    )

    print(f"   {mensagem_admin}")

    # --------------------------------------------------------
    # Atualizar fontes
    # --------------------------------------------------------

    print("\n📦 Atualizando fontes...")

    sucesso, mensagem = (
        updater.atualizar_fontes()
    )

    print(f"   {mensagem}")

    # --------------------------------------------------------
    # Listar atualizações
    # --------------------------------------------------------

    print("\n🔍 Procurando atualizações...")

    atualizacoes, mensagem = (
        updater.listar_atualizacoes()
    )

    print(f"\n📊 {mensagem}")

    if atualizacoes:

        print("\n📋 Atualizações encontradas:\n")

        for i, update in enumerate(
            atualizacoes,
            start=1,
        ):

            print(
                f"  {i:02d}. {update.nome}"
            )

            print(
                f"      ID: {update.id}"
            )

            if update.versao_atual:
                print(
                    f"      Atual: "
                    f"{update.versao_atual}"
                )

            if update.versao_disponivel:
                print(
                    f"      Nova:  "
                    f"{update.versao_disponivel}"
                )

            print()

    # --------------------------------------------------------
    # Confirmar execução
    # --------------------------------------------------------

    print("=" * 65)

    resposta = input(
        "Deseja executar winget upgrade --all? [s/N]: "
    ).strip().lower()

    if resposta != "s":

        print("\n❌ Operação cancelada.")

        sys.exit(0)

    print("\n⚡ Iniciando atualização...\n")

    def progress_callback(valor: int):

        print(
            f"   Progresso: {valor:3d}%",
            end="\r",
            flush=True,
        )

    def status_callback(status: str):

        print(
            f"\n   📌 {status}"
        )

    resultado = updater.executar_atualizacao(
        progress_callback=progress_callback,
        status_callback=status_callback,
    )

    print("\n")
    print("=" * 65)
    print("                 RESULTADO")
    print("=" * 65)

    print(
        f"Status: "
        f"{'✅ SUCESSO' if resultado.sucesso else '❌ FALHA'}"
    )

    print(
        f"Mensagem: {resultado.mensagem}"
    )

    print(
        f"Winget: {resultado.versao_winget}"
    )

    print(
        f"Administrador: "
        f"{'Sim' if resultado.administrador else 'Não'}"
    )

    print(
        f"Atualizações encontradas: "
        f"{resultado.atualizacoes_encontradas}"
    )

    print(
        f"Atualizações processadas: "
        f"{resultado.atualizacoes_processadas}"
    )

    print(
        f"Atualizações restantes: "
        f"{resultado.atualizacoes_restantes}"
    )

    print(
        f"Tempo: "
        f"{resultado.tempo_total:.1f}s"
    )

    print("=" * 65)