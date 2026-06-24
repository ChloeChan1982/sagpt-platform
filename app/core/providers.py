import csv
import io
import json
from typing import Any


PROVIDER_CSV_FIELDS = [
    "id",
    "created_at",
    "updated_at",
    "status",
    "name",
    "email",
    "target_countries",
    "service_categories",
    "bio",
    "experience_years",
    "portfolio",
    "reviewed_by",
    "review_notes",
]


def _list_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _format_time(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def provider_to_admin_dict(application: Any) -> dict[str, Any]:
    return {
        "id": str(getattr(application, "id", "")),
        "created_at": _format_time(getattr(application, "created_at", None)),
        "updated_at": _format_time(getattr(application, "updated_at", None)),
        "status": getattr(application, "status", None) or "pending",
        "name": getattr(application, "name", None),
        "email": getattr(application, "email", None),
        "target_countries": _list_value(getattr(application, "target_countries", None)),
        "service_categories": _list_value(
            getattr(application, "service_categories", None)
        ),
        "bio": getattr(application, "bio", None),
        "experience_years": getattr(application, "experience_years", None),
        "portfolio": getattr(application, "portfolio", None),
        "reviewed_by": getattr(application, "reviewed_by", None),
        "review_notes": getattr(application, "review_notes", None),
    }


def build_provider_csv(applications: list[Any]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=PROVIDER_CSV_FIELDS)
    writer.writeheader()

    for application in applications:
        row = provider_to_admin_dict(application)
        row["target_countries"] = json.dumps(
            row["target_countries"], ensure_ascii=False
        )
        row["service_categories"] = json.dumps(
            row["service_categories"], ensure_ascii=False
        )
        writer.writerow({field: row.get(field) for field in PROVIDER_CSV_FIELDS})

    return "\ufeff" + output.getvalue()
