import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_community.document_loaders import SitemapLoader, RecursiveUrlLoader

from agent_llm_test.model_agent.model import base_embeddings

load_dotenv()

# Загрузка документов
os.environ["USER_AGENT"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
SITEMAP_URL = "https://зоопарк.екатеринбург.рф//sitemap.xml"
ROOT_URL = "https://зоопарк.екатеринбург.рф/"

# 1) Загружаем все страницы из sitemap
sitemap_loader = SitemapLoader(
    web_path=SITEMAP_URL,
    filter_urls=[ROOT_URL],  # на всякий случай ограничиваем доменом
)
sitemap_docs = sitemap_loader.load()

# 2) Дополнительно рекурсивно обходим сайт от корня
recursive_loader = RecursiveUrlLoader(
    url=ROOT_URL,
    max_depth=2,          # глубину при желании можно увеличить
    prevent_outside=True  # не выходим за пределы домена
)
recursive_docs = recursive_loader.load()

# 3) Объединяем всё в один список документов для RAG
docs = sitemap_docs + recursive_docs


loader = WebBaseLoader('https://зоопарк.екатеринбург.рф/zoo/svedeniya-ob-uchrezhdenii/')
docs = loader.load()

# print(f"Total documents: {len(docs)}")
# print(f"Total characters: {sum(len(doc.page_content) for doc in docs)}")

# ================================================================================================================

# Разбиение на чанки и создание векторного хранилища

text_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.HTML,   # учитываем структуру HTML
    chunk_size=1200,          # немного больше, т.к. структура сохраняется лучше
    chunk_overlap=200,
)

splits = text_splitter.split_documents(docs)

# ================================================================================================================

# Расставляем Префиксы
class PrefixedEmbeddings(Embeddings):
    def __init__(self, base, query_prefix="", doc_prefix=""):
        self.base = base
        self.query_prefix = query_prefix
        self.doc_prefix = doc_prefix

    def embed_documents(self, texts):
        texts_prefixed = [self.doc_prefix + t for t in texts]
        return self.base.embed_documents(texts_prefixed)

    def embed_query(self, text):
        return self.base.embed_query(self.query_prefix + text)

embeddings = PrefixedEmbeddings(
    base_embeddings,
    query_prefix="search_query: ",
    doc_prefix="search_document: ",
)

persist_directory = "./chroma_db_zoo"

if Path(persist_directory).exists():
    # Индекс уже есть — просто загружаем
    vectorstore = Chroma(
        embedding_function=embeddings,
        persist_directory=persist_directory,
    )
else:
    # Первый запуск — создаём индекс
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=persist_directory,
    )

# ================================================================================================================

retriever = vectorstore.as_retriever(
    search_type="mmr",  # вместо простого similarity
    search_kwargs={
        "k": 8,          # сколько документов вернуть в итоге
        "fetch_k": 32,   # из скольких кандидатов выбирать (больше = разнообразнее)
        # при желании можно добавить lambda_mult для тонкой настройки
        # lambda_mult – это параметр MMR, который задаёт баланс между релевантностью документов запросу и их разнообразием: чем ближе значение к 1, тем сильнее приоритет близости к запросу, чем ближе к 0 – тем важнее разнообразие результатов.
        # "lambda_mult": 0.8,
    },
)


