# Agrega la raíz del proyecto al path de Python para que los imports de src/ funcionen
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configura matplotlib para modo no interactivo (sin ventana GUI)
# Debe hacerse ANTES de importar cualquier módulo que use matplotlib
import matplotlib
matplotlib.use("Agg")

# Importa Streamlit como framework principal de la aplicación web
import streamlit as st
# Importa el menú lateral con iconos de Bootstrap Icons
from streamlit_option_menu import option_menu

# Configura la página: título en el browser y layout ancho
st.set_page_config(
    page_title="Bibliometría GenAI",
    layout="wide",
)

# Importa todas las vistas de la aplicación (cada una tiene una función render())
from app.views import api_search, clustering, concepts, export_pdf, overview, similarity, upload_files, visualization

# Diccionario que mapea nombre de página → módulo de vista
_PAGES = {
    "Inicio": overview,
    "Cargar archivos": upload_files,
    "Búsqueda API": api_search,
    "Similitud": similarity,
    "Conceptos": concepts,
    "Clustering": clustering,
    "Visualizaciones": visualization,
    "Exportar PDF": export_pdf,
}

# Iconos de Bootstrap Icons correspondientes a cada página (en el mismo orden)
_ICONS = [
    "house",
    "cloud-upload",
    "search",
    "diagram-2",
    "lightbulb",
    "diagram-3",
    "bar-chart-line",
    "file-earmark-pdf",
]

# Construye el sidebar con el menú de navegación
with st.sidebar:
    # Título y créditos del proyecto
    st.title("Bibliometría GenAI")
    st.caption(
        "Universidad del Quindío  \n"
        "Análisis de Algoritmos  \n\n"
        "Daniel Stiven Perez Cordoba  \n"
        "Cristhian Eduardo Osorio Restrepo"
    )
    st.divider()
    # Menú de navegación con iconos; retorna el nombre de la página seleccionada
    page_name = option_menu(
        menu_title=None,
        options=list(_PAGES.keys()),
        icons=_ICONS,
        default_index=0,
        styles={
            "container": {"padding": "0", "margin-top": "-20px", "background-color": "transparent"},
            "nav-link": {"font-size": "0.9rem", "text-align": "left", "margin": "1px 0"},
            "nav-link-selected": {"background-color": "rgba(255,255,255,0.12)", "font-weight": "600"},
        },
    )

# Llama a la función render() de la vista activa según lo que seleccionó el usuario
_PAGES[page_name].render()
