-- ============================================================
-- Views for analytics and reporting
-- ============================================================

USE payflow_upi;

-- User-level transaction summary
CREATE OR REPLACE VIEW v_user_transaction_summary AS
SELECT 
    u.id AS user_id,
    u.username,
    u.full_name,
    COUNT(CASE WHEN t.sender_upi IN (SELECT upi_id FROM upi_accounts WHERE user_id = u.id) THEN 1 END) AS total_sent_count,
    COALESCE(SUM(CASE WHEN t.sender_upi IN (SELECT upi_id FROM upi_accounts WHERE user_id = u.id) AND t.status = 'SUCCESS' THEN t.amount END), 0) AS total_sent_amount,
    COUNT(CASE WHEN t.receiver_upi IN (SELECT upi_id FROM upi_accounts WHERE user_id = u.id) THEN 1 END) AS total_received_count,
    COALESCE(SUM(CASE WHEN t.receiver_upi IN (SELECT upi_id FROM upi_accounts WHERE user_id = u.id) AND t.status = 'SUCCESS' THEN t.amount END), 0) AS total_received_amount
FROM users u
LEFT JOIN transactions t ON t.sender_upi IN (SELECT upi_id FROM upi_accounts WHERE user_id = u.id)
                       OR t.receiver_upi IN (SELECT upi_id FROM upi_accounts WHERE user_id = u.id)
GROUP BY u.id, u.username, u.full_name;

-- Daily volume report
CREATE OR REPLACE VIEW v_daily_report AS
SELECT 
    DATE(created_at) AS txn_date,
    COUNT(*) AS total_txns,
    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failed_count,
    COALESCE(SUM(CASE WHEN status = 'SUCCESS' THEN amount ELSE 0 END), 0) AS total_volume,
    ROUND(AVG(CASE WHEN status = 'SUCCESS' THEN amount END), 2) AS avg_txn_amount
FROM transactions
GROUP BY DATE(created_at)
ORDER BY txn_date DESC;

-- Bank-wise volume
CREATE OR REPLACE VIEW v_bank_wise_volume AS
SELECT 
    ba.bank_name,
    COUNT(t.id) AS txn_count,
    COALESCE(SUM(CASE WHEN t.status = 'SUCCESS' THEN t.amount END), 0) AS volume
FROM bank_accounts ba
JOIN upi_accounts ua ON ua.bank_account_id = ba.id
LEFT JOIN transactions t ON t.sender_upi = ua.upi_id OR t.receiver_upi = ua.upi_id
GROUP BY ba.bank_name
ORDER BY volume DESC;
