nmapfullscan() {
  if [[ -z "$1" ]]; then
    echo -e "\e[31m❌ Use: nmapfullscan <IP or hostname>\e[0m"; return 1
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
  sudo nmap -T4 --min-rate=1000 -p- -n -v "$target" -oG - | tee "$temp"

  local openports
  openports=$(grep -oP '\d+/open' "$temp" | cut -d'/' -f1 | tr '\n' ',' | sed 's/,$//')

  if [[ -z "$openports" ]]; then
    echo -e "\e[31m⚠️ No open TCP-ports are found on ${target}.\e[0m"
  else
    echo -e "\e[32m✅ Found open TCP-ports: \e[33m${openports}\e[0m"
    echo -e "\e[34m🔬 Step 2: Detailed TCP-scan...\e[0m"

    local scan_output
    scan_output=$(sudo nmap -sC -sV -p"$openports" "$target")

    echo "$scan_output" | while IFS= read -r line; do
      if [[ "$line" =~ ^[0-9]+/tcp[[:space:]]+open ]]; then
        echo -e "\e[32m${line}\e[0m"
      elif [[ "$line" =~ ^[0-9]+/tcp[[:space:]]+closed ]]; then
        echo -e "\e[31m${line}\e[0m"
      else
        echo "$line"
      fi
    done | tee "$outfile"
  fi

  echo -e "\e[34m🌊 Step 3: UDP-scan on top 100 ports...\e[0m"
  sudo nmap -sU --top-ports 100 "$target" | tee -a "$outfile"

  echo -e "\e[32m📄 All results are saved in: \e[1m${outfile}\e[0m"
  trap - EXIT
}
