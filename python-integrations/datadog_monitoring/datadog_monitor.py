import os
import requests
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger("datadog-restriction-monitor")


class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"


class ChangeType(Enum):
    INITIAL_STATE = "initial_state"
    NEW_RESTRICTION = "new_restriction"
    QUERY_MODIFIED = "query_modified"
    ROLES_MODIFIED = "roles_modified"
    RESTRICTION_REMOVED = "restriction_removed"


@dataclass
class Change:
    type: str
    severity: str
    timestamp: str
    query: Optional[str] = None
    roles: Optional[List[str]] = None
    previous_query: Optional[str] = None
    previous_roles: Optional[List[str]] = None
    new_query: Optional[str] = None
    new_roles: Optional[List[str]] = None


class DatadogAPIError(Exception):
    """Custom exception for Datadog API errors."""
    pass


class StateFileError(Exception):
    """Custom exception for state file operations."""
    pass


class RestrictionMonitor:
    def __init__(
            self,
            api_key: str,
            app_key: str,
            api_host: str = "https://api.datadoghq.com",
            state_file: str = "restriction_state.json"
    ):
        if not api_key or not app_key:
            raise ValueError("API key and Application key are required")

        self.api_key = api_key
        self.app_key = app_key
        self.api_host = api_host.rstrip('/')
        self.headers = {
            "Content-Type": "application/json",
            "DD-API-KEY": self.api_key,
            "DD-APPLICATION-KEY": self.app_key
        }
        self.state_file = Path(state_file)
        self.critical_sources = frozenset({"crowdstrike", "cisco-duo"})
        self.security_role = os.environ.get("SECURITY_ROLE_NAME", "Security")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request to Datadog API with error handling."""
        url = f"{self.api_host}{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Datadog API request failed: {str(e)}"
            logger.error(error_msg)
            raise DatadogAPIError(error_msg) from e

    def get_restriction_state(self) -> Dict:
        """Get current state of all restriction queries and their roles."""
        logger.info("Fetching current restriction state from Datadog")
        data = self._make_request("GET", "/api/v2/logs/config/restriction_queries")

        state = {}
        for restriction in data.get('data', []):
            restriction_id = restriction['id']
            restriction_data = restriction['attributes']

            roles_data = self._make_request(
                "GET",
                f"/api/v2/logs/config/restriction_queries/{restriction_id}/roles"
            )
            roles = [role['attributes']['name'] for role in roles_data.get('data', [])]

            state[restriction_id] = {
                'query': restriction_data['restriction_query'],
                'roles': roles,
                'modified_at': restriction_data.get('modified_at'),
                'created_at': restriction_data.get('created_at')
            }

        return state

    def load_previous_state(self) -> Optional[Dict]:
        """Load the previous state from file."""
        try:
            if self.state_file.exists():
                logger.info(f"Loading previous state from {self.state_file}")
                with open(self.state_file, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            error_msg = f"Failed to load previous state: {str(e)}"
            logger.error(error_msg)
            raise StateFileError(error_msg) from e

        logger.info("No previous state file found")
        return None

    def save_current_state(self, state: Dict) -> None:
        """Save the current state to file."""
        try:
            logger.info(f"Saving current state to {self.state_file}")
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except (json.JSONEncodeError, OSError) as e:
            error_msg = f"Failed to save current state: {str(e)}"
            logger.error(error_msg)
            raise StateFileError(error_msg) from e

    def analyze_changes(self, previous_state: Optional[Dict], current_state: Dict) -> List[Change]:
        """Analyze changes between states."""
        logger.info("Analyzing changes in restriction states")
        changes = []

        if not previous_state:
            return [
                Change(
                    type=ChangeType.INITIAL_STATE.value,
                    query=data['query'],
                    roles=data['roles'],
                    timestamp=data['modified_at'],
                    severity=self._determine_severity(data).value
                )
                for restriction_id, data in current_state.items()
                if self._is_security_critical(data['query'])
            ]

        for restriction_id, current_data in current_state.items():
            if not self._is_security_critical(current_data['query']):
                continue

            if restriction_id not in previous_state:
                changes.append(Change(
                    type=ChangeType.NEW_RESTRICTION.value,
                    query=current_data['query'],
                    roles=current_data['roles'],
                    timestamp=current_data['created_at'],
                    severity=self._determine_severity(current_data).value
                ))
                continue

            previous_data = previous_state[restriction_id]

            if current_data['query'] != previous_data['query']:
                changes.append(Change(
                    type=ChangeType.QUERY_MODIFIED.value,
                    previous_query=previous_data['query'],
                    new_query=current_data['query'],
                    roles=current_data['roles'],
                    timestamp=current_data['modified_at'],
                    severity=self._determine_severity(current_data).value
                ))

            if set(current_data['roles']) != set(previous_data['roles']):
                changes.append(Change(
                    type=ChangeType.ROLES_MODIFIED.value,
                    query=current_data['query'],
                    previous_roles=previous_data['roles'],
                    new_roles=current_data['roles'],
                    timestamp=current_data['modified_at'],
                    severity=self._determine_severity(current_data).value
                ))

        for restriction_id, previous_data in previous_state.items():
            if (restriction_id not in current_state and
                    self._is_security_critical(previous_data['query'])):
                changes.append(Change(
                    type=ChangeType.RESTRICTION_REMOVED.value,
                    query=previous_data['query'],
                    previous_roles=previous_data['roles'],
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    severity=Severity.CRITICAL.value
                ))

        return changes

    def _is_security_critical(self, query: str) -> bool:
        """Check if a query is security-critical."""
        query_lower = query.lower()
        return any(source in query_lower for source in self.critical_sources)

    def _determine_severity(self, data: Dict) -> Severity:
        """Determine the severity of a change based on security implications."""
        query = data['query'].lower()
        roles = set(data['roles'])

        if any(source in query for source in self.critical_sources):
            if self.security_role in roles:
                return Severity.HIGH if len(roles) > 1 else Severity.MEDIUM
            return Severity.CRITICAL

        return Severity.MEDIUM

    def send_to_datadog(self, changes: List[Change]) -> None:
        """Send change events to Datadog."""
        if not changes:
            logger.info("No changes to send to Datadog")
            return

        logger.info(f"Sending {len(changes)} changes to Datadog")
        for change in changes:
            event_title = f"Log Restriction Change - {change.type}"
            alert_type = 'error' if change.severity in [Severity.CRITICAL.value, Severity.HIGH.value] else 'warning'

            event_text = self._format_event_text(change)

            event_data = {
                'title': event_title,
                'text': event_text,
                'alert_type': alert_type,
                'source_type_name': 'LOG_RESTRICTION_MONITOR',
                'tags': [
                    f'severity:{change.severity}',
                    f'change_type:{change.type}',
                    'security:log_restrictions'
                ]
            }

            self._make_request("POST", "/api/v1/events", json=event_data)

    @staticmethod
    def _format_event_text(change: Change) -> str:
        """Format event text based on change type."""
        text_parts = [f"Severity: {change.severity}"]

        if change.type == ChangeType.QUERY_MODIFIED.value:
            text_parts.extend([
                f"Previous query: {change.previous_query}",
                f"New query: {change.new_query}",
                f"Affected roles: {', '.join(change.roles or [])}"
            ])
        elif change.type == ChangeType.ROLES_MODIFIED.value:
            text_parts.extend([
                f"Query: {change.query}",
                f"Previous roles: {', '.join(change.previous_roles or [])}",
                f"New roles: {', '.join(change.new_roles or [])}"
            ])
        else:
            text_parts.extend([
                f"Query: {change.query or 'N/A'}",
                f"Roles: {', '.join(change.roles or [])}"
            ])

        return "\n".join(text_parts)