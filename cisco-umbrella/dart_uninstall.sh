#!/bin/sh

INSTPREFIX="/opt/cisco/secureclient"
BINDIR="${INSTPREFIX}/bin"
DARTDIR="${INSTPREFIX}/dart"
CONFIGXMLDIR="${DARTDIR}/xml/config"
REQUESTXMLDIR="${DARTDIR}/xml/request"
APPDIR="/Applications/Cisco"
DARTAPP="Cisco Secure Client - DART.app"
ACMANIFESTDAT="${INSTPREFIX}/VPNManifest.dat"
DARTMANIFEST="ACManifestDART.xml"
LOGDIR="/var/log/secureclient"
LOG="${LOGDIR}/csc_dart_uninstall.log"
UNINSTALLER="Uninstall Cisco Secure Client - DART.app"
DARTHELPER="com.cisco.secureclient.dart.helper"
HELPER_DIR="/Library/PrivilegedHelperTools"
LAUNCHD_DIR="/Library/LaunchDaemons"
LAUNCHD_FILE="${DARTHELPER}.plist"
AUTH_RULE="com.cisco.secureclient.dart.collect"

CISCO_SECURE_CLIENT_DART_PACKAGE_ID=com.cisco.pkg.anyconnect.dart
CISCO_SECURE_CLIENT_DART_APPLICATION_NAME="Cisco Secure Client - DART"

# List of files to remove
FILELIST=("${APPDIR}/${DARTAPP}" \
          "${INSTPREFIX}/${DARTMANIFEST}" \
          "${BINDIR}/dart_uninstall.sh" \
          "${BINDIR}/manifesttool_dart" \
          "${BINDIR}/SetUIDTool_dart" \
          "${DARTDIR}" \
          "${APPDIR}/${UNINSTALLER}")

# Create log directory if not exist
if [ ! -d ${LOGDIR} ]; then
  mkdir -p ${LOGDIR} >/dev/null 2>&1
fi
		  
echo "Uninstalling Cisco Secure Client - DART..."
echo "Uninstalling Cisco Secure Client - DART..." > "${LOG}"
echo `whoami` "invoked $0 from " `pwd` " at " `date` >> "${LOG}"

# Check for root privileges
if [ `id | sed -e 's/(.*//'` != "uid=0" ]; then
  echo "Sorry, you need super user privileges to run this script."
  echo "Sorry, you need super user privileges to run this script." >> "${LOG}"
  exit 1
fi

# update the VPNManifest.dat
echo "${BINDIR}/manifesttool_dart -x ${INSTPREFIX} ${INSTPREFIX}/${DARTMANIFEST}" >> "${LOG}"
${BINDIR}/manifesttool_dart -x ${INSTPREFIX} ${INSTPREFIX}/${DARTMANIFEST} >> "${LOG}"

# ensure that DART is not running
OURPROCS=`ps -A -o pid,command | egrep "$CISCO_SECURE_CLIENT_DART_APPLICATION_NAME" | egrep -v "grep|dart_uninstall|${UNINSTALLER}" | awk '{print $1}'`
if [ -n "${OURPROCS}" ] ; then
    for DOOMED in ${OURPROCS}; do
        echo Killing `ps -A -o pid,command -p ${DOOMED} | grep ${DOOMED} | egrep -v 'ps|grep'` >> "${LOG}"
        kill -INT ${DOOMED} >> "${LOG}" 2>&1
    done
fi

# Remove DART helper
if [ -f ${HELPER_DIR}/${DARTHELPER} ]; then
  # Stop the helper if it's still running
  OS_VER_MAJOR=$(sw_vers -productVersion | awk -F. '{ print $1; }')
  OS_VER_MINOR=$(sw_vers -productVersion | awk -F. '{ print $2; }')
  if [ "$OS_VER_MAJOR" -gt 10 ] || [ "$OS_VER_MINOR" -ge 11 ] ; then
    # Use new launchctl subcommand for macOS 10.11 and later
    echo "launchctl bootout system ${LAUNCHD_DIR}/${LAUNCHD_FILE}" >> "${LOG}"
    launchctl bootout system ${LAUNCHD_DIR}/${LAUNCHD_FILE} >> "${LOG}" 2>&1
  else
    # Use legacy launchctl subcommand for earlier macOS
    # IMPORTANT: The use of sudo here is necessary to ensure that we communicate
    #  with the global instance of launchd. Without the sudo, the uninstall will fail
    #  when initiated from the GUI. This appears to be due to launchctl working
    #  based on the UID, rather than the EUID. The GUI program will only set the
    #  EUID to root, while the UID remains as the user.
    echo "sudo launchctl unload ${LAUNCHD_DIR}/${LAUNCHD_FILE}" >> "${LOG}"
    sudo launchctl unload ${LAUNCHD_DIR}/${LAUNCHD_FILE} >> "${LOG}" 2>&1
  fi
  # Remove DART helper file
  echo "Removing ${LAUNCHD_DIR}/${LAUNCHD_FILE}" >> "${LOG}"
  rm -f ${LAUNCHD_DIR}/${LAUNCHD_FILE}
  echo "Removing ${HELPER_DIR}/${DARTHELPER}" >> "${LOG}"
  rm -f ${HELPER_DIR}/${DARTHELPER}
fi

# Cleanup authorization database rule
echo "security -q authorizationdb remove ${AUTH_RULE}" >> "${LOG}"
security -q authorizationdb remove ${AUTH_RULE}

# Remove only those files that we know we installed
INDEX=0
while [ $INDEX -lt ${#FILELIST[@]} ] ; do
    echo "rm -rf "${FILELIST[${INDEX}]}"" >> "${LOG}"
    rm -rf "${FILELIST[${INDEX}]}"
    let  "INDEX = $INDEX + 1"
done

# Remove the bin directory if it is empty
if [ -e ${BINDIR} ] ; then
  if [ ! -z `find "${BINDIR}" -prune -empty` ] ; then
    echo "rm -df "${BINDIR}"" >> ${LOG}
    rm -df "${BINDIR}" >> ${LOG} 2>&1
  fi	
fi

# Remove the Cisco directory if it is empty
if [ ! -z `find "${APPDIR}" -prune -empty` ] ; then 
    echo "rm -rf "${APPDIR}"" >> "${LOG}"
    rm -rf "${APPDIR}"
fi

# remove installer receipt
pkgutil --forget ${CISCO_SECURE_CLIENT_DART_PACKAGE_ID} >> "${LOG}" 2>&1

echo "Successfully removed Cisco Secure Client - DART from the system." >> "${LOG}"
echo "Successfully removed Cisco Secure Client - DART from the system."

exit 0
