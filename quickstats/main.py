"""QuickStats desktop application."""

from __future__ import annotations

import logging
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from quickstats.hardware import UNAVAILABLE, get_hardware_info
from quickstats.metrics import SystemMonitor, SystemSnapshot
from quickstats.theme import STYLESHEET
from quickstats.widgets import HardwareCard, HistoryChart, MetricCard

logger = logging.getLogger(__name__)


def format_bytes(value: int | float | None) -> str:
    if value is None:
        return UNAVAILABLE
    amount = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if amount < 1000 or unit == "PB":
            return f"{amount:.0f} {unit}" if unit == "B" else f"{amount:.1f} {unit}"
        amount /= 1000
    return UNAVAILABLE


def format_rate(value: float | None, available: bool) -> str:
    if value is None:
        return "Sampling…" if available else UNAVAILABLE
    return f"{format_bytes(value)}/s"


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return UNAVAILABLE
    total = max(0, int(seconds))
    days, remainder = divmod(total, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    if days:
        return f"{days}d {hours:02}h {minutes:02}m"
    return f"{hours}h {minutes:02}m"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("QuickStats")
        self.resize(1060, 760)
        self.setMinimumSize(780, 620)
        self._monitor = SystemMonitor()

        root = QWidget()
        self.setCentralWidget(root)
        page = QVBoxLayout(root)
        page.setContentsMargins(24, 20, 24, 20)
        page.setSpacing(18)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title = QLabel("QuickStats")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Live system overview")
        subtitle.setObjectName("subtitle")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        header.addLayout(title_block)
        header.addStretch(1)
        self.uptime = QLabel("Uptime: —")
        self.uptime.setObjectName("uptime")
        header.addWidget(self.uptime)
        header.addSpacing(18)
        interval_label = QLabel("Refresh")
        interval_label.setProperty("class", "muted")
        header.addWidget(interval_label)
        self.interval = QComboBox()
        for seconds in (1, 2, 5, 10):
            self.interval.addItem(f"{seconds} sec", seconds)
        self.interval.currentIndexChanged.connect(self._set_refresh_interval)
        header.addWidget(self.interval)
        self.refresh_button = QPushButton("Refresh now")
        self.refresh_button.clicked.connect(self.refresh_stats)
        header.addWidget(self.refresh_button)
        page.addLayout(header)

        cards = QGridLayout()
        cards.setSpacing(14)
        self.cpu_card = MetricCard("CPU", "cpuBar")
        self.memory_card = MetricCard("Memory", "memoryBar")
        self.storage_card = MetricCard("System drive", "storageBar")
        self.network_card = MetricCard("Network")
        for index, card in enumerate(
            (self.cpu_card, self.memory_card, self.storage_card, self.network_card)
        ):
            cards.addWidget(card, 0, index)
        page.addLayout(cards)

        lower = QHBoxLayout()
        lower.setSpacing(14)
        chart_frame = QFrame()
        chart_frame.setProperty("class", "card")
        chart_frame.setObjectName("card")
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(18, 16, 18, 14)
        chart_layout.setSpacing(6)
        chart_title = QLabel("Performance history")
        chart_title.setStyleSheet("font-size: 12pt; font-weight: 700;")
        chart_layout.addWidget(chart_title)
        self.chart = HistoryChart()
        chart_layout.addWidget(self.chart, 1)
        self.hardware_card = HardwareCard()
        lower.addWidget(chart_frame, 3)
        lower.addWidget(self.hardware_card, 2)
        page.addLayout(lower, 1)

        self._load_hardware()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_stats)
        self._timer.start(1000)
        self.refresh_stats()

    def _load_hardware(self) -> None:
        try:
            info = get_hardware_info()
            drives = ", ".join(
                f"{drive.mountpoint} ({format_bytes(drive.total_bytes)})"
                for drive in info.drives
            ) or UNAVAILABLE
            gpus = ", ".join(info.gpus) or UNAVAILABLE
            self.hardware_card.set_details(
                cpu=info.cpu_model,
                memory=format_bytes(info.memory_total_bytes),
                drives=drives,
                operating_system=info.operating_system,
                gpu=gpus,
            )
        except Exception:
            logger.exception("Could not load hardware information")
            self.hardware_card.set_details(*(UNAVAILABLE for _ in range(5)))

    def _set_refresh_interval(self, _index: int) -> None:
        seconds = self.interval.currentData()
        if seconds:
            self._timer.setInterval(int(seconds) * 1000)

    def refresh_stats(self) -> None:
        try:
            snapshot = self._monitor.sample()
        except Exception:
            logger.exception("Could not collect system statistics")
            return
        self._update_dashboard(snapshot)

    def _update_dashboard(self, data: SystemSnapshot) -> None:
        self.cpu_card.set_metric(
            f"{data.cpu_percent:.0f}%" if data.cpu_percent is not None else UNAVAILABLE,
            "Processor utilization",
            data.cpu_percent,
        )

        memory_subtitle = (
            f"{format_bytes(data.memory_used)} of {format_bytes(data.memory_total)}"
        )
        self.memory_card.set_metric(
            f"{data.memory_percent:.0f}%"
            if data.memory_percent is not None
            else UNAVAILABLE,
            memory_subtitle,
            data.memory_percent,
        )

        storage_subtitle = (
            f"{format_bytes(data.storage_used)} of {format_bytes(data.storage_total)}"
        )
        self.storage_card.set_metric(
            f"{data.storage_percent:.0f}%"
            if data.storage_percent is not None
            else UNAVAILABLE,
            storage_subtitle,
            data.storage_percent,
        )

        self.network_card.set_metric(
            f"↓ {format_rate(data.download_bytes_per_second, data.network_available)}",
            f"↑ {format_rate(data.upload_bytes_per_second, data.network_available)}",
        )
        self.uptime.setText(f"Uptime: {format_duration(data.uptime_seconds)}")
        self.chart.add_sample(data.cpu_percent, data.memory_percent)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    app = QApplication(sys.argv)
    app.setApplicationName("QuickStats")
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec()
