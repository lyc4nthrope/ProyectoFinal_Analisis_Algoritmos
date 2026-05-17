import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


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
