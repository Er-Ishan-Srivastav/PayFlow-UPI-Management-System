from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.bank_account import BankAccount
from app.models.upi import UPIId
from app.forms.account_forms import LinkBankForm, CreateUPIForm
from app.utils.upi_helpers import make_upi_address
from app.models.transaction_log import TransactionLog

account_bp = Blueprint("account", __name__, url_prefix="/account")


@account_bp.route("/banks", methods=["GET", "POST"])
@login_required
def banks():
    form = LinkBankForm()
    if form.validate_on_submit():
        count = current_user.bank_accounts.count()
        if count >= 3:
            flash("Maximum of 3 bank accounts allowed.", "danger")
            return redirect(url_for("account.banks"))
        if BankAccount.query.filter_by(account_no=form.account_no.data).first():
            flash("That account number is already linked.", "danger")
            return redirect(url_for("account.banks"))
        acc = BankAccount(
            user_id=current_user.user_id,
            bank_name=form.bank_name.data,
            account_no=form.account_no.data,
            ifsc_code=form.ifsc_code.data.upper(),
            account_type=form.account_type.data,
            balance=form.opening_balance.data,
        )
        db.session.add(acc)
        db.session.commit()
        flash("Bank account linked.", "success")
        return redirect(url_for("account.banks"))
    accounts = current_user.bank_accounts.all()
    return render_template("account/banks.html", form=form, accounts=accounts)


@account_bp.route("/upi", methods=["GET", "POST"])
@login_required
def manage_upi():
    form = CreateUPIForm()
    accounts = current_user.bank_accounts.all()
    form.account_id.choices = [
        (a.account_id, f"{a.bank_name} · {a.masked_account()}") for a in accounts
    ]
    if not accounts:
        form.account_id.choices = [(0, "Link a bank first")]

    if form.validate_on_submit() and accounts:
        address = make_upi_address(form.handle.data, form.provider.data)
        if UPIId.query.filter_by(upi_address=address).first():
            flash("This UPI ID is already taken.", "danger")
            return redirect(url_for("account.manage_upi"))
        acc = db.session.get(BankAccount, form.account_id.data)
        if not acc or acc.user_id != current_user.user_id:
            flash("Invalid bank account.", "danger")
            return redirect(url_for("account.manage_upi"))
        make_primary = form.is_primary.data or current_user.upi_ids.count() == 0
        if make_primary:
            current_user.upi_ids.update({UPIId.is_primary: False})
        upi = UPIId(
            user_id=current_user.user_id,
            account_id=acc.account_id,
            upi_address=address,
            is_primary=make_primary,
        )
        upi.set_pin(form.pin.data)
        db.session.add(upi)
        db.session.commit()
        flash(f"UPI ID {address} created.", "success")
        return redirect(url_for("account.manage_upi"))

    return render_template(
        "account/manage_upi.html", form=form, upis=current_user.upi_ids.all(), accounts=accounts
    )


@account_bp.route("/upi/<int:pk>/primary", methods=["POST"])
@login_required
def set_primary(pk):
    upi = db.session.get(UPIId, pk)
    if not upi or upi.user_id != current_user.user_id:
        flash("Not found.", "danger")
        return redirect(url_for("account.manage_upi"))
    current_user.upi_ids.update({UPIId.is_primary: False})
    upi.is_primary = True
    db.session.commit()
    flash(f"{upi.upi_address} is now primary.", "success")
    return redirect(url_for("account.manage_upi"))
