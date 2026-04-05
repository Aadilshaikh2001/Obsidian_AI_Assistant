"""
Tests for Vault Writer
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from vault_writer import VaultWriter, get_writer, save_to_vault


class TestVaultWriter:
    """Tests for VaultWriter class."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            inbox = os.path.join(tmpdir, "inbox")
            os.makedirs(inbox, exist_ok=True)
            yield tmpdir

    def test_initialization(self, temp_vault):
        """Test writer initialization."""
        writer = VaultWriter(
            vault_path=temp_vault,
            inbox_dir="inbox",
        )

        assert writer.vault_path == temp_vault
        assert writer.inbox_dir == "inbox"
        assert os.path.exists(writer.inbox_path)

    def test_write_creates_file(self, temp_vault):
        """Test that write creates a properly formatted file."""
        writer = VaultWriter(vault_path=temp_vault, inbox_dir="inbox")

        filepath = writer.write(
            content="This is a test response.",
            query="What is a test?",
            sources=["projects/test.md"],
        )

        assert filepath is not None
        assert filepath.startswith(writer.inbox_path)
        assert filepath.endswith(".md")

        # Verify file content
        with open(filepath, "r") as f:
            content = f.read()

        assert "---" in content  # Front-matter
        assert "## Response" in content
        assert "This is a test response." in content
        assert "## Context Used" in content
        assert "projects/test.md" in content

    def test_write_unique_filename(self, temp_vault):
        """Test that filenames are unique."""
        writer = VaultWriter(vault_path=temp_vault, inbox_dir="inbox")

        # Write multiple files
        filepath1 = writer.write(content="Response 1", query="test")
        filepath2 = writer.write(content="Response 2", query="test")
        filepath3 = writer.write(content="Response 3", query="different query")

        assert filepath1 != filepath2
        assert filepath3 != filepath1

        # All should be in inbox
        assert os.path.dirname(filepath1) == writer.inbox_path
        assert os.path.dirname(filepath2) == writer.inbox_path
        assert os.path.dirname(filepath3) == writer.inbox_path

    def test_write_no_sources(self, temp_vault):
        """Test writing without sources."""
        writer = VaultWriter(vault_path=temp_vault, inbox_dir="inbox")

        filepath = writer.write(
            content="Test response without sources",
            query="Test query",
        )

        with open(filepath, "r") as f:
            content = f.read()

        assert "---" in content
        assert "## Response" in content
        # No Context Used section since sources not provided
        assert "## Context Used" not in content

    def test_generate_slug(self, temp_vault):
        """Test slug generation."""
        writer = VaultWriter(vault_path=temp_vault, inbox_dir="inbox")

        # Test slug generation
        slug1 = writer._generate_slug("What is BM25 retrieval?")
        slug2 = writer._generate_slug("How does vector search work?")

        assert "bm25" in slug1.lower()
        assert "vector" in slug2.lower()

        # Should be 5 words or less
        assert len(slug1.split("-")) <= 5
        assert len(slug2.split("-")) <= 5

    def test_validate_path_safe(self, temp_vault):
        """Test path validation for safe paths."""
        writer = VaultWriter(vault_path=temp_vault, inbox_dir="inbox")

        assert writer._validate_path(os.path.join(temp_vault, "inbox", "test.md")) is True
        assert writer._validate_path(temp_vault) is True

    def test_validate_path_unsafe(self, temp_vault):
        """Test path validation for unsafe paths."""
        writer = VaultWriter(vault_path=temp_vault, inbox_dir="inbox")

        # Outside vault path
        assert writer._validate_path("/etc/passwd") is False
        assert writer._validate_path(os.path.join(temp_vault, "..", "outside")) is False

    def test_write_response(self, temp_vault):
        """Test write_response convenience method."""
        writer = VaultWriter(vault_path=temp_vault, inbox_dir="inbox")

        sources = [
            {"source": "projects/test.md", "title": "Test", "heading": "Introduction"},
        ]

        filepath = writer.write_response(
            response="Test response",
            query="Test query",
            sources=sources,
        )

        with open(filepath, "r") as f:
            content = f.read()

        assert "projects/test.md" in content


class TestGetWriter:
    """Tests for get_writer singleton."""

    def test_get_writer_creates_instance(self):
        """Test that get_writer creates a new instance."""
        with patch("vault_writer.VaultWriter") as MockWriter:
            MockWriter.return_value = Mock()
            result = get_writer(vault_path="/test/vault")
            MockWriter.assert_called_once()
            MockWriter.assert_called_with("/test/vault", "inbox")

    def test_get_writer_returns_cached(self):
        """Test that get_writer returns cached instance."""
        with patch("vault_writer.VaultWriter") as MockWriter:
            MockWriter.return_value = Mock()
            # First call
            get_writer()
            # Reset
            MockWriter.reset_mock()
            # Second call
            result = get_writer()
            MockWriter.assert_not_called()


class TestSaveToVault:
    """Tests for save_to_vault convenience function."""

    def test_save_to_vault_calls_writer(self):
        """Test that save_to_vault delegates to writer."""
        mock_writer = Mock()
        mock_writer.write_response.return_value = "/path/to/file.md"

        with patch("vault_writer.get_writer") as mock_get:
            mock_get.return_value = mock_writer
            result = save_to_vault(
                response="Test response",
                query="Test query",
                sources=[],
            )

            assert result == "/path/to/file.md"
            mock_writer.write_response.assert_called_once()


class TestIntegration:
    """Integration tests (requires file system)."""

    def test_full_write_cycle(self, tmp_path):
        """Test complete write cycle with file system."""
        writer = VaultWriter(vault_path=tmp_path, inbox_dir="inbox")

        # Write a file
        filepath = writer.write(
            content="This is a test response that should be written to the vault.",
            query="Test query for vault writer",
            sources=["projects/test-note.md"],
        )

        # Verify file was created
        assert os.path.exists(filepath)

        # Verify content
        with open(filepath, "r") as f:
            content = f.read()

        assert "---" in content  # Has front-matter
        assert "## Response" in content
        assert "Test query for vault writer" in content
        assert "projects/test-note.md" in content

        # Verify no duplicate writes
        filepath2 = writer.write(
            content="Second test",
            query="Test query for vault writer",  # Same query
        )
        assert filepath2 != filepath  # Different filename
        assert os.path.exists(filepath2)