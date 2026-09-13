from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.models.transaction import Transaction
from app.models.upi import UPIId
from app.forms.transaction_forms import SendMoneyForm, HistoryFilterForm
from app.utils.transaction_helpers import perform_transfer
from app.utils.upi_helpers import is_valid_upi

transaction_bp = Blueprint("transaction", __name__, url_prefix="/pay")


@transaction_bp.route("/send", methods=["GET", "POST"])
@login_required
def send():
    form = SendMoneyForm()
    prefill = request.args.get("to")
    if prefill and not form.receiver_upi.data:
        form.receiver_upi.data = prefill
    if form.validate_on_submit():
        addr = form.receiver_upi.data.strip().lower()
        if not is_valid_upi(addr):
            flash("Enter a valid UPI ID such as name@bank.", "danger")
            return render_template("transaction/send.html", form=form, primary=current_user.primary_upi)
        result = perform_transfer(
            current_user,
            addr,
            form.amount.data,
            form.remarks.data,
            form.pin.data,
        )
        flash(result["message"] + (f"  Ref {result['txn_id']}" if result.get("txn_id") else ""),
              "success" if result["success"] else "danger")
        if result["success"]:
            return redirect(url_for("transaction.history"))
    return render_template("transaction/send.html", form=form, primary=current_user.primary_upi)


@transaction_bp.route("/history")
@login_required
def history():
    form = HistoryFilterForm(request.args, meta={"csrf": False})
    pks = [u.upi_id_pk for u in current_user.upi_ids.all()]
    q = Transaction.query
    if pks:
        q = q.filter(or_(Transaction.sender_upi.in_(pks), Transaction.receiver_upi.in_(pks)))
    else:
        q = q.filter(Transaction.txn_id == -1)

    if form.status.data:
        q = q.filter(Transaction.status == form.status.data)
    if form.direction.data == "sent" and pks:
        q = q.filter(Transaction.sender_upi.in_(pks))
    elif form.direction.data == "received" and pks:
        q = q.filter(Transaction.receiver_upi.in_(pks))
    if form.q.data:
        term = f"%{form.q.data.strip()}%"
        q = q.filter(
            or_(
                Transaction.reference_id.ilike(term),
                Transaction.remarks.ilike(term),
            )
        )

    page = request.args.get("page", 1, type=int)
    pagination = q.order_by(Transaction.timestamp.desc()).paginate(page=page, per_page=12, error_out=False)
    upi_map = {u.upi_id_pk: u.upi_address for u in UPIId.query.all()}
    return render_template(
        "transaction/history.html",
        form=form,
        pagination=pagination,
        txns=pagination.items,
        upi_map=upi_map,
        my_pks=set(pks),
    )
