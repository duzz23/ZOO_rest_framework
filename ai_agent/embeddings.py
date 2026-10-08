"""Кастомные эмбеддинги с префиксами для улучшения ретрива."""
import logging
from typing import List

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

from . import config

logger = logging.getLogger(__name__)


class PrefixedEmbeddings(Embeddings):
    """Обертка над Embeddings, добавляющая префиксы к текстам.

    Улучшает разделение между query и document эмбеддингами
    за счет добавления различных префиксов перед генерацией.
    """

    def __init__(
        self,
        base: Embeddings,
        query_prefix: str = config.EMBEDDING_QUERY_PREFIX,
        doc_prefix: str = config.EMBEDDING_DOC_PREFIX,
    ):
        """Инициализация обертки.

        Args:
            base: Базовый экземпляр Embeddings для использования.
            query_prefix: Префикс для запросов.
            doc_prefix: Префикс для документов.
        """
        self.base = base
        self.query_prefix = query_prefix
        self.doc_prefix = doc_prefix

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Эмбеддинги для списка документов.

        Args:
            texts: Список текстов для эмбеддинга.

        Returns:
            Список векторов эмбеддингов.
        """
        texts_prefixed = [self.doc_prefix + text for text in texts]

        if len(texts_prefixed) > config.PROGRESS_BAR_THRESHOLD:
            logger.info(
                "Embedding %d documents individually (batch size: %d)",
                len(texts_prefixed),
                config.EMBEDDING_BATCH_SIZE,
            )
            results = []
            for text in texts_prefixed:
                results.append(self.base.embed_query(text))
            return results

        return self.base.embed_documents(texts_prefixed)

    def embed_query(self, text: str) -> List[float]:
        """Эмбеддинг для запроса.

        Args:
            text: Текст запроса.

        Returns:
            Вектор эмбеддинга запроса.
        """
        return self.base.embed_query(self.query_prefix + text)


def create_embeddings() -> PrefixedEmbeddings:
    """Создает и настраивает экземпляр PrefixedEmbeddings.

    Returns:
        Настроенный экземпляр PrefixedEmbeddings с моделью RoSBERTa.
    """
    base_embeddings = HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL,
        model_kwargs={"device": config.EMBEDDING_DEVICE},
        encode_kwargs={
            "batch_size": config.EMBEDDING_BATCH_SIZE,
            "normalize_embeddings": True,
        },
    )

    return PrefixedEmbeddings(
        base=base_embeddings,
        query_prefix=config.EMBEDDING_QUERY_PREFIX,
        doc_prefix=config.EMBEDDING_DOC_PREFIX,
    )
