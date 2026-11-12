from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from .models import AuditLog, Facility, User, db, log
from .permissions import allowed, visible_mothers
from .status import LABELS, follow_up_status

bp = Blueprint("admin", __name__, url_prefix="/admin")

ROLES = ("chw", "nurse", "supervisor")


@bp.route("/users", methods=["GET", "POST"])
@allowed("manage_users")
def users():
    if request.method == "POST":
        form = request.form
        username = form.get("username", "").strip().lower()
        if len(form.get("password", "")) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif not username or User.query.filter_by(username=username).first():
            flash("Choose a username that is not already taken.", "error")
        else:
            role = form.get("role") if form.get("role") in ROLES else "chw"
            user = User(username=username, full_name=form.get("full_name") or username,
                        role=role, is_active=True,
                        facility_id=int(form["facility_id"]) if form.get("facility_id") else None)
            user.set_password(form["password"])
            db.session.add(user)
            log(g.user, "create_user", f"{username} ({user.role})")
            db.session.commit()
            flash(f"Account for {user.full_name} created.", "success")
        return redirect(url_for("admin.users"))

    people = User.query.order_by(User.is_active, User.role, User.full_name).all()
    facilities = Facility.query.order_by(Facility.name).all()
    return render_template("admin/users.html", people=people, facilities=facilities)


@bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@allowed("manage_users")
def toggle(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == g.user.id:
        flash("You cannot disable your own account.", "error")
    else:
        user.is_active = not user.is_active
        user.locked_until = None
        log(g.user, "enable_user" if user.is_active else "disable_user", user.username)
        db.session.commit()
        flash(f"{user.full_name} is now {'active' if user.is_active else 'disabled'}.", "info")
    return redirect(url_for("admin.users"))


@bp.route("/summary")
@allowed("view_summary")
def summary():
    table = {}
    for mother in visible_mothers(g.user).all():
        row = table.setdefault(mother.facility.name, {key: 0 for key in LABELS} | {"risk": 0})
        row[follow_up_status(mother)] += 1
        row["risk"] += bool(mother.active_risks)
    entries = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(15).all()
    return render_template("admin/summary.html", table=table, labels=LABELS, entries=entries)