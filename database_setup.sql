-- ===============================
-- WiFi FTP Database Setup
-- ===============================

-- 1. Create Database
CREATE DATABASE IF NOT EXISTS ftp_app;

-- 2. Use Database
USE ftp_app;

-- ===============================
-- 3. Users Table
-- ===============================

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- 4. Sample Data (optional)
-- ===============================

INSERT INTO users (username, password)
VALUES ('admin', 'admin123');

-- ===============================
-- END
-- ===============================
