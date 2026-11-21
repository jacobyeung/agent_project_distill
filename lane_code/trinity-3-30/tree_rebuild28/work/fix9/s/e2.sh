date -u +%TZ
cd /scratch/jjyeung
timeout 300 nice -n 10 find /scratch/jjyeung -xdev \( -name '*_packed.jsonl.gz' -o -name 'ROUTE_DIRECT*.jsonl.gz' -o -name 'u.gz' -o -name 'rows.sqlite' -o -name 'd.db' \) -size +1k -printf '%s %p\n' 2>/dev/null | sort -k2 > /tmp/fix9_find.txt
echo rc=$?; wc -l /tmp/fix9_find.txt; cat /tmp/fix9_find.txt | head -400
date -u +%TZ
