"""Gráfico de barras minimalista (QPainter) para o dashboard anual."""
from __future__ import annotations

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget

from .. import theme


class BarChart(QWidget):
    """Barras por mês com crescimento animado, baseline e rótulos limpos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._values: list[float] = [0.0] * 12
        self._labels: list[str] = []
        self._grow = 1.0
        self._anim: QPropertyAnimation | None = None
        self.setMinimumHeight(200)

    def set_data(self, values: list[float], labels: list[str], animate: bool = True) -> None:
        self._values = list(values)
        self._labels = list(labels)
        if not animate or not self.isVisible():
            self._grow = 1.0
            self.update()
            return
        if self._anim is not None:
            self._anim.stop()
        anim = QPropertyAnimation(self, b"grow", self)
        anim.setDuration(620)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._anim = anim

    def _get_grow(self) -> float:
        return self._grow

    def _set_grow(self, v: float) -> None:
        self._grow = v
        self.update()

    grow = Property(float, _get_grow, _set_grow)

    def showEvent(self, e):
        super().showEvent(e)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.width(), self.height()
        pad_left, pad_right = 10, 10
        pad_top, pad_bottom = 14, 26
        plot = QRectF(pad_left, pad_top, w - pad_left - pad_right,
                      h - pad_top - pad_bottom)

        vmax = max(self._values) if self._values and max(self._values) > 0 else 1.0

        # gridlines suaves
        grid_pen = QPen(QColor(theme.BORDER))
        grid_pen.setWidth(1)
        p.setPen(grid_pen)
        for frac in (0.0, 0.5, 1.0):
            y = plot.bottom() - frac * plot.height()
            p.drawLine(int(plot.left()), int(y), int(plot.right()), int(y))

        n = len(self._values)
        if n == 0:
            p.end()
            return

        slot = plot.width() / n
        bar_w = min(26.0, slot * 0.55)
        font = QFont(theme.FONT_FAMILY)
        font.setPointSize(8)

        for i, val in enumerate(self._values):
            cx = plot.left() + slot * (i + 0.5)
            frac = (val / vmax) if vmax > 0 else 0.0
            bh = frac * plot.height() * self._grow
            bar = QRectF(cx - bar_w / 2, plot.bottom() - bh, bar_w, bh)

            grad = QLinearGradient(0, bar.top(), 0, bar.bottom())
            if val > 0:
                grad.setColorAt(0.0, QColor(theme.PRIMARY_GRAD_1))
                grad.setColorAt(1.0, QColor(theme.PRIMARY_GRAD_2))
            else:
                grad.setColorAt(0.0, QColor(theme.BORDER))
                grad.setColorAt(1.0, QColor(theme.BORDER))
            p.setPen(Qt.NoPen)
            p.setBrush(grad)
            radius = min(6.0, bar_w / 2)
            if bh > 1:
                p.drawRoundedRect(bar, radius, radius)
            else:
                # marca de "vazio" — ponto na baseline
                p.setBrush(QColor(theme.BORDER))
                p.drawEllipse(QRectF(cx - 2, plot.bottom() - 2, 4, 4))

            # rótulo do mês
            if i < len(self._labels):
                p.setFont(font)
                p.setPen(QColor(theme.TEXT_SUBTLE))
                p.drawText(
                    QRectF(cx - slot / 2, plot.bottom() + 4, slot, 18),
                    Qt.AlignHCenter | Qt.AlignTop, self._labels[i],
                )
        p.end()
