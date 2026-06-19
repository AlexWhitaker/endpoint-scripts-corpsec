import os
from typing import Dict, Any


def _require(var: str) -> str:
    value = os.environ.get(var)
    if not value:
        raise EnvironmentError(f"Required environment variable not set: {var}")
    return value


DATADOG_API_KEY = _require("DATADOG_API_KEY")
DATADOG_SITE = os.environ.get("DATADOG_SITE", "datadoghq.com")

CROWDSTRIKE_CLIENT_ID = _require("CROWDSTRIKE_CLIENT_ID")
CROWDSTRIKE_CLIENT_SECRET = _require("CROWDSTRIKE_CLIENT_SECRET")
CROWDSTRIKE_BASE_URL = os.environ.get("CROWDSTRIKE_BASE_URL", "https://api.us-2.crowdstrike.com")

UMBRELLA_ORG_ID = _require("UMBRELLA_ORG_ID")
UMBRELLA_API_KEY = _require("UMBRELLA_API_KEY")
UMBRELLA_API_SECRET = _require("UMBRELLA_API_SECRET")
UMBRELLA_BASE_URL = os.environ.get("UMBRELLA_BASE_URL", "https://api.umbrella.com/v1")
UMBRELLA_TOKEN_ENDPOINT = os.environ.get("UMBRELLA_TOKEN_ENDPOINT", "https://api.umbrella.com/auth/v2/token")

KANDJI_API_TOKEN = _require("KANDJI_API_TOKEN")
KANDJI_SUBDOMAIN = _require("KANDJI_SUBDOMAIN")
KANDJI_API_URL = f"https://{KANDJI_SUBDOMAIN}.api.kandji.io/api/v1/prism/device_information"
LIMIT = int(os.environ.get("KANDJI_PAGE_LIMIT", "100"))

AIRWATCH_CLIENT_ID = _require("AIRWATCH_CLIENT_ID")
AIRWATCH_CLIENT_SECRET = _require("AIRWATCH_CLIENT_SECRET")
ACCESS_TOKEN_URL = os.environ.get("AIRWATCH_TOKEN_URL", "https://na.uemauth.vmwservices.com/connect/token")
AIRWATCH_URL = _require("AIRWATCH_URL")

SERVICE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "crowdstrike": {
        "hostname_field": "hostname",
        "last_check_in_field": "last_seen",
        "service_name": "crowdstrike_host"
    },
    "umbrella": {
        "hostname_field": "name",
        "last_check_in_field": "lastSyncTime",
        "service_name": "umbrella_host"
    },
    "kandji": {
        "hostname_field": "device__name",
        "last_check_in_field": "last_checkin",
        "service_name": "kandji_host"
    },
    "airwatch": {
        "hostname_field": "DeviceFriendlyName",
        "last_check_in_field": "LastSeen",
        "service_name": "airwatch_host"
    }
}
