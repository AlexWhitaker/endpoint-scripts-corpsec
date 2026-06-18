#!/bin/bash

# Check if Cisco Umbrella Secure Client is running using pgrep
umbrella_process=$(pgrep -fl "OpenDNSConnector")

if [ -n "$umbrella_process" ]; then
    echo "Cisco Umbrella Secure Client is running."
else
    echo "Cisco Umbrella Secure Client is not running."
fi

# Alternatively, check using the CLI tool if available
umbrella_cli="/Library/Application Support/OpenDNS Roaming Client/umbrella_cli"

if [ -f "$umbrella_cli" ]; then
    "$umbrella_cli" status
else
    echo "Umbrella CLI tool not found."
fi

