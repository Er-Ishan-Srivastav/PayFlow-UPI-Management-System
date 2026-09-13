-- ============================================================
-- Triggers
-- ============================================================

USE payflow_upi;

DELIMITER $$

-- Auto-log successful / failed transactions into audit_log
CREATE TRIGGER trg_transaction_after_insert
AFTER INSERT ON transactions
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, action, record_id, new_values, changed_at)
    VALUES (
        'transactions',
        'INSERT',
        NEW.transaction_id,
        JSON_OBJECT(
            'sender_upi', NEW.sender_upi,
            'receiver_upi', NEW.receiver_upi,
            'amount', NEW.amount,
            'status', NEW.status
        ),
        NOW()
    );
END$$

-- Simple high-value fraud flag example
CREATE TRIGGER trg_high_value_fraud
AFTER INSERT ON transactions
FOR EACH ROW
BEGIN
    IF NEW.amount >= 50000 AND NEW.status = 'SUCCESS' THEN
        INSERT INTO fraud_flags (transaction_id, rule_name, severity, details)
        VALUES (
            NEW.transaction_id,
            'high_value',
            'HIGH',
            JSON_OBJECT('amount', NEW.amount, 'threshold', 50000)
        );
    END IF;
END$$

DELIMITER ;
