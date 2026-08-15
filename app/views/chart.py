"""Gráfico de barras minimalista (QPainter) para o dashboard anual.

v2: crescimento em cascata (stagger por barra), hover interativo com tooltip
de valor e coreografia de entrada — se os dados chegam com o widget oculto,
as barras crescem quando a página aparece.
"""
from __future__ import annotations

from PySide6.QtCore import (
    Property, QEasingCurve, QPropertyAnimation, QRectF, Qt,
)
from PySide6.QtGui import (
    QColor, QFont, QLinearGradient, QMouseEvent, QPainter, QPainterPath, QPen,
)
from PySide6.QtWidgets import QWidget

from .. import theme
from ..utils import minutes_to_hhmm


class BarChart(QWidget):
    """Barras por mês com crescimento animado, baseline e rótulos limpos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._values: list[float] = [0.0] * 12
        self._labels: list[str] = []
        self._grow = 1.0
        self._anim: QPropertyAnimation | None = None
        self._pending_entrance = False
        self._hover_idx = -1
        self.setMinimumHeight(200)
        self.setMouseTracking(True)

    def set_data(self, values: list[float], labels: list[str], animate: bool = True) -> None:
        self._values = list(values)
        self._labels = list(labels)
        if not animate:
            self._grow = 1.0
            self.update()
            return
        if not self.isVisible():
            # entra zerado; cresce quando a página aparecer (showEvent)
            self._grow = 0.0
            self._pending_entrance = True
            self.update()
            return
        self._start_grow()

    def _start_grow(self) -> None:
        if self._anim is not None:
            self._anim.stop()
        anim = QPropertyAnimation(self, b"grow", self)
        anim.setDuration(720)
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
        if self._pending_entrance:
            self._pending_entrance = False
            self._start_grow()
        self.update()

    # ---------------- hover ----------------
    def _plot_rect(self) -> QRectF:
        return QRectF(10, 14, self.width() - 20, self.height() - 14 - 26)

    def mouseMoveEvent(self, e: QMouseEvent):
        plot = self._plot_rect()
        n = len(self._values)
        idx = -1
        if n and plot.contains(e.position()):
            slot = plot.width() / n
            idx = int((e.position().x() - plot.left()) // slot)
            idx = max(0, min(n - 1, idx))
            if self._values[idx] <= 0:
                idx = -1
        if idx != self._hover_idx:
            self._hover_idx = idx
            self.update()
        super().mouseMoveEvent(e)

    def leaveEvent(self, e):
        if self._hover_idx != -1:
            self._hover_idx = -1
            self.update()
        super().leaveEvent(e)

    # ---------------- pintura ----------------
    @staticmethod
    def _bar_local_t(global_t: float, i: int, n: int) -> float:
        """Progresso individual da barra i com atraso em cascata."""
        if n <= 1:
            return global_t
        delay = 0.35 * (i / (n - 1))
        span = 1.0 - delay
        if span <= 0:
            return global_t
        return max(0.0, min(1.0, (global_t - delay) / span))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        plot = self._plot_rect()
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
            local_t = self._bar_local_t(self._grow, i, n)
            bh = frac * plot.height() * local_t
            bar = QRectF(cx - bar_w / 2, plot.bottom() - bh, bar_w, bh)
            hovered = i == self._hover_idx

            grad = QLinearGradient(0, bar.top(), 0, bar.bottom())
            if val > 0:
                if hovered:
                    grad.setColorAt(0.0, QColor(theme.VIOLET))
                    grad.setColorAt(1.0, QColor(theme.PRIMARY))
                else:
                    grad.setColorAt(0.0, QColor(theme.PRIMARY_GRAD_1))
                    grad.setColorAt(1.0, QColor(theme.PRIMARY_GRAD_2))
            else:
                grad.setColorAt(0.0, QColor(theme.BORDER))
                grad.setColorAt(1.0, QColor(theme.BORDER))
            p.setPen(Qt.NoPen)
            p.setBrush(grad)
            radius = min(6.0, bar_w / 2)
            if bh > 1:
                # arredonda apenas o topo da barra
                path = QPainterPath()
                path.addRoundedRect(bar, radius, radius)
                path.addRect(QRectF(bar.left(), bar.bottom() - radius,
                                    bar.width(), radius))
                p.drawPath(path.simplified())
            else:
                # marca de "vazio" — ponto na baseline
                p.setBrush(QColor(theme.BORDER))
                p.drawEllipse(QRectF(cx - 2, plot.bottom() - 2, 4, 4))

            # rótulo do mês
            if i < len(self._labels):
                p.setFont(font)
                p.setPen(QColor(
                    theme.PRIMARY if hovered else theme.TEXT_SUBTLE
                ))
                p.drawText(
                    QRectF(cx - slot / 2, plot.bottom() + 4, slot, 18),
                    Qt.AlignHCenter | Qt.AlignTop, self._labels[i],
                )

            # tooltip com o valor em HH:MM acima da barra
            if hovered and bh > 1:
                texto = minutes_to_hhmm(int(round(val * 60)))
                tip_font = QFont(theme.FONT_FAMILY)
                tip_font.setPointSize(8)
                tip_font.setWeight(QFont.DemiBold)
                p.setFont(tip_font)
                fm = p.fontMetrics()
                tw = fm.horizontalAdvance(texto) + 16
                th = fm.height() + 8
                tx = cx - tw / 2
                ty = bar.top() - th - 6
                if ty < 0:
                    ty = bar.top() + 6
                tip = QRectF(tx, ty, tw, th)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(theme.CHROME_BOT))
                p.drawRoundedRect(tip, 7, 7)
                p.setPen(QColor("#FFFFFF"))
                p.drawText(tip, Qt.AlignCenter, texto)
        p.end()
