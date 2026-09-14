from functools import wraps
from flask import Blueprint, render_template, abort, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, case, or_
from werkzeug.security import generate_password_hash
from app import db
from app.models.user import User
from app.models.bank_account import BankAccount
from app.models.upi import UPIId
from app.models.transaction import Transaction
from app.models.beneficiary import Beneficiary
from app.models.transaction_log import TransactionLog

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/")
@login_required
@admin_required
def console():
    stats = {
        "users": User.query.count(),
        "active_users": User.query.filter_by(is_active=True).count(),
        "blocked_users": User.query.filter_by(is_active=False).count(),
        "accounts": BankAccount.query.count(),
        "upi_ids": UPIId.query.count(),
        "beneficiaries": Beneficiary.query.count(),
        "transactions": Transaction.query.count(),
        "success_txns": Transaction.query.filter_by(status="SUCCESS").count(),
        "failed_txns": Transaction.query.filter_by(status="FAILED").count(),
        "flagged_txns": Transaction.query.filter_by(is_flagged=True).count(),
        "total_volume": db.session.query(
            func.coalesce(func.sum(case((Transaction.status == "SUCCESS", Transaction.amount), else_=0)), 0)
        ).scalar() or 0,
        "total_balance": db.session.query(
            func.coalesce(func.sum(BankAccount.balance), 0)
        ).scalar() or 0,
    }

    recent_users = User.query.order_by(User.created_at.desc()).limit(8).all()
    recent_txns = Transaction.query.order_by(Transaction.timestamp.desc()).limit(12).all()
    flagged = Transaction.query.filter_by(is_flagged=True).order_by(Transaction.timestamp.desc()).limit(8).all()

    bank_dist = (
        db.session.query(
            BankAccount.bank_name,
            func.count(BankAccount.account_id),
            func.coalesce(func.sum(BankAccount.balance), 0),
        )
        .group_by(BankAccount.bank_name)
        .order_by(func.count(BankAccount.account_id).desc())
        .all()
    )

    daily = (
        db.session.query(
            func.date(Transaction.timestamp).label("d"),
            func.count(Transaction.txn_id),
            func.sum(case((Transaction.status == "SUCCESS", Transaction.amount), else_=0)),
            func.sum(case((Transaction.status == "FAILED", 1), else_=0)),
        )
        .group_by(func.date(Transaction.timestamp))
        .order_by(func.date(Transaction.timestamp).desc())
        .limit(14)
        .all()
    )
    daily = list(reversed(daily))

    status_dist = (
        db.session.query(Transaction.status, func.count(Transaction.txn_id))
        .group_by(Transaction.status)
        .all()
    )

    return render_template(
        "admin/console.html",
        stats=stats,
        recent_users=recent_users,
        recent_txns=recent_txns,
        flagged=flagged,
        bank_dist=bank_dist,
        daily=daily,
        status_dist=status_dist,
    )


