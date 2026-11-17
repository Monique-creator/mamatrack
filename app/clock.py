from datetime import datetime
from zoneinfo import ZoneInfo

from flask import current_app


def today():
    """Today's date in Rwanda, even when the server runs on UTC."""
    return datetime.now(ZoneInfo(current_app.config["TIMEZONE"])).date()