# PayFlow UPI

Flask + SQLAlchemy UPI payment system aligned with the course schema (`upi_db`).

Demo: sign in as `rahul@gmail.com` / `1234`. UPI PIN is `1234`. Pay `priya@hdfc`.

## Stack

| Layer | Tech |
| --- | --- |
| Presentation | Jinja2, CSS, Chart.js |
| Application | Flask blueprints, WTForms, Flask-Login |
| Data | SQLAlchemy ORM + raw SQL (views, triggers, procedures) |
| Database | MySQL 8 in production, SQLite for local demo |

## Schema (6 tables)

`users` → `bank_accounts` → `upi_ids` → `transactions` + `beneficiaries` + `transaction_logs`

SQL lives in `database/`:

- `schema.sql` — 3NF, FKs, CHECK
- `indexes.sql`
- `views.sql` — profile, history, daily summary, bank report
- `triggers.sql` — audit log, negative-balance guard
- `stored_procedures.sql` — `sp_transfer_money`, register, link bank, dashboard
- `seed_data.sql` — 5 demo users
- `seed_data_large.sql` — 1000 users / 10k transactions

The running app executes the same transfer rules in Python (`app/utils/transaction_helpers.py`): begin, row lock, debit, credit, insert, commit or rollback.

## Run (SQLite demo)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open the printed URL. Demo accounts (password + PIN `1234`):

| Name | Email | UPI |
| --- | --- | --- |
| Rahul Sharma | rahul@gmail.com | rahul@sbi |
| Priya Patel | priya@gmail.com | priya@hdfc |
| Amit Kumar | amit@gmail.com | amit@icici |
| Sneha Reddy | sneha@gmail.com | sneha@axis |
| Vikram Singh | vikram@gmail.com | vikram@kotak |

## MySQL (submission)

```sql
SOURCE database/schema.sql;
SOURCE database/indexes.sql;
SOURCE database/views.sql;
SOURCE database/triggers.sql;
SOURCE database/stored_procedures.sql;
SOURCE database/seed_data.sql;
-- optional
SOURCE database/seed_data_large.sql;
```

Then set `DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/upi_db`.

## Tests

```bash
pytest tests/ -v
```

Covers login, successful transfer, bad PIN, insufficient balance (failed txn persisted).
