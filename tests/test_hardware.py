from types import SimpleNamespace

import psutil

from quickstats.hardware import _available_drives, _operating_system, get_hardware_info


def test_available_drives_ignores_duplicate_devices_and_inaccessible_volumes(monkeypatch):
    partitions = [
        SimpleNamespace(device="C:", mountpoint="C:\\"),
        SimpleNamespace(device="C:", mountpoint="D:\\mounted"),
        SimpleNamespace(device="E:", mountpoint="E:\\"),
    ]
    monkeypatch.setattr(psutil, "disk_partitions", lambda all=False: partitions)

    def disk_usage(path):
        if path == "E:\\":
            raise PermissionError("not mounted")
        return SimpleNamespace(total=1000)

    monkeypatch.setattr(psutil, "disk_usage", disk_usage)

    drives = _available_drives()

    assert len(drives) == 1
    assert drives[0].device == "C:"
    assert drives[0].mountpoint == "C:\\"
    assert drives[0].total_bytes == 1000


def test_hardware_collection_handles_unavailable_memory_and_drives(monkeypatch):
    monkeypatch.setattr(
        psutil,
        "virtual_memory",
        lambda: (_ for _ in ()).throw(OSError("unavailable")),
    )
    monkeypatch.setattr(
        psutil,
        "disk_partitions",
        lambda all=False: (_ for _ in ()).throw(OSError("unavailable")),
    )

    info = get_hardware_info()

    assert info.memory_total_bytes is None
    assert info.drives == ()
    assert info.operating_system


def test_windows_build_number_distinguishes_windows_11(monkeypatch):
    monkeypatch.setattr("quickstats.hardware.sys.platform", "win32")
    monkeypatch.setattr(
        "quickstats.hardware.platform.win32_ver",
        lambda: ("10", "10.0.26100", "", ""),
    )

    assert _operating_system() == "Windows 11 (10.0.26100)"
