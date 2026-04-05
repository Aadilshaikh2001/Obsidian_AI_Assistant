"""Vault module for Cornelius-Ollama."""

from .retriever import VaultRetriever, get_retriever, search_vault
from .writer import VaultWriter, get_writer, save_to_vault

__all__ = [
    "VaultRetriever",
    "get_retriever",
    "search_vault",
    "VaultWriter",
    "get_writer",
    "save_to_vault",
]
