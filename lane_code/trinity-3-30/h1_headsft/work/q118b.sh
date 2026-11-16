cd /scratch/jjyeung || exit 1
timeout 200 find orch_cd/devs1_direct orch_n30 -maxdepth 8 -type f \( -name "*.jsonl" -o -name "*.json" \) -size -30M 2>/dev/null | grep -v -E "/(tmp|cache|pytest)" | head -5000 > /tmp/h1t.txt
wc -l < /tmp/h1t.txt
timeout 300 xargs -a /tmp/h1t.txt -d '\n' sha256sum 2>/dev/null | grep -E "^(730ed536|4d6c3a94)" | head -6
