# SAGPT WeChat Demand Mini Program Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a native WeChat mini program where authenticated Chinese enterprise users can improve and submit demands, upload protected attachments, view their own demand status, and receive authorized status notifications.

**Architecture:** Add a separate `/api/mini` FastAPI boundary backed by new WeChat-user/session tables and ownership fields on demands. Keep the existing demand matching and administration flow, store attachments on a Render persistent disk behind authorized download endpoints, and add a native `miniprogram/` client that never exposes expert or Stripe data.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, PostgreSQL, `httpx`, existing OpenAI-compatible GLM client, Render persistent disk, native WeChat Mini Program JavaScript/WXML/WXSS.

---

## File Structure

### Backend files to create

- `app/core/mini_auth.py`: bearer-token parsing, mini-session creation, and current mini-user dependency.
- `app/core/mini_files.py`: attachment validation, random storage names, and safe disk paths.
- `app/routers/mini.py`: all mini-program login, profile, demand, attachment, AI optimization, and subscription endpoints.
- `app/services/wechat_service.py`: WeChat code exchange, phone retrieval, and subscription-message delivery.
- `tests/test_mini_auth.py`: mini authentication and ownership tests.
- `tests/test_mini_demands.py`: demand creation, idempotency, AI response, and privacy tests.
- `tests/test_mini_files.py`: attachment validation and authorization tests.
- `tests/test_wechat_notifications.py`: notification trigger and failure-isolation tests.
- `miniprogram/app.js`, `app.json`, `app.wxss`, `project.config.json`, `sitemap.json`: native mini-program shell.
- `miniprogram/config.js`: API base URL and non-secret client settings.
- `miniprogram/utils/api.js`: authenticated request and upload wrapper.
- `miniprogram/utils/session.js`: WeChat login and token persistence.
- `miniprogram/utils/draft.js`: local demand draft persistence.
- `miniprogram/pages/index/*`: home page.
- `miniprogram/pages/publish/*`: demand form, AI improvement, attachment upload, consent, and submission.
- `miniprogram/pages/demands/*`: current user demand list.
- `miniprogram/pages/demand-detail/*`: current user demand detail.
- `miniprogram/pages/privacy/*`: privacy summary.
- `docs/wechat-mini-program-release.md`: configuration, Render deployment, and WeChat release checklist.

### Backend files to modify

- `app/models/models.py`: add mini users, sessions, subscription grants, attachment metadata, and demand ownership/idempotency fields.
- `app/models/schemas.py`: add mini-program request and public response schemas.
- `app/core/config.py`: add WeChat and attachment settings.
- `app/services/ai_service.py`: add non-streaming demand-description improvement method.
- `app/routers/demands.py`: invoke notification service after qualifying admin status changes.
- `main.py`: register the mini router.
- `.env.example`: document new environment variables.
- `requirements.txt`: add `httpx`.
- `render.yaml`: mount persistent disk and define non-secret upload settings.

## API Contract

All protected mini-program endpoints require:

```http
Authorization: Bearer <opaque-mini-session-token>
```

Endpoints:

```text
POST   /api/mini/auth/login
POST   /api/mini/profile/phone
GET    /api/mini/me
POST   /api/mini/demands/improve
POST   /api/mini/attachments
GET    /api/mini/attachments/{attachment_id}
POST   /api/mini/demands
GET    /api/mini/demands
GET    /api/mini/demands/{demand_id}
POST   /api/mini/subscriptions/grant
```

---

### Task 1: Add Mini-Program Configuration and Persistence Models

**Files:**
- Modify: `app/core/config.py`
- Modify: `app/models/models.py`
- Modify: `.env.example`
- Test: `tests/test_mini_auth.py`

- [ ] **Step 1: Write the failing model/config test**

