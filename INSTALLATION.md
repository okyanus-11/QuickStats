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

## Tests and executable build

```powershell
pip install -r requirements-dev.txt
python -m pytest
python -m PyInstaller --clean --noconfirm quickstats.spec
```

The standalone app is generated under `dist\QuickStats\QuickStats.exe`. Build on Windows for Windows. If PowerShell blocks activation, invoke `.\.venv\Scripts\python.exe` directly instead.
