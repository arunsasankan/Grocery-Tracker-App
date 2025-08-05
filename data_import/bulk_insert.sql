-- Bulk INSERT statements for the 'groceries' table
-- Generated from the provided CSV file.
USE grocery_db;

INSERT INTO groceries (name, type, category, status, quantity, quantity_unit, purchase_date, is_essential, expiry_date, notes, user_id) VALUES
('Putt Powder', 'Non-Perishable', 'Breakfast & Cereal', 'Excess', 2.00, 'kg', '2025-08-05', TRUE, NULL, NULL, 1),
('Appam/Idiyappam Powder', 'Non-Perishable', 'Breakfast & Cereal', 'In-Stock', 1.00, 'Packet', '2025-08-05', TRUE, NULL, NULL, 1),
('Museli/Cereal', 'Non-Perishable', 'Breakfast & Cereal', 'Running low', 100.00, 'g', '2025-08-05', TRUE, NULL, NULL, 1),
('Idly/Dosa Chutney Powder', 'Non-Perishable', 'Breakfast & Cereal', 'In-Stock', 1.00, 'Packet', '2025-08-05', TRUE, NULL, NULL, 1),
('Idly/Dosa/Appam Batter', 'Perishable', 'Breakfast & Cereal', 'In-Stock', 1.00, 'Packet', '2025-08-05', TRUE, NULL, NULL, 1),
('Sugar', 'Non-Perishable', 'Condiments & Sauces', 'Running low', 150.00, 'g', '2025-08-05', TRUE, NULL, NULL, 1),
('Tea Powder', 'Non-Perishable', 'Condiments & Sauces', 'Running low', 50.00, 'g', '2025-08-05', TRUE, NULL, NULL, 1),
('Coffee Powder', 'Non-Perishable', 'Condiments & Sauces', 'In-Stock', 150.00, 'g', '2025-08-05', TRUE, NULL, NULL, 1),
('Tamarind(Regular)', 'Non-Perishable', 'Condiments & Sauces', 'Running low', 50.00, 'g', '2025-08-05', TRUE, NULL, NULL, 1),
('Malabar Tamarind(Kudampuli)', 'Non-Perishable', 'Condiments & Sauces', 'Running low', 0.00, 'g', '2025-08-05', TRUE, NULL, NULL, 1),
('Coconut Oil', 'Non-Perishable', 'Condiments & Sauces', 'Running low', 0.00, 'liters', '2025-08-05', FALSE, NULL, NULL, 1),
('Sunflower Oil', 'Non-Perishable', 'Condiments & Sauces', 'In-Stock', 850.00, 'ml', '2025-08-05', TRUE, NULL, NULL, 1),
('Noodles', 'Non-Perishable', 'Condiments & Sauces', 'Excess', 20.00, 'Packet', '2025-08-05', TRUE, NULL, NULL, 1),
('Pasta', 'Non-Perishable', 'Condiments & Sauces', 'In-Stock', 700.00, 'g', '2025-08-05', TRUE, NULL, NULL, 1),
('Jaggery', 'Non-Perishable', 'Condiments & Sauces', 'In-Stock', 500.00, 'g', '2025-08-05', TRUE, NULL, NULL, 1),
('Soya Chunks', 'Non-Perishable', 'Condiments & Sauces', 'Excess', 400.00, 'g', '2025-08-05', TRUE, NULL, NULL, 1),
('Tomato Rice Powder', 'Non-Perishable', 'Condiments & Sauces', 'In-Stock', 1.00, 'Packet', '2025-08-05', TRUE, NULL, NULL, 1),
('Lemon Rice Powder', 'Non-Perishable', 'Condiments & Sauces', 'In-Stock', 1.00, 'Packet', '2025-08-05', TRUE, NULL, NULL, 1),
('Puliyogare Powder', 'Non-Perishable', 'Condiments & Sauces', 'Running low', 0.00, 'Packet', '2025-08-05', FALSE, NULL, NULL, 1),
('Soy Sauce', 'Non-Perishable', 'Condiments & Sauces', 'In-Stock', 1.00, 'Bottle', '2025-08-05', TRUE, NULL, NULL, 1);


