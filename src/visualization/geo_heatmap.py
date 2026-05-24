import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from matplotlib.figure import Figure as MplFigure

from src.visualization.geo_resolver import resolve_countries


def build_country_counts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resuelve el país del primer autor de cada artículo y
    devuelve un DataFrame con columnas [country, count].
    """
    dois = df["doi"].fillna("").tolist()
    country_map = resolve_countries(dois)

    df = df.copy()
    df["country"] = df["doi"].fillna("").apply(
        lambda doi: country_map.get(doi, "Unknown") if doi else "Unknown"
    )

    counts = (
        df[df["country"] != "Unknown"]
        .groupby("country")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    return counts


def build_heatmap_figure(country_counts: pd.DataFrame) -> go.Figure:
    fig = px.choropleth(
        country_counts,
        locations="country",
        locationmode="country names",
        color="count",
        color_continuous_scale="Reds",
        title="Distribución geográfica de publicaciones (primer autor)",
        labels={"count": "Publicaciones", "country": "País"},
    )
    fig.update_layout(
        coloraxis_colorbar={"title": "Publicaciones"},
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        height=500,
    )
    return fig


def build_heatmap_figure_mpl(country_counts: pd.DataFrame) -> MplFigure:
    top = country_counts.head(20).sort_values("count")
    fig, ax = plt.subplots(figsize=(10, max(4, len(top) * 0.4)))
    ax.barh(top["country"], top["count"], color="indianred")
    ax.set_xlabel("Publicaciones")
    ax.set_title("Distribución geográfica — top países (primer autor)")
    fig.tight_layout()
    return fig
