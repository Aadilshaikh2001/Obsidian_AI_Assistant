"""
Vault Retriever

Indexes and searches an Obsidian vault using BM25 lexical ranking.
Returns top-N context chunks for LLM prompt injection.
"""

import os
import re
from typing import Optional

import frontmatter
from rank_bm25 import BM25Okapi


class VaultRetriever:
    """
    BM25-based vault search for Obsidian notes.

    Indexes all .md files in the vault directory and provides
    lexical search over sections (chunked by ## headings).
    """

    def __init__(
        self,
        vault_path: str,
        top_k: int = 3,
        min_score: float = 0.1,
        exclude_dirs: list[str] = None,
    ):
        """
        Initialize the vault retriever.

        Args:
            vault_path: Path to the Obsidian vault directory.
            top_k: Number of top chunks to return per search.
            min_score: Minimum BM25 score threshold for relevance.
            exclude_dirs: Directory names to skip during indexing.
        """
        self.vault_path = os.path.abspath(vault_path)
        self.top_k = top_k
        self.min_score = min_score
        self.exclude_dirs = exclude_dirs or [".obsidian", ".trash", "templates"]

        # Initialize BM25 storage
        self.corpus = []  # List of tokenized text chunks
        self.chunks = []  # List of chunk metadata + content
        self.indexed = False

        # Build index on startup
        self.reindex()

    def reindex(self) -> None:
        """Rebuild the BM25 index from vault files."""
        self.corpus = []
        self.chunks = []

        # Walk the vault directory
        file_count = 0
        for root, dirs, files in os.walk(self.vault_path):
            # Exclude configured directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for filename in files:
                if not filename.endswith(".md"):
                    continue

                file_count += 1
                filepath = os.path.join(root, filename)
                self._process_file(filepath)

        # Build BM25 index
        if self.corpus:
            self.bm25 = BM25Okapi(self.corpus)
            self.indexed = True
        else:
            self.bm25 = None
            self.indexed = False

        # Print indexing summary
        if file_count > 0:
            print(f"[INFO] Indexed {file_count} .md files")
        else:
            print(f"[WARN] No .md files found in vault at: {self.vault_path}")

    def _process_file(self, filepath: str) -> None:
        """
        Process a single .md file, chunking by ## headings.

        Args:
            filepath: Full path to the markdown file.
        """
        try:
            # Read file content
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse frontmatter - returns (metadata_dict, content_string)
            metadata, body = frontmatter.parse(content)
            frontmatter_data = metadata if metadata else {}

            # Get relative path from vault root for source info
            rel_path = os.path.relpath(filepath, self.vault_path)

            # Get title from frontmatter or filename
            title = frontmatter_data.get("title", os.path.splitext(rel_path)[0])

            # Chunk by ## headings
            sections = self._split_by_headings(body, title, rel_path)

            for section in sections:
                # Tokenize the section content
                tokens = self._tokenize(section["content"])
                self.corpus.append(tokens)
                self.chunks.append(section)

        except Exception as e:
            # Skip files that can't be processed
            print(f"[WARN] Could not process {filepath}: {e}")

    def _split_by_headings(self, content: str, title: str, rel_path: str) -> list[dict]:
        """
        Split content into sections by ## headings.

        Args:
            content: Raw markdown content.
            title: Note title.
            rel_path: Relative path from vault root.

        Returns:
            List of section dicts with content and metadata.
        """
        sections = []

        # Split by ## headings - pattern captures heading and following newlines
        # The content after the newlines becomes the section body
        heading_pattern = r"(## .+?)\n+"
        parts = re.split(heading_pattern, content)

        # Reconstruct sections with their headings
        if len(parts) > 1:
            # First part is content before any ## heading
            if parts[0].strip():
                sections.append({
                    "title": title,
                    "source": rel_path,
                    "heading": "Introduction",
                    "content": parts[0].strip(),
                })

            # Reconstruct ## sections - pattern is: heading, content, heading, content...
            i = 1
            while i < len(parts):
                heading = parts[i].replace("## ", "").strip()
                body = parts[i + 1].strip() if i + 1 < len(parts) else ""
                if body:
                    sections.append({
                        "title": title,
                        "source": rel_path,
                        "heading": heading,
                        "content": body,
                    })
                i += 2
        else:
            # No ## headings, use entire content
            if content.strip():
                sections.append({
                    "title": title,
                    "source": rel_path,
                    "heading": "Content",
                    "content": content.strip(),
                })

        return sections

    def _tokenize(self, text: str) -> list[str]:
        """
        Tokenize text for BM25 indexing.

        Args:
            text: Input text.

        Returns:
            List of lowercase tokens.
        """
        # Convert to lowercase and split on non-alphanumeric
        text = text.lower()
        tokens = re.findall(r"\b\w+\b", text)
        return tokens

    def search(self, query: str, top_k: int = None) -> list[dict]:
        """
        Search vault for relevant chunks.

        Args:
            query: Search query string.
            top_k: Override for number of results.

        Returns:
            List of matching chunks with scores.
        """
        if not self.indexed:
            return []

        top_k = top_k or self.top_k

        # Tokenize query
        query_tokens = self._tokenize(query)

        # Get BM25 scores
        if not self.bm25:
            return []

        scores = self.bm25.get_scores(query_tokens)

        # Get top-k results above threshold
        results = []
        for idx in scores.argsort()[-top_k:][::-1]:
            score = float(scores[idx])
            if score >= self.min_score:
                chunk = self.chunks[idx].copy()
                chunk["score"] = score
                results.append(chunk)

        return results

    def format_context(self, chunks: list[dict]) -> str:
        """
        Format chunks as context string for LLM prompt.

        Args:
            chunks: List of chunk dicts from search().

        Returns:
            Formatted context string with source info.
        """
        if not chunks:
            return ""

        context_parts = ["--- VAULT CONTEXT ---"]

        for chunk in chunks:
            source = chunk.get("source", "unknown")
            heading = chunk.get("heading", "Content")
            title = chunk.get("title", "Note")
            content = chunk.get("content", "")

            # Truncate long content
            if len(content) > 3000:
                content = content[:3000] + "..."

            context_parts.append(
                f"[Source: {source} | Section: ## {heading}]"
            )
            context_parts.append(content)
            context_parts.append("")

        context_parts.append("--- END CONTEXT ---")

        return "\n".join(context_parts)

    def get_vault_path(self) -> str:
        """Return the vault path."""
        return self.vault_path


# Convenience singleton
_retriever = None


def get_retriever(
    vault_path: str = None,
    top_k: int = None,
    min_score: float = None,
) -> VaultRetriever:
    """
    Get or create the vault retriever singleton.

    Args:
        vault_path: Override vault path from config.
        top_k: Override top_k from config.
        min_score: Override min_score from config.

    Returns:
        VaultRetriever instance.
    """
    global _retriever

    if _retriever is None:
        # Get defaults from environment/config
        vault_path = vault_path or os.getenv(
            "VAULT_PATH", "D:/Obsidian/Obsidian_AI_Assistant"
        )
        top_k = top_k or int(os.getenv("VAULT_TOP_K", "3"))
        min_score = min_score or float(os.getenv("VAULT_MIN_SCORE", "0.1"))

        _retriever = VaultRetriever(vault_path, top_k, min_score)

    return _retriever


def search_vault(query: str, top_k: int = None) -> list[dict]:
    """
    Convenience function to search the vault.

    Args:
        query: Search query.
        top_k: Number of results.

    Returns:
        List of matching chunks.
    """
    retriever = get_retriever()
    return retriever.search(query, top_k)
