# 🐦‍⬛ CleanCrow (Legacy)

CleanCrow is a desktop application for **Windows system maintenance, cleaning, and optimization**, developed in Python with a PyQt5 graphical interface.

The software automates common maintenance tasks, removing unnecessary files, executing cleanup routines, and assisting in the management of installed packages on the system.

---

## ⚙️ Features

- 🧹 **Temporary files cleanup**
  - `%TEMP%` directories
  - System cache
  - Common residual files

- 🗑️ **Removal of unnecessary files**
  - Old log files
  - Application residues

- ⚡ **Basic system optimizations**
  - Execution of native Windows commands
  - Cleanup of accumulated components

- 📦 **Integration with winget**
  - Package installation and updates
  - CLI command automation

- 📊 **Real-time feedback execution**
  - Progress bar
  - Detailed operation logs

- 🔐 **Automatic privilege elevation**
  - Runs as administrator when needed

---

## 🏗️ Project Architecture

The project follows a simple separation between interface and logic:

- **Interface Layer (`interface.py`)**
  - Built with PyQt5
  - Responsible for user interaction
  - Log and progress updates

- **Logic Layer (`limpeza_sistema.py`)**
  - Execution of cleanup routines
  - Operating system calls
  - File and directory manipulation

- **Entry Point (`main.py`)**
  - Application initialization
  - Execution and permission control

---

## 📁 Directory Structure

```
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

## 🚀 Execution

### Prerequisites

- Python 3.10 or higher
- Windows operating system
- Pip installed

### Installing Dependencies

```bash
pip install PyQt5
```

### Running the Application

```bash
python main.py
```

> The software automatically requests privilege elevation when necessary.

---

## 🏗️ Building the Executable

### Using PyInstaller

```bash
pyinstaller --onefile limpeza_sistema.py
```

Or with the configuration file:

```bash
pyinstaller cleancrow.spec
```

Output:

```
/dist/cleancrow.exe
```

---

## 🔐 Permissions and Security

The software performs operations that require elevated privileges, including:

- Access to protected system directories
- Deletion of global temporary files
- Execution of administrative commands

Elevation is handled automatically at the start of execution.

---

## ⚠️ Limitations

- Windows-compatible only
- Depends on native tools (e.g., `winget`)
- Does not perform Windows registry cleaning
- No rollback system for executed actions

---

## 🔧 Technologies Used

- Python
- PyQt5
- ctypes (Windows API integration)
- Winget
- PyInstaller

---

## 🧠 Technical Considerations

- Cleanup operations are performed directly through file manipulation and system calls
- Potentially lengthy executions are accompanied by visual feedback
- Logs allow traceability of executed actions
- Modular structure facilitates maintenance and extension

---

## 📌 Possible Extensions

- Registry cleaning implementation
- Support for multiple operating systems
- Plugin system for additional routines
- Automatic task scheduling
- Detailed post-execution reports

---

## 📄 License

Distributed under the GNU GPL v3.0 license.
