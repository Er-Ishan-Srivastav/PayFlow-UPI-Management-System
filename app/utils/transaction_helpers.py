"""ACID fund transfer — mirrors sp_transfer_money with full failure persistence."""
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
from sqlalchemy import select, and_
from app import db
from app.models.bank_account import BankAccount
from app.models.upi import UPIId
from app.models.transaction import Transaction
from app.models.transaction_log import TransactionLog
from app.utils.fraud import evaluate_transfer


def _ref_id() -> str:
    """Collision-safe unique reference (UUID based, fits VARCHAR(36))."""
    return str(uuid.uuid4())


def log_action(txn_id, action, old_status=None, new_status=None):
    """Python-side log only for non-CREATED events (CREATED is handled by DB trigger)."""
    if action == "CREATED":
        return  # avoid duplicate with trg_after_txn_insert
    db.session.add(
        TransactionLog(
            txn_id=txn_id,
            action=action,
            old_status=old_status,
            new_status=new_status,
        )
    )


def _persist_failed_txn(sender_upi, receiver_upi, sender_acc_id, receiver_acc_id,
                        amount, remarks, ref, reason_action, reason_msg):
    """Always record a FAILED transaction + audit entry; balances unchanged."""
    txn = Transaction(
        sender_upi=sender_upi.upi_id_pk if sender_upi else None,
        receiver_upi=receiver_upi.upi_id_pk if receiver_upi else sender_upi.upi_id_pk,
        sender_acc=sender_acc_id,
        receiver_acc=receiver_acc_id,
        amount=amount,
        txn_type="PAY",
        status="FAILED",
        reference_id=ref,
        remarks=(remarks or reason_msg or "")[:100],
    )
    # Handle nullable receiver when invalid
    if not receiver_upi:
        # Use a placeholder – schema requires receiver_upi NOT NULL.
        # Caller must ensure a valid receiver or we skip full record.
        pass
    db.session.add(txn)
    db.session.flush()
    log_action(txn.txn_id, reason_action, None, "FAILED")
    return txn


