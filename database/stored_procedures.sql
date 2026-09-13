-- ============================================
-- STORED PROCEDURES
-- Run AFTER schema.sql
-- ============================================

USE upi_db;

-- ------------------------------------------
-- PROCEDURE 1: Transfer Money (Core Feature)
-- ------------------------------------------
DELIMITER //

CREATE PROCEDURE sp_transfer_money(
    IN p_sender_upi_addr   VARCHAR(50),
    IN p_receiver_upi_addr VARCHAR(50),
    IN p_amount            DECIMAL(10,2),
    IN p_remarks           VARCHAR(100),
    OUT p_result           VARCHAR(50)
)
BEGIN
    DECLARE v_sender_upi_pk   INT;
    DECLARE v_receiver_upi_pk INT;
    DECLARE v_sender_acc      INT;
    DECLARE v_receiver_acc    INT;
    DECLARE v_sender_bal      DECIMAL(12,2);
    DECLARE v_ref_id          VARCHAR(20);

    -- Get sender UPI PK and account
    SELECT u.upi_id_pk, u.account_id
    INTO v_sender_upi_pk, v_sender_acc
    FROM upi_ids u WHERE u.upi_address = p_sender_upi_addr;

    -- Get receiver UPI PK and account
    SELECT u.upi_id_pk, u.account_id
    INTO v_receiver_upi_pk, v_receiver_acc
    FROM upi_ids u WHERE u.upi_address = p_receiver_upi_addr;

    -- Check if both exist
    IF v_sender_upi_pk IS NULL OR v_receiver_upi_pk IS NULL THEN
        SET p_result = 'ERROR: Invalid UPI ID';
    ELSE
        -- Check sender balance
        SELECT balance INTO v_sender_bal
        FROM bank_accounts WHERE account_id = v_sender_acc;

        IF v_sender_bal < p_amount THEN
            SET p_result = 'ERROR: Insufficient Balance';
        ELSE
            -- Generate reference ID
            SET v_ref_id = CONCAT('TXN', DATE_FORMAT(NOW(), '%Y%m%d%H%i%s'));

            -- START TRANSACTION (ACID)
            START TRANSACTION;

            -- Debit sender
            UPDATE bank_accounts
            SET balance = balance - p_amount
            WHERE account_id = v_sender_acc;

            -- Credit receiver
            UPDATE bank_accounts
            SET balance = balance + p_amount
            WHERE account_id = v_receiver_acc;

            -- Record transaction
            INSERT INTO transactions
                (sender_upi, receiver_upi, sender_acc, receiver_acc,
                 amount, txn_type, status, reference_id, remarks)
            VALUES
                (v_sender_upi_pk, v_receiver_upi_pk, v_sender_acc,
                 v_receiver_acc, p_amount, 'PAY', 'SUCCESS',
                 v_ref_id, p_remarks);

            COMMIT;
            SET p_result = 'SUCCESS';
        END IF;
    END IF;
END //

DELIMITER ;


-- ------------------------------------------
-- PROCEDURE 2: Register New User
-- ------------------------------------------
DELIMITER //

CREATE PROCEDURE sp_register_user(
    IN p_name     VARCHAR(50),
    IN p_email    VARCHAR(50),
    IN p_phone    VARCHAR(15),
    IN p_password VARCHAR(255),
    OUT p_user_id INT
)
BEGIN
    INSERT INTO users (full_name, email, phone, password_hash)
    VALUES (p_name, p_email, p_phone, p_password);

    SET p_user_id = LAST_INSERT_ID();
END //

DELIMITER ;


-- ------------------------------------------
-- PROCEDURE 3: Link Bank Account
-- ------------------------------------------
DELIMITER //

CREATE PROCEDURE sp_link_bank(
    IN p_user_id     INT,
    IN p_bank_name   VARCHAR(50),
    IN p_account_no  VARCHAR(20),
    IN p_ifsc        VARCHAR(15),
    IN p_balance     DECIMAL(12,2),
    OUT p_result     VARCHAR(50)
)
BEGIN
    DECLARE acc_count INT;

    SELECT COUNT(*) INTO acc_count
    FROM bank_accounts WHERE user_id = p_user_id;

    IF acc_count >= 3 THEN
        SET p_result = 'ERROR: Max 3 accounts allowed';
    ELSE
        INSERT INTO bank_accounts
            (user_id, bank_name, account_no, ifsc_code, balance)
        VALUES
            (p_user_id, p_bank_name, p_account_no, p_ifsc, p_balance);
        SET p_result = 'SUCCESS';
    END IF;
END //

DELIMITER ;


-- ------------------------------------------
-- PROCEDURE 4: Get User Dashboard Summary
-- ------------------------------------------
DELIMITER //

CREATE PROCEDURE sp_dashboard_summary(
    IN p_user_id INT
)
BEGIN
    -- Total balance across all accounts
    SELECT
        u.full_name,
        u.upi_address AS primary_upi,
        SUM(b.balance) AS total_balance,
        (SELECT COUNT(*) FROM transactions t
         JOIN upi_ids up ON t.sender_upi = up.upi_id_pk
         WHERE up.user_id = p_user_id AND t.status = 'SUCCESS'
        ) AS total_sent,
        (SELECT COUNT(*) FROM transactions t
         JOIN upi_ids up ON t.receiver_upi = up.upi_id_pk
         WHERE up.user_id = p_user_id AND t.status = 'SUCCESS'
        ) AS total_received
    FROM users u
    JOIN upi_ids up ON u.user_id = up.user_id AND up.is_primary = TRUE
    JOIN bank_accounts b ON u.user_id = b.user_id
    WHERE u.user_id = p_user_id
    GROUP BY u.user_id;
END //

DELIMITER ;