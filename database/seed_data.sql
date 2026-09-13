-- ============================================================
-- Seed Data (realistic sample for testing)
-- Password for all users: Password@123
-- ============================================================

USE payflow_upi;

-- Users (password_hash is werkzeug hash of 'Password@123')
INSERT INTO users (username, email, phone, password_hash, full_name, is_admin) VALUES
('harsh_j', 'harsh@example.com', '9876543210', 'pbkdf2:sha256:600000$dummy$hash', 'Harsh Jadhav', TRUE),
('komal_l', 'komal@example.com', '9876543211', 'pbkdf2:sha256:600000$dummy$hash', 'Komal Londhe', FALSE),
('hansal', 'hansal@example.com', '9876543212', 'pbkdf2:sha256:600000$dummy$hash', 'Hansal', FALSE),
('krunal', 'krunal@example.com', '9876543213', 'pbkdf2:sha256:600000$dummy$hash', 'Krunal', FALSE),
('khushi', 'khushi@example.com', '9876543214', 'pbkdf2:sha256:600000$dummy$hash', 'Khushi Joshi', FALSE),
('harshav', 'harshav@example.com', '9876543215', 'pbkdf2:sha256:600000$dummy$hash', 'Harshavardhan', FALSE),
('ishan', 'ishan@example.com', '9876543216', 'pbkdf2:sha256:600000$dummy$hash', 'Ishan Srivastav', FALSE);

-- Bank Accounts
INSERT INTO bank_accounts (user_id, bank_name, account_number, ifsc_code, balance, is_primary) VALUES
(1, 'HDFC Bank', '50100123456789', 'HDFC0001234', 150000.00, TRUE),
(2, 'ICICI Bank', '60100123456780', 'ICIC0001234', 85000.00, TRUE),
(3, 'SBI', '30100123456781', 'SBIN0001234', 42000.50, TRUE),
(4, 'Axis Bank', '40100123456782', 'UTIB0001234', 210000.00, TRUE),
(5, 'Kotak', '70100123456783', 'KKBK0001234', 67000.00, TRUE),
(6, 'Yes Bank', '80100123456784', 'YESB0001234', 33000.00, TRUE),
(7, 'PNB', '90100123456785', 'PUNB0001234', 95000.00, TRUE);

-- UPI Accounts
INSERT INTO upi_accounts (user_id, bank_account_id, upi_id, is_primary) VALUES
(1, 1, 'harsh@payflow', TRUE),
(2, 2, 'komal@payflow', TRUE),
(3, 3, 'hansal@payflow', TRUE),
(4, 4, 'krunal@payflow', TRUE),
(5, 5, 'khushi@payflow', TRUE),
(6, 6, 'harshav@payflow', TRUE),
(7, 7, 'ishan@payflow', TRUE);

-- Sample successful transactions
INSERT INTO transactions (transaction_id, sender_upi, receiver_upi, amount, status, remarks, completed_at) VALUES
(UUID(), 'harsh@payflow', 'komal@payflow', 2500.00, 'SUCCESS', 'Lunch money', NOW() - INTERVAL 2 DAY),
(UUID(), 'komal@payflow', 'hansal@payflow', 1200.00, 'SUCCESS', 'Movie tickets', NOW() - INTERVAL 1 DAY),
(UUID(), 'hansal@payflow', 'krunal@payflow', 5000.00, 'SUCCESS', 'Project contribution', NOW() - INTERVAL 12 HOUR),
(UUID(), 'krunal@payflow', 'khushi@payflow', 750.50, 'SUCCESS', 'Coffee', NOW() - INTERVAL 6 HOUR),
(UUID(), 'khushi@payflow', 'ishan@payflow', 3000.00, 'SUCCESS', 'Birthday gift', NOW() - INTERVAL 3 HOUR);

-- One failed transaction
INSERT INTO transactions (transaction_id, sender_upi, receiver_upi, amount, status, failure_reason, created_at) VALUES
(UUID(), 'harshav@payflow', 'unknown@payflow', 1000.00, 'FAILED', 'Receiver UPI does not exist', NOW() - INTERVAL 1 HOUR);
