import time

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .models import Facility, User, db

bp = Blueprint("auth", __name__)

HOME_FOR_ROLE = {"chw": "chw.field", "nurse": "mothers.dashboard",
                 "supervisor": "mothers.dashboard"}


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.pop("expired", False):
        flash("You were signed out after 15 minutes of inactivity.", "info")

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if user and user.is_locked():
            flash("Too many failed attempts. This account is locked for 15 minutes.", "error")
        elif user and user.check_password(password):
            if not user.is_active:
                flash("Your account is waiting for supervisor approval.", "info")
            else:
                user.failed_attempts = 0
                user.locked_until = None
                db.session.commit()
                session.clear()
                session.permanent = True
                session["user_id"] = user.id
                session["last_seen"] = time.time()
                target = request.args.get("next", "")
                if not target.startswith("/") or target.startswith("//"):
                    target = url_for(HOME_FOR_ROLE[user.role])
                return redirect(target)
        else:
            if user:
                user.register_failure()
                db.session.commit()
            flash("Incorrect username or password.", "error")

    return render_template("auth/login.html")


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    facilities = Facility.query.order_by(Facility.name).all()
    if request.method == "POST":
        form = request.form
        username = form.get("username", "").strip().lower()
        password = form.get("password", "")
        error = None

        if not all([form.get("full_name"), username, form.get("role"), form.get("facility_id")]):
            error = "Please fill in every field."
        elif form.get("role") not in ("chw", "nurse"):
            error = "Choose a valid role."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != form.get("confirm"):
            error = "Passwords do not match."
        elif User.query.filter_by(username=username).first():
            error = "That username is already taken."

        if error:
            flash(error, "error")
        else:
            user = User(username=username, full_name=form["full_name"].strip(),
                        role=form["role"], facility_id=int(form["facility_id"]))
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Account created. A supervisor will approve it before you can sign in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/signup.html", facilities=facilities)


@bp.route("/logout")
def logout():
    session.clear()
    flash("You have signed out.", "info")
    return redirect(url_for("auth.login"))