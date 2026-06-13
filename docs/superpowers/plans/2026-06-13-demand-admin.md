# Demand Admin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Return demand submissions promptly and add protected demand list and CSV export APIs.

**Architecture:** A focused demand-admin helper module handles API-key validation and CSV serialization. The demand router schedules matching in a detached worker thread with its own database session and exposes protected, filtered management endpoints.

**Tech Stack:** FastAPI, SQLAlchemy, Python `csv`, `unittest`

---

### Task 1: Add failing demand administration tests

**Files:**
- Create: `tests/test_demands.py`

- [ ] Test missing and invalid API keys are rejected.
- [ ] Test valid API key is accepted.
- [ ] Test CSV output contains demand details and Excel-compatible BOM.
- [ ] Test the submit route schedules background matching.
- [ ] Run `python -m unittest tests.test_demands -v` and confirm failure.

### Task 2: Implement demand administration helpers and routes

**Files:**
- Create: `app/core/demands.py`
- Modify: `app/routers/demands.py`

- [ ] Implement `require_admin_api_key`.
- [ ] Implement CSV serialization.
- [ ] Move matching to a background task with a fresh database session.
- [ ] Add protected paginated list and CSV export routes.
- [ ] Run `python -m unittest tests.test_demands -v` and confirm pass.

### Task 3: Verify and publish

**Files:**
- Verify all changed files.

- [ ] Run `python -m unittest discover -s tests -v`.
- [ ] Run `python -m py_compile app/core/demands.py app/routers/demands.py`.
- [ ] Run `git diff --check`.
- [ ] Commit and push the verified changes.
