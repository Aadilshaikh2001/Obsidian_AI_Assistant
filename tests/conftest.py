"""
pytest configuration for Cornelius-Ollama tests
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cleanup singletons between tests
import pytest
from vault_writer import _writer as writer_singleton
from ollama_client import _client as client_singleton
from vault_retriever import _retriever as retriever_singleton


@pytest.fixture(autouse=True)
def cleanup_singletons():
    """Reset singletons between tests."""
    global writer_singleton, client_singleton, retriever_singleton
    writer_singleton = None
    client_singleton = None
    retriever_singleton = None
    yield