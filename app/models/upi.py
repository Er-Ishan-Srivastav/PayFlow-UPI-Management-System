from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


MAX_PIN_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 30


class UPIId(db.Model):
    __tablename__ = "upi_ids"

    upi_id_pk = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True)
    account_id = db.Column(
        db.Integer, db.ForeignKey("bank_accounts.account_id"), nullable=False
    )
    upi_address = db.Column(db.String(50), nullable=False, unique=True, index=True)
    upi_pin_hash = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_pin(self, pin):
        self.upi_pin_hash = generate_password_hash(pin)

    def check_pin(self, pin):
        return check_password_hash(self.upi_pin_hash, pin)

    def record_pin_failure(self, account):
        """Increment attempt counter; lock account on 5th failure."""
        account.pin_attempts = (account.pin_attempts or 0) + 1
        if account.pin_attempts >= MAX_PIN_ATTEMPTS:
            account.status = "LOCKED"
            account.locked_until = datetime.utcnow() + timedelta(minutes=LOCK_DURATION_MINUTES)
            return True  # locked
        return False

    def reset_pin_attempts(self, account):
        account.pin_attempts = 0
        if account.status == "LOCKED" and (
            not account.locked_until or account.locked_until <= datetime.utcnow()
        ):
            account.status = "ACTIVE"
            account.locked_until = None

    def __repr__(self):
        return f"<UPIId {self.upi_address}>"
