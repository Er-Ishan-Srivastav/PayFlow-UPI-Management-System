from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True, index=True)
    phone = db.Column(db.String(15), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    bank_accounts = db.relationship(
        "BankAccount", backref="owner", lazy="dynamic", cascade="all, delete-orphan"
    )
    upi_ids = db.relationship(
        "UPIId", backref="owner", lazy="dynamic", cascade="all, delete-orphan"
    )
    beneficiaries = db.relationship(
        "Beneficiary", backref="owner", lazy="dynamic", cascade="all, delete-orphan"
    )

    def get_id(self):
        return str(self.user_id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def primary_upi(self):
        return self.upi_ids.filter_by(is_primary=True).first()

    @property
    def total_balance(self):
        from sqlalchemy import func
        from app.models.bank_account import BankAccount

        val = (
            db.session.query(func.coalesce(func.sum(BankAccount.balance), 0))
            .filter(BankAccount.user_id == self.user_id)
            .scalar()
        )
        return val or 0

    def __repr__(self):
        return f"<User {self.email}>"
