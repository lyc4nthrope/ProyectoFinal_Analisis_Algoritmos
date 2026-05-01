import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from wordcloud import WordCloud

from src.processing.text_preprocessing import tokenize


def _build_frequency_map(abstracts: list[str], keywords: list[str]) -> dict[str, int]:
    freq: dict[str, int] = {}
    for text in abstracts + keywords:
        for token in tokenize(text):
            freq[token] = freq.get(token, 0) + 1
    return freq


def build_wordcloud_figure(abstracts: list[str], keywords: list[str]) -> Figure:
    freq = _build_frequency_map(abstracts, keywords)

    wc = WordCloud(
        width=1200,
        height=600,
        background_color="white",
        colormap="viridis",
        max_words=100,
        prefer_horizontal=0.8,
    ).generate_from_frequencies(freq)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(
        "Nube de palabras — términos más frecuentes en abstracts y keywords",
        fontsize=13,
        pad=12,
    )
    plt.tight_layout()
    return fig
