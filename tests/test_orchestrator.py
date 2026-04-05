"""
Tests for Orchestrator
"""

import tempfile
from unittest.mock import Mock, patch

import pytest

from orchestrator import Orchestrator, get_orchestrator, run_chat, save_response, get_status
from ollama_client import OllamaConnectionError, stream_response_to_client


class TestOrchestrator:
    """Tests for Orchestrator class."""

    @pytest.fixture
    def mock_retriever(self):
        """Create a mock vault retriever."""
        mock = Mock()
        mock.vault_path = "/test/vault"
        mock.search.return_value = []
        mock.format_context.return_value = ""
        return mock

    @pytest.fixture
    def mock_client(self):
        """Create a mock Ollama client."""
        mock = Mock()
        mock.model = "qwen3-coder-next:cloud"
        mock.stream_chat.return_value = ["This", " is", " a", " test", " response"]
        return mock

    @pytest.fixture
    def orchestrator(self, mock_retriever, mock_client):
        """Create an orchestrator with mocked dependencies."""
        return Orchestrator(
            vault_retriever=mock_retriever,
            ollama_client=mock_client,
        )

    @pytest.fixture(autouse=True)
    def mock_stream(self):
        """Patch stream_response_to_client for all tests."""
        with patch("orchestrator.stream_response_to_client") as mock_stream:
            mock_stream.return_value = ["This", " is", " a", " test", " response"]
            yield mock_stream

    def test_initialization(self, mock_retriever, mock_client):
        """Test orchestrator initialization."""
        orch = Orchestrator(
            vault_retriever=mock_retriever,
            ollama_client=mock_client,
        )

        assert orch.vault_retriever == mock_retriever
        assert orch.ollama_client == mock_client
        assert orch.message_history == []
        assert orch.last_response is None
        assert orch.last_query is None

    def test_build_default_system_prompt(self, mock_retriever):
        """Test default system prompt includes vault path."""
        orch = Orchestrator(vault_retriever=mock_retriever)
        prompt = orch.system_prompt

        assert "Cornelius" in prompt
        assert "local AI assistant" in prompt
        assert "Obsidian knowledge vault" in prompt
        assert "mock" in prompt  # Mock path will contain "mock" in repr

    def test_add_to_history(self, orchestrator):
        """Test message history management."""
        orchestrator._add_to_history("user", "Hello")
        orchestrator._add_to_history("assistant", "Hi there")

        assert len(orchestrator.message_history) == 2
        assert orchestrator.message_history[0] == {"role": "user", "content": "Hello"}
        assert orchestrator.message_history[1] == {"role": "assistant", "content": "Hi there"}

    def test_add_to_history_trims_old(self, orchestrator):
        """Test that old messages are trimmed."""
        orchestrator.max_history = 3
        orchestrator._add_to_history("user", "1")
        orchestrator._add_to_history("user", "2")
        orchestrator._add_to_history("user", "3")
        orchestrator._add_to_history("user", "4")

        # Should only have 3 messages
        assert len(orchestrator.message_history) == 3
        assert orchestrator.message_history[0]["content"] == "2"

    def test_run_success(self, orchestrator):
        """Test successful run."""
        with patch("orchestrator.stream_response_to_client") as mock_stream:
            mock_stream.return_value = ["This", " is", " a", " test", " response"]
            result = orchestrator.run("What is a test?", debug=False)

        # Check response
        assert result == "This is a test response"
        assert orchestrator.last_query == "What is a test?"
        assert orchestrator.last_response == "This is a test response"

        # Check history
        assert len(orchestrator.message_history) == 2
        assert orchestrator.message_history[0]["content"] == "What is a test?"

    def test_run_with_context(self, orchestrator):
        """Test run with vault context."""
        orchestrator.vault_retriever.search.return_value = [
            {"content": "Relevant context", "score": 0.9},
        ]
        orchestrator.vault_retriever.format_context.return_value = "--- VAULT CONTEXT ---\nRelevant context\n--- END CONTEXT ---"

        # Mock the stream function with context-aware response
        with patch("orchestrator.stream_response_to_client") as mock_stream:
            mock_stream.return_value = ["This is a test response"]
            result = orchestrator.run("What is a test?")

        # Should include context in search
        orchestrator.vault_retriever.search.assert_called_once_with("What is a test?")

    def test_run_with_debug(self, orchestrator):
        """Test run with debug mode shows retrieved context."""
        # Set up a real mock console that will be used
        mock_console = Mock()
        orchestrator.console = mock_console

        # Mock the vault_retriever to return context
        orchestrator.vault_retriever.search.return_value = [{"content": "test", "score": 0.9}]
        orchestrator.vault_retriever.format_context.return_value = "--- VAULT CONTEXT ---\nTest context\n--- END CONTEXT ---"

        with patch("orchestrator.stream_response_to_client") as mock_stream:
            mock_stream.return_value = ["Test"]
            orchestrator.run("What is a test?", debug=True)

        # Debug mode should print the context header
        mock_console.print.assert_any_call("[bold yellow]Retrieved Context:[/bold yellow]")

    def test_run_ollama_error(self, orchestrator):
        """Test error handling for Ollama errors."""
        # Patch stream_response_to_client to raise the error
        with patch("orchestrator.stream_response_to_client") as mock_stream:
            mock_stream.side_effect = OllamaConnectionError("Connection refused")
            result = orchestrator.run("What is a test?")

            # Should handle error gracefully
            assert result == ""

    def test_save_last_response(self, orchestrator):
        """Test save_last_response."""
        orchestrator.last_response = "Test response"
        orchestrator.last_query = "Test query"

        mock_writer = Mock()
        mock_writer.write_response.return_value = "/test/vault/inbox/test.md"

        with patch("orchestrator.save_to_vault") as mock_save:
            mock_save.return_value = "/test/vault/inbox/test.md"
            filepath = orchestrator.save_last_response()

            assert filepath == "/test/vault/inbox/test.md"
            mock_save.assert_called_once()

    def test_get_status(self, orchestrator):
        """Test status reporting."""
        orchestrator._add_to_history("user", "Hello")
        orchestrator._add_to_history("assistant", "Hi")

        status = orchestrator.get_status()

        assert status["model"] == "qwen3-coder-next:cloud"
        assert status["vault_path"] == "/test/vault"
        assert status["message_count"] == 2
        assert status["has_last_response"] is False


