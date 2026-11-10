import time
from datetime import date

from dotenv import load_dotenv
from flask import Flask, current_app, g, jsonify, redirect, request, session, url_for

from .config import Config
from .models import User, db
from .permissions import can
from .risks import risk_label
from .status import LABELS, days_overdue, follow_up_status

PUBLIC_ENDPOINTS = {"main.home", "auth.login", "auth.signup", "static", "main.service_worker"}


def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from .admin import bp as admin_bp
    from .auth import bp as auth_bp
    from .chw import bp as chw_bp
    from .main import bp as main_bp
    from .mothers import bp as mothers_bp
    from .visits import bp as visits_bp

    for blueprint in (main_bp, auth_bp, mothers_bp, visits_bp, chw_bp, admin_bp):
        app.register_blueprint(blueprint)

    app.before_request(load_user)
    app.jinja_env.globals.update(can=can, status_of=follow_up_status,
                                 status_label=LABELS, risk_label=risk_label,
                                 days_overdue=days_overdue,
                                 today=lambda: date.today().isoformat())

    with app.app_context():
        db.create_all()
        from .seed import seed_if_empty
        seed_if_empty()

    return app


def load_user():
    g.user = None
    user_id = session.get("user_id")
    last_seen = session.get("last_seen", 0)

    timeout = current_app.config["PERMANENT_SESSION_LIFETIME"].total_seconds()

    if user_id and time.time() - last_seen > timeout:
        session.clear()
        session["expired"] = True
    elif user_id:
        user = db.session.get(User, user_id)
        if user and user.is_active:
            g.user = user
            session["last_seen"] = time.time()
        else:
            session.clear()

    if g.user is None and request.endpoint not in PUBLIC_ENDPOINTS:
        if request.path.startswith("/api/"):
            return jsonify(error="login required", mothers=[]), 401
        return redirect(url_for("auth.login", next=request.path))
    