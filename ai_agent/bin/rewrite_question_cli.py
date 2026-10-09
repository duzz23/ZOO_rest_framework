#!/usr/bin/env python3
"""Скрипт для тестирования переписывания вопросов."""
import sys
from pathlib import Path
from dotenv import load_dotenv

from ai_agent.prompts import create_llm, create_question_rewrite_chain

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

load_dotenv()


def main():
    """Тестирует переписывание вопросов для улучшения ретрива."""
    questions = [
        "Стоимость входа",
        "Время работы",
        "Какой адрес",
    ]

    # Инициализация LLM и цепочки
    llm = create_llm()
    rewrite_chain = create_question_rewrite_chain(llm)

    print(f"Testing question rewriting for {len(questions)} questions")

    for q in questions:
        result = rewrite_chain.invoke({"question": q})
        rewritten = result.get("question", "")
        print(f"Original:  '{q}'")
        print(f"Rewritten: '{rewritten}'")
        print("-" * 72)


if __name__ == "__main__":
    main()
