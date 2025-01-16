import psycopg2
from psycopg2 import sql
import pandas as pd
from datetime import datetime
import shutil
import os

info = []

# Database connection parameters
db_params = {
    'dbname': 'mriutilisation',
    'user': 'mridevs',
    'password': 'qwer1234',
    'host': 'localhost',
    'port': 5432
}


def check_and_handle_directories(dir_list):
    for directory in dir_list:
        if not os.path.exists(directory):
            # Create directory if it doesn't exist
            print(f"Creating directory: {directory}")
            os.makedirs(directory)
        else:
            # Directory exists
            if os.listdir(directory):
                # Directory is not empty
                print(f"The directory '{directory}' exists and is not empty.")
                while True:
                    choice = input(f"Do you want to delete its contents and recreate it? (y/n): ").lower()
                    if choice == 'y':
                        # Delete and recreate the directory
                        print(f"Deleting contents of {directory} and recreating it.")
                        shutil.rmtree(directory)
                        os.makedirs(directory)
                        break
                    elif choice == 'n':
                        print(f"Leaving the directory '{directory}' as is.")
                        break
                    else:
                        print("Invalid input. Please enter 'y' or 'n'.")
            else:
                print(f"The directory '{directory}' exists and is empty.")


def get_schemas(cursor):
    """Retrieve all schemas in the database."""
    cursor.execute("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'public')
        ORDER BY schema_name;
    """)
    return [row[0] for row in cursor.fetchall()]


def get_tables(cursor, schema):
    """Retrieve all tables in a schema."""
    cursor.execute(sql.SQL("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
        ORDER BY table_name;
    """), [schema])
    return [row[0] for row in cursor.fetchall()]


def get_columns(cursor, schema, table):
    """Retrieve all columns for a specific table in a schema."""
    cursor.execute(sql.SQL("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position;
    """), [schema, table])
    return cursor.fetchall()


try:
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()

    # Get all schemas
    schemas = get_schemas(cursor)

    for schema_name in schemas:
        # Initialize schema as an empty dictionary for each schema
        schema_dict = {}
        # Get tables in the schema
        tables = get_tables(cursor, schema_name)
        if tables:
            for table in tables:
                # Get columns for the table
                columns = get_columns(cursor, schema_name, table)
                schema_dict[table] = columns  # Store columns for the table in the schema
        info.append({schema_name: schema_dict})  # Append the schema dictionary to info with schema_name as the key


except Exception as e:
    print(f"Error: {e}")
finally:
    # Close the connection
    if conn:
        conn.close()


def get_valid_integer(prompt):
    while True:
        user_input = input(prompt)
        try:
            # Try to convert input to an integer
            return int(user_input)
        except ValueError:
            # Handle invalid input
            print("Invalid input. Please enter a valid integer.")

# Introduction
check_and_handle_directories([f"{os.getcwd()}/Queries"])
print("Welcome to the MRI Dashboard Query Tool")
print("---------------------------------------")
print()
print('Available scanners are:')
for idx, i in enumerate(schemas):
    print(f"{idx+1}. {i.upper()}")


# Get the correct schema
schema_check = get_valid_integer("Please select a number from the options:  ")
print(f"You have chosen {schemas[schema_check-1]} scans")
selected_dict_pre = info[schema_check-1]
selected_schema = f"{schemas[schema_check-1]}"
selected_dict = selected_dict_pre[selected_schema]
tables_to_query = list(selected_dict.keys())


# Get the correct tables
print()
print()
print("Please select the tables you want to query.")
for idx, i in enumerate(tables_to_query):
    print(f"{idx+1}. {i}")

selected_tables_pre = []
print()
table_to_choose = get_valid_integer("Please select a number from the options:  ")
selected_tables_pre.append(tables_to_query[table_to_choose-1])


# finished = False
# print()
# while finished is False:
#     table_to_choose = get_valid_integer("Please select a number from the options:  ")
#     selected_tables_pre.append(tables_to_query[table_to_choose-1])
#     again = input("Table selected.  Would you like to query another table (y/n)?:  ")
#     if again.lower() != 'y':
#         finished = True

selected_tables = list(set(selected_tables_pre))


# Get the correct columns
columns = ['id']
finished = False
for i in selected_tables:
    print(f"From the {i} table, please select the columns you want to query.")
    columns_to_query = list(selected_dict[i])
    filtered_data = [tup for tup in columns_to_query if 'id' not in tup[0]]
    for idx, j in enumerate(filtered_data):
        print(f"{idx+1}. {j[0]}")
    print()
    while finished is False:
        column_to_choose = get_valid_integer("Please select a number from the options:  ")
        columns.append(filtered_data[column_to_choose - 1][0])
        again = input("Column selected.  Would you like to query another column (y/n)?:  ")
        if again.lower() != 'y':
            finished = True


# The actual query function with the information
def get_data(schema, table, columns, start_date, end_date, db_params, excel_file_path):
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(
            host=db_params['host'],
            dbname=db_params['dbname'],
            user=db_params['user'],
            password=db_params['password'],
            port=db_params['port']
        )

        cursor = connection.cursor()

        # Dynamically create the column names for the SELECT statement
        columns_str = ", ".join([f"t.{col}" for col in columns])

        # SQL query to get data for a given date range, joining with the dates table
        query = sql.SQL("""
            SELECT {columns}, d.date
            FROM {schema}.{table} t
            JOIN {schema}.dates d ON t.date_id = d.id
            WHERE d.date BETWEEN %s AND %s
            ORDER BY d.date;
        """).format(
            columns=sql.SQL(columns_str),
            schema=sql.Identifier(schema),
            table=sql.Identifier(table)
        )

        # Execute the query with the given parameters (start_date and end_date)
        cursor.execute(query, (start_date, end_date))

        # Fetch all results
        data = cursor.fetchall()

        # Convert the data to a Pandas DataFrame
        column_names = columns + ['date']
        df = pd.DataFrame(data, columns=column_names)
        df = df.drop(df.columns[0], axis=1)

        # Save the DataFrame to an Excel file
        df.to_excel(excel_file_path, index=False)

        # Inform the user
        print()
        print(f"Data has been saved to {excel_file_path}")

        # Close the cursor and connection
        cursor.close()
        connection.close()

    except Exception as e:
        print(f"Error: {e}")

# Example usage
current_datetime = datetime.now()
formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H:%M")

table = selected_tables[0]

print()
start_date = input("Please type in the start date to query in the format 'YYYY-MM-DD':  ")
end_date = input("Please type in the end date to query in the format 'YYYY-MM-DD':  ")
excel_file_path = f'./Queries/{formatted_datetime}_Data.xlsx'  # Specify the path where you want to save the Excel file
get_data(selected_schema, table, columns, start_date, end_date, db_params, excel_file_path)

