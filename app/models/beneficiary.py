from app import db
from datetime import datetime

class Beneficiary(db.Model):
    __tablename__ = 'beneficiaries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    upi_id = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'upi_id', name='uq_user_beneficiary'),
    )

    def __repr__(self):
        return f'<Beneficiary {self.name} ({self.upi_id})>'
