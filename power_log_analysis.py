import os
import time
from datetime import datetime, timedelta, time
from power_log_merge import process_log_file, \
                            merge, \
                            get_scan_energy, \
                            extract_scans, \
                            add_energy_column


# Run the energy log analysis:
file_path = '/Users/oscarlally/Downloads/New Logs/EnergyTextFile.txt'
blocks = process_log_file(file_path)
# # Output the result
# for idx, block in enumerate(blocks):
#     print(f"Index: {idx} - Start Time: {block['start_time']} - End Time: {block['end_time']} - Duration: {block['duration']}s - Total Energy: {block['total_energy']} Ws")


# Save the day into a df
df_scans = extract_scans('smrvid', '2024-06-24')
df_scans.to_csv('./Data/output.csv', index=False)


# Extract the relevant parameters to feed to the main function
scan_idx = 1
start_time = df_scans.loc[scan_idx]['start_time']
duration = df_scans.loc[scan_idx]['scan_length']
protocol = df_scans.loc[scan_idx]['protocol']
date_id = df_scans.loc[scan_idx]['date_id']
end_time = (datetime.combine(datetime.today(), start_time) + timedelta(minutes=duration)).time()


# Get the total energy during that protocol
idx_1, idx_2 = merge(blocks, start_time, end_time, 1)
if idx_1 is not None:

    scan_energy = round(get_scan_energy(blocks, idx_1, idx_2), 3)
    print(f"Total energy in the scan {protocol}: {scan_energy} J")

    # Create a new energy column
    print(type('smrvid'), type('scans'), type(date_id), type(start_time), type(float(scan_energy)))
    add_energy_column('smrvid', 'scans', int(date_id), start_time, float(scan_energy))




