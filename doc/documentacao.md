
---

## 📄 DOCUMENTAÇÃO.md (Documentação Detalhada)

```markdown
# 📘 Documentação Técnica do CleanCrow

## 1. Visão Geral

O **CleanCrow** é um aplicativo de desktop para Windows que automatiza tarefas de manutenção, limpeza e atualização do sistema. Ele foi desenvolvido em Python e utiliza a biblioteca PyQt5 para a interface gráfica. O projeto é estruturado de forma modular, permitindo a fácil adição de novos "cleaners" (módulos de limpeza).

---

## 2. Arquitetura

O projeto segue uma arquitetura em camadas:

### 2.1 Camada de Interface (interface.py)
- Responsável pela interação com o usuário.
- Utiliza PyQt5 para criar a interface gráfica.
- Exibe logs em tempo real, barra de progresso e status de operações.
- Controla os modos de limpeza (Normal, Rápido, Seguro).

### 2.2 Camada de Motor (core/engine.py)
- Orquestra a execução de todos os cleaners.
- Gerencia o scan (detecção) e a limpeza.
- Executa operações em paralelo (ThreadPoolExecutor).
- Fornece callbacks para atualização de progresso e logs.

### 2.3 Camada de Cleaners (core/cleaners/)
- Cada cleaner é responsável por uma categoria específica de limpeza.
- Todos herdam da classe base `BaseCleaner`.
- Implementam métodos para detectar, calcular tamanho e limpar.

### 2.4 Camada de APIs do Windows (core/win32_api.py)
- Utiliza `ctypes` para acessar APIs nativas do Windows.
- Exemplos: esvaziar lixeira, verificar permissões de administrador, obter espaço em disco.

### 2.5 Camada de Logs (core/logger.py)
- Registra todas as operações realizadas.
- Suporta callbacks para exibição em tempo real.
- Exporta logs em formato JSON.

---

## 3. Detalhamento dos Cleaners

| Nome do Cleaner | Descrição | Requer Admin | Risco |
|---|---|---|---|
| `TempCleaner` | Limpa arquivos temporários do usuário | Não | 🟢 Seguro |
| `WindowsTempCleaner` | Limpa `C:/Windows/Temp` | Sim | 🟢 Seguro |
| `RecycleBinCleaner` | Esvazia a Lixeira | Não | 🟢 Seguro |
| `ThumbnailCleaner` | Limpa cache de miniaturas | Não | 🟢 Seguro |
| `WERCleaner` | Limpa relatórios de erro | Não | 🟢 Seguro |
| `WindowsUpdateCleaner` | Limpa cache do Windows Update | Sim | 🟡 Avançado |
| `BrowsersCleaner` | Limpa cache de navegadores | Não | 🟢 Seguro |
| `WebCacheCleaner` | Limpa cache de aplicações web | Não | 🟠 Especial |
| `NvidiaCacheCleaner` | Limpa shader cache NVIDIA | Não | 🟡 Avançado |
| `AmdCacheCleaner` | Limpa shader cache AMD | Não | 🟡 Avançado |
| `SystemCleaner` | Limpeza avançada (cleanmgr + DISM) | Sim | 🟡 Avançado |
| `DNSCleaner` | Limpa cache DNS | Sim | 🟢 Seguro |
| `ComponentStoreCleaner` | Limpa Component Store via DISM | Sim | 🟡 Avançado |

---

## 4. Modos de Limpeza

### 4.1 Modo Normal
- Executa todos os cleaners disponíveis (exceto WebCache).
- Recomendado para uso geral.

### 4.2 Modo Rápido
- Executa apenas cleaners de caches e temporários.
- Mais rápido, ideal para limpeza frequente.

### 4.3 Modo Seguro
- Executa apenas cleaners sem risco.
- Não fecha navegadores nem executa comandos avançados.

---

## 5. Integração com Winget

O módulo `winget_updater.py` automatiza a atualização de programas via Windows Package Manager:

1. **Verifica se o winget está instalado**.
2. **Atualiza as fontes do repositório**.
3. **Detecta atualizações disponíveis** (parsing da saída do `winget upgrade`).
4. **Solicita elevação UAC** se necessário.
5. **Executa `winget upgrade --all`**.
6. **Verifica atualizações restantes** após a operação.

---

## 6. Logs

O sistema de logs (`core/logger.py`) registra todas as operações com os seguintes níveis:

| Nível | Descrição |
|---|---|
| `info` | Informações gerais |
| `success` | Operação bem-sucedida |
| `warning` | Avisos (ex: arquivo bloqueado) |
| `error` | Erros |
| `step` | Etapas da limpeza |
| `system` | Mensagens do sistema |
| `detail` | Detalhes técnicos |

---

## 7. Requisitos de Sistema

- **SO**: Windows 10 ou 11 (64 bits)
- **Python**: 3.10 ou superior
- **Dependências**:
  - `PyQt5`
  - `qtawesome`
  - `PyInstaller` (apenas para build)

---

## 8. Build do Executável

Para gerar o executável, utilize o arquivo de especificação PyInstaller:

```bash
pyinstaller CLEANCROW.spec --clean