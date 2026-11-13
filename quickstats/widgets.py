"""Reusable dashboard cards and a lightweight Qt-painted history graph."""

from __future__ import annotations

from collections import deque

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from quickstats import theme


class MetricCard(QFrame):
    def __init__(self, title: str, progress_name: str | None = None) -> None:
        super().__init__()
        self.setProperty("class", "card")
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 16)
        layout.setSpacing(8)

        self.title = QLabel(title.upper())
        self.title.setProperty("class", "metricTitle")
        self.value = QLabel("—")
        self.value.setProperty("class", "metricValue")
        self.value.setMinimumWidth(0)
        self.subtitle = QLabel("")
        self.subtitle.setProperty("class", "muted")
        self.subtitle.setWordWrap(True)

        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.subtitle)
        self.progress = None
        if progress_name:
            self.progress = QProgressBar()
            self.progress.setObjectName(progress_name)
            self.progress.setRange(0, 100)
            self.progress.setTextVisible(False)
            layout.addWidget(self.progress)
        layout.addStretch(1)

    def set_metric(
        self,
        value: str,
        subtitle: str,
        percent: float | None = None,
    ) -> None:
        self.value.setText(value)
        self.subtitle.setText(subtitle)
        if self.progress is not None:
            self.progress.setVisible(percent is not None)
            if percent is not None:
                self.progress.setValue(round(max(0, min(percent, 100))))


class HistoryChart(QWidget):
    """Draws CPU and memory percentages against a fixed 0–100% scale."""

    def __init__(self, history_length: int = 60) -> None:
        super().__init__()
        self._history: deque[tuple[float | None, float | None]] = deque(
            maxlen=history_length
        )
        self.setMinimumHeight(190)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def add_sample(self, cpu: float | None, memory: float | None) -> None:
        self._history.append((cpu, memory))
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(42, 18, -14, -30)
        if rect.width() <= 0 or rect.height() <= 0:
            return

        grid_pen = QPen(QColor(theme.SURFACE_ALT), 1)
        painter.setPen(grid_pen)
        for value in (0, 25, 50, 75, 100):
            y = rect.bottom() - rect.height() * value / 100
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            painter.setPen(QColor(theme.MUTED))
            painter.drawText(0, round(y - 8), 34, 16, Qt.AlignmentFlag.AlignRight, f"{value}%")
            painter.setPen(grid_pen)

        self._draw_series(painter, rect, 0, theme.BLUE)
        self._draw_series(painter, rect, 1, theme.MAUVE)

        painter.setPen(QColor(theme.BLUE))
        painter.drawText(round(rect.left()), self.height() - 6, "CPU")
        painter.setPen(QColor(theme.MAUVE))
        painter.drawText(round(rect.left() + 54), self.height() - 6, "Memory")
        painter.end()

    def _draw_series(self, painter: QPainter, rect, series: int, color: str) -> None:
        points = [
            (index, row[series])
            for index, row in enumerate(self._history)
            if row[series] is not None
        ]
        if not points:
            return

        denominator = max(1, len(self._history) - 1)
        path = QPainterPath()
        for point_index, (index, value) in enumerate(points):
            x = rect.left() + rect.width() * index / denominator
            y = rect.bottom() - rect.height() * max(0, min(value, 100)) / 100
            if point_index == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        painter.setPen(QPen(QColor(color), 2))
        painter.drawPath(path)


class DetailRow(QWidget):
    def __init__(self, label: str, value: str) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        key = QLabel(label)
        key.setProperty("class", "muted")
        key.setMinimumWidth(80)
        self.value = QLabel(value)
        self.value.setWordWrap(True)
        self.value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(key)
        layout.addWidget(self.value, 1)


class HardwareCard(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setProperty("class", "card")
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        heading = QLabel("Hardware")
        heading.setStyleSheet("font-size: 12pt; font-weight: 700;")
        layout.addWidget(heading)

        self.rows: dict[str, DetailRow] = {}
        for key, label in (
            ("cpu", "Processor"),
            ("memory", "Installed RAM"),
            ("drives", "Drives"),
            ("os", "Windows"),
            ("gpu", "Graphics"),
        ):
            row = DetailRow(label, "Loading…")
            self.rows[key] = row
            layout.addWidget(row)
        layout.addStretch(1)

    def set_details(
        self,
        cpu: str,
        memory: str,
        drives: str,
        operating_system: str,
        gpu: str,
    ) -> None:
        for key, value in (
            ("cpu", cpu),
            ("memory", memory),
            ("drives", drives),
            ("os", operating_system),
            ("gpu", gpu),
        ):
            self.rows[key].value.setText(value)
