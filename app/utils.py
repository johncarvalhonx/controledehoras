"""Helpers de formatação (BRL, datas, horas)."""
from datetime import date


def format_valor(value: float) -> str:
    """Formata só o número no padrão brasileiro: 1234.5 -> '1.234,50' (sem R$)."""
    negativo = value < 0
    value = abs(value)
    inteiro, dec = f"{value:.2f}".split(".")
    inteiro_formatado = ""
    for i, ch in enumerate(reversed(inteiro)):
        if i and i % 3 == 0:
            inteiro_formatado = "." + inteiro_formatado
        inteiro_formatado = ch + inteiro_formatado
    sinal = "-" if negativo else ""
    return f"{sinal}{inteiro_formatado},{dec}"


def format_brl(value: float) -> str:
    """Formata um número como moeda brasileira: 1234.5 -> 'R$ 1.234,50'."""
    negativo = value < 0
    return f"{'-' if negativo else ''}R$ {format_valor(abs(value))}"


def format_date_br(d: date) -> str:
    """Formata data como 28/05/2026."""
    return d.strftime("%d/%m/%Y")


def minutes_to_hhmm(minutes: int) -> str:
    """Converte minutos totais em string 'HH:MM' (suporta valores grandes)."""
    if minutes < 0:
        return "-" + minutes_to_hhmm(-minutes)
    h, m = divmod(int(minutes), 60)
    return f"{h:02d}:{m:02d}"


def minutes_to_decimal_hours(minutes: int) -> float:
    """Converte minutos em horas decimais (90 -> 1.5)."""
    return minutes / 60.0


def hhmm_to_minutes(hhmm: str) -> int:
    """Converte 'HH:MM' em minutos totais. Aceita também 'H:MM'."""
    parts = hhmm.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Formato inválido: {hhmm}")
    h, m = int(parts[0]), int(parts[1])
    return h * 60 + m


def gerar_opcoes_hhmm(min_minutos: int = 30, max_minutos: int = 12 * 60,
                      passo: int = 30) -> list[str]:
    """Gera lista de strings HH:MM em intervalos regulares."""
    opcoes = []
    m = min_minutos
    while m <= max_minutos:
        opcoes.append(minutes_to_hhmm(m))
        m += passo
    return opcoes
