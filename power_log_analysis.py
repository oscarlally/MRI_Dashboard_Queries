import os
import time
from datetime import datetime


def process_log_file(file_path):
    start_code_time = time.time()

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
                current_block['total_energy'] += wattage
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

    execution_time = time.time() - start_code_time
    return blocks, execution_time


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


# Example usage:
file_path = '/Users/oscarlally/Downloads/New Logs/EnergyTextFile.txt'
blocks, execution_time = process_log_file(file_path)

# Output the result
for block in blocks:
    print(f"Start Time: {block['start_time']} - End Time: {block['end_time']} - Duration: {block['duration']}s - Total Energy: {block['total_energy']} Ws")

print(f"Code execution time: {execution_time} seconds")