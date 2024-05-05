# database.py
import sqlite3
import os
import pandas as pd
import datetime
import sys

def process_data(excel_file):
    try:
        # Ensure the 'databases' directory exists, if not, create it
        if not os.path.exists('databases'):
            os.makedirs('databases')

        # Get the current date and time
        now = datetime.datetime.now()

        # Format the current date and time as a string
        now_str = now.strftime('%Y%m%d%H%M%S')

        # Use the current date and time as the database name
        database_name = f'database_{now_str}'

        # Connect to the database (it will be created if it doesn't exist)
        conn = sqlite3.connect(f'databases/{database_name}.db')

        # Create a cursor object
        cursor = conn.cursor()

        # Load the data from the Excel file
        data = pd.read_excel(excel_file)

        # Replace colons in column names with underscore
        data.columns = data.columns.str.replace(':', '_')

        # Get the column names from the DataFrame
        cols = data.columns.tolist()

        # Remove 'Unnamed: 0' from the column names if it exists
        cols = [col for col in cols if col != 'Unnamed: 0']

        # Create a table with the same structure as the data
        cols_str = ', '.join([f'"{col}" TEXT' for col in cols])  # quote the column names
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS demo(
                id INTEGER PRIMARY KEY,
                {cols_str}
            )
        ''')

        # Convert the data to a list of tuples
        data_tuples = list(data.itertuples(index=False, name=None))

        # Insert the data into the table
        placeholders = ', '.join(['?' for _ in cols])
        cols_str = ', '.join([f'"{col}"' for col in cols])  # quote the column names
        cursor.executemany(f"INSERT INTO demo ({cols_str}) VALUES ({placeholders})", data_tuples)

        # Commit the transaction and close the connection
        conn.commit()
        conn.close()

    except Exception as e:
        print(f"An error occurred while processing the data: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:  # check if a command-line argument was provided
        excel_file = sys.argv[1]  # use the first command-line argument as the Excel file to process
        process_data(excel_file)
    else:
        print("No Excel file provided.")