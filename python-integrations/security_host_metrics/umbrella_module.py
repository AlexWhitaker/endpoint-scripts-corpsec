import requests
from typing import List, Dict, Any
import logging
from config import UMBRELLA_API_KEY, UMBRELLA_API_SECRET, UMBRELLA_TOKEN_ENDPOINT

logger = logging.getLogger("umbrella-module")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_umbrella_access_token() -> str:
    """Get OAuth2 access token from Umbrella"""
    try:
        response = requests.post(
            UMBRELLA_TOKEN_ENDPOINT,
            auth=(UMBRELLA_API_KEY, UMBRELLA_API_SECRET),
            data={"grant_type": "client_credentials"}
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        logger.error(f"Failed to get Umbrella access token: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response content: {e.response.text}")
        raise

def get_umbrella_devices() -> List[Dict[str, Any]]:
    """Get all Umbrella devices"""
    try:
        access_token = get_umbrella_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        api_endpoint = "https://api.umbrella.com/deployments/v2/roamingcomputers"
        page_number = 1
        all_devices = []
        
        while True:
            response = requests.get(
                api_endpoint, 
                params={"page": page_number, "limit": 100}, 
                headers=headers
            )
            response.raise_for_status()
            
            devices = response.json()
            if not devices:
                break
                
            all_devices.extend(devices)
            if len(devices) < 100:  # Less than limit means last page
                break
                
            page_number += 1
            
        logger.info(f"Successfully fetched {len(all_devices)} devices from Umbrella")
        return all_devices
        
    except Exception as e:
        logger.error(f"Failed to get Umbrella devices: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response content: {e.response.text}")
        return [] 