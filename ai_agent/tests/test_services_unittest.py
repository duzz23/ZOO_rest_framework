"""Unit tests for ai_agent.services using unittest."""
import unittest
from unittest.mock import patch, MagicMock, PropertyMock

from ai_agent.services import (
    format_docs,
    ensure_context,
    PrefixedEmbeddings,
    rewrite_question_if_needed,
    answer_question,
    get_retriever,
    ask_ai,
    build_vector_store,
    _retriever_instance,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_doc(source: str = "test.html", page=None, content: str = "some text"):
    """Create a mock Document-like object."""
    doc = MagicMock()
    doc.metadata = {"source": source, "page": page}
    doc.page_content = content
    return doc


# ---------------------------------------------------------------------------
# TestFormatDocs
# ---------------------------------------------------------------------------

class TestFormatDocs(unittest.TestCase):
    """Tests for format_docs()."""

    def test_format_docs_basic(self):
        docs = [_make_doc(source="a.html", content="text A"),
                _make_doc(source="b.html", content="text B")]
        result = format_docs(docs)
        self.assertIn("Source: a.html", result)
        self.assertIn("text A", result)
        self.assertIn("Source: b.html", result)
        self.assertIn("text B", result)
        self.assertIn("\n\n---\n\n", result)

    def test_format_docs_with_page(self):
        doc = _make_doc(source="a.html", page=3, content="content")
        result = format_docs([doc])
        self.assertIn("Page: 3", result)

    def test_format_docs_without_page(self):
        doc = _make_doc(source="a.html", page=None, content="content")
        result = format_docs([doc])
        self.assertNotIn("Page:", result)
        self.assertIn("Source: a.html", result)

    def test_format_docs_empty_list(self):
        result = format_docs([])
        self.assertEqual(result, "")

    def test_format_docs_max_chars(self):
        docs = [
            _make_doc(source="a.html", content="A" * 100),
            _make_doc(source="b.html", content="B" * 100),
            _make_doc(source="c.html", content="C" * 100),
        ]
        result = format_docs(docs, max_chars=150)
        # Only the first doc should fit
        self.assertIn("Source: a.html", result)
        self.assertNotIn("Source: b.html", result)

    def test_format_docs_default_max_chars(self):
        """With default max_chars=8000 all small docs should fit."""
        docs = [_make_doc(content="short") for _ in range(5)]
        result = format_docs(docs)
        self.assertEqual(result.count("\n\n---\n\n"), 4)

    def test_format_docs_unknown_source(self):
        doc = MagicMock()
        doc.metadata = {}
        doc.page_content = "no metadata"
        result = format_docs([doc])
        self.assertIn("unknown_source", result)


# ---------------------------------------------------------------------------
# TestEnsureContext
# ---------------------------------------------------------------------------

class TestEnsureContext(unittest.TestCase):
    """Tests for ensure_context()."""

    def test_ensure_context_nonempty(self):
        inp = {"context": "some context"}
        result = ensure_context(inp)
        self.assertEqual(result["context"], "some context")
        self.assertIs(result, inp)  # mutated in-place

    def test_ensure_context_empty(self):
        inp = {"context": ""}
        result = ensure_context(inp)
        self.assertIn("Контекст пуст", result["context"])

    def test_ensure_context_whitespace_only(self):
        inp = {"context": "   "}
        result = ensure_context(inp)
        self.assertIn("Контекст пуст", result["context"])

    def test_ensure_context_missing_key(self):
        inp = {"other": "value"}
        result = ensure_context(inp)
        self.assertIn("Контекст пуст", result["context"])


# ---------------------------------------------------------------------------
# TestPrefixedEmbeddings
# ---------------------------------------------------------------------------

class TestPrefixedEmbeddings(unittest.TestCase):
    """Tests for PrefixedEmbeddings class."""

    def setUp(self):
        self.base = MagicMock()
        self.base.embed_documents.return_value = [[0.1, 0.2, 0.3]]
        self.base.embed_query.return_value = [0.4, 0.5, 0.6]

    def test_embed_documents_small_batch(self):
        """<=100 docs should call base.embed_documents."""
        pe = PrefixedEmbeddings(self.base, query_prefix="q:", doc_prefix="d:")
        texts = ["a", "b"]
        result = pe.embed_documents(texts)
        # Check that the prefixed texts were passed
        call_args = self.base.embed_documents.call_args
        prefixed_texts = call_args[0][0]
        self.assertIn("d:a", prefixed_texts)
        self.assertIn("d:b", prefixed_texts)
        self.assertEqual(result, [[0.1, 0.2, 0.3]])

    def test_embed_documents_large_batch(self):
        """>100 docs should use tqdm loop with embed_query."""
        pe = PrefixedEmbeddings(self.base, query_prefix="q:", doc_prefix="d:")
        texts = ["doc_" + str(i) for i in range(150)]
        result = pe.embed_documents(texts)
        # Should NOT call embed_documents for large batches
        self.base.embed_documents.assert_not_called()
        # Should call embed_query for each text
        self.assertEqual(self.base.embed_query.call_count, 150)
        # First call should have the prefixed text
        first_call = self.base.embed_query.call_args_list[0]
        self.assertIn("d:doc_0", first_call[0][0])

    def test_embed_documents_exactly_100(self):
        """Exactly 100 docs should use batch path."""
        pe = PrefixedEmbeddings(self.base, query_prefix="q:", doc_prefix="d:")
        texts = ["t" for _ in range(100)]
        pe.embed_documents(texts)
        self.base.embed_documents.assert_called_once()

    def test_embed_documents_exactly_101(self):
        """Exactly 101 docs should use tqdm loop path."""
        pe = PrefixedEmbeddings(self.base, query_prefix="q:", doc_prefix="d:")
        texts = ["t" for _ in range(101)]
        pe.embed_documents(texts)
        self.base.embed_documents.assert_not_called()
        self.assertEqual(self.base.embed_query.call_count, 101)

    def test_embed_query(self):
        pe = PrefixedEmbeddings(self.base, query_prefix="search_query: ", doc_prefix="search_document: ")
        result = pe.embed_query("my question")
        call_arg = self.base.embed_query.call_args[0][0]
        self.assertEqual(call_arg, "search_query: my question")
        self.assertEqual(result, [0.4, 0.5, 0.6])


# ---------------------------------------------------------------------------
# TestRewriteQuestion
# ---------------------------------------------------------------------------

class TestRewriteQuestion(unittest.TestCase):
    """Tests for rewrite_question_if_needed()."""

    @patch("ai_agent.services.question_rewrite_chain")
    def test_rewrite_returns_question(self, mock_chain):
        mock_chain.invoke.return_value = {"question": "Переписанный вопрос"}
        result = rewrite_question_if_needed("плохой вопрос")
        self.assertEqual(result, "Переписанный вопрос")
        mock_chain.invoke.assert_called_once_with({"question": "плохой вопрос"})

    @patch("ai_agent.services.question_rewrite_chain")
    def test_rewrite_strips_whitespace(self, mock_chain):
        mock_chain.invoke.return_value = {"question": "  answer  "}
        result = rewrite_question_if_needed("q")
        self.assertEqual(result, "answer")

    @patch("ai_agent.services.question_rewrite_chain")
    def test_rewrite_returns_empty_question(self, mock_chain):
        mock_chain.invoke.return_value = {"question": ""}
        result = rewrite_question_if_needed("q")
        self.assertEqual(result, "")


# ---------------------------------------------------------------------------
# TestAnswerQuestion
# ---------------------------------------------------------------------------

class TestAnswerQuestion(unittest.TestCase):
    """Tests for answer_question()."""

    @patch("ai_agent.services.rag_chain")
    def test_answer_question_calls_rag_chain(self, mock_rag_chain):
        mock_rag_chain.invoke.return_value = "Ответ ИИ"
        result = answer_question("Вопрос?", "Контекст")
        mock_rag_chain.invoke.assert_called_once_with(
            {"question": "Вопрос?", "context": "Контекст"}
        )
        self.assertEqual(result, "Ответ ИИ")


# ---------------------------------------------------------------------------
# TestGetRetriever
# ---------------------------------------------------------------------------

class TestGetRetriever(unittest.TestCase):
    """Tests for get_retriever() singleton."""

    def tearDown(self):
        # Reset singleton state after each test
        import ai_agent.services as svc
        svc._retriever_instance = None

    @patch("ai_agent.services._get_retriever")
    def test_first_call_initializes(self, mock_get):
        mock_get.return_value = MagicMock()
        result = get_retriever()
        mock_get.assert_called_once()
        self.assertIs(result, mock_get.return_value)

    @patch("ai_agent.services._get_retriever")
    def test_second_call_returns_cached(self, mock_get):
        mock_get.return_value = MagicMock()
        first = get_retriever()
        second = get_retriever()
        self.assertIs(first, second)
        # _get_retriever should only be called once
        self.assertEqual(mock_get.call_count, 1)


# ---------------------------------------------------------------------------
# TestAskAi
# ---------------------------------------------------------------------------

class TestAskAi(unittest.TestCase):
    """Tests for ask_ai() full pipeline."""

    @patch("ai_agent.services.answer_question")
    @patch("ai_agent.services.format_docs")
    @patch("ai_agent.services.get_retriever")
    @patch("ai_agent.services.rewrite_question_if_needed")
    def test_full_pipeline(self, mock_rewrite, mock_getter, mock_format, mock_answer):
        mock_rewrite.return_value = "rewritten"
        mock_getter.return_value.invoke.return_value = [
            _make_doc(source="a.html", content="doc1"),
            _make_doc(source="b.html", content="doc2"),
        ]
        mock_format.return_value = "formatted context"
        mock_answer.return_value = "AI answer"

        result = ask_ai("original question")

        mock_rewrite.assert_called_once_with("original question")
        mock_getter.return_value.invoke.assert_called_once_with("rewritten")
        mock_format.assert_called_once()
        mock_answer.assert_called_once_with(question="original question", context="formatted context")
        self.assertEqual(result, "AI answer")


# ---------------------------------------------------------------------------
# TestBuildVectorStore
# ---------------------------------------------------------------------------

class TestBuildVectorStore(unittest.TestCase):
    """Tests for build_vector_store()."""

    @patch("ai_agent.services.Chroma")
    def test_cached_retriever(self, mock_chroma_cls):
        """Existing store with docs > 0 should return cached retriever."""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 42
        mock_existing = MagicMock()
        mock_existing._collection = mock_collection
        mock_existing.as_retriever.return_value = "cached_retriever"
        mock_chroma_cls.return_value = mock_existing

        result = build_vector_store()

        self.assertEqual(result, "cached_retriever")
        mock_chroma_cls.assert_called_once()
        mock_existing.as_retriever.assert_called_once_with(
            search_type="mmr", search_kwargs={"k": 8, "fetch_k": 32}
        )

    @patch("ai_agent.services.Chroma")
    def test_empty_store_rebuilds(self, mock_chroma_cls):
        """Existing store with count=0 should rebuild."""
        mock_existing = MagicMock()
        type(mock_existing._collection).count = PropertyMock(return_value=0)
        mock_chroma_cls.return_value = mock_existing

        with patch("ai_agent.services.shutil") as mock_shutil, \
             patch("ai_agent.services.SitemapLoader") as mock_sitemap, \
             patch("ai_agent.services.RecursiveUrlLoader") as mock_recursive, \
             patch("ai_agent.services.RecursiveCharacterTextSplitter") as mock_splitter:

            mock_sitemap.return_value.load.return_value = []
            mock_recursive.return_value.load.return_value = []
            mock_splitter.from_language.return_value.split_documents.return_value = []
            mock_new = MagicMock()
            mock_new.as_retriever.return_value = "new_retriever"
            mock_chroma_cls.from_documents.return_value = mock_new

            result = build_vector_store(force_rebuild=True)

            self.assertEqual(result, "new_retriever")
            mock_shutil.rmtree.assert_not_called()
            mock_chroma_cls.from_documents.assert_called_once()

    @patch("ai_agent.services.Path.exists", return_value=False)
    @patch("ai_agent.services.Chroma")
    def test_no_existing_db_rebuilds(self, mock_chroma_cls, mock_exists):
        """No existing DB should rebuild."""
        with patch("ai_agent.services.SitemapLoader") as mock_sitemap, \
             patch("ai_agent.services.RecursiveUrlLoader") as mock_recursive, \
             patch("ai_agent.services.RecursiveCharacterTextSplitter") as mock_splitter:

            mock_sitemap.return_value.load.return_value = []
            mock_recursive.return_value.load.return_value = []
            mock_splitter.from_language.return_value.split_documents.return_value = []
            mock_new = MagicMock()
            mock_new.as_retriever.return_value = "new_retriever"
            mock_chroma_cls.from_documents.return_value = mock_new

            result = build_vector_store()

            self.assertEqual(result, "new_retriever")
            mock_chroma_cls.from_documents.assert_called_once()


if __name__ == "__main__":
    unittest.main()
