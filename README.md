# security-tooling-scripts

macOS shell scripts for endpoint security tool validation, deployment, and remediation. Covers Cisco Umbrella/Secure Client, CrowdStrike Falcon, Tenable Nessus Agent, and macOS system utilities.

All scripts target macOS and are designed to run in MDM-managed environments (Kandji, Jamf).

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
sudo TENABLE_LINKING_KEY=<key> NESSUS_AGENT_DMG=NessusAgent-10.6.1.dmg \
    sh nessus/nessus_postinstall.sh
```

| Variable | Description |
|---|---|
| `TENABLE_LINKING_KEY` | Agent linking key from Tenable → Sensors |
| `NESSUS_AGENT_DMG` | DMG filename placed in `/private/var/tmp/` |

### `nessus_audit_enforce.sh`

Compliance check that validates the Nessus Agent is:
1. Installed at the expected path
2. Running (`nessusd` process check)
3. Linked to `sensor.cloud.tenable.com:443`

Returns exit 0 on pass. Set `FORCE_REINSTALL=true` to trigger a reinstall path.

```bash
sh nessus/nessus_audit_enforce.sh
# Force reinstall
FORCE_REINSTALL=true sh nessus/nessus_audit_enforce.sh
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

Backs up macOS Mail messages to a timestamped directory without touching originals. Recursively scans `~/Library/Mail/V9` for `.mbox` files and for each mailbox:
- Exports individual messages as `.eml` files
- Writes a `metadata.json` with subject, sender, recipient, and date

```bash
python macos-utilities/mail_backup.py
# Optional: specify output directory
python -c "from mail_backup import backup_mac_mail; backup_mac_mail('/path/to/backup')"
```

---

## Requirements

- macOS (all scripts)
- Root/sudo privileges for install/uninstall scripts
- Python 3.9+ for `mail_backup.py` (stdlib only, no dependencies)
- Jamf Pro or similar MDM for Extension Attribute scripts (optional)

## Usage in MDM

The CrowdStrike scripts (`falcon_status.sh`, `falcon_last_seen.sh`) are formatted as Jamf Extension Attributes — the `<result>` tag wrapping is parsed directly by Jamf inventory.

The Nessus lifecycle scripts (`nessus_preinstall.sh`, `nessus_postinstall.sh`, `nessus_audit_enforce.sh`) are designed as Kandji/Jamf custom scripts. Pass `TENABLE_LINKING_KEY` and `NESSUS_AGENT_DMG` via your MDM's script parameter fields.

## Security

None of these scripts contain hardcoded credentials. Sensitive values (Tenable linking key) are passed via environment variables. See `.env.example`.
