# Contributing

## Guidelines

- All scripts must target macOS and be tested on at least one recent macOS version
- Use `set -euo pipefail` at the top of every shell script
- No hardcoded credentials or org-specific values — use environment variables or script arguments
- Privilege checks: scripts requiring root should verify `[ "$(id -u)" -eq 0 ]` and exit with a clear message if not

## Pull requests

- Keep PRs focused on a single script or change
- Include a brief description of what was tested and on which macOS version
- For MDM-targeting scripts, note whether the script is Kandji, Jamf, or generic

## Reporting security issues

See [SECURITY.md](SECURITY.md).