INSERT INTO groceries (name, type, category, status, quantity, quantity_unit, purchase_date, is_essential, expiry_date, notes, user_id) VALUES
('Red Chilli Sauce', 'Non-Perishable', 'Condiments & Sauces', 'In-Stock', 1.00, 'Bottle', '2025-08-05', TRUE, NULL, NULL, 1),
('Green Chilli Sauce', 'Non-Perishable', 'Condiments & Sauces', 'In-Stock', 1.00, 'Bottle', '2025-08-05', TRUE, NULL, NULL, 1),
('Payasam Mix', 'Non-Perishable', 'Condiments & Sauces', 'In-Stock', 200.00, 'g', '2025-08-05', FALSE, NULL, NULL, 1),
('Peanut Butter', 'Non-Perishable', 'Condiments & Sauces', 'In-Stock', 1.00, 'Bottle', '2025-08-05', TRUE, NULL, NULL, 1),
('Pickles', 'Non-Perishable', 'Condiments & Sauces', 'In-Stock', 1.00, 'Bottle', '2025-08-05', FALSE, NULL, NULL, 1),
('Pappadom', 'Non-Perishable', 'Condiments & Sauces', 'In-Stock', 3.00, 'Packet', '2025-08-05', FALSE, NULL, NULL, 1),
('Nutella', 'Non-Perishable', 'Condiments & Sauces', 'In-Stock', 150.00, 'g', '2025-08-05', FALSE, NULL, NULL, 1),
('Eggs', 'Perishable', 'Dairy & Eggs', 'In-Stock', 4.00, 'Count', '2025-08-05', TRUE, NULL, NULL, 1),
('Milk', 'Perishable', 'Dairy & Eggs', 'In-Stock', 1.00, 'Packet', '2025-08-05', TRUE, NULL, NULL, 1),
('Cheese Slices', 'Perishable', 'Dairy & Eggs', 'In-Stock', 1.00, 'Packet', '2025-08-05', FALSE, NULL, NULL, 1),
('Butter', 'Perishable', 'Dairy & Eggs', 'In-Stock', 100.00, 'g', '2025-08-05', FALSE, NULL, NULL, 1),
('Parmesan Cheese', 'Perishable', 'Dairy & Eggs', 'In-Stock', 50.00, 'g', '2025-08-05', FALSE, NULL, NULL, 1),
('Brown Rice', 'Non-Perishable', 'Grains', 'Excess', 2.50, 'kg', '2025-08-05', FALSE, NULL, NULL, 1),
('Sona Masoori Rice', 'Non-Perishable', 'Grains', 'Running low', 1.50, 'kg', '2025-08-05', TRUE, NULL, NULL, 1),
('Raw Rice', 'Non-Perishable', 'Grains', 'Running low', 0.00, 'kg', '2025-08-05', TRUE, NULL, NULL, 1),
('Aval(Rice Flakes)', 'Non-Perishable', 'Grains', 'In-Stock', 500.00, 'g', '2025-08-05', TRUE, NULL, NULL, 1),
('Detergent Liquid', 'Non-Perishable', 'Household & Cleaning', 'Running low', 100.00, 'ml', '2025-08-05', TRUE, NULL, NULL, 1),
('Dishwash Liquid', 'Non-Perishable', 'Household & Cleaning', 'Running low', 100.00, 'ml', '2025-08-05', TRUE, NULL, NULL, 1),
('Handwash ', 'Non-Perishable', 'Household & Cleaning', 'In-Stock', 500.00, 'ml', '2025-08-05', TRUE, NULL, NULL, 1),
('Air Wick (Refill)', 'Non-Perishable', 'Household & Cleaning', 'Running low', 0.00, 'Count', '2025-08-05', FALSE, NULL, NULL, 1);

