<div align="center">

<!-- HERO BANNER -->
<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:0f172a,50:1e3a8a,100:0ea5e9&height=220&section=header&text=PayFlow%20UPI&fontSize=70&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=A%20Simulated%20UPI%20Transaction%20Engine%20Built%20on%20Flask%20%26%20MySQL&descAlignY=60&descSize=16&descColor=93c5fd"/>

<p>
<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white"/>
<img src="https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white"/>
<img src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white"/>
</p>

<p>
<img src="https://img.shields.io/badge/CDAC%20Kharghar-2026-DC2626?style=for-the-badge"/>
<img src="https://img.shields.io/badge/PGCP%20--%20BDA-Minor%20Project-1D4ED8?style=for-the-badge"/>
<img src="https://img.shields.io/badge/ACID-Compliant-22C55E?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Team-7%20Builders-F59E0B?style=for-the-badge"/>
</p>

<br/>

> **"Every rupee that moves through this app is fake. Every guarantee that it moves correctly is real."**

A weekend build that turns lecture-slide DBMS concepts — ACID, normalization, triggers, concurrency — into something you can actually click a button and watch happen.

<br/>

</div>

---

## 🧠 What is PayFlow UPI, actually?

PayFlow is a **simulated** UPI-style payment platform — dummy users, dummy bank accounts, dummy money. There are no real payment rails and no real bank integration here, and that's on purpose: the point of this project is to *prove out relational database design and transaction handling*, not to compete with a fintech startup.

What it does do, for real:
- 🔐 Register & log in with hashed passwords and rate-limited login attempts
- 🏦 Link bank accounts and mint UPI IDs against them
- 💸 Send money with genuine `BEGIN / COMMIT / ROLLBACK` guarantees — a failed transfer never leaves one account debited without the other credited
- 🧾 Raise and track complaints against a transaction
- 📊 Pull transaction history, daily summaries, and bank-wise reports straight from MySQL views
- 🛡️ Get flagged automatically for suspicious activity — large amounts, rapid-fire sends, repeated failures

<details>
<summary><b>🤔 Why simulate instead of just building CRUD screens?</b></summary>
<br/>
Because a CRUD app proves you can call <code>INSERT</code> and <code>SELECT</code>. A payment simulator with real transaction boundaries, row-level locking, and optimistic concurrency control proves you understand <i>why</i> a database exists in the first place. That distinction is the whole grading rubric.
</details>

---

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    THREE-TIER ARCHITECTURE                          │
├───────────────────┬──────────────────────┬──────────────────────────┤
│   PRESENTATION    │     APPLICATION      │        DATABASE          │
│   LAYER           │     LAYER (Flask)    │        LAYER (MySQL)      │
├───────────────────┼──────────────────────┼──────────────────────────┤
│  HTML + Jinja2    │  Auth Blueprint      │  6 tables, 3NF            │
│  Bootstrap 5      │  Account Blueprint   │  8 indexes                │
│  Chart.js         │  Complaints Blueprint│  4 views                  │
│  Vanilla JS       │  Transaction Engine  │  4 triggers               │
│                   │  Fraud Rules         │  Stored procedures        │
│                   │  Analytics Queries   │  Optimistic row locking   │
│                   │                      │                          │
│                   │  Business logic:     │  SQLAlchemy ORM for       │
│                   │  • ACID transfers    │  app tables, raw SQL      │
│                   │  • Balance checks    │  for procs/triggers/views │
│                   │  • Concurrency ctrl  │                           │
└───────────────────┴──────────────────────┴──────────────────────────┘
```

### The transfer flow, step by step

```
1. Sender enters a receiver UPI ID + amount
2. Flask checks: does the receiver's UPI ID exist?
3. Flask checks: does the sender have sufficient balance?
4. sp_transfer_money() runs as a single transaction:

   BEGIN;
     UPDATE bank_accounts SET balance = balance - :amount
       WHERE account_id = :sender_acc;
     UPDATE bank_accounts SET balance = balance + :amount
       WHERE account_id = :receiver_acc;
     INSERT INTO transactions (sender_upi, receiver_upi, sender_acc,
       receiver_acc, amount, txn_type, status, reference_id, remarks)
       VALUES (...);
   COMMIT;   -- any failure anywhere in here → ROLLBACK instead

5. Fraud rules run against the completed transaction
   (high value / rapid-fire / repeated failures → fraud_flags)
