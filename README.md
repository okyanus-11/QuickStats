# QuickStats

QuickStats is a lightweight Windows 10/11 desktop dashboard for live system
statistics. It reads CPU, memory, storage, network, and boot-time data from
`psutil`; hardware details are gathered from the operating system. Readings
that the system does not provide are shown as unavailable rather than guessed.

## Features

- Live CPU and memory utilization, system-drive usage, and network transfer
  rates, refreshed every second by default.
- A CPU and memory history graph, system uptime, and selectable refresh
  intervals (1, 2, 5, or 10 seconds).
- Hardware details for the processor, installed memory, mounted storage
  volumes, Windows version, and display adapters when Windows reports them.
- Dark Catppuccin Mocha-inspired interface with resizable metric cards.

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

Install the development dependencies and run the test suite:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

The tests cover the system-monitoring data layer and do not require a running
desktop session.

## Build a Windows executable

On Windows, install the development dependencies, then run:

```powershell
python -m PyInstaller --clean --noconfirm quickstats.spec
```

The standalone application is written to `dist\QuickStats\QuickStats.exe`.
Build on Windows for Windows; PyInstaller does not cross-compile executables.

## Project layout

```text
quickstats/
  hardware.py       Hardware details from OS APIs
  main.py           Qt application window and refresh loop
  metrics.py        Testable live system metrics
  theme.py          Catppuccin-inspired Qt stylesheet
  widgets.py        Metric cards and history graph
tests/
  test_hardware.py
  test_metrics.py
```
