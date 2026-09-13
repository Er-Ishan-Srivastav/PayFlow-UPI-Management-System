from datetime import datetime
from app import db


class Beneficiary(db.Model):
    __tablename__ = "beneficiaries"

    ben_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True)
    ben_name = db.Column(db.String(50), nullable=False)
    ben_upi = db.Column(db.String(50), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "ben_upi", name="uq_user_ben"),
    )

    def __repr__(self):
        return f"<Beneficiary {self.ben_name} {self.ben_upi}>"