```python
# tests/test_mini_auth.py
import unittest
from app.core.config import Settings
from app.models.models import MiniUser, MiniSession, MiniSubscriptionGrant


class MiniModelTests(unittest.TestCase):
    def test_wechat_settings_and_models_exist(self):
        settings = Settings()
        self.assertTrue(hasattr(settings, "WECHAT_APP_ID"))
        self.assertTrue(hasattr(settings, "WECHAT_APP_SECRET"))
        self.assertEqual(MiniUser.__tablename__, "mini_users")
        self.assertEqual(MiniSession.__tablename__, "mini_sessions")
        self.assertEqual(MiniSubscriptionGrant.__tablename__, "mini_subscription_grants")
```

- [ ] **Step 2: Run the test and verify failure**

Run: `python -m unittest tests.test_mini_auth.MiniModelTests.test_wechat_settings_and_models_exist -v`

Expected: FAIL because mini settings and models do not exist.

- [ ] **Step 3: Add settings and models**

Add to `Settings`:

```python
WECHAT_APP_ID: str = os.getenv("WECHAT_APP_ID", "")
WECHAT_APP_SECRET: str = os.getenv("WECHAT_APP_SECRET", "")
WECHAT_CONTACTED_TEMPLATE_ID: str = os.getenv("WECHAT_CONTACTED_TEMPLATE_ID", "")
WECHAT_COMPLETED_TEMPLATE_ID: str = os.getenv("WECHAT_COMPLETED_TEMPLATE_ID", "")
MINI_SESSION_DAYS: int = int(os.getenv("MINI_SESSION_DAYS", "30"))
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
MAX_ATTACHMENT_BYTES: int = 20 * 1024 * 1024
MAX_ATTACHMENTS_PER_DEMAND: int = 3
```

Add models with these exact responsibilities:

```python
class MiniUser(Base):
    __tablename__ = "mini_users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    openid = Column(String(128), nullable=False, unique=True, index=True)
    unionid = Column(String(128), unique=True, index=True)
    phone = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MiniSession(Base):
    __tablename__ = "mini_sessions"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mini_user_id = Column(String(36), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MiniSubscriptionGrant(Base):
    __tablename__ = "mini_subscription_grants"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mini_user_id = Column(String(36), nullable=False, index=True)
    template_id = Column(String(255), nullable=False, index=True)
    remaining_uses = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DemandAttachment(Base):
    __tablename__ = "demand_attachments"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mini_user_id = Column(String(36), nullable=False, index=True)
    demand_id = Column(String(36), index=True)
    original_name = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=False, unique=True)
    content_type = Column(String(150), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

Add to `Demand`:

```python
mini_user_id = Column(String(36), index=True)
client_request_id = Column(String(100), unique=True, index=True)
```

- [ ] **Step 4: Document environment variables**

Append to `.env.example`:

```dotenv
WECHAT_APP_ID=wx_your_app_id
WECHAT_APP_SECRET=your_wechat_app_secret
WECHAT_CONTACTED_TEMPLATE_ID=your_contacted_template_id
WECHAT_COMPLETED_TEMPLATE_ID=your_completed_template_id
MINI_SESSION_DAYS=30
UPLOAD_DIR=/var/data/sagpt-uploads
```

- [ ] **Step 5: Run the focused test**

Run: `python -m unittest tests.test_mini_auth.MiniModelTests.test_wechat_settings_and_models_exist -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/core/config.py app/models/models.py .env.example tests/test_mini_auth.py
git commit -m "Add mini program persistence models"
```

---

### Task 2: Implement WeChat Login and Bearer Sessions

**Files:**
- Create: `app/services/wechat_service.py`
- Create: `app/core/mini_auth.py`
- Create: `app/routers/mini.py`
- Modify: `app/models/schemas.py`
- Modify: `main.py`
- Modify: `requirements.txt`
- Test: `tests/test_mini_auth.py`

- [ ] **Step 1: Write failing authentication tests**

```python
def test_mini_auth_uses_bearer_token_and_hashes_session(self):
    from app.core.mini_auth import parse_bearer_token
    self.assertEqual(parse_bearer_token("Bearer secret-token"), "secret-token")
    with self.assertRaises(Exception):
        parse_bearer_token(None)


