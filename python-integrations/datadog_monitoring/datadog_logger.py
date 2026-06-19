import json
import requests
import logging
import os

class DatadogLogger:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://http-intake.logs.datadoghq.com/api/v2/logs"
        self.headers = {
            'Content-Type': 'application/json',
            'DD-API-KEY': self.api_key
        }

    def send_log(self, log, ddsource="default_source", ddtags="default:tags", hostname="default_hostname", service="default_service"):
        payload = {
            "ddsource": ddsource,
            "ddtags": ddtags,
            "hostname": hostname,
            "service": service,
            "message": json.dumps(log)
        }
        response = requests.post(self.api_url, headers=self.headers, data=json.dumps(payload))
        if response.status_code != 202:
            logging.error(f"Failed to send data to Datadog: {response.status_code} {response.text}")
        else:
            logging.info(f"Data sent to Datadog successfully: {response.status_code}")

# Example usage
if __name__ == "__main__":
    DATADOG_API_KEY = os.environ["DATADOG_API_KEY"]
    logger = DatadogLogger(DATADOG_API_KEY)
    
    log_data = {"example_key": "example_value"}
    logger.send_log(log_data, ddsource="custom_source", ddtags="env:prod,source:app", hostname="custom_hostname", service="custom_service")

