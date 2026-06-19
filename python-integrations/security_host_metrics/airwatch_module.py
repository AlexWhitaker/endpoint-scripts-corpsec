import requests
from typing import Dict, Any, List
import logging
from config import AIRWATCH_CLIENT_ID, AIRWATCH_CLIENT_SECRET, ACCESS_TOKEN_URL, AIRWATCH_URL

logger = logging.getLogger("airwatch-module")

def get_airwatch_devices() -> List[Dict[str, Any]]:
    """Get all AirWatch devices"""
    try:
        # Get access token
        payload = {
            "client_id": AIRWATCH_CLIENT_ID,
            "grant_type": "client_credentials",
            "client_secret": AIRWATCH_CLIENT_SECRET,
        }
        token_response = requests.post(ACCESS_TOKEN_URL, data=payload)
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]

        # Get devices
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        response = requests.get(f"{AIRWATCH_URL}/api/mdm/devices/search", headers=headers)
        response.raise_for_status()
        
        devices = response.json().get("Devices", [])
        logger.info(f"Retrieved {len(devices)} AirWatch devices")
        return devices

    except Exception as e:
        logger.error(f"Error fetching AirWatch devices: {str(e)}")
        return [] 