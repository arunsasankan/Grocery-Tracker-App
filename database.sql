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
    status ENUM('Running low', 'In-Stock', 'Excess', 'Buy More') NOT NULL,
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
    type ENUM('Perishable', 'Non-Perishable'),
    icon_class VARCHAR(50)
);

-- 9. Populate the master pantry items table
INSERT INTO pantry_items (name, type, category, icon_class) VALUES
-- Spices
('Turmeric Powder (Haldi)', 'Non-Perishable', 'Spices', 'fas fa-pepper-hot'),
('Red Chilli Powder (Lal Mirch)', 'Non-Perishable', 'Spices', 'fas fa-pepper-hot'),
('Kashmiri Chilli Powder', 'Non-Perishable', 'Spices', 'fas fa-pepper-hot'),
('Coriander Powder (Dhania)', 'Non-Perishable', 'Spices', 'fas fa-seedling'),
('Cumin Powder (Jeera)', 'Non-Perishable', 'Spices', 'fas fa-seedling'),
('Cumin Seeds (Jeera)', 'Non-Perishable', 'Spices', 'fas fa-seedling'),
('Mustard Seeds (Rai/Sarson)', 'Non-Perishable', 'Spices', 'fas fa-circle'),
('Garam Masala', 'Non-Perishable', 'Spices', 'fas fa-pepper-hot'),
('Asafoetida (Hing)', 'Non-Perishable', 'Spices', 'fas fa-mortar-pestle'),
('Salt (Namak)', 'Non-Perishable', 'Spices', 'fas fa-cube'),
('Black Peppercorns (Kali Mirch)', 'Non-Perishable', 'Spices', 'fas fa-circle'),
('Cardamom (Elaichi)', 'Non-Perishable', 'Spices', 'fas fa-seedling'),
('Cloves (Laung)', 'Non-Perishable', 'Spices', 'fas fa-star-of-life'),
('Cinnamon (Dalchini)', 'Non-Perishable', 'Spices', 'fas fa-bars'),
('Bay Leaves (Tej Patta)', 'Non-Perishable', 'Spices', 'fas fa-leaf'),
('Fenugreek Seeds (Methi Dana)', 'Non-Perishable', 'Spices', 'fas fa-seedling'),
('Dry Mango Powder (Amchur)', 'Non-Perishable', 'Spices', 'fas fa-mortar-pestle'),
('Sambar Powder', 'Non-Perishable', 'Spices', 'fas fa-mortar-pestle'),
('Rasam Powder', 'Non-Perishable', 'Spices', 'fas fa-mortar-pestle'),
-- Grains & Flours
('Basmati Rice', 'Non-Perishable', 'Grains', 'fas fa-seedling'),
('Sona Masoori Rice', 'Non-Perishable', 'Grains', 'fas fa-seedling'),
('Idli Rice', 'Non-Perishable', 'Grains', 'fas fa-seedling'),
('Whole Wheat Flour (Atta)', 'Non-Perishable', 'Grains', 'fas fa-bread-slice'),
('Gram Flour (Besan)', 'Non-Perishable', 'Grains', 'fas fa-bread-slice'),
('Rice Flour', 'Non-Perishable', 'Grains', 'fas fa-bread-slice'),
('Semolina (Sooji/Rava)', 'Non-Perishable', 'Grains', 'fas fa-seedling'),
('Flattened Rice (Poha)', 'Non-Perishable', 'Grains', 'fas fa-seedling'),
('All-Purpose Flour (Maida)', 'Non-Perishable', 'Grains', 'fas fa-bread-slice'),
('Ragi Flour', 'Non-Perishable', 'Grains', 'fas fa-bread-slice'),
-- Pulses & Lentils
('Split Pigeon Peas (Toor/Arhar Dal)', 'Non-Perishable', 'Pulses', 'fas fa-dot-circle'),
('Split Red Lentils (Masoor Dal)', 'Non-Perishable', 'Pulses', 'fas fa-dot-circle'),
('Split Mung Beans (Moong Dal)', 'Non-Perishable', 'Pulses', 'fas fa-dot-circle'),
('Split Black Gram (Urad Dal)', 'Non-Perishable', 'Pulses', 'fas fa-dot-circle'),
('Chickpeas (Kabuli Chana)', 'Non-Perishable', 'Pulses', 'fas fa-dot-circle'),
('Black Chickpeas (Kala Chana)', 'Non-Perishable', 'Pulses', 'fas fa-dot-circle'),
('Kidney Beans (Rajma)', 'Non-Perishable', 'Pulses', 'fas fa-dot-circle'),
('Green Peas (Dried)', 'Non-Perishable', 'Pulses', 'fas fa-dot-circle'),
-- Oils & Fats
('Ghee (Clarified Butter)', 'Non-Perishable', 'Baking', 'fas fa-tint'),
('Mustard Oil', 'Non-Perishable', 'Baking', 'fas fa-tint'),
('Sunflower/Vegetable Oil', 'Non-Perishable', 'Baking', 'fas fa-tint'),
('Coconut Oil', 'Non-Perishable', 'Baking', 'fas fa-tint'),
('Groundnut Oil', 'Non-Perishable', 'Baking', 'fas fa-tint'),
-- Fresh Produce
('Onions', 'Perishable', 'Produce', 'fas fa-carrot'),
('Tomatoes', 'Perishable', 'Produce', 'fas fa-carrot'),
('Potatoes', 'Perishable', 'Produce', 'fas fa-carrot'),
('Ginger', 'Perishable', 'Produce', 'fas fa-carrot'),
('Garlic', 'Perishable', 'Produce', 'fas fa-carrot'),
('Green Chillies', 'Perishable', 'Produce', 'fas fa-pepper-hot'),
('Coriander Leaves (Dhania)', 'Perishable', 'Produce', 'fas fa-leaf'),
('Mint Leaves (Pudina)', 'Perishable', 'Produce', 'fas fa-leaf'),
('Curry Leaves', 'Perishable', 'Produce', 'fas fa-leaf'),
('Lemons', 'Perishable', 'Produce', 'fas fa-lemon'),
('Carrot', 'Perishable', 'Produce', 'fas fa-carrot'),
('Cucumber', 'Perishable', 'Produce', 'fas fa-carrot'),
('Capsicum', 'Perishable', 'Produce', 'fas fa-pepper-hot'),
-- Dairy & Eggs
('Milk', 'Perishable', 'Dairy & Eggs', 'fas fa-mug-hot'),
('Yogurt (Dahi)', 'Perishable', 'Dairy & Eggs', 'fas fa-dot-circle'),
('Paneer (Indian Cottage Cheese)', 'Perishable', 'Dairy & Eggs', 'fas fa-cube'),
('Butter', 'Perishable', 'Dairy & Eggs', 'fas fa-cube'),
('Cheese', 'Perishable', 'Dairy & Eggs', 'fas fa-cheese'),
('Eggs', 'Perishable', 'Dairy & Eggs', 'fas fa-egg'),
-- Other Staples
('Sugar (Cheeni)', 'Non-Perishable', 'Condiments', 'fas fa-cube'),
('Jaggery (Gud)', 'Non-Perishable', 'Condiments', 'fas fa-cube'),
('Tamarind (Imli)', 'Non-Perishable', 'Condiments', 'fas fa-seedling'),
('Tea (Chai)', 'Non-Perishable', 'Beverages', 'fas fa-mug-hot'),
('Coffee', 'Non-Perishable', 'Beverages', 'fas fa-mug-hot'),
('Pickles (Achar)', 'Non-Perishable', 'Condiments', 'fas fa-bottle-droplet'),
('Papad', 'Non-Perishable', 'Snacks', 'fas fa-circle'),
('Biscuits', 'Non-Perishable', 'Snacks', 'fas fa-cookie-bite'),
-- Italian Cuisine
('Pasta (Spaghetti/Penne)', 'Non-Perishable', 'Grains', 'fas fa-utensils'),
('Olive Oil', 'Non-Perishable', 'Baking', 'fas fa-tint'),
('Parmesan Cheese', 'Perishable', 'Dairy & Eggs', 'fas fa-cheese'),
('Canned Tomatoes (Whole/Diced)', 'Non-Perishable', 'Produce', 'fas fa-carrot'),
('Dried Oregano', 'Non-Perishable', 'Spices', 'fas fa-leaf'),
('Fresh Basil', 'Perishable', 'Produce', 'fas fa-leaf'),
('Balsamic Vinegar', 'Non-Perishable', 'Condiments', 'fas fa-bottle-droplet'),
-- Mexican Cuisine
('Tortillas (Corn/Flour)', 'Perishable', 'Bakery', 'fas fa-circle'),
('Black Beans (Canned)', 'Non-Perishable', 'Pulses', 'fas fa-dot-circle'),
('Salsa', 'Non-Perishable', 'Condiments', 'fas fa-pepper-hot'),
('Avocado', 'Perishable', 'Produce', 'fas fa-carrot'),
('Cilantro', 'Perishable', 'Produce', 'fas fa-leaf'),
('Limes', 'Perishable', 'Produce', 'fas fa-lemon'),
('Chilli Powder', 'Non-Perishable', 'Spices', 'fas fa-pepper-hot'),
('Sour Cream', 'Perishable', 'Dairy & Eggs', 'fas fa-dot-circle'),
-- East Asian Cuisine
('Soy Sauce', 'Non-Perishable', 'Condiments', 'fas fa-bottle-droplet'),
('Sesame Oil', 'Non-Perishable', 'Baking', 'fas fa-tint'),
('Ramen Noodles', 'Non-Perishable', 'Grains', 'fas fa-utensils'),
('Tofu', 'Perishable', 'Other', 'fas fa-cube'),
('Kimchi', 'Perishable', 'Produce', 'fas fa-leaf'),
('Gochujang Paste', 'Non-Perishable', 'Condiments', 'fas fa-pepper-hot'),
('Mirin (Sweet Rice Wine)', 'Non-Perishable', 'Condiments', 'fas fa-wine-bottle'),
('Sushi Rice', 'Non-Perishable', 'Grains', 'fas fa-seedling'),
('Nori (Seaweed Sheets)', 'Non-Perishable', 'Snacks', 'fas fa-leaf'),
-- Household & Personal Care
('Dish Wash Soap', 'Non-Perishable', 'Household & Personal Care', 'fas fa-pump-soap'),
('Detergent Powder', 'Non-Perishable', 'Household & Personal Care', 'fas fa-box'),
('Toothpaste', 'Non-Perishable', 'Household & Personal Care', 'fas fa-tooth'),
('Toothbrush', 'Non-Perishable', 'Household & Personal Care', 'fas fa-tooth'),
('Bathing Soap', 'Non-Perishable', 'Household & Personal Care', 'fas fa-pump-soap'),
('Shampoo', 'Non-Perishable', 'Household & Personal Care', 'fas fa-pump-soap'),
('Hand Wash', 'Non-Perishable', 'Household & Personal Care', 'fas fa-pump-soap'),
('Toilet Paper', 'Non-Perishable', 'Household & Personal Care', 'fas fa-scroll'),
('Paper Towels', 'Non-Perishable', 'Household & Personal Care', 'fas fa-scroll'),
('Floor Cleaner', 'Non-Perishable', 'Household & Personal Care', 'fas fa-spray-can'),
('Toilet Cleaner', 'Non-Perishable', 'Household & Personal Care', 'fas fa-spray-can'),
('Garbage Bags', 'Non-Perishable', 'Household & Personal Care', 'fas fa-trash'),
('Aluminum Foil', 'Non-Perishable', 'Household & Personal Care', 'fas fa-box'),
('Body Lotion', 'Non-Perishable', 'Household & Personal Care', 'fas fa-pump-soap'),
('Face Wash', 'Non-Perishable', 'Household & Personal Care', 'fas fa-pump-soap'),
('Sanitary Napkins', 'Non-Perishable', 'Household & Personal Care', 'fas fa-box');
