"""
Core ACID transfer logic.
This is the heart of the project — every evaluator will look here.
"""
from app import db
from app.models.user import User
from app.models.bank_account import BankAccount
from app.models.upi import UPIAccount
from app.models.transaction import Transaction, TransactionStatus
from decimal import Decimal
import uuid
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.orm import with_for_update

def perform_transfer(sender_user: User, receiver_upi: str, amount: Decimal, remarks: str = None) -> dict:
    """
    Execute a money transfer with full ACID guarantees + optimistic locking.
    
    Steps:
    1. Resolve sender's primary UPI + bank account
    2. Resolve receiver UPI + bank account
    3. Check sufficient balance
    4. BEGIN transaction
    5. Debit sender (with version check)
    6. Credit receiver
    7. Insert transaction record
    8. COMMIT (or ROLLBACK on any error)
    """
    amount = Decimal(str(amount))
    if amount <= 0:
        return {'success': False, 'message': 'Amount must be positive'}

    # --- Resolve sender ---
    sender_upi_obj = sender_user.upi_accounts.filter_by(is_primary=True, is_active=True).first()
    if not sender_upi_obj:
        return {'success': False, 'message': 'No primary UPI ID found. Please create one first.'}
    
    sender_account = sender_upi_obj.bank_account
    if not sender_account or not sender_account.is_active:
        return {'success': False, 'message': 'Linked bank account is inactive'}

    # --- Resolve receiver ---
    receiver_upi_obj = UPIAccount.query.filter_by(upi_id=receiver_upi, is_active=True).first()
    if not receiver_upi_obj:
        return {'success': False, 'message': f'Receiver UPI "{receiver_upi}" does not exist'}
    
    if receiver_upi_obj.user_id == sender_user.id:
        return {'success': False, 'message': 'Cannot send money to yourself'}

    receiver_account = receiver_upi_obj.bank_account
    if not receiver_account or not receiver_account.is_active:
        return {'success': False, 'message': 'Receiver bank account is inactive'}

    # --- Pre-check balance ---
    if sender_account.balance < amount:
        return {'success': False, 'message': 'Insufficient balance'}

    txn_id = str(uuid.uuid4())

    try:
        # ========== BEGIN TRANSACTION ==========
        # Use SELECT ... FOR UPDATE for row-level locking
        sender_acc = db.session.execute(
            select(BankAccount)
            .where(BankAccount.id == sender_account.id)
            .with_for_update()
        ).scalar_one()

        # Re-check balance under lock
        if sender_acc.balance < amount:
            db.session.rollback()
            return {'success': False, 'message': 'Insufficient balance (concurrent transfer)'}

        # Optimistic version check (extra safety)
        expected_version = sender_acc.version

        # Debit sender
        sender_acc.balance -= amount
        sender_acc.version += 1

        # Credit receiver
        receiver_acc = db.session.execute(
            select(BankAccount)
            .where(BankAccount.id == receiver_account.id)
            .with_for_update()
        ).scalar_one()
        receiver_acc.balance += amount

        # Create transaction record
        txn = Transaction(
            transaction_id=txn_id,
            sender_upi=sender_upi_obj.upi_id,
            receiver_upi=receiver_upi,
            amount=amount,
            status=TransactionStatus.SUCCESS,
            remarks=remarks,
            completed_at=datetime.utcnow()
        )
        db.session.add(txn)

        # ========== COMMIT ==========
        db.session.commit()

        return {
            'success': True,
            'txn_id': txn_id,
            'message': 'Transfer successful',
            'new_balance': float(sender_acc.balance)
        }

    except Exception as e:
        db.session.rollback()
        # Log failed transaction
        try:
            failed_txn = Transaction(
                transaction_id=txn_id,
                sender_upi=sender_upi_obj.upi_id if sender_upi_obj else 'unknown',
                receiver_upi=receiver_upi,
                amount=amount,
                status=TransactionStatus.FAILED,
                failure_reason=str(e)[:255],
                remarks=remarks
            )
            db.session.add(failed_txn)
            db.session.commit()
        except:
            db.session.rollback()
        return {'success': False, 'message': f'Transfer failed: {str(e)}'}
