"""
Exporta el informe bibliométrico a PDF.
Plotly → PNG via kaleido; Matplotlib → PNG via savefig; combinación con fpdf2.
"""

import io
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio
from fpdf import FPDF
from matplotlib.figure import Figure as MplFigure

from src.config import PROJECT_ROOT

_EXPORTS_DIR = PROJECT_ROOT / "exports"
_PAGE_W_MM = 210
_MARGIN_MM = 15
_USABLE_W_MM = _PAGE_W_MM - 2 * _MARGIN_MM
_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _configure_fonts(pdf: FPDF) -> None:
    pdf.add_font("DejaVu", "", _FONT_PATH)
    pdf.add_font("DejaVu", "B", _FONT_BOLD_PATH)


def _plotly_to_png(fig: go.Figure, width: int = 1100, height: int = 550) -> bytes:
    return pio.to_image(fig, format="png", width=width, height=height, scale=2)


def _matplotlib_to_png(fig: MplFigure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    return buf.read()


def _add_figure_page(pdf: FPDF, title: str, image_bytes: bytes) -> None:
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 13)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(3)
    pdf.image(io.BytesIO(image_bytes), x=_MARGIN_MM, w=_USABLE_W_MM)


def _build_cover(pdf: FPDF) -> None:
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 22)
    pdf.ln(70)
    pdf.cell(0, 14, "Informe Bibliométrico", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("DejaVu", "", 13)
    pdf.ln(4)
    pdf.cell(
        0, 8,
        "Generative Artificial Intelligence — Análisis de Literatura",
        new_x="LMARGIN", new_y="NEXT", align="C",
    )
    pdf.ln(6)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(
        0, 6,
        "Universidad del Quindío — Análisis de Algoritmos",
        new_x="LMARGIN", new_y="NEXT", align="C",
    )


def _add_note_page(pdf: FPDF, title: str, lines: list[str]) -> None:
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 13)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("DejaVu", "", 11)
    for line in lines:
        pdf.multi_cell(0, 6, line)
        pdf.ln(1)


def export_report(
    figures: list[tuple[str, go.Figure | MplFigure]],
    filename: str = "informe_bibliometrico.pdf",
    notes: list[tuple[str, list[str]]] | None = None,
) -> Path:
    """
    Genera un PDF con portada y una página por figura.

    Args:
        figures: lista de (título, figura) donde figura es Plotly o Matplotlib.
        filename: nombre del archivo de salida en exports/.
        notes: páginas de texto opcionales con notas metodológicas.

    Returns:
        Path al PDF generado.
    """
    _EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = _EXPORTS_DIR / filename

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=_MARGIN_MM)
    pdf.set_margins(_MARGIN_MM, _MARGIN_MM, _MARGIN_MM)
    _configure_fonts(pdf)

    _build_cover(pdf)

    for title, lines in notes or []:
        _add_note_page(pdf, title, lines)

    for title, fig in figures:
        image_bytes = (
            _matplotlib_to_png(fig) if isinstance(fig, MplFigure)
            else _plotly_to_png(fig)
        )
        _add_figure_page(pdf, title, image_bytes)

    pdf.output(str(output_path))
    return output_path
