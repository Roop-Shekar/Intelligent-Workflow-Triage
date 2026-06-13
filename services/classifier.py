import json
import os
import re
import time

import requests


DEPARTMENTS = {"HR", "Finance", "Legal", "Operations"}


def classify_request(request_text):
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return fallback_classification(request_text)

    try:
        data = call_gemini(request_text, api_key)
        return parse_gemini_response(data)
    except Exception:
        return fallback_classification(request_text)


def call_gemini(request_text, api_key):
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    endpoint = os.getenv(
        "GEMINI_ENDPOINT", "https://generativelanguage.googleapis.com/v1beta"
    ).rstrip("/")
    url = f"{endpoint}/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": build_prompt(request_text)}]}]}

    last_error = None
    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(0.8 * (attempt + 1))
    raise last_error


def build_prompt(request_text):
    return f"""
Classify this automation request into one department: HR, Finance, Legal, or Operations.
Return only JSON with:
category, priority_score, automation_potential, complexity, reasoning.

priority_score: 1 to 10
automation_potential: 0 to 100
complexity: Low, Medium, or High

Request: {request_text}
"""


def parse_gemini_response(data):
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("Gemini did not return JSON")

    parsed = json.loads(match.group(0))
    usage = data.get("usageMetadata", {})
    input_tokens = usage.get("promptTokenCount", 0)
    output_tokens = usage.get("candidatesTokenCount", 0)

    category = str(parsed.get("category", "Operations")).strip()
    if category not in DEPARTMENTS:
        category = "Operations"

    try:
        priority_score = int(parsed["priority_score"])
        if priority_score < 1 or priority_score > 10:
            priority_score = 5
    except (KeyError, TypeError, ValueError):
        priority_score = 5

    try:
        automation_potential = float(parsed["automation_potential"])
        if automation_potential < 0 or automation_potential > 100:
            automation_potential = 70
    except (KeyError, TypeError, ValueError):
        automation_potential = 70

    complexity = str(parsed.get("complexity", "Medium")).strip().title()
    if complexity not in {"Low", "Medium", "High"}:
        complexity = "Medium"

    return {
        "category": category,
        "priority_score": priority_score,
        "automation_potential": automation_potential,
        "complexity": complexity,
        "reasoning": parsed.get("reasoning", ""),
        "token_usage": input_tokens + output_tokens,
        "estimated_cost": estimate_cost(input_tokens, output_tokens),
    }


def fallback_classification(request_text):
    text = request_text.lower()
    keyword_map = {
        "Finance": ["invoice", "expense", "vendor", "payment", "reimburse"],
        "HR": ["employee", "onboarding", "candidate", "leave", "payroll"],
        "Legal": ["contract", "compliance", "clause", "legal", "policy"],
        "Operations": ["weekly", "operations", "inventory", "shipment", "summary"],
    }

    category = "Operations"
    for department, keywords in keyword_map.items():
        if any(word in text for word in keywords):
            category = department
            break

    automation_potential = {
        "Finance": 90,
        "HR": 80,
        "Legal": 75,
        "Operations": 70,
    }[category]

    if any(word in text for word in ["urgent", "risk", "duplicate", "compliance"]):
        priority_score = 8
    elif category in {"Finance", "Legal"}:
        priority_score = 7
    else:
        priority_score = 6

    complexity = {
        "Finance": "Medium",
        "HR": "Low",
        "Legal": "High",
        "Operations": "Medium",
    }[category]

    return {
        "category": category,
        "priority_score": priority_score,
        "automation_potential": automation_potential,
        "complexity": complexity,
        "reasoning": "Classified using simple keyword rules.",
        "token_usage": 0,
        "estimated_cost": 0,
    }


def estimate_cost(input_tokens, output_tokens):
    input_rate = float(os.getenv("GEMINI_COST_PER_1K_INPUT_TOKENS", "0.000075"))
    output_rate = float(os.getenv("GEMINI_COST_PER_1K_OUTPUT_TOKENS", "0.0003"))
    return round((input_tokens / 1000 * input_rate) + (output_tokens / 1000 * output_rate), 6)
