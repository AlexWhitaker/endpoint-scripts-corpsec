from typing import Dict, Any, List
import logging
from crowdstrike_metrics import CrowdstrikeMetrics
from umbrella_metrics import UmbrellaMetrics
from kandji_metrics import KandjiMetrics
from airwatch_metrics import AirWatchMetrics
from crowdstrike_module import get_crowdstrike_devices
from umbrella_module import get_umbrella_devices
from kandji_module import get_kandji_devices
from airwatch_module import get_airwatch_devices

logger = logging.getLogger("security-metrics-main")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main function to process all security tools"""
    try:
        # Initialize metrics processors
        crowdstrike = CrowdstrikeMetrics()
        umbrella = UmbrellaMetrics()
        kandji = KandjiMetrics()
        airwatch = AirWatchMetrics()
        
        # Process Crowdstrike devices
        logger.info("Fetching Crowdstrike devices...")
        crowdstrike_devices = get_crowdstrike_devices()
        if crowdstrike_devices:
            logger.info(f"Processing {len(crowdstrike_devices)} Crowdstrike devices")
            for device in crowdstrike_devices:
                crowdstrike.process_device(device)
        
        # Process Umbrella devices
        logger.info("Fetching Umbrella devices...")
        umbrella_devices = get_umbrella_devices()
        if umbrella_devices:
            logger.info(f"Processing {len(umbrella_devices)} Umbrella devices")
            for device in umbrella_devices:
                umbrella.process_device(device)

        # Process Kandji devices
        logger.info("Fetching Kandji devices...")
        kandji_devices = get_kandji_devices()
        if kandji_devices:
            logger.info(f"Processing {len(kandji_devices)} Kandji devices")
            for device in kandji_devices:
                kandji.process_device(device)

        # Process AirWatch devices
        logger.info("Fetching AirWatch devices...")
        airwatch_devices = get_airwatch_devices()
        if airwatch_devices:
            logger.info(f"Processing {len(airwatch_devices)} AirWatch devices")
            for device in airwatch_devices:
                airwatch.process_device(device)
        
        logger.info("Successfully processed all device metrics")
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")

if __name__ == "__main__":
    main()