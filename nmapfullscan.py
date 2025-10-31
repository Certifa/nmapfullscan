#!/usr/bin/env python3

import argparse
import subprocess
from datetime import datetime
from pathlib import Path
import re
from colorama import Fore, Style, init

init(autoreset=True)

def color_port_line(line):
    # Match lines as: NN/proto open ... service version
    m = re.match(r'^(\d+)/(tcp|udp)\s+(open|closed|filtered)\s+(\S+)(.*)', line)
    if m:
        port, proto, state, service, rest = m.groups()
        state_color = Fore.GREEN if state == "open" else Fore.RED
        return (
            f"{Fore.YELLOW}{port}{Style.RESET_ALL}/"
            f"{Fore.CYAN}{proto}{Style.RESET_ALL} "
            f"{state_color}{state}{Style.RESET_ALL} "
            f"{Fore.MAGENTA}{service}{Style.RESET_ALL}{rest}"
        )
    return line

def color_portsummary_line(line):
    m = re.match(r'(Host: .+Ports: )(\d+)(/open/tcp//domain///.*)', line)
    if m:
        hostpart, port, rest = m.groups()
        return f"{hostpart}{Fore.YELLOW}{port}{Style.RESET_ALL}{rest}"
    return line

def main():
    parser = argparse.ArgumentParser(description="Full nmap scan in Python")
    parser.add_argument("target", help="IP or hostname to scan")
    parser.add_argument("--no-udp", action="store_true", help="Skip UDP scan")
    parser.add_argument("--output-dir", default="./nmap-scans", help="Where to save results")
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_target = "".join([c if c.isalnum() or c in "._-" else "_" for c in args.target])
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    outfile = outdir / f"nmap_{safe_target}_{ts}.txt"

    print(f"{Fore.BLUE}🔍 Step 1: Quick TCP-scan...{Style.RESET_ALL}")
    quickscan = subprocess.run(
        ["sudo", "nmap", "-T4", "--min-rate=1000", "-p-", "-n", "-v", args.target, "-oG", "-"],
        text=True, capture_output=True
    )
    with open(outfile, "w") as outfh:
        for line in quickscan.stdout.splitlines():
            if re.match(r'^\d+/(tcp|udp)\s+(open|closed|filtered)', line):
                print(color_port_line(line))
                outfh.write(line + "\n")
            elif "Ports: " in line and "/open/tcp" in line:
                print(color_portsummary_line(line))
                outfh.write(line + "\n")
            elif "open" in line and not line.startswith("Host:"):
                print(Fore.GREEN + line + Style.RESET_ALL)
                outfh.write(line + "\n")
            elif re.search("closed|filtered", line):
                print(Fore.RED + line + Style.RESET_ALL)
                outfh.write(line + "\n")
            else:
                print(line)
                outfh.write(line + "\n")

    # Extract open ports
    open_ports = []
    for line in quickscan.stdout.splitlines():
        if "open" in line and "/tcp" in line:
            parts = line.split()
            for part in parts:
                if "/tcp" in part and "open" in line:
                    port = part.split("/")[0]
                    if port.isdigit():
                        open_ports.append(port)
    ports_str = ",".join(open_ports)

    # Step 2
    if open_ports:
        print(f"{Fore.BLUE}🔎 Step 2: Detailed scan op open TCP-poorten: {Fore.YELLOW}{ports_str}{Style.RESET_ALL}")
        detail = subprocess.run(
            ["sudo", "nmap", "-sV", "-sC", "-p", ports_str, args.target],
            text=True, capture_output=True
        )
        with open(outfile, "a") as outfh:
            for line in detail.stdout.splitlines():
                if re.match(r'^\d+/(tcp|udp)\s+(open|closed|filtered)', line):
                    print(color_port_line(line))
                else:
                    print(line)
                outfh.write(line + "\n")
    else:
        print(Fore.YELLOW + "⚠️ Geen open TCP ports gevonden" + Style.RESET_ALL)

    # Step 3 UDP
    if not args.no_udp:
        print(f"{Fore.BLUE}🌊 Step 3: UDP-scan op top 100 ports...{Style.RESET_ALL}")
        udpscan = subprocess.run(
            ["sudo", "nmap", "-sU", "--top-ports", "100", args.target],
            text=True, capture_output=True
        )
        with open(outfile, "a") as outfh:
            for line in udpscan.stdout.splitlines():
                if re.match(r'^\d+/(tcp|udp)\s+(open|closed|filtered)', line):
                    print(color_port_line(line))
                else:
                    print(line)
                outfh.write(line + "\n")
    else:
        print(Fore.YELLOW + "⚠️ Skipping UDP scan (--no-udp specified)" + Style.RESET_ALL)

    print(f"{Fore.GREEN}📄 All results are saved in: {Fore.GREEN}{outfile}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
