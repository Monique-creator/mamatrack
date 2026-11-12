from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .models import RiskIndicator, Visit, db, log
from .mothers import get_mother
from .permissions import allowed, visible_mothers
from .risks import RISK_TYPES, VISIT_OUTCOMES
from .status import follow_up_status
from .validators import check_risk, check_visit

bp = Blueprint("visits", __name__)


def back_to(mother):
    return redirect(url_for("mothers.profile", mother_id=mother.id))


@bp.route("/mothers/<int:mother_id>/visit", methods=["GET", "POST"])
@allowed("record_visit")
def record(mother_id):
    mother = get_mother(mother_id)
    if follow_up_status(mother) in ("completed", "review", "lost"):
        flash("This follow-up is already closed.", "info")
        return back_to(mother)

    errors = {}
    if request.method == "POST":
        errors, visited = check_visit(request.form, mother)
        if not errors:
            db.session.add(Visit(mother=mother, visit_date=visited,
                                 outcome=request.form["outcome"],
                                 note=request.form.get("note", "").strip() or None,
                                 recorded_by=g.user.id))
            db.session.commit()
            flash(f"Visit saved. {mother.full_name} is now marked Completed.", "success")
            return back_to(mother)

    return render_template("mothers/visit_form.html", mother=mother, errors=errors,
                           outcomes=VISIT_OUTCOMES)


@bp.route("/visits/<int:visit_id>/edit", methods=["GET", "POST"])
@allowed("edit_completed_visit")
def edit_completed(visit_id):
    visit = db.get_or_404(Visit, visit_id)
    if visit.state != "confirmed":
        abort(400)
    errors = {}
    if request.method == "POST":
        errors, visited = check_visit(request.form, visit.mother)
        reason = request.form.get("reason", "").strip()
        if not reason:
            errors["reason"] = "A reason is required to change a completed visit."
        if not errors:
            before = f"{visit.visit_date} {visit.outcome}"
            visit.visit_date = visited
            visit.outcome = request.form["outcome"]
            visit.note = request.form.get("note", "").strip() or None
            log(g.user, "edit_visit", f"{visit.mother.code} {before} -> "
                f"{visited} {visit.outcome}. Reason: {reason}")
            db.session.commit()
            flash("Completed visit corrected and the change was logged.", "success")
            return back_to(visit.mother)

    return render_template("mothers/visit_form.html", mother=visit.mother, visit=visit,
                           errors=errors, outcomes=VISIT_OUTCOMES)


@bp.route("/mothers/<int:mother_id>/risk", methods=["GET", "POST"])
@allowed("add_risk")
def add_risk(mother_id):
    mother = get_mother(mother_id)
    if follow_up_status(mother) not in ("on_time", "due_soon", "overdue"):
        flash("Risk indicators can only be added to current cases.", "info")
        return back_to(mother)

    errors = {}
    if request.method == "POST":
        errors = check_risk(request.form)
        if not errors:
            db.session.add(RiskIndicator(mother=mother, risk_type=request.form["risk_type"],
                                         note=request.form.get("risk_note", "").strip() or None,
                                         created_by=g.user.id))
            db.session.commit()
            flash("Risk indicator added.", "success")
            return back_to(mother)

    return render_template("mothers/risk_form.html", mother=mother, errors=errors,
                           risk_types=RISK_TYPES)


@bp.route("/risks/<int:risk_id>/clear", methods=["POST"])
@allowed("change_risk")
def clear_risk(risk_id):
    risk = db.get_or_404(RiskIndicator, risk_id)
    mother = get_mother(risk.mother_id)
    risk.active = False
    log(g.user, "clear_risk", f"{mother.code}: {RISK_TYPES.get(risk.risk_type)} removed")
    db.session.commit()
    flash("Risk indicator removed. It stays in the history.", "info")
    return back_to(mother)


@bp.route("/conflicts")
@allowed("resolve_conflict")
def conflicts():
    mothers = [m for m in visible_mothers(g.user).all() if follow_up_status(m) == "review"]
    return render_template("mothers/conflicts.html", mothers=mothers)


@bp.route("/visits/<int:visit_id>/keep", methods=["POST"])
@allowed("resolve_conflict")
def keep_visit(visit_id):
    chosen = db.get_or_404(Visit, visit_id)
    mother = get_mother(chosen.mother_id)
    if chosen.state != "review":
        abort(400)
    for visit in mother.visits:
        if visit.state == "review":
            visit.state = "confirmed" if visit.id == chosen.id else "rejected"
    log(g.user, "resolve_conflict", f"{mother.code}: kept visit of {chosen.visit_date}")
    db.session.commit()
    flash("Conflict resolved. The other record is kept in the history.", "success")
    return redirect(url_for("visits.conflicts"))