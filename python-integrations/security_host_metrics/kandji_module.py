import requests
from typing import Dict, Any, List
import logging
from config import KANDJI_API_TOKEN, KANDJI_API_URL, LIMIT

logger = logging.getLogger("kandji-module")

def get_kandji_devices() -> List[Dict[str, Any]]:
    """Get all Kandji devices"""
    offset = 0
    all_devices = []
    headers = {"Authorization": f"Bearer {KANDJI_API_TOKEN}"}
    
    logger.info("Fetching devices from Kandji...")
    while True:
        try:
            response = requests.get(
                KANDJI_API_URL,
                headers=headers,
                params={"limit": LIMIT, "offset": offset}
            )
            response.raise_for_status()
            
            data = response.json()
            devices = data.get("data", [])
            if not devices:
                break
                
            all_devices.extend(devices)
            logger.info(f"Retrieved {len(devices)} devices")
            
            if len(devices) < LIMIT:
                break
                
            offset += LIMIT
            
        except Exception as e:
            logger.error(f"Error fetching Kandji devices: {str(e)}")
            break
    
    logger.info(f"Total Kandji devices retrieved: {len(all_devices)}")
    return all_devices 