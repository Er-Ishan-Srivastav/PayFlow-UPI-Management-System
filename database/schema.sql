-- ============================================
-- UPI DATABASE MANAGEMENT SYSTEM
-- Schema Creation Script
-- Run this FIRST
-- ============================================

CREATE DATABASE IF NOT EXISTS upi_db;
USE upi_db;

-- ------------------------------------------
-- TABLE 1: USERS
-- ------------------------------------------
CREATE TABLE users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    full_name     VARCHAR(50)  NOT NULL,
    email         VARCHAR(50)  NOT NULL UNIQUE,
    phone         VARCHAR(15)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    is_active     BOOLEAN      DEFAULT TRUE
);

-- ------------------------------------------
-- TABLE 2: BANK_ACCOUNTS
-- Composite uniqueness: (bank_name, account_no)
-- Status machine: ACTIVE / BLOCKED / LOCKED
-- Optimistic locking via version column
-- ------------------------------------------
CREATE TABLE bank_accounts (
    account_id     INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT            NOT NULL,
    bank_name      VARCHAR(50)    NOT NULL,
    account_no     VARCHAR(20)    NOT NULL,
    ifsc_code      VARCHAR(15)    NOT NULL,
    balance        DECIMAL(12,2)  NOT NULL DEFAULT 0.00,
    account_type   VARCHAR(20)    DEFAULT 'Savings',
    status         ENUM('ACTIVE','BLOCKED','LOCKED') NOT NULL DEFAULT 'ACTIVE',
    pin_attempts   INT            NOT NULL DEFAULT 0,
    locked_until   DATETIME       NULL,
    cooldown_until DATETIME       NULL,
    version        INT            NOT NULL DEFAULT 1,
    created_at     DATETIME       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_balance CHECK (balance >= 0),
    CONSTRAINT uq_bank_account UNIQUE (bank_name, account_no),
    CONSTRAINT fk_bank_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE
);

-- ------------------------------------------
-- TABLE 3: UPI_IDS
-- ------------------------------------------
CREATE TABLE upi_ids (
    upi_id_pk    INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT            NOT NULL,
    account_id   INT            NOT NULL,
    upi_address  VARCHAR(50)    NOT NULL UNIQUE,
    upi_pin_hash VARCHAR(255)   NOT NULL,
    is_primary   BOOLEAN        DEFAULT FALSE,
    created_at   DATETIME       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_upi_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_upi_account FOREIGN KEY (account_id)
        REFERENCES bank_accounts(account_id) ON DELETE CASCADE
);

-- ------------------------------------------
-- TABLE 4: BENEFICIARIES
-- ------------------------------------------
CREATE TABLE beneficiaries (
    ben_id     INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT          NOT NULL,
    ben_name   VARCHAR(50)  NOT NULL,
    ben_upi    VARCHAR(50)  NOT NULL,
    added_at   DATETIME     DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ben_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT uq_user_ben UNIQUE (user_id, ben_upi)
);

-- ------------------------------------------
-- TABLE 5: TRANSACTIONS
-- receiver_acc FK added; failed txns persisted
-- ------------------------------------------
CREATE TABLE transactions (
    txn_id       INT AUTO_INCREMENT PRIMARY KEY,
    sender_upi   INT            NOT NULL,
    receiver_upi INT            NOT NULL,
    sender_acc   INT            NOT NULL,
    receiver_acc INT,
    amount       DECIMAL(10,2)  NOT NULL,
    txn_type     ENUM('PAY','REQUEST','REFUND') DEFAULT 'PAY',
    status       ENUM('SUCCESS','FAILED','PENDING') DEFAULT 'PENDING',
    reference_id VARCHAR(36)    NOT NULL UNIQUE,
    remarks      VARCHAR(100),
    timestamp    DATETIME       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_amount CHECK (amount > 0),
    CONSTRAINT fk_txn_sender FOREIGN KEY (sender_upi)
        REFERENCES upi_ids(upi_id_pk),
    CONSTRAINT fk_txn_receiver FOREIGN KEY (receiver_upi)
        REFERENCES upi_ids(upi_id_pk),
    CONSTRAINT fk_txn_sender_acc FOREIGN KEY (sender_acc)
        REFERENCES bank_accounts(account_id),
    CONSTRAINT fk_txn_receiver_acc FOREIGN KEY (receiver_acc)
        REFERENCES bank_accounts(account_id)
);

-- ------------------------------------------
-- TABLE 6: TRANSACTION_LOGS
-- txn_id nullable for non-transaction audit events
-- ------------------------------------------
CREATE TABLE transaction_logs (
    log_id     INT AUTO_INCREMENT PRIMARY KEY,
    txn_id     INT          NULL,
    action     VARCHAR(30)  NOT NULL,
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    log_time   DATETIME     DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_log_txn FOREIGN KEY (txn_id)
        REFERENCES transactions(txn_id) ON DELETE CASCADE
);
