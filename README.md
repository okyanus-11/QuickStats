# QuickStats

QuickStats is a lightweight Windows 10/11 desktop dashboard for live system
statistics. It reads CPU, memory, storage, network, and boot-time data from
`psutil`; hardware details are gathered from the operating system. Readings
that the system does not provide are shown as unavailable rather than guessed.


<p align="center">
  <a href="https://github.com/okyanus-11/QuickStats/releases/download/v1.0.0/QuickStats-Setup-1.0.0.exe"><strong>⬇️ Download for Windows — Installer (.exe)</strong></a>
  · <a href="https://github.com/okyanus-11/QuickStats/releases/latest">All releases</a>
</p>

> **Windows 10/11:** Click the installer above to install the app. No Python setup or ZIP extraction required.


## Features

- Live CPU and memory utilization, system-drive usage, and network transfer
  rates, refreshed every second by default.
- A CPU and memory history graph, system uptime, and selectable refresh
  intervals (1, 2, 5, or 10 seconds).
- Hardware details for processor, memory, mounted storage, Windows version,
  and display adapters when Windows reports them.
- Graphite, Midnight and Light themes with six accent presets or any custom hex colour.
- Theme and accent preferences persist between launches.
- Metric collection and hardware inventory run in background workers so slow
  OS queries do not freeze the interface.

## Requirements

- Windows 10 or Windows 11
- Python 3.11 or newer

## Run from source

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m quickstats
```

## Tests

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

## Install on Windows

Download [QuickStats-Setup-1.0.0.exe from the latest release](https://github.com/okyanus-11/QuickStats/releases/latest) and run the setup wizard. It installs the complete application without requiring Python, adds a Start Menu shortcut, offers an optional desktop shortcut, and registers a Windows uninstaller. See [INSTALLATION.md](INSTALLATION.md) for details.

## Build a Windows executable

```powershell
python -m PyInstaller --clean --noconfirm quickstats.spec
```

The standalone application is written to `dist\QuickStats\QuickStats.exe`.

## Installation

Requires Windows 10/11 and Python 3.11+. Create a virtual environment, install `requirements.txt`, and launch with `python -m quickstats`. For tests, install `requirements-dev.txt` and run `python -m pytest`; the standalone Windows build uses `quickstats.spec`. See the [full installation guide](INSTALLATION.md).
