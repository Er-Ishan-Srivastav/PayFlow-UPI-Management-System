-- ============================================
-- STORED PROCEDURES
-- Run AFTER schema.sql
-- ============================================

USE upi_db;

-- ------------------------------------------
-- PROCEDURE 1: Transfer Money (Core Feature)
-- Matches Flask perform_transfer business rules:
-- amount > 0, self-transfer guard, status checks,
-- FOR UPDATE ordered locking, failed txn persistence,
-- unique UUID-style reference, proper rollback.
-- ------------------------------------------
DELIMITER //

CREATE PROCEDURE sp_transfer_money(
    IN p_sender_upi_addr   VARCHAR(50),
    IN p_receiver_upi_addr VARCHAR(50),
    IN p_amount            DECIMAL(10,2),
    IN p_remarks           VARCHAR(100),
    OUT p_result           VARCHAR(100)
)
BEGIN
    DECLARE v_sender_upi_pk   INT DEFAULT NULL;
    DECLARE v_receiver_upi_pk INT DEFAULT NULL;
    DECLARE v_sender_acc      INT DEFAULT NULL;
    DECLARE v_receiver_acc    INT DEFAULT NULL;
    DECLARE v_sender_user     INT DEFAULT NULL;
    DECLARE v_receiver_user   INT DEFAULT NULL;
    DECLARE v_sender_bal      DECIMAL(12,2) DEFAULT 0;
    DECLARE v_sender_status   VARCHAR(10) DEFAULT 'ACTIVE';
    DECLARE v_receiver_status VARCHAR(10) DEFAULT 'ACTIVE';
    DECLARE v_ref_id          VARCHAR(36);
    DECLARE v_first_id        INT;
    DECLARE v_second_id       INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_result = 'ERROR: Transfer rolled back';
    END;

    IF p_amount IS NULL OR p_amount <= 0 THEN
        SET p_result = 'ERROR: Amount must be greater than zero';
        -- leave without inserting (no valid accounts yet)
    ELSE
        -- Resolve sender
        SELECT u.upi_id_pk, u.account_id, u.user_id
        INTO v_sender_upi_pk, v_sender_acc, v_sender_user
        FROM upi_ids u WHERE u.upi_address = p_sender_upi_addr LIMIT 1;

        -- Resolve receiver
        SELECT u.upi_id_pk, u.account_id, u.user_id
        INTO v_receiver_upi_pk, v_receiver_acc, v_receiver_user
        FROM upi_ids u WHERE u.upi_address = p_receiver_upi_addr LIMIT 1;

        IF v_sender_upi_pk IS NULL OR v_receiver_upi_pk IS NULL THEN
            SET p_result = 'ERROR: Invalid UPI ID';
        ELSEIF v_sender_user = v_receiver_user THEN
            -- Self-transfer
            SET v_ref_id = UUID();
            INSERT INTO transactions
                (sender_upi, receiver_upi, sender_acc, receiver_acc,
                 amount, txn_type, status, reference_id, remarks)
            VALUES
                (v_sender_upi_pk, v_receiver_upi_pk, v_sender_acc, v_receiver_acc,
                 p_amount, 'PAY', 'FAILED', v_ref_id, COALESCE(p_remarks, 'Self-transfer'));
            SET p_result = 'ERROR: Self-transfer not allowed';
        ELSE
            SELECT balance, status INTO v_sender_bal, v_sender_status
            FROM bank_accounts WHERE account_id = v_sender_acc;

            SELECT status INTO v_receiver_status
            FROM bank_accounts WHERE account_id = v_receiver_acc;

            IF v_sender_status IN ('BLOCKED', 'LOCKED') THEN
                SET v_ref_id = UUID();
                INSERT INTO transactions
                    (sender_upi, receiver_upi, sender_acc, receiver_acc,
                     amount, txn_type, status, reference_id, remarks)
                VALUES
                    (v_sender_upi_pk, v_receiver_upi_pk, v_sender_acc, v_receiver_acc,
                     p_amount, 'PAY', 'FAILED', v_ref_id, 'Account blocked/locked');
                SET p_result = 'ERROR: Sender account blocked or locked';
            ELSEIF v_receiver_status = 'BLOCKED' THEN
                SET v_ref_id = UUID();
                INSERT INTO transactions
                    (sender_upi, receiver_upi, sender_acc, receiver_acc,
                     amount, txn_type, status, reference_id, remarks)
                VALUES
                    (v_sender_upi_pk, v_receiver_upi_pk, v_sender_acc, v_receiver_acc,
                     p_amount, 'PAY', 'FAILED', v_ref_id, 'Receiver blocked');
                SET p_result = 'ERROR: Receiver account blocked';
            ELSEIF v_sender_bal < p_amount THEN
                SET v_ref_id = UUID();
                INSERT INTO transactions
                    (sender_upi, receiver_upi, sender_acc, receiver_acc,
                     amount, txn_type, status, reference_id, remarks)
                VALUES
                    (v_sender_upi_pk, v_receiver_upi_pk, v_sender_acc, v_receiver_acc,
                     p_amount, 'PAY', 'FAILED', v_ref_id, COALESCE(p_remarks, 'Insufficient balance'));
                SET p_result = 'ERROR: Insufficient Balance';
            ELSE
                -- Ordered locking to prevent deadlocks
                IF v_sender_acc < v_receiver_acc THEN
                    SET v_first_id = v_sender_acc;
                    SET v_second_id = v_receiver_acc;
                ELSE
                    SET v_first_id = v_receiver_acc;
                    SET v_second_id = v_sender_acc;
                END IF;

                START TRANSACTION;

                SELECT balance INTO v_sender_bal
                FROM bank_accounts WHERE account_id = v_first_id FOR UPDATE;
                SELECT balance INTO v_sender_bal
                FROM bank_accounts WHERE account_id = v_second_id FOR UPDATE;

                -- Re-read sender balance under lock
                SELECT balance INTO v_sender_bal
                FROM bank_accounts WHERE account_id = v_sender_acc;

                IF v_sender_bal < p_amount THEN
                    ROLLBACK;
                    SET v_ref_id = UUID();
                    INSERT INTO transactions
                        (sender_upi, receiver_upi, sender_acc, receiver_acc,
                         amount, txn_type, status, reference_id, remarks)
                    VALUES
                        (v_sender_upi_pk, v_receiver_upi_pk, v_sender_acc, v_receiver_acc,
                         p_amount, 'PAY', 'FAILED', v_ref_id, 'Insufficient balance under lock');
                    SET p_result = 'ERROR: Insufficient Balance';
                ELSE
                    UPDATE bank_accounts
                    SET balance = balance - p_amount, version = version + 1
                    WHERE account_id = v_sender_acc;

                    UPDATE bank_accounts
                    SET balance = balance + p_amount, version = version + 1
                    WHERE account_id = v_receiver_acc;

                    SET v_ref_id = UUID();
                    INSERT INTO transactions
                        (sender_upi, receiver_upi, sender_acc, receiver_acc,
                         amount, txn_type, status, reference_id, remarks)
                    VALUES
                        (v_sender_upi_pk, v_receiver_upi_pk, v_sender_acc,
                         v_receiver_acc, p_amount, 'PAY', 'SUCCESS',
                         v_ref_id, p_remarks);

                    COMMIT;
                    SET p_result = CONCAT('SUCCESS:', v_ref_id);
                END IF;
            END IF;
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
-- Respects composite unique (bank_name, account_no)
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
    DECLARE dup_count INT;

    SELECT COUNT(*) INTO acc_count
    FROM bank_accounts WHERE user_id = p_user_id;

    IF acc_count >= 5 THEN
        SET p_result = 'ERROR: Max 5 accounts allowed';
    ELSE
        SELECT COUNT(*) INTO dup_count
        FROM bank_accounts
        WHERE bank_name = p_bank_name AND account_no = p_account_no;

        IF dup_count > 0 THEN
            SET p_result = 'ERROR: Account already exists for this bank';
        ELSE
            INSERT INTO bank_accounts
                (user_id, bank_name, account_no, ifsc_code, balance)
            VALUES
                (p_user_id, p_bank_name, p_account_no, p_ifsc, p_balance);
            SET p_result = 'SUCCESS';
        END IF;
    END IF;
