# Demand Admin Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a secure visual dashboard for SAGPT operators to review, filter, export, and update enterprise demands.

**Architecture:** FastAPI serves a small self-contained admin application from `frontend/admin`, while protected JSON endpoints in the existing demands router provide statistics and status updates. The page stores the administrator API key in browser `sessionStorage` and sends it through `X-API-Key` on every data request.

**Tech Stack:** FastAPI, SQLAlchemy, vanilla HTML/CSS/JavaScript, Python unittest

---

## File Structure

- Create `frontend/admin/index.html`: dashboard markup and login shell.
- Create `frontend/admin/admin.css`: responsive operational dashboard styling.
- Create `frontend/admin/admin.js`: session authentication, API calls, filtering, table/detail rendering, status updates, and CSV export.
- Modify `main.py`: mount admin static assets and serve `/admin/demands`.
- Modify `app/routers/demands.py`: add protected statistics and status-update endpoints.
- Modify `app/models/schemas.py`: define the administrator status-update request model.
- Modify `tests/test_demands.py`: cover endpoint contracts and dashboard routing/assets.

### Task 1: Protected Demand Status Update API

**Files:**
- Modify: `app/models/schemas.py`
- Modify: `app/routers/demands.py`
- Test: `tests/test_demands.py`

- [ ] **Step 1: Write failing tests for supported and unsupported status updates**

Add tests that verify:

```python
def test_admin_status_update_contract_is_protected_and_validated(self):
    source = (Path(__file__).parents[1] / "app" / "routers" / "demands.py").read_text(
        encoding="utf-8"
    )
    self.assertIn('@router.patch("/admin/{demand_id}/status")', source)
    self.assertIn("Depends(require_admin_api_key)", source)
    self.assertIn("SUPPORTED_DEMAND_STATUSES", source)
    self.assertIn("Unsupported demand status", source)
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```powershell
python -m unittest tests.test_demands.DemandAdministrationTests.test_admin_status_update_contract_is_protected_and_validated -v
```

Expected: `FAIL` because the status endpoint and supported-status validation do not exist.

- [ ] **Step 3: Add the request schema and minimal protected endpoint**

Add to `app/models/schemas.py`:

```python
class DemandStatusUpdate(BaseModel):
    status: str
```

Add to `app/routers/demands.py`:

```python
SUPPORTED_DEMAND_STATUSES = {"pending", "matching", "contacted", "completed", "closed"}


@router.patch("/admin/{demand_id}/status")
async def update_demand_status_for_admin(
    demand_id: uuid.UUID,
    status_update: schemas.DemandStatusUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_api_key),
):
    if status_update.status not in SUPPORTED_DEMAND_STATUSES:
        raise HTTPException(status_code=422, detail="Unsupported demand status")

    demand = db.query(Demand).filter(Demand.id == str(demand_id)).first()
    if not demand:
        raise HTTPException(status_code=404, detail="Demand not found")

    demand.status = status_update.status
    db.commit()
    db.refresh(demand)
    return demand_to_admin_dict(demand)
```

- [ ] **Step 4: Run focused and full demand tests**

Run:

```powershell
python -m unittest tests.test_demands -v
```

Expected: all demand tests pass.

- [ ] **Step 5: Commit**

```powershell
git add app/models/schemas.py app/routers/demands.py tests/test_demands.py
git commit -m "Add protected demand status updates"
```

### Task 2: Protected Demand Statistics API

**Files:**
- Modify: `app/routers/demands.py`
- Test: `tests/test_demands.py`

- [ ] **Step 1: Write a failing test for protected status statistics**

Add:

```python
def test_admin_stats_contract_is_protected_and_counts_operational_statuses(self):
    source = (Path(__file__).parents[1] / "app" / "routers" / "demands.py").read_text(
        encoding="utf-8"
    )
    self.assertIn('@router.get("/admin/stats")', source)
    for status in ("pending", "matching", "contacted", "completed", "closed"):
        self.assertIn(f'"{status}"', source)
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```powershell
python -m unittest tests.test_demands.DemandAdministrationTests.test_admin_stats_contract_is_protected_and_counts_operational_statuses -v
```

Expected: `FAIL` because `/admin/stats` does not exist.

- [ ] **Step 3: Add protected status counts**

Add before the public parameterized demand route:

```python
@router.get("/admin/stats")
async def get_admin_demand_stats(
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_api_key),
):
    counts = {
        status: db.query(func.count(Demand.id)).filter(Demand.status == status).scalar() or 0
        for status in SUPPORTED_DEMAND_STATUSES
    }
    return {
        "total": db.query(func.count(Demand.id)).scalar() or 0,
        **counts,
    }
```

- [ ] **Step 4: Run demand tests**

Run:

```powershell
python -m unittest tests.test_demands -v
```

Expected: all demand tests pass.

- [ ] **Step 5: Commit**

