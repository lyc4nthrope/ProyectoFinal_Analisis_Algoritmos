import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.visualization.geo_resolver import resolve_countries


def build_country_counts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resuelve el país del primer autor de cada artículo y
    devuelve un DataFrame con columnas [country, count].
    """
    dois = df["doi"].fillna("").tolist()
    country_map = resolve_countries(dois)

    countries = []
    for _, row in df.iterrows():
        doi = row.get("doi", "")
        countries.append(country_map.get(doi, "Unknown") if doi else "Unknown")

    df = df.copy()
    df["country"] = countries

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
