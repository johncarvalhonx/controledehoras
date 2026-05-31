"""
Controle de Horas Extras
Aplicativo desktop para registro e cálculo de horas extras mensais.
"""
import sys
from pathlib import Path

from PySide6.QtCore import QLocale, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPalette
from PySide6.QtWidgets import QApplication

# Política de arredondamento HiDPI — precisa ser definida antes do QApplication
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)


def main() -> int:
    QApplication.setApplicationName("Controle de Horas Extras")
    QApplication.setOrganizationName("ControleHoras")
    QLocale.setDefault(QLocale(QLocale.Portuguese, QLocale.Brazil))

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Palette — força texto branco sobre o índigo nos itens selecionados de
    # QListView/QComboBox etc. (o delegate padrão usa palette, não QSS).
    from app import theme
    primary = QColor(theme.PRIMARY)
    palette = app.palette()
    palette.setColor(QPalette.Highlight, primary)
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.Active, QPalette.Highlight, primary)
    palette.setColor(QPalette.Active, QPalette.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.Inactive, QPalette.Highlight, primary)
    palette.setColor(QPalette.Inactive, QPalette.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor("#94A3B8"))
    palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(palette)

    # Caminho dos assets (compatível com PyInstaller onefile)
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    assets_dir = base_dir / "app" / "assets"

    # Carrega a fonte Inter embutida
    fonts_dir = assets_dir / "fonts"
    for weight in ("Regular", "Medium", "SemiBold", "Bold"):
        QFontDatabase.addApplicationFont(str(fonts_dir / f"Inter-{weight}.ttf"))
    app.setFont(QFont("Inter", 10))

    from app.styles import build_stylesheet
    app.setStyleSheet(build_stylesheet(assets_dir))

    icon_path = assets_dir / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    from app.views.main_window import MainWindow
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
