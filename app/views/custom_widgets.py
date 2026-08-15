"""Componentes customizados reutilizáveis."""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import (
    Property, QEasingCurve, QParallelAnimationGroup, QPointF, QSize,
    QPropertyAnimation, QRect, QRectF, Qt, Signal,
)
from PySide6.QtGui import (
    QColor, QFont, QLinearGradient, QMouseEvent, QPainter, QPainterPath,
    QPen, QWheelEvent,
)
from PySide6.QtWidgets import (
    QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from .. import icons
from .. import theme
from ..anim import window_pop_in
from ..utils import format_brl
from .window_controls import WindowControlButton


SHADOW_MARGIN = 14  # margem ao redor da janela para a sombra


# =====================================================================
#  AnimatedButton — ripple (Material) + hover animado + glow opcional
# =====================================================================
class AnimatedButton(QPushButton):
    """Botão com ripple ao clicar, brilho de hover animado e, opcionalmente,
    uma sombra colorida ("glow") que se intensifica no hover. Herda todo o
    QSS por objectName."""

    def __init__(
        self,
        text: str = "",
        *,
        radius: int = 10,
        ripple_light: bool = False,
        glow: bool = False,
        parent=None,
    ):
        super().__init__(text, parent)
        self._radius = radius
        # Cor do ripple já com o alpha de pico embutido; multiplicamos pela
        # opacidade animada (1 → 0) na hora de pintar.
        self._ripple_light = ripple_light
        self._ripple_color = self._color_for(ripple_light)
        self._ripple_radius = 0.0
        self._ripple_opacity = 0.0
        self._ripple_center = QPointF()
        self._ripple_anim: QParallelAnimationGroup | None = None
        self._hover_t = 0.0
        self._hover_anim: QPropertyAnimation | None = None
        self._glow: QGraphicsDropShadowEffect | None = None
        self._glow_anim: QPropertyAnimation | None = None
        if glow:
            self._glow = QGraphicsDropShadowEffect(self)
            self._glow.setBlurRadius(18)
            self._glow.setXOffset(0)
            self._glow.setYOffset(5)
            c = QColor(theme.PRIMARY)
            c.setAlpha(80)
            self._glow.setColor(c)
            self.setGraphicsEffect(self._glow)
        self.setAttribute(Qt.WA_Hover, True)

    @staticmethod
    def _color_for(light: bool) -> QColor:
        # branco translúcido sobre botões coloridos; azul translúcido sobre claros
        return QColor(255, 255, 255, 90) if light else QColor(37, 99, 235, 55)

    def set_ripple_light(self, light: bool) -> None:
        self._ripple_light = light
        self._ripple_color = self._color_for(light)

    # ---- propriedades animáveis ----
    def _get_rr(self) -> float:
        return self._ripple_radius

    def _set_rr(self, v: float) -> None:
        self._ripple_radius = v
        self.update()

    rippleRadius = Property(float, _get_rr, _set_rr)

    def _get_ro(self) -> float:
        return self._ripple_opacity

    def _set_ro(self, v: float) -> None:
        self._ripple_opacity = v
        self.update()

    rippleOpacity = Property(float, _get_ro, _set_ro)

    def _get_ht(self) -> float:
        return self._hover_t

    def _set_ht(self, v: float) -> None:
        self._hover_t = v
        self.update()

    hoverProgress = Property(float, _get_ht, _set_ht)

    # ---- hover animado ----
    def _animate_hover(self, target: float) -> None:
        if self._hover_anim is not None:
            self._hover_anim.stop()
        anim = QPropertyAnimation(self, b"hoverProgress", self)
        anim.setDuration(theme.DUR_FAST)
        anim.setStartValue(self._hover_t)
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._hover_anim = anim
        if self._glow is not None:
            if self._glow_anim is not None:
                self._glow_anim.stop()
            ganim = QPropertyAnimation(self._glow, b"blurRadius", self)
            ganim.setDuration(180)
            ganim.setStartValue(self._glow.blurRadius())
            ganim.setEndValue(30 if target > 0.5 else 18)
            ganim.setEasingCurve(QEasingCurve.OutCubic)
            ganim.start()
            self._glow_anim = ganim
            c = QColor(theme.PRIMARY)
            c.setAlpha(120 if target > 0.5 else 80)
            self._glow.setColor(c)

    def enterEvent(self, e):
        if self.isEnabled():
            self._animate_hover(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._animate_hover(0.0)
        super().leaveEvent(e)

    # ---- disparo do ripple ----
    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton and self.isEnabled():
            self._ripple_center = e.position()
            self._start_ripple()
        super().mousePressEvent(e)

    def _start_ripple(self) -> None:
        if self._ripple_anim is not None:
            self._ripple_anim.stop()

        cx, cy = self._ripple_center.x(), self._ripple_center.y()
        w, h = self.width(), self.height()
        max_r = max(
            ((cx - x) ** 2 + (cy - y) ** 2) ** 0.5
            for x, y in ((0, 0), (w, 0), (0, h), (w, h))
        )

        a_r = QPropertyAnimation(self, b"rippleRadius", self)
        a_r.setStartValue(max_r * 0.18)
        a_r.setEndValue(max_r)
        a_r.setDuration(440)
        a_r.setEasingCurve(QEasingCurve.OutCubic)

        a_o = QPropertyAnimation(self, b"rippleOpacity", self)
        a_o.setStartValue(1.0)
        a_o.setEndValue(0.0)
        a_o.setDuration(480)
        a_o.setEasingCurve(QEasingCurve.OutCubic)

        grp = QParallelAnimationGroup(self)
        grp.addAnimation(a_r)
        grp.addAnimation(a_o)
        grp.start()
        self._ripple_anim = grp

    def paintEvent(self, e):
        super().paintEvent(e)  # QSS pinta fundo, borda e texto
        needs_hover = self._hover_t > 0.01 and self.isEnabled()
        needs_ripple = self._ripple_opacity > 0.01 and self._ripple_radius > 0.5
        if not needs_hover and not needs_ripple:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(self.rect()), self._radius, self._radius)
        p.setClipPath(clip)
        if needs_hover:
            # véu de hover: branco sobre botões coloridos, tinta índigo nos claros
            if self._ripple_light:
                veil = QColor(255, 255, 255, int(26 * self._hover_t))
            else:
                veil = QColor(79, 70, 229, int(14 * self._hover_t))
            p.setPen(Qt.NoPen)
            p.setBrush(veil)
            p.drawRoundedRect(QRectF(self.rect()), self._radius, self._radius)
        if needs_ripple:
            color = QColor(self._ripple_color)
            color.setAlphaF(color.alphaF() * self._ripple_opacity)
            p.setBrush(color)
            p.setPen(Qt.NoPen)
            p.drawEllipse(
                self._ripple_center, self._ripple_radius, self._ripple_radius
            )
        p.end()


# =====================================================================
#  _SpinDisplay — número com transição "odômetro" (slide vertical + fade)
# =====================================================================
class _SpinDisplay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._text = ""
        self._prev = ""
        self._dir = 1
        self._t = 1.0
        self._anim: QPropertyAnimation | None = None
        self._font = QFont(theme.FONT_FAMILY)
        self._font.setPointSize(13)
        self._font.setWeight(QFont.DemiBold)

    def set_text(self, text: str, animate: bool = True, direction: int = 1) -> None:
        if text == self._text:
            return
        self._prev = self._text
        self._text = text
        self._dir = direction
        if not animate or not self.isVisible():
            self._t = 1.0
            self.update()
            return
        if self._anim is not None:
            self._anim.stop()
        anim = QPropertyAnimation(self, b"prog", self)
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._anim = anim

    def _get_prog(self) -> float:
        return self._t

    def _set_prog(self, v: float) -> None:
        self._t = v
        self.update()

    prog = Property(float, _get_prog, _set_prog)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = self.rect()
        # fundo + linhas de topo/base (combina com o restante do input)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(theme.SURFACE))
        p.drawRect(r)
        pen = QPen(QColor(theme.BORDER))
        pen.setWidth(1)
        p.setPen(pen)
        p.drawLine(r.left(), r.top(), r.right(), r.top())
        p.drawLine(r.left(), r.bottom(), r.right(), r.bottom())

        p.setFont(self._font)
        shift = int(r.height() * 0.5)
        t = self._t
        if t < 1.0 and self._prev:
            # texto que sai
            out = QColor(theme.TEXT)
            out.setAlphaF(max(0.0, 1.0 - t))
            p.setPen(out)
            p.drawText(r.translated(0, int(-self._dir * shift * t)),
                       Qt.AlignCenter, self._prev)
            # texto que entra
            inc = QColor(theme.TEXT)
            inc.setAlphaF(t)
            p.setPen(inc)
            p.drawText(r.translated(0, int(self._dir * shift * (1.0 - t))),
                       Qt.AlignCenter, self._text)
        else:
            p.setPen(QColor(theme.TEXT))
            p.drawText(r, Qt.AlignCenter, self._text)
        p.end()


# =====================================================================
#  PlusMinusSpin — spin com botões − / + (ícones vetoriais) e display animado
# =====================================================================
class PlusMinusSpin(QWidget):
    """Spin numérico com botões − e + customizados e transição suave de valor."""

    valueChanged = Signal(int)

    def __init__(
        self,
        *,
        minimum: int = 0,
        maximum: int = 99,
        step: int = 1,
        value: int = 0,
        suffix: str = "",
        width_min: int = 110,
        parent=None,
    ):
        super().__init__(parent)
        self._min = int(minimum)
        self._max = int(maximum)
        self._step = int(step)
        self._suffix = suffix
        self._value = self._clamp(int(value))

        self.setMinimumWidth(width_min)
        self.setFixedHeight(40)
        self.setFocusPolicy(Qt.WheelFocus)

        self._build_ui()
        self.display.set_text(self._fmt(), animate=False)
        self._refresh_icons()
        self._update_buttons()

    def _fmt(self) -> str:
        return f"{self._value:02d}{self._suffix}"

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.btn_minus = QPushButton()
        self.btn_minus.setObjectName("SpinMinus")
        self.btn_minus.setFixedSize(38, 40)
        self.btn_minus.setIconSize(QSize(16, 16))
        self.btn_minus.setCursor(Qt.PointingHandCursor)
        self.btn_minus.setFocusPolicy(Qt.NoFocus)
        self.btn_minus.setAutoRepeat(True)
        self.btn_minus.setAutoRepeatDelay(380)
        self.btn_minus.setAutoRepeatInterval(65)
        self.btn_minus.clicked.connect(self._decrement)

        self.display = _SpinDisplay()

        self.btn_plus = QPushButton()
        self.btn_plus.setObjectName("SpinPlus")
        self.btn_plus.setFixedSize(38, 40)
        self.btn_plus.setIconSize(QSize(16, 16))
        self.btn_plus.setCursor(Qt.PointingHandCursor)
        self.btn_plus.setFocusPolicy(Qt.NoFocus)
        self.btn_plus.setAutoRepeat(True)
        self.btn_plus.setAutoRepeatDelay(380)
        self.btn_plus.setAutoRepeatInterval(65)
        self.btn_plus.clicked.connect(self._increment)

        layout.addWidget(self.btn_minus)
        layout.addWidget(self.display, 1)
        layout.addWidget(self.btn_plus)

    # API
    def value(self) -> int:
        return self._value

    def setValue(self, v: int) -> None:
        v = self._clamp(int(v))
        if v == self._value:
            self._update_buttons()
            return
        direction = 1 if v > self._value else -1
        self._value = v
        self.display.set_text(self._fmt(), animate=True, direction=direction)
        self._update_buttons()
        self.valueChanged.emit(v)

    def setRange(self, mn: int, mx: int) -> None:
        self._min, self._max = int(mn), int(mx)
        self.setValue(self._value)

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        self._refresh_icons()
        self._update_buttons()

    # ---- internos ----
    def _clamp(self, v: int) -> int:
        return max(self._min, min(self._max, v))

    def _refresh_icons(self) -> None:
        color = theme.TEXT_MUTED if self.isEnabled() else theme.TEXT_FAINT
        self.btn_minus.setIcon(icons.icon("minus", color, 16, 2.4))
        self.btn_plus.setIcon(icons.icon("plus", color, 16, 2.4))

    def _update_buttons(self) -> None:
        if self.isEnabled():
            self.btn_minus.setEnabled(self._value > self._min)
            self.btn_plus.setEnabled(self._value < self._max)
        else:
            self.btn_minus.setEnabled(False)
            self.btn_plus.setEnabled(False)

    def _increment(self) -> None:
        self.setValue(self._value + self._step)

    def _decrement(self) -> None:
        self.setValue(self._value - self._step)

    def wheelEvent(self, e: QWheelEvent) -> None:
        if not self.isEnabled():
            return
        d = 1 if e.angleDelta().y() > 0 else -1
        self.setValue(self._value + d * self._step)
        e.accept()


# =====================================================================
#  CurrencyField — entrada monetária com máscara BRL (estilo banco)
# =====================================================================
class CurrencyField(QLineEdit):
    """Campo de moeda: o usuário digita os dígitos e o valor é formatado em
    tempo real como R$ 0.000,00 (entrada baseada em centavos)."""

    valueChanged = Signal(float)

    def __init__(self, value: float = 0.0, parent=None):
        super().__init__(parent)
        self._cents = 0
        self.setMinimumHeight(44)
        self.setClearButtonEnabled(False)
        self.textEdited.connect(self._on_edit)
        self.set_value(value)

    def _on_edit(self, text: str) -> None:
        digits = "".join(ch for ch in text if ch.isdigit())
        self._cents = int(digits) if digits else 0
        self._render()
        self.valueChanged.emit(self.value())

    def _render(self) -> None:
        self.blockSignals(True)
        self.setText(format_brl(self._cents / 100.0))
        self.blockSignals(False)
        self.setCursorPosition(len(self.text()))

    def value(self) -> float:
        return self._cents / 100.0

    def set_value(self, v: float) -> None:
        self._cents = max(0, int(round(float(v) * 100)))
        self._render()


# =====================================================================
#  HourMinutePicker
# =====================================================================
class HourMinutePicker(QWidget):
    """Seletor de horário HH:MM via dois PlusMinusSpin."""

    timeChanged = Signal(int, int)

    def __init__(self, hour: int = 0, minute: int = 0, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.spin_h = PlusMinusSpin(
            minimum=0, maximum=23, value=hour, width_min=120,
        )
        self.spin_h.valueChanged.connect(self._emit)

        sep = QLabel(":")
        sep.setObjectName("HourMinuteSep")
        sep.setAlignment(Qt.AlignCenter)
        sep.setFixedWidth(10)

        self.spin_m = PlusMinusSpin(
            minimum=0, maximum=59, value=minute, width_min=120,
        )
        self.spin_m.valueChanged.connect(self._emit)

        layout.addWidget(self.spin_h, 1)
        layout.addWidget(sep, 0)
        layout.addWidget(self.spin_m, 1)

    def time(self) -> tuple[int, int]:
        return self.spin_h.value(), self.spin_m.value()

    def setTime(self, h: int, m: int) -> None:
        self.spin_h.setValue(h)
        self.spin_m.setValue(m)
        self._emit()

    def _emit(self) -> None:
        self.timeChanged.emit(*self.time())


# =====================================================================
#  AnimatedStackedWidget  — transição por snapshot (60fps, estilo iOS)
# =====================================================================
class _SlideOverlay(QWidget):
    """Desliza duas "fotos" (QPixmap) das páginas. Cada frame é só 2 blits —
    nenhum widget real é repintado durante a transição, garantindo fluidez."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._out = None
        self._in = None
        self._dir = 1
        self._p = 0.0

    def setup(self, out_pix, in_pix, direction: int) -> None:
        self._out = out_pix
        self._in = in_pix
        self._dir = direction
        self._p = 0.0
        self.update()

    def release(self) -> None:
        self._out = None
        self._in = None

    def _get_p(self) -> float:
        return self._p

    def _set_p(self, v: float) -> None:
        self._p = v
        self.update()

    progress = Property(float, _get_p, _set_p)

    def paintEvent(self, e):
        if self._out is None or self._in is None:
            return
        p = QPainter(self)
        w, h = self.width(), self.height()
        d = self._dir
        t = self._p
        shift = t * w

        # página que sai: parallax (45% da velocidade) + véu que escurece
        p.drawPixmap(int(round(-d * shift * 0.45)), 0, self._out)
        p.fillRect(self.rect(), QColor(15, 23, 42, int(34 * t)))

        # página que entra por cima, com sombra na aresta de ataque
        x_in = d * w - d * shift
        p.drawPixmap(int(round(x_in)), 0, self._in)

        edge_w = 26
        alpha = int(46 * (1.0 - t))
        if alpha > 2:
            if d > 0:
                grad = QLinearGradient(x_in - edge_w, 0, x_in, 0)
            else:
                edge_x = x_in + w
                grad = QLinearGradient(edge_x + edge_w, 0, edge_x, 0)
            grad.setColorAt(0.0, QColor(15, 23, 42, 0))
            grad.setColorAt(1.0, QColor(15, 23, 42, alpha))
            p.setPen(Qt.NoPen)
            p.setBrush(grad)
            if d > 0:
                p.drawRect(QRectF(x_in - edge_w, 0, edge_w, h))
            else:
                p.drawRect(QRectF(x_in + w, 0, edge_w, h))
        p.end()


class AnimatedStackedWidget(QWidget):
    """Troca de página com deslize lateral fluido.

    Cada página é renderizada para um QPixmap uma única vez no início da
    transição; em seguida apenas as imagens deslizam (via _SlideOverlay), o que
    elimina o custo de repintar árvores de widgets complexas a cada frame —
    resultando em movimento suave (60fps) mesmo com cards, sombras e gráfico.
    """

    DURATION = 340  # ms

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pages: list[QWidget] = []
        self._current: int = -1
        self._anim: QPropertyAnimation | None = None
        self._cleanup = None
        self._overlay = _SlideOverlay(self)
        self._overlay.hide()

    # ---- API compatível com QStackedWidget ----
    def addWidget(self, widget: QWidget) -> int:
        idx = len(self._pages)
        self._pages.append(widget)
        widget.setParent(self)
        widget.hide()
        return idx

    def count(self) -> int:
        return len(self._pages)

    def currentIndex(self) -> int:
        return self._current

    def currentWidget(self) -> QWidget | None:
        if 0 <= self._current < len(self._pages):
            return self._pages[self._current]
        return None

    def widget(self, index: int) -> QWidget | None:
        if 0 <= index < len(self._pages):
            return self._pages[index]
        return None

    # ---- ciclo de vida da animação ----
    def _finalize(self) -> None:
        cb, self._cleanup = self._cleanup, None
        self._anim = None
        if cb is not None:
            cb()

    def _snapshot(self, widget: QWidget, w: int, h: int):
        """Garante layout e renderiza a página para um QPixmap."""
        widget.setGeometry(0, 0, w, h)
        widget.ensurePolished()
        lay = widget.layout()
        if lay is not None:
            lay.activate()
        return widget.grab()

    def setCurrentIndex(self, index: int) -> None:
        if not (0 <= index < len(self._pages)) or index == self._current:
            return

        # Encerra transição em andamento (responsivo a cliques rápidos)
        if self._anim is not None:
            self._anim.stop()
            self._finalize()

        old_idx = self._current
        old_w = self.currentWidget()
        new_w = self._pages[index]
        self._current = index
        w, h = self.width(), self.height()

        # Primeira exibição (sem animação)
        if old_w is None or w == 0 or h == 0:
            for p in self._pages:
                p.setGeometry(self.rect())
                p.setVisible(p is new_w)
            return

        direction = 1 if index > old_idx else -1

        # 1) fotografa as duas páginas (uma única vez)
        out_pix = self._snapshot(old_w, w, h)
        in_pix = self._snapshot(new_w, w, h)

        # 2) mostra o overlay (bitmaps) por cima e então oculta as páginas reais
        self._overlay.setGeometry(0, 0, w, h)
        self._overlay.setup(out_pix, in_pix, direction)
        self._overlay.show()
        self._overlay.raise_()
        old_w.hide()
        new_w.hide()

        # 3) anima um único float -> frames baratíssimos (60fps)
        anim = QPropertyAnimation(self._overlay, b"progress", self)
        anim.setDuration(self.DURATION)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutQuint)

        def cleanup(nw=new_w):
            nw.setGeometry(0, 0, self.width(), self.height())
            nw.show()
            nw.raise_()
            self._overlay.hide()
            self._overlay.release()

        self._cleanup = cleanup
        anim.finished.connect(self._finalize)
        self._anim = anim
        anim.start()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._anim is None and 0 <= self._current < len(self._pages):
            self._pages[self._current].setGeometry(self.rect())


# =====================================================================
#  NavItem — item de navegação com morphing animado (ícone + rótulo)
# =====================================================================
def _mix(c1: QColor, c2: QColor, t: float) -> QColor:
    t = max(0.0, min(1.0, t))
    return QColor(
        int(c1.red() + (c2.red() - c1.red()) * t),
        int(c1.green() + (c2.green() - c1.green()) * t),
        int(c1.blue() + (c2.blue() - c1.blue()) * t),
    )


class NavItem(QWidget):
    """Item da navegação: crossfade de cor, leve elevação do ícone ao ativar
    e hover suave — tudo pintado à mão para transições contínuas."""

    clicked = Signal(int)

    def __init__(self, icon_name: str, label: str, index: int, parent=None):
        super().__init__(parent)
        self._index = index
        self._label = label
        self._t = 0.0        # progresso de ativação (0 → 1)
        self._h = 0.0        # progresso de hover
        self._t_anim: QPropertyAnimation | None = None
        self._h_anim: QPropertyAnimation | None = None
        self.setFixedSize(150, 56)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

        self._pm_idle = icons.pixmap(icon_name, theme.ON_DARK_MUTED, 22, 2.0)
        self._pm_active = icons.pixmap(icon_name, "#FFFFFF", 22, 2.1)

        self._col_idle = QColor(theme.ON_DARK_MUTED)
        self._col_hover = QColor("#CBD5E1")
        self._col_active = QColor("#FFFFFF")

    # ---- propriedades animáveis ----
    def _get_t(self) -> float:
        return self._t

    def _set_t(self, v: float) -> None:
        self._t = v
        self.update()

    activation = Property(float, _get_t, _set_t)

    def _get_h(self) -> float:
        return self._h

    def _set_h(self, v: float) -> None:
        self._h = v
        self.update()

    hoverProgress = Property(float, _get_h, _set_h)

    def _animate(self, prop: bytes, current: float, target: float, dur: int):
        anim = QPropertyAnimation(self, prop, self)
        anim.setDuration(dur)
        anim.setStartValue(current)
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        return anim

    def set_active(self, active: bool) -> None:
        target = 1.0 if active else 0.0
        if abs(self._t - target) < 0.001:
            return
        if self._t_anim is not None:
            self._t_anim.stop()
        self._t_anim = self._animate(b"activation", self._t, target, 260)

    def enterEvent(self, e):
        if self._h_anim is not None:
            self._h_anim.stop()
        self._h_anim = self._animate(b"hoverProgress", self._h, 1.0, theme.DUR_FAST)
        super().enterEvent(e)

    def leaveEvent(self, e):
        if self._h_anim is not None:
            self._h_anim.stop()
        self._h_anim = self._animate(b"hoverProgress", self._h, 0.0, theme.DUR_BASE)
        super().leaveEvent(e)

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self._index)
        super().mousePressEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        t, h = self._t, self._h

        # ícone: blend idle → ativo com leve subida
        icon_size = 22
        lift = 1.5 * t
        ix = (self.width() - icon_size) / 2
        iy = 8 - lift
        hover_boost = h * (1.0 - t)
        if t < 1.0:
            p.setOpacity(1.0 - t * 0.85)
            p.drawPixmap(int(ix), int(iy), self._pm_idle)
        alpha_active = max(t, hover_boost * 0.45)
        if alpha_active > 0.01:
            p.setOpacity(alpha_active)
            p.drawPixmap(int(ix), int(iy), self._pm_active)
        p.setOpacity(1.0)

        # rótulo: cor interpolada + peso conforme ativação
        base = _mix(self._col_idle, self._col_hover, hover_boost)
        col = _mix(base, self._col_active, t)
        font = QFont(theme.FONT_FAMILY)
        font.setPointSizeF(8.5)
        font.setWeight(QFont.DemiBold if t > 0.5 else QFont.Medium)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0.2)
        p.setFont(font)
        p.setPen(col)
        p.drawText(
            QRectF(0, 32 - lift * 0.4, self.width(), 18),
            Qt.AlignHCenter | Qt.AlignVCenter, self._label,
        )
        p.end()


class _NavPill(QWidget):
    """Cápsula translúcida + barra superior indigo, deslizada sob o item ativo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect())
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 20))
        p.drawRoundedRect(r, 14, 14)
        # barra indicadora superior (gradiente indigo)
        bw = r.width() * 0.42
        bar = QRectF(r.center().x() - bw / 2, r.top() + 2, bw, 3)
        grad = QLinearGradient(bar.left(), 0, bar.right(), 0)
        grad.setColorAt(0.0, QColor(theme.PRIMARY_GRAD_1))
        grad.setColorAt(1.0, QColor(theme.VIOLET))
        p.setBrush(grad)
        p.drawRoundedRect(bar, 1.5, 1.5)
        p.end()


