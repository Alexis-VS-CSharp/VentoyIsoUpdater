🇬🇧 **English** · 🇫🇷 [Français](CHANGELOG.fr.md)

# Changelog

All notable changes to this project are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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

[1.1.0]: https://github.com/celmax85/VentoyIsoUpdater/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/celmax85/VentoyIsoUpdater/compare/v1.0.0...v1.0.1
