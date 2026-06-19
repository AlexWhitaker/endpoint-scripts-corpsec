import http.client
import json
import os
import time
import requests

KANDJI_SUBDOMAIN = os.environ["KANDJI_SUBDOMAIN"]
KANDJI_API_TOKEN = os.environ["KANDJI_API_TOKEN"]
KANDJI_API_URL = f"https://{KANDJI_SUBDOMAIN}.api.kandji.io/api/v1/prism/device_information"

DATADOG_API_KEY = os.environ["DATADOG_API_KEY"]
DATADOG_LOGS_API_URL = "https://http-intake.logs.datadoghq.com/api/v2/logs"


def fetch_kandji_data():
    conn = http.client.HTTPSConnection(f"{KANDJI_SUBDOMAIN}.api.kandji.io")
    headers = {
        'Authorization': f'Bearer {KANDJI_API_TOKEN}'
    }
    conn.request("GET", "/api/v1/prism/device_information", '', headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))


def send_to_datadog(logs):
    headers = {
        'Content-Type': 'application/json',
        'DD-API-KEY': DATADOG_API_KEY
    }
    payload = {
        "ddsource": "kandji",
        "ddtags": "env:production,source:kandji",
        "hostname": "kandji-host",
        "service": "kandji_service",
        "message": json.dumps(logs)
    }
    response = requests.post(DATADOG_LOGS_API_URL, headers=headers, data=json.dumps([payload]))
    if response.status_code != 202:
        print(f"Failed to send data to Datadog: {response.status_code} {response.text}")
    else:
        print(f"Data sent to Datadog successfully: {response.status_code}")


def main():
    while True:
        data = fetch_kandji_data()
        send_to_datadog(data)
        time.sleep(60)


if __name__ == "__main__":
    main()
