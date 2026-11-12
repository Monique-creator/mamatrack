from datetime import date, datetime

from .risks import NOTE_LIMIT, RISK_TYPES, VISIT_OUTCOMES


def parse_date(value):
    try:
        return datetime.strptime(value or "", "%Y-%m-%d").date()
    except ValueError:
        return None


def check_mother(form):
    errors = {}
    if not form.get("full_name", "").strip():
        errors["full_name"] = "Mother's name is required."
    if not form.get("facility_id"):
        errors["facility_id"] = "Place of delivery is required."

    delivered = parse_date(form.get("delivery_date"))
    if delivered is None:
        errors["delivery_date"] = "Enter a valid delivery date."
    elif delivered > date.today():
        errors["delivery_date"] = "Delivery date cannot be in the future."

    phone = form.get("phone", "").strip()
    if phone and not phone.replace("+", "").replace(" ", "").isdigit():
        errors["phone"] = "Phone number can only contain digits."
    return errors, delivered


def check_visit(form, mother):
    errors = {}
    visited = parse_date(form.get("visit_date"))
    if visited is None:
        errors["visit_date"] = "Enter a valid visit date."
    elif visited > date.today():
        errors["visit_date"] = "Visit date cannot be in the future."
    elif visited < mother.delivery_date:
        errors["visit_date"] = "Visit date cannot be before the delivery date."

    if form.get("outcome") not in VISIT_OUTCOMES:
        errors["outcome"] = "Choose an outcome."
    if len(form.get("note", "")) > NOTE_LIMIT:
        errors["note"] = f"Note must be {NOTE_LIMIT} characters or fewer."
    return errors, visited


def check_risk(form):
    errors = {}
    if form.get("risk_type") not in RISK_TYPES:
        errors["risk_type"] = "Choose a risk indicator."
    if len(form.get("risk_note", "")) > NOTE_LIMIT:
        errors["risk_note"] = f"Note must be {NOTE_LIMIT} characters or fewer."
    return errors