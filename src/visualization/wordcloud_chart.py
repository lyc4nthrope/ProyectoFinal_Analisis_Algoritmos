# Importa matplotlib para crear la figura donde se muestra la nube de palabras
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
# Importa WordCloud para generar la nube de palabras a partir de frecuencias
from wordcloud import WordCloud

# Importa la función de tokenización para limpiar los textos antes de contar
from src.processing.text_preprocessing import tokenize


def _build_frequency_map(abstracts: list[str], keywords: list[str]) -> dict[str, int]:
    # Construye un mapa de frecuencias: {palabra: cantidad_de_apariciones}
    freq: dict[str, int] = {}
    # Procesa tanto los abstracts como las keywords juntos
    for text in abstracts + keywords:
        # Tokeniza el texto (normaliza, divide en palabras, elimina stopwords)
        for token in tokenize(text):
            freq[token] = freq.get(token, 0) + 1
    return freq


def build_wordcloud_figure(abstracts: list[str], keywords: list[str]) -> Figure:
    # Calcula el mapa de frecuencias de todos los abstracts y keywords
    freq = _build_frequency_map(abstracts, keywords)

    # Configura y genera la nube de palabras con las frecuencias calculadas
    wc = WordCloud(
        width=1200,               # Ancho de la imagen en píxeles
        height=600,               # Alto de la imagen en píxeles
        background_color="white", # Fondo blanco para mejor legibilidad
        colormap="viridis",       # Paleta de colores viridis (azul → verde → amarillo)
        max_words=100,            # Máximo 100 palabras mostradas
        prefer_horizontal=0.8,   # 80% de las palabras en horizontal
    ).generate_from_frequencies(freq)

    # Crea la figura matplotlib y dibuja la nube de palabras
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(wc, interpolation="bilinear")  # bilinear suaviza los bordes
    ax.axis("off")  # Oculta los ejes (no son relevantes para una nube de palabras)
    ax.set_title(
        "Nube de palabras — términos más frecuentes en abstracts y keywords",
        fontsize=13,
        pad=12,
    )
    plt.tight_layout()
    return fig
