"""Botões de controle de janela (min / max / restore / close) pintados via QPainter.

Hover/press com transição animada de fundo — sempre nítidos em qualquer DPI.
"""
from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QPushButton

from .. import theme


def _lerp(c1: QColor, c2: QColor, t: float) -> QColor:
    t = max(0.0, min(1.0, t))
    return QColor(
        int(c1.red()   + (c2.red()   - c1.red())   * t),
        int(c1.green() + (c2.green() - c1.green()) * t),
        int(c1.blue()  + (c2.blue()  - c1.blue())  * t),
        int(c1.alpha() + (c2.alpha() - c1.alpha()) * t),
    )


class WindowControlButton(QPushButton):
    TYPES = ("min", "max", "restore", "close")

    def __init__(self, kind: str, on_dark: bool = True, parent=None):
        super().__init__(parent)
        if kind not in self.TYPES:
            raise ValueError(f"tipo inválido: {kind}")
        self._kind = kind
        self._on_dark = on_dark
        self._hover_t = 0.0
        self._hover_anim: QPropertyAnimation | None = None
        self.setFixedSize(46, 38)
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.ArrowCursor)
        self.setAttribute(Qt.WA_Hover, True)
        self.setObjectName("WinCtrl")  # estilizado só por nós (sem bg via QSS)

    # ---- estado animado ----
    def _get_ht(self) -> float:
        return self._hover_t

    def _set_ht(self, v: float) -> None:
        self._hover_t = v
        self.update()

    hoverProgress = Property(float, _get_ht, _set_ht)

    def _animate_to(self, target: float) -> None:
        if self._hover_anim is not None:
            self._hover_anim.stop()
        anim = QPropertyAnimation(self, b"hoverProgress", self)
        anim.setDuration(130)
        anim.setStartValue(self._hover_t)
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._hover_anim = anim

    def kind(self) -> str:
        return self._kind

    def set_kind(self, kind: str) -> None:
        if kind in self.TYPES and kind != self._kind:
            self._kind = kind
            self.update()

    # ---- pintura ----
    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        t = self._hover_t
        if self.isDown():
            t = min(1.0, t + 0.18)

        # fundo
        if t > 0.001:
            if self._kind == "close":
                bg = _lerp(QColor(232, 17, 35, 0), QColor(232, 17, 35, 255), t)
                if self.isDown():
                    bg = QColor("#C50F1F")
            elif self._on_dark:
                bg = _lerp(QColor(255, 255, 255, 0), QColor(255, 255, 255, 28), t)
            else:
                bg = _lerp(QColor(15, 23, 42, 0), QColor(15, 23, 42, 22), t)
            p.setPen(Qt.NoPen)
            p.setBrush(bg)
            p.drawRect(self.rect())

        # cor do glifo
        if self._kind == "close":
            idle = QColor("#CBD5E1") if self._on_dark else QColor("#64748B")
            glyph = _lerp(idle, QColor("#FFFFFF"), t)
        elif self._on_dark:
            glyph = _lerp(QColor("#CBD5E1"), QColor("#FFFFFF"), t)
        else:
            glyph = _lerp(QColor("#64748B"), QColor(theme.TEXT), t)

        pen = QPen(glyph)
        pen.setWidthF(1.3)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        cx = self.width() / 2.0
        cy = self.height() / 2.0
        s = 5.0

        if self._kind == "min":
            y = cy + 0.5
            p.drawLine(int(cx - s), int(y), int(cx + s), int(y))
        elif self._kind == "max":
            p.drawRoundedRect(QRectF(cx - s, cy - s, 2 * s, 2 * s), 1.4, 1.4)
        elif self._kind == "restore":
            # quadrado da frente (outline completo)
            front = QRectF(cx - s, cy - s + 2, 2 * s - 2, 2 * s - 2)
            p.drawRoundedRect(front, 1.2, 1.2)
            # quadrado de trás: apenas topo + lado direito (L), sem precisar apagar
            p.drawLine(int(cx - s + 2), int(cy - s), int(cx + s), int(cy - s))
            p.drawLine(int(cx + s), int(cy - s), int(cx + s), int(cy + s - 2))
        elif self._kind == "close":
            p.drawLine(int(cx - s), int(cy - s), int(cx + s), int(cy + s))
            p.drawLine(int(cx - s), int(cy + s), int(cx + s), int(cy - s))
        p.end()

    def enterEvent(self, e):
        self._animate_to(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._animate_to(0.0)
        super().leaveEvent(e)
