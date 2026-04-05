"""
Vault Writer

Writes AI-generated content as atomic Markdown notes to the vault's inbox.
"""

import os
import re
import shutil
from datetime import datetime
from typing import Optional


class VaultWriter:
    """
    Atomic writer for AI-generated notes in Obsidian vault.

    Writes .md files to the vault inbox folder with proper
    front-matter and generates unique filenames.
    """

    def __init__(
        self,
        vault_path: str,
        inbox_dir: str = "inbox",
    ):
        """
        Initialize the vault writer.

        Args:
            vault_path: Path to the Obsidian vault directory.
            inbox_dir: Name of the inbox subdirectory.
        """
        self.vault_path = os.path.abspath(vault_path)
        self.inbox_dir = inbox_dir
        self.inbox_path = os.path.join(self.vault_path, inbox_dir)

        # Create inbox directory if it doesn't exist
        os.makedirs(self.inbox_path, exist_ok=True)

    def _validate_path(self, path: str) -> bool:
        """
        Validate that a path stays within the vault directory.

        Args:
            path: Path to validate.

        Returns:
            True if path is safe, False otherwise.
        """
        # Resolve to absolute path
        abs_path = os.path.abspath(path)

        # Check if it's under vault path
        return abs_path.startswith(self.vault_path + os.sep) or abs_path == self.vault_path

    def _generate_slug(self, query: str) -> str:
        """
        Generate a 5-word kebab-case slug from a query.

        Args:
            query: User query string.

        Returns:
            Slug string (e.g., "what-is-bm25-retrieval").
        """
        # Tokenize and clean
        words = re.findall(r"\b\w+\b", query.lower())

        # Take first 5 words
        words = words[:5]

        # Join with hyphens
        return "-".join(words) if words else "ai-response"

    def _generate_filename(self, query: str) -> str:
        """
        Generate a unique filename for the new note.

        Args:
            query: User query for slug generation.

        Returns:
            Full path to the new .md file.
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        slug = self._generate_slug(query)

        # Try to generate a unique filename
        counter = 0
        while True:
            if counter == 0:
                filename = f"ai-{date_str}-{slug}.md"
            else:
                filename = f"ai-{date_str}-{slug}-{counter}.md"

            filepath = os.path.join(self.inbox_path, filename)
            if not os.path.exists(filepath):
                return filepath

            counter += 1
            if counter > 100:
                # Fallback with timestamp
                timestamp = datetime.now().strftime("%H%M%S")
                return os.path.join(
                    self.inbox_path,
                    f"ai-{date_str}-{timestamp}.md",
                )

    def write(
        self,
        content: str,
        query: str,
        sources: list[str] = None,
        title: str = None,
    ) -> str:
        """
        Write content to a new note in the vault inbox.

        Args:
            content: Main content to write (markdown or plain text).
            query: Original user query (used for slug and metadata).
            sources: List of source file paths used for context.
            title: Optional custom title.

        Returns:
            Path to the created file.
        """
        # Generate filename
        filepath = self._generate_filename(query)

        # Validate path
        if not self._validate_path(filepath):
            raise ValueError("Invalid file path: outside vault directory")

        # Generate metadata
        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M:%S")
        custom_title = title or f"AI Response — {query[:50]}..."

        # Build front-matter
        frontmatter_lines = [
            "---",
            f"title: \"{custom_title}\"",
            f"date: {date_str}",
            "tags:",
            "  - ai-generated",
            "  - source/cornelius-ollama",
            'source: "Cornelius-Ollama | qwen3-coder-next:cloud"',
            f'query: "{query}"',
            "---",
            "",
        ]

        # Build content
        content_lines = [
            f"## Response",
            "",
            content,
            "",
        ]

        # Add context section if sources provided
        if sources:
            content_lines.extend([
                "## Context Used",
                "",
            ])
            for source in sources:
                content_lines.append(f"- {source}")
            content_lines.append("")

        # Combine all parts
        full_content = "\n".join(frontmatter_lines + content_lines)

        # Atomic write: write to temp file, then rename
        temp_filepath = filepath + ".tmp"

        try:
            # Write to temp file
            with open(temp_filepath, "w", encoding="utf-8") as f:
                f.write(full_content)

            # Move to final location (atomic on most systems)
            shutil.move(temp_filepath, filepath)

        except Exception as e:
            # Cleanup temp file on error
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            raise e

        return filepath

    def write_response(
        self,
        response: str,
        query: str,
        sources: list[dict] = None,
    ) -> str:
        """
        Write an AI response to vault with context.

        Args:
            response: Full AI response string.
            query: Original user query.
            sources: List of source chunk dicts from vault_retriever.

        Returns:
            Path to created file.
        """
        # Extract source paths from chunks
        source_paths = []
        if sources:
            for chunk in sources:
                source = chunk.get("source", "unknown")
                source_paths.append(source)

        return self.write(
            content=response,
            query=query,
            sources=source_paths,
        )


# Convenience singleton
_writer = None


def get_writer(vault_path: str = None, inbox_dir: str = None) -> VaultWriter:
    """
    Get or create the vault writer singleton.

    Args:
        vault_path: Override vault path.
        inbox_dir: Override inbox directory name.

    Returns:
        VaultWriter instance.
    """
    global _writer

    if _writer is None:
        vault_path = vault_path or os.getenv(
            "VAULT_PATH", "D:/Obsidian/Obsidian_AI_Assistant"
        )
        inbox_dir = inbox_dir or os.getenv("VAULT_INBOX", "inbox")

        _writer = VaultWriter(vault_path, inbox_dir)

    return _writer


def save_to_vault(
    response: str,
    query: str,
    sources: list[dict] = None,
) -> str:
    """
    Convenience function to save an AI response to vault.

    Args:
        response: Full AI response string.
        query: Original user query.
        sources: List of source chunks.

    Returns:
        Path to created file.
    """
    writer = get_writer()
    return writer.write_response(response, query, sources)
