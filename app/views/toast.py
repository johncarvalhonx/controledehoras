"""Toasts — notificações discretas e animadas no canto da janela.

v2: chip de ícone tonal, barra de progresso do tempo restante, clique para
fechar e entrada com leve efeito de mola.
"""
from __future__ import annotations

from PySide6.QtCore import (
    QAbstractAnimation, QEasingCurve, QEvent, QPoint, QPropertyAnimation,
    QTimer, QVariantAnimation, Qt, Signal,
)
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPainterPath
from PySide6.QtWidgets import QGraphicsOpacityEffect, QHBoxLayout, QLabel, QWidget

from .. import icons
from .. import theme
from .widgets import attach_shadow

_KINDS = {
    "success": {
        "icon": "check-circle", "fg": theme.ACCENT_DARK,
        "bar": theme.ACCENT, "chip": theme.ACCENT_SOFT,
    },
    "error": {
        "icon": "alert-triangle", "fg": theme.DANGER_DARK,
        "bar": theme.DANGER, "chip": theme.DANGER_SOFT,
    },
    "info": {
        "icon": "info", "fg": theme.PRIMARY,
        "bar": theme.PRIMARY, "chip": theme.PRIMARY_SOFT,
    },
}


class Toast(QWidget):
    dismissed = Signal(object)  # emitido ao clicar (self)

    def __init__(self, message: str, kind: str, timeout: int, parent=None):
        super().__init__(parent)
        cfg = _KINDS.get(kind, _KINDS["info"])
        self._bar = QColor(cfg["bar"])
        self._chip_bg = QColor(cfg["chip"])
        self._progress = 1.0
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setCursor(Qt.PointingHandCursor)
        attach_shadow(self, blur=30, dy=10, alpha=55)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 18, 14)
        lay.setSpacing(12)

        chip = QLabel()
        chip.setFixedSize(32, 32)
        chip.setAlignment(Qt.AlignCenter)
        chip.setStyleSheet(
            f"background-color:{cfg['chip']}; border-radius:9px;"
        )
        chip.setPixmap(icons.pixmap(cfg["icon"], cfg["fg"], 19, 2.2))
        lay.addWidget(chip, 0, Qt.AlignVCenter)

        text = QLabel(message)
        text.setStyleSheet(
            f"color:{theme.TEXT}; background:transparent; "
            "font-size:9.5pt; font-weight:600;"
        )
        text.setWordWrap(True)
        lay.addWidget(text, 1)

        self.setFixedWidth(340)
        self.adjustSize()

        # barra de progresso do tempo restante
        self._progress_anim = QVariantAnimation(self)
        self._progress_anim.setStartValue(1.0)
        self._progress_anim.setEndValue(0.0)
        self._progress_anim.setDuration(timeout)

        def _tick(v):
            self._progress = float(v)
            self.update()

        self._progress_anim.valueChanged.connect(_tick)
        self._progress_anim.start()

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self.dismissed.emit(self)
            e.accept()
            return
        super().mousePressEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = self.rect().adjusted(0, 0, -1, -1)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(theme.SURFACE))
        p.drawRoundedRect(r, 12, 12)

        # barra de progresso na base (encolhe conforme o tempo passa)
        if self._progress > 0.005:
            path = QPainterPath()
            path.addRoundedRect(0, 0, r.width(), r.height(), 12, 12)
            p.setClipPath(path)
            track = QColor(self._bar)
            track.setAlpha(36)
            p.setBrush(track)
            p.drawRect(0, r.height() - 3, r.width(), 3)
            p.setBrush(self._bar)
            p.drawRect(0, r.height() - 3, int(r.width() * self._progress), 3)
        p.end()


class ToastManager:
    """Gerencia a pilha de toasts no canto superior direito de um host."""

    MARGIN = 18
    SPACING = 12

    def __init__(self, host: QWidget):
        self._host = host
        self._toasts: list[Toast] = []
        host.installEventFilter(_HostWatcher(self))

    def show(self, message: str, kind: str = "success", timeout: int = 3000) -> None:
        toast = Toast(message, kind, timeout, self._host)
        toast.dismissed.connect(self._dismiss)
        toast.show()
        self._toasts.append(toast)
        self._relayout(animate_new=toast)
        QTimer.singleShot(timeout, lambda: self._dismiss(toast))

    def _dismiss(self, toast: Toast) -> None:
        if toast not in self._toasts:
            return
        self._toasts.remove(toast)

        # fade + deslize para a direita
        eff = QGraphicsOpacityEffect(toast)
        toast.setGraphicsEffect(eff)
        fade = QPropertyAnimation(eff, b"opacity", toast)
        fade.setDuration(190)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.InCubic)

        slide = QPropertyAnimation(toast, b"pos", toast)
        slide.setDuration(190)
        slide.setStartValue(toast.pos())
        slide.setEndValue(toast.pos() + QPoint(34, 0))
        slide.setEasingCurve(QEasingCurve.InCubic)

        fade.finished.connect(toast.deleteLater)
        fade.finished.connect(self._relayout)
        fade.start(QAbstractAnimation.DeleteWhenStopped)
        slide.start(QAbstractAnimation.DeleteWhenStopped)

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
                start = QPoint(x_right - tw + 56, y)
                toast.move(start)
                anim = QPropertyAnimation(toast, b"pos", toast)
                anim.setDuration(340)
                anim.setStartValue(start)
                anim.setEndValue(target)
                curve = QEasingCurve(QEasingCurve.OutBack)
                curve.setOvershoot(1.2)
                anim.setEasingCurve(curve)
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
