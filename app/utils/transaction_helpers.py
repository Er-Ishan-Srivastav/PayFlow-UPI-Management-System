"""ACID fund transfer — mirrors sp_transfer_money."""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, func
from app import db
from app.models.bank_account import BankAccount
from app.models.upi import UPIId
from app.models.transaction import Transaction
from app.models.transaction_log import TransactionLog
from app.utils.fraud import evaluate_transfer


def _ref_id() -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    n = db.session.query(func.count(Transaction.txn_id)).scalar() or 0
    return f"TXN{stamp}{n % 10000:04d}"[:20]


def log_action(txn_id, action, old_status=None, new_status=None):
    db.session.add(
        TransactionLog(
            txn_id=txn_id,
            action=action,
            old_status=old_status,
            new_status=new_status,
        )
    )


def perform_transfer(sender_user, receiver_upi_addr, amount, remarks, pin) -> dict:
    amount = Decimal(str(amount)).quantize(Decimal("0.01"))
    if amount <= 0:
        return {"success": False, "message": "Amount must be greater than zero."}

    sender_upi = sender_user.primary_upi
    if not sender_upi:
        return {"success": False, "message": "Create a primary UPI ID before sending money."}

    if not sender_upi.check_pin(pin):
        return {"success": False, "message": "Incorrect UPI PIN."}

    receiver_upi = UPIId.query.filter_by(upi_address=receiver_upi_addr.strip().lower()).first()
    if not receiver_upi:
        return {"success": False, "message": "Receiver UPI ID does not exist."}

    if receiver_upi.user_id == sender_user.user_id:
        return {"success": False, "message": "You cannot pay yourself."}

    fraud = evaluate_transfer(sender_user, amount)
    if fraud.get("block"):
        return {"success": False, "message": fraud["message"]}

    ref = _ref_id()

    try:
        sender_acc = db.session.execute(
            select(BankAccount)
            .where(BankAccount.account_id == sender_upi.account_id)
            .with_for_update()
        ).scalar_one()
        receiver_acc = db.session.execute(
            select(BankAccount)
            .where(BankAccount.account_id == receiver_upi.account_id)
            .with_for_update()
        ).scalar_one()

        if sender_acc.balance < amount:
            txn = Transaction(
                sender_upi=sender_upi.upi_id_pk,
                receiver_upi=receiver_upi.upi_id_pk,
                sender_acc=sender_acc.account_id,
                receiver_acc=receiver_acc.account_id,
                amount=amount,
                txn_type="PAY",
                status="FAILED",
                reference_id=ref,
                remarks=remarks,
            )
            db.session.add(txn)
            db.session.flush()
            log_action(txn.txn_id, "CREATED", None, "FAILED")
            db.session.commit()
            return {"success": False, "message": "Insufficient balance.", "txn_id": ref}

        sender_acc.balance = Decimal(sender_acc.balance) - amount
        receiver_acc.balance = Decimal(receiver_acc.balance) + amount

        txn = Transaction(
            sender_upi=sender_upi.upi_id_pk,
            receiver_upi=receiver_upi.upi_id_pk,
            sender_acc=sender_acc.account_id,
            receiver_acc=receiver_acc.account_id,
            amount=amount,
            txn_type="PAY",
            status="SUCCESS",
            reference_id=ref,
            remarks=remarks,
        )
        db.session.add(txn)
        db.session.flush()
        log_action(txn.txn_id, "CREATED", None, "SUCCESS")
        if fraud.get("flag"):
            log_action(txn.txn_id, "FRAUD_FLAG", None, fraud.get("rule"))
        db.session.commit()
        return {
            "success": True,
            "message": "Payment successful.",
            "txn_id": ref,
            "new_balance": sender_acc.balance,
        }
    except Exception as exc:
        db.session.rollback()
        try:
            txn = Transaction(
                sender_upi=sender_upi.upi_id_pk,
                receiver_upi=receiver_upi.upi_id_pk,
                sender_acc=sender_upi.account_id,
                receiver_acc=receiver_upi.account_id,
                amount=amount,
                txn_type="PAY",
                status="FAILED",
                reference_id=ref,
                remarks=(remarks or "")[:80],
            )
            db.session.add(txn)
            db.session.flush()
            log_action(txn.txn_id, "CREATED", None, "FAILED")
            log_action(txn.txn_id, "ERROR", None, str(exc)[:20])
            db.session.commit()
        except Exception:
            db.session.rollback()
        return {"success": False, "message": "Transfer failed. The transaction was rolled back."}
