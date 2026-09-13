from app import db
from datetime import datetime

class UPIAccount(db.Model):
    __tablename__ = 'upi_accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    bank_account_id = db.Column(db.Integer, db.ForeignKey('bank_accounts.id'), nullable=False)
    upi_id = db.Column(db.String(100), unique=True, nullable=False, index=True)  # e.g. name@payflow
    is_primary = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bank_account = db.relationship('BankAccount', backref='upi_ids')

    def __repr__(self):
        return f'<UPIAccount {self.upi_id}>'
