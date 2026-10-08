"""Публичный API для работы с RAG-агентом."""
import logging
from typing import Any, Dict

from langsmith import traceable

from .chains import format_docs

logger = logging.getLogger(__name__)


@traceable(name="zoo_answer_question")
def answer_question(question: str, context: str, rag_chain: Any) -> str:
    """Генерирует ответ на вопрос с использованием контекста.

    Args:
        question: Вопрос пользователя.
        context: Контекст из ретривера.
        rag_chain: LCEL-цепочка для генерации.

    Returns:
        Сгенерированный ответ.
    """
    logger.debug("Answering question with context (length: %d chars)", len(context))
    inputs: Dict[str, str] = {"question": question, "context": context}
    result = rag_chain.invoke(inputs)
    logger.debug("Answer generated (length: %d chars)", len(result))
    return result


def ask_ai(
    question: str,
    rewrite_chain: Any,
    retriever_manager: Any,
    rag_chain: Any,
) -> str:
    """Публичный API для ответа на вопросы о зоопарке.

    Выполняет полный RAG-конвейер:
    1. Переписывает вопрос для улучшения ретрива.
    2. Извлекает релевантные документы.
    3. Форматирует контекст.
    4. Генерирует ответ.

    Args:
        question: Вопрос пользователя.
        rewrite_chain: Цепочка для переписывания вопросов.
        retriever_manager: Менеджер ретривера (RetrieverManager).
        rag_chain: RAG-цепочка для генерации ответов.

    Returns:
        Сгенерированный ответ на вопрос.
    """
    logger.info("Processing question: %s", question)

    # 1) Переписать вопрос, если это необходимо
    rewritten_data = rewrite_chain.invoke({"question": question})
    rewritten = rewritten_data.get("question", question)
    logger.debug("Question rewritten to: %s", rewritten)

    # 2) Извлечь соответствующие документы
    retrieved_docs = retriever_manager.get_retriever().invoke(rewritten)
    logger.info("Retrieved %d documents", len(retrieved_docs))

    # 3) Отформатировать в контекстную строку
    ctx = format_docs(retrieved_docs)
    logger.debug("Context formatted (length: %d chars)", len(ctx))

    # 4) Сгенерировать ответ
    result = answer_question(question=question, context=ctx, rag_chain=rag_chain)
    logger.info("Answer generated successfully")
    return result
