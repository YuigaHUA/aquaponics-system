from flask import Blueprint, render_template
from flask_login import login_required


bp = Blueprint("dashboard", __name__)


@bp.route("/dashboard")
@login_required
def dashboard_page():
    return render_template("dashboard.html")
