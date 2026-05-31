"""Widgets reutilizáveis premium: cards com sombra, ícone tonal e seletor de mês animado."""
from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve, QPropertyAnimation, QRect, QRectF, Qt, Signal,
)
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QHBoxLayout,
    QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from .. import icons
from .. import theme


# =====================================================================
#  Sombra reutilizável
# =====================================================================
def attach_shadow(
    widget: QWidget,
    blur: int = 26,
    dy: int = 10,
    alpha: int = 34,
    color: str = "#1E293B",
) -> QGraphicsDropShadowEffect:
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(blur)
    eff.setXOffset(0)
    eff.setYOffset(dy)
    c = QColor(color)
    c.setAlpha(alpha)
    eff.setColor(c)
    widget.setGraphicsEffect(eff)
    return eff


# =====================================================================
#  Card genérico (fundo branco, borda, sombra suave)
# =====================================================================
class Card(QFrame):
    def __init__(self, parent=None, *, shadow: bool = True):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setFrameShape(QFrame.NoFrame)
        if shadow:
            attach_shadow(self, blur=24, dy=8, alpha=28)


# =====================================================================
#  SummaryCard — métrica com ícone tonal, hover elevado e pulse de valor
# =====================================================================
class SummaryCard(QFrame):
    def __init__(
        self,
        label: str,
        value: str = "—",
        value_style: str = "CardValue",
        icon_name: str = "clock",
        icon_tone: str = "primary",
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("SummaryCard")
        self.setFrameShape(QFrame.NoFrame)
        self.setAttribute(Qt.WA_Hover, True)
        self._tone = theme.TONES.get(icon_tone, theme.TONES["primary"])

        self._shadow = attach_shadow(self, blur=24, dy=8, alpha=26)
        self._hover_anim: QPropertyAnimation | None = None

        outer = QHBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(16)

        # chip do ícone
        self._chip = QLabel()
        self._chip.setObjectName("CardIconChip")
        self._chip.setProperty("tone", icon_tone)
        self._chip.setFixedSize(48, 48)
        self._chip.setAlignment(Qt.AlignCenter)
        self._chip.setPixmap(icons.pixmap(icon_name, self._tone["fg"], 24, 2.1))
        outer.addWidget(self._chip, 0, Qt.AlignVCenter)

        col = QVBoxLayout()
        col.setSpacing(3)
        col.setContentsMargins(0, 0, 0, 0)
        self._label = QLabel(label)
        self._label.setObjectName("CardLabel")
        self._label.setWordWrap(True)
        self._value = QLabel(value)
        self._value.setObjectName(value_style)
        self._value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        col.addStretch(1)
        col.addWidget(self._label)
        col.addWidget(self._value)
        col.addStretch(1)
        outer.addLayout(col, 1)

        self._pulse_anim: QPropertyAnimation | None = None

    # ---- valor + pulse ----
    def set_value(self, value: str, animate: bool = True) -> None:
        changed = self._value.text() != value
        self._value.setText(value)
        if changed and animate:
            self._pulse()

    def _pulse(self) -> None:
        eff = QGraphicsOpacityEffect(self._value)
        self._value.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self._value)
        anim.setDuration(420)
        anim.setStartValue(0.15)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: self._value.setGraphicsEffect(None))
        anim.start()
        self._pulse_anim = anim

    # ---- hover: eleva a sombra ----
    def _animate_shadow(self, blur: int, dy: int, alpha: int) -> None:
        if self._hover_anim is not None:
            self._hover_anim.stop()
        anim = QPropertyAnimation(self._shadow, b"blurRadius", self)
        anim.setDuration(170)
        anim.setStartValue(self._shadow.blurRadius())
        anim.setEndValue(blur)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._hover_anim = anim
        self._shadow.setYOffset(dy)
        c = self._shadow.color()
        c.setAlpha(alpha)
        self._shadow.setColor(c)

    def enterEvent(self, e):
        self._animate_shadow(blur=40, dy=14, alpha=48)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._animate_shadow(blur=24, dy=8, alpha=26)
        super().leaveEvent(e)