6. Dashboard shows "Success" — or the exact failure reason
```

`bank_accounts` carries a `version` column, so concurrent transfers against the same account are protected by **optimistic locking** on top of MySQL InnoDB's own row-level locks — two simultaneous sends from the same account can't silently race each other into an inconsistent balance.

---

## 🚀 DBMS Concepts, Mapped to Actual Code

| Concept | Where it lives |
|---|---|
| **Normalization (3NF)** | `users`, `bank_accounts`, `upi_ids`, `beneficiaries`, `transactions`, `transaction_logs` — no repeated data anywhere |
| **ACID Transactions** | `sp_transfer_money` — wrapped in `START TRANSACTION` / `COMMIT`, rolls back on any failure |
| **Stored Procedures** | `sp_transfer_money`, `sp_register_user`, `sp_link_bank`, `sp_dashboard_summary` |
| **Triggers** | `trg_after_txn_insert`, `trg_after_txn_update`, `trg_before_balance_update`, `trg_after_beneficiary_add` |
| **Views** | `vw_user_profile`, `vw_transaction_history`, `vw_daily_summary`, `vw_bank_balance_report` |
| **Indexes** | On `upi_address`, `phone`, `email`, `sender_upi`, `receiver_upi`, `timestamp`, `status`, `account_no` |
| **Constraints** | FK on every reference, UNIQUE on email/phone/upi_address/account_no, `CHECK (balance >= 0)`, `CHECK (amount > 0)` |
| **Joins** | `vw_transaction_history` joins transactions → upi_ids → users, twice (sender + receiver) |
| **Aggregation** | `vw_daily_summary`, `vw_bank_balance_report` — `SUM`, `COUNT`, `AVG`, `GROUP BY` |
| **Concurrency Control** | `version` column on `bank_accounts` (optimistic locking) + InnoDB row-level locks |
| **Fraud Detection** | Pluggable rule engine (`high_value`, `rapid_fire`, `repeated_failures`) writing to `fraud_flags` |

---

## 🛠️ Technology Stack

<div align="center">

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | Flask 3 + Blueprints | Modular application layer |
| **ORM** | SQLAlchemy 2 + Flask-Migrate | Models, migrations, connection pooling |
| **Database** | MySQL 8.0 | Relational store, full ACID support |
| **Auth** | Flask-Login + Werkzeug hashing | Session management & password security |
| **Forms** | Flask-WTF + WTForms | CSRF-protected forms |
| **Rate Limiting** | Flask-Limiter | Brute-force protection on login |
| **Frontend** | Jinja2 + Bootstrap 5 + Chart.js | Responsive UI + analytics dashboards |
| **Testing** | pytest + pytest-flask | Unit & integration tests |
| **Deployment** | Gunicorn + python-dotenv | Production-style entrypoint |

</div>

> **Note:** the account/complaints routes call the MySQL stored procedures directly (raw SQL) rather than going through the ORM — a deliberate choice so the procedures stay visible as first-class DBMS objects rather than being reimplemented as ORM logic.

---

## 📁 Repository Structure

```
📦 upi-management-system
┣ 📂 app/
┃ ┣ 📜 __init__.py                 # App factory + blueprint registration
┃ ┣ 📜 config.py                   # Configuration (dev/prod)
┃ ┣ 📂 models/                     # SQLAlchemy models (3NF)
┃ ┃ ┣ 📜 user.py
┃ ┃ ┣ 📜 bank_account.py
┃ ┃ ┣ 📜 upi.py
┃ ┃ ┣ 📜 transaction.py
┃ ┃ ┗ 📜 beneficiary.py
┃ ┣ 📂 routes/                     # Blueprints
┃ ┃ ┣ 📜 auth.py                   # Login / Register / Logout
┃ ┃ ┣ 📜 dashboard.py
┃ ┃ ┣ 📜 account.py                # Bank linking & UPI management
┃ ┃ ┣ 📜 complaints.py             # Raise / track / resolve
┃ ┃ ┗ 📜 transaction.py            # Send money + history
┃ ┣ 📂 forms/
┃ ┣ 📂 templates/                  # Jinja2 + Bootstrap
┃ ┣ 📂 static/                     # CSS / JS / images
┃ ┣ 📂 fraud/                      # Fraud rule engine
┃ ┗ 📂 utils/                      # Helpers (UPI validation, DB connection)
┣ 📂 database/
┃ ┣ 📜 schema.sql                  # Full DDL (tables, constraints)
┃ ┣ 📜 indexes.sql                 # Performance indexes
┃ ┣ 📜 views.sql                   # Reporting views
┃ ┣ 📜 triggers.sql                # Audit + validation triggers
┃ ┣ 📜 stored_procedures.sql       # Transfer, register, link, dashboard
┃ ┗ 📜 seed_data.sql               # Demo users + sample transactions
┣ 📂 migrations/                   # Flask-Migrate
┣ 📂 tests/
┣ 📜 .env.example
┣ 📜 requirements.txt
┣ 📜 run.py
┗ 📜 README.md
```

---

## ⚙️ Getting Started

### Prerequisites
```bash
Python >= 3.10
MySQL 8.0+
Git
```

### 1. Clone & Set Up the Environment
```bash
git clone https://github.com/YOUR_USERNAME/upi-management-system.git
cd upi-management-system

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure the Database
```bash
cp .env.example .env
# Edit .env with your MySQL credentials
```

