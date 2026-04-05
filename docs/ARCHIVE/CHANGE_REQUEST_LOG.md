# Change Request Log

**Project:** Cornelius-Ollama  
**Version:** 0.1.0-MVP  
**Status:** MVP Complete - Changes Frozen for Stabilization  
**Last Updated:** 2026-04-05

---

## Change Request Overview

| Status | Count | Description |
|--------|-------|-------------|
| Approved (MVP) | 0 | Features in current release |
| Post-MVP Approved | 0 | Features approved for future |
| Under Review | 5 | Pending review by PM |
| Rejected | 2 | Not approved for roadmap |
| **Total** | **7** | |

---

## Post-MVP Enhancement Requests

### #1: Chat History Persistence
**Priority:** High  
**Category:** User Experience  
**Status:** ⏳ Under Review

**Description:** Persist conversation history across restarts.

**Requirements:**
- Save chat history to file on exit
- Load history on startup (configurable)
- Support for multiple saved sessions

**Effort Estimate:** 4-6 hours

**Rationale:** Current behavior requires re-pasting context on restart. Users expect continuity.

---

### #2: Multiple Model Support
**Priority:** High  
**Category:** Functionality  
**Status:** ⏳ Under Review

**Description:** Allow users to switch between multiple installed models.

**Requirements:**
- List all available Ollama models
- Select active model via `/model` command
- Cache model切换 performance

**Effort Estimate:** 3-4 hours

**Rationale:** Users may want different models for different tasks.

---

### #3: Export Conversation
**Priority:** Medium  
**Category:** Functionality  
**Status:** ⏳ Under Review

**Description:** Export current conversation to file.

**Requirements:**
- Export as Markdown (default)
- Export as plain text
- Include timestamps and sources

**Effort Estimate:** 2-3 hours

**Rationale:** Users want to save or share conversations.

---

### #4: Configurable Models via YAML
**Priority:** Medium  
**Category:** Configuration  
**Status:** ⏳ Under Review

**Description:** Support multiple named model profiles in config.

**Requirements:**
- Define profiles in config.yaml
- Switch between profiles via command
- Persist profile selection

**Effort Estimate:** 4-5 hours

**Rationale:** Advanced users want different configs for different use cases.

---

### #5: File Watcher for Auto-Indexing
**Priority:** Medium  
**Category:** Performance  
**Status:** ⏳ Under Review

**Description:** Automatically reindex when vault files change.

**Requirements:**
- Watch vault directory for changes
- Trigger reindex on file create/update/delete
- Configurable debounce interval

**Effort Estimate:** 8-10 hours

**Rationale:** Current `/reload` command is manual; automation preferred.

---

## Rejected Change Requests

### #6: Web UI
**Priority:** High  
**Status:** ❌ Rejected  
**Date:** 2026-04-05

**Rationale:** Project scope is CLI-first, local-first. Web UI would require significant architectural changes and is out of scope for MVP.

**Alternatives:** Users can run locally and access via terminal. Future web options could use Electron or similar if needed.

---

### #7: API Server (HTTP)
**Priority:** Medium  
**Status:** ❌ Rejected  
**Date:** 2026-04-05

**Rationale:** Current architecture intentionally avoids HTTP server. Adding FastAPI/Flask would violate the "local-first, no HTTP server" design principle.

**Alternatives:** Users can use Ollama's API directly if HTTP access is needed.

---

## MVP-Complete Items (Not Change Requests)

These were MVP requirements, now complete:

| Feature | Completion Date | Status |
|---------|-----------------|--------|
| Ollama adapter | 2026-04-04 | ✅ |
| BM25 retrieval | 2026-04-04 | ✅ |
| Vault writer | 2026-04-04 | ✅ |
| CLI REPL | 2026-04-04 | ✅ |
| Voice input | 2026-04-04 | ✅ |
| Unit tests | 2026-04-05 | ✅ |
| Documentation | 2026-04-05 | ✅ |

---

## Change Request Process

1. **Submit:** Create issue/PR with description
2. **Triage:** Assign priority (High/Medium/Low)
3. **Review:** PM reviews and approves/rejects
4. **Schedule:** Add to backlog or milestone
5. **Implement:** Developer implements
6. **Test:** Validate with tests
7. **Merge:** Deploy to next release

---

## Roadmap

### Phase 1: Stabilization (Current)
- Bug fixes only
- Performance optimization
- Documentation updates

### Phase 2: Enhancement (Sprint 2)
- Chat history persistence
- Model switching
- Export functionality

### Phase 3: Advanced Features (Sprint 3+)
- File watcher
- Multiple profiles
- Plugin system

---

## Notes

- **Freeze:** No new features being accepted for MVP
- All PRs must target `stabilization` branch
- Emergency fixes go directly to `main` with approval