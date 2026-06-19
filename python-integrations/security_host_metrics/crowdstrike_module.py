from typing import List, Dict, Any
import requests
from datetime import datetime
import pytz
import logging
from config import CROWDSTRIKE_CLIENT_ID, CROWDSTRIKE_CLIENT_SECRET, CROWDSTRIKE_BASE_URL

logger = logging.getLogger("crowdstrike-module")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class CrowdstrikeAPI:
    def __init__(self):
        self.base_url = CROWDSTRIKE_BASE_URL
        self.access_token = self._get_access_token()

    def _get_access_token(self) -> str:
        """Get OAuth2 access token from Crowdstrike"""
        try:
            auth_url = f"{self.base_url}/oauth2/token"
            response = requests.post(
                auth_url,
                data={
                    "client_id": CROWDSTRIKE_CLIENT_ID,
                    "client_secret": CROWDSTRIKE_CLIENT_SECRET,
                    "grant_type": "client_credentials"
                }
            )
            response.raise_for_status()
            return response.json()["access_token"]
        except Exception as e:
            logger.error(f"Failed to get Crowdstrike access token: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    def get_devices(self) -> List[Dict[str, Any]]:
        """Fetch all devices from Crowdstrike API with their last check-in times"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            }
            
            # Get all device IDs with pagination
            all_device_ids = []
            offset = ""
            limit = 5000  # Maximum allowed by Crowdstrike API
            
            while True:
                devices_url = f"{self.base_url}/devices/queries/devices/v1"
                params = {"limit": limit}
                if offset:
                    params["offset"] = offset
                    
                response = requests.get(devices_url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                device_ids = data.get("resources", [])
                all_device_ids.extend(device_ids)
                
                # Check if there are more pages
                offset = data.get("meta", {}).get("pagination", {}).get("offset")
                if not offset or not device_ids:
                    break

            if not all_device_ids:
                logger.warning("No devices found in Crowdstrike")
                return []

            logger.info(f"Found total of {len(all_device_ids)} device IDs")

            # Get device details in batches of 100
            all_devices = []
            batch_size = 100
            
            for i in range(0, len(all_device_ids), batch_size):
                batch_ids = all_device_ids[i:i + batch_size]
                details_url = f"{self.base_url}/devices/entities/devices/v1"
                response = requests.get(
                    details_url,
                    headers=headers,
                    params={"ids": batch_ids}
                )
                response.raise_for_status()
                
                devices = response.json().get("resources", [])
                for device in devices:
                    processed_device = {
                        "device_id": device.get("device_id"),
                        "hostname": device.get("hostname"),
                        "last_seen": device.get("last_seen"),
                        "os_type": device.get("platform_name"),
                        "device_type": device.get("system_product_name", "unknown"),
                        "status": device.get("status")
                    }
                    all_devices.append(processed_device)

                logger.info(f"Processed batch of {len(devices)} devices. Total so far: {len(all_devices)}")

            return all_devices

        except Exception as e:
            logger.error(f"Error fetching Crowdstrike devices: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return []

def get_crowdstrike_devices() -> List[Dict[str, Any]]:
    """Main function to get Crowdstrike devices with their health status"""
    try:
        cs_api = CrowdstrikeAPI()
        devices = cs_api.get_devices()
        
        if not devices:
            logger.warning("No devices returned from Crowdstrike API")
            return []
            
        logger.info(f"Successfully fetched {len(devices)} devices from Crowdstrike")
        return devices
        
    except Exception as e:
        logger.error(f"Failed to get Crowdstrike devices: {str(e)}")
        return [] 