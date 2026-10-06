"""Pytest tests for ai_agent.services."""
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from ai_agent.services import (
    format_docs,
    ensure_context,
    PrefixedEmbeddings,
    rewrite_question_if_needed,
    answer_question,
    get_retriever,
    ask_ai,
    build_vector_store,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doc(source: str = "test.html", page=None, content: str = "text"):
    """Create a mock Document-like object."""
    d = MagicMock()
    d.metadata = {"source": source, "page": page}
    d.page_content = content
    return d


# ---------------------------------------------------------------------------
# format_docs
# ---------------------------------------------------------------------------

def test_format_docs_basic():
    """Basic formatting with separator."""
    docs = [_doc("a.html", content="A"), _doc("b.html", content="B")]
    result = format_docs(docs)
    assert "Source: a.html" in result
    assert "A" in result
    assert "Source: b.html" in result
    assert "B" in result
    assert "\n\n---\n\n" in result


def test_format_docs_max_chars():
    """Docs are cut off when exceeding max_chars."""
    docs = [
        _doc("a.html", content="A" * 200),
        _doc("b.html", content="B" * 200),
    ]
    result = format_docs(docs, max_chars=250)
    assert "Source: a.html" in result
    assert "Source: b.html" not in result


def test_format_docs_empty():
    """Empty list returns empty string."""
    assert format_docs([]) == ""


def test_format_docs_source_page():
    """Source and Page are included in the header."""
    doc = _doc("page.html", page=5, content="content")
    result = format_docs([doc])
    assert "Source: page.html" in result
    assert "Page: 5" in result


def test_format_docs_no_page():
    """When page is None, 'Page:' is not in output."""
    doc = _doc("page.html", page=None, content="content")
    result = format_docs([doc])
    assert "Page:" not in result


# ---------------------------------------------------------------------------
# ensure_context
# ---------------------------------------------------------------------------

def test_ensure_context_empty():
    """Empty context gets default message."""
    inp = {"context": ""}
    result = ensure_context(inp)
    assert "Контекст пуст" in result["context"]


def test_ensure_context_nonempty():
    """Non-empty context is preserved."""
    inp = {"context": "real context"}
    result = ensure_context(inp)
    assert result["context"] == "real context"


def test_ensure_context_whitespace():
    """Whitespace-only context is treated as empty."""
    inp = {"context": "   \n  "}
    result = ensure_context(inp)
    assert "Контекст пуст" in result["context"]


# ---------------------------------------------------------------------------
# PrefixedEmbeddings
# ---------------------------------------------------------------------------

def test_prefixed_embeddings_embed_documents_small():
    """<=100 docs use batch embed_documents."""
    base = MagicMock()
    base.embed_documents.return_value = [[0.1]]
    pe = PrefixedEmbeddings(base, doc_prefix="search_document: ")
    result = pe.embed_documents(["a", "b"])
    call_texts = base.embed_documents.call_args[0][0]
    assert all(t.startswith("search_document:") for t in call_texts)
    assert result == [[0.1]]


def test_prefixed_embeddings_embed_documents_large():
    """>100 docs use tqdm loop with embed_query."""
    base = MagicMock()
    base.embed_query.return_value = [0.1, 0.2]
    pe = PrefixedEmbeddings(base, doc_prefix="doc:")
    texts = [f"t{i}" for i in range(150)]
    pe.embed_documents(texts)
    base.embed_documents.assert_not_called()
    assert base.embed_query.call_count == 150


def test_prefixed_embeddings_embed_query():
    """embed_query applies query_prefix."""
    base = MagicMock()
    base.embed_query.return_value = [0.1]
    pe = PrefixedEmbeddings(base, query_prefix="search_query: ")
    pe.embed_query("hello")
    called = base.embed_query.call_args[0][0]
    assert called == "search_query: hello"


# ---------------------------------------------------------------------------
# rewrite_question_if_needed
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "input_question, mock_return, expected",
    [
        ("плохой вопрос", {"question": "Хороший вопрос?"}, "Хороший вопрос?"),
        ("q", {"question": "  trimmed  "}, "trimmed"),
        ("q", {"question": ""}, ""),
    ],
)
def test_rewrite_question_mocked(input_question, mock_return, expected):
    """rewrite_question_if_needed calls chain and returns stripped question."""
    with patch("ai_agent.services.question_rewrite_chain") as mock_chain:
        mock_chain.invoke.return_value = mock_return
        result = rewrite_question_if_needed(input_question)
        assert result == expected
        mock_chain.invoke.assert_called_once_with({"question": input_question})


