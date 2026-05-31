"""Exportação do formulário de pedido de NF.

O documento-modelo (``app/assets/nf_template.doc``) é um .doc binário do Word
que contém o valor-modelo ``7.235,10`` em uma célula de tabela. Na exportação,
abrimos o modelo via automação do Word (pywin32), trocamos esse valor pelo
valor final do mês e salvamos uma cópia (.doc, .docx ou .pdf) — preservando
todo o restante do documento.

Observação: requer Microsoft Word instalado + pywin32 (Windows).
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QThread, Signal

# Valor-modelo presente no documento (será substituído na exportação)
NF_PLACEHOLDER = "7.235,10"


class NFExportError(Exception):
    """Erro tratável de exportação (mensagem amigável para o usuário)."""


def default_template_path() -> Path:
    """Caminho do modelo embarcado (funciona em dev e no .exe via _MEIPASS)."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / "app" / "assets" / "nf_template.doc"


def _clean_cell_text(text: str) -> str:
    return text.replace("\x07", "").replace("\r", "").replace("\a", "").strip()


def _aplicar_valor(doc, placeholder: str, new_value: str) -> bool:
    """Substitui o valor-modelo no documento aberto. Retorna True se aplicou."""
    aplicado = False

    # 1) Procura em células de tabela (caso do modelo atual) e seta o texto direto
    for ti in range(1, doc.Tables.Count + 1):
        tb = doc.Tables.Item(ti)
        for ri in range(1, tb.Rows.Count + 1):
            try:
                row = tb.Rows.Item(ri)
            except Exception:
                continue
            for ci in range(1, row.Cells.Count + 1):
                try:
                    cell = row.Cells.Item(ci)
                except Exception:
                    continue
                if placeholder in _clean_cell_text(cell.Range.Text):
                    rng = cell.Range
                    rng.End = rng.End - 1  # não inclui a marca de fim de célula
                    rng.Text = new_value
                    aplicado = True

    # 2) Fallback: localizar no corpo e setar o texto do range encontrado
    if not aplicado:
        rng = doc.Content
        find = rng.Find
        find.ClearFormatting()
        find.Text = placeholder
        if find.Execute():
            rng.Text = new_value
            aplicado = True

    return aplicado


def replace_value_in_doc(
    template_path: str | Path,
    out_path: str | Path,
    new_value: str,
    placeholder: str = NF_PLACEHOLDER,
) -> None:
    """Abre o modelo, troca o valor e salva em out_path (.doc/.docx/.pdf).

    Levanta NFExportError com mensagem amigável em caso de problema conhecido.
    """
    template_path = Path(template_path)
    out_path = Path(out_path)
    if not template_path.exists():
        raise NFExportError(
            "Modelo da NF não encontrado. Reinstale o aplicativo."
        )

    try:
        import pythoncom  # noqa
        import win32com.client as win32
    except ImportError:
        raise NFExportError(
            "O recurso de exportação requer o pacote 'pywin32'.\n"
            "Instale com: pip install pywin32"
        )

    pythoncom.CoInitialize()
    word = None
    doc = None
    try:
        try:
            word = win32.DispatchEx("Word.Application")
        except Exception:
            raise NFExportError(
                "Não foi possível iniciar o Microsoft Word.\n"
                "Verifique se o Word está instalado neste computador."
            )
        word.Visible = False
        try:
            word.DisplayAlerts = 0
        except Exception:
            pass

        doc = word.Documents.Open(str(template_path), ReadOnly=False)
        aplicado = _aplicar_valor(doc, placeholder, new_value)
        if not aplicado:
            raise NFExportError(
                f"Não encontrei o valor-modelo ({placeholder}) no documento."
            )

        ext = out_path.suffix.lower()
        out_str = str(out_path)
        if ext == ".pdf":
            doc.ExportAsFixedFormat(out_str, 17)  # wdExportFormatPDF
        elif ext == ".docx":
            doc.SaveAs(out_str, 16)               # wdFormatDocumentDefault (.docx)
        else:
            doc.SaveAs(out_str, 0)                # wdFormatDocument (.doc)
        doc.Close(False)
        doc = None
    finally:
        try:
            if doc is not None:
                doc.Close(False)
        except Exception:
            pass
        try:
            if word is not None:
                word.Quit()
        except Exception:
            pass
        pythoncom.CoUninitialize()


class NFExportWorker(QThread):
    """Executa a exportação em uma thread (Word pode levar alguns segundos)."""

    succeeded = Signal(str)   # caminho do arquivo gerado
    failed = Signal(str)      # mensagem de erro amigável

    def __init__(self, template_path, out_path, new_value,
                 placeholder: str = NF_PLACEHOLDER, parent=None):
        super().__init__(parent)
        self._template = template_path
        self._out = str(out_path)
        self._value = new_value
        self._placeholder = placeholder

    def run(self) -> None:
        try:
            replace_value_in_doc(
                self._template, self._out, self._value, self._placeholder
            )
            self.succeeded.emit(self._out)
        except NFExportError as e:
            self.failed.emit(str(e))
        except Exception as e:  # qualquer falha inesperada do COM
            self.failed.emit(f"Falha ao exportar a NF: {e}")
