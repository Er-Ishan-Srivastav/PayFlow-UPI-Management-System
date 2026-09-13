from datetime import datetime, timedelta
from sqlalchemy import func, case, text
from app import db
from app.models.transaction import Transaction
from app.models.upi import UPIId
from app.models.bank_account import BankAccount
from app.models.user import User


def user_upi_pks(user_id):
    return [u.upi_id_pk for u in UPIId.query.filter_by(user_id=user_id).all()]


def dashboard_summary(user_id):
    pks = user_upi_pks(user_id)
    user = db.session.get(User, user_id)
    total_balance = user.total_balance if user else 0
    if not pks:
        return {
            "total_balance": total_balance,
            "sent_count": 0,
            "received_count": 0,
            "sent_amount": 0,
            "received_amount": 0,
            "failed_count": 0,
            "primary_upi": user.primary_upi.upi_address if user and user.primary_upi else None,
        }

    sent_q = db.session.query(
        func.count(Transaction.txn_id),
        func.coalesce(func.sum(case((Transaction.status == "SUCCESS", Transaction.amount), else_=0)), 0),
        func.sum(case((Transaction.status == "FAILED", 1), else_=0)),
    ).filter(Transaction.sender_upi.in_(pks)).one()

    recv_q = db.session.query(
        func.count(Transaction.txn_id),
        func.coalesce(func.sum(case((Transaction.status == "SUCCESS", Transaction.amount), else_=0)), 0),
    ).filter(Transaction.receiver_upi.in_(pks), Transaction.status == "SUCCESS").one()

    return {
        "total_balance": total_balance,
        "sent_count": sent_q[0] or 0,
        "sent_amount": sent_q[1] or 0,
        "failed_count": sent_q[2] or 0,
        "received_count": recv_q[0] or 0,
        "received_amount": recv_q[1] or 0,
        "primary_upi": user.primary_upi.upi_address if user and user.primary_upi else None,
    }


def daily_volume(user_id, days=14):
    pks = user_upi_pks(user_id)
    since = datetime.utcnow() - timedelta(days=days)
    if not pks:
        return []
    rows = (
        db.session.query(
            func.date(Transaction.timestamp).label("d"),
            func.sum(case((Transaction.status == "SUCCESS", Transaction.amount), else_=0)).label("vol"),
            func.sum(case((Transaction.status == "SUCCESS", 1), else_=0)).label("ok"),
            func.sum(case((Transaction.status == "FAILED", 1), else_=0)).label("fail"),
        )
        .filter(
            Transaction.timestamp >= since,
            db.or_(Transaction.sender_upi.in_(pks), Transaction.receiver_upi.in_(pks)),
        )
        .group_by(func.date(Transaction.timestamp))
        .order_by(func.date(Transaction.timestamp))
        .all()
    )
    out = []
    for r in rows:
        d = r[0]
        out.append(
            {
                "date": d if isinstance(d, str) else (d.isoformat() if d else ""),
                "volume": float(r[1] or 0),
                "success": int(r[2] or 0),
                "failed": int(r[3] or 0),
            }
        )
    return out


def bank_breakdown(user_id):
    rows = (
        db.session.query(
            BankAccount.bank_name,
            func.count(BankAccount.account_id),
            func.coalesce(func.sum(BankAccount.balance), 0),
        )
        .filter(BankAccount.user_id == user_id)
        .group_by(BankAccount.bank_name)
        .all()
    )
    return [
        {"bank": r[0], "accounts": r[1], "balance": float(r[2] or 0)} for r in rows
    ]


def recent_transactions(user_id, limit=8):
    pks = user_upi_pks(user_id)
    if not pks:
        return []
    return (
        Transaction.query.filter(
            db.or_(Transaction.sender_upi.in_(pks), Transaction.receiver_upi.in_(pks))
        )
        .order_by(Transaction.timestamp.desc())
        .limit(limit)
        .all()
    )
