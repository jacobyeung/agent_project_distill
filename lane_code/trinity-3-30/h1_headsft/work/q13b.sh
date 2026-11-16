cd /scratch/jjyeung/orch_n30 || exit 1
timeout 200 find cont_ops/work/d0 b13_facing rows_rebuild3 -maxdepth 9 -type f \( -name "*.jsonl" -o -name "*.json" \) -size -30M 2>/dev/null | head -3000 > /tmp/h1q.txt
wc -l < /tmp/h1q.txt
timeout 240 xargs -a /tmp/h1q.txt -d '\n' sha256sum 2>/dev/null | grep -E "^(730ed536|4d6c3a94)" | head -6
