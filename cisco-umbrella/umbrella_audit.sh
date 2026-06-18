#!/bin/bash

if ! [[ -d "/Library/Application Support/OpenDNS Roaming Client" || -d "/Library/Application Support/Cisco/Cisco Secure Client" ]]; then
    echo "Umbrella path not found"
    exit 1
fi

if ! pgrep -q dnscryptproxy; then
    echo "DNSCryptProxy process is not running"
    exit 1
fi

if ! pgrep -q acumbrellaagent; then
    echo "acumbrellaagent process is not running"
    exit 1
fi

if ! pgrep -q vpnagentd; then
    echo "vpnagentd process is not running"
    exit 1
fi

if [[ $(sudo /usr/bin/dig +time=10 debug.opendns.com txt | grep "dnscrypt enabled" | awk -F '"' '{print $2}' | cut -d'(' -f1 | sed 's/^[[:space:]]*//') != "dnscrypt enabled " ]]; then
    echo "Umbrella agent is not on!"
    exit 1
fi

echo "Pass. Umbrella is installed and the proccess are running"
