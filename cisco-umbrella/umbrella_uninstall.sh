#!/bin/sh

CISCO_SECURE_CLIENT_APPLICATION_NAME="Cisco Secure Client"
CSC_INSTPREFIX="/opt/cisco/secureclient"
POSTURE_BINDIR="${CSC_INSTPREFIX}/securefirewallposture/bin64/"
CISCO_SECURE_CLIENT_BINDIR=${CSC_INSTPREFIX}/bin
NVM_BINDIR=${CSC_INSTPREFIX}/NVM/bin

VPN_UNINST=${CISCO_SECURE_CLIENT_BINDIR}/vpn_uninstall.sh
POSTURE_UNINST=${POSTURE_BINDIR}/posture_uninstall.sh
ISEPOSTURE_UNINST=${CISCO_SECURE_CLIENT_BINDIR}/iseposture_uninstall.sh
ISECOMPLIANCE_UNINST=${CISCO_SECURE_CLIENT_BINDIR}/isecompliance_uninstall.sh
NVM_UNINST=${NVM_BINDIR}/nvm_uninstall.sh
UMBRELLA_UNINST=${CISCO_SECURE_CLIENT_BINDIR}/umbrella_uninstall.sh
FIREAMP_UNINST=${CISCO_SECURE_CLIENT_BINDIR}/amp_uninstall.sh

# Gracefully quit the Cisco Secure Client App prior to running uninstall script(s)
echo "Exiting ${CISCO_SECURE_CLIENT_APPLICATION_NAME}"
osascript -e "quit app \"${CISCO_SECURE_CLIENT_APPLICATION_NAME}\"" > /dev/null 2>&1

if [ -x "${ISEPOSTURE_UNINST}" ]; then
  ${ISEPOSTURE_UNINST}
  if [ $? -ne 0 ]; then
    echo "Error uninstalling Cisco Secure Client - ISE Posture."
  fi
fi

if [ -x "${ISECOMPLIANCE_UNINST}" ]; then
  ${ISECOMPLIANCE_UNINST}
  if [ $? -ne 0 ]; then
    echo "Error uninstalling Cisco Secure Client - ISE Compliance."
  fi
fi

if [ -x "${POSTURE_UNINST}" ]; then
  ${POSTURE_UNINST}
  if [ $? -ne 0 ]; then
    echo "Error uninstalling Cisco Secure Client - Secure Firewall Posture."
  fi
fi

if [ -x "${UMBRELLA_UNINST}" ]; then
  ${UMBRELLA_UNINST}
  if [ $? -ne 0 ]; then
    echo "Error uninstalling Cisco Secure Client - Umbrella."
  fi
fi

if [ -x "${FIREAMP_UNINST}" ]; then
  ${FIREAMP_UNINST}
  if [ $? -ne 0 ]; then
  echo "Error uninstalling Cisco Secure Client - AMP Enabler."
  fi
fi

if [ -x "${NVM_UNINST}" ]; then
  ${NVM_UNINST}
  if [ $? -ne 0 ]; then
  echo "Error uninstalling Cisco Secure Client - Network Visibility Module."
  fi
fi

if [ -x "${VPN_UNINST}" ]; then
  ${VPN_UNINST}
  if [ $? -ne 0 ]; then
    echo "Error uninstalling Cisco Secure Client."
  fi
fi

exit 0
