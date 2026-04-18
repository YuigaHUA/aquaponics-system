from flask import Blueprint, jsonify, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.models import User


bp = Blueprint("auth", __name__)


@bp.route("/")
def root():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard_page"))
    return redirect(url_for("auth.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        username = str(data.get("username", "")).strip()
        password = str(data.get("password", "")).strip()

        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            if request.is_json:
                return jsonify({"ok": False, "message": "账号或密码不正确。"}), 401
            flash("账号或密码不正确。", "danger")
            return render_template("login.html"), 401

        login_user(user)
        if request.is_json:
            return jsonify({"ok": True, "redirect": url_for("dashboard.dashboard_page")})
        return redirect(url_for("dashboard.dashboard_page"))

    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard_page"))
    return render_template("login.html")


@bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    if request.is_json:
        return jsonify({"ok": True})
    return redirect(url_for("auth.login"))
