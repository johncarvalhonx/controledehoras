"""Date picker customizado — campo + calendário popup com animações fluidas.

Substitui o QDateEdit nativo: o campo pinta a data formatada em pt-BR e abre
um calendário próprio (popup frameless com sombra) com:
  - pílula de seleção que desliza entre os dias;
  - hover suave animado por célula;
  - transição de mês com deslize lateral (estilo iOS);
  - anel destacando o dia de hoje e atalho "Hoje".
"""
from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import (
    QEasingCurve, QPoint, QPointF, QRectF, Qt, QTimer, QVariantAnimation,
    Signal,
)
from PySide6.QtGui import (
    QColor, QFont, QKeyEvent, QLinearGradient, QMouseEvent, QPainter,
    QPen, QPixmap, QWheelEvent,
)
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QVBoxLayout, QWidget,
)

from .. import icons
from .. import theme
from ..anim import window_pop_in
from ..config import MESES_PT
from .custom_widgets import AnimatedButton
from .widgets import attach_shadow

_DIAS_SEMANA = ["D", "S", "T", "Q", "Q", "S", "S"]  # domingo → sábado
_DIAS_LONGO = [
    "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
    "sexta-feira", "sábado", "domingo",
]

CELL_W, CELL_H = 40, 36
GRID_COLS, GRID_ROWS = 7, 6


def _mix(c1: QColor, c2: QColor, t: float) -> QColor:
    t = max(0.0, min(1.0, t))
    return QColor(
        int(c1.red() + (c2.red() - c1.red()) * t),
        int(c1.green() + (c2.green() - c1.green()) * t),
        int(c1.blue() + (c2.blue() - c1.blue()) * t),
    )


