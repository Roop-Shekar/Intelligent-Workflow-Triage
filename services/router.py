from automation_modules import finance, hr, legal, operations


MODULES = {
    "Finance": finance.run,
    "HR": hr.run,
    "Legal": legal.run,
    "Operations": operations.run,
}


def run_automation(category, request_text, uploaded_file=None):
    automation = MODULES.get(category, operations.run)
    try:
        if category == "Finance":
            return automation(request_text, uploaded_file)
        return automation(request_text)
    except Exception as exc:
        return {
            "module_name": "Failed Automation",
            "summary": "The automation module failed while processing the request.",
            "success": False,
            "error_message": str(exc),
        }
