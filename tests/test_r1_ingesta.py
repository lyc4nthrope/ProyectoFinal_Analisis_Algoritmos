"""
R1 — Automatización de descarga y unificación de datos.

Spec: "Se debe automatizar la información de descarga sobre dos bases de datos.
Posteriormente se debe unificar la información en un solo archivo garantizando
una sola instancia del producto. En el otro archivo se debe almacenar toda la
información con el registro de los productos repetidos."
"""

# Importa textwrap para escribir el contenido BibTeX sin sangría extra
import textwrap

import pytest

# Importa los elementos a testear: campos requeridos, parser, dedup y normalización
from src.data_sources.base_parser import ARTICLE_FIELDS
from src.data_sources.bibtex_parser import BibtexFileParser
from src.processing.deduplication import deduplicate
from src.processing.text_preprocessing import normalize


# ── Fixtures ──────────────────────────────────────────────────────────────────

# Contenido BibTeX mínimo con dos artículos para probar el parser
BIBTEX_CONTENT = textwrap.dedent("""\
    @article{smith2024,
      title     = {Generative AI in Education},
      author    = {Smith, John and Doe, Jane},
      journal   = {Journal of Educational Technology},
      year      = {2024},
      doi       = {10.1000/test.2024.001},
      abstract  = {This study examines generative artificial intelligence in education.},
      keywords  = {generative AI, education, machine learning},
      volume    = {12},
      number    = {3},
      pages     = {100--120},
      issn      = {1234-5678},
    }

    @article{jones2023,
      title     = {Machine Learning for Personalized Education},
      author    = {Jones, Alice},
      journal   = {AI Research},
      year      = {2023},
      doi       = {10.1000/test.2023.002},
      abstract  = {Machine learning enables personalized learning at scale.},
      keywords  = {machine learning, personalization},
    }
""")


# Fixture que crea un archivo .bib temporal con el contenido de prueba
@pytest.fixture
def bibtex_file(tmp_path):
    path = tmp_path / "test.bib"
    path.write_text(BIBTEX_CONTENT, encoding="utf-8")
    return str(path)


# ── Parser ────────────────────────────────────────────────────────────────────

class TestBibtexParser:
    # Verifica que el parser devuelve una lista con los artículos del archivo BibTeX
    def test_parser_returns_list_of_articles(self, bibtex_file):
        parser = BibtexFileParser(source_name="test_source")
        articles = parser.parse(bibtex_file)
        assert isinstance(articles, list)
        assert len(articles) == 2

    # Verifica que cada artículo tiene todos los campos requeridos por el esquema
    def test_each_article_has_all_required_fields(self, bibtex_file):
        parser = BibtexFileParser(source_name="test_source")
        articles = parser.parse(bibtex_file)
        for article in articles:
            for field in ARTICLE_FIELDS:
                assert field in article, f"Campo '{field}' faltante en artículo"

    # Verifica que el título se extrae correctamente desde el campo BibTeX
    def test_title_extracted_correctly(self, bibtex_file):
        parser = BibtexFileParser(source_name="test_source")
        articles = parser.parse(bibtex_file)
        titles = [a["title"] for a in articles]
        assert "Generative AI in Education" in titles

    # Verifica que el año se extrae como string desde el campo BibTeX
    def test_year_extracted_correctly(self, bibtex_file):
        parser = BibtexFileParser(source_name="test_source")
        articles = parser.parse(bibtex_file)
        years = {a["title"]: a["year"] for a in articles}
        assert years["Generative AI in Education"] == "2024"

    # Verifica que el DOI se extrae sin transformaciones
    def test_doi_extracted_correctly(self, bibtex_file):
        parser = BibtexFileParser(source_name="test_source")
        articles = parser.parse(bibtex_file)
        dois = [a["doi"] for a in articles]
        assert "10.1000/test.2024.001" in dois

    # Verifica que el campo "source" se toma del source_name pasado al constructor
    def test_source_field_matches_source_name(self, bibtex_file):
        parser = BibtexFileParser(source_name="sciencedirect")
        articles = parser.parse(bibtex_file)
        for article in articles:
            assert article["source"] == "sciencedirect"

    # Verifica que el abstract se extrae y contiene el texto original
    def test_abstract_extracted_correctly(self, bibtex_file):
        parser = BibtexFileParser(source_name="test_source")
        articles = parser.parse(bibtex_file)
        abstract = next(a["abstract"] for a in articles if a["title"] == "Generative AI in Education")
        assert len(abstract) > 0
        assert "generative" in abstract.lower()


# ── Deduplicación ─────────────────────────────────────────────────────────────