def field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("FieldLabel")
    return lbl


# =====================================================================
#  MonthSelector — seletor Jan..Dez com pílula indicadora deslizante
# =====================================================================
class _MonthCell(QWidget):
    clicked = Signal(int)

    def __init__(self, label: str, index: int, parent=None):
        super().__init__(parent)
        self._label = label
        self._index = index
        self._active = False
        self._hover = False
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
        self.setMinimumHeight(38)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_active(self, active: bool) -> None:
        if self._active != active:
            self._active = active
            self.update()

    def enterEvent(self, e):
        self._hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self.update()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self._index)
        super().mousePressEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)

        if not self._active and self._hover:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(theme.PRIMARY_SOFT))
            p.drawRoundedRect(r, 9, 9)

        if self._active:
            color = QColor("#FFFFFF")
            font = QFont(theme.FONT_FAMILY)
            font.setPointSize(10)
            font.setWeight(QFont.DemiBold)
        else:
            color = QColor(theme.PRIMARY if self._hover else theme.TEXT_MUTED)
            font = QFont(theme.FONT_FAMILY)
            font.setPointSize(10)
            font.setWeight(QFont.Medium)
        p.setFont(font)
        p.setPen(color)
        p.drawText(self.rect(), Qt.AlignCenter, self._label)
        p.end()


class _MonthPill(QWidget):
    """Pílula com gradiente indigo + sombra, deslizada por trás da célula ativa."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        attach_shadow(self, blur=18, dy=5, alpha=90, color=theme.PRIMARY)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        grad = QLinearGradient(0, 0, 0, r.height())
        grad.setColorAt(0.0, QColor(theme.PRIMARY_GRAD_1))
        grad.setColorAt(1.0, QColor(theme.PRIMARY_GRAD_2))
        p.setPen(Qt.NoPen)
        p.setBrush(grad)
        p.drawRoundedRect(r, 9, 9)
        p.end()


class MonthSelector(QWidget):
    """Linha Jan..Dez com indicador animado. Emite monthChanged(1..12)."""

    monthChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current = 1
        self._cells: list[_MonthCell] = []

        self.setMinimumHeight(50)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(2)

        self._pill = _MonthPill(self)
        self._pill.lower()

        for i, nome in enumerate(theme_meses(), start=1):
            cell = _MonthCell(nome, i, self)
            cell.clicked.connect(self._on_cell)
            self._cells.append(cell)
            lay.addWidget(cell)

        self._pill_anim: QPropertyAnimation | None = None

    def set_month(self, month: int, animate: bool = True) -> None:
        month = max(1, min(12, int(month)))
        self._current = month
        for c in self._cells:
            c.set_active(c._index == month)
        self._move_pill(animate)

    def current_month(self) -> int:
        return self._current

    def _on_cell(self, index: int) -> None:
        if index == self._current:
            return
        self.set_month(index, animate=True)
        self.monthChanged.emit(index)

    def _target_rect(self) -> QRect:
        cell = self._cells[self._current - 1]
        return cell.geometry()

    def _move_pill(self, animate: bool) -> None:
        target = self._target_rect()
        if target.width() <= 0:
            return
        if not animate or not self._pill.isVisible():
            self._pill.setGeometry(target)
            self._pill.show()
            return
        anim = QPropertyAnimation(self._pill, b"geometry", self)
        anim.setDuration(theme.DUR_SLOW)
        anim.setStartValue(self._pill.geometry())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._pill_anim = anim

    def showEvent(self, e):
        super().showEvent(e)
        self._move_pill(animate=False)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # reposiciona instantaneamente ao redimensionar
        target = self._target_rect()
        if target.width() > 0 and (self._pill_anim is None or
                                   self._pill_anim.state() != QPropertyAnimation.Running):
            self._pill.setGeometry(target)


def theme_meses() -> list[str]:
    from ..config import MESES_PT_CURTO
    return MESES_PT_CURTO