# =====================================================================
#  _NavButton — chevron com círculo de hover animado
# =====================================================================
class _NavButton(QWidget):
    clicked = Signal()

    def __init__(self, icon_name: str, parent=None):
        super().__init__(parent)
        self._pm = icons.pixmap(icon_name, theme.TEXT_MUTED, 17, 2.2)
        self._pm_hover = icons.pixmap(icon_name, theme.PRIMARY, 17, 2.4)
        self._t = 0.0
        self._anim: QVariantAnimation | None = None
        self.setFixedSize(32, 32)
        self.setCursor(Qt.PointingHandCursor)

    def _animate(self, target: float) -> None:
        if self._anim is not None:
            self._anim.stop()
        anim = QVariantAnimation(self)
        anim.setStartValue(self._t)
        anim.setEndValue(target)
        anim.setDuration(theme.DUR_FAST)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def _tick(v):
            self._t = float(v)
            self.update()

        anim.valueChanged.connect(_tick)
        anim.start()
        self._anim = anim

    def enterEvent(self, e):
        self._animate(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._animate(0.0)
        super().leaveEvent(e)

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        if self._t > 0.01:
            bg = QColor(theme.PRIMARY_SOFT)
            bg.setAlphaF(self._t)
            p.setPen(Qt.NoPen)
            p.setBrush(bg)
            p.drawEllipse(self.rect().adjusted(1, 1, -1, -1))
        pm = self._pm_hover if self._t > 0.5 else self._pm
        x = (self.width() - 17) / 2
        y = (self.height() - 17) / 2
        p.drawPixmap(int(x), int(y), pm)
        p.end()


# =====================================================================
#  _DayGrid — grade 6x7 pintada à mão com animações
# =====================================================================
class _DayGrid(QWidget):
    daySelected = Signal(object)      # date
    monthNavigated = Signal(int)      # +1 / -1 (clique em dia de outro mês)

    def __init__(self, selected: date, parent=None):
        super().__init__(parent)
        self._selected = selected
        self._view_year = selected.year
        self._view_month = selected.month
        self._days: list[date] = []
        self._hover_idx = -1
        self._hover_t = 0.0
        self._hover_anim: QVariantAnimation | None = None
        self._sel_pos: QPointF | None = None
        self._sel_anim: QVariantAnimation | None = None
        # transição de mês (deslize)
        self._trans_pix: QPixmap | None = None
        self._trans_dir = 1
        self._trans_t = 1.0
        self._trans_anim: QVariantAnimation | None = None

        self.setFixedSize(CELL_W * GRID_COLS, CELL_H * GRID_ROWS)
        self.setMouseTracking(True)
        self._rebuild_days()

    # ------------------------------------------------------------
    def view(self) -> tuple[int, int]:
        return self._view_year, self._view_month

    def selected(self) -> date:
        return self._selected

    def set_selected(self, d: date, animate: bool = True) -> None:
        old = self._selected
        self._selected = d
        if (d.year, d.month) != (self._view_year, self._view_month):
            direction = 1 if d > old else -1
            self.set_view(d.year, d.month, direction=direction)
            return
        self._animate_selection(animate)
        self.update()

    def set_view(self, year: int, month: int, direction: int = 0) -> None:
        if (year, month) == (self._view_year, self._view_month):
            return
        if direction == 0:
            direction = 1 if (year, month) > (self._view_year, self._view_month) else -1
        # fotografa a grade atual para o deslize
        if self.isVisible():
            self._trans_pix = self.grab()
            self._trans_dir = direction
            self._start_transition()
        self._view_year, self._view_month = year, month
        self._rebuild_days()
        self._sync_selection_pos(animate=False)
        self.update()

    # ------------------------------------------------------------
    def _rebuild_days(self) -> None:
        primeiro = date(self._view_year, self._view_month, 1)
        # domingo como primeiro dia da semana
        offset = (primeiro.weekday() + 1) % 7
        inicio = primeiro - timedelta(days=offset)
        self._days = [inicio + timedelta(days=i) for i in range(42)]

    def _idx_of(self, d: date) -> int:
        try:
            return self._days.index(d)
        except ValueError:
            return -1

    def _cell_center(self, idx: int) -> QPointF:
        row, col = divmod(idx, GRID_COLS)
        return QPointF(col * CELL_W + CELL_W / 2, row * CELL_H + CELL_H / 2)

    def _sync_selection_pos(self, animate: bool) -> None:
        idx = self._idx_of(self._selected)
        if idx < 0:
            self._sel_pos = None
            return
        target = self._cell_center(idx)
        if not animate or self._sel_pos is None or not self.isVisible():
            self._sel_pos = target
            return
        self._animate_selection(True)

    def _animate_selection(self, animate: bool) -> None:
        idx = self._idx_of(self._selected)
        if idx < 0:
            self._sel_pos = None
            return
        target = self._cell_center(idx)
        if not animate or self._sel_pos is None or not self.isVisible():
            self._sel_pos = target
            self.update()
            return
        if self._sel_anim is not None:
            self._sel_anim.stop()
        anim = QVariantAnimation(self)
        anim.setStartValue(self._sel_pos)
        anim.setEndValue(target)
        anim.setDuration(220)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def _tick(v):
            self._sel_pos = v
            self.update()

        anim.valueChanged.connect(_tick)
        anim.start()
        self._sel_anim = anim

    def _start_transition(self) -> None:
        if self._trans_anim is not None:
            self._trans_anim.stop()
        self._trans_t = 0.0
        anim = QVariantAnimation(self)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(280)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def _tick(v):
            self._trans_t = float(v)
            self.update()

        def _done():
            self._trans_pix = None
            self.update()

        anim.valueChanged.connect(_tick)
        anim.finished.connect(_done)
        anim.start()
        self._trans_anim = anim

    # ------------------------------------------------------------
    def _animate_hover(self, target: float) -> None:
        if self._hover_anim is not None:
            self._hover_anim.stop()
        anim = QVariantAnimation(self)
        anim.setStartValue(self._hover_t)
        anim.setEndValue(target)
        anim.setDuration(120)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def _tick(v):
            self._hover_t = float(v)
            self.update()

        anim.valueChanged.connect(_tick)
        anim.start()
        self._hover_anim = anim

    def mouseMoveEvent(self, e: QMouseEvent):
        col = int(e.position().x() // CELL_W)
        row = int(e.position().y() // CELL_H)
        idx = row * GRID_COLS + col
        if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS and idx < len(self._days):
            if idx != self._hover_idx:
                self._hover_idx = idx
                self._hover_t = 0.0
                self._animate_hover(1.0)
        else:
            self._hover_idx = -1
            self.update()
        super().mouseMoveEvent(e)

    def leaveEvent(self, e):
        self._hover_idx = -1
        self.update()
        super().leaveEvent(e)

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton and self._hover_idx >= 0:
            d = self._days[self._hover_idx]
            if (d.year, d.month) != (self._view_year, self._view_month):
                self.monthNavigated.emit(1 if d > self._selected else -1)
            self._selected = d
            self._animate_selection(True)
            self.daySelected.emit(d)
        super().mousePressEvent(e)

    # ------------------------------------------------------------
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w = self.width()

        # transição de mês: pixmap antigo desliza para fora, grade nova entra
        if self._trans_pix is not None and self._trans_t < 1.0:
            d = self._trans_dir
            shift = self._trans_t * w
            p.setOpacity(1.0 - self._trans_t)
            p.drawPixmap(int(-d * shift), 0, self._trans_pix)
            p.setOpacity(self._trans_t)
            p.translate(d * w - d * shift, 0)
            self._paint_grid(p)
            p.end()
            return

        self._paint_grid(p)
        p.end()

    def _paint_grid(self, p: QPainter) -> None:
        hoje = date.today()
        font = QFont(theme.FONT_FAMILY)
        font.setPointSize(9)

        # pílula de seleção (desliza entre células)
        sel_idx = self._idx_of(self._selected)
        if sel_idx >= 0 and self._sel_pos is None:
            self._sel_pos = self._cell_center(sel_idx)
        if sel_idx >= 0 and self._sel_pos is not None:
            r = 15.0
            rect = QRectF(
                self._sel_pos.x() - r, self._sel_pos.y() - r, 2 * r, 2 * r
            )
            grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            grad.setColorAt(0.0, QColor(theme.PRIMARY_GRAD_1))
            grad.setColorAt(1.0, QColor(theme.PRIMARY_GRAD_3))
            p.setPen(Qt.NoPen)
            p.setBrush(grad)
            p.drawEllipse(rect)

        for idx, d in enumerate(self._days):
            center = self._cell_center(idx)
            in_month = (d.year, d.month) == (self._view_year, self._view_month)
            is_sel = d == self._selected
            is_today = d == hoje

            # hover suave
            if (idx == self._hover_idx and not is_sel and self._hover_t > 0.01):
                bg = QColor(theme.PRIMARY_SOFT)
                bg.setAlphaF(self._hover_t)
                p.setPen(Qt.NoPen)
                p.setBrush(bg)
                p.drawEllipse(center, 15.0, 15.0)

            # anel do dia de hoje
            if is_today and not is_sel:
                p.setBrush(Qt.NoBrush)
                ring_pen = QPen(QColor(theme.PRIMARY))
                ring_pen.setWidthF(1.6)
                p.setPen(ring_pen)
                p.drawEllipse(center, 14.0, 14.0)

            # número do dia
            if is_sel:
                color = QColor("#FFFFFF")
                font.setWeight(QFont.Bold)
            elif is_today:
                color = QColor(theme.PRIMARY)
                font.setWeight(QFont.DemiBold)
            elif in_month:
                color = QColor(theme.TEXT)
                font.setWeight(QFont.Medium)
            else:
                color = QColor(theme.TEXT_FAINT)
                font.setWeight(QFont.Normal)
            p.setFont(font)
            p.setPen(color)
            rect = QRectF(center.x() - CELL_W / 2, center.y() - CELL_H / 2,
                          CELL_W, CELL_H)
            p.drawText(rect, Qt.AlignCenter, str(d.day))


# =====================================================================
#  CalendarPopup — popup frameless com header, grade e rodapé
# =====================================================================
class CalendarPopup(QWidget):
    dateSelected = Signal(object)  # date

    SHADOW = 16

    def __init__(self, selected: date, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        root = QVBoxLayout(self)
        root.setContentsMargins(self.SHADOW, self.SHADOW, self.SHADOW, self.SHADOW)
        root.setSpacing(0)

        panel = QWidget()
        panel.setObjectName("CalendarPanel")
        attach_shadow(panel, blur=30, dy=10, alpha=55)
        root.addWidget(panel)

        lay = QVBoxLayout(panel)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)

        # ---- header: mês/ano + navegação
        head = QHBoxLayout()
        head.setSpacing(4)
        self._lbl = QLabel("")
        self._lbl.setStyleSheet(
            f"color:{theme.TEXT_STRONG}; background:transparent; "
            "font-size:10.5pt; font-weight:700;"
        )
        self.btn_prev = _NavButton("chevron-left")
        self.btn_next = _NavButton("chevron-right")
        self.btn_prev.clicked.connect(lambda: self._navigate(-1))
        self.btn_next.clicked.connect(lambda: self._navigate(1))
        head.addWidget(self._lbl, 1)
        head.addWidget(self.btn_prev, 0)
        head.addWidget(self.btn_next, 0)
        lay.addLayout(head)

        # ---- dias da semana
        week = QHBoxLayout()
        week.setContentsMargins(0, 2, 0, 0)
        week.setSpacing(0)
        for d in _DIAS_SEMANA:
            l = QLabel(d)
            l.setAlignment(Qt.AlignCenter)
            l.setFixedSize(CELL_W, 18)
            l.setStyleSheet(
                f"color:{theme.TEXT_SUBTLE}; background:transparent; "
                "font-size:7.5pt; font-weight:700; letter-spacing:0.5px;"
            )
            week.addWidget(l)
        week.addStretch(1)
        lay.addLayout(week)

        # ---- grade de dias
        self.grid = _DayGrid(selected)
        self.grid.daySelected.connect(self._on_day)
        self.grid.monthNavigated.connect(self._on_month_nav)
        lay.addWidget(self.grid, 0, Qt.AlignHCenter)

        # ---- rodapé
        foot = QHBoxLayout()
        foot.setContentsMargins(0, 4, 0, 0)
        self.btn_hoje = AnimatedButton("Hoje")
        self.btn_hoje.setObjectName("GhostButton")
        self.btn_hoje.setCursor(Qt.PointingHandCursor)
        self.btn_hoje.setFixedHeight(30)
        self.btn_hoje.setMinimumWidth(72)
        self.btn_hoje.setStyleSheet("padding: 4px 12px; font-size: 8.5pt;")
        self.btn_hoje.clicked.connect(self._ir_hoje)
        foot.addStretch(1)
        foot.addWidget(self.btn_hoje)
        lay.addLayout(foot)

        self._update_header()

    # ------------------------------------------------------------
    def _update_header(self) -> None:
        y, m = self.grid.view()
        self._lbl.setText(f"{MESES_PT[m - 1]} {y}")

    def _navigate(self, delta: int) -> None:
        y, m = self.grid.view()
        m += delta
        if m < 1:
            m, y = 12, y - 1
        elif m > 12:
            m, y = 1, y + 1
        self.grid.set_view(y, m, direction=delta)
        self._update_header()

    def _on_month_nav(self, delta: int) -> None:
        self._update_header()

    def _on_day(self, d: date) -> None:
        self._update_header()
        self.dateSelected.emit(d)
        # pequena pausa para o usuário ver a pílula deslizar até o dia
        QTimer.singleShot(160, self.close)

    def _ir_hoje(self) -> None:
        hoje = date.today()
        self.grid.set_selected(hoje)
        self._update_header()
        self.dateSelected.emit(hoje)
        QTimer.singleShot(200, self.close)

    # ------------------------------------------------------------
    def keyPressEvent(self, e: QKeyEvent):
        d = self.grid.selected()
        delta = {
            Qt.Key_Left: -1, Qt.Key_Right: 1,
            Qt.Key_Up: -7, Qt.Key_Down: 7,
        }.get(e.key())
        if delta is not None:
            novo = d + timedelta(days=delta)
            self.grid.set_selected(novo)
            self._update_header()
            e.accept()
            return
        if e.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.dateSelected.emit(self.grid.selected())
            self.close()
            e.accept()
            return
        super().keyPressEvent(e)

    def wheelEvent(self, e: QWheelEvent):
        self._navigate(-1 if e.angleDelta().y() > 0 else 1)
        e.accept()

    def paintEvent(self, e):
        # painel branco arredondado com borda (pintado sob os children)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        m = self.SHADOW
        r = QRectF(self.rect()).adjusted(m, m, -m, -m)
        p.setPen(QColor(theme.BORDER))
        p.setBrush(QColor(theme.SURFACE))
        p.drawRoundedRect(r, 14, 14)
        p.end()


# =====================================================================
#  DatePickerField — campo de data que abre o CalendarPopup
# =====================================================================
class DatePickerField(QWidget):
    """Campo de data com visual de input: ícone, data por extenso e chevron
    que gira ao abrir o calendário."""

    dateChanged = Signal(object)  # date

    def __init__(self, value: date | None = None, parent=None):
        super().__init__(parent)
        self._date = value or date.today()
        self._open = False
        self._hover_t = 0.0
        self._chevron_t = 0.0  # 0 = fechado, 1 = aberto (gira 180°)
        self._hover_anim: QVariantAnimation | None = None
        self._chev_anim: QVariantAnimation | None = None
        self.setFixedHeight(46)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)

    # ---- API ----
    def date(self) -> date:
        return self._date

    def setDate(self, d: date) -> None:
        if d != self._date:
            self._date = d
            self.update()
            self.dateChanged.emit(d)

    # ---- animações ----
    def _animate(self, attr: str, target: float, dur: int = 150):
        current = getattr(self, attr)
        anim = QVariantAnimation(self)
        anim.setStartValue(current)
        anim.setEndValue(target)
        anim.setDuration(dur)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def _tick(v, a=attr):
            setattr(self, a, float(v))
            self.update()

        anim.valueChanged.connect(_tick)
        anim.start()
        return anim

    def enterEvent(self, e):
        if self._hover_anim is not None:
            self._hover_anim.stop()
        self._hover_anim = self._animate("_hover_t", 1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        if self._hover_anim is not None:
            self._hover_anim.stop()
        self._hover_anim = self._animate("_hover_t", 0.0, 220)
        super().leaveEvent(e)

    # ---- popup ----
    def _open_popup(self) -> None:
        if self._open:
            return
        self._open = True
        if self._chev_anim is not None:
            self._chev_anim.stop()
        self._chev_anim = self._animate("_chevron_t", 1.0, 220)

        popup = CalendarPopup(self._date)
        popup.dateSelected.connect(self._on_selected)
        popup.destroyed.connect(self._on_popup_closed)

        # posiciona logo abaixo do campo (ou acima se faltar espaço)
        popup.adjustSize()
        gpos = self.mapToGlobal(QPoint(0, self.height() + 2))
        screen = QApplication.screenAt(gpos) or QApplication.primaryScreen()
        if screen is not None:
            avail = screen.availableGeometry()
            if gpos.y() + popup.height() > avail.bottom():
                gpos = self.mapToGlobal(QPoint(0, -popup.height() - 2))
            if gpos.x() + popup.width() > avail.right():
                gpos.setX(avail.right() - popup.width())
        popup.move(gpos - QPoint(CalendarPopup.SHADOW, CalendarPopup.SHADOW))
        popup.setAttribute(Qt.WA_DeleteOnClose, True)
        popup.show()
        window_pop_in(popup, duration=200, rise=10)

    def _on_popup_closed(self, *_):
        self._open = False
        if self._chev_anim is not None:
            self._chev_anim.stop()
        self._chev_anim = self._animate("_chevron_t", 0.0, 220)

    def _on_selected(self, d: date) -> None:
        self.setDate(d)

    # ---- interação ----
    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._open_popup()
            e.accept()
            return
        super().mousePressEvent(e)

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self._open_popup()
            e.accept()
            return
        if e.key() == Qt.Key_Left:
            self.setDate(self._date - timedelta(days=1))
            e.accept()
            return
        if e.key() == Qt.Key_Right:
            self.setDate(self._date + timedelta(days=1))
            e.accept()
            return
        super().keyPressEvent(e)

    def wheelEvent(self, e: QWheelEvent):
        delta = -1 if e.angleDelta().y() > 0 else 1
        self.setDate(self._date + timedelta(days=delta))
        e.accept()

    # ---- pintura ----
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        focused = self.hasFocus() or self._open
        if focused:
            border = QColor(theme.PRIMARY)
            bw = 2.0
        else:
            border = _mix(
                QColor(theme.BORDER_STRONG), QColor(theme.TEXT_SUBTLE),
                self._hover_t,
            )
            bw = 1.0

        pen = QPen(border)
        pen.setWidthF(bw)
        p.setPen(pen)
        p.setBrush(QColor("#FCFDFF" if focused else theme.SURFACE))
        p.drawRoundedRect(r, 12, 12)

        # ícone calendário
        icon_color = theme.PRIMARY if focused else theme.TEXT_MUTED
        pm = icons.pixmap("calendar", icon_color, 18, 2.0)
        p.drawPixmap(14, int((self.height() - 18) / 2), pm)

        # texto: data + dia da semana
        data_txt = self._date.strftime("%d/%m/%Y")
        dia_txt = _DIAS_LONGO[self._date.weekday()]

        f1 = QFont(theme.FONT_FAMILY)
        f1.setPointSize(10)
        f1.setWeight(QFont.DemiBold)
        p.setFont(f1)
        p.setPen(QColor(theme.TEXT))
        fm1 = p.fontMetrics()
        x = 42
        y = int((self.height() + fm1.ascent() - fm1.descent()) / 2)
        p.drawText(x, y, data_txt)
        x += fm1.horizontalAdvance(data_txt) + 10

        f2 = QFont(theme.FONT_FAMILY)
        f2.setPointSize(9)
        p.setFont(f2)
        p.setPen(QColor(theme.TEXT_MUTED))
        p.drawText(x, y, f"· {dia_txt}")

        # chevron com rotação animada
        chev = icons.rotated_pixmap(
            "chevron-down", theme.PRIMARY if focused else theme.TEXT_MUTED,
            16, 180.0 * self._chevron_t, 2.0,
        )
        p.drawPixmap(
            self.width() - 16 - 14, int((self.height() - 16) / 2), chev
        )
        p.end()
