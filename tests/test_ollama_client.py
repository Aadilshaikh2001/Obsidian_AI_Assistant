"""
Tests for Ollama Client
"""

import json
from unittest.mock import Mock, patch

import pytest
import requests.exceptions

from ollama_client import (
    OllamaClient,
    OllamaConnectionError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
    get_client,
)


class TestOllamaClient:
    """Tests for OllamaClient class."""

    @pytest.fixture
    def client(self):
        """Create OllamaClient instance."""
        return OllamaClient(
            host="http://localhost:11434",
            model="qwen3-coder-next:cloud",
            timeout=30,
        )

    @patch("requests.post")
    def test_stream_chat_success(self, mock_post, client):
        """Test successful streaming chat."""
        # Mock response chunks
        mock_response = Mock()
        mock_response.iter_lines.return_value = [
            b'{"message":{"content":"Hello"},"done":false}',
            b'{"message":{"content":" world"},"done":false}',
            b'{"message":{"content":"!"},"done":true}',
        ]
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Say hello."},
        ]

        tokens = list(client.stream_chat(messages))

        assert tokens == ["Hello", " world", "!"]
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["model"] == "qwen3-coder-next:cloud"
        assert call_args[1]["json"]["stream"] is True

    @patch("requests.post")
    def test_stream_chat_connection_error(self, mock_post, client):
        """Test connection error handling."""
        mock_post.side_effect = requests.exceptions.ConnectionError()

        with pytest.raises(OllamaConnectionError):
            list(client.stream_chat([{"role": "user", "content": "test"}]))

    @patch("requests.post")
    def test_stream_chat_model_not_found(self, mock_post, client):
        """Test model not found error handling."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response

        with pytest.raises(OllamaModelNotFoundError) as exc_info:
            list(client.stream_chat([{"role": "user", "content": "test"}]))

        assert "not found" in str(exc_info.value).lower()

    @patch("requests.post")
    def test_stream_chat_timeout(self, mock_post, client):
        """Test timeout error handling."""
        import requests.exceptions

        mock_post.side_effect = requests.exceptions.Timeout()

        with pytest.raises(OllamaTimeoutError):
            list(client.stream_chat([{"role": "user", "content": "test"}]))

    @patch("requests.get")
    def test_get_available_models(self, mock_get, client):
        """Test getting available models."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "qwen3-coder-next:cloud"},
                {"name": "llama3:8b"},
                {"name": "mistral:7b"},
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        models = client.get_available_models()

        assert models == ["qwen3-coder-next:cloud", "llama3:8b", "mistral:7b"]

    @patch("requests.get")
    def test_get_available_models_connection_error(self, mock_get, client):
        """Test connection error when listing models."""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        with pytest.raises(OllamaConnectionError):
            client.get_available_models()


class TestOllamaClientIntegration:
    """Integration tests (requires Ollama running)."""

    def test_actual_connection_if_available(self):
        """Test actual Ollama connection (if available)."""
        client = OllamaClient()

        # This will only work if Ollama is running
        try:
            models = client.get_available_models()
            assert len(models) >= 1
        except OllamaConnectionError:
            # Ollama not running, test skipped
            pytest.skip("Ollama not running")

    @patch("requests.post")
    def test_actual_streaming(self, mock_post):
        """Test actual streaming behavior."""
        # Simulate real Ollama response format
        mock_response = Mock()
        mock_response.iter_lines.return_value = [
            b'{"model":"qwen3-coder-next:cloud","created_at":"2024-01-01T00:00:00.000Z","message":{"role":"assistant","content":"Test"},"done":false}',
            b'{"model":"qwen3-coder-next:cloud","created_at":"2024-01-01T00:00:00.100Z","message":{"role":"assistant","content":" response"},"done":false}',
            b'{"model":"qwen3-coder-next:cloud","created_at":"2024-01-01T00:00:00.200Z","message":{"role":"assistant","content":"."},"done":true,"done_reason":"stop","eval_count":5}',
        ]
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = OllamaClient()
        tokens = list(client.stream_chat([{"role": "user", "content": "test"}]))

        assert tokens == ["Test", " response", "."]


class TestGetClient:
    """Tests for get_client singleton."""

    def test_get_client_creates_instance(self):
        """Test that get_client creates a new instance if none exists."""
        with patch("ollama_client.OllamaClient") as MockClient:
            MockClient.return_value = Mock()
            result = get_client()
            MockClient.assert_called_once()

    def test_get_client_returns_cached(self):
        """Test that get_client returns cached instance."""
        with patch("ollama_client.OllamaClient") as MockClient:
            MockClient.return_value = Mock()
            # First call creates instance
            get_client()
            # Reset mock
            MockClient.reset_mock()
            # Second call returns cached
            result = get_client()
            MockClient.assert_not_called()