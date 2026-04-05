"""
Ollama Client Adapter

Replaces the Anthropic SDK with Ollama HTTP API calls.
Handles streaming responses and error handling.
"""

import json
import os
from typing import Generator

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class OllamaConnectionError(Exception):
    """Raised when Ollama is not running or unreachable."""
    pass


class OllamaModelNotFoundError(Exception):
    """Raised when the specified model is not found in Ollama."""
    pass


class OllamaTimeoutError(Exception):
    """Raised when the request exceeds the timeout."""
    pass


class OllamaClient:
    """Ollama HTTP client for chat completions with streaming support."""

    def __init__(
        self,
        host: str = None,
        model: str = None,
        timeout: int = 120,
    ):
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen3-coder-next:cloud")
        self.timeout = timeout

    def stream_chat(
        self, messages: list[dict], model: str = None
    ) -> Generator[str, None, None]:
        """
        POST to Ollama /api/chat endpoint with streaming.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                      Format: [{"role": "system", "content": "..."},
                               {"role": "user", "content": "..."}]
            model: Optional model name override.

        Yields:
            Token strings as they arrive from the stream.

        Raises:
            OllamaConnectionError: If Ollama is not running.
            OllamaModelNotFoundError: If model doesn't exist.
            OllamaTimeoutError: If request exceeds timeout.
        """
        model = model or self.model
        url = f"{self.host}/api/chat"

        try:
            response = requests.post(
                url,
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": 0.7,
                        "num_ctx": 4096,
                    },
                },
                stream=True,
                timeout=self.timeout,
            )

            # Check for model not found (HTTP 404)
            if response.status_code == 404:
                raise OllamaModelNotFoundError(
                    f"Model '{model}' not found. Pull with: ollama pull {model}"
                )

            # Check for connection errors
            response.raise_for_status()

            # Stream the response
            for line in response.iter_lines():
                if line:
                    # Decode the line
                    line_str = line.decode("utf-8")
                    if not line_str.strip():
                        continue

                    # Parse JSON chunk
                    try:
                        chunk = json.loads(line_str)
                    except json.JSONDecodeError:
                        continue

                    # Extract token content
                    token = chunk.get("message", {}).get("content", "")

                    # Yield the token if present
                    if token:
                        yield token

                    # Check for done signal
                    if chunk.get("done", False):
                        break

        except requests.exceptions.ConnectionError:
            raise OllamaConnectionError(
                "Ollama not running. Start with: ollama serve"
            )
        except requests.exceptions.Timeout:
            raise OllamaTimeoutError(
                f"Request timed out after {self.timeout} seconds"
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise OllamaModelNotFoundError(
                    f"Model '{model}' not found. Pull with: ollama pull {model}"
                )
            raise

    def get_available_models(self) -> list[str]:
        """
        Get list of available models from Ollama.

        Returns:
            List of model names.

        Raises:
            OllamaConnectionError: If Ollama is not running.
        """
        url = f"{self.host}/api/tags"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            return [model.get("name") for model in data.get("models", [])]
        except requests.exceptions.ConnectionError:
            raise OllamaConnectionError(
                "Ollama not running. Start with: ollama serve"
            )


# Convenience singleton
_client = None


def get_client() -> OllamaClient:
    """Get or create the Ollama client singleton."""
    global _client
    if _client is None:
        _client = OllamaClient()
    return _client


def stream_response_to_client(
    messages: list[dict], model: str = None
) -> Generator[str, None, None]:
    """
    Convenience function to stream a response from Ollama.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
        model: Optional model name override.

    Yields:
        Token strings as they arrive.
    """
    client = get_client()
    yield from client.stream_chat(messages, model)
