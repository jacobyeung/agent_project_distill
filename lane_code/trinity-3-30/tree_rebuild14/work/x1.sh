date -u +%TZ; hostname -s; df -BG --output=avail /scratch | tail -1; free -g | sed -n 2p; nproc; uptime; ls /scratch/jjyeung/ 2>/dev/null | head; ls /scratch/jjyeung/envs 2>/dev/null
