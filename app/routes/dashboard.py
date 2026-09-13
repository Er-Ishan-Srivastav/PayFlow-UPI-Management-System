from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.utils.analytics import dashboard_summary, daily_volume, bank_breakdown, recent_transactions
from app.models.upi import UPIId
from app.models.bank_account import BankAccount

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("auth.login"))


@dashboard_bp.route("/dashboard")
@login_required
def index():
    summary = dashboard_summary(current_user.user_id)
    series = daily_volume(current_user.user_id)
    banks = bank_breakdown(current_user.user_id)
    recent = recent_transactions(current_user.user_id)
    accounts = current_user.bank_accounts.all()
    upis = current_user.upi_ids.all()
    pk_map = {u.upi_id_pk: u for u in UPIId.query.all()}
    return render_template(
        "dashboard/index.html",
        summary=summary,
        series=series,
        banks=banks,
        recent=recent,
        accounts=accounts,
        upis=upis,
        pk_map=pk_map,
    )
