
# Intelligent Workflow Triage System

A Flask project that accepts automation requests, classifies them with Gemini, routes them to department-specific modules, logs execution data, and shows automation impact on a dashboard.

The structure is intentionally simple. It is meant to look like a strong 3rd-year CSE student project: clear modules, direct database functions, and enough engineering discipline without a heavy enterprise architecture.

## Folder Structure

```text
project/
  app.py
  database.py
  services/
    classifier.py
    router.py
    analytics.py
  automation_modules/
    finance.py
    hr.py
    legal.py
    operations.py
  templates/
  static/
  database/
    schema.sql
  logs/
  reports/
  requirements.txt
  .env.example
```

## What It Does

1. A user submits an automation request in plain English.
2. `services/classifier.py` uses Gemini to classify it into HR, Finance, Legal, or Operations.
3. If Gemini is not configured, the app uses simple keyword rules so the demo still works.
4. `services/router.py` runs the correct module from `automation_modules/`.
5. `database.py` saves the request, execution log, token usage, estimated AI cost, hours saved, and cost savings.
6. `services/analytics.py` prepares dashboard metrics, Google Sheets export, and weekly PDF reports.

## Features Kept

- Gemini API integration
- Flask routes and templates
- SQLite database
- Request history
- Dashboard analytics
- Cost tracking
- Failure tracking
- Logging
- Google Sheets integration
- Weekly PDF report generation

## Database Tables

### `automation_requests`

Stores the intake request, classification result, routed module, status, hours saved, token usage, and cost estimates.

### `execution_logs`

Stores execution time, success/failure, error messages, token usage, and estimated AI cost.

### `weekly_reports`

Stores generated report metadata and a JSON snapshot of the dashboard metrics.

## Setup

Create a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create your environment file:

```powershell
copy .env.example .env
```

Run the app:

```powershell
python app.py
```

Open:

```text
http://localhost:5000
```

## Environment Variables

The app runs without API keys by using the fallback classifier.

To use Gemini:

```text
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-1.5-flash
```

To sync rows to Google Sheets:

```text
GOOGLE_SERVICE_ACCOUNT_FILE=C:\path\to\service-account.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_sheet_id
```

## Example Requests

```text
I need to compare 50 vendor invoices for duplicates.
Generate an employee onboarding checklist.
Review this contract and generate a compliance checklist.
Summarize weekly expense reports.
```

## Why This Refactor Is Simpler

The first version used an app factory, service classes, repository classes, and several wrappers. That is useful in a large production system, but it made this student project feel more complicated than it needed to be.

This version keeps the same core features but uses:

- `app.py` for routes
- `database.py` for SQLite functions
- `classifier.py` for Gemini classification
- `router.py` for choosing the automation module
- `analytics.py` for dashboard/reporting logic
- one `run()` function per automation module

That makes the project easier to explain in an interview and easier to extend.
=======
# Intelligent-Workflow-Triage

