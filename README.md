# nmapfullscan

A lightweight Python tool to run quick and targeted Nmap scans and save results. Small, safe, and reproducible workflow for local labs and authorized testing.

---

## Overview

`nmapfullscan.py`:

- Runs a **quick TCP sweep** (grepable output) to discover open ports.
- Runs a **targeted detailed scan** (`-sC -sV` and additional options) on discovered ports.
- Lists all scanned ports.
- Appends a **top-100 UDP** scan.
- Saves the final human-readable report to `./nmap-scans/` by default (can override with `--output-dir`).

---

## Behaviour & internals (concise)

Flow:

- Quick TCP sweep (nmap -T4 --min-rate=1000 -p- -n -v -oG -) to find open ports
- Parse open ports from grepable output
- If open ports exist → nmap -sC -sV -p<ports> saved to the final text file (and XML if configured)
- Append nmap -sU --top-ports 100 to the same text file

---

## Example

![Example scan](docs/nmap_scan.jpg)

---

## Files in this repo
**nmapfullscan/**
- ├─ nmapfullscan.py # the main Python tool
- ├─ README.md # you are reading it
- └─ .gitignore # recommended ignore rules

---

## Prerequisites

- Python 3.8+ installed and available on your command line
- Nmap installed and in PATH (sudo required for some scans)
  - Linux: `sudo apt install nmap` or `sudo pacman -S nmap`
  - macOS: `brew install nmap`
- Python modules: `colorama`, `requests` (install via `pip install colorama requests`)

---

## Install (quick)

1. Clone this repo:
git clone https://github.com/Certifa/nmapfullscan.git
2. Install the `requirements` with
- `pip install -r requirements.txt`
cd nmapfullscan
3. Optionally, create an alias for easier use: alias nmapfullscan='python3 /full/path/to/nmapfullscan.py'
4. Reload your shell or `.zshrc`:
source ~/.zshrc

---

## Usage

nmapfullscan <IP or hostname> [--no-udp] [--output-dir <directory>]

Reactivate your regular scanning workflow, with enhanced readability and quick results saving.

---

## Safety & legal (important)

Only run scans against systems you own or have explicit written permission to test. Unauthorized scanning is illegal and may cause disruption.

By using `nmapfullscan`, you agree to the following responsibilities:

- Obtain explicit, written authorization before scanning third-party systems.
- Respect any scope, time-window, and usage limits in the authorization.
- Use reasonable timing/rate limits and avoid aggressive scans on production systems.
- Do **not** share or publish scan outputs or sensitive information.
- Follow responsible disclosure processes if vulnerabilities are found.
- The author is not liable for misuse.

---

## Contributions and feedback

Fork, open issues, or pull requests are welcome via GitHub.

---

> **Disclaimer:** This tool is provided for educational and authorized testing only. The author accepts no liability for misuse.
