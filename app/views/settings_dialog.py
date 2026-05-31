"""Diálogo de configurações — salário base e valor da hora (personalizáveis)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .. import icons
from .. import theme
from ..database import Database
from .custom_widgets import AnimatedButton, BaseDialog, CurrencyField
from .widgets import field_label


class SettingsDialog(BaseDialog):
    """Permite ao usuário definir o salário base e o valor da hora extra."""

    def __init__(self, db: Database, parent=None):
        super().__init__(title="Configurações", parent=parent)
        self.db = db
        content = self._setup("Configurações")
        self.setMinimumWidth(540)
        self._build_ui(content)

    def _build_ui(self, content: QWidget) -> None:
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(8)

        # Cabeçalho com ícone
        head = QHBoxLayout()
        head.setSpacing(14)
        chip = QLabel()
        chip.setObjectName("DialogIconChip")
        chip.setFixedSize(44, 44)
        chip.setAlignment(Qt.AlignCenter)
        chip.setPixmap(icons.pixmap("sliders", theme.PRIMARY, 24, 2.1))
        head.addWidget(chip, 0, Qt.AlignTop)

        head_txt = QVBoxLayout()
        head_txt.setSpacing(2)
        titulo = QLabel("Personalização")
        titulo.setObjectName("DialogTitle")
        sub = QLabel(
            "Defina seu salário base mensal e o valor recebido por hora extra. "
            "Os cálculos do app passam a usar esses valores."
        )
        sub.setObjectName("DialogSubtitle")
        sub.setWordWrap(True)
        head_txt.addWidget(titulo)
        head_txt.addWidget(sub)
        head.addLayout(head_txt, 1)
        layout.addLayout(head)
        layout.addSpacing(10)

        # Salário base
        layout.addWidget(field_label("Salário base mensal"))
        self.field_salario = CurrencyField(self.db.get_salario())
        layout.addWidget(self.field_salario)
        layout.addSpacing(6)

        # Valor da hora + sugestão
        layout.addWidget(field_label("Valor da hora extra"))
        hora_row = QHBoxLayout()
        hora_row.setSpacing(10)
        self.field_hora = CurrencyField(self.db.get_valor_hora())
        hora_row.addWidget(self.field_hora, 1)

        self.btn_sugerir = AnimatedButton("Sugerir (220 h/mês)")
        self.btn_sugerir.setObjectName("GhostButton")
        self.btn_sugerir.setCursor(Qt.PointingHandCursor)
        self.btn_sugerir.setMinimumHeight(44)
        self.btn_sugerir.setToolTip(
            "Calcula o valor da hora dividindo o salário base por 220 horas/mês"
        )
        self.btn_sugerir.clicked.connect(self._sugerir)
        hora_row.addWidget(self.btn_sugerir, 0)
        layout.addLayout(hora_row)

        dica = QLabel(
            "Dica: você pode digitar os valores livremente — o campo formata em "
            "reais automaticamente."
        )
        dica.setWordWrap(True)
        dica.setStyleSheet(
            f"color:{theme.TEXT_SUBTLE}; background:transparent; font-size:8.5pt;"
        )
        layout.addSpacing(4)
        layout.addWidget(dica)
        layout.addSpacing(12)

        # Botões
        botoes = QHBoxLayout()
        botoes.addStretch(1)
        cancelar = AnimatedButton("Cancelar")
        cancelar.setCursor(Qt.PointingHandCursor)
        cancelar.setMinimumHeight(42)
        cancelar.setMinimumWidth(110)
        cancelar.clicked.connect(self.reject)
        botoes.addWidget(cancelar)

        self.btn_salvar = AnimatedButton("Salvar configurações", ripple_light=True)
        self.btn_salvar.setObjectName("PrimaryButton")
        self.btn_salvar.setIcon(icons.icon("check", "#FFFFFF", 16, 2.3))
        self.btn_salvar.setCursor(Qt.PointingHandCursor)
        self.btn_salvar.setMinimumHeight(42)
        self.btn_salvar.setMinimumWidth(190)
        self.btn_salvar.setDefault(True)
        self.btn_salvar.clicked.connect(self._salvar)
        botoes.addWidget(self.btn_salvar)
        layout.addLayout(botoes)

    def _sugerir(self) -> None:
        salario = self.field_salario.value()
        if salario > 0:
            self.field_hora.set_value(round(salario / 220.0, 2))

    def _salvar(self) -> None:
        self.db.set_salario(self.field_salario.value())
        self.db.set_valor_hora(self.field_hora.value())
        self.accept()
