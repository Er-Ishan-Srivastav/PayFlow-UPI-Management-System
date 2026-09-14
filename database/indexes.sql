-- ============================================
-- INDEXES (Performance Optimization)
-- Run AFTER schema.sql
-- ============================================

USE upi_db;

-- Fast UPI ID lookup (used in every transaction)
CREATE INDEX idx_upi_address ON upi_ids(upi_address);

-- Fast phone login
CREATE INDEX idx_user_phone ON users(phone);

-- Fast email login
CREATE INDEX idx_user_email ON users(email);

-- Fast transaction search by sender
CREATE INDEX idx_txn_sender ON transactions(sender_upi);

-- Fast transaction search by receiver
CREATE INDEX idx_txn_receiver ON transactions(receiver_upi);

-- Fast date-based filtering
CREATE INDEX idx_txn_timestamp ON transactions(timestamp);

-- Fast status filtering
CREATE INDEX idx_txn_status ON transactions(status);

-- Fast account number lookup
CREATE INDEX idx_account_no ON bank_accounts(account_no);

-- Account status / lock checks
CREATE INDEX idx_account_status ON bank_accounts(status);
CREATE INDEX idx_account_user ON bank_accounts(user_id);