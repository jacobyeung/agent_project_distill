set -u
hostname -s; date -u +%FT%TZ; free -g | head -2; df -h /scratch | tail -1
for d in /scratch/jjyeung/k1/m544_parts /scratch/jjyeung/orch_n30/trin_read3 /scratch/jjyeung/orch_n30/trin_read2 /scratch/jjyeung/orch_n30/trin_read; do echo "== $d"; ls -la $d 2>&1 | head -12; done
find /scratch/jjyeung/k1 /scratch/jjyeung/orch_n30/trin_read3 -maxdepth 5 \( -name 'heads.pt' -o -name 'full_weights.json' -o -name 'artifact.json' \) 2>/dev/null | head -10
for f in $(find /scratch/jjyeung/k1 /scratch/jjyeung/orch_n30/trin_read3 -maxdepth 5 -name 'heads.pt' 2>/dev/null | head -3); do ls -la $f; done
ls /scratch/jjyeung/envs 2>&1 | head -20
