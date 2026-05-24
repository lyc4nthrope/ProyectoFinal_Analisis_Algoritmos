import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from matplotlib.figure import Figure as MplFigure


def _clean_year(value: object) -> int | None:
    try:
        year = int(float(value))
        return year if 1990 <= year <= 2030 else None
    except (ValueError, TypeError):
        return None


def build_year_timeline(df: pd.DataFrame) -> go.Figure:
    years = df["year"].apply(_clean_year).dropna().astype(int)
    counts = years.value_counts().sort_index().reset_index()
    counts.columns = ["year", "count"]

    fig = px.bar(
        counts,
        x="year",
        y="count",
        title="Publicaciones por año",
        labels={"year": "Año", "count": "Número de publicaciones"},
        color="count",
        color_continuous_scale="Blues",
    )
    fig.update_layout(
        xaxis={"dtick": 1, "title": "Año"},
        yaxis={"title": "Publicaciones"},
        coloraxis_showscale=False,
        height=400,
    )
    return fig


def build_journal_timeline(df: pd.DataFrame) -> go.Figure:
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

    top_journals = (
        counts.groupby("journal")["count"].sum()
        .nlargest(10)
        .index.tolist()
    )
    counts = counts[counts["journal"].isin(top_journals)]

    fig = px.line(
        counts,
        x="year",
        y="count",
        color="journal",
        title="Publicaciones por año y revista (top 10 revistas)",
        labels={"year": "Año", "count": "Publicaciones", "journal": "Revista"},
        markers=True,
    )
    fig.update_layout(
        xaxis={"dtick": 1},
        legend={"title": "Revista", "font": {"size": 9}},
        height=500,
    )
    return fig


def build_year_timeline_mpl(df: pd.DataFrame) -> MplFigure:
    years = df["year"].apply(_clean_year).dropna().astype(int)
    counts = years.value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(11, 4))
    ax.bar(counts.index, counts.values, color="steelblue")
    ax.set_xlabel("Año")
    ax.set_ylabel("Publicaciones")
    ax.set_title("Publicaciones por año")
    ax.set_xticks(counts.index)
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig


def build_journal_timeline_mpl(df: pd.DataFrame) -> MplFigure:
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
    top_journals = (
        counts.groupby("journal")["count"].sum()
        .nlargest(10)
        .index.tolist()
    )
    counts = counts[counts["journal"].isin(top_journals)]

    fig, ax = plt.subplots(figsize=(12, 5))
    for journal in top_journals:
        jdata = counts[counts["journal"] == journal].sort_values("year")
        ax.plot(jdata["year"], jdata["count"], marker="o", label=journal[:30])
    ax.set_xlabel("Año")
    ax.set_ylabel("Publicaciones")
    ax.set_title("Publicaciones por año y revista (top 10)")
    ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    fig.tight_layout()
    return fig
