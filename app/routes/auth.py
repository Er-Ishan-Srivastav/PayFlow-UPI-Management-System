from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from urllib.parse import urlparse
from app import db, limiter
from app.models.user import User
from app.forms.auth_forms import LoginForm, RegisterForm

auth_bp = Blueprint("auth", __name__)


def _is_safe_redirect(target: str) -> bool:
    """Prevent open redirects – only allow relative local paths."""
    if not target:
        return False
    # Reject absolute URLs / protocol-relative
    parsed = urlparse(target)
    if parsed.netloc or parsed.scheme:
        return False
    if not target.startswith("/"):
        return False
    if target.startswith("//"):
        return False
    return True


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    form = LoginForm()
    if form.validate_on_submit():
        ident = form.login.data.strip()
        user = User.query.filter(
            or_(User.email == ident.lower(), User.phone == ident)
        ).first()
        if user and user.is_active and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            nxt = request.args.get("next")
            if nxt and _is_safe_redirect(nxt):
                return redirect(nxt)
            return redirect(url_for("dashboard.index"))
        flash("Invalid credentials.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip(),
            phone=form.phone.data.strip(),
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created. Sign in to continue.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Signed out.", "info")
    return redirect(url_for("auth.login"))
