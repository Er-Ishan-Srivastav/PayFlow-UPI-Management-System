-- ============================================
-- SEED DATA (Demo Users for Testing)
-- Run AFTER schema.sql + triggers + procedures
-- Password / PIN hashes are placeholders.
-- Use app/seed.py (Flask) to load real hashes for login.
-- Documented demo credentials (via app/seed.py):
--   email: rahul@gmail.com   password: password123   PIN: 1234
-- ============================================

USE upi_db;

-- Clear any prior seed (safe for re-runs on fresh DB)
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE transaction_logs;
TRUNCATE TABLE transactions;
TRUNCATE TABLE beneficiaries;
TRUNCATE TABLE upi_ids;
TRUNCATE TABLE bank_accounts;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------
-- 5 Demo Users
-- password_hash will be replaced by app/seed.py with real Werkzeug hashes
-- Temporary known-good hash for "password123" (pbkdf2) – may need refresh
-- ------------------------------------------
INSERT INTO users (full_name, email, phone, password_hash) VALUES
('Rahul Sharma',   'rahul@gmail.com',   '9876543210', 'pbkdf2:sha256:600000$seedfix$placeholder'),
('Priya Patel',    'priya@gmail.com',   '9876543211', 'pbkdf2:sha256:600000$seedfix$placeholder'),
('Amit Kumar',     'amit@gmail.com',    '9876543212', 'pbkdf2:sha256:600000$seedfix$placeholder'),
('Sneha Reddy',    'sneha@gmail.com',   '9876543213', 'pbkdf2:sha256:600000$seedfix$placeholder'),
('Vikram Singh',   'vikram@gmail.com',  '9876543214', 'pbkdf2:sha256:600000$seedfix$placeholder');

-- ------------------------------------------
-- Bank Accounts – same account_no allowed across different banks
-- ------------------------------------------
INSERT INTO bank_accounts (user_id, bank_name, account_no, ifsc_code, balance, account_type, status) VALUES
(1, 'State Bank of India',  '123456789012', 'SBIN0001234', 10000.00, 'Savings', 'ACTIVE'),
(1, 'HDFC Bank',            '123456789012', 'HDFC0001234',  5000.00, 'Savings', 'ACTIVE'),  -- same number, different bank
(2, 'HDFC Bank',            '234567890123', 'HDFC0001234', 15000.00, 'Savings', 'ACTIVE'),
(3, 'ICICI Bank',           '345678901234', 'ICIC0001234',  8000.00, 'Current', 'ACTIVE'),
(4, 'Axis Bank',            '456789012345', 'UTIB0001234', 20000.00, 'Savings', 'ACTIVE'),
(5, 'Kotak Mahindra Bank',  '567890123456', 'KKBK0001234',  5000.00, 'Savings', 'ACTIVE');

-- ------------------------------------------
-- UPI IDs (PIN placeholder – set via app/seed.py)
-- ------------------------------------------
INSERT INTO upi_ids (user_id, account_id, upi_address, upi_pin_hash, is_primary) VALUES
(1, 1, 'rahul@sbi',    'pbkdf2:sha256:600000$seedpin$placeholder', TRUE),
(1, 2, 'rahul@hdfc',   'pbkdf2:sha256:600000$seedpin$placeholder', FALSE),
(2, 3, 'priya@hdfc',   'pbkdf2:sha256:600000$seedpin$placeholder', TRUE),
(3, 4, 'amit@icici',   'pbkdf2:sha256:600000$seedpin$placeholder', TRUE),
(4, 5, 'sneha@axis',   'pbkdf2:sha256:600000$seedpin$placeholder', TRUE),
(5, 6, 'vikram@kotak', 'pbkdf2:sha256:600000$seedpin$placeholder', TRUE);

-- ------------------------------------------
-- Beneficiaries
-- ------------------------------------------
INSERT INTO beneficiaries (user_id, ben_name, ben_upi) VALUES
(1, 'Priya',  'priya@hdfc'),
(1, 'Amit',   'amit@icici'),
(2, 'Rahul',  'rahul@sbi'),
(3, 'Sneha',  'sneha@axis'),
(4, 'Vikram', 'vikram@kotak');

-- ------------------------------------------
-- Sample Transactions (including a FAILED one for history)
-- ------------------------------------------
INSERT INTO transactions
    (sender_upi, receiver_upi, sender_acc, receiver_acc,
     amount, txn_type, status, reference_id, remarks)
VALUES
(1, 3, 1, 3, 500.00,  'PAY', 'SUCCESS', 'TXN-SEED-0001', 'Lunch money'),
(3, 4, 3, 4, 1200.00, 'PAY', 'SUCCESS', 'TXN-SEED-0002', 'Rent share'),
(1, 5, 1, 5, 300.00,  'PAY', 'SUCCESS', 'TXN-SEED-0003', 'Movie ticket'),
(4, 1, 4, 1, 750.00,  'PAY', 'SUCCESS', 'TXN-SEED-0004', 'Groceries'),
(6, 3, 6, 3, 200.00,  'PAY', 'FAILED',  'TXN-SEED-0005', 'Insufficient funds'),
(5, 1, 5, 1, 1500.00, 'PAY', 'SUCCESS', 'TXN-SEED-0006', 'Freelance payment');
