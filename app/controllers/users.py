from flask import Blueprint, render_template
from flask_login import login_required


bp = Blueprint("users", __name__)


@bp.route("/users")
@login_required
def users_page():
    return render_template("users.html")
