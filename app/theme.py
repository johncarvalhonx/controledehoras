"""Design tokens — fonte única de verdade para cores, raios, espaçamentos e tempos.

Tanto o QSS (app/styles.py) quanto os componentes pintados à mão (cards, nav,
gráfico, etc.) consomem estas constantes, garantindo identidade visual coesa.
"""

# =====================================================================
#  Cores de marca
# =====================================================================
PRIMARY        = "#4F46E5"   # indigo-600
PRIMARY_HOVER  = "#4338CA"   # indigo-700
PRIMARY_PRESS  = "#3730A3"   # indigo-800
PRIMARY_GRAD_1 = "#6366F1"   # topo do gradiente (indigo-500)
PRIMARY_GRAD_2 = "#4F46E5"   # base do gradiente (indigo-600)
PRIMARY_GRAD_3 = "#7C3AED"   # fim do gradiente de marca (violet-600)
PRIMARY_SOFT   = "#EEF2FF"   # indigo-50
PRIMARY_SOFT_2 = "#E0E7FF"   # indigo-100
PRIMARY_TINT   = "#C7D2FE"   # indigo-200

# Acento — valores monetários / positivo
ACCENT         = "#10B981"   # emerald-500
ACCENT_DARK    = "#059669"   # emerald-600
ACCENT_SOFT    = "#ECFDF5"   # emerald-50

# Secundária — variação de ícones / gráfico
VIOLET         = "#8B5CF6"
VIOLET_DARK    = "#7C3AED"
VIOLET_SOFT    = "#F5F3FF"

# Estados
DANGER         = "#EF4444"
DANGER_DARK    = "#DC2626"
DANGER_PRESS   = "#B91C1C"
DANGER_SOFT    = "#FEF2F2"
WARNING        = "#F59E0B"
WARNING_SOFT   = "#FFFBEB"

# =====================================================================
#  Neutros / superfícies
# =====================================================================
APP_BG         = "#F4F6FB"   # canvas do app (atrás dos cards)
SURFACE        = "#FFFFFF"   # cards / inputs
SURFACE_ALT    = "#F8FAFC"   # variação suave
SURFACE_MUTED  = "#F1F5F9"   # zebra / headers

# Chrome escuro (title bar + navegação)
CHROME_TOP     = "#1A2236"   # topo do gradiente da barra de título
CHROME_BOT     = "#0E1424"   # base
NAV_BG         = "#0E1424"
NAV_HOVER      = "#1B2540"

# Texto sobre claro
TEXT           = "#0F172A"
TEXT_STRONG    = "#020617"
TEXT_MUTED     = "#64748B"
TEXT_SUBTLE    = "#94A3B8"
TEXT_FAINT     = "#CBD5E1"

# Texto sobre escuro
ON_DARK        = "#E5E9F2"
ON_DARK_MUTED  = "#94A3B8"
ON_DARK_FAINT  = "#475569"

# Bordas
BORDER         = "#E6EAF1"
BORDER_STRONG  = "#D5DCE7"
BORDER_FOCUS   = PRIMARY

# Linhas / hover de tabela
ROW_HOVER      = "#F6F8FD"
ROW_SELECTED   = "#EEF2FF"
ROW_FLASH      = "#DDE3FF"   # destaque temporário ao inserir

# =====================================================================
#  Geometria / tempo
# =====================================================================
RADIUS_SM   = 8
RADIUS      = 12
RADIUS_LG   = 16
RADIUS_XL   = 20
RADIUS_PILL = 999

DUR_FAST   = 140
DUR_BASE   = 220
DUR_SLOW   = 320
DUR_SLOWER = 460

FONT_FAMILY = "Inter"


# =====================================================================
#  Tonalidades para os ícones dos cards (chip colorido + ícone)
# =====================================================================
TONES = {
    "primary": {"fg": PRIMARY,     "bg": PRIMARY_SOFT,  "bg2": PRIMARY_SOFT_2},
    "accent":  {"fg": ACCENT_DARK, "bg": ACCENT_SOFT,   "bg2": "#D1FAE5"},
    "violet":  {"fg": VIOLET_DARK, "bg": VIOLET_SOFT,   "bg2": "#EDE9FE"},
    "neutral": {"fg": "#475569",   "bg": SURFACE_MUTED, "bg2": "#E2E8F0"},
}


def qss_tokens() -> dict:
    """Dicionário usado no .format() do template QSS em styles.py."""
    return {k: v for k, v in globals().items() if k.isupper() and isinstance(v, str)}
