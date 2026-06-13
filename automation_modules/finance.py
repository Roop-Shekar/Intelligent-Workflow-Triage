import re
from collections import Counter

import pandas as pd


def run(request_text, uploaded_file=None):
    if uploaded_file and uploaded_file.filename:
        return check_invoice_csv(uploaded_file)

    invoice_ids = re.findall(r"\b(?:INV[- ]?)?\d{3,}\b", request_text.upper())
    duplicates = [item for item, count in Counter(invoice_ids).items() if count > 1]

    if duplicates:
        summary = f"Found {len(duplicates)} possible duplicate invoice ID(s): {', '.join(duplicates)}."
    else:
        summary = "Set up an invoice duplicate check using vendor, invoice ID, amount, and due date."

    return {
        "module_name": "Invoice Duplicate Checker",
        "summary": summary,
        "success": True,
        "details": {
            "duplicate_invoice_ids": duplicates,
            "checks": ["vendor name", "invoice id", "amount", "due date"],
        },
    }


def check_invoice_csv(uploaded_file):
    invoices = pd.read_csv(uploaded_file)
    invoices.columns = [column.strip().lower() for column in invoices.columns]
    required_columns = {"invoice_id", "vendor", "amount"}

    if not required_columns.issubset(invoices.columns):
        missing = ", ".join(sorted(required_columns - set(invoices.columns)))
        return {
            "module_name": "Invoice Duplicate Checker",
            "summary": f"CSV is missing required column(s): {missing}.",
            "success": False,
            "error_message": "Invalid invoice CSV format",
        }

    duplicate_rows = invoices[invoices.duplicated("invoice_id", keep=False)]
    duplicate_rows = duplicate_rows.sort_values(["invoice_id", "vendor"])

    if duplicate_rows.empty:
        summary = f"Checked {len(invoices)} invoices. No duplicate invoice IDs were found."
    else:
        lines = [
            f"{row.invoice_id} | {row.vendor} | ${row.amount}"
            for row in duplicate_rows.itertuples()
        ]
        summary = (
            f"Checked {len(invoices)} invoices and found "
            f"{duplicate_rows['invoice_id'].nunique()} duplicate invoice ID(s): "
            + "; ".join(lines[:8])
        )

    return {
        "module_name": "Invoice Duplicate Checker",
        "summary": summary,
        "success": True,
        "details": {
            "rows_checked": len(invoices),
            "duplicate_rows": duplicate_rows.to_dict(orient="records"),
        },
    }
