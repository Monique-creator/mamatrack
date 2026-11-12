from flask import Blueprint, abort, g, jsonify, render_template, request
from sqlalchemy.exc import IntegrityError

from .models import db
from .permissions import visible_mothers
from .risks import RISK_TYPES, VISIT_OUTCOMES
from .status import prioritise
from .sync import apply_update

bp = Blueprint("chw", __name__)


@bp.route("/field")
def field():
    if g.user.role != "chw":
        abort(403)
    mothers = prioritise(visible_mothers(g.user).all())
    return render_template("chw/field.html", mothers=mothers, outcomes=VISIT_OUTCOMES,
                           risk_types=RISK_TYPES)


@bp.route("/api/sync", methods=["POST"])
def sync():
    if g.user.role != "chw":
        return jsonify(error="Only CHWs can sync field updates."), 403

    items = (request.get_json(silent=True) or {}).get("updates", [])
    results = []
    for item in items[:100]:
        try:
            with db.session.begin_nested():
                result, message = apply_update(item, g.user)
        except IntegrityError:
            result, message = "synced", "Already saved."
        results.append({"ref": item.get("ref"), "result": result, "message": message})
    db.session.commit()
    return jsonify(results=results)