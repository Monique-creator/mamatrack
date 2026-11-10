from datetime import datetime, timedelta

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class Facility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    district = db.Column(db.String(80))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # chw, nurse, supervisor
    facility_id = db.Column(db.Integer, db.ForeignKey("facility.id"))
    is_active = db.Column(db.Boolean, default=False)
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)

    facility = db.relationship("Facility")

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    def is_locked(self):
        return self.locked_until is not None and self.locked_until > datetime.now()

    def register_failure(self):
        self.failed_attempts = (self.failed_attempts or 0) + 1
        if self.failed_attempts >= current_app.config["MAX_FAILED_LOGINS"]:
            minutes = current_app.config["LOCK_MINUTES"]
            self.locked_until = datetime.now() + timedelta(minutes=minutes)
            self.failed_attempts = 0


class Mother(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    delivery_date = db.Column(db.Date, nullable=False)
    facility_id = db.Column(db.Integer, db.ForeignKey("facility.id"), nullable=False)
    chw_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    registered_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    lost_reason = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)

    facility = db.relationship("Facility")
    chw = db.relationship("User", foreign_keys=[chw_id])
    visits = db.relationship("Visit", backref="mother", cascade="all, delete-orphan",
                             order_by="Visit.visit_date")
    risks = db.relationship("RiskIndicator", backref="mother", cascade="all, delete-orphan",
                            order_by="RiskIndicator.created_at.desc()")

    @property
    def code(self):
        return f"MT-{self.id:04d}"

    @property
    def due_date(self):
        return self.delivery_date + timedelta(days=current_app.config["FOLLOW_UP_DAYS"])

    @property
    def active_risks(self):
        return [r for r in self.risks if r.active]


class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mother_id = db.Column(db.Integer, db.ForeignKey("mother.id"), nullable=False)
    visit_date = db.Column(db.Date, nullable=False)
    outcome = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(200))
    state = db.Column(db.String(20), default="confirmed")  # confirmed, review, rejected
    source = db.Column(db.String(10), default="web")  # web or chw
    client_ref = db.Column(db.String(64), unique=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    recorded_at = db.Column(db.DateTime, default=datetime.now)

    author = db.relationship("User")


class RiskIndicator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mother_id = db.Column(db.Integer, db.ForeignKey("mother.id"), nullable=False)
    risk_type = db.Column(db.String(30), nullable=False)
    note = db.Column(db.String(200))
    active = db.Column(db.Boolean, default=True)
    client_ref = db.Column(db.String(64), unique=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.now)

    author = db.relationship("User")


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    action = db.Column(db.String(60), nullable=False)
    detail = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship("User")


def log(user, action, detail=""):
    db.session.add(AuditLog(user_id=user.id, action=action, detail=detail[:300]))