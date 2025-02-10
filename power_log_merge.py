from datetime import datetime
from psycopg2 import sql
import pandas as pd
import numpy as np
import psycopg2
import os


def process_log_file(file_path):

    folder_path = os.path.dirname(file_path)
    files_in_folder = sorted([f for f in os.listdir(folder_path) if f.endswith('.txt')])
    current_file_index = files_in_folder.index(os.path.basename(file_path))

    # Get paths to previous and next files
    previous_file_path = os.path.join(folder_path, files_in_folder[current_file_index - 1]) if current_file_index > 0 else None
    next_file_path = os.path.join(folder_path, files_in_folder[current_file_index + 1]) if current_file_index < len(files_in_folder) - 1 else None

    blocks = []
    current_block = None

    with open(file_path, 'r') as file:
        lines = file.readlines()

        for i, line in enumerate(lines):
            # Start of a block
            if "cmdStartMeasurement" in line:
                if current_block:
                    blocks.append(current_block)  # Save the previous block
                current_block = {
                    'start_time': parse_timestamp(line.split('|')[0]),
                    'total_energy': 0.0,
                    'end_time': None,
                    'duration': None,
                }

            # Update energy info within a block
            elif "cmdUpdateEngInfo" in line and current_block:
                wattage = float(line.split("energy: ")[-1].split(" ")[0])
                current_block['total_energy'] = wattage
                #current_block['end_time'] = parse_timestamp(line.split('|')[0])  # Update end_time

            # End of a block
            elif "cmdEndMeasurement" in line and current_block:
                current_block['end_time'] = parse_timestamp(line.split('|')[0])
                current_block['duration'] = calculate_duration(
                    current_block['start_time'], current_block['end_time']
                )
                blocks.append(current_block)  # Finalise the block
                current_block = None  # Reset for the next block

        # Handle incomplete block at the end of the file
        if current_block and not current_block.get('end_time'):

            current_block = complete_block_from_adjacent_files(
                current_block, file_path, previous_file_path, next_file_path
            )
            blocks.append(current_block)

    return blocks


def complete_block_from_adjacent_files(current_block, file_path, previous_file_path, next_file_path):
    """Check both the next and previous files for the continuation of an incomplete block."""
    current_file_last_time = get_last_timestamp(file_path)

    # Check the next file
    if next_file_path:
        next_file_second_time = get_second_timestamp(next_file_path)
        if next_file_second_time and time_difference_in_seconds(current_file_last_time, next_file_second_time) <= 2:
            current_block = complete_block_from_next_file(current_block, next_file_path)

    # Check the previous file
    if previous_file_path and not current_block['end_time']:
        previous_file_second_time = get_second_timestamp(previous_file_path)

        if previous_file_second_time and time_difference_in_seconds(current_file_last_time, previous_file_second_time) <= 2:

            current_block = complete_block_from_previous_file(current_block, previous_file_path)

    return current_block


def complete_block_from_next_file(current_block, next_file_path):
    """Check the next file for continuation."""
    with open(next_file_path, 'r') as next_file:
        for line in next_file:  # Read file in natural order
            if "cmdUpdateEngInfo" in line:
                # Parse energy and timestamp from the line
                timestamp = parse_timestamp(line.split('|')[0])
                wattage = float(line.split("energy: ")[-1].split(" ")[0])
                current_block['total_energy'] += wattage

                # Update the block's end time based on the most recent data
                #current_block['end_time'] = timestamp

            elif "cmdEndMeasurement" in line:
                # Set the end time to the line's timestamp
                current_block['end_time'] = parse_timestamp(line.split('|')[0])

                # Calculate the block's duration
                current_block['duration'] = calculate_duration(
                    current_block['start_time'], current_block['end_time']
                )
                return current_block  # Block is complete, exit early

    return current_block  # Return the block if no end line is found


def complete_block_from_previous_file(current_block, previous_file_path):
    """Check the previous file for continuation."""
    with open(previous_file_path, 'r') as previous_file:
        for line in previous_file:  # Read file in natural order
            if "cmdUpdateEngInfo" in line:
                # Parse energy and timestamp from the line
                timestamp = parse_timestamp(line.split('|')[0])
                wattage = float(line.split("energy: ")[-1].split(" ")[0])
                current_block['total_energy'] += wattage

                # If start time is missing, set it based on the first valid data line
                #if current_block['start_time'] is None:
                #    current_block['start_time'] = timestamp

            elif "cmdEndMeasurement" in line:
               # Set the end time to the line's timestamp
                current_block['end_time'] = parse_timestamp(line.split('|')[0])

                # Calculate the block's duration
                current_block['duration'] = calculate_duration(
                    current_block['start_time'], current_block['end_time']
                )
                return current_block  # Block is complete, exit early

    return current_block  # Return the block if no start line is found



def get_second_timestamp(file_path):
    """Get the timestamp of the second valid line in the file."""
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines[1:]:
            if "|" in line:
                return parse_timestamp(line.split('|')[0])
    return None


def get_last_timestamp(file_path):
    """Get the timestamp of the last valid line in the file."""
    with open(file_path, 'r') as file:
        for line in reversed(file.readlines()):
            if "|" in line:
                return parse_timestamp(line.split('|')[0])
    return None