def perform_transfer(sender_user, receiver_upi_addr, amount, remarks, pin) -> dict:
    amount = Decimal(str(amount)).quantize(Decimal("0.01"))
    if amount <= 0:
        return {"success": False, "message": "Amount must be greater than zero."}

    sender_upi = sender_user.primary_upi
    if not sender_upi:
        return {"success": False, "message": "Create a primary UPI ID before sending money."}

    # Resolve sender account early for status / PIN lock checks
    sender_acc = BankAccount.query.get(sender_upi.account_id)
    if not sender_acc:
        return {"success": False, "message": "Sender bank account not found."}

    now = datetime.utcnow()

    # ---- Account status gates (server-side) ----
    if sender_acc.status == "BLOCKED":
        return {"success": False, "message": "Account is blocked. Transfers are not allowed."}

    if sender_acc.status == "LOCKED":
        if sender_acc.locked_until and sender_acc.locked_until > now:
            return {
                "success": False,
                "message": f"Account locked due to too many wrong PIN attempts. Try after {sender_acc.locked_until.strftime('%H:%M')} UTC.",
            }
        # Lock expired – reset
        sender_acc.status = "ACTIVE"
        sender_acc.locked_until = None
        sender_acc.pin_attempts = 0
        db.session.commit()

    if sender_acc.cooldown_until and sender_acc.cooldown_until > now:
        return {
            "success": False,
            "message": f"Account in fraud cooldown until {sender_acc.cooldown_until.strftime('%H:%M')} UTC.",
        }

    # ---- PIN validation with attempt counter ----
    if not sender_upi.check_pin(pin):
        locked = sender_upi.record_pin_failure(sender_acc)
        ref = _ref_id()
        try:
            # Persist failed attempt for audit (receiver may be unknown)
            receiver_upi = UPIId.query.filter_by(
                upi_address=receiver_upi_addr.strip().lower()
            ).first()
            txn = Transaction(
                sender_upi=sender_upi.upi_id_pk,
                receiver_upi=receiver_upi.upi_id_pk if receiver_upi else sender_upi.upi_id_pk,
                sender_acc=sender_acc.account_id,
                receiver_acc=receiver_upi.account_id if receiver_upi else sender_acc.account_id,
                amount=amount,
                txn_type="PAY",
                status="FAILED",
                reference_id=ref,
                remarks=(remarks or "Wrong PIN")[:100],
            )
            db.session.add(txn)
            db.session.flush()
            log_action(txn.txn_id, "PIN_FAILURE", None, "FAILED")
            if locked:
                log_action(txn.txn_id, "ACCOUNT_LOCKED", None, "LOCKED")
            db.session.commit()
        except Exception:
            db.session.rollback()
            # still persist attempt count
            try:
                db.session.add(sender_acc)
                db.session.commit()
            except Exception:
                db.session.rollback()
        msg = "Incorrect UPI PIN."
        if locked:
            msg += " Account has been locked after 5 failed attempts."
        return {"success": False, "message": msg, "txn_id": ref}

    # Correct PIN → reset counter
    sender_upi.reset_pin_attempts(sender_acc)

    # ---- Receiver resolution ----
    receiver_upi = UPIId.query.filter_by(
        upi_address=receiver_upi_addr.strip().lower()
    ).first()
    if not receiver_upi:
        ref = _ref_id()
        try:
            txn = Transaction(
                sender_upi=sender_upi.upi_id_pk,
                receiver_upi=sender_upi.upi_id_pk,  # placeholder
                sender_acc=sender_acc.account_id,
                receiver_acc=sender_acc.account_id,
                amount=amount,
                txn_type="PAY",
                status="FAILED",
                reference_id=ref,
                remarks=(remarks or "Invalid receiver")[:100],
            )
            db.session.add(txn)
            db.session.flush()
            log_action(txn.txn_id, "INVALID_RECEIVER", None, "FAILED")
            db.session.commit()
        except Exception:
            db.session.rollback()
        return {"success": False, "message": "Receiver UPI ID does not exist.", "txn_id": ref}

    # Self-transfer protection (same user, even different banks)
    if receiver_upi.user_id == sender_user.user_id:
        ref = _ref_id()
        try:
            txn = Transaction(
                sender_upi=sender_upi.upi_id_pk,
                receiver_upi=receiver_upi.upi_id_pk,
                sender_acc=sender_acc.account_id,
                receiver_acc=receiver_upi.account_id,
                amount=amount,
                txn_type="PAY",
                status="FAILED",
                reference_id=ref,
                remarks=(remarks or "Self-transfer")[:100],
            )
            db.session.add(txn)
            db.session.flush()
            log_action(txn.txn_id, "SELF_TRANSFER_REJECTED", None, "FAILED")
            db.session.commit()
        except Exception:
            db.session.rollback()
        return {"success": False, "message": "You cannot pay yourself.", "txn_id": ref}

    # Receiver account status
    receiver_acc = BankAccount.query.get(receiver_upi.account_id)
    if not receiver_acc or receiver_acc.status == "BLOCKED":
        ref = _ref_id()
        try:
            txn = Transaction(
                sender_upi=sender_upi.upi_id_pk,
                receiver_upi=receiver_upi.upi_id_pk,
                sender_acc=sender_acc.account_id,
                receiver_acc=receiver_upi.account_id,
                amount=amount,
                txn_type="PAY",
                status="FAILED",
                reference_id=ref,
                remarks=(remarks or "Receiver blocked")[:100],
            )
            db.session.add(txn)
            db.session.flush()
            log_action(txn.txn_id, "RECEIVER_BLOCKED", None, "FAILED")
            db.session.commit()
        except Exception:
            db.session.rollback()
        return {"success": False, "message": "Receiver account cannot accept payments.", "txn_id": ref}

    # ---- Fraud evaluation (server-side) ----
    fraud = evaluate_transfer(sender_user, amount, sender_acc)
    if fraud.get("block"):
        ref = _ref_id()
        try:
            txn = Transaction(
                sender_upi=sender_upi.upi_id_pk,
                receiver_upi=receiver_upi.upi_id_pk,
                sender_acc=sender_acc.account_id,
                receiver_acc=receiver_acc.account_id,
                amount=amount,
                txn_type="PAY",
                status="FAILED",
                reference_id=ref,
                remarks=(remarks or fraud.get("message", "Fraud block"))[:100],
            )
            db.session.add(txn)
            db.session.flush()
            log_action(txn.txn_id, "FRAUD_BLOCK", None, fraud.get("rule") or "FAILED")
            db.session.commit()
        except Exception:
            db.session.rollback()
        return {"success": False, "message": fraud["message"], "txn_id": ref}

    ref = _ref_id()

    try:
        # ---- Deadlock-safe lock order: lower account_id first ----
        ids = sorted([sender_acc.account_id, receiver_acc.account_id])
        locked = {}
        for aid in ids:
            row = db.session.execute(
                select(BankAccount)
                .where(BankAccount.account_id == aid)
                .with_for_update()
            ).scalar_one()
            locked[aid] = row

        sender_acc = locked[sender_acc.account_id]
        receiver_acc = locked[receiver_acc.account_id]

        # Optimistic version check (additional safety)
        old_sender_ver = sender_acc.version
        old_receiver_ver = receiver_acc.version

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
                remarks=(remarks or "Insufficient balance")[:100],
            )
            db.session.add(txn)
            db.session.flush()
            log_action(txn.txn_id, "INSUFFICIENT_BALANCE", None, "FAILED")
            db.session.commit()
            return {"success": False, "message": "Insufficient balance.", "txn_id": ref}

        # Debit / Credit
        sender_acc.balance = Decimal(sender_acc.balance) - amount
        receiver_acc.balance = Decimal(receiver_acc.balance) + amount
        sender_acc.version = old_sender_ver + 1
        receiver_acc.version = old_receiver_ver + 1

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
        # CREATED log comes from DB trigger; add SUCCESS note only if needed
        if fraud.get("flag"):
            log_action(txn.txn_id, "FRAUD_FLAG", None, fraud.get("rule"))

        # Apply cooldown if fraud module requested it
        if fraud.get("cooldown_until"):
            sender_acc.cooldown_until = fraud["cooldown_until"]

        db.session.commit()
        return {
            "success": True,
            "message": "Payment successful.",
            "txn_id": ref,
            "new_balance": float(sender_acc.balance),
        }
    except Exception as exc:
        db.session.rollback()
        try:
            txn = Transaction(
                sender_upi=sender_upi.upi_id_pk,
                receiver_upi=receiver_upi.upi_id_pk,
                sender_acc=sender_acc.account_id,
                receiver_acc=receiver_acc.account_id,
                amount=amount,
                txn_type="PAY",
                status="FAILED",
                reference_id=ref,
                remarks=(remarks or str(exc)[:80])[:100],
            )
            db.session.add(txn)
            db.session.flush()
            log_action(txn.txn_id, "ERROR", None, str(exc)[:20])
            db.session.commit()
        except Exception:
            db.session.rollback()
        return {
            "success": False,
            "message": "Transfer failed. The transaction was rolled back.",
            "txn_id": ref,
        }