def test_wechat_code_exchange_contract(self):
    from app.services.wechat_service import WeChatService
    service = WeChatService(app_id="wx-test", app_secret="secret")
    self.assertEqual(service.app_id, "wx-test")
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_mini_auth -v`

Expected: FAIL because modules are missing.

- [ ] **Step 3: Implement WeChat service**

`app/services/wechat_service.py` must use `httpx` and expose:

```python
class WeChatService:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret

    async def exchange_code(self, code: str) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://api.weixin.qq.com/sns/jscode2session",
                params={
                    "appid": self.app_id,
                    "secret": self.app_secret,
                    "js_code": code,
                    "grant_type": "authorization_code",
                },
            )
        payload = response.json()
        if response.is_error or payload.get("errcode"):
            raise WeChatAPIError("WeChat login failed")
        return payload
```

Do not log `session_key`, AppSecret, or raw tokens.

- [ ] **Step 4: Implement mini bearer authentication**

`app/core/mini_auth.py` must:

- parse `Authorization: Bearer ...`;
- hash tokens using existing `hash_opaque_token`;
- create 30-day opaque sessions using existing `generate_opaque_token`;
- reject missing, expired, revoked, and unknown sessions;
- return the matching `MiniUser`.

- [ ] **Step 5: Add login schema and route**

Add schemas:

```python
class MiniLoginRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=500)


class MiniLoginResponse(BaseModel):
    token: str
    user_id: UUID
    expires_at: datetime
```

Implement `POST /mini/auth/login`:

1. exchange code;
2. find or create `MiniUser` by `openid`;
3. create `MiniSession`;
4. return raw opaque token once.

Register `mini.router` in `main.py` using `app.include_router(mini.router, prefix="/api")`.

- [ ] **Step 6: Run tests**

Run: `python -m unittest tests.test_mini_auth -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add app/services/wechat_service.py app/core/mini_auth.py app/routers/mini.py app/models/schemas.py main.py requirements.txt tests/test_mini_auth.py
git commit -m "Add WeChat mini program authentication"
```

---

### Task 3: Add Private Mini-Program Demand APIs

**Files:**
- Modify: `app/routers/mini.py`
- Modify: `app/models/schemas.py`
- Test: `tests/test_mini_demands.py`

- [ ] **Step 1: Write failing ownership and privacy tests**

```python
class MiniDemandContractTests(unittest.TestCase):
    def test_public_mini_demand_never_contains_internal_matching_data(self):
        from app.models.schemas import MiniDemandResponse
        self.assertNotIn("matched_expert_ids", MiniDemandResponse.model_fields)
        self.assertNotIn("ai_match_score", MiniDemandResponse.model_fields)

    def test_routes_require_current_mini_user(self):
        source = Path("app/routers/mini.py").read_text(encoding="utf-8")
        self.assertIn('@router.post("/demands")', source)
        self.assertIn('@router.get("/demands")', source)
        self.assertIn('@router.get("/demands/{demand_id}")', source)
        self.assertGreaterEqual(source.count("Depends(get_current_mini_user)"), 3)
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_mini_demands -v`

Expected: FAIL because schemas and routes do not exist.

- [ ] **Step 3: Add public mini demand schemas**

```python
class MiniDemandCreate(BaseModel):
    client_request_id: str = Field(..., min_length=8, max_length=100)
    target_country: str = Field(..., min_length=1, max_length=100)
    industry: str = Field(..., min_length=1, max_length=100)
    scenario: str = Field(..., min_length=1, max_length=100)
    budget_range: str = Field(..., min_length=1, max_length=100)
    urgency: str = Field(default="normal", pattern="^(normal|urgent)$")
    description: str = Field(..., min_length=10, max_length=2000)
    company_name: str = Field(..., min_length=1, max_length=200)
    wechat_phone: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=5, max_length=50)
    email: Optional[EmailStr] = None
    attachment_ids: List[UUID] = Field(default_factory=list, max_length=3)


class MiniDemandResponse(BaseModel):
    id: UUID
    target_country: str
    industry: str
    scenario: str
    budget_range: str
    urgency: str
    description: str
    company_name: str
    wechat_phone: str
    phone: str
    email: Optional[str]
    status: str
    attachment_ids: List[UUID]
    created_at: datetime
    updated_at: Optional[datetime]
