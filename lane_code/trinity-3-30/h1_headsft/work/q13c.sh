cd /scratch/jjyeung/orch_n30 2>/dev/null || exit 1
for d in tree_rebuild_w rows_rebuild3 rows_rebuild2 rows_rebuild cont_ops/work/d0 native_r4; do [ -d "$d" ] && echo "DIR $d"; done
timeout 150 find tree_rebuild_w rows_rebuild3 rows_rebuild2 native_r4 -maxdepth 7 -type f \( -name "*.jsonl" -o -name "*.jsonl.gz" \) -size -200M 2>/dev/null | head -400 > /tmp/h1c.txt
wc -l < /tmp/h1c.txt
while read f; do case "$f" in *.gz) c=$(timeout 20 zcat "$f" 2>/dev/null | head -c 20000000 | grep -c '<move from=' );; *) c=$(timeout 20 head -c 20000000 "$f" | grep -c '<move from=');; esac; [ "${c:-0}" -gt 0 ] && echo "$c $(stat -c %s "$f") $f"; done < /tmp/h1c.txt | sort -rn | head -12
