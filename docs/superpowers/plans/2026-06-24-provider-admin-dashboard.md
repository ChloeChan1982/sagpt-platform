# Provider Application Admin Dashboard

## Goal

Add an operations dashboard for service provider applications submitted from www.sagpt.com so the SAGPT team can review, filter, export, and update provider application status.

## Scope

- Backend protected admin endpoints for provider applications.
- CSV export for provider applications.
- Status update support for provider applications.
- A standalone admin page at `/admin/providers`.
- Tests for provider admin serialization and route contracts.

## Backend Plan

1. Add provider admin serialization helpers in `app/core/providers.py`.
2. Add `ProviderStatusUpdate` schema.
3. Add protected provider admin endpoints:
   - `GET /api/providers/admin/list`
   - `GET /api/providers/admin/stats`
   - `GET /api/providers/admin/export.csv`
   - `PATCH /api/providers/admin/{application_id}/status`
4. Reuse the existing admin API key validation used by demand management.
5. Add `/admin/providers` route in `main.py`.

## Frontend Plan

1. Create `frontend/admin/providers.html`.
2. Create `frontend/admin/providers.js`.
3. Reuse existing admin CSS and UI patterns.
4. Support login with admin key, search/filter, detail view, CSV download, and status updates.

## Verification

- `python -m unittest tests.test_providers tests.test_demands`
- `python -m py_compile app\routers\providers.py app\core\providers.py main.py`
- `node --check frontend\admin\providers.js`
- `git diff --check`
