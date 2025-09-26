# nmapfullscan

Zsh helper function to run quick → targeted Nmap scans and save results.
Small, safe and reproducible workflow for local labs and authorised testing.

---

## Summary

`nmapfullscan` is a tiny zsh helper that:

- Runs a **quick TCP sweep** (grepable) to discover open ports.
- Runs a **targeted detailed scan** (`-sC -sV and more`) on discovered ports.
- Lists all scanned ports.
- Appends a **top-100 UDP** scan.
- Saves the final human-readable report to `./nmap-scans/` by default (override with `NMAP_OUTDIR`).

This repo contains the function as a file you can `source` into your `~/.zshrc`.

---

## Behaviour & internals (concise)

Flow:

Quick TCP sweep (nmap -T4 --min-rate=1000 -p- -n -v -oG -) to find open ports.

Parse open ports from grepable output.

If open ports exist → nmap -sC -sV -p<ports> saved to the final text file (and XML if configured).

Append nmap -sU --top-ports 100 to the same text file.

## Example

![Example scan](docs/nmap_scan.jpg)

## Files in this repo

```
nmapfullscan/
├─ scripts/
│ └─ nmapfullscan.zsh # the function (source this file in your zsh)
├─ README.md # you are reading it
└─ .gitignore # recommended ignore rules
```

---

## Prerequisites

- `zsh` (interactive shell) — function is intended to be `sourced`.
- `nmap` installed and in PATH (sudo required for some scans).
  - Linux: `sudo apt install nmap` or `sudo pacman -S nmap`
  - macOS: `brew install nmap`
- Basic familiarity with running commands and editing `~/.zshrc`.

---

## Install (quick)

1. Clone the repo:

```bash
git clone https://github.com/<youruser>/nmapfullscan.git
cd nmapfullscan
echo "source $(pwd)/scripts/nmapfullscan.zsh" >> ~/.zshrc
# then reload:
source ~/.zshrc

Or open ~/.zshrc and paste:
source /full/path/to/nmapfullscan/scripts/nmapfullscan.zsh

Test locally
nmapfullscan 127.0.0.1
```

## Output & file naming

By default the function writes to the directory where **you** invoked it (or NMAP_OUTDIR):

nmap*<safe_target>*<YYYYmmdd_HHMMSS>.txt — final human-readable report (detailed TCP + UDP appended).

When NMAP*SAVE_XML=1, nmap*<safe*target>*<ts>.xml — machine-readable XML for parsers.

Temporary grepable output is created during the run and moved/removed safely; no leftover temp files.

safe_target is a sanitized version of the input target for safe filenames (non-ASCII and special characters replaced).

## S## Safety & legal (important)

**Only run scans against systems you own or have explicit written permission to test.**
Unauthorized scanning can be illegal, violate Terms of Service, and may cause disruption.

By using `nmapfullscan` you agree to the following responsibilities:

- **Permission:** Obtain explicit, written authorization before scanning third-party systems (customers, employers, CTF/HTB machines unless the platform explicitly allows sharing, etc.).
- **Scope & rules:** Respect any scope, time-window, and usage limits in the authorization. For CTF platforms (HackTheBox, etc.) follow their rules and avoid publishing identifiable targets or spoilers.
- **Minimize impact:** Use reasonable timing/rate limits on production systems; do not perform aggressive scans without coordination. Consider `--host-timeout`, `--max-retries`, or lower `-T` values in sensitive environments.
- **Data handling:** Do **not** commit or publish scan outputs, target lists, credentials, or any sensitive artifacts. Use `.gitignore` to exclude `nmap-scans/` and similar files.
- **Responsible disclosure:** If you discover a vulnerability on a third-party system, follow a responsible disclosure process — contact the owner/provider and avoid public disclosure until it’s fixed or permitted.
- **Legal compliance:** You are responsible for complying with applicable laws and organizational policies. The repository author is not liable for misuse.

If you want to include a short acknowledgement line in your repo:

> **Disclaimer:** This tool is provided for educational and authorized testing only. The author accepts no liability for misuse.
