from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.beneficiary import Beneficiary
from app.models.upi import UPIId
from app.models.transaction_log import TransactionLog
from app.forms.transaction_forms import BeneficiaryForm
from app.utils.upi_helpers import is_valid_upi

beneficiary_bp = Blueprint("beneficiary", __name__, url_prefix="/beneficiaries")


@beneficiary_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    form = BeneficiaryForm()
    if form.validate_on_submit():
        addr = form.ben_upi.data.strip().lower()
        if not is_valid_upi(addr):
            flash("Invalid UPI ID format.", "danger")
            return redirect(url_for("beneficiary.index"))
        if not UPIId.query.filter_by(upi_address=addr).first():
            flash("That UPI ID is not registered on PayFlow.", "danger")
            return redirect(url_for("beneficiary.index"))
        exists = Beneficiary.query.filter_by(user_id=current_user.user_id, ben_upi=addr).first()
        if exists:
            flash("Already saved.", "warning")
            return redirect(url_for("beneficiary.index"))
        ben = Beneficiary(
            user_id=current_user.user_id,
            ben_name=form.ben_name.data.strip(),
            ben_upi=addr,
        )
        db.session.add(ben)
        db.session.add(
            TransactionLog(txn_id=None, action="BENEFICIARY_ADDED", new_status=addr)
        )
        db.session.commit()
        flash("Beneficiary saved.", "success")
        return redirect(url_for("beneficiary.index"))
    items = current_user.beneficiaries.order_by(Beneficiary.added_at.desc()).all()
    return render_template("account/beneficiaries.html", form=form, items=items)


@beneficiary_bp.route("/<int:ben_id>/delete", methods=["POST"])
@login_required
def delete(ben_id):
    ben = db.session.get(Beneficiary, ben_id)
    if ben and ben.user_id == current_user.user_id:
        db.session.delete(ben)
        db.session.commit()
        flash("Removed.", "info")
    return redirect(url_for("beneficiary.index"))
