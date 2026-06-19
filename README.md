# endpoint-scripts-corpsec

macOS shell scripts and Python integrations for endpoint security tool deployment, health monitoring, and platform-to-Datadog pipelines. Covers Cisco Umbrella, CrowdStrike Falcon, Tenable Nessus, Kandji MDM, and AirWatch.

Scripts are designed to run in MDM-managed environments (Kandji, Jamf). Python integrations run as scheduled services or one-off analysis jobs.

---

## cisco-umbrella

Scripts for managing Cisco Umbrella (Secure Client) installation and validating agent health.

### `umbrella_uninstall.sh`

Gracefully removes all Cisco Secure Client modules in the correct dependency order: ISE Posture → ISE Compliance → Secure Firewall Posture → Umbrella → AMP Enabler → NVM → VPN. Quits the application before running any uninstaller to avoid partial-removal errors.

```bash
sudo sh cisco-umbrella/umbrella_uninstall.sh
```

### `dart_uninstall.sh`

Enterprise-grade DART (Diagnostics and Reporting Tool) component uninstaller. Features:
- Comprehensive audit log at `/var/log/secureclient/csc_dart_uninstall.log`
- Root privilege verification
- Graceful process termination
- macOS version-aware launchctl handling (10.11+ vs legacy)
- Authorization database cleanup
- Package receipt removal via `pkgutil`

```bash
sudo sh cisco-umbrella/dart_uninstall.sh
```

### `umbrella_full_test.sh`

Validates Umbrella installation by checking known install paths and verifying that all three expected processes (`UmbrellaAgent`, `LogUploader`, `DNSCryptProxy`) are running. Returns exit 0 on pass, exit 1 on failure.

```bash
sudo sh cisco-umbrella/umbrella_full_test.sh
```

### `umbrella_status.sh`

Quick status check using `pgrep` against the `OpenDNSConnector` process. Also invokes the Umbrella CLI tool if present.

```bash
sh cisco-umbrella/umbrella_status.sh
```

### `umbrella_audit.sh`

Deep validation: checks install paths, verifies three critical processes via `pgrep`, and confirms DNS encryption is active using `dig` against `debug.opendns.com`. Returns exit 0 on pass, exit 1 with descriptive message on failure.

```bash
sudo sh cisco-umbrella/umbrella_audit.sh
```

---

## crowdstrike

Scripts for inspecting CrowdStrike Falcon sensor health.

### `falcon_status.sh`

Returns the Falcon sensor connection state. Checks both legacy (`/Library/CS/falconctl`) and modern (`/Applications/Falcon.app`) installation paths, with a fallback to "Not Connected".

Output is wrapped in `<result>` tags for Jamf Extension Attribute compatibility.

```bash
sh crowdstrike/falcon_status.sh
```

### `falcon_last_seen.sh`

Reports the timestamp of the last successful cloud connection. Dynamically locates `falconctl` under `Falcon.app` using `find`, handles multiple output formats from different Falcon versions, and formats the timestamp as `YYYY-MM-DD HH:MM:SS`. Falls back to `1970-01-01 09:00:00` if the agent is absent or the timestamp is unavailable.

Output is wrapped in `<result>` tags for Jamf Extension Attribute compatibility.

```bash
zsh crowdstrike/falcon_last_seen.sh
```

---

## nessus

Scripts for Tenable Nessus Agent lifecycle management.

### `nessus_preinstall.sh`

Removes any existing Nessus Agent installation before a fresh install:
- Unlinks the agent from Tenable Cloud
- Removes the agent directory and launch daemon plist
- Removes the preference pane
- Unloads the launchd service

```bash
sudo sh nessus/nessus_preinstall.sh
```

### `nessus_postinstall.sh`

Installs a Nessus Agent from a DMG and links it to Tenable Cloud. Takes credentials via environment variables (no hardcoded values).

```bash
sudo TENABLE_LINKING_KEY=<key> NESSUS_DMG=NessusAgent-10.6.1.dmg \
    sh nessus/nessus_postinstall.sh
```

| Variable | Description |
|---|---|
| `TENABLE_LINKING_KEY` | Agent linking key from Tenable → Sensors |
| `NESSUS_DMG` | DMG filename placed in `/private/var/tmp/` |

### `nessus_audit_enforce.sh`

Compliance check that validates the Nessus Agent is installed, running, and linked to `sensor.cloud.tenable.com:443`. Returns exit 0 on pass. Set `force_reinstall=true` in the script to trigger a reinstall path.

```bash
sh nessus/nessus_audit_enforce.sh
```

---

## macos-utilities

General-purpose macOS endpoint management utilities.

### `super_removal.sh`

Completely removes the [Super](https://github.com/Macjutsu/super) macOS software update management tool. Handles both v3 and v4+ of Super with version-aware cleanup flags. Removes: LaunchDaemon, Super folder, symbolic link, PID file, mist-cli binary, and erase-install folder.

```bash
sudo sh macos-utilities/super_removal.sh
```

### `mail_backup.py`

Backs up macOS Mail messages to a timestamped directory without touching originals. Recursively scans `~/Library/Mail/V9` for `.mbox` files and exports individual messages as `.eml` files with a `metadata.json` per mailbox.

```bash
python macos-utilities/mail_backup.py
```

---

## python-integrations

Python integrations connecting enterprise security platforms to Datadog for unified device health monitoring, vulnerability management, and alert routing.

```
python-integrations/
├── security_host_metrics/     Multi-platform device health pipeline → Datadog
├── datadog_monitoring/        Log restriction monitor with Jira alerting
├── mdm_integrations/          Kandji and Umbrella data pipelines
├── vulnerability_management/  Nessus → Jira sync and agent deployment
├── requirements.txt
└── .env.example
```

### `security_host_metrics/`

Base class + per-platform modules pull device status from CrowdStrike Falcon, Cisco Umbrella, Kandji, and VMware AirWatch, normalize into a common schema, and ship metrics to Datadog.

### `datadog_monitoring/`

Monitors Datadog log restriction policies for unauthorized changes. Classifies change type (query modified, roles modified) and opens a Jira ticket for security review.

### `mdm_integrations/`

- `kandji_client.py` — Production Kandji API client with retry logic and full device inventory pagination
- `kandji_datadog_pipeline.py` — Polls Kandji and forwards device data to Datadog log intake
- `umbrella_analysis.py` — Pulls all roaming computers from Umbrella, segments by status and sync recency, exports to Excel

### `vulnerability_management/`

- `jira_nessus_sync.py` — Reads Nessus scan findings and creates/updates Jira issues by hostname + plugin ID; handles PCI scans (medium+ severity) separately from standard (high/critical)
- `nessus_agent_deploy.sh` — Installs and links Nessus Agent with timezone-based scanner group assignment

### Setup

```bash
cd python-integrations
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill in credentials
```

All credentials are loaded from environment variables. See [`python-integrations/.env.example`](python-integrations/.env.example) for the full list.

---

## Requirements

- macOS (all shell scripts)
- Root/sudo privileges for install/uninstall scripts
- Python 3.9+ for Python integrations
- Jamf Pro or Kandji for MDM-deployed scripts (optional)

## Security

No hardcoded credentials anywhere in this repo. Sensitive values are passed via environment variables or script arguments. See `python-integrations/.env.example`.
