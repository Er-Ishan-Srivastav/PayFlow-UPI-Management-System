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
    status_breakdown = []
    hour_heatmap = []
    top_counterparties = []

    if pks:
        bind = db.session.get_bind()
        dialect = bind.dialect.name if bind is not None else "mysql"
        if dialect == "sqlite":
            month_expr = func.strftime("%Y-%m", Transaction.timestamp)
            hour_expr = func.strftime("%H", Transaction.timestamp)
        else:
            month_expr = func.date_format(Transaction.timestamp, "%Y-%m")
            hour_expr = func.hour(Transaction.timestamp)

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

        status_breakdown = (
            db.session.query(
                Transaction.status,
                func.count(Transaction.txn_id),
                func.coalesce(func.sum(Transaction.amount), 0),
            )
            .filter(
                db.or_(Transaction.sender_upi.in_(pks), Transaction.receiver_upi.in_(pks))
            )
            .group_by(Transaction.status)
            .all()
        )

        hour_heatmap = (
            db.session.query(
                hour_expr.label("h"),
                func.count(Transaction.txn_id),
            )
            .filter(
                db.or_(Transaction.sender_upi.in_(pks), Transaction.receiver_upi.in_(pks)),
                Transaction.status == "SUCCESS",
            )
            .group_by("h")
            .order_by("h")
            .all()
        )

        # Top receivers (outgoing)
        top_counterparties = (
            db.session.query(
                Transaction.receiver_upi,
                func.count(Transaction.txn_id),
                func.coalesce(func.sum(case((Transaction.status == "SUCCESS", Transaction.amount), else_=0)), 0),
            )
            .filter(Transaction.sender_upi.in_(pks))
            .group_by(Transaction.receiver_upi)
            .order_by(func.count(Transaction.txn_id).desc())
            .limit(6)
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

    # Resolve UPI addresses for counterparties
    from app.models.upi import UPIId
    cp_list = []
    for upi_pk, cnt, vol in top_counterparties:
        u = db.session.get(UPIId, upi_pk)
        cp_list.append({
            "upi": u.upi_address if u else f"#{upi_pk}",
            "count": cnt,
            "volume": float(vol or 0),
        })

    return render_template(
        "dashboard/reports.html",
        summary=summary,
        series=series,
        banks=banks,
        monthly=monthly,
        global_banks=global_banks,
        status_breakdown=status_breakdown,
        hour_heatmap=hour_heatmap,
        counterparties=cp_list,
    )
