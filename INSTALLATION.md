# Installation

## Requirements
- Windows 10 or Windows 11
- Python 3.11+
- Git

## Run from source (PowerShell)

```powershell
git clone https://github.com/okyanus-11/QuickStats.git
cd QuickStats
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m quickstats
```

## Windows installer

Download `QuickStats-Setup-1.0.0.exe` from the [latest GitHub release](https://github.com/okyanus-11/QuickStats/releases/latest). Run it and follow the setup wizard. It installs per-user under `%LOCALAPPDATA%\\Programs\\QuickStats`, creates a Start Menu shortcut, and offers an optional desktop shortcut. Administrator privileges and a separate Python installation are not required. The installer includes the complete PyInstaller application folder and registers a standard Windows uninstaller.

The installer is built and smoke-tested on Windows by GitHub Actions. Main-branch builds are available as 30-day workflow artifacts; version-tagged builds are attached to GitHub Releases. Installers are currently unsigned, so Windows SmartScreen may show an unfamiliar-app warning.

## Tests and executable build

```powershell
pip install -r requirements-dev.txt
python -m pytest
python -m PyInstaller --clean --noconfirm quickstats.spec
```

The standalone app is generated under `dist\QuickStats\QuickStats.exe`. Build on Windows for Windows. If PowerShell blocks activation, invoke `.\.venv\Scripts\python.exe` directly instead.
