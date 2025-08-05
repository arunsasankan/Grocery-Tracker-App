-- database.sql
-- This script creates the database and tables for the multi-user, household-based grocery tracker.

-- 1. Create the database (if it doesn't exist)
CREATE DATABASE IF NOT EXISTS grocery_db;

-- 2. Use the newly created database
USE grocery_db;

-- 3. Drop tables in reverse order of dependency to avoid foreign key errors
DROP TABLE IF EXISTS groceries;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS households;
DROP TABLE IF EXISTS roles;

-- 4. Create the 'roles' table
CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- 5. Create the 'households' table
CREATE TABLE households (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Create the 'users' table with foreign keys to roles and households
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    household_id INT, -- Can be NULL for admins or unassigned users
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE SET NULL
);

-- 7. Create the 'groceries' table with audit columns and a link to households
CREATE TABLE groceries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    household_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    category ENUM('Dairy & Eggs', 'Bakery', 'Meat & Fish', 'Produce', 'Spices', 'Pulses', 'Grains', 'Condiments & Sauces', 'Baking', 'Breakfast & Cereal', 'Snacks', 'Frozen Foods', 'Beverages', 'Household & Cleaning', 'Personal Care', 'Other'),
    type VARCHAR(50),
    quantity DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    quantity_unit ENUM('Count', 'kg', 'g', 'liters', 'ml', 'Packet', 'Bottle', 'Other') NOT NULL,
    status ENUM('Running low', 'In-Stock', 'Excess', 'Not Needed Anymore') NOT NULL,
    is_essential BOOLEAN DEFAULT TRUE,
    purchase_date DATE,
    expiry_date DATE,
    notes TEXT,
    created_by INT NOT NULL,
    modified_by INT,
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (modified_by) REFERENCES users(id)
);

-- 8. Insert the initial roles
INSERT INTO roles (name) VALUES ('admin'), ('user');

