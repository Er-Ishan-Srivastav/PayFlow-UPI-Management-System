from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.transaction import Transaction, TransactionStatus
from app.forms.transaction_forms import SendMoneyForm
from app.utils.transaction_helpers import perform_transfer
import uuid
from datetime import datetime

transaction_bp = Blueprint('transaction', __name__, url_prefix='/transaction')

@transaction_bp.route('/send', methods=['GET', 'POST'])
@login_required
def send():
    form = SendMoneyForm()
    if form.validate_on_submit():
        try:
            result = perform_transfer(
                sender_user=current_user,
                receiver_upi=form.receiver_upi.data,
                amount=form.amount.data,
                remarks=form.remarks.data
            )
            if result['success']:
                flash(f"₹{form.amount.data} sent successfully! Txn ID: {result['txn_id']}", 'success')
            else:
                flash(result['message'], 'danger')
        except Exception as e:
            flash(f"Transfer failed: {str(e)}", 'danger')
        return redirect(url_for('transaction.history'))
    return render_template('transaction/send.html', form=form)

@transaction_bp.route('/history')
@login_required
def history():
    # TODO: Filter + pagination + search
    page = request.args.get('page', 1, type=int)
    # Placeholder query
    transactions = []  
    return render_template('transaction/history.html', transactions=transactions)
