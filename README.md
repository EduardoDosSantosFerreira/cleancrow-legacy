# 🐦‍⬛ CleanCrow (Legacy)

CleanCrow é uma aplicação desktop para **manutenção, limpeza e otimização de sistemas Windows**, desenvolvida em Python com interface gráfica em PyQt5.

O software automatiza tarefas comuns de manutenção, removendo arquivos desnecessários, executando rotinas de limpeza e auxiliando no gerenciamento de pacotes instalados no sistema.

---

## ⚙️ Funcionalidades

* 🧹 **Limpeza de arquivos temporários**

  * Diretórios de `%TEMP%`
  * Cache do sistema
  * Arquivos residuais comuns

* 🗑️ **Remoção de arquivos desnecessários**

  * Arquivos de log antigos
  * Resíduos de aplicações

* ⚡ **Otimizações básicas do sistema**

  * Execução de comandos nativos do Windows
  * Limpeza de componentes acumulados

* 📦 **Integração com winget**

  * Instalação e atualização de pacotes
  * Automação de comandos via CLI

* 📊 **Execução com feedback em tempo real**

  * Barra de progresso
  * Logs detalhados por operação

* 🔐 **Elevação de privilégios automática**

  * Execução como administrador quando necessário

---

## 🏗️ Arquitetura do Projeto

O projeto segue uma separação simples entre interface e lógica:

* **Camada de Interface (`interface.py`)**

  * Construída com PyQt5
  * Responsável pela interação com o usuário
  * Atualização de logs e progresso

* **Camada de Lógica (`limpeza_sistema.py`)**

  * Execução das rotinas de limpeza
  * Chamadas ao sistema operacional
  * Manipulação de arquivos e diretórios

* **Ponto de Entrada (`main.py`)**

  * Inicialização da aplicação
  * Controle de execução e permissões

---

## 📁 Estrutura de Diretórios

```id="c8o1sl"
cleancrow-legacy/
│
├── main.py
├── interface.py
├── limpeza_sistema.py
│
├── dist/
├── src/
│   └── assets/
│
├── index.html
├── cleancrow.spec
├── LICENSE
└── README.md
```

---

## 🚀 Execução

### Pré-requisitos

* Python 3.10 ou superior
* Sistema operacional Windows
* Pip instalado

### Instalação de dependências

```bash id="y2n0bb"
pip install PyQt5
```

### Execução

```bash id="x2ktm4"
python main.py
```

> O software solicita elevação de privilégios automaticamente quando necessário.

---

## 🏗️ Build do Executável

### Utilizando PyInstaller

```bash id="5k2w7s"
pyinstaller --onefile limpeza_sistema.py
```

Ou com o arquivo de configuração:

```bash id="9z0p2u"
pyinstaller cleancrow.spec
```

Saída:

```id="v4r2dx"
/dist/cleancrow.exe
```

---

## 🔐 Permissões e Segurança

O software executa operações que exigem privilégios elevados, incluindo:

* Acesso a diretórios protegidos do sistema
* Exclusão de arquivos temporários globais
* Execução de comandos administrativos

A elevação é tratada automaticamente no início da execução.

---

## ⚠️ Limitações

* Compatível apenas com Windows
* Dependência de ferramentas nativas (ex: `winget`)
* Não realiza limpeza de registro do Windows
* Não possui sistema de rollback das ações executadas

---

## 🔧 Tecnologias Utilizadas

* Python
* PyQt5
* ctypes (integração com Windows API)
* Winget
* PyInstaller

---

## 🧠 Considerações Técnicas

* Operações de limpeza são realizadas diretamente via manipulação de arquivos e chamadas ao sistema
* Execuções potencialmente demoradas são acompanhadas por feedback visual
* Logs permitem rastreabilidade das ações executadas
* Estrutura modular facilita manutenção e extensão

---

## 📌 Possíveis Extensões

* Implementação de limpeza de registro (Registry)
* Suporte a múltiplos sistemas operacionais
* Sistema de plugins para rotinas adicionais
* Agendamento automático de tarefas
* Relatórios detalhados pós-execução

---

## 📄 Licença

Distribuído sob a licença GNU GPL v3.0.