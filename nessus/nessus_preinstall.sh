#!/bin/bash
if [ -d /Library/NessusAgent ]; then
    echo "NessusAgent Detected"
    /Library/NessusAgent/Run/sbin/nessuscli agent unlink --force
    rm -rf /Library/NessusAgent
    echo "NessusAgent Uninstalled"
fi
if [ -f /Library/LaunchDaemons/com.tenablesecurity.nessusagent.plist ]; then
    rm /Library/LaunchDaemons/com.tenablesecurity.nessusagent.plist
    echo "Remove nessusagent plist"
fi
if [ -d /Library/PreferencePanes/Nessus\ Agent\ Preferences.prefPane ]; then
    rm -rf /Library/PreferencePanes/Nessus\ Agent\ Preferences.prefPane
    echo "Remove nessusagent prefPane"
fi
if [ -z "$(launchctl list | grep com.tenablesecurity.nessusagent | awk '{print $NF}')" ]; then
    launchctl remove com.tenablesecurity.nessusagent
    echo "Remove nessusagent"
fi