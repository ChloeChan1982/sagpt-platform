import json
import os
import urllib.request


def send_auth_email(*, to_email: str, subject: str, html: str) -> None:
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    from_email = os.getenv("AUTH_FROM_EMAIL", "SAGPT <account@mail.sagpt.com>").strip()
    if not api_key:
        raise RuntimeError("Resend is not configured")

    payload = json.dumps(
        {"from": from_email, "to": [to_email], "subject": subject, "html": html}
    ).encode()
    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20):
        pass


def verification_email_html(token: str) -> str:
    app_url = os.getenv("APP_BASE_URL", "https://www.sagpt.com").rstrip("/")
    link = f"{app_url}/verify-email?token={token}"
    return f"<p>Welcome to SAGPT.</p><p><a href=\"{link}\">Verify your email</a></p>"


def reset_email_html(token: str) -> str:
    app_url = os.getenv("APP_BASE_URL", "https://www.sagpt.com").rstrip("/")
    link = f"{app_url}/reset-password?token={token}"
    return f"<p><a href=\"{link}\">Reset your SAGPT password</a></p><p>This link expires in 30 minutes.</p>"
