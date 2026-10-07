#!/usr/bin/env python3
"""Скрипт для создания векторной базы данных на основе сайта зоопарка."""
import sys
from pathlib import Path

# Добавляем zoo/ в sys.path, чтобы импортировать ai_agent
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
from ai_agent.services import build_vector_store

load_dotenv()


def main():
    """Создаём векторное хранилище, загружая данные с сайта."""
    print("Starting vector store build...")
    retriever = build_vector_store()
    print(f"Vector store built successfully. Retriever: {retriever}")


if __name__ == "__main__":
    main()
