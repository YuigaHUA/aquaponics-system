from flask import Blueprint, render_template
from flask_login import login_required


bp = Blueprint("simulator", __name__)


@bp.route("/simulator")
@login_required
def simulator_page():
    return render_template("simulator.html")
