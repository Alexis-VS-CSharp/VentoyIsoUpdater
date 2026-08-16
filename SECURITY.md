🇬🇧 **English** · 🇫🇷 [Français](SECURITY.fr.md)

# Security policy

VentoyIsoUpdater downloads executable files (the Ventoy installer) and may
request elevated privileges (`pkexec`/`sudo` on Linux, administrator rights
on Windows) to install Ventoy onto a USB drive. Any flaw affecting that
path — download, integrity verification, archive extraction, execution — is
treated as a priority.

## Reporting a vulnerability

Please do **not** open a public issue for a security problem. Instead,
contact: **maxencebaffet@pratimedia.com**

Please include, if possible:
- a description of the issue and its impact;
- steps to reproduce it;
- the affected VentoyIsoUpdater version and OS.

## Response time

Acknowledgment within 7 days. A fix or a remediation plan will be shared
before any public disclosure.

## Scope

In scope, in particular:
- `core/ventoy_installer.py` (downloading, integrity verification, and
  privileged execution of the Ventoy installer);
- `core/downloader.py` (downloading and verifying ISOs/logos);
- the `sources/` checkers (network requests to third-party sources).

Vulnerabilities in the third-party sites queried by `sources/` (Ubuntu,
Debian, etc.) are out of scope for this repository — please report them
directly to the project concerned.
