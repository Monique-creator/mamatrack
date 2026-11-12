"""Applies CHW updates that were saved on the phone while offline (FR7, Rule 8)."""
from datetime import datetime

from .models import Mother, RiskIndicator, Visit, db
from .validators import check_risk, check_visit


def apply_update(item, user):
    ref = str(item.get("ref", ""))[:64]
    mother = db.session.get(Mother, item.get("mother_id"))
    if not ref or mother is None or mother.chw_id != user.id:
        return "rejected", "This mother is not assigned to you."

    recorded_at = parse_time(item.get("recorded_at"))
    result, message = "synced", "Saved on the server."

    if item.get("visit_date"):
        result, message = apply_visit(item, mother, user, ref, recorded_at)
        if result == "rejected":
            return result, message

    if item.get("risk_type"):
        apply_risk(item, mother, user, ref, recorded_at)
    return result, message


def apply_visit(item, mother, user, ref, recorded_at):
    if Visit.query.filter_by(client_ref=ref).first():
        return "synced", "Already saved."

    errors, visited = check_visit(item, mother)
    if errors:
        return "rejected", " ".join(errors.values())

    existing = [v for v in mother.visits if v.state != "rejected"]
    for visit in existing:
        if visit.visit_date == visited and visit.outcome == item["outcome"]:
            return "merged", "Same visit was already recorded. Records combined."

    visit = Visit(mother=mother, visit_date=visited, outcome=item["outcome"],
                  note=(item.get("note") or "").strip() or None, source="chw",
                  client_ref=ref, recorded_by=user.id, recorded_at=recorded_at)
    db.session.add(visit)

    if existing:
        visit.state = "review"
        for other in existing:
            other.state = "review"
        return "review", "A different visit already exists. Sent to the nurse for review."
    return "synced", "Visit saved. Follow-up completed."


def apply_risk(item, mother, user, ref, recorded_at):
    risk_ref = f"{ref}-risk"
    if check_risk(item) or RiskIndicator.query.filter_by(client_ref=risk_ref).first():
        return
    db.session.add(RiskIndicator(mother=mother, risk_type=item["risk_type"],
                                 note=(item.get("risk_note") or "").strip() or None,
                                 client_ref=risk_ref, created_by=user.id,
                                 created_at=recorded_at))


def parse_time(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return datetime.now()