hostname -s
for d in /scratch/jjyeung/orch_n30/native_r2/work/direct /scratch/jjyeung/orch_n30/native_r2/work/analysis; do echo "== $d"; ls -la "$d" 2>&1 | head -30; done
cd /scratch/jjyeung/orch_n30/native_r2/work/direct 2>/dev/null && for f in *.jsonl *.json; do [ -f "$f" ] && [ $(stat -c %s "$f") -lt 30000000 ] && sha256sum "$f"; done
cd /scratch/jjyeung/orch_n30/native_r2/work/direct 2>/dev/null && for f in *.jsonl; do [ -f "$f" ] && echo "$f $(wc -l < $f)" && head -c 1500 "$f" && echo; done 2>/dev/null | head -c 5000
