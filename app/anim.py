"""Helpers de animação reutilizáveis (PySide6).

Centraliza curvas e padrões usados em todo o app para que as microinterações
fiquem consistentes e o código não espalhe lógica de animação solta.
"""
from __future__ import annotations

from PySide6.QtCore import (
    QAbstractAnimation, QEasingCurve, QPoint, QPropertyAnimation, Qt,
)
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

# Curvas padrão do app
EASE_OUT     = QEasingCurve.OutCubic
EASE_IN      = QEasingCurve.InCubic
EASE_IN_OUT  = QEasingCurve.InOutCubic
EASE_QUINT   = QEasingCurve.OutQuint
EASE_SPRING  = QEasingCurve.OutBack    # leve overshoot ("mola")


def _curve(c: QEasingCurve.Type, overshoot: float | None = None) -> QEasingCurve:
    ec = QEasingCurve(c)
    if overshoot is not None:
        ec.setOvershoot(overshoot)
    return ec


def fade_in(
    widget: QWidget,
    duration: int = 220,
    start: float = 0.0,
    curve: QEasingCurve.Type = EASE_OUT,
    on_finished=None,
) -> QPropertyAnimation:
    """Aplica um QGraphicsOpacityEffect e faz fade até 1.0, removendo-o ao fim."""
    eff = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(eff)
    eff.setOpacity(start)
    anim = QPropertyAnimation(eff, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(1.0)
    anim.setEasingCurve(_curve(curve))

    def _done():
        # remove o efeito para não pesar/affetar repaints futuros
        if widget is not None:
            widget.setGraphicsEffect(None)
        if on_finished:
            on_finished()

    anim.finished.connect(_done)
    anim.start(QAbstractAnimation.DeleteWhenStopped)
    return anim


def window_pop_in(
    win: QWidget,
    duration: int = 260,
    rise: int = 14,
    curve: QEasingCurve.Type = EASE_OUT,
) -> QPropertyAnimation:
    """Entrada elegante para janelas/diálogos frameless top-level:
    fade de opacidade + leve subida. Usa windowOpacity (não conflita com
    efeitos de opacidade aplicados ao conteúdo)."""
    target = win.pos()
    win.setWindowOpacity(0.0)
    win.move(target.x(), target.y() + rise)

    fade = QPropertyAnimation(win, b"windowOpacity", win)
    fade.setDuration(duration)
    fade.setStartValue(0.0)
    fade.setEndValue(1.0)
    fade.setEasingCurve(_curve(curve))

    move = QPropertyAnimation(win, b"pos", win)
    move.setDuration(duration)
    move.setStartValue(QPoint(target.x(), target.y() + rise))
    move.setEndValue(QPoint(target.x(), target.y()))
    move.setEasingCurve(_curve(curve))

    fade.start(QAbstractAnimation.DeleteWhenStopped)
    move.start(QAbstractAnimation.DeleteWhenStopped)
    return fade


def make_opacity(widget: QWidget, start: float = 1.0) -> tuple[QGraphicsOpacityEffect, "function"]:
    """Devolve (efeito, setter). Útil para animar opacidade de um sub-widget."""
    eff = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(eff)
    eff.setOpacity(start)
    return eff, eff.setOpacity
