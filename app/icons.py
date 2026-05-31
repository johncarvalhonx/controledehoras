"""Ícones vetoriais (estilo Lucide) renderizados via QtSvg — nítidos em qualquer DPI.

Uso:
    from app.icons import icon, pixmap
    botao.setIcon(icon("plus", "#FFFFFF", 18))
    label.setPixmap(pixmap("clock", theme.PRIMARY, 22))

Os ícones são paths de contorno (stroke), coloridos dinamicamente — a cor é
injetada no markup SVG antes de renderizar, então a mesma definição serve para
qualquer cor/tamanho.
"""
from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# ---------------------------------------------------------------------
#  Registro de ícones — apenas o conteúdo interno do <svg> (viewBox 24x24)
# ---------------------------------------------------------------------
_ICONS: dict[str, str] = {
    # navegação / telas
    "calendar": '<path d="M8 2v4"/><path d="M16 2v4"/>'
                '<rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>',
    "calendar-days": '<path d="M8 2v4"/><path d="M16 2v4"/>'
                     '<rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>'
                     '<path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/>'
                     '<path d="M8 18h.01"/><path d="M12 18h.01"/>',
    "bar-chart": '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    "calculator": '<rect width="16" height="20" x="4" y="2" rx="2"/>'
                  '<line x1="8" x2="16" y1="6" y2="6"/><line x1="16" x2="16" y1="14" y2="18"/>'
                  '<path d="M16 10h.01"/><path d="M12 10h.01"/><path d="M8 10h.01"/>'
                  '<path d="M12 14h.01"/><path d="M8 14h.01"/><path d="M12 18h.01"/><path d="M8 18h.01"/>',
    # métricas
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "wallet": '<path d="M20 12V8H6a2 2 0 0 1-2-2c0-1.1.9-2 2-2h12v4"/>'
              '<path d="M4 6v12c0 1.1.9 2 2 2h14v-4"/>'
              '<path d="M18 12a2 2 0 0 0-2 2c0 1.1.9 2 2 2h4v-4h-4z"/>',
    "trending-up": '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>'
                   '<polyline points="16 7 22 7 22 13"/>',
    "coins": '<circle cx="8" cy="8" r="6"/>'
             '<path d="M18.09 10.37A6 6 0 1 1 10.34 18"/>'
             '<path d="M7 6h1v4"/><path d="m16.71 13.88.7.71-2.82 2.82"/>',
    "receipt": '<path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1-2-1Z"/>'
               '<path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"/><path d="M12 17.5v-11"/>',
    "gauge": '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
    "piggy-bank": '<path d="M19 5c-1.5 0-2.8 1.4-3 2-3.5-1.5-11-.3-11 5 0 1.8 0 3 2 4.5V20h4v-2h3v2h4v-4c1-.5 1.7-1 2-2h2v-4h-2c0-1-.5-1.5-1-2V5z"/>'
                  '<path d="M2 9v1c0 1.1.9 2 2 2h1"/><path d="M16 11h.01"/>',
    # ações
    "plus": '<path d="M5 12h14"/><path d="M12 5v14"/>',
    "minus": '<path d="M5 12h14"/>',
    "pencil": '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "trash": '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>'
             '<path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>'
             '<line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/>',
    "rotate-ccw": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
    "corner-down-left": '<polyline points="9 10 4 15 9 20"/><path d="M20 4v7a4 4 0 0 1-4 4H4"/>',
    "save": '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>'
            '<polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>',
    # chevrons / direção
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "chevron-left": '<path d="m15 18-6-6 6-6"/>',
    "chevron-right": '<path d="m9 18 6-6-6-6"/>',
    # feedback
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "check-circle": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "alert-triangle": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>'
                      '<line x1="12" x2="12" y1="9" y2="13"/><line x1="12" x2="12.01" y1="17" y2="17"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    # configurações
    "settings": '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0'
                'l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51'
                'a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0'
                'l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25'
                'a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74'
                'v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08'
                'a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
    "sliders": '<line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/>'
               '<line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/>'
               '<line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/>'
               '<line x1="2" x2="6" y1="14" y2="14"/><line x1="10" x2="14" y1="8" y2="8"/>'
               '<line x1="18" x2="22" y1="16" y2="16"/>',
    "banknote": '<rect width="20" height="12" x="2" y="6" rx="2"/><circle cx="12" cy="12" r="2"/>'
                '<path d="M6 12h.01M18 12h.01"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
                '<polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>',
    "file-text": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>'
                 '<path d="M14 2v5h5"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>',
}


def _markup(name: str, color: str, stroke: float) -> bytes:
    body = _ICONS.get(name)
    if body is None:
        raise KeyError(f"ícone desconhecido: {name!r}")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="{stroke}" '
        f'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    ).encode("utf-8")


def _dpr() -> float:
    app = QGuiApplication.instance()
    if app is not None:
        screen = app.primaryScreen()
        if screen is not None:
            return max(1.0, float(screen.devicePixelRatio()))
    return 2.0


@lru_cache(maxsize=512)
def _pixmap_cached(name: str, color: str, size: int, stroke: float, dpr_x100: int) -> QPixmap:
    dpr = dpr_x100 / 100.0
    renderer = QSvgRenderer(QByteArray(_markup(name, color, stroke)))
    px = max(1, int(round(size * dpr)))
    pm = QPixmap(px, px)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    renderer.render(p)
    p.end()
    pm.setDevicePixelRatio(dpr)
    return pm


def pixmap(name: str, color: str = "#0F172A", size: int = 20, stroke: float = 2.0) -> QPixmap:
    """QPixmap nítido (escala pelo DPR atual). Resultado é cacheado."""
    dpr_x100 = int(round(_dpr() * 100))
    return _pixmap_cached(name, color, int(size), float(stroke), dpr_x100)


def icon(name: str, color: str = "#0F172A", size: int = 20, stroke: float = 2.0) -> QIcon:
    return QIcon(pixmap(name, color, size, stroke))


def has(name: str) -> bool:
    return name in _ICONS
