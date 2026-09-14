from datetime import datetime
from app import db


class Transaction(db.Model):
    __tablename__ = "transactions"

    txn_id = db.Column(db.Integer, primary_key=True)
    sender_upi = db.Column(db.Integer, db.ForeignKey("upi_ids.upi_id_pk"), nullable=False, index=True)
    receiver_upi = db.Column(db.Integer, db.ForeignKey("upi_ids.upi_id_pk"), nullable=False, index=True)
    sender_acc = db.Column(db.Integer, db.ForeignKey("bank_accounts.account_id"), nullable=False)
    receiver_acc = db.Column(db.Integer, db.ForeignKey("bank_accounts.account_id"))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    txn_type = db.Column(db.String(10), default="PAY")
    status = db.Column(db.String(10), default="PENDING", index=True)
    reference_id = db.Column(db.String(36), nullable=False, unique=True, index=True)
    remarks = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    # Additive column — does not break existing schema/data
    is_flagged = db.Column(db.Boolean, default=False, nullable=False)

    sender_upi_rel = db.relationship("UPIId", foreign_keys=[sender_upi])
    receiver_upi_rel = db.relationship("UPIId", foreign_keys=[receiver_upi])
    sender_acc_rel = db.relationship("BankAccount", foreign_keys=[sender_acc])
    receiver_acc_rel = db.relationship("BankAccount", foreign_keys=[receiver_acc])
    logs = db.relationship("TransactionLog", backref="transaction", lazy="dynamic")

    def __repr__(self):
        return f"<Transaction {self.reference_id} {self.status}>"
