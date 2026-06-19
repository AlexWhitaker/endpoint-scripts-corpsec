from datetime import datetime
import pytz
from typing import Dict, Any, List
import logging
from base_metrics import BaseDeviceMetrics

logger = logging.getLogger("airwatch-metrics")

class AirWatchMetrics(BaseDeviceMetrics):
    def calculate_status(self, device: Dict[str, Any]) -> tuple[str, float]:
        """Calculate AirWatch device status and flakiness score"""
        try:
            if not device.get('LastSeen'):
                return 'critical', 1.0

            now = datetime.now(pytz.UTC)
            last_seen = datetime.fromisoformat(device['LastSeen']).replace(tzinfo=pytz.UTC)
            days_since_checkin = (now - last_seen).days

            # Calculate flakiness based on multiple factors
            flakiness_score = 0.0
            if device.get('ComplianceStatus') != 'Compliant':
                flakiness_score += 0.4
            if device.get('EnrollmentStatus') != 'Enrolled':
                flakiness_score += 0.3
            if days_since_checkin >= 3:
                flakiness_score += 0.3

            # Cap flakiness at 1.0
            flakiness_score = min(flakiness_score, 1.0)

            # Determine status based on device state
            if (device.get('ComplianceStatus') == 'Compliant' and 
                device.get('EnrollmentStatus') == 'Enrolled' and 
                days_since_checkin < 2):
                return 'healthy', flakiness_score
            elif (device.get('ComplianceStatus') == 'Compliant' and 
                  device.get('EnrollmentStatus') == 'Enrolled' and 
                  days_since_checkin < 3):
                return 'degrading', flakiness_score
            elif device.get('ComplianceStatus') != 'Compliant':
                return 'warning', flakiness_score
            elif (days_since_checkin >= 3 or 
                  device.get('EnrollmentStatus') != 'Enrolled'):
                return 'critical', flakiness_score

            return 'unknown', flakiness_score

        except Exception as e:
            logger.error(f"Error calculating AirWatch status: {str(e)}")
            return 'unknown', 1.0

    def get_tags(self, device: Dict[str, Any]) -> List[str]:
        """Get AirWatch-specific tags"""
        tags = ['tool:airwatch_host', 'env:mgmt']
        
        # Device identifiers
        if device.get('SerialNumber'):
            tags.append(f'serial:{device["SerialNumber"]}')
        if device.get('DeviceFriendlyName'):
            tags.append(f'hostname:{device["DeviceFriendlyName"]}')
        if device.get('Uuid'):
            tags.append(f'device_id:{device["Uuid"]}')

        # Platform and Model information
        if device.get('Platform'):
            tags.append(f'platform:{device["Platform"]}')
        if device.get('Model'):
            tags.append(f'model:{device["Model"]}')
        if device.get('OEMInfo'):
            tags.append(f'manufacturer:{device["OEMInfo"]}')

        # OS information
        if device.get('OperatingSystem'):
            tags.append(f'os_version:{device["OperatingSystem"]}')
        if device.get('OSBuildVersion'):
            tags.append(f'os_build:{device["OSBuildVersion"]}')

        # Status information
        if device.get('ComplianceStatus'):
            tags.append(f'compliance_status:{device["ComplianceStatus"]}')
        if device.get('EnrollmentStatus'):
            tags.append(f'enrollment_status:{device["EnrollmentStatus"]}')
        if device.get('CompromisedStatus') is not None:
            tags.append(f'compromised:{str(device["CompromisedStatus"]).lower()}')

        # User information
        if device.get('UserName'):
            tags.append(f'username:{device["UserName"]}')
        if device.get('Ownership'):
            tags.append(f'ownership:{device["Ownership"]}')

        return tags

    def process_device(self, device: Dict[str, Any]) -> None:
        """Process a single AirWatch device"""
        try:
            hostname = device.get('DeviceFriendlyName', 'unknown')
            status, flakiness_score = self.calculate_status(device)
            
            tags = self.get_tags(device)
            
            # Core metrics (measurements and calculations)
            status_value = {
                'healthy': 0,
                'degrading': 1,
                'warning': 2,
                'critical': 3,
                'unknown': 4
            }[status]
            
            # 1. Overall status (calculated from multiple factors)
            self.send_metric('security.device.status', status_value, tags, hostname)
            
            # 2. Flakiness score (0.0-1.0 scale)
            self.send_metric('security.device.flakiness', flakiness_score, tags, hostname)

            # 3. Time measurement (standardized to days for both tools)
            if device.get('LastSeen'):
                now = datetime.now(pytz.UTC)
                last_seen = datetime.fromisoformat(device['LastSeen']).replace(tzinfo=pytz.UTC)
                days_since_checkin = (now - last_seen).days
                self.send_metric('security.device.days_since_checkin', days_since_checkin, tags, hostname)

        except Exception as e:
            logger.error(f"Error processing AirWatch device {device.get('Uuid', 'unknown')}: {str(e)}") 