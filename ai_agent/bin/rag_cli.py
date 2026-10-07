#!/usr/bin/env python3
import sys
from pathlib import Path
import time
from dotenv import load_dotenv
from ai_agent.services import format_docs, answer_question, get_retriever, rewrite_question_if_needed

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
load_dotenv()

"""Тест вопросы для RAG"""

def main():

    questions = [
        "Какие есть животные в зоопарке?",
        "Афиша мероприятий?",
        "адрес?",
        "А есть медведи?",
        "Часы работы?",
    ]

    print(f"Starting RAG batch with {len(questions)} questions")
    t1 = time.time()

    for q in questions:
        print("Вопрос:", q)
        # 1) rewrite question if needed
        q = rewrite_question_if_needed(q)

        # 2) retrieve documents
        retriever = get_retriever()
        retrieved_docs = retriever.invoke(q)

        # 3) format context
        ctx = format_docs(retrieved_docs)

        # 4) generate answer
        answer = answer_question(question=q, context=ctx)

        print("Ответ:", answer)
        print("=" * 72)

    t2 = time.time()
    print(f"RAG batch completed in {t2 - t1:.2f} seconds")


if __name__ == "__main__":
    main()
