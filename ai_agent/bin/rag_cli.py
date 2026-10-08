#!/usr/bin/env python3
"""RAG CLI для пакетной обработки вопросов."""
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

from ai_agent.prompts import create_llm, create_question_rewrite_chain
from ai_agent.embeddings import create_embeddings
from ai_agent.chains import format_docs, create_rag_chain
from ai_agent.retriever import RetrieverManager
from ai_agent.api import ask_ai

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
load_dotenv()


def main():
    """Основная функция для обработки вопросов о зоопарке."""
    questions = [
        "Какие есть животные в зоопарке?",
        "Афиша мероприятий?",
        "адрес?",
        "А есть медведи?",
        "Часы работы?",
    ]

    # Инициализация зависимостей
    llm = create_llm()
    embeddings = create_embeddings()
    rewrite_chain = create_question_rewrite_chain(llm)
    rag_chain = create_rag_chain(llm)
    retriever_manager = RetrieverManager(embeddings)

    print(f"Starting RAG batch with {len(questions)} questions")
    t1 = time.time()

    for q in questions:
        print("Вопрос:", q)

        # Полный RAG-конвейер через единый API
        answer = ask_ai(
            question=q,
            rewrite_chain=rewrite_chain,
            retriever_manager=retriever_manager,
            rag_chain=rag_chain,
        )

        print("Ответ:", answer)
        print("=" * 72)

    t2 = time.time()
    print(f"RAG batch completed in {t2 - t1:.2f} seconds")


if __name__ == "__main__":
    main()
