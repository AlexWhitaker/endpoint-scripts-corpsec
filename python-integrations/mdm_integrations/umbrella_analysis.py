import json
import os
import requests
from datetime import datetime, timedelta, timezone
import pandas as pd

token_endpoint = "https://api.umbrella.com/auth/v2/token"
api_key = os.environ["UMBRELLA_API_KEY"]
secret = os.environ["UMBRELLA_API_SECRET"]
grant_type = "client_credentials"

response = requests.post(
    token_endpoint,
    auth=(api_key, secret),
    data={"grant_type": grant_type}
)

access_token = response.json()["access_token"]

api_endpoint = "https://api.umbrella.com/deployments/v2/roamingcomputers"
page_number = 1

all_computers = []


def fetch_page(page_number):
    response = requests.get(
        api_endpoint,
        params={"page": page_number},
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.json()}")
        return []


data = fetch_page(page_number)
total_items = len(data)
all_computers.extend(data)

while len(data) == 200:
    page_number += 1
    data = fetch_page(page_number)
    all_computers.extend(data)

encrypted_computers = []
open_computers = []
off_computers = []
uninstalled_computers = []

for computer in all_computers:
    status = computer.get("status")
    if status == "Encrypted":
        encrypted_computers.append(computer)
    elif status == "Open":
        open_computers.append(computer)
    elif status == "Off":
        off_computers.append(computer)
    elif status == "Uninstalled":
        uninstalled_computers.append(computer)

encrypted_count = len(encrypted_computers)
open_count = len(open_computers)
off_count = len(off_computers)
uninstalled_count = len(uninstalled_computers)

print("Count of Computers by Status:")
print(f"Encrypted: {encrypted_count}")
print(f"Open: {open_count}")
print(f"Off: {off_count}")
print(f"Uninstalled: {uninstalled_count}")

off_within_24_hours = []
off_not_within_24_hours = []

current_time = datetime.now(timezone.utc)

for computer in off_computers:
    last_sync = computer.get("lastSync")
    if last_sync:
        last_sync_time = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
        time_difference = current_time - last_sync_time
        if time_difference < timedelta(hours=24):
            off_within_24_hours.append(computer)
        else:
            off_not_within_24_hours.append(computer)

print("\nBreakdown of 'Off' Computers:")
print(f"Off within 24 hours: {len(off_within_24_hours)}")
print(f"Off not within 24 hours: {len(off_not_within_24_hours)}")

encrypted_macs = []
encrypted_windows = []

for computer in encrypted_computers:
    os_version = computer.get("osVersionName", "")
    if "Mac OS" in os_version:
        encrypted_macs.append(computer)
    elif "Windows" in os_version:
        encrypted_windows.append(computer)

print("\nCount of Encrypted Computers by Operating System:")
print(f"Mac OS: {len(encrypted_macs)}")
print(f"Windows: {len(encrypted_windows)}")

mac_count = 0
windows_count = 0

for computer in all_computers:
    os_version = computer.get("osVersionName", "")
    if "Mac OS" in os_version:
        mac_count += 1
    elif "Windows" in os_version:
        windows_count += 1

print("\nTotal Count of Computers by Operating System:")
print(f"Mac OS: {mac_count}")
print(f"Windows: {windows_count}")
print(f"\nTotal number of computers pulled down: {len(all_computers)}")

computers_within_24_hours = []
computers_not_within_24_hours = []

for computer in all_computers:
    last_sync = computer.get("lastSync")
    if last_sync:
        last_sync_time = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
        time_difference = current_time - last_sync_time
        days = time_difference.days
        hours, remainder = divmod(time_difference.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        computer["time_since_sync"] = f"{days} days, {hours} hours, {minutes} minutes"
        if time_difference < timedelta(hours=24):
            computers_within_24_hours.append(computer)
        else:
            computers_not_within_24_hours.append(computer)

computers_not_within_24_hours.sort(key=lambda x: x.get("lastSync"))

mac_within_24_hours_count = sum(
    1 for c in computers_within_24_hours if "Mac OS" in c.get("osVersionName", "")
)
windows_within_24_hours_count = sum(
    1 for c in computers_within_24_hours if "Windows" in c.get("osVersionName", "")
)
mac_not_within_24_hours_count = sum(
    1 for c in computers_not_within_24_hours if "Mac OS" in c.get("osVersionName", "")
)
windows_not_within_24_hours_count = sum(
    1 for c in computers_not_within_24_hours if "Windows" in c.get("osVersionName", "")
)

print("\nBreakdown of Computers with LastSync Within 24 Hours by Operating System:")
print(f"Mac OS: {mac_within_24_hours_count}")
print(f"Windows: {windows_within_24_hours_count}")

print("\nBreakdown of Computers with LastSync Not Within 24 Hours by Operating System:")
print(f"Mac OS: {mac_not_within_24_hours_count}")
print(f"Windows: {windows_not_within_24_hours_count}")

print(f"\nTotal checked in within 24 hours: {len(computers_within_24_hours)}")
print(f"Total checked in more than 24 hours: {len(computers_not_within_24_hours)}")
print(f"\nTotal Macs checked in within 24 hours / total Macs in Umbrella: {mac_within_24_hours_count} / {mac_count}")
print(f"Total Windows checked in within 24 hours / total Windows in Umbrella: {windows_within_24_hours_count} / {windows_count}")

df_within_24_hours = pd.DataFrame(computers_within_24_hours)
df_not_within_24_hours = pd.DataFrame(computers_not_within_24_hours)

with pd.ExcelWriter("computers_summary.xlsx") as writer:
    df_within_24_hours.to_excel(writer, sheet_name="Computers Within 24 Hours", index=False)
    df_not_within_24_hours.to_excel(writer, sheet_name="Computers Not Within 24 Hours", index=False)

print("\nExported to computers_summary.xlsx")
