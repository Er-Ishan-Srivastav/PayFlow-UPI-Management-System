from datetime import datetime
from app import db


class BankAccount(db.Model):
    __tablename__ = "bank_accounts"
    __table_args__ = (
        db.UniqueConstraint("bank_name", "account_no", name="uq_bank_account"),
    )

    account_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True)
    bank_name = db.Column(db.String(50), nullable=False)
    account_no = db.Column(db.String(20), nullable=False, index=True)
    ifsc_code = db.Column(db.String(15), nullable=False)
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    account_type = db.Column(db.String(20), default="Savings")
    status = db.Column(db.String(10), nullable=False, default="ACTIVE")  # ACTIVE | BLOCKED | LOCKED
    pin_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    cooldown_until = db.Column(db.DateTime, nullable=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    upi_ids = db.relationship("UPIId", backref="bank_account", lazy="dynamic")

    def masked_account(self):
        n = self.account_no or ""
        if len(n) <= 4:
            return n
        return "•••• " + n[-4:]

    def is_operable(self):
        """Server-side gate: ACTIVE and not under lock/cooldown."""
        now = datetime.utcnow()
        if self.status == "BLOCKED":
            return False
        if self.status == "LOCKED":
            if self.locked_until and self.locked_until > now:
                return False
            # lock expired → allow transition back (caller may reset)
            return True
        if self.cooldown_until and self.cooldown_until > now:
            return False
        return self.status == "ACTIVE"

    def __repr__(self):
        return f"<BankAccount {self.bank_name}:{self.account_no}>"
