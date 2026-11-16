cd /dev/shm/jjyeung 2>/dev/null && { ls; echo ---; ls -la exports/m544 | head -30; echo ---; ls b05 b05/stage 2>/dev/null | head -30; }; echo ---; df -h /dev/shm | tail -1; free -g | head -2; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
ls /scratch/jjyeung/orch_n30/ 2>/dev/null | tr '\n' ' '
