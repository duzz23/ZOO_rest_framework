#!/usr/bin/env python3
"""Скрипт для создания векторной базы данных на основе сайта зоопарка."""
import sys
from pathlib import Path

from ai_agent.embeddings import create_embeddings
from ai_agent.retriever import build_vector_store

# Добавляем zoo/ в sys.path, чтобы импортировать ai_agent
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv


load_dotenv()


def main():
    """Создаём векторное хранилище, загружая данные с сайта."""
    print("Starting vector store build...")
    embeddings = create_embeddings()
    retriever = build_vector_store(embeddings)
    print(f"Vector store built successfully. Retriever: {retriever}")


if __name__ == "__main__":
    main()
