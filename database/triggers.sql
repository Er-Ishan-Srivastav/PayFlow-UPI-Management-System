-- ============================================
-- TRIGGERS
-- Run AFTER schema.sql
-- ============================================

USE upi_db;

-- ------------------------------------------
-- TRIGGER 1: Auto-log every new transaction (authoritative CREATED)
-- ------------------------------------------
DELIMITER //

CREATE TRIGGER trg_after_txn_insert
AFTER INSERT ON transactions
FOR EACH ROW
BEGIN
    INSERT INTO transaction_logs (txn_id, action, old_status, new_status)
    VALUES (NEW.txn_id, 'CREATED', NULL, NEW.status);
END //

DELIMITER ;


-- ------------------------------------------
-- TRIGGER 2: Log status changes
-- ------------------------------------------
DELIMITER //

CREATE TRIGGER trg_after_txn_update
AFTER UPDATE ON transactions
FOR EACH ROW
BEGIN
    IF OLD.status != NEW.status THEN
        INSERT INTO transaction_logs
            (txn_id, action, old_status, new_status)
        VALUES
            (NEW.txn_id, 'STATUS_CHANGE', OLD.status, NEW.status);
    END IF;
END //

DELIMITER ;


-- ------------------------------------------
-- TRIGGER 3: Prevent negative balance
-- ------------------------------------------
DELIMITER //

CREATE TRIGGER trg_before_balance_update
BEFORE UPDATE ON bank_accounts
FOR EACH ROW
BEGIN
    IF NEW.balance < 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Balance cannot go below zero';
    END IF;
END //

DELIMITER ;


-- ------------------------------------------
-- TRIGGER 4: Log when beneficiary is added
-- Uses NULL txn_id (nullable FK) – no placeholder 0
-- ------------------------------------------
DELIMITER //

CREATE TRIGGER trg_after_beneficiary_add
AFTER INSERT ON beneficiaries
FOR EACH ROW
BEGIN
    INSERT INTO transaction_logs (txn_id, action, old_status, new_status)
    VALUES (NULL, 'BENEFICIARY_ADDED', NULL, NEW.ben_upi);
END //

DELIMITER ;
