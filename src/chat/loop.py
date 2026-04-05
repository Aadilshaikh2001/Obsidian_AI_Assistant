"""
Chat Loop — Terminal REPL Entry Point

Runs a blocking input/output loop for the Cornelius-Ollama assistant.
"""

import argparse
import os
import sys
from datetime import datetime

import yaml
from rich.console import Console
from rich.markdown import Markdown

from .orchestrator import Orchestrator, get_orchestrator, save_response


class ChatLoop:
    """
    Terminal REPL for Cornelius-Ollama.

    Handles user input, commands, and orchestrator coordination.
    """

    def __init__(self, orchestrator: Orchestrator = None):
        """Initialize the chat loop."""
        self.orchestrator = orchestrator or get_orchestrator()
        self.console = Console()
        self.last_response = ""

    def print_welcome(self) -> None:
        """Print welcome banner on startup."""
        status = self.orchestrator.get_status()

        self.console.print(
            "[bold]═══════════════════════════════════════════════[/bold]"
        )
        self.console.print(
            "  [bold]Cornelius-Ollama[/bold] | "
            f"Model: {status['model']} | "
            f"Vault: {os.path.basename(status['vault_path'])}"
        )
        self.console.print(
            "  Type [bold]/help[/bold] for commands. [bold]/quit[/bold] to exit."
        )
        self.console.print(
            "[bold]═══════════════════════════════════════════════[/bold]"
        )
        self.console.print()

    def print_help(self) -> None:
        """Print available commands."""
        commands = [
            ("[bold]/quit[/bold] or [bold]/exit[/bold]", "Graceful shutdown"),
            ("[bold]/help[/bold]", "Print this help message"),
            ("[bold]/save[/bold]", "Write last response to vault [bold]inbox/[/bold]"),
            ("[bold]/clear[/bold]", "Clear session message history"),
            ("[bold]/reload[/bold]", "Reindex vault files"),
            ("[bold]/voice[/bold]", "Record and transcribe voice input"),
            ("[bold]/vault[/bold] <query>", "Raw vault search, print top chunks"),
            ("[bold]/model[/bold] <name>", "Switch model mid-session (hot swap)"),
            ("[bold]/status[/bold]", "Show model name, vault path, message count"),
            ("[bold]/debug[/bold]", "Toggle debug mode (show context chunks)"),
        ]

        self.console.print("[bold]Available Commands:[/bold]")
        for cmd, desc in commands:
            self.console.print(f"  {cmd:30} {desc}")
        self.console.print()

    def handle_voice_command(self) -> None:
        """Handle the /voice command - record, transcribe, and send."""
        try:
            # Load config for voice settings
            config_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "config.yaml"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f) or {}
                voice_config = config.get("voice", {})
                model = voice_config.get("model", "base")
                language = voice_config.get("language", "en")
            else:
                model = "base"
                language = "en"

            # Import here to avoid circular dependency
            from ..voice import VoiceProcessor
            voice_processor = VoiceProcessor(model_name=model, language=language)

            # Record and transcribe
            text = voice_processor.record_and_get_text()

            if text:
                # Send to orchestrator
                print()
                response = self.orchestrator.run(text)
                self.last_response = response
                print()
            else:
                self.console.print(
                    "[yellow]Voice input cancelled.[/yellow]"
                )

        except ImportError as e:
            self.console.print(
                f"[bold red]Voice feature not available:[/bold red] {e}"
            )
            self.console.print(
                "[dim]Install with: pip install openai-whisper sounddevice soundfile[/dim]"
            )
        except Exception as e:
            self.console.print(
                f"[bold red]Error recording voice:[/bold red] {e}"
            )

    def print_vault_results(self, query: str) -> None:
        """Print vault search results without LLM call."""
        chunks = self.orchestrator.vault_retriever.search(query)

        if not chunks:
            self.console.print(f"[yellow]No results for: {query}[/yellow]")
            return

        self.console.print(f"[bold]Vault Search: {query}[/bold]")
        self.console.print()

        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("source", "unknown")
            heading = chunk.get("heading", "Content")
            title = chunk.get("title", "Note")
            content = chunk.get("content", "")[:500]  # Truncate
            score = chunk.get("score", 0)

            self.console.print(f"[bold]Result {i}[/bold] (score: {score:.3f})")
            self.console.print(f"  [dim]Source:[/dim] {source} | [dim]Section:[/dim] ## {heading}")
            self.console.print(f"  {content}...")
            self.console.print()

    def handle_command(self, line: str) -> bool:
        """
        Handle a command line (starting with /).

        Args:
            line: Full input line including / prefix.

        Returns:
            True if should continue, False if should quit.
        """
        parts = line.strip().split(None, 1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("/quit", "/exit"):
            self.console.print("[green]Goodbye![/green]")
            return False

        elif cmd == "/help":
            self.print_help()

        elif cmd == "/save":
            filepath = save_response()
            if filepath:
                self.last_response = ""

        elif cmd == "/voice":
            self.handle_voice_command()

        elif cmd == "/clear":
            self.orchestrator.message_history.clear()
            self.last_response = ""
            self.console.print("[green]Session history cleared.[/green]")

        elif cmd == "/vault":
            if arg:
                # Remove angle brackets if present
                query = arg.strip("<>")
                self.console.print(f"[bold]Searching vault for: {query}[/bold]")
                chunks = self.orchestrator.vault_retriever.search(query)
                self.console.print(f"[INFO] Found {len(chunks)} matching chunks")
                if not chunks:
                    self.console.print("[yellow]No results for: " + query + "[/yellow]")
                else:
                    for i, chunk in enumerate(chunks, 1):
                        source = chunk.get("source", "unknown")
                        heading = chunk.get("heading", "Content")
                        content = chunk.get("content", "")[:300]
                        self.console.print(f"[bold]Result {i}[/bold] (score: {chunk.get('score', 0):.2f})")
                        self.console.print(f"  [dim]{source} | ## {heading}[/dim]")
                        self.console.print(f"  {content}...")
                        self.console.print()
            else:
                self.console.print("[yellow]Usage: /vault <query>[/yellow]")

        elif cmd == "/model":
            if arg:
                self.orchestrator.ollama_client.model = arg
                self.console.print(f"[green]Model set to: {arg}[/green]")
            else:
                self.console.print(f"[yellow]Current model: {self.orchestrator.ollama_client.model}[/yellow]")

        elif cmd == "/status":
            status = self.orchestrator.get_status()
            self.console.print(f"[bold]Model:[/bold] {status['model']}")
            self.console.print(f"[bold]Vault:[/bold] {status['vault_path']}")
            self.console.print(f"[bold]Messages:[/bold] {status['message_count']}")
            self.console.print()

        elif cmd == "/reload":
            self.console.print("[yellow]Reloading vault index...[/yellow]")
            self.orchestrator.vault_retriever.reindex()
            status = self.orchestrator.get_status()
            self.console.print(f"[green]Vault reloaded: {status['vault_path']}[/green]")

        elif cmd == "/debug":
            # Toggle debug mode
            self.console.print("[yellow]Debug mode not implemented yet.[/yellow]")

        else:
            self.console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
            self.console.print("Type [bold]/help[/bold] for available commands.")

        return True

    def run(self) -> None:
        """Run the main REPL loop."""
        self.print_welcome()

        while True:
            try:
                # Get user input
                user_input = input("> ").strip()

                if not user_input:
                    continue

                # Check for commands
                if user_input.startswith("/"):
                    should_continue = self.handle_command(user_input)
                    if not should_continue:
                        break
                    continue

                # Regular chat query
                print()
                response = self.orchestrator.run(user_input)
                self.last_response = response
                print()

            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                print()
                self.console.print("[yellow]Interrupted.[/yellow]")
                continue

            except EOFError:
                # Handle Ctrl+D (Unix) or Ctrl+Z+Enter (Windows)
                print()
                self.console.print("[green]Goodbye![/green]")
                break

            except Exception as e:
                # Catch any other errors
                self.console.print(f"[bold red]Error:[/bold red] {e}")
                continue


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Cornelius-Ollama: Terminal AI Assistant"
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        help="Override model name",
    )
    parser.add_argument(
        "--no-vault",
        action="store_true",
        help="Disable vault retrieval",
    )
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="Rebuild vault index on startup",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    parser.add_argument(
        "--vault-path",
        type=str,
        help="Override vault path",
    )

    args = parser.parse_args()

    # Create orchestrator with overrides if needed
    orchestrator = get_orchestrator()

    # Apply model override
    if args.model:
        orchestrator.ollama_client.model = args.model

    # Apply vault path override
    if args.vault_path:
        orchestrator.vault_retriever.vault_path = args.vault_path
        orchestrator.vault_retriever.inbox_path = os.path.join(
            args.vault_path,
            orchestrator.vault_retriever.inbox_path,
        )

    # Reindex if requested
    if args.reindex:
        orchestrator.vault_retriever.reindex()

    # Run the chat loop
    chat = ChatLoop(orchestrator)
    chat.run()


if __name__ == "__main__":
    main()