# =====================================================================
#  BottomNavBar — navegação inferior com indicador deslizante
# =====================================================================
class BottomNavBar(QFrame):
    page_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BottomNav")
        self.setFixedHeight(74)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 0, 24, 0)
        lay.setSpacing(6)

        self._items: list[NavItem] = []
        self._active = 0

        self._pill = _NavPill(self)
        self._pill.lower()
        self._pill_anim: QPropertyAnimation | None = None

        lay.addStretch(1)
        for icon_name, label, idx in (
            ("calendar", "Controle Mensal", 0),
            ("bar-chart", "Resumo Anual", 1),
            ("calculator", "Calculadora", 2),
        ):
            item = NavItem(icon_name, label, idx)
            item.clicked.connect(self._on_click)
            self._items.append(item)
            lay.addWidget(item)
        lay.addStretch(1)

        ano = datetime.now().year
        sig = QLabel(
            f"Criado por <b style='color:#CBD5E1;'>"
            f"João Pedro Villas Boas de Carvalho</b><br>"
            f"<span style='color:{theme.ON_DARK_FAINT};'>© {ano} · v1.0</span>"
        )
        sig.setObjectName("BottomNavSignature")
        sig.setTextFormat(Qt.RichText)
        sig.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(sig)

    def _on_click(self, idx: int) -> None:
        if idx == self._active:
            return
        self.set_active(idx)
        self.page_selected.emit(idx)

    def set_active(self, idx: int) -> None:
        self._active = idx
        for i, item in enumerate(self._items):
            item.set_active(i == idx)
        self._move_pill(animate=True)

    def _pill_target(self) -> QRect:
        item = self._items[self._active]
        g = item.geometry()
        return QRect(g.x(), g.y() + 2, g.width(), g.height() - 4)

    def _move_pill(self, animate: bool) -> None:
        target = self._pill_target()
        if target.width() <= 0:
            return
        if not animate or not self._pill.isVisible():
            self._pill.setGeometry(target)
            self._pill.show()
            return
        anim = QPropertyAnimation(self._pill, b"geometry", self)
        anim.setDuration(380)
        anim.setStartValue(self._pill.geometry())
        anim.setEndValue(target)
        curve = QEasingCurve(QEasingCurve.OutBack)
        curve.setOvershoot(1.1)
        anim.setEasingCurve(curve)
        anim.start()
        self._pill_anim = anim

    def showEvent(self, e):
        super().showEvent(e)
        self._move_pill(animate=False)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        running = (self._pill_anim is not None and
                   self._pill_anim.state() == QPropertyAnimation.Running)
        if not running:
            self._pill.setGeometry(self._pill_target())