END //

DELIMITER ;


-- ------------------------------------------
-- PROCEDURE 4: Get User Dashboard Summary
-- Fixed: upi_address lives on upi_ids, not users
-- ------------------------------------------
DELIMITER //

CREATE PROCEDURE sp_dashboard_summary(
    IN p_user_id INT
)
BEGIN
    SELECT
        u.full_name,
        (SELECT up.upi_address FROM upi_ids up
         WHERE up.user_id = p_user_id AND up.is_primary = TRUE
         LIMIT 1) AS primary_upi,
        COALESCE(SUM(b.balance), 0) AS total_balance,
        (SELECT COUNT(*) FROM transactions t
         JOIN upi_ids up ON t.sender_upi = up.upi_id_pk
         WHERE up.user_id = p_user_id AND t.status = 'SUCCESS'
        ) AS total_sent,
        (SELECT COUNT(*) FROM transactions t
         JOIN upi_ids up ON t.receiver_upi = up.upi_id_pk
         WHERE up.user_id = p_user_id AND t.status = 'SUCCESS'
        ) AS total_received
    FROM users u
    LEFT JOIN bank_accounts b ON u.user_id = b.user_id
    WHERE u.user_id = p_user_id
    GROUP BY u.user_id, u.full_name;
END //

DELIMITER ;
