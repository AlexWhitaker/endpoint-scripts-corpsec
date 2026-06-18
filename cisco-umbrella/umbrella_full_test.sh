#!/bin/bash

# Paths to check for Cisco Umbrella Secure Client installation
paths=(
    "/Library/Application Support/OpenDNS Roaming Client"
    "/Library/Application Support/Cisco/Cisco Secure Client"
    "/Library/Application Support/Cisco/umbrella"
)

# Check if any of the specified paths exist
umbrella_installed=false
for path in "${paths[@]}"; do
    if [ -e "$path" ]; then
        umbrella_installed=true
        echo "Found Cisco Umbrella installation at: $path"
        break
    fi
done

# Get the process list and store it in a variable
ps_output=$(ps aux)

# Check for specific Cisco Umbrella Secure Client processes
processes=(
    "UmbrellaAgent"
    "LogUploader"
    "DNSCryptProxy"
)

umbrella_running=true
for process in "${processes[@]}"; do
    if ! echo "$ps_output" | grep -q "$process"; then
        umbrella_running=false
        echo "Process $process is not running."
        break
    fi
done

# Exit status based on checks
if [[ $umbrella_installed == true && $umbrella_running == true ]]; then
    echo "Cisco Umbrella is installed and running."
    exit 0
else
    echo "Cisco Umbrella is not fully operational."
    exit 1
fi