### 3. Initialize Schema, Objects, and Seed Data

Run these **in order** — later files depend on tables (and triggers) created by earlier ones:

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p upi_db < database/indexes.sql
mysql -u root -p upi_db < database/views.sql
mysql -u root -p upi_db < database/triggers.sql
mysql -u root -p upi_db < database/stored_procedures.sql
mysql -u root -p upi_db < database/seed_data.sql
```

> Triggers must exist **before** `seed_data.sql` runs, or the seed inserts won't generate audit log rows.

### 4. Run the Application
```bash
python run.py
# Visit http://127.0.0.1:5000
```

Demo login (from seed data): any of `rahul@gmail.com` / `priya@gmail.com` / `amit@gmail.com` — password `1234`.

### 5. Run Tests
```bash
pytest tests/ -v
```

---

## 👥 Team & Ownership

| Role | Member | Owns | Focus |
|---|---|---|---|
| **#1 Database Lead** | Harsh Jadhav | `models/`, `schema.sql`, seed data, migrations, ERD | Schema, indexes, views |
| **#2 Auth & Core Backend** | Komal Londhe | App factory, config, auth blueprint, security | Login, rate-limiting, CSRF |
| **#3 Transaction Engine** | Hansal | Transaction routes + services, ACID, locking | Send-money correctness |
| **#4 CRUD & Complaints** | Krunal | Account routes, UPI linking, complaints | Bank/UPI CRUD, complaint workflow |
| **#5 SQL Analytics** | Khushi Joshi | Analytics queries, window functions, CTEs | Dashboard data feeds |
| **#6 Dashboard & Frontend** | Harshavardhan | Templates, static assets, Chart.js | UI + visualizations |
| **#7 Integration & QA** | Ishan Srivastav | Git workflow, fraud engine, tests, README | Merge, CI, end-to-end demo |

---

## 🔭 Where This Could Go Next

Realistic next steps if this moves beyond the weekend build:

- [ ] Admin view over `fraud_flags` and `complaints` for triage
- [ ] QR-code UPI address sharing (cosmetic — no real payment rail)
- [ ] OTP-style second factor on login
- [ ] Dockerized one-command local setup

...and a couple of "why not" stretch ideas for later: a lightweight anomaly-scoring model instead of fixed fraud thresholds, and a read-only public dashboard of the aggregate (fully anonymized) daily-volume view.

---

## 📄 Citation

```bibtex
@project{payflow2026,
  title   = {PayFlow: A Simulated UPI Transaction System Demonstrating Core DBMS Concepts},
  author  = {Jadhav, Harsh and Londhe, Komal and Hansal and Krunal and Joshi, Khushi and Harshavardhan and Srivastav, Ishan},
  school  = {CDAC Kharghar, Navi Mumbai},
  year    = {2026},
  note    = {PGCP - BDA Minor Project}
}
```

---

<div align="center">

**Keywords:** `UPI` · `Flask` · `MySQL` · `ACID Transactions` · `SQLAlchemy` · `Stored Procedures` · `Triggers` · `Views` · `Optimistic Concurrency Control` · `Fraud Detection` · `3NF`

<br/>

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:0ea5e9,50:1e3a8a,100:0f172a&height=120&section=footer"/>

</div>
