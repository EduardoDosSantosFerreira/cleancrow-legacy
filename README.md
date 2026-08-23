<img src="https://cleancrow.vercel.app/src/assets/img/profile_icons/crowico.png" width="110">

# CleanCrow

**CleanCrow** is an advanced desktop application for **Windows system cleaning, optimization, and updating**, developed in Python with a modern PyQt5 graphical interface.

It automates routine maintenance tasks, removes unnecessary files, executes safe cleaning routines, and assists in managing installed packages on your system — all using **native Windows tools** for maximum security and compatibility.

---

## ✨ Features

### 🧹 Temporary File Cleaning
- Removes user temporary files (`%TEMP%`, `%LOCALAPPDATA%/Temp`).
- Removes Windows temporary files (`C:/Windows/Temp`).
- **Schedules deletion of locked files** for the next reboot using the Windows API `MoveFileEx`.

### 🗑️ Removal of Unnecessary Files
- **Recycle Bin**: Empties the Windows Recycle Bin via native API.
- **Thumbnail Cache**: Clears Windows Explorer thumbnail cache.
- **Error Reports (WER)**: Removes old Windows Error Reporting reports.
- **Logs**: Removes unnecessary system logs.
- **Browser Cache**: Cleans Chrome, Edge, Firefox, Brave, and Opera caches (automatically closes browsers to free files).
- **Shader Cache**: Cleans NVIDIA and AMD GPU shader caches.
- **Windows Update Cache**: Removes old update downloads (requires stopping services).
- **WebCache**: Cleans Windows web application caches (SearchApp, etc.).

### ⚡ System Optimizations
- **Advanced Cleaning**: Executes `cleanmgr` (Disk Cleanup) and `DISM /StartComponentCleanup`.
- **DirectX Shader Cache**: Removes DirectX shader caches.

### 📦 Program Updates (Winget Integration)
- Detects the Windows Package Manager (winget).
- Updates repository sources.
- Executes `winget upgrade --all` to update all programs.
- Verifies remaining updates after the operation.
- Automatically requests UAC elevation when necessary.

### 📊 Interface & Feedback
- Modern graphical interface with PyQt5 (dark theme).
- Real-time progress bar.
- Detailed operation log (with levels: `info`, `success`, `warning`, `error`, `step`, `system`, `detail`).
- Cleaning modes: **Normal**, **Fast**, and **Safe**.
- Visual indicator of administrator status.

### 🔐 Security
- Uses only **native Windows tools** (`cmd`, `dism`, `cleanmgr`, `winget`).
- Does **not** use third-party libraries for system cleaning.
- All operations are logged.
- Recommends running as Administrator for best performance.

---

## 🏗️ Project Architecture

The project follows a **layered architecture**, making it modular, maintainable, and extensible:

### Layer 1: Interface (`interface.py`)
- Built with PyQt5.
- Handles user interaction.
- Displays logs in real-time, progress bar, and operation status.
- Controls cleaning modes (Normal, Fast, Safe).

### Layer 2: Engine (`core/engine.py`)
- Orchestrates all cleaners.
- Manages scanning (detection) and cleaning.
- Executes operations in parallel (`ThreadPoolExecutor`).
- Provides callbacks for progress and log updates.

### Layer 3: Cleaners (`core/cleaners/`)
- Each cleaner handles a specific cleaning category.
- All inherit from the base class `BaseCleaner`.
- Implement methods to detect, calculate size, and clean.

### Layer 4: Windows APIs (`core/win32_api.py`)
- Uses `ctypes` to access native Windows APIs.
- Examples: emptying recycle bin, checking admin privileges, getting disk space.

### Layer 5: Logger (`core/logger.py`)
- Registers all operations performed.
- Supports callbacks for real-time display.
- Exports logs in JSON format.

---

## 🧹 Available Cleaners

| Cleaner | Description | Requires Admin | Risk Level |
|---|---|---|---|
| `TempCleaner` | User temporary files | No | 🟢 Safe |
| `WindowsTempCleaner` | Windows temporary files | Yes | 🟢 Safe |
| `RecycleBinCleaner` | Empties the Recycle Bin | No | 🟢 Safe |
| `ThumbnailCleaner` | Clears thumbnail cache | No | 🟢 Safe |
| `WERCleaner` | Removes error reports | No | 🟢 Safe |
| `WindowsUpdateCleaner` | Clears Windows Update cache | Yes | 🟡 Advanced |
| `BrowsersCleaner` | Clears browser cache | No | 🟢 Safe |
| `WebCacheCleaner` | Clears web application cache | No | 🟠 Special |
| `NvidiaCacheCleaner` | Clears NVIDIA shader cache | No | 🟡 Advanced |
| `AmdCacheCleaner` | Clears AMD shader cache | No | 🟡 Advanced |
| `SystemCleaner` | Advanced cleaning (cleanmgr + DISM) | Yes | 🟡 Advanced |
| `DNSCleaner` | Clears DNS cache | Yes | 🟢 Safe |
| `ComponentStoreCleaner` | Component Store (DISM) | Yes | 🟡 Advanced |

---

## 🔄 Cleaning Modes

| Mode | Description |
|---|---|
| **Normal** | Executes all available cleaners (except WebCache). Recommended for general use. |
| **Fast** | Executes only cache and temporary cleaners. Faster, ideal for frequent cleaning. |
| **Safe** | Executes only risk-free cleaners. Does not close browsers or run advanced commands. |

---

## 📊 Log System

The logging system records operations with the following levels:

| Level | Description |
|---|---|
| `info` | General information |
| `success` | Successful operation |
| `warning` | Warnings (e.g., locked file) |
| `error` | Errors |
| `step` | Cleaning steps |
| `system` | System messages |
| `detail` | Technical details |

