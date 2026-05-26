"""
Fixtures compartidos para todos los tests del proyecto bibliométrico.
Los datos de prueba son independientes del corpus real (data/processed/).
"""

# Configura matplotlib para no usar GUI — indispensable en entornos sin Tk (CI, servidores)
import matplotlib
matplotlib.use("Agg")  # sin GUI — necesario para entornos sin Tk

# Importa pytest para definir los fixtures y pandas para construir el DataFrame de prueba
import pytest
import pandas as pd


# Corpus mínimo con vocabulario variado para que TF-IDF y clustering funcionen.
# Cada abstract contiene algunos conceptos del spec (R3) para verificar frecuencias.
# Se usan 10 documentos: suficiente para entrenar modelos sin ser costoso en tiempo.
SAMPLE_ABSTRACTS = [
    "Generative artificial intelligence models are transforming education through personalized learning and privacy concerns.",
    "Machine learning algorithms enable prompting strategies in large language models for educational purposes.",
    "Ethics and privacy issues arise with the adoption of generative AI models in educational settings.",
    "Fine-tuning transformer models on domain-specific training data improves AI literacy and personalization outcomes.",
    "Human-AI interaction patterns reveal new insights about co-creation in digital learning environments.",
    "Multimodality in generative models combines text, images, and audio for richer educational content.",
    "Algorithmic bias in training data affects the fairness of AI-generated educational materials.",
    "Explainability and transparency are key factors in building trust in AI systems for education.",
    "Personalization through generative models enables adaptive learning at scale with machine learning.",
    "Privacy-preserving machine learning techniques protect student data in AI-powered educational platforms.",
]

# Títulos correspondientes a cada abstract — usados como etiquetas en el clustering
SAMPLE_TITLES = [
    "Generative AI and Education",
    "Prompting Strategies in LLMs",
    "Ethics of AI in Education",
    "Fine-tuning for AI Literacy",
    "Human-AI Interaction Patterns",
    "Multimodal Generative Models",
    "Algorithmic Bias in Education",
    "Explainability in AI Systems",
    "Personalized Learning with AI",
    "Privacy-Preserving ML",
]


# Fixture que expone solo la lista de abstracts (usada en R2, R3, R5)
@pytest.fixture
def sample_abstracts() -> list[str]:
    return SAMPLE_ABSTRACTS


# Fixture que construye un DataFrame completo con todas las columnas del esquema del corpus
# Incluye metadatos mínimos (authors, keywords, year, journal, doi, url, etc.)
@pytest.fixture
def sample_df() -> pd.DataFrame:
    n = len(SAMPLE_ABSTRACTS)
    return pd.DataFrame({
        "title":    SAMPLE_TITLES,
        "abstract": SAMPLE_ABSTRACTS,
        # Alterna entre dos autores para tener variedad sin complicar el fixture
        "authors":  ["Author A", "Author B"] * (n // 2),
        "keywords": ["generative AI, education, machine learning"] * n,
        # Mezcla de años 2023 y 2024 para probar las visualizaciones de cronología
        "year":     [2023, 2024, 2024, 2024, 2023, 2024, 2023, 2024, 2024, 2023],
        # Tres revistas distintas para probar el top-10 de journal_timeline
        "journal":  ["Journal A", "Journal B", "Journal A", "Journal C",
                     "Journal B", "Journal A", "Journal C", "Journal B",
                     "Journal A", "Journal C"],
        # DOIs únicos generados por índice para tests de deduplicación por DOI
        "doi":      [f"10.1000/test{i}" for i in range(n)],
        "url":      [""] * n,
        "volume":   [""] * n,
        "number":   [""] * n,
        "pages":    [""] * n,
        "issn":     [""] * n,
        "source":   ["test"] * n,
    })
