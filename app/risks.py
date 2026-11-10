# Adding a new risk indicator only needs a new line here (NFR7).
RISK_TYPES = {
    "bleeding": "Heavy bleeding",
    "high_bp": "High blood pressure",
    "infection": "Illness / infection symptoms",
    "distance": "Transport / distance barrier",
    "other": "Other concern",
}

VISIT_OUTCOMES = ["Attended", "Referred", "Other"]

NOTE_LIMIT = 200


def risk_label(code):
    return RISK_TYPES.get(code, code)