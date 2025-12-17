import os
import json

def fallback_explanation(alert: dict) -> dict:
    cc = int(alert.get("connection_count", 0))
    bs = int(alert.get("bytes_sent", 0))
    br = int(alert.get("bytes_received", 0))
    device = alert.get("device_id", "unknown_device")
    dtype = alert.get("device_type", "unknown_type")
    sev = alert.get("severity", "UNKNOWN")

    why = []
    if cc > 200:
        why.append("unusually high connection volume")
    if bs > 500_000 or br > 500_000:
        why.append("unusually high data transfer")

    if not why:
        why = ["behavior deviates from baseline across one or more telemetry signals"]

    return {
        "risk_level": sev,
        "summary": f"Anomalous behavior detected for {device} ({dtype}).",
        "why_suspicious": why,
        "likely_causes": [
            "misconfiguration or firmware update",
            "new/changed usage pattern",
            "unauthorized access or compromised device"
        ],
        "recommended_actions": [
            "Verify device ownership and recent changes (app logins, firmware updates).",
            "Check router/DNS logs for unusual destinations.",
            "Temporarily isolate the device (guest network / block outbound) if risk is HIGH.",
            "Rotate Wi-Fi password and enable MFA on the device account."
        ],
    }

def explain_with_openai(alert: dict) -> dict:
    """
    Uses OpenAI if OPENAI_API_KEY is set. Returns a JSON dict explanation.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return fallback_explanation(alert)

    # Lazy import so fallback works without the package installed
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    system = (
        "You are a SOC analyst assistant for an IoT security product. "
        "Given one alert record, produce a concise triage explanation as JSON."
    )

    user = {
        "task": "Explain why this alert is suspicious and what to do next.",
        "alert": alert,
        "output_schema": {
            "risk_level": "LOW|MEDIUM|HIGH",
            "summary": "1-2 sentence summary",
            "why_suspicious": ["bullet reasons"],
            "likely_causes": ["ranked guesses"],
            "recommended_actions": ["immediate next steps"],
            "questions_to_investigate": ["what to check next"],
        },
        "constraints": [
            "Be practical and SOC-like.",
            "No long paragraphs.",
            "No markdown, output JSON only."
        ]
    }

    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user)}
        ],
        temperature=0.2,
    )

    text = resp.choices[0].message.content.strip()

    # Safety: if model returns non-JSON, fallback
    try:
        return json.loads(text)
    except Exception:
        out = fallback_explanation(alert)
        out["summary"] += " (AI output parsing failed; using fallback.)"
        return out