Logs are stored in `%LOCALAPPDATA%/CleanCrow/Logs/` and can be exported to JSON.

---

## 🚀 How to Run

### Prerequisites
- Windows 10 or 11 (64-bit)
- Python 3.10 or higher
- Pip installed

### Installing Dependencies
```bash
pip install PyQt5 qtawesome
```

### Running the Application
```bash
python main.py
```

> The application will automatically request administrator privileges when necessary.

---

## 🏗️ How to Build the Executable

### Using PyInstaller
```bash
pip install pyinstaller
pyinstaller CLEANCROW.spec
```

The executable will be generated at `dist/CLEANCROW.exe`.

---

## 🔐 Permissions & Security

CleanCrow performs operations that require elevated privileges, including:
- Access to protected system directories.
- Deletion of global temporary files.
- Execution of administrative commands (`cleanmgr`, `dism`, `winget`).

Elevation is handled automatically at the start of execution.

### Security Principles
- **No third-party cleaning libraries** — only native Windows tools.
- **Transparent logging** — every action is recorded.
- **User control** — critical operations require confirmation.
- **No registry modifications** — unless explicitly requested in future versions.

---

## ⚠️ Known Limitations

- **Windows only** — not cross-platform.
- **Depends on native tools** — e.g., `winget` must be installed.
- **No registry cleaning** — currently not implemented.
- **No rollback system** — actions cannot be undone automatically.
- **Locked files** — some files may remain and will be removed on next reboot.
- **Browsers are closed** — to allow cache cleaning.
- **Windows Update** — can only be cleaned if the service is stopped.

---

## 🛣️ Roadmap (Future Extensions)

- [ ] Windows registry cleaning.
- [ ] Support for multiple operating systems.
- [ ] Plugin system for additional routines.
- [ ] Automatic task scheduling.
- [ ] Detailed post-execution reports (PDF/HTML).
- [ ] Startup program management.

---

## 📄 License

Distributed under the **GNU General Public License v3.0 (GPLv3)**.  
You are free to modify and redistribute the code, provided you maintain the same license.

See the `LICENSE` file for more details.

---

## 📬 Contact

- **Author**: Eduardo S Ferreira
- **GitHub**: [EduardoDosSantosFerreira](https://github.com/EduardoDosSantosFerreira)
- **LinkedIn**: [Eduardo Dos Santos Ferreira](https://www.linkedin.com/in/eduardodossantosferreira/)
- **Discord**: eduardo_dsf
- **Email**: eduardo.dsf.dev@gmail.com

---

## 🧠 Technical Considerations

- **Built with Python 3.10+** and **PyQt5**.
- **Uses `ctypes`** for native Windows API access.
- **Uses `ThreadPoolExecutor`** for parallel cleaning operations.
- **Uses `winreg`** for Windows registry interaction (only for configuring `cleanmgr`).
- **Uses `subprocess`** for executing native commands (`cleanmgr`, `dism`, `winget`, `ipconfig`).
- **Uses `MoveFileEx`** for scheduling locked file deletion.
- **No external dependencies** beyond `PyQt5` and `qtawesome` for the GUI.

---

## 📂 Project Structure

```
cleancrow/
│
├── main.py                 # Application entry point
├── interface.py            # PyQt5 GUI
├── doc.html                # Documentation page
├── doc.css                 # Documentation stylesheet
├── index.html              # Project landing page
├── LICENSE                 # GNU GPL v3.0
├── README.md               # This file
│
├── core/
│   ├── __init__.py         # Core package initialization
│   ├── engine.py           # Cleaning engine (orchestrator)
│   ├── models.py           # Data models (CleanerInfo, CleanerResult, etc.)
│   ├── logger.py           # Logging system
│   ├── winget_updater.py   # Winget integration module
│   ├── win32_api.py        # Windows APIs (Recycle Bin, Admin, Disk)
│   │
│   └── cleaners/
│       ├── __init__.py     # Cleaner imports
│       ├── base.py         # Base cleaner class
│       ├── temp_cleaner.py         # User temp files
│       ├── windows_temp.py         # Windows temp files
│       ├── recycle_bin.py          # Recycle Bin
│       ├── thumbnail_cleaner.py    # Thumbnail cache
│       ├── wer_cleaner.py          # WER reports
│       ├── windows_update.py       # Windows Update cache
│       ├── browsers.py             # Browser cache
│       ├── web_cache.py            # WebCache
│       ├── nvidia_cache.py         # NVIDIA shader cache
│       ├── amd_cache.py            # AMD shader cache
│       ├── system_cleaner.py       # Advanced cleaning (cleanmgr + DISM)
│       ├── component_store.py      # Component Store (DISM)
│       └── dns_cleaner.py          # DNS cache
│
├── dist/                   # Compiled executable (CLEANCROW.exe)
├── build/                  # PyInstaller build directory
├── src/
│   └── assets/             # Static assets (images, css, js)
│
└── CLEANCROW.spec          # PyInstaller configuration file
```

---

## 🎯 Why Choose CleanCrow?

- ✅ **100% Free & Open Source** (GPL v3.0).
- ✅ **No Malware, No Tracking** — uses only native Windows tools.
- ✅ **Secure** — does not modify registry without permission.
- ✅ **Fast** — parallel cleaning with `ThreadPoolExecutor`.
- ✅ **Modern UI** — dark theme with real-time feedback.
- ✅ **Automatic Updates** — integrated with `winget`.
- ✅ **Safe Modes** — Normal, Fast, and Safe cleaning options.
- ✅ **Detailed Logs** — all operations recorded and exportable.

---

**CleanCrow — Keep Your Windows Clean, Fast, and Up to Date!** 🐦‍⬛
```

---
