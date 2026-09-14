"""Server-side fraud rules. All decisions happen here, never only in the UI."""
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func
from app import db
from app.models.transaction import Transaction


HIGH_VALUE = Decimal("50000")
LARGE_TXN_THRESHOLD = Decimal("10000")
LARGE_TXN_COUNT = 3          # consecutive large successful txns
COOLDOWN_MINUTES = 15
RAPID_WINDOW_MIN = 5
RAPID_COUNT = 5
FAIL_WINDOW_MIN = 10
FAIL_COUNT = 4


def evaluate_transfer(sender_user, amount, sender_acc=None) -> dict:
    """
    Returns:
      block (bool) – reject the transfer
      flag (bool)  – mark as high-risk but allow
      rule (str)
      message (str)
      cooldown_until (datetime|None) – set on account when threshold hit
    """
    amount = Decimal(str(amount))
    result = {
        "block": False,
        "flag": False,
        "rule": None,
        "message": "",
        "cooldown_until": None,
    }

    if amount >= HIGH_VALUE:
        result["flag"] = True
        result["rule"] = "high_value"

    upi_pks = [u.upi_id_pk for u in sender_user.upi_ids.all()]
    if not upi_pks:
        return result

    now = datetime.utcnow()

    # Rapid-fire successful payments
    since_rapid = now - timedelta(minutes=RAPID_WINDOW_MIN)
    recent_success = (
        db.session.query(func.count(Transaction.txn_id))
        .filter(
            Transaction.sender_upi.in_(upi_pks),
            Transaction.timestamp >= since_rapid,
            Transaction.status == "SUCCESS",
        )
        .scalar()
        or 0
    )
    if recent_success >= RAPID_COUNT:
        result["block"] = True
        result["flag"] = True
        result["rule"] = "rapid_fire"
        result["message"] = "Too many payments in a short window. Try again later."
        result["cooldown_until"] = now + timedelta(minutes=COOLDOWN_MINUTES)
        return result

    # Repeated failures
    since_fail = now - timedelta(minutes=FAIL_WINDOW_MIN)
    fails = (
        db.session.query(func.count(Transaction.txn_id))
        .filter(
            Transaction.sender_upi.in_(upi_pks),
            Transaction.timestamp >= since_fail,
            Transaction.status == "FAILED",
        )
        .scalar()
        or 0
    )
    if fails >= FAIL_COUNT:
        result["block"] = True
        result["flag"] = True
        result["rule"] = "repeated_failures"
        result["message"] = "Multiple failed attempts detected. Payment blocked."
        return result

    # Large-transaction cooldown (successful large txns only)
    if amount >= LARGE_TXN_THRESHOLD:
        since_large = now - timedelta(minutes=30)
        large_count = (
            db.session.query(func.count(Transaction.txn_id))
            .filter(
                Transaction.sender_upi.in_(upi_pks),
                Transaction.timestamp >= since_large,
                Transaction.status == "SUCCESS",
                Transaction.amount >= LARGE_TXN_THRESHOLD,
            )
            .scalar()
            or 0
        )
        if large_count >= LARGE_TXN_COUNT - 1:  # this one would tip over
            result["flag"] = True
            result["rule"] = "large_txn_cooldown"
            result["cooldown_until"] = now + timedelta(minutes=COOLDOWN_MINUTES)
            # still allow this transfer; subsequent ones blocked via cooldown_until

    return result