```

- [ ] **Step 4: Implement create/list/detail routes**

Rules:

- Require current mini user.
- On duplicate `client_request_id`, return the existing demand owned by the same user.
- Reject a `client_request_id` already used by another user.
- Attach only attachment records owned by the current user and not already linked.
- Store `email or ""` because the existing database column is non-null.
- Call existing `schedule_demand_matching`.
- Filter every list/detail query by `Demand.mini_user_id == mini_user.id`.
- Return only `MiniDemandResponse`; never return matching fields.

- [ ] **Step 5: Run tests**

Run: `python -m unittest tests.test_mini_demands -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/routers/mini.py app/models/schemas.py tests/test_mini_demands.py
git commit -m "Add private mini program demand APIs"
```

---

### Task 4: Add Protected Attachment Upload and Download

**Files:**
- Create: `app/core/mini_files.py`
- Modify: `app/routers/mini.py`
- Modify: `render.yaml`
- Test: `tests/test_mini_files.py`

- [ ] **Step 1: Write failing file-policy tests**

```python
import unittest
from app.core.mini_files import validate_attachment


class MiniFileTests(unittest.TestCase):
    def test_accepts_supported_file(self):
        validate_attachment("brief.pdf", "application/pdf", 1024)

    def test_rejects_unsupported_or_oversized_file(self):
        with self.assertRaises(ValueError):
            validate_attachment("payload.exe", "application/octet-stream", 1024)
        with self.assertRaises(ValueError):
            validate_attachment("large.pdf", "application/pdf", 20 * 1024 * 1024 + 1)
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_mini_files -v`

Expected: FAIL because file policy does not exist.

- [ ] **Step 3: Implement file validation and safe paths**

Allow:

```python
ALLOWED_ATTACHMENT_TYPES = {
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
    ".pdf": {"application/pdf"},
    ".doc": {"application/msword"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
}
```

`safe_storage_path(upload_dir, stored_name)` must resolve the path and verify it remains under `upload_dir`.

- [ ] **Step 4: Implement upload and download endpoints**

- `POST /mini/attachments` accepts one `UploadFile`, streams it to disk, enforces the 20MB limit while reading, and creates `DemandAttachment`.
- `GET /mini/attachments/{attachment_id}` only returns the file when the attachment belongs to the current mini user.
- Use a UUID-based stored filename and preserve the original filename only as metadata.
- Delete partial files if validation or database persistence fails.

- [ ] **Step 5: Configure Render persistent disk**

Before deploying attachments to production, manually upgrade the `sagpt-api` Render Web Service from the free plan to a paid instance type that supports persistent disks. Do not enable production attachment uploads while `sagpt-api` remains on the free plan because files would be lost on restart or redeploy.

Add to the backend service in `render.yaml`:

```yaml
plan: starter
disk:
  name: sagpt-uploads
  mountPath: /var/data
  sizeGB: 1
envVars:
  - key: UPLOAD_DIR
    value: /var/data/sagpt-uploads
```

- [ ] **Step 6: Run tests**

Run: `python -m unittest tests.test_mini_files -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add app/core/mini_files.py app/routers/mini.py render.yaml tests/test_mini_files.py
git commit -m "Add protected mini program attachments"
```

---

### Task 5: Add AI Demand Description Improvement

**Files:**
- Modify: `app/services/ai_service.py`
- Modify: `app/models/schemas.py`
- Modify: `app/routers/mini.py`
- Test: `tests/test_mini_demands.py`

- [ ] **Step 1: Write the failing AI contract test**

```python
def test_improve_endpoint_is_authenticated_and_returns_suggestion(self):
    source = Path("app/routers/mini.py").read_text(encoding="utf-8")
    self.assertIn('@router.post("/demands/improve")', source)
    self.assertIn("Depends(get_current_mini_user)", source)
    self.assertIn("improve_demand_description", source)
```

- [ ] **Step 2: Run the test and verify failure**

Run: `python -m unittest tests.test_mini_demands.MiniDemandContractTests.test_improve_endpoint_is_authenticated_and_returns_suggestion -v`

Expected: FAIL.

- [ ] **Step 3: Add non-streaming AI method**

Add `LLMService.improve_demand_description(fields: dict) -> str` that:

- sends a concise Chinese system prompt;
- asks for a clear, factual 100-500 Chinese-character description;
- does not invent budget, country, company, or regulatory facts;
- returns the original description when no client is configured or the call fails.

- [ ] **Step 4: Add schema and route**

```python
class MiniDemandImproveRequest(BaseModel):
    target_country: str = Field(..., min_length=1, max_length=100)
    industry: str = Field(..., min_length=1, max_length=100)
    scenario: str = Field(..., min_length=1, max_length=100)
    budget_range: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=2000)


