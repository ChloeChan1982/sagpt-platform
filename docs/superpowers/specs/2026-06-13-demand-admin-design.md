# Demand Admin Design

## Goal

Make enterprise demand submission return immediately after persistence, and provide
protected backend APIs for staff to view and download submitted demands.

## Design

- `POST /api/demands/submit` commits the demand, schedules AI matching in a detached
  worker thread, and immediately returns the demand ID with an empty preview list.
- The background matcher opens its own SQLAlchemy session and runs blocking AI SDK
  calls outside the web server event loop.
- `GET /api/demands/admin/list` returns paginated demands with optional status, country,
  and text search filters.
- `GET /api/demands/admin/export.csv` downloads the same filtered demand data as UTF-8
  CSV with a BOM for Excel compatibility.
- Both admin endpoints require the `X-API-Key` header to match `API_SECRET_KEY`.

## Error Handling

- Invalid or missing admin keys return HTTP 401.
- Background matching failures are logged and leave the saved demand available for
  staff review and later rematching.
- CSV output serializes list fields as JSON strings.

## Verification

- Unit tests cover admin-key validation, CSV output, and route/source contracts.
- Existing project tests must remain green.
