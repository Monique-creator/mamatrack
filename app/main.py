from flask import Blueprint, g, redirect, render_template, send_from_directory, url_for

bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    if g.user:
        target = "chw.field" if g.user.role == "chw" else "mothers.dashboard"
        return redirect(url_for(target))
    return render_template("home.html")


@bp.route("/help")
def help_page():
    return render_template("help.html")


ERRORS = {
    403: ("Not allowed", "Your role does not have permission to do this."),
    404: ("Page not found", "The page or record you are looking for does not exist."),
}


@bp.app_errorhandler(403)
@bp.app_errorhandler(404)
def show_error(error):
    title, message = ERRORS[error.code]
    return render_template("error.html", code=error.code, title=title, message=message), error.code


@bp.route("/sw.js")
def service_worker():
    response = send_from_directory("static/js", "sw.js")
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response