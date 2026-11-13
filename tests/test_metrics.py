from types import SimpleNamespace

import psutil

from quickstats.metrics import SystemMonitor


def install_monitor_mocks(monkeypatch, *, cpu=23.5, memory=None, disk=None, network=None):
    monkeypatch.setattr(psutil, "cpu_percent", lambda interval=None: cpu)
    monkeypatch.setattr(
        psutil,
        "virtual_memory",
        lambda: memory or SimpleNamespace(percent=62.0, used=620, total=1000),
    )
    monkeypatch.setattr(
        psutil,
        "disk_usage",
        lambda path: disk or SimpleNamespace(percent=40.0, used=400, total=1000),
    )
    monkeypatch.setattr(
        psutil,
        "net_io_counters",
        lambda: network or SimpleNamespace(bytes_sent=100, bytes_recv=200),
    )
    monkeypatch.setattr(psutil, "boot_time", lambda: 1000.0)


def test_snapshot_contains_os_reported_values(monkeypatch):
    install_monitor_mocks(
        monkeypatch,
        memory=SimpleNamespace(percent=71.2, used=712, total=1000),
        disk=SimpleNamespace(percent=35.0, used=350, total=1000),
    )
    monkeypatch.setattr("quickstats.metrics.time.time", lambda: 4600.0)

    snapshot = SystemMonitor().sample()

    assert snapshot.cpu_percent == 23.5
    assert (snapshot.memory_percent, snapshot.memory_used, snapshot.memory_total) == (
        71.2,
        712,
        1000,
    )
    assert (snapshot.storage_percent, snapshot.storage_used, snapshot.storage_total) == (
        35.0,
        350,
        1000,
    )
    assert snapshot.uptime_seconds == 3600
    assert snapshot.network_available is True
    assert snapshot.upload_bytes_per_second is None


def test_network_rates_use_counter_deltas_and_elapsed_time(monkeypatch):
    counters = iter(
        (
            SimpleNamespace(bytes_sent=100, bytes_recv=200),
            SimpleNamespace(bytes_sent=300, bytes_recv=700),
        )
    )
    install_monitor_mocks(monkeypatch)
    monkeypatch.setattr(psutil, "net_io_counters", lambda: next(counters))
    ticks = iter((10.0, 12.0))
    monkeypatch.setattr("quickstats.metrics.time.monotonic", lambda: next(ticks))
    monitor = SystemMonitor()

    first = monitor.sample()
    second = monitor.sample()

    assert first.upload_bytes_per_second is None
    assert second.upload_bytes_per_second == 100
    assert second.download_bytes_per_second == 250


def test_unavailable_network_resets_baseline_until_next_sample(monkeypatch):
    install_monitor_mocks(monkeypatch)
    readings = iter(
        (
            SimpleNamespace(bytes_sent=100, bytes_recv=200),
            RuntimeError("network unavailable"),
            SimpleNamespace(bytes_sent=800, bytes_recv=900),
            SimpleNamespace(bytes_sent=900, bytes_recv=1100),
        )
    )

    def network_reading():
        reading = next(readings)
        if isinstance(reading, Exception):
            raise reading
        return reading

    monkeypatch.setattr(
        psutil,
        "net_io_counters",
        network_reading,
    )
    ticks = iter((10.0, 11.0, 12.0, 14.0))
    monkeypatch.setattr("quickstats.metrics.time.monotonic", lambda: next(ticks))
    monitor = SystemMonitor()

    initial = monitor.sample()
    unavailable = monitor.sample()
    new_baseline = monitor.sample()
    measured = monitor.sample()

    assert initial.network_available is True
    assert unavailable.network_available is False
    assert new_baseline.upload_bytes_per_second is None
    assert measured.upload_bytes_per_second == 50
    assert measured.download_bytes_per_second == 100


def test_storage_and_memory_errors_are_reported_as_unavailable(monkeypatch):
    install_monitor_mocks(monkeypatch)
    monkeypatch.setattr(
        psutil, "virtual_memory", lambda: (_ for _ in ()).throw(OSError("denied"))
    )
    monkeypatch.setattr(
        psutil, "disk_usage", lambda path: (_ for _ in ()).throw(OSError("denied"))
    )

    snapshot = SystemMonitor().sample()

    assert snapshot.memory_percent is None
    assert snapshot.memory_total is None
    assert snapshot.storage_percent is None