# =====================================================================
#  OuterContainer — pinta a sombra e oferece áreas de resize
# =====================================================================
class OuterContainer(QWidget):
    """Container externo da janela frameless: pinta sombra + redimensionamento por borda."""

    RESIZE_ZONE = 6  # px adicionais dentro do inner que ainda contam como borda

    def __init__(self, main_window: QWidget, parent=None):
        super().__init__(parent)
        self._main = main_window
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._margin = SHADOW_MARGIN
        self._maximized = False
        self._resizable = True

    def set_maximized(self, maximized: bool) -> None:
        self._maximized = maximized
        self._margin = 0 if maximized else SHADOW_MARGIN
        self.update()

    def set_resizable(self, resizable: bool) -> None:
        self._resizable = resizable

    # ---------- pintura da sombra ----------
    def paintEvent(self, e):
        if self._maximized or self._margin <= 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(Qt.NoPen)

        rect = self.rect()
        margin = self._margin
        inner_x = margin
        inner_y = margin
        inner_w = rect.width() - 2 * margin
        inner_h = rect.height() - 2 * margin
        if inner_w <= 0 or inner_h <= 0:
            return

        # Camadas concêntricas — alpha decresce conforme se afasta do inner
        for i in range(margin, 0, -1):
            t = i / margin
            # ease quadrático para sombra mais suave
            alpha = max(0, int(70 * (1 - t) ** 1.8))
            if alpha == 0:
                continue
            color = QColor(15, 23, 42, alpha)
            p.setBrush(color)
            r = QRectF(
                inner_x - i,
                inner_y - i + 2,  # leve offset para baixo
                inner_w + 2 * i,
                inner_h + 2 * i,
            )
            p.drawRoundedRect(r, 6 + i * 0.5, 6 + i * 0.5)
        p.end()

    # ---------- resize via borda ----------
    def _edges_at(self, pos) -> Qt.Edges:
        if self._maximized or not self._resizable:
            return Qt.Edges()
        m = self._margin + self.RESIZE_ZONE
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        edges = Qt.Edges()
        if x <= m:
            edges |= Qt.LeftEdge
        elif x >= w - m:
            edges |= Qt.RightEdge
        if y <= m:
            edges |= Qt.TopEdge
        elif y >= h - m:
            edges |= Qt.BottomEdge
        return edges

    def _cursor_for_edges(self, edges) -> Qt.CursorShape:
        if (edges & Qt.LeftEdge and edges & Qt.TopEdge) or \
           (edges & Qt.RightEdge and edges & Qt.BottomEdge):
            return Qt.SizeFDiagCursor
        if (edges & Qt.RightEdge and edges & Qt.TopEdge) or \
           (edges & Qt.LeftEdge and edges & Qt.BottomEdge):
            return Qt.SizeBDiagCursor
        if edges & (Qt.LeftEdge | Qt.RightEdge):
            return Qt.SizeHorCursor
        if edges & (Qt.TopEdge | Qt.BottomEdge):
            return Qt.SizeVerCursor
        return Qt.ArrowCursor

    def mouseMoveEvent(self, e: QMouseEvent):
        edges = self._edges_at(e.position().toPoint())
        self.setCursor(self._cursor_for_edges(edges))
        super().mouseMoveEvent(e)

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton and not self._maximized:
            edges = self._edges_at(e.position().toPoint())
            if edges:
                handle = self._main.windowHandle()
                if handle is not None:
                    handle.startSystemResize(edges)
                    e.accept()
                    return
        super().mousePressEvent(e)

    def leaveEvent(self, e):
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(e)


