#!/usr/bin/env python3
"""
Cornelius-Ollama: CLI-First Obsidian-Integrated LLM Assistant
GitHub: https://github.com/abilityai/cornelius (base template)
"""

import sys

if sys.version_info < (3, 11):
    print("ERROR: Python 3.11+ is required")
    sys.exit(1)

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .chat.loop import main

if __name__ == "__main__":
    main()
