# Importa módulo de expresiones regulares para buscar y reemplazar patrones en texto
import re
# Importa unicodedata para normalizar caracteres Unicode (quitar tildes, etc.)
import unicodedata

# Importa NLTK, librería de procesamiento de lenguaje natural
import nltk
# Importa el corpus de palabras vacías (stopwords) en inglés de NLTK
from nltk.corpus import stopwords
# Importa el tokenizador de palabras de NLTK
from nltk.tokenize import word_tokenize


# Función interna que descarga los recursos de NLTK si no están instalados localmente
def _ensure_nltk_resources() -> None:
    # Verifica si cada recurso existe; si no, lo descarga silenciosamente
    for resource, path in [("tokenizers/punkt_tab", "punkt_tab"), ("corpora/stopwords", "stopwords")]:
        try:
            nltk.data.find(resource)
        except LookupError:
            nltk.download(path, quiet=True)


# Ejecuta la descarga de recursos al importar el módulo (se hace solo una vez)
_ensure_nltk_resources()

# Carga el conjunto de palabras vacías en inglés como un set para búsqueda O(1)
_STOPWORDS = set(stopwords.words("english"))


def normalize(text: str) -> str:
    """Limpieza básica: minúsculas, sin acentos, sin puntuación. Sin tokenizar ni eliminar stopwords."""
    # Descompone caracteres Unicode y los convierte a ASCII, eliminando tildes y caracteres especiales
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    # Convierte todo el texto a minúsculas para uniformidad
    text = text.lower()
    # Reemplaza cualquier carácter que no sea letra, número o espacio con un espacio
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    # Colapsa múltiples espacios seguidos en uno solo y elimina espacios al inicio/fin
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str, remove_stopwords: bool = True) -> list[str]:
    # Normaliza el texto y luego lo divide en tokens individuales usando NLTK
    tokens = word_tokenize(normalize(text))
    # Filtra los tokens: conserva solo palabras alfabéticas de más de 1 carácter
    tokens = [t for t in tokens if t.isalpha() and len(t) > 1]
    # Si se solicita, elimina las palabras vacías (stopwords) del conjunto
    if remove_stopwords:
        tokens = [t for t in tokens if t not in _STOPWORDS]
    return tokens


def to_string(text: str, remove_stopwords: bool = True) -> str:
    # Tokeniza el texto y vuelve a unir los tokens en una cadena separada por espacios
    return " ".join(tokenize(text, remove_stopwords))