```powershell
git add app/routers/demands.py tests/test_demands.py
git commit -m "Add protected demand dashboard statistics"
```

### Task 3: Dashboard Page And FastAPI Delivery

**Files:**
- Create: `frontend/admin/index.html`
- Create: `frontend/admin/admin.css`
- Create: `frontend/admin/admin.js`
- Modify: `main.py`
- Test: `tests/test_demands.py`

- [ ] **Step 1: Write failing tests for dashboard routing and required controls**

Add:

```python
def test_admin_dashboard_assets_and_route_exist(self):
    root = Path(__file__).parents[1]
    main_source = (root / "main.py").read_text(encoding="utf-8")
    html = (root / "frontend" / "admin" / "index.html").read_text(encoding="utf-8")
    script = (root / "frontend" / "admin" / "admin.js").read_text(encoding="utf-8")

    self.assertIn('@app.get("/admin/demands"', main_source)
    self.assertIn("sessionStorage", script)
    self.assertIn("X-API-Key", script)
    self.assertIn("/api/demands/admin/list", script)
    self.assertIn("/api/demands/admin/stats", script)
    self.assertIn("/api/demands/admin/export.csv", script)
    self.assertIn("需求管理", html)
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```powershell
python -m unittest tests.test_demands.DemandAdministrationTests.test_admin_dashboard_assets_and_route_exist -v
```

Expected: `ERROR` or `FAIL` because the dashboard files and route do not exist.

- [ ] **Step 3: Create dashboard HTML**

Create `frontend/admin/index.html` containing:

- API-key login view.
- Compact header with refresh, CSV export, and logout buttons.
- Six summary counters.
- Keyword, status, and country filters.
- Paginated demand table.
- Right-side detail panel with status selector and save button.
- Empty, loading, and error states.

Link `/admin-assets/admin.css` and `/admin-assets/admin.js`.

- [ ] **Step 4: Create dashboard CSS**

Create `frontend/admin/admin.css` with:

- Neutral white and gray operational palette with teal status accents.
- Stable table columns and compact controls.
- Status badges for all supported states.
- A fixed right-side detail panel on desktop.
- A full-width overlay detail panel below `900px`.
- Visible keyboard focus and disabled/loading states.

- [ ] **Step 5: Create dashboard JavaScript**

Create `frontend/admin/admin.js` implementing:

```javascript
const API_KEY_STORAGE = "sagpt_admin_api_key";
const state = { page: 1, pageSize: 50, status: "", country: "", search: "", selected: null };

function apiHeaders(extra = {}) {
  return { "X-API-Key": sessionStorage.getItem(API_KEY_STORAGE) || "", ...extra };
}
```

The script must:

- Validate the key by loading `/api/demands/admin/stats`.
- Load list and statistics in parallel.
- Build query parameters from active filters.
- Render rows safely using DOM text content.
- Open and close the detail panel.
- Update status with `PATCH /api/demands/admin/{id}/status`.
- Download filtered CSV using an authenticated fetch and Blob URL.
- Clear the session key and return to login on logout or HTTP `401`.

- [ ] **Step 6: Serve assets and page from FastAPI**

Modify `main.py`:

```python
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

admin_dir = Path(__file__).parent / "frontend" / "admin"
app.mount("/admin-assets", StaticFiles(directory=admin_dir), name="admin-assets")


@app.get("/admin/demands", include_in_schema=False)
async def demand_admin_dashboard():
    return FileResponse(admin_dir / "index.html")
```

- [ ] **Step 7: Run focused and full demand tests**

Run:

```powershell
python -m unittest tests.test_demands -v
```

Expected: all demand tests pass.

- [ ] **Step 8: Commit**

```powershell
git add frontend/admin main.py tests/test_demands.py
git commit -m "Add visual demand administration dashboard"
```

### Task 4: Full Verification And Deployment Readiness

**Files:**
- Verify all modified files

- [ ] **Step 1: Run the complete automated test suite**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Compile Python sources**

Run:

```powershell
python -m py_compile main.py app\routers\demands.py app\models\schemas.py
```

Expected: no output and exit code `0`.

- [ ] **Step 3: Check patch cleanliness**

Run:

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors; only intended dashboard changes are present.

- [ ] **Step 4: Start local service and manually verify**

Run:

```powershell
python main.py
```

Open `http://127.0.0.1:8000/admin/demands` and verify:

- Invalid key is rejected.
- Valid key loads statistics and demand rows.
- Search and filters update the list.
- A row opens the detail panel.
- Status updates persist.
- CSV export downloads the filtered records.
- Mobile viewport has no overlapping controls.

- [ ] **Step 5: Commit any verification fixes**

```powershell
git add app frontend tests main.py
git commit -m "Polish demand administration dashboard"
```

- [ ] **Step 6: Push production-ready changes**

```powershell
git push origin main
```

Expected: GitHub accepts the commits and Render begins deployment.
