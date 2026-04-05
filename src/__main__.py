"""
 Cornelius-Ollama: CLI-First Obsidian-Integrated LLM Assistant

A local-first, terminal-only AI assistant for your Obsidian vault.
Powered by Ollama. No cloud. No browser. Just a terminal.

GitHub: https://github.com/cornelius-ollama/cornelius
"""

import sys

if sys.version_info < (3, 11):
    print("ERROR: Python 3.11+ is required")
    sys.exit(1)

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.main import main

if __name__ == "__main__":
    main()
