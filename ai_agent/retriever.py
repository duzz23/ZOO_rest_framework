"""Управление векторным хранилищем и ретривером."""
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Optional

from langchain_chroma import Chroma
from langchain_community.document_loaders import SitemapLoader, RecursiveUrlLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

from . import config

logger = logging.getLogger(__name__)


class RetrieverManager:
    """Управляет жизненным циклом ретривера с кэшированием.

    Заменяет глобальный синглтон на инкапсулированный менеджер,
    что упрощает тестирование и управление состоянием.
    """

    def __init__(self, embeddings: Any):
        """Инициализация менеджера.

        Args:
            embeddings: Экземпляр Embeddings для использования.
        """
        self._embeddings = embeddings
        self._retriever: Optional[Any] = None

    def get_retriever(self) -> Any:
        """Получает ретривер с ленивой инициализацией.

        Returns:
            Настроенный MMR-ретривер из Chroma DB.
        """
        if self._retriever is None:
            logger.info("Initializing retriever (lazy singleton)")
            self._retriever = self._create_retriever()
        else:
            logger.debug("Returning cached retriever instance")
        return self._retriever

    def _create_retriever(self) -> Any:
        """Создает новый ретривер из Chroma DB.

        Returns:
            Настроенный MMR-ретривер.
        """
        logger.debug("Creating retriever from Chroma DB at %s", config.CHROMA_DB_PATH)
        vectorstore = Chroma(
            embedding_function=self._embeddings,
            persist_directory=config.CHROMA_DB_PATH,
        )
        return vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": config.RAG_MMR_K, "fetch_k": config.RAG_MMR_FETCH_K},
        )

    def reset(self) -> None:
        """Сбрасывает кэш ретривера. Полезно для тестов."""
        self._retriever = None


def build_vector_store(embeddings: Any, force_rebuild: bool = False) -> Any:
    """Создает или обновляет векторное хранилище с данными зоопарка.

    Загружает страницы с сайта через sitemap и рекурсивный обход,
    разделяет на чанки и индексирует в Chroma DB.

    Args:
        embeddings: Экземпляр Embeddings для индексации.
        force_rebuild: Если True, пересоздает хранилище даже если оно существует.

    Returns:
        MMR-ретривер для поиска по документам.
    """
    db_path = Path(config.CHROMA_DB_PATH)

    if db_path.exists() and not force_rebuild:
        existing = Chroma(
            embedding_function=embeddings,
            persist_directory=config.CHROMA_DB_PATH,
        )
        count = existing._collection.count()  # pylint: disable=protected-access
        if count > 0:
            logger.info("Vector store already exists with %d documents.", count)
            logger.info("Use force_rebuild=True to rebuild from scratch.")
            return existing.as_retriever(
                search_type="mmr",
                search_kwargs={"k": config.RAG_MMR_K, "fetch_k": config.RAG_MMR_FETCH_K},
            )

        logger.warning("Existing store is empty, rebuilding...")
        shutil.rmtree(db_path)

    # Настройка загрузчика
    os.environ["USER_AGENT"] = config.USER_AGENT

    # Загрузить с карты сайта
    logger.info("Loading sitemap from %s", config.SITEMAP_URL)
    sitemap_loader = SitemapLoader(
        web_path=config.SITEMAP_URL,
        filter_urls=[config.ROOT_URL],
    )
    sitemap_docs = sitemap_loader.load()
    logger.info("Loaded %d pages from sitemap", len(sitemap_docs))

    # Загрузить рекурсивно
    logger.info("Loading pages recursively from %s", config.ROOT_URL)
    recursive_loader = RecursiveUrlLoader(
        url=config.ROOT_URL,
        max_depth=config.MAX_RECURSIVE_DEPTH,
        prevent_outside=True,
    )
    recursive_docs = recursive_loader.load()
    logger.info("Loaded %d pages recursively", len(recursive_docs))

    # Склеить все документы
    docs = sitemap_docs + recursive_docs
    logger.info("Total documents loaded: %d", len(docs))

    # Разделить на чанки
    text_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.HTML,
        chunk_size=config.RAG_CHUNK_SIZE,
        chunk_overlap=config.RAG_CHUNK_OVERLAP,
    )
    logger.info("Splitting documents into chunks...")
    splits = text_splitter.split_documents(docs)
    logger.info("Created %d text chunks", len(splits))

    # Убедиться, что директория существует
    db_dir = Path(config.CHROMA_DB_PATH)
    db_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Vector store directory: %s", db_dir)

    # Построить векторное хранилище
    logger.info("Building vector store (generating embeddings & indexing)...")
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=config.CHROMA_DB_PATH,
    )

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": config.RAG_MMR_K, "fetch_k": config.RAG_MMR_FETCH_K},
    )
    return retriever
