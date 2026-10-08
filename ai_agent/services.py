"""RAG pipeline для агента (DEPRECATED: используйте импорты из подмодулей).

Этот файл сохранен для обратной совместимости.
Новый код должен импортировать функции напрямую из подмодулей:
- ai_agent.config
- ai_agent.prompts
- ai_agent.embeddings
- ai_agent.chains
- ai_agent.retriever
- ai_agent.api
"""
import logging
from typing import Any

from .prompts import create_llm, create_question_rewrite_chain
from .embeddings import PrefixedEmbeddings, create_embeddings
from .chains import format_docs, ensure_context, create_rag_chain
from .retriever import RetrieverManager, build_vector_store
from .api import ask_ai, answer_question

logger = logging.getLogger(__name__)

# Создание экземпляров для обратной совместимости
_llm = create_llm()
_embeddings = create_embeddings()
_question_rewrite_chain = create_question_rewrite_chain(_llm)
_rag_chain = create_rag_chain(_llm)
_retriever_manager = RetrieverManager(_embeddings)


def rewrite_question_if_needed(question: str) -> str:
    """Переписывает вопрос для улучшения качества ретрива.

    Args:
        question: Исходный вопрос пользователя.

    Returns:
        Переформлированный вопрос.
    """
    logger.debug("Rewriting question: %s", question)
    data = _question_rewrite_chain.invoke({"question": question})
    logger.debug("Rewritten question: %s", data.get("question", ""))
    return data["question"].strip()


def get_retriever() -> Any:
    """Получает ретривер для поиска по документам.

    Returns:
        MMR-ретривер из Chroma DB.
    """
    return _retriever_manager.get_retriever()


__all__ = [
    "format_docs",
    "ensure_context",
    "PrefixedEmbeddings",
    "rewrite_question_if_needed",
    "answer_question",
    "get_retriever",
    "ask_ai",
    "build_vector_store",
    "_llm",
    "_embeddings",
    "_question_rewrite_chain",
    "_rag_chain",
    "_retriever_manager",
]
