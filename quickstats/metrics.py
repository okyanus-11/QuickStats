"""Live system metrics collected from the host operating system."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Callable, TypeVar

import psutil

logger = logging.getLogger(__name__)
MetricValue = TypeVar("MetricValue")


@dataclass(frozen=True)
class SystemSnapshot:
    cpu_percent: float | None
    memory_percent: float | None
    memory_used: int | None
    memory_total: int | None
    storage_percent: float | None
    storage_used: int | None
    storage_total: int | None
    upload_bytes_per_second: float | None
    download_bytes_per_second: float | None
    network_available: bool
    uptime_seconds: float | None


def _system_drive() -> str:
    if os.name == "nt":
        return os.environ.get("SystemDrive", "C:") + os.sep
    return os.path.abspath(os.sep)


class SystemMonitor:
    """Samples real host metrics and derives network rates between samples."""

    def __init__(self) -> None:
        self._previous_network: tuple[int, int, float] | None = None
        try:
            # psutil returns a zero value on its first non-blocking CPU sample.
            psutil.cpu_percent(interval=None)
        except Exception:
            logger.exception("Could not initialize CPU sampling")

    def sample(self) -> SystemSnapshot:
        now = time.monotonic()

        cpu_percent = self._read("CPU usage", lambda: psutil.cpu_percent(interval=None))

        memory = self._read("memory usage", psutil.virtual_memory)
        memory_percent = memory.percent if memory is not None else None
        memory_used = memory.used if memory is not None else None
        memory_total = memory.total if memory is not None else None

        storage = self._read("system drive usage", lambda: psutil.disk_usage(_system_drive()))
        storage_percent = storage.percent if storage is not None else None
        storage_used = storage.used if storage is not None else None
        storage_total = storage.total if storage is not None else None

        counters = self._read("network counters", psutil.net_io_counters)
        upload_rate: float | None = None
        download_rate: float | None = None
        network_available = counters is not None
        if counters is not None:
            previous = self._previous_network
            self._previous_network = (counters.bytes_sent, counters.bytes_recv, now)
            if previous is not None:
                elapsed = now - previous[2]
                sent_delta = counters.bytes_sent - previous[0]
                received_delta = counters.bytes_recv - previous[1]
                if elapsed > 0 and sent_delta >= 0 and received_delta >= 0:
                    upload_rate = sent_delta / elapsed
                    download_rate = received_delta / elapsed
        else:
            self._previous_network = None

        boot_time = self._read("system boot time", psutil.boot_time)
        uptime_seconds = max(0.0, time.time() - boot_time) if boot_time is not None else None

        return SystemSnapshot(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used=memory_used,
            memory_total=memory_total,
            storage_percent=storage_percent,
            storage_used=storage_used,
            storage_total=storage_total,
            upload_bytes_per_second=upload_rate,
            download_bytes_per_second=download_rate,
            network_available=network_available,
            uptime_seconds=uptime_seconds,
        )

    @staticmethod
    def _read(label: str, reader: Callable[[], MetricValue]) -> MetricValue | None:
        try:
            return reader()
        except Exception:
            logger.exception("Could not read %s", label)
            return None
