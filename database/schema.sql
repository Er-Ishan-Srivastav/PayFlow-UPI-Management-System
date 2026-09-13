-- ============================================================
-- PayFlow UPI Management System - Full Schema (MySQL 8)
-- Demonstrates: 3NF, Constraints, Indexes, CHECK, FKs
-- ============================================================

CREATE DATABASE IF NOT EXISTS payflow_upi
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE payflow_upi;

-- -----------------------------------------------------------
-- 1. USERS
-- -----------------------------------------------------------
CREATE TABLE users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(80)  NOT NULL UNIQUE,
    email           VARCHAR(120) NOT NULL UNIQUE,
    phone           VARCHAR(15)  NOT NULL UNIQUE,
    password_hash   VARCHAR(256) NOT NULL,
    full_name       VARCHAR(150) NOT NULL,
    is_admin        BOOLEAN      NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_users_username (username),
    INDEX idx_users_email (email),
    INDEX idx_users_phone (phone)
) ENGINE=InnoDB;

-- -----------------------------------------------------------
-- 2. BANK_ACCOUNTS
-- -----------------------------------------------------------
CREATE TABLE bank_accounts (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT          NOT NULL,
    bank_name       VARCHAR(100) NOT NULL,
    account_number  VARCHAR(20)  NOT NULL UNIQUE,
    ifsc_code       VARCHAR(11)  NOT NULL,
    account_type    ENUM('Savings', 'Current') NOT NULL DEFAULT 'Savings',
    balance         DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    version         INT          NOT NULL DEFAULT 1,          -- Optimistic locking
    is_primary      BOOLEAN      NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_bank_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_balance_non_negative CHECK (balance >= 0),

    INDEX idx_bank_user (user_id),
    INDEX idx_bank_account_no (account_number)
) ENGINE=InnoDB;

-- -----------------------------------------------------------
-- 3. UPI_ACCOUNTS
-- -----------------------------------------------------------
CREATE TABLE upi_accounts (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT          NOT NULL,
    bank_account_id INT          NOT NULL,
    upi_id          VARCHAR(100) NOT NULL UNIQUE,
    is_primary      BOOLEAN      NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_upi_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_upi_bank FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id) ON DELETE CASCADE,

    INDEX idx_upi_id (upi_id),
    INDEX idx_upi_user (user_id)
) ENGINE=InnoDB;

-- -----------------------------------------------------------
-- 4. TRANSACTIONS
-- -----------------------------------------------------------
CREATE TABLE transactions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id  CHAR(36)     NOT NULL UNIQUE,           -- UUID
    sender_upi      VARCHAR(100) NOT NULL,
    receiver_upi    VARCHAR(100) NOT NULL,
    amount          DECIMAL(15,2) NOT NULL,
    status          ENUM('PENDING','SUCCESS','FAILED','REVERSED') NOT NULL DEFAULT 'PENDING',
    remarks         VARCHAR(255),
    failure_reason  VARCHAR(255),
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME,

    INDEX idx_txn_id (transaction_id),
    INDEX idx_txn_sender (sender_upi),
    INDEX idx_txn_receiver (receiver_upi),
    INDEX idx_txn_created (created_at),
    INDEX idx_txn_status (status)
) ENGINE=InnoDB;

-- -----------------------------------------------------------
-- 5. BENEFICIARIES
-- -----------------------------------------------------------
CREATE TABLE beneficiaries (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT          NOT NULL,
    name            VARCHAR(100) NOT NULL,
    upi_id          VARCHAR(100) NOT NULL,
    nickname        VARCHAR(50),
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ben_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uq_user_beneficiary UNIQUE (user_id, upi_id),

    INDEX idx_ben_user (user_id)
) ENGINE=InnoDB;

-- -----------------------------------------------------------
-- 6. FRAUD_FLAGS (for the fraud engine)
-- -----------------------------------------------------------
CREATE TABLE fraud_flags (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id  CHAR(36),
    user_id         INT,
    rule_name       VARCHAR(50)  NOT NULL,                  -- high_value, rapid_fire, etc.
    severity        ENUM('LOW','MEDIUM','HIGH','CRITICAL') NOT NULL DEFAULT 'MEDIUM',
    details         JSON,
    is_resolved     BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_fraud_txn (transaction_id),
    INDEX idx_fraud_user (user_id),
    INDEX idx_fraud_rule (rule_name)
) ENGINE=InnoDB;

-- -----------------------------------------------------------
-- 7. AUDIT_LOG (optional, filled by triggers)
-- -----------------------------------------------------------
CREATE TABLE audit_log (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    table_name      VARCHAR(50)  NOT NULL,
    action          ENUM('INSERT','UPDATE','DELETE') NOT NULL,
    record_id       VARCHAR(50),
    old_values      JSON,
    new_values      JSON,
    changed_by      INT,
    changed_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_audit_table (table_name),
    INDEX idx_audit_time (changed_at)
) ENGINE=InnoDB;
