<div align="center">

<!-- HERO BANNER -->
<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:0f172a,50:1e3a8a,100:0ea5e9&height=220&section=header&text=PayFlow%20UPI&fontSize=70&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Secure%20UPI%20Transaction%20Management%20System%20with%20Flask%20%26%20MySQL&descAlignY=60&descSize=16&descColor=93c5fd"/>

<!-- BADGES ROW 1 -->
<p>
<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white"/>
<img src="https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white"/>
<img src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white"/>
</p>

<!-- BADGES ROW 2 -->
<p>
<img src="https://img.shields.io/badge/Chandigarh%20University-2026-DC2626?style=for-the-badge&logo=graduation-cap&logoColor=white"/>
<img src="https://img.shields.io/badge/BE%20CSE%20(BDA)-8th%20Semester-1D4ED8?style=for-the-badge"/>
<img src="https://img.shields.io/badge/ACID-Compliant-22C55E?style=for-the-badge"/>
<img src="https://img.shields.io/badge/DBMS%20Concepts-Full%20Stack-F59E0B?style=for-the-badge"/>
</p>

<br/>

> **"Turning textbook DBMS concepts into a production-grade UPI payment experience — ACID, concurrency, fraud detection and all."**

<br/>

</div>

---

## 🧠 What is PayFlow UPI?

**PayFlow** is a full-stack **UPI-inspired digital payment platform** built with **Flask + MySQL** that demonstrates every core Database Management System concept in a real-world banking scenario.

Users can:
- 🔐 Register & login securely
- 🏦 Link bank accounts and create UPI IDs
- 💸 Send money instantly with full ACID guarantees
- 📊 View rich transaction history, daily reports & analytics
- 🛡️ Benefit from fraud detection rules and row-level locking

This is **not** a toy CRUD app. Every fund transfer runs inside a real database transaction with `BEGIN / COMMIT / ROLLBACK`, optimistic locking, triggers, stored procedures, views and proper 3NF design.

---

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MODERN THREE-TIER ARCHITECTURE                   │
├───────────────────┬──────────────────────┬──────────────────────────┤
│   PRESENTATION    │     APPLICATION      │        DATABASE          │
│   LAYER           │     LAYER (Flask)    │        LAYER             │
├───────────────────┼──────────────────────┼──────────────────────────┤
│                   │                      │                          │
│  HTML + Jinja2    │  Auth Blueprint      │  MySQL 8.0               │
│  Bootstrap 5      │  Account Blueprint   │  Tables + Indexes        │
│  Chart.js         │  Transaction Engine  │  Views                   │
│  Vanilla JS       │  Fraud Rules         │  Triggers                │
│                   │  Analytics Queries   │  Stored Procedures       │
│                   │                      │  Row-level Locking       │
│                   │  Business Logic:     │                          │
│                   │  • ACID Transfers    │  SQLAlchemy ORM +        │
│                   │  • Balance Checks    │  Raw SQL for analytics   │
│                   │  • Concurrency Ctrl  │                          │
└───────────────────┴──────────────────────┴──────────────────────────┘
```

**Fund Transfer Flow (ACID):**
```sql
BEGIN;
  UPDATE bank_accounts SET balance = balance - :amount, version = version + 1
    WHERE upi_id = :sender AND balance >= :amount AND version = :expected_version;
  UPDATE bank_accounts SET balance = balance + :amount
    WHERE upi_id = :receiver;
  INSERT INTO transactions (sender_upi, receiver_upi, amount, status, ...)
    VALUES (...);
COMMIT;   -- or ROLLBACK on any failure
```

---

## 🚀 Key DBMS Concepts Demonstrated

| Concept              | Implementation                                                                 |
|----------------------|---------------------------------------------------------------------------------|
| **Normalization**    | Full 3NF schema — no redundancy across users, accounts, UPI IDs, transactions  |
| **ACID Transactions**| Every money transfer wrapped in `BEGIN/COMMIT/ROLLBACK`                        |
| **Stored Procedures**| `sp_transfer_funds(sender, receiver, amount)`                                  |
| **Triggers**         | Auto-log to `fraud_flags` / audit table on INSERT/UPDATE of transactions   |
| **Views**            | `v_user_transaction_summary`, `v_daily_report`, `v_bank_wise_volume`           |
| **Indexes**          | On `upi_id`, `phone`, `account_number`, `created_at` for fast lookups          |
| **Constraints**      | FK, UNIQUE, CHECK (balance >= 0), NOT NULL                                    |
| **Joins**            | Transaction history with user + bank details                                   |
| **Aggregation**      | Total sent/received, monthly summaries, success/failure rates                  |
| **Concurrency**      | Optimistic locking via `version` column + row-level locks                      |
| **Fraud Detection**  | Rule engine: high-value, rapid-fire, repeated failures → `fraud_flags` table   |

---

## 🛠️ Technology Stack

<div align="center">

| Layer              | Technology                          | Purpose                                      |
|--------------------|-------------------------------------|----------------------------------------------|
| **Backend**        | Flask 3 + Blueprints                | Modular application layer                    |
| **ORM**            | SQLAlchemy 2 + Flask-Migrate        | Models, migrations, connection pooling       |
| **Database**       | MySQL 8.0                           | Relational store with full ACID support      |
| **Auth**           | Flask-Login + Werkzeug hashing      | Session management & password security       |
| **Forms**          | Flask-WTF + WTForms                 | CSRF-protected forms                         |
| **Rate Limiting**  | Flask-Limiter                       | Brute-force protection on login              |
| **Frontend**       | Jinja2 + Bootstrap 5 + Chart.js     | Responsive UI + analytics dashboards         |
| **Testing**        | pytest + pytest-flask               | Unit & integration tests                     |
| **Deployment**     | Gunicorn + python-dotenv            | Production-ready entrypoint                  |

</div>

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
┃ ┃ ┗ 📜 transaction.py            # Send money + history
┃ ┣ 📂 forms/
┃ ┣ 📂 templates/                  # Jinja2 + Bootstrap
┃ ┣ 📂 static/                     # CSS / JS / images
┃ ┗ 📂 utils/                      # Helpers (UPI validation, fraud rules)
┣ 📂 database/
┃ ┣ 📜 schema.sql                  # Full DDL (tables, indexes, constraints)
┃ ┣ 📜 stored_procedures.sql
┃ ┣ 📜 triggers.sql
┃ ┣ 📜 views.sql
┃ ┗ 📜 seed_data.sql               # 20-30 realistic users + transactions
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

### 1. Clone & Setup
```bash
git clone https://github.com/YOUR_USERNAME/upi-management-system.git
cd upi-management-system

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Database Configuration
```bash
# Create database
mysql -u root -p -e "CREATE DATABASE payflow_upi CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Copy environment file
cp .env.example .env
# Edit .env with your MySQL credentials
```

