from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from sqlalchemy import false, or_

from .models import Facility, Mother, User, db, log
from .permissions import allowed, can_see, visible_mothers
from .status import follow_up_status, prioritise
from .validators import check_mother

bp = Blueprint("mothers", __name__)

FILTERS = {"due_soon", "overdue", "completed", "risk", "review"}


def get_mother(mother_id):
    mother = db.get_or_404(Mother, mother_id)
    if not can_see(g.user, mother):
        abort(403)
    return mother


def form_options():
    facilities = Facility.query.order_by(Facility.name)
    chws = User.query.filter_by(role="chw", is_active=True).order_by(User.full_name)
    if g.user.role == "nurse":
        facilities = facilities.filter_by(id=g.user.facility_id)
        chws = chws.filter_by(facility_id=g.user.facility_id)
    return facilities.all(), chws.all()


@bp.route("/dashboard")
def dashboard():
    query = visible_mothers(g.user)
    term = request.args.get("q", "").strip()
    if term:
        code = term.upper().removeprefix("MT-").lstrip("0")
        match_id = Mother.id == int(code) if code.isdigit() else false()
        query = query.filter(or_(Mother.full_name.ilike(f"%{term}%"), match_id))

    mothers = prioritise(query.all())
    counts = {key: 0 for key in FILTERS}
    for mother in mothers:
        status = follow_up_status(mother)
        counts[status] = counts.get(status, 0) + 1
        counts["risk"] += bool(mother.active_risks)

    chosen = request.args.get("status")
    if chosen == "risk":
        mothers = [m for m in mothers if m.active_risks]
    elif chosen in FILTERS:
        mothers = [m for m in mothers if follow_up_status(m) == chosen]

    return render_template("mothers/dashboard.html", mothers=mothers, counts=counts,
                           term=term, chosen=chosen)


@bp.route("/mothers/new", methods=["GET", "POST"])
@allowed("register_mother")
def register():
    facilities, chws = form_options()
    errors = {}
    if request.method == "POST":
        errors, delivered = check_mother(request.form)
        if not errors:
            duplicate = Mother.query.filter(
                Mother.full_name.ilike(request.form["full_name"].strip()),
                Mother.delivery_date == delivered,
                Mother.facility_id == int(request.form["facility_id"])).first()
            if duplicate and not request.form.get("confirm_duplicate"):
                return render_template("mothers/form.html", facilities=facilities, chws=chws,
                                       errors={}, duplicate=duplicate, mother=None)

            mother = Mother(registered_by=g.user.id)
            fill_mother(mother, request.form, delivered)
            db.session.add(mother)
            db.session.commit()
            flash(f"{mother.full_name} registered. Follow-up due on "
                  f"{mother.due_date:%d %b %Y}.", "success")
            return redirect(url_for("mothers.dashboard"))

    return render_template("mothers/form.html", facilities=facilities, chws=chws,
                           errors=errors, mother=None)


@bp.route("/mothers/<int:mother_id>")
def profile(mother_id):
    mother = get_mother(mother_id)
    return render_template("mothers/profile.html", mother=mother)


@bp.route("/mothers/<int:mother_id>/edit", methods=["GET", "POST"])
@allowed("edit_mother")
def edit(mother_id):
    mother = get_mother(mother_id)
    facilities, chws = form_options()
    errors = {}
    if request.method == "POST":
        errors, delivered = check_mother(request.form)
        if not errors:
            fill_mother(mother, request.form, delivered)
            log(g.user, "edit_mother", f"{mother.code} details updated")
            db.session.commit()
            flash(f"Details saved. Follow-up due date is now {mother.due_date:%d %b %Y}.",
                  "success")
            return redirect(url_for("mothers.profile", mother_id=mother.id))

    return render_template("mothers/form.html", facilities=facilities, chws=chws,
                           errors=errors, mother=mother)


@bp.route("/mothers/<int:mother_id>/lost", methods=["POST"])
@allowed("mark_lost")
def mark_lost(mother_id):
    mother = get_mother(mother_id)
    reason = request.form.get("reason", "").strip()
    if not reason:
        flash("Give a reason before marking a mother as lost to follow-up.", "error")
    else:
        mother.lost_reason = reason[:200]
        log(g.user, "mark_lost", f"{mother.code}: {reason}")
        db.session.commit()
        flash(f"{mother.full_name} marked as lost to follow-up.", "info")
    return redirect(url_for("mothers.profile", mother_id=mother.id))


def fill_mother(mother, form, delivered):
    mother.full_name = form["full_name"].strip()
    mother.phone = form.get("phone", "").strip() or None
    mother.delivery_date = delivered
    mother.facility_id = int(form["facility_id"])
    mother.chw_id = int(form["chw_id"]) if form.get("chw_id") else None