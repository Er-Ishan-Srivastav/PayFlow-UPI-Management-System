from datetime import datetime
from app import db


class TransactionLog(db.Model):
    __tablename__ = "transaction_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    txn_id = db.Column(db.Integer, db.ForeignKey("transactions.txn_id"), nullable=True, index=True)
    action = db.Column(db.String(30), nullable=False)
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20))
    log_time = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TransactionLog {self.action}>"