# ---------------------------------------------------------------------------
# answer_question
# ---------------------------------------------------------------------------

def test_answer_question_mocked():
    """answer_question passes inputs to rag_chain and returns result."""
    with patch("ai_agent.services.rag_chain") as mock_rag:
        mock_rag.invoke.return_value = "AI response"
        result = answer_question("Q?", "C")
        mock_rag.invoke.assert_called_once_with(
            {"question": "Q?", "context": "C"}
        )
        assert result == "AI response"


# ---------------------------------------------------------------------------
# ask_ai
# ---------------------------------------------------------------------------

def test_ask_ai_full_pipeline():
    """Full pipeline: rewrite → retrieve → format → answer."""
    with patch("ai_agent.services.rewrite_question_if_needed", return_value="rew") as mock_rw, \
         patch("ai_agent.services.get_retriever") as mock_getter, \
         patch("ai_agent.services.format_docs", return_value="ctx") as mock_fmt, \
         patch("ai_agent.services.answer_question", return_value="ans") as mock_ans:

        mock_getter.return_value.invoke.return_value = [_doc(content="d1"), _doc(content="d2")]

        result = ask_ai("original")

        mock_rw.assert_called_once_with("original")
        mock_getter.return_value.invoke.assert_called_once_with("rew")
        mock_fmt.assert_called_once()
        mock_ans.assert_called_once_with(question="original", context="ctx")
        assert result == "ans"


# ---------------------------------------------------------------------------
# get_retriever
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_retriever():
    """Reset singleton before/after each test."""
    import ai_agent.services as svc
    svc._retriever_instance = None
    yield
    svc._retriever_instance = None


def test_get_retriever_singleton():
    """Second call returns the same instance without reinitializing."""
    with patch("ai_agent.services._get_retriever") as mock_get:
        mock_get.return_value = MagicMock()
        first = get_retriever()
        second = get_retriever()
        assert first is second
        assert mock_get.call_count == 1


# ---------------------------------------------------------------------------
# build_vector_store
# ---------------------------------------------------------------------------

def test_build_vector_store_cached():
    """Existing store with count > 0 returns cached retriever."""
    with patch("ai_agent.services.Chroma") as mock_cls:
        mock_collection = MagicMock()
        mock_collection.count.return_value = 100
        mock_existing = MagicMock()
        mock_existing._collection = mock_collection
        mock_existing.as_retriever.return_value = "cached"
        mock_cls.return_value = mock_existing

        result = build_vector_store()

        assert result == "cached"
        mock_existing.as_retriever.assert_called_once_with(
            search_type="mmr", search_kwargs={"k": 8, "fetch_k": 32}
        )


def test_build_vector_store_force_rebuild():
    """force_rebuild=True triggers full rebuild."""
    with patch("ai_agent.services.Path.exists", return_value=False), \
         patch("ai_agent.services.SitemapLoader") as mock_sitemap, \
         patch("ai_agent.services.RecursiveUrlLoader") as mock_recursive, \
         patch("ai_agent.services.RecursiveCharacterTextSplitter") as mock_splitter, \
         patch("ai_agent.services.Chroma") as mock_cls:

        mock_sitemap.return_value.load.return_value = []
        mock_recursive.return_value.load.return_value = []
        mock_splitter.from_language.return_value.split_documents.return_value = []

        mock_new = MagicMock()
        mock_new.as_retriever.return_value = "new_retriever"
        mock_cls.from_documents.return_value = mock_new

        result = build_vector_store(force_rebuild=True)

        assert result == "new_retriever"
        mock_cls.from_documents.assert_called_once()


def test_build_vector_store_empty_rebuilds():
    """Existing store with count=0 triggers rebuild."""
    with patch("ai_agent.services.shutil") as mock_shutil, \
         patch("ai_agent.services.SitemapLoader") as mock_sitemap, \
         patch("ai_agent.services.RecursiveUrlLoader") as mock_recursive, \
         patch("ai_agent.services.RecursiveCharacterTextSplitter") as mock_splitter, \
         patch("ai_agent.services.Chroma") as mock_cls:

        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_existing = MagicMock()
        mock_existing._collection = mock_collection
        mock_cls.return_value = mock_existing

        mock_sitemap.return_value.load.return_value = []
        mock_recursive.return_value.load.return_value = []
        mock_splitter.from_language.return_value.split_documents.return_value = []

        mock_new = MagicMock()
        mock_new.as_retriever.return_value = "new_retriever"
        mock_cls.from_documents.return_value = mock_new

        result = build_vector_store()

        assert result == "new_retriever"
        mock_shutil.rmtree.assert_called_once()
