-- 创建数据库
CREATE DATABASE IF NOT EXISTS bitcoin_op_return CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE bitcoin_op_return;

-- 创建OP_RETURN数据表
CREATE TABLE IF NOT EXISTS op_return_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    block_height INT NOT NULL,
    txid VARCHAR(64) NOT NULL,
    vout_index INT NOT NULL,
    raw_data TEXT,
    decoded_text TEXT,
    protocol_name VARCHAR(50),
    data_size INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_block_height (block_height),
    INDEX idx_txid (txid),
    INDEX idx_protocol (protocol_name),
    UNIQUE KEY unique_output (txid, vout_index)
);

-- 创建处理进度表
CREATE TABLE IF NOT EXISTS scan_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    last_scanned_block INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 插入初始进度记录
INSERT INTO scan_progress (last_scanned_block) VALUES (0) ON DUPLICATE KEY UPDATE id=id;