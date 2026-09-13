from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.bank_account import BankAccount
from app.models.upi import UPIAccount
from app.forms.account_forms import LinkBankForm, CreateUPIForm

account_bp = Blueprint('account', __name__, url_prefix='/account')

@account_bp.route('/link-bank', methods=['GET', 'POST'])
@login_required
def link_bank():
    form = LinkBankForm()
    if form.validate_on_submit():
        # TODO: Implement bank linking logic
        flash('Bank account linked successfully!', 'success')
        return redirect(url_for('account.balance'))
    return render_template('account/link_bank.html', form=form)

@account_bp.route('/manage-upi', methods=['GET', 'POST'])
@login_required
def manage_upi():
    form = CreateUPIForm()
    upi_accounts = current_user.upi_accounts.all()
    return render_template('account/manage_upi.html', form=form, upi_accounts=upi_accounts)

@account_bp.route('/balance')
@login_required
def balance():
    accounts = current_user.bank_accounts.filter_by(is_active=True).all()
    return render_template('account/balance.html', accounts=accounts)