class MiniDemandImproveResponse(BaseModel):
    original: str
    suggestion: str
```

Require login and return both texts so the mini program can ask the user to confirm replacement.

- [ ] **Step 5: Run tests and commit**

Run: `python -m unittest tests.test_mini_demands -v`

Expected: PASS.

```bash
git add app/services/ai_service.py app/models/schemas.py app/routers/mini.py tests/test_mini_demands.py
git commit -m "Add AI demand description improvement"
```

---

### Task 6: Add Phone Binding and Subscription Notifications

**Files:**
- Modify: `app/services/wechat_service.py`
- Modify: `app/models/schemas.py`
- Modify: `app/routers/mini.py`
- Modify: `app/routers/demands.py`
- Test: `tests/test_wechat_notifications.py`

- [ ] **Step 1: Write failing notification tests**

```python
class WeChatNotificationContractTests(unittest.TestCase):
    def test_only_contacted_and_completed_trigger_notifications(self):
        source = Path("app/routers/demands.py").read_text(encoding="utf-8")
        self.assertIn('{"contacted", "completed"}', source)
        self.assertIn("send_demand_status_notification", source)

    def test_notification_failure_does_not_rollback_status(self):
        source = Path("app/routers/demands.py").read_text(encoding="utf-8")
        self.assertIn("except WeChatAPIError", source)
        self.assertIn("db.commit()", source)
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_wechat_notifications -v`

Expected: FAIL.

- [ ] **Step 3: Add WeChat phone and message methods**

`WeChatService` must provide:

- `get_phone_number(code)` using a cached access token;
- `send_subscription_message(openid, template_id, page, data)`;
- generic errors that do not expose WeChat secrets.

- [ ] **Step 4: Add mini routes**

- `POST /mini/profile/phone`: accepts the one-time phone code, retrieves phone, and stores it on `MiniUser`.
- `POST /mini/subscriptions/grant`: stores one grant per accepted template authorization.
- `GET /mini/me`: returns mini user ID and bound phone only.

- [ ] **Step 5: Trigger notification after status commit**

In `update_demand_status_for_admin`:

1. update and commit status first;
2. if status is `contacted` or `completed` and demand has `mini_user_id`, attempt notification;
3. consume one matching subscription grant only after a successful send;
4. catch and log `WeChatAPIError` without changing the successful admin response.

- [ ] **Step 6: Run tests and commit**

Run: `python -m unittest tests.test_wechat_notifications -v`

Expected: PASS.

```bash
git add app/services/wechat_service.py app/models/schemas.py app/routers/mini.py app/routers/demands.py tests/test_wechat_notifications.py
git commit -m "Add WeChat status notifications"
```

---

### Task 7: Scaffold the Native WeChat Mini Program

**Files:**
- Create: `miniprogram/app.js`
- Create: `miniprogram/app.json`
- Create: `miniprogram/app.wxss`
- Create: `miniprogram/project.config.json`
- Create: `miniprogram/sitemap.json`
- Create: `miniprogram/config.js`
- Create: `miniprogram/utils/api.js`
- Create: `miniprogram/utils/session.js`
- Create: `miniprogram/utils/draft.js`
- Create: `miniprogram/pages/index/index.js`
- Create: `miniprogram/pages/index/index.json`
- Create: `miniprogram/pages/index/index.wxml`
- Create: `miniprogram/pages/index/index.wxss`

- [ ] **Step 1: Create the app configuration**

`app.json` must register only:

```json
{
  "pages": [
    "pages/index/index",
    "pages/publish/publish",
    "pages/demands/demands",
    "pages/demand-detail/demand-detail",
    "pages/privacy/privacy"
  ],
  "window": {
    "navigationBarTitleText": "SAGPT 企业出海服务",
    "navigationBarBackgroundColor": "#ffffff",
    "navigationBarTextStyle": "black"
  }
}
```

- [ ] **Step 2: Implement API and session utilities**

- `config.js` exports only `API_BASE_URL: "https://api.sagpt.com/api/mini"` and template IDs; no secrets.
- `session.js` calls `wx.login`, posts the code to `/auth/login`, and persists the returned bearer token.
- `api.js` retries a request once after a 401 by calling `session.login()`.
- `draft.js` saves, loads, and clears a single local demand draft.

- [ ] **Step 3: Implement the home page**

The first viewport must show the SAGPT identity and two clear actions:

- “发布需求”
- “我的需求”

Both call `session.ensureLogin()` before navigation.

- [ ] **Step 4: Validate in WeChat Developer Tools**

Expected:

- project imports successfully;
- no secret values appear in source;
- both actions trigger login before navigation;
- desktop and phone simulator layouts do not overflow.

- [ ] **Step 5: Commit**

```bash
git add miniprogram
git commit -m "Scaffold SAGPT WeChat mini program"
```

---

### Task 8: Build Publish Demand, AI Improvement, Upload, and Consent Flow

**Files:**
- Create: `miniprogram/pages/publish/publish.js`
- Create: `miniprogram/pages/publish/publish.json`
- Create: `miniprogram/pages/publish/publish.wxml`
- Create: `miniprogram/pages/publish/publish.wxss`
- Create: `miniprogram/pages/privacy/privacy.js`
- Create: `miniprogram/pages/privacy/privacy.json`
- Create: `miniprogram/pages/privacy/privacy.wxml`
- Create: `miniprogram/pages/privacy/privacy.wxss`

- [ ] **Step 1: Implement form state and validation**

Required fields:

```text
company_name, wechat_phone, phone, target_country, industry,
scenario, budget_range, urgency, description, privacy_accepted
```

Email remains optional. Disable submission while submitting.

- [ ] **Step 2: Implement AI improvement confirmation**

Call `/demands/improve`, display original and suggestion in a confirmation modal, and replace the description only after user confirmation.

- [ ] **Step 3: Implement attachment selection and upload**

- Use `wx.chooseMessageFile` for PDF/Word and `wx.chooseMedia` for images.
- Enforce three files and 20MB per file before upload.
- Upload sequentially through `wx.uploadFile`.
- Store returned attachment IDs in form state.

- [ ] **Step 4: Implement consent and notifications**

- Require privacy checkbox before submission.
- Call `wx.requestSubscribeMessage` with contacted/completed template IDs.
- Post accepted template IDs to `/subscriptions/grant`.
- A rejected notification request must not block demand submission.

- [ ] **Step 5: Implement idempotent submission**

Generate one `client_request_id` when a draft starts. Preserve it through retries and clear the draft only after a successful response.

- [ ] **Step 6: Validate in WeChat Developer Tools**

Expected:

- missing fields show a specific message;
- AI failure leaves original text intact;
- fourth attachment and oversized files are rejected;
- double tap creates one request;
- successful submission navigates to demand detail.

- [ ] **Step 7: Commit**

```bash
git add miniprogram/pages/publish miniprogram/pages/privacy
git commit -m "Add mini program demand publishing flow"
```

---

### Task 9: Build My Demands and Demand Detail

**Files:**
- Create: `miniprogram/pages/demands/demands.js`
- Create: `miniprogram/pages/demands/demands.json`
- Create: `miniprogram/pages/demands/demands.wxml`
- Create: `miniprogram/pages/demands/demands.wxss`
- Create: `miniprogram/pages/demand-detail/demand-detail.js`
- Create: `miniprogram/pages/demand-detail/demand-detail.json`
- Create: `miniprogram/pages/demand-detail/demand-detail.wxml`
- Create: `miniprogram/pages/demand-detail/demand-detail.wxss`

- [ ] **Step 1: Implement demand list**

Load `/demands` on `onShow`, support pull-to-refresh, and display:

- company;
- target country;
- submission date;
- translated public status;
- updated time.

- [ ] **Step 2: Implement demand detail**

Load `/demands/{id}` and display public fields and attachment names. Open attachments through the authenticated download endpoint.

Never render:

```text
matched_expert_ids, ai_match_score, expert contact data, internal notes
```

- [ ] **Step 3: Validate privacy with two test users**

Expected:

- user A sees only user A demands;
- user B receives 404 when requesting user A demand or attachment;
- status changes appear after refresh;
- no expert or Stripe fields appear.

- [ ] **Step 4: Commit**

```bash
git add miniprogram/pages/demands miniprogram/pages/demand-detail
git commit -m "Add mini program demand tracking"
```

---

### Task 10: Production Configuration, Full Verification, and Release Guide

**Files:**
- Create: `docs/wechat-mini-program-release.md`
- Modify: `render.yaml`
- Test: all backend tests and WeChat Developer Tools

- [ ] **Step 1: Write the release guide**

Document:

1. create/re-register the WeChat mini program;
2. obtain AppID and AppSecret;
3. configure Render secrets;
4. upgrade the Render Web Service from free to starter, then create/mount the persistent disk;
5. configure `https://api.sagpt.com` as request, upload, and download legal domain;
6. configure contacted/completed subscription templates;
7. complete privacy protection guidance, service category, and filing;
8. import `miniprogram/` into WeChat Developer Tools;
9. test on a real phone;
10. submit for WeChat review and release.

