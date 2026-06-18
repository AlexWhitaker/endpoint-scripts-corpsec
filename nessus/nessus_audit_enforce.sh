#!/bin/bash
# Validates that the Nessus Agent is installed, running, and linked to Tenable Cloud.
# Returns exit 0 on pass, exit 1 on any failure condition.
#
# Set FORCE_REINSTALL=true to force a reinstall trigger (exit 1).

set -euo pipefail

force_reinstall="${FORCE_REINSTALL:-false}"

if [ "$force_reinstall" = "true" ]; then
    echo "Reinstall forced via FORCE_REINSTALL=true"
    exit 1
fi

if ! [[ -x /Library/NessusAgent/run/sbin/nessuscli ]]; then
    echo "nessuscli not found — Nessus Agent may not be installed"
    exit 1
fi

if ! pgrep -q nessusd; then
    echo "nessusd process is not running"
    exit 1
fi

link_status=$(/Library/NessusAgent/run/sbin/nessuscli agent status | sed -En 's/.*Link status: (.*)/\1/p')
if [[ "$link_status" != "Connected to sensor.cloud.tenable.com:443" ]]; then
    echo "Nessus agent is not properly linked: ${link_status}"
    exit 1
fi

echo "Pass: Nessus Agent is installed, running, and linked to Tenable Cloud."