def parse_timestamp(timestamp):
    """Parse the timestamp from the log and return a datetime object."""
    return datetime.strptime(timestamp, "%Y/%m/%d-%H:%M:%S.%f")


def time_difference_in_seconds(time1, time2):
    """Calculate the absolute time difference in seconds between two timestamps."""
    return abs((time1 - time2).total_seconds())


def calculate_duration(start_time, end_time):
    """Calculate the duration in seconds between two datetime objects."""
    if start_time is None or end_time is None:
        return None
    return (end_time - start_time).total_seconds()


def extract_scans(schema, target_date):
    """Finds the date_id for a given date and returns all scans ordered by start_time as a DataFrame."""

    # Database connection parameters
    db_params = {
        'dbname': 'mriutilisation',
        'user': 'mridevs',
        'password': 'qwer1234',
        'host': 'localhost',
        'port': 5432
    }

    # Establish a connection to the database
    conn = psycopg2.connect(**db_params)

    try:
        with conn.cursor() as cur:
            # Step 1: Get the date_id for the given target_date
            cur.execute(sql.SQL("""
                SELECT id FROM {}.dates WHERE date = %s;
            """).format(sql.Identifier(schema)), (target_date,))
            result = cur.fetchone()

            if not result:
                print(f"No matching date_id found for {target_date} in schema {schema}.")
                return pd.DataFrame()  # Return empty DataFrame

            date_id = result[0]

            # Step 2: Fetch all scans with this date_id, ordered by start_time
            cur.execute(sql.SQL("""
                SELECT * FROM {}.scans WHERE date_id = %s ORDER BY start_time;
            """).format(sql.Identifier(schema)), (date_id,))

            columns = [desc[0] for desc in cur.description]  # Get column names
            scans = cur.fetchall()

            # Convert to DataFrame
            df = pd.DataFrame(scans, columns=columns)
            return df

    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

    finally:
        # Close the connection
        conn.close()


def diff_mins(block, time):

    # Convert to datetime objects (same arbitrary date)
    datetime1 = datetime.combine(datetime.min, block[time[0]].time())
    datetime2 = datetime.combine(datetime.min, time[1])

    # Get the difference in minutes
    return (datetime2 - datetime1).total_seconds() / 60


def merge(blocks, start_time, end_time, tolerance):

    start_idx = 0

    for idx, block in enumerate(blocks):

        if start_idx == 0:
            difference = diff_mins(block, ['start_time', start_time])
            if abs(difference) < tolerance:
                start_idx = idx

        else:
            difference = diff_mins(block,  ['end_time', end_time])
            if abs(difference) < tolerance:
                return start_idx, idx

    return None, None


def get_scan_energy(blocks, start_idx, end_idx):

    protocol_energy = 0

    if end_idx + 1 > len(blocks):
        end_range = len(blocks)
    else:
        end_range = end_idx + 1

    for i in range(start_idx, end_range):
        protocol_energy += float(blocks[i]['total_energy'])

    return protocol_energy


def add_energy_column(schema, table, date_id, start_time, energy):
    """Adds an 'energy' column if missing and updates a row where date_id and start_time match."""

    # Ensure energy is a plain float
    if isinstance(energy, (np.int64, np.float64)):
        energy = float(energy)

    # Database connection parameters
    db_params = {
        'dbname': 'mriutilisation',
        'user': 'mridevs',
        'password': 'qwer1234',
        'host': 'localhost',
        'port': 5432
    }

    # Establish a connection to the database
    conn = psycopg2.connect(**db_params)

    try:
        with conn.cursor() as cur:
            # Step 1: Add the 'energy' column if it doesn't exist
            cur.execute(sql.SQL("""
                ALTER TABLE {}.{} 
                ADD COLUMN IF NOT EXISTS energy FLOAT;
            """).format(sql.Identifier(schema), sql.Identifier(table)))

            # Step 2: Update the row where date_id and start_time match
            cur.execute(sql.SQL("""
                UPDATE {}.{} 
                SET energy = %s 
                WHERE date_id = %s AND start_time = %s;
            """).format(sql.Identifier(schema), sql.Identifier(table)),
                (energy, date_id, start_time))

            # Commit changes
            conn.commit()
            print(f"Updated {schema}.{table}: Set energy={energy} for date_id={date_id} and start_time={start_time}")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()

    finally:
        # Close the connection
        conn.close()






# def hamlet_add(blocks, start_idx, end_idx):
#
#     protocol_energy = 0
#     compare = 0
#
#     if end_idx + 1 > len(blocks):
#         end_range = len(blocks)
#     else:
#         end_range = end_idx + 1
#
#     for i in range(start_idx, end_range):
#         if float(blocks[i]['total_energy']) > compare:
#             compare = float(blocks[i]['total_energy'])
#             protocol_energy += float(blocks[i]['total_energy']) - compare
#         else:
#             compare = float(blocks[i]['total_energy'])
#             protocol_energy += float(blocks[i]['total_energy'])
#
#     return protocol_energy



