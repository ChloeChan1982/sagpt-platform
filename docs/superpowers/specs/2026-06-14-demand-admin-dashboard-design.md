# SAGPT Demand Admin Dashboard Design

## Goal

Provide SAGPT operators with a secure visual dashboard for reviewing submitted enterprise demands, filtering and exporting records, inspecting AI matching results, and updating each demand's operational status.

## Scope

The first version includes:

- Administrator API-key login.
- Demand summary statistics.
- Search, status filtering, country filtering, and pagination.
- Demand list and detail view.
- Operational status updates.
- CSV export using the active filters.

The first version does not include permanent deletion, administrator account management, or editing customer-submitted demand details.

## Access And Security

The dashboard is served by the FastAPI backend at:

`GET /admin/demands`

The initial screen asks for the configured `API_SECRET_KEY`. The browser stores the key in `sessionStorage` only, so it is removed when the browser session closes. Every protected API request sends it through the existing `X-API-Key` header.

The HTML page itself may load without authentication, but no demand data or statistics are returned until a valid key is supplied. Invalid or expired keys return the user to the login state with a clear error.

## User Interface

The dashboard uses a restrained operational layout optimized for repeated use:

- A compact header with the SAGPT name, CSV export action, and logout action.
- Summary counters for total, pending, matching, contacted, completed, and closed demands.
- A filter bar containing keyword search, status filter, country filter, and refresh action.
- A paginated demand table showing submission time, company, target country, industry, status, and AI match score.
- A right-side detail panel that opens when an operator selects a row.

The detail panel shows:

- Company name, email, phone, and WeChat/phone contact.
- Target country, industry, scenario, budget range, and urgency.
- Full demand description.
- Attachments when present.
- AI match score and matched expert IDs.
- A status selector and explicit save action.

The interface is responsive. On narrow screens, the detail panel becomes a full-width overlay.

## Demand Status Workflow

Supported operational statuses:

- `pending`
- `matching`
- `contacted`
- `completed`
- `closed`

Status changes require an explicit save action. The server validates the requested status and persists it to PostgreSQL. The dashboard refreshes the selected row and summary counters after a successful update.

## Backend API

Existing APIs remain in use:

- `GET /api/demands/admin/list`
- `GET /api/demands/admin/export.csv`

New APIs:

- `GET /api/demands/admin/stats`
  - Returns counts for total and each supported status.
  - Uses the same administrator API-key protection.
- `PATCH /api/demands/admin/{demand_id}/status`
  - Accepts `{ "status": "<supported-status>" }`.
  - Returns the updated administrator demand representation.
  - Returns `422` for an unsupported status and `404` for an unknown demand.

CSV export applies the currently selected search, status, and country filters.

## Page Delivery

The dashboard is implemented as a small self-contained static application served by FastAPI. Its HTML, CSS, and JavaScript live under a dedicated `frontend/admin` directory and are mounted by the backend.

This keeps the operational dashboard independent from the Readdy customer-facing frontend and allows it to use the same backend origin without additional CORS configuration.

## Error Handling

The dashboard presents clear user-facing states for:

- Invalid administrator key.
- Failed network requests.
- Empty filtered results.
- Missing demand records.
- Invalid status changes.
- CSV download failures.

Buttons show loading states during requests, and repeated actions are disabled until the active request finishes.

## Testing

Automated backend tests cover:

- Administrator authentication on new endpoints.
- Status update persistence.
- Rejection of invalid statuses.
- Missing-demand behavior.
- Protected status statistics.
- Presence and routing of the dashboard page.

Manual verification covers:

- Administrator login and logout.
- Search and filter behavior.
- Detail panel rendering.
- Status update refresh.
- Filtered CSV download.
- Desktop and mobile layout.

## Deployment

The dashboard ships with the existing `sagpt-api` Render service. No new service or environment variable is required. Operators use the existing production `API_SECRET_KEY`, which must remain secret and should be rotated whenever exposed.
