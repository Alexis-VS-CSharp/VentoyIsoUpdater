🇬🇧 **English** · 🇫🇷 [Français](CONTRIBUTING.fr.md)

# Contributing

## Adding a distribution

See `CLAUDE.md` for the general architecture. In short: one
`sources/<distro>.py` file (subclassing `BaseChecker`) plus one entry in
`data/distros.json`.

`sources/` is the project's largest surface exposed to external
contributions: it's code that makes network requests to third-party sites
and applies regular expressions to filenames. Before opening a PR touching
`sources/` or `data/distros.json`, please check:

- **HTTPS only.** No `http://` URL unless technically unavoidable and
  documented in a comment (real case: `download.proxmox.com`'s TLS
  certificate doesn't match its own hostname — see `sources/proxmox.py`,
  which uses `enterprise.proxmox.com` instead).
- **`timeout=` is mandatory** on every `requests.get`/`head`/`post` call.
- **Never `shell=True`**, `eval`, `exec`, `pickle`, or `yaml.load`.
- **Real checksum whenever available.** If the source publishes a checksum
  file (`SHA256SUMS`, `CHECKSUM`, `*.sha256`…), populate `VersionInfo`'s
  `checksum=` field — not just `checksum_type=`, which alone triggers no
  verification at all (see `core/downloader.py`). The
  `sources/_checksum.py::fetch_sha256sums` / `fetch_bsd_sha256` helpers
  cover the two most common formats. If no checksum is published, leave
  both unset rather than implying a verification that doesn't happen.
- **No catastrophic-backtracking regexes.** Avoid nested patterns like
  `(.*)+` or `(\d+)+` applied to untrusted text (a filename scanned off the
  drive, an HTML response from a third-party site) — prefer precise
  character classes (`[\d.]+`, etc.), as the rest of `sources/` already
  does.
- **Log failures, don't just swallow them.** `except Exception: return
  None`/`[]` is the expected pattern (an unreachable source shouldn't crash
  the app), but add a `logger.debug(...)` call (see `core/logger.py`) so a
  real bug stays diagnosable instead of being indistinguishable from a
  source that's simply down.

## Tests

```bash
.venv/bin/pytest tests/ -v
```

Any new logic in `core/` deserves a test in `tests/`. The `sources/`
checkers aren't unit-tested one by one (that would mean 64 network-dependent
test suites) — `tests/test_version_checker.py` and
`tests/test_base_checker.py` cover the shared contract (`BaseChecker`,
`VersionInfo`, orchestration).
