def run(request_text):
    text = request_text.lower()
    clause_checks = {
        "contract": "Confirm parties, effective date, scope, and signature authority.",
        "compliance": "Check whether the agreement mentions regulatory or audit obligations.",
        "policy": "Compare the request against internal policy requirements.",
        "payment": "Review payment terms, due dates, late fees, and invoice process.",
        "confidentiality": "Check confidentiality duration, exceptions, and data handling rules.",
        "termination": "Review notice period, renewal language, and early termination rights.",
        "liability": "Flag liability caps, indemnity, insurance, and excluded damages.",
    }

    checklist = [
        action for keyword, action in clause_checks.items() if keyword in text
    ]
    if not checklist:
        checklist = [
            "No specific clauses were detected. Do a basic review for parties, dates, payment, confidentiality, termination, and liability."
        ]

    return {
        "module_name": "Contract Review Checklist Generator",
        "summary": "Generated legal checklist: " + " ".join(checklist),
        "success": True,
        "details": {"detected_items": checklist},
    }
