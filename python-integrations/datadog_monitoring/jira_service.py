from jira import JIRA
import os
from datadog_monitor import Change, ChangeType
import logging

logger = logging.getLogger("jira-monitor")

JIRA_SERVER = os.environ["JIRA_SERVER"]
PROJECT_KEY = os.environ["JIRA_PROJECT_KEY"]
ISSUE_TYPE = os.environ.get("JIRA_ISSUE_TYPE", "Task")
USERNAME = os.environ["JIRA_USERNAME"]
JIRA_API_KEY = os.environ["JIRA_API_KEY"]


class JiraTicketCreator:
    def __init__(self):
        if not JIRA_API_KEY:
            raise ValueError("JIRA_API_KEY environment variable is required")

        self.jira = JIRA(
            server=JIRA_SERVER,
            basic_auth=(USERNAME, JIRA_API_KEY)
        )

    def create_ticket(self, change: Change) -> str:
        """Create a Jira ticket for a detected change."""
        summary = f"Security Log Restriction Change Detected - {change.type}"
        description = self._format_description(change)

        issue_dict = {
            'project': {'key': PROJECT_KEY},
            'summary': summary,
            'description': description,
            'issuetype': {'name': ISSUE_TYPE},
            'labels': ['security', 'log-restriction-change']
        }

        new_issue = self.jira.create_issue(fields=issue_dict)
        logger.info(f"Created Jira ticket: {new_issue.key}")
        return f"{JIRA_SERVER}/browse/{new_issue.key}"

    def _format_description(self, change: Change) -> str:
        """Format the Jira ticket description."""
        sections = [
            "h2. Security Log Restriction Change Detected",
            "",
            f"*Change Type:* {change.type}",
            f"*Timestamp:* {change.timestamp}",
            "",
            "h3. Details"
        ]

        if change.type == ChangeType.QUERY_MODIFIED.value:
            sections.extend([
                "",
                "*Previous Query:*",
                "{noformat}",
                change.previous_query,
                "{noformat}",
                "",
                "*New Query:*",
                "{noformat}",
                change.new_query,
                "{noformat}",
                "",
                f"*Affected Roles:* {', '.join(change.roles or [])}"
            ])
        elif change.type == ChangeType.ROLES_MODIFIED.value:
            sections.extend([
                "",
                "*Query:*",
                "{noformat}",
                change.query,
                "{noformat}",
                "",
                f"*Previous Roles:* {', '.join(change.previous_roles or [])}",
                f"*New Roles:* {', '.join(change.new_roles or [])}"
            ])
        else:
            sections.extend([
                "",
                "*Query:*",
                "{noformat}",
                change.query or "N/A",
                "{noformat}",
                "",
                f"*Roles:* {', '.join(change.roles or [])}"
            ])

        sections.extend([
            "",
            "h3. Action Required",
            "# Review the changes to ensure they are authorized",
            "# Verify that security team access is maintained where necessary",
            "# Update documentation if needed"
        ])

        return "\n".join(sections)
