# database.py
import os
import sys
import pandas as pd
import datetime
from sqlalchemy import create_engine

def process_data(excel_files, database_name=None):
    try:
        # Ensure the 'databases' directory exists, if not, create it
        if not os.path.exists('databases'):
            os.makedirs('databases')

        # If no custom database name is provided, use the current date and time
        if not database_name:
            # Get the current date and time
            now = datetime.datetime.now()

            # Format the current date and time as a string
            now_str = now.strftime('%Y%m%d%H%M%S')

            # Use the current date and time as the database name
            database_name = f'database_{now_str}'

        # Initialize an empty DataFrame to store all data
        all_data = pd.DataFrame()

        # Process each Excel file
        for excel_file in excel_files:
            # Load the data from the Excel file
            data = pd.read_excel(excel_file)

            # Replace colons in column names with underscore
            data.columns = data.columns.str.replace(':', '_')

            # Append the data to the all_data DataFrame
            all_data = pd.concat([all_data, data], ignore_index=True)

        # Create a SQLAlchemy engine
        engine = create_engine(f'sqlite:///databases/{database_name}.db')

        # Save the DataFrame to a SQLite database
        if not all_data.empty:
            all_data.to_sql('data', engine, index=False, if_exists='replace')
        else:
            print("Warning: The DataFrame is empty. No data was written to the database.")

        # Print debug information
        print(f"Processed {len(excel_files)} Excel files.")
        print(f"Inserted {len(all_data)} rows into the database.")
        print(f"Database saved as 'databases/{database_name}.db'.")

    except Exception as e:
        print(f"An error occurred while processing the data: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 2:  # check if two command-line arguments were provided
        excel_files = sys.argv[1:-1]  # use all but the last command-line argument as the Excel files to process
        database_name = sys.argv[-1]  # use the last command-line argument as the database name
        process_data(excel_files, database_name)
    elif len(sys.argv) > 1:  # check if a command-line argument was provided
        excel_files = sys.argv[1:]  # use all command-line arguments as the Excel files to process
        process_data(excel_files)
    else:
        print("No Excel files provided.")