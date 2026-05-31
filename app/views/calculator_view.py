"""Calculadora de horas — diferença entre dois horários, com desconto opcional."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel,
    QVBoxLayout, QWidget,
)

from .. import icons
from .. import theme
from ..database import Database
from ..utils import format_brl, minutes_to_decimal_hours, minutes_to_hhmm
from .custom_widgets import AnimatedButton, ConfirmDialog, HourMinutePicker
from .widgets import Card, SummaryCard, field_label


class CalculatorView(QWidget):
    """Calcula a duração entre dois horários e permite virar registro."""

    usar_como_registro = Signal(int)  # emite minutos para criar registro

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.setObjectName("Page")
        self.db = db
        self._build_ui()
        self._recalcular()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(34, 28, 34, 28)
        root.setSpacing(20)

        titulos = QVBoxLayout()
        titulos.setSpacing(3)
        lbl = QLabel("Calculadora de Horas")
        lbl.setObjectName("PageTitle")
        sub = QLabel(
            "Informe o horário de entrada e saída para calcular a duração — "
            "útil para registrar horas extras com precisão."
        )
        sub.setObjectName("PageSubtitle")
        sub.setWordWrap(True)
        titulos.addWidget(lbl)
        titulos.addWidget(sub)
        root.addLayout(titulos)

        # Card de entrada
        entrada_card = Card()
        ent_lay = QGridLayout(entrada_card)
        ent_lay.setContentsMargins(28, 24, 28, 24)
        ent_lay.setHorizontalSpacing(20)
        ent_lay.setVerticalSpacing(8)

        ent_lay.addWidget(field_label("Horário inicial"), 0, 0)
        ent_lay.addWidget(field_label("Horário final"), 0, 1)
        ent_lay.addWidget(field_label("Descontar intervalo"), 0, 2)

        self.picker_inicio = HourMinutePicker(18, 0)
        self.picker_inicio.timeChanged.connect(self._recalcular)
        ent_lay.addWidget(self.picker_inicio, 1, 0)

        self.picker_fim = HourMinutePicker(20, 30)
        self.picker_fim.timeChanged.connect(self._recalcular)
        ent_lay.addWidget(self.picker_fim, 1, 1)

        self.combo_intervalo = QComboBox()
        self.combo_intervalo.addItem("Nenhum", userData=0)
        for minutos in (15, 30, 45, 60):
            self.combo_intervalo.addItem(
                minutes_to_hhmm(minutos), userData=minutos
            )
        self.combo_intervalo.currentIndexChanged.connect(self._recalcular)
        self.combo_intervalo.setMinimumHeight(40)
        ent_lay.addWidget(self.combo_intervalo, 1, 2)

        self.chk_virada = QCheckBox(
            "Cruza a meia-noite (saída no dia seguinte)"
        )
        self.chk_virada.stateChanged.connect(self._recalcular)
        ent_lay.addWidget(self.chk_virada, 2, 0, 1, 3)

        root.addWidget(entrada_card)

        # Cards de resultado
        resultado_row = QHBoxLayout()
        resultado_row.setSpacing(14)
        self.card_duracao = SummaryCard(
            "Duração calculada", "00:00",
            value_style="CardValuePrimary", icon_name="clock", icon_tone="primary",
        )
        self.card_valor = SummaryCard(
            "Valor estimado", "R$ 0,00",
            value_style="CardValueAccent", icon_name="wallet", icon_tone="accent",
        )
        resultado_row.addWidget(self.card_duracao, 1)
        resultado_row.addWidget(self.card_valor, 1)
        root.addLayout(resultado_row)

        # Botões
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.btn_zerar = AnimatedButton("Limpar")
        self.btn_zerar.setIcon(icons.icon("rotate-ccw", theme.TEXT_MUTED, 16, 2.1))
        self.btn_zerar.setCursor(Qt.PointingHandCursor)
        self.btn_zerar.setMinimumHeight(44)
        self.btn_zerar.setMinimumWidth(128)
        self.btn_zerar.clicked.connect(self._limpar)
        self.btn_registrar = AnimatedButton(
            "Usar como novo registro", ripple_light=True
        )
        self.btn_registrar.setObjectName("PrimaryButton")
        self.btn_registrar.setIcon(icons.icon("corner-down-left", "#FFFFFF", 17, 2.2))
        self.btn_registrar.setCursor(Qt.PointingHandCursor)
        self.btn_registrar.setMinimumHeight(44)
        self.btn_registrar.setMinimumWidth(230)
        self.btn_registrar.clicked.connect(self._usar_como_registro)
        btn_row.addWidget(self.btn_zerar)
        btn_row.addWidget(self.btn_registrar)
        root.addLayout(btn_row)

        root.addStretch(1)

    def _minutos_calculados(self) -> int:
        h_ini, m_ini = self.picker_inicio.time()
        h_fim, m_fim = self.picker_fim.time()
        diff = (h_fim * 60 + m_fim) - (h_ini * 60 + m_ini)
        if self.chk_virada.isChecked() or diff < 0:
            diff += 24 * 60
        intervalo = int(self.combo_intervalo.currentData() or 0)
        return max(0, diff - intervalo)

    def _recalcular(self) -> None:
        minutos = self._minutos_calculados()
        self.card_duracao.set_value(minutes_to_hhmm(minutos))
        valor = minutes_to_decimal_hours(minutos) * self.db.get_valor_hora()
        self.card_valor.set_value(format_brl(valor))
        self.btn_registrar.setEnabled(minutos > 0)

    def atualizar_valores(self) -> None:
        """Recalcula usando os valores atuais de configuração."""
        self._recalcular()

    def _limpar(self) -> None:
        self.picker_inicio.setTime(18, 0)
        self.picker_fim.setTime(20, 30)
        self.combo_intervalo.setCurrentIndex(0)
        self.chk_virada.setChecked(False)
        self._recalcular()

    def _usar_como_registro(self) -> None:
        minutos = self._minutos_calculados()
        if minutos <= 0:
            ConfirmDialog(
                "Duração inválida",
                "A duração calculada precisa ser maior que zero.",
                confirm_text="OK", cancel_text="",
                parent=self.window(),
            ).exec()
            return
        self.usar_como_registro.emit(minutos)
