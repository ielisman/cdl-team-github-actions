#!/usr/bin/env python3
"""
Create Documenso documents from a template, prefill text fields from a CSV, email each signer.

Usage:
  python3 documenso_test_send.py users.csv
      DRY RUN: fetches the template, shows field mapping and payloads. Nothing is sent.
  python3 documenso_test_send.py users.csv --only igor@brooklyncdl.com,igor@redhookcdl.com --send
      Sends only to the listed emails.
  python3 documenso_test_send.py users.csv --send
      Sends to EVERY row in the CSV (asks you to type YES first).

CSV columns expected: CID, FirstName, LastName, Email, Phone, Submitted
Only the Python standard library is needed.
"""
import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request

# ---------------- CONFIG ----------------
API_TOKEN = ""  # <-- replace with your Documenso API token
# Your server is v1.12.x, where the template API lives under /api/v2-beta (not /api/v2).
BASE_URL = "https://sign.redhookcdl.com/api/v2-beta"
TEMPLATE_ID = 5  # from .../t/ateam/templates/5

# Template field label  ->  CSV column name
FIELD_MAP = {
    "firstName": "FirstName",
    "lastName": "LastName",
    "cid": "CID",
    "email": "Email",
    "phone": "Phone",
}
DELAY_SECONDS = 1.0  # pause between sends (rate limits)

EMAIL_SUBJECT = "Quick Favor Needed: Please Sign Red Hook CDL ELDT Self Certificate (Takes 30 Seconds)"

# {FirstName} is replaced per recipient. Line breaks are kept exactly as written here.
EMAIL_MESSAGE = """Dear {FirstName},

We truly APOLOGIZE for the inconvenience and for reaching out like this.

When you trained with us, we did our best to support and help YOU become a CDL driver,
now we are asking for a QUICK FAVOR in return.

To comply with FMCSA ELDT rules for behind-the-wheel,
we are required to have a SIGNED ELDT SELF-CERTIFICATION
from our current and former students.

Since self-certification for behind-the-wheel training WAS NOT SIGNED in the past,
our SCHOOL'S operations are currently PAUSED by FMCSA - we are incurring financial losses.

YOUR HELP MEANS A LOT TO US and it will allow us to get OUR SCHOOL BACK AND RUNNING.

YOUR INFORMATION IS ALREADY FILLED IN THE FORM -
all you need to do is open the link and add your signature and date.
IT TAKES LESS THAN 30 SECONDS.


THANK YOU SO MUCH FOR YOUR TIME AND SUPPORT.

Best Regards,
Red Hook Commercial Driving School, Inc."""
# ----------------------------------------


def call(method, path, body=None):
    req = urllib.request.Request(
        BASE_URL + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": API_TOKEN, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} on {method} {BASE_URL}{path}: {e.read().decode()[:500]}")


def field_label(field):
    meta = field.get("fieldMeta") or {}
    return meta.get("label") or meta.get("placeholder") or ""


def load_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [{k.strip(): (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(f)]
    return [r for r in rows if r.get("Email")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_file")
    ap.add_argument("--send", action="store_true", help="actually create + email documents")
    ap.add_argument("--only", help="comma-separated emails to restrict to")
    args = ap.parse_args()

    rows = load_rows(args.csv_file)
    if args.only:
        wanted = {e.strip().lower() for e in args.only.split(",")}
        rows = [r for r in rows if r["Email"].lower() in wanted]
    if not rows:
        sys.exit("No matching rows.")

    for col in set(FIELD_MAP.values()) | {"Email"}:
        if col not in rows[0]:
            sys.exit(f"CSV is missing column {col!r}. Found: {list(rows[0])}")

    template = call("GET", f"/template/{TEMPLATE_ID}")
    recipients = template.get("recipients") or []
    if not recipients:
        sys.exit("Template has no recipients.")
    recipient_id = recipients[0]["id"]  # R1

    fields_by_label = {}
    print("Template fields found:")
    for f in template.get("fields", []):
        print(f"  id={f.get('id')} type={f.get('type')} label={field_label(f)!r}")
        if field_label(f):
            fields_by_label[field_label(f).lower()] = f  # case-insensitive match
    missing = [k for k in FIELD_MAP if k.lower() not in fields_by_label]
    if missing:
        sys.exit(f"\nNo template field with label/placeholder: {missing}\n"
                 "Fix FIELD_MAP at the top to match the labels printed above.")

    print(f"\n{len(rows)} row(s) to process.")
    if args.send and not args.only:
        if input(f"Send to ALL {len(rows)} recipients? Type YES to confirm: ") != "YES":
            sys.exit("Cancelled.")

    ok, failed = 0, []
    for row in rows:
        prefill = []
        for label, col in FIELD_MAP.items():
            if row[col]:  # skip blanks (e.g. missing phone) so the signer can fill them in
                f = fields_by_label[label.lower()]
                prefill.append({"id": f["id"], "type": str(f.get("type", "TEXT")).lower(), "value": row[col]})
        payload = {
            "templateId": TEMPLATE_ID,
            "recipients": [{
                "id": recipient_id,
                "email": row["Email"],
                "name": f"{row['FirstName']} {row['LastName']}".strip(),
            }],
            "prefillFields": prefill,
            # Create as a draft first; the email subject/message are applied at distribute time.
            "distributeDocument": False,
        }
        distribute_meta = {
            "subject": EMAIL_SUBJECT,
            "message": EMAIL_MESSAGE.replace("{FirstName}", row["FirstName"]),
        }
        if not args.send:
            print(f"\n[DRY RUN] {row['Email']}:")
            print("1) POST /template/use")
            print(json.dumps(payload, indent=2))
            print("2) POST /document/distribute  (documentId = id returned by step 1)")
            print(json.dumps({"documentId": "<id>", "meta": distribute_meta}, indent=2))
            continue
        try:
            created = call("POST", "/template/use", payload)
            doc_id = created.get("id") or created.get("documentId")
            if doc_id is None:
                raise RuntimeError(f"Could not find document id in response: {json.dumps(created)[:300]}")
            call("POST", "/document/distribute", {"documentId": doc_id, "meta": distribute_meta})
            ok += 1
            print(f"Sent to {row['Email']} (document {doc_id})")
        except RuntimeError as e:
            failed.append(row["Email"])
            print(f"FAILED {row['Email']}: {e}")
        time.sleep(DELAY_SECONDS)

    if args.send:
        print(f"\nDone. Sent: {ok}, failed: {len(failed)} {failed if failed else ''}")
    else:
        print("\nDry run only. Add --send (and optionally --only) to create and email documents.")


if __name__ == "__main__":
    main()