class TestDeduplication:
    # Helper que construye un artículo con campos controlados según el nivel de riqueza
    def _make_article(self, title: str, abstract: str = "sample abstract", extra_fields: int = 3) -> dict:
        return {
            "title":    title,
            "abstract": abstract,
            "authors":  "Author A" if extra_fields >= 1 else "",
            "keywords": "keyword" if extra_fields >= 2 else "",
            "year":     "2024" if extra_fields >= 3 else "",
            "journal":  "",
            "doi":      "",
            "url":      "",
            "volume":   "",
            "number":   "",
            "pages":    "",
            "issn":     "",
            "source":   "test",
        }

    # Verifica que artículos con títulos distintos se conservan todos
    def test_unique_articles_are_all_kept(self):
        articles = [
            self._make_article("Article About Machine Learning"),
            self._make_article("Study on Neural Networks"),
            self._make_article("Research in Computer Vision"),
        ]
        unique, duplicates = deduplicate(articles)
        assert len(unique) == 3
        assert len(duplicates) == 0

    # Verifica que un duplicado exacto (mismo título) queda como uno solo
    def test_exact_duplicate_is_removed(self):
        title = "Generative AI in Education: A Survey"
        articles = [
            self._make_article(title),
            self._make_article(title),
        ]
        unique, duplicates = deduplicate(articles)
        assert len(unique) == 1
        assert len(duplicates) == 1

    # Verifica que títulos muy similares (similitud >= 0.90) se tratan como duplicados
    def test_fuzzy_duplicate_is_removed(self):
        # Títulos con similitud >= 0.90 — un carácter diferente en string largo
        title_a = "Generative Artificial Intelligence in Higher Education Contexts"
        title_b = "Generative Artificial Intelligence in Higher Education Context"
        similarity = 1 - abs(len(title_a) - len(title_b)) / max(len(title_a), len(title_b))
        assert similarity >= 0.90, "El fixture de test no tiene similitud >= 0.90"

        articles = [self._make_article(title_a), self._make_article(title_b)]
        unique, duplicates = deduplicate(articles)
        assert len(unique) == 1
        assert len(duplicates) == 1

    # Verifica que cuando hay duplicados, el artículo con más campos llenos gana
    def test_richer_article_wins_on_duplicate(self):
        title = "AI in Education"
        poor    = self._make_article(title, extra_fields=0)
        rich    = self._make_article(title, extra_fields=3)
        articles = [poor, rich]
        unique, duplicates = deduplicate(articles)
        assert len(unique) == 1
        # El artículo ganador debe tener el campo authors del artículo rico
        assert unique[0]["authors"] == "Author A"

    # Verifica que el artículo descartado aparece en la lista de duplicados
    def test_duplicate_article_registered_in_duplicates_list(self):
        title = "Repeated Article Title"
        articles = [self._make_article(title), self._make_article(title)]
        _, duplicates = deduplicate(articles)
        assert len(duplicates) == 1

    # Verifica que los artículos de salida tienen todos los campos del esquema
    def test_output_articles_have_all_required_fields(self):
        articles = [self._make_article("Unique Article One"), self._make_article("Unique Article Two")]
        unique, _ = deduplicate(articles)
        for article in unique:
            for field in ARTICLE_FIELDS:
                assert field in article


# ── Unificador ────────────────────────────────────────────────────────────────

class TestUnifier:
    def test_unified_csv_exists_and_has_required_columns(self):
        """El unificador debe haber generado unified.csv con todas las columnas."""
        # Requiere que unified.csv ya exista (generado previamente por el pipeline)
        from src.config import PROCESSED_DIR
        import pandas as pd

        unified_path = PROCESSED_DIR / "unified.csv"
        assert unified_path.exists(), "unified.csv no fue generado — ejecuta el unificador primero"

        # Verifica que el CSV tiene todas las columnas del esquema de artículos
        df = pd.read_csv(unified_path)
        for field in ARTICLE_FIELDS:
            assert field in df.columns, f"Columna '{field}' faltante en unified.csv"

    def test_unified_csv_has_no_duplicate_titles(self):
        """No deben existir títulos normalizados duplicados en el corpus unificado."""
        from src.config import PROCESSED_DIR
        import pandas as pd

        # Normaliza todos los títulos y verifica que no hay duplicados tras normalización
        df = pd.read_csv(PROCESSED_DIR / "unified.csv").fillna("")
        normalized = df["title"].apply(normalize)
        assert normalized.duplicated().sum() == 0, "Hay títulos duplicados en unified.csv"

    # Verifica que el archivo de duplicados fue generado junto con unified.csv
    def test_duplicates_csv_exists(self):
        from src.config import PROCESSED_DIR
        assert (PROCESSED_DIR / "duplicates.csv").exists()
