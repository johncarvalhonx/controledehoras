"""Camada de acesso ao banco SQLite."""
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from typing import Iterator

from .config import DATABASE_PATH, SALARIO_BASE, VALOR_HORA


@dataclass
class Registro:
    id: int
    data: date
    minutos: int
    motivo: str

    @property
    def ano(self) -> int:
        return self.data.year

    @property
    def mes(self) -> int:
        return self.data.month


class Database:
    def __init__(self, path=DATABASE_PATH):
        self.path = str(path)
        self._init_schema()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(
            self.path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._conn() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS registros (
                    id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    data    DATE    NOT NULL,
                    minutos INTEGER NOT NULL CHECK (minutos > 0),
                    motivo  TEXT    NOT NULL DEFAULT ''
                )
                """
            )
            c.execute(
                "CREATE INDEX IF NOT EXISTS idx_registros_data ON registros(data)"
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

    # ---------- Configurações (key/value) ----------
    def _get_setting(self, key: str, default: str | None = None) -> str | None:
        with self._conn() as c:
            row = c.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row is not None else default

    def _set_setting(self, key: str, value: str) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, str(value)),
            )

    def get_salario(self) -> float:
        v = self._get_setting("salario_base")
        try:
            return float(v) if v is not None else SALARIO_BASE
        except (TypeError, ValueError):
            return SALARIO_BASE

    def set_salario(self, value: float) -> None:
        self._set_setting("salario_base", f"{float(value):.2f}")

    def get_valor_hora(self) -> float:
        v = self._get_setting("valor_hora")
        try:
            return float(v) if v is not None else VALOR_HORA
        except (TypeError, ValueError):
            return VALOR_HORA

    def set_valor_hora(self, value: float) -> None:
        self._set_setting("valor_hora", f"{float(value):.2f}")

    # ---------- CRUD ----------
    def adicionar(self, data: date, minutos: int, motivo: str) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO registros (data, minutos, motivo) VALUES (?, ?, ?)",
                (data.isoformat(), minutos, motivo.strip()),
            )
            return cur.lastrowid

    def atualizar(self, registro_id: int, data: date, minutos: int, motivo: str) -> None:
        with self._conn() as c:
            c.execute(
                "UPDATE registros SET data = ?, minutos = ?, motivo = ? WHERE id = ?",
                (data.isoformat(), minutos, motivo.strip(), registro_id),
            )

    def excluir(self, registro_id: int) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM registros WHERE id = ?", (registro_id,))

    def listar_mes(self, ano: int, mes: int) -> list[Registro]:
        with self._conn() as c:
            inicio = date(ano, mes, 1).isoformat()
            if mes == 12:
                fim = date(ano + 1, 1, 1).isoformat()
            else:
                fim = date(ano, mes + 1, 1).isoformat()
            rows = c.execute(
                "SELECT id, data, minutos, motivo FROM registros "
                "WHERE data >= ? AND data < ? ORDER BY data ASC, id ASC",
                (inicio, fim),
            ).fetchall()
            return [self._row_to_registro(r) for r in rows]

    def total_minutos_mes(self, ano: int, mes: int) -> int:
        with self._conn() as c:
            inicio = date(ano, mes, 1).isoformat()
            if mes == 12:
                fim = date(ano + 1, 1, 1).isoformat()
            else:
                fim = date(ano, mes + 1, 1).isoformat()
            row = c.execute(
                "SELECT COALESCE(SUM(minutos), 0) AS t FROM registros "
                "WHERE data >= ? AND data < ?",
                (inicio, fim),
            ).fetchone()
            return int(row["t"])

    def totais_por_mes(self, ano: int) -> dict[int, int]:
        """Retorna {mes: minutos_totais} para o ano."""
        with self._conn() as c:
            inicio = date(ano, 1, 1).isoformat()
            fim = date(ano + 1, 1, 1).isoformat()
            rows = c.execute(
                "SELECT CAST(strftime('%m', data) AS INTEGER) AS mes, "
                "       COALESCE(SUM(minutos), 0) AS t "
                "FROM registros WHERE data >= ? AND data < ? "
                "GROUP BY mes",
                (inicio, fim),
            ).fetchall()
            resultado = {m: 0 for m in range(1, 13)}
            for r in rows:
                resultado[int(r["mes"])] = int(r["t"])
            return resultado

    def anos_com_registros(self) -> list[int]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT DISTINCT CAST(strftime('%Y', data) AS INTEGER) AS ano "
                "FROM registros ORDER BY ano DESC"
            ).fetchall()
            return [int(r["ano"]) for r in rows]

    @staticmethod
    def _row_to_registro(row: sqlite3.Row) -> Registro:
        data_val = row["data"]
        if isinstance(data_val, str):
            data_val = date.fromisoformat(data_val)
        return Registro(
            id=row["id"],
            data=data_val,
            minutos=row["minutos"],
            motivo=row["motivo"] or "",
        )
