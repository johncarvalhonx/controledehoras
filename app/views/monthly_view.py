"""Tela mensal: registros do mês selecionado + resumo financeiro."""
from datetime import date

from PySide6.QtCore import QEasingCurve, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QLabel,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from .. import icons
from .. import theme
from ..anim import fade_in, stagger_fade
from ..config import MESES_PT
from ..database import Database, Registro
from ..utils import (
    format_brl, format_date_br, minutes_to_decimal_hours, minutes_to_hhmm,
)
from .custom_widgets import AnimatedButton, ConfirmDialog
from .record_dialog import RecordDialog
from .widgets import Card, MonthSelector, SummaryCard


class MonthlyView(QWidget):
    """View principal de controle mensal."""

    data_changed = Signal()

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.setObjectName("Page")
        self.db = db
        self.ano_atual = 2026
        self.mes_atual = date.today().month
        self.notifier = lambda *_a, **_k: None      # injetado pela MainWindow
        self.open_settings = lambda *_a, **_k: None  # idem
        self._flash_anim: QVariantAnimation | None = None
        self._entered = False
        self._mostrando_vazio = False
        self._build_ui()
        self.seletor.set_month(self.mes_atual, animate=False)
        self.refresh()

    # ---------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(34, 28, 34, 24)
        root.setSpacing(18)

        # Cabeçalho
        header = QHBoxLayout()
        header.setSpacing(16)
        titulos = QVBoxLayout()
        titulos.setSpacing(3)
        self.lbl_title = QLabel("Controle Mensal")
        self.lbl_title.setObjectName("PageTitle")
        self.lbl_subtitle = QLabel("Acompanhe suas horas extras de cada mês.")
        self.lbl_subtitle.setObjectName("PageSubtitle")
        titulos.addWidget(self.lbl_title)
        titulos.addWidget(self.lbl_subtitle)
        header.addLayout(titulos, 1)

        self.btn_novo = AnimatedButton("Novo registro", ripple_light=True, glow=True)
        self.btn_novo.setObjectName("PrimaryButton")
        self.btn_novo.setIcon(icons.icon("plus", "#FFFFFF", 18, 2.4))
        self.btn_novo.setCursor(Qt.PointingHandCursor)
        self.btn_novo.setMinimumHeight(44)
        self.btn_novo.setMinimumWidth(170)
        self.btn_novo.clicked.connect(self._novo_registro)
        header.addWidget(self.btn_novo, 0, Qt.AlignBottom)
        root.addLayout(header)

        # Seletor de meses
        chip_card = Card()
        chip_layout = QVBoxLayout(chip_card)
        chip_layout.setContentsMargins(10, 8, 10, 8)
        self.seletor = MonthSelector()
        self.seletor.monthChanged.connect(self._on_month_changed)
        chip_layout.addWidget(self.seletor)
        root.addWidget(chip_card)

        # Cards de resumo
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        self.card_horas = SummaryCard(
            "Horas extras no mês", "00:00",
            value_style="CardValuePrimary", icon_name="clock", icon_tone="primary",
        )
        self.card_valor_extra = SummaryCard(
            "Valor das horas extras", "R$ 0,00",
            value_style="CardValueAccent", icon_name="wallet", icon_tone="accent",
        )
        self.card_salario_total = SummaryCard(
            "Salário estimado do mês", "R$ 0,00",
            value_style="CardValue", icon_name="trending-up", icon_tone="violet",
        )
        cards_row.addWidget(self.card_horas, 1)
        cards_row.addWidget(self.card_valor_extra, 1)
        cards_row.addWidget(self.card_salario_total, 1)
        root.addLayout(cards_row)

        # Linha de info base (personalizável)
        info_card = Card()
        info_layout = QHBoxLayout(info_card)
        info_layout.setContentsMargins(20, 12, 16, 12)
        info_layout.setSpacing(28)
        row_sal, self._val_salario = self._info(
            "receipt", "Salário base", format_brl(self.db.get_salario())
        )
        row_hora, self._val_hora = self._info(
            "coins", "Valor da hora", format_brl(self.db.get_valor_hora())
        )
        info_layout.addLayout(row_sal)
        info_layout.addLayout(row_hora)
        info_layout.addStretch(1)

        self.btn_personalizar = AnimatedButton("Personalizar")
        self.btn_personalizar.setObjectName("GhostButton")
        self.btn_personalizar.setIcon(icons.icon("sliders", theme.PRIMARY, 16, 2.0))
        self.btn_personalizar.setCursor(Qt.PointingHandCursor)
        self.btn_personalizar.setMinimumHeight(40)
        self.btn_personalizar.setToolTip("Definir salário e valor da hora")
        self.btn_personalizar.clicked.connect(lambda: self.open_settings())
        info_layout.addWidget(self.btn_personalizar, 0, Qt.AlignVCenter)
        root.addWidget(info_card)

        # Tabela
        tabela_card = Card()
        tab_lay = QVBoxLayout(tabela_card)
        tab_lay.setContentsMargins(20, 18, 20, 18)
        tab_lay.setSpacing(12)

        cabecalho = QHBoxLayout()
        self.lbl_tabela = QLabel("Registros do mês")
        self.lbl_tabela.setObjectName("SectionTitle")
        cabecalho.addWidget(self.lbl_tabela)
        cabecalho.addStretch(1)
        self.lbl_qtd = QLabel("")
        self.lbl_qtd.setObjectName("CardLabel")
        cabecalho.addWidget(self.lbl_qtd)
        tab_lay.addLayout(cabecalho)

        self.tabela = QTableWidget(0, 5)
        self.tabela.setHorizontalHeaderLabels(
            ["DATA", "DURAÇÃO", "MOTIVO", "VALOR", "AÇÕES"]
        )
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabela.setShowGrid(False)
        self.tabela.setFocusPolicy(Qt.NoFocus)
        self.tabela.verticalHeader().setDefaultSectionSize(56)
        self.tabela.doubleClicked.connect(lambda _: self._editar_selecionado())

        h = self.tabela.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.Fixed)
        self.tabela.setColumnWidth(4, 168)
        h.setHighlightSections(False)
        self.tabela.setMinimumHeight(220)
        tab_lay.addWidget(self.tabela)

        # Estado vazio (aparece quando o mês não tem registros)
        self.empty_state = self._build_empty_state()
        self.empty_state.hide()
        tab_lay.addWidget(self.empty_state, 1)

        root.addWidget(tabela_card, 1)
        self._tabela_card = tabela_card
        self._chip_card = chip_card
        self._info_card = info_card

    def _build_empty_state(self) -> QWidget:
        host = QWidget()
        host.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(host)
        lay.setContentsMargins(0, 26, 0, 26)
        lay.setSpacing(6)
        lay.setAlignment(Qt.AlignCenter)

        chip = QLabel()
        chip.setFixedSize(72, 72)
        chip.setAlignment(Qt.AlignCenter)
        chip.setStyleSheet(
            f"background-color:{theme.PRIMARY_SOFT}; border-radius:36px;"
        )
        chip.setPixmap(icons.pixmap("inbox", theme.PRIMARY, 32, 1.8))
        lay.addWidget(chip, 0, Qt.AlignHCenter)
        lay.addSpacing(8)

        titulo = QLabel("Nenhum registro neste mês")
        titulo.setObjectName("EmptyTitle")
        titulo.setAlignment(Qt.AlignCenter)
        lay.addWidget(titulo)

        sub = QLabel("Adicione sua primeira hora extra para ver o resumo do mês.")
        sub.setObjectName("EmptySub")
        sub.setAlignment(Qt.AlignCenter)
        lay.addWidget(sub)
        lay.addSpacing(12)

        btn = AnimatedButton("Adicionar registro")
        btn.setObjectName("GhostButton")
        btn.setIcon(icons.icon("plus", theme.PRIMARY, 16, 2.2))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(40)
        btn.setMinimumWidth(180)
        btn.clicked.connect(self._novo_registro)
        lay.addWidget(btn, 0, Qt.AlignHCenter)
        return host

    def _info(self, icon_name: str, label: str, valor: str) -> tuple[QHBoxLayout, QLabel]:
        row = QHBoxLayout()
        row.setSpacing(11)
        chip = QLabel()
        chip.setObjectName("CardIconChip")
        chip.setProperty("tone", "neutral")
        chip.setFixedSize(38, 38)
        chip.setAlignment(Qt.AlignCenter)
        chip.setPixmap(icons.pixmap(icon_name, theme.TEXT_MUTED, 19, 2.0))
        row.addWidget(chip, 0)
        box = QVBoxLayout()
        box.setSpacing(1)
        l = QLabel(label)
        l.setObjectName("CardLabel")
        v = QLabel(valor)
        v.setStyleSheet(f"font-weight:700;color:{theme.TEXT_STRONG};background:transparent;font-size:11pt;")
        box.addWidget(l)
        box.addWidget(v)
        row.addLayout(box)
        return row, v

    # ---------------------------------------------------------------
    def _on_month_changed(self, mes: int) -> None:
        self.mes_atual = mes
        self.refresh()

    # ---------------------------------------------------------------
    def refresh(self) -> None:
        self.lbl_subtitle.setText(
            f"{MESES_PT[self.mes_atual - 1]} de {self.ano_atual}"
        )
        self.lbl_tabela.setText("Registros do mês")

        salario = self.db.get_salario()
        valor_hora = self.db.get_valor_hora()
        self._val_salario.setText(format_brl(salario))
        self._val_hora.setText(format_brl(valor_hora))

        registros = self.db.listar_mes(self.ano_atual, self.mes_atual)
        self._preencher_tabela(registros)

        total_min = sum(r.minutos for r in registros)
        valor_extra = minutes_to_decimal_hours(total_min) * valor_hora
        self.card_horas.set_numeric(
            total_min, lambda v: minutes_to_hhmm(int(round(v)))
        )
        self.card_valor_extra.set_numeric(valor_extra, format_brl)
        self.card_salario_total.set_numeric(salario + valor_extra, format_brl)

        qtd = len(registros)
        self.lbl_qtd.setText(
            "Nenhum registro" if qtd == 0
            else f"{qtd} registro{'s' if qtd != 1 else ''}"
        )

        # alterna tabela ⇄ estado vazio com um fade suave
        vazio = qtd == 0
        if vazio != self._mostrando_vazio:
            self._mostrando_vazio = vazio
            self.tabela.setVisible(not vazio)
            self.empty_state.setVisible(vazio)
            alvo = self.empty_state if vazio else self.tabela
            if self.isVisible():
                fade_in(alvo, duration=240)

    def _preencher_tabela(self, registros: list[Registro]) -> None:
        valor_hora = self.db.get_valor_hora()
        self.tabela.setRowCount(0)
        for r in registros:
            row = self.tabela.rowCount()
            self.tabela.insertRow(row)

            item_data = QTableWidgetItem(format_date_br(r.data))
            item_data.setData(Qt.UserRole, r.id)

            item_dur = QTableWidgetItem(minutes_to_hhmm(r.minutos))
            item_dur.setTextAlignment(Qt.AlignCenter)
            f = QFont(); f.setBold(True); item_dur.setFont(f)

            item_motivo = QTableWidgetItem(r.motivo or "—")

            valor = minutes_to_decimal_hours(r.minutos) * valor_hora
            item_valor = QTableWidgetItem(format_brl(valor))
            item_valor.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            f2 = QFont(); f2.setBold(True); item_valor.setFont(f2)
            item_valor.setForeground(QColor(theme.ACCENT_DARK))

            self.tabela.setItem(row, 0, item_data)
            self.tabela.setItem(row, 1, item_dur)
            self.tabela.setItem(row, 2, item_motivo)
            self.tabela.setItem(row, 3, item_valor)

            self.tabela.setCellWidget(row, 4, self._acoes(r.id))

    def _acoes(self, rid: int) -> QWidget:
        acoes = QWidget()
        acoes.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(acoes)
        lay.setContentsMargins(8, 8, 10, 8)
        lay.setSpacing(8)
        lay.addStretch(1)

        btn_edit = AnimatedButton("Editar", radius=9)
        btn_edit.setObjectName("RowActionEdit")
        btn_edit.setIcon(icons.icon("pencil", theme.PRIMARY, 14, 2.1))
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.setFixedHeight(34)
        btn_edit.setMinimumWidth(92)
        btn_edit.setToolTip("Editar registro")
        btn_edit.clicked.connect(lambda _=False, r=rid: self._editar(r))

        btn_del = AnimatedButton("", radius=9)
        btn_del.setObjectName("RowActionDelete")
        btn_del.setIcon(icons.icon("trash", theme.DANGER_DARK, 15, 2.1))
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setFixedSize(38, 34)
        btn_del.setToolTip("Excluir registro")
        btn_del.clicked.connect(lambda _=False, r=rid: self._excluir(r))

        lay.addWidget(btn_edit)
        lay.addWidget(btn_del)
        lay.addStretch(1)
        return acoes

    # ---------------------------------------------------------------
    def _row_of(self, registro_id: int) -> int | None:
        for row in range(self.tabela.rowCount()):
            it = self.tabela.item(row, 0)
            if it is not None and int(it.data(Qt.UserRole)) == registro_id:
                return row
        return None

    def _flash_row(self, registro_id: int) -> None:
        row = self._row_of(registro_id)
        if row is None:
            return
        anim = QVariantAnimation(self)
        anim.setStartValue(QColor(theme.ROW_FLASH))
        anim.setEndValue(QColor(255, 255, 255, 0))
        anim.setDuration(1100)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def upd(c):
            for col in range(self.tabela.columnCount()):
                it = self.tabela.item(row, col)
                if it is not None:
                    it.setBackground(QBrush(c))

        def done():
            for col in range(self.tabela.columnCount()):
                it = self.tabela.item(row, col)
                if it is not None:
                    it.setBackground(QBrush())

        anim.valueChanged.connect(upd)
        anim.finished.connect(done)
        anim.start()
        self._flash_anim = anim

    def _registro_por_id(self, registro_id: int) -> Registro | None:
        for r in self.db.listar_mes(self.ano_atual, self.mes_atual):
            if r.id == registro_id:
                return r
        return None

    def _editar_selecionado(self) -> None:
        rows = self.tabela.selectionModel().selectedRows()
        if not rows:
            return
        item = self.tabela.item(rows[0].row(), 0)
        if item is not None:
            self._editar(int(item.data(Qt.UserRole)))

    def _novo_registro(self) -> None:
        data_default = date(self.ano_atual, self.mes_atual,
                            min(date.today().day, 28))
        dlg = RecordDialog(self, data_default=data_default)
        if dlg.exec() == RecordDialog.Accepted:
            data, minutos, motivo = dlg.get_dados()
            new_id = self.db.adicionar(data, minutos, motivo)
            self.mes_atual = data.month
            self.seletor.set_month(self.mes_atual)
            self.refresh()
            self._flash_row(new_id)
            self.notifier("Registro adicionado com sucesso.", "success")
            self.data_changed.emit()

    def _editar(self, registro_id: int) -> None:
        reg = self._registro_por_id(registro_id)
        if reg is None:
            return
        dlg = RecordDialog(self, registro=reg)
        if dlg.exec() == RecordDialog.Accepted:
            data, minutos, motivo = dlg.get_dados()
            self.db.atualizar(registro_id, data, minutos, motivo)
            self.mes_atual = data.month
            self.seletor.set_month(self.mes_atual)
            self.refresh()
            self._flash_row(registro_id)
            self.notifier("Registro atualizado.", "success")
            self.data_changed.emit()

    def _excluir(self, registro_id: int) -> None:
        dlg = ConfirmDialog(
            "Excluir registro",
            "Tem certeza que deseja excluir este registro?\n"
            "Esta ação não pode ser desfeita.",
            confirm_text="Excluir", cancel_text="Cancelar",
            danger=True, parent=self.window(),
        )
        if dlg.exec() == ConfirmDialog.Accepted:
            self.db.excluir(registro_id)
            self.refresh()
            self.notifier("Registro excluído.", "info")
            self.data_changed.emit()

    # ---------------------------------------------------------------
    def adicionar_a_partir_de_calculadora(self, minutos: int) -> None:
        dlg = RecordDialog(self, data_default=date.today(), minutos_default=minutos)
        if dlg.exec() == RecordDialog.Accepted:
            data, m, motivo = dlg.get_dados()
            new_id = self.db.adicionar(data, m, motivo)
            self.mes_atual = data.month
            self.seletor.set_month(self.mes_atual)
            self.refresh()
            self._flash_row(new_id)
            self.notifier("Registro criado a partir da calculadora.", "success")
            self.data_changed.emit()

    # ---------------------------------------------------------------
    def showEvent(self, e):
        super().showEvent(e)
        if not self._entered:
            self._entered = True
            stagger_fade(
                [
                    self._chip_card,
                    self.card_horas,
                    self.card_valor_extra,
                    self.card_salario_total,
                    self._info_card,
                    self._tabela_card,
                ],
                start_delay=60, step=70, duration=430,
            )
