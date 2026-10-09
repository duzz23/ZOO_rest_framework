"""Pytest tests for ai_agent modules."""
from unittest.mock import MagicMock, patch

import pytest

# Импорты из новых модулей
from ai_agent.chains import format_docs, ensure_context
from ai_agent.embeddings import PrefixedEmbeddings
from ai_agent.retriever import RetrieverManager
from ai_agent import config


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
# Config tests
# ---------------------------------------------------------------------------

def test_config_has_all_constants():
    """Config module has all expected constants."""
    assert hasattr(config, "CHROMA_DB_PATH")
    assert hasattr(config, "LLM_MODEL")
    assert hasattr(config, "RAG_MAX_CHARS")
    assert hasattr(config, "RAG_MMR_K")
    assert hasattr(config, "EMBEDDING_QUERY_PREFIX")
    assert config.RAG_MAX_CHARS == 8000
    assert config.RAG_MMR_K == 8
    assert config.RAG_MMR_FETCH_K == 32


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


def test_format_docs_unknown_source():
    """When source is missing, uses 'unknown_source'."""
    doc = MagicMock()
    doc.metadata = {}
    doc.page_content = "content"
    result = format_docs([doc])
    assert "unknown_source" in result


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


def test_ensure_context_missing_key():
    """Missing context key is treated as empty."""
    inp = {"other": "value"}
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


def test_prefixed_embeddings_embed_documents_exactly_100():
    """Exactly 100 docs should use batch path."""
    base = MagicMock()
    base.embed_documents.return_value = [[0.1]]
    pe = PrefixedEmbeddings(base, doc_prefix="doc:")
    texts = ["t" for _ in range(100)]
    pe.embed_documents(texts)
    base.embed_documents.assert_called_once()


def test_prefixed_embeddings_embed_documents_exactly_101():
    """Exactly 101 docs should use tqdm loop path."""
    base = MagicMock()
    base.embed_query.return_value = [0.1]
    pe = PrefixedEmbeddings(base, doc_prefix="doc:")
    texts = ["t" for _ in range(101)]
    pe.embed_documents(texts)
    base.embed_documents.assert_not_called()
    assert base.embed_query.call_count == 101


def test_prefixed_embeddings_embed_query():
    """embed_query applies query_prefix."""
    base = MagicMock()
    base.embed_query.return_value = [0.1]
    pe = PrefixedEmbeddings(base, query_prefix="search_query: ")
    pe.embed_query("hello")
    called = base.embed_query.call_args[0][0]
    assert called == "search_query: hello"


# ---------------------------------------------------------------------------
# RetrieverManager
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_manager():
    """Reset RetrieverManager state before/after each test."""
    yield
    # Note: manager is created fresh in each test, so no reset needed


def test_retriever_manager_creates_retriever():
    """First call creates a new retriever."""
    with patch("ai_agent.retriever.Chroma") as mock_chroma:
        mock_vectorstore = MagicMock()
        mock_retriever = MagicMock()
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_chroma.return_value = mock_vectorstore

        base_embeddings = MagicMock()
        manager = RetrieverManager(base_embeddings)
        result = manager.get_retriever()

        assert result is mock_retriever
        mock_chroma.assert_called_once()
        mock_vectorstore.as_retriever.assert_called_once_with(
            search_type="mmr",
            search_kwargs={"k": config.RAG_MMR_K, "fetch_k": config.RAG_MMR_FETCH_K},
        )


def test_retriever_manager_caches_retriever():
    """Second call returns cached retriever without recreating."""
    with patch("ai_agent.retriever.Chroma") as mock_chroma:
        mock_vectorstore = MagicMock()
        mock_retriever = MagicMock()
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_chroma.return_value = mock_vectorstore

        base_embeddings = MagicMock()
        manager = RetrieverManager(base_embeddings)

        first = manager.get_retriever()
        second = manager.get_retriever()

        assert first is second
        assert mock_chroma.call_count == 1


def test_retriever_manager_reset():
    """Reset clears the cached retriever."""
    with patch("ai_agent.retriever.Chroma") as mock_chroma:
        mock_vectorstore1 = MagicMock()
        mock_retriever1 = MagicMock()
        mock_vectorstore1.as_retriever.return_value = mock_retriever1

        mock_vectorstore2 = MagicMock()
        mock_retriever2 = MagicMock()
        mock_vectorstore2.as_retriever.return_value = mock_retriever2

        # First call returns mock1, second call returns mock2
        mock_chroma.side_effect = [mock_vectorstore1, mock_vectorstore2]

        base_embeddings = MagicMock()
        manager = RetrieverManager(base_embeddings)

        first = manager.get_retriever()
        manager.reset()
        second = manager.get_retriever()

        assert first is not second
        assert mock_chroma.call_count == 2


# ---------------------------------------------------------------------------
# Backward compatibility (services.py)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_services_singleton():
    """Reset singleton state in services.py before/after each test."""
    import ai_agent.services as svc
    svc._retriever_manager._retriever = None
    yield
    svc._retriever_manager._retriever = None


def test_rewrite_question_if_needed_backward_compat():
    """rewrite_question_if_needed works through services.py."""
    with patch("ai_agent.services._question_rewrite_chain") as mock_chain:
        mock_chain.invoke.return_value = {"question": "Rewritten question"}
        from ai_agent.services import rewrite_question_if_needed
        result = rewrite_question_if_needed("original")
        assert result == "Rewritten question"
        mock_chain.invoke.assert_called_once_with({"question": "original"})


def test_get_retriever_backward_compat():
    """get_retriever returns cached retriever through services.py."""
    with patch("ai_agent.retriever.Chroma") as mock_chroma:
        mock_vectorstore = MagicMock()
        mock_retriever = MagicMock()
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_chroma.return_value = mock_vectorstore

        from ai_agent.services import get_retriever
        first = get_retriever()
        second = get_retriever()
        assert first is second
        assert mock_chroma.call_count == 1


def test_answer_question_backward_compat():
    """answer_question works through services.py."""
    with patch("ai_agent.services._rag_chain") as mock_rag:
        mock_rag.invoke.return_value = "AI response"
        from ai_agent.services import answer_question
        result = answer_question("Q?", "C", mock_rag)
        mock_rag.invoke.assert_called_once_with({"question": "Q?", "context": "C"})
        assert result == "AI response"


def test_ask_ai_backward_compat():
    """ask_ai full pipeline works through services.py."""
    with patch("ai_agent.services._question_rewrite_chain") as mock_rewrite, \
         patch("ai_agent.services._rag_chain") as mock_rag, \
         patch("ai_agent.services._retriever_manager") as mock_manager:

        mock_rewrite.invoke.return_value = {"question": "rewritten"}
        mock_manager.get_retriever.return_value.invoke.return_value = [_doc(content="d1")]

        from ai_agent.services import ask_ai
        result = ask_ai(
            "original question",
            mock_rewrite,
            mock_manager,
            mock_rag,
        )

        mock_rewrite.invoke.assert_called_once_with({"question": "original question"})
        mock_manager.get_retriever.return_value.invoke.assert_called_once_with("rewritten")
        assert result is not None
