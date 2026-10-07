"""RAG pipeline для агента"""
import os
import shutil
import logging
from pathlib import Path
from typing import List
from langsmith import traceable
from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from langchain_community.document_loaders import WebBaseLoader, SitemapLoader, RecursiveUrlLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from tqdm import tqdm

logger = logging.getLogger(__name__)

load_dotenv()

# Модель gemma3:4b

llm_agent_gemma = ChatOpenAI(
    api_key=os.getenv("OLLAMA_API_KEY"),
    base_url=os.getenv("OLLAMA_API_URL"),
    model="gemma3:4b",
    temperature=0.2,
    max_tokens=512,
    top_p=0.9,
)
# Модель  для embeddings ai-forever/ru-en-RoSBERTa
base_embeddings = HuggingFaceEmbeddings(
    model_name="ai-forever/ru-en-RoSBERTa",
    model_kwargs={"device": "cpu"},  # Измени на "cuda", если есть GPU
    encode_kwargs={
        "batch_size": 64,  # Увеличен с дефолтного 1 для параллельного инференса
        "normalize_embeddings": True,  # Нормализация для лучшего cosine similarity
    },
)


# Промт для rewrite 

question_rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Ты подготавливаешь вопрос для RAG по Зоопарку в Екатеринбурге.\n"
     "Верни результат СТРОГО в JSON без лишнего текста.\n"
     "Формат: {{\"question\": \"...\"}}\n"
     "Правила:\n"
     "- Если вопрос хороший — верни его как есть.\n"
     "- Если плохой — перепиши в чёткий самодостаточный вопрос.\n"
     "- Не добавляй префиксы вроде 'Формулировка для поиска:'\n"
     "- Не используй кавычки-ёлочки «» и двойные кавычки вокруг всего вопроса.\n"
     "- Всегда упоминай 'Зоопарк в Екатеринбурге', если уместно.\n"
     ),
    ("human", "{question}")
])

question_rewrite_chain = (
        question_rewrite_prompt
        | llm_agent_gemma
        | JsonOutputParser() # используем JsonOutputParser так как возвращаем JSON
)

 # Ретривер уточнения для вопросов к модели

def rewrite_question_if_needed(question: str) -> str:
    logger.debug("Rewriting question: %s", question)
    # для json
    data = question_rewrite_chain.invoke({"question": question})
    logger.debug("Rewritten question: %s", data.get("question", ""))
    return data["question"].strip()


# Создание векторной БД и загрузка данных

_BASE_DIR = Path(__file__).resolve().parent.parent  # zoo/
CHROMA_DB_PATH = str(_BASE_DIR / "ai_agent" / "chroma_db_zoo")

# Расставляем Префиксы search_query и search_document
class PrefixedEmbeddings(Embeddings):

    def __init__(self, base, query_prefix: str = "", doc_prefix: str = ""):
        self.base = base
        self.query_prefix = query_prefix
        self.doc_prefix = doc_prefix

    def embed_documents(self, texts):
        texts_prefixed = [self.doc_prefix + t for t in texts]
        # Показываем прогресс-бар только при большом количестве текстов
        if len(texts_prefixed) > 100:
            results = []
            for text in tqdm(texts_prefixed, desc="Embedding documents", unit="doc"):
                results.append(self.base.embed_query(text))
            return results
        return self.base.embed_documents(texts_prefixed)

    def embed_query(self, text):
        return self.base.embed_query(self.query_prefix + text)


embeddings = PrefixedEmbeddings(
    base_embeddings,
    query_prefix="search_query: ",
    doc_prefix="search_document: ",
)


def _get_retriever():
    logger.debug("Creating retriever from Chroma DB at %s", CHROMA_DB_PATH)
    vectorstore = Chroma(
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_PATH,
    )
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 8, "fetch_k": 32},
    )

_retriever_instance = None


def get_retriever():
    global _retriever_instance
    if _retriever_instance is None:
        logger.info("Initializing retriever (lazy singleton)")
        _retriever_instance = _get_retriever()
    else:
        logger.debug("Returning cached retriever instance")
    return _retriever_instance



# RAG chain

rag_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Ты помощник, который отвечает СТРОГО НА РУССКОМ ЯЗЫКЕ. "
        "Используй только информацию из предоставленного контекста, не придумывай факты. "
        "Если ответа в контексте нет или данных недостаточно, честно скажи, что не нашёл ответа в базе. "
        "При необходимости можешь упоминать источник в формате из заголовка (Source и Page). "
        "Отвечай кратко и по делу, обычно до 5–7 предложений.",
    ),
    MessagesPlaceholder("history"),
    (
        "human",
        "Контекст:\n{context}\n\nВопрос: {question}",
    ),
])

