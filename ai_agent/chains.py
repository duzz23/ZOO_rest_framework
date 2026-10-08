"""RAG-цепочки и логика обработки документов."""
import logging
from typing import Any, Dict, List

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

from . import config

logger = logging.getLogger(__name__)


def create_rag_prompt() -> ChatPromptTemplate:
    """Создает промпт для RAG-генерации ответов.

    Returns:
        Настроенный ChatPromptTemplate с инструкциями для LLM.
    """
    return ChatPromptTemplate.from_messages([
        (
            "system",
            "Ты помощник, который отвечает СТРОГО НА РУССКОМ ЯЗЫКЕ. "
            "Используй только информацию из предоставленного контекста, "
            "не придумывай факты. "
            "Если ответа в контексте нет или данных недостаточно, "
            "честно скажи, что не нашёл ответа в базе. "
            "При необходимости можешь упоминать источник в формате "
            "из заголовка (Source и Page). "
            "Отвечай кратко и по делу, обычно до 5–7 предложений.",
        ),
        MessagesPlaceholder("history"),
        (
            "human",
            "Контекст:\n{context}\n\nВопрос: {question}",
        ),
    ])


def format_docs(docs: List[Document], max_chars: int = config.RAG_MAX_CHARS) -> str:
    """Собирает тексты из документов в один блок, строго ограничивая размер.

    Аргументирует каждый документ источником и страницей (если есть).
    Останавливается при достижении лимита символов.

    Args:
        docs: Список документов для форматирования.
        max_chars: Максимальное количество символов в результате.

    Returns:
        Отформатированная строка с документами, разделенными '---'.
    """
    formatted = []
    total_len = 0
    for doc in docs:
        source = doc.metadata.get("source", "unknown_source")
        page = doc.metadata.get("page", None)

        header = f"Source: {source}"
        if page is not None:
            header += f" | Page: {page}"
        text = doc.page_content.strip()
        block = f"{header}\n{text}"

        if total_len + len(block) > max_chars:
            break

        formatted.append(block)
        total_len += len(block)

    return "\n\n---\n\n".join(formatted)


def ensure_context(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Проверяет контекст на пустоту и добавляет дефолтное сообщение.

    Если контекст пуст или содержит только пробелы, подставляет
    сообщение о том, что данные не найдены.

    Args:
        input_dict: Словарь с ключом 'context'.

    Returns:
        Словарь с гарантированно непустым контекстом.
    """
    context = input_dict.get("context", "").strip()
    if not context:
        input_dict["context"] = (
            "Контекст пуст: ретривер не нашёл ни одного подходящего фрагмента. "
            "Если ответ важен, лучше явно сказать пользователю об этом."
        )
    return input_dict


def create_rag_chain(llm: Any) -> Any:
    """Создает RAG-цепочку для генерации ответов.

    Цепочка: извлечение контекста -> проверка -> промпт -> LLM -> парсер.

    Args:
        llm: Экземпляр LLM для использования в цепочке.

    Returns:
        LCEL-цепочка, принимающая словарь с 'question' и 'context'.
    """
    rag_prompt = create_rag_prompt()

    return (
        {
            "context": lambda d: d.get("context", ""),
            "question": lambda d: d.get("question", ""),
            "history": lambda _: [],
        }
        | RunnableLambda(ensure_context)
        | rag_prompt
        | llm
        | StrOutputParser()
    ).with_config(run_name="rag_chain")
