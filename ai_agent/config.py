"""Конфигурация RAG-конвейера."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка env только один раз при инициализации конфига
load_dotenv()

# Пути
_BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DB_PATH = str(_BASE_DIR / "ai_agent" / "chroma_db_zoo")

# LLM-параметры
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")
LLM_MODEL = "gemma3:4b"
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 512
LLM_TOP_P = 0.9

# Embedding-параметры
EMBEDDING_MODEL = "ai-forever/ru-en-RoSBERTa"
EMBEDDING_DEVICE = "cpu"
EMBEDDING_BATCH_SIZE = 64
EMBEDDING_QUERY_PREFIX = "search_query: "
EMBEDDING_DOC_PREFIX = "search_document: "

# RAG-параметры
RAG_MMR_K = 8
RAG_MMR_FETCH_K = 32
RAG_MAX_CHARS = 8000
RAG_CHUNK_SIZE = 1200
RAG_CHUNK_OVERLAP = 200

# Loader-параметры
SITEMAP_URL = "https://зоопарк.екатеринбург.рф/sitemap.xml"
ROOT_URL = "https://зоопарк.екатеринбург.рф/"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
MAX_RECURSIVE_DEPTH = 2

# Threshold для прогресс-бара
PROGRESS_BAR_THRESHOLD = 100
