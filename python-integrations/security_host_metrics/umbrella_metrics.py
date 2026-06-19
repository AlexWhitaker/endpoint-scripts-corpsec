from datetime import datetime
import pytz
from typing import Dict, Any, List
import logging
from base_metrics import BaseDeviceMetrics

logger = logging.getLogger("umbrella-metrics")

class UmbrellaMetrics(BaseDeviceMetrics):
    def calculate_status(self, device: Dict[str, Any]) -> tuple[str, float]:
        """Calculate Umbrella device status and flakiness score"""
        try:
            if not device.get('lastSync'):
                return 'critical', 1.0

            now = datetime.now(pytz.UTC)
            last_sync = datetime.fromisoformat(device['lastSync'].replace('Z', '+00:00'))
            hours_since_sync = (now - last_sync).total_seconds() / 3600
            
            status = device.get('status', 'Unknown')
            sync_status = device.get('lastSyncStatus', 'Unknown')

            # Calculate flakiness based on status combinations
            flakiness_score = 0.0
            if status == 'Off' or sync_status == 'Off':
                flakiness_score += 0.3
            if hours_since_sync >= 24:
                flakiness_score += 0.3
            if sync_status in ['Uninstalled', 'Open']:
                flakiness_score += 0.4
            
            # Cap flakiness at 1.0
            flakiness_score = min(flakiness_score, 1.0)

            # Healthy: Encrypted and recently synced
            if (status == 'Encrypted' and 
                sync_status == 'Encrypted' and 
                hours_since_sync < 2):
                return 'healthy', flakiness_score

            # Degrading: Still working but not optimal
            elif ((status == 'Open' and sync_status == 'Open') or
                  (status == 'Transparent' and sync_status == 'Transparent') or
                  (status == 'Encrypted' and hours_since_sync >= 2 and hours_since_sync < 24)):
                return 'degrading', flakiness_score

            # Warning: Off but recently synced
            elif (status == 'Off' and 
                  sync_status in ['Encrypted', 'Off'] and 
                  hours_since_sync < 24):
                return 'warning', flakiness_score

            # Critical: Various bad states
            elif (hours_since_sync >= 24 or
                  sync_status in ['Uninstalled', 'Open'] or
                  (status == 'Off' and sync_status == 'Off' and hours_since_sync >= 24)):
                return 'critical', flakiness_score

            return 'unknown', flakiness_score

        except Exception as e:
            logger.error(f"Error calculating Umbrella status: {str(e)}")
            return 'unknown', 1.0

    def get_tags(self, device: Dict[str, Any]) -> List[str]:
        """Get Umbrella-specific tags"""
        tags = ['tool:umbrella_host', 'env:mgmt']
        
        # Device identifiers
        if device.get('originId'):
            tags.append(f'origin_id:{device["originId"]}')
        if device.get('deviceId'):
            tags.append(f'device_id:{device["deviceId"]}')
        if device.get('name'):
            tags.append(f'hostname:{device["name"]}')
        if device.get('anyconnectDeviceId'):
            tags.append(f'anyconnect_id:{device["anyconnectDeviceId"]}')
        
        # Type and Status information
        if device.get('type'):
            tags.append(f'client_type:{device["type"]}')
        if device.get('status'):
            tags.append(f'umbrella_status:{device["status"]}')
        if device.get('lastSyncStatus'):
            tags.append(f'sync_status:{device["lastSyncStatus"]}')
        
        # Version and OS information
        if device.get('version'):
            tags.append(f'client_version:{device["version"]}')
        if device.get('osVersion'):
            tags.append(f'os_version:{device["osVersion"]}')
        if device.get('osVersionName'):
            tags.append(f'os_name:{device["osVersionName"]}')
        
        # Configuration
        if device.get('hasIpBlocking') is not None:
            tags.append(f'ip_blocking:{str(device["hasIpBlocking"]).lower()}')
        if device.get('appliedBundle'):
            tags.append(f'bundle_id:{device["appliedBundle"]}')

        return tags

    def process_device(self, device: Dict[str, Any]) -> None:
        """Process a single Umbrella device"""
        try:
            hostname = device.get('name', 'unknown')
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
            if device.get('lastSync'):
                last_sync = datetime.fromisoformat(device['lastSync'].replace('Z', '+00:00'))
                days_since_sync = (datetime.now(pytz.UTC) - last_sync).total_seconds() / 86400
                self.send_metric('security.device.days_since_checkin', days_since_sync, tags, hostname)

        except Exception as e:
            logger.error(f"Error processing Umbrella device {device.get('deviceId', 'unknown')}: {str(e)}") 