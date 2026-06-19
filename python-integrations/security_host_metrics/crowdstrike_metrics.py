from datetime import datetime
import pytz
from typing import Dict, Any, List
import logging
from base_metrics import BaseDeviceMetrics

logger = logging.getLogger("crowdstrike-metrics")

class CrowdstrikeMetrics(BaseDeviceMetrics):
    def calculate_status(self, device: Dict[str, Any]) -> tuple[str, float]:
        """Calculate Crowdstrike device status"""
        try:
            if not device.get('last_seen'):
                return 'critical', 1.0

            now = datetime.now(pytz.UTC)
            check_in_date = datetime.fromisoformat(device['last_seen'].replace('Z', '+00:00'))
            days_since_check_in = (now - check_in_date).days
            
            device_status = device.get('status')
            
            # Calculate status based on check-in time and device status
            if days_since_check_in < 3 and device_status == "normal":
                return 'healthy', 0.0
            elif days_since_check_in < 3 and device_status != "normal":
                return 'degrading', 0.3
            elif days_since_check_in >= 3 and days_since_check_in < 7:
                return 'degrading', 0.6
            elif days_since_check_in >= 7 and days_since_check_in < 15:
                return 'warning', 0.8
            elif days_since_check_in >= 15:
                return 'critical', 1.0
            
            return 'unknown', 1.0

        except Exception as e:
            logger.error(f"Error calculating Crowdstrike status: {str(e)}")
            return 'unknown', 1.0

    def get_tags(self, device: Dict[str, Any]) -> List[str]:
        """Get Crowdstrike-specific tags"""
        tags = ['tool:crowdstrike_host', 'env:mgmt']
        
        # Device identifiers
        if device.get('device_id'):
            tags.append(f'device_id:{device["device_id"]}')
        if device.get('hostname'):
            tags.append(f'hostname:{device["hostname"]}')
        if device.get('serial_number'):
            tags.append(f'serial:{device["serial_number"]}')

        # System information
        if device.get('os_version'):
            tags.append(f'os_version:{device["os_version"]}')
        if device.get('platform_name'):
            tags.append(f'platform:{device["platform_name"]}')
        if device.get('agent_version'):
            tags.append(f'agent_version:{device["agent_version"]}')

        return tags

    def process_device(self, device: Dict[str, Any]) -> None:
        """Process a single Crowdstrike device"""
        try:
            hostname = device.get('hostname', 'unknown')
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
            if device.get('last_seen'):
                last_seen = datetime.fromisoformat(device['last_seen'].replace('Z', '+00:00'))
                days_since_checkin = (datetime.now(pytz.UTC) - last_seen).days
                self.send_metric('security.device.days_since_checkin', days_since_checkin, tags, hostname)

        except Exception as e:
            logger.error(f"Error processing Crowdstrike device {device.get('device_id', 'unknown')}: {str(e)}") 