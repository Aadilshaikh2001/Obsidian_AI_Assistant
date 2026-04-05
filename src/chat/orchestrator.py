"""
Orchestrator

Coordinates the chat flow: vault retrieval → prompt building → LLM call → streaming.
"""

import os
from typing import Optional

import yaml
from rich.console import Console
from rich.markdown import Markdown

from ollama import OllamaClient, OllamaConnectionError, stream_response_to_client
from vault import VaultRetriever, get_retriever, search_vault, save_to_vault


class Orchestrator:
    """
    Core orchestration of chat, retrieval, and LLM calls.

    Manages session state and coordinates between vault retriever,
    LLM client, and output streaming.
    """

    def __init__(
        self,
        vault_retriever: VaultRetriever = None,
        ollama_client: OllamaClient = None,
        system_prompt: str = None,
        max_history: int = 20,
    ):
        """
        Initialize the orchestrator.

        Args:
            vault_retriever: VaultRetriever instance.
            ollama_client: OllamaClient instance.
            system_prompt: Custom system prompt. Defaults to built-in.
            max_history: Maximum messages to keep in history.
        """
        self.vault_retriever = vault_retriever or get_retriever()
        self.ollama_client = ollama_client or OllamaClient()

        # Default system prompt
        self.system_prompt = system_prompt or self._build_default_system_prompt()

        # Session state
        self.message_history: list[dict] = []
        self.last_response: Optional[str] = None
        self.last_query: Optional[str] = None
        self.max_history = max_history

        # Console for formatted output
        self.console = Console()

    def _build_default_system_prompt(self) -> str:
        """Build the default system prompt."""
        vault_path = self.vault_retriever.get_vault_path()

        return f"""You are Cornelius, a local AI assistant with access to Aadil's Obsidian knowledge vault.

Your role:
- Answer questions accurately and concisely
- Use the vault context provided to ground your answers in the user's existing notes
- When vault context is relevant, cite the source file naturally in your answer
- When vault context is not relevant, answer from your own knowledge
- Never fabricate vault contents — only use what is explicitly provided

Vault context will be injected between --- VAULT CONTEXT --- markers above the user message.
If no context is provided, the vault had no relevant notes for this query.

Style:
- Respond in plain text (no markdown unless user asks)
- Be direct and technical — the user is a developer and PM
- Do not start responses with "Certainly!", "Great question!", or similar filler
- Keep responses under 400 words unless the user asks for detailed output
- If saving a response to vault makes sense, end your response with: [Save-worthy: yes/no]

Vault path: {vault_path}"""

    def _add_to_history(self, role: str, content: str) -> None:
        """Add a message to history, trimming old messages if needed."""
        self.message_history.append({
            "role": role,
            "content": content,
        })

        # Trim history if needed
        while len(self.message_history) > self.max_history:
            self.message_history.pop(0)

    def _build_messages(self, user_message: str, context: str = "") -> list[dict]:
        """Build the full message list for the LLM."""
        messages = [
            {"role": "system", "content": self.system_prompt},
        ]

        # Add context if provided
        if context:
            messages.append({
                "role": "user",
                "content": f"{context}\n\n{user_message}",
            })
        else:
            messages.append({
                "role": "user",
                "content": user_message,
            })

        # Add prior conversation history
        messages.extend(self.message_history[-(self.max_history - 2):])

        return messages

    def _get_vault_context(self, query: str) -> str:
        """Get and format vault context for a query."""
        chunks = self.vault_retriever.search(query)
        return self.vault_retriever.format_context(chunks)

    def run(self, user_message: str, debug: bool = False) -> str:
        """
        Execute a user query through the full pipeline.

        Args:
            user_message: The user's input text.
            debug: If True, show retrieved context before LLM call.

        Returns:
            The full AI response string.
        """
        # Store the query for later
        self.last_query = user_message

        # Retrieve vault context
        context = self._get_vault_context(user_message)

        if debug and context:
            self.console.print("[bold yellow]Retrieved Context:[/bold yellow]")
            self.console.print(context)
            self.console.print()

        # Build full message list
        messages = self._build_messages(user_message, context)

        # Track response tokens
        response_tokens = []

        # Stream the response
        self.console.print("[bold cyan]Cornelius:[/bold cyan] ", end="")

        try:
            for token in stream_response_to_client(messages):
                print(token, end="", flush=True)
                response_tokens.append(token)

        except OllamaConnectionError as e:
            self.console.print(f"[bold red]Error:[/bold red] {e}")
            return ""

        print()  # Newline after streaming

        # Store full response
        self.last_response = "".join(response_tokens)
        self._add_to_history("user", user_message)
        self._add_to_history("assistant", self.last_response)

        return self.last_response

    def save_last_response(self) -> Optional[str]:
        """
        Save the last response to the vault inbox.

        Returns:
            Path to created file, or None if no last response.
        """
        if not self.last_response:
            self.console.print("[yellow]No response to save.[/yellow]")
            return None

        sources = self.vault_retriever.search(self.last_query or "")
        filepath = save_to_vault(
            response=self.last_response,
            query=self.last_query or "AI Response",
            sources=sources,
        )

        self.console.print(f"[green]Saved to:[/green] {filepath}")
        return filepath

    def get_status(self) -> dict:
        """Get current session status."""
        return {
            "model": self.ollama_client.model,
            "vault_path": self.vault_retriever.vault_path,
            "message_count": len(self.message_history),
            "has_last_response": self.last_response is not None,
        }


# Convenience singleton
_orchestrator = None


def get_orchestrator() -> Orchestrator:
    """Get or create the orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


def run_chat(user_message: str, debug: bool = False) -> str:
    """
    Convenience function to run a chat query.

    Args:
        user_message: User input text.
        debug: Show debug output.

    Returns:
        AI response string.
    """
    orchestrator = get_orchestrator()
    return orchestrator.run(user_message, debug)


def save_response() -> Optional[str]:
    """Convenience function to save the last response."""
    orchestrator = get_orchestrator()
    return orchestrator.save_last_response()


def get_status() -> dict:
    """Convenience function to get status."""
    orchestrator = get_orchestrator()
    return orchestrator.get_status()
