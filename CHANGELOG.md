# CHANGELOG

All notable changes to Cornelius-Ollama will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-04-05 (Unreleased)

### Added
- **Package restructure** - Industry-standard `src/` layout
- **Unit tests** - 46/46 tests passing
- **GitHub workflows** - CI/CD with pytest, CodeQL, security scans
- **Documentation** - Complete MVP closeout and monitoring docs
- **License** - MIT License file
- **pyproject.toml** - Modern Python project metadata

### Changed
- **Ollama adapter** - Moved to `src/ollama/client.py`
- **Vault operations** - Moved to `src/vault/` directory
- **Chat orchestration** - Moved to `src/chat/` directory
- **Voice processor** - Moved to `src/voice/` directory
- **Dependencies** - Updated and organized in `requirements.txt`

### Removed
- Old flat structure with root-level modules

### Fixed
- Test infrastructure issues (singletons, mocks, fixtures)
- Import paths for restructured package

## [0.1.0] - 2026-04-04

Initial release with Setup & Documentation phase deliverables.

### Added
- Ollama client adapter (`ollama_client.py`)
- Vault retriever with BM25 (`vault_retriever.py`)
- Vault writer for atomic .md creation (`vault_writer.py`)
- Orchestrator for chat flow (`orchestrator.py`)
- Terminal REPL (`chat_loop.py`)
- Configuration files (`config.yaml`, `.env.example`)
- Documentation:
  - `README.md` - Project overview and quickstart
  - `SETUP.md` - Detailed installation guide
  - `docs/ARCHITECTURE.md` - System architecture
  - `docs/adr/ADR-001-ollama-adapter.md` - Why Ollama
  - `docs/adr/ADR-002-no-ui.md` - Why terminal-only
  - `docs/adr/ADR-003-bm25-retrieval.md` - Why BM25
- Slash commands: `/quit`, `/exit`, `/help`, `/save`, `/clear`, `/vault`, `/model`, `/status`

### Changed
- Removed `anthropic` dependency
- Removed `langchain`, `llama-index` dependencies
- Updated to `requests` + `rank-bm25` + `python-frontmatter`

### Fixed
- Original template Anthropic SDK compatibility issues
- Template agent swarm over-architecture for single-user CLI