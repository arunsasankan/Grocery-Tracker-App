-- database.sql
-- This script creates the database and tables for the multi-user, multi-household grocery tracker.

-- 1. Create the database (if it doesn't exist)
CREATE DATABASE IF NOT EXISTS grocery_db;

-- 2. Use the newly created database
USE grocery_db;

-- 3. Create the 'users' table with more details
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(150),
    email VARCHAR(150) NOT NULL UNIQUE,
    mobile_number VARCHAR(20),
    is_superadmin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Create the 'households' table
DROP TABLE IF EXISTS households;
CREATE TABLE households (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    address TEXT,
    location VARCHAR(255),
    admin_id INT NOT NULL,
    household_code VARCHAR(8) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 5. Create a mapping table for users and households
DROP TABLE IF EXISTS user_households;
CREATE TABLE user_households (
    user_id INT NOT NULL,
    household_id INT NOT NULL,
    status ENUM('pending', 'approved', 'denied') DEFAULT 'pending',
    PRIMARY KEY (user_id, household_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE CASCADE
);

-- 6. Update the 'groceries' table to be linked to a household instead of a user
DROP TABLE IF EXISTS groceries;
CREATE TABLE groceries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    household_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    category ENUM('Dairy & Eggs', 'Bakery', 'Meat & Fish', 'Produce', 'Spices', 'Pulses', 'Grains', 'Condiments', 'Baking', 'Breakfast & Cereal', 'Snacks', 'Frozen Foods', 'Beverages', 'Household & Personal Care', 'Other'),
    type VARCHAR(50),
    quantity DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    quantity_unit ENUM('Count', 'kg', 'g', 'liters', 'ml', 'Packet', 'Bottle', 'Other') NOT NULL,
    status ENUM('Running low', 'In-Stock', 'Excess', 'Not Needed Anymore') NOT NULL,
    is_essential BOOLEAN DEFAULT TRUE,
    purchase_date DATE,
    expiry_date DATE,
    notes TEXT,
    created_by INT,
    modified_by INT,
    modified_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (modified_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 7. Create an audit trail table
DROP TABLE IF EXISTS audit_log;
CREATE TABLE audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    household_id INT,
    action VARCHAR(255) NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE CASCADE
);

-- 8. Create the master pantry items table
DROP TABLE IF EXISTS pantry_items;
CREATE TABLE pantry_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category ENUM('Dairy & Eggs', 'Bakery', 'Meat & Fish', 'Produce', 'Spices', 'Pulses', 'Grains', 'Condiments', 'Baking', 'Breakfast & Cereal', 'Snacks', 'Frozen Foods', 'Beverages', 'Household & Personal Care', 'Other'),
    type ENUM('Perishable', 'Non-Perishable')
);

-- 9. Populate the master pantry items table
INSERT INTO pantry_items (name, type, category) VALUES
('Turmeric Powder (Haldi)', 'Non-Perishable', 'Spices'),
('Red Chilli Powder (Lal Mirch)', 'Non-Perishable', 'Spices'),
('Coriander Powder (Dhania)', 'Non-Perishable', 'Spices'),
('Cumin Seeds (Jeera)', 'Non-Perishable', 'Spices'),
('Mustard Seeds (Rai/Sarson)', 'Non-Perishable', 'Spices'),
('Garam Masala', 'Non-Perishable', 'Spices'),
('Asafoetida (Hing)', 'Non-Perishable', 'Spices'),
('Salt (Namak)', 'Non-Perishable', 'Spices'),
('Black Peppercorns (Kali Mirch)', 'Non-Perishable', 'Spices'),
('Cardamom (Elaichi)', 'Non-Perishable', 'Spices'),
('Cloves (Laung)', 'Non-Perishable', 'Spices'),
('Cinnamon (Dalchini)', 'Non-Perishable', 'Spices'),
('Bay Leaves (Tej Patta)', 'Non-Perishable', 'Spices'),
('Fenugreek Seeds (Methi Dana)', 'Non-Perishable', 'Spices'),
('Basmati Rice', 'Non-Perishable', 'Grains'),
('Sona Masoori Rice', 'Non-Perishable', 'Grains'),
('Whole Wheat Flour (Atta)', 'Non-Perishable', 'Grains'),
('Gram Flour (Besan)', 'Non-Perishable', 'Grains'),
('Semolina (Sooji/Rava)', 'Non-Perishable', 'Grains'),
('Flattened Rice (Poha)', 'Non-Perishable', 'Grains'),
('All-Purpose Flour (Maida)', 'Non-Perishable', 'Grains'),
('Split Pigeon Peas (Toor/Arhar Dal)', 'Non-Perishable', 'Pulses'),
('Split Red Lentils (Masoor Dal)', 'Non-Perishable', 'Pulses'),
('Split Mung Beans (Moong Dal)', 'Non-Perishable', 'Pulses'),
('Split Black Gram (Urad Dal)', 'Non-Perishable', 'Pulses'),
('Chickpeas (Kabuli Chana)', 'Non-Perishable', 'Pulses'),
('Kidney Beans (Rajma)', 'Non-Perishable', 'Pulses'),
('Ghee (Clarified Butter)', 'Non-Perishable', 'Baking'),
('Mustard Oil', 'Non-Perishable', 'Baking'),
('Sunflower/Vegetable Oil', 'Non-Perishable', 'Baking'),
('Coconut Oil', 'Non-Perishable', 'Baking'),
('Onions', 'Perishable', 'Produce'),
('Tomatoes', 'Perishable', 'Produce'),
('Potatoes', 'Perishable', 'Produce'),
('Ginger', 'Perishable', 'Produce'),
('Garlic', 'Perishable', 'Produce'),
('Green Chillies', 'Perishable', 'Produce'),
('Coriander Leaves (Dhania)', 'Perishable', 'Produce'),
('Lemons', 'Perishable', 'Produce'),
('Milk', 'Perishable', 'Dairy & Eggs'),
('Yogurt (Dahi)', 'Perishable', 'Dairy & Eggs'),
('Paneer (Indian Cottage Cheese)', 'Perishable', 'Dairy & Eggs'),
('Butter', 'Perishable', 'Dairy & Eggs'),
('Eggs', 'Perishable', 'Dairy & Eggs'),
('Sugar (Cheeni)', 'Non-Perishable', 'Condiments'),
('Jaggery (Gud)', 'Non-Perishable', 'Condiments'),
('Tea (Chai)', 'Non-Perishable', 'Beverages'),
('Coffee', 'Non-Perishable', 'Beverages'),
('Pickles (Achar)', 'Non-Perishable', 'Condiments'),
('Papad', 'Non-Perishable', 'Snacks');

