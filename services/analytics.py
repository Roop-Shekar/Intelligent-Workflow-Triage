import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

import database


def get_dashboard_data(db_path):
    metrics = database.get_metrics(db_path)
    request_rows = database.get_history(db_path, limit=10000)
    logs = database.get_logs(db_path)

    department_counts = Counter(row["category"] for row in request_rows)
    complexity_counts = Counter(row["complexity"] for row in request_rows)

    priority_totals = {}
    priority_counts = {}
    for row in request_rows:
        category = row["category"]
        priority_totals[category] = priority_totals.get(category, 0) + row["priority_score"]
        priority_counts[category] = priority_counts.get(category, 0) + 1

    metrics["department_distribution"] = [
        {"label": department, "value": count}
        for department, count in department_counts.items()
    ]
    metrics["complexity_distribution"] = [
        {"label": complexity, "value": count}
        for complexity, count in complexity_counts.items()
    ]
    metrics["priority_by_department"] = [
        {"label": category, "value": round(priority_totals[category] / count, 2)}
        for category, count in priority_counts.items()
    ]
    metrics["recent_failures"] = [row for row in logs if row["success"] == 0][:5]
    return metrics


def generate_weekly_report(db_path, reports_dir):
    metrics = get_dashboard_data(db_path)
    period_end = datetime.now(timezone.utc).date()
    period_start = period_end - timedelta(days=7)
    metrics["period_start"] = period_start.isoformat()
    metrics["period_end"] = period_end.isoformat()

    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    title = f"Weekly Automation Impact Report ({period_start} to {period_end})"
    pdf_path = reports_dir / f"weekly_impact_report_{period_start}_to_{period_end}.pdf"

    sections = [
        ("Requests Processed", str(metrics["total_requests"])),
        ("Department Distribution", format_distribution(metrics["department_distribution"])),
        ("Time Saved", f"{metrics['estimated_hours_saved']} hours"),
        ("Cost Savings", f"${metrics['estimated_cost_savings']:.2f}"),
        ("Failure Analysis", failure_summary(metrics["recent_failures"])),
        ("Recommendations", build_recommendations(metrics)),
    ]
    write_pdf(pdf_path, title, sections)

    google_doc_url = create_google_doc(title, sections)
    return {
        "title": title,
        "pdf_path": str(pdf_path),
        "google_doc_url": google_doc_url or "",
        "metrics": metrics,
    }


def append_to_google_sheet(row):
    service_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
    if not service_file or not spreadsheet_id or not row:
        return

    values = [[
        row["id"],
        row["submitted_at"],
        row["category"],
        row["priority_score"],
        row["automation_potential"],
        row["complexity"],
        row["status"],
        row["hours_saved"],
        row["cost_savings"],
    ]]
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
        "/values/Requests!A:I:append"
    )
    params = {"valueInputOption": "USER_ENTERED"}
    payload = {"values": values}
    google_request("POST", url, ["https://www.googleapis.com/auth/spreadsheets"], params=params, json=payload)


def create_google_doc(title, sections):
    service_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
    if not service_file:
        return ""

    scopes = [
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive",
    ]
    doc = google_request(
        "POST",
        "https://docs.googleapis.com/v1/documents",
        scopes,
        json={"title": title},
    ).json()
    document_id = doc["documentId"]
    text = title + "\n\n" + "\n\n".join(f"{heading}\n{body}" for heading, body in sections)
    google_request(
        "POST",
        f"https://docs.googleapis.com/v1/documents/{document_id}:batchUpdate",
        scopes,
        json={"requests": [{"insertText": {"location": {"index": 1}, "text": text}}]},
    )
    return f"https://docs.google.com/document/d/{document_id}/edit"


def google_request(method, url, scopes, **kwargs):
    # Google service accounts use OAuth: create a short-lived access token,
    # then send it as a Bearer token to Sheets or Docs.
    token = google_token(scopes)
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"

    last_error = None
    for attempt in range(3):
        try:
            response = requests.request(method, url, headers=headers, timeout=25, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt < 2:
                import time

                time.sleep(0.8 * (attempt + 1))
    raise last_error


def google_token(scopes):
    # The JSON key stays local. Google returns a temporary token for the scopes requested.
    credentials = service_account.Credentials.from_service_account_file(
        os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE"), scopes=scopes
    )
    credentials.refresh(Request())
    return credentials.token


def write_pdf(path, title, sections):
    pdf = canvas.Canvas(str(path), pagesize=letter)
    y = 740
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, title[:90])
    y -= 35

    for heading, body in sections:
        if y < 90:
            pdf.showPage()
            y = 740
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(50, y, heading)
        y -= 18
        pdf.setFont("Helvetica", 10)
        for line in wrap_text(body, 95):
            pdf.drawString(65, y, line)
            y -= 14
        y -= 8
    pdf.save()


def wrap_text(text, width):
    lines = []
    for raw_line in str(text).splitlines() or [""]:
        current = ""
        for word in raw_line.split():
            if len(current) + len(word) + 1 > width:
                lines.append(current)
                current = word
            else:
                current = f"{current} {word}".strip()
        lines.append(current)
    return lines


def format_distribution(items):
    return ", ".join(f"{item['label']}: {item['value']}" for item in items) or "No data yet"


def failure_summary(failures):
    if not failures:
        return "No failures were recorded."
    return f"{len(failures)} recent failure(s) need review."


def build_recommendations(metrics):
    if metrics["failed_automations"]:
        return "Review failed requests and add better input validation."
    if metrics["total_requests"] == 0:
        return "Submit sample requests to start building dashboard data."
    return "Keep tracking requests and expand the highest-value department modules."
