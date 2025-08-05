import csv
import os
import datetime

def clean_category(category_str):
    """Cleans the category string to match the ENUM values in the database."""
    if "Condiments" in category_str:
        return "Condiments & Sauces"
    return category_str

def clean_status(status_str):
    """Cleans the status string to match ENUM values."""
    if status_str.lower() == 'running low':
        return 'Running low'
    return status_str

def format_value(value):
    """Formats values for SQL, handling NULLs and escaping strings."""
    if value is None or value == '':
        return 'NULL'
    # Escape single quotes by replacing them with two single quotes
    return f"'{str(value).replace("'", "''")}'"

def create_insert_statements(csv_file_path, batch_size=20):
    """
    Reads a CSV file and converts its rows into SQL INSERT statements.

    Args:
        csv_file_path (str): The path to the input CSV file.

    Returns:
        str: A string containing all the generated SQL INSERT statements.
    """
    if not os.path.exists(csv_file_path):
        return f"Error: File not found at '{csv_file_path}'"

    all_insert_statements = []
    all_insert_statements.append("-- Bulk INSERT statements for the 'groceries' table")
    all_insert_statements.append("-- Generated from the provided CSV file.")
    all_insert_statements.append("USE grocery_db;\n")

    try:
        with open(csv_file_path, mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            header = next(reader)  # Skip the header row

            base_insert = "INSERT INTO groceries (name, type, category, status, quantity, quantity_unit, purchase_date, is_essential, expiry_date, notes, user_id) VALUES\n"
            
            values_list = []
            for row in reader:
                # Map columns to variables for clarity
                name = row[0]
                item_type = row[1]
                category = clean_category(row[2])
                status = clean_status(row[3])
                try:
                    quantity = float(row[4]) if row[4] not in (None, '', 'NULL') else 0.0
                except ValueError:
                    quantity = 0.0
                quantity_unit = row[5]
                purchase_date = datetime.date.today().isoformat()
                is_essential = 'TRUE' if row[7].strip().lower() == 'true' else 'FALSE'
                expiry_date = row[8] if row[8] else None
                notes = row[9]
                user_id = 1

                # Format each value for the SQL statement
                values_str = f"({format_value(name)}, {format_value(item_type)}, {format_value(category)}, {format_value(status)}, {quantity:.2f}, {format_value(quantity_unit)}, {format_value(purchase_date)}, {is_essential}, {format_value(expiry_date)}, {format_value(notes)}, {user_id})"
                values_list.append(values_str)

            # Create insert statements in batches
            for i in range(0, len(values_list), batch_size):
                chunk = values_list[i:i + batch_size]
                
                base_insert = "INSERT INTO groceries (name, type, category, status, quantity, quantity_unit, purchase_date, is_essential, expiry_date, notes, user_id) VALUES\n"
                values_for_this_batch = ",\n".join(chunk)
                
                full_query = base_insert + values_for_this_batch + ";"
                all_insert_statements.append(full_query)
                all_insert_statements.append("\n") # Add a newline for readability
    except Exception as e:
        return f"An error occurred: {e}"

    return "\n".join(all_insert_statements)

# --- Main Execution ---
if __name__ == "__main__":
    # Name of the CSV file you want to convert
    input_csv_file = 'data_import/groceries.csv'
    
    # Generate the SQL script
    sql_script = create_insert_statements(input_csv_file)
    
    # Print the result to the console
    print(sql_script)

    # Optionally, save the output to a .sql file
    with open('data_import/bulk_insert.sql', 'w', encoding='utf-8') as outfile:
        outfile.write(sql_script)
    print(f"\nSQL script has been saved to 'bulk_insert.sql'")

