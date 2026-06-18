#!/bin/bash
# Installs a Nessus Agent from a DMG and links it to Tenable Cloud.
#
# Usage:
#   sudo TENABLE_LINKING_KEY=<key> NESSUS_AGENT_DMG=<filename> ./nessus_postinstall.sh
#
# Required environment variables:
#   TENABLE_LINKING_KEY  — Tenable agent linking key
#   NESSUS_AGENT_DMG     — DMG filename located in /private/var/tmp/

set -euo pipefail

LINKING_KEY="${TENABLE_LINKING_KEY:?TENABLE_LINKING_KEY environment variable must be set}"
NESSUS_DMG="${NESSUS_AGENT_DMG:?NESSUS_AGENT_DMG environment variable must be set}"

if [[ $EUID -ne 0 ]]; then
    echo "Error: This script must be run as root." >&2
    exit 1
fi

DMG_PATH="/private/var/tmp/${NESSUS_DMG}"

if [[ ! -f "$DMG_PATH" ]]; then
    echo "Error: DMG not found at ${DMG_PATH}" >&2
    exit 1
fi

echo "Mounting DMG: ${DMG_PATH}"
hdiutil attach -nobrowse "$DMG_PATH"

echo "Installing Nessus Agent..."
installer -pkg "/Volumes/Nessus Agent Install/Install Nessus Agent.pkg" -target /

echo "Detaching DMG..."
hdiutil detach "/Volumes/Nessus Agent Install"

echo "Linking agent to Tenable Cloud..."
/Library/NessusAgent/run/sbin/nessuscli agent link \
    --key="${LINKING_KEY}" \
    --groups=All \
    --cloud

echo "Removing installer DMG..."
rm "$DMG_PATH"

echo "Nessus Agent installed and linked successfully."
