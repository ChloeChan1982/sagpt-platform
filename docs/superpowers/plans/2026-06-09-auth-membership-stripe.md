# Authentication, Membership, and Stripe Webhook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build secure email/password authentication and automatically synchronize Stripe subscriptions to SAGPT memberships.

**Architecture:** FastAPI issues opaque session cookies backed by PostgreSQL. Resend delivers single-use verification and reset links. Stripe Checkout binds a verified user, and signed idempotent Webhook events update one membership record per user.

**Tech Stack:** FastAPI, SQLAlchemy, PostgreSQL, Python standard cryptography primitives, Resend HTTP API, Stripe Python SDK.

---

### Task 1: Authentication primitives and models

**Files:**
- Create: `app/core/auth.py`
- Modify: `app/models/models.py`
- Test: `tests/test_auth.py`

- [ ] Write failing tests for password hashing, opaque token hashing, and Stripe membership status mapping.
- [ ] Run `python -m unittest tests.test_auth -v` and confirm missing-module failure.
- [ ] Implement the minimal primitives and database models.
- [ ] Run the tests and confirm they pass.

### Task 2: Resend email and authentication routes

**Files:**
- Create: `app/services/email_service.py`
- Create: `app/routers/auth.py`
- Modify: `app/models/schemas.py`
- Modify: `main.py`
- Modify: `render.yaml`
- Modify: `.env.example`
- Test: `tests/test_auth.py`

- [ ] Add failing tests for public user serialization and verification requirements.
- [ ] Implement register, verify, login, logout, me, forgot-password, and reset-password.
- [ ] Configure secure cookie settings and Resend environment variables.
- [ ] Run all tests.

### Task 3: Authenticated Checkout and Stripe Webhook

**Files:**
- Modify: `app/core/payments.py`
- Modify: `app/routers/payments.py`
- Modify: `app/models/models.py`
- Modify: `render.yaml`
- Test: `tests/test_payments.py`

- [ ] Add failing tests for checkout user metadata and Stripe status mapping.
- [ ] Require a verified session for Checkout and bind user ID/email.
- [ ] Implement signed, idempotent Webhook processing for Checkout, invoice, and subscription events.
- [ ] Run all tests.

### Task 4: Verification and deployment

- [ ] Run `python -m unittest discover -s tests -v`.
- [ ] Run Python syntax compilation for all changed modules.
- [ ] Review security-sensitive code and remove generated caches.
- [ ] Commit, push, and verify deployed endpoints.
- [ ] Configure Stripe Webhook endpoint and `STRIPE_WEBHOOK_SECRET`.
