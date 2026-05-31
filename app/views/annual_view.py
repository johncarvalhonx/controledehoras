"""Tela de resumo anual: dashboard com cards, gráfico e tabela por mês."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from .. import theme
from ..config import MESES_PT, MESES_PT_CURTO
from ..database import Database
from ..utils import format_brl, minutes_to_decimal_hours, minutes_to_hhmm
from .chart import BarChart
from .widgets import Card, SummaryCard


class AnnualView(QWidget):
    """Resumo anual de horas extras."""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.setObjectName("Page")
        self.db = db
        self.ano_atual = 2026
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(34, 28, 34, 12)
        root.setSpacing(18)

        header = QHBoxLayout()
        titulos = QVBoxLayout()
        titulos.setSpacing(3)
        self.lbl_title = QLabel("Resumo Anual")
        self.lbl_title.setObjectName("PageTitle")
        self.lbl_subtitle = QLabel("Visão consolidada do ano.")
        self.lbl_subtitle.setObjectName("PageSubtitle")
        titulos.addWidget(self.lbl_title)
        titulos.addWidget(self.lbl_subtitle)
        header.addLayout(titulos, 1)
        root.addLayout(header)

        # área rolável (responsiva)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("Page")
        col = QVBoxLayout(content)
        col.setContentsMargins(0, 0, 4, 8)
        col.setSpacing(18)

        # Cards
        cards = QHBoxLayout()
        cards.setSpacing(16)
        self.card_total_horas = SummaryCard(
            "Total de horas no ano", "00:00",
            value_style="CardValuePrimary", icon_name="clock", icon_tone="primary",
        )
        self.card_total_valor = SummaryCard(
            "Total recebido em extras", "R$ 0,00",
            value_style="CardValueAccent", icon_name="wallet", icon_tone="accent",
        )
        self.card_media_mes = SummaryCard(
            "Média mensal de horas", "00:00",
            value_style="CardValue", icon_name="bar-chart", icon_tone="violet",
        )
        self.card_total_anual = SummaryCard(
            "Salário base + extras (ano)", "R$ 0,00",
            value_style="CardValue", icon_name="receipt", icon_tone="neutral",
        )
        for c in (self.card_total_horas, self.card_total_valor,
                  self.card_media_mes, self.card_total_anual):
            cards.addWidget(c, 1)
        col.addLayout(cards)

        # Gráfico
        chart_card = Card()
        ch_lay = QVBoxLayout(chart_card)
        ch_lay.setContentsMargins(20, 16, 20, 14)
        ch_lay.setSpacing(8)
        ch_title = QLabel("Horas extras por mês")
        ch_title.setObjectName("SectionTitle")
        ch_lay.addWidget(ch_title)
        self.chart = BarChart()
        ch_lay.addWidget(self.chart, 1)
        col.addWidget(chart_card)

        # Tabela mensal
        tabela_card = Card()
        tab_lay = QVBoxLayout(tabela_card)
        tab_lay.setContentsMargins(20, 16, 20, 16)
        tab_lay.setSpacing(10)
        t_title = QLabel("Detalhamento por mês")
        t_title.setObjectName("SectionTitle")
        tab_lay.addWidget(t_title)

        grid_host = QWidget()
        self.grid = QGridLayout(grid_host)
        self.grid.setContentsMargins(0, 4, 0, 0)
        self.grid.setHorizontalSpacing(8)
        self.grid.setVerticalSpacing(4)
        self._montar_cabecalho_grid()
        tab_lay.addWidget(grid_host)
        col.addWidget(tabela_card)
        col.addStretch(1)

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    def _montar_cabecalho_grid(self) -> None:
        cabecalhos = ["MÊS", "HORAS EXTRAS", "VALOR DAS HORAS EXTRAS",
                      "SALÁRIO ESTIMADO"]
        for col, txt in enumerate(cabecalhos):
            lbl = QLabel(txt)
            lbl.setObjectName("AnnualHeaderCell")
            if col == 0:
                lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            elif col == 1:
                lbl.setAlignment(Qt.AlignCenter)
            else:
                lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.grid.addWidget(lbl, 0, col)
        self.grid.setColumnStretch(0, 2)
        self.grid.setColumnStretch(1, 1)
        self.grid.setColumnStretch(2, 2)
        self.grid.setColumnStretch(3, 2)

    # ----------------------------------------------------------------
    def refresh(self) -> None:
        self.lbl_subtitle.setText(f"Visão consolidada de {self.ano_atual}.")

        salario = self.db.get_salario()
        valor_hora = self.db.get_valor_hora()

        totais = self.db.totais_por_mes(self.ano_atual)
        total_min = sum(totais.values())
        total_valor = minutes_to_decimal_hours(total_min) * valor_hora
        media_min = total_min // 12

        self.card_total_horas.set_value(minutes_to_hhmm(total_min))
        self.card_total_valor.set_value(format_brl(total_valor))
        self.card_media_mes.set_value(minutes_to_hhmm(media_min))
        self.card_total_anual.set_value(format_brl(salario * 12 + total_valor))

        # gráfico (horas decimais por mês)
        horas_por_mes = [minutes_to_decimal_hours(totais.get(m, 0)) for m in range(1, 13)]
        self.chart.set_data(horas_por_mes, MESES_PT_CURTO, animate=True)

        # limpa e reconstrói o grid
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            w = item.widget() if item is not None else None
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._montar_cabecalho_grid()

        for mes in range(1, 13):
            min_mes = totais.get(mes, 0)
            valor = minutes_to_decimal_hours(min_mes) * valor_hora
            salario_mes = salario + valor
            tem = min_mes > 0
            style = "AnnualCell" if tem else "AnnualCellEmpty"

            lbl_mes = QLabel(MESES_PT[mes - 1])
            lbl_mes.setObjectName("AnnualCellMonth")
            lbl_h = QLabel(minutes_to_hhmm(min_mes) if tem else "—")
            lbl_h.setObjectName(style)
            lbl_h.setAlignment(Qt.AlignCenter)
            lbl_v = QLabel(format_brl(valor) if tem else "—")
            lbl_v.setObjectName(style)
            lbl_v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl_s = QLabel(format_brl(salario_mes))
            lbl_s.setObjectName(style)
            lbl_s.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.grid.addWidget(lbl_mes, mes, 0)
            self.grid.addWidget(lbl_h, mes, 1)
            self.grid.addWidget(lbl_v, mes, 2)
            self.grid.addWidget(lbl_s, mes, 3)

        # linha de total
        base = "font-weight:800;background:transparent;padding-top:10px;"
        l_t = QLabel("Total do ano")
        l_t.setStyleSheet(base + f"color:{theme.TEXT_STRONG};")
        l_th = QLabel(minutes_to_hhmm(total_min))
        l_th.setAlignment(Qt.AlignCenter)
        l_th.setStyleSheet(base + f"color:{theme.PRIMARY};")
        l_tv = QLabel(format_brl(total_valor))
        l_tv.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        l_tv.setStyleSheet(base + f"color:{theme.ACCENT_DARK};")
        l_ts = QLabel(format_brl(salario * 12 + total_valor))
        l_ts.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        l_ts.setStyleSheet(base + f"color:{theme.TEXT_STRONG};")
        self.grid.addWidget(l_t, 13, 0)
        self.grid.addWidget(l_th, 13, 1)
        self.grid.addWidget(l_tv, 13, 2)
        self.grid.addWidget(l_ts, 13, 3)
