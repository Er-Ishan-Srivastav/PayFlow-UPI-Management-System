-- ============================================
-- SEED DATA (Demo Users for Testing)
-- Run AFTER schema.sql
-- ============================================

USE upi_db;

-- ------------------------------------------
-- 5 Demo Users
-- (password_hash = hashed version of "1234")
-- ------------------------------------------
INSERT INTO users (full_name, email, phone, password_hash) VALUES
('Rahul Sharma',   'rahul@gmail.com',   '9876543210', 'pbkdf2:sha256:600000$xyz$hash1'),
('Priya Patel',    'priya@gmail.com',   '9876543211', 'pbkdf2:sha256:600000$xyz$hash2'),
('Amit Kumar',     'amit@gmail.com',    '9876543212', 'pbkdf2:sha256:600000$xyz$hash3'),
('Sneha Reddy',    'sneha@gmail.com',   '9876543213', 'pbkdf2:sha256:600000$xyz$hash4'),
('Vikram Singh',   'vikram@gmail.com',  '9876543214', 'pbkdf2:sha256:600000$xyz$hash5');

-- ------------------------------------------
-- Bank Accounts (1 per user, ₹10,000 each)
-- ------------------------------------------
INSERT INTO bank_accounts (user_id, bank_name, account_no, ifsc_code, balance, account_type) VALUES
(1, 'State Bank of India',  '123456789012', 'SBIN0001234', 10000.00, 'Savings'),
(2, 'HDFC Bank',            '234567890123', 'HDFC0001234', 15000.00, 'Savings'),
(3, 'ICICI Bank',           '345678901234', 'ICIC0001234',  8000.00, 'Current'),
(4, 'Axis Bank',            '456789012345', 'UTIB0001234', 20000.00, 'Savings'),
(5, 'Kotak Mahindra Bank',  '567890123456', 'KKBK0001234',  5000.00, 'Savings');

-- ------------------------------------------
-- UPI IDs (1 per user, PIN hash = hashed "1234")
-- ------------------------------------------
INSERT INTO upi_ids (user_id, account_id, upi_address, upi_pin_hash, is_primary) VALUES
(1, 1, 'rahul@sbi',    'pbkdf2:sha256:600000$xyz$pin1', TRUE),
(2, 2, 'priya@hdfc',   'pbkdf2:sha256:600000$xyz$pin2', TRUE),
(3, 3, 'amit@icici',   'pbkdf2:sha256:600000$xyz$pin3', TRUE),
(4, 4, 'sneha@axis',   'pbkdf2:sha256:600000$xyz$pin4', TRUE),
(5, 5, 'vikram@kotak', 'pbkdf2:sha256:600000$xyz$pin5', TRUE);

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
-- Sample Transactions
-- ------------------------------------------
INSERT INTO transactions
    (sender_upi, receiver_upi, sender_acc, receiver_acc,
     amount, txn_type, status, reference_id, remarks)
VALUES
(1, 2, 1, 2, 500.00,  'PAY', 'SUCCESS', 'TXN20250101001', 'Lunch money'),
(2, 3, 2, 3, 1200.00, 'PAY', 'SUCCESS', 'TXN20250101002', 'Rent share'),
(1, 4, 1, 4, 300.00,  'PAY', 'SUCCESS', 'TXN20250102001', 'Movie ticket'),
(3, 1, 3, 1, 750.00,  'PAY', 'SUCCESS', 'TXN20250102002', 'Groceries'),
(5, 2, 5, 2, 200.00,  'PAY', 'FAILED',  'TXN20250103001', 'Insufficient funds'),
(4, 1, 4, 1, 1500.00, 'PAY', 'SUCCESS', 'TXN20250103002', 'Freelance payment');


USE upi_db;

-- 1. Allow txn_id to be NULL in transaction_logs
ALTER TABLE transaction_logs MODIFY txn_id INT NULL;

-- 2. Drop the faulty trigger
DROP TRIGGER IF EXISTS trg_after_beneficiary_add;

-- 3. Recreate the trigger using NULL instead of 0
DELIMITER //

CREATE TRIGGER trg_after_beneficiary_add
AFTER INSERT ON beneficiaries
FOR EACH ROW
BEGIN
    INSERT INTO transaction_logs (txn_id, action, old_status, new_status)
    VALUES (NULL, 'BENEFICIARY_ADDED', NULL, NEW.ben_upi);
END //

DELIMITER ;