echo "1-18 $(date -u +%TZ) avail=$(free -g | awk '/Mem/{print $7}')G"; nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr "\n" " "; echo
timeout 100 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'bash -s' <<'Y'
echo "2-28 $(date -u +%TZ)"; nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr "\n" " "; echo
nvidia-smi --query-compute-apps=pid,gpu_uuid --format=csv,noheader | while IFS=, read -r p u; do echo -n "$(ps -o user= -p $p) "; done; echo
Y
