import json
import logging
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.logs_api import LogsApi
from datadog_api_client.v2.model.http_log import HTTPLog
from datadog_api_client.v2.model.http_log_item import HTTPLogItem

class DatadogLogger:
    def __init__(self, api_key):
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = api_key
        self.api_client = ApiClient(configuration)
        self.api_instance = LogsApi(self.api_client)

    def send_log(
        self,
        log,
        ddsource="default_source",
        ddtags="default:tags",
        hostname="default_hostname",
        service="default_service",
    ):
        try:
            body = HTTPLog(
                [
                    HTTPLogItem(
                        ddsource=ddsource,
                        ddtags=ddtags,
                        hostname=hostname,
                        message=json.dumps(log),
                        service=service,
                    )
                ]
            )
            self.api_instance.submit_log(body=body)
        except Exception as e:
            logging.error(f"Failed to send data to Datadog: {e}", exc_info=True)