"""
Fixtures compartidos para todos los tests del proyecto bibliométrico.
Los datos de prueba son independientes del corpus real (data/processed/).
"""

import matplotlib
matplotlib.use("Agg")  # sin GUI — necesario para entornos sin Tk

import pytest
import pandas as pd


# Corpus mínimo con vocabulario variado para que TF-IDF y clustering funcionen.
# Cada abstract contiene algunos conceptos del spec (R3) para verificar frecuencias.
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


@pytest.fixture
def sample_abstracts() -> list[str]:
    return SAMPLE_ABSTRACTS


@pytest.fixture
def sample_df() -> pd.DataFrame:
    n = len(SAMPLE_ABSTRACTS)
    return pd.DataFrame({
        "title":    SAMPLE_TITLES,
        "abstract": SAMPLE_ABSTRACTS,
        "authors":  ["Author A", "Author B"] * (n // 2),
        "keywords": ["generative AI, education, machine learning"] * n,
        "year":     [2023, 2024, 2024, 2024, 2023, 2024, 2023, 2024, 2024, 2023],
        "journal":  ["Journal A", "Journal B", "Journal A", "Journal C",
                     "Journal B", "Journal A", "Journal C", "Journal B",
                     "Journal A", "Journal C"],
        "doi":      [f"10.1000/test{i}" for i in range(n)],
        "url":      [""] * n,
        "volume":   [""] * n,
        "number":   [""] * n,
        "pages":    [""] * n,
        "issn":     [""] * n,
        "source":   ["test"] * n,
    })
