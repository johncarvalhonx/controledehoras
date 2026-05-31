"""Barra de título customizada — substitui a moldura nativa do Windows."""
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

from .. import icons
from .. import theme
from .custom_widgets import AnimatedButton
from .window_controls import WindowControlButton


class TitleBar(QFrame):
    """Barra de título arrastável com botões de janela."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(44)
        self.setMouseTracking(True)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 0, 0)
        layout.setSpacing(11)

        icon = QLabel()
        icon.setFixedSize(22, 22)
        icon.setAlignment(Qt.AlignCenter)
        icon.setPixmap(icons.pixmap("clock", theme.PRIMARY_TINT, 19, 2.1))
        layout.addWidget(icon, 0)

        self.title_label = QLabel("Controle de Horas Extras")
        self.title_label.setObjectName("TitleBarTitle")
        layout.addWidget(self.title_label, 0)

        layout.addStretch(1)

        # Botão de configurações (engrenagem)
        self.btn_settings = AnimatedButton(radius=8, ripple_light=True)
        self.btn_settings.setObjectName("TitleBarTool")
        self.btn_settings.setIcon(icons.icon("settings", "#CBD5E1", 18, 2.0))
        self.btn_settings.setIconSize(QSize(18, 18))
        self.btn_settings.setFixedSize(40, 34)
        self.btn_settings.setCursor(Qt.PointingHandCursor)
        self.btn_settings.setToolTip("Configurações")
        layout.addWidget(self.btn_settings, 0, Qt.AlignVCenter)
        layout.addSpacing(8)

        self.btn_min = WindowControlButton("min", on_dark=True)
        self.btn_max = WindowControlButton("max", on_dark=True)
        self.btn_close = WindowControlButton("close", on_dark=True)
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

    # ----- drag / double-click -----
    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            window = self.window()
            handle = window.windowHandle() if window is not None else None
            if handle is not None:
                handle.startSystemMove()
                e.accept()
                return
        super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            window = self.window()
            if hasattr(window, "toggle_maximized"):
                window.toggle_maximized()
            e.accept()
            return
        super().mouseDoubleClickEvent(e)
