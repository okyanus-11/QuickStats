"""QuickStats desktop application."""

from __future__ import annotations

import logging
import sys

from PySide6.QtCore import QObject, QRunnable, Qt, QSettings, QThreadPool, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
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
from quickstats import theme
from quickstats.widgets import HardwareCard, HistoryChart, MetricCard

logger = logging.getLogger(__name__)


class _SampleSignals(QObject):
    finished = Signal(object)
    failed = Signal(str)


class _SampleWorker(QRunnable):
    def __init__(self, monitor: SystemMonitor) -> None:
        super().__init__()
        self.monitor = monitor
        self.signals = _SampleSignals()

    def run(self) -> None:
        try:
            self.signals.finished.emit(self.monitor.sample())
        except Exception as error:
            self.signals.failed.emit(str(error))


class _HardwareWorker(QRunnable):
    def __init__(self) -> None:
        super().__init__()
        self.signals = _SampleSignals()

    def run(self) -> None:
        try:
            self.signals.finished.emit(get_hardware_info())
        except Exception as error:
            self.signals.failed.emit(str(error))


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
        self._sampling = False
        self._sample_worker = None
        self._settings = QSettings("Okyanus11", "QuickStats")
        self._theme_name = str(self._settings.value("appearance/theme", "graphite"))
        self._accent_name = str(self._settings.value("appearance/accent", "blue"))

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
        header.addSpacing(14)
        appearance_label = QLabel("Theme")
        appearance_label.setProperty("class", "muted")
        header.addWidget(appearance_label)
        self.theme_select = QComboBox()
        for key, label in (("graphite", "Graphite"), ("midnight", "Midnight"), ("light", "Light")):
            self.theme_select.addItem(label, key)
        self.theme_select.setCurrentIndex(max(0, self.theme_select.findData(self._theme_name)))
        self.theme_select.currentIndexChanged.connect(self._appearance_changed)
        header.addWidget(self.theme_select)
        self.accent_select = QComboBox()
        for key, label in (
            ("blue", "Blue"), ("violet", "Violet"), ("teal", "Teal"),
            ("emerald", "Emerald"), ("amber", "Amber"), ("rose", "Rose"),
        ):
            self.accent_select.addItem(label, key)
        if self._accent_name.startswith("#"):
            self.accent_select.addItem(f"Custom ({self._accent_name})", self._accent_name)
        self.accent_select.setCurrentIndex(max(0, self.accent_select.findData(self._accent_name)))
        self.accent_select.currentIndexChanged.connect(self._appearance_changed)
        header.addWidget(self.accent_select)
        custom_accent_button = QPushButton("Custom…")
        custom_accent_button.clicked.connect(self._choose_custom_accent)
        header.addWidget(custom_accent_button)
        header.addSpacing(8)
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

    def _choose_custom_accent(self) -> None:
        current = theme.current_palette()["accent"]
        color = QColorDialog.getColor(QColor(current), self, "Choose accent colour")
        if not color.isValid():
            return
        self._accent_name = color.name()
        index = self.accent_select.findData(self._accent_name)
        if index < 0:
            self.accent_select.addItem(f"Custom ({self._accent_name})", self._accent_name)
            index = self.accent_select.count() - 1
        self.accent_select.setCurrentIndex(index)
        self._settings.setValue("appearance/accent", self._accent_name)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme.build_stylesheet(self._theme_name, self._accent_name))
        self.update()

    def _appearance_changed(self, _index: int) -> None:
        self._theme_name = str(self.theme_select.currentData() or "graphite")
        self._accent_name = str(self.accent_select.currentData() or "blue")
        self._settings.setValue("appearance/theme", self._theme_name)
        self._settings.setValue("appearance/accent", self._accent_name)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme.build_stylesheet(self._theme_name, self._accent_name))
        self.update()

    def _load_hardware(self) -> None:
        self._hardware_worker = _HardwareWorker()
        self._hardware_worker.signals.finished.connect(self._hardware_finished)
        self._hardware_worker.signals.failed.connect(self._hardware_failed)
        QThreadPool.globalInstance().start(self._hardware_worker)

    def _hardware_finished(self, info) -> None:
        self._hardware_worker = None
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

    def _hardware_failed(self, message: str) -> None:
        self._hardware_worker = None
        logger.error("Could not load hardware information: %s", message)
        self.hardware_card.set_details(*(UNAVAILABLE for _ in range(5)))

    def _set_refresh_interval(self, _index: int) -> None:
        seconds = self.interval.currentData()
        if seconds:
            self._timer.setInterval(int(seconds) * 1000)

    def refresh_stats(self) -> None:
        # Never block Qt's event loop on OS metric providers. Skip a timer tick
        # if the previous sample is still running rather than queueing stale work.
        if self._sampling:
            return
        self._sampling = True
        worker = _SampleWorker(self._monitor)
        self._sample_worker = worker
        worker.signals.finished.connect(self._sample_finished)
        worker.signals.failed.connect(self._sample_failed)
        QThreadPool.globalInstance().start(worker)

    def _sample_finished(self, snapshot: SystemSnapshot) -> None:
        self._sampling = False
        self._sample_worker = None
        self._update_dashboard(snapshot)

    def _sample_failed(self, message: str) -> None:
        self._sampling = False
        self._sample_worker = None
        logger.error("Could not collect system statistics: %s", message)

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
    window = MainWindow()
    app.setStyleSheet(theme.build_stylesheet(window._theme_name, window._accent_name))
    window.show()
    return app.exec()
