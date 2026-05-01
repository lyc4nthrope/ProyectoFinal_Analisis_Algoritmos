import pandas as pd
import streamlit as st

from app.loader import load_corpus


def render() -> None:
    st.title("Corpus bibliográfico")
    df = load_corpus()

    years = pd.to_numeric(df["year"], errors="coerce").dropna().astype(int)
    journals = df["journal"].replace("", pd.NA).dropna()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Artículos únicos", len(df))
    col2.metric("Revistas distintas", int(journals.nunique()))
    col3.metric("Año más antiguo", int(years.min()) if len(years) > 0 else "—")
    col4.metric("Año más reciente", int(years.max()) if len(years) > 0 else "—")

    st.subheader("Todos los artículos")
    display = df[["title", "authors", "journal", "year", "doi"]].copy()
    display.columns = ["Título", "Autores", "Revista", "Año", "DOI"]
    st.dataframe(display, width="stretch", hide_index=True)
