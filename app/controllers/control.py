from flask import Blueprint, render_template
from flask_login import login_required


bp = Blueprint("control", __name__)


@bp.route("/control")
@login_required
def control_page():
    return render_template("control.html")
