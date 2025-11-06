#!/usr/bin/env python3
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
import re
from colorama import Fore, Style, init

init(autoreset=True)

PORT_ENTRY_RE = re.compile(
    r"(\d+)/(open|closed|filtered|open\|filtered)/(tcp|udp)//([^/]*)/"
)


def color_port_line(line):
    m = re.match(
        r"^(\d+)/(tcp|udp)\s+(open|closed|filtered|open\|filtered)\s+(\S+)(.*)", line
    )
    if m:
        port, proto, state, service, rest = m.groups()
        state_color = Fore.GREEN if state.startswith("open") else Fore.RED
        return (
            f"{Fore.YELLOW}{port}{Style.RESET_ALL}/"
            f"{Fore.CYAN}{proto}{Style.RESET_ALL} "
            f"{state_color}{state}{Style.RESET_ALL} "
            f"{Fore.MAGENTA}{service}{Style.RESET_ALL}{rest}"
        )
    return line


def color_portsummary_line(line):
    m = re.match(r"(Host: .+Ports: )(\d+)(/open/tcp//domain///.*)", line)
    if m:
        hostpart, port, rest = m.groups()
        return f"{hostpart}{Fore.YELLOW}{port}{Style.RESET_ALL}{rest}"
    return line


def parse_open_tcp_ports_from_grepable(og_text):
    open_ports = []
    for line in og_text.splitlines():
        if line.startswith("Host:") and "Ports:" in line:
            try:
                ports_field = line.split("Ports:")[1].strip()
            except IndexError:
                continue
            entries = [e.strip() for e in ports_field.split(",")]
            for e in entries:
                parts = e.split("/")
                if len(parts) >= 3:
                    port_s, state, proto = parts[0], parts[1], parts[2]
                    if proto == "tcp" and state == "open" and port_s.isdigit():
                        open_ports.append(port_s)
    open_ports = sorted(set(open_ports), key=lambda x: int(x))
    return open_ports


def main():
    parser = argparse.ArgumentParser(description="Full nmap scan in Python")
    parser.add_argument("target", help="IP of hostname to scan")
    parser.add_argument("--no-udp", action="store_true", help="Skip UDP scan")
    parser.add_argument(
        "--output-dir", default="./nmap-scans", help="Where to save results"
    )
    parser.add_argument(
        "--profile",
        choices=["safe", "balanced", "fast"],
        default="balanced",
        help="Timing profiel (safe/balanced/fast)",
    )
    args = parser.parse_args()

    # Timing presets Nmap docs:
    # - balanced: T4 with min-rate 1000 and max-retries 2
    # - fast: more agressive for HTB; risk for possible misses
    if args.profile == "safe":
        tcp_timing = ["-T3", "--min-rate", "300", "--max-retries", "3"]  # normal paced
    elif args.profile == "fast":
        tcp_timing = ["-T4", "--min-rate", "5000", "--max-retries", "1"]  # fast
    else:
        tcp_timing = [
            "-T4",
            "--min-rate",
            "1000",
            "--max-retries",
            "2",
        ]  # balanced default

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_target = "".join(
        [c if c.isalnum() or c in "._-" else "_" for c in args.target]
    )
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    outfile_txt = outdir / f"nmap_{safe_target}_{ts}.txt"
    outfile_xml_quick = outdir / f"nmap_{safe_target}_{ts}_quick.xml"
    outfile_xml_detail = outdir / f"nmap_{safe_target}_{ts}_detail.xml"
    outfile_xml_udp = outdir / f"nmap_{safe_target}_{ts}_udp.xml"

    print(f"{Fore.BLUE}🔍 Step 1: Quick TCP-scan...{Style.RESET_ALL}")
    # -n to skip DNS
    quick_cmd = (
        ["sudo", "nmap", "-sS", "-n", "-p-", "-v"]
        + tcp_timing
        + ["-oG", "-", "-oX", str(outfile_xml_quick), args.target]
    )
    quickscan = subprocess.run(quick_cmd, text=True, capture_output=True)

    with open(outfile_txt, "w") as outfh:
        for line in quickscan.stdout.splitlines():
            if re.match(
                r"^\d+/(tcp|udp)\s+(open|closed|filtered|open\|filtered)", line
            ):
                colored = color_port_line(line)
                print(colored)
                outfh.write(line + "\n")
            elif "Ports: " in line and line.startswith("Host:"):
                colored = color_portsummary_line(line)
                print(colored)
                outfh.write(line + "\n")
            elif "open" in line and not line.startswith("Host:"):
                print(Fore.GREEN + line + Style.RESET_ALL)
                outfh.write(line + "\n")
            elif re.search(r"\b(closed|filtered)\b", line):
                print(Fore.RED + line + Style.RESET_ALL)
                outfh.write(line + "\n")
            else:
                print(line)
                outfh.write(line + "\n")

    open_ports = parse_open_tcp_ports_from_grepable(quickscan.stdout)
    ports_str = ",".join(open_ports)

    # Step 2: Detailscan on open TCP
    if open_ports:
        print(
            f"{Fore.BLUE}🔎 Step 2: Detailed scan op open TCP-poorten: {Fore.YELLOW}{ports_str}{Style.RESET_ALL}"
        )
        detail_cmd = [
            "sudo",
            "nmap",
            "-sV",
            "--version-intensity",
            "2",
            "-sC",
            "-n",
            "-p",
            ports_str,
            "-T4",
            "-oX",
            str(outfile_xml_detail),
            args.target,
        ]
        detail = subprocess.run(detail_cmd, text=True, capture_output=True)
        with open(outfile_txt, "a") as outfh:
            for line in detail.stdout.splitlines():
                if re.match(
                    r"^\d+/(tcp|udp)\s+(open|closed|filtered|open\|filtered)", line
                ):
                    print(color_port_line(line))
                else:
                    print(line)
                outfh.write(line + "\n")
    else:
        print(Fore.YELLOW + "⚠️ Geen open TCP ports gevonden" + Style.RESET_ALL)

    # Step 3: UDP
    if not args.no_udp:
        print(f"{Fore.BLUE}🌊 Step 3: UDP-scan op top 100 ports...{Style.RESET_ALL}")
        udp_cmd = [
            "sudo",
            "nmap",
            "-sU",
            "--top-ports",
            "100",
            "-sV",
            "--version-intensity",
            "2",
            "-n",
            "-T4",
            "--max-retries",
            "1",
            "-oX",
            str(outfile_xml_udp),
            args.target,
        ]
        udpscan = subprocess.run(udp_cmd, text=True, capture_output=True)
        with open(outfile_txt, "a") as outfh:
            for line in udpscan.stdout.splitlines():
                if re.match(
                    r"^\d+/(tcp|udp)\s+(open|closed|filtered|open\|filtered)", line
                ):
                    print(color_port_line(line))
                else:
                    print(line)
                outfh.write(line + "\n")
    else:
        print(
            Fore.YELLOW + "⚠️ Skipping UDP scan (--no-udp specified)" + Style.RESET_ALL
        )

    print(
        f"{Fore.GREEN}📄 All results are saved in: {Fore.GREEN}{outfile_txt}{Style.RESET_ALL}"
    )


if __name__ == "__main__":
    main()