@admin_bp.route("/users", methods=["GET", "POST"])
@login_required
@admin_required
def users():
    if request.method == "POST":
        action = request.form.get("action")
        uid = request.form.get("user_id", type=int)

        if action == "create":
            full_name = (request.form.get("full_name") or "").strip()
            email = (request.form.get("email") or "").strip().lower()
            phone = (request.form.get("phone") or "").strip()
            password = request.form.get("password") or "password123"
            make_admin = request.form.get("is_admin") == "on"
            if not full_name or not email or not phone:
                flash("Name, email and phone are required.", "danger")
            elif User.query.filter(or_(User.email == email, User.phone == phone)).first():
                flash("Email or phone already registered.", "danger")
            else:
                u = User(
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    password_hash=generate_password_hash(password),
                    is_active=True,
                    is_admin=make_admin,
                )
                db.session.add(u)
                db.session.commit()
                flash(f"User {full_name} created.", "success")
            return redirect(url_for("admin.users"))

        if not uid:
            flash("Missing user id.", "danger")
            return redirect(url_for("admin.users"))

        user = db.session.get(User, uid)
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("admin.users"))

        if user.user_id == current_user.user_id:
            flash("You cannot modify your own admin account this way.", "warning")
            return redirect(url_for("admin.users"))

        if action == "block":
            user.is_active = False
            db.session.commit()
            flash(f"Blocked {user.full_name}.", "warning")
        elif action == "unblock":
            user.is_active = True
            db.session.commit()
            flash(f"Unblocked {user.full_name}.", "success")
        elif action == "delete":
            # Safe delete: remove dependents that cascade cleanly, then user
            try:
                # Beneficiaries owned by user
                Beneficiary.query.filter_by(user_id=user.user_id).delete()
                # UPI + bank accounts cascade from User relationships
                # Transactions reference UPI — null-safe approach: delete logs then leave txns
                # or remove user's UPIs only if no txn refs — simplest: block-only for txns
                # Hard delete user + cascade bank/upi/beneficiaries
                for upi in user.upi_ids.all():
                    # Detach from transactions by leaving FKs (SQLite may restrict)
                    pass
                db.session.delete(user)
                db.session.commit()
                flash(f"Deleted user {user.full_name}.", "success")
            except Exception as e:
                db.session.rollback()
                # Fallback: soft-delete (block) if hard delete fails due to FKs
                user.is_active = False
                db.session.commit()
                flash(
                    f"Could not hard-delete (transactions reference this user). Account blocked instead. ({e.__class__.__name__})",
                    "warning",
                )
        elif action == "make_admin":
            user.is_admin = True
            db.session.commit()
            flash(f"{user.full_name} is now an admin.", "success")
        elif action == "revoke_admin":
            user.is_admin = False
            db.session.commit()
            flash(f"Admin rights revoked for {user.full_name}.", "success")

        return redirect(url_for("admin.users"))

    q = request.args.get("q", "").strip()
    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(User.full_name.like(like), User.email.like(like), User.phone.like(like))
        )
    users_list = query.order_by(User.created_at.desc()).limit(150).all()
    return render_template("admin/users.html", users=users_list, q=q)


@admin_bp.route("/transactions", methods=["GET", "POST"])
@login_required
@admin_required
def transactions():
    if request.method == "POST":
        action = request.form.get("action")
        txn_id = request.form.get("txn_id", type=int)
        txn = db.session.get(Transaction, txn_id) if txn_id else None
        if not txn:
            flash("Transaction not found.", "danger")
            return redirect(url_for("admin.transactions"))

        if action == "flag":
            txn.is_flagged = True
            db.session.add(
                TransactionLog(
                    txn_id=txn.txn_id,
                    action="FLAGGED",
                    old_status=txn.status,
                    new_status=txn.status,
                )
            )
            db.session.commit()
            flash(f"Flagged {txn.reference_id}.", "warning")
        elif action == "unflag":
            txn.is_flagged = False
            db.session.add(
                TransactionLog(
                    txn_id=txn.txn_id,
                    action="UNFLAGGED",
                    old_status=txn.status,
                    new_status=txn.status,
                )
            )
            db.session.commit()
            flash(f"Unflagged {txn.reference_id}.", "success")
        elif action == "mark_failed":
            old = txn.status
            txn.status = "FAILED"
            txn.is_flagged = True
            db.session.add(
                TransactionLog(
                    txn_id=txn.txn_id,
                    action="ADMIN_FAIL",
                    old_status=old,
                    new_status="FAILED",
                )
            )
            db.session.commit()
            flash(f"Marked {txn.reference_id} as FAILED and flagged.", "warning")

        return redirect(url_for("admin.transactions", status=request.args.get("status", ""), q=request.args.get("q", "")))

    status = request.args.get("status", "")
    flagged_only = request.args.get("flagged") == "1"
    q = request.args.get("q", "").strip()
    query = Transaction.query
    if status in ("SUCCESS", "FAILED", "PENDING"):
        query = query.filter_by(status=status)
    if flagged_only:
        query = query.filter_by(is_flagged=True)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(Transaction.reference_id.like(like), Transaction.remarks.like(like))
        )
    txns = query.order_by(Transaction.timestamp.desc()).limit(100).all()
    return render_template(
        "admin/transactions.html",
        txns=txns,
        status=status,
        q=q,
        flagged_only=flagged_only,
    )


@admin_bp.route("/system")
@login_required
@admin_required
def system():
    logs = TransactionLog.query.order_by(TransactionLog.log_time.desc()).limit(80).all()
    return render_template("admin/system.html", logs=logs)
