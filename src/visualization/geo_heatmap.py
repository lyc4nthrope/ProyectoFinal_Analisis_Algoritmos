# Importa matplotlib para crear la versión estática (PNG) del mapa geográfico
import matplotlib.pyplot as plt
# Importa pandas para manipular el DataFrame de artículos
import pandas as pd
# Importa plotly express para el mapa coroplético interactivo
import plotly.express as px
# Importa plotly graph_objects para el tipo de retorno explícito
import plotly.graph_objects as go
# Importa el tipo de figura de matplotlib para el tipo de retorno
from matplotlib.figure import Figure as MplFigure

# Importa la función que resuelve el país de cada artículo consultando CrossRef
from src.visualization.geo_resolver import resolve_countries


def build_country_counts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resuelve el país del primer autor de cada artículo y
    devuelve un DataFrame con columnas [country, count].
    """
    # Extrae la lista de DOIs del corpus para consultarlos en CrossRef
    dois = df["doi"].fillna("").tolist()
    # Resuelve el país de cada DOI usando la caché local + CrossRef API
    country_map = resolve_countries(dois)

    df = df.copy()
    # Agrega la columna "country" mapeando cada DOI a su país resuelto
    df["country"] = df["doi"].fillna("").apply(
        lambda doi: country_map.get(doi, "Unknown") if doi else "Unknown"
    )

    # Agrupa por país y cuenta artículos, excluyendo los no resueltos
    counts = (
        df[df["country"] != "Unknown"]
        .groupby("country")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)  # Ordena de mayor a menor
    )
    return counts


def build_heatmap_figure(country_counts: pd.DataFrame) -> go.Figure:
    # Crea un mapa coroplético interactivo con Plotly: el color representa la cantidad de publicaciones
    fig = px.choropleth(
        country_counts,
        locations="country",          # Columna con nombres de países
        locationmode="country names", # Modo de geocodificación por nombre
        color="count",                # Columna que determina el color
        color_continuous_scale="Reds",# Escala de colores de blanco a rojo
        title="Distribución geográfica de publicaciones (primer autor)",
        labels={"count": "Publicaciones", "country": "País"},
    )
    fig.update_layout(
        coloraxis_colorbar={"title": "Publicaciones"},
        margin={"r": 0, "t": 50, "l": 0, "b": 0},  # Márgenes del mapa
        height=500,
    )
    return fig


def build_heatmap_figure_mpl(country_counts: pd.DataFrame) -> MplFigure:
    # Versión matplotlib del mapa: gráfico de barras horizontales con el top 20 de países
    top = country_counts.head(20).sort_values("count")  # Ordena ascendente para barh
    fig, ax = plt.subplots(figsize=(10, max(4, len(top) * 0.4)))
    # Dibuja las barras horizontales en color "indianred"
    ax.barh(top["country"], top["count"], color="indianred")
    ax.set_xlabel("Publicaciones")
    ax.set_title("Distribución geográfica — top países (primer autor)")
    fig.tight_layout()
    return fig
