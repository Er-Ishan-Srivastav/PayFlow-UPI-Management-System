from datetime import datetime
from app import db


class BankAccount(db.Model):
    __tablename__ = "bank_accounts"

    account_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True)
    bank_name = db.Column(db.String(50), nullable=False)
    account_no = db.Column(db.String(20), nullable=False, unique=True, index=True)
    ifsc_code = db.Column(db.String(15), nullable=False)
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    account_type = db.Column(db.String(20), default="Savings")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    upi_ids = db.relationship("UPIId", backref="bank_account", lazy="dynamic")

    def masked_account(self):
        n = self.account_no or ""
        if len(n) <= 4:
            return n
        return "•••• " + n[-4:]

    def __repr__(self):
        return f"<BankAccount {self.account_no}>"