class TestGetOrchestrator:
    """Tests for get_orchestrator singleton."""

    def test_get_orchestrator_creates_instance(self):
        """Test that get_orchestrator creates a new instance."""
        with patch("orchestrator.Orchestrator") as MockOrch:
            MockOrch.return_value = Mock()
            result = get_orchestrator()
            MockOrch.assert_called_once()

    def test_get_orchestrator_returns_cached(self):
        """Test that get_orchestrator returns cached instance."""
        with patch("orchestrator.Orchestrator") as MockOrch:
            MockOrch.return_value = Mock()
            # First call
            get_orchestrator()
            # Reset
            MockOrch.reset_mock()
            # Second call
            result = get_orchestrator()
            MockOrch.assert_not_called()


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_run_chat(self):
        """Test run_chat convenience function."""
        with patch("orchestrator.get_orchestrator") as mock_get:
            mock_orch = Mock()
            mock_orch.run.return_value = "Response"
            mock_get.return_value = mock_orch

            result = run_chat("test query")

            assert result == "Response"
            mock_orch.run.assert_called_once_with("test query", False)

    def test_save_response(self):
        """Test save_response convenience function."""
        with patch("orchestrator.get_orchestrator") as mock_get:
            mock_orch = Mock()
            mock_orch.save_last_response.return_value = "/path/to/file.md"
            mock_get.return_value = mock_orch

            result = save_response()

            assert result == "/path/to/file.md"
            mock_orch.save_last_response.assert_called_once()

    def test_get_status(self):
        """Test get_status convenience function."""
        with patch("orchestrator.get_orchestrator") as mock_get:
            mock_orch = Mock()
            mock_orch.get_status.return_value = {"model": "test"}
            mock_get.return_value = mock_orch

            result = get_status()

            assert result == {"model": "test"}
            mock_orch.get_status.assert_called_once()