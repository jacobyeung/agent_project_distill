hostname -s; date -u +%FT%TZ
df -h /scratch
echo "## scratch depth1"; ls -la /scratch/jjyeung 2>&1
echo "## scratch depth2"; for d in /scratch/jjyeung/*/; do echo "### $d"; ls -la "$d" 2>&1 | head -60; done
echo "## shm"; for d in /dev/shm/jjyeung* /dev/shm/mdg*; do [ -e "$d" ] || continue; echo "### $d"; ls -la "$d" 2>&1 | head -80; done
