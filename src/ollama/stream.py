"""Stream module for Ollama integration."""

from typing import Generator

from .client import OllamaClient, get_client


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
