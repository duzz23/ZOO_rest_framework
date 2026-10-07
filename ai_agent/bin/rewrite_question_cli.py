#!/usr/bin/env python3

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from ai_agent.services import rewrite_question_if_needed

load_dotenv()

"""Тест вопросы для rewrite_question_if_needed"""

def main():
    questions = [
        "Стоимость входа",
        "Время работы",
        "Какой адрес",
    ]

    print(f"Testing question rewriting for {len(questions)} questions")

    for q in questions:
        rewritten = rewrite_question_if_needed(q)
        print(f"Original:  '{q}'")
        print(f"Rewritten: '{rewritten}'")
        print("-" * 72)


if __name__ == "__main__":
    main()
