from datetime import datetime, timedelta
import json
import os

app_path = "/Users/oscarlally/Desktop/Oscar/PhysicsDashboard/tailwind-dashboard-template-main/public"
base_paths = ['/Users/oscarlally/Desktop/try/GMRI3', '/Users/oscarlally/Desktop/try/GMRI4', '/Users/oscarlally/Desktop/try/SMRVID']

# Get the date a week ago
scanner_list = ["EMRI1", "EXMRI", "SMRVID", "GMRI3", "GMRI4"]
current_datetime = datetime.now()

# Generate a list of all days from yesterday to a week ago
days_list = []
for i in range(7):
    day = current_datetime - timedelta(days=i+1)  # Subtract i+1 days from current date
    formatted_day = day.strftime("%d-%m-%y")
    days_list.append(formatted_day)

messages = []

for i in base_paths:
    file_names = [f for f in os.listdir(i) if not f.startswith('.')]
    full_file_names = [os.path.join(i, file) for file in file_names]
    all_files = "".join(full_file_names)
    if not any(day in all_files for day in days_list):
        for j in scanner_list:
            if j in all_files:
                messages.append(f"{j}")


# Create the new dictionary entry
message = ""
for idx, i in enumerate(messages):
    if idx == 0:
        message = message + i
    if 0 < idx < len(messages) - 1:
        message = message + ', ' + i
    if idx == len(messages) - 1 and idx != 0:
        message = message + ' and ' + i

if len(messages) == 1:
    message = 'CRITICAL: ' + message + ' is offline and inactive. Please rectify immediately.'
    icon = '🚨'
elif len(messages) > 1:
    message = 'CRITICAL: ' + message + ' are offline and inactive. Please rectify immediately.'
    icon = '🚨'
else:
    message = "All scanners are regularly updating!"
    icon = '🔔'


# Save the new data in a dictionary
new_data = {
        "icon": icon,
        "message": f"{message}",
        "date": current_datetime.strftime("%b %d, %Y"),
        "link": "#0"
        }


# Read the existing JSON data
with open(f"{app_path}/notifications.json", 'r') as file:
    data = json.load(file)

# Replace the first item
data[0] = new_data

# Write the updated data back to the JSON file
with open(f"{app_path}/notifications.json", 'w') as file:
    json.dump(data, file, indent=2)











