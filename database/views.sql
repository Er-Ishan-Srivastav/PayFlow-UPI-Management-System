-- ============================================
-- VIEWS
-- Run AFTER schema.sql
-- ============================================

USE upi_db;

-- ------------------------------------------
-- VIEW 1: User Full Profile
-- ------------------------------------------
CREATE VIEW vw_user_profile AS
SELECT
    u.user_id,
    u.full_name,
    u.phone,
    u.email,
    up.upi_address,
    b.bank_name,
    b.account_no,
    b.balance,
    b.ifsc_code
FROM users u
JOIN upi_ids up ON u.user_id = up.user_id AND up.is_primary = TRUE
JOIN bank_accounts b ON up.account_id = b.account_id;


-- ------------------------------------------
-- VIEW 2: Transaction History (Readable)
-- ------------------------------------------
CREATE VIEW vw_transaction_history AS
SELECT
    t.txn_id,
    t.reference_id,
    s_upi.upi_address  AS sender_upi,
    r_upi.upi_address  AS receiver_upi,
    s_user.full_name   AS sender_name,
    r_user.full_name   AS receiver_name,
    t.amount,
    t.txn_type,
    t.status,
    t.remarks,
    t.timestamp
FROM transactions t
JOIN upi_ids s_upi  ON t.sender_upi   = s_upi.upi_id_pk
JOIN upi_ids r_upi  ON t.receiver_upi = r_upi.upi_id_pk
JOIN users s_user   ON s_upi.user_id  = s_user.user_id
JOIN users r_user   ON r_upi.user_id  = r_user.user_id;


-- ------------------------------------------
-- VIEW 3: Daily Transaction Summary
-- ------------------------------------------
CREATE VIEW vw_daily_summary AS
SELECT
    DATE(t.timestamp) AS txn_date,
    COUNT(*)          AS total_transactions,
    SUM(CASE WHEN t.status = 'SUCCESS' THEN t.amount ELSE 0 END)
                      AS total_amount,
    SUM(CASE WHEN t.status = 'SUCCESS' THEN 1 ELSE 0 END)
                      AS successful_count,
    SUM(CASE WHEN t.status = 'FAILED' THEN 1 ELSE 0 END)
                      AS failed_count
FROM transactions t
GROUP BY DATE(t.timestamp);


-- ------------------------------------------
-- VIEW 4: Bank-wise Balance Report
-- ------------------------------------------
CREATE VIEW vw_bank_balance_report AS
SELECT
    b.bank_name,
    COUNT(b.account_id)  AS total_accounts,
    SUM(b.balance)       AS total_deposits,
    AVG(b.balance)       AS avg_balance
FROM bank_accounts b
GROUP BY b.bank_name;