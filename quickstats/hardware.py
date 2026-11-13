"""Hardware and operating-system information from native system APIs."""

from __future__ import annotations

import ctypes
import logging
import platform
import sys
from dataclasses import dataclass

import psutil

logger = logging.getLogger(__name__)
UNAVAILABLE = "Unavailable"


@dataclass(frozen=True)
class DriveInfo:
    device: str
    mountpoint: str
    total_bytes: int


@dataclass(frozen=True)
class HardwareInfo:
    cpu_model: str
    memory_total_bytes: int | None
    drives: tuple[DriveInfo, ...]
    operating_system: str
    gpus: tuple[str, ...]


def _cpu_model() -> str:
    if sys.platform == "win32":
        try:
            import winreg

            key_path = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                model, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                if model.strip():
                    return model.strip()
        except (OSError, ImportError):
            logger.exception("Could not read the processor model from the registry")

    model = platform.processor().strip()
    return model if model else UNAVAILABLE


def _operating_system() -> str:
    if sys.platform == "win32":
        release, version, _, _ = platform.win32_ver()
        if release == "10":
            try:
                if int(version.rsplit(".", 1)[-1]) >= 22000:
                    release = "11"
            except ValueError:
                pass
        if release and version:
            return f"Windows {release} ({version})"
        details = " ".join(part for part in (release, version) if part)
        return f"Windows {details}".strip() if details else "Windows (version unavailable)"
    return platform.platform() or UNAVAILABLE


def _display_adapters() -> tuple[str, ...]:
    if sys.platform != "win32":
        return ()

    from ctypes import wintypes

    class DisplayDevice(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("DeviceName", wintypes.WCHAR * 32),
            ("DeviceString", wintypes.WCHAR * 128),
            ("StateFlags", wintypes.DWORD),
            ("DeviceID", wintypes.WCHAR * 128),
            ("DeviceKey", wintypes.WCHAR * 128),
        ]

    try:
        user32 = ctypes.windll.user32
        adapters: list[str] = []
        index = 0
        while True:
            device = DisplayDevice()
            device.cb = ctypes.sizeof(device)
            if not user32.EnumDisplayDevicesW(None, index, ctypes.byref(device), 0):
                break
            name = device.DeviceString.strip()
            if name and name not in adapters:
                adapters.append(name)
            index += 1
        return tuple(adapters)
    except (AttributeError, OSError):
        logger.exception("Could not enumerate Windows display adapters")
        return ()


def _available_drives() -> tuple[DriveInfo, ...]:
    drives: list[DriveInfo] = []
    seen_devices: set[str] = set()
    try:
        partitions = psutil.disk_partitions(all=False)
    except Exception:
        logger.exception("Could not enumerate storage volumes")
        return ()

    for partition in partitions:
        device = partition.device or partition.mountpoint
        identity = device.casefold()
        if identity in seen_devices:
            continue
        try:
            usage = psutil.disk_usage(partition.mountpoint)
        except (OSError, PermissionError):
            logger.info("Skipping inaccessible volume %s", partition.mountpoint)
            continue
        except Exception:
            logger.exception("Could not read storage volume %s", partition.mountpoint)
            continue
        seen_devices.add(identity)
        drives.append(DriveInfo(device, partition.mountpoint, usage.total))
    return tuple(drives)


def get_hardware_info() -> HardwareInfo:
    try:
        memory_total = psutil.virtual_memory().total
    except Exception:
        logger.exception("Could not read installed memory size")
        memory_total = None

    return HardwareInfo(
        cpu_model=_cpu_model(),
        memory_total_bytes=memory_total,
        drives=_available_drives(),
        operating_system=_operating_system(),
        gpus=_display_adapters(),
    )
