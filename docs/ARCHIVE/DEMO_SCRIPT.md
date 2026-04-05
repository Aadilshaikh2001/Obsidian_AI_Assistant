# Demo Script for Cornelius-Ollama

**Project:** Obsidian AI Assistant  
**Duration:** ~8 minutes  
**Audience:** Technical stakeholders, product team  
**Presenter:** Claude Code / Demo Runner

---

## Pre-Demo Checklist

- [ ] Ollama running (`ollama serve`)
- [ ] Python environment active (`python -m venv .venv`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Environment variables loaded (`.env` exists)
- [ ] Test suite passes (`python -m pytest tests/ -v`)

---

## Part 1: Introduction (1 minute)

> "I'll demonstrate the Cornelius-Ollama Obsidian AI Assistant - a local-first, terminal-based assistant that integrates with your Obsidian knowledge vault."

### Script
```
Welcome! I'll show you:

1. The CLI interface and chat flow
2. How it reads from your Obsidian vault
3. How it saves responses back to your vault
4. Voice input capability
5. The technical architecture

Let's get started!
```

---

## Part 2: Starting the Assistant (1 minute)

### Script
```
First, let's start the assistant. I'll run:
  python run.py
```

**Command:** `python run.py`

### Expected Output
```
═══════════════════════════════════════════════
  Cornelius-Ollama | Model: qwen3-coder-next:cloud | Vault: Obsidian_AI_Assistant
  Type /help for commands. /quit to exit.
═══════════════════════════════════════════════
```

**Narration:** "Notice the welcome banner - it shows our model (Qwen) and vault path. This is a local LLM running on Ollama."

---

## Part 3: Basic Chat (1.5 minutes)

### Script
```
Now let's ask a simple question. I'll type:
  "What is Python?"
```

**Command:** `What is Python?`

### Expected Output
```
Cornelius: Python is a high-level, interpreted, general-purpose programming language...
```

**Narration:** "The response streams in real-time from the local Ollama instance. You can see the model is working and responding directly."

**Command:** `/save`

**Expected Output:** `Saved to: inbox/ai-2026-04-05-*.md`

**Narration:** "The `/save` command wrote this response to our Obsidian vault with proper frontmatter."

---

## Part 4: Vault Search (1 minute)

### Script
```
Let's search the vault directly for content:
  /vault Python
```

**Command:** `/vault Python`

### Expected Output
```
Vault Search: Python
Result 1 (score: 1.865)
  Source: inbox\ai-2026-04-05-what-is-python.md
  Content: Python is a programming language...
```

**Narration:** "The BM25 retrieval found the file we just created. This is lexical search - matching keywords in the vault."

---

## Part 5: Voice Input (1.5 minutes)

### Script
```
Now let's try voice input:
  /voice
```

**Command:** `/voice`

**Flow:**
1. Press Enter to start recording
2. Speak: "What is machine learning?"
3. Press Enter to stop
4. Transcription appears in panel
5. Type: `Y` to accept

### Expected Output
```
🎤 Start speaking...
Press Enter to stop recording...

[Recording audio...]

Transcription panel appears with:
  "What is machine learning?"

What would you like to do?
  [Y]es - Send to AI
  [E]dit text
  [C]ancel

Select option (Y/E/C): y
```

**Narration:** "Voice input works with Whisper. We can review, edit, or cancel before sending to the AI."

---

## Part 6: Status and Commands (1 minute)

### Script
```
Let me show you the status command:
  /status

And a quick list of all commands:
  /help
```

**Commands:**
```
/status
/help
```

### Expected Output
```
Model: qwen3-coder-next:cloud
Vault: D:\Obsidian\Obsidian_AI_Assistant
Messages: 0

Available Commands:
  /quit or /exit             Graceful shutdown
  /help                      Print this help message
  /save                      Write last response to vault inbox/
  /clear                     Clear session message history
  /reload                    Reindex vault files
  /voice                     Record and transcribe voice input
  /vault <query>             Raw vault search, print top chunks
  /model <name>              Switch model mid-session (hot swap)
  /status                    Show model name, vault path, message count
```

---

## Part 7: Exit and Summary (1 minute)

### Script
```
Let's exit:
  /quit
```

**Command:** `/quit`

**Expected Output:**
```
Goodbye!
```

### Summary
```
That's the demo! Here's what we've validated:

✅ LLM response loop - Ollama streaming works
✅ Vault CRUD - Create, Read, Save all functional
✅ Retrieval - BM25 search finds relevant content
✅ Voice input - Whisper transcription with edit support
✅ CLI interface - All commands working

The system is local-first, no cloud API keys needed.
Everything runs on your machine with your data.
```

---

## Technical Deep Dive (Optional - 3 minutes)

> "If you're interested, I can walk through the architecture."

### Architecture Diagram (visual or describe)

```
┌─────────────────────────────────────────────────┐
│                   TERMINAL                      │
│  User: "What is Python?"                       │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│               CHAT ORCHESTRATOR                 │
│  - Routes requests                             │
│  - Manages conversation history                │
│  - Coordinates services                        │
└──────────────┬──────────────┬───────────────────┘
               │              │
               ▼              ▼
    ┌────────────────┐  ┌────────────────┐
    │  Ollama Client │  │ Vault Retriever│
    │  (Ollama API)  │  │   (BM25)       │
    │  - Streaming   │  │  - Indexing    │
    │  - Error       │  │  - Search      │
    └────────────────┘  └────────────────┘
                                │
                                ▼
                   ┌──────────────────┐
                   │ Vault Writer     │
                   │ - Atomic writes  │
                   │ - Frontmatter    │
                   └──────────────────┘
```

### Key Components

1. **Ollama Client** - HTTP adapter for local LLM
2. **Vault Retriever** - BM25 lexical search over markdown files
3. **Vault Writer** - Atomic note creation with frontmatter
4. **Chat Orchestrator** - Request routing and history
5. **Voice Processor** - Whisper transcription

---

## Q&A Transition

> "That's the Cornelius-Ollama assistant. I've covered:
> - CLI-first interface
> - Local LLM integration
> - Obsidian vault operations
> - Voice input capability

> I'd be happy to answer any questions or walk through specific features in more detail."

---

## Troubleshooting Notes (For Presenter)

### If Ollama isn't running
```
ERROR: Ollama not running. Start with: ollama serve
SOLUTION: Open a new terminal and run: ollama serve
```

### If model not found
```
ERROR: Model 'qwen3-coder-next:cloud' not found
SOLUTION: ollama pull qwen3-coder-next:cloud
```

### If imports fail
```
ERROR: Module not found
SOLUTION: pip install -r requirements.txt
```

---

## Demo Timing Guide

| Section | Time | Buffer |
|---------|------|--------|
| Introduction | 1 min | 15s |
| Starting Assistant | 1 min | 15s |
| Basic Chat | 1.5 min | 20s |
| Vault Search | 1 min | 10s |
| Voice Input | 1.5 min | 20s |
| Status & Commands | 1 min | 10s |
| Exit & Summary | 1 min | 10s |
| Q&A | 2+ min | - |
| **Total** | **8 min** | **80s** |

---

## Success Criteria

| Metric | Target | Pass |
|--------|--------|------|
| Startup time | < 3s | ✅ |
| First response | < 10s | ✅ |
| Voice latency | < 5s | ✅ |
| Vault save | < 2s | ✅ |
| Tests passing | 46/46 | ✅ |

---

**Presenter Notes:**
- Speak at a moderate pace
- Pause after key features
- Be ready to handle errors gracefully
- Have Ollama running before demo starts