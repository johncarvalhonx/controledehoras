"""Folha de estilo (QSS) global — consome os tokens de app/theme.py."""
from pathlib import Path

from . import theme

_QSS_TEMPLATE = """
* {{ outline: 0; }}

QMainWindow, QDialog {{ background: transparent; }}

QWidget {{
    color: {TEXT};
    font-size: 10pt;
}}

QToolTip {{
    background-color: {CHROME_BOT};
    color: {ON_DARK};
    border: 1px solid {NAV_HOVER};
    padding: 6px 10px;
    border-radius: 8px;
    font-weight: 500;
}}

/* ================== Janela frameless ================== */
QFrame#InnerContainer {{
    background-color: {APP_BG};
    border: 1px solid {BORDER_STRONG};
}}
QWidget#Body, QWidget#ContentStack {{ background-color: {APP_BG}; }}
QWidget#Page {{ background-color: {APP_BG}; }}

/* ================== Title bar ================== */
QFrame#TitleBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {CHROME_TOP}, stop:1 {CHROME_BOT});
    border: none;
}}
QLabel#TitleBarTitle {{
    color: {ON_DARK};
    background: transparent;
    font-size: 10pt;
    font-weight: 600;
    letter-spacing: 0.3px;
}}
QPushButton#TitleBarTool {{
    background: transparent; border: none; border-radius: 8px; padding: 0;
}}
QPushButton#TitleBarTool:hover {{ background: rgba(255, 255, 255, 0.10); }}
QPushButton#TitleBarTool:pressed {{ background: rgba(255, 255, 255, 0.16); }}

/* ================== Bottom navigation ================== */
QFrame#BottomNav {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {CHROME_BOT}, stop:1 {NAV_BG});
    border: none;
    border-top: 1px solid #1B2540;
}}
QLabel#BottomNavSignature {{
    color: {ON_DARK_MUTED};
    font-size: 7.5pt;
    background: transparent;
    padding-right: 2px;
}}

/* ================== Tipografia de página ================== */
QLabel#PageTitle {{
    font-size: 23pt;
    font-weight: 800;
    color: {TEXT_STRONG};
    background: transparent;
}}
QLabel#PageSubtitle {{
    font-size: 10.5pt;
    color: {TEXT_MUTED};
    background: transparent;
}}
QLabel#SectionTitle {{
    font-size: 12.5pt;
    font-weight: 700;
    color: {TEXT};
    background: transparent;
}}

/* ================== Cards ================== */
QFrame#Card {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 16px;
}}
QFrame#SummaryCard {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 16px;
}}
QFrame#SummaryCard:hover {{
    border: 1px solid {PRIMARY_TINT};
}}

QLabel#CardIconChip {{
    background-color: {PRIMARY_SOFT};
    border-radius: 14px;
}}
QLabel#CardIconChip[tone="accent"]  {{ background-color: {ACCENT_SOFT}; }}
QLabel#CardIconChip[tone="violet"]  {{ background-color: {VIOLET_SOFT}; }}
QLabel#CardIconChip[tone="neutral"] {{ background-color: {SURFACE_MUTED}; }}

QLabel#DialogIconChip {{
    background-color: {PRIMARY_SOFT};
    border-radius: 12px;
}}
QLabel#DialogIconChip[danger="true"] {{ background-color: {DANGER_SOFT}; }}

QLabel#CardLabel {{
    color: {TEXT_MUTED};
    font-size: 9pt;
    font-weight: 700;
    background: transparent;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}
QLabel#CardValue {{
    color: {TEXT_STRONG};
    font-size: 20pt;
    font-weight: 800;
    background: transparent;
}}
QLabel#CardValueAccent {{
    color: {ACCENT_DARK};
    font-size: 20pt;
    font-weight: 800;
    background: transparent;
}}
QLabel#CardValuePrimary {{
    color: {PRIMARY};
    font-size: 20pt;
    font-weight: 800;
    background: transparent;
}}

/* ================== Inputs ================== */
QLineEdit, QComboBox, QDateEdit {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER_STRONG};
    border-radius: 12px;
    padding: 10px 13px;
    min-height: 22px;
    selection-background-color: {PRIMARY};
    selection-color: #FFFFFF;
}}
QLineEdit:hover, QComboBox:hover, QDateEdit:hover {{
    border: 1px solid {TEXT_SUBTLE};
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
    border: 2px solid {PRIMARY};
    padding: 9px 12px;            /* compensa +1px da borda, sem "pular" */
    background-color: #FCFDFF;
}}
QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled {{
    background-color: {SURFACE_ALT};
    color: {TEXT_SUBTLE};
}}
QLineEdit {{ selection-background-color: {PRIMARY}; }}

/* ComboBox */
QComboBox::drop-down {{
    border: none; width: 28px;
    subcontrol-origin: padding; subcontrol-position: top right;
}}
QComboBox::down-arrow {{
    image: url("__CHEVRON_DOWN__"); width: 14px; height: 14px; margin-right: 9px;
}}
QComboBox QAbstractItemView {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 6px;
    outline: 0;
}}
QComboBox QAbstractItemView::item {{
    background-color: {SURFACE};
    color: {TEXT};
    padding: 9px 10px;
    border-radius: 8px;
    min-height: 22px;
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: {PRIMARY_SOFT};
    color: {PRIMARY_PRESS};
}}
QComboBox QAbstractItemView::item:selected {{
    background-color: {PRIMARY};
    color: #FFFFFF;
}}

/* DateEdit + calendário */
QDateEdit::drop-down {{
    border: none; width: 28px;
    subcontrol-origin: padding; subcontrol-position: top right;
}}
QDateEdit::down-arrow {{
    image: url("__CHEVRON_DOWN__"); width: 14px; height: 14px; margin-right: 9px;
}}
QCalendarWidget {{ background-color: {SURFACE}; }}
QCalendarWidget QToolButton {{
    color: {TEXT}; background-color: transparent;
    padding: 6px 10px; border-radius: 8px; font-weight: 600;
}}
QCalendarWidget QToolButton:hover {{ background-color: {PRIMARY_SOFT}; color: {PRIMARY}; }}
QCalendarWidget QWidget {{ alternate-background-color: {SURFACE_ALT}; }}
QCalendarWidget QMenu {{
    background-color: {SURFACE}; border: 1px solid {BORDER};
    border-radius: 8px; padding: 4px;
}}
QCalendarWidget QSpinBox {{
    background-color: {SURFACE}; border: 1px solid {BORDER};
    border-radius: 6px; padding: 2px 6px;
}}
QCalendarWidget QAbstractItemView:enabled {{
    color: {TEXT}; background-color: {SURFACE};
    selection-background-color: {PRIMARY}; selection-color: #FFFFFF; outline: 0;
}}

QLabel#FieldLabel {{
    color: {TEXT}; font-size: 9pt; font-weight: 600;
    background: transparent; padding-bottom: 5px;
}}

/* Checkbox */
QCheckBox {{ background: transparent; color: {TEXT}; spacing: 10px; padding: 4px 0; }}
QCheckBox::indicator {{
    width: 19px; height: 19px;
    border: 1.5px solid {BORDER_STRONG}; border-radius: 6px; background-color: {SURFACE};
}}
QCheckBox::indicator:hover {{ border-color: {PRIMARY}; }}
QCheckBox::indicator:checked {{
    background-color: {PRIMARY}; border-color: {PRIMARY};
    image: url("__CHECK_ICON__");
}}
QCheckBox::indicator:checked:hover {{ background-color: {PRIMARY_HOVER}; border-color: {PRIMARY_HOVER}; }}

/* ================== Botões ================== */
QPushButton {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER_STRONG};
    border-radius: 12px;
    padding: 10px 18px;
    font-weight: 600;
    min-height: 22px;
}}
QPushButton:hover {{ background-color: {SURFACE_ALT}; border-color: {TEXT_SUBTLE}; color: {PRIMARY_PRESS}; }}
QPushButton:pressed {{ background-color: {SURFACE_MUTED}; padding-top: 11px; padding-bottom: 9px; }}
QPushButton:disabled {{ background-color: {SURFACE_MUTED}; color: {TEXT_SUBTLE}; border-color: {BORDER}; }}

QPushButton#PrimaryButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {PRIMARY_GRAD_1}, stop:0.55 {PRIMARY_GRAD_2}, stop:1 {PRIMARY_GRAD_3});
    color: #FFFFFF;
    border: 1px solid {PRIMARY};
    border-radius: 12px;
    font-weight: 700;
}}
QPushButton#PrimaryButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {PRIMARY}, stop:0.55 {PRIMARY_HOVER}, stop:1 #6D28D9);
    border-color: {PRIMARY_HOVER};
}}
QPushButton#PrimaryButton:pressed {{
    background: {PRIMARY_PRESS}; border-color: {PRIMARY_PRESS};
}}
QPushButton#PrimaryButton:disabled {{
    background: #A5B4FC; color: #EEF2FF; border-color: #A5B4FC;
}}

QPushButton#DangerButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #F87171, stop:1 {DANGER_DARK});
    color: #FFFFFF;
    border: 1px solid {DANGER_DARK};
    border-radius: 12px;
    font-weight: 700;
}}
QPushButton#DangerButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {DANGER}, stop:1 {DANGER_PRESS});
    border-color: {DANGER_PRESS};
}}
QPushButton#DangerButton:pressed {{ background: {DANGER_PRESS}; border-color: {DANGER_PRESS}; }}

QPushButton#GhostButton {{
    background-color: transparent; color: {PRIMARY};
    border: 1px solid {PRIMARY_TINT};
}}
QPushButton#GhostButton:hover {{ background-color: {PRIMARY_SOFT}; border-color: {PRIMARY}; }}

QPushButton#RowActionEdit {{
    background-color: {SURFACE}; color: {PRIMARY};
    border: 1px solid {BORDER_STRONG}; border-radius: 9px;
    padding: 0 12px; font-size: 9pt; font-weight: 600; min-height: 0;
}}
QPushButton#RowActionEdit:hover {{ background-color: {PRIMARY_SOFT}; border-color: {PRIMARY}; }}

QPushButton#RowActionDelete {{
    background-color: {SURFACE}; color: {DANGER_DARK};
    border: 1px solid {BORDER_STRONG}; border-radius: 9px;
    padding: 0; min-height: 0;
}}
QPushButton#RowActionDelete:hover {{ background-color: {DANGER_SOFT}; border-color: {DANGER}; }}

/* Spin custom (− / +) */
QPushButton#SpinMinus, QPushButton#SpinPlus {{
    background-color: {SURFACE_ALT};
    border: 1px solid {BORDER_STRONG};
    padding: 0; min-height: 0;
}}
QPushButton#SpinMinus {{ border-top-left-radius: 10px; border-bottom-left-radius: 10px;
    border-top-right-radius: 0; border-bottom-right-radius: 0; border-right: none; }}
QPushButton#SpinPlus {{ border-top-right-radius: 10px; border-bottom-right-radius: 10px;
    border-top-left-radius: 0; border-bottom-left-radius: 0; border-left: none; }}
QPushButton#SpinMinus:hover, QPushButton#SpinPlus:hover {{ background-color: {PRIMARY_SOFT}; border-color: {PRIMARY}; }}
QPushButton#SpinMinus:pressed, QPushButton#SpinPlus:pressed {{ background-color: {PRIMARY_SOFT_2}; }}
QPushButton#SpinMinus:disabled, QPushButton#SpinPlus:disabled {{ background-color: {SURFACE_ALT}; border-color: {BORDER}; }}

QLabel#HourMinuteSep {{
    background: transparent; color: {TEXT_SUBTLE};
    font-size: 16pt; font-weight: 700;
}}

/* ================== Tabela ================== */
QTableWidget {{
    background-color: {SURFACE};
    color: {TEXT};
    border: none;
    gridline-color: transparent;
    selection-background-color: {ROW_SELECTED};
    selection-color: {TEXT};
}}
QTableWidget::item {{
    padding: 10px 10px;
    border: none;
    border-bottom: 1px solid {SURFACE_MUTED};
}}
QTableWidget::item:hover {{ background-color: {ROW_HOVER}; }}
QTableWidget::item:selected {{ background-color: {ROW_SELECTED}; color: {TEXT}; }}
QHeaderView {{ background-color: transparent; }}
QHeaderView::section {{
    background-color: {SURFACE_MUTED};
    color: {TEXT_MUTED};
    padding: 11px 10px;
    border: none;
    font-weight: 700;
    font-size: 8pt;
    letter-spacing: 0.7px;
}}
QHeaderView::section:first {{ border-top-left-radius: 10px; border-bottom-left-radius: 10px; }}
QHeaderView::section:last {{ border-top-right-radius: 10px; border-bottom-right-radius: 10px; }}
QTableCornerButton::section {{ background-color: {SURFACE_MUTED}; border: none; }}

/* ================== Scrollbars ================== */
QScrollBar:vertical {{ background: transparent; width: 11px; margin: 4px 2px 4px 0; }}
QScrollBar::handle:vertical {{ background: {BORDER_STRONG}; border-radius: 5px; min-height: 32px; }}
QScrollBar::handle:vertical:hover {{ background: {TEXT_SUBTLE}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QScrollBar:horizontal {{ background: transparent; height: 11px; margin: 0 4px 2px 4px; }}
QScrollBar::handle:horizontal {{ background: {BORDER_STRONG}; border-radius: 5px; min-width: 32px; }}
QScrollBar::handle:horizontal:hover {{ background: {TEXT_SUBTLE}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollArea {{ background-color: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background-color: transparent; }}

/* ================== Diálogos ================== */
QFrame#DialogHeader {{
    background-color: {SURFACE_ALT};
    border-bottom: 1px solid {BORDER};
}}
QLabel#DialogHeaderTitle {{
    color: {TEXT}; background: transparent; font-size: 11pt; font-weight: 700;
}}
QFrame#DialogContent {{ background-color: {SURFACE}; }}
QLabel#DialogTitle {{
    font-size: 16pt; font-weight: 800; color: {TEXT_STRONG}; background: transparent;
}}
QLabel#DialogSubtitle {{ font-size: 9pt; color: {TEXT_MUTED}; background: transparent; }}

/* ================== Estado vazio ================== */
QLabel#EmptyTitle {{
    color: {TEXT}; font-size: 12.5pt; font-weight: 700; background: transparent;
}}
QLabel#EmptySub {{
    color: {TEXT_MUTED}; font-size: 9.5pt; background: transparent;
}}

/* ================== Resumo anual ================== */
QLabel#AnnualHeaderCell {{
    color: {TEXT_MUTED}; font-size: 8pt; font-weight: 700; background: transparent;
    letter-spacing: 0.6px; padding: 8px 4px; border-bottom: 1px solid {BORDER};
}}
QLabel#AnnualCellMonth {{
    color: {TEXT}; font-size: 10pt; font-weight: 600; background: transparent; padding: 9px 4px;
}}
QLabel#AnnualCell {{ color: {TEXT}; font-size: 10pt; background: transparent; padding: 9px 4px; }}
QLabel#AnnualCellEmpty {{ color: {TEXT_SUBTLE}; font-size: 10pt; background: transparent; padding: 9px 4px; }}
"""


def build_stylesheet(assets_dir: Path) -> str:
    qss = _QSS_TEMPLATE.format(**theme.qss_tokens())
    check = assets_dir / "check.svg"
    chevron = assets_dir / "chevron-down.svg"
    qss = qss.replace("__CHECK_ICON__", check.as_posix() if check.exists() else "")
    qss = qss.replace("__CHEVRON_DOWN__", chevron.as_posix() if chevron.exists() else "")
    return qss
