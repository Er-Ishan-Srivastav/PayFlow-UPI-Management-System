from app import db
from datetime import datetime
import enum

class TransactionStatus(enum.Enum):
    PENDING = 'PENDING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    REVERSED = 'REVERSED'

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(36), unique=True, nullable=False, index=True)  # UUID
    sender_upi = db.Column(db.String(100), nullable=False, index=True)
    receiver_upi = db.Column(db.String(100), nullable=False, index=True)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    status = db.Column(db.Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    remarks = db.Column(db.String(255))
    failure_reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    completed_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Transaction {self.transaction_id} | {self.amount} | {self.status.value}>'
