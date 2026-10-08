"""Промпты и LLM-цепочки для RAG."""
import logging
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI

from . import config

logger = logging.getLogger(__name__)


def create_llm() -> ChatOpenAI:
    """Создает экземпляр LLM (Gemma3) для генерации ответов.

    Returns:
        Настроенный экземпляр ChatOpenAI, подключенный к Ollama.
    """
    return ChatOpenAI(
        api_key=config.OLLAMA_API_KEY,
        base_url=config.OLLAMA_API_URL,
        model=config.LLM_MODEL,
        temperature=config.LLM_TEMPERATURE,
        max_tokens=config.LLM_MAX_TOKENS,
        top_p=config.LLM_TOP_P,
    )


def create_question_rewrite_chain(llm: ChatOpenAI) -> Any:
    """Создает цепочку для переписывания вопросов.

    Используется для улучшения качества ретрива путем
    нормализации формулировок вопросов.

    Args:
        llm: Экземпляр LLM для использования в цепочке.

    Returns:
        LCEL-цепочка, возвращающая словарь с ключом 'question'.
    """
    question_rewrite_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Ты подготавливаешь вопрос для RAG по Зоопарку в Екатеринбурге.\n"
            "Верни результат СТРОГО в JSON без лишнего текста.\n"
            "Формат: {{\"question\": \"...\"}}\n"
            "Правила:\n"
            "- Если вопрос хороший — верни его как есть.\n"
            "- Если плохой — перепиши в чёткий самодостаточный вопрос.\n"
            "- Не добавляй префиксы вроде 'Формулировка для поиска:'\n"
            "- Не используй кавычки-ёлочки «» и двойные кавычки вокруг всего вопроса.\n"
            "- Всегда упоминай 'Зоопарк в Екатеринбурге', если уместно.\n",
        ),
        ("human", "{question}"),
    ])

    return question_rewrite_prompt | llm | JsonOutputParser()
