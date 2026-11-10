from datetime import date

from flask import current_app

LABELS = {
    "overdue": "Overdue",
    "due_soon": "Due soon",
    "on_time": "On track",
    "completed": "Completed",
    "review": "Needs review",
    "lost": "Lost to follow-up",
}

# Lower number = higher on the dashboard (FR6)
RANK = {"overdue": 1, "review": 2, "due_soon": 3, "on_time": 4, "completed": 5, "lost": 6}


def follow_up_status(mother, today=None):
    today = today or date.today()
    if mother.lost_reason:
        return "lost"
    if any(v.state == "review" for v in mother.visits):
        return "review"
    if any(v.state == "confirmed" for v in mother.visits):
        return "completed"
    days_left = (mother.due_date - today).days
    if days_left < 0:
        return "overdue"
    if days_left <= current_app.config["DUE_SOON_DAYS"]:
        return "due_soon"
    return "on_time"


def days_overdue(mother, today=None):
    today = today or date.today()
    return max((today - mother.due_date).days, 0)


def priority_key(mother):
    status = follow_up_status(mother)
    rank = RANK[status]
    if status == "overdue" and mother.active_risks:
        rank = 0
    return (rank, mother.due_date)


def prioritise(mothers):
    return sorted(mothers, key=priority_key)