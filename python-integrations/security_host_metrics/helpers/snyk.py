import os
from enum import Enum
from typing import Dict, List
from helpers.datadog import log_to_datadog, LogLevel

import snyk as pysnyk

TOKEN = os.environ["SNYK_TOKEN"]
GITLAB_TOKEN = os.environ["GITLAB_TOKEN"]
GITLAB_URL = os.environ["GITLAB_URL"]

CLIENT = pysnyk.SnykClient(TOKEN)

REST_API_VERSION = "2024-02-28"
REST_API_ENDPOINT = "https://api.snyk.io/rest"
REST_CLIENT = pysnyk.SnykClient(TOKEN, version=REST_API_VERSION, url=REST_API_ENDPOINT)


class Org(str, Enum):
    GROUP_A = "group-a"
    GROUP_B = "group-b"
    GROUP_C = "group-c"
    GROUP_D = "group-d"
    GROUP_E = "group-e"
    GROUP_F = "group-f"


ORG_IDS: Dict[str, str] = {
    Org.GROUP_A: os.environ["SNYK_ORG_ID_GROUP_A"],
    Org.GROUP_B: os.environ["SNYK_ORG_ID_GROUP_B"],
    Org.GROUP_C: os.environ["SNYK_ORG_ID_GROUP_C"],
    Org.GROUP_D: os.environ["SNYK_ORG_ID_GROUP_D"],
    Org.GROUP_E: os.environ["SNYK_ORG_ID_GROUP_E"],
    Org.GROUP_F: os.environ["SNYK_ORG_ID_GROUP_F"],
}

DEFAULT_ORG = Org.GROUP_A

REPO_GROUP_MAP: Dict[str, Org] = {
    # Map GitLab repo group prefixes to Snyk orgs.
    # Keys are the first path component of the repo (e.g. "platform" in "platform/my-service").
    # Add entries here for each GitLab group in your organization.
}

GITLAB_INTEGRATION_NAME = "gitlab"


def get_group_for_repo(repo: str) -> str:
    return repo.split("/")[0].lower()


def snyk_org_id_for_repo(repo: str) -> str:
    # Ensure consistency by converting the repo to lowercase
    repo = repo.lower()

    # Extract the group name from the full repo string
    group = get_group_for_repo(repo)
    if not group:
        raise ValueError(f"Invalid repo: {repo}")

    # Look up the group in REPO_GROUP_MAP; fall back to DEFAULT_ORG
    org = REPO_GROUP_MAP.get(group)
    if org is None:
        log_to_datadog(
            LogLevel.WARN,
            "Unknown repo group for Snyk; falling back to default",
            {"repo": repo, "default_org": DEFAULT_ORG},
        )
        return ORG_IDS[DEFAULT_ORG]
    return ORG_IDS[org]


def fetch_all_targets_from_snyk() -> List[str]:
    targets: List[str] = []

    for org_id in ORG_IDS.values():
        params = {"exclude_empty": False}
        org_targets = REST_CLIENT.get_rest_pages(f"orgs/{org_id}/targets", params=params)

        if org_targets is None or len(org_targets) == 0:
            raise Exception(f"Unable to fetch targets from Snyk for {org_id}")

        log_to_datadog(
            LogLevel.INFO,
            "Fetched targets from Snyk",
            {"org_id": org_id, "num_targets": len(org_targets)},
        )

        for target in org_targets:
            display_name = target.get("attributes").get("display_name")
            if display_name is None:
                raise Exception(f"Unable to fetch display name for target: {target['id']}")

            # Ensure we have consistency by downcasing the display_name
            targets.append(display_name.lower())

    return targets


def get_gitlab_integration_id_for_org(org_id: str) -> str:
    # Snyk has an integration for each organization, instead of one global one.
    #
    # To figure out the integration ID, we need to get the organization ID for the repo and then filter on the
    # available integrations to find the GitLab one.
    snyk_org = CLIENT.organizations.get(org_id)
    all_integrations = snyk_org.integrations.all()
    gitlab_integrations = [
        integration for integration in all_integrations if integration.name == GITLAB_INTEGRATION_NAME
    ]

    if gitlab_integrations is None or len(gitlab_integrations) == 0:
        log_to_datadog(
            LogLevel.ERROR,
            "No GitLab integrations found for Snyk org",
            {
                "org_id": org_id,
                "integrations": [[integration.name, integration.id] for integration in all_integrations],
            },
        )
        raise Exception(f"No GitLab integrations found for Snyk org: {org_id}")

    if len(gitlab_integrations) > 1:
        # While this is unexpected, it shouldn't block us from proceeding.
        log_to_datadog(
            LogLevel.WARN,
            "Multiple GitLab integrations found for Snyk org",
            {
                "org_id": org_id,
                "gitlab_integrations": [integration.id for integration in gitlab_integrations],
            },
        )

    return gitlab_integrations[0].id


def _fetch_gitlab_project(repo: str) -> dict:
    import urllib.parse
    import requests as _requests
    encoded = urllib.parse.quote(repo, safe="")
    resp = _requests.get(
        f"{GITLAB_URL}/api/v4/projects/{encoded}",
        headers={"PRIVATE-TOKEN": GITLAB_TOKEN},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def import_repo_into_snyk(repo: str) -> bool:
    org_id = snyk_org_id_for_repo(repo)
    gitlab_integration_id = get_gitlab_integration_id_for_org(org_id)
    gitlab_project = _fetch_gitlab_project(repo)

    request = {
        "target": {
            "id": gitlab_project["id"],
            "branch": gitlab_project["default_branch"],
        }
    }

    response = CLIENT.post(f"org/{org_id}/integrations/{gitlab_integration_id}/import", request)

    if response is None or response.status_code != 201:
        log_to_datadog(
            LogLevel.ERROR,
            "Unable to import repo into Snyk",
            {
                "repo": repo,
                "org_id": org_id,
                "gitlab_integration_id": gitlab_integration_id,
            },
        )
        raise Exception(f"Unable to import repo into Snyk: {repo}")

    log_to_datadog(
        LogLevel.INFO,
        "Imported repo into Snyk",
        {
            "repo": repo,
            "org_id": org_id,
            "gitlab_integration_id": gitlab_integration_id,
            "import_status": response.headers.get("Location"),
        },
    )
    return True