- [ ] **Step 2: Run focused backend tests**

Run:

```powershell
python -m unittest tests.test_mini_auth tests.test_mini_demands tests.test_mini_files tests.test_wechat_notifications -v
```

Expected: all mini-program tests PASS.

- [ ] **Step 3: Run full regression suite**

Run:

```powershell
python -m unittest discover -s tests -v
python -m py_compile main.py app\routers\mini.py app\services\wechat_service.py app\core\mini_auth.py app\core\mini_files.py
git diff --check
```

Expected: all tests PASS, compile succeeds, and no whitespace errors.

- [ ] **Step 4: Deploy backend to Render**

Set these secret environment variables in Render:

```text
WECHAT_APP_ID
WECHAT_APP_SECRET
WECHAT_CONTACTED_TEMPLATE_ID
WECHAT_COMPLETED_TEMPLATE_ID
```

Confirm:

```text
GET https://api.sagpt.com/health -> 200
```

- [ ] **Step 5: Perform production end-to-end acceptance**

Using two real WeChat accounts:

1. login;
2. bind or enter phone;
3. improve description;
4. upload image, PDF, and Word files;
5. submit demand;
6. confirm it appears in `https://api.sagpt.com/admin/demands`;
7. confirm AI matching runs only in admin;
8. update status to contacted and receive notification;
9. update status to completed and receive notification;
10. verify the other WeChat account cannot access the demand or attachments;
11. confirm CSV export still works.

- [ ] **Step 6: Commit**

```bash
git add docs/wechat-mini-program-release.md render.yaml
git commit -m "Document WeChat mini program release"
```

---

## Implementation Order and Checkpoints

1. Tasks 1-2 establish identity and must pass before any mini-program data API is exposed.
2. Tasks 3-6 complete and secure the backend before building the client.
3. Tasks 7-9 build the native client against stable backend contracts.
4. Task 10 deploys and verifies production behavior.
5. After each task, run its focused tests and commit before continuing.

## Final Acceptance Definition

The feature is complete only when a real WeChat user can log in, publish one demand with authorized contact details and up to three protected attachments, optionally improve its description with GLM, see only their own demand status, and receive authorized contacted/completed notifications while the existing admin dashboard, AI matching, and CSV export continue working.
