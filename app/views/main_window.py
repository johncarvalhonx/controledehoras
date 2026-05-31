"""Janela principal — frameless, redimensionável, com navegação inferior animada."""
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import (
    QApplication, QFrame, QMainWindow, QVBoxLayout, QWidget,
)

from ..anim import window_pop_in
from ..database import Database
from .annual_view import AnnualView
from .calculator_view import CalculatorView
from .custom_widgets import (
    AnimatedStackedWidget, BottomNavBar, OuterContainer, SHADOW_MARGIN,
)
from .monthly_view import MonthlyView
from .settings_dialog import SettingsDialog
from .title_bar import TitleBar
from .toast import ToastManager

TARGET_W, TARGET_H = 1320, 860
MIN_W, MIN_H = 1040, 700


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Controle de Horas Extras")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setMinimumSize(MIN_W, MIN_H)

        self.db = Database()
        self._entrance_done = False

        # ----- Outer (sombra + resize por borda) -----------------------
        self.outer = OuterContainer(self)
        outer_lay = QVBoxLayout(self.outer)
        outer_lay.setContentsMargins(
            SHADOW_MARGIN, SHADOW_MARGIN, SHADOW_MARGIN, SHADOW_MARGIN
        )
        outer_lay.setSpacing(0)
        self._outer_lay = outer_lay

        # ----- Inner (a "janela" visível) ------------------------------
        self.inner = QFrame()
        self.inner.setObjectName("InnerContainer")
        self.inner.setMouseTracking(True)
        inner_lay = QVBoxLayout(self.inner)
        inner_lay.setContentsMargins(0, 0, 0, 0)
        inner_lay.setSpacing(0)

        self.title_bar = TitleBar(self)
        self.title_bar.btn_min.clicked.connect(self.showMinimized)
        self.title_bar.btn_max.clicked.connect(self.toggle_maximized)
        self.title_bar.btn_close.clicked.connect(self.close)
        self.title_bar.btn_settings.clicked.connect(self._abrir_config)
        inner_lay.addWidget(self.title_bar)

        # toasts ancorados ao inner
        self.toasts = ToastManager(self.inner)

        body = QWidget()
        body.setObjectName("Body")
        body.setMouseTracking(True)
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        self.stack = AnimatedStackedWidget()
        self.stack.setObjectName("ContentStack")
        self.stack.setMouseTracking(True)
        self.page_mensal = MonthlyView(self.db)
        self.page_anual = AnnualView(self.db)
        self.page_calc = CalculatorView(self.db)
        for p in (self.page_mensal, self.page_anual, self.page_calc):
            p.setMouseTracking(True)
            self.stack.addWidget(p)
        body_lay.addWidget(self.stack, 1)

        self.nav_bar = BottomNavBar()
        self.nav_bar.page_selected.connect(self._on_nav_selected)
        body_lay.addWidget(self.nav_bar, 0)

        inner_lay.addWidget(body, 1)
        outer_lay.addWidget(self.inner)
        self.setCentralWidget(self.outer)

        # Notificações de feedback + acesso às configurações
        self.page_mensal.notifier = self.toasts.show
        self.page_mensal.open_settings = self._abrir_config

        # Sinais entre views
        self.page_mensal.data_changed.connect(self.page_anual.refresh)
        self.page_calc.usar_como_registro.connect(self._usar_da_calculadora)

        self._aplicar_tamanho_inicial()
        self._selecionar_pagina(0)

    # =====================================================================
    def _aplicar_tamanho_inicial(self) -> None:
        screen = self.screen() or QApplication.primaryScreen()
        if screen is not None:
            avail = screen.availableGeometry()
            w = min(TARGET_W, avail.width() - 40)
            h = min(TARGET_H, avail.height() - 40)
            self.resize(w, h)
            self.move(
                avail.x() + (avail.width() - w) // 2,
                avail.y() + (avail.height() - h) // 2,
            )
        else:
            self.resize(TARGET_W, TARGET_H)

    # =====================================================================
    def _on_nav_selected(self, idx: int) -> None:
        if idx == 0:
            self.page_mensal.refresh()
        elif idx == 1:
            self.page_anual.refresh()
        self.stack.setCurrentIndex(idx)

    def _selecionar_pagina(self, idx: int) -> None:
        self.nav_bar.set_active(idx)
        self._on_nav_selected(idx)

    def _usar_da_calculadora(self, minutos: int) -> None:
        self._selecionar_pagina(0)
        self.page_mensal.adicionar_a_partir_de_calculadora(minutos)

    def _abrir_config(self) -> None:
        dlg = SettingsDialog(self.db, parent=self)
        if dlg.exec() == SettingsDialog.Accepted:
            self.page_mensal.refresh()
            self.page_anual.refresh()
            self.page_calc.atualizar_valores()
            self.toasts.show("Configurações salvas com sucesso.", "success")

    # =====================================================================
    def toggle_maximized(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def changeEvent(self, e):
        if e.type() == QEvent.WindowStateChange:
            maximized = self.isMaximized()
            if maximized:
                self._outer_lay.setContentsMargins(0, 0, 0, 0)
                self.title_bar.btn_max.set_kind("restore")
            else:
                self._outer_lay.setContentsMargins(
                    SHADOW_MARGIN, SHADOW_MARGIN, SHADOW_MARGIN, SHADOW_MARGIN
                )
                self.title_bar.btn_max.set_kind("max")
            self.outer.set_maximized(maximized)
        super().changeEvent(e)

    def showEvent(self, e):
        super().showEvent(e)
        if not self._entrance_done:
            self._entrance_done = True
            window_pop_in(self, duration=300, rise=16)
