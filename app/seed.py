"""Seed demo users. Password and UPI PIN for all demo accounts: 1234"""
from datetime import datetime, timedelta
from decimal import Decimal
from random import Random
from werkzeug.security import generate_password_hash
from app import db
from app.models.user import User
from app.models.bank_account import BankAccount
from app.models.upi import UPIId
from app.models.beneficiary import Beneficiary
from app.models.transaction import Transaction
from app.models.transaction_log import TransactionLog

DEMO = [
    {
        "full_name": "Rahul Sharma",
        "email": "rahul@gmail.com",
        "phone": "9876543210",
        "bank": "State Bank of India",
        "account_no": "123456789012",
        "ifsc": "SBIN0001234",
        "balance": Decimal("25000.00"),
        "upi": "rahul@sbi",
        "type": "Savings",
    },
    {
        "full_name": "Priya Patel",
        "email": "priya@gmail.com",
        "phone": "9876543211",
        "bank": "HDFC Bank",
        "account_no": "234567890123",
        "ifsc": "HDFC0001234",
        "balance": Decimal("18000.00"),
        "upi": "priya@hdfc",
        "type": "Savings",
    },
    {
        "full_name": "Amit Kumar",
        "email": "amit@gmail.com",
        "phone": "9876543212",
        "bank": "ICICI Bank",
        "account_no": "345678901234",
        "ifsc": "ICIC0001234",
        "balance": Decimal("12000.00"),
        "upi": "amit@icici",
        "type": "Current",
    },
    {
        "full_name": "Sneha Reddy",
        "email": "sneha@gmail.com",
        "phone": "9876543213",
        "bank": "Axis Bank",
        "account_no": "456789012345",
        "ifsc": "UTIB0001234",
        "balance": Decimal("30000.00"),
        "upi": "sneha@axis",
        "type": "Savings",
    },
    {
        "full_name": "Vikram Singh",
        "email": "vikram@gmail.com",
        "phone": "9876543214",
        "bank": "Kotak Mahindra Bank",
        "account_no": "567890123456",
        "ifsc": "KKBK0001234",
        "balance": Decimal("9000.00"),
        "upi": "vikram@kotak",
        "type": "Savings",
    },
]

NOTES = [
    "Lunch", "Rent share", "Groceries", "Cab", "Movie", "Coffee",
    "Electricity", "Gift", "Freelance", "Books", "Pharmacy", "Recharge",
]


def seed(force=False):
    if User.query.first() and not force:
        return False

    pw = generate_password_hash("1234")
    pin = generate_password_hash("1234")

    users = []
    accounts = []
    upis = []
    for row in DEMO:
        u = User(
            full_name=row["full_name"],
            email=row["email"],
            phone=row["phone"],
            password_hash=pw,
            is_active=True,
        )
        db.session.add(u)
        db.session.flush()
        users.append(u)
        acc = BankAccount(
            user_id=u.user_id,
            bank_name=row["bank"],
            account_no=row["account_no"],
            ifsc_code=row["ifsc"],
            balance=row["balance"],
            account_type=row["type"],
        )
        db.session.add(acc)
        db.session.flush()
        accounts.append(acc)
        upi = UPIId(
            user_id=u.user_id,
            account_id=acc.account_id,
            upi_address=row["upi"],
            upi_pin_hash=pin,
            is_primary=True,
        )
        db.session.add(upi)
        db.session.flush()
        upis.append(upi)

    pairs = [(0, 1), (0, 2), (1, 0), (2, 3), (3, 4), (4, 1)]
    for a, b in pairs:
        db.session.add(
            Beneficiary(
                user_id=users[a].user_id,
                ben_name=users[b].full_name.split()[0],
                ben_upi=upis[b].upi_address,
            )
        )

    rng = Random(42)
    now = datetime.utcnow()
    n = 0
    for day in range(18, -1, -1):
        for _ in range(rng.randint(2, 5)):
            s, r = rng.sample(range(5), 2)
            amount = Decimal(str(rng.choice([50, 80, 120, 200, 350, 500, 750, 999, 1200, 1500])))
            ok = rng.random() > 0.08
            status = "SUCCESS" if ok else "FAILED"
            ref = f"TXN{now.strftime('%Y%m%d')}{n:04d}"
            ts = now - timedelta(days=day, hours=rng.randint(0, 20), minutes=rng.randint(0, 59))
            txn = Transaction(
                sender_upi=upis[s].upi_id_pk,
                receiver_upi=upis[r].upi_id_pk,
                sender_acc=accounts[s].account_id,
                receiver_acc=accounts[r].account_id,
                amount=amount,
                txn_type="PAY",
                status=status,
                reference_id=ref[:20],
                remarks=rng.choice(NOTES),
                timestamp=ts,
            )
            db.session.add(txn)
            db.session.flush()
            db.session.add(
                TransactionLog(
                    txn_id=txn.txn_id,
                    action="CREATED",
                    new_status=status,
                    log_time=ts,
                )
            )
            if ok:
                accounts[s].balance = Decimal(accounts[s].balance) - amount
                accounts[r].balance = Decimal(accounts[r].balance) + amount
            n += 1

    db.session.commit()
    return True
