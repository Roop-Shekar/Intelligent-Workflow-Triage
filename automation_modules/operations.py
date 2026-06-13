def run(request_text):
    lines = [line.strip("- ").strip() for line in request_text.splitlines() if line.strip()]
    if not lines:
        lines = [sentence.strip() for sentence in request_text.split(".") if sentence.strip()]

    blockers = [line for line in lines if any(word in line.lower() for word in ["blocked", "delay", "issue", "risk"])]
    metrics = [line for line in lines if any(char.isdigit() for char in line)]
    actions = [line for line in lines if any(word in line.lower() for word in ["next", "follow", "need", "plan"])]

    summary_parts = []
    if metrics:
        summary_parts.append("Metrics: " + "; ".join(metrics[:3]))
    if blockers:
        summary_parts.append("Blockers: " + "; ".join(blockers[:3]))
    if actions:
        summary_parts.append("Next actions: " + "; ".join(actions[:3]))
    if not summary_parts:
        summary_parts.append("Summary: " + "; ".join(lines[:4]))

    return {
        "module_name": "Weekly Operations Summary Generator",
        "summary": " ".join(summary_parts),
        "success": True,
        "details": {"metrics": metrics, "blockers": blockers, "actions": actions},
    }