### 3. Initialize Schema & Seed
```bash
# Option A: Raw SQL (recommended for full DBMS features)
mysql -u root -p payflow_upi < database/schema.sql
mysql -u root -p payflow_upi < database/stored_procedures.sql
mysql -u root -p payflow_upi < database/triggers.sql
mysql -u root -p payflow_upi < database/views.sql
mysql -u root -p payflow_upi < database/seed_data.sql

# Option B: Flask-Migrate
flask db upgrade
python -c "from app import create_app; from app.models import db; ..."  # seed script
```

### 4. Run the Application
```bash
python run.py
# Visit http://127.0.0.1:5000
```

### 5. Run Tests
```bash
pytest tests/ -v
```

---

## 👥 Team & Ownership

| Role                        | Member                  | Ownership                                      | Days Focus                  |
|-----------------------------|-------------------------|------------------------------------------------|-----------------------------|
| **#1 Database Lead**        | Harsh Jadhav            | models/, schema.sql, seed, migrations, ERD     | Schema first, indexes, views|
| **#2 Auth & Core Backend**  | Komal Londhe            | app factory, config, auth blueprint, security  | Login, rate-limit, CSRF     |
| **#3 Transaction Engine**   | Hansal                  | transaction routes + services, ACID, locking   | Send-money correctness      |
| **#4 CRUD & Complaints**    | Krunal                  | account routes, UPI linking, complaints        | Bank/UPI CRUD               |
| **#5 SQL Analytics**        | Khushi Joshi            | Analytics queries, window functions, CTEs      | Dashboard data feeds        |
| **#6 Dashboard & Frontend** | Harshavardhan           | templates/, static/, Chart.js integration      | UI + visualizations         |
| **#7 Integration & QA**     | Ishan Srivastav         | Git workflow, fraud engine, tests, README      | Merge, CI, end-to-end demo  |

**Supervisor:** TBD  
**Department:** AIT – CSE (Big Data Analytics), Chandigarh University  
**Program:** BE Computer Science · 8th Semester · 2026

---

## 🔭 Future Roadmap

- [ ] Real UPI QR code generation & scanning
- [ ] Multi-factor authentication (OTP via SMS/Email)
- [ ] Advanced fraud ML model (isolation forest / autoencoder)
- [ ] Admin dashboard with live transaction monitoring
- [ ] Docker + docker-compose for one-command setup
- [ ] Kubernetes deployment manifest
- [ ] GraphQL API layer
- [ ] Mobile-responsive PWA version
- [ ] Integration with actual payment gateway sandbox

---

## 📄 Citation

If you use this work for academic purposes, please cite:

```bibtex
@project{payflow2026,
  title   = {PayFlow: A Full-Stack UPI Transaction Management System Demonstrating Advanced DBMS Concepts},
  author  = {Jadhav, Harsh and Londhe, Komal and Hansal and Krunal and Joshi, Khushi and Harshavardhan and Srivastav, Ishan},
  school  = {Chandigarh University, AIT -- CSE (BDA)},
  year    = {2026},
  note    = {BE Computer Science (Big Data Analytics), 8th Semester Project}
}
```

---

<div align="center">

**Keywords:** `UPI` · `Flask` · `MySQL` · `ACID Transactions` · `SQLAlchemy` · `Stored Procedures` · `Triggers` · `Views` · `Concurrency Control` · `Fraud Detection` · `3NF` · `Banking System`

<br/>

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:0ea5e9,50:1e3a8a,100:0f172a&height=120&section=footer"/>

</div>
