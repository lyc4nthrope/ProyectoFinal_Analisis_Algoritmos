# Importa matplotlib para las versiones estáticas (PNG) de las gráficas
import matplotlib.pyplot as plt
# Importa pandas para manipular los DataFrames de publicaciones
import pandas as pd
# Importa plotly express para las versiones interactivas de las gráficas
import plotly.express as px
# Importa plotly graph_objects para el tipo de retorno de las figuras Plotly
import plotly.graph_objects as go
# Importa el tipo de figura de matplotlib para el tipo de retorno
from matplotlib.figure import Figure as MplFigure


def _clean_year(value: object) -> int | None:
    try:
        # Convierte el valor a float primero para manejar "2023.0", luego a int
        year = int(float(value))
        # Solo acepta años en rango razonable (1990-2030); descarta valores inválidos
        return year if 1990 <= year <= 2030 else None
    except (ValueError, TypeError):
        return None


def build_year_timeline(df: pd.DataFrame) -> go.Figure:
    # Extrae y limpia los años; elimina los NaN (años inválidos)
    years = df["year"].apply(_clean_year).dropna().astype(int)
    # Cuenta publicaciones por año y ordena cronológicamente
    counts = years.value_counts().sort_index().reset_index()
    counts.columns = ["year", "count"]

    # Crea un gráfico de barras interactivo: X=año, Y=número de publicaciones
    fig = px.bar(
        counts,
        x="year",
        y="count",
        title="Publicaciones por año",
        labels={"year": "Año", "count": "Número de publicaciones"},
        color="count",                    # El color de la barra varía según la cantidad
        color_continuous_scale="Blues",   # Escala de azules
    )
    fig.update_layout(
        xaxis={"dtick": 1, "title": "Año"},   # Una marca por año en el eje X
        yaxis={"title": "Publicaciones"},
        coloraxis_showscale=False,             # Oculta la barra de colores (redundante)
        height=400,
    )
    return fig


def build_journal_timeline(df: pd.DataFrame) -> go.Figure:
    valid = df.copy()
    # Limpia los años y elimina filas sin año o sin revista
    valid["year"] = valid["year"].apply(_clean_year)
    valid = valid.dropna(subset=["year", "journal"])
    valid["year"] = valid["year"].astype(int)
    # Filtra filas donde la revista está vacía
    valid = valid[valid["journal"].str.strip() != ""]

    # Agrupa por año y revista para contar publicaciones de cada revista por año
    counts = (
        valid.groupby(["year", "journal"])
        .size()
        .reset_index(name="count")
        .sort_values("year")
    )

    # Selecciona solo las top 10 revistas con más publicaciones totales
    top_journals = (
        counts.groupby("journal")["count"].sum()
        .nlargest(10)
        .index.tolist()
    )
    counts = counts[counts["journal"].isin(top_journals)]

    # Crea un gráfico de líneas: cada línea es una revista, X=año, Y=publicaciones
    fig = px.line(
        counts,
        x="year",
        y="count",
        color="journal",              # Una línea de color diferente por revista
        title="Publicaciones por año y revista (top 10 revistas)",
        labels={"year": "Año", "count": "Publicaciones", "journal": "Revista"},
        markers=True,                 # Muestra puntos en cada año
    )
    fig.update_layout(
        xaxis={"dtick": 1},
        legend={"title": "Revista", "font": {"size": 9}},
        height=500,
    )
    return fig


def build_year_timeline_mpl(df: pd.DataFrame) -> MplFigure:
    # Versión matplotlib de la gráfica de barras por año (para exportar a PDF)
    years = df["year"].apply(_clean_year).dropna().astype(int)
    counts = years.value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(11, 4))
    ax.bar(counts.index, counts.values, color="steelblue")
    ax.set_xlabel("Año")
    ax.set_ylabel("Publicaciones")
    ax.set_title("Publicaciones por año")
    # Muestra todos los años como marcas en el eje X
    ax.set_xticks(counts.index)
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig


def build_journal_timeline_mpl(df: pd.DataFrame) -> MplFigure:
    # Versión matplotlib del gráfico de líneas por revista (para exportar a PDF)
    valid = df.copy()
    valid["year"] = valid["year"].apply(_clean_year)
    valid = valid.dropna(subset=["year", "journal"])
    valid["year"] = valid["year"].astype(int)
    valid = valid[valid["journal"].str.strip() != ""]

    counts = (
        valid.groupby(["year", "journal"])
        .size()
        .reset_index(name="count")
        .sort_values("year")
    )
    # Selecciona top 10 revistas por total de publicaciones
    top_journals = (
        counts.groupby("journal")["count"].sum()
        .nlargest(10)
        .index.tolist()
    )
    counts = counts[counts["journal"].isin(top_journals)]

    fig, ax = plt.subplots(figsize=(12, 5))
    # Dibuja una línea por revista con sus datos ordenados por año
    for journal in top_journals:
        jdata = counts[counts["journal"] == journal].sort_values("year")
        # Trunca el nombre de la revista a 30 caracteres para la leyenda
        ax.plot(jdata["year"], jdata["count"], marker="o", label=journal[:30])
    ax.set_xlabel("Año")
    ax.set_ylabel("Publicaciones")
    ax.set_title("Publicaciones por año y revista (top 10)")
    # La leyenda va fuera del gráfico para no tapar las líneas
    ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    fig.tight_layout()
    return fig
