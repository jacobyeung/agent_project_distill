f=/project/community/jjyeung/okh7/e6fc152498/r2/sj/h10sub_b01ec87a6f29b00029a87/items.jsonl
s=$(stat -c %s "$f"); [ "$s" -lt 20000000 ] || { echo TOOBIG >&2; exit 3; }
cat "$f"
