from functools import wraps

from flask import abort, g
from sqlalchemy.orm import joinedload, selectinload

# Rule 9 from the SRS: who is allowed to do what.
RULES = {
    "register_mother": {"nurse", "supervisor"},
    "edit_mother": {"nurse", "supervisor"},
    "record_visit": {"chw", "nurse"},
    "add_risk": {"chw", "nurse"},
    "change_risk": {"nurse", "supervisor"},
    "edit_completed_visit": {"supervisor"},
    "mark_lost": {"nurse", "supervisor"},
    "resolve_conflict": {"nurse", "supervisor"},
    "manage_users": {"supervisor"},
    "view_summary": {"nurse", "supervisor"},
}


def can(action, user=None):
    user = user or g.get("user")
    return user is not None and user.role in RULES.get(action, set())


def allowed(action):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not can(action):
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def visible_mothers(user):
    from .models import Mother

    # Load visits, risks and names in a few queries so 500 records still open fast (NFR2).
    query = Mother.query.options(selectinload(Mother.visits), selectinload(Mother.risks),
                                 joinedload(Mother.chw), joinedload(Mother.facility))
    if user.role == "chw":
        return query.filter_by(chw_id=user.id)
    if user.role == "nurse":
        return query.filter_by(facility_id=user.facility_id)
    return query


def can_see(user, mother):
    if user.role == "chw":
        return mother.chw_id == user.id
    if user.role == "nurse":
        return mother.facility_id == user.facility_id
    return True