import re
import unicodedata

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


def _ensure_nltk_resources() -> None:
    for resource, path in [("tokenizers/punkt_tab", "punkt_tab"), ("corpora/stopwords", "stopwords")]:
        try:
            nltk.data.find(resource)
        except LookupError:
            nltk.download(path, quiet=True)


_ensure_nltk_resources()

_STOPWORDS = set(stopwords.words("english"))


def normalize(text: str) -> str:
    """Limpieza básica: minúsculas, sin acentos, sin puntuación. Sin tokenizar ni eliminar stopwords."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str, remove_stopwords: bool = True) -> list[str]:
    tokens = word_tokenize(normalize(text))
    tokens = [t for t in tokens if t.isalpha() and len(t) > 1]
    if remove_stopwords:
        tokens = [t for t in tokens if t not in _STOPWORDS]
    return tokens


def to_string(text: str, remove_stopwords: bool = True) -> str:
    return " ".join(tokenize(text, remove_stopwords))
