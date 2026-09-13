from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func
from app import db
from app.models.transaction import Transaction
from app.models.upi import UPIId


HIGH_VALUE = Decimal("50000")
RAPID_WINDOW_MIN = 5
RAPID_COUNT = 5


def evaluate_transfer(sender_user, amount) -> dict:
    amount = Decimal(str(amount))
    result = {"block": False, "flag": False, "rule": None, "message": ""}

    if amount >= HIGH_VALUE:
        result["flag"] = True
        result["rule"] = "high_value"

    upi_pks = [u.upi_id_pk for u in sender_user.upi_ids.all()]
    if upi_pks:
        since = datetime.utcnow() - timedelta(minutes=RAPID_WINDOW_MIN)
        recent = (
            db.session.query(func.count(Transaction.txn_id))
            .filter(
                Transaction.sender_upi.in_(upi_pks),
                Transaction.timestamp >= since,
                Transaction.status == "SUCCESS",
            )
            .scalar()
            or 0
        )
        if recent >= RAPID_COUNT:
            result["block"] = True
            result["flag"] = True
            result["rule"] = "rapid_fire"
            result["message"] = "Too many payments in a short window. Try again later."
            return result

        fails = (
            db.session.query(func.count(Transaction.txn_id))
            .filter(
                Transaction.sender_upi.in_(upi_pks),
                Transaction.timestamp >= since,
                Transaction.status == "FAILED",
            )
            .scalar()
            or 0
        )
        if fails >= 4:
            result["block"] = True
            result["flag"] = True
            result["rule"] = "repeated_failures"
            result["message"] = "Multiple failed attempts detected. Payment blocked."
            return result

    return result
