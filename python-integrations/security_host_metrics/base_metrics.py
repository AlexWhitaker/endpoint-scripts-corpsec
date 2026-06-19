from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.metrics_api import MetricsApi
from datadog_api_client.v2.model.metric_intake_type import MetricIntakeType
from datadog_api_client.v2.model.metric_payload import MetricPayload
from datadog_api_client.v2.model.metric_point import MetricPoint
from datadog_api_client.v2.model.metric_resource import MetricResource
from datadog_api_client.v2.model.metric_series import MetricSeries
from datetime import datetime
from typing import Dict, Any, List
import pytz
import logging
from config import DATADOG_API_KEY, DATADOG_SITE

logger = logging.getLogger("security-metrics-base")

class BaseDeviceMetrics:
    def __init__(self):
        configuration = Configuration()
        configuration.api_key['apiKeyAuth'] = DATADOG_API_KEY
        configuration.server_variables["site"] = DATADOG_SITE
        self.api_client = ApiClient(configuration)
        self.metrics_api = MetricsApi(self.api_client)

    def send_metric(self, metric_name: str, value: float, tags: List[str], hostname: str) -> None:
        """Common method for sending metrics to Datadog"""
        try:
            series = MetricSeries(
                metric=metric_name,
                type=MetricIntakeType.GAUGE,
                points=[MetricPoint(timestamp=int(datetime.now().timestamp()), value=value)],
                resources=[MetricResource(name=hostname, type="host")],
                tags=tags
            )
            payload = MetricPayload(series=[series])
            self.metrics_api.submit_metrics(body=payload)
        except Exception as e:
            logger.error(f"Error sending metric {metric_name}: {str(e)}")