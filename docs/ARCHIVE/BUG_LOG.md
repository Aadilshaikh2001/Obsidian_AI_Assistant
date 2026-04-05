# Bug / Issue Log

**Project:** Cornelius-Ollama  
**Tracking System:** Manual Log  
**Last Updated:** 2026-04-05

---

## Defect Tracking Summary

| Severity | Open | Resolved | Total |
|----------|------|----------|---------|
| Critical | 0 | 0 | 0 |
| High | 0 | 2 | 2 |
| Medium | 2 | 1 | 3 |
| Low | 1 | 3 | 4 |
| **Total** | **3** | **6** | **9** |

---

## Resolved Issues

### #1: Missing Mock import in test files
**Severity:** High  
**Status:** ✅ Fixed  
**Date:** 2026-04-05

**Description:** Tests in `test_vault_writer.py`, `test_ollama_client.py`, `test_vault_retriever.py` failed with `NameError: name 'Mock' is not defined`.

**Root Cause:** `Mock` was imported from `unittest.mock` but not imported directly.

**Fix:**
```python
# Changed from:
from unittest.mock import patch
# To:
from unittest.mock import Mock, patch
```

**Impact:** All tests passing (46/46).

---

### #2: Wrong exception type in connection tests
**Severity:** High  
**Status:** ✅ Fixed  
**Date:** 2026-04-05

**Description:** Tests used `ConnectionRefusedError()` but `requests` raises `requests.exceptions.ConnectionError`.

**Fix:**
```python
# Changed from:
mock_post.side_effect = ConnectionRefusedError()
# To:
mock_post.side_effect = requests.exceptions.ConnectionError()
```

**Impact:** Connection error handling tests now pass.

---

### #3: Fixture name mismatch in test_vault_writer.py
**Severity:** Medium  
**Status:** ✅ Fixed  
**Date:** 2026-04-05

**Description:** `TestIntegration.test_full_write_cycle` used `temp_vault` fixture but it was defined as `tmp_path`.

**Fix:** Updated to use `tmp_path` consistently.

**Impact:** Integration test now passes.

---

### #4: Missing singleton cleanup between tests
**Severity:** Medium  
**Status:** ✅ Fixed  
**Date:** 2026-04-05

**Description:** Tests for singleton patterns failed due to module-level state persistence.

**Fix:** Added `cleanup_singletons()` fixture in `conftest.py`.

**Impact:** All singleton tests now pass.

---

### #5: Mock stream not configured in orchestrator tests
**Severity:** Medium  
**Status:** ✅ Fixed  
**Date:** 2026-04-05

**Description:** Orchestrator tests failed because `stream_response_to_client` wasn't properly mocked.

**Fix:** Added `autouse=True` fixture to mock the stream function.

**Impact:** Orchestrator tests now pass.

---

### #6: Debug mode test assertion failure
**Severity:** Low  
**Status:** ✅ Fixed  
**Date:** 2026-04-05

**Description:** Test expected debug output but mock setup was incorrect.

**Fix:** Updated test to properly mock console and set it on orchestrator before running.

**Impact:** Debug mode test now passes.

---

## Open Issues

### #7: Voice input requires audio hardware
**Severity:** Medium  
**Status:** ⚠️ Open  
**Date:** 2026-04-05

**Description:** `/voice` command requires microphone access and working audio drivers.

**Notes:**
- Test confirmed the processor handles silent audio gracefully
- Full voice testing requires actual recording hardware
- May need audio device detection

**Workaround:** CLI text input remains fully functional.

**Planned:** Add audio device check with graceful fallback.

---

### #8: No chat history persistence
**Severity:** Low  
**Status:** ⚠️ Open  
**Date:** 2026-04-05

**Description:** Message history clears on restart.

**Notes:**
- Not MVP-critical (documented limitation)
- Users expect session continuity

**Planned:** Add `--persist` flag to save/load conversation.

---

### #9: Auto-reload not implemented
**Severity:** Low  
**Status:** ⚠️ Open  
**Date:** 2026-04-05

**Description:** New vault files aren't automatically indexed.

**Notes:**
- Requires `/reload` command to pick up changes
- Could implement file watcher for auto-reload

**Planned:** Add file watcher in background thread.

---

## Severity Definitions

| Level | Definition | Response Time |
|-------|------------|---------------|
| Critical | System crash, data loss, security breach | Immediate |
| High | Core functionality broken, major feature broken | 24 hours |
| Medium | Partial functionality affected, workarounds exist | 1 week |
| Low | Cosmetic issues, minor UX problems | 2 weeks |

---

## Defect Trend

```
Week 1: 0 fixed, 0 open
Week 2: 6 fixed, 0 open
Week 3: 0 fixed, 3 open (documentation issues)
```

---

## Notes

- All test infrastructure issues resolved in MVP stabilization
- Remaining open issues are feature limitations, not bugs
- No security or data integrity issues identified