-- database.sql
-- This script creates the database and tables for the multi-user grocery tracker.

-- 1. Create the database (if it doesn't exist)
CREATE DATABASE IF NOT EXISTS grocery_db;

-- 2. Use the newly created database
USE grocery_db;

-- 3. Create the 'users' table
-- This table will store user login information.
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Create the 'groceries' table with a user_id foreign key
DROP TABLE IF EXISTS groceries;
CREATE TABLE groceries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    category ENUM('Dairy & Eggs', 'Bakery', 'Meat & Fish', 'Produce', 'Spices', 'Pulses', 'Grains', 'Condiments & Sauces', 'Baking', 'Breakfast & Cereal', 'Snacks', 'Frozen Foods', 'Beverages', 'Household & Cleaning', ' Personal Care', 'Other'),
    type VARCHAR(50),
    quantity DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    quantity_unit ENUM('Count', 'kg', 'g', 'liters', 'ml', 'Packet', 'Bottle', 'Other') NOT NULL,
    status ENUM('Running low', 'In-Stock', 'Excess', 'Not Needed Anymore') NOT NULL,
    is_essential BOOLEAN DEFAULT TRUE,
    purchase_date DATE,
    expiry_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

