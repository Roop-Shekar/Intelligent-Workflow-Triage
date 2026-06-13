print("STEP 1")

import logging
import os
import time
from pathlib import Path

print("STEP 2")

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for

print("STEP 3")

import database

print("STEP 4")

from services import analytics, classifier, router

print("STEP 5")

load_dotenv()

print("STEP 6")

app = Flask(__name__)

print("STEP 7")
app.secret_key = os.getenv("SECRET_KEY", "dev-key-change-later")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "database/triage.db")
LOG_FILE = BASE_DIR / os.getenv("LOG_FILE", "logs/triage.log")
REPORTS_DIR = BASE_DIR / "reports"
HOURS_SAVED = {
    "Finance": 3,
    "HR": 2,
    "Legal": 4,
    "Operations": 1.5,
}

print("STEP 8")
database.init_db(DB_PATH)
print("STEP 9")

LOG_FILE.parent.mkdir(exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
print("STEP 10")

@app.route("/")
def index():
    examples = [
        "I need to compare 50 vendor invoices for duplicates.",
        "Generate an employee onboarding checklist.",
        "Review this contract and generate a compliance checklist.",
        "Summarize weekly expense reports.",
    ]
    return render_template("index.html", examples=examples)


@app.route("/submit", methods=["POST"])
def submit_request():
    request_text = request.form.get("raw_request", "").strip()
    requester_name = request.form.get("requester_name", "").strip()
    department_hint = request.form.get("department_hint", "").strip()
    invoice_csv = request.files.get("invoice_csv")

    if not request_text and invoice_csv and invoice_csv.filename:
        request_text = "Check uploaded invoice CSV for duplicate invoices."

    if not request_text:
        return render_template(
            "index.html",
            examples=[],
            error="Please enter an automation request.",
        ), 400

    started = time.perf_counter()
    ai_result = classifier.classify_request(request_text)
    automation = router.run_automation(ai_result["category"], request_text, invoice_csv)

    hourly_rate = float(os.getenv("DEFAULT_HOURLY_RATE", "55"))
    status = "Success" if automation["success"] else "Failure"
    hours_saved = HOURS_SAVED.get(ai_result["category"], 1)
    if not automation["success"]:
        hours_saved = 0
    cost_savings = round(hours_saved * hourly_rate, 2)

    request_id = database.save_request(
        DB_PATH,
        {
            "requester_name": requester_name,
            "department_hint": department_hint,
            "raw_request": request_text,
            "category": ai_result["category"],
            "priority_score": ai_result["priority_score"],
            "automation_potential": ai_result["automation_potential"],
            "complexity": ai_result["complexity"],
            "module_name": automation["module_name"],
            "status": status,
            "result_summary": automation["summary"],
            "hours_saved": hours_saved,
            "cost_savings": cost_savings,
            "estimated_cost": ai_result["estimated_cost"],
            "token_usage": ai_result["token_usage"],
        },
    )

    execution_time_ms = int((time.perf_counter() - started) * 1000)
    database.save_log(
        DB_PATH,
        {
            "request_id": request_id,
            "category": ai_result["category"],
            "execution_time_ms": execution_time_ms,
            "success": 1 if automation["success"] else 0,
            "error_message": automation.get("error_message", ""),
            "token_usage": ai_result["token_usage"],
            "estimated_cost": ai_result["estimated_cost"],
        },
    )

    try:
        analytics.append_to_google_sheet(database.get_request(DB_PATH, request_id))
    except Exception as exc:
        logging.warning("google_sheet_sync_failed request_id=%s error=%s", request_id, exc)
    logging.info("request_id=%s category=%s status=%s", request_id, ai_result["category"], status)
    return redirect(url_for("request_detail", request_id=request_id))


@app.route("/requests/<int:request_id>")
def request_detail(request_id):
    automation_request = database.get_request(DB_PATH, request_id)
    if not automation_request:
        return render_template("not_found.html"), 404
    return render_template("request_detail.html", automation_request=automation_request)


@app.route("/history")
def history():
    return render_template("history.html", requests=database.get_history(DB_PATH))


@app.route("/dashboard")
def dashboard():
    metrics = analytics.get_dashboard_data(DB_PATH)
    return render_template("dashboard.html", metrics=metrics)


@app.route("/api/metrics")
def api_metrics():
    return jsonify(analytics.get_dashboard_data(DB_PATH))


@app.route("/reports")
def reports():
    return render_template("reports.html", reports=database.get_reports(DB_PATH))


@app.route("/reports/weekly", methods=["POST"])
def weekly_report():
    report = analytics.generate_weekly_report(DB_PATH, REPORTS_DIR)
    database.save_report(DB_PATH, report)
    return render_template("report_generated.html", report=report)


if __name__ == "__main__":
    print("STEP 11")
    app.run(debug=False)