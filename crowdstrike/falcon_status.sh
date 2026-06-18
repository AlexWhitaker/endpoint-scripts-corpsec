#!/bin/sh
# Conditional check based on connection state
if [ -e /Library/CS/falconctl ]; then
    falconHostState=$(/Library/CS/falconctl stats | awk '/^ *State: /{print $2}')
    if [ -z "$falconHostState" ]
    then
        falconHostState=$(/Library/CS/falconctl stats 2>/dev/null | awk '/^ *State: /{print $2}')
    fi
elif [ -e /Applications/Falcon.app/Contents/Resources/falconctl ]; then
    falconHostState=$(/Applications/Falcon.app/Contents/Resources/falconctl stats 2>/dev/null | awk '/^ *State: /{print $2}')
else
    falconHostState="Not Connected"
fi
echo "<result>$falconHostState</result>"
