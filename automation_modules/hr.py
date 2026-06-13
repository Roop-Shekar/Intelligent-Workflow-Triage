def run(request_text):
    text = request_text.lower()
    role = "General Employee"
    role_tasks = []

    if "developer" in text or "engineer" in text:
        role = "Developer"
        role_tasks = [
            "Give access to GitHub, Jira, development database, and staging environment.",
            "Assign codebase walkthrough and first bug-fix ticket.",
        ]
    elif "tester" in text or "qa" in text:
        role = "Tester"
        role_tasks = [
            "Give access to test management tools and QA environments.",
            "Share regression checklist and sample bug report format.",
        ]
    elif "manager" in text:
        role = "Manager"
        role_tasks = [
            "Set up approval permissions and team dashboards.",
            "Schedule handover meetings with direct reports.",
        ]
    elif "hr" in text:
        role = "HR"
        role_tasks = [
            "Give access to HRIS, policy repository, and employee records system.",
            "Review confidentiality rules for employee data.",
        ]

    checklist = [
        "Create employee profile and employee ID.",
        "Send offer documents and policy acknowledgements.",
        "Provision email, SSO, laptop, and required apps.",
        "Schedule orientation and manager introduction.",
        "Confirm payroll, tax, benefits, and emergency contact details.",
    ] + role_tasks

    return {
        "module_name": "Onboarding Checklist Generator",
        "summary": f"Generated a {role} onboarding checklist: " + " ".join(checklist),
        "success": True,
        "details": {"role": role, "checklist": checklist},
    }