# =====================================================================
#  BaseDialog — diálogo frameless com header próprio
# =====================================================================
class BaseDialog(QDialog):
    """Diálogo modal sem moldura nativa, com header arrastável e sombra."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        # Layout raiz sem margem — _DialogShadow já tem margem interna
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._shadow = _DialogShadow()
        lay.addWidget(self._shadow)

    # ------------- construído pelo subclasse --------------
    def _setup(self, title: str) -> QFrame:
        """Cria o esqueleto: header + content frame. Retorna o content_frame."""
        inner = QFrame()
        inner.setObjectName("InnerContainer")
        inner.setMouseTracking(True)
        self._shadow.set_inner(inner)

        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(0, 0, 0, 0)
        inner_lay.setSpacing(0)

        header = _DialogHeader(self, title)
        inner_lay.addWidget(header)
        self._header = header

        content = QFrame()
        content.setObjectName("DialogContent")
        inner_lay.addWidget(content, 1)
        return content

    def set_title(self, title: str) -> None:
        if hasattr(self, "_header"):
            self._header.set_title(title)

    def showEvent(self, e):
        super().showEvent(e)
        if not getattr(self, "_did_pop", False):
            self._did_pop = True
            window_pop_in(self, duration=240, rise=12)


class _DialogShadow(QWidget):
    """Container que pinta a sombra ao redor do inner do diálogo."""

    SHADOW_MARGIN = 12

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._inner: QWidget | None = None
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(
            self.SHADOW_MARGIN, self.SHADOW_MARGIN,
            self.SHADOW_MARGIN, self.SHADOW_MARGIN,
        )
        self._lay.setSpacing(0)

    def set_inner(self, inner: QWidget) -> None:
        self._inner = inner
        self._lay.addWidget(inner)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(Qt.NoPen)

        rect = self.rect()
        margin = self.SHADOW_MARGIN
        inner_x = margin
        inner_y = margin
        inner_w = rect.width() - 2 * margin
        inner_h = rect.height() - 2 * margin
        if inner_w <= 0 or inner_h <= 0:
            return

        for i in range(margin, 0, -1):
            t = i / margin
            alpha = max(0, int(60 * (1 - t) ** 1.8))
            if alpha == 0:
                continue
            color = QColor(15, 23, 42, alpha)
            p.setBrush(color)
            r = QRectF(
                inner_x - i,
                inner_y - i + 2,
                inner_w + 2 * i,
                inner_h + 2 * i,
            )
            p.drawRoundedRect(r, 6 + i * 0.5, 6 + i * 0.5)
        p.end()


class _DialogHeader(QFrame):
    """Header do diálogo (arrastável + botão fechar)."""

    def __init__(self, dialog: QDialog, title: str):
        super().__init__()
        self._dialog = dialog
        self.setObjectName("DialogHeader")
        self.setFixedHeight(40)
        self.setMouseTracking(True)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 4, 0)
        lay.setSpacing(8)

        self._title = QLabel(title)
        self._title.setObjectName("DialogHeaderTitle")
        lay.addWidget(self._title, 1)

        self.btn_close = WindowControlButton("close", on_dark=False)
        self.btn_close.clicked.connect(dialog.reject)
        lay.addWidget(self.btn_close)

    def set_title(self, title: str) -> None:
        self._title.setText(title)

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            handle = self._dialog.windowHandle()
            if handle is not None:
                handle.startSystemMove()
                e.accept()
                return
        super().mousePressEvent(e)


# =====================================================================
#  ConfirmDialog — substitui QMessageBox.question
# =====================================================================
class ConfirmDialog(BaseDialog):
    """Diálogo de confirmação Sim/Não frameless."""

    def __init__(
        self,
        title: str,
        message: str,
        *,
        confirm_text: str = "Confirmar",
        cancel_text: str = "Cancelar",
        danger: bool = False,
        icon_name: str | None = None,
        parent=None,
    ):
        super().__init__(title=title, parent=parent)
        content = self._setup(title)
        self.setMinimumWidth(456)

        lay = QVBoxLayout(content)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(16)

        # linha ícone + mensagem
        msg_row = QHBoxLayout()
        msg_row.setSpacing(14)
        if icon_name is None:
            icon_name = "alert-triangle" if danger else "info"
        tone = theme.TONES["primary"] if not danger else {
            "fg": theme.DANGER_DARK, "bg": theme.DANGER_SOFT,
        }
        chip = QLabel()
        chip.setObjectName("DialogIconChip")
        chip.setProperty("danger", danger)
        chip.setFixedSize(44, 44)
        chip.setAlignment(Qt.AlignCenter)
        chip.setPixmap(icons.pixmap(icon_name, tone["fg"], 24, 2.1))
        msg_row.addWidget(chip, 0, Qt.AlignTop)

        lbl = QLabel(message)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            "color:#334155;font-size:10pt;background:transparent;line-height:1.5em;"
        )
        msg_row.addWidget(lbl, 1)
        lay.addLayout(msg_row)
        lay.addSpacing(2)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        self.btn_cancel = AnimatedButton(cancel_text)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setMinimumHeight(38)
        self.btn_cancel.setMinimumWidth(110)
        self.btn_cancel.clicked.connect(self.reject)
        if not cancel_text:
            self.btn_cancel.setVisible(False)

        self.btn_confirm = AnimatedButton(confirm_text, ripple_light=True)
        self.btn_confirm.setCursor(Qt.PointingHandCursor)
        self.btn_confirm.setMinimumHeight(38)
        self.btn_confirm.setMinimumWidth(130)
        self.btn_confirm.setDefault(True)
        self.btn_confirm.setObjectName(
            "DangerButton" if danger else "PrimaryButton"
        )
        self.btn_confirm.clicked.connect(self.accept)

        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_confirm)
        lay.addLayout(btn_row)
