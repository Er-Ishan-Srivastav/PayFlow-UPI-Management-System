from app import db
from datetime import datetime

class BankAccount(db.Model):
    __tablename__ = 'bank_accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    bank_name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    ifsc_code = db.Column(db.String(11), nullable=False)
    account_type = db.Column(db.String(20), default='Savings')  # Savings / Current
    balance = db.Column(db.Numeric(15, 2), default=0.00, nullable=False)
    version = db.Column(db.Integer, default=1, nullable=False)  # Optimistic locking
    is_primary = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Constraint: balance >= 0 is enforced at DB level via CHECK

    def __repr__(self):
        return f'<BankAccount {self.account_number} | ₹{self.balance}>'
