"""
Tests for Vault Retriever
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from vault_retriever import VaultRetriever, get_retriever, search_vault


class TestVaultRetriever:
    """Tests for VaultRetriever class."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault directory with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test markdown files
            os.makedirs(os.path.join(tmpdir, "projects"), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, "daily"), exist_ok=True)

            # Create test files
            with open(os.path.join(tmpdir, "projects", "rag-notes.md"), "w") as f:
                f.write("""---
title: "RAG Notes"
tags: [rag, retrieval]
---

## BM25 Explanation

BM25 is a bag-of-words ranking function used by search engines.

## Vector Search

Vector search uses embeddings to find similar documents.

## Hybrid Search

Hybrid search combines lexical and semantic search.
""")

            with open(os.path.join(tmpdir, "daily", "2026-03-15.md"), "w") as f:
                f.write("""---
title: "Daily Notes - March 15"
tags: [daily, meeting]
---

## Meeting Notes

Discussed retrieval pipeline with team.

## Project Update

Working on RAG implementation.
""")

            yield tmpdir

    def test_initialization(self, temp_vault):
        """Test retriever initialization."""
        retriever = VaultRetriever(
            vault_path=temp_vault,
            top_k=3,
            min_score=0.1,
        )

        assert retriever.vault_path == temp_vault
        assert retriever.top_k == 3
        assert retriever.min_score == 0.1

    def test_reindex_finds_files(self, temp_vault):
        """Test that reindex finds and indexes files."""
        retriever = VaultRetriever(
            vault_path=temp_vault,
            top_k=3,
            min_score=0.1,
        )

        # Reindex to load files
        retriever.reindex()

        assert retriever.indexed is True
        assert len(retriever.chunks) > 0

    def test_search_returns_results(self, temp_vault):
        """Test search functionality."""
        retriever = VaultRetriever(
            vault_path=temp_vault,
            top_k=3,
            min_score=0.1,
        )
        retriever.reindex()

        # Search for "BM25"
        results = retriever.search("BM25")

        assert len(results) >= 1
        assert any("BM25" in r["content"] or "bm25" in r["content"].lower() for r in results)

    def test_search_with_min_score_filter(self, temp_vault):
        """Test that min_score filter works."""
        retriever = VaultRetriever(
            vault_path=temp_vault,
            top_k=5,
            min_score=0.5,  # High threshold
        )
        retriever.reindex()

        results = retriever.search("BM25")

        # With high threshold, should have fewer or no results
        assert all(r["score"] >= 0.5 for r in results)

    def test_format_context(self, temp_vault):
        """Test context formatting."""
        retriever = VaultRetriever(
            vault_path=temp_vault,
            top_k=3,
            min_score=0.1,
        )
        retriever.reindex()

        # Get some results
        results = retriever.search("BM25")

        if results:
            context = retriever.format_context(results)
            assert "--- VAULT CONTEXT ---" in context
            assert "--- END CONTEXT ---" in context
            assert "Source:" in context

    def test_excludes_directories(self, temp_vault):
        """Test that excluded directories are skipped."""
        # Create an .obsidian directory with a markdown file
        obsidian_dir = os.path.join(temp_vault, ".obsidian")
        os.makedirs(obsidian_dir, exist_ok=True)
        with open(os.path.join(obsidian_dir, "config.md"), "w") as f:
            f.write("---\ntitle: Config\n---\nTheme: dark")

        retriever = VaultRetriever(
            vault_path=temp_vault,
            top_k=3,
            min_score=0.1,
        )
        retriever.reindex()

        # The config.md should not be in results
        results = retriever.search("config")
        # No results expected since .obsidian is excluded
        assert len(results) == 0


class TestGetRetriever:
    """Tests for get_retriever singleton."""

    def test_get_retriever_creates_instance(self):
        """Test that get_retriever creates a new instance."""
        with patch("vault_retriever.VaultRetriever") as MockRetriever:
            MockRetriever.return_value = Mock()
            result = get_retriever(vault_path="/test/path")
            MockRetriever.assert_called_once()
            MockRetriever.assert_called_with("/test/path", 3, 0.1)

    def test_get_retriever_returns_cached(self):
        """Test that get_retriever returns cached instance."""
        with patch("vault_retriever.VaultRetriever") as MockRetriever:
            MockRetriever.return_value = Mock()
            # First call
            get_retriever()
            # Reset
            MockRetriever.reset_mock()
            # Second call
            result = get_retriever()
            MockRetriever.assert_not_called()


class TestSearchVault:
    """Tests for search_vault convenience function."""

    def test_search_vault_calls_retriever(self):
        """Test that search_vault delegates to retriever."""
        mock_retriever = Mock()
        mock_retriever.search.return_value = [
            {"content": "test", "score": 1.0},
        ]

        with patch("vault_retriever.get_retriever") as mock_get:
            mock_get.return_value = mock_retriever
            results = search_vault("test query", top_k=5)

            assert results == [{"content": "test", "score": 1.0}]
            mock_retriever.search.assert_called_once_with("test query", 5)