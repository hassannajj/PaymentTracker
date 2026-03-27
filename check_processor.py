import anthropic
import base64
import json
from datetime import date

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env


def extract_checks_from_files(files, customers):
    customer_list_str = "\n".join(f"ID {c.id}: {c.name}" for c in customers)

    content = []
    for file in files:
        file_bytes = file.read()
        b64 = base64.standard_b64encode(file_bytes).decode("utf-8")
        media_type = file.content_type or "image/jpeg"
        if media_type == "application/pdf":
            content.append({
                "type": "document",
                "source": {"type": "base64", "media_type": "application/pdf", "data": b64}
            })
        else:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": b64}
            })

    prompt = f"""You are processing scanned checks for a payment tracking system.

The following customers exist in the system:
{customer_list_str}

For each check image or document provided, extract the following and return a JSON array — one element per check, in order.
Each element must have exactly these keys:
- "payer_name": name written on the check as the payer (string)
- "customer_id": integer ID of the best-matching customer above, or null if no reasonable match
- "amount": dollar amount as a number (no $ or commas)
- "check_number": check number printed on the check (string), or null
- "date": date on the check in YYYY-MM-DD format, or null
- "memo": memo/notes line (string), or null

Matching rules: match names case-insensitively and tolerantly (e.g. "J. Smith" can match "John Smith"). Set customer_id to null if ambiguous.
Do not invent data — use null for any field that is not clearly readable.
Return ONLY the JSON array, no explanation, no markdown."""

    content.append({"type": "text", "text": prompt})

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": content}]
    )

    extracted = json.loads(message.content[0].text.strip())

    today = date.today().strftime("%Y-%m-%d")
    for item in extracted:
        parts = []
        if item.get("check_number"):
            parts.append(f"Check #{item['check_number']}")
        if item.get("memo"):
            parts.append(item["memo"])
        item["notes"] = " — ".join(parts) if parts else ""
        if not item.get("date"):
            item["date"] = today

    return extracted
