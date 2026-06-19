from datetime import datetime
import pytz
from typing import Dict, Any, List
import logging
from base_metrics import BaseDeviceMetrics

logger = logging.getLogger("kandji-metrics")

class KandjiMetrics(BaseDeviceMetrics):
    def calculate_status(self, device: Dict[str, Any]) -> tuple[str, float]:
        """Calculate Kandji device status and flakiness score"""
        try:
            if not device.get('last_checkin'):
                return 'critical', 1.0

            now = datetime.now(pytz.UTC)
            last_checkin = datetime.fromisoformat(device['last_checkin'])
            days_since_checkin = (now - last_checkin).days

            # Calculate flakiness based on MDM status and check-in time
            flakiness_score = 0.0
            if not device.get('mdm_enabled'):
                flakiness_score += 0.4
            if not device.get('agent_installed'):
                flakiness_score += 0.3
            if days_since_checkin >= 3:
                flakiness_score += 0.3

            # Cap flakiness at 1.0
            flakiness_score = min(flakiness_score, 1.0)

            # Determine status based on device state
            if (device.get('mdm_enabled') and 
                device.get('agent_installed') and 
                days_since_checkin < 2):
                return 'healthy', flakiness_score
            elif (device.get('mdm_enabled') and 
                  device.get('agent_installed') and 
                  days_since_checkin < 3):
                return 'degrading', flakiness_score
            elif (not device.get('mdm_enabled') or 
                  not device.get('agent_installed')):
                return 'warning', flakiness_score
            elif days_since_checkin >= 3:
                return 'critical', flakiness_score

            return 'unknown', flakiness_score

        except Exception as e:
            logger.error(f"Error calculating Kandji status: {str(e)}")
            return 'unknown', 1.0

    def get_tags(self, device: Dict[str, Any]) -> List[str]:
        """Get Kandji-specific tags"""
        tags = ['tool:kandji_host', 'env:mgmt']
        
        # Device identifiers
        if device.get('device_id'):
            tags.append(f'device_id:{device["device_id"]}')
        if device.get('device__name'):
            tags.append(f'hostname:{device["device__name"]}')
        if device.get('serial_number'):
            tags.append(f'serial:{device["serial_number"]}')

        # Device information
        if device.get('device__family'):
            tags.append(f'device_family:{device["device__family"]}')
        if device.get('model'):
            tags.append(f'model:{device["model"]}')
        if device.get('model_name'):
            tags.append(f'model_name:{device["model_name"]}')

        # OS information
        if device.get('os_version'):
            tags.append(f'os_version:{device["os_version"]}')
        if device.get('marketing_name'):
            tags.append(f'os_name:{device["marketing_name"]}')
        if device.get('agent_version'):
            tags.append(f'agent_version:{device["agent_version"]}')

        # MDM status
        if device.get('mdm_enabled') is not None:
            tags.append(f'mdm_enabled:{str(device["mdm_enabled"]).lower()}')
        if device.get('agent_installed') is not None:
            tags.append(f'agent_installed:{str(device["agent_installed"]).lower()}')

        return tags

    def process_device(self, device: Dict[str, Any]) -> None:
        """Process a single Kandji device"""
        try:
            hostname = device.get('device__name', 'unknown')
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
            if device.get('last_checkin'):
                last_checkin = datetime.fromisoformat(device['last_checkin'])
                days_since_checkin = (datetime.now(pytz.UTC) - last_checkin).days
                self.send_metric('security.device.days_since_checkin', days_since_checkin, tags, hostname)

        except Exception as e:
            logger.error(f"Error processing Kandji device {device.get('device_id', 'unknown')}: {str(e)}") 