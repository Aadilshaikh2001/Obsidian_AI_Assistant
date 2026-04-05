# Project Structure

## Directory Overview

```
cornelius-ollama/
├── src/                          # Source code (modern Python structure)
│   ├── __init__.py              # Package initialization
│   ├── __main__.py              # Module entry point (python -m src)
│   ├── ollama/                  # Ollama client adapter
│   │   ├── __init__.py
│   │   ├── client.py            # HTTP client with streaming
│   │   └── stream.py            # Convenience functions
│   ├── vault/                   # Vault operations
│   │   ├── __init__.py
│   │   ├── retriever.py         # BM25 search
│   │   └── writer.py            # Atomic note creation
│   ├── chat/                    # Chat orchestration
│   │   ├── __init__.py
│   │   ├── orchestrator.py      # Request routing
│   │   └── loop.py              # Terminal REPL
│   └── voice/                   # Whisper integration
│       ├── __init__.py
│       └── processor.py         # Voice-to-text
├── tests/                       # Test files
│   ├── __init__.py
│   ├── conftest.py             # Shared fixtures
│   ├── test_ollama_client.py
│   ├── test_vault_retriever.py
│   ├── test_vault_writer.py
│   └── test_orchestrator.py
├── .github/                     # GitHub workflows
│   ├── workflows/              # CI/CD
│   │   ├── tests.yml
│   │   ├── codeql.yml
│   │   ├── release.yml
│   │   ├── lint.yml
│   │   └── security.yml
│   ├── badges/                 # Status badges
│   │   ├── status.json
│   │   ├── tests.json
│   │   ├── coverage.json
│   │   ├── python.json
│   │   └── config.json
│   └── dependabot.yml          # Dependency updates
├── docs/                        # Documentation
│   ├── ARCHIVE/                # Archived documents
│   │   ├── MVP_COMPLETION_REPORT.md
│   │   ├── BUG_LOG.md
│   │   ├── CHANGE_REQUEST_LOG.md
│   │   ├── DEMO_SCRIPT.md
│   │   ├── LESSONS_LEARNED.md
│   │   └── MONITORING_CHECKLIST.md
│   ├── adr/                    # Architecture Decision Records
│   └── ARCHITECTURE.md
├── .env                         # Environment configuration (local)
├── .env.example                 # Environment template
├── config.yaml                  # YAML configuration
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Project metadata (modern)
├── setup.cfg                    # Setuptools configuration
├── LICENSE                      # MIT License
├── README.md                    # Project overview
├── CHANGELOG.md                 # Version history
└── run.py                       # CLI entry point
```

## Key Changes

### Before (Flat Structure)
```
ollama_client.py
vault_retriever.py
vault_writer.py
orchestrator.py
chat_loop.py
run.py
```

### After (Structured Package)
```
src/
├── ollama/
│   ├── client.py (was: ollama_client.py)
│   └── stream.py (new)
├── vault/
│   ├── retriever.py (was: vault_retriever.py)
│   └── writer.py (was: vault_writer.py)
├── chat/
│   ├── orchestrator.py (was: orchestrator.py)
│   └── loop.py (was: chat_loop.py)
└── voice/
    └── processor.py (was: voice_processor.py)
```

## Benefits of Restructuring

1. **Clean Imports**: `from src.ollama import OllamaClient`
2. **Scalability**: Easy to add new modules
3. **Standard Practice**: Industry-standard `src/` layout
4. **Test Isolation**: Clear separation of test and source
5. **Modern Python**: pyproject.toml for metadata

## Running the Project

### Option 1: Direct script
```bash
python run.py
```

### Option 2: Module
```bash
python -m src
```

### Option 3: Package install
```bash
pip install -e .
cornelius
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage (requires pytest-cov)
python -m pytest tests/ -v --cov=src

# Linting
flake8 src/ tests/

# Type checking
mypy src/

# Formatting
black src/ tests/
```
