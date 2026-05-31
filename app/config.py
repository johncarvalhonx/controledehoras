"""Configurações fixas do aplicativo."""
from pathlib import Path

# Valores financeiros
SALARIO_BASE = 7150.00
VALOR_HORA = 42.55

# Caminho do banco — fica em %APPDATA%/ControleHoras/horas.db no Windows
def _data_dir() -> Path:
    import os
    base = os.environ.get("APPDATA")
    if base:
        path = Path(base) / "ControleHoras"
    else:
        path = Path.home() / ".controle_horas"
    path.mkdir(parents=True, exist_ok=True)
    return path


DATABASE_PATH = _data_dir() / "horas.db"

MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril",
    "Maio", "Junho", "Julho", "Agosto",
    "Setembro", "Outubro", "Novembro", "Dezembro",
]

MESES_PT_CURTO = [
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez",
]
