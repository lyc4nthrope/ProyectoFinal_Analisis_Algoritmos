"""
Exporta el informe bibliométrico a PDF.
Plotly → PNG via kaleido; Matplotlib → PNG via savefig; combinación con fpdf2.
"""

# Importa io para crear buffers en memoria (evita escribir archivos temporales)
import io
# Importa Path para manejo de rutas
from pathlib import Path

# Importa plotly para manejar figuras interactivas
import plotly.graph_objects as go
# Importa pio para convertir figuras Plotly a PNG
import plotly.io as pio
# Importa FPDF para generar el archivo PDF página por página
from fpdf import FPDF
# Importa el tipo de figura de matplotlib para diferenciarlas de las Plotly
from matplotlib.figure import Figure as MplFigure

# Importa la raíz del proyecto para calcular la ruta de la carpeta de exportaciones
from src.config import PROJECT_ROOT

# Carpeta donde se guardan los PDFs generados
_EXPORTS_DIR = PROJECT_ROOT / "exports"
# Dimensiones de la página A4 en milímetros
_PAGE_W_MM = 210
_MARGIN_MM = 15
# Ancho útil de la página (descontando márgenes izquierdo y derecho)
_USABLE_W_MM = _PAGE_W_MM - 2 * _MARGIN_MM
# Rutas a las fuentes DejaVu que soportan caracteres Unicode (tildes, ñ, etc.)
_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _configure_fonts(pdf: FPDF) -> str:
    # Intenta cargar la fuente DejaVu (soporta Unicode completo)
    if Path(_FONT_PATH).exists() and Path(_FONT_BOLD_PATH).exists():
        pdf.add_font("DejaVu", "", _FONT_PATH)
        pdf.add_font("DejaVu", "B", _FONT_BOLD_PATH)
        return "DejaVu"
    # Si DejaVu no está disponible, usa Helvetica (fuente por defecto de fpdf2)
    return "Helvetica"


def _plotly_to_png(fig: go.Figure, width: int = 1100, height: int = 550) -> bytes:
    try:
        # Intenta convertir la figura Plotly a PNG usando kaleido
        return pio.to_image(fig, format="png", width=width, height=height, scale=2)
    except Exception:
        # Fallback: si kaleido no está disponible, muestra un placeholder con matplotlib
        import matplotlib.pyplot as plt
        mpl_fig, ax = plt.subplots(figsize=(11, 5.5))
        ax.text(
            0.5, 0.5,
            "Figura Plotly\n(kaleido no disponible en esta plataforma)",
            ha="center", va="center", fontsize=14, color="gray",
            transform=ax.transAxes,
        )
        ax.axis("off")
        # Convierte la figura matplotlib a bytes PNG
        buf = io.BytesIO()
        mpl_fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        plt.close(mpl_fig)
        buf.seek(0)
        return buf.read()


def _matplotlib_to_png(fig: MplFigure) -> bytes:
    # Convierte una figura matplotlib a bytes PNG usando un buffer en memoria
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    return buf.read()


def _add_figure_page(pdf: FPDF, title: str, image_bytes: bytes, font: str = "DejaVu") -> None:
    # Agrega una nueva página al PDF con el título centrado y la imagen debajo
    pdf.add_page()
    pdf.set_font(font, "B", 13)
    # Título centrado con salto de línea al final
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(3)
    # Inserta la imagen PNG ocupando todo el ancho útil de la página
    pdf.image(io.BytesIO(image_bytes), x=_MARGIN_MM, w=_USABLE_W_MM)


def _build_cover(pdf: FPDF, font: str = "DejaVu") -> None:
    # Agrega la portada del informe con título y subtítulos centrados
    pdf.add_page()
    pdf.set_font(font, "B", 22)
    pdf.ln(70)  # Baja 70mm para centrar verticalmente el título
    pdf.cell(0, 14, "Informe Bibliométrico", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font(font, "", 13)
    pdf.ln(4)
    pdf.cell(
        0, 8,
        "Generative Artificial Intelligence - Analisis de Literatura",
        new_x="LMARGIN", new_y="NEXT", align="C",
    )
    pdf.ln(6)
    pdf.set_font(font, "", 11)
    pdf.cell(
        0, 6,
        "Universidad del Quindio - Analisis de Algoritmos",
        new_x="LMARGIN", new_y="NEXT", align="C",
    )


def _add_note_page(pdf: FPDF, title: str, lines: list[str], font: str = "DejaVu") -> None:
    # Agrega una página de texto con título y líneas de contenido (notas metodológicas)
    pdf.add_page()
    pdf.set_font(font, "B", 13)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font(font, "", 11)
    # Usa multi_cell para que las líneas largas se ajusten automáticamente
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
    # Crea la carpeta de exportaciones si no existe
    _EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = _EXPORTS_DIR / filename

    # Inicializa el objeto PDF con salto de página automático
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=_MARGIN_MM)
    pdf.set_margins(_MARGIN_MM, _MARGIN_MM, _MARGIN_MM)
    # Configura las fuentes y obtiene el nombre de fuente disponible
    font = _configure_fonts(pdf)

    # Agrega la portada como primera página
    _build_cover(pdf, font)

    # Agrega páginas de notas metodológicas (si se proporcionaron)
    for title, lines in notes or []:
        _add_note_page(pdf, title, lines, font)

    # Agrega una página por cada figura: detecta si es Plotly o Matplotlib y convierte a PNG
    for title, fig in figures:
        image_bytes = (
            _matplotlib_to_png(fig) if isinstance(fig, MplFigure)
            else _plotly_to_png(fig)
        )
        _add_figure_page(pdf, title, image_bytes, font)

    # Escribe el PDF al disco y retorna la ruta
    pdf.output(str(output_path))
    return output_path
