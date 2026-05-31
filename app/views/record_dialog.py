"""Diálogo frameless para adicionar / editar um registro de hora extra."""
from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QHBoxLayout, QLabel, QLineEdit,
    QVBoxLayout, QWidget,
)

from .. import icons
from ..utils import gerar_opcoes_hhmm, hhmm_to_minutes
from .custom_widgets import (
    AnimatedButton, BaseDialog, ConfirmDialog, PlusMinusSpin,
)
from .widgets import field_label


class RecordDialog(BaseDialog):
    """Diálogo de cadastro/edição de hora extra."""

    def __init__(
        self,
        parent=None,
        *,
        registro=None,
        data_default: date | None = None,
        minutos_default: int | None = None,
    ):
        super().__init__(title="Registro de hora extra", parent=parent)
        self.registro = registro
        self.setMinimumWidth(540)

        content = self._setup("Registro de hora extra")
        self._build_ui(content)
        self._preencher(registro, data_default, minutos_default)

    # ----------------------------------------------------------------
    def _build_ui(self, content: QWidget) -> None:
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(14)

        titulo = QLabel(
            "Editar registro" if self.registro else "Novo registro"
        )
        titulo.setObjectName("DialogTitle")
        sub = QLabel(
            "Selecione a data, a duração e descreva o motivo. "
            "A duração tem opções pré-definidas ou modo personalizado."
        )
        sub.setObjectName("DialogSubtitle")
        sub.setWordWrap(True)
        layout.addWidget(titulo)
        layout.addWidget(sub)
        layout.addSpacing(8)

        # ----- Data
        layout.addWidget(field_label("Data"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setDate(QDate.currentDate())
        layout.addWidget(self.date_edit)

        # ----- Duração
        layout.addWidget(field_label("Duração"))
        h_row = QHBoxLayout()
        h_row.setSpacing(10)

        self.combo_horas = QComboBox()
        self.combo_horas.addItem("Personalizado…", userData=-1)
        for hhmm in gerar_opcoes_hhmm(30, 12 * 60, 30):
            minutos = hhmm_to_minutes(hhmm)
            self.combo_horas.addItem(hhmm, userData=minutos)
        idx_default = self.combo_horas.findData(60)
        if idx_default >= 0:
            self.combo_horas.setCurrentIndex(idx_default)
        self.combo_horas.currentIndexChanged.connect(self._on_combo_changed)
        h_row.addWidget(self.combo_horas, 2)

        self.spin_h = PlusMinusSpin(
            minimum=0, maximum=23, value=0, suffix=" h", width_min=140,
        )
        self.spin_h.setEnabled(False)
        h_row.addWidget(self.spin_h, 1)

        self.spin_m = PlusMinusSpin(
            minimum=0, maximum=59, value=0, suffix=" min", width_min=150,
        )
        self.spin_m.setEnabled(False)
        h_row.addWidget(self.spin_m, 1)

        layout.addLayout(h_row)

        # ----- Motivo
        layout.addWidget(field_label("Motivo"))
        self.motivo = QLineEdit()
        self.motivo.setPlaceholderText(
            "Ex.: demanda urgente, implantação, sustentação…"
        )
        self.motivo.setMaxLength(200)
        layout.addWidget(self.motivo)

        layout.addSpacing(8)

        # ----- Botões
        botoes = QHBoxLayout()
        botoes.addStretch(1)

        cancelar = AnimatedButton("Cancelar")
        cancelar.setCursor(Qt.PointingHandCursor)
        cancelar.setMinimumHeight(40)
        cancelar.setMinimumWidth(110)
        cancelar.clicked.connect(self.reject)
        botoes.addWidget(cancelar)

        self.btn_salvar = AnimatedButton("Salvar registro", ripple_light=True)
        self.btn_salvar.setObjectName("PrimaryButton")
        self.btn_salvar.setIcon(icons.icon("save", "#FFFFFF", 16, 2.1))
        self.btn_salvar.setCursor(Qt.PointingHandCursor)
        self.btn_salvar.setMinimumHeight(42)
        self.btn_salvar.setMinimumWidth(168)
        self.btn_salvar.setDefault(True)
        self.btn_salvar.clicked.connect(self._on_accept)
        botoes.addWidget(self.btn_salvar)

        layout.addLayout(botoes)

    # ----------------------------------------------------------------
    def _preencher(self, registro, data_default, minutos_default) -> None:
        if registro is not None:
            self.date_edit.setDate(QDate(
                registro.data.year, registro.data.month, registro.data.day
            ))
            self.motivo.setText(registro.motivo)
            self._setar_minutos(registro.minutos)
        else:
            if data_default is not None:
                self.date_edit.setDate(QDate(
                    data_default.year, data_default.month, data_default.day
                ))
            if minutos_default is not None and minutos_default > 0:
                self._setar_minutos(minutos_default)

    def _setar_minutos(self, minutos: int) -> None:
        idx = self.combo_horas.findData(minutos)
        if idx >= 0:
            self.combo_horas.setCurrentIndex(idx)
        else:
            self.combo_horas.setCurrentIndex(0)
            self.spin_h.setValue(minutos // 60)
            self.spin_m.setValue(minutos % 60)

    def _on_combo_changed(self, _idx: int) -> None:
        personalizado = self.combo_horas.currentData() == -1
        self.spin_h.setEnabled(personalizado)
        self.spin_m.setEnabled(personalizado)

    def _minutos_selecionados(self) -> int:
        data = self.combo_horas.currentData()
        if data == -1:
            return self.spin_h.value() * 60 + self.spin_m.value()
        return int(data)

    def _on_accept(self) -> None:
        minutos = self._minutos_selecionados()
        if minutos <= 0:
            ConfirmDialog(
                "Duração inválida",
                "Informe uma duração maior que zero.",
                confirm_text="OK", cancel_text="", parent=self,
            ).exec()
            return
        if not self.motivo.text().strip():
            ConfirmDialog(
                "Motivo obrigatório",
                "Informe o motivo das horas extras.",
                confirm_text="OK", cancel_text="", parent=self,
            ).exec()
            self.motivo.setFocus()
            return
        self.accept()

    # API pública
    def get_dados(self) -> tuple[date, int, str]:
        qd = self.date_edit.date()
        return (
            date(qd.year(), qd.month(), qd.day()),
            self._minutos_selecionados(),
            self.motivo.text().strip(),
        )
