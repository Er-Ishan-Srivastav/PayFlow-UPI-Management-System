-- ============================================================
-- Stored Procedures
-- ============================================================

USE payflow_upi;

DELIMITER $$

-- Classic transfer procedure (can be called from Flask via CALL)
CREATE PROCEDURE sp_transfer_funds(
    IN p_sender_upi VARCHAR(100),
    IN p_receiver_upi VARCHAR(100),
    IN p_amount DECIMAL(15,2),
    IN p_remarks VARCHAR(255),
    OUT p_txn_id CHAR(36),
    OUT p_status VARCHAR(20),
    OUT p_message VARCHAR(255)
)
proc_body: BEGIN
    DECLARE v_sender_acc_id INT;
    DECLARE v_receiver_acc_id INT;
    DECLARE v_sender_balance DECIMAL(15,2);
    DECLARE v_sender_version INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status = 'FAILED';
        SET p_message = 'Database error occurred';
    END;

    SET p_txn_id = UUID();
    START TRANSACTION;

    -- Resolve sender account
    SELECT ba.id, ba.balance, ba.version
    INTO v_sender_acc_id, v_sender_balance, v_sender_version
    FROM upi_accounts ua
    JOIN bank_accounts ba ON ba.id = ua.bank_account_id
    WHERE ua.upi_id = p_sender_upi AND ua.is_active = TRUE AND ba.is_active = TRUE
    FOR UPDATE;

    IF v_sender_acc_id IS NULL THEN
        SET p_status = 'FAILED';
        SET p_message = 'Sender UPI not found or inactive';
        ROLLBACK;
        LEAVE proc_body;
    END IF;

    IF v_sender_balance < p_amount THEN
        SET p_status = 'FAILED';
        SET p_message = 'Insufficient balance';
        ROLLBACK;
        LEAVE proc_body;
    END IF;

    -- Resolve receiver
    SELECT ba.id INTO v_receiver_acc_id
    FROM upi_accounts ua
    JOIN bank_accounts ba ON ba.id = ua.bank_account_id
    WHERE ua.upi_id = p_receiver_upi AND ua.is_active = TRUE AND ba.is_active = TRUE
    FOR UPDATE;

    IF v_receiver_acc_id IS NULL THEN
        SET p_status = 'FAILED';
        SET p_message = 'Receiver UPI not found or inactive';
        ROLLBACK;
        LEAVE proc_body;
    END IF;

    -- Perform updates
    UPDATE bank_accounts
    SET balance = balance - p_amount, version = version + 1
    WHERE id = v_sender_acc_id AND version = v_sender_version;

    IF ROW_COUNT() = 0 THEN
        SET p_status = 'FAILED';
        SET p_message = 'Concurrent modification detected';
        ROLLBACK;
        LEAVE proc_body;
    END IF;

    UPDATE bank_accounts
    SET balance = balance + p_amount
    WHERE id = v_receiver_acc_id;

    INSERT INTO transactions (transaction_id, sender_upi, receiver_upi, amount, status, remarks, completed_at)
    VALUES (p_txn_id, p_sender_upi, p_receiver_upi, p_amount, 'SUCCESS', p_remarks, NOW());

    COMMIT;
    SET p_status = 'SUCCESS';
    SET p_message = 'Transfer completed successfully';
END$$

DELIMITER ;
