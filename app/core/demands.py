import csv
import io
import json
import secrets


CSV_FIELDS = [
    "id",
    "created_at",
    "status",
    "company_name",
    "email",
    "phone",
    "wechat_phone",
    "target_country",
    "industry",
    "scenario",
    "budget_range",
    "urgency",
    "description",
    "attachments",
    "ai_match_score",
    "matched_expert_ids",
]

INSECURE_ADMIN_KEYS = {
    "sagpt-dev-secret-key-change-in-production",
    "change-this-to-a-random-secret-key-in-production",
}


def is_admin_api_key_valid(provided_key, expected_key):
    if (
        not provided_key
        or not expected_key
        or expected_key in INSECURE_ADMIN_KEYS
    ):
        return False
    return secrets.compare_digest(provided_key, expected_key)


def _attachment_detail(attachment_id, attachments_by_id):
    detail = {
        "id": str(attachment_id),
        "original_name": str(attachment_id),
        "size_bytes": None,
        "content_type": None,
        "download_url": f"/api/demands/admin/attachments/{attachment_id}",
    }
    attachment = (attachments_by_id or {}).get(str(attachment_id))
    if attachment:
        detail.update(
            {
                "original_name": getattr(attachment, "original_name", str(attachment_id)),
                "size_bytes": getattr(attachment, "size_bytes", None),
                "content_type": getattr(attachment, "content_type", None),
            }
        )
    return detail


def demand_to_admin_dict(demand, attachments_by_id=None):
    result = {}
    for field in CSV_FIELDS:
        value = getattr(demand, field, None)
        if field in {"attachments", "matched_expert_ids"}:
            value = value or []
        elif value is not None and not isinstance(value, (str, int, float, bool)):
            value = str(value)
        result[field] = value
    result["attachment_details"] = [
        _attachment_detail(attachment_id, attachments_by_id)
        for attachment_id in result["attachments"]
    ]
    return result

def build_demand_csv(demands):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for demand in demands:
        demand_dict = demand_to_admin_dict(demand)
        row = {field: demand_dict.get(field) for field in CSV_FIELDS}
        row["attachments"] = json.dumps(row["attachments"], ensure_ascii=False)
        row["matched_expert_ids"] = json.dumps(
            row["matched_expert_ids"], ensure_ascii=False
        )
        writer.writerow(row)
    return "\ufeff" + output.getvalue()
