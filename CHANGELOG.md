🇬🇧 **English** · 🇫🇷 [Français](CHANGELOG.fr.md)

# Changelog

All notable changes to this project are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.1.2] — 2026-09-14

### Fixed
- **Downloaded Ventoy forgotten every time the "Create a Ventoy drive" wizard was reopened**: the download went to a throwaway `tempfile.mkdtemp()` directory that only the running dialog instance knew about. Closing the wizard and reopening it (or even just letting the OS clean `/tmp`) made it report "Ventoy not found locally" again, forcing a full re-download — and, since nothing then re-selected the USB drive relationship automatically, it could look like the download "did nothing" even though it had actually just repeated itself. Fixed by downloading into a persistent cache (`~/.local/share/ventoyisoupdater/ventoy/`) that both the download step and the "already installed?" check now look at, so a previously downloaded copy is found immediately and the Install button is ready right away. The now-unneeded archive is also deleted right after extraction instead of being left behind on every download.
- **Ventoy installation silently doing nothing on Linux**: `Ventoy2Disk.sh` always asks "Continue? (y/n)" on stdin before wiping the disk (twice, for a plain install), and has no flag to skip it. The app ran it without ever answering that prompt, so depending on how stdin was inherited it either hung until the 2-minute timeout, or hit EOF immediately, read that as "no", and exited with status 0 — which the app then reported as a **successful** install even though the disk was never touched. Fixed by feeding the confirmation automatically (the same warning is already shown to the user beforehand, in the app's own confirmation dialog), and raised the timeout to 180s.
- **Ventoy installation always failing on Linux**: the code looked for the installer script as `ventoy2disk.sh`, but the official Ventoy Linux archive ships it as `Ventoy2Disk.sh` (mixed case). On any case-sensitive filesystem (ext4, btrfs, xfs — i.e. virtually every Linux distro, Fedora included) the lookup never matched, so `find_ventoy_in_dir`/`find_ventoy_binary` always returned nothing and the app reported "Ventoy2Disk.sh not found" even right after downloading and extracting a fresh copy. Fixed by matching the real filename (both cases now accepted, as a third-party package could still use the lowercase form).

## [1.1.1] — 2026-08-23

### Fixed
- **Logo download failing for 4 distros** (Kali, AlmaLinux, Manjaro, Nobara): `logo_url` pointed to an `.svg` file, a format PIL can't decode at all — every logo sync attempt failed with a raw `cannot identify image file` error, for every user, every time. Fixed by bundling a real PNG for each under `assets/logos/` (same mechanism already used for Proxmox/Pop!_OS) instead of depending on a vector URL.

## [1.1.0] — 2026-08-22

### Added
- **ARM64 support alongside x86_64** for 13 distributions whose upstream source publishes a genuine, generic, Ventoy-bootable ARM64 ISO (not a device-specific SBC image): Proxmox VE, AlmaLinux, CentOS Stream 9/10, Rocky Linux, Debian, FreeBSD, Gentoo, openSUSE Tumbleweed, Kali Linux, Oracle Linux, Alpine Linux, Void Linux (glibc+musl), Ubuntu Server. x86_64 stays the priority default everywhere; each ARM64 build appears as its own clearly labeled `(ARM64)` entry, never mixed with its x86_64 counterpart. 123 registered variants, up from 108.

### Fixed
- **Void Linux (glibc)**: the filename pattern no longer matched the real files the checker itself downloads (missing the `-base`/`-xfce`/etc. suffix) — local version detection was silently broken.
- **CentOS Stream 9/10**: the x86_64 filename pattern was broad enough to also match an aarch64 file sitting on the same USB drive, defeating the point of telling the two architectures apart.

## [1.0.1] — 2026-08-22

### Fixed
- **Proxmox VE**: the upstream directory now lists an arm64 ISO (`proxmox-ve_9.2-1-arm64.iso`) alongside the regular amd64 build. The filename regex only avoided matching it by accident (no explicit architecture anchor) — hardened to explicitly reject any filename containing `arm`.
- Same fix also deduplicates matches: the source page repeats each filename several times (link, size, date), which previously produced 5–10 duplicate entries per version in the version browser.

### Internal
- Every code comment, docstring, and diagnostic log message translated to English (previously French-first). No effect on the app's UI or behavior — the French/English toggle for what the *user* sees is untouched.

[1.1.1]: https://github.com/celmax85/VentoyIsoUpdater/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/celmax85/VentoyIsoUpdater/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/celmax85/VentoyIsoUpdater/compare/v1.0.0...v1.0.1