# собирает текст из нескольких документов в один большой блок, строго ограничивая его итоговый размер.
def format_docs(docs, max_chars: int = 8000):
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

# Зашита от пустого котекста
def ensure_context(input_dict: dict) -> dict:
    context = input_dict.get("context", "").strip()
    if not context:
        input_dict["context"] = (
            "Контекст пуст: ретривер не нашёл ни одного подходящего фрагмента. "
            "Если ответ важен, лучше явно сказать пользователю об этом."
        )
    return input_dict


rag_chain = (
    {
        "context": lambda d: d.get("context", ""),
        "question": lambda d: d.get("question", ""),
        "history": lambda _: [],
    }
    | RunnableLambda(ensure_context)
    | rag_prompt
    | llm_agent_gemma
    | StrOutputParser()
).with_config(run_name="rag_chain")

# Настройка LangSmith для отслеживания RAG
@traceable(name="zoo_answer_question")
def answer_question(question: str, context: str) -> str:
    logger.debug("Answering question with context (length: %d chars)", len(context))
    inputs = {"question": question, "context": context}
    result = rag_chain.invoke(inputs)
    logger.debug("Answer generated (length: %d chars)", len(result))
    return result



# Public API

def ask_ai(question: str) -> str:
    logger.info("Processing question: %s", question)
    # 1) Перемените вопрос, если это необходимо
    rewritten = rewrite_question_if_needed(question)
    logger.debug("Question rewritten to: %s", rewritten)

    # 2) Извлеките соответствующие документы
    retrieved_docs = get_retriever().invoke(rewritten)
    logger.info("Retrieved %d documents", len(retrieved_docs))

    # 3) Отформатировать в контекстную строку
    ctx = format_docs(retrieved_docs)
    logger.debug("Context formatted (length: %d chars)", len(ctx))

    # 4) Сгенерировать ответ
    result = answer_question(question=question, context=ctx)
    logger.info("Answer generated successfully")
    return result


# Создание векторного хранилища

def build_vector_store(force_rebuild: bool = False):
    db_path = Path(CHROMA_DB_PATH)
    if db_path.exists() and not force_rebuild:
        existing = Chroma(
            embedding_function=embeddings,
            persist_directory=CHROMA_DB_PATH,
        )
        count = existing._collection.count()
        if count > 0:
            logger.info("Vector store already exists with %d documents.", count)
            logger.info("Use force_rebuild=True to rebuild from scratch.")
            return existing.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 8, "fetch_k": 32},
            )
        else:
            logger.warning("Existing store is empty, rebuilding...")
            shutil.rmtree(db_path)

    os.environ["USER_AGENT"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    SITEMAP_URL = "https://зоопарк.екатеринбург.рф/sitemap.xml"
    ROOT_URL = "https://зоопарк.екатеринбург.рф/"

    # Загрузить с карты сайта
    logger.info("Loading sitemap from %s", SITEMAP_URL)
    sitemap_loader = SitemapLoader(
        web_path=SITEMAP_URL,
        filter_urls=[ROOT_URL],
    )
    sitemap_docs = sitemap_loader.load()
    logger.info("Loaded %d pages from sitemap", len(sitemap_docs))

    # Загружать рекурсивно
    logger.info("Loading pages recursively from %s", ROOT_URL)
    recursive_loader = RecursiveUrlLoader(
        url=ROOT_URL,
        max_depth=2,
        prevent_outside=True,
    )
    recursive_docs = recursive_loader.load()
    logger.info("Loaded %d pages recursively", len(recursive_docs))

    # Склейка всех документов
    docs = sitemap_docs + recursive_docs
    logger.info("Total documents loaded: %d", len(docs))

    text_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.HTML,
        chunk_size=1200,
        chunk_overlap=200,
    )
    logger.info("Splitting documents into chunks...")
    splits = text_splitter.split_documents(docs)
    logger.info("Created %d text chunks", len(splits))

    # ⚡ ГЛАВНОЕ УСКОРЕНИЕ: одна вставка вместо цикла
    # ChromaDB internally сам разобьёт данные на оптимальные батчи,
    # минимизирует обращения к диску и выполнит persist() один раз
    logger.info("Building vector store (generating embeddings & indexing)...")
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=CHROMA_DB_PATH,
    )

    # Ленивая инициализация синглтона _retriever_instance
    global _retriever_instance
    _retriever_instance = None

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 8, "fetch_k": 32},
    )
    return retriever
