# Obsidian_AI_Assistant

A local-first, terminal-based AI assistant for Obsidian vaults.

## Features
- CLI-first interface with Ollama LLM
- BM25-based vault retrieval
- Voice input with Whisper transcription
- Atomic note writing to Obsidian vault
- 100% test coverage (46/46 tests)

## Quick Start
```bash
git clone https://github.com/Aadilshaikh2001/Obsidian_AI_Assistant.git
cd Obsidian_AI_Assistant
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

## Project Structure
```
src/              # Modern package layout
tests/            # 46 tests passing
docs/ARCHIVE/     # MVP closeout docs
.github/          # CI/CD workflows
```

## Testing
```bash
python -m pytest tests/ -v
```

## License
MIT License - see LICENSE file for details.