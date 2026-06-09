# SAGPT Authentication, Membership, and Stripe Webhook Design

## Goal

Provide email/password authentication with mandatory email verification, secure
cookie sessions, password reset, a member profile API, and Stripe subscription
events that automatically update membership status.

## API Contract

The backend exposes the Readdy-defined endpoints under `/api/auth`:

- `POST /register`
- `POST /login`
- `POST /logout`
- `GET /me`
- `POST /verify-email`
- `POST /forgot-password`
- `POST /reset-password`

Stripe endpoints remain under `/api/payments`. Checkout requires a verified
session and binds the Stripe session to the user. `/webhook` verifies Stripe's
signature and processes subscription events idempotently.

## Data Model

- `users`: identity, password hash, email verification, profile fields.
- `user_sessions`: hashed opaque session tokens with expiry and revocation.
- `auth_tokens`: hashed single-use email verification and password reset tokens.
- `memberships`: one current subscription record per user.
- `stripe_webhook_events`: processed event IDs for idempotency.

## Security

- Passwords use PBKDF2-HMAC-SHA256 with random salts.
- Raw session and action tokens are never stored.
- Authentication cookie is `Secure`, `HttpOnly`, and `SameSite=Lax`.
- Registration, login, and checkout never reveal secrets.
- Forgot-password always returns the same response.
- Stripe Webhooks require `STRIPE_WEBHOOK_SECRET` signature verification.

## Membership Mapping

- `active` and `trialing` become `active`.
- `past_due`, `unpaid`, `incomplete`, `incomplete_expired`, and `canceled`
  become `expired`.
- No subscription becomes `none`.

## Email

Resend sends verification and reset links from `AUTH_FROM_EMAIL`. Links target
the Readdy pages on `APP_BASE_URL`.
