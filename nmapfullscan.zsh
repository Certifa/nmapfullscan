nmapfullscan() {
  local skip_udp=false
  local args=()

  for arg in "$@"; do
    case "$arg" in
      --no-udp) skip_udp=true ;;
      *) args+=("$arg") ;;
    esac
  done
  set -- "${args[@]}"

  if [[ $# -lt 1 ]]; then
    echo -e "\e[31m❌ Use: nmapfullscan <IP or hostname> [--no-udp]\e[0m"
    return 1
  fi

  local target=$1

  local outdir="${NMAP_OUTDIR:-./nmap-scans}"
  mkdir -p "$outdir"

  local ts; ts=$(date +%Y%m%d_%H%M%S)
  local safe_target="${target//[^A-Za-z0-9._-]/_}"
  local outfile="${outdir}/nmap_${safe_target}_${ts}.txt"

  # temp bestand + auto cleanup
  local temp; temp="$(mktemp "/tmp/ports_temp_${safe_target}.XXXXXX")"
  trap '[[ -f "$temp" ]] && rm -f "$temp"' EXIT

  echo -e "\e[34m🔍 Step 1: Quick TCP-scan...\e[0m"
  sudo nmap -T4 --min-rate=1000 -p- -n -v "$target" -oG - 2>&1 | tee "$temp" | while IFS= read -r line; do
    if [[ "$line" =~ open ]]; then
      echo -e "\e[32m${line}\e[0m"
    elif [[ "$line" =~ closed|filtered ]]; then
      echo -e "\e[31m${line}\e[0m"
    else
      echo "$line"
    fi
  done | tee "$outfile"

  # Extract open ports
  local openports
  openports=$(grep -oP '^\d+(?=/tcp\s+open)' "$temp" | tr '\n' ',' | sed 's/,$//')

  if [[ -n "$openports" ]]; then
    echo -e "\e[34m🔎 Step 2: Detailed scan op open ports...\e[0m"
    sudo nmap -sV -sC -p "$openports" "$target" | tee -a "$outfile"
  else
    echo -e "\e[33m⚠️ Geen open TCP ports gevonden\e[0m"
  fi

  if ! $skip_udp; then
    echo -e "\e[34m🌊 Step 3: UDP-scan op top 100 ports...\e[0m"
    sudo nmap -sU --top-ports 100 "$target" | tee -a "$outfile"
  else
    echo -e "\e[33m⚠️ Skipping UDP scan (--no-udp specified)\e[0m"
  fi

  echo -e "\e[32m📄 All results are saved in: \e[1m${outfile}\e[0m"
  trap - EXIT
}
