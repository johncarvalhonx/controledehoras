"""Toasts — notificações discretas e animadas no canto da janela."""
from __future__ import annotations

from PySide6.QtCore import (
    QAbstractAnimation, QEasingCurve, QPoint, QPropertyAnimation, QTimer, Qt,
    QEvent,
)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QGraphicsOpacityEffect, QHBoxLayout, QLabel, QWidget

from .. import icons
from .. import theme
from .widgets import attach_shadow

_KINDS = {
    "success": {"icon": "check-circle", "fg": theme.ACCENT_DARK, "bar": theme.ACCENT},
    "error":   {"icon": "alert-triangle", "fg": theme.DANGER_DARK, "bar": theme.DANGER},
    "info":    {"icon": "info", "fg": theme.PRIMARY, "bar": theme.PRIMARY},
}


class Toast(QWidget):
    def __init__(self, message: str, kind: str, parent=None):
        super().__init__(parent)
        cfg = _KINDS.get(kind, _KINDS["info"])
        self._bar = QColor(cfg["bar"])
        self.setAttribute(Qt.WA_StyledBackground, False)
        attach_shadow(self, blur=30, dy=10, alpha=55)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 18, 12)
        lay.setSpacing(12)

        icon = QLabel()
        icon.setFixedSize(26, 26)
        icon.setAlignment(Qt.AlignCenter)
        icon.setPixmap(icons.pixmap(cfg["icon"], cfg["fg"], 24, 2.2))
        lay.addWidget(icon, 0)

        text = QLabel(message)
        text.setStyleSheet(
            f"color:{theme.TEXT}; background:transparent; font-size:9.5pt; font-weight:600;"
        )
        text.setWordWrap(True)
        lay.addWidget(text, 1)

        self.setFixedWidth(330)
        self.adjustSize()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = self.rect().adjusted(0, 0, -1, -1)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(theme.SURFACE))
        p.drawRoundedRect(r, 12, 12)
        # barra de acento à esquerda
        p.setBrush(self._bar)
        p.drawRoundedRect(0, 8, 4, r.height() - 16, 2, 2)
        p.end()


class ToastManager:
    """Gerencia a pilha de toasts no canto superior direito de um host."""

    MARGIN = 18
    SPACING = 12

    def __init__(self, host: QWidget):
        self._host = host
        self._toasts: list[Toast] = []
        host.installEventFilter(_HostWatcher(self))

    def show(self, message: str, kind: str = "success", timeout: int = 2600) -> None:
        toast = Toast(message, kind, self._host)
        toast.show()
        self._toasts.append(toast)
        self._relayout(animate_new=toast)
        QTimer.singleShot(timeout, lambda: self._dismiss(toast))

    def _dismiss(self, toast: Toast) -> None:
        if toast not in self._toasts:
            return
        eff = QGraphicsOpacityEffect(toast)
        toast.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", toast)
        anim.setDuration(200)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InCubic)

        def done():
            if toast in self._toasts:
                self._toasts.remove(toast)
            toast.deleteLater()
            self._relayout()

        anim.finished.connect(done)
        anim.start(QAbstractAnimation.DeleteWhenStopped)

    def _relayout(self, animate_new: Toast | None = None) -> None:
        if not self._host:
            return
        x_right = self._host.width() - self.MARGIN
        y = self.MARGIN + 44  # abaixo da title bar
        for toast in self._toasts:
            tw = toast.width()
            th = toast.sizeHint().height()
            toast.resize(tw, th)
            target = QPoint(x_right - tw, y)
            if toast is animate_new:
                start = QPoint(x_right - tw + 40, y)
                toast.move(start)
                anim = QPropertyAnimation(toast, b"pos", toast)
                anim.setDuration(theme.DUR_BASE)
                anim.setStartValue(start)
                anim.setEndValue(target)
                anim.setEasingCurve(QEasingCurve.OutCubic)
                anim.start(QAbstractAnimation.DeleteWhenStopped)
            else:
                anim = QPropertyAnimation(toast, b"pos", toast)
                anim.setDuration(theme.DUR_BASE)
                anim.setStartValue(toast.pos())
                anim.setEndValue(target)
                anim.setEasingCurve(QEasingCurve.OutCubic)
                anim.start(QAbstractAnimation.DeleteWhenStopped)
            toast.raise_()
            y += th + self.SPACING


class _HostWatcher(QWidget):
    """Observa redimensionamento do host para reposicionar os toasts."""

    def __init__(self, manager: ToastManager):
        super().__init__()
        self._manager = manager

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            self._manager._relayout()
        return False
