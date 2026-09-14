from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func, case
from app import db
from app.models.transaction import Transaction
from app.models.bank_account import BankAccount
from app.utils.analytics import dashboard_summary, daily_volume, bank_breakdown, user_upi_pks

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@login_required
def index():
    summary = dashboard_summary(current_user.user_id)
    series = daily_volume(current_user.user_id, days=30)
    banks = bank_breakdown(current_user.user_id)
    pks = user_upi_pks(current_user.user_id)

    monthly = []
    if pks:
        # MySQL: date_format; SQLite: strftime – dialect-safe
        bind = db.session.get_bind()
        dialect = bind.dialect.name if bind is not None else "mysql"
        if dialect == "sqlite":
            month_expr = func.strftime("%Y-%m", Transaction.timestamp)
        else:
            month_expr = func.date_format(Transaction.timestamp, "%Y-%m")
        monthly = (
            db.session.query(
                month_expr.label("m"),
                func.sum(case((Transaction.status == "SUCCESS", Transaction.amount), else_=0)),
                func.count(Transaction.txn_id),
            )
            .filter(
                db.or_(Transaction.sender_upi.in_(pks), Transaction.receiver_upi.in_(pks))
            )
            .group_by("m")
            .order_by("m")
            .all()
        )

    global_banks = (
        db.session.query(
            BankAccount.bank_name,
            func.count(BankAccount.account_id),
            func.coalesce(func.sum(BankAccount.balance), 0),
        )
        .group_by(BankAccount.bank_name)
        .all()
    )

    return render_template(
        "dashboard/reports.html",
        summary=summary,
        series=series,
        banks=banks,
        monthly=monthly,
        global_banks=global_banks,
    )
